from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import config


def run_rq1(priced: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Analyze price drivers: rarity, age, pokemon, illustrator.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {"priced_cards_analyzed": len(priced)}

    if priced.empty:
        return summary

    top_rarities = priced["rarity"].value_counts().head(12).index.tolist()
    rarity_df = priced[priced["rarity"].isin(top_rarities)]
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=rarity_df, x="rarity", y="market_price")
    plt.xticks(rotation=45, ha="right")
    plt.title("RQ1: Market price by rarity")
    plt.tight_layout()
    plt.savefig(output_dir / "rq1_rarity_boxplot.png", dpi=120)
    plt.close()
    summary["rarity_median_prices"] = (
        priced.groupby("rarity")["market_price"].median().sort_values(ascending=False)
        .head(10)
        .round(2)
        .to_dict()
    )

    pokemon = priced[priced["dex_id"].notna()]
    top_pokemon = (
        pokemon.groupby("dex_id")["market_price"]
        .agg(["mean", "count"])
        .query("count >= 5")
        .sort_values("mean", ascending=False)
        .head(20)
    )
    plt.figure(figsize=(10, 6))
    top_pokemon["mean"].plot(kind="bar")
    plt.title("RQ1: Top Pokemon by average market price (dex_id, min 5 cards)")
    plt.ylabel("Average market price ($)")
    plt.tight_layout()
    plt.savefig(output_dir / "rq1_top_pokemon.png", dpi=120)
    plt.close()
    summary["top_pokemon_by_avg_price"] = {
        str(k): {"avg_price": round(v["mean"], 2), "count": int(v["count"])}
        for k, v in top_pokemon.iterrows()
    }

    top_ill = (
        priced.groupby("illustrator")["market_price"]
        .agg(["mean", "count"])
        .query("count >= 5")
        .sort_values("mean", ascending=False)
        .head(15)
    )
    plt.figure(figsize=(10, 6))
    top_ill["mean"].plot(kind="bar")
    plt.title("RQ1: Top illustrators by average market price (min 5 cards)")
    plt.ylabel("Average market price ($)")
    plt.tight_layout()
    plt.savefig(output_dir / "rq1_top_illustrators.png", dpi=120)
    plt.close()
    summary["top_illustrators_by_avg_price"] = {
        k: {"avg_price": round(v["mean"], 2), "count": int(v["count"])}
        for k, v in top_ill.iterrows()
    }

    snapshot = pd.to_datetime(priced["snapshot_date"])
    release = pd.to_datetime(priced["set_release_date"])
    age = (snapshot - release).dt.days / 365.25
    age_valid = priced[age.notna()].copy()
    age_valid["card_age_years"] = age[age.notna()]
    plt.figure(figsize=(10, 6))
    plt.scatter(age_valid["card_age_years"], age_valid["market_price"], alpha=0.2, s=8)
    plt.xlabel("Card age (years since set release)")
    plt.ylabel("Market price ($)")
    plt.title("RQ1: Card age vs market price")
    plt.tight_layout()
    plt.savefig(output_dir / "rq1_age_scatter.png", dpi=120)
    plt.close()
    corr = age_valid["card_age_years"].corr(age_valid["market_price"])
    summary["age_price_correlation"] = round(float(corr), 4) if pd.notna(corr) else None

    summary["methodology_note"] = (
        "Cross-sectional analysis at snapshot date; excludes trainer-kit prefixes "
        f"{list(config.ANALYSIS_EXCLUDED_SET_PREFIXES)} and sets flagged by quality suspicious_sets rule."
    )
    return summary
