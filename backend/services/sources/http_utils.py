import asyncio
import random
import httpx

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
]

REQUEST_DELAY_RANGE = (1.5, 3.5)
MAX_RETRIES = 3


def random_headers(extra: dict | None = None) -> dict:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if extra:
        headers.update(extra)
    return headers


async def get_with_retry(client: httpx.AsyncClient, url: str, params: dict | None = None) -> httpx.Response | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await client.get(url, params=params, headers=random_headers(), timeout=20, follow_redirects=True)
            if resp.status_code == 429:
                await asyncio.sleep(5 * attempt)
                continue
            resp.raise_for_status()
            return resp
        except httpx.HTTPError:
            if attempt == MAX_RETRIES:
                return None
            await asyncio.sleep(2 * attempt)
    return None


async def polite_delay():
    await asyncio.sleep(random.uniform(*REQUEST_DELAY_RANGE))
