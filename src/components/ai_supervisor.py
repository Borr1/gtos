"""Bounded AI supervisor for schema health and vNext AI routing diagnostics.

The supervisor is not a trading decision maker. It reads local diagnostic logs,
emits a health decision, and can disable AI-narrowing dependent paths when the
configured health checks fail.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
import copy
import json
import logging


logger = logging.getLogger(__name__)

AISupervisorAction = Literal[
    "SUPERVISOR_DISABLED",
    "HEALTHY",
    "WARN",
    "DISABLE_AI_NARROWING",
    "BLOCK_SUPERVISOR_DEPENDENT_AI",
]

DEFAULT_AI_TRACE_LOG_PATH = Path("shadow_logs/ai_decision_trace.jsonl")
DEFAULT_MALFORMED_LOG_PATH = Path("shadow_logs/malformed_responses.jsonl")
DEFAULT_VNEXT_DECISION_LOG_PATH = Path("shadow_logs/gtos_vnext_runtime_decisions.jsonl")
DEFAULT_SUPERVISOR_LOG_PATH = Path("shadow_logs/ai_supervisor_decisions.jsonl")


@dataclass(frozen=True)
class AIResponseFormatRepair:
    """Result from a semantics-preserving response formatting repair attempt."""

    repaired: bool
    repaired_text: str
    reason: str
    original_sha256: str
    repaired_sha256: str

    def to_record(self) -> dict[str, Any]:
        return {
            "repaired": self.repaired,
            "repaired_text": self.repaired_text,
            "reason": self.reason,
            "original_sha256": self.original_sha256,
            "repaired_sha256": self.repaired_sha256,
        }


@dataclass(frozen=True)
class AISupervisorDecision:
    """Health decision emitted by the bounded AI supervisor."""

    action: AISupervisorAction
    enabled: bool
    apply_runtime_overrides: bool
    severity: str
    reason: str
    disable_ai_narrowing: bool = False
    block_supervisor_dependent_ai: bool = False
    checks: dict[str, Any] = field(default_factory=dict)
    effects: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "enabled": self.enabled,
            "apply_runtime_overrides": self.apply_runtime_overrides,
            "severity": self.severity,
            "reason": self.reason,
            "disable_ai_narrowing": self.disable_ai_narrowing,
            "block_supervisor_dependent_ai": self.block_supervisor_dependent_ai,
            "checks": dict(self.checks),
            "effects": dict(self.effects),
        }


def _cfg(config: dict[str, Any] | None) -> dict[str, Any]:
    raw = (config or {}).get("ai_supervisor", {}) or {}
    return raw if isinstance(raw, dict) else {}


def _as_path(value: Any, default: Path) -> Path:
    return Path(str(value or default))


def _tail_jsonl(path: Path, max_rows: int) -> list[dict[str, Any]]:
    if max_rows <= 0 or not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines[-max_rows:]:
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"_malformed_jsonl_row": True, "raw_length": len(line)})
    return rows


def _counter_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted((str(key), int(value)) for key, value in counter.items()))


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def repair_ai_response_format_preserving_semantics(raw_response: str) -> AIResponseFormatRepair:
    """Extract an intact JSON object without changing any field semantics."""
    raw = raw_response or ""
    stripped = raw.strip()
    original_hash = _sha256_text(raw)
    if not stripped:
        return AIResponseFormatRepair(False, raw, "empty_response", original_hash, original_hash)
    candidates = [stripped]
    fence_start = stripped.find("```")
    if fence_start >= 0:
        first_newline = stripped.find("\n", fence_start)
        fence_end = stripped.rfind("```")
        if first_newline >= 0 and fence_end > first_newline:
            candidates.append(stripped[first_newline + 1:fence_end].strip())
    brace_start = stripped.find("{")
    brace_end = stripped.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        candidates.append(stripped[brace_start:brace_end + 1])
    for candidate in candidates:
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            continue
        repaired = candidate != raw
        return AIResponseFormatRepair(
            repaired=repaired,
            repaired_text=candidate,
            reason="json_object_extracted_without_field_mutation" if repaired else "already_valid_json",
            original_sha256=original_hash,
            repaired_sha256=_sha256_text(candidate),
        )
    return AIResponseFormatRepair(
        repaired=False,
        repaired_text=raw,
        reason="no_valid_json_object_found",
        original_sha256=original_hash,
        repaired_sha256=original_hash,
    )


def _summarize_trace(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(row.get("response_status")) for row in rows)
    parse_retries = sum(1 for row in rows if int(row.get("parse_attempts") or 0) > 1)
    token_usage = Counter()
    candidate_clusters = Counter()
    missing_hash_rows = 0
    missing_cache_identity_rows = 0
    for row in rows:
        usage = row.get("usage") or {}
        if isinstance(usage, dict):
            for key in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_create_tokens"):
                token_usage[key] += int(usage.get(key) or 0)
        if row.get("decision") == "CANDIDATE":
            candidate_clusters[f"{row.get('symbol')}::{row.get('kill_zone')}"] += 1
        fingerprint = row.get("prompt_fingerprint") or {}
        if not isinstance(fingerprint, dict) or not fingerprint.get("prompt_bundle_sha256"):
            missing_hash_rows += 1
        cache_identity = row.get("content_addressed_cache_identity") or {}
        if (
            not isinstance(cache_identity, dict)
            or cache_identity.get("cache_key_status") != "complete"
            or not cache_identity.get("content_addressed_cache_key")
        ):
            missing_cache_identity_rows += 1
    return {
        "row_count": len(rows),
        "response_status_counts": _counter_dict(statuses),
        "parse_retry_rows": parse_retries,
        "token_usage": _counter_dict(token_usage),
        "candidate_clusters": _counter_dict(candidate_clusters),
        "missing_prompt_hash_rows": missing_hash_rows,
        "missing_cache_identity_rows": missing_cache_identity_rows,
    }


def _summarize_malformed(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "attempt_counts": _counter_dict(Counter(str(row.get("attempt")) for row in rows)),
        "models": _counter_dict(Counter(str(row.get("model")) for row in rows)),
        "symbols": _counter_dict(Counter(str(row.get("symbol")) for row in rows)),
    }


def _summarize_vnext(rows: list[dict[str, Any]]) -> dict[str, Any]:
    phase_counts = Counter(str(row.get("phase")) for row in rows)
    shadowed_policy_rows = 0
    missing_source_bound_rows = 0
    legacy_block_rows = 0
    stale_artifact_rows = 0
    for row in rows:
        decision = (row.get("decision") or {})
        if not isinstance(decision, dict):
            continue
        if row.get("phase") == "ai_policy_pre_call":
            if decision.get("action") != decision.get("would_action"):
                shadowed_policy_rows += 1
            scope = decision.get("prompt_scope") or {}
            would_action = str(decision.get("would_action") or "")
            if (
                would_action in {"CALL_AI_NARROWED_ROUTE", "CALL_AI_MIXED_RESOLUTION"}
                and isinstance(scope, dict)
                and not scope.get("source_bound")
            ):
                missing_source_bound_rows += 1
            if decision.get("reason") == "legacy_broad_ai_fallback_not_replayed":
                legacy_block_rows += 1
        reason = str(decision.get("reason") or "")
        if "evidence_index_below_min_loaded_rows" in reason:
            stale_artifact_rows += 1
    return {
        "row_count": len(rows),
        "phase_counts": _counter_dict(phase_counts),
        "shadowed_policy_rows": shadowed_policy_rows,
        "missing_source_bound_rows": missing_source_bound_rows,
        "legacy_block_rows": legacy_block_rows,
        "stale_artifact_rows": stale_artifact_rows,
    }


def evaluate_ai_supervisor(
    *,
    config: dict[str, Any] | None,
    trace_rows: list[dict[str, Any]] | None = None,
    malformed_rows: list[dict[str, Any]] | None = None,
    vnext_rows: list[dict[str, Any]] | None = None,
) -> AISupervisorDecision:
    """Evaluate AI health from local logs and return bounded supervisor action."""
    cfg = _cfg(config)
    enabled = bool(cfg.get("enabled", True))
    apply_overrides = bool(cfg.get("apply_runtime_overrides", True))
    if not enabled:
        return AISupervisorDecision(
            action="SUPERVISOR_DISABLED",
            enabled=False,
            apply_runtime_overrides=False,
            severity="disabled",
            reason="ai_supervisor_disabled",
        )
    max_rows = int(cfg.get("max_log_rows", 500) or 500)
    if trace_rows is None:
        trace_rows = _tail_jsonl(
            _as_path(cfg.get("ai_decision_trace_path"), DEFAULT_AI_TRACE_LOG_PATH),
            max_rows,
        )
    if malformed_rows is None:
        malformed_rows = _tail_jsonl(
            _as_path(cfg.get("malformed_response_path"), DEFAULT_MALFORMED_LOG_PATH),
            max_rows,
        )
    if vnext_rows is None:
        vnext_rows = _tail_jsonl(
            _as_path(cfg.get("vnext_decision_log_path"), DEFAULT_VNEXT_DECISION_LOG_PATH),
            max_rows,
        )
    trace = _summarize_trace(trace_rows)
    malformed = _summarize_malformed(malformed_rows)
    vnext = _summarize_vnext(vnext_rows)
    checks = {
        "ai_decision_trace": trace,
        "malformed_responses": malformed,
        "vnext_route_drift": vnext,
        "latency_monitoring": {
            "available": False,
            "reason": "ai_decision_trace_rows_do_not_currently_store_latency_ms",
        },
        "cost_monitoring": {
            "available": True,
            "token_usage": trace["token_usage"],
        },
    }

    failures: list[str] = []
    warnings: list[str] = []
    if malformed["row_count"] >= int(cfg.get("max_malformed_rows", 5) or 5):
        failures.append("malformed_response_threshold")
    malformed_demoted = trace["response_status_counts"].get("malformed_demoted", 0)
    if malformed_demoted >= int(cfg.get("max_malformed_demoted_rows", 2) or 2):
        failures.append("malformed_demoted_threshold")
    if trace["missing_prompt_hash_rows"] > 0:
        failures.append("missing_prompt_hash")
    if (
        bool(cfg.get("require_complete_trace_cache_identity", True))
        and trace["missing_cache_identity_rows"] > 0
    ):
        failures.append("missing_trace_cache_identity")
    if vnext["missing_source_bound_rows"] >= int(cfg.get("max_missing_source_bound_rows", 1) or 1):
        failures.append("missing_source_bound_prompt_scope")
    if vnext["stale_artifact_rows"] > 0:
        failures.append("stale_or_truncated_artifact_load")
    max_cluster = int(cfg.get("max_candidate_cluster_rows", 3) or 3)
    if any(count > max_cluster for count in trace["candidate_clusters"].values()):
        failures.append("abnormal_trade_cluster")
    if trace["parse_retry_rows"] > 0:
        warnings.append("parse_retry_rows_present")
    if vnext["legacy_block_rows"] > 0:
        warnings.append("legacy_broad_fallback_blocks_present")

    if failures:
        action: AISupervisorAction = "DISABLE_AI_NARROWING"
        severity = "critical"
        reason = ",".join(sorted(failures))
        disable_ai_narrowing = True
    elif warnings:
        action = "WARN"
        severity = "warning"
        reason = ",".join(sorted(warnings))
        disable_ai_narrowing = False
    else:
        action = "HEALTHY"
        severity = "ok"
        reason = "ai_supervisor_health_checks_passed"
        disable_ai_narrowing = False

    effects = {
        "disable_ai_narrowing": disable_ai_narrowing,
        "disable_vnext_ai_policy_active_effect": disable_ai_narrowing,
        "blocks_trades_directly": False,
        "changes_trade_direction": False,
        "changes_trade_parameters": False,
    }
    return AISupervisorDecision(
        action=action,
        enabled=True,
        apply_runtime_overrides=apply_overrides,
        severity=severity,
        reason=reason,
        disable_ai_narrowing=disable_ai_narrowing,
        block_supervisor_dependent_ai=False,
        checks=checks,
        effects=effects,
    )


def apply_ai_supervisor_runtime_overrides(
    config: dict[str, Any],
    decision: AISupervisorDecision,
) -> dict[str, Any]:
    """Return a config copy with AI-narrowing active effects disabled if needed."""
    effective = copy.deepcopy(config)
    if not (
        decision.enabled
        and decision.apply_runtime_overrides
        and decision.disable_ai_narrowing
    ):
        return effective
    runtime = effective.setdefault("gtos_vnext_runtime", {})
    runtime["pre_ai_apply_to_ai_call"] = False
    runtime["ai_policy_apply_to_ai_call"] = False
    runtime["ai_supervisor_override_reason"] = decision.reason
    runtime["ai_supervisor_override_action"] = decision.action
    return effective


def record_ai_supervisor_decision(
    *,
    decision: AISupervisorDecision,
    config: dict[str, Any] | None,
    phase: str,
    symbol: str | None = None,
    kill_zone: str | None = None,
    log_path: Path | str | None = None,
) -> None:
    cfg = _cfg(config)
    if not bool(cfg.get("decision_log_enabled", True)):
        return
    path = Path(log_path or cfg.get("decision_log_path") or DEFAULT_SUPERVISOR_LOG_PATH)
    row = {
        "schema_version": "ai_supervisor_decision_v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "symbol": symbol,
        "kill_zone": kill_zone,
        "decision": decision.to_record(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError as exc:
        logger.warning("ai_supervisor decision log failed: %s", exc)


__all__ = [
    "AIResponseFormatRepair",
    "AISupervisorDecision",
    "apply_ai_supervisor_runtime_overrides",
    "evaluate_ai_supervisor",
    "record_ai_supervisor_decision",
    "repair_ai_response_format_preserving_semantics",
]
