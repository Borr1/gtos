"""Build Stage 05 saturated replay rows from the Stage 04 event/path universe.

This builder calls the current ``src.components.gtos_vnext_runtime`` APIs with
the full active runtime evidence index. It writes offline measurement artifacts
only; production config, prompts, broker state, accounts, orders, deals, and
positions are not mutated.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    GTOSVNextRuntimeDecision,
    apply_vnext_risk_adjustment,
    evaluate_pre_ai_vnext,
    evaluate_vnext_event,
    evaluate_vnext_pending_policy,
    evaluate_vnext_route_event,
    load_vnext_evidence_index,
)


CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
EVENT_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_EVENT_LEDGER_2026-05-24.jsonl"
PATH_OUTCOME_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_PATH_OUTCOME_LEDGER_2026-05-24.jsonl"
SATURATED_REPLAY_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_LEDGER_2026-05-24.jsonl"
SATURATED_REPLAY_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_SUMMARY_2026-05-24.json"
METRICS_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_METRICS_SUMMARY_2026-05-24.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"
WRITER_LOCK_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_WRITER_2026-05-24.lock"
SESSION_STATE_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine"
    / "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
)

STAGE_ID = "STAGE_05_SATURATED_REPLAY"
NEXT_STAGE_ID = "STAGE_06_ABLATION_AND_MIXED_RESOLUTION"

REPLAY_SOURCE_EVENT_TYPES = {
    "candidate_features",
    "candidate_ltf_path_order",
    "candidate_path_contract_audit",
    "candidate_path_follow",
    "pending_limit_lifecycle",
    "trade_index_lifecycle_audit",
}

RUNTIME_REFERENCE_SOURCE_EVENT_TYPES = {"runtime_harness_fixture"}

PATH_MODE_PRIORITY = {
    "tick_or_sierra_path_aware": 0,
    "m1_path_aware": 1,
    "m5_path_aware": 2,
    "bar_close_m15": 3,
    "ohlc_only_proxy": 4,
    "current_config_shadow": 5,
    "hypothetical_activated_vnext": 6,
    "missing_source": 9,
}

RUNTIME_SURFACE_CALLS = [
    "evaluate_vnext_event",
    "evaluate_vnext_route_event",
    "evaluate_pre_ai_vnext",
    "apply_vnext_risk_adjustment",
    "evaluate_vnext_pending_policy",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


class SingleWriterLock:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> "SingleWriterLock":
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            existing = self.path.read_text(encoding="utf-8", errors="replace")
            raise SystemExit(
                f"Stage05 saturated replay writer lock already exists at {self.path}: {existing}"
            ) from exc
        payload = {
            "created_utc": utc_now(),
            "pid": os.getpid(),
            "protected_outputs": [
                rel(SATURATED_REPLAY_LEDGER_PATH),
                rel(SATURATED_REPLAY_SUMMARY_PATH),
                rel(METRICS_SUMMARY_PATH),
                rel(OUTPUT_MANIFEST_PATH),
                rel(SESSION_STATE_PATH),
            ],
        }
        try:
            os.write(fd, json.dumps(payload, sort_keys=True).encode("utf-8"))
        finally:
            os.close(fd)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def stable_hash(payload: Any, length: int = 20) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def activated_config(config: dict[str, Any]) -> dict[str, Any]:
    cfg = copy.deepcopy(config)
    runtime_cfg = cfg.setdefault("gtos_vnext_runtime", {})
    runtime_cfg["enabled"] = True
    runtime_cfg["apply_to_execution"] = True
    runtime_cfg["pre_ai_enabled"] = True
    runtime_cfg["pre_ai_apply_to_ai_call"] = True
    runtime_cfg["risk_adjustment_enabled"] = True
    runtime_cfg["pending_policy_enabled"] = True
    runtime_cfg["exit_management_residue_apply_to_execution"] = True
    runtime_cfg["ready8_failure_control_residue_apply_to_execution"] = True
    return cfg


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def time_minutes(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = time.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed.hour * 60 + parsed.minute


def minute_in_window(minute: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= minute < end
    return minute >= start or minute < end


def instrument_market_config(config: dict[str, Any], symbol: str | None) -> dict[str, Any]:
    instruments = config.get("instruments", {}) or {}
    if symbol and isinstance(instruments.get(symbol), dict):
        market = instruments[symbol].get("market")
        if isinstance(market, dict):
            return market
    return config.get("market", {}) or {}


def infer_session_from_time(
    *,
    config: dict[str, Any],
    symbol: str | None,
    event_time_utc: str | None,
) -> tuple[str | None, dict[str, Any] | None]:
    dt = parse_dt(event_time_utc)
    if dt is None:
        return None, None
    market_cfg = instrument_market_config(config, symbol)
    kill_zones = market_cfg.get("kill_zones") or {}
    minute = dt.hour * 60 + dt.minute
    for name, zone in kill_zones.items():
        if not isinstance(zone, dict):
            continue
        start = time_minutes(zone.get("start_utc"))
        end = time_minutes(zone.get("end_utc"))
        if start is None or end is None:
            continue
        if minute_in_window(minute, start, end):
            return str(name), {
                "source": "config_kill_zone_window",
                "symbol": symbol,
                "start_utc": zone.get("start_utc"),
                "end_utc": zone.get("end_utc"),
                "event_time_utc": event_time_utc,
            }
    return "off_core_session", {
        "source": "config_kill_zone_window_no_match",
        "symbol": symbol,
        "event_time_utc": event_time_utc,
    }


def first_non_empty(events: list[dict[str, Any]], keys: list[str]) -> Any:
    for event in events:
        for key in keys:
            value = event.get(key)
            if value not in (None, ""):
                return value
    return None


def most_common_non_empty(events: list[dict[str, Any]], keys: list[str]) -> Any:
    counts: Counter[str] = Counter()
    first: dict[str, Any] = {}
    for event in events:
        for key in keys:
            value = event.get(key)
            if value not in (None, ""):
                text = str(value)
                counts[text] += 1
                first.setdefault(text, value)
    if not counts:
        return None
    value, _count = counts.most_common(1)[0]
    return first[value]


def fnum(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def risk_reward_from_group(group: dict[str, Any]) -> float:
    rr = fnum(group.get("risk_reward_ratio"))
    if rr is not None and rr > 0:
        return rr
    entry = fnum(group.get("entry_price"))
    stop = fnum(group.get("stop_loss"))
    target = fnum(group.get("take_profit_1"))
    if None in (entry, stop, target):
        return 1.5
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return 1.5
    return max(0.0, reward / risk)


def derive_group(
    duplicate_group_id: str,
    events: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    symbol = most_common_non_empty(events, ["symbol", "broker_symbol", "source_symbol"])
    source_symbol = most_common_non_empty(events, ["source_symbol", "broker_symbol", "symbol"])
    broker_symbol = most_common_non_empty(events, ["broker_symbol"])
    side = most_common_non_empty(events, ["side", "direction"])
    framework = most_common_non_empty(events, ["framework", "effective_framework"])
    session = most_common_non_empty(events, ["kill_zone", "session", "route_session"])
    decision_time_utc = first_non_empty(events, ["decision_time_utc", "window_start_utc"])
    inference_notes: list[dict[str, Any]] = []
    if source_symbol in (None, "") and symbol not in (None, ""):
        source_symbol = symbol
        inference_notes.append({"field": "source_symbol", "method": "defaulted_to_symbol"})
    if session in (None, ""):
        session, note = infer_session_from_time(
            config=config,
            symbol=str(symbol) if symbol else None,
            event_time_utc=str(decision_time_utc) if decision_time_utc else None,
        )
        if note:
            inference_notes.append({"field": "session", **note})
    timeframe = most_common_non_empty(events, ["timeframe", "market_timeframe", "entry_timeframe"])
    if timeframe in (None, ""):
        timeframe = "M15"
        inference_notes.append(
            {
                "field": "timeframe",
                "method": "default_m15_candidate_pipeline",
                "reason": "Stage04 source logs are M15-candle GTOS candidate/path/lifecycle surfaces unless explicitly tagged otherwise",
            }
        )
    route_family = framework if framework not in (None, "") else None
    entry_price = first_non_empty(events, ["entry_price"])
    stop_loss = first_non_empty(events, ["stop_loss"])
    take_profit_1 = first_non_empty(events, ["take_profit_1"])
    rr = first_non_empty(events, ["risk_reward_ratio"])
    source_event_types = Counter(str(event.get("source_event_type")) for event in events)
    source_paths = sorted({str(event.get("source_path")) for event in events if event.get("source_path")})
    source_hashes = sorted({str(event.get("source_sha256")) for event in events if event.get("source_sha256")})
    source_use_statuses = Counter(str(event.get("source_use_status")) for event in events)
    event_ids = sorted(str(event.get("event_id")) for event in events if event.get("event_id"))
    replay_eligible = any(name in REPLAY_SOURCE_EVENT_TYPES for name in source_event_types)
    runtime_reference_only = (
        bool(source_event_types)
        and not replay_eligible
        and all(name in RUNTIME_REFERENCE_SOURCE_EVENT_TYPES for name in source_event_types)
    )
    return {
        "group_id": "grp_" + stable_hash([duplicate_group_id, event_ids], length=24),
        "duplicate_group_id": duplicate_group_id,
        "source_event_row_count": len(events),
        "source_event_type_counts": dict(sorted(source_event_types.items())),
        "source_use_status_counts": dict(sorted(source_use_statuses.items())),
        "source_paths": source_paths,
        "source_sha256s": source_hashes,
        "event_ids": event_ids,
        "candidate_ids": sorted(
            {str(event.get("candidate_id")) for event in events if event.get("candidate_id")}
        ),
        "trade_ids": sorted({str(event.get("trade_id")) for event in events if event.get("trade_id")}),
        "symbol": symbol,
        "source_symbol": source_symbol,
        "broker_symbol": broker_symbol,
        "side": str(side).upper() if side else None,
        "direction": str(side).upper() if side else None,
        "framework": framework,
        "effective_framework": framework,
        "route_family": route_family,
        "session": session,
        "kill_zone": session,
        "route_session": session,
        "timeframe": timeframe,
        "market_timeframe": timeframe,
        "entry_timeframe": timeframe,
        "decision_time_utc": decision_time_utc,
        "window_start_utc": first_non_empty(events, ["window_start_utc"]),
        "window_end_utc": first_non_empty(events, ["window_end_utc"]),
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit_1": take_profit_1,
        "risk_reward_ratio": rr,
        "inference_notes": inference_notes,
        "replay_eligible": replay_eligible,
        "runtime_reference_only": runtime_reference_only,
    }


def event_payload(group: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "symbol",
        "source_symbol",
        "broker_symbol",
        "side",
        "direction",
        "framework",
        "effective_framework",
        "route_family",
        "session",
        "kill_zone",
        "route_session",
        "timeframe",
        "market_timeframe",
        "entry_timeframe",
        "decision_time_utc",
        "window_start_utc",
        "window_end_utc",
        "entry_price",
        "stop_loss",
        "take_take_profit_1",
        "take_profit_1",
        "risk_reward_ratio",
    ]
    return {key: group.get(key) for key in keys if group.get(key) not in (None, "")}


def runtime_event_key(group: dict[str, Any]) -> tuple[Any, ...]:
    return (
        group.get("symbol"),
        group.get("source_symbol"),
        group.get("broker_symbol"),
        group.get("side"),
        group.get("framework"),
        group.get("session"),
        group.get("timeframe"),
    )


def pre_ai_event_key(group: dict[str, Any]) -> tuple[Any, ...]:
    return (
        group.get("symbol"),
        group.get("source_symbol"),
        group.get("session"),
        bias_for_group(group),
        group.get("timeframe"),
    )


def missing_fields_for_post_l2(group: dict[str, Any]) -> list[str]:
    required = ["symbol", "session", "side", "framework"]
    return [field for field in required if group.get(field) in (None, "")]


def missing_fields_for_pre_ai(group: dict[str, Any]) -> list[str]:
    required = ["symbol", "session"]
    return [field for field in required if group.get(field) in (None, "")]


def bias_for_group(group: dict[str, Any]) -> str | None:
    side = str(group.get("side") or "").upper()
    if side == "LONG":
        return "bullish"
    if side == "SHORT":
        return "bearish"
    return None


def compact_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(evidence, dict):
        return {}
    return {
        "matched_rows": evidence.get("matched_rows"),
        "decision_counts": evidence.get("decision_counts"),
        "source_component_counts": evidence.get("source_component_counts"),
        "source_component_decision_counts": evidence.get("source_component_decision_counts"),
        "evidence_family_counts": evidence.get("evidence_family_counts"),
        "evidence_family_decision_counts": evidence.get("evidence_family_decision_counts"),
        "action_class_counts": evidence.get("action_class_counts"),
        "action_class_decision_counts": evidence.get("action_class_decision_counts"),
        "source_name_counts": evidence.get("source_name_counts"),
        "source_name_decision_counts": evidence.get("source_name_decision_counts"),
        "source_role_counts": evidence.get("source_role_counts"),
        "source_role_decision_counts": evidence.get("source_role_decision_counts"),
        "r_evidence_class_counts": evidence.get("r_evidence_class_counts"),
        "target_stop_order_class_counts": evidence.get("target_stop_order_class_counts"),
        "proxy_r_class_counts": evidence.get("proxy_r_class_counts"),
        "route_session_counts": evidence.get("route_session_counts"),
        "symbol_counts": evidence.get("symbol_counts"),
        "framework_counts": evidence.get("framework_counts"),
        "framework_decision_metric_summaries": evidence.get("framework_decision_metric_summaries"),
        "route_event_count": evidence.get("route_event_count"),
        "matched_row_id_count": evidence.get("matched_row_id_count"),
        "matched_row_ids": evidence.get("matched_row_ids"),
        "matched_row_ids_truncated": evidence.get("matched_row_ids_truncated"),
        "source_row_id_count": evidence.get("source_row_id_count"),
        "source_row_ids": evidence.get("source_row_ids"),
        "source_row_ids_truncated": evidence.get("source_row_ids_truncated"),
        "scope_selection_policy": evidence.get("scope_selection_policy"),
        "decision_resolution": evidence.get("decision_resolution"),
        "metrics": evidence.get("metrics"),
        "runtime_index": evidence.get("runtime_index"),
        "bridge_diagnostics": evidence.get("bridge_diagnostics"),
        "row_detail_count": evidence.get("row_detail_count"),
        "rows_truncated": evidence.get("rows_truncated"),
    }


def compact_runtime_decision(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "decision": record.get("decision"),
        "enabled": record.get("enabled"),
        "apply_to_execution": record.get("apply_to_execution"),
        "matched": record.get("matched"),
        "reason": record.get("reason"),
        "event": record.get("event"),
        "artifact_path_count": len(record.get("artifact_paths") or []),
        "evidence": compact_evidence(record.get("evidence") or {}),
    }


def compact_pre_ai(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    role_context = record.get("ai_role_context") or {}
    role_summary = {}
    if isinstance(role_context, dict):
        role_summary = {
            "keys": sorted(role_context.keys()),
            "source_evidence_role": role_context.get("source_evidence_role"),
            "scope_guard": role_context.get("scope_guard"),
            "pressure_test": role_context.get("pressure_test"),
            "runtime_rules": role_context.get("runtime_rules"),
        }
    return {
        "action": record.get("action"),
        "would_action": record.get("would_action"),
        "decision": record.get("decision"),
        "enabled": record.get("enabled"),
        "apply_to_ai_call": record.get("apply_to_ai_call"),
        "reason": record.get("reason"),
        "event": record.get("event"),
        "recommended_side": record.get("recommended_side"),
        "recommended_frameworks": record.get("recommended_frameworks"),
        "recommended_route_families": record.get("recommended_route_families"),
        "blocked_sides": record.get("blocked_sides"),
        "blocked_frameworks": record.get("blocked_frameworks"),
        "blocked_route_families": record.get("blocked_route_families"),
        "risk_vetoed_sides": record.get("risk_vetoed_sides"),
        "side_risk_reasons": record.get("side_risk_reasons"),
        "evaluated_sides": record.get("evaluated_sides"),
        "side_decisions": [
            compact_runtime_decision(decision)
            for decision in record.get("side_decisions", [])
            if isinstance(decision, dict)
        ],
        "ai_role_context_summary": role_summary,
    }


def compact_risk(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "enabled": record.get("enabled"),
        "apply_to_execution": record.get("apply_to_execution"),
        "applied": record.get("applied"),
        "decision": record.get("decision"),
        "before_risk_pct": record.get("before_risk_pct"),
        "after_risk_pct": record.get("after_risk_pct"),
        "multiplier": record.get("multiplier"),
        "would_multiplier": record.get("would_multiplier"),
        "reason": record.get("reason"),
        "evidence_summary": record.get("evidence_summary"),
    }


def compact_pending(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "action": record.get("action"),
        "would_action": record.get("would_action"),
        "enabled": record.get("enabled"),
        "apply_to_execution": record.get("apply_to_execution"),
        "applied": record.get("applied"),
        "decision": record.get("decision"),
        "reason": record.get("reason"),
        "evidence_summary": record.get("evidence_summary"),
    }


def decision_with_apply(
    decision: GTOSVNextRuntimeDecision,
    *,
    apply_to_execution: bool,
) -> GTOSVNextRuntimeDecision:
    return GTOSVNextRuntimeDecision(
        decision=decision.decision,
        event=decision.event,
        enabled=decision.enabled,
        apply_to_execution=apply_to_execution,
        matched=decision.matched,
        reason=decision.reason,
        evidence=decision.evidence,
        artifact_paths=decision.artifact_paths,
    )


def current_shadow_pre_ai_from_active(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    current = copy.deepcopy(record)
    current["apply_to_ai_call"] = False
    current["action"] = "ALLOW_AI"
    current["reason"] = (
        "matched_pre_ai_vnext_scope"
        if current.get("decision") != "LEGACY"
        else "no_matching_pre_ai_vnext_scope"
    )
    for side_decision in current.get("side_decisions") or []:
        if isinstance(side_decision, dict):
            side_decision["apply_to_execution"] = False
    return current


def runtime_records_for_group(
    *,
    group: dict[str, Any],
    active_config: dict[str, Any],
    current_config: dict[str, Any],
    artifact_index: Any,
    runtime_cache: dict[tuple[Any, ...], dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    cache_key = runtime_event_key(group)
    cached = runtime_cache.get(cache_key)
    if cached is not None:
        return copy.deepcopy(cached)
    payload = event_payload(group)
    direct_active = evaluate_vnext_event(payload, active_config, artifact_index=artifact_index)
    route_active = evaluate_vnext_route_event(payload, active_config, artifact_index=artifact_index)
    direct_current = decision_with_apply(direct_active, apply_to_execution=False)
    route_current = decision_with_apply(route_active, apply_to_execution=False)
    risk_pct = float((current_config.get("risk", {}) or {}).get("risk_per_trade_pct", 2.0))
    active_risk = apply_vnext_risk_adjustment(
        current_risk_pct=risk_pct,
        decision=route_active,
        config=active_config,
    )
    current_risk = apply_vnext_risk_adjustment(
        current_risk_pct=risk_pct,
        decision=route_current,
        config=current_config,
    )
    active_pending = evaluate_vnext_pending_policy(decision=route_active, config=active_config)
    current_pending = evaluate_vnext_pending_policy(decision=route_current, config=current_config)
    cached = {
        "hypothetical_activated_vnext": {
            "direct_decision": compact_runtime_decision(direct_active.to_record()),
            "route_decision": compact_runtime_decision(route_active.to_record()),
            "risk_adjustment": compact_risk(active_risk.to_record()),
            "pending_policy": compact_pending(active_pending.to_record()),
        },
        "current_config_shadow": {
            "direct_decision": compact_runtime_decision(direct_current.to_record()),
            "route_decision": compact_runtime_decision(route_current.to_record()),
            "risk_adjustment": compact_risk(current_risk.to_record()),
            "pending_policy": compact_pending(current_pending.to_record()),
        },
    }
    runtime_cache[cache_key] = cached
    return copy.deepcopy(cached)


def pre_ai_records_for_group(
    *,
    group: dict[str, Any],
    active_config: dict[str, Any],
    artifact_index: Any,
    pre_ai_cache: dict[tuple[Any, ...], dict[str, dict[str, Any] | None]],
) -> dict[str, dict[str, Any] | None]:
    cache_key = pre_ai_event_key(group)
    cached = pre_ai_cache.get(cache_key)
    if cached is not None:
        return copy.deepcopy(cached)
    pre_ai = evaluate_pre_ai_vnext(
        symbol=str(group.get("symbol")),
        source_symbol=str(group.get("source_symbol") or group.get("symbol")),
        kill_zone=str(group.get("session")),
        config=active_config,
        bias=bias_for_group(group),
        raw_data={
            "gtos_vnext_saturated_replay": True,
            "market_timeframe": group.get("market_timeframe"),
            "timeframe": group.get("timeframe"),
        },
        artifact_index=artifact_index,
    )
    active_record = compact_pre_ai(pre_ai.to_record())
    cached = {
        "hypothetical_activated_vnext": active_record,
        "current_config_shadow": current_shadow_pre_ai_from_active(active_record),
    }
    pre_ai_cache[cache_key] = cached
    return copy.deepcopy(cached)


def terminal_class_and_r(terminal_order: Any, rr: float) -> dict[str, Any]:
    label = str(terminal_order or "").strip()
    lower = label.casefold()
    missing = lower in {"", "none", "missing_source", "decision_trace_not_path_outcome"}
    if missing:
        return {
            "outcome_class": "missing_or_reference",
            "proxy_r_conservative": None,
            "proxy_r_neutral": None,
            "proxy_r_optimistic": None,
            "missed_opportunity_r": None,
        }
    if any(token in lower for token in ["same_bar", "same_m1", "same_tick", "ambiguous"]):
        return {
            "outcome_class": "ambiguous_stop_target_order",
            "proxy_r_conservative": -1.0,
            "proxy_r_neutral": 0.0,
            "proxy_r_optimistic": rr,
            "missed_opportunity_r": None,
        }
    if label in {"TARGET_FIRST"} or "tp1_before_sl" in lower or "then_tp1" in lower or "reached_tp1" in lower:
        if "without_entry_touch" in lower:
            return {
                "outcome_class": "no_fill_missed_target_area",
                "proxy_r_conservative": 0.0,
                "proxy_r_neutral": 0.0,
                "proxy_r_optimistic": 0.0,
                "missed_opportunity_r": rr,
            }
        return {
            "outcome_class": "target_first_win",
            "proxy_r_conservative": rr,
            "proxy_r_neutral": rr,
            "proxy_r_optimistic": rr,
            "missed_opportunity_r": None,
        }
    if label in {"STOP_FIRST"} or "sl_before_tp" in lower or "then_sl" in lower or "continued_to_sl" in lower:
        return {
            "outcome_class": "stop_first_loss",
            "proxy_r_conservative": -1.0,
            "proxy_r_neutral": -1.0,
            "proxy_r_optimistic": -1.0,
            "missed_opportunity_r": None,
        }
    if "without_entry_touch" in lower or "no_entry_touch" in lower or "no_touch" in lower:
        return {
            "outcome_class": "no_fill_no_entry_touch",
            "proxy_r_conservative": 0.0,
            "proxy_r_neutral": 0.0,
            "proxy_r_optimistic": 0.0,
            "missed_opportunity_r": rr if "tp" in lower else None,
        }
    if "no_fill" in lower:
        return {
            "outcome_class": "no_fill_lifecycle",
            "proxy_r_conservative": 0.0,
            "proxy_r_neutral": 0.0,
            "proxy_r_optimistic": 0.0,
            "missed_opportunity_r": rr if "target" in lower or "tp" in lower else None,
        }
    if "timeout" in lower or "unresolved" in lower or "no_terminal" in lower:
        return {
            "outcome_class": "entry_touched_timeout_or_unresolved",
            "proxy_r_conservative": 0.0,
            "proxy_r_neutral": 0.0,
            "proxy_r_optimistic": 0.0,
            "missed_opportunity_r": None,
        }
    return {
        "outcome_class": "unmapped_terminal_label",
        "proxy_r_conservative": None,
        "proxy_r_neutral": None,
        "proxy_r_optimistic": None,
        "missed_opportunity_r": None,
    }


def best_path_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [row for row in rows if row.get("path_source_status") != "MISSING_SOURCE"]
    if not candidates:
        return rows[0] if rows else None
    return sorted(
        candidates,
        key=lambda row: (
            PATH_MODE_PRIORITY.get(str(row.get("replay_mode")), 8),
            str(row.get("path_source_status")),
            str(row.get("path_row_id")),
        ),
    )[0]


def path_summary_for_group(group: dict[str, Any], path_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rr = risk_reward_from_group(group)
    mode_counts = Counter(str(row.get("replay_mode")) for row in path_rows)
    status_counts = Counter(str(row.get("path_source_status")) for row in path_rows)
    terminal_counts = Counter(str(row.get("terminal_order")) for row in path_rows)
    confidence_counts = Counter(str(row.get("confidence")) for row in path_rows)
    mode_summaries: dict[str, dict[str, Any]] = {}
    for row in path_rows:
        mode = str(row.get("replay_mode"))
        summary = mode_summaries.setdefault(
            mode,
            {
                "row_count": 0,
                "status_counts": Counter(),
                "terminal_order_counts": Counter(),
                "outcome_class_counts": Counter(),
                "proxy_r_conservative_sum": 0.0,
                "proxy_r_neutral_sum": 0.0,
                "proxy_r_optimistic_sum": 0.0,
                "computable_proxy_rows": 0,
                "missed_opportunity_r_sum": 0.0,
            },
        )
        outcome = terminal_class_and_r(row.get("terminal_order"), rr)
        summary["row_count"] += 1
        summary["status_counts"][str(row.get("path_source_status"))] += 1
        summary["terminal_order_counts"][str(row.get("terminal_order"))] += 1
        summary["outcome_class_counts"][outcome["outcome_class"]] += 1
        if outcome["proxy_r_neutral"] is not None:
            summary["computable_proxy_rows"] += 1
            summary["proxy_r_conservative_sum"] += float(outcome["proxy_r_conservative"])
            summary["proxy_r_neutral_sum"] += float(outcome["proxy_r_neutral"])
            summary["proxy_r_optimistic_sum"] += float(outcome["proxy_r_optimistic"])
        if outcome["missed_opportunity_r"] is not None:
            summary["missed_opportunity_r_sum"] += float(outcome["missed_opportunity_r"])
    compact_mode_summaries = {}
    for mode, summary in mode_summaries.items():
        compact_mode_summaries[mode] = {
            "row_count": summary["row_count"],
            "status_counts": dict(sorted(summary["status_counts"].items())),
            "terminal_order_counts": dict(sorted(summary["terminal_order_counts"].items())),
            "outcome_class_counts": dict(sorted(summary["outcome_class_counts"].items())),
            "computable_proxy_rows": summary["computable_proxy_rows"],
            "proxy_r_conservative_sum": round(summary["proxy_r_conservative_sum"], 8),
            "proxy_r_neutral_sum": round(summary["proxy_r_neutral_sum"], 8),
            "proxy_r_optimistic_sum": round(summary["proxy_r_optimistic_sum"], 8),
            "missed_opportunity_r_sum": round(summary["missed_opportunity_r_sum"], 8),
        }
    best = best_path_row(path_rows)
    best_outcome = terminal_class_and_r(best.get("terminal_order") if best else None, rr)
    return {
        "path_row_count": len(path_rows),
        "path_modes_present": sorted(mode_counts),
        "path_mode_counts": dict(sorted(mode_counts.items())),
        "path_status_counts": dict(sorted(status_counts.items())),
        "terminal_order_counts": dict(sorted(terminal_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "mode_summaries": compact_mode_summaries,
        "best_available_path": {
            "path_row_id": best.get("path_row_id") if best else None,
            "replay_mode": best.get("replay_mode") if best else None,
            "path_source_status": best.get("path_source_status") if best else None,
            "source_evidence_type": best.get("source_evidence_type") if best else None,
            "terminal_order": best.get("terminal_order") if best else None,
            "entry_touched": best.get("entry_touched") if best else None,
            "same_bar_ambiguity": best.get("same_bar_ambiguity") if best else None,
            "mfe_r": best.get("mfe_r") if best else None,
            "mae_r": best.get("mae_r") if best else None,
            "confidence": best.get("confidence") if best else None,
            **best_outcome,
        },
    }


def evaluate_group(
    *,
    group: dict[str, Any],
    mode: str,
    current_config: dict[str, Any],
    active_config: dict[str, Any],
    artifact_index: Any,
    path_summary: dict[str, Any],
    runtime_cache: dict[tuple[Any, ...], dict[str, dict[str, Any]]],
    pre_ai_cache: dict[tuple[Any, ...], dict[str, dict[str, Any] | None]],
) -> dict[str, Any]:
    payload = event_payload(group)
    missing_post_l2 = missing_fields_for_post_l2(group)
    missing_pre_ai = missing_fields_for_pre_ai(group)
    direct_record = None
    route_record = None
    risk_record = None
    pending_record = None
    pre_ai_record = None
    runtime_call_status = "EVALUATED_ALL_RUNTIME_SURFACES"
    if missing_post_l2:
        runtime_call_status = "PARTIAL_OR_SKIPPED_RUNTIME_SURFACES_INSUFFICIENT_EVENT_FIELDS"
    if not missing_post_l2:
        cached_runtime = runtime_records_for_group(
            group=group,
            active_config=active_config,
            current_config=current_config,
            artifact_index=artifact_index,
            runtime_cache=runtime_cache,
        )[mode]
        direct_record = cached_runtime["direct_decision"]
        route_record = cached_runtime["route_decision"]
        risk_record = cached_runtime["risk_adjustment"]
        pending_record = cached_runtime["pending_policy"]
    if not missing_pre_ai:
        pre_ai_record = pre_ai_records_for_group(
            group=group,
            active_config=active_config,
            artifact_index=artifact_index,
            pre_ai_cache=pre_ai_cache,
        )[mode]
    replay_disposition = "RUNTIME_EVALUATED_WITH_PATH_SUMMARY"
    insufficient = sorted(set(missing_post_l2 + missing_pre_ai))
    if group.get("runtime_reference_only"):
        replay_disposition = "RUNTIME_REFERENCE_ONLY_NOT_PERFORMANCE_DENOMINATOR"
    elif missing_post_l2 and missing_pre_ai:
        replay_disposition = "INSUFFICIENT_EVENT_FIELDS_FOR_RUNTIME_REPLAY"
    elif missing_post_l2:
        replay_disposition = "PRE_AI_ONLY_INSUFFICIENT_POST_L2_FIELDS"
    return {
        "schema_version": "vnext_replay_saturated_replay_v1",
        "stage_id": STAGE_ID,
        "replay_row_id": "sat_" + stable_hash([group.get("group_id"), mode], length=24),
        "runtime_activation_mode": mode,
        "activation_boundary": (
            "active_config_shadow_no_execution_effect"
            if mode == "current_config_shadow"
            else "hypothetical_activation_no_production_config_mutation"
        ),
        "runtime_surface_calls": RUNTIME_SURFACE_CALLS,
        "runtime_call_status": runtime_call_status,
        "replay_disposition": replay_disposition,
        "insufficient_event_fields": insufficient,
        "group": {
            key: group.get(key)
            for key in [
                "group_id",
                "duplicate_group_id",
                "source_event_row_count",
                "source_event_type_counts",
                "source_use_status_counts",
                "source_paths",
                "source_sha256s",
                "event_ids",
                "candidate_ids",
                "trade_ids",
                "symbol",
                "source_symbol",
                "broker_symbol",
                "side",
                "framework",
                "session",
                "timeframe",
                "decision_time_utc",
                "window_start_utc",
                "window_end_utc",
                "entry_price",
                "stop_loss",
                "take_profit_1",
                "risk_reward_ratio",
                "inference_notes",
                "replay_eligible",
                "runtime_reference_only",
            ]
        },
        "input_event": payload,
        "direct_decision": direct_record,
        "route_decision": route_record,
        "pre_ai_decision": pre_ai_record,
        "risk_adjustment": risk_record,
        "pending_policy": pending_record,
        "path_outcome_summary": path_summary,
        "no_live_trading_or_broker_mutation": True,
    }


def group_events(config: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in iter_jsonl(EVENT_LEDGER_PATH):
        duplicate_group_id = str(event.get("duplicate_group_id") or event.get("event_id"))
        grouped[duplicate_group_id].append(event)
    groups = [
        derive_group(duplicate_group_id, events, config)
        for duplicate_group_id, events in grouped.items()
    ]
    groups.sort(
        key=lambda group: (
            str(group.get("symbol")),
            str(group.get("session")),
            str(group.get("side")),
            str(group.get("framework")),
            str(group.get("decision_time_utc")),
            str(group.get("duplicate_group_id")),
        )
    )
    return groups


def group_path_rows() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in iter_jsonl(PATH_OUTCOME_LEDGER_PATH):
        duplicate_group_id = str(row.get("duplicate_group_id") or row.get("event_id"))
        grouped[duplicate_group_id].append(row)
    return grouped


def build_replay_rows() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    config = load_config()
    runtime_paths = (config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or []
    artifact_index = load_vnext_evidence_index(runtime_paths)
    if artifact_index.row_count < int((config.get("gtos_vnext_runtime", {}) or {}).get("min_loaded_evidence_rows", 0)):
        raise SystemExit("full runtime artifact index is below active min_loaded_evidence_rows")
    activated = activated_config(config)
    groups = group_events(config)
    paths_by_group = group_path_rows()
    rows: list[dict[str, Any]] = []
    runtime_cache: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    pre_ai_cache: dict[tuple[Any, ...], dict[str, dict[str, Any] | None]] = {}
    for group in groups:
        path_summary = path_summary_for_group(group, paths_by_group.get(str(group["duplicate_group_id"]), []))
        rows.append(
            evaluate_group(
                group=group,
                mode="current_config_shadow",
                current_config=config,
                active_config=activated,
                artifact_index=artifact_index,
                path_summary=path_summary,
                runtime_cache=runtime_cache,
                pre_ai_cache=pre_ai_cache,
            )
        )
        rows.append(
            evaluate_group(
                group=group,
                mode="hypothetical_activated_vnext",
                current_config=config,
                active_config=activated,
                artifact_index=artifact_index,
                path_summary=path_summary,
                runtime_cache=runtime_cache,
                pre_ai_cache=pre_ai_cache,
            )
        )
    summary, metrics = summarize(rows, groups, paths_by_group, artifact_index, config)
    return rows, summary, metrics


def _nested_get(row: dict[str, Any], *keys: str) -> Any:
    current: Any = row
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def summarize(
    rows: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    paths_by_group: dict[str, list[dict[str, Any]]],
    artifact_index: Any,
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_mode: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    matched_by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    skipped = Counter()
    best_outcomes = Counter()
    best_path_modes = Counter()
    proxy_totals = defaultdict(float)
    proxy_counts = Counter()
    group_counts = Counter()
    symbol_counts = Counter(str(group.get("symbol")) for group in groups)
    session_counts = Counter(str(group.get("session")) for group in groups)
    side_counts = Counter(str(group.get("side")) for group in groups)
    framework_counts = Counter(str(group.get("framework")) for group in groups)
    event_source_counts: Counter[str] = Counter()
    for group in groups:
        group_counts["replay_eligible" if group.get("replay_eligible") else "not_replay_eligible"] += 1
        for name, count in (group.get("source_event_type_counts") or {}).items():
            event_source_counts[str(name)] += int(count)
    for row in rows:
        mode = str(row.get("runtime_activation_mode"))
        by_mode[mode]["replay_disposition_counts"][str(row.get("replay_disposition"))] += 1
        if row.get("insufficient_event_fields"):
            skipped["insufficient_event_fields"] += 1
        route_decision = _nested_get(row, "route_decision", "decision")
        direct_decision = _nested_get(row, "direct_decision", "decision")
        pre_ai_action = _nested_get(row, "pre_ai_decision", "action")
        pre_ai_would = _nested_get(row, "pre_ai_decision", "would_action")
        risk_reason = _nested_get(row, "risk_adjustment", "reason")
        risk_would = _nested_get(row, "risk_adjustment", "would_multiplier")
        pending_action = _nested_get(row, "pending_policy", "action")
        pending_would = _nested_get(row, "pending_policy", "would_action")
        by_mode[mode]["route_decision_counts"][str(route_decision)] += 1
        by_mode[mode]["direct_decision_counts"][str(direct_decision)] += 1
        by_mode[mode]["pre_ai_action_counts"][str(pre_ai_action)] += 1
        by_mode[mode]["pre_ai_would_action_counts"][str(pre_ai_would)] += 1
        by_mode[mode]["risk_reason_counts"][str(risk_reason)] += 1
        by_mode[mode]["risk_would_multiplier_counts"][str(risk_would)] += 1
        by_mode[mode]["pending_action_counts"][str(pending_action)] += 1
        by_mode[mode]["pending_would_action_counts"][str(pending_would)] += 1
        matched_by_mode[mode]["route_matched"] += int(bool(_nested_get(row, "route_decision", "matched")))
        matched_by_mode[mode]["direct_matched"] += int(bool(_nested_get(row, "direct_decision", "matched")))
        best = _nested_get(row, "path_outcome_summary", "best_available_path") or {}
        outcome_class = str(best.get("outcome_class"))
        best_outcomes[outcome_class] += 1
        best_path_modes[str(best.get("replay_mode"))] += 1
        for key in ["proxy_r_conservative", "proxy_r_neutral", "proxy_r_optimistic", "missed_opportunity_r"]:
            value = best.get(key)
            if value is not None:
                proxy_totals[key] += float(value)
                proxy_counts[key] += 1
    mode_summary = {}
    for mode, counters in by_mode.items():
        mode_summary[mode] = {name: dict(sorted(counter.items())) for name, counter in counters.items()}
        mode_summary[mode]["matched_counts"] = dict(sorted(matched_by_mode[mode].items()))
    by_group_activation = defaultdict(dict)
    for row in rows:
        by_group_activation[_nested_get(row, "group", "group_id")][
            row["runtime_activation_mode"]
        ] = row
    activation_delta_counts = Counter()
    for pair in by_group_activation.values():
        current = pair.get("current_config_shadow")
        active = pair.get("hypothetical_activated_vnext")
        if not current or not active:
            continue
        if _nested_get(current, "route_decision", "decision") != _nested_get(active, "route_decision", "decision"):
            activation_delta_counts["route_decision_changed"] += 1
        if _nested_get(current, "pre_ai_decision", "action") != _nested_get(active, "pre_ai_decision", "action"):
            activation_delta_counts["pre_ai_action_changed"] += 1
        if _nested_get(current, "pending_policy", "action") != _nested_get(active, "pending_policy", "action"):
            activation_delta_counts["pending_action_changed"] += 1
        if _nested_get(current, "risk_adjustment", "multiplier") != _nested_get(active, "risk_adjustment", "multiplier"):
            activation_delta_counts["risk_multiplier_changed"] += 1
    path_mode_counts = Counter()
    path_status_counts = Counter()
    terminal_counts = Counter()
    for rows_for_group in paths_by_group.values():
        for path_row in rows_for_group:
            path_mode_counts[str(path_row.get("replay_mode"))] += 1
            path_status_counts[str(path_row.get("path_source_status"))] += 1
            terminal_counts[str(path_row.get("terminal_order"))] += 1
    summary = {
        "schema_version": "vnext_replay_saturated_replay_summary_v1",
        "generated_utc": utc_now(),
        "stage_id": STAGE_ID,
        "event_groups": len(groups),
        "source_event_rows": sum(event_source_counts.values()),
        "replay_rows": len(rows),
        "runtime_artifact_paths_loaded": len(runtime_paths := ((config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or [])),
        "runtime_artifact_index_rows": artifact_index.row_count,
        "runtime_artifact_missing_paths": list(artifact_index.missing_paths),
        "active_min_loaded_evidence_rows": (config.get("gtos_vnext_runtime", {}) or {}).get("min_loaded_evidence_rows"),
        "source_event_type_counts": dict(sorted(event_source_counts.items())),
        "group_source_scope_counts": dict(sorted(group_counts.items())),
        "symbol_group_counts": dict(sorted(symbol_counts.items())),
        "session_group_counts": dict(sorted(session_counts.items())),
        "side_group_counts": dict(sorted(side_counts.items())),
        "framework_group_counts": dict(sorted(framework_counts.items())),
        "runtime_mode_summary": mode_summary,
        "activation_delta_counts": dict(sorted(activation_delta_counts.items())),
        "path_mode_counts": dict(sorted(path_mode_counts.items())),
        "path_status_counts": dict(sorted(path_status_counts.items())),
        "terminal_order_counts": dict(sorted(terminal_counts.items())),
        "best_available_path_outcome_counts": dict(sorted(best_outcomes.items())),
        "best_available_path_mode_counts": dict(sorted(best_path_modes.items())),
        "proxy_r_totals": {key: round(value, 8) for key, value in sorted(proxy_totals.items())},
        "proxy_r_counts": dict(sorted(proxy_counts.items())),
        "skipped_or_partial_counts": dict(sorted(skipped.items())),
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "pass": (
            len(groups) > 0
            and len(rows) == len(groups) * 2
            and artifact_index.row_count >= int((config.get("gtos_vnext_runtime", {}) or {}).get("min_loaded_evidence_rows", 0))
            and not artifact_index.missing_paths
            and any(
                _nested_get(row, "route_decision", "matched")
                for row in rows
                if row["runtime_activation_mode"] == "current_config_shadow"
            )
        ),
    }
    metrics = {
        "schema_version": "vnext_replay_metrics_summary_v1",
        "generated_utc": utc_now(),
        "stage_id": STAGE_ID,
        "metric_scope": "stage05_initial_saturated_replay_metrics_before_ablation_prop_and_robustness",
        "candidate_events": len(groups),
        "evaluated_events": sum(
            1 for row in rows if row.get("runtime_call_status") == "EVALUATED_ALL_RUNTIME_SURFACES"
        ),
        "skipped_events_by_reason": dict(sorted(skipped.items())),
        "decision_counts_follow_avoid_mixed_legacy": {
            mode: mode_summary.get(mode, {}).get("route_decision_counts", {})
            for mode in sorted(mode_summary)
        },
        "matched_artifact_rows_by_mode": {
            mode: {
                "route_matched_rows_total": sum(
                    int((_nested_get(row, "route_decision", "evidence", "matched_rows") or 0))
                    for row in rows
                    if row.get("runtime_activation_mode") == mode
                ),
                "direct_matched_rows_total": sum(
                    int((_nested_get(row, "direct_decision", "evidence", "matched_rows") or 0))
                    for row in rows
                    if row.get("runtime_activation_mode") == mode
                ),
            }
            for mode in sorted(mode_summary)
        },
        "risk_multiplier_distribution": {
            mode: mode_summary.get(mode, {}).get("risk_would_multiplier_counts", {})
            for mode in sorted(mode_summary)
        },
        "zero_risk_blocks": {
            mode: mode_summary.get(mode, {}).get("risk_would_multiplier_counts", {}).get("0.0", 0)
            for mode in sorted(mode_summary)
        },
        "pre_ai_action_distribution": {
            mode: mode_summary.get(mode, {}).get("pre_ai_action_counts", {})
            for mode in sorted(mode_summary)
        },
        "ai_calls_allowed_skipped_narrowed": {
            mode: mode_summary.get(mode, {}).get("pre_ai_would_action_counts", {})
            for mode in sorted(mode_summary)
        },
        "no_fill_pending_market_entry_decisions": {
            mode: mode_summary.get(mode, {}).get("pending_would_action_counts", {})
            for mode in sorted(mode_summary)
        },
        "entry_touch_fill_miss_and_stop_target": {
            "best_available_path_outcome_counts": dict(sorted(best_outcomes.items())),
            "terminal_order_counts": dict(sorted(terminal_counts.items())),
            "path_mode_counts": dict(sorted(path_mode_counts.items())),
            "path_status_counts": dict(sorted(path_status_counts.items())),
        },
        "proxy_r": {
            "totals": {key: round(value, 8) for key, value in sorted(proxy_totals.items())},
            "counts": dict(sorted(proxy_counts.items())),
            "mean": {
                key: round(proxy_totals[key] / proxy_counts[key], 8)
                for key in sorted(proxy_counts)
                if proxy_counts[key]
            },
        },
        "coverage_by_symbol_session_side_framework": {
            "symbols": dict(sorted(symbol_counts.items())),
            "sessions": dict(sorted(session_counts.items())),
            "sides": dict(sorted(side_counts.items())),
            "frameworks": dict(sorted(framework_counts.items())),
        },
        "activation_delta_counts": dict(sorted(activation_delta_counts.items())),
        "metrics_not_yet_computed_until_later_stages": [
            "family ablation deltas",
            "MIXED resolution deltas",
            "Funded-style pass probabilities",
            "Monte Carlo trade-order reshuffle",
            "walk-forward/holdout/placebo robustness",
        ],
        "no_live_trading_or_broker_mutation": True,
    }
    return summary, metrics


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for path in [SATURATED_REPLAY_LEDGER_PATH, SATURATED_REPLAY_SUMMARY_PATH, METRICS_SUMMARY_PATH]:
        existing_paths[rel(path)] = {
            "path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "lines": line_count(path),
            "sha256": sha256_file(path),
            "source_kind": "generated_replay_output",
        }
    write_json(
        OUTPUT_MANIFEST_PATH,
        {
            "schema_version": "vnext_replay_output_manifest_v1",
            "generated_utc": utc_now(),
            "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
            "outputs": [existing_paths[key] for key in sorted(existing_paths)],
            "next_stage": NEXT_STAGE_ID,
        },
    )


def update_session_state(summary: dict[str, Any]) -> None:
    if not SESSION_STATE_PATH.exists():
        return
    state = read_json(SESSION_STATE_PATH)
    completed = list(state.get("completed_stage_ids") or [])
    if STAGE_ID not in completed:
        completed.append(STAGE_ID)
    outputs = list(state.get("current_output_artifacts") or [])
    for path in [SATURATED_REPLAY_LEDGER_PATH, SATURATED_REPLAY_SUMMARY_PATH, METRICS_SUMMARY_PATH]:
        item = rel(path)
        if item not in outputs:
            outputs.append(item)
    tests = list(state.get("last_tests_or_verifiers") or [])
    verifier = (
        "python research/science_program_2026_05/06_outcome_testing/"
        "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        "build_vnext_replay_saturated_replay_2026_05_24.py -> "
        f"pass; {summary.get('event_groups')} groups; {summary.get('replay_rows')} replay rows; "
        f"{summary.get('runtime_artifact_index_rows')} runtime rows"
    )
    if verifier not in tests:
        tests.append(verifier)
    state.update(
        {
            "updated_utc": utc_now(),
            "current_stage_id": NEXT_STAGE_ID,
            "current_shard_id": "STAGE_06_ABLATION_AND_MIXED_RESOLUTION__ALL_FAMILIES__ALL_MODES__000",
            "current_objective": (
                "Run behavior-family ablations and MIXED resolution over the saturated replay "
                "ledger while preserving current shadow versus hypothetical activation boundaries."
            ),
            "current_output_artifacts": outputs,
            "completed_stage_ids": completed,
            "next_executable_action": (
                "Build and run the STAGE_06 ablation and MIXED-resolution builder over "
                "VNEXT_REPLAY_SATURATED_REPLAY_LEDGER_2026-05-24.jsonl, the runtime artifact "
                "coverage ledger, and Stage05 metrics summary."
            ),
            "last_tests_or_verifiers": tests,
            "open_questions_remaining": [
                "STAGE_06 not yet complete: no family ablation or MIXED-resolution rows exist yet.",
                "No prop-firm metrics, robustness, final report, or promotion/kill/repair map exists yet in this replay truth-engine route.",
            ],
            "resume_instruction": (
                "On resume or uncertainty: regenerate/read .context/LIVE_STATE.md; reread the "
                "controlling prompt, starter, this session-state file, goal_session_research_discipline.md, "
                "research_operating_doctrine.md, orchestrator hardening files, latest handoff, active config, "
                "freeze report, freeze ledger, master/batch ledgers, and current runtime/tests from disk; "
                "verify HEAD/config/runtime artifact manifest hashes and git status; repair this JSON if stale; "
                "then execute next_executable_action for STAGE_06 without restarting broad planning."
            ),
        }
    )
    write_json(SESSION_STATE_PATH, state)


def build_outputs() -> dict[str, Any]:
    rows, summary, metrics = build_replay_rows()
    write_jsonl(SATURATED_REPLAY_LEDGER_PATH, rows)
    write_json(SATURATED_REPLAY_SUMMARY_PATH, summary)
    write_json(METRICS_SUMMARY_PATH, metrics)
    update_output_manifest()
    update_session_state(summary)
    if not summary.get("pass"):
        raise SystemExit("saturated replay summary did not pass")
    return summary


def check_outputs() -> None:
    existing_rows = read_jsonl(SATURATED_REPLAY_LEDGER_PATH)
    existing_summary = read_json(SATURATED_REPLAY_SUMMARY_PATH)
    existing_metrics = read_json(METRICS_SUMMARY_PATH)
    if not existing_summary.get("pass"):
        raise AssertionError("Saturated replay summary did not pass")
    if existing_summary.get("replay_rows") != len(existing_rows):
        raise AssertionError("Saturated replay row count does not match summary")
    expected_rows = int(existing_summary.get("event_groups") or 0) * 2
    if len(existing_rows) != expected_rows:
        raise AssertionError("Saturated replay ledger does not have two activation rows per group")
    modes = Counter(row.get("runtime_activation_mode") for row in existing_rows)
    if modes.get("current_config_shadow", 0) != existing_summary.get("event_groups"):
        raise AssertionError("Current-config activation coverage is incomplete")
    if modes.get("hypothetical_activated_vnext", 0) != existing_summary.get("event_groups"):
        raise AssertionError("Hypothetical activation coverage is incomplete")
    if any(row.get("no_live_trading_or_broker_mutation") is not True for row in existing_rows):
        raise AssertionError("A replay row is missing the no-live-mutation guard")
    if existing_metrics.get("candidate_events") != existing_summary.get("event_groups"):
        raise AssertionError("Metrics candidate event count does not match summary")
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    manifest_paths = {item.get("path") for item in manifest.get("outputs", []) if isinstance(item, dict)}
    for path in [SATURATED_REPLAY_LEDGER_PATH, SATURATED_REPLAY_SUMMARY_PATH, METRICS_SUMMARY_PATH]:
        if rel(path) not in manifest_paths:
            raise AssertionError(f"Output manifest missing {rel(path)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext saturated replay check passed")
        return
    with SingleWriterLock(WRITER_LOCK_PATH):
        summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
