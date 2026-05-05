import sqlite3
import json
import logging
import numpy as np
import faiss
from pathlib import Path

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
# Load Embeddings
# ==============================

def load_embeddings():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, embedding
        FROM yc_companies
        WHERE embedding IS NOT NULL
    """)

    rows = cursor.fetchall()

    conn.close()

    ids = []
    vectors = []

    for company_id, emb_json in rows:

        embedding = json.loads(emb_json)

        ids.append(company_id)

        vectors.append(embedding)

    vectors = np.array(vectors).astype("float32")

    logger.info(f"Loaded {len(vectors)} embeddings")

    return ids, vectors



# ==============================
# Build Index
# ==============================

def build_index():

    ids, vectors = load_embeddings()

    dimension = vectors.shape[1]

    logger.info(f"Vector dimension: {dimension}")

    # L2-normalize vectors for cosine similarity
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(dimension)

    index.add(vectors)

    logger.info(
        f"Index contains {index.ntotal} vectors"
    )

    faiss.write_index(
        index,
        str(INDEX_PATH)
    )

    logger.info(
        f"Index saved to {INDEX_PATH}"
    )

    with open(ID_MAP_PATH, "w") as f:

        json.dump(ids, f)

    logger.info(
        f"ID map saved to {ID_MAP_PATH}"
    )

# ==============================

if __name__ == "__main__":

    build_index()
