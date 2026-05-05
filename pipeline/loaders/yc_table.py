import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "ingestion" / "data" / "yc_database.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.executescript("""
DROP TABLE IF EXISTS yc_companies;

CREATE TABLE yc_companies (
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
);

CREATE INDEX idx_batch       ON yc_companies(batch);
CREATE INDEX idx_industries  ON yc_companies(industries);
CREATE INDEX idx_name        ON yc_companies(name);
""")

conn.commit()
conn.close()

print("Table and indexes created successfully!")
