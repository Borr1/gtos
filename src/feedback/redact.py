"""Strip bot tokens from anything that might be logged or stored."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"\d{6,}:[A-Za-z0-9_-]{20,}")


def redact(text: str) -> str:
    return TOKEN_RE.sub("[REDACTED_TOKEN]", text)
