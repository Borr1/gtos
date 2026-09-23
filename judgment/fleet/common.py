"""Shared fleet constants, ledger normalize, and schema checks.

One producer (Challenge book events). Chair never places on observer books.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

MODULE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = MODULE_ROOT.parents[1]
SCHEMA_DIR = MODULE_ROOT / "schemas"

SOURCE_LOGIN = 0
QUARANTINE_LOGINS = frozenset({0})
CHALLENGE_NS = "operator"

FLEET_EVENT_SCHEMA = "gtos.fleet_event.v0"
FLEET_FEEDBACK_SCHEMA = "gtos.fleet_feedback.v0"
CLOSE_LOOP_SCHEMA = "gtos.close_loop.v1"
FLEET_REGISTRY_SCHEMA = "gtos.fleet_registry.v0"

FLEET_KINDS = frozenset({"fill", "close", "mfe", "high", "candidate"})
KIND_ALIASES = {
    "fill": "fill",
    "open": "fill",
    "opened": "fill",
    "deal_in": "fill",
    "close": "close",
    "closed": "close",
    "deal_out": "close",
    "mfe": "mfe",
    "high": "high",
    "candidate": "candidate",
    "test": "candidate",
}
SIDE_ALIASES = {
    "buy": "buy",
    "long": "buy",
    "sell": "sell",
    "short": "sell",
}

ENV_LEDGER = "GTOS_FLEET_LEDGER"
ENV_LIVE_DIR = "GTOS_LIVE_DIR"
ENV_OUTBOX = "GTOS_FLEET_OUTBOX"
JUDGMENT_LIVE_DIR = REPO_ROOT / "judgment" / "live"
DEFAULT_LIVE_DIRS = (
    JUDGMENT_LIVE_DIR,
    Path(os.environ.get(ENV_LIVE_DIR) or "/workspace/gtos/live"),
    Path("/workspace/gtos/live"),
    Path("/workspace/gtos"),
)
LEDGER_FILENAMES = ("book_event_ledger.jsonl", "book_event_spoken.jsonl")

# VPS Chair path of record. Legacy outbox kept as fallback for PR #28 trees.
DEFAULT_OUTBOX = JUDGMENT_LIVE_DIR / "fleet_events.jsonl"
LEGACY_OUTBOX = MODULE_ROOT / "outbox" / "fleet_events.jsonl"
DEFAULT_RELAY_STATE = MODULE_ROOT / "outbox" / "relay_state.json"
DEFAULT_INBOX = MODULE_ROOT / "inbox" / "fleet_feedback.jsonl"
DEFAULT_LABELS = MODULE_ROOT / "labels" / "close_loop_labels.jsonl"
DEFAULT_PROMOTE_STATE = MODULE_ROOT / "labels" / "promote_state.json"
MIRROR_REGISTRY = MODULE_ROOT / "mirror" / "registry" / "observers.v0.json"
SCHEMA_REGISTRY = SCHEMA_DIR / "observers.v0.json"
DEFAULT_REGISTRY = MIRROR_REGISTRY
MIRROR_RUN_DIR = MODULE_ROOT / "mirror" / "run"
MIRROR_LOG_DIR = MODULE_ROOT / "mirror" / "logs"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"schema {name} is not an object")
    return payload


def load_feedback_schema() -> dict[str, Any]:
    return load_schema("fleet_feedback.v0.json")


def load_event_schema() -> dict[str, Any]:
    return load_schema("fleet_event.v0.json")


def load_close_loop_lock() -> dict[str, Any]:
    return load_schema("schema_locks_v1.json")


def timing_enum() -> tuple[str, ...]:
    return tuple(load_feedback_schema()["timing_enum"])


def miss_type_map() -> dict[str, str]:
    raw = load_feedback_schema()["maps_to_close_loop_miss_type"]
    return {str(k): str(v) for k, v in raw.items()}


def miss_type_for_timing(timing: str) -> str:
    mapped = miss_type_map().get(timing)
    if mapped is None:
        raise ValueError(f"unknown timing {timing!r}")
    return mapped


def close_loop_miss_types() -> frozenset[str]:
    lock = load_close_loop_lock()
    return frozenset(str(x) for x in lock.get("miss_type_enum") or ())


def close_loop_miss_type(mapped: str) -> str:
    """Join fleet map onto the locked close_loop enum. Unknown → unlabeled."""
    allowed = close_loop_miss_types()
    if mapped in allowed:
        return mapped
    return "unlabeled"


def _as_int_login(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return int(text) if text.isdigit() else None


def extract_logins(row: Mapping[str, Any]) -> list[int]:
    found: list[int] = []
    for key in ("source_login", "login", "account_login", "account"):
        login = _as_int_login(row.get(key))
        if login is not None:
            found.append(login)
    inner = row.get("input")
    if isinstance(inner, Mapping):
        found.extend(extract_logins(inner))
    return found


def login_decision(row: Mapping[str, Any]) -> tuple[bool, str]:
    """Accept Challenge source; quarantine 0; reject any other stamped login."""
    logins = extract_logins(row)
    if any(login in QUARANTINE_LOGINS for login in logins):
        return False, "quarantined_login"
    foreign = [login for login in logins if login != SOURCE_LOGIN]
    if foreign:
        return False, "foreign_login"
    return True, "ok"


def _unwrap_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    inner = row.get("input")
    if isinstance(inner, Mapping) and (inner.get("ticket") or inner.get("order") or inner.get("deal")):
        return inner
    return row


def _kind(row: Mapping[str, Any], raw: Mapping[str, Any]) -> str | None:
    for src in (row, raw):
        token = src.get("kind") or src.get("event") or src.get("type")
        if token:
            aliased = KIND_ALIASES.get(str(token).strip().lower())
            if aliased:
                return aliased
    if raw.get("input") and (row.get("ticket") or row.get("close_time") or row.get("exit_class")):
        return "close"
    return None


def _side(row: Mapping[str, Any]) -> str | None:
    raw = row.get("side") or row.get("type_str") or row.get("direction")
    if raw is None or raw == "":
        return None
    return SIDE_ALIASES.get(str(raw).strip().lower())


def _ticket(row: Mapping[str, Any]) -> Any:
    for key in ("ticket", "order", "deal", "position"):
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def _symbol(row: Mapping[str, Any]) -> str | None:
    value = row.get("symbol") or row.get("sym")
    if value is None or value == "":
        return None
    return str(value)


def _r_orig(row: Mapping[str, Any]) -> Any:
    for key in ("r_orig", "r", "R"):
        if row.get(key) is not None and row.get(key) != "":
            return row.get(key)
    return None


def normalize_book_row(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Challenge ledger / replay / host-event row → fleet_event.v0 or None.

    Does not invent tickets. Does not emit quarantine or foreign-login rows.
    """
    if not isinstance(row, Mapping):
        return None
    ok, _reason = login_decision(row)
    if not ok:
        return None
    body = _unwrap_row(row)
    ok, _reason = login_decision(body)
    if not ok:
        return None
    kind = _kind(body, row)
    if kind not in FLEET_KINDS:
        return None
    ticket = _ticket(body)
    if ticket is None:
        return None
    symbol = _symbol(body)
    if not symbol:
        return None
    ts = body.get("ts_utc") or body.get("ts") or body.get("close_time") or body.get("open_time") or utc_now()
    return {
        "schema": FLEET_EVENT_SCHEMA,
        "fleet_event_id": str(uuid.uuid4()),
        "ts_utc": str(ts),
        "kind": kind,
        "ticket": ticket,
        "symbol": symbol,
        "side": _side(body),
        "sleeve": body.get("sleeve") or body.get("tag") or None,
        "r_orig": _r_orig(body),
        "mfe": body.get("mfe"),
        "exit_class": body.get("exit_class"),
        "note": body.get("note"),
        "ns": body.get("ns") or row.get("namespace") or CHALLENGE_NS,
        "source_login": SOURCE_LOGIN,
        "relay_ts_utc": utc_now(),
        "volume": body.get("volume") if body.get("volume") is not None else body.get("lots"),
        "sl": body.get("sl") if body.get("sl") not in (None, "") else body.get("orig_sl"),
        "tp": body.get("tp") if body.get("tp") not in (None, "") else body.get("take_profit"),
        "price": body.get("price"),
    }


