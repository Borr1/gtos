"""Stage 05 dominance/pollution counterfactuals and MIXED resolution.

This route-local builder consumes Stage03 runtime traces plus Stage04 path/R
truth. It writes per-source durable shards with atomic temp-to-final
replacement. It does not change production config, prompts, broker/account
state, orders, deals, positions, history, or source data.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE_ID = "2026-05-24"
ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
STAGE_ID = "STAGE_05_DOMINANCE_POLLUTION_MIXED"
PREVIOUS_STAGE_ID = "STAGE_04_SOURCE_MODE_PATH_R"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


STAGE04_STATUS_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
STAGE04_VERIFIER_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_VERIFIER_{DATE_ID}.json"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_ID}.json"
COMPLETION_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_ID}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_{DATE_ID}.json"
ACTIVE_QUESTION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_ID}.jsonl"
EXTRA_STEP_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_EXTRA_STEP_PURSUIT_LEDGER_{DATE_ID}.jsonl"
PROMPT_APPLICATION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_ID}.jsonl"
LINE_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_{DATE_ID}.jsonl"

OUTPUTS = {
    "dominance_and_pollution": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_DOMINANCE_AND_POLLUTION_LEDGER_{DATE_ID}.jsonl"
    ),
    "mixed_resolution": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_MIXED_RESOLUTION_LEDGER_{DATE_ID}.jsonl"
    ),
    "mixed_resolution_summary": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_MIXED_RESOLUTION_SUMMARY_{DATE_ID}.json"
    ),
    "stage05_summary": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_DOMINANCE_POLLUTION_SUMMARY_{DATE_ID}.json"
    ),
    "stage05_verifier": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_VERIFIER_{DATE_ID}.json",
    "stage05_shard_contract": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_SHARD_CONTRACT_{DATE_ID}.json"
    ),
    "stage05_heartbeat": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_HEARTBEAT_{DATE_ID}.json",
    "stage05_shard_status": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
    ),
}

SHARD_DIR = ROUTE_DIR / "stage05_shards"
SHARDED_ARTIFACT_KEYS = ("dominance_and_pollution", "mixed_resolution")
COUNTERFACTUAL_VARIANTS = (
    "all_evidence",
    "dominant_family_removed",
    "broad_unanchored_removed",
    "stale_legacy_removed",
    "current_source_bound_only",
)
RUNTIME_SURFACES = ("route_decision", "pre_ai_decision", "risk_adjustment", "pending_policy")
PRICE_PATH_PRIORITY = (
    "tick_or_sierra_path_aware",
    "m1_path_aware",
    "m5_path_aware",
    "bar_close_m15",
    "ohlc_only_proxy",
)
SOURCE_REQUIRED_TOKENS = (
    "source_required",
    "source_requirement",
    "source_repair",
    "source_capture",
    "missing_source",
    "missing_denominator",
    "exact_r_missing",
    "broker_execution_geometry",
    "geometry_required",
)
STALE_LEGACY_TOKENS = (
    "legacy",
    "v2",
    "v3",
    "v4",
    "cascade",
    "paper_live_friction",
    "old_runtime",
)
BROAD_TOKENS = (
    "all_sides",
    "all_sessions",
    "all_markets",
    "all_available",
    "unmapped",
    "<blank>",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def repo_path(path: str | Path | None) -> Path:
    if path is None:
        return REPO_ROOT / "__missing__"
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(raw).hexdigest()


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


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


class AtomicGzipJsonlWriter:
    def __init__(self, final_path: Path) -> None:
        self.final_path = final_path
        self.tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
        self.count = 0
        self._handle: gzip.GzipFile | None = None

    def __enter__(self) -> "AtomicGzipJsonlWriter":
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = gzip.open(self.tmp_path, "wt", encoding="utf-8", newline="\n")
        return self

    def write(self, row: dict[str, Any]) -> None:
        if self._handle is None:
            raise RuntimeError("writer is not open")
        self._handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.count += 1

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._handle is not None:
            self._handle.close()
        if exc_type is None:
            self.tmp_path.replace(self.final_path)
        elif self.tmp_path.exists():
            self.tmp_path.unlink()


def write_stage05_heartbeat(payload: dict[str, Any]) -> None:
    write_json(OUTPUTS["stage05_heartbeat"], payload)


def write_shard_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)


def stage04_manifests() -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for row in iter_jsonl(STAGE04_STATUS_PATH):
        if row.get("shard_status") == "complete":
            manifests.append(row)
    return sorted(manifests, key=lambda row: int(row.get("source_index") or 0))


def source_inventory_hash(manifests: list[dict[str, Any]]) -> str:
    payload = [
        {
            "source_index": row.get("source_index"),
            "source_path": row.get("source_path"),
            "stage02_shard_id": row.get("stage02_shard_id"),
            "stage03_shard_id": row.get("stage03_shard_id"),
            "stage04_shard_id": row.get("shard_id"),
            "candidate_rows": row.get("candidate_rows"),
            "path_outcome_rows": (row.get("outputs") or {})
            .get("path_outcome_r", {})
            .get("row_count"),
        }
        for row in manifests
    ]
    return stable_hash(payload)


def source_stage05_shard_id(stage04_manifest: dict[str, Any]) -> str:
    payload = {
        "stage04_shard_id": stage04_manifest.get("shard_id"),
        "stage03_shard_id": stage04_manifest.get("stage03_shard_id"),
        "source_path": stage04_manifest.get("source_path"),
    }
    return stable_id("stage05src", payload, length=16)


def stage05_shard_paths(shard_id: str) -> dict[str, Path]:
    base = SHARD_DIR / shard_id
    return {
        "dominance_and_pollution": base / "dominance_and_pollution.jsonl.gz",
        "mixed_resolution": base / "mixed_resolution.jsonl.gz",
        "manifest": base / "manifest.json",
        "heartbeat": base / "heartbeat.json",
    }


def row_text(row: dict[str, Any]) -> str:
    keys = (
        "evidence_family",
        "source_component",
        "source_name",
        "source_role",
        "source_group",
        "action_class",
        "implementation_action",
        "system_surface",
        "loaded_from",
        "drill_through_path",
        "exact_r_status",
    )
    parts = [str(row.get(key) or "") for key in keys]
    event_scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
    parts.extend(str(value or "") for value in event_scope.values())
    return " ".join(parts).lower()


def token_hit(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def event_scope(row: dict[str, Any]) -> dict[str, Any]:
    scope = row.get("event_scope")
    return scope if isinstance(scope, dict) else {}


def scope_matches_event(scope: dict[str, Any], event: dict[str, Any]) -> bool:
    if not scope:
        return False
    symbol = str(event.get("symbol") or event.get("market") or "")
    source_symbol = str(event.get("source_symbol") or symbol)
    side = str(event.get("side") or "")
    timeframe = str(event.get("market_timeframe") or event.get("timeframe") or "")
    route_session = str(event.get("route_session") or event.get("session") or "")
    scope_symbol = str(scope.get("symbol") or scope.get("market") or "")
    scope_source = str(scope.get("source_symbol") or scope_symbol)
    scope_side = str(scope.get("side") or "")
    scope_tf = str(scope.get("market_timeframe") or scope.get("timeframe") or "")
    scope_session = str(scope.get("route_session") or scope.get("session") or "")
    symbol_ok = not scope_symbol or scope_symbol in {symbol, source_symbol} or scope_source in {
        symbol,
        source_symbol,
    }
    side_ok = not scope_side or not side or scope_side == side
    timeframe_ok = not scope_tf or not timeframe or scope_tf == timeframe
    session_ok = (
        not scope_session
        or not route_session
        or scope_session == route_session
        or scope_session.startswith(route_session)
        or route_session.startswith(scope_session)
    )
    return symbol_ok and side_ok and timeframe_ok and session_ok


def classify_evidence_row(row: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    text = row_text(row)
    scope = event_scope(row)
    broad = (
        not scope
        or token_hit(text, BROAD_TOKENS)
        or str(scope.get("side") or "").lower() in {"", "none", "all"}
        or str(scope.get("symbol") or scope.get("market") or "").lower() in {"", "none", "all"}
    )
    stale = token_hit(text, STALE_LEGACY_TOKENS)
    source_required = token_hit(text, SOURCE_REQUIRED_TOKENS)
    source_bound = scope_matches_event(scope, event) and not broad and not stale
    return {
        "broad_unanchored": broad,
        "stale_legacy": stale,
        "source_required": source_required,
        "current_source_bound": source_bound,
    }


def evidence_row_id(row: dict[str, Any]) -> str:
    for key in (
        "row_key",
        "numeric_result_row_id",
        "rejected_candidate_l2_value_runtime_row_id",
        "rejected_candidate_l2_value_row_id",
        "accepted_candidate_m1_fill_source_repair_runtime_row_id",
        "nofill_pending_lifecycle_runtime_row_id",
        "source_geometry_runtime_row_id",
        "source_repair_missing_denominator_runtime_row_id",
        "cp280_scorer_filter_router_runtime_row_id",
        "cp281_rule_replay_event_row_key",
        "frontier_action_id",
        "recommendation_unified_candidate_id",
    ):
        value = row.get(key)
        if value:
            return str(value)
    family = row.get("evidence_family") or "row"
    return f"{family}:{stable_hash(row)[:16]}"


def normalize_row_id(row_id: str) -> str:
    if ":" in row_id:
        return row_id.split(":", 1)[1]
    return row_id


def rows_from_surface_decision(decision_obj: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(decision_obj, dict):
        return []
    evidence = decision_obj.get("evidence")
    if isinstance(evidence, dict) and isinstance(evidence.get("rows"), list):
        return [row for row in evidence["rows"] if isinstance(row, dict)]
    if isinstance(decision_obj.get("rows"), list):
        return [row for row in decision_obj["rows"] if isinstance(row, dict)]
    return []


def evidence_counts_from_surface(decision_obj: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(decision_obj, dict):
        return {}
    evidence = decision_obj.get("evidence")
    if isinstance(evidence, dict):
        return {
            "decision_counts": evidence.get("decision_counts"),
            "evidence_family_counts": evidence.get("evidence_family_counts"),
            "source_component_counts": evidence.get("source_component_counts"),
            "action_class_counts": evidence.get("action_class_counts"),
            "matched_rows": evidence.get("matched_rows"),
            "matched_row_id_count": evidence.get("matched_row_id_count"),
            "rows_truncated": evidence.get("rows_truncated"),
        }
    return {}


def row_score(row: dict[str, Any], score_by_id: dict[str, dict[str, Any]]) -> float:
    rid = normalize_row_id(evidence_row_id(row))
    if rid in score_by_id:
        scored = score_by_id[rid]
        score = fnum(scored.get("score"))
        if score is not None and score != 0:
            return score
        effective_n = fnum(scored.get("effective_n"))
        decision = str(scored.get("row_decision") or row.get("decision") or "").upper()
        if effective_n is not None and decision == "AVOID":
            return -abs(effective_n)
        if effective_n is not None and decision == "FOLLOW":
            return abs(effective_n)
    metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
    for metric_name in ("proxy_score", "cost_adjusted_simulated_r", "stress_simulated_r"):
        metric = metrics.get(metric_name)
        if isinstance(metric, dict):
            value = fnum(metric.get("sum"))
            if value is not None and value != 0:
                return value
    value = fnum(row.get("proxy_score"))
    if value is not None and value != 0:
        return value
    decision = str(row.get("decision") or row.get("computed_decision") or "").upper()
    if decision == "AVOID":
        return -1.0
    if decision == "FOLLOW":
        return 1.0
    return 0.0


def score_rows(rows: list[dict[str, Any]], score_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    avoid_pressure = 0.0
    follow_pressure = 0.0
    mixed_rows = 0
    source_required_rows = 0
    for row in rows:
        decision = str(row.get("decision") or row.get("computed_decision") or "").upper()
        score = row_score(row, score_by_id)
        if decision == "MIXED":
            mixed_rows += 1
        if decision == "AVOID" or score < 0:
            avoid_pressure += abs(score) if score else 1.0
        elif decision == "FOLLOW" or score > 0:
            follow_pressure += abs(score) if score else 1.0
        if token_hit(row_text(row), SOURCE_REQUIRED_TOKENS):
            source_required_rows += 1
    if avoid_pressure > follow_pressure and avoid_pressure > 0:
        decision = "AVOID"
    elif follow_pressure > avoid_pressure and follow_pressure > 0:
        decision = "FOLLOW"
    elif avoid_pressure == 0 and follow_pressure == 0 and mixed_rows == 0:
        decision = "LEGACY"
    else:
        decision = "MIXED"
    if source_required_rows and decision == "LEGACY":
        decision = "MIXED"
    return {
        "decision": decision,
        "avoid_pressure": round(avoid_pressure, 12),
        "follow_pressure": round(follow_pressure, 12),
        "mixed_rows": mixed_rows,
        "source_required_rows": source_required_rows,
        "rows_selected": len(rows),
    }


def decision_resolution(surface_obj: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(surface_obj, dict):
        return {}
    evidence = surface_obj.get("evidence")
    if isinstance(evidence, dict) and isinstance(evidence.get("decision_resolution"), dict):
        return evidence["decision_resolution"]
    return {}


def score_map(surface_obj: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    resolution = decision_resolution(surface_obj)
    rows = resolution.get("row_scores")
    out: dict[str, dict[str, Any]] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("row_id") or "")
            if rid:
                out[normalize_row_id(rid)] = row
    return out


def dominant_row(
    rows: list[dict[str, Any]], score_by_id: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not rows:
        return None, {
            "dominant_row_id": None,
            "dominant_evidence_family": None,
            "dominant_source_component": None,
            "dominant_action_class": None,
            "dominant_decision": None,
            "dominant_score": None,
        }
    best = max(rows, key=lambda row: abs(row_score(row, score_by_id)))
    score = row_score(best, score_by_id)
    meta = {
        "dominant_row_id": evidence_row_id(best),
        "dominant_evidence_family": best.get("evidence_family"),
        "dominant_source_component": best.get("source_component"),
        "dominant_action_class": best.get("action_class"),
        "dominant_decision": best.get("decision") or best.get("computed_decision"),
        "dominant_score": score,
    }
    return best, meta


def variant_rows(
    variant: str,
    rows: list[dict[str, Any]],
    dominant_meta: dict[str, Any],
    event: dict[str, Any],
) -> list[dict[str, Any]]:
    if variant == "all_evidence":
        return rows
    if variant == "dominant_family_removed":
        family = dominant_meta.get("dominant_evidence_family")
        if not family:
            return rows
        return [row for row in rows if row.get("evidence_family") != family]
    if variant == "broad_unanchored_removed":
        return [
            row
            for row in rows
            if not classify_evidence_row(row, event).get("broad_unanchored")
        ]
    if variant == "stale_legacy_removed":
        return [row for row in rows if not classify_evidence_row(row, event).get("stale_legacy")]
    if variant == "current_source_bound_only":
        return [row for row in rows if classify_evidence_row(row, event).get("current_source_bound")]
    raise ValueError(f"unknown variant: {variant}")


def baseline_decision(surface: str, trace: dict[str, Any], cache: dict[str, Any]) -> str:
    if surface == "route_decision":
        return str((trace.get("route_decision") or {}).get("decision") or "LEGACY")
    if surface == "pre_ai_decision":
        return str((trace.get("pre_ai_decision") or {}).get("decision") or "LEGACY")
    if surface == "risk_adjustment":
        return str((trace.get("risk_adjustment") or {}).get("decision") or "LEGACY")
    if surface == "pending_policy":
        return str((trace.get("pending_policy") or {}).get("decision") or "LEGACY")
    return "LEGACY"


def baseline_action(surface: str, trace: dict[str, Any]) -> str | None:
    if surface == "pre_ai_decision":
        return (trace.get("pre_ai_decision") or {}).get("action")
    if surface == "pending_policy":
        return (trace.get("pending_policy") or {}).get("action")
    if surface == "risk_adjustment":
        risk = trace.get("risk_adjustment") or {}
        return "RISK_ZERO" if fnum(risk.get("after_risk_pct")) == 0 else "RISK_KEEP"
    return baseline_decision(surface, trace, {})


def surface_object(surface: str, trace: dict[str, Any], cache: dict[str, Any]) -> dict[str, Any] | None:
    if surface == "route_decision":
        return cache.get("route_decision")
    if surface == "pre_ai_decision":
        pre = cache.get("pre_ai_decision") if isinstance(cache.get("pre_ai_decision"), dict) else {}
        side = str(trace.get("side") or "")
        side_decisions = pre.get("side_decisions") if isinstance(pre, dict) else None
        if isinstance(side_decisions, list):
            for decision in side_decisions:
                event = decision.get("event") if isinstance(decision, dict) else {}
                if str(event.get("side") or "") == side:
                    return decision
        return cache.get("route_decision")
    if surface in {"risk_adjustment", "pending_policy"}:
        return cache.get("route_decision")
    return None


def surface_is_material(surface: str, trace: dict[str, Any]) -> bool:
    if surface == "route_decision":
        return True
    if surface == "pre_ai_decision":
        pre = trace.get("pre_ai_decision") or {}
        return str(pre.get("action") or "") not in {"", "ALLOW_AI"} or str(
            pre.get("decision") or ""
        ) in {"AVOID", "FOLLOW", "MIXED"}
    if surface == "risk_adjustment":
        risk = trace.get("risk_adjustment") or {}
        return bool(risk.get("applied")) or fnum(risk.get("after_risk_pct")) == 0 or str(
            risk.get("decision") or ""
        ) in {"AVOID", "FOLLOW", "MIXED"}
    if surface == "pending_policy":
        pending = trace.get("pending_policy") or {}
        return str(pending.get("action") or "") not in {"", "PLACE_LIMIT"} or str(
            pending.get("decision") or ""
        ) in {"AVOID", "FOLLOW", "MIXED"}
    return False


def action_for_variant(surface: str, decision: str) -> str:
    if surface == "pre_ai_decision":
        if decision == "AVOID":
            return "SKIP_AI_AVOID_ONLY"
        if decision == "FOLLOW":
            return "NARROW_AI_TO_SIDE"
        if decision == "MIXED":
            return "ALLOW_AI_WITH_MIXED_CONTEXT"
        return "ALLOW_AI"
    if surface == "risk_adjustment":
        return "RISK_ZERO" if decision == "AVOID" else "RISK_KEEP"
    if surface == "pending_policy":
        return "SKIP_PENDING_NOFILL_AVOID" if decision == "AVOID" else "PLACE_LIMIT"
    return decision


def counterfactuals_for_surface(
    surface: str,
    trace: dict[str, Any],
    cache: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    event = trace.get("runtime_input_event") or {}
    obj = surface_object(surface, trace, cache)
    rows = rows_from_surface_decision(obj)
    score_by_id = score_map(obj)
    dominant, dominant_meta = dominant_row(rows, score_by_id)
    classified = [classify_evidence_row(row, event) for row in rows]
    broad_count = sum(1 for row in classified if row.get("broad_unanchored"))
    stale_count = sum(1 for row in classified if row.get("stale_legacy"))
    source_required_count = sum(1 for row in classified if row.get("source_required"))
    source_bound_count = sum(1 for row in classified if row.get("current_source_bound"))
    baseline = baseline_decision(surface, trace, cache)
    base_action = baseline_action(surface, trace)
    variants: dict[str, Any] = {}
    variant_details: list[dict[str, Any]] = []
    for variant in COUNTERFACTUAL_VARIANTS:
        selected = variant_rows(variant, rows, dominant_meta, event)
        pressure = score_rows(selected, score_by_id)
        decision = pressure["decision"] if rows else baseline
        if variant == "all_evidence":
            decision = baseline
        action = action_for_variant(surface, decision)
        variants[variant] = {
            "decision": decision,
            "action": action,
            "changed_decision": decision != baseline,
            "changed_action": action != base_action,
            "rows_selected": pressure["rows_selected"],
            "avoid_pressure": pressure["avoid_pressure"],
            "follow_pressure": pressure["follow_pressure"],
            "mixed_rows": pressure["mixed_rows"],
            "source_required_rows": pressure["source_required_rows"],
        }
        variant_details.append({"variant": variant, **variants[variant]})
    pollution = {
        "matched_rows": len(rows),
        "broad_unanchored_rows": broad_count,
        "stale_legacy_rows": stale_count,
        "source_required_rows": source_required_count,
        "current_source_bound_rows": source_bound_count,
        "rows_truncated": (evidence_counts_from_surface(obj).get("rows_truncated")),
        "counterfactual_method": "offline_pressure_counterfactual_from_stage03_matched_rows",
        "dominant_removed_computable": bool(rows and dominant_meta.get("dominant_evidence_family")),
        "current_source_bound_only_computable": source_bound_count > 0,
    }
    return variants, {**dominant_meta, **pollution}, variant_details


def load_cache_by_id(stage03_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output = (stage03_manifest.get("outputs") or {}).get("runtime_event_cache") or {}
    path = repo_path(output.get("path"))
    cache: dict[str, dict[str, Any]] = {}
    for row in iter_gzip_jsonl(path):
        cache[str(row.get("runtime_event_cache_id"))] = row
    return cache


def load_manifest(path: str | Path) -> dict[str, Any]:
    return read_json(repo_path(path))


def load_path_context(stage04_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    outputs = stage04_manifest.get("outputs") or {}
    context: dict[str, dict[str, Any]] = defaultdict(dict)
    missed_path = repo_path((outputs.get("missed_winner_avoided_loser") or {}).get("path"))
    nofill_path = repo_path((outputs.get("nofill_pending_lifecycle") or {}).get("path"))
    disagreement_path = repo_path((outputs.get("m15_vs_ltf_disagreement") or {}).get("path"))
    for row in iter_gzip_jsonl(missed_path):
        context[str(row["candidate_id"])]["missed_winner_avoided_loser"] = row
    for row in iter_gzip_jsonl(nofill_path):
        context[str(row["candidate_id"])]["nofill_pending_lifecycle"] = row
    for row in iter_gzip_jsonl(disagreement_path):
        cid = str(row["candidate_id"])
        item = context[cid].setdefault("m15_vs_ltf_disagreements", [])
        item.append(row)
    return context


def best_path_from_context(context: dict[str, Any]) -> dict[str, Any]:
    missed = context.get("missed_winner_avoided_loser") or {}
    nofill = context.get("nofill_pending_lifecycle") or {}
    return {
        "best_available_replay_mode": missed.get("best_available_replay_mode")
        or nofill.get("best_available_replay_mode"),
        "best_path_row_id": missed.get("best_path_row_id"),
        "best_available_terminal_outcome": missed.get("best_available_terminal_outcome")
        or nofill.get("terminal_outcome"),
        "best_available_simulated_r": missed.get("best_available_simulated_r"),
        "missed_winner_avoided_loser_classification": missed.get("classification"),
        "would_change_decision_or_execution_with_ltf_source": missed.get(
            "would_change_decision_or_execution_with_ltf_source"
        ),
        "pending_lifecycle_state": nofill.get("pending_lifecycle_state"),
        "entry_touched": nofill.get("entry_touched"),
        "no_fill": nofill.get("no_fill"),
        "source_gap_class": nofill.get("source_gap_class"),
        "m15_vs_ltf_disagreement_count": len(context.get("m15_vs_ltf_disagreements") or []),
    }


def dominance_row(
    trace: dict[str, Any],
    surface: str,
    cache: dict[str, Any],
    path_context: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    variants, dominance, variant_details = counterfactuals_for_surface(surface, trace, cache)
    best_path = best_path_from_context(path_context)
    baseline = baseline_decision(surface, trace, cache)
    base_action = baseline_action(surface, trace)
    all_variant = variants.get("all_evidence") or {}
    changed_variants = [
        name
        for name, payload in variants.items()
        if name != "all_evidence"
        and (payload.get("changed_decision") or payload.get("changed_action"))
    ]
    row = {
        "schema_version": "vnext_full_replay_stage05_dominance_pollution_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "dominance_row_id": stable_id(
            "dom05",
            {
                "candidate_id": trace.get("candidate_id"),
                "runtime_mode": trace.get("runtime_mode"),
                "surface": surface,
            },
        ),
        "candidate_id": trace.get("candidate_id"),
        "runtime_trace_id": trace.get("runtime_trace_id"),
        "runtime_event_cache_id": trace.get("runtime_event_cache_id"),
        "runtime_mode": trace.get("runtime_mode"),
        "surface": surface,
        "symbol": trace.get("symbol"),
        "source_symbol": trace.get("source_symbol"),
        "side": trace.get("side"),
        "framework": trace.get("framework"),
        "route_family": trace.get("route_family"),
        "route_session": trace.get("route_session"),
        "session_bucket": trace.get("session_bucket"),
        "market_timeframe": trace.get("market_timeframe"),
        "candle_time_utc": trace.get("candle_time_utc"),
        "source_origin": trace.get("source_origin"),
        "source_path": trace.get("source_path"),
        "source_sha256": trace.get("source_sha256"),
        "source_universe_row_id": trace.get("source_universe_row_id"),
        "baseline_decision": baseline,
        "baseline_action": base_action,
        "all_evidence_decision": all_variant.get("decision", baseline),
        "dominant_evidence_family": dominance.get("dominant_evidence_family"),
        "dominant_source_component": dominance.get("dominant_source_component"),
        "dominant_action_class": dominance.get("dominant_action_class"),
        "dominant_decision": dominance.get("dominant_decision"),
        "dominant_row_id": dominance.get("dominant_row_id"),
        "dominant_score": dominance.get("dominant_score"),
        "pollution_flags": {
            "broad_unanchored_rows": dominance.get("broad_unanchored_rows"),
            "stale_legacy_rows": dominance.get("stale_legacy_rows"),
            "source_required_rows": dominance.get("source_required_rows"),
            "current_source_bound_rows": dominance.get("current_source_bound_rows"),
            "rows_truncated": dominance.get("rows_truncated"),
        },
        "matched_rows": dominance.get("matched_rows"),
        "counterfactual_variants": variants,
        "changed_counterfactual_variants": changed_variants,
        "changed_action_or_decision_under_counterfactual": bool(changed_variants),
        "counterfactual_method": dominance.get("counterfactual_method"),
        "counterfactual_limitations": {
            "dominant_removed_computable": dominance.get("dominant_removed_computable"),
            "current_source_bound_only_computable": dominance.get(
                "current_source_bound_only_computable"
            ),
            "runtime_subset_switch_not_used": True,
            "offline_pressure_recomputed_from_stage03_matched_rows": True,
        },
        "path_context": best_path,
        "would_change_execution_with_ltf_source": best_path.get(
            "would_change_decision_or_execution_with_ltf_source"
        ),
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
    }
    return row, variant_details


def path_pending_dominance_row(trace: dict[str, Any], path_context: dict[str, Any]) -> dict[str, Any]:
    best_path = best_path_from_context(path_context)
    return {
        "schema_version": "vnext_full_replay_stage05_dominance_pollution_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "dominance_row_id": stable_id(
            "dom05",
            {"candidate_id": trace.get("candidate_id"), "surface": "path_nofill_pending"},
        ),
        "candidate_id": trace.get("candidate_id"),
        "runtime_trace_id": None,
        "runtime_event_cache_id": None,
        "runtime_mode": "best_available_path_source",
        "surface": "path_nofill_pending_lifecycle",
        "symbol": trace.get("symbol"),
        "source_symbol": trace.get("source_symbol"),
        "side": trace.get("side"),
        "framework": trace.get("framework"),
        "route_family": trace.get("route_family"),
        "route_session": trace.get("route_session"),
        "session_bucket": trace.get("session_bucket"),
        "market_timeframe": trace.get("market_timeframe"),
        "candle_time_utc": trace.get("candle_time_utc"),
        "source_origin": trace.get("source_origin"),
        "source_path": trace.get("source_path"),
        "source_sha256": trace.get("source_sha256"),
        "source_universe_row_id": trace.get("source_universe_row_id"),
        "baseline_decision": "PATH_TRUTH_ONLY",
        "baseline_action": best_path.get("pending_lifecycle_state"),
        "all_evidence_decision": "PATH_TRUTH_ONLY",
        "dominant_evidence_family": "stage04_best_available_path_truth",
        "dominant_source_component": "nofill_pending_lifecycle",
        "dominant_action_class": best_path.get("pending_lifecycle_state"),
        "dominant_decision": best_path.get("best_available_terminal_outcome"),
        "dominant_row_id": best_path.get("best_path_row_id"),
        "dominant_score": best_path.get("best_available_simulated_r"),
        "pollution_flags": {
            "broad_unanchored_rows": 0,
            "stale_legacy_rows": 0,
            "source_required_rows": 1 if best_path.get("source_gap_class") else 0,
            "current_source_bound_rows": 1 if best_path.get("best_path_row_id") else 0,
            "rows_truncated": False,
        },
        "matched_rows": 1,
        "counterfactual_variants": {
            "all_evidence": {
                "decision": "PATH_TRUTH_ONLY",
                "action": best_path.get("pending_lifecycle_state"),
                "changed_decision": False,
                "changed_action": False,
                "rows_selected": 1,
            }
        },
        "changed_counterfactual_variants": [],
        "changed_action_or_decision_under_counterfactual": False,
        "counterfactual_method": "path_truth_join_no_runtime_counterfactual_claim",
        "counterfactual_limitations": {
            "runtime_subset_switch_not_used": True,
            "path_truth_row_has_no_evidence_family_subset": True,
        },
        "path_context": best_path,
        "would_change_execution_with_ltf_source": best_path.get(
            "would_change_decision_or_execution_with_ltf_source"
        ),
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
    }


def mixed_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("runtime_mode") or ""),
        str(row.get("surface") or ""),
        str(row.get("dominant_evidence_family") or "NO_DOMINANT_FAMILY"),
        str(row.get("dominant_source_component") or "NO_SOURCE_COMPONENT"),
        str(row.get("dominant_action_class") or "NO_ACTION_CLASS"),
        str(row.get("symbol") or ""),
        str(row.get("route_session") or ""),
        str(row.get("side") or ""),
        str(row.get("framework") or ""),
    )


def should_track_mixed(row: dict[str, Any]) -> bool:
    if row.get("baseline_decision") == "MIXED" or row.get("dominant_decision") == "MIXED":
        return True
    variants = row.get("counterfactual_variants") or {}
    if any(payload.get("mixed_rows") for payload in variants.values() if isinstance(payload, dict)):
        return True
    text = " ".join(
        str(row.get(key) or "")
        for key in (
            "dominant_evidence_family",
            "dominant_source_component",
            "dominant_action_class",
        )
    ).lower()
    return "mixed" in text or bool((row.get("pollution_flags") or {}).get("source_required_rows"))


def update_mixed_stats(stats: dict[tuple[str, ...], dict[str, Any]], row: dict[str, Any]) -> None:
    if not should_track_mixed(row):
        return
    key = mixed_key(row)
    item = stats.setdefault(
        key,
        {
            "row_count": 0,
            "candidate_ids": set(),
            "baseline_decision_counts": Counter(),
            "classification_counts": Counter(),
            "variant_change_count": 0,
            "best_r_sum": 0.0,
            "best_r_count": 0,
            "source_required_rows": 0,
            "broad_unanchored_rows": 0,
            "stale_legacy_rows": 0,
            "current_source_bound_rows": 0,
            "ltf_change_count": 0,
            "examples": [],
        },
    )
    item["row_count"] += 1
    item["candidate_ids"].add(row.get("candidate_id"))
    item["baseline_decision_counts"][str(row.get("baseline_decision") or "UNKNOWN")] += 1
    item["classification_counts"][
        str((row.get("path_context") or {}).get("missed_winner_avoided_loser_classification") or "UNKNOWN")
    ] += 1
    if row.get("changed_action_or_decision_under_counterfactual"):
        item["variant_change_count"] += 1
    path = row.get("path_context") or {}
    sim_r = fnum(path.get("best_available_simulated_r"))
    if sim_r is not None:
        item["best_r_sum"] += sim_r
        item["best_r_count"] += 1
    flags = row.get("pollution_flags") or {}
    item["source_required_rows"] += int(flags.get("source_required_rows") or 0)
    item["broad_unanchored_rows"] += int(flags.get("broad_unanchored_rows") or 0)
    item["stale_legacy_rows"] += int(flags.get("stale_legacy_rows") or 0)
    item["current_source_bound_rows"] += int(flags.get("current_source_bound_rows") or 0)
    if path.get("would_change_decision_or_execution_with_ltf_source"):
        item["ltf_change_count"] += 1
    if len(item["examples"]) < 5:
        item["examples"].append(row.get("dominance_row_id"))


def classify_mixed_resolution(stats: dict[str, Any]) -> tuple[str, str]:
    baseline_counts: Counter[str] = stats["baseline_decision_counts"]
    classifications: Counter[str] = stats["classification_counts"]
    mean_r = (
        stats["best_r_sum"] / stats["best_r_count"] if stats.get("best_r_count") else None
    )
    if stats.get("source_required_rows"):
        return (
            "source_required_and_guarded",
            "MIXED/source-required evidence remains useful as a source-acquisition guard, not as terminal direction.",
        )
    if stats.get("broad_unanchored_rows") and stats.get("variant_change_count"):
        return (
            "broad_unanchored_noisy_pressure",
            "Removing broad/unanchored rows changes pressure; keep as repair/pollution item.",
        )
    if stats.get("stale_legacy_rows") and stats.get("variant_change_count"):
        return (
            "stale_legacy_pollution_candidate",
            "Removing stale/legacy rows changes pressure; treat as pollution until fresher source-bound evidence dominates.",
        )
    if baseline_counts.get("MIXED", 0) and mean_r is not None and mean_r > 0:
        return (
            "replay_resolvable_into_follow_candidate",
            "MIXED cohort has positive best-available path/R in this replay slice.",
        )
    if baseline_counts.get("MIXED", 0) and mean_r is not None and mean_r < 0:
        return (
            "replay_resolvable_into_avoid_candidate",
            "MIXED cohort has negative best-available path/R in this replay slice.",
        )
    if classifications.get("avoided_loser", 0) > classifications.get("missed_winner", 0):
        return (
            "useful_avoid_context",
            "MIXED-involved evidence avoided more losers than it missed winners in this slice.",
        )
    if classifications.get("missed_winner", 0) > classifications.get("avoided_loser", 0):
        return (
            "harmful_overblock_context",
            "MIXED-involved evidence missed more winners than it avoided losers in this slice.",
        )
    if not stats.get("variant_change_count"):
        return (
            "neutral_no_effect_context",
            "MIXED-involved evidence did not change offline counterfactual pressure in this slice.",
        )
    return (
        "ambiguous_but_replay_measured",
        "MIXED-involved evidence changed pressure but lacks decisive path/R or source-repair classification.",
    )


def mixed_rows_from_stats(
    stats: dict[tuple[str, ...], dict[str, Any]],
    source_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, item in sorted(stats.items()):
        (
            runtime_mode,
            surface,
            evidence_family,
            source_component,
            action_class,
            symbol,
            route_session,
            side,
            framework,
        ) = key
        resolution_class, rationale = classify_mixed_resolution(item)
        best_r_mean = (
            item["best_r_sum"] / item["best_r_count"] if item.get("best_r_count") else None
        )
        rows.append(
            {
                "schema_version": "vnext_full_replay_stage05_mixed_resolution_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "mixed_resolution_row_id": stable_id(
                    "mix05",
                    {
                        "key": key,
                        "source_path": source_manifest.get("source_path"),
                    },
                ),
                "runtime_mode": runtime_mode,
                "surface": surface,
                "evidence_family": evidence_family,
                "source_component": source_component,
                "action_class": action_class,
                "symbol": symbol,
                "route_session": route_session,
                "side": side,
                "framework": framework,
                "source_path": source_manifest.get("source_path"),
                "source_index": source_manifest.get("source_index"),
                "stage04_shard_id": source_manifest.get("shard_id"),
                "candidate_count": len(item["candidate_ids"]),
                "dominance_row_count": item["row_count"],
                "baseline_decision_counts": dict(sorted(item["baseline_decision_counts"].items())),
                "missed_winner_avoided_loser_classification_counts": dict(
                    sorted(item["classification_counts"].items())
                ),
                "variant_change_count": item["variant_change_count"],
                "best_available_simulated_r_mean": best_r_mean,
                "best_available_simulated_r_count": item.get("best_r_count"),
                "source_required_rows": item.get("source_required_rows"),
                "broad_unanchored_rows": item.get("broad_unanchored_rows"),
                "stale_legacy_rows": item.get("stale_legacy_rows"),
                "current_source_bound_rows": item.get("current_source_bound_rows"),
                "ltf_execution_change_count": item.get("ltf_change_count"),
                "resolution_class": resolution_class,
                "resolution_rationale": rationale,
                "resolution_scope": "stage05_replay_measured_not_final_promotion",
                "example_dominance_row_ids": item["examples"],
            }
        )
    return rows


def completed_shard_manifest(
    stage04_manifest: dict[str, Any], source_hash: str
) -> dict[str, Any] | None:
    shard_id = source_stage05_shard_id(stage04_manifest)
    paths = stage05_shard_paths(shard_id)
    manifest_path = paths["manifest"]
    if not manifest_path.exists():
        return None
    manifest = read_json(manifest_path)
    if manifest.get("shard_status") != "complete":
        return None
    if manifest.get("source_inventory_hash") != source_hash:
        return None
    expected = int(stage04_manifest.get("candidate_rows") or 0)
    if int(manifest.get("expected_candidate_rows") or -1) != expected:
        return None
    for key in SHARDED_ARTIFACT_KEYS:
        output = (manifest.get("outputs") or {}).get(key) or {}
        path = repo_path(output.get("path"))
        if not path.exists() or sha256_file(path) != output.get("sha256"):
            return None
    return manifest


def write_one_source_shard(
    source_index: int,
    source_count: int,
    stage04_manifest: dict[str, Any],
    source_hash: str,
) -> dict[str, Any]:
    completed = completed_shard_manifest(stage04_manifest, source_hash)
    if completed:
        return completed

    shard_id = source_stage05_shard_id(stage04_manifest)
    paths = stage05_shard_paths(shard_id)
    paths["manifest"].parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    stage03_manifest = load_manifest(
        repo_path(stage04_manifest["input_runtime_trace_path"]).parent / "manifest.json"
    )
    runtime_trace_path = repo_path(stage04_manifest["input_runtime_trace_path"])
    cache_by_id = load_cache_by_id(stage03_manifest)
    path_context_by_candidate = load_path_context(stage04_manifest)
    row_counts: Counter[str] = Counter()
    baseline_decisions: Counter[str] = Counter()
    surface_counts: Counter[str] = Counter()
    resolution_counts: Counter[str] = Counter()
    mixed_stats: dict[tuple[str, ...], dict[str, Any]] = {}
    seen_path_candidates: set[str] = set()

    heartbeat = {
        "schema_version": "vnext_full_replay_stage05_shard_heartbeat_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": stage04_manifest.get("source_path"),
        "started_at_utc": started_at,
        "updated_at_utc": started_at,
        "status": "running",
        "resume_cursor": {
            "runtime_trace_rows_processed": 0,
            "dominance_rows_written": 0,
            "mixed_resolution_rows_written": 0,
        },
    }
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage05_heartbeat(heartbeat)

    with AtomicGzipJsonlWriter(paths["dominance_and_pollution"]) as dom_writer:
        for trace in iter_gzip_jsonl(runtime_trace_path):
            cid = str(trace.get("candidate_id"))
            cache = cache_by_id.get(str(trace.get("runtime_event_cache_id"))) or {}
            path_context = path_context_by_candidate.get(cid) or {}
            for surface in RUNTIME_SURFACES:
                if not surface_is_material(surface, trace):
                    continue
                row, _variant_details = dominance_row(trace, surface, cache, path_context)
                dom_writer.write(row)
                row_counts["dominance_and_pollution"] += 1
                baseline_decisions[str(row.get("baseline_decision"))] += 1
                surface_counts[str(row.get("surface"))] += 1
                update_mixed_stats(mixed_stats, row)
            if cid not in seen_path_candidates:
                row = path_pending_dominance_row(trace, path_context)
                dom_writer.write(row)
                seen_path_candidates.add(cid)
                row_counts["dominance_and_pollution"] += 1
                baseline_decisions[str(row.get("baseline_decision"))] += 1
                surface_counts[str(row.get("surface"))] += 1
            row_counts["runtime_trace_rows_processed"] += 1
            if row_counts["runtime_trace_rows_processed"] % 10000 == 0:
                heartbeat["updated_at_utc"] = utc_now()
                heartbeat["resume_cursor"] = {
                    "runtime_trace_rows_processed": row_counts["runtime_trace_rows_processed"],
                    "dominance_rows_written": dom_writer.count,
                    "mixed_resolution_rows_written": 0,
                }
                write_shard_json(paths["heartbeat"], heartbeat)
                write_stage05_heartbeat(heartbeat)

    mixed_rows = mixed_rows_from_stats(mixed_stats, stage04_manifest)
    with AtomicGzipJsonlWriter(paths["mixed_resolution"]) as mixed_writer:
        for row in mixed_rows:
            mixed_writer.write(row)
            row_counts["mixed_resolution"] += 1
            resolution_counts[str(row.get("resolution_class"))] += 1

    outputs: dict[str, dict[str, Any]] = {}
    for key in SHARDED_ARTIFACT_KEYS:
        path = paths[key]
        outputs[key] = {
            "path": rel(path),
            "row_count": row_counts[key],
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    completed_at = utc_now()
    manifest = {
        "schema_version": "vnext_full_replay_stage05_shard_manifest_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "shard_id": shard_id,
        "shard_status": "complete",
        "source_index": source_index,
        "source_count": source_count,
        "source_path": stage04_manifest.get("source_path"),
        "stage02_shard_id": stage04_manifest.get("stage02_shard_id"),
        "stage03_shard_id": stage04_manifest.get("stage03_shard_id"),
        "stage04_shard_id": stage04_manifest.get("shard_id"),
        "input_runtime_trace_path": rel(runtime_trace_path),
        "input_stage04_manifest_path": rel(repo_path(stage04_manifest.get("outputs", {}).get("path_outcome_r", {}).get("path")).parent / "manifest.json"),
        "expected_candidate_rows": int(stage04_manifest.get("candidate_rows") or 0),
        "runtime_trace_rows_processed": row_counts["runtime_trace_rows_processed"],
        "candidate_rows_with_path_pending_surface": len(seen_path_candidates),
        "outputs": outputs,
        "row_counts": dict(row_counts),
        "baseline_decision_counts": dict(sorted(baseline_decisions.items())),
        "surface_counts": dict(sorted(surface_counts.items())),
        "mixed_resolution_class_counts": dict(sorted(resolution_counts.items())),
        "source_inventory_hash": source_hash,
        "started_at_utc": started_at,
        "completed_at_utc": completed_at,
        "heartbeat_updated_at_utc": completed_at,
        "resume_cursor": {
            "runtime_trace_rows_processed": row_counts["runtime_trace_rows_processed"],
            "dominance_rows_written": row_counts["dominance_and_pollution"],
            "mixed_resolution_rows_written": row_counts["mixed_resolution"],
            "next_source_index": source_index + 1,
            "completed_source_path": stage04_manifest.get("source_path"),
        },
        "counterfactual_variants": list(COUNTERFACTUAL_VARIANTS),
        "counterfactual_method": "offline_pressure_counterfactual_from_stage03_matched_rows",
    }
    write_shard_json(paths["manifest"], manifest)
    heartbeat.update(
        {
            "updated_at_utc": completed_at,
            "status": "complete",
            "resume_cursor": manifest["resume_cursor"],
        }
    )
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage05_heartbeat(heartbeat)
    return manifest


def build_shard_contract(manifests: list[dict[str, Any]], source_hash: str) -> None:
    rows = []
    for index, manifest in enumerate(manifests, start=1):
        shard_id = source_stage05_shard_id(manifest)
        paths = stage05_shard_paths(shard_id)
        rows.append(
            {
                "shard_id": shard_id,
                "source_index": index,
                "source_count": len(manifests),
                "source_path": manifest.get("source_path"),
                "stage04_shard_id": manifest.get("shard_id"),
                "input_runtime_trace_path": manifest.get("input_runtime_trace_path"),
                "input_stage04_outputs": manifest.get("outputs"),
                "outputs": {key: rel(paths[key]) for key in SHARDED_ARTIFACT_KEYS},
                "temp_outputs": {
                    key: rel(paths[key].with_suffix(paths[key].suffix + ".tmp"))
                    for key in SHARDED_ARTIFACT_KEYS
                },
                "atomic_rename": "write .tmp then replace final after full gzip jsonl close",
                "heartbeat_path": rel(paths["heartbeat"]),
                "manifest_path": rel(paths["manifest"]),
                "resume_rule": "skip shard only when manifest/source_inventory_hash/input count/output sha256 all match",
                "source_inventory_hash": source_hash,
            }
        )
    payload = {
        "schema_version": "vnext_full_replay_stage05_shard_contract_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "created_at_utc": utc_now(),
        "source_shard_count": len(rows),
        "counterfactual_variants": list(COUNTERFACTUAL_VARIANTS),
        "shards": rows,
    }
    write_json(OUTPUTS["stage05_shard_contract"], payload)


def write_master_indices_from_shards(manifests: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for key in SHARDED_ARTIFACT_KEYS:
        rows = []
        for chunk_index, manifest in enumerate(manifests, start=1):
            output = (manifest.get("outputs") or {}).get(key) or {}
            rows.append(
                {
                    "schema_version": "vnext_full_replay_chunk_index_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "logical_artifact_path": rel(OUTPUTS[key]),
                    "chunk_index": chunk_index,
                    "chunk_path": output.get("path"),
                    "row_count": int(output.get("row_count") or 0),
                    "bytes": output.get("bytes"),
                    "sha256": output.get("sha256"),
                    "source_index": manifest.get("source_index"),
                    "source_path": manifest.get("source_path"),
                    "shard_id": manifest.get("shard_id"),
                    "shard_status": manifest.get("shard_status"),
                }
            )
            counts[key] += int(output.get("row_count") or 0)
        write_jsonl(OUTPUTS[key], rows)
    write_jsonl(OUTPUTS["stage05_shard_status"], manifests)
    counts["stage05_source_shards_completed"] = len(manifests)
    return dict(counts)


def aggregate_summary(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    counts = write_master_indices_from_shards(manifests)
    baseline_counts: Counter[str] = Counter()
    surface_counts: Counter[str] = Counter()
    mixed_resolution_counts: Counter[str] = Counter()
    for manifest in manifests:
        baseline_counts.update(manifest.get("baseline_decision_counts") or {})
        surface_counts.update(manifest.get("surface_counts") or {})
        mixed_resolution_counts.update(manifest.get("mixed_resolution_class_counts") or {})
    summary = {
        "schema_version": "vnext_full_replay_stage05_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "created_at_utc": utc_now(),
        "counts": counts,
        "source_shards": len(manifests),
        "baseline_decision_counts": dict(sorted(baseline_counts.items())),
        "surface_counts": dict(sorted(surface_counts.items())),
        "mixed_resolution_class_counts": dict(sorted(mixed_resolution_counts.items())),
        "counterfactual_variants": list(COUNTERFACTUAL_VARIANTS),
        "counterfactual_method": "offline_pressure_counterfactual_from_stage03_matched_rows",
        "stage_scope_boundary": "dominance/pollution and MIXED resolution only; ablations, robustness, prop metrics, behavioral forensics, and final decision map remain incomplete",
    }
    write_json(OUTPUTS["stage05_summary"], summary)
    write_json(
        OUTPUTS["mixed_resolution_summary"],
        {
            "schema_version": "vnext_full_replay_mixed_resolution_summary_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "created_at_utc": utc_now(),
            "mixed_resolution_rows": counts.get("mixed_resolution"),
            "mixed_resolution_class_counts": dict(sorted(mixed_resolution_counts.items())),
            "resolution_scope": "stage05_replay_measured_not_final_promotion",
        },
    )
    return summary


def build_outputs() -> dict[str, Any]:
    if not STAGE04_VERIFIER_PATH.exists():
        raise FileNotFoundError(f"missing Stage04 verifier: {STAGE04_VERIFIER_PATH}")
    verifier = read_json(STAGE04_VERIFIER_PATH)
    if str(verifier.get("status") or "").upper() != "OK" or int(
        verifier.get("failure_count") or 0
    ):
        raise RuntimeError("Stage04 verifier is not OK; refusing Stage05")
    manifests = stage04_manifests()
    source_hash = source_inventory_hash(manifests)
    build_shard_contract(manifests, source_hash)
    completed: list[dict[str, Any]] = []
    for index, manifest in enumerate(manifests, start=1):
        completed.append(write_one_source_shard(index, len(manifests), manifest, source_hash))
    summary = aggregate_summary(completed)
    verifier_payload = verify_outputs(summary)
    update_route_control_ledgers(summary, verifier_payload)
    return summary


def audit_chunked_artifact(path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    for index_row in iter_jsonl(path):
        chunk_path = repo_path(index_row.get("chunk_path"))
        parse_errors = 0
        row_count = 0
        first_row = None
        last_row = None
        required_missing: Counter[str] = Counter()
        duplicate_ids: Counter[str] = Counter()
        id_field = (
            "dominance_row_id"
            if artifact_key == "dominance_and_pollution"
            else "mixed_resolution_row_id"
        )
        with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                row_count += 1
                if first_row is None:
                    first_row = row
                last_row = row
                rid = row.get(id_field)
                if rid:
                    duplicate_ids[str(rid)] += 1
                for field in ("route_id", "stage_id", id_field, "candidate_id" if artifact_key == "dominance_and_pollution" else "resolution_class"):
                    if row.get(field) in (None, "", "UNKNOWN"):
                        required_missing[field] += 1
        rows.append(
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "artifact_key": artifact_key,
                "logical_artifact_path": rel(path),
                "file_path": rel(chunk_path),
                "row_count": row_count,
                "manifest_row_count": int(index_row.get("row_count") or 0),
                "byte_count": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path),
                "first_row": first_row,
                "last_row": last_row,
                "parse_error_count": parse_errors,
                "required_missing_counts": dict(required_missing),
                "duplicate_id_count": sum(1 for value in duplicate_ids.values() if value > 1),
                "audit_status": (
                    "PASS"
                    if parse_errors == 0
                    and row_count == int(index_row.get("row_count") or 0)
                    and not required_missing
                    else "FAIL"
                ),
                "source_builder": rel(Path(__file__).resolve()),
            }
        )
    return rows


def audit_simple_artifact(path: Path, artifact_key: str) -> dict[str, Any]:
    parse_errors = 0
    row_count = 0
    first_row = None
    last_row = None
    if path.exists() and path.suffix == ".jsonl":
        for row in iter_jsonl(path):
            row_count += 1
            first_row = first_row or row
            last_row = row
    elif path.exists():
        try:
            first_row = read_json(path)
            last_row = first_row
            row_count = 1
        except Exception:
            parse_errors += 1
    return {
        "schema_version": "vnext_full_replay_line_accountability_audit_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "artifact_key": artifact_key,
        "file_path": rel(path),
        "row_count": row_count,
        "byte_count": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
        "first_row": first_row,
        "last_row": last_row,
        "parse_error_count": parse_errors,
        "audit_status": "PASS" if path.exists() and parse_errors == 0 else "FAIL",
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
        "mixed_resolution_summary",
        "stage05_summary",
        "stage05_verifier",
        "stage05_shard_contract",
        "stage05_heartbeat",
        "stage05_shard_status",
    ):
        stage_rows.append(audit_simple_artifact(OUTPUTS[key], key))
    write_jsonl(LINE_AUDIT_PATH, existing + stage_rows)


def chunk_artifact_manifest(logical_path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    logical_count = 0
    if not logical_path.exists():
        return rows
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
        "dominance_and_pollution",
        "dominance_and_pollution_chunk",
        "mixed_resolution",
        "mixed_resolution_chunk",
        "mixed_resolution_summary",
        "stage05_summary",
        "stage05_verifier",
        "stage05_shard_contract",
        "stage05_heartbeat",
        "stage05_shard_status",
        "active_questions",
        "extra_step",
        "prompt_application",
        "line_audit",
        "completion_audit",
    }
    old = [row for row in existing.get("artifacts", []) if row.get("artifact_key") not in stage_keys]
    artifacts: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        artifacts.extend(chunk_artifact_manifest(OUTPUTS[key], key))
    for key in (
        "mixed_resolution_summary",
        "stage05_summary",
        "stage05_verifier",
        "stage05_shard_contract",
        "stage05_heartbeat",
        "stage05_shard_status",
    ):
        path = OUTPUTS[key]
        artifacts.append(
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
    for key, path in (
        ("active_questions", ACTIVE_QUESTION_PATH),
        ("extra_step", EXTRA_STEP_PATH),
        ("prompt_application", PROMPT_APPLICATION_PATH),
        ("line_audit", LINE_AUDIT_PATH),
        ("completion_audit", COMPLETION_AUDIT_PATH),
    ):
        artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "row_count": sum(1 for _ in iter_jsonl(path)) if path.suffix == ".jsonl" else 1,
                "logical_row_count": None,
                "source_kind": "route_control_output",
            }
        )
    existing["artifacts"] = old + artifacts
    existing["updated_at_utc"] = utc_now()
    write_json(OUTPUT_MANIFEST_PATH, existing)


def verify_outputs(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = summary or (read_json(OUTPUTS["stage05_summary"]) if OUTPUTS["stage05_summary"].exists() else {})
    failures: list[str] = []
    manifests = list(iter_jsonl(OUTPUTS["stage05_shard_status"]))
    if len(manifests) != len(stage04_manifests()):
        failures.append("stage05_shard_count_does_not_match_stage04")
    counts = summary.get("counts") or {}
    if counts.get("dominance_and_pollution", 0) < 506468:
        failures.append("dominance_rows_less_than_stage03_runtime_trace_rows")
    if counts.get("mixed_resolution", 0) <= 0:
        failures.append("mixed_resolution_rows_missing")
    for key in SHARDED_ARTIFACT_KEYS:
        logical_total = 0
        for index_row in iter_jsonl(OUTPUTS[key]):
            chunk_path = repo_path(index_row.get("chunk_path"))
            if not chunk_path.exists():
                failures.append(f"{key}_chunk_missing:{chunk_path}")
                continue
            parsed = sum(1 for _ in iter_gzip_jsonl(chunk_path))
            expected = int(index_row.get("row_count") or 0)
            logical_total += expected
            if parsed != expected:
                failures.append(f"{key}_row_count_mismatch:{chunk_path}:{parsed}!={expected}")
            if sha256_file(chunk_path) != index_row.get("sha256"):
                failures.append(f"{key}_sha_mismatch:{chunk_path}")
        if logical_total != counts.get(key):
            failures.append(f"{key}_logical_total_mismatch:{logical_total}!={counts.get(key)}")
    verifier = {
        "schema_version": "vnext_full_replay_stage05_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "checked_at_utc": utc_now(),
        "status": "OK" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures[:100],
        "counts": counts,
        "baseline_decision_counts": summary.get("baseline_decision_counts"),
        "surface_counts": summary.get("surface_counts"),
        "mixed_resolution_class_counts": summary.get("mixed_resolution_class_counts"),
    }
    write_json(OUTPUTS["stage05_verifier"], verifier)
    if failures:
        raise RuntimeError(json.dumps(verifier, indent=2, sort_keys=True))
    return verifier


def update_session_state(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE_PATH) if SESSION_STATE_PATH.exists() else {}
    counts = state.get("counts") or {}
    counts.update(
        {
            "stage05_dominance_and_pollution_rows": summary["counts"].get(
                "dominance_and_pollution"
            ),
            "stage05_mixed_resolution_rows": summary["counts"].get("mixed_resolution"),
            "stage05_source_shards_completed": summary["counts"].get(
                "stage05_source_shards_completed"
            ),
        }
    )
    state.update(
        {
            "schema_version": "vnext_full_replay_session_state_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "git_head": git_head(),
            "current_stage": STAGE_ID,
            "active_invariant": "Stage05 dominance/pollution counterfactuals and MIXED resolution",
            "first_incomplete_invariant": "Stage06 ablations, robustness, prop metrics, behavioral forensics, and final decision map",
            "next_action": "build Stage06 ablation/metrics/robustness/prop-firm/behavioral-forensics outputs from Stage03-05 joined replay rows",
            "goal_complete": False,
            "counts": counts,
            "stage05_output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
            "stage05_verifier_status": verifier.get("status"),
            "stage05_scope_boundary": summary.get("stage_scope_boundary"),
            "stage05_baseline_decision_counts": summary.get("baseline_decision_counts"),
            "stage05_surface_counts": summary.get("surface_counts"),
            "stage05_mixed_resolution_class_counts": summary.get(
                "mixed_resolution_class_counts"
            ),
        }
    )
    write_json(SESSION_STATE_PATH, state)


def update_completion_audit(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    audit = read_json(COMPLETION_AUDIT_PATH) if COMPLETION_AUDIT_PATH.exists() else {}
    completed = list(audit.get("completed_requirements_stage05") or [])
    for item in (
        "Stage05 dominance/pollution builder built route-locally",
        "Stage03 runtime decisions joined to Stage04 best available path/R and no-fill context",
        "Counterfactual variants computed for all evidence, dominant-family removed, broad/unanchored removed, stale/legacy removed, and current-source-bound only",
        "MIXED-involved evidence groups classified with replay/path/source-pollution rationale",
        "Stage05 verifier enforces shard coverage, dominance row coverage, chunk hashes, and MIXED rows",
    ):
        if item not in completed:
            completed.append(item)
    remaining = [
        "ablation/robustness/prop metrics",
        "behavioral forensics",
        "subagent or equivalent independent review for terminal outputs",
        "final promote/kill/repair map",
        "goal completion audit",
    ]
    audit.update(
        {
            "schema_version": "vnext_full_replay_completion_audit_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "completion_status": "IN_PROGRESS_NOT_COMPLETE",
            "goal_may_be_marked_complete": False,
            "completed_requirements_stage05": completed,
            "remaining_prompt_requirements_not_complete": remaining,
            "same_evidence_class_next_action": "build Stage06 ablation/metrics/robustness/prop-firm/behavioral-forensics outputs",
            "stage05_counts": summary.get("counts"),
            "stage05_verifier_status": verifier.get("status"),
        }
    )
    write_json(COMPLETION_AUDIT_PATH, audit)


def update_route_control_ledgers(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    existing_questions = [
        row
        for row in (list(iter_jsonl(ACTIVE_QUESTION_PATH)) if ACTIVE_QUESTION_PATH.exists() else [])
        if row.get("question_id")
        not in {"Q009_STAGE04_DOMINANCE_POLLUTION_NEXT", "Q010_STAGE04_MIXED_RESOLUTION_NEXT", "Q011_STAGE05_ABLATION_METRICS_NEXT"}
    ]
    question_rows = [
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q009_STAGE04_DOMINANCE_POLLUTION_NEXT",
            "question": "Which vNext evidence families dominate or pollute generated-candidate runtime decisions?",
            "status": "answered_stage05",
            "evidence_path": rel(OUTPUTS["dominance_and_pollution"]),
            "row_count": summary["counts"].get("dominance_and_pollution"),
            "created_at_utc": utc_now(),
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q010_STAGE04_MIXED_RESOLUTION_NEXT",
            "question": "Which MIXED decisions resolve or remain source-required once replay path truth is joined?",
            "status": "answered_stage05",
            "evidence_path": rel(OUTPUTS["mixed_resolution"]),
            "row_count": summary["counts"].get("mixed_resolution"),
            "created_at_utc": utc_now(),
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q011_STAGE05_ABLATION_METRICS_NEXT",
            "question": "Which decision surfaces survive ablation, robustness, prop-firm, concentration, and behavioral forensics?",
            "status": "open_next_stage",
            "evidence_path": rel(OUTPUTS["stage05_summary"]),
            "created_at_utc": utc_now(),
        },
    ]
    write_jsonl(ACTIVE_QUESTION_PATH, existing_questions + question_rows)

    extra_rows = list(iter_jsonl(EXTRA_STEP_PATH)) if EXTRA_STEP_PATH.exists() else []
    extra_rows.append(
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "pursuit_id": stable_id("extra05", summary.get("counts")),
            "requirement": "Join Stage03 runtime decisions to Stage04 path/R rows for dominance/pollution and MIXED resolution",
            "actions_executed": [
                "read Stage04 shard manifests",
                "read Stage03 runtime_trace and runtime_event_cache shards",
                "read Stage04 nofill, missed-winner/avoided-loser, and M15-vs-LTF disagreement shards",
                "compute five counterfactual pressure variants per material surface",
                "write per-source dominance and MIXED shards with verifier",
            ],
            "result": "completed_stage05_next_ablation_metrics_forensics",
            "evidence_path": rel(OUTPUTS["stage05_summary"]),
            "created_at_utc": utc_now(),
        }
    )
    write_jsonl(EXTRA_STEP_PATH, extra_rows)

    prompt_rows = list(iter_jsonl(PROMPT_APPLICATION_PATH)) if PROMPT_APPLICATION_PATH.exists() else []
    prompt_rows.append(
        {
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "prompt_requirement": "Compute dominance/pollution counterfactual pressure variants and resolve MIXED evidence using replay rows",
            "application_status": "applied_partial_replay_spine_continues",
            "evidence_path": rel(OUTPUTS["dominance_and_pollution"]),
            "row_count": summary["counts"].get("dominance_and_pollution"),
            "created_at_utc": utc_now(),
        }
    )
    write_jsonl(PROMPT_APPLICATION_PATH, prompt_rows)

    update_line_audit()
    update_session_state(summary, verifier)
    update_completion_audit(summary, verifier)
    update_output_manifest(summary)


def check_outputs() -> dict[str, Any]:
    summary = read_json(OUTPUTS["stage05_summary"])
    verifier = verify_outputs(summary)
    update_line_audit()
    return {"summary": summary, "verifier": verifier}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify existing outputs only")
    args = parser.parse_args(argv)
    if args.check:
        result = check_outputs()
    else:
        summary = build_outputs()
        result = {"summary": summary, "verifier": read_json(OUTPUTS["stage05_verifier"])}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
