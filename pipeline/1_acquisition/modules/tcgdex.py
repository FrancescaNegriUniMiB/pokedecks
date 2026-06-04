import concurrent.futures
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import click
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout
from tqdm import tqdm

import config


def _request_json(url: str, context: str) -> Any:
    '''GET JSON with retries on transient network or server errors.'''
    last_error: Optional[Exception] = None
    for attempt in range(config.API_RETRIES):
        try:
            resp = requests.get(url, timeout=config.API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as exc:
            last_error = exc
            status = exc.response.status_code if exc.response is not None else None
            if status == 404:
                raise
            if status in {429, 500, 502, 503, 504} and attempt + 1 < config.API_RETRIES:
                wait = config.API_RETRY_BACKOFF_SEC * (attempt + 1)
                click.echo(
                    f"{context}: HTTP {status}, retry {attempt + 1}/{config.API_RETRIES - 1} in {wait:.0f}s…",
                    err=True,
                )
                time.sleep(wait)
                continue
            raise
        except (ConnectionError, Timeout) as exc:
            last_error = exc
            if attempt + 1 < config.API_RETRIES:
                wait = config.API_RETRY_BACKOFF_SEC * (attempt + 1)
                click.echo(
                    f"{context}: network error, retry {attempt + 1}/{config.API_RETRIES - 1} in {wait:.0f}s…",
                    err=True,
                )
                time.sleep(wait)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError(f"{context}: request failed")

def fetch_set_list() -> List[Dict[str, Any]]:
    '''Fetch the set summary list from GET /sets.'''
    url = f"{config.TCGDEX_BASE}/sets"
    try:
        return _request_json(url, "Set list")
    except Exception as e:
        click.echo(f"Failed to fetch sets: {e}", err=True)
        return []

def fetch_set_details(
        sets: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
    '''Index each set, then download all card details in one parallel batch.'''

    def _fetch_one_card(card_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        safe_id = urllib.parse.quote(card_id, safe="")
        url = f"{config.TCGDEX_BASE}/cards/{safe_id}"
        try:
            return _request_json(url, f"Card {card_id}"), None
        except HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None, "not_found"
            click.echo(f"Failed to fetch details for {card_id}: {exc}", err=True)
            return None, "http_error"
        except (ConnectionError, Timeout) as exc:
            click.echo(f"Failed to fetch details for {card_id}: {exc}", err=True)
            return None, "network"
        except Exception as exc:
            click.echo(f"Failed to fetch details for {card_id}: {exc}", err=True)
            return None, "other"

    def _fetch_cards(
            card_ids: List[str],
        ) -> Tuple[List[Dict[str, Any]], List[str]]:

        if not card_ids:
            return [], []

        results: List[Dict[str, Any]] = []
        failed_ids: List[str] = []
        error_counts: Dict[str, int] = {
            "not_found": 0, "network": 0, "http_error": 0, "other": 0,
        }
        max_workers = config.MAX_CONCURRENT_REQUESTS
        total = len(card_ids)

        click.echo(
            f"Acquisition: downloading details for {total} cards "
            f"({max_workers} workers, up to {config.API_RETRIES} retries on network errors)…"
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {
                executor.submit(_fetch_one_card, card_id): card_id
                for card_id in card_ids
            }
            card_bar = tqdm(
                concurrent.futures.as_completed(future_to_id),
                total=total,
                desc="Cards",
            )
            for future in card_bar:
                card_id = future_to_id[future]
                data, error_kind = future.result()
                if data:
                    results.append(data)
                else:
                    failed_ids.append(card_id)
                    if error_kind:
                        error_counts[error_kind] = error_counts.get(error_kind, 0) + 1
                done = card_bar.n
                card_bar.set_postfix(
                    ok=len(results),
                    failed=len(failed_ids),
                    overall=f"{100 * done / total:.1f}%",
                    refresh=False,
                )

        click.echo(
            f"Acquisition: details done — {len(results)} ok, {len(failed_ids)} failed "
            f"(not_found={error_counts['not_found']}, network={error_counts['network']}, "
            f"http={error_counts['http_error']}, other={error_counts['other']})"
        )
        return results, failed_ids

    release_dates: Dict[str, Optional[str]] = {}
    card_ids: List[str] = []
    set_total = len(sets)

    set_bar = tqdm(sets, desc="Sets")
    for sets_done, set_info in enumerate(set_bar, start=1):
        set_id = set_info.get("id")
        if not set_id:
            continue

        safe_id = urllib.parse.quote(set_id, safe="")
        url = f"{config.TCGDEX_BASE}/sets/{safe_id}"
        try:
            set_data = _request_json(url, f"Set {set_id}")
        except Exception as e:
            click.echo(f"Failed to fetch set {set_id}: {e}", err=True)
            continue

        release_dates[set_id] = set_data.get("releaseDate")
        ids = [c["id"] for c in (set_data.get("cards") or []) if c.get("id")]
        card_ids.extend(ids)

        set_bar.set_postfix(
            indexed=f"{len(card_ids):,} cards",
            overall=f"{100 * sets_done / set_total:.1f}%",
            refresh=False,
        )

    if not card_ids:
        return [], []

    details, failed_ids = _fetch_cards(card_ids)
    acquired: List[Dict[str, Any]] = []
    for detail in details:
        set_id = (detail.get("set") or {}).get("id")
        if set_id:
            detail.setdefault("set", {})["releaseDate"] = release_dates.get(set_id)
        acquired.append(detail)

    return acquired, failed_ids