def validate_fleet_event(row: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    spec = load_event_schema()
    if row.get("schema") != spec["schema"]:
        errors.append("schema")
    for field in spec["required"]:
        if row.get(field) in (None, ""):
            errors.append(f"missing:{field}")
    if row.get("kind") not in spec["kinds"]:
        errors.append("kind")
    login = _as_int_login(row.get("source_login"))
    if login != SOURCE_LOGIN:
        errors.append("source_login")
    if login in QUARANTINE_LOGINS:
        errors.append("quarantined_login")
    side = row.get("side")
    if side not in (None, "buy", "sell"):
        errors.append("side")
    return errors


def validate_fleet_feedback(row: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    spec = load_feedback_schema()
    if row.get("schema") != spec["schema"]:
        errors.append("schema")
    for field in spec["required"]:
        if row.get(field) in (None, ""):
            errors.append(f"missing:{field}")
    if row.get("timing") not in spec["timing_enum"]:
        errors.append("timing")
    if row.get("verb") != "LABEL":
        errors.append("verb")
    if row.get("place") is True:
        errors.append("place")
    login = _as_int_login(row.get("source_login"))
    if login != SOURCE_LOGIN:
        errors.append("source_login")
    return errors


def resolve_outbox(explicit: Path | None = None) -> Path:
    """Challenge fill/close bus. Prefer ``judgment/live/fleet_events.jsonl``."""
    if explicit is not None:
        return explicit
    env = (os.environ.get(ENV_OUTBOX) or "").strip()
    if env:
        return Path(env)
    return DEFAULT_OUTBOX


def resolve_registry_candidates() -> list[Path]:
    env = (os.environ.get("GTOS_FLEET_REGISTRY") or "").strip()
    paths: list[Path] = []
    if env:
        paths.append(Path(env))
    paths.extend((MIRROR_REGISTRY, SCHEMA_REGISTRY))
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def candidate_ledgers() -> list[Path]:
    paths: list[Path] = []
    env = (os.environ.get(ENV_LEDGER) or "").strip()
    if env:
        paths.append(Path(env))
    for root in DEFAULT_LIVE_DIRS:
        for name in LEDGER_FILENAMES:
            paths.append(Path(root) / name)
    # Dedup while keeping order.
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def pick_ledger(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        return explicit if explicit.is_file() else None
    for path in candidate_ledgers():
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file():
        return dict(default or {})
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else dict(default or {})


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows
