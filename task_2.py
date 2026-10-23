import asyncio
import time
import httpx

URLS = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 21)]
BAD_URLS = ["https://no-such-site.invalid", "https://httpbingo.org/delay/10"]
ALL_URLS = URLS + BAD_URLS

async def robust_fetch(client, url):
    for attempt in range(3):
        try:
            resp = await client.get(url, timeout=3.0)
            resp.raise_for_status()
            return resp.status_code
        except Exception as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(2 ** attempt)

async def robust_main():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(robust_fetch(client, url) for url in ALL_URLS),
            return_exceptions=True
        )
    
    ok = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, Exception)]
    return ok, errors

if __name__ == "__main__":
    start = time.perf_counter()
    ok, errors = asyncio.run(robust_main())
    print(f"\nasync robust: {time.perf_counter() - start:.2f}s")
    print(f"Успешных ответов: {len(ok)}")
    print(f"Ошибок: {len(errors)}")