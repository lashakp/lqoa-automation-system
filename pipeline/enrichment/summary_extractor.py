# pipeline/enrichment/summary_extractor.py

import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3),
       wait=wait_exponential(min=2, max=15))
async def fetch_html(session, url):
    async with session.get(url, timeout=12) as resp:
        resp.raise_for_status()
        return await resp.text()


async def extract_summary(session, url):
    if pd.isna(url):
        return "N/A"

    try:
        html = await fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"][:500]

        return soup.title.string.strip() if soup.title else "No Summary"

    except Exception:
        return "Error"


async def enrich_summaries(df):
    async with aiohttp.ClientSession(
        headers={'User-Agent': 'LQOA-Bot/1.0 (Educational)'}
    ) as session:

        tasks = [extract_summary(session, w) for w in df["website"]]
        summaries = await asyncio.gather(*tasks)

        df["website_summary"] = summaries

    return df
