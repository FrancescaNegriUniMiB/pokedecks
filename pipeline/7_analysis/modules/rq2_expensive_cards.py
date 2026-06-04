from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config
from .rq1_value_drivers import _analysis_frame


def run_rq2(df: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Analyze distribution of expensive cards by set release year.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    priced = _analysis_frame(df)
    threshold = config.EXPENSIVE_CARD_THRESHOLD
    summary: Dict[str, Any] = {
        "expensive_threshold": threshold,
        "priced_cards_analyzed": len(priced),
    }

    if priced.empty or "set_release_date" not in priced.columns:
        return summary

    priced = priced.copy()
    priced["release_year"] = pd.to_datetime(
        priced["set_release_date"], errors="coerce"
    ).dt.year
    priced = priced[priced["release_year"].notna()]
    if priced.empty:
        return summary

    expensive = priced[priced["market_price"] >= threshold]
    by_year = (
        priced.groupby("release_year")
        .agg(total_cards=("market_price", "count"), expensive_cards=("market_price", lambda s: (s >= threshold).sum()))
        .reset_index()
    )
    by_year["expensive_pct"] = (
        100 * by_year["expensive_cards"] / by_year["total_cards"]
    ).round(2)

    plt.figure(figsize=(12, 6))
    plt.bar(by_year["release_year"].astype(int), by_year["expensive_cards"])
    plt.xlabel("Set release year")
    plt.ylabel(f"Cards with market_price >= ${threshold}")
    plt.title("RQ2: Expensive cards by set release year")
    plt.tight_layout()
    plt.savefig(output_dir / "rq2_expensive_by_year.png", dpi=120)
    plt.close()

    recent_cutoff = int(by_year["release_year"].max()) - 5
    recent = by_year[by_year["release_year"] >= recent_cutoff]
    older = by_year[by_year["release_year"] < recent_cutoff]
    summary["expensive_cards_total"] = int(len(expensive))
    summary["expensive_cards_pct"] = round(100 * len(expensive) / len(priced), 2)
    summary["recent_years_expensive_pct_avg"] = round(
        float(recent["expensive_pct"].mean()), 2
    ) if not recent.empty else None
    summary["older_years_expensive_pct_avg"] = round(
        float(older["expensive_pct"].mean()), 2
    ) if not older.empty else None
    summary["by_release_year"] = by_year.to_dict(orient="records")
    summary["methodology_note"] = (
        "Cross-sectional: compares sets from different release years at the same market snapshot."
    )
    return summary
