from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_DIR = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)
BATCH_LEDGER_PATH = BUILDER_DIR / "GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"
ROWS_PATH = BUILDER_DIR / "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
SUMMARY_PATH = BUILDER_DIR / "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
WAVE_ID = "WAVE_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME"

G0_DIR = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit"
)
G12_DIR = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_scid_ready8_numerical_screen_audit"
)
R11_DIR = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "ready8_r11_trade_geometry_source_capture_repair_packet_after_r10_g12_audit"
)

G0_SYNTHESIS_PATH = G0_DIR / "G0_SCID_READY8_LEARNING_SYNTHESIS_SYNTHESIS_2026-05-13.md"
G0_DECISION_PATH = G0_DIR / "G0_SCID_READY8_LEARNING_SYNTHESIS_DECISION_LEDGER_2026-05-13.json"
G0_ROUTE_RANKING_PATH = G0_DIR / "G0_SCID_READY8_LEARNING_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-13.json"
G12_DECISION_PATH = G12_DIR / "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_DECISION_LEDGER_2026-05-13.json"
R11_DECISION_PATH = R11_DIR / "R11_DECISION_LEDGER_2026-05-16.json"
R11_METRIC_SUMMARY_PATH = R11_DIR / "R11_METRIC_SUMMARY_2026-05-16.json"
R11_ROW_UNIVERSE_PATH = R11_DIR / "R11_ROW_UNIVERSE_RECONCILIATION_2026-05-16.json"
G12_R11_DECISION_PATH = R11_DIR / "G12_R11_DECISION_LEDGER_2026-05-16.json"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_batch_wave() -> dict[str, Any]:
    try:
        lines = BATCH_LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return {}
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("wave_id") == WAVE_ID:
            return row
    return {}


