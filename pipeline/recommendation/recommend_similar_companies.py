import sqlite3
import json
import logging
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Tuple, Optional
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

INDEX_PATH = (
    BASE_DIR
    / "pipeline"
    / "indexing"
    / "faiss_index.bin"
)

ID_MAP_PATH = (
    BASE_DIR
    / "pipeline"
    / "indexing"
    / "id_map.json"
)

# ==============================
# Load Model & Index
# ==============================

logger.info("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

logger.info(f"Model loaded on {device}")

logger.info("Loading FAISS index...")

index = faiss.read_index(str(INDEX_PATH))

with open(ID_MAP_PATH, "r") as f:
    id_map = json.load(f)

logger.info(f"Index loaded with {index.ntotal} vectors")

# ==============================
# Database Helpers
# ==============================

def get_company(
    company_id: Optional[str] = None,
    name: Optional[str] = None
):

    if not company_id and not name:
        return None

    with get_connection() as conn:

        if company_id:

            cursor = conn.execute(
                """
                SELECT id,
                       name,
                       industries,
                       batch,
                       location,
                       website_summary
                FROM yc_companies
                WHERE id = ?
                """,
                (company_id,)
            )

        else:

            cursor = conn.execute(
                """
                SELECT id,
                       name,
                       industries,
                       batch,
                       location,
                       website_summary
                FROM yc_companies
                WHERE LOWER(name) = LOWER(?)
                """,
                (name,)
            )

        row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": str(row[0]),
        "name": row[1],
        "industries": row[2],
        "batch": row[3],
        "location": row[4],
        "summary": row[5],
    }


def get_company_text(company):

    parts = [
        company.get("name", ""),
        company.get("industries", ""),
        company.get("summary", ""),
    ]

    return " ".join(parts).strip()


# ==============================
# Recommendation Engine
# ==============================

def recommend_similar_companies(
    company_id: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 10
) -> List[Tuple[float, dict]]:

    company = get_company(
        company_id=company_id,
        name=name
    )

    if not company:

        logger.warning(
            "Company not found"
        )

        return []

    logger.info(
        f"Generating recommendations for: {company['name']}"
    )

    company_text = get_company_text(company)

    embedding = model.encode(
        company_text,
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(
        embedding.reshape(1, -1)
    )

    scores, indices = index.search(
        embedding.reshape(1, -1),
        limit + 1
    )

    similar_ids = []

    for idx in indices[0]:

        if idx >= len(id_map):
            continue

        cid = str(id_map[idx])

        if cid == company["id"]:
            continue

        similar_ids.append(cid)

    similar_ids = similar_ids[:limit]

    if not similar_ids:
        return []

    placeholders = ",".join(
        ["?"] * len(similar_ids)
    )

    query = f"""
        SELECT id,
               name,
               industries,
               batch,
               location,
               website_summary
        FROM yc_companies
        WHERE id IN ({placeholders})
    """

    with get_connection() as conn:

        cursor = conn.execute(
            query,
            similar_ids
        )

        rows = cursor.fetchall()

    company_lookup = {
        str(row[0]): {
            "id": str(row[0]),
            "name": row[1],
            "industries": row[2],
            "batch": row[3],
            "location": row[4],
            "summary": row[5],
        }
        for row in rows
    }

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx >= len(id_map):
            continue

        cid = str(id_map[idx])

        if cid not in company_lookup:
            continue

        results.append(
            (
                float(score),
                company_lookup[cid]
            )
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:limit]


# ==============================
# CLI
# ==============================

if __name__ == "__main__":

    print(
        "\n--- Similar Company Recommendation ---\n"
    )

    choice = input(
        "Search by (1) ID or (2) Name: "
    ).strip()

    if choice == "1":

        company_id = input(
            "Enter company ID: "
        ).strip()

        results = recommend_similar_companies(
            company_id=company_id,
            limit=5
        )

    else:

        name = input(
            "Enter company name: "
        ).strip()

        results = recommend_similar_companies(
            name=name,
            limit=5
        )

    print("\nTop Similar Companies:\n")

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
            f"Similarity: {round(score, 4)}"
        )

        print(
            company["summary"]
        )

        print("-" * 60)
