from typing import Dict, List

import pandas as pd

import config


def suspicious_sets(df: pd.DataFrame) -> pd.DataFrame:
    '''Flag sets with uniformly high market_price (likely bad enrichment matches).'''
    priced = df[df["market_price"].notna() & df["set_id"].notna()].copy()
    grouped = (
        priced.groupby(["set_id", "set_name"], dropna=False)["market_price"]
        .agg(["count", "mean", "std"])
        .reset_index()
    )
    grouped["std"] = grouped["std"].fillna(0.0)
    mask = (
        (grouped["mean"] > config.SUSPICIOUS_SET_MEAN_THRESHOLD)
        & (grouped["std"] < config.SUSPICIOUS_SET_STDDEV_THRESHOLD)
    )
    return grouped[mask].sort_values("mean", ascending=False)


def analysis_excluded_set_ids(df: pd.DataFrame) -> Dict[str, List[str]]:
    '''Set IDs excluded from RQ analysis (trainer-kit prefixes + suspicious sets).'''
    set_ids = df["set_id"].astype(str)
    tk_mask = False
    for prefix in config.ANALYSIS_EXCLUDED_SET_PREFIXES:
        tk_mask = tk_mask | set_ids.str.startswith(prefix)
    trainer_kit = sorted(set_ids[tk_mask].unique().tolist())
    suspicious = sorted(suspicious_sets(df)["set_id"].astype(str).unique().tolist())
    return {"trainer_kit": trainer_kit, "suspicious": suspicious}


def analysis_frame(df: pd.DataFrame) -> pd.DataFrame:
    '''Priced cards only, excluding trainer-kit prefixes and suspicious sets.'''
    priced = df[df["market_price"].notna()].copy()
    excluded = analysis_excluded_set_ids(df)
    drop_ids = set(excluded["trainer_kit"]) | set(excluded["suspicious"])
    return priced[~priced["set_id"].astype(str).isin(drop_ids)]
