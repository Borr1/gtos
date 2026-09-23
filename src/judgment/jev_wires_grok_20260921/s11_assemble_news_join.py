"""DRAFT ONLY — session 11_host_events_news_join_honesty.

Not landed. Not imported by live writer. place=false. No NEWS_PROTOCOL.

Intended land path (Chair later):
  src/judgment/news_join.py

COMPLETE_STATE.news_join = object | "STATE_MISSING"
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Literal, Mapping

# Intended imports after land:
# from .cross_asset import event_join_features
# from .fluid_local import warsh_class
# from .host_events import news_inventory_at, news_inventory_extra, load_host_events, resolve_host_events_path
# from .news_spine import attach_news, load_spines
# from .veto import refuse_invented_news_protocol

STATE_MISSING: Literal["STATE_MISSING"] = "STATE_MISSING"
SCHEMA = "gtos.complete_state.news_join.v0"


def real_join_exists(*, spines: Mapping[str, Any] | None, host_inv: Mapping[str, Any] | None) -> bool:
    n_files = int((spines or {}).get("n_files") or 0)
    sources = (spines or {}).get("sources") or []
    json_join = n_files >= 1 or bool(sources)
    host_join = (host_inv or {}).get("host_news_source") == "challenge_host_news_writer"
    return bool(json_join or host_join)


def assemble_news_join(
    as_of_utc: datetime | None,
    *,
    spines: dict[str, Any] | None = None,
    host_events: Iterable[dict[str, Any]] | None = None,
    path: Any = None,
    live: bool = False,
    symbol: str = "XAUUSD",
    attach_news_fn=None,
    load_spines_fn=None,
    news_inventory_at_fn=None,
    news_inventory_extra_fn=None,
    event_join_features_fn=None,
    warsh_class_fn=None,
    refuse_invented_news_protocol_fn=None,
) -> dict[str, Any] | Literal["STATE_MISSING"]:
    """Return news_join object or STATE_MISSING. Never invent HIGH / NEWS_PROTOCOL.

    Injected fns keep this draft import-safe outside the organism.
    """
    if as_of_utc is None:
        return STATE_MISSING

    packed = spines if spines is not None else (load_spines_fn() if load_spines_fn else {"n_files": 0, "sources": [], "events": []})
    news = attach_news_fn(as_of_utc, spines=packed, symbol=symbol) if attach_news_fn else {
        "spine_empty": True,
        "events": [],
        "source": "unassembled",
        "high_in_f5_window": None,
        "high_in_w7_window": None,
        "minutes_to_nearest_high": None,
        "challenge_axis_covering": False,
    }
    if news_inventory_extra_fn is not None and host_events is None:
        host_inv = news_inventory_extra_fn(as_of_utc, path, live=live)
    elif news_inventory_at_fn is not None:
        host_inv = news_inventory_at_fn(host_events, as_of_utc)
    else:
        host_inv = {
            "host_news_inventory_status": None,
            "host_news_n_in_window": None,
            "host_news_event": None,
            "host_news_ts_utc": None,
            "host_news_source": "unassembled",
        }

    if not real_join_exists(spines=packed, host_inv=host_inv):
        return STATE_MISSING

    if refuse_invented_news_protocol_fn:
        refuse_invented_news_protocol_fn(list(news.keys()) + list(host_inv.keys()))

    spine_empty = bool(news.get("spine_empty"))
    if event_join_features_fn and not spine_empty:
        event_join: Any = event_join_features_fn(news)
    else:
        event_join = STATE_MISSING

    warsh = "none"
    if warsh_class_fn:
        warsh = warsh_class_fn({"news": news})
    elif spine_empty or not (news.get("events") or []):
        warsh = "none"

    obj = {
        "schema": SCHEMA,
        "protocol": STATE_MISSING,
        "spine_empty": spine_empty,
        "challenge_axis_covering": bool(news.get("challenge_axis_covering")),
        "source": news.get("source") or "unassembled",
        "spine_id": news.get("spine_id"),
        "events": list(news.get("events") or []),
        "minutes_to_nearest_high": news.get("minutes_to_nearest_high"),
        "high_in_f5_window": news.get("high_in_f5_window") if not spine_empty else None,
        "high_in_w7_window": news.get("high_in_w7_window") if not spine_empty else None,
        "warsh_class": warsh,
        "host_news_source": host_inv.get("host_news_source") or "unassembled",
        "host_news_inventory_status": host_inv.get("host_news_inventory_status"),
        "host_news_n_in_window": host_inv.get("host_news_n_in_window"),
        "host_news_event": host_inv.get("host_news_event"),
        "host_news_ts_utc": host_inv.get("host_news_ts_utc"),
        "event_join": event_join,
        "official_high_spine": STATE_MISSING,
        "news_brief": STATE_MISSING,
        "walter": {"present": False},
        "invented": False,
        "never_invent_news_protocol": True,
        "place": False,
    }
    if "NEWS_PROTOCOL" in obj:
        raise RuntimeError("news_join must not carry NEWS_PROTOCOL")
    return obj


def stamp_complete_state_news_join(complete: dict[str, Any], news_join: dict[str, Any] | str) -> dict[str, Any]:
    """Optional COMPLETE_STATE field. Missing join increments n_incomplete; does not alone refuse."""
    out = dict(complete)
    out["news_join"] = news_join
    if news_join == STATE_MISSING:
        out["n_incomplete"] = int(out.get("n_incomplete") or 0) + 1
    out.setdefault("place_context", {})
    return out
