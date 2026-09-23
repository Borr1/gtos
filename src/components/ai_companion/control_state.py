"""Validated runtime control state for AI companions.

This module is the runtime trust boundary. Companion processes can observe logs
and write JSON, but live trading code only applies the controls accepted here:

* pause_new_entries: observe-only for new entries, management still runs.
* symbol_sleeve_cooldown: skip a matching candidate until expiry.
* risk_multiplier: reduce risk only; values above 1.0 are rejected.

No control can place orders, increase risk, override execution gates, mutate
broker state, or change credentials.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping


AI_COMPANION_CONTROL_SCHEMA = "gtos.ai_companion.control_state.v1"
DEFAULT_CONTROL_STATE_PATH = "pipeline_state/ai_companion/control_state.json"
DEFAULT_DECISION_LOG_PATH = "shadow_logs/ai_companion_decisions.jsonl"
MAX_CONTROL_CLOCK_SKEW_SECONDS = 300.0

ALLOWED_AUTHORITY_LEVELS = {"observe", "advisory", "protective"}
APPLIED_AUTHORITY_LEVELS = {"protective"}
ALLOWED_CONTROL_TYPES = {"pause_new_entries", "symbol_sleeve_cooldown", "risk_multiplier"}
RUNTIME_EFFECT_BOUNDARY = (
    "bounded_protective_runtime_controls_only_no_order_placement_no_risk_increase_"
    "no_hard_gate_override_no_broker_account_order_deal_position_or_credential_mutation"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(dt: datetime | None = None) -> str:
    return (dt or utc_now()).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _runtime_config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    cfg = config or {}
    return cfg.get("gtos_vnext_runtime", cfg) or {}


def ai_companion_config(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    rt = _runtime_config(config)
    nested = rt.get("ai_companion")
    return nested if isinstance(nested, Mapping) else {}


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    return bool(default)


def config_bool(config: Mapping[str, Any] | None, key: str, default: bool = False) -> bool:
    cfg = config or {}
    if key in cfg:
        return _parse_bool(cfg.get(key), default)
    rt = _runtime_config(config)
    nested = ai_companion_config(config)
    if key in nested:
        return _parse_bool(nested.get(key), default)
    return _parse_bool(rt.get(f"ai_companion_{key}", default), default)


def config_value(config: Mapping[str, Any] | None, key: str, default: Any = None) -> Any:
    cfg = config or {}
    if key in cfg:
        return cfg.get(key)
    rt = _runtime_config(config)
    nested = ai_companion_config(config)
    if key in nested:
        return nested.get(key)
    return rt.get(f"ai_companion_{key}", default)


def build_empty_control_state(
    *,
    authority_level: str = "protective",
    now: datetime | None = None,
    ttl_minutes: int = 10,
    source: str = "ai_companion",
) -> dict[str, Any]:
    ts = now or utc_now()
    expires = ts + timedelta(minutes=max(1, int(ttl_minutes)))
    return {
        "schema": AI_COMPANION_CONTROL_SCHEMA,
        "generated_at_utc": iso_utc(ts),
        "expires_at_utc": iso_utc(expires),
        "authority_level": authority_level,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "source": source,
        "controls": [],
        "rejected_controls": [],
        "summary": {
            "active_control_count": 0,
            "pause_new_entries": False,
            "symbol_sleeve_cooldown_count": 0,
            "risk_multiplier_count": 0,
        },
    }


def load_control_state(repo_root: str | Path, control_state_path: str = DEFAULT_CONTROL_STATE_PATH) -> dict[str, Any] | None:
    path = Path(repo_root) / control_state_path
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return loaded if isinstance(loaded, dict) else None


def write_control_state_atomic(
    repo_root: str | Path,
    state: Mapping[str, Any],
    control_state_path: str = DEFAULT_CONTROL_STATE_PATH,
) -> Path:
    path = Path(repo_root) / control_state_path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))
    return path


def _match(value: Any, wanted: str | None) -> bool:
    if wanted in (None, "", "*"):
        return True
    return str(value) == str(wanted)


def _control_namespace_matches(control: Mapping[str, Any], namespace: str | None) -> bool:
    wanted = control.get("namespace")
    if wanted in (None, ""):
        return False
    if str(wanted) == "*":
        return True
    if namespace in (None, ""):
        return False
    return str(namespace) == str(wanted)


def _active_control(control: Mapping[str, Any], now: datetime, namespace: str | None) -> tuple[bool, str | None]:
    expires = parse_utc(control.get("expires_at_utc"))
    if expires is None:
        return False, "missing_or_invalid_expires_at_utc"
    if expires <= now:
        return False, "expired"
    if not _control_namespace_matches(control, namespace):
        return False, "namespace_mismatch"
    return True, None


def _sanitize_control(
    control: Mapping[str, Any],
    *,
    now: datetime,
    namespace: str | None,
    max_ttl_minutes: int,
) -> tuple[dict[str, Any] | None, str | None]:
    ctype = str(control.get("type") or "")
    if ctype not in ALLOWED_CONTROL_TYPES:
        return None, f"unsupported_control_type:{ctype or 'missing'}"
    if control.get("namespace") in (None, ""):
        return None, "missing_namespace"
    active, inactive_reason = _active_control(control, now, namespace)
    if not active:
        return None, inactive_reason
    generated = parse_utc(control.get("generated_at_utc"))
    expires = parse_utc(control.get("expires_at_utc"))
    if generated is None:
        return None, "missing_or_invalid_generated_at_utc"
    if generated > now + timedelta(seconds=MAX_CONTROL_CLOCK_SKEW_SECONDS):
        return None, "generated_at_utc_in_future"
    if expires is None:
        return None, "missing_or_invalid_expires_at_utc"
    if expires <= generated:
        return None, "expires_at_not_after_generated_at"
    ttl = (expires - generated).total_seconds() / 60.0
    if ttl > max(1, int(max_ttl_minutes)):
        return None, f"ttl_exceeds_max:{ttl:.1f}>{int(max_ttl_minutes)}"
    evidence = control.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return None, "missing_evidence"
    sanitized = dict(control)
    sanitized["type"] = ctype
    sanitized.setdefault("control_id", f"{ctype}:{control.get('namespace') or '*'}:{control.get('symbol') or '*'}:{control.get('sleeve') or '*'}")
    sanitized["accepted_at_utc"] = iso_utc(now)
    if ctype == "risk_multiplier":
        try:
            multiplier = float(control.get("multiplier"))
        except (TypeError, ValueError):
            return None, "invalid_risk_multiplier"
        if multiplier > 1.0:
            return None, "risk_multiplier_above_one_forbidden"
        if multiplier < 0.0:
            return None, "risk_multiplier_below_zero_forbidden"
        sanitized["multiplier"] = multiplier
    return sanitized, None


def validate_control_state(
    state: Mapping[str, Any] | None,
    *,
    now: datetime | None = None,
    namespace: str | None = None,
    max_ttl_minutes: int = 120,
) -> tuple[bool, dict[str, Any]]:
    ts = now or utc_now()
    issues: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    if not isinstance(state, Mapping):
        return False, {
            "schema": AI_COMPANION_CONTROL_SCHEMA,
            "enabled": False,
            "active": False,
            "issues": [{"code": "missing_control_state"}],
            "accepted_controls": [],
            "rejected_controls": [],
        }
    if state.get("schema") != AI_COMPANION_CONTROL_SCHEMA:
        issues.append({"code": "schema_mismatch", "value": state.get("schema")})
    if state.get("runtime_effect_boundary") != RUNTIME_EFFECT_BOUNDARY:
        issues.append({"code": "runtime_effect_boundary_mismatch", "value": state.get("runtime_effect_boundary")})
    authority = str(state.get("authority_level") or "observe")
    if authority not in ALLOWED_AUTHORITY_LEVELS:
        issues.append({"code": "invalid_authority_level", "value": authority})
    generated = parse_utc(state.get("generated_at_utc"))
    expires = parse_utc(state.get("expires_at_utc"))
    if generated is None:
        issues.append({"code": "missing_or_invalid_state_generated_at_utc"})
    elif generated > ts + timedelta(seconds=MAX_CONTROL_CLOCK_SKEW_SECONDS):
        issues.append({
            "code": "state_generated_at_utc_in_future",
            "generated_at_utc": state.get("generated_at_utc"),
        })
    if expires is None:
        issues.append({"code": "missing_or_invalid_state_expires_at_utc"})
    elif expires <= ts:
        issues.append({"code": "state_expired", "expires_at_utc": state.get("expires_at_utc")})
    if generated is not None and expires is not None:
        if expires <= generated:
            issues.append({"code": "state_expires_at_not_after_generated_at"})
        else:
            ttl = (expires - generated).total_seconds() / 60.0
            if ttl > max(1, int(max_ttl_minutes)):
                issues.append({
                    "code": "state_ttl_exceeds_max",
                    "ttl_minutes": round(ttl, 3),
                    "max_ttl_minutes": int(max_ttl_minutes),
                })
    controls = state.get("controls")
    if controls is None:
        controls = []
    if not isinstance(controls, list):
        issues.append({"code": "controls_not_list"})
        controls = []
    for index, control in enumerate(controls):
        if not isinstance(control, Mapping):
            rejected.append({"index": index, "reason": "control_not_object"})
            continue
        accepted_control, reject_reason = _sanitize_control(
            control,
            now=ts,
            namespace=namespace,
            max_ttl_minutes=max_ttl_minutes,
        )
        if accepted_control is None:
            rejected.append({"index": index, "control_id": control.get("control_id"), "reason": reject_reason})
        else:
            accepted.append(accepted_control)
    active = not issues and authority in APPLIED_AUTHORITY_LEVELS and bool(accepted)
    summary = {
        "schema": AI_COMPANION_CONTROL_SCHEMA,
        "enabled": True,
        "active": active,
        "authority_level": authority,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "issues": issues,
        "accepted_controls": accepted,
        "rejected_controls": rejected,
        "active_control_count": len(accepted) if authority in APPLIED_AUTHORITY_LEVELS and not issues else 0,
        "loaded_generated_at_utc": state.get("generated_at_utc"),
        "loaded_expires_at_utc": state.get("expires_at_utc"),
    }
    return not issues, summary


@dataclass(frozen=True)
class ActiveControl:
    control_id: str
    type: str
    reason: str
    control: Mapping[str, Any]


class AICompanionRuntimeGate:
    """Runtime view over the latest validated AI companion control state."""

    def __init__(self, config: Mapping[str, Any] | None, repo_root: str | Path, namespace: str | None):
        self.config = config or {}
        self.repo_root = Path(repo_root)
        self.namespace = namespace
        self.enabled = config_bool(config, "enabled", False)
        self.authority_level = str(config_value(config, "authority_level", "observe") or "observe")
        self.control_state_path = str(config_value(config, "control_state_path", DEFAULT_CONTROL_STATE_PATH))
        self.fail_closed_on_issue = config_bool(
            config,
            "fail_closed_on_issue",
            self.authority_level in APPLIED_AUTHORITY_LEVELS,
        )
        try:
            self.max_ttl_minutes = int(config_value(config, "max_control_ttl_minutes", 120) or 120)
        except (TypeError, ValueError):
            self.max_ttl_minutes = 120

    def snapshot(self, now: datetime | None = None) -> dict[str, Any]:
        if not self.enabled:
            return {
                "schema": AI_COMPANION_CONTROL_SCHEMA,
                "enabled": False,
                "active": False,
                "authority_level": self.authority_level,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "accepted_controls": [],
                "rejected_controls": [],
                "issues": [],
            }
        state_path = self.repo_root / self.control_state_path
        loaded = load_control_state(self.repo_root, self.control_state_path)
        if loaded is None:
            issue_code = "control_state_unreadable" if state_path.exists() else "control_state_absent"
            return {
                "schema": AI_COMPANION_CONTROL_SCHEMA,
                "enabled": True,
                "active": False,
                "authority_level": self.authority_level,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "accepted_controls": [],
                "rejected_controls": [],
                "issues": [{"code": issue_code, "path": self.control_state_path}],
                "ok": False,
                "control_state_path": self.control_state_path,
                "fail_closed_new_entries": (
                    self.fail_closed_on_issue
                    and self.authority_level in APPLIED_AUTHORITY_LEVELS
                ),
            }
        ok, summary = validate_control_state(
            loaded,
            now=now,
            namespace=self.namespace,
            max_ttl_minutes=self.max_ttl_minutes,
        )
        summary["enabled"] = True
        if summary.get("authority_level") != self.authority_level:
            loaded_authority = summary.get("authority_level")
            if self.authority_level in APPLIED_AUTHORITY_LEVELS:
                issues = summary.get("issues")
                if not isinstance(issues, list):
                    issues = []
                issues.append({
                    "code": "authority_level_mismatch",
                    "configured_authority_level": self.authority_level,
                    "loaded_authority_level": loaded_authority,
                })
                summary["issues"] = issues
                summary["active"] = False
                summary["active_control_count"] = 0
                ok = False
            # Runtime config remains the authority; a stale file cannot promote itself.
            summary["authority_level"] = self.authority_level
            if self.authority_level not in APPLIED_AUTHORITY_LEVELS:
                summary["active"] = False
                summary["active_control_count"] = 0
        summary["ok"] = ok
        summary["control_state_path"] = self.control_state_path
        summary["fail_closed_new_entries"] = (
            self.fail_closed_on_issue
            and self.authority_level in APPLIED_AUTHORITY_LEVELS
            and bool(summary.get("issues"))
        )
        return summary

    @staticmethod
    def _accepted(snapshot: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        if not snapshot.get("enabled") or not snapshot.get("active"):
            return []
        controls = snapshot.get("accepted_controls")
        return controls if isinstance(controls, list) else []

    def control_state_issue_pause(self, snapshot: Mapping[str, Any]) -> ActiveControl | None:
        if not snapshot.get("enabled"):
            return None
        if self.authority_level not in APPLIED_AUTHORITY_LEVELS or not self.fail_closed_on_issue:
            return None
        if not snapshot.get("fail_closed_new_entries"):
            return None
        issues = snapshot.get("issues")
        issue_codes = [
            str(item.get("code") or "unknown")
            for item in issues
            if isinstance(item, Mapping)
        ] if isinstance(issues, list) else []
        reason = "ai_companion_control_state_issue"
        if issue_codes:
            reason = f"{reason}:{','.join(sorted(set(issue_codes)))}"
        return ActiveControl(
            control_id="ai_companion_control_state_issue",
            type="pause_new_entries",
            reason=reason,
            control={
                "type": "pause_new_entries",
                "reason": reason,
                "issues": issues if isinstance(issues, list) else [],
                "control_state_path": snapshot.get("control_state_path") or self.control_state_path,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            },
        )

    def pause_new_entries(self, snapshot: Mapping[str, Any]) -> ActiveControl | None:
        for control in self._accepted(snapshot):
            if control.get("type") == "pause_new_entries":
                return ActiveControl(
                    control_id=str(control.get("control_id") or "pause_new_entries"),
                    type="pause_new_entries",
                    reason=str(control.get("reason") or "ai_companion_pause_new_entries"),
                    control=control,
                )
        return None

    def cooldown_for(
        self,
        snapshot: Mapping[str, Any],
        *,
        symbol: str | None,
        sleeve: str | None,
    ) -> ActiveControl | None:
        for control in self._accepted(snapshot):
            if control.get("type") != "symbol_sleeve_cooldown":
                continue
            if _match(symbol, control.get("symbol")) and _match(sleeve, control.get("sleeve")):
                return ActiveControl(
                    control_id=str(control.get("control_id") or "symbol_sleeve_cooldown"),
                    type="symbol_sleeve_cooldown",
                    reason=str(control.get("reason") or "ai_companion_symbol_sleeve_cooldown"),
                    control=control,
                )
        return None

    def risk_multiplier_for(
        self,
        snapshot: Mapping[str, Any],
        *,
        symbol: str | None,
        sleeve: str | None,
    ) -> ActiveControl | None:
        best: ActiveControl | None = None
        for control in self._accepted(snapshot):
            if control.get("type") != "risk_multiplier":
                continue
            if not (_match(symbol, control.get("symbol")) and _match(sleeve, control.get("sleeve"))):
                continue
            current = float(control.get("multiplier", 1.0))
            previous = float(best.control.get("multiplier", 1.0)) if best else 1.0
            if best is None or current < previous:
                best = ActiveControl(
                    control_id=str(control.get("control_id") or "risk_multiplier"),
                    type="risk_multiplier",
                    reason=str(control.get("reason") or "ai_companion_risk_multiplier"),
                    control=control,
                )
        return best

    @staticmethod
    def adjusted_unit(unit: Mapping[str, Any], multiplier_control: ActiveControl | None) -> dict[str, Any]:
        cloned = dict(unit)
        if multiplier_control is None:
            return cloned
        multiplier = float(multiplier_control.control.get("multiplier", 1.0))
        for key in ("risk_pct_per_trade", "unit_risk_pct"):
            if cloned.get(key) is None:
                continue
            try:
                cloned[key] = max(0.0, float(cloned.get(key) or 0.0) * multiplier)
            except (TypeError, ValueError):
                pass
        cloned["ai_companion_risk_multiplier"] = multiplier
        cloned["ai_companion_control_id"] = multiplier_control.control_id
        cloned["ai_companion_reason"] = multiplier_control.reason
        return cloned
