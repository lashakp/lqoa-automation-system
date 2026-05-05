# pipeline/enrichment/location_enrichment.py

import pandas as pd


def guess_location(batch: str) -> str | None:
    if "W2026" in str(batch):
        return "San Francisco, CA, USA"
    return None


def enrich_locations(df: pd.DataFrame) -> pd.DataFrame:
    missing = df["location"].isna()

    for idx in df[missing].index:
        guessed = guess_location(df.loc[idx, "batch"])
        if guessed:
            df.at[idx, "location"] = guessed

    return df
