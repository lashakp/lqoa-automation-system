# pipeline/enrichment/website_discovery.py

import asyncio
import aiohttp
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


COMMON_TLDS = [".com", ".io", ".ai", ".co", ".app", ".tech"]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def async_head_check(session, url):
    async with session.head(url, timeout=8, allow_redirects=True) as resp:
        if resp.status < 400:
            return url
        raise ValueError(f"Bad status: {resp.status}")


async def discover_website_async(session, name):
    name_slug = name.lower().replace(" ", "").replace("-", "")
    for tld in COMMON_TLDS:
        url = f"https://{name_slug}{tld}"
        try:
            return await async_head_check(session, url)
        except Exception:
            await asyncio.sleep(0.5)
    return None


async def enrich_websites(df):
    async with aiohttp.ClientSession(
        headers={'User-Agent': 'LQOA-Bot/1.0 (Educational)'}
    ) as session:

        tasks = []
        missing_indices = df[df["website"].isna()].index

        for idx in missing_indices:
            tasks.append(discover_website_async(session, df.loc[idx, "name"]))

        results = await asyncio.gather(*tasks)

        for idx, result in zip(missing_indices, results):
            if result:
                df.at[idx, "website"] = result

    return df
