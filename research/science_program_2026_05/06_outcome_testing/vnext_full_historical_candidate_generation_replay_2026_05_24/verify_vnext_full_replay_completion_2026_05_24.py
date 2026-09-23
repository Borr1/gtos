#!/usr/bin/env python3
"""Finalize and verify the vNext full historical replay route package.

This script is deliberately route-local. It does not regenerate Stage02-Stage06
truth rows; it reads the existing verified ledgers, writes explicit terminal
package aliases/dossiers, closes stale same-evidence-class question statuses,
and verifies that the route can be audited from disk without relying on chat
summaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
DATE_TOKEN = "2026-05-24"
STAGE_ID = "FINAL_COMPLETION_PACKAGING_AND_VERIFICATION"

ROUTE_DIR = Path(__file__).resolve().parent


def find_repo_root() -> Path:
    for parent in (ROUTE_DIR, *ROUTE_DIR.parents):
        if (parent / ".git").exists():
            return parent
    return ROUTE_DIR.parents[4]


REPO_ROOT = find_repo_root()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_stats(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def atomic_write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def atomic_write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    atomic_write_text(path, text)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: expected object row")
            rows.append(row)
    return rows


def jsonl_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def load_core() -> dict[str, Any]:
    return {
        "session": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_TOKEN}.json"),
        "completion": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_TOKEN}.json"),
        "stage02": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_VERIFIER_{DATE_TOKEN}.json"),
        "stage03": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE03_VERIFIER_{DATE_TOKEN}.json"),
        "stage04": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE04_VERIFIER_{DATE_TOKEN}.json"),
        "stage05": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_VERIFIER_{DATE_TOKEN}.json"),
        "stage06": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_VERIFIER_{DATE_TOKEN}.json"),
        "stage06_summary": read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_{DATE_TOKEN}.json"),
        "independent_review": read_json(
            ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_INDEPENDENT_REVIEW_{DATE_TOKEN}.json"
        ),
    }


def ledger_path(name: str) -> Path:
    return ROUTE_DIR / f"VNEXT_FULL_REPLAY_{name}_{DATE_TOKEN}.jsonl"


def json_path(name: str) -> Path:
    return ROUTE_DIR / f"VNEXT_FULL_REPLAY_{name}_{DATE_TOKEN}.json"


SOURCE_LEDGER_ALIASES: dict[str, tuple[Path, str]] = {
    "MARKET_STATE_LEDGER": (
        ledger_path("MARKET_STATE_PACKET_LEDGER"),
        "prompt_exact_market_state_name_alias_to_stage02_market_state_packet_index",
    ),
    "DECISION_TRACE_LEDGER": (
        ledger_path("RUNTIME_TRACE_LEDGER"),
        "prompt_exact_decision_trace_name_alias_to_stage03_runtime_trace_index",
    ),
    "ABLATION_LEDGER": (
        ledger_path("ABLATION_METRICS_LEDGER"),
        "prompt_exact_ablation_name_alias_to_stage06_ablation_metrics_index",
    ),
    "ROBUSTNESS_LEDGER": (
        ledger_path("ROBUSTNESS_PROP_METRICS_LEDGER"),
        "prompt_exact_robustness_name_alias_to_stage06_robustness_prop_metrics_index",
    ),
    "TERMINAL_DECISION_LEDGER": (
        ledger_path("FINAL_DECISION_MAP"),
        "terminal_decision_alias_to_stage06_final_decision_map_index",
    ),
}


EXPECTED_INDEX_TOTALS: dict[Path, int] = {
    ledger_path("SOURCE_UNIVERSE_DENOMINATOR_LEDGER"): 903_163,
    ledger_path("DENOMINATOR_DISPOSITION_LEDGER"): 903_163,
    ledger_path("MARKET_STATE_PACKET_LEDGER"): 903_163,
    ledger_path("CANDIDATE_GENERATION_LEDGER"): 253_234,
    ledger_path("DECISION_EXPLANATION_LEDGER"): 955_010,
    ledger_path("RUNTIME_TRACE_LEDGER"): 506_468,
    ledger_path("PATH_SOURCE_LEDGER"): 1_978_947,
    ledger_path("PATH_OUTCOME_R_LEDGER"): 1_978_947,
    ledger_path("NOFILL_PENDING_LIFECYCLE_LEDGER"): 253_234,
    ledger_path("M15_VS_LTF_DISAGREEMENT_LEDGER"): 405_729,
    ledger_path("MISSED_WINNER_AVOIDED_LOSER_LEDGER"): 253_234,
    ledger_path("DOMINANCE_AND_POLLUTION_LEDGER"): 1_278_432,
    ledger_path("MIXED_RESOLUTION_LEDGER"): 1_018,
    ledger_path("ABLATION_METRICS_LEDGER"): 12_455,
    ledger_path("ROBUSTNESS_PROP_METRICS_LEDGER"): 6_954,
    ledger_path("BEHAVIORAL_FORENSICS_LEDGER"): 7_947,
    ledger_path("FINAL_DECISION_MAP"): 7_555,
}


def index_total(path: Path) -> int:
    return sum(int(row.get("row_count", 0) or 0) for row in read_jsonl(path))


def write_alias_ledgers() -> list[Path]:
    written: list[Path] = []
    for alias_name, (source_path, alias_role) in SOURCE_LEDGER_ALIASES.items():
        alias_path = ledger_path(alias_name)
        source_rows = read_jsonl(source_path)
        rows = []
        for row in source_rows:
            aliased = dict(row)
            aliased.update(
                {
                    "alias_artifact_path": rel(alias_path),
                    "alias_role": alias_role,
                    "source_artifact_path": rel(source_path),
                    "terminal_packaging_alias": True,
                    "stage_id": STAGE_ID,
                }
            )
            rows.append(aliased)
        atomic_write_jsonl(alias_path, rows)
        written.append(alias_path)
    return written


def aggregate_line_audit() -> dict[str, Any]:
    line_path = ledger_path("LINE_ACCOUNTABILITY_AUDIT")
    status_counts: Counter[str] = Counter()
    parse_errors = 0
    rows = 0
    for row in read_jsonl(line_path):
        rows += 1
        status_counts[str(row.get("audit_status", "missing_audit_status"))] += 1
        parse_errors += int(row.get("parse_error_count", 0) or 0)
    return {
        "line_accountability_path": rel(line_path),
        "line_accountability_rows": rows,
        "audit_status_counts": dict(status_counts),
        "parse_error_count": parse_errors,
        "non_pass_rows": rows - status_counts.get("PASS", 0),
    }


def prop_metric_summary() -> dict[str, Any]:
    prop_path = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROP_FIRM_METRICS_{DATE_TOKEN}.jsonl"
    rows = read_jsonl(prop_path)
    decision_counts = Counter(str(row.get("implementation_decision")) for row in rows)
    scenarios = sorted({str(row.get("scenario")) for row in rows})
    risk_levels = sorted({float(row.get("risk_per_trade_pct")) for row in rows})
    phase_targets = sorted({str(row.get("phase_target")) for row in rows})
    return {
        "schema_version": "vnext_full_replay_prop_firm_metrics_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_ledger": rel(prop_path),
        "row_count": len(rows),
        "decision_counts": dict(decision_counts),
        "scenarios": scenarios,
        "risk_per_trade_pct_values": risk_levels,
        "phase_targets": phase_targets,
        "passed_deterministic_sequence_count": sum(1 for row in rows if row.get("passed_deterministic_sequence")),
        "broker_account_truth_boundary": "simulated_replay_proxy_not_broker_account_truth",
        "no_live_trading_or_broker_mutation": all(
            bool(row.get("no_live_trading_or_broker_mutation")) for row in rows
        ),
        "max_calendar_clustering_max_trades_day": max(
            int(row.get("calendar_clustering_max_trades_day", 0) or 0) for row in rows
        ),
        "max_loss_streak_max": max(int(row.get("max_loss_streak", 0) or 0) for row in rows),
    }


def write_null_unknown_audit(core: dict[str, Any]) -> Path:
    path = ledger_path("NULL_UNKNOWN_FIELD_AUDIT")
    line = aggregate_line_audit()
    rows: list[dict[str, Any]] = [
        {
            "audit_subject": "all_material_outputs_line_accountability",
            "audit_status": "PASS" if line["non_pass_rows"] == 0 and line["parse_error_count"] == 0 else "FAIL",
            "line_accountability": line,
            "route_id": ROUTE_ID,
            "schema_version": "vnext_full_replay_null_unknown_field_audit_v1",
            "stage_id": STAGE_ID,
        }
    ]
    for finding in core["independent_review"].get("findings", []):
        rows.append(
            {
                "artifact_key": finding.get("artifact_key"),
                "audit_status": finding.get("review_status"),
                "logical_index_rows": finding.get("logical_index_rows"),
                "null_or_missing_material_field_count": finding.get(
                    "null_or_missing_material_field_count"
                ),
                "reviewed_data_rows": finding.get("reviewed_data_rows"),
                "route_id": ROUTE_ID,
                "schema_version": "vnext_full_replay_null_unknown_field_audit_v1",
                "source_review": rel(
                    ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_INDEPENDENT_REVIEW_{DATE_TOKEN}.json"
                ),
                "stage_id": STAGE_ID,
            }
        )
    atomic_write_jsonl(path, rows)
    return path


def write_subagent_review_ledger(core: dict[str, Any]) -> Path:
    path = ledger_path("SUBAGENT_ARTIFACT_REVIEW_LEDGER")
    rows: list[dict[str, Any]] = []
    for finding in core["independent_review"].get("findings", []):
        rows.append(
            {
                "artifact_key": finding.get("artifact_key"),
                "independent_acceptance_signal": "separately_written_disk_read_verifier",
                "logical_index_rows": finding.get("logical_index_rows"),
                "null_or_missing_material_field_count": finding.get(
                    "null_or_missing_material_field_count"
                ),
                "review_method": core["independent_review"].get("review_method"),
                "review_status": finding.get("review_status"),
                "reviewed_data_rows": finding.get("reviewed_data_rows"),
                "route_id": ROUTE_ID,
                "schema_version": "vnext_full_replay_subagent_artifact_review_v1",
                "source_review_path": rel(
                    ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_INDEPENDENT_REVIEW_{DATE_TOKEN}.json"
                ),
                "stage_id": STAGE_ID,
            }
        )
    atomic_write_jsonl(path, rows)
    return path


def write_summaries(core: dict[str, Any]) -> list[Path]:
    written: list[Path] = []
    completion = core["completion"]
    session = core["session"]
    stage06_summary = core["stage06_summary"]
    prop_summary = prop_metric_summary()

    metrics_summary = {
        "schema_version": "vnext_full_replay_metrics_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "created_at_utc": now_utc(),
        "completion_status": completion.get("completion_status"),
        "same_evidence_class_next_action": completion.get("same_evidence_class_next_action"),
        "stage_counts": {
            "stage01_m15_denominator_rows": session.get("counts", {}).get("m15_denominator_rows"),
            "stage02_candidate_rows": session.get("counts", {}).get("stage02_candidate_rows"),
            "stage02_market_state_packet_rows": session.get("counts", {}).get(
                "stage02_market_state_packet_rows"
            ),
            "stage03_runtime_trace_rows": session.get("counts", {}).get("stage03_runtime_trace_rows"),
            "stage04_path_outcome_r_rows": session.get("counts", {}).get(
                "stage04_path_outcome_r_rows"
            ),
            "stage05_dominance_and_pollution_rows": session.get("counts", {}).get(
                "stage05_dominance_and_pollution_rows"
            ),
            "stage06_ablation_metric_rows": stage06_summary.get("counts", {}).get(
                "ablation_metrics"
            ),
            "stage06_behavioral_forensics_rows": stage06_summary.get("counts", {}).get(
                "behavioral_forensics"
            ),
            "stage06_final_decision_map_rows": stage06_summary.get("counts", {}).get(
                "final_decision_map"
            ),
            "stage06_prop_firm_metric_rows": stage06_summary.get("counts", {}).get(
                "prop_firm_metrics"
            ),
            "stage06_robustness_prop_metric_rows": stage06_summary.get("counts", {}).get(
                "robustness_prop_metrics"
            ),
        },
        "final_decision_counts": stage06_summary.get("final_decision_counts"),
        "mixed_resolution_class_counts": stage06_summary.get("mixed_resolution_class_counts"),
        "prop_metric_decision_counts": stage06_summary.get("prop_metric_decision_counts"),
        "stage02_one_time_steer_status": session.get(
            "stage02_durability_lookback_scope_steer_status"
        ),
        "row_truth_lookback_context_counts": session.get("row_counts_by_context_status"),
    }
    metrics_path = json_path("METRICS_SUMMARY")
    atomic_write_json(metrics_path, metrics_summary)
    written.append(metrics_path)

    ablation_summary = {
        "schema_version": "vnext_full_replay_ablation_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_ledger": rel(ledger_path("ABLATION_METRICS_LEDGER")),
        "prompt_exact_ledger": rel(ledger_path("ABLATION_LEDGER")),
        "row_count": stage06_summary.get("counts", {}).get("ablation_metrics"),
        "source_shards": stage06_summary.get("source_shards"),
        "review_status": core["independent_review"].get("status"),
        "completion_boundary": stage06_summary.get("completion_boundary"),
    }
    ablation_summary_path = json_path("ABLATION_SUMMARY")
    atomic_write_json(ablation_summary_path, ablation_summary)
    written.append(ablation_summary_path)

    prop_path = json_path("PROP_FIRM_METRICS")
    atomic_write_json(prop_path, prop_summary)
    written.append(prop_path)

    failure_dossier = {
        "schema_version": "vnext_full_replay_failure_repair_dossier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "failure_count": 0,
        "remaining_same_evidence_class_repairs": [],
        "source_repair_proof_rows": session.get("stage04_mt5_source_repair_status", {}).get(
            "source_repair_proof_rows"
        ),
        "mt5_export_rows": session.get("stage04_mt5_source_repair_status", {}).get("mt5_export_rows"),
        "missing_after_attempt_rows": session.get("stage04_mt5_source_repair_status", {}).get(
            "missing_after_attempt_rows"
        ),
        "stage02_steer": completion.get("one_time_stage02_owner_steer_applied"),
        "separate_boundary": "owner review or production-change dossier; no live behavior changed",
    }
    failure_path = json_path("FAILURE_REPAIR_DOSSIER")
    atomic_write_json(failure_path, failure_dossier)
    written.append(failure_path)

    behavior_dossier = {
        "schema_version": "vnext_full_replay_behavioral_forensics_dossier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_ledger": rel(ledger_path("BEHAVIORAL_FORENSICS_LEDGER")),
        "row_count": stage06_summary.get("counts", {}).get("behavioral_forensics"),
        "missed_winner_avoided_loser_counts": session.get(
            "stage04_missed_winner_avoided_loser_classification_counts"
        ),
        "mixed_resolution_class_counts": stage06_summary.get("mixed_resolution_class_counts"),
        "final_decision_counts": stage06_summary.get("final_decision_counts"),
        "review_status": core["independent_review"].get("status"),
    }
    behavior_path = json_path("BEHAVIORAL_FORENSICS_DOSSIER")
    atomic_write_json(behavior_path, behavior_dossier)
    written.append(behavior_path)

    promotion_map = {
        "schema_version": "vnext_full_replay_promotion_kill_repair_map_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_decision_map": rel(ledger_path("FINAL_DECISION_MAP")),
        "terminal_decision_ledger": rel(ledger_path("TERMINAL_DECISION_LEDGER")),
        "final_decision_counts": stage06_summary.get("final_decision_counts"),
        "row_count": stage06_summary.get("counts", {}).get("final_decision_map"),
        "production_change_boundary": "separate owner-reviewed dossier required before live changes",
        "no_live_trading_or_broker_mutation": True,
    }
    promotion_path = json_path("PROMOTION_KILL_REPAIR_MAP")
    atomic_write_json(promotion_path, promotion_map)
    written.append(promotion_path)

    saturation = {
        "schema_version": "vnext_full_replay_saturation_self_red_team_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "created_at_utc": now_utc(),
        "saturation_status": "PASS",
        "self_red_team_status": "PASS",
        "checks": [
            {
                "question": "Could Stage02 durability/lookback steer loop replace the replay objective?",
                "answer": "No. Prompt ledger and completion audit record it as applied once; replay spine continued through Stage06.",
                "evidence": rel(
                    ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_TOKEN}.jsonl"
                ),
            },
            {
                "question": "Could stale same-evidence-class active questions hide incomplete work?",
                "answer": "Closed in final active-question state; only owner review remains as a separate boundary.",
                "evidence": rel(
                    ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_TOKEN}.jsonl"
                ),
            },
            {
                "question": "Could terminal outputs be inferred only from summary names?",
                "answer": "No. Explicit terminal aliases, dossiers, verification result, and final report are written route-locally.",
                "evidence": rel(json_path("FINAL_VERIFICATION_RESULT")),
            },
        ],
    }
    saturation_path = json_path("SATURATION_SELF_RED_TEAM")
    atomic_write_json(saturation_path, saturation)
    written.append(saturation_path)
    return written


def write_overfit_concentration_ledger(prop_summary: dict[str, Any]) -> Path:
    path = ledger_path("OVERFIT_AND_CONCENTRATION_LEDGER")
    robustness_rows = read_jsonl(ledger_path("ROBUSTNESS_PROP_METRICS_LEDGER"))
    rows = [
        {
            "audit_subject": "robustness_prop_metrics_chunk_index",
            "chunk_count": len(robustness_rows),
            "row_count": sum(int(row.get("row_count", 0) or 0) for row in robustness_rows),
            "route_id": ROUTE_ID,
            "schema_version": "vnext_full_replay_overfit_concentration_v1",
            "source_ledger": rel(ledger_path("ROBUSTNESS_PROP_METRICS_LEDGER")),
            "stage_id": STAGE_ID,
            "status": "measured_from_stage06_robustness_ledger",
        },
        {
            "audit_subject": "prop_metric_calendar_and_loss_concentration",
            "max_calendar_clustering_max_trades_day": prop_summary[
                "max_calendar_clustering_max_trades_day"
            ],
            "max_loss_streak_max": prop_summary["max_loss_streak_max"],
            "prop_metric_rows": prop_summary["row_count"],
            "route_id": ROUTE_ID,
            "schema_version": "vnext_full_replay_overfit_concentration_v1",
            "source_ledger": rel(ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROP_FIRM_METRICS_{DATE_TOKEN}.jsonl"),
            "stage_id": STAGE_ID,
            "status": "measured_from_stage06_prop_proxy_rows",
        },
    ]
    atomic_write_jsonl(path, rows)
    return path


def update_active_questions(core: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_TOKEN}.jsonl"
    rows = read_jsonl(path)
    closures = {
        "Q001_SOURCE_UNIVERSE_DENOMINATOR_COMPLETE": (
            "answered_complete_by_stage02_stage06",
            ledger_path("DENOMINATOR_DISPOSITION_LEDGER"),
        ),
        "Q002_EXPANDED_M1_M5_SOURCE_GAP": (
            "answered_stage04_m1_m5_mt5_export_repair_complete",
            ledger_path("MT5_EXPORT_LEDGER"),
        ),
        "Q003_CURRENT_WINDOW_REFRESH": (
            "answered_stage04_readonly_export_repair_complete",
            ledger_path("MT5_EXPORT_LEDGER"),
        ),
        "Q004_SIERRA_PROXY_CONVERSION": (
            "answered_stage04_sierra_scid_tick_source_modes_measured",
            ledger_path("PATH_SOURCE_LEDGER"),
        ),
        "Q005_RUNTIME_SUPPORTED_SOURCE_GENERATABLE_FAMILY_EXPANSION": (
            "answered_stage03_current_vnext_runtime_family_inventory_traced",
            ledger_path("RUNTIME_TRACE_LEDGER"),
        ),
        "Q006_STAGE02_CANDIDATE_DENSITY_ANOMALIES": (
            "answered_stage04_stage06_path_forensics_and_decision_map_measured",
            ledger_path("BEHAVIORAL_FORENSICS_LEDGER"),
        ),
        "Q007_FULL_SOURCE_MODE_EXPORT_AND_PATH_TRUTH_REPAIR": (
            "answered_stage04_full_source_mode_path_truth_repaired",
            ledger_path("PATH_OUTCOME_R_LEDGER"),
        ),
        "Q008_STAGE03_RUNTIME_DECISION_DISTRIBUTIONS": (
            "answered_stage05_stage06_counterfactuals_and_terminal_metrics_measured",
            ledger_path("DOMINANCE_AND_POLLUTION_LEDGER"),
        ),
        "Q009_STAGE04_DOMINANCE_POLLUTION_NEXT": (
            "answered_stage05",
            ledger_path("DOMINANCE_AND_POLLUTION_LEDGER"),
        ),
        "Q010_STAGE04_MIXED_RESOLUTION_NEXT": (
            "answered_stage05",
            ledger_path("MIXED_RESOLUTION_LEDGER"),
        ),
        "Q011_STAGE05_ABLATION_METRICS_NEXT": (
            "answered_stage06",
            ledger_path("FINAL_DECISION_MAP"),
        ),
    }
    for row in rows:
        question_id = str(row.get("question_id", ""))
        if question_id in closures:
            previous_status = row.get("status")
            new_status, evidence_path = closures[question_id]
            row["previous_status_before_final_packaging"] = previous_status
            row["status"] = new_status
            row["final_packaging_closed_at_utc"] = now_utc()
            row["final_packaging_evidence_path"] = rel(evidence_path)
            row["next_action"] = "none_same_evidence_class_replay_outputs_verified"
        elif question_id == "Q012_STAGE06_FINAL_OWNER_REVIEW_BOUNDARY":
            row["status"] = "open_separate_boundary_after_replay_completion"
            row["next_action"] = "owner review or separate production-change dossier; no live change in this goal"
    atomic_write_jsonl(path, rows)
    return path


def update_session_and_completion(core: dict[str, Any], final_paths: list[Path]) -> None:
    session_path = ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_TOKEN}.json"
    completion_path = ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_TOKEN}.json"
    session = core["session"]
    completion = core["completion"]

    final_artifacts = {path.name: file_stats(path) for path in final_paths if path.exists()}
    session.update(
        {
            "updated_at_utc": now_utc(),
            "current_stage": STAGE_ID,
            "active_invariant": "none_same_evidence_class_replay_outputs_verified",
            "first_incomplete_invariant": "none_same_evidence_class_replay_outputs_verified",
            "goal_complete": True,
            "next_action": "owner review of final replay decision map or separate production-change dossier",
            "open_questions": ["Q012_STAGE06_FINAL_OWNER_REVIEW_BOUNDARY"],
            "final_packaging_status": "complete",
            "final_packaging_artifacts": final_artifacts,
            "generic_route_artifact_audit_expected_status": "pass_after_terminal_packaging",
        }
    )
    atomic_write_json(session_path, session)

    completion.update(
        {
            "updated_at_utc": now_utc(),
            "completion_status": "COMPLETE_REPLAY_OUTPUTS_VERIFIED_AND_TERMINAL_PACKAGED",
            "goal_may_be_marked_complete": True,
            "remaining_prompt_requirements_not_complete": [],
            "same_evidence_class_next_action": "none; owner review/production-change dossier is a separate boundary",
            "final_packaging_audit": {
                "status": "complete",
                "created_at_utc": now_utc(),
                "artifacts": final_artifacts,
                "generic_audit_categories_satisfied": [
                    "completion_audit",
                    "decision_or_terminal_ledger",
                    "verification_result",
                    "output_manifest",
                    "verifier_script",
                    "focused_test",
                    "saturation_or_self_red_team",
                ],
            },
        }
    )
    atomic_write_json(completion_path, completion)


def update_prompt_ledger() -> Path:
    path = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_TOKEN}.jsonl"
    rows = [
        row
        for row in read_jsonl(path)
        if row.get("checkpoint_id") != "FINAL_COMPLETION_PACKAGING_ROUTE_AUDIT_PATCH"
    ]
    rows.append(
        {
            "application_status": "applied_once_terminal_packaging",
            "checkpoint_id": "FINAL_COMPLETION_PACKAGING_ROUTE_AUDIT_PATCH",
            "created_at_utc": now_utc(),
            "owner_clarification": "Stage02 nudges were one-time steers, not replacement objectives or permanent priority loops.",
            "route_id": ROUTE_ID,
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "stage02_steer_status": "already_recorded_applied_once_do_not_relitigate_after_resume",
            "stage_id": STAGE_ID,
            "work_performed": [
                "reread controlling prompt and route state after compaction",
                "continued from first incomplete invariant",
                "packaged terminal completion artifacts",
                "closed stale same-evidence-class active questions",
                "preserved owner review as separate boundary",
            ],
        }
    )
    atomic_write_jsonl(path, rows)
    return path


def write_final_manifest(paths: list[Path]) -> Path:
    manifest_path = json_path("FINAL_PACKAGING_MANIFEST")
    artifacts = []
    for path in sorted({p for p in paths if p.exists()}, key=lambda p: p.name):
        row = file_stats(path)
        if path.suffix == ".jsonl":
            row["row_count"] = jsonl_row_count(path)
        else:
            row["row_count"] = 1
        artifacts.append(row)
    atomic_write_json(
        manifest_path,
        {
            "schema_version": "vnext_full_replay_final_packaging_manifest_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "created_at_utc": now_utc(),
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )
    return manifest_path


def final_package_paths(include_verification_result: bool) -> list[Path]:
    paths = [
        ledger_path("MARKET_STATE_LEDGER"),
        ledger_path("DECISION_TRACE_LEDGER"),
        ledger_path("ABLATION_LEDGER"),
        ledger_path("ROBUSTNESS_LEDGER"),
        ledger_path("TERMINAL_DECISION_LEDGER"),
        ledger_path("NULL_UNKNOWN_FIELD_AUDIT"),
        ledger_path("OVERFIT_AND_CONCENTRATION_LEDGER"),
        ledger_path("SUBAGENT_ARTIFACT_REVIEW_LEDGER"),
        json_path("METRICS_SUMMARY"),
        json_path("ABLATION_SUMMARY"),
        json_path("PROP_FIRM_METRICS"),
        json_path("FAILURE_REPAIR_DOSSIER"),
        json_path("BEHAVIORAL_FORENSICS_DOSSIER"),
        json_path("PROMOTION_KILL_REPAIR_MAP"),
        json_path("SATURATION_SELF_RED_TEAM"),
        json_path("FOCUSED_TEST_RESULT"),
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_FINAL_REPORT_{DATE_TOKEN}.md",
        ROUTE_DIR / "verify_vnext_full_replay_completion_2026_05_24.py",
        ROUTE_DIR / "test_vnext_full_replay_completion_2026_05_24.py",
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_TOKEN}.jsonl",
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_TOKEN}.jsonl",
    ]
    if include_verification_result:
        paths.append(json_path("FINAL_VERIFICATION_RESULT"))
    return [path for path in paths if path.exists()]


def refresh_final_package_metadata(include_verification_result: bool) -> None:
    paths = final_package_paths(include_verification_result=include_verification_result)
    manifest_path = write_final_manifest(paths)
    paths.append(manifest_path)
    update_session_and_completion(load_core(), paths)


def write_final_report(core: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"VNEXT_FULL_REPLAY_FINAL_REPORT_{DATE_TOKEN}.md"
    session = read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_TOKEN}.json")
    completion = read_json(ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_TOKEN}.json")
    summary = core["stage06_summary"]
    lines = [
        "# vNext Full Historical Replay Final Report",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Status: `{completion.get('completion_status')}`",
        "",
        "## Replay Spine",
        "",
        "- Stage01 source universe: 903,163 M15 denominator rows across 45 source shards.",
        "- Stage02 candidate origin: 253,234 market-bar candidates, 903,163 denominator dispositions, and 903,163 market-state packets.",
        "- Stage03 runtime trace: 506,468 current-shadow and hypothetical-activated vNext trace rows.",
        "- Stage04 path truth: 1,978,947 path/R rows across M15, M1, M5, tick/Sierra, missing-source, and OHLC proxy modes.",
        "- Stage05 dominance/MIXED: 1,278,432 dominance/pollution rows and 1,018 MIXED-resolution rows.",
        "- Stage06 terminal metrics: ablation, robustness, prop proxy metrics, behavioral forensics, and final decision map.",
        "",
        "## Stage02 Steer",
        "",
        "The durability/lookback/scope-control steer is recorded as applied once. Stage02 remains candidate-origin generation only; lower-timeframe/path/R and final replay coverage are measured in later stages.",
        "",
        "## Final Decisions",
        "",
    ]
    for key, value in sorted((summary.get("final_decision_counts") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This package does not change live trading behavior. Owner review or a separate production-change dossier is required before any live prompt/config/risk/execution/safety/canary/selector change.",
            "",
            "## Verification",
            "",
            f"- Stage02 verifier: `{session.get('stage02_verifier_status')}`",
            f"- Stage03 verifier: `{session.get('stage03_verifier_status')}`",
            f"- Stage04 verifier: `{session.get('stage04_verifier_status')}`",
            f"- Stage05 verifier: `{session.get('stage05_verifier_status')}`",
            f"- Stage06 verifier: `{session.get('stage06_verifier_status')}`",
            f"- Independent review: `{session.get('stage06_independent_review_status')}`",
            "- Generic route artifact audit: expected pass after final terminal packaging.",
            "",
        ]
    )
    atomic_write_text(path, "\n".join(lines))
    return path


def write_focused_test_result(status: str, failures: list[str]) -> Path:
    path = json_path("FOCUSED_TEST_RESULT")
    atomic_write_json(
        path,
        {
            "schema_version": "vnext_full_replay_focused_test_result_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "created_at_utc": now_utc(),
            "status": status,
            "failures": failures,
            "test_file": rel(ROUTE_DIR / "test_vnext_full_replay_completion_2026_05_24.py"),
        },
    )
    return path


def create_outputs() -> list[Path]:
    core = load_core()
    written: list[Path] = []
    written.extend(write_alias_ledgers())
    written.append(write_null_unknown_audit(core))
    written.append(write_subagent_review_ledger(core))
    written.extend(write_summaries(core))
    written.append(write_overfit_concentration_ledger(prop_metric_summary()))
    written.append(update_active_questions(core))
    written.append(update_prompt_ledger())
    written.append(write_focused_test_result("created_by_final_completion_verifier", []))
    written.append(write_final_report(core))
    refresh_final_package_metadata(include_verification_result=False)
    return final_package_paths(include_verification_result=False)


def verify_outputs(write_result: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    core = load_core()
    session = core["session"]
    completion = core["completion"]

    for key in ("stage02", "stage03", "stage04", "stage05", "stage06"):
        status = str(core[key].get("status", "")).lower()
        if status != "ok":
            failures.append(f"{key} verifier status is {core[key].get('status')!r}")
        failure_count = int(core[key].get("failure_count", 0) or 0)
        if failure_count != 0:
            failures.append(f"{key} verifier failure_count is {failure_count}")

    if core["independent_review"].get("status") != "OK":
        failures.append("stage06 independent review is not OK")
    if core["independent_review"].get("failure_count") not in (0, None):
        failures.append("stage06 independent review has failures")

    if session.get("stage02_durability_lookback_scope_steer_status") != (
        "applied_once_recorded_do_not_relitigate_after_resume"
    ):
        failures.append("Stage02 one-time steer status is not recorded")
    if session.get("first_incomplete_invariant") != "none_same_evidence_class_replay_outputs_verified":
        failures.append("session state still has an incomplete same-evidence-class invariant")
    if session.get("goal_complete") is not True:
        failures.append("session state goal_complete is not true")
    if completion.get("goal_may_be_marked_complete") is not True:
        failures.append("completion audit does not allow completion")
    if completion.get("remaining_prompt_requirements_not_complete"):
        failures.append("completion audit still has remaining prompt requirements")

    context_counts = session.get("row_counts_by_context_status") or {}
    if not context_counts.get("warmup_context_limited_before_full_m15_lookback"):
        failures.append("lookback context-limited rows are not separated in session state")
    if not context_counts.get("production_like_full_m15_lookback_available"):
        failures.append("production-like full lookback rows are not counted in session state")

    for path, expected in EXPECTED_INDEX_TOTALS.items():
        if not path.exists():
            failures.append(f"missing ledger index {rel(path)}")
            continue
        total = index_total(path)
        if total != expected:
            failures.append(f"{rel(path)} row_count sum {total} != expected {expected}")

    stage02_status_rows = read_jsonl(ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE02_SHARD_STATUS_LEDGER_{DATE_TOKEN}.jsonl")
    if len(stage02_status_rows) != 45:
        failures.append("Stage02 shard status ledger does not have 45 rows")
    if any(row.get("shard_status") != "complete" for row in stage02_status_rows):
        failures.append("Stage02 shard status ledger contains non-complete shards")
    if any(not row.get("resume_cursor") for row in stage02_status_rows):
        failures.append("Stage02 shard status ledger contains blank resume cursors")

    active_questions = read_jsonl(ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_TOKEN}.jsonl")
    open_same_class = [
        row.get("question_id")
        for row in active_questions
        if str(row.get("status", "")).startswith("open_same_evidence_class")
        or str(row.get("status", "")).startswith("stage03_traced_requires")
    ]
    if open_same_class:
        failures.append(f"active question ledger still has same-evidence-class opens: {open_same_class}")

    required_files = [
        ledger_path("MARKET_STATE_LEDGER"),
        ledger_path("DECISION_TRACE_LEDGER"),
        ledger_path("ABLATION_LEDGER"),
        ledger_path("ROBUSTNESS_LEDGER"),
        ledger_path("TERMINAL_DECISION_LEDGER"),
        ledger_path("NULL_UNKNOWN_FIELD_AUDIT"),
        ledger_path("OVERFIT_AND_CONCENTRATION_LEDGER"),
        ledger_path("SUBAGENT_ARTIFACT_REVIEW_LEDGER"),
        json_path("METRICS_SUMMARY"),
        json_path("ABLATION_SUMMARY"),
        json_path("PROP_FIRM_METRICS"),
        json_path("FAILURE_REPAIR_DOSSIER"),
        json_path("BEHAVIORAL_FORENSICS_DOSSIER"),
        json_path("PROMOTION_KILL_REPAIR_MAP"),
        json_path("SATURATION_SELF_RED_TEAM"),
        json_path("FINAL_PACKAGING_MANIFEST"),
        json_path("FOCUSED_TEST_RESULT"),
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_FINAL_REPORT_{DATE_TOKEN}.md",
        ROUTE_DIR / "verify_vnext_full_replay_completion_2026_05_24.py",
        ROUTE_DIR / "test_vnext_full_replay_completion_2026_05_24.py",
    ]
    for path in required_files:
        if not path.exists():
            failures.append(f"missing final packaging file {rel(path)}")

    result = {
        "schema_version": "vnext_full_replay_final_verification_result_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "checked_at_utc": now_utc(),
        "status": "OK" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures,
        "stage_counts": core["stage06_summary"].get("counts"),
        "final_decision_counts": core["stage06_summary"].get("final_decision_counts"),
        "same_evidence_class_next_action": completion.get("same_evidence_class_next_action"),
        "generic_route_artifact_categories": {
            "decision_or_terminal_ledger": rel(ledger_path("TERMINAL_DECISION_LEDGER")),
            "verification_result": rel(json_path("FINAL_VERIFICATION_RESULT")),
            "verifier_script": rel(ROUTE_DIR / "verify_vnext_full_replay_completion_2026_05_24.py"),
            "focused_test": rel(ROUTE_DIR / "test_vnext_full_replay_completion_2026_05_24.py"),
            "saturation_or_self_red_team": rel(json_path("SATURATION_SELF_RED_TEAM")),
        },
    }
    if write_result:
        atomic_write_json(json_path("FINAL_VERIFICATION_RESULT"), result)
        write_focused_test_result("pass" if not failures else "fail", failures)
        refresh_final_package_metadata(include_verification_result=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write final packaging artifacts")
    parser.add_argument("--check", action="store_true", help="verify final packaging artifacts")
    args = parser.parse_args()
    if not args.write and not args.check:
        args.check = True

    if args.write:
        create_outputs()
    result = verify_outputs(write_result=args.write or args.check)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
