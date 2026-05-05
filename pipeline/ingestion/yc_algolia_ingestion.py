import os
import logging
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
from bs4 import BeautifulSoup


# ==============================
# 1. Directory Setup
# ==============================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ENRICHED_DIR = DATA_DIR / "enriched"
LOG_DIR = BASE_DIR / "logs"

for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR, ENRICHED_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ==============================
# 2. Logging Configuration
# ==============================

log_file = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Scraper started")


# ==============================
# TOGGLE: Use real YC mirror or fallback list
# ==============================
USE_YC_MIRROR = True   # Set to False to use the old 20-company fallback


# ==============================
# New: Load real YC companies from public mirror (reliable replacement for broken Algolia)
# ==============================

def load_yc_mirror():
    url = "https://yc-oss.github.io/api/companies/all.json"
    logger.info(f"Fetching fresh YC companies from mirror: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Normalize to our expected columns
        companies = []
        for item in data:
            companies.append({
                "name": item.get("name"),
                "website": item.get("website"),
                "description": item.get("long_description") or item.get("one_liner"),
                "location": item.get("all_locations"),
                "batch": item.get("batch"),
                "industries": ", ".join(item.get("industries", [])) if item.get("industries") else None
            })
        
        df_mirror = pd.DataFrame(companies)
        logger.info(f"Loaded {len(df_mirror)} companies from YC mirror")
        return df_mirror
    except Exception as e:
        logger.error(f"Failed to load YC mirror: {e}")
        return None


# ==============================
# 3. Load or Create DataFrame
# ==============================

raw_file = RAW_DIR / "sample_raw.csv"

if USE_YC_MIRROR:
    logger.info("Using YC mirror as primary data source...")
    df = load_yc_mirror()
    if df is None or df.empty:
        logger.warning("Mirror failed → falling back to hardcoded 20 companies")
        df = pd.DataFrame(fallback_data)
else:
    if raw_file.exists():
        try:
            df = pd.read_csv(raw_file)
            logger.info(f"Loaded existing raw data from {raw_file} with shape: {df.shape}")
        except Exception as e:
            logger.error(f"Failed to load raw CSV: {e}")
            df = pd.DataFrame(fallback_data)
            logger.info(f"Using fallback data with shape: {df.shape}")
    else:
        df = pd.DataFrame(fallback_data)
        df.to_csv(raw_file, index=False)
        logger.info(f"Created and saved fallback raw data to {raw_file} with shape: {df.shape}")


# Save raw source (whether mirror or fallback)
raw_source_file = RAW_DIR / f"raw_source_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(raw_source_file, index=False)
logger.info(f"Raw source data saved: {raw_source_file}")


# ==============================
# 4. Data Validation
# ==============================

logger.info("Running validation checks...")

missing_values = df.isnull().sum()
duplicates = df.duplicated(subset=['name']).sum()

logger.info(f"Missing values:\n{missing_values}")
logger.info(f"Duplicate names: {duplicates}")


# ==============================
# 5. Basic Processing
# ==============================

df["industries"] = df["industries"].str.lower().fillna("")
df["name"] = df["name"].str.strip()

processed_file = PROCESSED_DIR / "sample_processed.csv"
df.to_csv(processed_file, index=False)
logger.info(f"Processed data saved to {processed_file}")


# ==============================
# 6. Enrichment: Website Discovery for Missing Entries
# ==============================

COMMON_TLDS = [".com", ".io", ".ai", ".co", ".app", ".tech"]

def discover_website(name, batch):
    if pd.isna(name):
        return None
    name_slug = name.lower().replace(" ", "").replace("-", "")
    for tld in COMMON_TLDS:
        potential = f"https://{name_slug}{tld}"
        try:
            r = requests.head(potential, timeout=5, allow_redirects=True)
            if r.status_code < 400:
                logger.info(f"Discovered: {potential}")
                return potential
        except:
            pass
    logger.debug(f"No website discovered for {name}")
    return None

logger.info("Starting website enrichment...")

missing_websites = df["website"].isna().sum()
logger.info(f"Missing websites before enrichment: {missing_websites}")

for idx, row in df[df["website"].isna()].iterrows():
    url = discover_website(row["name"], row["batch"])
    if url:
        df.at[idx, "website"] = url

remaining_missing = df["website"].isna().sum()
logger.info(f"Remaining missing websites after enrichment: {remaining_missing}")


# ==============================
# 7. Location Enrichment
# ==============================

def guess_location(name, batch, description):
    if pd.isna(batch):
        return None
    if "W2026" in str(batch) or "S202" in str(batch):
        return "San Francisco, CA, USA"
    return None

logger.info("Enriching missing locations...")

missing_locations = df["location"].isna().sum()
logger.info(f"Missing locations before: {missing_locations}")

for idx, row in df[df["location"].isna()].iterrows():
    loc = guess_location(row["name"], row["batch"], row.get("description", ""))
    if loc:
        df.at[idx, "location"] = loc

logger.info(f"Remaining missing locations: {df['location'].isna().sum()}")


# ==============================
# 8. Website Summary Extraction
# ==============================

def ethical_scrape_summary(url):
    if pd.isna(url):
        return 'N/A'
    headers = {'User-Agent': 'LQOA-Bot/1.0 (Educational; no-archive)'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return 'Fetch Error'
        soup = BeautifulSoup(r.text, 'html.parser')
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and meta.get('content'):
            return meta['content'][:500]
        p = soup.find('p')
        if p:
            return p.get_text(strip=True)[:500]
        return soup.title.string.strip()[:500] if soup.title else 'No Summary'
    except Exception as e:
        logger.debug(f"Summary error {url}: {e}")
        return 'Error'

logger.info("Extracting website summaries...")
df['website_summary'] = df['website'].apply(ethical_scrape_summary)


# ==============================
# 9. Final Save & Validation
# ==============================

enriched_file = ENRICHED_DIR / "sample_enriched.csv"
df.to_csv(enriched_file, index=False)
logger.info(f"Final enriched data saved to {enriched_file}")

logger.info("Final validation:")
logger.info(f"Missing values:\n{df.isnull().sum()}")
logger.info(f"Shape: {df.shape}")
logger.info(f"Sample rows:\n{df[['name', 'batch', 'website', 'location', 'industries']].head(8).to_string(index=False)}")

logger.info("Scraper finished successfully")