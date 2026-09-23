"""HTTP JSON calls that wait out Telegram and GitHub 429s.

A 429 is not a drop. The same call is repeated after the server's
Retry-After, or one second when that header is missing.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from src.feedback.redact import redact


def retry_after_seconds(header_value: str | None) -> float:
    if header_value is None or str(header_value).strip() == "":
        return 1.0
    try:
        return max(0.0, float(str(header_value).strip()))
    except ValueError:
        return 1.0


class RateLimited(RuntimeError):
    """The server asked us to wait. The update or page is not dropped."""

    def __init__(self, seconds: float) -> None:
        super().__init__("rate limit")
        self.seconds = seconds


@dataclass
class HttpResult:
    status: int
    body: Any
    headers: dict[str, str]


def next_link(headers: dict[str, str]) -> str:
    link = headers.get("Link") or headers.get("link") or ""
    for part in link.split(","):
        if 'rel="next"' in part:
            return part.split(";")[0].strip().lstrip("<").rstrip(">")
    return ""


class HttpJson:
    def __init__(
        self,
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._opener = opener
        self._sleeper = sleeper

    def __call__(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout: float = 70,
    ) -> HttpResult:
        data = None if body is None else json.dumps(body).encode("utf-8")
        hdrs = {"Content-Type": "application/json", "User-Agent": "gtos-feedback-intake"}
        if headers:
            hdrs.update(headers)
        while True:
            req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
            try:
                with self._opener(req, timeout=timeout) as resp:
                    raw = resp.read()
                    status = int(getattr(resp, "status", 200))
                    resp_headers = {k: v for k, v in dict(getattr(resp, "headers", {})).items()}
                    if not raw:
                        return HttpResult(status, None, resp_headers)
                    return HttpResult(status, json.loads(raw.decode("utf-8")), resp_headers)
            except urllib.error.HTTPError as exc:
                retry = None
                if exc.headers is not None:
                    retry = exc.headers.get("Retry-After")
                seconds = retry_after_seconds(retry)
                if exc.code == 429 and seconds <= 120:
                    self._sleeper(seconds)
                    continue
                if exc.code in (403, 429):
                    try:
                        detail_body = exc.read().decode("utf-8", "ignore").lower()
                    except Exception:
                        detail_body = ""
                    reason = str(getattr(exc, "reason", "") or "").lower()
                    if exc.code == 429 or "rate limit" in detail_body or "rate limit" in reason:
                        raise RateLimited(seconds) from None
                detail = redact(getattr(exc, "reason", "") or "")
                raise RuntimeError(f"http {exc.code} {detail}") from None
