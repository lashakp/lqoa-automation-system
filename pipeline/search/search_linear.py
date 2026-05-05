import sqlite3
import json
import logging
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch
from pipeline.api.dependencies.database import get_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# Paths
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_PATH = (
    BASE_DIR
    / "pipeline"
    / "ingestion"
    / "data"
    / "yc_database.db"
)

# ==============================
# Model
# ==============================

MODEL_NAME = "all-MiniLM-L6-v2"

logger.info("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

logger.info(f"Model loaded on {device}")

# ==============================
# Math
# ==============================

def cosine_similarity(a, b):
    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

# ==============================
# Load Companies With Filters
# ==============================

def load_companies(
    industry=None,
    batch=None,
    location=None
):

    conn = get_connection()

    cursor = conn.cursor()

    query = """
        SELECT
            id,
            name,
            industries,
            batch,
            location,
            website_summary,
            embedding
        FROM yc_companies
        WHERE embedding IS NOT NULL
    """

    params = []

    if industry:
        query += " AND industries LIKE ?"
        params.append(f"%{industry}%")

    if batch:
        query += " AND batch = ?"
        params.append(batch)

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")

    cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    companies = []

    for row in rows:

        companies.append(
            {
                "id": row[0],
                "name": row[1],
                "industries": row[2],
                "batch": row[3],
                "location": row[4],
                "summary": row[5],
                "embedding": np.array(
                    json.loads(row[6])
                ),
            }
        )

    logger.info(
        f"Loaded {len(companies)} companies"
    )

    return companies

# ==============================
# Search
# ==============================

def semantic_search(
    query,
    industry=None,
    batch=None,
    location=None,
    top_k=10
):

    companies = load_companies(
        industry,
        batch,
        location
    )

    if not companies:

        print(
            "\nNo companies matched your filters."
        )

        return []

    logger.info(
        f"Searching for: {query}"
    )

    query_embedding = model.encode(
        query,
        convert_to_numpy=True
    )

    scores = []

    for company in companies:

        score = cosine_similarity(
            query_embedding,
            company["embedding"]
        )

        scores.append(
            (
                score,
                company
            )
        )

    scores.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return scores[:top_k]

def clean_summary(text):

    if not text:
        return "No summary available"

    text = text.strip()

    if text.lower() in [
        "fetch error",
        "error",
        "no summary"
    ]:
        return "No summary available"

    return text


# ==============================
# CLI
# ==============================

if __name__ == "__main__":

    print("\n--- Semantic Search ---\n")

    query = input(
        "Enter search query: "
    )

    industry = input(
        "Filter industry (optional): "
    ).strip()

    if industry == "":
        industry = None

    batch = input(
        "Filter batch (optional): "
    ).strip()

    if batch == "":
        batch = None

    location = input(
        "Filter location (optional): "
    ).strip()

    if location == "":
        location = None

    top_k_input = input(
        "Number of results (default 10): "
    ).strip()

    if top_k_input.isdigit():
        top_k = int(top_k_input)
    else:
        top_k = 10

    results = semantic_search(
        query,
        industry,
        batch,
        location,
        top_k
    )

    print("\nTop Matches:\n")

    for score, company in results:

        print(company["name"])

        print(
            f"Industry: {company['industries']}"
        )

        print(
            f"Batch: {company['batch']}"
        )

        print(
            f"Location: {company['location']}"
        )

        print(
            f"Score: {round(score, 4)}"
        )

        print(clean_summary(company["summary"]))


        print("-" * 60)
