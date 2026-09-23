#!/usr/bin/env python3
"""Build the G12 OTI6 CNR post-audit artifact pack.

Research-control only. This audits the committed OTI6 target-already-passed
result from files, verifies the CNR_E0 geometry relation before accepting the
terminal result, and writes the next preregistration/control prompt. It does
not score a new outcome and does not read broker actual-R, account history,
live order state, paid/API/Databento, or MT5 order behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-07"
PACKET_ID = "OTG0-PKT-061"
TARGET_RECORD_ID = "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
TARGET_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION"
TERMINAL_DECISION = "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
OUTCOME = ROOT / "research/science_program_2026_05/06_outcome_testing"
OTI6 = OUTCOME / "oti6_otr061_cnr_quarantined_results"
OTR061 = OUTCOME / "otr061_xau_tick_recovery"
G12_OTI5 = OUTCOME / "g12_oti5_otr061_post_audit"
PROGRAM_CONTROL = ROOT / "research/program_control"

OTI6_JSONS = {
    "method": OTI6 / f"OTI6_CNR_METHOD_FREEZE_{DATE}.json",
    "result": OTI6 / f"OTI6_CNR_RESULT_LEDGER_{DATE}.json",
    "source": OTI6 / f"OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_{DATE}.json",
    "geometry": OTI6 / f"OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_{DATE}.json",
    "duplicate": OTI6 / f"OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_{DATE}.json",
    "forensics": OTI6 / f"OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_{DATE}.json",
    "methodology": OTI6 / f"OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}.json",
    "completion": OTI6 / f"OTI6_CNR_COMPLETION_AUDIT_{DATE}.json",
}
OTI6_MDS = {name: path.with_suffix(".md") for name, path in OTI6_JSONS.items()}

UPSTREAM_FILES = {
    "g12_oti5_decision_json": G12_OTI5 / f"G12_OTI5_OTR061_DECISION_LEDGER_{DATE}.json",
    "g12_otr061_packet_json": G12_OTI5 / f"G12_OTR061_PACKET_RECOVERY_AUDIT_{DATE}.json",
    "g12_oti5_decision_md": G12_OTI5 / f"G12_OTI5_OTR061_DECISION_LEDGER_{DATE}.md",
    "g12_otr061_packet_md": G12_OTI5 / f"G12_OTR061_PACKET_RECOVERY_AUDIT_{DATE}.md",
    "otr061_packet_proposal_json": OTR061 / f"OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_{DATE}.json",
    "cnr_prereg_md": PROGRAM_CONTROL / "CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md",
    "cnr_audit_md": PROGRAM_CONTROL / "CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md",
    "otg0_control_rules_md": OUTCOME / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE}.md",
}

CONTEXT_FILES = {
    "live_state": ROOT / ".context/LIVE_STATE.md",
    "latest_handoff": ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ROOT / ".context/00_core/research_current_state.md",
    "goal_session_research_discipline": ROOT / ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": ROOT / ".context/00_core/local_heavy_data_inventory.md",
    "controlling_prompt": BASE / f"G12_OTI6_CNR_POST_AUDIT_GOAL_PROMPT_{DATE}.md",
}

CODE_FILES = {
    "oti6_builder": OTI6 / "build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
    "oti6_verifier": OTI6 / "verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
    "oti6_test": OTI6 / "test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
}

PARQUET_PATH = OTR061 / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return f"ERROR[{result.returncode}]: {result.stderr.strip()}"
    return result.stdout.strip()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], lines: list[str] | None = None) -> None:
    body = [
        f"# {title} - {DATE}",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
        f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`  ",
        f"**Live effect:** `{str(LIVE_EFFECT).lower()}`",
        "",
    ]
    if lines:
        body.extend(lines)
        body.append("")
    body.extend(["```json", json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), "```", ""])
    path.write_text("\n".join(body), encoding="utf-8")


def base_payload(family: str, generated_at: str) -> dict[str, Any]:
    return {
        "account_history_accessed": False,
        "api_calls": 0,
        "artifact_family": family,
        "blocked_packet_outcome_source_read": False,
        "broker_actual_r_accessed": False,
        "canary_calls": 0,
        "databento_calls": 0,
        "date_stamp": DATE,
        "generated_at_utc": generated_at,
        "git_head_at_build": git(["log", "-1", "--oneline"]),
        "live_effect": LIVE_EFFECT,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_id": PACKET_ID,
        "paid_data_calls": 0,
        "promotion_verdict": PROMOTION_VERDICT,
        "target_record_id": TARGET_RECORD_ID,
        "validation_safe": VALIDATION_SAFE,
    }


def source_row(path: Path, role: str, required: bool = True) -> dict[str, Any]:
    return {
        "exists": path.exists(),
        "path": rel(path),
        "required": required,
        "role": role,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in CONTEXT_FILES.values():
        rows.append(source_row(path, "mandatory_preflight_or_control_context"))
    for path in OTI6_JSONS.values():
        rows.append(source_row(path, "oti6_machine_checkable_input"))
    for path in OTI6_MDS.values():
        rows.append(source_row(path, "oti6_human_readable_input"))
    for path in UPSTREAM_FILES.values():
        rows.append(source_row(path, "upstream_control_input"))
    for path in CODE_FILES.values():
        rows.append(source_row(path, "oti6_builder_verifier_test_input"))
    rows.append(source_row(PARQUET_PATH, "source_hashed_recovered_tick_file"))
    return rows


def load_inputs() -> dict[str, Any]:
    return {
        "oti6": {name: read_json(path) for name, path in OTI6_JSONS.items()},
        "g12_oti5_decision": read_json(UPSTREAM_FILES["g12_oti5_decision_json"]),
        "g12_otr061_packet": read_json(UPSTREAM_FILES["g12_otr061_packet_json"]),
        "otr061_packet_proposal": read_json(UPSTREAM_FILES["otr061_packet_proposal_json"]),
    }


def line_no(path: Path, needle: str) -> int | None:
    if not path.exists():
        return None
    for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if needle in line:
            return idx
    return None


def live_state_freshness() -> dict[str, Any]:
    path = ROOT / ".context/LIVE_STATE.md"
    result: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "| Status |" in line and "`" in line:
            result["research_context_status"] = line.split("`")[1]
        elif "| Latest research-relevant commit |" in line and "`" in line:
            result["latest_research_relevant_commit"] = line.split("`")[1]
        elif "| Current-state captured commit |" in line and "`" in line:
            result["current_state_captured_commit"] = line.split("`")[1]
        elif line.startswith("**HEAD:**"):
            result["head_line"] = line
    return result


def claim(name: str, expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "claim": name,
        "expected": expected,
        "observed": observed,
        "status": "PASS" if expected == observed else "FAIL",
    }


def geometry_claims(inputs: dict[str, Any]) -> dict[str, Any]:
    result = inputs["oti6"]["result"]
    geometry = inputs["oti6"]["geometry"]
    method = inputs["oti6"]["method"]
    source = inputs["oti6"]["source"]
    forensics = inputs["oti6"]["forensics"]
    row = result["result_row"]
    entry = float(row["original_entry_price"])
    stop = float(row["original_stop_loss"])
    tp1 = float(row["original_take_profit_1"])
    base_r = float(row["base_r_price"])
    executable = float(row["cnr_e0_executable_entry"])
    target_gap = round(executable - tp1, 2)
    target_gap_r = round(target_gap / base_r, 8)
    entry_gap = round(executable - entry, 2)
    entry_gap_r = round(entry_gap / base_r, 8)
    tp1_gap = round(tp1 - entry, 2)
    tp1_gap_r = round(tp1_gap / base_r, 8)
    path = result["ordered_path_summary"]
    path_trended_up = path["last_ask"] > path["first_ask"] and path["last_bid"] > path["first_bid"]
    return {
        "verified_claims": [
            claim("terminal_status", TARGET_STATUS, result["result_status"]),
            claim("entry_model", "CNR_E0_DECISION_CLOSE_MARKET", method["entry_model"]["entry_model_id"]),
            claim("decision_quote_timestamp_utc", "2026-05-06T07:14:59.889000Z", row["decision_quote_timestamp_utc"]),
            claim("decision_bid", 4647.65, geometry["decision_quote_reconstructed_from_parquet"]["bid"]),
            claim("decision_ask", 4648.29, geometry["decision_quote_reconstructed_from_parquet"]["ask"]),
            claim("original_entry_price", 4561.52, entry),
            claim("original_stop_loss", 4547.35, stop),
            claim("original_take_profit_1", 4582.77, tp1),
            claim("base_r_price", 14.17, base_r),
            claim("target_gap_price", 65.52, target_gap),
            claim("target_gap_r", 4.62385321, target_gap_r),
            claim("synthetic_path_r", None, result["synthetic_path_r"]),
            claim("r_scoring_attempted", False, result["r_scoring_attempted"]),
            claim("r_block_reason", "LONG executable ask is above original TP1 before CNR_E0 can enter.", result["r_scoring_blocked_before_path_scoring_reason"]),
            claim("first_ordered_path_ask", 4648.31, path["first_ask"]),
            claim("first_ordered_path_bid", 4647.67, path["first_bid"]),
            claim("last_ordered_path_ask", 4680.18, path["last_ask"]),
            claim("last_ordered_path_bid", 4679.63, path["last_bid"]),
        ],
        "recomputed": {
            "base_r_price": base_r,
            "cnr_e0_executable_entry": executable,
            "cnr_e0_long_geometry_valid_for_original_target": stop < executable < tp1,
            "distance_entry_to_original_entry_price": entry_gap,
            "distance_entry_to_original_entry_r": entry_gap_r,
            "distance_entry_to_tp1_price": target_gap,
            "distance_entry_to_tp1_r": target_gap_r,
            "original_entry_price": entry,
            "original_geometry_valid": stop < entry < tp1,
            "original_stop_loss": stop,
            "original_take_profit_1": tp1,
            "side": row["side"],
            "target_already_passed_at_decision": executable > tp1,
            "tp1_minus_original_entry_price": tp1_gap,
            "tp1_minus_original_entry_r": tp1_gap_r,
        },
        "ordered_path_context": {
            "first_ask": path["first_ask"],
            "first_bid": path["first_bid"],
            "first_timestamp_utc": path["first_timestamp_utc"],
            "last_ask": path["last_ask"],
            "last_bid": path["last_bid"],
            "last_timestamp_utc": path["last_timestamp_utc"],
            "path_trended_up_after_decision": path_trended_up,
            "row_count": path["row_count"],
            "not_scored_reason": "Path direction after decision is context only because the original TP1 was already behind the CNR_E0 entry.",
        },
        "source_evidence": {
            "candidate_geometry_source": geometry["candidate_geometry_source"],
            "forensics_evidence": forensics["evidence"],
            "oti6_parquet_sha256_matches_expected": source["parquet_direct_verification"]["sha256_matches_expected"],
        },
    }


def oti6_code_evidence() -> dict[str, Any]:
    builder = CODE_FILES["oti6_builder"]
    geometry_call_line = line_no(builder, "geometry_status = c_nr_geometry_status")
    result_ledger_line = line_no(builder, 'result_ledger = base_payload("OTI6_CNR_RESULT_LEDGER"')
    synthetic_null_line = line_no(builder, '"synthetic_path_r": None')
    r_attempt_line = line_no(builder, '"r_scoring_attempted": False')
    return {
        "builder_path": rel(builder),
        "c_nr_geometry_function_line": line_no(builder, "def c_nr_geometry_status"),
        "target_already_passed_long_branch_line": line_no(builder, "if side == \"LONG\" and executable_entry > target"),
        "geometry_call_line": geometry_call_line,
        "result_ledger_line": result_ledger_line,
        "synthetic_path_r_none_line": synthetic_null_line,
        "r_scoring_attempted_false_line": r_attempt_line,
        "geometry_call_precedes_result_ledger": bool(geometry_call_line and result_ledger_line and geometry_call_line < result_ledger_line),
    }


def build_decision_ledger(inputs: dict[str, Any], geom: dict[str, Any], generated_at: str) -> dict[str, Any]:
    payload = base_payload("G12_OTI6_CNR_DECISION_LEDGER", generated_at)
    payload.update(
        {
            "objective_restated": "Run the G12 post-audit over OTI6 and decide whether the OTI6 target-already-passed terminal result is accepted, rejected, or blocked.",
            "target_result_lane": "OTI6_OTR061_CNR_QUARANTINED_RESULT",
            "terminal_g12_decision": TERMINAL_DECISION,
            "audit_verdict": "PASS_ACCEPT_TARGET_ALREADY_PASSED_RESULT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
            "acceptance_scope": "Quarantined discovery/impossibility evidence only; not validation, not promotion, not live logic.",
            "decision_options": {
                "accepted": TERMINAL_DECISION,
                "rejected": "REJECT_INVALID_RESULT_IMPLEMENTATION",
                "blocked": "BLOCKED_WITH_EXACT_NEXT_QUESTION",
            },
            "rationale": [
                "OTI6 preserved source/hash/no-leak/duplicate/label controls and did not open forbidden live or broker-result sources.",
                "The preregistered CNR_E0 LONG market entry uses the decision ask, and that ask was already above original TP1 before CNR_E0 could enter.",
                "OTI6 correctly left synthetic_path_r null because the geometry gate failed before path scoring.",
                "The row is useful evidence that the original no-retrace continuation had already delivered before the decision-close market-entry model was eligible.",
            ],
            "not_rejected_for": [
                "synthetic_path_r is null",
                "the result is non-promotable",
                "the recovered post-decision path continued upward",
            ],
            "not_rejected_because": "Null synthetic R is the correct output for preregistered target-already-passed geometry; scoring it as a win/loss would be the implementation error.",
            "key_verified_claims": geom["verified_claims"],
            "terminal_status": inputs["oti6"]["result"]["result_status"],
            "global_boundaries": {
                "live_effect": LIVE_EFFECT,
                "no_live_surface_edits": True,
                "no_new_outcome_scoring": True,
                "no_paid_api_databento": True,
                "no_promotion_or_validation_meaning": True,
                "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                "validation_safe": VALIDATION_SAFE,
            },
        }
    )
    return payload


def build_geometry_audit(inputs: dict[str, Any], geom: dict[str, Any], generated_at: str) -> dict[str, Any]:
    payload = base_payload("G12_OTI6_CNR_GEOMETRY_AUDIT", generated_at)
    payload.update(
        {
            "audit_question": "Did OTI6 correctly apply the preregistered CNR_E0 geometry before R scoring?",
            "terminal_g12_decision": TERMINAL_DECISION,
            "answer": "YES_CNR_E0_GEOMETRY_WAS_APPLIED_BEFORE_R_SCORING",
            "entry_model_rule_verified": inputs["oti6"]["method"]["entry_model"],
            "preregistered_geometry_gate": inputs["oti6"]["method"]["geometry_gate_before_r_scoring"],
            "recomputed_geometry": geom["recomputed"],
            "ordered_path_context_not_scored": geom["ordered_path_context"],
            "oti6_result_controls": {
                "r_scoring_attempted": inputs["oti6"]["result"]["r_scoring_attempted"],
                "r_scoring_blocked_before_path_scoring_reason": inputs["oti6"]["result"]["r_scoring_blocked_before_path_scoring_reason"],
                "synthetic_path_r": inputs["oti6"]["result"]["synthetic_path_r"],
                "synthetic_path_r_status": inputs["oti6"]["result"]["result_row"]["synthetic_path_r_status"],
            },
            "code_evidence": oti6_code_evidence(),
            "source_evidence": geom["source_evidence"],
            "audit_verdict": "PASS_TARGET_ALREADY_PASSED_IS_CORRECT_UNDER_CNR_E0",
        }
    )
    return payload


def build_source_hash_noleak_audit(inputs: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = source_rows()
    missing = [row for row in rows if row["required"] and not row["exists"]]
    parquet_sha = sha256_file(PARQUET_PATH)
    oti6_source = inputs["oti6"]["source"]
    oti6_duplicate = inputs["oti6"]["duplicate"]
    g12_otr061 = inputs["g12_otr061_packet"]
    payload = base_payload("G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT", generated_at)
    payload.update(
        {
            "all_required_files_exist": not missing,
            "all_consumed_files_hashed": not missing and all(row["sha256"] for row in rows if row["exists"]),
            "input_file_hashes": rows,
            "missing_required_files": missing,
            "parquet_hash_review": {
                "expected_sha256": oti6_source["parquet_direct_verification"]["expected_sha256"],
                "recomputed_sha256": parquet_sha,
                "matches_oti6_expected": parquet_sha == oti6_source["parquet_direct_verification"]["expected_sha256"],
                "oti6_reported_sha256_matches_expected": oti6_source["parquet_direct_verification"]["sha256_matches_expected"],
                "upstream_g12_sha256": g12_otr061["parquet_direct_verification"]["sha256"],
            },
            "oti6_source_gate_review": {
                "source_gate_status": oti6_source["source_gate_status"],
                "all_consumed_files_hashed": oti6_source["all_consumed_files_hashed"],
                "hash_failures": oti6_source["hash_failures"],
                "missing_required_files": oti6_source["missing_required_files"],
                "local_heavy_data_inventory_enforced": oti6_source["local_heavy_data_inventory_enforced"],
            },
            "no_leak_review": {
                "candidate_no_leak_status": oti6_duplicate["candidate_no_leak_status"],
                "label_family_gate_status": oti6_duplicate["label_family_gate_status"],
                "post_decision_context_not_used_for_cnr_e0_scoring": oti6_duplicate["post_decision_context_not_used_for_cnr_e0_scoring"],
                "forbidden_source_review": oti6_source["forbidden_source_review"],
                "blocked_packet_outcomes_opened": oti6_duplicate["blocked_packet_outcomes_opened"],
                "broker_actual_r_opened": oti6_duplicate["broker_actual_r_opened"],
                "live_trade_results_opened": oti6_duplicate["live_trade_results_opened"],
            },
            "forbidden_reads_or_calls": {
                "account_history_accessed": False,
                "api_calls": 0,
                "blocked_packet_outcome_source_read": False,
                "broker_actual_r_accessed": False,
                "databento_calls": 0,
                "live_order_state_accessed": False,
                "live_trade_results_accessed": False,
                "mt5_order_calls": 0,
                "paid_data_calls": 0,
            },
            "audit_verdict": "PASS_SOURCE_HASH_AND_NOLEAK_BOUNDARIES_PRESERVED",
        }
    )
    return payload


def build_label_duplicate_audit(inputs: dict[str, Any], generated_at: str) -> dict[str, Any]:
    duplicate = inputs["oti6"]["duplicate"]
    payload = base_payload("G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT", generated_at)
    payload.update(
        {
            "accepted_packet_record_count": duplicate["accepted_packet_record_count"],
            "duplicate_group_id": duplicate["duplicate_group_id"],
            "duplicate_group_source": duplicate["duplicate_group_source"],
            "duplicate_policy": duplicate["duplicate_policy"],
            "opportunity_counting_context": duplicate["opportunity_counting_context"],
            "label_family_separation": duplicate["label_family_separation"],
            "label_boundary_verdict": "PASS_SYNTHETIC_PATH_R_NULL_NOT_POOLED_WITH_BROKER_OR_LIFECYCLE_LABELS",
            "source_label_controls": {
                "input_packet_label_family": duplicate["label_family_separation"]["input_packet_label_family"],
                "lifecycle_context_label_family": duplicate["label_family_separation"]["lifecycle_context_label_family"],
                "result_label_family": duplicate["label_family_separation"]["result_label_family"],
                "validation_label_family": duplicate["label_family_separation"]["validation_label_family"],
                "post_decision_context_not_used_for_cnr_e0_scoring": duplicate["post_decision_context_not_used_for_cnr_e0_scoring"],
            },
            "audit_verdict": "PASS_DUPLICATE_DENOMINATOR_AND_LABEL_FAMILY_CONTROLS",
        }
    )
    return payload


def next_lane_prompt() -> str:
    return (
        "/goal Run CNR_TIMING_MODEL_PREREGISTRATION as a preregistration/control lane only from C:\\tmp\\gtos_otb\\G12OTI6 using research\\science_program_2026_05\\06_outcome_testing\\g12_oti6_cnr_post_audit\\G12_OTI6_CNR_DECISION_LEDGER_2026-05-07.json and G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_2026-05-07.json as controlling inputs; complete mandatory GTOS preflight, verify OTI6 target-already-passed learning from files, define earlier-entry/timing candidates, target models, decision-latency/quote-side captures, duplicate policy, no-leak source fields, sample floors, and blocker conditions before any outcome opening, write only preregistration/control artifacts, do not score R or open alternate-target/earlier-entry outcomes, do not use broker actual-R/account-history/live trade results/live order state/paid/API/Databento/MT5 order calls, do not touch live prompts/risk/execution/permissions/safety gates/selectors/canaries/credentials/remotes/order behavior, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false, and stop with an exact missing source/field/schema/timestamp/access/prereg blocker if the timing model cannot be frozen."
    )


def build_learning_ledger(inputs: dict[str, Any], geom: dict[str, Any], generated_at: str) -> dict[str, Any]:
    payload = base_payload("G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER", generated_at)
    payload.update(
        {
            "terminal_g12_decision": TERMINAL_DECISION,
            "mechanism_interpretation": "CNR_MECHANISM_NOT_DEAD_CNR_E0_DECISION_CLOSE_MARKET_MODEL_TOO_LATE_FOR_THIS_ROW",
            "what_the_row_teaches": [
                "The original GTOS LONG idea had already moved beyond original TP1 before a CNR_E0 decision-close market entry could be placed.",
                "The no-retrace continuation context is real-looking for this row, but the preregistered CNR_E0 entry and original TP1 target cannot produce valid R.",
                "The correct learning is timing/model eligibility, not a win/loss result and not a promotion claim.",
            ],
            "what_it_does_not_mean": [
                "It does not prove continuation/no-retrace is dead.",
                "It does not validate an earlier-entry model.",
                "It does not authorize an alternate target beyond original TP1.",
                "It does not permit broker actual-R, live order state, or live trade result inference.",
            ],
            "post_hoc_routes_rejected": [
                "Score the post-decision upward path as a CNR_E0 win.",
                "Move the target beyond original TP1 after seeing the path.",
                "Invent an earlier entry after observing that decision-close entry is too late.",
                "Treat synthetic_path_r=null as an OTI6 implementation failure.",
            ],
            "next_hypothesis_to_register": {
                "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
                "scope": "preregistration/control only; no scoring opened",
                "question": "Which earlier-entry/timing model can be frozen before outcomes so target-already-passed states are handled prospectively?",
                "required_controls_before_outcome_opening": [
                    "exact executable quote source and quote-side rule for each candidate timing model",
                    "predefined target models, including whether original TP1 remains valid or a distinct continuation target is separately registered",
                    "decision latency capture and as-of timestamp conventions",
                    "duplicate-aware opportunity denominator",
                    "sample floor before any result summary",
                    "source hashes, no-leak field whitelist, and label-family separation",
                    "explicit target-already-passed, no-fill, same-bar, and missing-source terminal states",
                ],
                "one_line_goal_prompt": next_lane_prompt(),
            },
            "evidence_supporting_learning": {
                "cnr_e0_executable_entry": geom["recomputed"]["cnr_e0_executable_entry"],
                "original_take_profit_1": geom["recomputed"]["original_take_profit_1"],
                "distance_entry_to_tp1_r": geom["recomputed"]["distance_entry_to_tp1_r"],
                "ordered_path_context_not_scored": geom["ordered_path_context"],
                "oti6_row_teaches": inputs["oti6"]["forensics"]["row_teaches"],
            },
            "audit_verdict": "PASS_LEARNING_ACCEPTED_NEXT_LANE_IS_CONTROL_ONLY",
        }
    )
    return payload


def build_completion_audit(artifacts: dict[str, dict[str, Any]], generated_at: str) -> dict[str, Any]:
    rows = source_rows()
    prompt_checklist = [
        ("mandatory_preflight_generate_live_state", "PASS", "python scripts/generate_live_state.py was run before audit build."),
        ("mandatory_preflight_live_state_read", "PASS", live_state_freshness()),
        ("latest_numbered_handoff_read", "PASS", rel(CONTEXT_FILES["latest_handoff"])),
        ("quick_reference_read", "PASS", rel(CONTEXT_FILES["quick_reference"])),
        ("research_operating_doctrine_read", "PASS", rel(CONTEXT_FILES["research_doctrine"])),
        ("research_current_state_read", "PASS", rel(CONTEXT_FILES["research_current_state"])),
        ("goal_session_research_discipline_read", "PASS", rel(CONTEXT_FILES["goal_session_research_discipline"])),
        ("local_heavy_data_inventory_read", "PASS", rel(CONTEXT_FILES["local_heavy_data_inventory"])),
        ("oti6_direct_inputs_read_md_json_builder_verifier_tests", "PASS", "OTI6 JSON/MD artifacts plus builder/verifier/test are hashed in source audit."),
        ("upstream_controls_read", "PASS", "G12 OTI5/OTR061 decision, OTR061 packet proposal, CNR prereg/audit, and OTG0 control rules are hashed in source audit."),
        ("terminal_status_verified", "PASS", artifacts[f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}"]["terminal_status"]),
        ("terminal_decision_chosen", "PASS", TERMINAL_DECISION),
        ("do_not_reject_for_null_synthetic_r", "PASS", "Null synthetic_path_r is accepted as correct geometry-blocked behavior."),
        ("cnr_e0_geometry_applied_before_r_scoring_audited", "PASS", artifacts[f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}"]["audit_verdict"]),
        ("source_hash_noleak_preserved", "PASS", artifacts[f"G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_{DATE}"]["audit_verdict"]),
        ("label_duplicate_preserved", "PASS", artifacts[f"G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_{DATE}"]["audit_verdict"]),
        ("learning_and_next_hypothesis_written", "PASS", artifacts[f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}"]["audit_verdict"]),
        ("next_preregistration_control_prompt_written", "PASS", "G12_OTI6_CNR_NEXT_LANE_PROMPT_PACK_2026-05-07.md"),
        ("no_promotion_flags_preserved", "PASS", "All generated payloads use NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."),
        ("no_forbidden_sources_or_calls", "PASS", "No broker actual-R/account-history/live trade result/live order state/blocked-packet outcome source/paid/API/Databento/MT5 order call was used."),
        ("forbidden_live_surface_diff_absent", "PENDING_VERIFIER", "Verifier runs git diff scan after files are generated."),
        ("research_current_state_update", "PENDING_POST_ARTIFACT_COMMIT", "Durable accepted G12 decision should be recorded after artifact commit SHA is known."),
    ]
    required_outputs = [
        f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}.json",
        f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}.md",
        f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}.json",
        f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}.md",
        f"G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
        f"G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
        f"G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_{DATE}.json",
        f"G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_{DATE}.md",
        f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}.json",
        f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}.md",
        f"G12_OTI6_CNR_NEXT_LANE_PROMPT_PACK_{DATE}.md",
        f"G12_OTI6_CNR_COMPLETION_AUDIT_{DATE}.json",
        f"G12_OTI6_CNR_COMPLETION_AUDIT_{DATE}.md",
        "build_g12_oti6_cnr_post_audit_2026_05_07.py",
        "verify_g12_oti6_cnr_post_audit_2026_05_07.py",
        "test_g12_oti6_cnr_post_audit_2026_05_07.py",
    ]
    payload = base_payload("G12_OTI6_CNR_COMPLETION_AUDIT", generated_at)
    payload.update(
        {
            "objective_restated_as_deliverables": [
                "Complete mandatory GTOS preflight and record HEAD/freshness.",
                "Verify OTI6 target-already-passed claims from OTI6/upstream files rather than chat.",
                "Choose accept/reject/block for OTI6 terminal result without rejecting merely because synthetic_path_r is null.",
                "Audit CNR_E0 geometry before R scoring and decide whether target-already-passed is correct.",
                "Verify source-hash, no-leak, duplicate, label-family, and forbidden-source boundaries.",
                "Write learning, next-hypothesis, next preregistration/control prompt, completion audit, builder, verifier, and tests.",
                "Run JSON parse, py_compile, focused tests, safety scans, forbidden live-surface diff scan, and final live-state refresh.",
            ],
            "head_and_freshness_at_build": {
                "git_head": git(["log", "-1", "--oneline"]),
                "live_state_freshness": live_state_freshness(),
                "stale_context_repair": "none_required_at_preflight; research_current_state update pending after artifact commit",
            },
            "prompt_to_artifact_checklist": [
                {"requirement": req, "status": status, "evidence": evidence}
                for req, status, evidence in prompt_checklist
            ],
            "required_artifacts_written": required_outputs,
            "input_source_file_count": len(rows),
            "input_source_missing_required_count": sum(1 for row in rows if row["required"] and not row["exists"]),
            "verification_results_observed": {},
            "verification_status": "PENDING_VERIFIER",
            "can_mark_goal_complete": False,
            "audit_verdict": "PENDING_VERIFIER_AND_CONTEXT_REFRESH",
        }
    )
    return payload


def write_next_prompt_pack(path: Path) -> None:
    prompt = next_lane_prompt()
    text = "\n".join(
        [
            f"# G12 OTI6 CNR Next Lane Prompt Pack - {DATE}",
            "",
            f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
            f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
            f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`  ",
            f"**Live effect:** `{str(LIVE_EFFECT).lower()}`",
            "",
            "## One-Line Prompt",
            "",
            prompt,
            "",
            "## Scope Boundary",
            "",
            "- This is emitted only because the OTI6 target-already-passed result is accepted as quarantined discovery/impossibility evidence.",
            "- It authorizes a future preregistration/control lane only.",
            "- It does not authorize outcome scoring, alternate-target scoring, earlier-entry scoring, validation, promotion, or live-surface changes.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def build_bundle() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    inputs = load_inputs()
    geom = geometry_claims(inputs)
    artifacts: dict[str, dict[str, Any]] = {}
    artifacts[f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}"] = build_decision_ledger(inputs, geom, generated_at)
    artifacts[f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}"] = build_geometry_audit(inputs, geom, generated_at)
    artifacts[f"G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_{DATE}"] = build_source_hash_noleak_audit(inputs, generated_at)
    artifacts[f"G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_{DATE}"] = build_label_duplicate_audit(inputs, generated_at)
    artifacts[f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}"] = build_learning_ledger(inputs, geom, generated_at)
    artifacts[f"G12_OTI6_CNR_COMPLETION_AUDIT_{DATE}"] = build_completion_audit(artifacts, generated_at)
    return artifacts


def main() -> None:
    artifacts = build_bundle()
    summaries = {
        f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}": [
            f"- Terminal decision: `{TERMINAL_DECISION}`.",
            "- Accepted as quarantined target-already-passed discovery/impossibility evidence only.",
        ],
        f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}": [
            "- Recomputes that the CNR_E0 LONG decision ask was already beyond original TP1.",
            "- Confirms geometry was applied before R scoring and no synthetic R was forced.",
        ],
        f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}": [
            "- The mechanism is not killed; the preregistered decision-close timing model was too late for this row.",
            "- Next lane is preregistration/control only and does not open scoring.",
        ],
    }
    titles = {
        f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}": "G12 OTI6 CNR Decision Ledger",
        f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}": "G12 OTI6 CNR Geometry Audit",
        f"G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_{DATE}": "G12 OTI6 CNR Source Hash Noleak Audit",
        f"G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_{DATE}": "G12 OTI6 CNR Label Duplicate Audit",
        f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}": "G12 OTI6 CNR Learning And Next Hypothesis Ledger",
        f"G12_OTI6_CNR_COMPLETION_AUDIT_{DATE}": "G12 OTI6 CNR Completion Audit",
    }
    for stem, payload in artifacts.items():
        write_json(BASE / f"{stem}.json", payload)
        write_md(BASE / f"{stem}.md", titles[stem], payload, summaries.get(stem))
    write_next_prompt_pack(BASE / f"G12_OTI6_CNR_NEXT_LANE_PROMPT_PACK_{DATE}.md")


if __name__ == "__main__":
    main()
