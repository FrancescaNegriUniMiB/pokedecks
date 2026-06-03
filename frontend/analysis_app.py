import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

import config
from frontend.ui import render_exit_button

ANALYSIS_DIR = Path(config.DEFAULT_ANALYSIS_DIR)
QUALITY_DIR = Path(config.DEFAULT_QUALITY_DIR)

CHART_FILES = [
    ("RQ1: Price by rarity", "rq1_rarity_boxplot.png"),
    ("RQ1: Top Pokemon", "rq1_top_pokemon.png"),
    ("RQ1: Top illustrators", "rq1_top_illustrators.png"),
    ("RQ1: Age vs price", "rq1_age_scatter.png"),
    ("RQ2: Expensive cards by year", "rq2_expensive_by_year.png"),
    ("RQ3: Set cost by release year", "rq3_set_cost_by_year.png"),
]

POKEDEX_NAMES = {
    25: "Pikachu",
    6: "Charizard",
    150: "Mewtwo",
    151: "Mew",
    249: "Lugia",
    250: "Ho-Oh",
    384: "Rayquaza",
    445: "Garchomp",
    94: "Gengar",
    130: "Gyarados",
}


def list_snapshot_dates() -> list[str]:
    if not ANALYSIS_DIR.exists():
        return []
    return sorted(
        [p.name for p in ANALYSIS_DIR.iterdir() if p.is_dir()],
        reverse=True,
    )


def _corr_label(corr: Optional[float]) -> str:
    if corr is None:
        return "not enough data"
    if abs(corr) < 0.1:
        return "essentially no linear relationship"
    if abs(corr) < 0.3:
        return "weak relationship"
    if abs(corr) < 0.5:
        return "moderate relationship"
    return "strong relationship"


def _pokemon_label(dex_id: str) -> str:
    try:
        num = int(float(dex_id))
    except ValueError:
        return dex_id
    name = POKEDEX_NAMES.get(num)
    return f"#{num} {name}" if name else f"#{num}"


def render_rq1(rq1: Dict[str, Any]) -> None:
    st.markdown("#### RQ1 — What makes a card valuable?")
    corr = rq1.get("age_price_correlation")

    c1, c2, c3 = st.columns(3)
    c1.metric("Cards in analysis", f"{rq1.get('priced_cards_analyzed', 0):,}")
    c2.metric("Age vs price (correlation)", f"{corr:.2f}" if corr is not None else "—")
    c3.metric("Rarity tiers compared", len(rq1.get("rarity_median_prices", {})))

    st.info(
        f"Card **age alone does not explain price**: correlation is **{corr:.2f}** "
        f"({_corr_label(corr)}). **Rarity, Pokémon, and illustrator** matter more than release year."
        if corr is not None
        else "Not enough release-date data to estimate age vs price."
    )

    left, right = st.columns(2)

    with left:
        st.markdown("**Highest median price by rarity**")
        rarity = rq1.get("rarity_median_prices", {})
        if rarity:
            df = pd.DataFrame(
                [{"Rarity": k, "Median price ($)": v} for k, v in rarity.items()]
            )
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.caption("No rarity breakdown available.")

    with right:
        st.markdown("**Top Pokémon by average price** (min. 5 cards)")
        pokemon = rq1.get("top_pokemon_by_avg_price", {})
        if pokemon:
            df = pd.DataFrame(
                [
                    {
                        "Pokémon": _pokemon_label(k),
                        "Avg price ($)": v["avg_price"],
                        "Cards": v["count"],
                    }
                    for k, v in list(pokemon.items())[:8]
                ]
            )
            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Avg price ($)": st.column_config.NumberColumn(format="$%.2f"),
                },
            )
        else:
            st.caption("No Pokémon breakdown available.")

    illustrators = rq1.get("top_illustrators_by_avg_price", {})
    if illustrators:
        st.markdown("**Top illustrators by average price** (min. 5 cards)")
        df = pd.DataFrame(
            [
                {
                    "Illustrator": k,
                    "Avg price ($)": v["avg_price"],
                    "Cards": v["count"],
                }
                for k, v in list(illustrators.items())[:8]
            ]
        )
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Avg price ($)": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

    if rq1.get("methodology_note"):
        st.caption(rq1["methodology_note"])


