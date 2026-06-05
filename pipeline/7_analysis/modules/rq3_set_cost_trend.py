from pathlib import Path
from typing import Any, Dict

import pandas as pd

import config
from config import new_figure, plt, rotate_xticks, save_chart


def chart_set_cost_by_year(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Line chart of average set completion cost vs set release year.'''
    set_stats = (
        priced.groupby(["set_id", "set_name", "set_release_date"], dropna=False)
        .agg(
            completion_cost=("market_price", "sum"),
            avg_card_price=("market_price", "mean"),
            priced_cards=("market_price", "count"),
        )
        .reset_index()
    )
    set_stats["release_year"] = pd.to_datetime(set_stats["set_release_date"]).dt.year
    set_stats = set_stats[set_stats["release_year"].notna()]

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

    new_figure(wide=True)
    plt.plot(
        by_year["release_year"],
        by_year["avg_set_completion_cost"],
        color=config.CHART_LINE_COLOR,
        marker=config.CHART_LINE_MARKER,
    )
    plt.xlabel("Set release year")
    plt.ylabel("Average set completion cost ($)")
    rotate_xticks()
    save_chart(
        output_dir / "rq3_set_cost_by_year.png",
        "RQ3: Average cost to complete a set vs release year",
    )

    summary: Dict[str, Any] = {
        "sets_analyzed": int(len(set_stats)),
        "by_release_year": by_year.round(2).to_dict(orient="records"),
    }
    if len(by_year) >= 2:
        first_half = by_year.iloc[: len(by_year) // 2]["avg_set_completion_cost"].mean()
        second_half = by_year.iloc[len(by_year) // 2 :]["avg_set_completion_cost"].mean()
        summary["avg_completion_cost_first_half_years"] = round(float(first_half), 2)
        summary["avg_completion_cost_second_half_years"] = round(float(second_half), 2)
    return summary


def run_rq3(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Run all RQ3 charts and merge their summary metrics.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {"sets_analyzed": 0}

    if priced.empty:
        return summary

    summary.update(chart_set_cost_by_year(priced, output_dir))
    summary["methodology_note"] = (
        "Cross-sectional proxy: sum of current card prices per set, grouped by release year. "
        "Not CPI-adjusted; excludes cards without market_price from set totals."
    )
    return summary
