from pathlib import Path
from typing import Any, Dict

import pandas as pd

import config
from config import new_figure, plt, rotate_xticks, save_chart


def chart_expensive_by_year(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Bar chart of expensive cards (market_price >= threshold) by set release year.'''
    threshold = config.EXPENSIVE_CARD_THRESHOLD
    priced = priced.copy()
    priced["release_year"] = pd.to_datetime(priced["set_release_date"]).dt.year
    priced = priced[priced["release_year"].notna()]

    expensive = priced[priced["market_price"] >= threshold]
    by_year = (
        priced.groupby("release_year")
        .agg(total_cards=("market_price", "count"), expensive_cards=("market_price", lambda s: (s >= threshold).sum()))
        .reset_index()
    )
    by_year["expensive_pct"] = (
        100 * by_year["expensive_cards"] / by_year["total_cards"]
    ).round(2)

    new_figure(wide=True)
    (
        by_year.set_index(by_year["release_year"].astype(int))["expensive_cards"]
        .plot(kind="bar", color=config.CHART_BAR_COLOR)
    )
    plt.xlabel("Set release year")
    plt.ylabel(f"Cards with market_price >= ${threshold}")
    rotate_xticks()
    save_chart(output_dir / "rq2_expensive_by_year.png", "RQ2: Expensive cards by set release year")

    recent_cutoff = int(by_year["release_year"].max()) - 5
    recent = by_year[by_year["release_year"] >= recent_cutoff]
    older = by_year[by_year["release_year"] < recent_cutoff]
    return {
        "expensive_cards_total": int(len(expensive)),
        "expensive_cards_pct": round(100 * len(expensive) / len(priced), 2),
        "recent_years_expensive_pct_avg": (
            round(float(recent["expensive_pct"].mean()), 2) if len(recent) else None
        ),
        "older_years_expensive_pct_avg": (
            round(float(older["expensive_pct"].mean()), 2) if len(older) else None
        ),
        "by_release_year": by_year.to_dict(orient="records"),
    }


def run_rq2(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Run all RQ2 charts and merge their summary metrics.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {
        "expensive_threshold": config.EXPENSIVE_CARD_THRESHOLD,
        "priced_cards_analyzed": len(priced),
    }

    if priced.empty:
        return summary

    summary.update(chart_expensive_by_year(priced, output_dir))
    summary["methodology_note"] = (
        "Cross-sectional: compares sets from different release years at the same market snapshot."
    )
    return summary
