"""Load fleet observers from registry JSON + env secret refs.

Passwords never live in git. Copy volume is the Challenge lot on the
fleet event. Do not invent 0.01. DRY_RUN skips order_send.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from judgment.fleet.allowlist import (
    ALLOWED_ACCOUNT_KINDS,
    FORBIDDEN_ACCOUNT_KINDS,
    PlaceVeto,
    account_kind_allowed,
    assert_demo_place_target,
    login_is_forbidden,
    place_veto_reason,
)
from judgment.fleet.common import DEFAULT_REGISTRY, load_json, resolve_registry_candidates

DEFAULT_MICRO_LOT = 0.01
ENV_MICRO_LOT = "GTOS_FLEET_MICRO_LOT"
ENV_DRY_RUN = "GTOS_FLEET_DRY_RUN"
ENV_REGISTRY = "GTOS_FLEET_REGISTRY"


@dataclass(frozen=True)
class Observer:
    id: str
    display_name: str
    channel: str
    demo_login: int
    server: str
    terminal_path: str
    password_env: str
    status: str
    place_enabled: bool
    account_kind: str
    terminal_dir: str = ""

    def password(self) -> str:
        if not self.password_env:
            return ""
        return os.environ.get(self.password_env, "")


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return int(text) if text.isdigit() else None


def _truthy_env(name: str) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def parse_micro_lot(raw: Any = None) -> float:
    if raw is None or raw == "":
        raw = os.environ.get(ENV_MICRO_LOT) or DEFAULT_MICRO_LOT
    try:
        lot = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid MICRO_LOT {raw!r}") from exc
    if lot <= 0:
        raise ValueError("MICRO_LOT must be > 0")
    return lot


def resolve_copy_volume(event: Mapping[str, Any] | None = None) -> float | None:
    """Challenge lot from the event. Never invent 0.01."""
    if not event:
        return None
    for key in ("volume", "lots", "lots_placed"):
        raw = event.get(key)
        if raw in (None, ""):
            continue
        try:
            lot = float(raw)
        except (TypeError, ValueError):
            continue
        if lot > 0:
            return lot
    return None


def resolve_copy_level(event: Mapping[str, Any] | None, *keys: str) -> float | None:
    """Challenge SL or TP. 0.0 means unset — do not invent a level."""
    if not event:
        return None
    for key in keys:
        raw = event.get(key)
        if raw in (None, ""):
            continue
        try:
            level = float(raw)
        except (TypeError, ValueError):
            continue
        if level > 0:
            return level
    return None


def resolve_copy_levels(event: Mapping[str, Any] | None = None) -> tuple[float | None, float | None]:
    sl = resolve_copy_level(event, "sl", "stop_loss", "orig_sl", "broker_position_sl")
    tp = resolve_copy_level(event, "tp", "take_profit", "take_profit_1", "broker_position_tp")
    return sl, tp


def parse_dry_run(explicit: bool | None = None) -> bool:
    if explicit is not None:
        return bool(explicit)
    return _truthy_env(ENV_DRY_RUN)


def infer_account_kind(row: Mapping[str, Any]) -> str:
    explicit = str(row.get("account_kind") or "").strip()
    if explicit:
        return explicit
    channel = str(row.get("channel") or "").strip().lower()
    if channel in {"mt5_demo", "demo"}:
        return "demo"
    if channel in {"telegram", "note"}:
        return "telegram"
    return channel or "unknown"


def default_place_enabled(row: Mapping[str, Any], account_kind: str) -> bool:
    if "place_enabled" in row:
        return bool(row.get("place_enabled"))
    kind = account_kind.strip().lower()
    if kind in FORBIDDEN_ACCOUNT_KINDS:
        return False
    return kind in ALLOWED_ACCOUNT_KINDS


def coerce_terminal_path(row: Mapping[str, Any]) -> tuple[str, str]:
    """Accept Chair's directory form ``C:\\MT5\\FTMO_redacted_account`` or a full exe path."""
    raw_dir = str(row.get("terminal_dir") or "").strip()
    raw_path = str(row.get("terminal_path") or "").strip()
    source = raw_path or raw_dir
    norm = source.replace("/", "\\").strip()
    directory = raw_dir.replace("/", "\\").strip()
    if norm.lower().endswith(".exe"):
        if not directory:
            directory = str(Path(norm.replace("\\", "/")).parent).replace("/", "\\")
        return norm, directory
    if not norm:
        return "", directory
    directory = directory or norm.rstrip("\\")
    return directory.rstrip("\\") + "\\terminal64.exe", directory


