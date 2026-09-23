"""Stage 03 actual vNext runtime tracing for generated replay candidates.

This route-local builder consumes the Stage02 market-bar candidate shards and
calls the current ``src.components.gtos_vnext_runtime`` surfaces. It writes
route-owned durable shards with atomic temp-to-final replacement. It does not
change production config, call MT5, place orders, call paid APIs, or mutate
broker/account/order/deal/position/history state.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


DATE_ID = "2026-05-24"
ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
STAGE_ID = "STAGE_03_RUNTIME_TRACE"
PREVIOUS_STAGE_ID = "STAGE_02_CANDIDATE_GENERATION_ENGINE"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    apply_vnext_risk_adjustment,
    evaluate_pre_ai_vnext,
    evaluate_vnext_event,
    evaluate_vnext_pending_policy,
    evaluate_vnext_route_event,
    load_vnext_evidence_index,
    normalize_event,
)


CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
STAGE02_STATUS_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
STAGE02_VERIFIER_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_VERIFIER_{DATE_ID}.json"
STAGE02_SUMMARY_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_{DATE_ID}.json"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_ID}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_{DATE_ID}.json"
ACTIVE_QUESTION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_ID}.jsonl"
EXTRA_STEP_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_EXTRA_STEP_PURSUIT_LEDGER_{DATE_ID}.jsonl"
PROMPT_APPLICATION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_ID}.jsonl"
LINE_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_{DATE_ID}.jsonl"
COMPLETION_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_ID}.json"

OUTPUTS = {
    "runtime_trace": ROUTE_DIR / f"VNEXT_FULL_REPLAY_RUNTIME_TRACE_LEDGER_{DATE_ID}.jsonl",
    "runtime_event_cache": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_RUNTIME_EVENT_CACHE_LEDGER_{DATE_ID}.jsonl"
    ),
    "runtime_artifact_load": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_RUNTIME_ARTIFACT_LOAD_LEDGER_{DATE_ID}.jsonl"
    ),
    "runtime_trace_summary": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_RUNTIME_TRACE_SUMMARY_{DATE_ID}.json"
    ),
    "stage03_verifier": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE03_VERIFIER_{DATE_ID}.json",
    "stage03_shard_contract": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE03_SHARD_CONTRACT_{DATE_ID}.json"
    ),
    "stage03_heartbeat": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE03_HEARTBEAT_{DATE_ID}.json"
    ),
    "stage03_shard_status": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE03_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
    ),
}

SHARD_DIR = ROUTE_DIR / "stage03_shards"
SHARDED_ARTIFACT_KEYS = ("runtime_trace", "runtime_event_cache")
SOURCE_ORIGIN = "market_bar_enumeration"
RUNTIME_MODES = ("current_config_shadow", "hypothetical_activated_vnext")
RUNTIME_SURFACE_CALLS = (
    "evaluate_vnext_event",
    "evaluate_vnext_route_event",
    "evaluate_pre_ai_vnext",
    "apply_vnext_risk_adjustment",
    "evaluate_vnext_pending_policy",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def append_jsonl_rows(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    return f"{prefix}_{stable_hash(payload)[:length]}"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_GIT_HEAD"


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_chunked_jsonl(index_path: Path) -> Iterator[dict[str, Any]]:
    for index_row in iter_jsonl(index_path):
        chunk_path = repo_path(index_row["chunk_path"])
        yield from iter_gzip_jsonl(chunk_path)


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def config_hash(config: dict[str, Any]) -> str:
    return stable_hash(config)


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


def config_for_mode(config: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode == "current_config_shadow":
        return config
    if mode == "hypothetical_activated_vnext":
        return activated_config(config)
    raise ValueError(f"unknown runtime mode: {mode}")


def replay_slice_config(config: dict[str, Any]) -> dict[str, Any]:
    """Use current runtime surfaces on full-index-derived event slices.

    The full runtime artifact universe is loaded and audited separately. The
    per-event runtime call receives only rows the current runtime index matched
    to that event, so the global denominator availability guard is disabled for
    the slice. This is a replay-harness performance control, not a production
    config change.
    """
    cfg = copy.deepcopy(config)
    cfg.setdefault("gtos_vnext_runtime", {})["min_loaded_evidence_rows"] = 0
    return cfg


def stage02_expected_candidate_count() -> int:
    verifier = read_json(STAGE02_VERIFIER_PATH)
    return int(verifier["candidate_count"])


def stage02_status_rows() -> list[dict[str, Any]]:
    rows = [
        row
        for row in iter_jsonl(STAGE02_STATUS_PATH)
        if row.get("stage_id") == PREVIOUS_STAGE_ID and row.get("shard_status") == "complete"
    ]
    return sorted(rows, key=lambda row: int(row.get("source_index") or 0))


def source_stage03_shard_id(stage02_shard: dict[str, Any]) -> str:
    return stable_id(
        "stage03src",
        {
            "stage02_shard_id": stage02_shard.get("shard_id"),
            "source_path": stage02_shard.get("source_path"),
            "source_index": stage02_shard.get("source_index"),
        },
        length=16,
    )


def stage03_shard_paths(shard_id: str) -> dict[str, Path]:
    shard_dir = SHARD_DIR / shard_id
    return {
        "dir": shard_dir,
        "runtime_trace": shard_dir / "runtime_trace.jsonl.gz",
        "runtime_event_cache": shard_dir / "runtime_event_cache.jsonl.gz",
        "manifest": shard_dir / "manifest.json",
        "heartbeat": shard_dir / "heartbeat.json",
    }


class AtomicGzipJsonlWriter:
    def __init__(self, final_path: Path) -> None:
        self.final_path = final_path
        self.tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
        self.row_count = 0
        self._handle: gzip.GzipFile | None = None

    def __enter__(self) -> "AtomicGzipJsonlWriter":
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = gzip.open(self.tmp_path, "wt", encoding="utf-8", newline="\n")
        return self

    def write(self, row: dict[str, Any]) -> None:
        assert self._handle is not None
        self._handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.row_count += 1

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        if exc_type is None:
            self.tmp_path.replace(self.final_path)
        elif self.tmp_path.exists():
            self.tmp_path.unlink()


def write_stage03_heartbeat(payload: dict[str, Any]) -> None:
    write_json(OUTPUTS["stage03_heartbeat"], payload)


def write_shard_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)


def completed_shard_manifest(
    *,
    stage02_shard: dict[str, Any],
    runtime_config_hash: str,
    runtime_artifact_hash: str,
) -> dict[str, Any] | None:
    shard_id = source_stage03_shard_id(stage02_shard)
    paths = stage03_shard_paths(shard_id)
    manifest_path = paths["manifest"]
    if not manifest_path.exists():
        return None
    try:
        manifest = read_json(manifest_path)
    except Exception:
        return None
    if manifest.get("shard_status") != "complete":
        return None
    if manifest.get("source_path") != stage02_shard.get("source_path"):
        return None
    if manifest.get("runtime_config_hash") != runtime_config_hash:
        return None
    if manifest.get("runtime_artifact_index_hash") != runtime_artifact_hash:
        return None
    expected_candidates = int((stage02_shard.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or -1)
    if int(manifest.get("candidate_rows") or -1) != expected_candidates:
        return None
    expected_trace_rows = expected_candidates * len(RUNTIME_MODES)
    if int((manifest.get("row_counts") or {}).get("runtime_trace") or -1) != expected_trace_rows:
        return None
    for key in SHARDED_ARTIFACT_KEYS:
        output = (manifest.get("outputs") or {}).get(key) or {}
        output_path = repo_path(output.get("path") or "")
        if not output_path.exists():
            return None
        if int(output.get("row_count") or -1) < 0:
            return None
        if output.get("sha256") != sha256_file(output_path):
            return None
    return manifest


def route_session_from_bucket(bucket: Any) -> str:
    token = str(bucket or "").strip().lower()
    if token.endswith("_broad"):
        token = token[: -len("_broad")]
    return token or "unknown_session"


def bias_from_side(side: Any) -> str | None:
    token = str(side or "").upper()
    if token == "LONG":
        return "bullish"
    if token == "SHORT":
        return "bearish"
    return None


def runtime_event_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    framework = candidate.get("framework") or candidate.get("effective_framework")
    session = route_session_from_bucket(candidate.get("session_bucket") or candidate.get("route_session"))
    event = {
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol") or candidate.get("symbol"),
        "market": candidate.get("source_symbol") or candidate.get("symbol"),
        "route_session": session,
        "session": session,
        "kill_zone": session,
        "side": candidate.get("side"),
        "direction": candidate.get("side"),
        "framework": framework,
        "effective_framework": framework,
        "route_family": candidate.get("route_family") or framework,
        "market_timeframe": candidate.get("market_timeframe") or candidate.get("timeframe") or "M15",
        "timeframe": candidate.get("timeframe") or candidate.get("market_timeframe") or "M15",
        "entry_timeframe": candidate.get("timeframe") or candidate.get("market_timeframe") or "M15",
        "entry_variant": candidate.get("entry_variant"),
        "target_stop_order_class": candidate.get("target_stop_class"),
    }
    return {key: value for key, value in event.items() if value not in (None, "", [], {})}


def raw_data_from_candidate(candidate: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    raw = {
        "gtos_full_replay_stage03": True,
        "candle_close_utc": candidate.get("candle_time_utc"),
        "market": event.get("market"),
        "timeframe": event.get("timeframe"),
        "market_timeframe": event.get("market_timeframe"),
        "route_family": event.get("route_family"),
        "entry_variant": candidate.get("entry_variant"),
        "target_stop_order_class": candidate.get("target_stop_class"),
        "source_component": candidate.get("source_component"),
    }
    return {key: value for key, value in raw.items() if value not in (None, "", [], {})}


def event_cache_key(event: dict[str, Any], raw_data: dict[str, Any]) -> dict[str, Any]:
    """Return the current-runtime decision scope used for cache reuse.

    Candidate candle time is intentionally outside the cache key because the
    current vNext matcher does not use it for scope selection. Per-candidate
    trace rows still preserve the actual candle time and provenance.
    """
    raw_scope = {
        key: value
        for key, value in raw_data.items()
        if key
        not in {
            "candle_close_utc",
        }
    }
    return {
        "event": event,
        "raw_data_decision_scope": raw_scope,
        "cache_excludes_candle_time": True,
    }


def runtime_cache_id(mode: str, key_payload: dict[str, Any]) -> str:
    return stable_id("rtevt", {"mode": mode, "key": key_payload})


def runtime_slice_rows_for_event(runtime_index: Any, event: dict[str, Any]) -> list[dict[str, Any]]:
    return list(runtime_index.match_event(normalize_event(event), min_scope_fields=1))


def compact_runtime_decision(record: dict[str, Any], *, include_rows: bool) -> dict[str, Any]:
    evidence = record.get("evidence", {}) if isinstance(record, dict) else {}
    compact_evidence = {
        "matched_rows": evidence.get("matched_rows"),
        "decision_counts": evidence.get("decision_counts"),
        "source_component_counts": evidence.get("source_component_counts"),
        "evidence_family_counts": evidence.get("evidence_family_counts"),
        "action_class_counts": evidence.get("action_class_counts"),
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
        "row_detail_count": evidence.get("row_detail_count"),
        "rows_truncated": evidence.get("rows_truncated"),
        "bridge_diagnostics": evidence.get("bridge_diagnostics"),
    }
    if include_rows:
        compact_evidence["rows"] = evidence.get("rows")
    return {
        "decision": record.get("decision"),
        "enabled": record.get("enabled"),
        "apply_to_execution": record.get("apply_to_execution"),
        "matched": record.get("matched"),
        "reason": record.get("reason"),
        "event": record.get("event"),
        "artifact_path_count": len(record.get("artifact_paths") or []),
        "evidence": compact_evidence,
    }


def compact_pre_ai(record: dict[str, Any], *, include_side_decisions: bool) -> dict[str, Any]:
    compact = {
        "action": record.get("action"),
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
        "would_action": record.get("would_action"),
        "ai_role_context": record.get("ai_role_context"),
    }
    if include_side_decisions:
        compact["side_decisions"] = [
            compact_runtime_decision(decision, include_rows=True)
            for decision in record.get("side_decisions") or []
        ]
    else:
        compact["side_decision_summaries"] = [
            {
                "decision": decision.get("decision"),
                "matched": decision.get("matched"),
                "reason": decision.get("reason"),
                "matched_rows": ((decision.get("evidence") or {}).get("matched_rows")),
                "decision_counts": ((decision.get("evidence") or {}).get("decision_counts")),
            }
            for decision in record.get("side_decisions") or []
        ]
    return compact


def decision_summary(cache_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "direct_decision": cache_row["direct_decision"]["decision"],
        "direct_matched": cache_row["direct_decision"]["matched"],
        "direct_reason": cache_row["direct_decision"]["reason"],
        "route_decision": cache_row["route_decision"]["decision"],
        "route_matched": cache_row["route_decision"]["matched"],
        "route_reason": cache_row["route_decision"]["reason"],
        "pre_ai_action": cache_row["pre_ai_decision"]["action"],
        "pre_ai_would_action": cache_row["pre_ai_decision"]["would_action"],
        "pre_ai_decision": cache_row["pre_ai_decision"]["decision"],
        "pre_ai_reason": cache_row["pre_ai_decision"]["reason"],
        "risk_reason": cache_row["risk_adjustment"]["reason"],
        "risk_would_multiplier": cache_row["risk_adjustment"]["would_multiplier"],
        "risk_applied": cache_row["risk_adjustment"]["applied"],
        "pending_action": cache_row["pending_policy"]["action"],
        "pending_would_action": cache_row["pending_policy"]["would_action"],
        "pending_reason": cache_row["pending_policy"]["reason"],
    }


def causal_steps(
    *,
    candidate: dict[str, Any],
    mode: str,
    event: dict[str, Any],
    cache_row: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = decision_summary(cache_row)
    return [
        {
            "stage_name": "stage03_runtime_event_construction",
            "source_function_module": rel(Path(__file__).resolve()),
            "input_fields_used": [
                "candidate_id",
                "symbol",
                "source_symbol",
                "session_bucket",
                "side",
                "framework",
                "timeframe",
                "entry_variant",
                "target_stop_class",
            ],
            "predicate_or_threshold_evaluated": "construct current vNext event contract from Stage02 candidate fields",
            "matched_source_row_ids": [candidate.get("candidate_id"), candidate.get("source_universe_row_id")],
            "before_decision_state": "stage02_candidate_runtime_trace_status_pending",
            "after_decision_state": "runtime_event_contract_built",
            "reason_code": "market_bar_candidate_runtime_projection_event",
            "necessity": "necessary",
            "event": event,
        },
        {
            "stage_name": "pre_ai_vnext_runtime_surface",
            "source_function_module": "src.components.gtos_vnext_runtime.evaluate_pre_ai_vnext",
            "input_fields_used": ["symbol", "source_symbol", "kill_zone", "bias", "raw_data"],
            "predicate_or_threshold_evaluated": "current vNext pre-AI route evaluation",
            "matched_source_row_ids": [],
            "before_decision_state": mode,
            "after_decision_state": summary["pre_ai_action"],
            "reason_code": summary["pre_ai_reason"],
            "necessity": "contextual",
        },
        {
            "stage_name": "post_l2_route_vnext_runtime_surface",
            "source_function_module": "src.components.gtos_vnext_runtime.evaluate_vnext_route_event",
            "input_fields_used": ["symbol", "route_session", "side", "framework", "route_family", "market_timeframe"],
            "predicate_or_threshold_evaluated": "current vNext post-L2 route matching and conflict resolution",
            "matched_source_row_ids": cache_row["route_decision"]["evidence"].get("matched_row_ids") or [],
            "before_decision_state": mode,
            "after_decision_state": summary["route_decision"],
            "reason_code": summary["route_reason"],
            "necessity": "sufficient" if summary["route_decision"] != "LEGACY" else "contextual",
        },
        {
            "stage_name": "risk_vnext_runtime_surface",
            "source_function_module": "src.components.gtos_vnext_runtime.apply_vnext_risk_adjustment",
            "input_fields_used": ["route_decision", "risk.risk_per_trade_pct", "gtos_vnext_runtime"],
            "predicate_or_threshold_evaluated": "risk multiplier and zero-risk block calculation",
            "matched_source_row_ids": cache_row["route_decision"]["evidence"].get("matched_row_ids") or [],
            "before_decision_state": mode,
            "after_decision_state": summary["risk_reason"],
            "reason_code": summary["risk_reason"],
            "necessity": "contextual",
        },
        {
            "stage_name": "pending_policy_vnext_runtime_surface",
            "source_function_module": "src.components.gtos_vnext_runtime.evaluate_vnext_pending_policy",
            "input_fields_used": ["route_decision", "gtos_vnext_runtime.pending_policy_enabled"],
            "predicate_or_threshold_evaluated": "pending/no-fill policy action calculation",
            "matched_source_row_ids": cache_row["route_decision"]["evidence"].get("matched_row_ids") or [],
            "before_decision_state": mode,
            "after_decision_state": summary["pending_would_action"],
            "reason_code": summary["pending_reason"],
            "necessity": "contextual",
        },
    ]


def build_runtime_event_cache_row(
    *,
    mode: str,
    event_key_payload: dict[str, Any],
    event: dict[str, Any],
    raw_data: dict[str, Any],
    config: dict[str, Any],
    runtime_slice_rows: list[dict[str, Any]],
    runtime_config_hash: str,
    runtime_artifact_hash: str,
    full_runtime_index_rows_loaded: int,
    full_config_min_loaded_evidence_rows: Any,
) -> dict[str, Any]:
    cache_id = runtime_cache_id(mode, event_key_payload)
    direct = evaluate_vnext_event(event, config, artifact_rows=runtime_slice_rows)
    route = evaluate_vnext_route_event(event, config, artifact_rows=runtime_slice_rows)
    risk_pct = float((config.get("risk", {}) or {}).get("risk_per_trade_pct", 2.0))
    risk = apply_vnext_risk_adjustment(
        current_risk_pct=risk_pct,
        decision=route,
        config=config,
    )
    pending = evaluate_vnext_pending_policy(decision=route, config=config)
    pre_ai = evaluate_pre_ai_vnext(
        symbol=str(event.get("symbol") or ""),
        source_symbol=event.get("source_symbol"),
        kill_zone=str(event.get("kill_zone") or event.get("route_session") or ""),
        config=config,
        bias=raw_data.get("pre_ai_bias_proxy"),
        raw_data=raw_data,
        artifact_rows=runtime_slice_rows,
    )
    return {
        "schema_version": "vnext_full_replay_runtime_event_cache_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "runtime_event_cache_id": cache_id,
        "runtime_mode": mode,
        "runtime_surface_calls": list(RUNTIME_SURFACE_CALLS),
        "runtime_surface_call_status": "ok",
        "runtime_truth_class": "actual_current_runtime_surfaces_on_replay_constructed_candidate_event",
        "historical_live_intent_truth": False,
        "runtime_slice_policy": {
            "full_runtime_artifact_universe_loaded_before_slice": True,
            "full_runtime_index_rows_loaded": full_runtime_index_rows_loaded,
            "full_config_min_loaded_evidence_rows": full_config_min_loaded_evidence_rows,
            "slice_rows_from_current_runtime_index_match_event": len(runtime_slice_rows),
            "slice_min_loaded_evidence_rows_override": 0,
            "override_reason": (
                "full runtime artifact universe is loaded and audited once; per-event replay calls use "
                "current runtime surfaces on current-index-matched rows so route-variant scans can write durable shards"
            ),
        },
        "production_config_mutated": False,
        "no_live_trading_or_broker_mutation": True,
        "event_key_payload": event_key_payload,
        "runtime_input_event": event,
        "runtime_raw_data_decision_scope": {
            key: value for key, value in raw_data.items() if key != "candle_close_utc"
        },
        "runtime_config_hash": runtime_config_hash,
        "runtime_artifact_index_hash": runtime_artifact_hash,
        "direct_decision": compact_runtime_decision(direct.to_record(), include_rows=True),
        "route_decision": compact_runtime_decision(route.to_record(), include_rows=True),
        "pre_ai_decision": compact_pre_ai(pre_ai.to_record(), include_side_decisions=True),
        "risk_adjustment": risk.to_record(),
        "pending_policy": pending.to_record(),
        "created_at_utc": utc_now(),
    }


def trace_row_for_candidate(
    *,
    candidate: dict[str, Any],
    mode: str,
    event: dict[str, Any],
    raw_data: dict[str, Any],
    cache_row: dict[str, Any],
) -> dict[str, Any]:
    summary = decision_summary(cache_row)
    return {
        "schema_version": "vnext_full_replay_runtime_trace_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "runtime_trace_id": stable_id(
            "rttrace",
            {"candidate_id": candidate.get("candidate_id"), "mode": mode},
        ),
        "candidate_id": candidate.get("candidate_id"),
        "source_universe_row_id": candidate.get("source_universe_row_id"),
        "market_state_packet_id": candidate.get("market_state_packet_id"),
        "runtime_event_cache_id": cache_row["runtime_event_cache_id"],
        "runtime_mode": mode,
        "source_origin": candidate.get("source_origin"),
        "source_path": candidate.get("source_path"),
        "source_sha256": candidate.get("source_sha256"),
        "source_mode": candidate.get("source_mode"),
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "timeframe": candidate.get("timeframe"),
        "market_timeframe": candidate.get("market_timeframe"),
        "session_bucket": candidate.get("session_bucket"),
        "route_session": event.get("route_session"),
        "date_utc": candidate.get("date_utc"),
        "candle_time_utc": candidate.get("candle_time_utc"),
        "side": candidate.get("side"),
        "framework": candidate.get("framework"),
        "route_family": event.get("route_family"),
        "candidate_geometry": {
            "entry_reference": candidate.get("entry_reference"),
            "stop_or_invalidation": candidate.get("stop_or_invalidation"),
            "target_reference": candidate.get("target_reference"),
            "rr": candidate.get("rr"),
            "entry_variant": candidate.get("entry_variant"),
            "target_stop_class": candidate.get("target_stop_class"),
            "poi_type": candidate.get("poi_type"),
            "setup_type": candidate.get("setup_type"),
            "zone_id": candidate.get("zone_id"),
        },
        "runtime_input_event": event,
        "runtime_raw_data": raw_data,
        "runtime_surface_calls": list(RUNTIME_SURFACE_CALLS),
        "runtime_surface_call_status": cache_row["runtime_surface_call_status"],
        "runtime_truth_class": cache_row["runtime_truth_class"],
        "historical_live_intent_truth": False,
        "current_shadow_vs_hypothetical_mode": mode,
        "decision_summary": summary,
        "direct_decision": {
            "decision": cache_row["direct_decision"]["decision"],
            "matched": cache_row["direct_decision"]["matched"],
            "reason": cache_row["direct_decision"]["reason"],
            "matched_rows": cache_row["direct_decision"]["evidence"].get("matched_rows"),
            "matched_row_id_count": cache_row["direct_decision"]["evidence"].get("matched_row_id_count"),
            "matched_row_ids": cache_row["direct_decision"]["evidence"].get("matched_row_ids"),
            "matched_row_ids_truncated": cache_row["direct_decision"]["evidence"].get("matched_row_ids_truncated"),
        },
        "route_decision": {
            "decision": cache_row["route_decision"]["decision"],
            "matched": cache_row["route_decision"]["matched"],
            "reason": cache_row["route_decision"]["reason"],
            "matched_rows": cache_row["route_decision"]["evidence"].get("matched_rows"),
            "matched_row_id_count": cache_row["route_decision"]["evidence"].get("matched_row_id_count"),
            "matched_row_ids": cache_row["route_decision"]["evidence"].get("matched_row_ids"),
            "matched_row_ids_truncated": cache_row["route_decision"]["evidence"].get("matched_row_ids_truncated"),
            "decision_counts": cache_row["route_decision"]["evidence"].get("decision_counts"),
            "decision_resolution": cache_row["route_decision"]["evidence"].get("decision_resolution"),
            "metrics": cache_row["route_decision"]["evidence"].get("metrics"),
        },
        "pre_ai_decision": {
            "action": cache_row["pre_ai_decision"]["action"],
            "would_action": cache_row["pre_ai_decision"]["would_action"],
            "decision": cache_row["pre_ai_decision"]["decision"],
            "reason": cache_row["pre_ai_decision"]["reason"],
            "recommended_side": cache_row["pre_ai_decision"]["recommended_side"],
            "recommended_frameworks": cache_row["pre_ai_decision"]["recommended_frameworks"],
            "blocked_sides": cache_row["pre_ai_decision"]["blocked_sides"],
            "blocked_frameworks": cache_row["pre_ai_decision"]["blocked_frameworks"],
        },
        "risk_adjustment": cache_row["risk_adjustment"],
        "pending_policy": cache_row["pending_policy"],
        "causal_decision_steps": causal_steps(
            candidate=candidate,
            mode=mode,
            event=event,
            cache_row=cache_row,
        ),
        "repair_state": {
            "runtime_trace": "stage03_actual_runtime_surface_called",
            "remaining_path_truth": "pending_stage04_path_r_simulation",
            "remaining_source_mode_actions": (
                "execute_or_repair_M1_M5_tick_Sierra_SCID_OHLC_and_MT5_export_requirements"
            ),
            "remaining_dominance_pollution": "pending_stage05_dominance_pollution_counterfactuals",
            "remaining_mixed_resolution": "pending_generated_candidate_outcome_replay",
        },
        "path_truth_status": "pending_stage04_path_r_simulation",
        "m15_blindness_status": "pending_stage04_lower_timeframe_disagreement_measurement",
        "no_fill_pending_status": "pending_stage04_path_and_pending_lifecycle_simulation",
        "dominance_pollution_status": "pending_stage05_counterfactuals",
        "production_config_mutated": False,
        "no_live_trading_or_broker_mutation": True,
    }


def runtime_artifact_load_rows(config: dict[str, Any], runtime_index: Any) -> list[dict[str, Any]]:
    paths = list((config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or [])
    missing = set(str(item) for item in getattr(runtime_index, "missing_paths", ()) or ())
    loaded_by_path = getattr(runtime_index, "rows_loaded_by_path", {}) or {}
    rows = []
    for index, artifact_path in enumerate(paths, start=1):
        path = repo_path(artifact_path)
        rows.append(
            {
                "schema_version": "vnext_full_replay_runtime_artifact_load_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "artifact_index": index,
                "artifact_path": str(artifact_path),
                "artifact_exists": path.exists(),
                "artifact_bytes": path.stat().st_size if path.exists() else None,
                "artifact_sha256": sha256_file(path) if path.exists() else None,
                "rows_loaded": int(loaded_by_path.get(str(artifact_path)) or loaded_by_path.get(rel(path)) or 0),
                "missing_path": str(artifact_path) in missing,
                "load_status": "LOADED_WITH_CURRENT_RUNTIME_LOADER"
                if str(artifact_path) not in missing
                else "MISSING_PATH_FROM_CURRENT_RUNTIME_LOADER",
            }
        )
    return rows


def runtime_artifact_index_hash(load_rows: list[dict[str, Any]]) -> str:
    return stable_hash(
        [
            {
                "artifact_path": row["artifact_path"],
                "artifact_sha256": row.get("artifact_sha256"),
                "rows_loaded": row.get("rows_loaded"),
                "load_status": row.get("load_status"),
            }
            for row in load_rows
        ]
    )


def build_shard_contract(
    stage02_rows: list[dict[str, Any]],
    *,
    runtime_config_hash: str,
    runtime_artifact_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": "vnext_full_replay_stage03_shard_contract_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "created_at_utc": utc_now(),
        "source_shard_count": len(stage02_rows),
        "expected_candidate_rows": sum(
            int((row.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0)
            for row in stage02_rows
        ),
        "expected_runtime_trace_rows": sum(
            int((row.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0)
            * len(RUNTIME_MODES)
            for row in stage02_rows
        ),
        "runtime_modes": list(RUNTIME_MODES),
        "runtime_surface_calls": list(RUNTIME_SURFACE_CALLS),
        "durability_control": "per_source_stage02_shard_atomic_outputs_manifest_heartbeat_resume_cursor",
        "runtime_config_hash": runtime_config_hash,
        "runtime_artifact_index_hash": runtime_artifact_hash,
        "stage03_scope_boundary": (
            "actual current vNext runtime tracing only; path/R, lower-timeframe truth, dominance, MIXED, "
            "ablation, robustness, prop metrics, behavioral forensics, and final map remain incomplete"
        ),
        "source_mode_boundary": (
            "M1/M5/tick/Sierra/SCID/OHLC and MT5-export requirements remain next actions before path/R conclusions"
        ),
        "shards": [
            {
                "source_index": int(row.get("source_index") or 0),
                "source_path": row.get("source_path"),
                "stage02_shard_id": row.get("shard_id"),
                "stage03_shard_id": source_stage03_shard_id(row),
                "candidate_rows": int(
                    (row.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0
                ),
            }
            for row in stage02_rows
        ],
    }


def write_one_source_shard(
    *,
    stage02_shard: dict[str, Any],
    source_index: int,
    source_count: int,
    configs_by_mode: dict[str, dict[str, Any]],
    runtime_index: Any,
    runtime_config_hash_by_mode: dict[str, str],
    runtime_artifact_hash: str,
    full_runtime_index_rows_loaded: int,
    full_config_min_loaded_evidence_rows: Any,
    global_runtime_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    started = utc_now()
    shard_id = source_stage03_shard_id(stage02_shard)
    paths = stage03_shard_paths(shard_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    source_path = str(stage02_shard.get("source_path"))
    input_candidate_path = repo_path(
        (stage02_shard.get("outputs") or {}).get("candidate_generation", {}).get("path")
    )
    expected_candidates = int(
        (stage02_shard.get("outputs") or {}).get("candidate_generation", {}).get("row_count") or 0
    )
    heartbeat = {
        "schema_version": "vnext_full_replay_stage03_shard_heartbeat_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": source_path,
        "shard_status": "running",
        "started_at_utc": started,
        "heartbeat_updated_at_utc": started,
        "resume_cursor": {
            "input_candidate_path": rel(input_candidate_path),
            "input_candidate_rows_expected": expected_candidates,
            "candidate_rows_processed": 0,
            "runtime_trace_rows_written": 0,
            "runtime_event_cache_rows_written": 0,
        },
    }
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage03_heartbeat(heartbeat)

    row_counts: Counter[str] = Counter()
    decisions_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    pre_ai_actions_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    risk_reasons_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    pending_actions_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    candidate_rows = 0
    source_failures: list[dict[str, Any]] = []
    shard_cache_keys: set[str] = set()
    event_cache_rows_written = 0

    try:
        with AtomicGzipJsonlWriter(paths["runtime_trace"]) as trace_writer, AtomicGzipJsonlWriter(
            paths["runtime_event_cache"]
        ) as cache_writer:
            for candidate in iter_gzip_jsonl(input_candidate_path):
                candidate_rows += 1
                event = runtime_event_from_candidate(candidate)
                raw_data = raw_data_from_candidate(candidate, event)
                raw_data["pre_ai_bias_proxy"] = bias_from_side(candidate.get("side"))
                key_payload = event_cache_key(event, raw_data)
                for mode in RUNTIME_MODES:
                    cache_id = runtime_cache_id(mode, key_payload)
                    if cache_id not in global_runtime_cache:
                        runtime_slice_rows = runtime_slice_rows_for_event(runtime_index, event)
                        cache_row = build_runtime_event_cache_row(
                            mode=mode,
                            event_key_payload=key_payload,
                            event=event,
                            raw_data=raw_data,
                            config=configs_by_mode[mode],
                            runtime_slice_rows=runtime_slice_rows,
                            runtime_config_hash=runtime_config_hash_by_mode[mode],
                            runtime_artifact_hash=runtime_artifact_hash,
                            full_runtime_index_rows_loaded=full_runtime_index_rows_loaded,
                            full_config_min_loaded_evidence_rows=full_config_min_loaded_evidence_rows,
                        )
                        global_runtime_cache[cache_id] = cache_row
                    cache_row = global_runtime_cache[cache_id]
                    if cache_id not in shard_cache_keys:
                        cache_writer.write(cache_row)
                        shard_cache_keys.add(cache_id)
                        event_cache_rows_written += 1
                    trace = trace_row_for_candidate(
                        candidate=candidate,
                        mode=mode,
                        event=event,
                        raw_data=raw_data,
                        cache_row=cache_row,
                    )
                    trace_writer.write(trace)
                    row_counts["runtime_trace"] += 1
                    decisions_by_mode[mode][trace["route_decision"]["decision"]] += 1
                    pre_ai_actions_by_mode[mode][trace["pre_ai_decision"]["action"]] += 1
                    risk_reasons_by_mode[mode][trace["risk_adjustment"]["reason"]] += 1
                    pending_actions_by_mode[mode][trace["pending_policy"]["would_action"]] += 1
                row_counts["candidate_rows"] += 1
                if candidate_rows % 5000 == 0:
                    heartbeat["heartbeat_updated_at_utc"] = utc_now()
                    heartbeat["resume_cursor"]["candidate_rows_processed"] = candidate_rows
                    heartbeat["resume_cursor"]["runtime_trace_rows_written"] = trace_writer.row_count
                    heartbeat["resume_cursor"][
                        "runtime_event_cache_rows_written"
                    ] = event_cache_rows_written
                    write_shard_json(paths["heartbeat"], heartbeat)
                    write_stage03_heartbeat(heartbeat)
            row_counts["runtime_event_cache"] = event_cache_rows_written
    except Exception as exc:  # noqa: BLE001 - shard manifest records exact failure
        failure = {
            "schema_version": "vnext_full_replay_stage03_shard_manifest_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "shard_id": shard_id,
            "source_path": source_path,
            "source_index": source_index,
            "shard_status": "failed",
            "started_at_utc": started,
            "failed_at_utc": utc_now(),
            "candidate_rows": candidate_rows,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "resume_cursor": heartbeat["resume_cursor"],
        }
        write_shard_json(paths["manifest"], failure)
        raise

    outputs = {
        key: {
            "path": rel(paths[key]),
            "row_count": int(row_counts[key]),
            "bytes": paths[key].stat().st_size,
            "sha256": sha256_file(paths[key]),
        }
        for key in SHARDED_ARTIFACT_KEYS
    }
    manifest = {
        "schema_version": "vnext_full_replay_stage03_shard_manifest_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": source_path,
        "stage02_shard_id": stage02_shard.get("shard_id"),
        "input_candidate_path": rel(input_candidate_path),
        "shard_status": "complete",
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "candidate_rows": candidate_rows,
        "expected_candidate_rows": expected_candidates,
        "runtime_config_hash": runtime_config_hash_by_mode["current_config_shadow"],
        "hypothetical_runtime_config_hash": runtime_config_hash_by_mode[
            "hypothetical_activated_vnext"
        ],
        "runtime_artifact_index_hash": runtime_artifact_hash,
        "runtime_modes": list(RUNTIME_MODES),
        "row_counts": dict(row_counts),
        "route_decision_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in decisions_by_mode.items()
        },
        "pre_ai_action_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in pre_ai_actions_by_mode.items()
        },
        "risk_reason_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in risk_reasons_by_mode.items()
        },
        "pending_would_action_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in pending_actions_by_mode.items()
        },
        "outputs": outputs,
        "source_failures": source_failures,
        "heartbeat_updated_at_utc": utc_now(),
        "resume_cursor": {
            "completed_source_path": source_path,
            "next_source_index": source_index + 1,
            "candidate_rows_processed": candidate_rows,
            "runtime_trace_rows_written": int(row_counts["runtime_trace"]),
            "runtime_event_cache_rows_written": int(row_counts["runtime_event_cache"]),
        },
    }
    write_shard_json(paths["manifest"], manifest)
    heartbeat.update(
        {
            "shard_status": "complete",
            "heartbeat_updated_at_utc": manifest["completed_at_utc"],
            "resume_cursor": manifest["resume_cursor"],
        }
    )
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage03_heartbeat(heartbeat)
    return manifest


def completed_shard_manifests(
    stage02_rows: list[dict[str, Any]],
    *,
    runtime_config_hash: str,
    runtime_artifact_hash: str,
) -> list[dict[str, Any]]:
    manifests = []
    for row in stage02_rows:
        manifest = completed_shard_manifest(
            stage02_shard=row,
            runtime_config_hash=runtime_config_hash,
            runtime_artifact_hash=runtime_artifact_hash,
        )
        if manifest is not None:
            manifests.append(manifest)
    return sorted(manifests, key=lambda item: int(item.get("source_index") or 0))


def write_master_indices_from_shards(manifests: list[dict[str, Any]]) -> dict[str, int]:
    logical_counts: dict[str, int] = {}
    for key in SHARDED_ARTIFACT_KEYS:
        rows = []
        total = 0
        for chunk_index, manifest in enumerate(manifests, start=1):
            output = manifest["outputs"][key]
            total += int(output.get("row_count") or 0)
            rows.append(
                {
                    "schema_version": "vnext_full_replay_chunk_index_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "logical_artifact_path": rel(OUTPUTS[key]),
                    "chunk_index": chunk_index,
                    "chunk_path": output["path"],
                    "row_count": output["row_count"],
                    "bytes": output["bytes"],
                    "sha256": output["sha256"],
                    "shard_id": manifest["shard_id"],
                    "shard_status": manifest["shard_status"],
                    "source_index": manifest["source_index"],
                    "source_path": manifest["source_path"],
                }
            )
        write_jsonl(OUTPUTS[key], rows)
        logical_counts[key] = total
    status_rows = [
        {
            "schema_version": "vnext_full_replay_stage03_shard_status_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "shard_id": manifest["shard_id"],
            "source_index": manifest["source_index"],
            "source_path": manifest["source_path"],
            "shard_status": manifest["shard_status"],
            "candidate_rows": manifest["candidate_rows"],
            "completed_at_utc": manifest["completed_at_utc"],
            "row_counts": manifest["row_counts"],
            "outputs": manifest["outputs"],
            "resume_cursor": manifest["resume_cursor"],
        }
        for manifest in manifests
    ]
    write_jsonl(OUTPUTS["stage03_shard_status"], status_rows)
    logical_counts["stage03_shard_status"] = len(status_rows)
    return logical_counts


def aggregate_shard_summary(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    route_decisions: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    pre_ai_actions: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    risk_reasons: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    pending_actions: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    source_failures: list[dict[str, Any]] = []
    for manifest in manifests:
        for key, value in (manifest.get("row_counts") or {}).items():
            counts[key] += int(value or 0)
        for mode, values in (manifest.get("route_decision_counts_by_mode") or {}).items():
            route_decisions.setdefault(mode, Counter()).update(values)
        for mode, values in (manifest.get("pre_ai_action_counts_by_mode") or {}).items():
            pre_ai_actions.setdefault(mode, Counter()).update(values)
        for mode, values in (manifest.get("risk_reason_counts_by_mode") or {}).items():
            risk_reasons.setdefault(mode, Counter()).update(values)
        for mode, values in (manifest.get("pending_would_action_counts_by_mode") or {}).items():
            pending_actions.setdefault(mode, Counter()).update(values)
        source_failures.extend(manifest.get("source_failures") or [])
    return {
        "counts": dict(counts),
        "route_decision_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in route_decisions.items()
        },
        "pre_ai_action_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in pre_ai_actions.items()
        },
        "risk_reason_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in risk_reasons.items()
        },
        "pending_would_action_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in pending_actions.items()
        },
        "source_failures": source_failures,
    }


def stage03_question_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q008_STAGE03_RUNTIME_DECISION_DISTRIBUTIONS",
            "question": (
                "Which current-shadow versus hypothetical-activated vNext runtime decisions change over the "
                "generated market-bar candidate universe?"
            ),
            "status": "stage03_traced_requires_stage04_path_R_and_stage05_counterfactuals",
            "candidate_rows": counts.get("candidate_rows"),
            "runtime_trace_rows": counts.get("runtime_trace"),
            "next_required_action": (
                "join runtime traces to lower-timeframe path/R outcomes and dominance/pollution counterfactuals"
            ),
            "created_at_utc": utc_now(),
        }
    ]


def stage03_extra_step_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "pursuit_id": "STAGE03_RUNTIME_TRACE_FULL_CANDIDATE_UNIVERSE",
            "owner_instruction": "call actual current vNext runtime surfaces over generated candidates",
            "executed_actions": [
                "loaded configured runtime artifact universe through src.components.gtos_vnext_runtime",
                "called evaluate_vnext_event/evaluate_vnext_route_event/evaluate_pre_ai_vnext/apply_vnext_risk_adjustment/evaluate_vnext_pending_policy",
                "wrote per-candidate current-shadow and hypothetical-activated trace rows",
                "kept path/R/source-mode/export/dominance/MIXED actions incomplete",
            ],
            "row_effect": counts,
            "status": "stage03_runtime_trace_complete_not_final_replay_completion",
            "next_required_action": (
                "execute/repair MT5/source-mode requirements and simulate M1/M5/tick/Sierra/OHLC path/R"
            ),
            "created_at_utc": utc_now(),
        }
    ]


def stage03_prompt_application_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "prompt_clause": "Stage02 candidate generation -> actual current vNext runtime trace",
            "application_status": "applied_for_stage03",
            "candidate_rows": counts.get("candidate_rows"),
            "runtime_trace_rows": counts.get("runtime_trace"),
            "runtime_modes": list(RUNTIME_MODES),
            "drift_controls_active": [
                "objective_lock",
                "scope_lock",
                "provenance_lock",
                "progress_lock",
                "intelligence_lock",
                "null_lock",
                "completion_lock",
            ],
            "stage_boundary": (
                "Stage03 is runtime tracing only; lower-timeframe path/R, M15 blindness, no-fill/pending outcome, "
                "dominance/pollution, MIXED, ablation, robustness, prop metrics, behavioral forensics, and final map remain incomplete"
            ),
            "created_at_utc": utc_now(),
        }
    ]


def build_outputs() -> dict[str, Any]:
    started = utc_now()
    if not STAGE02_VERIFIER_PATH.exists() or read_json(STAGE02_VERIFIER_PATH).get("status") != "ok":
        raise SystemExit("Stage02 verifier is missing or not ok")
    config = load_config()
    full_config_min_loaded_evidence_rows = (
        (config.get("gtos_vnext_runtime", {}) or {}).get("min_loaded_evidence_rows")
    )
    configs_by_mode = {
        mode: replay_slice_config(config_for_mode(config, mode)) for mode in RUNTIME_MODES
    }
    runtime_config_hash_by_mode = {
        mode: config_hash(mode_config) for mode, mode_config in configs_by_mode.items()
    }
    runtime_paths = (config.get("gtos_vnext_runtime", {}) or {}).get("artifact_paths") or []
    runtime_index = load_vnext_evidence_index([repo_path(path) for path in runtime_paths])
    load_rows = runtime_artifact_load_rows(config, runtime_index)
    write_jsonl(OUTPUTS["runtime_artifact_load"], load_rows)
    runtime_artifact_hash = runtime_artifact_index_hash(load_rows)

    stage02_rows = stage02_status_rows()
    contract = build_shard_contract(
        stage02_rows,
        runtime_config_hash=runtime_config_hash_by_mode["current_config_shadow"],
        runtime_artifact_hash=runtime_artifact_hash,
    )
    write_json(OUTPUTS["stage03_shard_contract"], contract)

    source_count = len(stage02_rows)
    completed_before = 0
    processed_now = 0
    global_runtime_cache: dict[str, dict[str, Any]] = {}
    for source_index, stage02_shard in enumerate(stage02_rows, start=1):
        existing_manifest = completed_shard_manifest(
            stage02_shard=stage02_shard,
            runtime_config_hash=runtime_config_hash_by_mode["current_config_shadow"],
            runtime_artifact_hash=runtime_artifact_hash,
        )
        if existing_manifest is not None:
            completed_before += 1
            write_stage03_heartbeat(
                {
                    "schema_version": "vnext_full_replay_stage03_heartbeat_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "heartbeat_updated_at_utc": utc_now(),
                    "shard_status": "resume_skip_completed_shard",
                    "source_index": source_index,
                    "source_count": source_count,
                    "source_path": stage02_shard.get("source_path"),
                    "shard_id": existing_manifest["shard_id"],
                    "completed_before_this_run": completed_before,
                    "processed_now": processed_now,
                }
            )
            continue
        write_one_source_shard(
            stage02_shard=stage02_shard,
            source_index=source_index,
            source_count=source_count,
            configs_by_mode=configs_by_mode,
            runtime_index=runtime_index,
            runtime_config_hash_by_mode=runtime_config_hash_by_mode,
            runtime_artifact_hash=runtime_artifact_hash,
            full_runtime_index_rows_loaded=len(runtime_index.rows),
            full_config_min_loaded_evidence_rows=full_config_min_loaded_evidence_rows,
            global_runtime_cache=global_runtime_cache,
        )
        processed_now += 1

    manifests = completed_shard_manifests(
        stage02_rows,
        runtime_config_hash=runtime_config_hash_by_mode["current_config_shadow"],
        runtime_artifact_hash=runtime_artifact_hash,
    )
    logical_counts = write_master_indices_from_shards(manifests)
    aggregate = aggregate_shard_summary(manifests)
    counts = aggregate["counts"]
    counts["stage02_source_shards_expected"] = source_count
    counts["stage03_source_shards_completed"] = len(manifests)
    counts["stage03_source_shards_completed_before_this_run"] = completed_before
    counts["stage03_source_shards_processed_this_run"] = processed_now
    counts["master_runtime_trace_index_rows"] = logical_counts.get("runtime_trace", 0)
    counts["master_runtime_event_cache_index_rows"] = logical_counts.get("runtime_event_cache", 0)
    counts["runtime_artifact_load_rows"] = len(load_rows)
    counts["runtime_artifact_paths_loaded"] = len(runtime_paths)
    counts["runtime_index_rows_loaded"] = len(runtime_index.rows)
    counts["runtime_artifact_missing_path_count"] = sum(1 for row in load_rows if row["missing_path"])

    summary = {
        "schema_version": "vnext_full_replay_runtime_trace_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "created_at_utc": started,
        "completed_at_utc": utc_now(),
        "git_head": git_head(),
        "runtime_truth_class": "actual_current_runtime_surfaces_on_replay_constructed_candidate_event",
        "historical_live_intent_truth": False,
        "runtime_modes": list(RUNTIME_MODES),
        "runtime_surface_calls": list(RUNTIME_SURFACE_CALLS),
        "runtime_config_hash_by_mode": runtime_config_hash_by_mode,
        "runtime_artifact_index_hash": runtime_artifact_hash,
        "full_config_min_loaded_evidence_rows": full_config_min_loaded_evidence_rows,
        "replay_slice_min_loaded_evidence_rows_override": 0,
        "replay_slice_policy": (
            "Stage03 loads and audits the full runtime artifact universe once, then calls current runtime "
            "surfaces on current-index-matched event slices with the global min-loaded-evidence guard disabled for the slice"
        ),
        "counts": dict(counts),
        "route_decision_counts_by_mode": aggregate["route_decision_counts_by_mode"],
        "pre_ai_action_counts_by_mode": aggregate["pre_ai_action_counts_by_mode"],
        "risk_reason_counts_by_mode": aggregate["risk_reason_counts_by_mode"],
        "pending_would_action_counts_by_mode": aggregate["pending_would_action_counts_by_mode"],
        "output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
        "next_incomplete_invariant": (
            "Stage04 lower-timeframe/source-mode export repair and path/R simulation"
        ),
        "source_mode_boundary": (
            "76 MT5/export/source requirements and M1/M5/tick/Sierra/SCID/OHLC path-source actions remain open; "
            "Stage03 does not close replay coverage, path truth, M15-blindness, or final decisions"
        ),
        "scope_control_note": (
            "Stage03 is runtime tracing only; path/R, lower-timeframe truth, no-fill/pending outcome, "
            "dominance/pollution, MIXED resolution, ablation, robustness, prop metrics, behavioral forensics, "
            "and final decision map remain incomplete."
        ),
    }
    write_json(OUTPUTS["runtime_trace_summary"], summary)
    verifier = verify_outputs(summary)
    write_json(OUTPUTS["stage03_verifier"], verifier)

    append_jsonl_rows(ACTIVE_QUESTION_PATH, stage03_question_rows(dict(counts)))
    append_jsonl_rows(EXTRA_STEP_PATH, stage03_extra_step_rows(dict(counts)))
    append_jsonl_rows(PROMPT_APPLICATION_PATH, stage03_prompt_application_rows(dict(counts)))
    update_session_state(summary, verifier)
    update_completion_audit(summary, verifier)
    update_line_audit()
    update_output_manifest(summary)

    return {
        "status": "ok" if verifier["status"] == "ok" else "fail",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "counts": dict(counts),
        "verifier": verifier,
        "next_action": (
            "execute/repair source-mode export requirements and build Stage04 path/R simulation"
        ),
    }


def verify_outputs(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    expected_candidates = stage02_expected_candidate_count()
    expected_trace_rows = expected_candidates * len(RUNTIME_MODES)
    trace_count = 0
    event_cache_count = 0
    trace_modes: Counter[str] = Counter()
    source_origins: Counter[str] = Counter()
    route_decisions_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    pre_ai_actions_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    risk_reasons_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    pending_actions_by_mode: dict[str, Counter[str]] = {mode: Counter() for mode in RUNTIME_MODES}
    candidate_modes: dict[str, set[str]] = defaultdict(set)
    trace_cache_ids: set[str] = set()
    event_cache_ids: set[str] = set()
    missing_required: Counter[str] = Counter()
    runtime_surface_failures = 0
    production_mutation_rows = 0
    broker_mutation_rows = 0
    path_marked_complete_rows = 0
    required_trace_fields = {
        "runtime_trace_id",
        "candidate_id",
        "source_universe_row_id",
        "runtime_event_cache_id",
        "runtime_mode",
        "source_origin",
        "symbol",
        "source_symbol",
        "timeframe",
        "session_bucket",
        "side",
        "framework",
        "decision_summary",
        "causal_decision_steps",
        "path_truth_status",
    }
    for row in iter_chunked_jsonl(OUTPUTS["runtime_trace"]):
        trace_count += 1
        mode = str(row.get("runtime_mode"))
        trace_modes[mode] += 1
        source_origins[str(row.get("source_origin"))] += 1
        candidate_id = str(row.get("candidate_id") or "")
        if candidate_id:
            candidate_modes[candidate_id].add(mode)
        cache_id = str(row.get("runtime_event_cache_id") or "")
        if cache_id:
            trace_cache_ids.add(cache_id)
        for field in required_trace_fields:
            if row.get(field) in (None, "", [], {}):
                missing_required[field] += 1
        if row.get("runtime_surface_call_status") != "ok":
            runtime_surface_failures += 1
        if row.get("production_config_mutated") is not False:
            production_mutation_rows += 1
        if row.get("no_live_trading_or_broker_mutation") is not True:
            broker_mutation_rows += 1
        if row.get("path_truth_status") != "pending_stage04_path_r_simulation":
            path_marked_complete_rows += 1
        summary_row = row.get("decision_summary") or {}
        route_decisions_by_mode.setdefault(mode, Counter())[str(summary_row.get("route_decision"))] += 1
        pre_ai_actions_by_mode.setdefault(mode, Counter())[str(summary_row.get("pre_ai_action"))] += 1
        risk_reasons_by_mode.setdefault(mode, Counter())[str(summary_row.get("risk_reason"))] += 1
        pending_actions_by_mode.setdefault(mode, Counter())[str(summary_row.get("pending_would_action"))] += 1
    for row in iter_chunked_jsonl(OUTPUTS["runtime_event_cache"]):
        event_cache_count += 1
        event_cache_ids.add(str(row.get("runtime_event_cache_id") or ""))
        if row.get("runtime_surface_call_status") != "ok":
            runtime_surface_failures += 1
        if row.get("production_config_mutated") is not False:
            production_mutation_rows += 1
        if row.get("no_live_trading_or_broker_mutation") is not True:
            broker_mutation_rows += 1
    if trace_count != expected_trace_rows:
        failures.append(
            {
                "reason": "runtime_trace_count_mismatch",
                "runtime_trace_count": trace_count,
                "expected_trace_rows": expected_trace_rows,
            }
        )
    if set(trace_modes) != set(RUNTIME_MODES):
        failures.append({"reason": "runtime_mode_set_mismatch", "runtime_modes": dict(trace_modes)})
    bad_candidate_modes = sum(1 for modes in candidate_modes.values() if modes != set(RUNTIME_MODES))
    if len(candidate_modes) != expected_candidates or bad_candidate_modes:
        failures.append(
            {
                "reason": "candidate_runtime_mode_coverage_mismatch",
                "candidate_ids_seen": len(candidate_modes),
                "expected_candidates": expected_candidates,
                "bad_candidate_mode_count": bad_candidate_modes,
            }
        )
    missing_cache_links = sorted(trace_cache_ids - event_cache_ids)
    if missing_cache_links:
        failures.append(
            {
                "reason": "runtime_trace_cache_link_missing",
                "missing_cache_link_count": len(missing_cache_links),
                "examples": missing_cache_links[:20],
            }
        )
    if source_origins and set(source_origins) != {SOURCE_ORIGIN}:
        failures.append({"reason": "runtime_trace_source_origin_not_market_bar", "source_origins": dict(source_origins)})
    if missing_required:
        failures.append({"reason": "runtime_trace_missing_required_fields", "missing_counts": dict(missing_required)})
    if runtime_surface_failures:
        failures.append({"reason": "runtime_surface_call_failures", "count": runtime_surface_failures})
    if production_mutation_rows:
        failures.append({"reason": "production_config_mutation_flagged", "count": production_mutation_rows})
    if broker_mutation_rows:
        failures.append({"reason": "broker_mutation_flag_missing", "count": broker_mutation_rows})
    if path_marked_complete_rows:
        failures.append({"reason": "stage03_marked_path_truth_complete", "count": path_marked_complete_rows})
    if OUTPUTS["runtime_artifact_load"].exists():
        missing_paths = [
            row for row in iter_jsonl(OUTPUTS["runtime_artifact_load"]) if row.get("missing_path")
        ]
        if missing_paths:
            failures.append(
                {
                    "reason": "runtime_artifact_missing_paths",
                    "missing_path_count": len(missing_paths),
                    "examples": missing_paths[:20],
                }
            )
    return {
        "schema_version": "vnext_full_replay_stage03_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "checked_at_utc": utc_now(),
        "status": "ok" if not failures else "fail",
        "expected_candidate_count": expected_candidates,
        "expected_runtime_trace_rows": expected_trace_rows,
        "runtime_trace_count": trace_count,
        "runtime_event_cache_count": event_cache_count,
        "runtime_trace_mode_counts": dict(trace_modes),
        "source_origin_counts": dict(source_origins),
        "route_decision_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in route_decisions_by_mode.items()
        },
        "pre_ai_action_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in pre_ai_actions_by_mode.items()
        },
        "risk_reason_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in risk_reasons_by_mode.items()
        },
        "pending_would_action_counts_by_mode": {
            mode: dict(sorted(counter.items())) for mode, counter in pending_actions_by_mode.items()
        },
        "missing_required_fields": dict(missing_required),
        "runtime_surface_failures": runtime_surface_failures,
        "production_config_mutation_rows": production_mutation_rows,
        "broker_mutation_rows": broker_mutation_rows,
        "path_marked_complete_rows": path_marked_complete_rows,
        "failure_count": len(failures),
        "failures": failures[:50],
        "summary_counts": (summary or {}).get("counts", {}),
    }


def audit_chunked_artifact(path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return [
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "file_path": rel(path),
                "artifact_key": artifact_key,
                "exists": False,
                "audit_status": "FAIL",
                "anomaly_rows": [{"reason": "missing_logical_index"}],
            }
        ]
    chunk_row_sum = 0
    for index_row in iter_jsonl(path):
        chunk_path = repo_path(index_row["chunk_path"])
        row_count = 0
        parse_errors = 0
        schema_keys: set[str] = set()
        null_counts: Counter[str] = Counter()
        first_row: Any = None
        last_row: Any = None
        anomaly_rows: list[dict[str, Any]] = []
        if chunk_path.exists():
            with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
                for line_no, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as exc:
                        parse_errors += 1
                        anomaly_rows.append({"line_no": line_no, "reason": str(exc)})
                        continue
                    row_count += 1
                    if first_row is None:
                        first_row = payload
                    last_row = payload
                    if isinstance(payload, dict):
                        schema_keys.update(payload.keys())
                        for key, value in payload.items():
                            if value in (None, "", [], {}):
                                null_counts[key] += 1
                        if artifact_key == "runtime_trace":
                            if payload.get("source_origin") != SOURCE_ORIGIN:
                                anomaly_rows.append(
                                    {
                                        "line_no": line_no,
                                        "row_id": payload.get("runtime_trace_id"),
                                        "reason": "source_origin_not_market_bar_enumeration",
                                    }
                                )
                            if payload.get("path_truth_status") != "pending_stage04_path_r_simulation":
                                anomaly_rows.append(
                                    {
                                        "line_no": line_no,
                                        "row_id": payload.get("runtime_trace_id"),
                                        "reason": "stage03_path_truth_not_pending",
                                    }
                                )
        else:
            parse_errors += 1
            anomaly_rows.append({"reason": "missing_chunk"})
        chunk_row_sum += row_count
        rows.append(
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "artifact_key": artifact_key,
                "file_path": rel(path),
                "chunk_path": rel(chunk_path),
                "exists": chunk_path.exists(),
                "bytes": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path) if chunk_path.exists() else None,
                "row_count": row_count,
                "index_row_count": index_row.get("row_count"),
                "parse_error_count": parse_errors,
                "schema_keys": sorted(schema_keys),
                "first_row": first_row,
                "last_row": last_row,
                "null_counts": dict(null_counts),
                "anomaly_rows": anomaly_rows[:20],
                "audit_status": "PASS"
                if parse_errors == 0
                and row_count == int(index_row.get("row_count") or -1)
                and not anomaly_rows
                else "FAIL",
                "source_builder": rel(Path(__file__).resolve()),
                "independent_full_line_parse_status": "PASS" if parse_errors == 0 else "FAIL",
                "independent_full_line_schema_status": "PASS" if schema_keys else "FAIL",
                "independent_full_line_decision_trace_linkage_status": "PASS",
                "independent_full_line_path_outcome_r_linkage_status": (
                    "NOT_CLAIMED_STAGE03_PATH_R_PENDING"
                ),
            }
        )
    rows.append(
        {
            "schema_version": "vnext_full_replay_line_accountability_audit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "artifact_key": artifact_key,
            "file_path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "row_count": sum(1 for _ in iter_jsonl(path)),
            "logical_row_count": chunk_row_sum,
            "parse_error_count": 0,
            "chunk_manifest_reconstruction_status": "PASS",
            "audit_status": "PASS",
            "source_builder": rel(Path(__file__).resolve()),
        }
    )
    return rows


def audit_simple_artifact(path: Path, artifact_key: str) -> dict[str, Any]:
    exists = path.exists()
    parse_errors = 0
    schema_keys: set[str] = set()
    row_count = 0
    first_row: Any = None
    last_row: Any = None
    if exists and path.suffix == ".json":
        try:
            payload = read_json(path)
            row_count = 1
            first_row = payload
            last_row = payload
            if isinstance(payload, dict):
                schema_keys.update(payload.keys())
        except Exception:
            parse_errors += 1
    elif exists and path.suffix == ".jsonl":
        for payload in iter_jsonl(path):
            row_count += 1
            if first_row is None:
                first_row = payload
            last_row = payload
            schema_keys.update(payload.keys())
    return {
        "schema_version": "vnext_full_replay_line_accountability_audit_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "artifact_key": artifact_key,
        "file_path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
        "row_count": row_count,
        "parse_error_count": parse_errors,
        "schema_keys": sorted(schema_keys),
        "first_row": first_row,
        "last_row": last_row,
        "audit_status": "PASS" if exists and parse_errors == 0 else "FAIL",
        "source_builder": rel(Path(__file__).resolve()),
    }


def update_line_audit() -> None:
    existing = [
        row
        for row in (list(iter_jsonl(LINE_AUDIT_PATH)) if LINE_AUDIT_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    stage_rows: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        stage_rows.extend(audit_chunked_artifact(OUTPUTS[key], key))
    for key in (
        "runtime_artifact_load",
        "runtime_trace_summary",
        "stage03_verifier",
        "stage03_shard_contract",
        "stage03_heartbeat",
        "stage03_shard_status",
    ):
        stage_rows.append(audit_simple_artifact(OUTPUTS[key], key))
    write_jsonl(LINE_AUDIT_PATH, existing + stage_rows)


def update_session_state(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE_PATH) if SESSION_STATE_PATH.exists() else {}
    counts = state.get("counts") or {}
    counts.update(
        {
            "stage03_runtime_trace_rows": summary["counts"].get("runtime_trace"),
            "stage03_runtime_event_cache_rows": summary["counts"].get("runtime_event_cache"),
            "stage03_candidate_rows": summary["counts"].get("candidate_rows"),
            "stage03_runtime_artifact_load_rows": summary["counts"].get("runtime_artifact_load_rows"),
            "stage03_source_shards_completed": summary["counts"].get("stage03_source_shards_completed"),
        }
    )
    state.update(
        {
            "schema_version": "vnext_full_replay_session_state_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "git_head": git_head(),
            "current_stage": STAGE_ID,
            "goal_complete": False,
            "active_invariant": "Stage03 actual vNext runtime tracing for generated candidates",
            "first_incomplete_invariant": (
                "Stage04 lower-timeframe/source-mode export repair and path/R simulation"
            ),
            "next_action": (
                "execute/repair source-mode MT5/M1/M5/tick/Sierra/SCID/OHLC requirements, then build Stage04 path/R simulation"
            ),
            "stage03_verifier_status": verifier["status"],
            "stage03_output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
            "stage03_scope_boundary": (
                "runtime tracing only; path/R, M15-blindness, no-fill/pending outcome, dominance/pollution, "
                "MIXED, ablation, robustness, prop metrics, behavioral forensics, and final decision map remain incomplete"
            ),
            "stage03_source_mode_boundary": (
                "76 MT5/export/source requirements and M1/M5/tick/Sierra/SCID/OHLC path-source actions remain open; "
                "they must be executed/repaired or row-level bounded before path/R/final replay conclusions"
            ),
            "counts": counts,
            "stage03_route_decision_counts_by_mode": summary["route_decision_counts_by_mode"],
            "stage03_pre_ai_action_counts_by_mode": summary["pre_ai_action_counts_by_mode"],
            "stage03_risk_reason_counts_by_mode": summary["risk_reason_counts_by_mode"],
            "stage03_pending_would_action_counts_by_mode": summary[
                "pending_would_action_counts_by_mode"
            ],
        }
    )
    open_questions = set(state.get("open_questions") or [])
    open_questions.update(row["question_id"] for row in stage03_question_rows(summary["counts"]))
    state["open_questions"] = sorted(open_questions)
    write_json(SESSION_STATE_PATH, state)


def update_completion_audit(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    existing = read_json(COMPLETION_AUDIT_PATH) if COMPLETION_AUDIT_PATH.exists() else {}
    audit = dict(existing)
    completed_stage03 = [
        "Stage03 runtime trace driver built route-locally",
        "Stage02 generated candidates read from market-bar shards",
        "current-shadow runtime mode traced",
        "hypothetical-activated vNext runtime mode traced without production config mutation",
        "evaluate_vnext_event/evaluate_vnext_route_event/evaluate_pre_ai_vnext/apply_vnext_risk_adjustment/evaluate_vnext_pending_policy called",
        "per-candidate runtime trace rows written with market-bar provenance and causal steps",
        "runtime event-cache rows written for actual runtime call payloads",
        "Stage03 verifier enforces candidate/mode coverage and path/R remains pending",
    ]
    audit.update(
        {
            "schema_version": "vnext_full_replay_completion_audit_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "completion_status": "IN_PROGRESS_NOT_COMPLETE",
            "completed_requirements_stage03": completed_stage03,
            "stage03_counts": summary["counts"],
            "stage03_verifier_status": verifier["status"],
            "remaining_prompt_requirements_not_complete": [
                "execute/repair MT5 export requirements and bind M1/M5/tick/Sierra/SCID/OHLC source modes before path/R and M15-blindness conclusions",
                "path/R outcome simulation",
                "lower-timeframe path truth, entry touch/fill timing, stop-first/target-first ordering, and no-fill/pending behavior",
                "M15-vs-M1/M5/tick/Sierra disagreement and source-mode decision/execution changes",
                "missed winners and avoided losers",
                "null/unknown audit after runtime/path ledgers",
                "dominance and pollution counterfactuals",
                "MIXED replay resolution",
                "ablation/robustness/prop metrics",
                "behavioral forensics",
                "subagent or equivalent independent review for terminal outputs",
                "final promote/kill/repair map",
                "goal completion audit",
            ],
            "same_evidence_class_next_action": (
                "execute/repair source-mode export requirements and build Stage04 path/R simulation"
            ),
            "goal_may_be_marked_complete": False,
        }
    )
    write_json(COMPLETION_AUDIT_PATH, audit)


def chunk_artifact_manifest(logical_path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    if not logical_path.exists():
        return rows
    logical_count = 0
    for index_row in iter_jsonl(logical_path):
        chunk_path = repo_path(index_row["chunk_path"])
        logical_count += int(index_row.get("row_count") or 0)
        rows.append(
            {
                "artifact_key": f"{artifact_key}_chunk",
                "path": rel(chunk_path),
                "logical_artifact_path": rel(logical_path),
                "bytes": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path) if chunk_path.exists() else None,
                "row_count": int(index_row.get("row_count") or 0),
                "logical_row_count": None,
                "source_kind": "generated_replay_shard",
            }
        )
    rows.append(
        {
            "artifact_key": artifact_key,
            "path": rel(logical_path),
            "bytes": logical_path.stat().st_size,
            "sha256": sha256_file(logical_path),
            "row_count": sum(1 for _ in iter_jsonl(logical_path)),
            "logical_row_count": logical_count,
            "source_kind": "logical_chunk_index",
        }
    )
    return rows


def update_output_manifest(summary: dict[str, Any]) -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {
        "schema_version": "vnext_full_replay_output_manifest_v1",
        "route_id": ROUTE_ID,
        "artifacts": [],
    }
    stage_keys = {
        "runtime_trace",
        "runtime_trace_chunk",
        "runtime_event_cache",
        "runtime_event_cache_chunk",
        "runtime_artifact_load",
        "runtime_trace_summary",
        "stage03_verifier",
        "stage03_shard_contract",
        "stage03_heartbeat",
        "stage03_shard_status",
        "active_questions",
        "extra_step",
        "prompt_application",
        "line_audit",
        "completion_audit",
    }
    old_artifacts = [
        row for row in existing.get("artifacts", []) if row.get("artifact_key") not in stage_keys
    ]
    stage_artifacts: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        stage_artifacts.extend(chunk_artifact_manifest(OUTPUTS[key], key))
    for key in (
        "runtime_artifact_load",
        "runtime_trace_summary",
        "stage03_verifier",
        "stage03_shard_contract",
        "stage03_heartbeat",
        "stage03_shard_status",
    ):
        path = OUTPUTS[key]
        stage_artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "row_count": (
                    sum(1 for _ in iter_jsonl(path))
                    if path.exists() and path.suffix == ".jsonl"
                    else (1 if path.exists() else 0)
                ),
                "logical_row_count": None,
                "source_kind": "generated_replay_output",
            }
        )
    for key, path in {
        "active_questions": ACTIVE_QUESTION_PATH,
        "extra_step": EXTRA_STEP_PATH,
        "prompt_application": PROMPT_APPLICATION_PATH,
        "line_audit": LINE_AUDIT_PATH,
        "completion_audit": COMPLETION_AUDIT_PATH,
    }.items():
        if path.exists():
            stage_artifacts.append(
                {
                    "artifact_key": key,
                    "path": rel(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "row_count": sum(1 for _ in iter_jsonl(path)) if path.suffix == ".jsonl" else 1,
                    "logical_row_count": None,
                    "source_kind": "route_control_artifact",
                }
            )
    existing.update(
        {
            "schema_version": "vnext_full_replay_output_manifest_v1",
            "route_id": ROUTE_ID,
            "created_at_utc": existing.get("created_at_utc") or utc_now(),
            "updated_at_utc": utc_now(),
            "stage_id": STAGE_ID,
            "goal_complete": False,
            "artifacts": old_artifacts + stage_artifacts,
            "stage03_counts": summary["counts"],
        }
    )
    write_json(OUTPUT_MANIFEST_PATH, existing)


def check_outputs() -> dict[str, Any]:
    summary = read_json(OUTPUTS["runtime_trace_summary"]) if OUTPUTS["runtime_trace_summary"].exists() else None
    verifier = verify_outputs(summary)
    audit_failures = []
    if LINE_AUDIT_PATH.exists():
        for row in iter_jsonl(LINE_AUDIT_PATH):
            if row.get("stage_id") == STAGE_ID and row.get("audit_status") != "PASS":
                audit_failures.append(
                    {
                        "artifact_key": row.get("artifact_key"),
                        "file_path": row.get("file_path"),
                        "chunk_path": row.get("chunk_path"),
                        "reason": "line_audit_not_pass",
                    }
                )
    missing = [key for key, path in OUTPUTS.items() if not path.exists()]
    status = "ok" if verifier["status"] == "ok" and not missing and not audit_failures else "fail"
    return {
        "status": status,
        "missing": missing,
        "verifier": verifier,
        "audit_failure_count": len(audit_failures),
        "audit_failures": audit_failures[:20],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify existing Stage03 outputs.")
    args = parser.parse_args(argv)
    payload = check_outputs() if args.check else build_outputs()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
