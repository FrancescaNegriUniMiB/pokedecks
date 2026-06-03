from pathlib import Path
from typing import Any, Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import config


def _analysis_frame(df: pd.DataFrame) -> pd.DataFrame:
    priced = df[df["market_price"].notna()].copy()
    if "set_id" in priced.columns:
        priced = priced[~priced["set_id"].astype(str).str.startswith("tk-")]
    return priced


def _card_age_years(df: pd.DataFrame) -> pd.Series:
    snapshot = pd.to_datetime(df["snapshot_date"], errors="coerce")
    release = pd.to_datetime(df["set_release_date"], errors="coerce")
    return (snapshot - release).dt.days / 365.25


def run_rq1(df: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    '''Analyze price drivers: rarity, age, pokemon, illustrator.'''
    output_dir.mkdir(parents=True, exist_ok=True)
    priced = _analysis_frame(df)
    summary: Dict[str, Any] = {"priced_cards_analyzed": len(priced)}

    if priced.empty:
        return summary

    if "rarity" in priced.columns and priced["rarity"].notna().any():
        top_rarities = (
            priced["rarity"].value_counts().head(12).index.tolist()
        )
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

    pokemon = priced[priced["dex_id"].notna()].copy()
    if not pokemon.empty:
        top_pokemon = (
            pokemon.groupby("dex_id")["market_price"]
            .agg(["mean", "count"])
            .query("count >= 5")
            .sort_values("mean", ascending=False)
            .head(20)
        )
        if not top_pokemon.empty:
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

    if "illustrator" in priced.columns and priced["illustrator"].notna().any():
        top_ill = (
            priced.groupby("illustrator")["market_price"]
            .agg(["mean", "count"])
            .query("count >= 5")
            .sort_values("mean", ascending=False)
            .head(15)
        )
        if not top_ill.empty:
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

    age = _card_age_years(priced)
    age_valid = priced[age.notna()].copy()
    age_valid["card_age_years"] = age[age.notna()]
    if not age_valid.empty:
        plt.figure(figsize=(10, 6))
        plt.scatter(age_valid["card_age_years"], age_valid["market_price"], alpha=0.2, s=8)
        plt.xlabel("Card age (years since set release)")
        plt.ylabel("Market price ($)")
        plt.title("RQ1: Card age vs market price")
        plt.tight_layout()
        plt.savefig(output_dir / "rq1_age_scatter.png", dpi=120)
        plt.close()
        corr = age_valid["card_age_years"].corr(age_valid["market_price"])
        summary["age_price_correlation"] = round(float(corr), 4) if corr == corr else None

    summary["methodology_note"] = (
        "Cross-sectional analysis at snapshot date; trainer kit sets (tk-*) excluded."
    )
    return summary
