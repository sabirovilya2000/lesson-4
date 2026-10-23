import asyncio
import hashlib
import time
from concurrent.futures import ProcessPoolExecutor

URLS = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 21)]

def heavy(text: str) -> str:
    h = hashlib.sha256(text.encode()).hexdigest()
    for _ in range(500_000):
        h = hashlib.sha256(h.encode()).hexdigest()
    return h

async def ticker():
    try:
        while True:
            print(".", end="", flush=True)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print(" [стоп]")
        raise

async def download(url):
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        return resp.text

async def cpu_main(use_processes=False):
    task = asyncio.create_task(ticker())
    
    texts = await asyncio.gather(*(download(url) for url in URLS))
    
    if use_processes:
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            await asyncio.gather(
                *(loop.run_in_executor(pool, heavy, text) for text in texts)
            )
    else:
        for text in texts:
            heavy(text)
            
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    print("\n1. В лоб (точки замирают):")
    start = time.perf_counter()
    asyncio.run(cpu_main(use_processes=False))
    print(f"\nВремя: {time.perf_counter() - start:.2f}s")

    print("\n2. В процессах (точки бегут):")
    start = time.perf_counter()
    asyncio.run(cpu_main(use_processes=True))
    print(f"\nВремя: {time.perf_counter() - start:.2f}s")