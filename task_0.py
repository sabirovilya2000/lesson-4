import asyncio
import time
import httpx

URLS = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 21)]

def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")

async def fetch(client, url):
    resp = await client.get(url)
    return resp.status_code

async def slow_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        for url in URLS:
            await fetch(client, url)

async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))

if __name__ == "__main__":
    timed("slow", lambda: asyncio.run(slow_main()))
    timed("fast", lambda: asyncio.run(fast_main()))