def _count_nonempty_lines(path: Path) -> int | None:
    try:
        if path.suffix.lower() == ".json":
            return 1 if path.stat().st_size else 0
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _source_artifacts_from_wave(wave: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    generated_paths = {
        _rel(ROWS_PATH),
        _rel(SUMMARY_PATH),
        "scripts/build_gtos_vnext_ready8_failure_control_residue_runtime_rows.py",
    }
    for item in wave.get("unit_dispositions") or []:
        if not isinstance(item, dict):
            continue
        path_text = str(item.get("source_artifact_path") or "")
        if not path_text:
            continue
        if path_text.replace("\\", "/") in generated_paths:
            continue
        path = REPO_ROOT / path_text
        row_count = item.get("row_count")
        if row_count in (None, "") and path.exists():
            row_count = _count_nonempty_lines(path)
        artifacts.append(
            {
                "unit_id": item.get("unit_id"),
                "path": path_text,
                "hash": item.get("source_artifact_hash") or (_sha256(path) if path.exists() else ""),
                "hash_algorithm": item.get("source_artifact_hash_algorithm") or "git_blob",
                "row_count": row_count,
            }
        )
    return artifacts


def _metric_coverage(metric_summary: dict[str, Any]) -> dict[str, dict[str, int]]:
    split = metric_summary.get("symbol_session_horizon_card_family_split_summary")
    symbols: Counter[str] = Counter()
    cards: Counter[str] = Counter()
    partitions: Counter[str] = Counter()
    target_families: Counter[str] = Counter()
    horizons: Counter[str] = Counter()
    if isinstance(split, dict):
        for key in split:
            parts = str(key).split("|")
            if len(parts) < 5:
                continue
            symbol, card, partition, family, horizon = parts[:5]
            if symbol:
                symbols[symbol] += 1
            if card:
                cards[card] += 1
            if partition:
                partitions[partition] += 1
            if family:
                target_families[family] += 1
            if horizon:
                horizons[horizon.lstrip("h")] += 1
    return {
        "symbols": dict(sorted(symbols.items())),
        "source_symbols": dict(sorted(symbols.items())),
        "markets": dict(sorted(symbols.items())),
        "timeframes": {"M15": sum(horizons.values())} if horizons else {"M15": 0},
        "sessions": {},
        "sides": {},
        "cards": dict(sorted(cards.items())),
        "partitions": dict(sorted(partitions.items())),
        "target_families": dict(sorted(target_families.items())),
        "horizons_m15_bars": dict(sorted(horizons.items())),
    }


def _base_row(
    *,
    row_id: str,
    source_component: str,
    action_class: str,
    implementation_action: str,
    runtime_effect_now: str,
    source_path: Path,
    r_evidence_class: str,
    reason: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "gtos_vnext_ready8_failure_control_residue_runtime_row_v1",
        "ready8_failure_control_residue_runtime_row_id": row_id,
        "source_name": "gtos_vnext_ready8_failure_control_residue_wave",
        "source_component": source_component,
        "evidence_family": "gtos_vnext_ready8_failure_control_residue",
        "source_group": "ready8_failure_control_residue",
        "source_role": "ready8_control_repair_runtime_guard",
        "system_surface": "ready8_control_source_geometry_runtime",
        "action_class": action_class,
        "implementation_action": implementation_action,
        "r_evidence_class": r_evidence_class,
        "runtime_effect_now": runtime_effect_now,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "config_enabled": True,
        "source_path": _rel(source_path),
        "source_artifact": _rel(source_path),
        "source_artifact_sha256": _sha256(source_path) if source_path.exists() else "",
        "orderflow_runtime_validated": True,
        "market_timeframe": "M15",
        "timeframe": "M15",
        "event_scope": {
            "source_component": source_component,
            "market_timeframe": "M15",
        },
        "reason": reason,
    }
    if "avoid" in action_class.casefold() or "filter" in action_class.casefold():
        payload["source_complete"] = True
    if extra:
        base_scope = dict(payload["event_scope"])
        for key, value in extra.items():
            if key != "event_scope":
                payload[key] = value
        if isinstance(extra.get("event_scope"), dict):
            payload["event_scope"] = {**base_scope, **extra["event_scope"]}
    return payload


def build_payloads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    wave = _read_batch_wave()
    source_artifacts = _source_artifacts_from_wave(wave)
    known_source_rows = [
        int(item["row_count"])
        for item in source_artifacts
        if item.get("row_count") not in (None, "")
    ]
    unknown_source_row_count = len(source_artifacts) - len(known_source_rows)
    g0_decision = _read_json(G0_DECISION_PATH)
    g0_route = _read_json(G0_ROUTE_RANKING_PATH)
    g12_decision = _read_json(G12_DECISION_PATH)
    r11_decision = _read_json(R11_DECISION_PATH)
    r11_metrics = _read_json(R11_METRIC_SUMMARY_PATH)
    r11_universe = _read_json(R11_ROW_UNIVERSE_PATH)
    g12_r11_decision = _read_json(G12_R11_DECISION_PATH)

    g12_counts = g12_decision.get("exact_reconciliation") or {}
    r11_counts = r11_decision.get("summary_counts") or {}
    g12_r11_counts = g12_r11_decision.get("summary_counts") or {}

    rows = [
        _base_row(
            row_id="READY8-FC-CONTROL-001",
            source_component="ready8_control_only_quarantine",
            action_class="avoid_filter_control_only_ready8_evidence",
            implementation_action="QUARANTINE_READY8_NUMERICAL_SCREEN_CONTROL_ONLY",
            runtime_effect_now="ready8_control_only_context_guard",
            source_path=G12_DECISION_PATH,
            r_evidence_class="READY8_CONTROL_EVIDENCE_ONLY_NO_PROMOTION",
            reason="accepted_ready8_screen_is_control_evidence_only_not_strategy_edge",
            extra={
                "row_count": int(g12_counts.get("target_result_rows") or 0),
                "source_rows_represented": int(g12_counts.get("target_result_rows") or 0),
                "ready8_source_candidates": g12_counts.get("source_candidates"),
                "ready8_candidate_card_rows": g12_counts.get("rowset_rows"),
                "ready8_target_result_rows": g12_counts.get("target_result_rows"),
            },
        ),
        _base_row(
            row_id="READY8-FC-CARD-RANK-001",
            source_component="ready8_card_rank_redundancy_kill",
            action_class="avoid_filter_ready8_card_rank_redundancy",
            implementation_action="KILL_CURRENT_PACKET_CARD_RANKING_SHARED_DENOMINATOR",
            runtime_effect_now="ready8_card_rank_runtime_veto",
            source_path=G0_SYNTHESIS_PATH,
            r_evidence_class="READY8_CARD_RANK_SHARED_DENOMINATOR_REDUNDANCY_KILL",
            reason="current_packet_card_level_movement_ranking_killed_by_identical_candidate_denominator",
            extra={
                "row_count": 8,
                "source_rows_represented": int(g12_counts.get("rowset_rows") or 0),
                "ready8_cards": g12_counts.get("ready_cards"),
                "ready8_horizons": g12_counts.get("horizons"),
                "ready8_target_families": g12_counts.get("target_families"),
            },
        ),
        _base_row(
            row_id="READY8-FC-SOURCE-001",
            source_component="ready8_source_control_repair_requirement",
            action_class="source_repair_required_ready8_discriminative_use",
            implementation_action="READY_DEFAULT_OFF_SOURCE_REPAIR",
            runtime_effect_now="ready8_source_control_repair_guard",
            source_path=G0_ROUTE_RANKING_PATH,
            r_evidence_class="READY8_DISCRIMINATIVE_SOURCE_CONTROL_REPAIR_REQUIRED",
            reason="discriminative_ready8_use_requires_card_specific_predicates_descriptors_denominators_and_fail_closed_policy",
            extra={
                "row_count": 1,
                "required_ready8_repairs": [
                    "card_specific_predicates",
                    "descriptor_contrast_and_overlap_policy",
                    "denominator_rules",
                    "fail_closed_policy",
                    "duplicate_concentration_controls",
                    "sealed_stress_partition_preregistration",
                ],
            },
        ),
        _base_row(
            row_id="READY8-FC-DENOM-001",
            source_component="ready8_denominator_overlap_requirement",
            action_class="source_repair_required_ready8_denominator_overlap",
            implementation_action="READY_DEFAULT_OFF_SOURCE_REPAIR",
            runtime_effect_now="ready8_denominator_overlap_guard",
            source_path=G0_DECISION_PATH,
            r_evidence_class="READY8_DENOMINATOR_AND_OVERLAP_CONTROL_REQUIRED",
            reason="accepted_redundancy_finding_preserves_repair_not_card_rank_promotion",
            extra={"row_count": 1},
        ),
        _base_row(
            row_id="READY8-FC-GEOM-001",
            source_component="ready8_exact_geometry_source_requirement",
            action_class="source_repair_required_ready8_exact_r_geometry",
            implementation_action="BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
            runtime_effect_now="ready8_exact_geometry_source_guard",
            source_path=R11_DECISION_PATH,
            r_evidence_class="READY8_NO_EXACT_R_OR_TARGET_STOP_SOURCE_BOUND_GEOMETRY",
            reason="r11_and_g12_found_zero_exact_r_rows_and_zero_target_stop_hit_miss_rows",
            extra={
                "row_count": int(r11_counts.get("row_universe") or 0),
                "source_rows_represented": int(r11_counts.get("row_universe") or 0),
                "proxy_r_class": "NO_EXACT_R_SOURCE_BOUND",
                "target_stop_order_class": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
                "exact_r_expectancy_rows_computed": r11_counts.get(
                    "exact_r_expectancy_rows_computed"
                ),
                "target_stop_hit_miss_rows_computed": r11_counts.get(
                    "target_stop_hit_miss_rows_computed"
                ),
                "event_scope": {
                    "proxy_r_class": "NO_EXACT_R_SOURCE_BOUND",
                    "target_stop_order_class": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
                },
            },
        ),
        _base_row(
            row_id="READY8-FC-WEAK-OVERLAP-001",
            source_component="ready8_weak_overlap_shadow_only",
            action_class="source_repair_context_ready8_weak_overlap",
            implementation_action="MERGE_AS_CONTEXT_STRESS_GUARD_INPUT",
            runtime_effect_now="ready8_weak_overlap_shadow_context_only",
            source_path=R11_METRIC_SUMMARY_PATH,
            r_evidence_class="READY8_WEAK_SYMBOL_TIME_OVERLAP_SHADOW_ONLY",
            reason="weak_symbol_time_overlaps_preserved_but_not_exact_source_bound_r_geometry",
            extra={
                "row_count": int(r11_counts.get("weak_shadow_symbol_time_matched_rows") or 0),
                "weak_shadow_symbol_time_matched_rows": r11_counts.get(
                    "weak_shadow_symbol_time_matched_rows"
                ),
                "weak_shadow_symbol_time_match_note": r11_metrics.get(
                    "weak_shadow_symbol_time_match_note"
                ),
            },
        ),
        _base_row(
            row_id="READY8-FC-FAILCLOSED-001",
            source_component="ready8_fail_closed_source_policy",
            action_class="avoid_filter_ready8_fail_closed_until_source_bound",
            implementation_action="FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY",
            runtime_effect_now="ready8_fail_closed_source_policy_guard",
            source_path=R11_ROW_UNIVERSE_PATH,
            r_evidence_class="READY8_CAPTURE_REQUIREMENT_FAIL_CLOSED_SOURCE_POLICY",
            reason="ready8_capture_requirements_need_source_bound_geometry_before_runtime_use",
            extra={
                "row_count": int(r11_universe.get("r10_g12_geometry_rows_recomputed") or 0),
                "source_rows_represented": int(
                    r11_universe.get("r10_g12_geometry_rows_recomputed") or 0
                ),
                "source_root_count": r11_universe.get("source_root_count"),
                "expanded_source_root_count": r11_universe.get("expanded_source_root_count"),
            },
        ),
        _base_row(
            row_id="READY8-FC-PROMOTION-001",
            source_component="ready8_promotion_validation_block",
            action_class="avoid_filter_ready8_no_promotion_no_live_use",
            implementation_action="BLOCK_READY8_PROMOTION_VALIDATION_LIVE_USE",
            runtime_effect_now="ready8_promotion_validation_block",
            source_path=G12_R11_DECISION_PATH,
            r_evidence_class="READY8_R11_G12_NO_PROMOTION_NO_LIVE_USE",
            reason="g12_r11_accepts_packet_as_audited_control_only_with_no_promotion_or_live_use",
            extra={
                "row_count": int(g12_r11_counts.get("row_universe") or 0),
                "source_rows_represented": int(g12_r11_counts.get("row_universe") or 0),
                "g12_r11_terminal_decision": g12_r11_decision.get("terminal_decision"),
            },
        ),
    ]

    coverage = _metric_coverage(r11_metrics)
    decision_counts = Counter()
    source_component_counts = Counter()
    r_class_counts = Counter()
    blank_anchor_counts = Counter()
    for row in rows:
        action_class = str(row.get("action_class") or "").casefold()
        implementation = str(row.get("implementation_action") or "").upper()
        if "avoid" in action_class or "filter" in action_class:
            decision_counts["AVOID"] += 1
        elif (
            "READY_DEFAULT_OFF_SOURCE_REPAIR" in implementation
            or "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R" in implementation
            or "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT" in implementation
        ):
            decision_counts["MIXED"] += 1
        else:
            decision_counts["MIXED"] += 1
        source_component_counts[str(row["source_component"])] += 1
        r_class_counts[str(row["r_evidence_class"])] += 1
        for anchor in (
            "symbol",
            "source_symbol",
            "market",
            "route_session",
            "side",
            "framework",
            "route_family",
            "entry_variant",
            "primitive",
        ):
            if not row.get(anchor):
                blank_anchor_counts[anchor] += 1

    summary = {
        "schema_version": "gtos_vnext_ready8_failure_control_residue_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "rows_path": _rel(ROWS_PATH),
        "summary_path": _rel(SUMMARY_PATH),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(known_source_rows),
        "wave_source_rows_counted": sum(known_source_rows),
        "wave_source_artifact_count": len(source_artifacts),
        "selected_open_unit_count": len(source_artifacts),
        "row_count_unknown_unit_count": unknown_source_row_count,
        "source_artifacts": source_artifacts,
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "r_evidence_class_counts": dict(sorted(r_class_counts.items())),
        "coverage_counts": coverage,
        "blank_anchor_counts": dict(sorted(blank_anchor_counts.items())),
        "accepted_screen_counts": {
            "source_candidates": g12_counts.get("source_candidates"),
            "ready_cards": g12_counts.get("ready_cards"),
            "candidate_card_rows": g12_counts.get("rowset_rows"),
            "target_result_rows": g12_counts.get("target_result_rows"),
            "horizons": g12_counts.get("horizons"),
            "target_families": g12_counts.get("target_families"),
        },
        "r11_counts": r11_counts,
        "g12_r11_counts": g12_r11_counts,
        "rank1_selected": g0_route.get("rank1_selected"),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if row.get("paid_api_or_vendor_call")
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row.get("runtime_trading_or_live_broker_effect")
        ),
        "expected_runtime_effect": (
            "READY8 control-only/card-rank evidence becomes a runtime guard, "
            "source-control repair requirements remain MIXED default-off context, "
            "and absent exact R/target-stop geometry requires source-bound "
            "geometry before READY8 can drive execution-adjacent behavior."
        ),
    }
    return rows, summary


def _write_or_check_json(path: Path, payload: dict[str, Any], *, check: bool) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            raise SystemExit(f"{path} is not up to date")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_or_check_jsonl(path: Path, rows: list[dict[str, Any]], *, check: bool) -> None:
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            raise SystemExit(f"{path} is not up to date")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, summary = build_payloads()
    _write_or_check_jsonl(ROWS_PATH, rows, check=args.check)
    _write_or_check_json(SUMMARY_PATH, summary, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
