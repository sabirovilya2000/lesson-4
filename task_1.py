import asyncio
import time
import httpx
import requests

URLS = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 21)]

def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

def sync_main():
    for url in URLS:
        requests.get(url, timeout=30.0)

async def fetch(client, url):
    resp = await client.get(url)
    return resp.status_code

async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))

if __name__ == "__main__":
    timed("sync", sync_main)
    timed("async", lambda: asyncio.run(fast_main()))