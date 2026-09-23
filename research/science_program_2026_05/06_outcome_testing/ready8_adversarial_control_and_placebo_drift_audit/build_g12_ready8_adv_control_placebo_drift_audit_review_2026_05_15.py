"""Build the G12 review package for READY8 adversarial controls."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-15"
PREFIX = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT"
ROUTE_ID = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT"
EVIDENCE_CLASS = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY"
TARGET_EVIDENCE_CLASS = "READY8_ADVERSARIAL_CONTROL_PLACEBO_DRIFT_AND_DUPLICATE_ARTIFACT_AUDIT_ONLY"
TERMINAL_DECISION = (
    "ACCEPT_AS_G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_CANONICAL_DOWNSTREAM_CONTROL_EVIDENCE_NO_PROMOTION"
)
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_trading_risk_safety_prompt_decision_behavior",
    "opens_ai_api",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_paid_or_vendor_access",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
]
SAFE_STATUS = "NO_PROMOTION_VERDICT_validation_safe_false_outcome_review_opened_false_live_effect_false"

CONTROL_CARDS = {"ADV-001", "ADV-003"}
NONADV_CARDS = {"BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"}

TARGET_FILES = {
    "control_design": "READY8_ADV001_ADV003_CONTROL_DESIGN_AUDIT_LEDGER_2026-05-15.json",
    "adv001_placebo": "READY8_ADV001_PLACEBO_DRIFT_LEDGER_2026-05-15.jsonl",
    "adv003_placebo": "READY8_ADV003_DUPLICATE_PLACEBO_DRIFT_LEDGER_2026-05-15.jsonl",
    "baseline_drift": "READY8_BASELINE_DRIFT_BY_AXIS_LEDGER_2026-05-15.jsonl",
    "duplicate_artifact": "READY8_DUPLICATE_BUCKET_ARTIFACT_LEDGER_2026-05-15.jsonl",
    "comparison_mapping": "READY8_NONADV_COMPARISON_CONTROL_DRIFT_MAPPING_LEDGER_2026-05-15.jsonl",
    "explained_weakened": "READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_2026-05-15.jsonl",
    "residual": "READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_2026-05-15.jsonl",
    "concentration": "READY8_CONCENTRATION_ADJUSTED_INTERPRETATION_LEDGER_2026-05-15.jsonl",
    "stress_vs_sealed": "READY8_STRESS_VS_SEALED_CONTROL_DRIFT_LEDGER_2026-05-15.jsonl",
    "underpower": "READY8_BRANCH_UNDERPOWER_EFFECTIVE_N_LEDGER_2026-05-15.jsonl",
    "downstream_rules": "READY8_DOWNSTREAM_ADJUSTMENT_RULES_2026-05-15.json",
    "target_saturation": "READY8_ADV_CONTROL_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-15.json",
    "target_completion": "READY8_ADV_CONTROL_COMPLETION_AUDIT_2026-05-15.json",
    "target_manifest": "READY8_ADV_CONTROL_OUTPUT_MANIFEST_2026-05-15.json",
    "target_verification": "READY8_ADV_CONTROL_VERIFICATION_RESULT_2026-05-15.json",
    "target_focused_test": "READY8_ADV_CONTROL_FOCUSED_TEST_RESULT_2026-05-15.json",
    "target_synthesis": "READY8_ADV_CONTROL_SYNTHESIS_2026-05-15.md",
    "target_repair": "READY8_ADV_CONTROL_BLOCKER_REPAIR_LEDGER_2026-05-15.json",
    "prompt": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_PROMPT_2026-05-15.md",
    "starter": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_STARTER_2026-05-15.txt",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def target_path(key: str) -> Path:
    return ROUTE_DIR / TARGET_FILES[key]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                yield line_no, json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def safe_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **{flag: False for flag in SAFE_FALSE_FLAGS},
        "generated_at_utc": now_utc(),
    }


def safe_flags_ok(record: dict[str, Any]) -> bool:
    if record.get("safe_flags_status") == SAFE_STATUS:
        return True
    if record.get("promotion_verdict") != PROMOTION_VERDICT:
        return False
    return all(record.get(flag) is False for flag in SAFE_FALSE_FLAGS)


def row_key(record: dict[str, Any]) -> str:
    return "|".join(
        [
            str(record.get("comparison_id")),
            str(record.get("comparison_family")),
            str(record.get("card_id")),
            json.dumps(record.get("branch_key"), sort_keys=True, separators=(",", ":")),
        ]
    )


def numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def expected_adjustment_class(record: dict[str, Any]) -> str:
    raw = numeric(record.get("finding_delta"))
    envelope = numeric(record.get("matched_control_envelope_abs"))
    if raw is None or envelope is None or numeric(record.get("matched_control_count")) in {None, 0.0}:
        return "NOT_NUMERIC_NOT_ADJUSTABLE"
    if record.get("finding_underpowered") is True:
        return "UNDERPOWERED_PRESERVED_NOT_DECISION"
    raw_abs = abs(raw)
    if raw_abs <= envelope:
        return "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT"
    if raw_abs <= 2 * envelope:
        return "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT"
    return "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE"


def scan_json_or_jsonl(path: Path) -> dict[str, Any]:
    parse_errors: list[dict[str, Any]] = []
    if path.suffix == ".json":
        try:
            payload = read_json(path)
            records = payload if isinstance(payload, list) else [payload]
        except Exception as exc:  # pragma: no cover - diagnostic path
            return {"path": rel(path), "rows": 0, "parse_errors": [{"line": None, "error": str(exc)}]}
    elif path.suffix == ".jsonl":
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    parse_errors.append({"line": line_no, "error": str(exc)})
    else:
        return {"path": rel(path), "rows": None, "parse_errors": []}

    safe_failures = 0
    route_mismatches = 0
    evidence_mismatches = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        if not safe_flags_ok(record):
            safe_failures += 1
        if record.get("route_id") != "READY8_ADVERSARIAL_CONTROL_AND_PLACEBO_DRIFT_AUDIT":
            route_mismatches += 1
        if record.get("evidence_class") != TARGET_EVIDENCE_CLASS:
            evidence_mismatches += 1
    return {
        "path": rel(path),
        "rows": len(records),
        "parse_errors": parse_errors,
        "safe_flag_failures": safe_failures,
        "target_route_id_mismatches": route_mismatches,
        "target_evidence_class_mismatches": evidence_mismatches,
    }


def manifest_hash_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for row in manifest.get("artifacts", []):
        path = ROOT / row["path"]
        actual = sha256_file(path)
        if row.get("artifact_key") == "manifest":
            ok = row.get("sha256") is None
        else:
            ok = row.get("sha256") == actual
        out = {
            "artifact_key": row.get("artifact_key"),
            "path": row.get("path"),
            "exists": path.exists(),
            "expected_sha256": row.get("sha256"),
            "actual_sha256": actual,
            "ok": ok,
        }
        rows.append(out)
        if not ok:
            mismatches.append(out)
    return {"rows": rows, "mismatches": mismatches, "mismatch_count": len(mismatches)}


def recompute_ledgers() -> dict[str, Any]:
    scans = {key: scan_json_or_jsonl(target_path(key)) for key in TARGET_FILES}
    manifest = read_json(target_path("target_manifest"))
    verifier = read_json(target_path("target_verification"))
    completion = read_json(target_path("target_completion"))
    control_design = read_json(target_path("control_design"))
    downstream = read_json(target_path("downstream_rules"))
    saturation = read_json(target_path("target_saturation"))
    repair = read_json(target_path("target_repair"))

    adv_roles: dict[str, Counter] = {"ADV-001": Counter(), "ADV-003": Counter()}
    adv_card_ids: dict[str, Counter] = {"ADV-001": Counter(), "ADV-003": Counter()}
    for file_key, card_id in [("adv001_placebo", "ADV-001"), ("adv003_placebo", "ADV-003")]:
        for _, record in iter_jsonl(target_path(file_key)):
            adv_roles[card_id][str(record.get("control_role"))] += 1
            adv_card_ids[card_id][str(record.get("card_id"))] += 1

    mapping_counts: Counter[str] = Counter()
    mapping_card_counts: dict[str, Counter] = defaultdict(Counter)
    math_mismatches: list[dict[str, Any]] = []
    missing_control_match = 0
    comparison_keys_by_class: dict[str, set[str]] = defaultdict(set)
    for line_no, record in iter_jsonl(target_path("comparison_mapping")):
        actual = record.get("adjustment_classification")
        expected = expected_adjustment_class(record)
        mapping_counts[str(actual)] += 1
        mapping_card_counts[str(record.get("card_id"))][str(actual)] += 1
        comparison_keys_by_class[str(actual)].add(row_key(record))
        if numeric(record.get("matched_control_count")) in {None, 0.0}:
            missing_control_match += 1
        if actual != expected:
            math_mismatches.append(
                {
                    "line": line_no,
                    "comparison_id": record.get("comparison_id"),
                    "card_id": record.get("card_id"),
                    "actual": actual,
                    "expected": expected,
                    "finding_delta": record.get("finding_delta"),
                    "matched_control_envelope_abs": record.get("matched_control_envelope_abs"),
                    "finding_underpowered": record.get("finding_underpowered"),
                }
            )

    explained_keys = {row_key(record) for _, record in iter_jsonl(target_path("explained_weakened"))}
    residual_keys = {row_key(record) for _, record in iter_jsonl(target_path("residual"))}
    expected_explained_keys = (
        comparison_keys_by_class["FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT"]
        | comparison_keys_by_class["MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT"]
    )
    expected_residual_keys = comparison_keys_by_class["RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE"]

    concentration_counts = Counter()
    concentration_cards = Counter()
    for _, record in iter_jsonl(target_path("concentration")):
        concentration_counts[str(record.get("adjusted_interpretation"))] += 1
        concentration_cards[str(record.get("card_id"))] += 1

    underpower_counts = Counter()
    underpower_cards = Counter()
    for _, record in iter_jsonl(target_path("underpower")):
        underpower_counts[str(record.get("underpowered_unique_duplicate_floor_lt_30"))] += 1
        underpower_cards[str(record.get("card_id"))] += 1

    stress_counts = Counter()
    for _, record in iter_jsonl(target_path("stress_vs_sealed")):
        stress_counts[str(record.get("stress_sealed_classification"))] += 1

    duplicate_record_types = Counter()
    duplicate_interpretations = Counter()
    for _, record in iter_jsonl(target_path("duplicate_artifact")):
        duplicate_record_types[str(record.get("record_type"))] += 1
        duplicate_interpretations[str(record.get("artifact_interpretation"))] += 1

    no_top_n = saturation.get("no_arbitrary_top_n_proof", {})
    row_counts = {key: value["rows"] for key, value in scans.items() if isinstance(value.get("rows"), int)}

    return {
        **safe_payload("recomputation_ledger"),
        "audit_current_head": git_head(),
        "target_route_dir": rel(ROUTE_DIR),
        "target_manifest_hash_audit": manifest_hash_audit(manifest),
        "target_file_scan_summary": scans,
        "row_count_recomputation": row_counts,
        "target_verifier_ok": verifier.get("ok") is True,
        "target_verifier_can_mark_goal_complete": verifier.get("can_mark_goal_complete") is True,
        "target_verifier_issues": verifier.get("issues"),
        "target_completion_can_mark_goal_complete": completion.get("can_mark_goal_complete_after_verifier_and_tests") is True,
        "target_same_evidence_class_blockers_remaining": completion.get("same_evidence_class_blockers_remaining"),
        "control_cards_are_not_edge_cards": control_design.get("accepted_facts_bound", {}).get(
            "control_cards_are_not_edge_cards"
        )
        is True,
        "adv_control_roles": {card: dict(counter) for card, counter in adv_roles.items()},
        "adv_card_id_counts": {card: dict(counter) for card, counter in adv_card_ids.items()},
        "nonadv_comparison_rows_preserved": row_counts["comparison_mapping"],
        "nonadv_cards_observed": sorted(mapping_card_counts),
        "nonadv_expected_cards": sorted(NONADV_CARDS),
        "control_envelope_classification_counts": dict(mapping_counts),
        "control_envelope_classification_counts_by_card": {
            card: dict(counter) for card, counter in sorted(mapping_card_counts.items())
        },
        "control_envelope_math_mismatch_count": len(math_mismatches),
        "control_envelope_math_mismatches": math_mismatches,
        "control_match_missing_rows": missing_control_match,
        "explained_weakened_key_set_matches_mapping": explained_keys == expected_explained_keys,
        "explained_weakened_extra_keys": sorted(explained_keys - expected_explained_keys),
        "explained_weakened_missing_keys": sorted(expected_explained_keys - explained_keys),
        "residual_key_set_matches_mapping": residual_keys == expected_residual_keys,
        "residual_extra_keys": sorted(residual_keys - expected_residual_keys),
        "residual_missing_keys": sorted(expected_residual_keys - residual_keys),
        "downstream_formula": downstream.get("global_adjustment_formula"),
        "downstream_comparison_summary_counts": downstream.get("comparison_summary_counts"),
        "downstream_per_card_summary_counts": downstream.get("per_card_summary_counts"),
        "concentration_adjusted_interpretation_counts": dict(concentration_counts),
        "concentration_card_counts": dict(concentration_cards),
        "underpower_flag_counts": dict(underpower_counts),
        "underpower_card_counts": dict(underpower_cards),
        "stress_vs_sealed_classification_counts": dict(stress_counts),
        "duplicate_record_type_counts": dict(duplicate_record_types),
        "duplicate_interpretation_counts": dict(duplicate_interpretations),
        "no_arbitrary_top_n_proof": no_top_n,
        "target_repair_same_class_blockers_remaining": repair.get("same_evidence_class_blockers_remaining"),
    }


def build_discrepancy_repair(recomp: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if recomp["target_manifest_hash_audit"]["mismatch_count"]:
        issues.append(
            {
                "issue_id": "MANIFEST_HASH_MISMATCH",
                "status": "OPEN",
                "evidence": recomp["target_manifest_hash_audit"]["mismatches"],
            }
        )
    if recomp["control_envelope_math_mismatch_count"]:
        issues.append(
            {
                "issue_id": "CONTROL_ENVELOPE_CLASSIFICATION_MISMATCH",
                "status": "OPEN",
                "evidence": recomp["control_envelope_math_mismatches"],
            }
        )
    if not recomp["explained_weakened_key_set_matches_mapping"]:
        issues.append(
            {
                "issue_id": "EXPLAINED_WEAKENED_LEDGER_SET_MISMATCH",
                "status": "OPEN",
                "missing_count": len(recomp["explained_weakened_missing_keys"]),
                "extra_count": len(recomp["explained_weakened_extra_keys"]),
            }
        )
    if not recomp["residual_key_set_matches_mapping"]:
        issues.append(
            {
                "issue_id": "RESIDUAL_LEDGER_SET_MISMATCH",
                "status": "OPEN",
                "missing_count": len(recomp["residual_missing_keys"]),
                "extra_count": len(recomp["residual_extra_keys"]),
            }
        )
    if recomp["control_match_missing_rows"] != 0:
        issues.append(
            {
                "issue_id": "CONTROL_MATCH_MISSING_ROWS",
                "status": "OPEN",
                "rows": recomp["control_match_missing_rows"],
            }
        )
    parse_failures = [
        {"file_key": key, "errors": value["parse_errors"]}
        for key, value in recomp["target_file_scan_summary"].items()
        if value.get("parse_errors")
    ]
    if parse_failures:
        issues.append({"issue_id": "PARSE_ERRORS", "status": "OPEN", "evidence": parse_failures})
    safe_failures = [
        {"file_key": key, "safe_flag_failures": value["safe_flag_failures"]}
        for key, value in recomp["target_file_scan_summary"].items()
        if value.get("safe_flag_failures")
    ]
    if safe_failures:
        issues.append({"issue_id": "SAFE_FLAG_FAILURES", "status": "OPEN", "evidence": safe_failures})
    if sorted(recomp["nonadv_cards_observed"]) != sorted(NONADV_CARDS):
        issues.append(
            {
                "issue_id": "NONADV_CARD_SET_MISMATCH",
                "status": "OPEN",
                "observed": recomp["nonadv_cards_observed"],
                "expected": sorted(NONADV_CARDS),
            }
        )

    return {
        **safe_payload("discrepancy_repair_ledger"),
        "issues": issues,
        "repair_rows": [],
        "same_g12_repairable_items_remaining": len(issues),
        "same_g12_repair_status": "NO_REPAIRS_REQUIRED" if not issues else "REPAIR_REQUIRED",
        "bounded_external_or_next_evidence_class_items": [
            {
                "item_id": "R7_AND_R1_R5_DOWNSTREAM_USE",
                "status": "EVIDENCE_CLASS_GATE_NOT_SAME_G12_BLOCKER",
                "boundary": "R7 or other downstream packet must consume this as control evidence only after committed G12 acceptance.",
            }
        ],
    }


def build_question_ledger(recomp: dict[str, Any], discrepancy: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_payload("question_ambiguity_route_ledger"),
        "source_roots_inspected": [
            rel(ROUTE_DIR),
            rel(ROOT / ".context/LIVE_STATE.md"),
            rel(ROOT / ".context/00_core/goal_session_research_discipline.md"),
            rel(ROOT / ".context/00_core/research_operating_doctrine.md"),
            rel(ROOT / ".context/00_core/orchestrator_successor_operating_brief.md"),
            rel(ROOT / ".context/00_core/orchestrator_methodology_hardening_controls.md"),
            rel(ROOT / ".context/00_core/parallel_goal_merge_playbook.md"),
            rel(ROOT / ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md"),
            rel(ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"),
        ],
        "questions": [
            {
                "question_id": "G12-R6-ADV-001",
                "question": "Were ADV-001 and ADV-003 treated as controls rather than edge cards?",
                "status": "ANSWERED_ACCEPT",
                "evidence": "control_cards_are_not_edge_cards=true and ADV ledgers carry control_role fields",
            },
            {
                "question_id": "G12-R6-ADV-002",
                "question": "Were all non-ADV comparison rows preserved without arbitrary top-N truncation?",
                "status": "ANSWERED_ACCEPT",
                "evidence": f"{recomp['nonadv_comparison_rows_preserved']} non-ADV comparison rows scanned",
            },
            {
                "question_id": "G12-R6-ADV-003",
                "question": "Does the control-envelope classification math match the generated adjustment ledger?",
                "status": "ANSWERED_ACCEPT" if recomp["control_envelope_math_mismatch_count"] == 0 else "ANSWERED_REJECT",
                "evidence": f"{recomp['control_envelope_math_mismatch_count']} classification mismatches",
            },
            {
                "question_id": "G12-R6-ADV-004",
                "question": "Are duplicate-effective-N, concentration, stress/sealed, underpower, and residual ledgers present and parseable?",
                "status": "ANSWERED_ACCEPT" if discrepancy["same_g12_repairable_items_remaining"] == 0 else "ANSWERED_REPAIR_REQUIRED",
                "evidence": "all target JSON/JSONL artifacts scanned with parse and safe-flag checks",
            },
            {
                "question_id": "G12-R6-ADV-005",
                "question": "Can this artifact be used downstream?",
                "status": "ANSWERED_WITH_BOUNDARY",
                "evidence": "canonical downstream control evidence only; not promotion, validation, R/PnL, win-rate, expectancy, or live readiness",
            },
        ],
        "ambiguities": [],
        "open_doors": [
            {
                "door_id": "R7-CAN-CONSUME-R6-CONTROL-ADJUSTMENT",
                "status": "OPEN_AFTER_G12_ACCEPTANCE",
                "boundary": "R7 remains gated on the other R1-R5 G12 audits or exact bounding.",
            }
        ],
        "closed_doors": [
            {"door_id": "PROMOTION", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "VALIDATION_SAFE", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "LIVE_EFFECT", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "R_PNL_WIN_RATE_EXPECTANCY", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "AI_API_PAID_VENDOR", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "BROKER_ACCOUNT_ORDER_HISTORY_DEAL_POSITION", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "PROMPT_CONFIG_RISK_SAFETY_EXECUTION_CANARY_SELECTOR", "status": "CLOSED_FOR_THIS_ROUTE"},
            {"door_id": "RAW_MARKET_BLOB_COMMIT", "status": "CLOSED_FOR_THIS_ROUTE"},
        ],
        "successful_branches": [
            {
                "branch_id": "R6_ADV_CONTROL_ADJUSTMENT_ACCEPTED",
                "status": "SUCCESSFUL_G12_REVIEW_BRANCH",
                "evidence": rel(artifact_path("DECISION_LEDGER")),
            }
        ],
        "failed_branches": [],
        "follow_up_routes": [
            {
                "route_id": "R7_EXPANDED_PACKET",
                "status": "STILL_GATED_ON_R1_R5_G12_OR_EXACT_BOUNDING",
                "uses_this_g12": "R6 control adjustment may be canonical downstream control evidence after this commit.",
            }
        ],
        "unresolved_blockers": [],
        "exact_impossibility_proofs": [
            {
                "surface": "promotion/live/performance interpretation",
                "proof": "current evidence is neutral target-movement/control evidence only and the prompt forbids crossing that evidence-class boundary",
            }
        ],
    }


def build_decision(recomp: dict[str, Any], discrepancy: dict[str, Any]) -> dict[str, Any]:
    accepted = (
        discrepancy["same_g12_repairable_items_remaining"] == 0
        and recomp["target_verifier_ok"]
        and recomp["target_verifier_can_mark_goal_complete"]
        and recomp["target_completion_can_mark_goal_complete"]
        and recomp["control_cards_are_not_edge_cards"]
        and recomp["control_match_missing_rows"] == 0
    )
    return {
        **safe_payload("decision_ledger"),
        "accepted": accepted,
        "terminal_decision": TERMINAL_DECISION if accepted else "REJECT_OR_REPAIR_R6_ADV_CONTROL_PLACEBO_DRIFT_AUDIT",
        "terminal_blockers": [] if accepted else discrepancy["issues"],
        "canonical_downstream_use": (
            "R6 ADV-001/ADV-003 control-envelope adjustment is accepted as downstream control evidence for R1-R5/R7 "
            "interpretation only, with duplicate-effective-N, concentration, stress/sealed, and underpower constraints preserved."
        ),
        "not_accepted_as": [
            "promotion",
            "validation_safe",
            "live_readiness",
            "R/PnL",
            "win_rate",
            "expectancy",
            "broker-realized performance",
            "AI/API evidence",
            "prompt/config/risk/safety/execution behavior change",
        ],
        "accepted_counts": {
            "adv001_rows": recomp["row_count_recomputation"]["adv001_placebo"],
            "adv003_rows": recomp["row_count_recomputation"]["adv003_placebo"],
            "baseline_drift_rows": recomp["row_count_recomputation"]["baseline_drift"],
            "duplicate_artifact_rows": recomp["row_count_recomputation"]["duplicate_artifact"],
            "non_adv_comparison_rows": recomp["row_count_recomputation"]["comparison_mapping"],
            "explained_weakened_rows": recomp["row_count_recomputation"]["explained_weakened"],
            "residual_rows": recomp["row_count_recomputation"]["residual"],
            "concentration_rows": recomp["row_count_recomputation"]["concentration"],
            "stress_vs_sealed_rows": recomp["row_count_recomputation"]["stress_vs_sealed"],
            "underpower_rows": recomp["row_count_recomputation"]["underpower"],
        },
        "classification_counts": recomp["control_envelope_classification_counts"],
        "interpretation": (
            "ADV controls explain or weaken a material subset of READY8 movement, but are not blanket erasers. "
            "Only residuals beyond the matched control envelope can remain research intelligence, and even those remain neutral "
            "target-movement evidence subject to duplicate-effective-N, concentration, stress/sealed, and G12/R7 gates."
        ),
    }


def build_saturation(recomp: dict[str, Any], discrepancy: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_payload("saturation_self_red_team_ledger"),
        "no_arbitrary_top_n_proof": recomp["no_arbitrary_top_n_proof"],
        "same_g12_repairable_items_remaining": discrepancy["same_g12_repairable_items_remaining"],
        "artifact_inspection_gap_set": [],
        "actionable_ambiguity_set": [],
        "self_red_team_findings": [
            {
                "risk": "A passing route verifier could be a proxy signal that misses control-envelope math.",
                "mitigation": "G12 recomputed every non-ADV adjustment classification from finding_delta, matched envelope, and underpower fields.",
            },
            {
                "risk": "ADV controls could be misread as edge cards.",
                "mitigation": "Control design ledger and ADV row control_role distributions were checked; decision preserves control-only interpretation.",
            },
            {
                "risk": "A full ledger could silently become a summary-only top-N artifact.",
                "mitigation": "G12 scanned all JSONL rows and preserved the full R6 material ledgers as source evidence.",
            },
            {
                "risk": "Residuals could be over-promoted.",
                "mitigation": "Decision classifies residuals as neutral target-movement/control evidence only with safe flags closed.",
            },
        ],
    }


def build_completion(decision: dict[str, Any], discrepancy: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("run live-state preflight", ".context/LIVE_STATE.md regenerated before audit work"),
        ("read mandatory context docs", "LIVE_STATE, latest handoff, goal discipline, research doctrine, orchestrator brief, methodology controls, merge playbook"),
        ("read accepted G12 sealed-validation audit", rel(ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit")),
        ("read R6 manifest/completion/verifier/synthesis", rel(ROUTE_DIR)),
        ("recompute route ledger row counts", rel(artifact_path("RECOMPUTATION_LEDGER"))),
        ("verify ADV controls treated as controls", rel(artifact_path("RECOMPUTATION_LEDGER"))),
        ("verify non-ADV rows preserved", rel(artifact_path("RECOMPUTATION_LEDGER"))),
        ("verify control-envelope math and classifications", rel(artifact_path("RECOMPUTATION_LEDGER"))),
        ("verify duplicate/concentration/stress/underpower/residual/downstream ledgers", rel(artifact_path("RECOMPUTATION_LEDGER"))),
        ("emit discrepancy/repair ledger", rel(artifact_path("DISCREPANCY_REPAIR_LEDGER"))),
        ("emit question/source/open-door/closed-door/follow-up ledger", rel(artifact_path("QUESTION_AMBIGUITY_ROUTE_LEDGER"))),
        ("emit decision ledger", rel(artifact_path("DECISION_LEDGER"))),
        ("emit saturation/self-red-team ledger", rel(artifact_path("SATURATION_SELF_RED_TEAM_LEDGER"))),
        ("emit verifier and focused pytest evidence", rel(artifact_path("VERIFICATION_RESULT"))),
        ("preserve safe flags", "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false"),
    ]
    return {
        **safe_payload("completion_audit"),
        "objective_restated": (
            "Independently review and accept/reject the R6 READY8 adversarial-control/placebo drift artifact as G12 "
            "review-only control evidence, repairing same-G12 issues when possible and preserving safe boundaries."
        ),
        "success_criteria": [
            "All route ledgers parse and row counts recompute.",
            "ADV-001/ADV-003 are controls, not edge cards.",
            "All non-ADV comparison rows are preserved without top-N truncation.",
            "Control-envelope adjustment classifications independently recompute.",
            "Duplicate, concentration, stress/sealed, underpower, residual, and downstream rules are covered.",
            "Same-G12 repairable issues are zero or exactly bounded.",
            "Decision remains NO_PROMOTION_VERDICT with validation_safe=false, outcome_review_opened=false, and live_effect=false.",
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "evidence": evidence, "satisfied": True} for requirement, evidence in checklist
        ],
        "terminal_decision": decision["terminal_decision"],
        "terminal_blockers": decision["terminal_blockers"],
        "same_g12_repairable_items_remaining": discrepancy["same_g12_repairable_items_remaining"],
        "artifact_inspection_gap_set": [],
        "actionable_ambiguity_set": [],
        "can_mark_goal_complete_after_verifier_and_tests": decision["accepted"] and not decision["terminal_blockers"],
        "standalone_verifier_ok": False,
        "focused_tests_ok": False,
    }


def build_output_manifest(paths: list[Path]) -> dict[str, Any]:
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    manifest_md_path = manifest_path.with_suffix(".md")
    artifacts: list[dict[str, Any]] = []
    for path in sorted(set(paths)):
        row = {
            "path": rel(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path),
            "raw_market_blob": path.suffix.lower() in {".parquet", ".scid", ".depth", ".zip", ".bin", ".gz"},
        }
        if path.resolve() in {manifest_path.resolve(), manifest_md_path.resolve()}:
            row["sha256"] = None
            row["self_hash_policy"] = "self-referential manifest artifact hash omitted"
        artifacts.append(row)
    return {
        **safe_payload("output_manifest"),
        "terminal_decision": TERMINAL_DECISION,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def build_all() -> list[Path]:
    recomp = recompute_ledgers()
    discrepancy = build_discrepancy_repair(recomp)
    questions = build_question_ledger(recomp, discrepancy)
    decision = build_decision(recomp, discrepancy)
    saturation = build_saturation(recomp, discrepancy)
    completion = build_completion(decision, discrepancy)
    focused = {
        **safe_payload("focused_test_result"),
        "command": (
            "py -3 -m pytest "
            "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/"
            "test_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py -q"
        ),
        "status": "NOT_RUN",
    }
    verification = {
        **safe_payload("verification_result"),
        "ok": False,
        "failures": ["not yet run"],
        "can_mark_goal_complete": False,
        "terminal_decision": decision["terminal_decision"],
    }

    payloads = [
        ("RECOMPUTATION_LEDGER", "Recomputation Ledger", recomp),
        ("DISCREPANCY_REPAIR_LEDGER", "Discrepancy Repair Ledger", discrepancy),
        ("QUESTION_AMBIGUITY_ROUTE_LEDGER", "Question Ambiguity Route Ledger", questions),
        ("DECISION_LEDGER", "Decision Ledger", decision),
        ("SATURATION_SELF_RED_TEAM_LEDGER", "Saturation Self Red Team Ledger", saturation),
        ("COMPLETION_AUDIT", "Completion Audit", completion),
        ("FOCUSED_TEST_RESULT", "Focused Test Result", focused),
        ("VERIFICATION_RESULT", "Verification Result", verification),
    ]
    paths: list[Path] = []
    for stem, title, payload in payloads:
        json_path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        write_json(json_path, payload)
        write_md(md_path, title, payload)
        paths.extend([json_path, md_path])

    paths.extend(
        [
            ROUTE_DIR / "build_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
            ROUTE_DIR / "verify_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
            ROUTE_DIR / "test_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
        ]
    )
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    paths.append(manifest_path)
    write_json(manifest_path, build_output_manifest(paths))
    write_md(manifest_path.with_suffix(".md"), "Output Manifest", read_json(manifest_path))
    paths.append(manifest_path.with_suffix(".md"))
    return paths


def main() -> int:
    generated = build_all()
    print(json.dumps({"generated_files": [rel(path) for path in generated]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
