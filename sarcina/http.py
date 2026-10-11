from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
TIMEOUT_S = 90
RETRIES = 4


class FetchError(Exception):
    def __init__(self, url: str, status: int | None, detail: str = ""):
        super().__init__(f"fetch failed ({status}): {url} {detail}".strip())
        self.url, self.status = url, status


def fetch_bytes(url: str, sleep: Callable[[float], None] = time.sleep) -> bytes:
    status, detail = None, ""
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            status, detail = e.code, str(e)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            status, detail = None, str(e)
        if attempt < RETRIES - 1:
            sleep(5 * 2**attempt)
    raise FetchError(url, status, detail)


def fetch_json(url: str, sleep: Callable[[float], None] = time.sleep) -> Any:
    return json.loads(fetch_bytes(url, sleep))
