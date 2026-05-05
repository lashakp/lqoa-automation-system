import sqlite3
import json
import logging
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch

# ==============================
# Logging
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

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

logger.info(
    "Loading embedding model "
    "(first run may take 1–2 min)..."
)

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)

device = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

model = model.to(device)

logger.info(f"Model loaded on {device}")

# ==============================
# Helper
# ==============================

def safe_text(row):

    name = str(row.get("name") or "")

    industries = str(
        row.get("industries") or ""
    )

    description = str(
        row.get("description") or ""
    )

    summary = (
        str(
            row.get("website_summary")
            or ""
        )
        .replace("Fetch Error", "")
        .replace("Error", "")
    )

    text = " ".join(
        filter(
            None,
            [
                name,
                industries,
                description,
                summary,
            ],
        )
    )

    return (
        text.strip()
        or "No description available"
    )

# ==============================
# Main
# ==============================

def generate_embeddings_local(
    batch_size=64
):

    conn = sqlite3.connect(DB_PATH)

    logger.info(
        "Loading companies "
        "without embeddings..."
    )

    df = pd.read_sql_query(
        """
        SELECT
            id,
            name,
            batch,
            description,
            website_summary,
            industries
        FROM yc_companies
        WHERE embedding IS NULL
           OR embedding = ''
        """,
        conn
    )

    if df.empty:

        logger.info(
            "All companies already embedded"
        )

        conn.close()

        return

    total = len(df)

    logger.info(
        f"Embedding {total} companies "
        f"(batch size {batch_size})..."
    )

    cursor = conn.cursor()

    for start in range(
        0,
        total,
        batch_size
    ):

        batch = df.iloc[
            start:
            start + batch_size
        ]

        texts = []

        for _, row in batch.iterrows():

            text = safe_text(row)

            texts.append(text)

        try:

            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            updates = []

            for db_id, emb in zip(
                batch["id"],
                embeddings
            ):

                updates.append(
                    (
                        json.dumps(
                            emb.tolist()
                        ),
                        db_id,
                    )
                )

            cursor.executemany(
                """
                UPDATE yc_companies
                SET embedding = ?
                WHERE id = ?
                """,
                updates,
            )

            conn.commit()

            logger.info(
                f"Processed "
                f"{start + len(batch)} "
                f"/ {total}"
            )

        except Exception as e:

            logger.error(
                f"Batch starting at "
                f"{start} failed: {e}"
            )

    conn.close()

    logger.info(
        "Local embeddings complete!"
    )

# ==============================

if __name__ == "__main__":

    generate_embeddings_local()
