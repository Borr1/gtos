"""Canonical session-token helpers shared by package and replay surfaces."""

from __future__ import annotations

from typing import Any


def canonical_utc_hour_bucket_token(value: Any) -> str | None:
    """Return canonical ``hNN_NN`` for one consecutive UTC-hour bucket."""

    token = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if token.startswith("moonshot_"):
        token = token.removeprefix("moonshot_")
    if (
        len(token) != 6
        or not token.startswith("h")
        or token[3] != "_"
        or not token[1:3].isdigit()
        or not token[4:6].isdigit()
    ):
        return None
    start_hour = int(token[1:3])
    end_hour = int(token[4:6])
    if not (0 <= start_hour < 24 and end_hour == (start_hour + 1) % 24):
        return None
    return f"h{start_hour:02d}_{end_hour:02d}"


def utc_hour_bucket_aliases(value: Any) -> set[str]:
    """Return symmetric raw and ``moonshot_`` aliases for a valid hour bucket."""

    token = canonical_utc_hour_bucket_token(value)
    if token is None:
        return set()
    return {token, f"moonshot_{token}"}
