import sqlite3
import pandas as pd
import hashlib
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "pipeline" / "ingestion" / "data" / "yc_database.db"
ENRICHED_CSV = BASE_DIR / "pipeline" / "ingestion" / "data" / "enriched" / "sample_enriched.csv"

SNAPSHOT_DATE = datetime.now().strftime("%Y-%m-%d")


def compute_id(name: str, batch: str) -> str:
    return hashlib.sha256(f"{name}|{batch}".encode()).hexdigest()[:32]


def load_to_sqlite():

    if not ENRICHED_CSV.exists():
        logger.error("Enriched CSV not found")
        return

    df = pd.read_csv(ENRICHED_CSV)

    # Deduplicate before insert
    df = df.drop_duplicates(subset=["name", "batch"], keep="first")
    logger.info(f"After pandas dedup: {len(df)} rows")

    # Compute ID and snapshot date
    df["id"] = df.apply(lambda row: compute_id(row["name"], str(row.get("batch", ""))), axis=1)
    df["source_snapshot_date"] = SNAPSHOT_DATE

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure table exists (schema managed separately)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS yc_companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            batch TEXT,
            website TEXT,
            location TEXT,
            industries TEXT,
            description TEXT,
            website_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_snapshot_date DATE NOT NULL,
            UNIQUE(name, batch)
        )
    """)

    upsert_query = """
        INSERT INTO yc_companies (
            id, name, batch, website, location,
            industries, description, website_summary,
            source_snapshot_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name, batch) DO UPDATE SET
            website = excluded.website,
            location = excluded.location,
            industries = excluded.industries,
            description = excluded.description,
            website_summary = excluded.website_summary,
            source_snapshot_date = excluded.source_snapshot_date,
            updated_at = CURRENT_TIMESTAMP
    """

    records = df[
        [
            "id", "name", "batch", "website", "location",
            "industries", "description", "website_summary",
            "source_snapshot_date"
        ]
    ].values.tolist()

    cursor.executemany(upsert_query, records)

    conn.commit()
    conn.close()

    logger.info(f"Upserted {len(records)} companies into SQLite.")


if __name__ == "__main__":
    load_to_sqlite()
