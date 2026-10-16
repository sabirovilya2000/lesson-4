"""
Задание 2. Реальный I/O и обработка ошибок

robust_fetch делает запрос с:
- таймаутом на каждый запрос (10 секунд);
- не более чем 3 попытками;
- экспоненциальным backoff: 1s → 2s → 4s + случайный jitter.

robust_main скачивает все URL конкурентно через asyncio.gather
с return_exceptions=True, чтобы падение одной задачи не рушило
остальные. Возвращает кортеж (результаты, ошибки).

=== Замеры (обнови своими цифрами после запуска) ===

Запуск на 20 рабочих URL + 2 битых.
"""

import asyncio
import random
import time

import httpx

# Стабильный публичный API — 20 разных URL, всегда отвечает 200.
URLS = [
    f"https://jsonplaceholder.typicode.com/posts/{i}"
    for i in range(1, 21)
]

BAD_URLS = [
    "https://no-such-site.invalid",       # DNS не разрешится
    "https://httpbingo.org/delay/10",     # отвечает 10 секунд → таймаут
]
ALL_URLS = URLS + BAD_URLS

REQUEST_TIMEOUT = 10.0
MAX_ATTEMPTS = 3
CONCURRENCY = 5

_semaphore = asyncio.Semaphore(CONCURRENCY)


async def robust_fetch(client: httpx.AsyncClient, url: str) -> int:
    """Запрос с таймаутом и до 3 попыток с экспоненциальным backoff."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with _semaphore:
                resp = await client.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.status_code
        except (
            httpx.TimeoutException,
            httpx.TransportError,
            httpx.HTTPStatusError,
        ) as error:
            last_error = error
            if attempt == MAX_ATTEMPTS:
                break
            backoff = 2 ** (attempt - 1)
            delay = backoff + random.uniform(0, backoff)
            print(
                f"    [retry {attempt}/{MAX_ATTEMPTS - 1}] {url}: "
                f"{type(error).__name__}, ждём {delay:.2f}s"
            )
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error


async def robust_main() -> tuple[list[int], list[tuple[str, str]]]:
    """Возвращает (успешные статусы, список (url, текст ошибки))."""
    headers = {"User-Agent": "Mozilla/5.0 (course-lab-2)"}
    async with httpx.AsyncClient(
        follow_redirects=True, headers=headers
    ) as client:
        results = await asyncio.gather(
            *(robust_fetch(client, url) for url in ALL_URLS),
            return_exceptions=True,
        )

    successes: list[int] = []
    errors: list[tuple[str, str]] = []
    for url, result in zip(ALL_URLS, results):
        if isinstance(result, Exception):
            errors.append((url, f"{type(result).__name__}: {result}"))
        else:
            successes.append(result)
    return successes, errors


if __name__ == "__main__":
    start = time.perf_counter()
    ok, bad = asyncio.run(robust_main())
    elapsed = time.perf_counter() - start
    print(f"\nasync robust: {elapsed:.2f}s")
    print(f"Успешных ответов: {len(ok)}")
    print(f"Ошибок: {len(bad)}")
    for url, msg in bad:
        print(f"  - {url}: {msg}")