def parse_observer(row: Mapping[str, Any]) -> Observer:
    login = _as_int(row.get("demo_login") if row.get("demo_login") not in (None, "") else row.get("login"))
    account_kind = infer_account_kind(row)
    observer_id = str(row.get("id") or "").strip()
    if not observer_id:
        raise ValueError("observer id required")
    if login is None:
        login = 0
    terminal_path, terminal_dir = coerce_terminal_path(row)
    return Observer(
        id=observer_id,
        display_name=str(row.get("display_name") or observer_id),
        channel=str(row.get("channel") or ""),
        demo_login=login,
        server=str(row.get("server") or ""),
        terminal_path=terminal_path,
        password_env=str(row.get("password_env") or ""),
        status=str(row.get("status") or "active"),
        place_enabled=default_place_enabled(row, account_kind),
        account_kind=account_kind,
        terminal_dir=terminal_dir,
    )


def resolve_registry_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    for path in resolve_registry_candidates():
        if path.is_file():
            return path
    return DEFAULT_REGISTRY


def fanout_targets(path: Path | None = None) -> list[str]:
    """``mirror_fanout.targets`` if present, else every placeable observer id."""
    registry = load_registry(path)
    block = registry.get("mirror_fanout")
    raw: list[Any] = []
    if isinstance(block, Mapping):
        raw = list(block.get("targets") or [])
    elif isinstance(registry.get("targets"), list):
        raw = list(registry.get("targets") or [])
    wanted = [str(item).strip() for item in raw if str(item).strip()]
    if wanted:
        return wanted
    return [observer.id for observer in placeable_observers(path)]


def targeted_observers(path: Path | None = None) -> list[Observer]:
    wanted = fanout_targets(path)
    by_id = {observer.id: observer for observer in placeable_observers(path)}
    return [by_id[item] for item in wanted if item in by_id]


def load_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = resolve_registry_path(path)
    payload = load_json(registry_path, {"observers": []})
    if "observers" not in payload or not isinstance(payload.get("observers"), list):
        payload["observers"] = []
    return payload


def load_observers(path: Path | None = None) -> list[Observer]:
    registry = load_registry(path)
    return [parse_observer(row) for row in registry.get("observers") or [] if isinstance(row, dict)]


def get_observer(observer_id: str, path: Path | None = None) -> Observer:
    for observer in load_observers(path):
        if observer.id == observer_id:
            return observer
    raise KeyError(f"observer not found: {observer_id}")


def placeable_observers(path: Path | None = None) -> list[Observer]:
    out: list[Observer] = []
    for observer in load_observers(path):
        if observer.status != "active":
            continue
        if not observer.place_enabled:
            continue
        if observer.channel.strip().lower() in {"telegram", "note"}:
            continue
        if login_is_forbidden(observer.demo_login):
            continue
        if not account_kind_allowed(observer.account_kind):
            continue
        if place_veto_reason(
            login=observer.demo_login,
            terminal_path=observer.terminal_path,
            account_kind=observer.account_kind,
        ):
            continue
        out.append(observer)
    return out


def require_placeable(observer: Observer) -> Observer:
    if observer.status != "active":
        raise PlaceVeto("observer_not_active", observer_id=observer.id)
    if not observer.place_enabled:
        raise PlaceVeto("place_disabled", observer_id=observer.id)
    assert_demo_place_target(
        login=observer.demo_login,
        terminal_path=observer.terminal_path,
        account_kind=observer.account_kind,
    )
    return observer
