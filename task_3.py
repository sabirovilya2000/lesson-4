"""
Задание 3 (*). Вынос CPU-bound-вычислений

Демонстрация того, как блокирующий CPU-bound-вызов (heavy) в event loop
останавливает весь цикл событий — видно по «пульсу» ticker: точки
перестают печататься, пока считаются хеши.

Решение — вынести вычисления в отдельный процесс через
loop.run_in_executor + ProcessPoolExecutor. Процессы не разделяют GIL,
поэтому считают реально параллельно, а event loop остаётся свободным.
ThreadPoolExecutor здесь не поможет — из-за GIL потоки не дают
параллелизма на CPU-bound-задаче.

Что видно на экране:
1) heavy вызывается прямо в корутине — точки ticker почти замирают;
2) heavy уходит в процессы — точки продолжают бежать ровно.

=== Замеры ===

cpu_blocking: тяжесть в loop — общее время большое, ticker встаёт.
cpu_executor: тяжесть в процессах — общее время меньше, ticker бежит.

=== Важное для Windows/macOS ===

Без if __name__ == "__main__": дочерние процессы заново импортируют
модуль — и ProcessPoolExecutor упадёт.
"""

import asyncio
import hashlib
import os
import time
from concurrent.futures import ProcessPoolExecutor

import httpx

URLS = [
    f"https://jsonplaceholder.typicode.com/posts/{i}"
    for i in range(1, 21)
]


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"\n{label}: {time.perf_counter() - start:.2f}s")


def heavy(body: bytes) -> str:
    """Долгий CPU-bound расчёт: 300 000 раундов sha256 от тела."""
    h = hashlib.sha256(body * 1000).digest()
    for _ in range(300_000):
        h = hashlib.sha256(h).digest()
    return h.hex()


async def ticker():
    """Пульс event loop: пока точки печатаются — loop живой."""
    try:
        while True:
            print(".", end="", flush=True)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print(" [ticker stopped]")
        raise


async def fetch_bytes(client: httpx.AsyncClient, url: str) -> bytes:
    resp = await client.get(url)
    resp.raise_for_status()
    return resp.content


async def cpu_main_blocking():
    """Вариант 1: heavy вызывается прямо в корутине → loop замирает."""
    print("\n--- CPU-bound в event loop (точки почти стоят) ---")
    ticker_task = asyncio.create_task(ticker())
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            bodies = await asyncio.gather(
                *(fetch_bytes(client, url) for url in URLS)
            )
        for body in bodies:
            heavy(body)  # БЛОКИРУЕТ loop
    finally:
        ticker_task.cancel()
        try:
            await ticker_task
        except asyncio.CancelledError:
            pass


async def cpu_main_executor():
    """Вариант 2: heavy уходит в пул процессов → loop свободен."""
    print("\n--- CPU-bound в ProcessPoolExecutor (точки бегут) ---")
    ticker_task = asyncio.create_task(ticker())
    loop = asyncio.get_running_loop()
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            bodies = await asyncio.gather(
                *(fetch_bytes(client, url) for url in URLS)
            )

        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            await asyncio.gather(
                *(loop.run_in_executor(pool, heavy, body) for body in bodies)
            )
    finally:
        ticker_task.cancel()
        try:
            await ticker_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    timed("cpu_blocking", lambda: asyncio.run(cpu_main_blocking()))
    timed("cpu_executor", lambda: asyncio.run(cpu_main_executor()))