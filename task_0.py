"""
Задание 0. Разминка-ловушка «Почему не быстрее?»

=== Проблема ===

В slow_main запросы выполняются последовательно:
    for url in URLs:
        await fetch(client, url)

Хотя код написан с async/await, каждый await fetch(...) дожидается
результата здесь и сейчас, прежде чем перейти к следующей итерации.
Конкурентности нет — это та же синхронная модель, только оформленная
в async-синтаксисе.

=== Как починить ===

Запустить все корутины fetch сразу и дождаться всех сразу:
    await asyncio.gather(*(fetch(client, url) for url in URLs))

Пока одна задача ждёт ответа от сервера, event loop выполняет другие.

=== Замеры (у меня получились такие) ===

slow (последовательно): 0.78 секунд
fast (конкурентно):      0.32 секунд
Ускорение:               ~2.4x

(у тебя цифры могут отличаться — зависят от скорости сети)

=== Замечание про follow_redirects ===

picsum.photos отвечает 302-редиректом. httpx по умолчанию редиректы
не следует, поэтому follow_redirects=True обязателен.
"""

import asyncio
import time

import httpx

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


async def slow_main():
    """Медленно: последовательные await в цикле for."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in URLS:
            await fetch(client, url)


async def fast_main():
    """Быстро: все запросы конкурентно через gather."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


if __name__ == "__main__":
    timed("slow", lambda: asyncio.run(slow_main()))
    timed("fast", lambda: asyncio.run(fast_main()))