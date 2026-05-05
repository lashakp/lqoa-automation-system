# pipeline/main.py

import asyncio
from pathlib import Path
import logging
from utils.logging_config import setup_logging
from ingestion.fallback_csv_loader import load_or_create_fallback
from enrichment.website_discovery import enrich_websites
from enrichment.location_enrichment import enrich_locations
from enrichment.summary_extractor import enrich_summaries


def main():
    base_dir = Path(__file__).resolve().parent.parent

    setup_logging(base_dir)

    df = load_or_create_fallback(base_dir)
    
    logging.info("Starting website enrichment")
    df = asyncio.run(enrich_websites(df))
    
    logging.info("Starting location enrichment")
    df = enrich_locations(df)
    
    logging.info("Starting summary extraction")
    df = asyncio.run(enrich_summaries(df))
    
    logging.info("Pipeline complete")

    df.to_csv(base_dir / "data/enriched/final_output.csv", index=False)


if __name__ == "__main__":
    main()