def render_rq2(rq2: Dict[str, Any]) -> None:
    st.markdown("#### RQ2 — Are expensive cards becoming more common?")
    threshold = rq2.get("expensive_threshold", 50)
    total = rq2.get("expensive_cards_total", 0)
    pct = rq2.get("expensive_cards_pct", 0)
    recent = rq2.get("recent_years_expensive_pct_avg")
    older = rq2.get("older_years_expensive_pct_avg")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price threshold", f"${threshold:.0f}")
    c2.metric("Expensive cards", f"{total:,}")
    c3.metric("Share of catalog", f"{pct:.1f}%")
    c4.metric("Cards analyzed", f"{rq2.get('priced_cards_analyzed', 0):,}")

    if recent is not None and older is not None:
        delta = recent - older
        direction = "more" if delta > 0 else "fewer"
        st.info(
            f"On average, **recent sets (last 5 years)** show **{recent:.1f}%** of cards above "
            f"${threshold:.0f}, vs **{older:.1f}%** in older years — slightly **{direction}** "
            f"expensive cards in recent releases ({delta:+.1f} pp). "
            f"The phenomenon is **not uniform**: some vintage years spike higher than recent ones."
        )

    by_year = rq2.get("by_release_year", [])
    if by_year:
        df = pd.DataFrame(by_year).sort_values("expensive_pct", ascending=False)
        st.markdown("**Peak years** (% of cards above threshold)")
        peak = df.head(5)[["release_year", "expensive_cards", "total_cards", "expensive_pct"]]
        peak = peak.rename(
            columns={
                "release_year": "Year",
                "expensive_cards": f"Cards ≥ ${threshold:.0f}",
                "total_cards": "Total cards",
                "expensive_pct": "Share (%)",
            }
        )
        st.dataframe(
            peak,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Share (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    if rq2.get("methodology_note"):
        st.caption(rq2["methodology_note"])


def render_rq3(rq3: Dict[str, Any]) -> None:
    st.markdown("#### RQ3 — Is the cost to complete a set rising?")
    first = rq3.get("avg_completion_cost_first_half_years")
    second = rq3.get("avg_completion_cost_second_half_years")
    sets_n = rq3.get("sets_analyzed", 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Sets analyzed", sets_n)
    c2.metric("Avg cost — older half of years", f"${first:,.0f}" if first else "—")
    c3.metric("Avg cost — newer half of years", f"${second:,.0f}" if second else "—")

    if first is not None and second is not None:
        delta = second - first
        pct_change = 100 * delta / first if first else 0
        st.info(
            f"Cross-sectional comparison (same price snapshot, different release eras): "
            f"completing a set from **newer years** costs about **${second:,.0f}** on average vs "
            f"**${first:,.0f}** for older eras (**{pct_change:+.0f}%**, not CPI-adjusted). "
            f"This is a **proxy trend**, not a time series of the same set over time."
        )

    by_year = rq3.get("by_release_year", [])
    if by_year:
        df = pd.DataFrame(by_year).sort_values("avg_set_completion_cost", ascending=False)
        st.markdown("**Most expensive eras to complete** (avg sum of card prices per set)")
        top = df.head(5)[
            ["release_year", "avg_set_completion_cost", "median_set_completion_cost", "set_count"]
        ].rename(
            columns={
                "release_year": "Year",
                "avg_set_completion_cost": "Avg set cost ($)",
                "median_set_completion_cost": "Median set cost ($)",
                "set_count": "Sets",
            }
        )
        st.dataframe(
            top,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Avg set cost ($)": st.column_config.NumberColumn(format="$%.0f"),
                "Median set cost ($)": st.column_config.NumberColumn(format="$%.0f"),
            },
        )

    if rq3.get("methodology_note"):
        st.caption(rq3["methodology_note"])


def render_summary(summary: Dict[str, Any]) -> None:
    st.subheader("Summary")
    st.caption(f"Snapshot **{summary.get('snapshot_date', '—')}** — key findings for each research question.")

    if "rq1" in summary:
        render_rq1(summary["rq1"])
    st.divider()
    if "rq2" in summary:
        render_rq2(summary["rq2"])
    st.divider()
    if "rq3" in summary:
        render_rq3(summary["rq3"])

    with st.expander("Technical details (raw JSON)"):
        st.json(summary)


st.set_page_config(page_title="PokeDecks Analysis", layout="wide")
render_exit_button()
st.title("PokeDecks — Analysis Results")
st.caption("Research questions RQ1–RQ3 on the Pokémon TCG market.")

dates = list_snapshot_dates()
if not dates:
    st.warning(
        f"No analysis output found in `{ANALYSIS_DIR}`. "
        "Run `poetry run python scripts/pipeline/analyze.py --date YYYY-MM-DD` first."
    )
    st.stop()

snapshot_date = st.selectbox("Snapshot date", dates)
run_dir = ANALYSIS_DIR / snapshot_date
summary_path = run_dir / "analysis_summary.json"

if summary_path.exists():
    with open(summary_path, encoding="utf-8") as f:
        summary = json.load(f)
    render_summary(summary)
else:
    st.info("No analysis_summary.json for this snapshot.")

st.subheader("Charts")
cols = st.columns(2)
for idx, (title, filename) in enumerate(CHART_FILES):
    path = run_dir / filename
    with cols[idx % 2]:
        st.markdown(f"**{title}**")
        if path.exists():
            st.image(str(path), use_container_width=True)
        else:
            st.caption(f"Missing: {filename}")

quality_summary = QUALITY_DIR / f"summary_{snapshot_date}.json"
if quality_summary.exists():
    with st.expander("Data quality report"):
        with open(quality_summary, encoding="utf-8") as f:
            quality = json.load(f)
        comp = quality.get("after_enrichment") or quality.get("completeness", {})
        q1, q2, q3 = st.columns(3)
        q1.metric("Total cards", comp.get("total_cards", "—"))
        q2.metric("With market price", comp.get("market_price_filled_pct", "—"))
        q3.metric("Suspicious sets", quality.get("suspicious_sets_count", "—"))
        st.caption(f"Full report: `{quality_summary}`")
