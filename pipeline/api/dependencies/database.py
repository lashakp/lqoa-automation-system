import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_PATH = (
    BASE_DIR
    / "ingestion"
    / "data"
    / "yc_database.db"
)


def get_connection():

    return sqlite3.connect(str(DB_PATH))
