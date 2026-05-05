from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = (
    BASE_DIR
    / "ingestion"
    / "data"
    / "yc_database.db"
)

API_VERSION = "v1"

DEFAULT_LIMIT = 10
MAX_LIMIT = 50
