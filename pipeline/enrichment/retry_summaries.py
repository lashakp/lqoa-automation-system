import sqlite3
import requests
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging

# ==============================
# Config
# ==============================

DB_PATH = Path(__file__).parent.parent / "ingestion" / "data" / "yc_database.db"
MAX_WORKERS = 20
RETRIES = 3
TIMEOUT = 8

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

# ==============================
# Fetch logic with retry
# ==============================

def fetch_summary(url):
    if not url:
        return None

    for attempt in range(RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

            # Explicit status handling
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")

                meta = soup.find("meta", attrs={"name": "description"})
                if meta and meta.get("content"):
                    return meta["content"][:500]

                p = soup.find("p")
                if p:
                    return p.get_text(strip=True)[:500]

                if soup.title:
                    return soup.title.string.strip()[:500]

                return "No Summary"

            # Retry on server / rate errors
            if r.status_code in [429, 500, 502, 503, 504]:
                time.sleep(2 ** attempt)
                continue

            # Hard failure (403, 404, etc.)
            return "Fetch Error"

        except Exception:
            time.sleep(2 ** attempt)

    return "Fetch Error"


# ==============================
# Main retry logic
# ==============================

def retry_failed_summaries():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, website
        FROM yc_companies
        WHERE website_summary IN ('Fetch Error', 'Error')
          AND website IS NOT NULL
    """)

    rows = cursor.fetchall()
    logger.info(f"Found {len(rows)} failed summaries to retry")

    if not rows:
        logger.info("Nothing to retry.")
        conn.close()
        return

    def process_row(row):
        company_id, website = row
        summary = fetch_summary(website)
        return (summary, company_id)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(process_row, rows))

    # 🔥 Critical safeguard:
    # Only update rows where new summary is NOT None
    filtered_results = [
        (summary, company_id)
        for summary, company_id in results
        if summary is not None
    ]

    cursor.executemany("""
        UPDATE yc_companies
        SET website_summary = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, filtered_results)

    conn.commit()
    conn.close()

    logger.info(f"Updated {len(filtered_results)} summaries successfully.")


if __name__ == "__main__":
    retry_failed_summaries()
