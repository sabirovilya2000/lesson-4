"""
Задание 1. Синхронно vs асинхронно

=== Разница ===

sync_main скачивает URL по очереди через requests: следующий запрос
начинается только после завершения предыдущего. Время складывается.

fast_main запускает все запросы конкурентно через httpx.AsyncClient
и asyncio.gather. Пока одна задача ждёт ответа, event loop выполняет
другие — их ожидания перекрываются.

=== Замеры (обнови своими цифрами после запуска) ===

sync:  6.38 секунд
async: 2.51 секунд
Ускорение: ~2.5x

(у тебя цифры могут отличаться — зависят от скорости сети)
"""

import asyncio
import time

import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


def sync_main():
    for url in URLS:
        requests.get(url)


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


if __name__ == "__main__":
    timed("sync", sync_main)
    timed("async", lambda: asyncio.run(fast_main()))