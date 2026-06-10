#!/usr/bin/env python3

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import click

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config

WORKFLOW = "update-snapshot.yml"
ARTIFACT = "pokedecks-snapshot"


def _request(url: str, token: str | None = None) -> bytes:
    headers = {"User-Agent": config.USER_AGENT, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def _github_json(url: str, token: str | None = None):
    return json.loads(_request(url, token).decode())


def _download(url: str, dest: Path, token: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(Request(url, headers={"User-Agent": config.USER_AGENT}), timeout=300) as resp:
        with dest.open("wb") as fh:
            shutil.copyfileobj(resp, fh)


def _extract_zip(zip_path: Path, dest: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    data_dir = dest / "data"
    if data_dir.is_dir():
        return data_dir
    if (dest / "pokedecks.db").is_file():
        return dest
    raise click.ClickException(f"Unexpected zip layout: {zip_path.name}")


def _merge_db(target: Path, sources: list[Path]) -> None:
    if not sources:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(sources[0], target)
        sources = sources[1:]
    conn = sqlite3.connect(target)
    for src in sources:
        conn.execute("ATTACH DATABASE ? AS merge_src", (str(src),))
        conn.execute("INSERT OR IGNORE INTO card_prices SELECT * FROM merge_src.card_prices")
        try:
            conn.execute(
                "INSERT OR IGNORE INTO user_collection SELECT * FROM merge_src.user_collection"
            )
        except sqlite3.OperationalError:
            pass
        conn.execute("DETACH DATABASE merge_src")
    conn.commit()
    conn.close()


def _merge_tree(target: Path, sources: list[Path], subdir: str) -> None:
    out = target / subdir
    out.mkdir(parents=True, exist_ok=True)
    for src_root in sources:
        src = src_root / subdir
        if not src.is_dir():
            continue
        for item in src.rglob("*"):
            if item.is_file():
                rel = item.relative_to(src)
                dest = out / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)


def _list_snapshot_dates(db_path: Path) -> list[str]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT DISTINCT snapshot_date FROM card_prices ORDER BY snapshot_date DESC"
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def _list_release_zips(repo: str, limit: int, token: str | None) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
    try:
        releases = _github_json(url, token)
    except HTTPError as exc:
        raise click.ClickException(f"GitHub releases API failed: {exc}") from exc
    items: list[dict] = []
    for rel in releases:
        for asset in rel.get("assets", []):
            if asset["name"].endswith(".zip"):
                items.append(
                    {
                        "tag": rel["tag_name"],
                        "url": asset["browser_download_url"],
                        "name": asset["name"],
                        "published_at": rel["published_at"],
                    }
                )
                break
    items.sort(key=lambda item: item["published_at"])
    return items[-limit:]


def _download_releases(repo: str, limit: int, dest: Path, token: str | None) -> list[str]:
    releases = _list_release_zips(repo, limit, token)
    if not releases:
        raise click.ClickException(f"No release zips found for {repo}")

    extracted: list[Path] = []
    tags: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pokedecks-snap-") as tmp:
        tmp_root = Path(tmp)
        for rel in releases:
            click.echo(f"Downloading release {rel['tag']} ({rel['name']})...")
            zip_path = tmp_root / rel["name"]
            _download(rel["url"], zip_path, token)
            extract_dir = tmp_root / rel["tag"]
            extracted.append(_extract_zip(zip_path, extract_dir))
            tags.append(rel["tag"])

        db_sources = [path / "pokedecks.db" for path in extracted if (path / "pokedecks.db").is_file()]
        if not db_sources:
            raise click.ClickException("Downloaded releases do not contain pokedecks.db")

        dest.mkdir(parents=True, exist_ok=True)
        _merge_db(dest / "pokedecks.db", db_sources)
        _merge_tree(dest, extracted, "quality")
        _merge_tree(dest, extracted, "analysis")

    return tags


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _download_artifacts(repo: str, limit: int, dest: Path) -> list[str]:
    if not _gh_available():
        raise click.ClickException("GitHub CLI (gh) is required for artifact downloads")

    proc = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            repo,
            f"--workflow={WORKFLOW}",
            f"--limit={limit}",
            "--status=success",
            "--json",
            "databaseId,displayTitle,createdAt",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise click.ClickException(proc.stderr.strip() or "gh run list failed")

    runs = json.loads(proc.stdout or "[]")
    if not runs:
        raise click.ClickException(f"No successful runs found for {WORKFLOW}")

    extracted: list[Path] = []
    labels: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pokedecks-art-") as tmp:
        tmp_root = Path(tmp)
        for run in reversed(runs):
            run_id = str(run["databaseId"])
            label = run.get("displayTitle") or run_id
            click.echo(f"Downloading artifact from run {run_id}...")
            out_dir = tmp_root / run_id
            out_dir.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    "gh",
                    "run",
                    "download",
                    run_id,
                    "--repo",
                    repo,
                    "-n",
                    ARTIFACT,
                    "-D",
                    str(out_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                raise click.ClickException(proc.stderr.strip() or f"gh run download {run_id} failed")
            if (out_dir / "pokedecks.db").is_file():
                extracted.append(out_dir)
            elif (out_dir / "data" / "pokedecks.db").is_file():
                extracted.append(out_dir / "data")
            else:
                raise click.ClickException(f"Artifact from run {run_id} has no pokedecks.db")
            labels.append(label)

        db_sources = [path / "pokedecks.db" for path in extracted]
        dest.mkdir(parents=True, exist_ok=True)
        _merge_db(dest / "pokedecks.db", db_sources)
        _merge_tree(dest, extracted, "quality")
        _merge_tree(dest, extracted, "analysis")

    return labels


@click.command()
@click.option("--limit", default=3, show_default=True, help="Number of snapshots to fetch")
@click.option("--repo", default=config.GITHUB_REPO, show_default=True)
@click.option(
    "--source",
    type=click.Choice(["auto", "releases", "artifacts"]),
    default="auto",
    show_default=True,
)
@click.option("--dest", default="data", type=click.Path(path_type=Path), show_default=True)
def main(limit: int, repo: str, source: str, dest: Path) -> None:
    """Download pre-built snapshots into data/ (GitHub Releases, no gh required)."""
    token = os.environ.get("GITHUB_TOKEN")
    dest = ROOT / dest

    if source == "auto":
        try:
            labels = _download_releases(repo, limit, dest, token)
            source_used = "releases"
        except click.ClickException as releases_err:
            if _gh_available():
                labels = _download_artifacts(repo, limit, dest)
                source_used = "artifacts"
            else:
                raise click.ClickException(
                    f"{releases_err}\nInstall gh for CI artifacts, or publish GitHub Releases."
                ) from releases_err
    elif source == "releases":
        labels = _download_releases(repo, limit, dest, token)
        source_used = "releases"
    else:
        labels = _download_artifacts(repo, limit, dest)
        source_used = "artifacts"

    db_path = dest / "pokedecks.db"
    dates = _list_snapshot_dates(db_path)
    click.echo(f"Source: {source_used}")
    click.echo(f"Fetched: {', '.join(labels)}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Snapshot dates in DB: {', '.join(dates) if dates else '(none)'}")


if __name__ == "__main__":
    main()
