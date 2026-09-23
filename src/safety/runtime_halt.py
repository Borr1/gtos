"""Source-bound runtime halt guard for hard-halt and autostart stops.

This module deliberately reads local repo flag files only. It does not inspect
broker account/order/deal/position state and never performs broker mutation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTROL_VERSION = "runtime_control_atomic_halt_v1"
DEFAULT_HALT_FLAG_PATHS = (
    "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag",
    "pipeline_state/RESEARCH_RUNTIME_HALT.flag",
    "knowledge_base/meta/AUTOSTART_DISABLED.flag",
)
DEFAULT_AUDIT_LOG_PATH = "pipeline_state/runtime_control_atomic_halt_audit.jsonl"


@dataclass(frozen=True)
class RuntimeHaltSnapshot:
    """Mechanical snapshot of local runtime-halt flag state."""

    active: bool
    status: str
    control_version: str
    checked_at_utc: str
    repo_root: str
    checked_paths: list[dict[str, Any]]
    active_flags: list[dict[str, Any]]
    missing_paths: list[dict[str, Any]]
    unreadable_paths: list[dict[str, Any]]
    fail_closed_on_unreadable_flag_path: bool
    source_boundary: str
    runtime_effect_boundary: str
    forbidden_surface_status: str
    broker_runtime_change_status: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "status": self.status,
            "control_version": self.control_version,
            "checked_at_utc": self.checked_at_utc,
            "repo_root": self.repo_root,
            "checked_paths": self.checked_paths,
            "active_flags": self.active_flags,
            "missing_paths": self.missing_paths,
            "unreadable_paths": self.unreadable_paths,
            "fail_closed_on_unreadable_flag_path": (
                self.fail_closed_on_unreadable_flag_path
            ),
            "source_boundary": self.source_boundary,
            "runtime_effect_boundary": self.runtime_effect_boundary,
            "forbidden_surface_status": self.forbidden_surface_status,
            "broker_runtime_change_status": self.broker_runtime_change_status,
        }


class RuntimeHaltError(RuntimeError):
    """Raised when an atomic runtime halt is active."""

    def __init__(self, action: str, snapshot: RuntimeHaltSnapshot):
        self.action = action
        self.snapshot = snapshot
        active_paths = [
            str(item.get("path")) for item in snapshot.active_flags
        ] or [
            str(item.get("path")) for item in snapshot.unreadable_paths
        ]
        super().__init__(
            f"runtime halt active for {action}: {', '.join(active_paths)}"
        )


def _runtime_control_config(config: dict | None) -> dict:
    if not isinstance(config, dict):
        return {}
    block = config.get("runtime_control")
    return block if isinstance(block, dict) else {}


def runtime_halt_guard_enabled(
    config: dict | None,
    *,
    default: bool = False,
) -> bool:
    """Return whether the runtime halt guard should enforce for this config."""

    block = _runtime_control_config(config)
    if "enabled" in block:
        return bool(block.get("enabled"))
    if "halt_guard_enabled" in block:
        return bool(block.get("halt_guard_enabled"))
    return default


def _repo_root(config: dict | None, repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    block = _runtime_control_config(config)
    configured = block.get("repo_root") or (config or {}).get("repo_root")
    if configured:
        return Path(str(configured)).expanduser().resolve()
    return Path.cwd().resolve()


def _configured_flag_paths(config: dict | None) -> list[str]:
    block = _runtime_control_config(config)
    raw_paths = block.get("halt_flag_paths")
    if isinstance(raw_paths, (list, tuple)) and raw_paths:
        return [str(path) for path in raw_paths]
    return list(DEFAULT_HALT_FLAG_PATHS)


def _audit_log_path(
    config: dict | None,
    repo_root: str | Path | None = None,
) -> Path:
    root = _repo_root(config, repo_root)
    block = _runtime_control_config(config)
    raw_path = str(block.get("audit_log_path") or DEFAULT_AUDIT_LOG_PATH)
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else root / path


def _resolve_path(root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else root / path


def read_runtime_halt_state(
    config: dict | None = None,
    *,
    repo_root: str | Path | None = None,
) -> RuntimeHaltSnapshot:
    """Read local halt flag state without touching broker/runtime processes."""

    root = _repo_root(config, repo_root)
    block = _runtime_control_config(config)
    fail_closed = bool(block.get("fail_closed_on_unreadable_flag_path", True))
    checked_paths: list[dict[str, Any]] = []
    active_flags: list[dict[str, Any]] = []
    missing_paths: list[dict[str, Any]] = []
    unreadable_paths: list[dict[str, Any]] = []

    for raw_path in _configured_flag_paths(config):
        path = _resolve_path(root, raw_path)
        record = {
            "configured_path": raw_path,
            "path": str(path),
            "exists": False,
            "read_status": "not_checked",
        }
        try:
            exists = path.exists()
            record["exists"] = exists
            record["read_status"] = "exists" if exists else "missing"
        except OSError as exc:
            record["read_status"] = "unreadable"
            record["error"] = str(exc)
            unreadable_paths.append(record)
            checked_paths.append(record)
            continue

        checked_paths.append(record)
        if exists:
            active_flags.append(record)
        else:
            missing_paths.append(record)

    unreadable_active = fail_closed and bool(unreadable_paths)
    active = bool(active_flags) or unreadable_active
    status = "runtime_halt_active" if active else "runtime_halt_clear"
    if unreadable_active and not active_flags:
        status = "runtime_halt_fail_closed_unreadable_flag_path"

    return RuntimeHaltSnapshot(
        active=active,
        status=status,
        control_version=CONTROL_VERSION,
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        repo_root=str(root),
        checked_paths=checked_paths,
        active_flags=active_flags,
        missing_paths=missing_paths,
        unreadable_paths=unreadable_paths,
        fail_closed_on_unreadable_flag_path=fail_closed,
        source_boundary=(
            "local_repo_flag_files_only_no_broker_account_order_deal_position_read"
        ),
        runtime_effect_boundary=(
            "blocks_scheduler_process_order_intent_and_new_order_send_paths_allows_risk_reducing_management"
        ),
        forbidden_surface_status=(
            "no_broker_account_order_deal_position_mutation_performed"
        ),
        broker_runtime_change_status=False,
    )


def append_runtime_halt_audit(
    *,
    action: str,
    snapshot: RuntimeHaltSnapshot,
    context: dict[str, Any] | None = None,
    config: dict | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Append one JSONL audit row for a halt decision."""

    row = {
        "schema_version": 1,
        "control_version": CONTROL_VERSION,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "context": context or {},
        "snapshot": snapshot.to_dict(),
        "decision": (
            "blocked_by_runtime_halt"
            if snapshot.active
            else "allowed_runtime_halt_clear"
        ),
        "source_boundary": snapshot.source_boundary,
        "runtime_effect_boundary": snapshot.runtime_effect_boundary,
        "forbidden_surface_status": snapshot.forbidden_surface_status,
        "broker_runtime_change_status": snapshot.broker_runtime_change_status,
    }
    path = _audit_log_path(config, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    return row


def enforce_runtime_not_halted(
    *,
    action: str,
    config: dict | None = None,
    context: dict[str, Any] | None = None,
    repo_root: str | Path | None = None,
    enabled_default: bool = False,
    audit: bool = True,
) -> RuntimeHaltSnapshot:
    """Raise RuntimeHaltError if enabled local halt flags are active."""

    snapshot = read_runtime_halt_state(config, repo_root=repo_root)
    if not runtime_halt_guard_enabled(config, default=enabled_default):
        return snapshot
    if snapshot.active:
        if audit:
            append_runtime_halt_audit(
                action=action,
                snapshot=snapshot,
                context=context,
                config=config,
                repo_root=repo_root,
            )
        raise RuntimeHaltError(action, snapshot)
    return snapshot
