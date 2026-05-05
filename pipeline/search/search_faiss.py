import sqlite3
import json
import logging
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch
from typing import Optional, Tuple, List
from pipeline.api.dependencies.database import get_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "pipeline" / "ingestion" / "data" / "yc_database.db"
INDEX_PATH = BASE_DIR / "pipeline" / "indexing" / "faiss_index.bin"
ID_MAP_PATH = BASE_DIR / "pipeline" / "indexing" / "id_map.json"

model = SentenceTransformer("all-MiniLM-L6-v2")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

index = faiss.read_index(str(INDEX_PATH))

with open(ID_MAP_PATH, "r") as f:
    id_map = json.load(f)

logger.info(f"Index loaded with {index.ntotal} vectors")

def clean_summary(summary):
    if not summary or summary in ["Fetch Error", "Error", "None", "null", ""]:
        return "No summary available"
    return summary.strip()

def clean_location(location):
    if not location:
        return "Location not specified"
    return location

def fetch_companies_by_ids(
    ids: list,
    industry: Optional[str] = None,
    batch: Optional[str] = None,
    location: Optional[str] = None
) -> Tuple[list, Optional[str]]:

    if not ids:
        return [], None

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(ids))
    params = list(ids)

    query = f"""
        SELECT id, name, industries, batch, location, 
               website_summary, lead_score
        FROM yc_companies
        WHERE id IN ({placeholders})
    """

    if industry:
        query += " AND LOWER(industries) LIKE ?"
        params.append(f"%{industry.lower()}%")

    if batch:
        query += " AND batch = ?"
        params.append(batch)

    if location:
        query += " AND LOWER(location) LIKE ?"
        params.append(f"%{location.lower()}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()

    warning = None

    if len(rows) == 0 and any([industry, batch, location]):
        warning = "No exact matches found for all your filters. Showing the best semantic matches instead."

        # Fallback: remove filters
        query = f"""
            SELECT id, name, industries, batch, location, 
                   website_summary, lead_score
            FROM yc_companies
            WHERE id IN ({placeholders})
        """
        cursor.execute(query, list(ids))
        rows = cursor.fetchall()

    companies = []
    for row in rows:
        companies.append({
            "id": str(row[0]),
            "name": row[1],
            "industries": row[2] or "",
            "batch": row[3] or "",
            "location": clean_location(row[4]),
            "summary": clean_summary(row[5]),
            "lead_score": float(row[6]) if row[6] is not None else 0.0,
        })

    conn.close()
    return companies, warning


def semantic_search(
    query: str,
    industry: Optional[str] = None,
    batch: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    similarity_weight: float = 0.75,
    ranking_weight: float = 0.25,
    mode: str = "demo"
) -> Tuple[List, Optional[str], int]:

    logger.info(f"Searching for: {query}")
    logger.info(f"Access mode: {mode}")

    # -----------------------------
    # Demo Mode Restrictions
    # -----------------------------

    if mode == "demo":

        DEMO_MAX_LIMIT = 15
        DEMO_MAX_OFFSET = 10

        if limit > DEMO_MAX_LIMIT:

            logger.info(
                f"Demo mode limit capped from {limit} to {DEMO_MAX_LIMIT}"
            )

            limit = DEMO_MAX_LIMIT

        if offset > DEMO_MAX_OFFSET:

            logger.info(
                f"Demo mode offset capped from {offset} to {DEMO_MAX_OFFSET}"
            )

            offset = DEMO_MAX_OFFSET

    # -----------------------------
    # Embedding
    # -----------------------------

    query_embedding = model.encode(
        query,
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(
        query_embedding.reshape(1, -1)
    )

    # -----------------------------
    # Retrieval Size
    # -----------------------------

    search_k = max(
        (offset + limit) * 5,
        20
    )

    scores, indices = index.search(
        query_embedding.reshape(1, -1),
        search_k
    )

    matched_ids = [

        str(id_map[i])

        for i in indices[0]

        if i < len(id_map)
    ]

    companies, warning = fetch_companies_by_ids(
        matched_ids,
        industry,
        batch,
        location
    )

    company_lookup = {

        c["id"]: c

        for c in companies
    }

    # -----------------------------
    # Ranking
    # -----------------------------

    results = []

    for similarity, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx >= len(id_map):

            continue

        company_id = str(
            id_map[idx]
        )

        if company_id not in company_lookup:

            continue

        company = company_lookup[
            company_id
        ]

        lead_score = max(
            0.0,
            min(
                float(
                    company.get(
                        "lead_score",
                        0.0
                    )
                ),
                1.0
            )
        )

        final_score = (

            similarity_weight
            * float(similarity)

            +

            ranking_weight
            * lead_score
        )

        company["similarity_score"] = float(
            similarity
        )

        company["final_score"] = float(
            final_score
        )

        results.append(
            (
                final_score,
                company
            )
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # -----------------------------
    # Pagination
    # -----------------------------

    paginated = results[
        offset : offset + limit
    ]

    return (
        paginated,
        warning,
        len(results)
    )
