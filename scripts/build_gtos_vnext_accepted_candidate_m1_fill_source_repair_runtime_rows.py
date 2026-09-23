#!/usr/bin/env python3
"""Build runtime rows for accepted-candidate M1 fill/source-repair evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_accepted_candidate_m1_fill_source_repair"
SOURCE_NAME = "gtos_vnext_accepted_candidate_m1_fill_source_repair_wave"

ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_UNITS: tuple[tuple[str, str, int | None], ...] = (
    ("UNIT_003285", "research/a4_trending_bull_replay_2026-04-28/fill_simulation_m1_results.json", 1),
    ("UNIT_003286", "research/a4_trending_bull_replay_2026-04-28/fill_simulation_results.json", 1),
    ("UNIT_003287", "research/a4_trending_bull_replay_2026-04-28/fill_simulator.py", None),
    ("UNIT_003288", "research/a4_trending_bull_replay_2026-04-28/fill_simulator_m1.py", None),
    ("UNIT_003290", "research/a4_trending_bull_replay_2026-04-28/fill_simulator_m1_full_cohort.py", None),
    ("UNIT_003531", "research/accepted_candidates_loser_mining/analyze.py", None),
    ("UNIT_003532", "research/accepted_candidates_loser_mining/feature_stratification.csv", 50),
    ("UNIT_003533", "research/accepted_candidates_loser_mining/h1_h2_split.json", 1),
    ("UNIT_003534", "research/accepted_candidates_loser_mining/section1_distributions.json", 1),
    ("UNIT_003535", "research/accepted_candidates_loser_mining/section2_feature_ranking.json", 1),
    ("UNIT_003536", "research/accepted_candidates_loser_mining/section3_classifier.json", 1),
    ("UNIT_003537", "research/accepted_candidates_loser_mining/section4_stratification.json", 1),
    ("UNIT_003538", "research/accepted_candidates_loser_mining/unified_filled_cands.jsonl", 217),
    ("UNIT_004536", "research/m1_backfill_e24_e26_rerun/backfill_m1.py", None),
    ("UNIT_004538", "research/m1_backfill_e24_e26_rerun/m1_backfill_log.csv", 8),
    ("UNIT_004539", "research/m1_backfill_e24_e26_rerun/per_feature_comparison.csv", 16),
    ("UNIT_004540", "research/m1_backfill_e24_e26_rerun/per_fill_features_m1.csv", 74),
    ("UNIT_004541", "research/m1_backfill_e24_e26_rerun/reconstructor_validation_m1.csv", 121),
    ("UNIT_004543", "research/m1_backfill_e24_e26_rerun/rerun_e26_m1.py", None),
    ("UNIT_004563", "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.json", 1),
    ("UNIT_004564", "research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md", 86),
    ("UNIT_004570", "research/ml_program/audit/data_backfill_2022_2023.md", 127),
    ("UNIT_004713", "research/ml_program/forensics/2026-04-29/agent_e_non_xau_fillback_inventory.json", 1),
    ("UNIT_005617", "research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.json", 1),
    ("UNIT_005618", "research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.md", 36),
    ("UNIT_007514", "research/science_program_2026_05/06_outcome_testing/g12_live_forward_evidence_capture_hardening_audit/MISSED_FILL_STUDY_AUDIT_2026-05-12.md", 23),
    ("UNIT_008351", "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_r11_adv_002_source_control_audit/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_EXACT_REQUIREMENT_ROWS_2026-05-13.json", 1),
    ("UNIT_008352", "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_r11_adv_002_source_control_audit/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_EXACT_REQUIREMENT_ROWS_2026-05-13.md", 131),
    ("UNIT_009335", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/build_main_orchestrator_action_after_exact_r_materialization_2026_05_17.py", None),
    ("UNIT_009366", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/build_main_orchestrator_exact_r_bridge_search_2026_05_17.py", None),
    ("UNIT_009483", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_2026-05-17.jsonl", None),
    ("UNIT_009484", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_SUMMARY_2026-05-17.json", 1),
    ("UNIT_009654", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_ALIAS_SEARCH_LEDGER_2026-05-17.jsonl", None),
    ("UNIT_009655", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_LEDGER_2026-05-17.jsonl", None),
    ("UNIT_009656", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_OUTPUT_MANIFEST_2026-05-17.json", 1),
    ("UNIT_009657", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_SUMMARY_2026-05-17.json", 1),
    ("UNIT_009658", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_VERIFICATION_RESULT_2026-05-17.json", 1),
    ("UNIT_009659", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json", 1),
    ("UNIT_009660", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_EXACT_R_MATERIALIZATION_VERIFICATION_RESULT_2026-05-17.json", 1),
    ("UNIT_010261", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/verify_main_orchestrator_action_after_exact_r_materialization_2026_05_17.py", None),
    ("UNIT_010292", "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/verify_main_orchestrator_exact_r_bridge_search_2026_05_17.py", None),
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "framework",
    "route_family",
    "source_component",
    "action_class",
    "entry_variant",
    "target_stop_order_class",
)

SESSION_MAP = {
    "london": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "tokyo": "tokyo_kz",
    "tokyo_core_0000_0300": "tokyo_kz",
    "all_sessions": "ALL_SESSIONS",
}


def _repo_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _session(value: Any) -> str:
    raw = _norm(value).casefold()
    return SESSION_MAP.get(raw, raw)


def _side(value: Any) -> str:
    raw = _norm(value).upper()
    return raw if raw in {"LONG", "SHORT"} else ""


def _symbol(value: Any) -> str:
    text = _norm(value)
    if "|" in text:
        text = text.split("|", 1)[0]
    return text


def _candidate_symbol(value: Any) -> str:
    text = _symbol(value)
    if "_" in text:
        return text.split("_", 1)[0]
    return text


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_row_count(path: Path) -> int:
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        return len(_read_jsonl(path))
    if suffix == ".csv":
        return len(_read_csv(path))
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            return len(data["rows"])
        if isinstance(data, dict) and all(isinstance(item, dict) for item in data.values()):
            return len(data)
        return 1
    if suffix in {".md", ".py"}:
        return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    return 1


def _metric(value: float | int | None, *, source_field: str, count: int = 1) -> dict[str, Any]:
    if value is None:
        return {
            "sum": None,
            "count": 0,
            "mean": None,
            "min": None,
            "max": None,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
            "match_rows_with_metric": 0,
            "source_field": source_field,
            "source_shape": "missing",
        }
    value = float(value)
    return {
        "sum": round(value * max(1, count), 12),
        "count": max(1, count),
        "mean": round(value, 12),
        "min": round(value, 12),
        "max": round(value, 12),
        "positive_rows": max(1, count) if value > 0 else 0,
        "negative_rows": max(1, count) if value < 0 else 0,
        "zero_rows": max(1, count) if value == 0 else 0,
        "match_rows_with_metric": max(1, count),
        "source_field": source_field,
        "source_shape": "scope_mean",
    }


def _decision_from_mean(count: int, mean_r: float | None) -> str:
    if mean_r is None or count < 3:
        return "MIXED"
    if mean_r <= -0.05:
        return "AVOID"
    if mean_r >= 0.05:
        return "FOLLOW"
    return "MIXED"


def _proxy_class(mean_r: float | None) -> str:
    if mean_r is None:
        return "MIXED_PROXY_R"
    if mean_r <= -0.5:
        return "STRONG_NEGATIVE_PROXY_R"
    if mean_r < 0:
        return "NEGATIVE_PROXY_R"
    if mean_r >= 0.5:
        return "STRONG_POSITIVE_PROXY_R"
    if mean_r > 0:
        return "POSITIVE_PROXY_R"
    return "MIXED_PROXY_R"


def _slug(value: Any, *, limit: int = 48) -> str:
    text = _norm(value).casefold()
    chars = [ch if ch.isalnum() else "_" for ch in text]
    slug = "_".join(part for part in "".join(chars).split("_") if part)
    return (slug or "unknown")[:limit]


def _scope(
    *,
    symbol: str = "",
    timeframe: str = "M15",
    session: str = "",
    side: str = "",
    framework: str = "",
    route_family: str = "",
    source_component: str,
    action_class: str,
    entry_variant: str = "",
    target_stop_order_class: str = "",
    source_path_sha256: str = "",
) -> dict[str, str]:
    symbol = _symbol(symbol)
    route_family = route_family or framework
    return {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": symbol,
            "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
            "market": symbol,
            "timeframe": timeframe if symbol or timeframe else "",
            "market_timeframe": timeframe if symbol or timeframe else "",
            "route_session": session,
            "side": side,
            "framework": framework,
            "route_family": route_family,
            "source_component": source_component,
            "action_class": action_class,
            "entry_variant": entry_variant,
            "target_stop_order_class": target_stop_order_class,
            "source_path_sha256": source_path_sha256 if not symbol else "",
        }.items()
        if value
    }


def _role(decision: str, base: str) -> str:
    if decision == "FOLLOW":
        return f"{base}_follow_pressure"
    if decision == "AVOID":
        return f"{base}_avoid_filter"
    return f"{base}_context_guard"


def _runtime_row(
    *,
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_suffix: str,
    decision: str,
    source_component: str,
    action_class: str,
    event_scope: dict[str, str],
    source_rows_represented: int,
    source_declared_row_count: int | None,
    source_row_count_known: bool,
    r_evidence_class: str,
    proxy_score: float | None = None,
    proxy_r_class: str = "",
    source_repair_required: bool = False,
    source_acquisition_required: bool = False,
    source_complete: bool = False,
    source_bound: bool = False,
    target_stop_order_class: str = "",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row_id = (
        "accepted_candidate_m1_fill_source_repair:"
        f"{_hash_text(f'{unit_id}|{row_suffix}|{path_text}|{json.dumps(event_scope, sort_keys=True)}')}"
    )
    runtime_score_allowed = decision in {"FOLLOW", "AVOID"} and source_complete
    row = {
        "accepted_candidate_m1_fill_source_repair_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": f"{unit_id}:{row_suffix}",
        "schema_version": "gtos_vnext_accepted_candidate_m1_fill_source_repair_runtime_v1",
        "wave_id": WAVE_ID,
        "source_unit_id": unit_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": action_class,
        "source_role": _role(decision, action_class),
        "system_surface": "accepted_candidate_m1_fill_source_repair_runtime",
        "source_component": source_component,
        "source_artifact_path": path_text,
        "source_path": path_text,
        "source_artifact": path_text,
        "source_artifact_sha256": path_sha,
        "source_path_sha256": path_sha,
        "source_declared_row_count": source_declared_row_count,
        "source_row_count_known": source_row_count_known,
        "source_rows_represented": source_rows_represented,
        "event_scope": event_scope,
        "symbol": event_scope.get("symbol", ""),
        "source_symbol": event_scope.get("source_symbol", ""),
        "symbol_family": event_scope.get("symbol_family", ""),
        "market": event_scope.get("market", ""),
        "timeframe": event_scope.get("timeframe", ""),
        "market_timeframe": event_scope.get("market_timeframe", ""),
        "route_session": event_scope.get("route_session", ""),
        "side": event_scope.get("side", ""),
        "framework": event_scope.get("framework", ""),
        "route_family": event_scope.get("route_family", ""),
        "action_class": action_class,
        "entry_variant": event_scope.get("entry_variant", ""),
        "target_stop_order_class": target_stop_order_class
        or event_scope.get("target_stop_order_class", ""),
        "decision": decision,
        "review_action": decision,
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": proxy_r_class or _proxy_class(proxy_score),
        "source_repair_required": source_repair_required,
        "source_acquisition_required": source_acquisition_required,
        "source_bound": source_bound,
        "source_complete": source_complete,
        "runtime_score_allowed": runtime_score_allowed,
        "runtime_candidate_use_permitted": runtime_score_allowed,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "validation_safe": False,
        "implementation_action": (
            "SOURCE_REPAIR_REQUIRED"
            if source_repair_required
            else "SOURCE_ACQUISITION_REQUIRED"
            if source_acquisition_required
            else "SCOPED_ACCEPTED_CANDIDATE_FILL_RUNTIME_PRESSURE"
            if runtime_score_allowed
            else "MERGE_AS_EXECUTION_ADJACENT_CONTEXT"
        ),
        "r_metrics": {
            "proxy_score": _metric(
                proxy_score,
                source_field="mean_r_or_proxy",
                count=max(1, source_rows_represented),
            ),
            "cost_adjusted_simulated_r": _metric(
                proxy_score,
                source_field="mean_r_or_proxy",
                count=max(1, source_rows_represented),
            ),
            "stress_simulated_r": _metric(
                proxy_score,
                source_field="mean_r_or_proxy",
                count=max(1, source_rows_represented),
            ),
            "effective_n": _metric(
                source_rows_represented,
                source_field="source_rows_represented",
                count=1,
            ),
        },
        "detail": detail or {},
    }
    return row


def _grouped_result_rows(
    *,
    unit_id: str,
    path_text: str,
    path_sha: str,
    source_declared_row_count: int | None,
    rows: Iterable[dict[str, Any]],
    source_component: str,
    action_class_prefix: str,
    timeframe: str,
    symbol_field: str,
    session_field: str,
    side_field: str,
    framework_field: str,
    r_field: str,
    row_suffix_prefix: str,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        value = _to_float(row.get(r_field))
        if value is None:
            continue
        key = (
            _symbol(row.get(symbol_field)),
            _session(row.get(session_field)),
            _side(row.get(side_field)),
            _norm(row.get(framework_field)) or "ob_retest",
        )
        groups[key].append(value)

    built: list[dict[str, Any]] = []
    for (symbol, sess, side, framework), values in sorted(groups.items()):
        count = len(values)
        mean_r = sum(values) / count if count else None
        decision = _decision_from_mean(count, mean_r)
        action_class = f"{action_class_prefix}_{decision.casefold()}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"{row_suffix_prefix}:{symbol}:{sess}:{side}:{framework}",
                decision=decision,
                source_component=source_component,
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    timeframe=timeframe,
                    session=sess,
                    side=side,
                    framework=framework,
                    source_component=source_component,
                    action_class=action_class,
                ),
                source_rows_represented=count,
                source_declared_row_count=source_declared_row_count,
                source_row_count_known=source_declared_row_count is not None,
                r_evidence_class=f"{action_class_prefix.upper()}_{decision}",
                proxy_score=mean_r,
                source_complete=True,
                source_bound=True,
                detail={
                    "group_count": count,
                    "sum_r": round(sum(values), 12),
                    "mean_r": round(mean_r, 12) if mean_r is not None else None,
                    "min_r": round(min(values), 12),
                    "max_r": round(max(values), 12),
                },
            )
        )
    return built


def _build_unified_filled_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    rows = _read_jsonl(_repo_path(path_text))
    built = _grouped_result_rows(
        unit_id=unit_id,
        path_text=path_text,
        path_sha=path_sha,
        source_declared_row_count=row_count,
        rows=rows,
        source_component="accepted_filled_candidate_result_pressure",
        action_class_prefix="accepted_filled_candidate_result",
        timeframe="M15",
        symbol_field="symbol",
        session_field="kill_zone",
        side_field="direction",
        framework_field="framework",
        r_field="r_multiple",
        row_suffix_prefix="symbol_session_side_framework",
    )

    touch_groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        value = _to_float(row.get("r_multiple"))
        if value is None:
            continue
        touch = _to_float(row.get("touch_count_at_eval"))
        if touch is None or touch < 0:
            bucket = "touch_unknown"
        elif touch <= 1:
            bucket = "touch_1"
        else:
            bucket = "touch_2plus"
        touch_groups[(_symbol(row.get("symbol")), _side(row.get("direction")), bucket)].append(value)
    for (symbol, side, bucket), values in sorted(touch_groups.items()):
        count = len(values)
        mean_r = sum(values) / count if count else None
        decision = _decision_from_mean(count, mean_r)
        action_class = f"accepted_candidate_touch_bucket_{bucket}_{decision.casefold()}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"touch_bucket:{symbol}:{side}:{bucket}",
                decision=decision,
                source_component="accepted_candidate_touch_bucket_result_pressure",
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    timeframe="M15",
                    side=side,
                    framework="ob_retest",
                    source_component="accepted_candidate_touch_bucket_result_pressure",
                    action_class=action_class,
                    entry_variant=bucket,
                ),
                source_rows_represented=count,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class=f"ACCEPTED_CANDIDATE_TOUCH_BUCKET_{decision}",
                proxy_score=mean_r,
                source_complete=True,
                source_bound=True,
                detail={
                    "touch_bucket": bucket,
                    "group_count": count,
                    "sum_r": round(sum(values), 12),
                    "mean_r": round(mean_r, 12) if mean_r is not None else None,
                },
            )
        )
    return built


def _build_feature_stratification_rows(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
) -> list[dict[str, Any]]:
    rows = _read_csv(_repo_path(path_text))
    built: list[dict[str, Any]] = []
    for row in rows:
        n = int(_to_float(row.get("n")) or 0)
        if n <= 0:
            continue
        feature = _norm(row.get("feature"))
        bucket = _norm(row.get("bucket"))
        exp_r = _to_float(row.get("exp_R"))
        decision = _decision_from_mean(n, exp_r)
        action_class = f"accepted_candidate_feature_bucket_{_slug(feature)}_{decision.casefold()}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"feature_bucket:{feature}:{bucket}",
                decision=decision,
                source_component="accepted_candidate_feature_stratification_pressure",
                action_class=action_class,
                event_scope=_scope(
                    timeframe="M15",
                    source_component="accepted_candidate_feature_stratification_pressure",
                    action_class=action_class,
                    entry_variant=f"{feature}:{bucket}",
                ),
                source_rows_represented=n,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class=f"ACCEPTED_CANDIDATE_FEATURE_BUCKET_{decision}",
                proxy_score=exp_r,
                source_complete=exp_r is not None and n >= 20,
                source_bound=exp_r is not None and n >= 20,
                detail=row,
            )
        )
    return built


def _distribution_proxy(row: dict[str, Any]) -> float | None:
    n = int(_to_float(row.get("N") or row.get("n")) or 0)
    wins = int(_to_float(row.get("WIN") or row.get("wins")) or 0)
    losses = int(_to_float(row.get("LOSS") or row.get("losses")) or 0)
    total = n or wins + losses
    if total <= 0:
        return None
    return round((wins - losses) / total, 12)


def _build_distribution_rows(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    sections = {
        "by_symbol": "symbol",
        "by_direction": "side",
        "by_framework": "framework",
        "by_kill_zone": "session",
    }
    for section, scope_type in sections.items():
        payload = data.get(section, {})
        if not isinstance(payload, dict):
            continue
        for key, stats in sorted(payload.items()):
            if not isinstance(stats, dict):
                continue
            n = int(_to_float(stats.get("N") or stats.get("n")) or 0)
            proxy = _distribution_proxy(stats)
            decision = _decision_from_mean(n, proxy)
            action_class = (
                f"accepted_candidate_distribution_{_slug(section)}_{decision.casefold()}"
            )
            built.append(
                _runtime_row(
                    unit_id=unit_id,
                    path_text=path_text,
                    path_sha=path_sha,
                    row_suffix=f"distribution:{section}:{key}",
                    decision=decision,
                    source_component="accepted_candidate_distribution_result_pressure",
                    action_class=action_class,
                    event_scope=_scope(
                        symbol=key if scope_type == "symbol" else "",
                        session=_session(key) if scope_type == "session" else "",
                        side=_side(key) if scope_type == "side" else "",
                        framework=key if scope_type == "framework" else "",
                        source_component="accepted_candidate_distribution_result_pressure",
                        action_class=action_class,
                    ),
                    source_rows_represented=max(1, n),
                    source_declared_row_count=row_count,
                    source_row_count_known=row_count is not None,
                    r_evidence_class=f"ACCEPTED_CANDIDATE_DISTRIBUTION_{decision}",
                    proxy_score=proxy,
                    source_complete=proxy is not None and n >= 20,
                    source_bound=proxy is not None and n >= 20,
                    detail={"section": section, "bucket": key, **stats},
                )
            )
    return built or _build_generic_context_row(
        unit_id,
        path_text,
        path_sha,
        row_count,
        "accepted_candidate_distribution_result_pressure",
    )


def _build_feature_ranking_rows(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    rows = data if isinstance(data, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        n = int(_to_float(row.get("n")) or 0)
        feature = _norm(row.get("feature"))
        rho = _to_float(row.get("rho_R"))
        p_value = _to_float(row.get("p_rho_R"))
        decision = "MIXED"
        if rho is not None and p_value is not None and n >= 20 and p_value <= 0.10:
            if rho <= -0.10:
                decision = "AVOID"
            elif rho >= 0.10:
                decision = "FOLLOW"
        action_class = f"accepted_candidate_feature_ranking_{decision.casefold()}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"feature_ranking:{feature}",
                decision=decision,
                source_component="accepted_candidate_feature_ranking_pressure",
                action_class=action_class,
                event_scope=_scope(
                    timeframe="M15",
                    source_component="accepted_candidate_feature_ranking_pressure",
                    action_class=action_class,
                    entry_variant=feature,
                ),
                source_rows_represented=max(1, n),
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class=f"ACCEPTED_CANDIDATE_FEATURE_RANKING_{decision}",
                proxy_score=rho,
                source_complete=decision in {"FOLLOW", "AVOID"},
                source_bound=decision in {"FOLLOW", "AVOID"},
                detail=row,
            )
        )
    return built or _build_generic_context_row(
        unit_id,
        path_text,
        path_sha,
        row_count,
        "accepted_candidate_feature_ranking_pressure",
    )


def _build_h1_h2_split_rows(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    for feature, stats in sorted(data.items()):
        if not isinstance(stats, dict):
            continue
        h2_rho = _to_float(stats.get("h2_rho"))
        action_class = "accepted_candidate_h1_h2_feature_stability_context"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"h1_h2:{feature}",
                decision="MIXED",
                source_component="accepted_candidate_h1_h2_feature_stability_context",
                action_class=action_class,
                event_scope=_scope(
                    timeframe="M15",
                    source_component="accepted_candidate_h1_h2_feature_stability_context",
                    action_class=action_class,
                    entry_variant=feature,
                ),
                source_rows_represented=1,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="ACCEPTED_CANDIDATE_H1_H2_FEATURE_STABILITY_CONTEXT",
                proxy_score=h2_rho,
                detail=stats,
            )
        )
    return built


def _build_classifier_validation_rows(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    for phase, stats in sorted(data.items()):
        if not isinstance(stats, dict):
            continue
        n_test = int(_to_float(stats.get("n_test")) or 0)
        auc = _to_float(stats.get("auc_test"))
        decision = "FOLLOW" if auc is not None and auc >= 0.70 and n_test >= 30 else "MIXED"
        action_class = f"accepted_candidate_classifier_validation_{decision.casefold()}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"classifier:{phase}",
                decision=decision,
                source_component="accepted_candidate_classifier_validation_context",
                action_class=action_class,
                event_scope=_scope(
                    timeframe="M15",
                    source_component="accepted_candidate_classifier_validation_context",
                    action_class=action_class,
                    entry_variant=phase,
                ),
                source_rows_represented=max(1, n_test),
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class=f"ACCEPTED_CANDIDATE_CLASSIFIER_VALIDATION_{decision}",
                proxy_score=auc,
                source_complete=decision == "FOLLOW",
                source_bound=decision == "FOLLOW",
                detail=stats,
            )
        )
    return built


def _build_stratification_json_rows(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    for feature, buckets in sorted(data.items()):
        if not isinstance(buckets, list):
            continue
        for row in buckets:
            if not isinstance(row, dict):
                continue
            n = int(_to_float(row.get("n")) or 0)
            if n <= 0:
                continue
            bucket = _norm(row.get("bucket"))
            exp_r = _to_float(row.get("exp_R"))
            decision = _decision_from_mean(n, exp_r)
            action_class = (
                f"accepted_candidate_stratification_{_slug(feature)}_{decision.casefold()}"
            )
            built.append(
                _runtime_row(
                    unit_id=unit_id,
                    path_text=path_text,
                    path_sha=path_sha,
                    row_suffix=f"stratification:{feature}:{bucket}",
                    decision=decision,
                    source_component="accepted_candidate_feature_stratification_pressure",
                    action_class=action_class,
                    event_scope=_scope(
                        timeframe="M15",
                        source_component="accepted_candidate_feature_stratification_pressure",
                        action_class=action_class,
                        entry_variant=f"{feature}:{bucket}",
                    ),
                    source_rows_represented=n,
                    source_declared_row_count=row_count,
                    source_row_count_known=row_count is not None,
                    r_evidence_class=f"ACCEPTED_CANDIDATE_FEATURE_BUCKET_{decision}",
                    proxy_score=exp_r,
                    source_complete=exp_r is not None and n >= 20,
                    source_bound=exp_r is not None and n >= 20,
                    detail=row,
                )
            )
    return built


def _build_m1_fill_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    rows = _read_csv(_repo_path(path_text))
    return _grouped_result_rows(
        unit_id=unit_id,
        path_text=path_text,
        path_sha=path_sha,
        source_declared_row_count=row_count,
        rows=rows,
        source_component="m1_fill_quality_result_pressure",
        action_class_prefix="m1_fill_quality_result",
        timeframe="M1",
        symbol_field="symbol",
        session_field="kill_zone",
        side_field="",
        framework_field="framework",
        r_field="r_multiple",
        row_suffix_prefix="symbol_session_framework",
    )


def _build_feature_comparison_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    rows = _read_csv(_repo_path(path_text))
    built: list[dict[str, Any]] = []
    for row in rows:
        symbol = _symbol(row.get("symbol"))
        feature = _norm(row.get("feature"))
        verdict = _norm(row.get("verdict_m1")) or _norm(row.get("verdict_m15"))
        action_class = "m1_micro_feature_no_signal_context"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"feature:{symbol}:{feature}",
                decision="MIXED",
                source_component="m1_micro_feature_no_signal_context",
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    timeframe="M1",
                    source_component="m1_micro_feature_no_signal_context",
                    action_class=action_class,
                    entry_variant=feature,
                ),
                source_rows_represented=1,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="M1_MICRO_FEATURE_NO_SIGNAL_OR_INSUFFICIENT_N",
                proxy_score=None,
                detail={"feature": feature, "verdict": verdict, "source_row": row},
            )
        )
    return built


def _build_m1_source_coverage_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    rows = _read_csv(_repo_path(path_text))
    built: list[dict[str, Any]] = []
    symbol_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        symbol_rows[_symbol(row.get("canonical_symbol") or row.get("symbol"))].append(row)
    for symbol, members in sorted(symbol_rows.items()):
        status_counts = Counter(_norm(row.get("status") or row.get("source")) for row in members)
        action_class = "m1_backfill_source_coverage_guard"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"coverage:{symbol}",
                decision="MIXED",
                source_component="m1_backfill_source_coverage_guard",
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    timeframe="M1",
                    source_component="m1_backfill_source_coverage_guard",
                    action_class=action_class,
                ),
                source_rows_represented=len(members),
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
                source_acquisition_required=True,
                detail={"status_counts": dict(status_counts)},
            )
        )
    return built


def _build_fill_sim_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    timeframe = "M1" if "m1" in Path(path_text).name.casefold() else "M15"
    for trade_id, row in sorted(data.items()):
        realized_r = _to_float(row.get("realized_r"))
        decision = "FOLLOW" if realized_r is not None and realized_r > 0 else "AVOID"
        exit_reason = _norm(row.get("exit_reason"))
        trade_parts = trade_id.split("_")
        trade_session = trade_parts[1] if len(trade_parts) > 1 else ""
        action_class = (
            "fill_sim_stop_first_avoid"
            if "sl_hit" in exit_reason.casefold()
            else "fill_sim_target_first_follow"
        )
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"fill_sim:{trade_id}",
                decision=decision,
                source_component="a4_fill_simulation_result_pressure",
                action_class=action_class,
                event_scope=_scope(
                    symbol="XAUUSD",
                    timeframe=timeframe,
                    session=_session(trade_session),
                    side=_side(row.get("direction")),
                    framework="ob_retest",
                    source_component="a4_fill_simulation_result_pressure",
                    action_class=action_class,
                    target_stop_order_class=(
                        "STOP_FIRST_FILLED_LOSS"
                        if decision == "AVOID"
                        else "TARGET_FIRST_FILLED_WIN"
                    ),
                ),
                source_rows_represented=1,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class=f"A4_FILL_SIMULATION_{decision}",
                proxy_score=realized_r,
                source_complete=True,
                source_bound=True,
                target_stop_order_class=(
                    "STOP_FIRST_FILLED_LOSS"
                    if decision == "AVOID"
                    else "TARGET_FIRST_FILLED_WIN"
                ),
                detail={"trade_id": trade_id, **row},
            )
        )
    return built


def _build_backfill_bias_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    path = _repo_path(path_text)
    if path.suffix.casefold() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        readout = data.get("bias_readout", {}) if isinstance(data, dict) else {}
        flags = readout.get("coverage_bias_flags", []) + readout.get("label_bias_flags", [])
        for idx, flag in enumerate(flags):
            symbol = _symbol(flag.get("symbol"))
            action_class = "old_backfill_source_bias_guard"
            built.append(
                _runtime_row(
                    unit_id=unit_id,
                    path_text=path_text,
                    path_sha=path_sha,
                    row_suffix=f"bias_flag:{idx}:{symbol}",
                    decision="MIXED",
                    source_component="old_backfill_source_bias_guard",
                    action_class=action_class,
                    event_scope=_scope(
                        symbol=symbol,
                        source_component="old_backfill_source_bias_guard",
                        action_class=action_class,
                    ),
                    source_rows_represented=1,
                    source_declared_row_count=row_count,
                    source_row_count_known=row_count is not None,
                    r_evidence_class="UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
                    source_acquisition_required=True,
                    detail=flag,
                )
            )
    if built:
        return built
    return _build_generic_context_row(unit_id, path_text, path_sha, row_count, "old_backfill_source_context")


def _build_fillback_inventory_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    panel = (
        data.get("f11_mechanical_2024_2025_projection", {})
        .get("non_xau_panel_2024_2025", {})
    )
    built: list[dict[str, Any]] = []
    for symbol, payload in sorted(panel.items()):
        action_class = "non_xau_fillback_source_inventory_guard"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"fillback_inventory:{symbol}",
                decision="MIXED",
                source_component="non_xau_fillback_source_inventory_guard",
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    source_component="non_xau_fillback_source_inventory_guard",
                    action_class=action_class,
                ),
                source_rows_represented=1,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
                source_acquisition_required=True,
                detail=payload if isinstance(payload, dict) else {"payload": payload},
            )
        )
    return built or _build_generic_context_row(unit_id, path_text, path_sha, row_count, "non_xau_fillback_source_inventory_guard")


def _build_missed_fill_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    counts = data.get("counts", {})
    action_class = "missed_fill_entry_geometry_source_requirement"
    built.append(
        _runtime_row(
            unit_id=unit_id,
            path_text=path_text,
            path_sha=path_sha,
            row_suffix="overall_missed_fill_rate",
            decision="MIXED",
            source_component="missed_fill_entry_geometry_source_requirement",
            action_class=action_class,
            event_scope=_scope(
                source_component="missed_fill_entry_geometry_source_requirement",
                action_class=action_class,
                source_path_sha256=path_sha,
            ),
            source_rows_represented=int(counts.get("countable_primary_opportunities") or 1),
            source_declared_row_count=row_count,
            source_row_count_known=row_count is not None,
            r_evidence_class="UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
            proxy_score=_to_float(counts.get("countable_missed_fill_rate")),
            source_acquisition_required=True,
            detail={"counts": counts, "promotion_verdict": data.get("promotion_verdict")},
        )
    )
    for row in data.get("examples_countable_missed", []):
        symbol = _symbol(row.get("symbol"))
        action_class = "missed_fill_to_tp_area_source_requirement"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"missed_fill_example:{row.get('candidate_id')}",
                decision="MIXED",
                source_component="missed_fill_to_tp_area_source_requirement",
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    timeframe="M15",
                    session=_session(row.get("session")),
                    side=_side(row.get("side")),
                    framework=_norm(row.get("framework")),
                    source_component="missed_fill_to_tp_area_source_requirement",
                    action_class=action_class,
                    target_stop_order_class="TARGET_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
                ),
                source_rows_represented=1,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
                proxy_score=_to_float(row.get("inside_r_required_to_touch")),
                source_acquisition_required=True,
                target_stop_order_class="TARGET_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
                detail=row,
            )
        )
    return built


def _build_adv002_requirement_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    built: list[dict[str, Any]] = []
    for row in data.get("rows", []):
        action_class = "adv002_source_control_exact_requirement_guard"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"requirement:{row.get('requirement_row_id')}",
                decision="MIXED",
                source_component="adv002_source_control_exact_requirement_guard",
                action_class=action_class,
                event_scope=_scope(
                    source_component="adv002_source_control_exact_requirement_guard",
                    action_class=action_class,
                    source_path_sha256=path_sha,
                ),
                source_rows_represented=1,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
                source_acquisition_required=True,
                detail=row,
            )
        )
    return built


def _mean_numeric(rows: Iterable[dict[str, Any]], fields: tuple[str, ...]) -> float | None:
    values: list[float] = []
    for row in rows:
        for field in fields:
            value = _to_float(row.get(field))
            if value is not None:
                values.append(value)
                break
    return sum(values) / len(values) if values else None


def _decision_for_exact_r_group(action_class: str, exact_join: str, mean_r: float | None) -> tuple[str, bool, bool, bool]:
    action = action_class.upper()
    join = exact_join.upper()
    source_repair = "NOT_COMPUTABLE" in join or "MISSING" in join
    source_complete = not source_repair and mean_r is not None
    if action == "KILL":
        return "AVOID", source_repair, False, source_complete
    if action == "REDESIGN":
        return "MIXED", True, False, False
    if action == "IMPLEMENT_DEFAULT_OFF" and mean_r is not None and mean_r > 0:
        return "FOLLOW", source_repair, False, source_complete
    if source_repair:
        return "MIXED", True, False, False
    return _decision_from_mean(3, mean_r), False, False, source_complete


def _build_exact_r_jsonl_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    rows = _read_jsonl(_repo_path(path_text))
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                _symbol(row.get("candidate_symbol") or row.get("symbol")),
                _norm(row.get("primitive_family")) or "unknown_primitive",
                _norm(row.get("action_class")) or _norm(row.get("current_action")) or "UNKNOWN_ACTION",
                _norm(row.get("exact_join_decision")) or _norm(row.get("implementation_decision")) or "UNKNOWN_EXACT_JOIN",
            )
        ].append(row)

    built: list[dict[str, Any]] = []
    for (symbol, primitive, action, exact_join), members in sorted(groups.items()):
        mean_r = _mean_numeric(
            members,
            (
                "exact_r",
                "after_proxy_r",
                "before_proxy_r",
                "input_proxy_r",
                "local_non_account_r_reference",
            ),
        )
        decision, source_repair, source_acquisition, source_complete = _decision_for_exact_r_group(
            action,
            exact_join,
            mean_r,
        )
        component = "exact_r_bridge_missing_identifier_source_repair" if source_repair else "exact_r_bridge_materialized_context"
        if action.upper() == "KILL":
            component = "exact_r_bridge_kill_branch_avoid"
        elif action.upper() == "REDESIGN":
            component = "exact_r_bridge_redesign_source_repair"
        action_class = f"{component}_{action.casefold()}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"exact_r:{symbol}:{primitive}:{action}:{exact_join}",
                decision=decision,
                source_component=component,
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    source_component=component,
                    action_class=action_class,
                    entry_variant=primitive,
                ),
                source_rows_represented=len(members),
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R" if source_repair else f"EXACT_R_BRIDGE_{decision}",
                proxy_score=mean_r,
                source_repair_required=source_repair,
                source_acquisition_required=source_acquisition,
                source_complete=source_complete,
                source_bound=source_complete,
                detail={
                    "primitive_family": primitive,
                    "action_class": action,
                    "exact_join_decision": exact_join,
                    "rows": len(members),
                    "missing_identifier_counts": dict(Counter(_norm(row.get("missing_identifier")) for row in members if _norm(row.get("missing_identifier")))),
                    "branch_decision_counts": dict(Counter(_norm(row.get("branch_decision")) for row in members).most_common(10)),
                },
            )
        )
    return built


def _build_alias_search_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    rows = _read_jsonl(_repo_path(path_text))
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        exact_count = int(row.get("exact_r_source_count") or 0)
        groups[(_candidate_symbol(row.get("candidate_id")), "exact_r_alias_found" if exact_count else "exact_r_alias_missing")].append(row)
    built: list[dict[str, Any]] = []
    for (symbol, status), members in sorted(groups.items()):
        source_repair = status == "exact_r_alias_missing"
        action_class = "exact_r_alias_search_source_repair" if source_repair else "exact_r_alias_search_context"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"alias:{symbol}:{status}",
                decision="MIXED",
                source_component=action_class,
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    source_component=action_class,
                    action_class=action_class,
                ),
                source_rows_represented=len(members),
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R" if source_repair else "EXACT_R_ALIAS_SEARCH_CONTEXT",
                source_repair_required=source_repair,
                detail={
                    "status": status,
                    "rows": len(members),
                    "source_alias_hit_count": sum(int(row.get("source_alias_hit_count") or 0) for row in members),
                },
            )
        )
    return built


def _build_exact_r_summary_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    summaries = data.get("group_summaries", {}) if isinstance(data, dict) else {}
    built: list[dict[str, Any]] = []
    for key, row in sorted(summaries.items()):
        if not isinstance(row, dict):
            continue
        symbol = _symbol(row.get("symbol"))
        session = _session(row.get("session"))
        primitive = _norm(row.get("strategy_or_family")) or "unknown_primitive"
        branch_decision = _norm(row.get("branch_decision"))
        exact_rows = int(row.get("exact_owner_rows") or 0) + int(row.get("exact_reference_rows") or 0)
        proxy_rows = int(row.get("proxy_rows") or 0)
        rows_represented = int(row.get("rows") or 0) or max(1, exact_rows + proxy_rows)
        exact_sum = _to_float(row.get("exact_owner_sum"))
        if exact_sum is None:
            exact_sum = 0.0
        exact_sum += _to_float(row.get("exact_reference_sum")) or 0.0
        proxy_sum = _to_float(row.get("proxy_sum")) or 0.0
        mean_r = None
        if exact_rows:
            mean_r = exact_sum / exact_rows
        elif proxy_rows:
            mean_r = proxy_sum / proxy_rows
        source_repair = "REDESIGN" in branch_decision.upper() and exact_rows == 0
        decision = _decision_from_mean(rows_represented, mean_r)
        if "KILL" in branch_decision.upper():
            decision = "AVOID"
            component = "exact_r_bridge_kill_branch_avoid"
        elif source_repair:
            decision = "MIXED"
            component = "exact_r_bridge_redesign_source_repair"
        else:
            component = "exact_r_bridge_materialized_context"
        action_class = f"{component}_{_slug(branch_decision, limit=64)}"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix=f"exact_r_summary:{key}",
                decision=decision,
                source_component=component,
                action_class=action_class,
                event_scope=_scope(
                    symbol=symbol,
                    session=session,
                    source_component=component,
                    action_class=action_class,
                    entry_variant=primitive,
                ),
                source_rows_represented=rows_represented,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R"
                if source_repair
                else f"EXACT_R_BRIDGE_{decision}",
                proxy_score=mean_r,
                source_repair_required=source_repair,
                source_complete=mean_r is not None and not source_repair,
                source_bound=mean_r is not None and not source_repair,
                detail=row,
            )
        )
    return built or _build_generic_context_row(
        unit_id,
        path_text,
        path_sha,
        row_count,
        "exact_r_source_materialization_support_context",
    )


def _build_exact_r_verification_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    data = json.loads(_repo_path(path_text).read_text(encoding="utf-8-sig"))
    source_repair_rows = int(data.get("missing_r_rows") or 0) + sum(
        int(value or 0) for value in (data.get("missing_identifier_counts") or {}).values()
    )
    exact_owner = int(data.get("exact_r_owner_rows") or data.get("after_exact_r_owner_rows") or 0)
    exact_ref = int(data.get("exact_r_reference_rows") or data.get("after_exact_r_reference_rows") or 0)
    built: list[dict[str, Any]] = []
    if source_repair_rows:
        action_class = "exact_r_verification_missing_identifier_source_repair"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix="verification_missing_identifier",
                decision="MIXED",
                source_component=action_class,
                action_class=action_class,
                event_scope=_scope(
                    source_component=action_class,
                    action_class=action_class,
                    source_path_sha256=path_sha,
                ),
                source_rows_represented=source_repair_rows,
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R",
                source_repair_required=True,
                detail=data,
            )
        )
    if exact_owner or exact_ref:
        mean_r = _to_float(data.get("exact_r_owner_sum") or data.get("after_exact_r_owner_sum"))
        if mean_r is not None and exact_owner:
            mean_r /= exact_owner
        action_class = "exact_r_verification_owner_reference_context"
        built.append(
            _runtime_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_suffix="verification_exact_owner_reference",
                decision="FOLLOW" if mean_r is not None and mean_r > 0 else "MIXED",
                source_component=action_class,
                action_class=action_class,
                event_scope=_scope(
                    source_component=action_class,
                    action_class=action_class,
                    source_path_sha256=path_sha,
                ),
                source_rows_represented=max(1, exact_owner + exact_ref),
                source_declared_row_count=row_count,
                source_row_count_known=row_count is not None,
                r_evidence_class="EXACT_R_OWNER_REFERENCE_CONTEXT",
                proxy_score=mean_r,
                source_complete=True,
                source_bound=True,
                detail=data,
            )
        )
    return built or _build_generic_context_row(unit_id, path_text, path_sha, row_count, "exact_r_verification_context")


def _build_generic_context_row(
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
    component: str,
) -> list[dict[str, Any]]:
    action_class = component
    represented = row_count if row_count is not None else _source_row_count(_repo_path(path_text))
    return [
        _runtime_row(
            unit_id=unit_id,
            path_text=path_text,
            path_sha=path_sha,
            row_suffix="source_context",
            decision="MIXED",
            source_component=component,
            action_class=action_class,
            event_scope=_scope(
                source_component=component,
                action_class=action_class,
                source_path_sha256=path_sha,
            ),
            source_rows_represented=max(1, int(represented or 1)),
            source_declared_row_count=row_count,
            source_row_count_known=row_count is not None,
            r_evidence_class="ACCEPTED_CANDIDATE_M1_FILL_SOURCE_CONTEXT",
            detail={"source_path": path_text},
        )
    ]


def build_runtime_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit_id, path_text, declared_count in SOURCE_UNITS:
        path = _repo_path(path_text)
        path_sha = _sha256(path)
        name = path.name
        lower = path_text.casefold()
        if name == "unified_filled_cands.jsonl":
            rows.extend(_build_unified_filled_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "feature_stratification.csv":
            rows.extend(_build_feature_stratification_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "h1_h2_split.json":
            rows.extend(_build_h1_h2_split_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "section1_distributions.json":
            rows.extend(_build_distribution_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "section2_feature_ranking.json":
            rows.extend(_build_feature_ranking_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "section3_classifier.json":
            rows.extend(_build_classifier_validation_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "section4_stratification.json":
            rows.extend(_build_stratification_json_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "per_fill_features_m1.csv":
            rows.extend(_build_m1_fill_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "per_feature_comparison.csv":
            rows.extend(_build_feature_comparison_rows(unit_id, path_text, path_sha, declared_count))
        elif name in {"m1_backfill_log.csv", "reconstructor_validation_m1.csv"}:
            rows.extend(_build_m1_source_coverage_rows(unit_id, path_text, path_sha, declared_count))
        elif name in {"fill_simulation_m1_results.json", "fill_simulation_results.json"}:
            rows.extend(_build_fill_sim_rows(unit_id, path_text, path_sha, declared_count))
        elif "d11_2022_2023_backfill_bias_check" in lower:
            rows.extend(_build_backfill_bias_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "agent_e_non_xau_fillback_inventory.json":
            rows.extend(_build_fillback_inventory_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.json":
            rows.extend(_build_missed_fill_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_EXACT_REQUIREMENT_ROWS_2026-05-13.json":
            rows.extend(_build_adv002_requirement_rows(unit_id, path_text, path_sha, declared_count))
        elif name == "MAIN_ORCH24_EXACT_R_ALIAS_SEARCH_LEDGER_2026-05-17.jsonl":
            rows.extend(_build_alias_search_rows(unit_id, path_text, path_sha, _source_row_count(path)))
        elif name in {
            "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_LEDGER_2026-05-17.jsonl",
            "MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_2026-05-17.jsonl",
        }:
            rows.extend(_build_exact_r_jsonl_rows(unit_id, path_text, path_sha, _source_row_count(path)))
        elif name in {
            "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_VERIFICATION_RESULT_2026-05-17.json",
            "MAIN_ORCH24_EXACT_R_MATERIALIZATION_VERIFICATION_RESULT_2026-05-17.json",
        }:
            rows.extend(_build_exact_r_verification_rows(unit_id, path_text, path_sha, declared_count))
        elif name in {
            "MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_SUMMARY_2026-05-17.json",
            "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_SUMMARY_2026-05-17.json",
        }:
            rows.extend(_build_exact_r_summary_rows(unit_id, path_text, path_sha, declared_count))
        else:
            if path.suffix.casefold() == ".py":
                component = "accepted_candidate_m1_fill_support_code_context"
            elif "missed_fill" in lower:
                component = "missed_fill_entry_geometry_source_requirement"
            elif "exact_requirement" in lower or "exact_r" in lower:
                component = "exact_r_source_materialization_support_context"
            elif "backfill" in lower:
                component = "old_backfill_source_context"
            else:
                component = "accepted_candidate_m1_fill_source_context"
            rows.extend(_build_generic_context_row(unit_id, path_text, path_sha, declared_count, component))
    rows.sort(key=lambda row: (row["source_unit_id"], row["source_row_id"], row["row_key"]))
    return rows


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "sides": "side",
        "frameworks": "framework",
        "route_families": "route_family",
        "source_components": "source_component",
        "action_classes": "action_class",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
        "r_evidence_classes": "r_evidence_class",
        "proxy_r_classes": "proxy_r_class",
    }
    return {
        label: dict(sorted(Counter(row.get(field) for row in rows if row.get(field)).items()))
        for label, field in fields.items()
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row["source_artifact_path"]].append(row)

    source_artifacts: list[dict[str, Any]] = []
    actual_rows_counted = 0
    for unit_id, path_text, declared_count in SOURCE_UNITS:
        path = _repo_path(path_text)
        actual_count = _source_row_count(path)
        actual_rows_counted += actual_count
        source_rows = by_source.get(path_text, [])
        source_artifacts.append(
            {
                "unit_id": unit_id,
                "path": path_text,
                "sha256_or_git_blob": _sha256(path),
                "declared_rows": declared_count,
                "actual_rows_counted": actual_count,
                "row_count_known": declared_count is not None,
                "runtime_rows_read": len(source_rows),
                "source_components": sorted({row["source_component"] for row in source_rows}),
                "decision_counts": dict(Counter(row["decision"] for row in source_rows)),
            }
        )

    blank_anchor_counts = {
        field: sum(1 for row in rows if not row.get(field))
        for field in ANCHOR_FIELDS
    }
    coverage = _coverage_counts(rows)
    summary = {
        "schema_version": "gtos_vnext_accepted_candidate_m1_fill_source_repair_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 0) for row in rows),
        "wave_source_rows_counted": actual_rows_counted,
        "wave_source_artifact_count": len(SOURCE_UNITS),
        "selected_source_unit_count": len(SOURCE_UNITS),
        "selected_open_unit_count": len(SOURCE_UNITS),
        "row_count_unknown_unit_count": sum(1 for _, _, row_count in SOURCE_UNITS if row_count is None),
        "decision_counts": dict(Counter(row["decision"] for row in rows)),
        "source_component_counts": dict(Counter(row["source_component"] for row in rows)),
        "source_group_counts": dict(Counter(row["source_group"] for row in rows)),
        "source_role_counts": dict(Counter(row["source_role"] for row in rows)),
        "action_class_counts": dict(Counter(row["action_class"] for row in rows)),
        "r_evidence_class_counts": dict(Counter(row["r_evidence_class"] for row in rows)),
        "proxy_r_class_counts": dict(Counter(row["proxy_r_class"] for row in rows if row.get("proxy_r_class"))),
        "source_repair_required_rows": sum(1 for row in rows if row.get("source_repair_required")),
        "source_acquisition_required_rows": sum(1 for row in rows if row.get("source_acquisition_required")),
        "follow_pressure_rows": sum(1 for row in rows if row["decision"] == "FOLLOW"),
        "avoid_veto_rows": sum(1 for row in rows if row["decision"] == "AVOID"),
        "context_rows": sum(1 for row in rows if row["decision"] == "MIXED"),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row.get("runtime_candidate_use_permitted")),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row.get("candidate_use_allowed_now")),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(1 for row in rows if row.get("paid_api_or_vendor_call")),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row.get("runtime_trading_or_live_broker_effect")
        ),
        "coverage_counts": coverage,
        "market_counts": coverage["markets"],
        "symbol_counts": coverage["symbols"],
        "timeframe_counts": coverage["timeframes"],
        "route_session_counts": coverage["sessions"],
        "side_counts": coverage["sides"],
        "framework_counts": coverage["frameworks"],
        "route_family_counts": coverage["route_families"],
        "blank_anchor_counts": blank_anchor_counts,
        "source_artifacts": source_artifacts,
    }
    return summary


def _jsonl_text(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROWS.write_text(_jsonl_text(rows), encoding="utf-8", newline="\n")
    OUTPUT_SUMMARY.write_text(_json_text(summary), encoding="utf-8", newline="\n")


def check_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> int:
    expected_rows = _jsonl_text(rows)
    expected_summary = _json_text(summary)
    if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != expected_rows:
        print(f"stale runtime rows: {OUTPUT_ROWS}")
        return 1
    if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != expected_summary:
        print(f"stale runtime summary: {OUTPUT_SUMMARY}")
        return 1
    print(
        "accepted_candidate_m1_fill_source_repair runtime rows verified: "
        f"{len(rows)} rows, {summary['runtime_source_rows_represented']} source rows represented"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = build_runtime_rows()
    summary = build_summary(rows)
    if args.check:
        return check_outputs(rows, summary)
    write_outputs(rows, summary)
    print(
        "wrote accepted-candidate M1 fill/source-repair runtime rows: "
        f"{len(rows)} rows -> {OUTPUT_ROWS}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
