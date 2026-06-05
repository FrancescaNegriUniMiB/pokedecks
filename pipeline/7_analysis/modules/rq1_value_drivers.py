from pathlib import Path
from typing import Any, Dict

import pandas as pd
import seaborn as sns

import config
from config import new_figure, plt, rotate_xticks, save_chart


def chart_rarity(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Boxplot of market_price by rarity (top 12 rarities by card count).'''
    top_rarities = priced["rarity"].value_counts().head(12).index.tolist()
    rarity_df = priced[priced["rarity"].isin(top_rarities)]
    new_figure(wide=True)
    sns.boxplot(data=rarity_df, x="rarity", y="market_price")
    rotate_xticks()
    save_chart(output_dir / "rq1_rarity_boxplot.png", "RQ1: Market price by rarity")
    return {
        "rarity_median_prices": (
            priced.groupby("rarity")["market_price"].median().sort_values(ascending=False)
            .head(10)
            .round(2)
            .to_dict()
        ),
    }


def chart_pokemon(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Bar chart of top Pokemon by average market_price (dex_id, min 5 cards).'''
    pokemon = priced[priced["dex_id"].notna()]
    top_pokemon = (
        pokemon.groupby("dex_id")["market_price"]
        .agg(["mean", "count"])
        .query("count >= 5")
        .sort_values("mean", ascending=False)
        .head(20)
    )
    new_figure()
    top_pokemon["mean"].plot(kind="bar", color=config.CHART_BAR_COLOR)
    plt.ylabel("Average market price ($)")
    save_chart(
        output_dir / "rq1_top_pokemon.png",
        "RQ1: Top Pokemon by average market price (dex_id, min 5 cards)",
    )
    return {
        "top_pokemon_by_avg_price": {
            str(k): {"avg_price": round(v["mean"], 2), "count": int(v["count"])}
            for k, v in top_pokemon.iterrows()
        },
    }


def chart_illustrators(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Bar chart of top illustrators by average market_price (min 5 cards).'''
    top_ill = (
        priced.groupby("illustrator")["market_price"]
        .agg(["mean", "count"])
        .query("count >= 5")
        .sort_values("mean", ascending=False)
        .head(15)
    )
    new_figure()
    top_ill["mean"].plot(kind="bar", color=config.CHART_BAR_COLOR)
    plt.ylabel("Average market price ($)")
    save_chart(
        output_dir / "rq1_top_illustrators.png",
        "RQ1: Top illustrators by average market price (min 5 cards)",
    )
    return {
        "top_illustrators_by_avg_price": {
            k: {"avg_price": round(v["mean"], 2), "count": int(v["count"])}
            for k, v in top_ill.iterrows()
        },
    }


def chart_age(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Scatter of card age (years since set release) vs market_price.'''
    snapshot = pd.to_datetime(priced["snapshot_date"])
    release = pd.to_datetime(priced["set_release_date"])
    age = (snapshot - release).dt.days / 365.25
    age_valid = priced[age.notna()].copy()
    age_valid["card_age_years"] = age[age.notna()]
    new_figure()
    plt.scatter(
        age_valid["card_age_years"],
        age_valid["market_price"],
        color=config.CHART_SCATTER_COLOR,
        alpha=config.CHART_SCATTER_ALPHA,
        s=config.CHART_SCATTER_SIZE,
    )
    plt.xlabel("Card age (years since set release)")
    plt.ylabel("Market price ($)")
    save_chart(output_dir / "rq1_age_scatter.png", "RQ1: Card age vs market price")
    corr = age_valid["card_age_years"].corr(age_valid["market_price"])
    return {
        "age_price_correlation": round(float(corr), 4) if pd.notna(corr) else None,
    }


def run_rq1(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Run all RQ1 charts and merge their summary metrics.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {"priced_cards_analyzed": len(priced)}

    if priced.empty:
        return summary

    summary.update(chart_rarity(priced, output_dir))
    summary.update(chart_pokemon(priced, output_dir))
    summary.update(chart_illustrators(priced, output_dir))
    summary.update(chart_age(priced, output_dir))
    summary["methodology_note"] = (
        "Cross-sectional analysis at snapshot date; excludes trainer-kit prefixes "
        f"{list(config.ANALYSIS_EXCLUDED_SET_PREFIXES)} and sets flagged by quality suspicious_sets rule."
    )
    return summary
