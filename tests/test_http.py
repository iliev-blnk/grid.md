import io
import urllib.error

import pytest

from sarcina import http


def _err(code):
    return urllib.error.HTTPError("https://x", code, "x", {}, io.BytesIO(b""))


def test_retries_then_raises(monkeypatch):
    calls = []

    def boom(req, timeout):
        calls.append(1)
        raise _err(429)

    monkeypatch.setattr(http.urllib.request, "urlopen", boom)
    with pytest.raises(http.FetchError) as e:
        http.fetch_bytes("https://x", sleep=lambda s: None)
    assert e.value.status == 429
    assert len(calls) == 4


def test_retry_succeeds(monkeypatch):
    seq = [_err(429), _err(429), b"ok"]
    delays = []

    class R:
        def __init__(self, b): self.b = b
        def read(self): return self.b
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake(req, timeout):
        v = seq.pop(0)
        if isinstance(v, Exception):
            raise v
        return R(v)

    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    assert http.fetch_bytes("https://x", sleep=delays.append) == b"ok"
    assert delays[0] < delays[1]
