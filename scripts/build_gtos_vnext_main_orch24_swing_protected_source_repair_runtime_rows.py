#!/usr/bin/env python3
"""Build runtime rows for Main Orch24 swing-protected source-repair evidence."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_swing_protected_source_repair_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_swing_protected_source_repair_runtime_wave"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_SUMMARY_{DATE}.json"
)

REQUIREMENT_SOURCE = (
    "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_LEDGER_2026-05-17.jsonl"
)
SCORER_SPLIT_SOURCE = (
    "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_LEDGER_2026-05-17.jsonl"
)
MATERIALIZED_SOURCE_LOG = (
    REPO_ROOT / "shadow_logs" / "swing_protected_stop_current_claim_repair_decisions.jsonl"
)

SOURCE_ARTIFACTS = (
    (
        "UNIT_009362",
        "build_main_orchestrator_action_after_swing_protected_requirement_repair_2026_05_17.py",
        "45e8447b43824c4baab546519883ba15327beb4e",
    ),
    (
        "UNIT_009363",
        "build_main_orchestrator_action_after_swing_protected_scorer_split_2026_05_17.py",
        "fd495cbbd0bb9fba3be14da7f21eca1b4e1dd0c7",
    ),
    (
        "UNIT_009482",
        "build_main_orchestrator_swing_protected_repair_default_source_materialization_2026_05_17.py",
        "4a1e34cfca64741005b4263aa7ff963157db6bdf",
    ),
    ("UNIT_009613", REQUIREMENT_SOURCE, "409f231eba4aff080818df0b98228de7306d6b20"),
    (
        "UNIT_009614",
        "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
        "fa93df4e8b84133a111ebbfe285415f1377497ef",
    ),
    (
        "UNIT_009615",
        "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_SUMMARY_2026-05-17.json",
        "826952912981b5ac87dba08c40a1d8c78f36bfc2",
    ),
    (
        "UNIT_009616",
        "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
        "526728d3168689ccf1e450bf30dd1aa5d897d89f",
    ),
    ("UNIT_009617", SCORER_SPLIT_SOURCE, "e5e9e4db3b58dd55e924a8a8f938ca6f71379923"),
    (
        "UNIT_009618",
        "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_OUTPUT_MANIFEST_2026-05-17.json",
        "0d3460f32d658ee6f6ba07524f4d1cf6d3b294a2",
    ),
    (
        "UNIT_009619",
        "MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_SUMMARY_2026-05-17.json",
        "f66fedf8791a65a1edd860d5c4b3e5bb24247e85",
    ),
    (
        "UNIT_009910",
        "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_OUTPUT_MANIFEST_2026-05-17.json",
        "ed1e418dfa2bd110a482c78257540c53f27a54b2",
    ),
    (
        "UNIT_009911",
        "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_SUMMARY_2026-05-17.json",
        "0a01f114dc1d8c9f0a51ad4358f695b9bfb80f67",
    ),
    (
        "UNIT_009912",
        "MAIN_ORCH24_SWING_PROTECTED_REPAIR_DEFAULT_SOURCE_MATERIALIZATION_VERIFY_RESULT_2026-05-17.json",
        "f0a8ed5826d0c83ca67752ff1aa35fdb767f30f6",
    ),
    (
        "UNIT_009913",
        "MAIN_ORCH24_SWING_PROTECTED_SCORER_SPLIT_VERIFICATION_RESULT_2026-05-17.json",
        "95b1589941056e32175d27fcdec5cd6c244e1071",
    ),
    (
        "UNIT_010288",
        "verify_main_orchestrator_action_after_swing_protected_requirement_repair_2026_05_17.py",
        "ef5b9d036d79243b00280f0b0f4b7f3efd40630f",
    ),
    (
        "UNIT_010289",
        "verify_main_orchestrator_action_after_swing_protected_scorer_split_2026_05_17.py",
        "87aa1401b64e40b28d238c2a9b048d55a2753964",
    ),
    (
        "UNIT_010408",
        "verify_main_orchestrator_swing_protected_repair_default_source_materialization_2026_05_17.py",
        "48787d03f72292027c89122190c7afd06af3cdce",
    ),
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "route_family",
    "primitive",
    "side",
    "source_component",
    "entry_variant",
    "target_stop_order_class",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _source_row_count(path: Path) -> int:
    if path.suffix.casefold() == ".jsonl":
        return len(_read_jsonl(path))
    return 1


def _metric(value: float | int | None, *, source_field: str, count: int = 1) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
    return {
        "sum": round(value, 12),
        "count": count,
        "mean": round(value / count, 12) if count else round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": count,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _candidate_session(candidate_id: Any) -> str:
    text = _norm(candidate_id)
    match = re.search(r"T(\d{2}):(\d{2})", text)
    if not match:
        return "ALL_SESSIONS"
    minute = int(match.group(1)) * 60 + int(match.group(2))
    if 0 <= minute < 180:
        return "tokyo_kz"
    if 420 <= minute < 720:
        return "london_core"
    if 780 <= minute < 1020:
        return "ny_core"
    return "off_core_session"


def _target_stop_order_class(row: dict[str, Any]) -> str:
    outcome = _upper(row.get("after_outcome_status"))
    if "TP1" in outcome and "SL" in outcome:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    if "TP1" in outcome:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "SL" in outcome:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "NO_FILL" in outcome:
        return "NO_FILL_TP_AREA_WITHOUT_LIMIT_TOUCH"
    if _upper(row.get("swing_protected_stop_status")) != "SWING_PROTECTED_STOP_CONFIRMED":
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"


def _is_target_row(row: dict[str, Any]) -> bool:
    return _norm(row.get("source_capture_surface")) == "swing_protected_stop_scorer"


def _behavior(row: dict[str, Any]) -> dict[str, str]:
    action = _upper(row.get("action_class"))
    branch = _upper(row.get("branch_decision"))
    swing_status = _upper(row.get("swing_protected_stop_status"))
    proxy = _float(row.get("after_proxy_r"))

    if action == "KILL" or swing_status in {
        "NO_SIDE_COMPATIBLE_PROTECTED_SWING",
        "STOP_DOES_NOT_PROTECT_COMPATIBLE_SWING",
    }:
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_swing_protected_unprotected_stop_guard",
            "source_role": "main_orch24_swing_protected_unprotected_stop_guard",
            "source_group": "main_orch24_swing_protected_unprotected_stop_avoid_filter",
            "system_surface": "execution_adjacent_main_orch24_swing_protected_stop_guard",
            "action_class": "main_orch24_swing_protected_unprotected_stop_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_SWING_PROTECTED_UNPROTECTED_STOP_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
        }
    if proxy is not None and proxy < 0:
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_swing_protected_negative_proxy_guard",
            "source_role": "main_orch24_swing_protected_negative_proxy_guard",
            "source_group": "main_orch24_swing_protected_negative_proxy_avoid_filter",
            "system_surface": "execution_adjacent_main_orch24_swing_protected_negative_proxy_guard",
            "action_class": "main_orch24_swing_protected_negative_proxy_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_SWING_PROTECTED_NEGATIVE_PROXY_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
        }
    if "ADVERSE" in branch and proxy is None:
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_swing_protected_source_acquisition",
            "source_role": "main_orch24_swing_protected_source_acquisition_guard",
            "source_group": "main_orch24_swing_protected_source_acquisition",
            "system_surface": "execution_adjacent_main_orch24_swing_protected_source_acquisition",
            "action_class": "main_orch24_swing_protected_source_acquisition_context",
            "r_evidence_class": "MAIN_ORCH24_SWING_PROTECTED_SOURCE_ACQUISITION_REQUIRED",
            "proxy_r_class": "MIXED_PROXY_R",
        }
    if proxy is not None and proxy > 0:
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_swing_protected_tick_repair_follow",
            "source_role": "main_orch24_swing_protected_tick_repair_follow",
            "source_group": "main_orch24_swing_protected_positive_proxy",
            "system_surface": "execution_adjacent_main_orch24_swing_protected_positive_proxy",
            "action_class": "main_orch24_swing_protected_positive_proxy_follow",
            "r_evidence_class": "MAIN_ORCH24_SWING_PROTECTED_POSITIVE_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_swing_protected_neutral_context",
        "source_role": "main_orch24_swing_protected_neutral_context",
        "source_group": "main_orch24_swing_protected_neutral_context",
        "system_surface": "execution_adjacent_main_orch24_swing_protected_neutral_context",
        "action_class": "main_orch24_swing_protected_neutral_context",
        "r_evidence_class": "MAIN_ORCH24_SWING_PROTECTED_NEUTRAL_CONTEXT",
        "proxy_r_class": "FLAT_PROXY_R",
    }


def _base_scope(
    *,
    symbol: str,
    side: str,
    route_session: str,
    primitive: str,
    source_component: str,
    target_stop_order_class: str,
) -> dict[str, str]:
    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": route_session or "ALL_SESSIONS",
        "route_family": "main_orch24_swing_protected_source_repair",
        "primitive": primitive,
        "source_component": source_component,
        "side": side,
        "entry_variant": "swing_protected_stop_source_repair",
        "target_stop_order_class": target_stop_order_class,
    }
    return {key: value for key, value in scope.items() if value}


def _runtime_row(
    *,
    line_no: int,
    source_path: Path,
    source_sha: str,
    source_row: dict[str, Any],
    behavior: dict[str, str],
    event_scope: dict[str, str],
    metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    row_id = (
        f"main_orch24:swing_protected:{line_no}:"
        f"{_sha256_text(json.dumps(source_row, sort_keys=True))[:16]}"
    )
    runtime = {
        "schema_version": "gtos_vnext_main_orch24_swing_protected_source_repair_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_swing_protected_source_repair_runtime_row",
        "main_orch24_swing_protected_source_repair_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_kind": "main_orch24_swing_protected_source_repair_row",
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": behavior["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": behavior["review_action"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
        "event_scope": event_scope,
        "source_bound": bool(event_scope),
        "source_complete": behavior["review_action"] in {"FOLLOW", "AVOID"},
        "candidate_use_allowed_now": behavior["review_action"] in {"FOLLOW", "AVOID"},
        "runtime_candidate_use_permitted": behavior["review_action"] in {"FOLLOW", "AVOID"},
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch24_swing_protected_source_repair_shadow_runtime",
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_row_id": source_row.get("row_id"),
        "candidate_id": source_row.get("candidate_id"),
        "source_payload_hash": _sha256_text(json.dumps(source_row, sort_keys=True)),
        "r_metrics": metrics,
        "original_action_class": source_row.get("action_class"),
        "branch_decision": source_row.get("branch_decision"),
        "current_action": source_row.get("current_action"),
        "implementation_decision": source_row.get("implementation_decision"),
        "coverage_status": source_row.get("coverage_status"),
        "data_requirement_state": source_row.get("data_requirement_state"),
        "decision_evidence": source_row.get("decision_evidence"),
        "scoring_boundary": source_row.get("scoring_boundary"),
        "next_action": source_row.get("next_action"),
        "primitive_family": source_row.get("primitive_family"),
        "after_proxy_r": _float(source_row.get("after_proxy_r")),
        "before_proxy_r": _float(source_row.get("before_proxy_r")),
        "proxy_r_delta": _float(source_row.get("proxy_r_delta")),
        "after_outcome_status": source_row.get("after_outcome_status"),
        "after_score_status": source_row.get("after_score_status"),
        "after_strategy_status": source_row.get("after_strategy_status"),
        "source_capture_surface": source_row.get("source_capture_surface"),
        "swing_protected_stop_status": source_row.get("swing_protected_stop_status"),
        "swing_protected_source_status": source_row.get("swing_protected_source_status"),
        "swing_protected_match_timeframe": source_row.get("swing_protected_match_timeframe"),
        "swing_protected_match_type": source_row.get("swing_protected_match_type"),
        "swing_protected_compatible_swing_count": source_row.get(
            "swing_protected_compatible_swing_count"
        ),
        "swing_protected_stop_distance_price": _float(
            source_row.get("swing_protected_stop_distance_price")
        ),
        "tick_structural_derivation_repair_status": source_row.get(
            "tick_structural_derivation_repair_status"
        ),
        "swing_protected_requirement_repair_status": source_row.get(
            "swing_protected_requirement_repair_status"
        ),
        "swing_protected_scorer_split_status": source_row.get(
            "swing_protected_scorer_split_status"
        ),
    }
    runtime.update(event_scope)
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> list[dict[str, Any]]:
    source_path = _source_path(SCORER_SPLIT_SOURCE)
    source_sha = _sha256_file(source_path)
    runtime_rows: list[dict[str, Any]] = []
    for line_no, row in enumerate(_read_jsonl(source_path), start=1):
        if not _is_target_row(row):
            continue
        behavior = _behavior(row)
        proxy = _float(row.get("after_proxy_r"))
        stop_distance = _float(row.get("swing_protected_stop_distance_price"))
        metrics = {
            key: value
            for key, value in {
                "proxy_score": _metric(proxy, source_field="after_proxy_r"),
                "cost_adjusted_simulated_r": _metric(proxy, source_field="after_proxy_r"),
                "proxy_r_delta": _metric(_float(row.get("proxy_r_delta")), source_field="proxy_r_delta"),
                "swing_protected_stop_distance_price": _metric(
                    stop_distance,
                    source_field="swing_protected_stop_distance_price",
                ),
                "effective_n": _metric(1, source_field="swing_protected_source_repair_target_row"),
            }.items()
            if value is not None
        }
        primitive = _norm(row.get("primitive_family")) or _norm(row.get("strategy_id"))
        target_stop_order_class = _target_stop_order_class(row)
        if (
            behavior["r_evidence_class"]
            == "MAIN_ORCH24_SWING_PROTECTED_SOURCE_ACQUISITION_REQUIRED"
        ):
            target_stop_order_class = "TARGET_STOP_SOURCE_ACQUISITION_REQUIRED"
        scope = _base_scope(
            symbol=_norm(row.get("symbol")),
            side=_norm(row.get("side")),
            route_session=_candidate_session(row.get("candidate_id")),
            primitive=primitive,
            source_component=behavior["source_component"],
            target_stop_order_class=target_stop_order_class,
        )
        runtime_rows.append(
            _runtime_row(
                line_no=line_no,
                source_path=source_path,
                source_sha=source_sha,
                source_row=row,
                behavior=behavior,
                event_scope=scope,
                metrics=metrics,
            )
        )
    return runtime_rows


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(
        sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items())
    )


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: sum(1 for row in rows if not _norm(row.get(field))) for field in ANCHOR_FIELDS}


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows_by_source = Counter(Path(row["source_artifact"]).name for row in rows)
    artifacts: list[dict[str, Any]] = []
    for unit_id, name, git_blob_hash in SOURCE_ARTIFACTS:
        path = _source_path(name)
        role = "primary_runtime_rows" if name == SCORER_SPLIT_SOURCE else "supporting_swing_protected_source_repair_evidence"
        artifacts.append(
            {
                "unit_id": unit_id,
                "name": name,
                "path": _path_text(path),
                "hash": git_blob_hash,
                "hash_algorithm": "git_blob",
                "sha256": _sha256_file(path),
                "row_count": _source_row_count(path),
                "runtime_rows_read": int(runtime_rows_by_source.get(name, 0)),
                "source_role": role,
            }
        )
    return artifacts


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = _source_artifacts(rows)
    coverage = {
        "symbols": _counter(rows, "symbol"),
        "source_symbols": _counter(rows, "source_symbol"),
        "markets": _counter(rows, "market"),
        "timeframes": _counter(rows, "timeframe"),
        "sessions": _counter(rows, "route_session"),
        "route_families": _counter(rows, "route_family"),
        "primitives": _counter(rows, "primitive"),
        "sides": _counter(rows, "side"),
        "source_components": _counter(rows, "source_component"),
        "action_classes": _counter(rows, "action_class"),
        "source_roles": _counter(rows, "source_role"),
        "source_groups": _counter(rows, "source_group"),
        "system_surfaces": _counter(rows, "system_surface"),
        "entry_variants": _counter(rows, "entry_variant"),
        "target_stop_order_classes": _counter(rows, "target_stop_order_class"),
        "swing_protected_stop_statuses": _counter(rows, "swing_protected_stop_status"),
        "after_outcome_statuses": _counter(rows, "after_outcome_status"),
    }
    proxy_values = [
        float(row["after_proxy_r"])
        for row in rows
        if isinstance(row.get("after_proxy_r"), (int, float))
    ]
    downstream_log = {
        "path": _path_text(MATERIALIZED_SOURCE_LOG),
        "sha256": _sha256_file(MATERIALIZED_SOURCE_LOG),
        "row_count": _source_row_count(MATERIALIZED_SOURCE_LOG),
        "already_converted_unit_id": "UNIT_013501",
        "source_role": "downstream_shadow_measurement_input_already_converted",
    }
    return {
        "schema_version": "gtos_vnext_main_orch24_swing_protected_source_repair_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "runtime_source_rows_represented": sum(int(item["runtime_rows_read"]) for item in artifacts),
        "wave_source_rows_counted": sum(int(item["row_count"]) for item in artifacts),
        "support_rows_represented": sum(
            int(item["row_count"])
            for item in artifacts
            if item["source_role"] != "primary_runtime_rows"
        ),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "source_acquisition_required_rows": sum(
            1
            for row in rows
            if row.get("r_evidence_class")
            == "MAIN_ORCH24_SWING_PROTECTED_SOURCE_ACQUISITION_REQUIRED"
        ),
        "positive_proxy_rows": sum(1 for value in proxy_values if value > 0),
        "negative_proxy_rows": sum(1 for value in proxy_values if value < 0),
        "zero_proxy_rows": sum(1 for value in proxy_values if value == 0),
        "positive_proxy_sum": round(sum(value for value in proxy_values if value > 0), 6),
        "negative_proxy_sum": round(sum(value for value in proxy_values if value < 0), 6),
        "decision_counts": _counter(rows, "review_action"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "action_class_counts": _counter(rows, "action_class"),
        "source_component_counts": _counter(rows, "source_component"),
        "source_role_counts": _counter(rows, "source_role"),
        "source_group_counts": _counter(rows, "source_group"),
        "source_kind_counts": _counter(rows, "source_kind"),
        "system_surface_counts": _counter(rows, "system_surface"),
        "proxy_r_class_counts": _counter(rows, "proxy_r_class"),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now") is True
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted") is True
        ),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect") is True),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation") is True),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if row.get("paid_api_or_vendor_call") is True
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row.get("runtime_trading_or_live_broker_effect") is True
        ),
        "source_artifacts": artifacts,
        "downstream_materialized_source_log": downstream_log,
    }


def write_outputs(*, check: bool = False) -> int:
    rows = build_rows()
    summary = build_summary(rows)
    rows_payload = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"

    if check:
        current_rows = OUTPUT_ROWS.read_text(encoding="utf-8") if OUTPUT_ROWS.exists() else ""
        current_summary = OUTPUT_SUMMARY.read_text(encoding="utf-8") if OUTPUT_SUMMARY.exists() else ""
        if current_rows != rows_payload or current_summary != summary_payload:
            print("Generated Main Orch24 swing-protected source-repair runtime artifacts are stale.")
            return 1
        print(
            "Main Orch24 swing-protected source-repair runtime artifacts are current: "
            f"{len(rows)} rows."
        )
        return 0

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROWS.write_text(rows_payload, encoding="utf-8")
    OUTPUT_SUMMARY.write_text(summary_payload, encoding="utf-8")
    print(f"Wrote {OUTPUT_ROWS} ({len(rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify outputs are current")
    args = parser.parse_args()
    return write_outputs(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
