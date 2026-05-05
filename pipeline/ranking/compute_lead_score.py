import sqlite3
import json
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch
from pipeline.api.dependencies.database import get_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_PATH = (
    BASE_DIR
    / "pipeline"
    / "ingestion"
    / "data"
    / "yc_database.db"
)

model = SentenceTransformer("all-MiniLM-L6-v2")

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

def cosine_similarity(a, b):

    return np.dot(a, b) / (
        np.linalg.norm(a)
        * np.linalg.norm(b)
        + 1e-8
    )

def compute_lead_score():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            id,
            industries,
            batch,
            description,
            website_summary,
            embedding
        FROM yc_companies
        """,
        conn
    )

    logger.info(
        f"Computing scores for {len(df)} companies"
    )

    icp_keywords = [
        "saas",
        "b2b",
        "ai",
        "fintech",
        "automation",
        "analytics"
    ]

    pain_keywords = [
        "fraud",
        "compliance",
        "security",
        "risk",
        "detection"
    ]

    df["has_icp"] = df["industries"].fillna("").str.lower().apply(
        lambda x: any(
            k in x
            for k in icp_keywords
        )
    ).astype(int)

    df["is_recent"] = df["batch"].str.contains(
        "202[4-9]",
        na=False
    ).astype(int)

    df["text"] = (
        df["description"].fillna("")
        + " "
        + df["website_summary"].fillna("")
    ).str.lower()

    df["pain_density"] = df["text"].apply(
        lambda t:
        sum(
            1 for kw in pain_keywords
            if kw in t
        )
        / max(1, len(t.split()))
    )

    reference_query = (
        "AI fraud detection fintech"
    )

    ref_embedding = model.encode(
        reference_query
    )

    def semantic_score(emb):

        if not emb:
            return 0.0

        try:

            vec = np.array(
                json.loads(emb)
            )

            return cosine_similarity(
                ref_embedding,
                vec
            )

        except:

            return 0.0

    df["semantic_score"] = df["embedding"].apply(
        semantic_score
    )

    df["lead_score"] = (

        df["has_icp"] * 0.30

        + df["is_recent"] * 0.25

        + df["pain_density"] * 0.20

        + df["semantic_score"] * 0.25

    )

    cursor = conn.cursor()

    # Check if column exists
    cursor.execute(
        "PRAGMA table_info(yc_companies)"
    )

    columns = [
        col[1]
        for col in cursor.fetchall()
    ]

    if "lead_score" not in columns:

        cursor.execute(
            """
            ALTER TABLE yc_companies
            ADD COLUMN lead_score REAL
            """
        )

        conn.commit()

        logger.info(
            "lead_score column created"
        )

    else:

        logger.info(
            "lead_score column already exists"
        )

    # Update all lead scores
    for _, row in df.iterrows():

        cursor.execute(
            """
            UPDATE yc_companies
            SET lead_score = ?
            WHERE id = ?
            """,
            (
                float(row["lead_score"]),
                row["id"]
            )
        )

    conn.commit()

    conn.close()

    logger.info(
        "Lead scores saved to database"
    )

if __name__ == "__main__":

    compute_lead_score()
