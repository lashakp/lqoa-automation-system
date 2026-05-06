import json
import logging
import numpy as np
import faiss
from pathlib import Path
from typing import Optional, Tuple, List

from pipeline.api.dependencies.database import get_connection

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = BASE_DIR / "pipeline" / "indexing" / "faiss_index.bin"
ID_MAP_PATH = BASE_DIR / "pipeline" / "indexing" / "id_map.json"

# =========================
# LAZY LOAD GLOBALS
# =========================

_model = None
_index = None
_id_map = None


def get_model():
    global _model

    if _model is None:
        logger.info("Loading embedding model...")
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")

    return _model


def get_index():
    global _index

    if _index is None:
        logger.info("Loading FAISS index...")
        _index = faiss.read_index(str(INDEX_PATH))

    return _index


def get_id_map():
    global _id_map

    if _id_map is None:
        logger.info("Loading ID map...")
        with open(ID_MAP_PATH, "r") as f:
            _id_map = json.load(f)

    return _id_map


# =========================
# HELPERS
# =========================

def clean_summary(summary):
    if not summary or summary in ["Fetch Error", "Error", "None", "null", ""]:
        return "No summary available"
    return summary.strip()


def clean_location(location):
    if not location:
        return "Location not specified"
    return location


# =========================
# DB FETCH
# =========================

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
        warning = "No exact matches found for all filters. Showing fallback results."

        cursor.execute(
            f"""
            SELECT id, name, industries, batch, location,
                   website_summary, lead_score
            FROM yc_companies
            WHERE id IN ({placeholders})
            """,
            list(ids)
        )
        rows = cursor.fetchall()

    conn.close()

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

    return companies, warning


# =========================
# MAIN SEARCH
# =========================

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
    logger.info(f"Mode: {mode}")

    # -----------------------------
    # Demo Mode Limits
    # -----------------------------
    if mode == "demo":
        limit = min(limit, 15)
        offset = min(offset, 10)

    # -----------------------------
    # LOAD RESOURCES (lazy)
    # -----------------------------
    model = get_model()
    index = get_index()
    id_map = get_id_map()

    # -----------------------------
    # EMBEDDING
    # -----------------------------
    query_embedding = model.encode(
        query,
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(query_embedding.reshape(1, -1))

    # -----------------------------
    # SEARCH
    # -----------------------------
    search_k = max((offset + limit) * 5, 20)

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

    company_lookup = {c["id"]: c for c in companies}

    # -----------------------------
    # RANKING
    # -----------------------------
    results = []

    for similarity, idx in zip(scores[0], indices[0]):

        if idx >= len(id_map):
            continue

        company_id = str(id_map[idx])

        if company_id not in company_lookup:
            continue

        company = company_lookup[company_id]

        lead_score = max(
            0.0,
            min(float(company.get("lead_score", 0.0)), 1.0)
        )

        final_score = (
            similarity_weight * float(similarity)
            + ranking_weight * lead_score
        )

        company["similarity_score"] = float(similarity)
        company["final_score"] = float(final_score)

        results.append((final_score, company))

    results.sort(key=lambda x: x[0], reverse=True)

    paginated = results[offset: offset + limit]

    return paginated, warning, len(results)