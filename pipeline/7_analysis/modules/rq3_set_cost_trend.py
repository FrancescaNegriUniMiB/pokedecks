from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .rq1_value_drivers import _analysis_frame


def run_rq3(df: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Analyze set completion cost vs set release year (cross-sectional).'''
    output_dir.mkdir(parents=True, exist_ok=True)
    priced = _analysis_frame(df)
    summary: Dict[str, Any] = {"sets_analyzed": 0}

    if priced.empty or "set_id" not in priced.columns:
        return summary

    set_stats = (
        priced.groupby(["set_id", "set_name", "set_release_date"], dropna=False)
        .agg(
            completion_cost=("market_price", "sum"),
            avg_card_price=("market_price", "mean"),
            priced_cards=("market_price", "count"),
        )
        .reset_index()
    )
    set_stats["release_year"] = pd.to_datetime(
        set_stats["set_release_date"], errors="coerce"
    ).dt.year
    set_stats = set_stats[set_stats["release_year"].notna()]
    if set_stats.empty:
        return summary

    by_year = (
        set_stats.groupby("release_year")
        .agg(
            avg_set_completion_cost=("completion_cost", "mean"),
            median_set_completion_cost=("completion_cost", "median"),
            set_count=("set_id", "count"),
        )
        .reset_index()
        .sort_values("release_year")
    )

    plt.figure(figsize=(12, 6))
    plt.plot(
        by_year["release_year"],
        by_year["avg_set_completion_cost"],
        marker="o",
    )
    plt.xlabel("Set release year")
    plt.ylabel("Average set completion cost ($)")
    plt.title("RQ3: Average cost to complete a set vs release year")
    plt.tight_layout()
    plt.savefig(output_dir / "rq3_set_cost_by_year.png", dpi=120)
    plt.close()

    summary["sets_analyzed"] = int(len(set_stats))
    summary["by_release_year"] = by_year.round(2).to_dict(orient="records")
    if len(by_year) >= 2:
        first_half = by_year.iloc[: len(by_year) // 2]["avg_set_completion_cost"].mean()
        second_half = by_year.iloc[len(by_year) // 2 :]["avg_set_completion_cost"].mean()
        summary["avg_completion_cost_first_half_years"] = round(float(first_half), 2)
        summary["avg_completion_cost_second_half_years"] = round(float(second_half), 2)
    summary["methodology_note"] = (
        "Cross-sectional proxy: sum of current card prices per set, grouped by release year. "
        "Not CPI-adjusted; excludes cards without market_price from set totals."
    )
    return summary
