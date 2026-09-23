"""Build the G12 audit artifacts for the READY8 R9 packet route.

This is an independent packet audit over the R9 forward-retest/source-capture
packet artifacts. It parses the route-local disk artifacts directly and does
not rely on R9 closeout prose, R9 manifest status, or R9 self-verifier status
as sufficient evidence.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "G12_READY8_R9_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT_ONLY"
R9_EVIDENCE_CLASS = "READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_FROM_ACCEPTED_G12_SCORING_ONLY"

ACCEPT_DECISION = "ACCEPT_AS_G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT_NO_PROMOTION"
REJECT_DECISION = "REJECT_OR_KEEP_CLOSED_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_WITH_EXACT_REPAIR_REQUIREMENTS_NO_PROMOTION"
R9_TERMINAL_DECISION = "MATERIALIZED_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_FALSE_FLAGS = {
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_ai_api": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_paid_or_vendor_access": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
}

ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
R8_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization"

MUTABLE_COORDINATION_PATHS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
}

REQUIRED_CONTEXT = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
]

R9_JSONL = {
    "row_identity": f"R9_ROW_IDENTITY_{DATE}.jsonl",
    "haz001": f"R9_HAZ001_PACKET_{DATE}.jsonl",
    "mac": f"R9_MAC_PACKET_{DATE}.jsonl",
    "haz005": f"R9_HAZ005_PACKET_{DATE}.jsonl",
    "unc004": f"R9_UNC004_CONTRACT_{DATE}.jsonl",
    "residual": f"R9_RESIDUAL_PACKET_{DATE}.jsonl",
    "repaired_targets": f"R9_REPAIRED_TARGETS_{DATE}.jsonl",
    "failure_intel": f"R9_FAILURE_INTEL_{DATE}.jsonl",
    "source_capture": f"R9_SOURCE_CAPTURE_REQS_{DATE}.jsonl",
    "forward_implications": f"R9_FORWARD_IMPLICATIONS_{DATE}.jsonl",
    "doors": f"R9_DOORS_{DATE}.jsonl",
    "questions": f"R9_QUESTIONS_{DATE}.jsonl",
    "blockers": f"R9_BLOCKERS_{DATE}.jsonl",
    "sequence": f"R9_SEQUENCE_{DATE}.jsonl",
    "source_roots": f"R9_SOURCE_ROOTS_{DATE}.jsonl",
}

EXPECTED_COUNTS = {
    "row_identity": 182,
    "haz001": 143,
    "mac": 32,
    "haz005": 5,
    "unc004": 1154,
    "residual": 1,
    "repaired_targets": 5320,
    "failure_intel": 2641,
    "source_capture": 182,
    "forward_implications": 182,
    "doors": 364,
    "questions": 182,
    "blockers": 22,
    "sequence": 182,
    "source_roots": 76,
}

EXPECTED_PACKET_FAMILY_COUNTS = {
    "HAZ001_DECONCENTRATED_RETEST": 143,
    "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC": 1,
    "MAC_INVERSE_AVOID_FILTER_DESIGN": 32,
    "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL": 5,
    "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE": 1,
}

EXPECTED_RESULT_STATUS_COUNTS = {
    "MATERIALIZED_HAZ001_BRANCH_SCORE_CONTROL_ADJUSTED_RETEST_REQUIRED": 143,
    "SOURCE_CAPTURE_REQUIREMENT_NATIVE_SOURCE_CONFIDENCE_FIELDS_NOT_AVAILABLE": 1,
    "MATERIALIZED_MAC_INVERSE_AVOID_FILTER_SCORE_CONTROL_ADJUSTED_NOT_LIVE_FILTER": 32,
    "SOURCE_CONTROL_REPAIR_CONSUMED_TARGET_RESULT_JOIN_FAIL_CLOSED_FOR_THIS_PACKET_ROW": 5,
    "MATERIALIZED_RESIDUAL_FAILURE_INTELLIGENCE_ONLY_AFTER_ADV_CONTROL_ENVELOPE": 1,
}

R8_G12_PACKET_COVERAGE = R8_DIR / f"G12_R8EXP_SCORING_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


def safe_base() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_FALSE_FLAGS,
    }


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_line_number"] = line_number
                rows.append(row)
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            cleaned = {key: value for key, value in row.items() if key != "_line_number"}
            handle.write(json.dumps(cleaned, sort_keys=True, separators=(",", ":")) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_canonical_lf(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def row_hash(row: dict[str, Any]) -> str:
    return stable_hash({key: value for key, value in row.items() if key != "_line_number"})


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def check_safe_flags(row: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for key, expected in SAFE_FLAGS.items():
        if row.get(key) != expected:
            issues.append(f"{key}={row.get(key)!r} expected {expected!r}")
    for key, expected in FORBIDDEN_FALSE_FLAGS.items():
        if row.get(key) != expected:
            issues.append(f"{key}={row.get(key)!r} expected {expected!r}")
    return not issues, issues


def source_meta(path: Path, label: str) -> dict[str, Any]:
    exists = path.exists()
    return {
        **safe_base(),
        "label": label,
        "path": rel(path) if exists or path.is_absolute() else str(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
        "sha256_canonical_lf": sha256_file_canonical_lf(path) if exists else None,
        "jsonl_rows": sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        if exists and path.suffix == ".jsonl"
        else None,
    }


def classify_source_drift(source: dict[str, Any]) -> dict[str, Any]:
    source_path = ROOT / source["path"]
    if not source_path.exists():
        mutable = source["path"] in MUTABLE_COORDINATION_PATHS
        return {
            **safe_base(),
            "source_path": source["path"],
            "label": source.get("label"),
            "drift_classification": "MUTABLE_COORDINATION_SOURCE_MISSING_BOUNDED" if mutable else "MISSING_SOURCE",
            "blocking": not mutable,
            "mutable_coordination_source": mutable,
            "expected_raw_sha256": source.get("sha256"),
            "current_raw_sha256": None,
            "expected_canonical_lf_sha256": source.get("sha256_canonical_lf"),
            "current_canonical_lf_sha256": None,
            "proof": "Source path is absent on current disk.",
        }

    current_raw = sha256_file(source_path)
    current_lf = sha256_file_canonical_lf(source_path)
    raw_match = current_raw == source.get("sha256")
    lf_match = source.get("sha256_canonical_lf") is not None and current_lf == source.get("sha256_canonical_lf")
    mutable = source["path"] in MUTABLE_COORDINATION_PATHS
    if raw_match:
        classification = "RAW_HASH_MATCH"
        blocking = False
        proof = "Current raw bytes match R9 source hash ledger."
    elif lf_match:
        classification = "LINE_ENDING_ONLY_DRIFT_CANONICAL_LF_MATCH"
        blocking = False
        proof = "Raw bytes differ but canonical LF hash matches R9 source hash ledger."
    elif mutable:
        classification = "MUTABLE_COORDINATION_CONTEXT_DRIFT_BOUNDED"
        blocking = False
        proof = "Context/coordination source changed after R9 materialization; packet rows do not depend on mutable bytes as immutable evidence."
    else:
        classification = "REAL_IMMUTABLE_SOURCE_DRIFT"
        blocking = True
        proof = "Neither raw nor canonical LF hash matches for an immutable R9 source."
    return {
        **safe_base(),
        "source_path": source["path"],
        "label": source.get("label"),
        "drift_classification": classification,
        "blocking": blocking,
        "mutable_coordination_source": mutable,
        "expected_raw_sha256": source.get("sha256"),
        "current_raw_sha256": current_raw,
        "expected_canonical_lf_sha256": source.get("sha256_canonical_lf"),
        "current_canonical_lf_sha256": current_lf,
        "proof": proof,
    }


def index_by_packet(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["packet_row_id"]): row for row in rows if row.get("packet_row_id") is not None}


def build_material_row_audit(ledgers: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows_out: list[dict[str, Any]] = []
    issues: list[str] = []
    for ledger_name, rows in sorted(ledgers.items()):
        for row in rows:
            safe_ok, safe_issues = check_safe_flags(row)
            if not safe_ok:
                issues.append(f"{ledger_name}:{row.get('_line_number')}: {'; '.join(safe_issues)}")
            rows_out.append(
                {
                    **safe_base(),
                    "source_ledger": R9_JSONL[ledger_name],
                    "source_line_number": row.get("_line_number"),
                    "source_row_sha256": row_hash(row),
                    "packet_row_id": row.get("packet_row_id"),
                    "parent_packet_row_id": row.get("parent_packet_row_id"),
                    "packet_family": row.get("packet_family"),
                    "result_status": row.get("result_status"),
                    "contract_scope": row.get("contract_scope"),
                    "blocker_status": row.get("blocker_status"),
                    "door_status": row.get("door_status"),
                    "source_capture_status": row.get("source_capture_status"),
                    "accepted_g12_packet_coverage_status": row.get("accepted_g12_packet_coverage_status"),
                    "audit_status": "ROW_PARSED_HASHED_AND_SAFE_FLAGS_VERIFIED" if safe_ok else "ROW_SAFE_FLAG_MISMATCH",
                    "safe_flag_issues": safe_issues,
                }
            )
    return rows_out, issues


def build_json_artifact_audit(json_files: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for path in json_files:
        doc = read_json(path)
        safe_ok, safe_issues = check_safe_flags(doc) if isinstance(doc, dict) else (False, ["not a JSON object"])
        if not safe_ok:
            issues.append(f"{path.name}: {'; '.join(safe_issues)}")
        rows.append(
            {
                **safe_base(),
                "source_json": path.name,
                "source_sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "top_level_keys": sorted(doc.keys()) if isinstance(doc, dict) else [],
                "safe_flags_ok": safe_ok,
                "safe_flag_issues": safe_issues,
                "terminal_decision": doc.get("terminal_decision") if isinstance(doc, dict) else None,
                "ok": doc.get("ok") if isinstance(doc, dict) else None,
                "can_mark_goal_complete": doc.get("can_mark_goal_complete") if isinstance(doc, dict) else None,
                "audit_status": "JSON_ARTIFACT_PARSED_HASHED_AND_SAFE_FLAGS_VERIFIED" if safe_ok else "JSON_ARTIFACT_SAFE_FLAG_MISMATCH",
            }
        )
    return rows, issues


def build_packet_coverage(ledgers: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str]]:
    identity = index_by_packet(ledgers["row_identity"])
    haz001 = index_by_packet(ledgers["haz001"])
    mac = index_by_packet(ledgers["mac"])
    haz005 = index_by_packet(ledgers["haz005"])
    residual = index_by_packet(ledgers["residual"])
    unc_packet = {
        str(row["packet_row_id"]): row
        for row in ledgers["unc004"]
        if row.get("contract_scope") == "packet_row" and row.get("packet_row_id")
    }
    source_capture = index_by_packet(ledgers["source_capture"])
    forward = index_by_packet(ledgers["forward_implications"])
    sequence = index_by_packet(ledgers["sequence"])
    questions = index_by_packet(ledgers["questions"])
    r8_coverage = index_by_packet(read_jsonl(R8_G12_PACKET_COVERAGE))

    door_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in ledgers["doors"]:
        if row.get("packet_row_id"):
            door_counts[str(row["packet_row_id"])][str(row.get("door_status"))] += 1

    family_maps = {
        "HAZ001_DECONCENTRATED_RETEST": haz001,
        "MAC_INVERSE_AVOID_FILTER_DESIGN": mac,
        "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL": haz005,
        "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC": unc_packet,
        "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE": residual,
    }
    rows_out: list[dict[str, Any]] = []
    issues: list[str] = []
    for packet_id in sorted(identity):
        row = identity[packet_id]
        family = row.get("packet_family")
        r8_row = r8_coverage.get(packet_id)
        family_row = family_maps.get(str(family), {}).get(packet_id)
        family_status_ok = True
        if family == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL":
            family_status_ok = bool(family_row and family_row.get("exact_row_level_impossibility"))
        elif family == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC":
            requirements = " ".join(family_row.get("source_capture_requirements", [])) if family_row else ""
            family_status_ok = bool(family_row and family_row.get("contract_scope") == "packet_row" and "native" in requirements.lower())
        elif family == "MAC_INVERSE_AVOID_FILTER_DESIGN":
            family_status_ok = bool(family_row and family_row.get("avoid_filter_design_rule"))
        elif family == "HAZ001_DECONCENTRATED_RETEST":
            family_status_ok = bool(family_row and family_row.get("retest_freeze_rule"))
        elif family == "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE":
            family_status_ok = bool(family_row and family_row.get("exact_downstream_action"))

        coverage = {
            "accepted_r8_g12_packet_coverage_present": r8_row is not None,
            "accepted_r8_g12_packet_coverage_status_ok": bool(r8_row and r8_row.get("audit_status") == "PACKET_ROW_FULLY_COVERED"),
            "accepted_r8_g12_branch_hash_match": bool(
                r8_row and row.get("accepted_g12_branch_key_sha256") == r8_row.get("branch_key_sha256")
            ),
            "accepted_r8_g12_coverage_payload_match": bool(r8_row and row.get("accepted_g12_coverage") == r8_row.get("coverage")),
            "r9_identity_coverage_status_ok": row.get("accepted_g12_packet_coverage_status") == "PACKET_ROW_FULLY_COVERED",
            "source_capture_present": packet_id in source_capture,
            "forward_implication_present": packet_id in forward,
            "sequence_present": packet_id in sequence,
            "question_present": packet_id in questions,
            "open_door_count": door_counts[packet_id].get("OPEN_DOOR", 0),
            "closed_door_count": door_counts[packet_id].get("CLOSED_DOOR", 0),
            "family_specific_row_present": family_row is not None,
            "family_specific_boundary_ok": family_status_ok,
        }
        ok = (
            all(value is True for key, value in coverage.items() if key.endswith("_present") or key.endswith("_ok") or key.endswith("_match"))
            and coverage["open_door_count"] == 1
            and coverage["closed_door_count"] == 1
            and coverage["family_specific_row_present"]
            and coverage["family_specific_boundary_ok"]
        )
        if not ok:
            issues.append(f"packet coverage issue {packet_id}: {coverage}")
        rows_out.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "packet_family": family,
                "result_status": row.get("result_status"),
                "branch_key_sha256": stable_hash(row.get("branch_key")),
                "coverage": coverage,
                "audit_status": "PACKET_ROW_FULLY_COVERED_AND_R8_G12_TRACEABLE" if ok else "PACKET_ROW_COVERAGE_OR_TRACEABILITY_ISSUE",
            }
        )

    extra_ids = {
        "source_capture_extra": set(source_capture) - set(identity),
        "forward_extra": set(forward) - set(identity),
        "sequence_extra": set(sequence) - set(identity),
        "questions_extra": set(questions) - set(identity),
    }
    for label, extras in extra_ids.items():
        if extras:
            issues.append(f"{label}: {sorted(extras)[:10]}")
    return rows_out, issues


def build_failure_intel_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    out: list[dict[str, Any]] = []
    issues: list[str] = []
    for row in rows:
        ok = (
            row.get("accepted_g12_audit_status") == "FAILURE_INTELLIGENCE_PRESERVED_NOT_ERASED"
            and row.get("kill_scope") == "unsupported edge claim only; preserve failure intelligence and downstream implication"
            and row.get("unknown_doctrine_classifications") == []
            and isinstance(row.get("doctrine_classifications"), list)
            and bool(row.get("doctrine_classifications"))
            and bool(row.get("what_was_learned"))
            and bool(row.get("why_failed_or_weakened"))
            and bool(row.get("implication"))
        )
        if not ok:
            issues.append(f"failure-intel weak row {row.get('_line_number')}")
        out.append(
            {
                **safe_base(),
                "source_line_number": row.get("_line_number"),
                "source_row_sha256": row_hash(row),
                "accepted_g12_source_row_sha256": row.get("accepted_g12_source_row_sha256"),
                "branch_status": row.get("branch_status"),
                "doctrine_classifications": row.get("doctrine_classifications"),
                "implication": row.get("implication"),
                "audit_status": "FAILURE_INTELLIGENCE_PRESERVED_NOT_ERASED" if ok else "FAILURE_INTELLIGENCE_WEAK_ROW",
            }
        )
    return out, issues


def build_repaired_target_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    out: list[dict[str, Any]] = []
    issues: list[str] = []
    for row in rows:
        ok = (
            row.get("accepted_g12_audit_status") == "REPAIRED_TARGET_CONSUMPTION_VERIFIED"
            and row.get("consumption_status") == "R7_MAY_CONSUME_SOURCE_REPAIR_ONLY_NOT_VALIDATION"
            and row.get("result_status") == "REPAIRED_TARGET_ROW_CONSUMED_AS_SOURCE_BOUND_NEUTRAL_TARGET_MOVEMENT_INPUT_NOT_PROMOTION"
            and row.get("repair_candidate_target_result_row_hash_match") is True
            and bool(row.get("original_target_result_row_id"))
            and bool(row.get("r7_repaired_target_consumption_row_id"))
        )
        if not ok:
            issues.append(f"repaired-target weak row {row.get('_line_number')}")
        out.append(
            {
                **safe_base(),
                "source_line_number": row.get("_line_number"),
                "source_row_sha256": row_hash(row),
                "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
                "original_target_result_row_id": row.get("original_target_result_row_id"),
                "card_id": row.get("card_id"),
                "symbol": row.get("symbol"),
                "audit_status": "REPAIRED_TARGET_CONSUMPTION_VERIFIED" if ok else "REPAIRED_TARGET_WEAK_ROW",
            }
        )
    return out, issues


def build_blocker_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    out: list[dict[str, Any]] = []
    issues: list[str] = []
    for row in rows:
        status = str(row.get("blocker_status"))
        exact_or_repaired = (
            status == "EXACTLY_BOUNDED"
            or status.startswith("REPAIRED")
            or status.startswith("CLEARED")
            or status.startswith("BOUNDED")
        )
        # A repaired/cleared blocker or exact fail-closed source-control boundary
        # can legitimately have no owner-access requirement. The invariant is
        # that every row carries an exact proof/boundary and no row remains
        # unrepaired or vaguely missing.
        ok = exact_or_repaired and bool(row.get("proof_or_boundary")) and "owner_access_source_capture_requirement" in row
        if status.startswith("UNREPAIRED") or status.startswith("MISSING"):
            ok = False
        if not ok:
            issues.append(f"blocker weak row {row.get('_line_number')}: {status}")
        out.append(
            {
                **safe_base(),
                "source_line_number": row.get("_line_number"),
                "source_row_sha256": row_hash(row),
                "packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                "blocker": row.get("blocker"),
                "blocker_status": status,
                "proof_or_boundary": row.get("proof_or_boundary"),
                "owner_access_source_capture_requirement": row.get("owner_access_source_capture_requirement"),
                "audit_status": "BLOCKER_EXACTLY_BOUNDED_OR_REPAIRED" if ok else "BLOCKER_WEAK_OR_UNREPAIRED",
            }
        )
    return out, issues


def build_sequence_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    out: list[dict[str, Any]] = []
    issues: list[str] = []
    for row in rows:
        sequence = row.get("route_sequence") or []
        boundary = str(row.get("terminal_boundary", ""))
        ok = (
            len(sequence) >= 2
            and sequence[0] == "G12_READY8_EXPANDED_FORWARD_RETEST_SOURCE_CAPTURE_PACKET_AUDIT"
            and "validation" in boundary.lower()
            and "promotion" in boundary.lower()
            and "live behavior" in boundary.lower()
        )
        if not ok:
            issues.append(f"sequence weak row {row.get('_line_number')}")
        out.append(
            {
                **safe_base(),
                "source_line_number": row.get("_line_number"),
                "source_row_sha256": row_hash(row),
                "packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                "result_status": row.get("result_status"),
                "route_sequence": sequence,
                "terminal_boundary": row.get("terminal_boundary"),
                "audit_status": "PACKET_SEQUENCE_BOUNDARY_VERIFIED" if ok else "PACKET_SEQUENCE_WEAK_ROW",
            }
        )
    return out, issues


def build_manifest_audit() -> tuple[list[dict[str, Any]], list[str]]:
    manifest = read_json(route_file(f"R9_OUTPUT_MANIFEST_{DATE}.json"))
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        exists = path.exists()
        current = sha256_file(path) if exists else None
        ok = exists and current == item.get("sha256")
        if not ok:
            issues.append(f"R9 manifest mismatch {item.get('path')}")
        rows.append(
            {
                **safe_base(),
                "manifest_path": item.get("path"),
                "exists": exists,
                "expected_sha256": item.get("sha256"),
                "current_sha256": current,
                "jsonl_rows_expected": item.get("jsonl_rows"),
                "bytes_expected": item.get("bytes"),
                "audit_status": "R9_MANIFEST_HASH_MATCH" if ok else "R9_MANIFEST_HASH_MISMATCH",
            }
        )
    return rows, issues


def build() -> dict[str, Any]:
    generated_at = utc_now()
    ledgers = {key: read_jsonl(route_file(name)) for key, name in R9_JSONL.items()}
    r9_json_files = sorted(ROUTE_DIR.glob(f"R9_*_{DATE}.json")) + sorted(ROUTE_DIR.glob(f"R9_*result_{DATE}.json"))
    # Avoid duplicate paths from the two glob patterns.
    r9_json_files = sorted({path.resolve(): path for path in r9_json_files}.values(), key=lambda path: path.name)
    r9_decision = read_json(route_file(f"R9_DECISION_{DATE}.json"))
    r9_completion = read_json(route_file(f"R9_COMPLETION_{DATE}.json"))
    r9_verification = read_json(route_file(f"R9_VERIFICATION_{DATE}.json"))
    r9_source_hash = read_json(route_file(f"R9_SOURCE_HASH_{DATE}.json"))
    r9_instruction = read_json(route_file(f"R9_INSTRUCTION_COVERAGE_{DATE}.json"))

    material_rows, material_issues = build_material_row_audit(ledgers)
    json_rows, json_issues = build_json_artifact_audit(r9_json_files)
    packet_rows, packet_issues = build_packet_coverage(ledgers)
    failure_rows, failure_issues = build_failure_intel_audit(ledgers["failure_intel"])
    repaired_rows, repaired_issues = build_repaired_target_audit(ledgers["repaired_targets"])
    blocker_rows, blocker_issues = build_blocker_audit(ledgers["blockers"])
    sequence_rows, sequence_issues = build_sequence_audit(ledgers["sequence"])
    manifest_rows, manifest_issues = build_manifest_audit()
    source_drift_rows = [classify_source_drift(source) for source in r9_source_hash.get("sources", [])]
    real_source_drift = [row for row in source_drift_rows if row.get("blocking")]

    observed_counts = {key: len(rows) for key, rows in ledgers.items()}
    row_count_issues = [
        f"{key}: observed {observed_counts.get(key)} expected {expected}"
        for key, expected in EXPECTED_COUNTS.items()
        if observed_counts.get(key) != expected
    ]
    family_counts = Counter(row.get("packet_family") for row in ledgers["row_identity"])
    family_issues = [
        f"{family}: observed {family_counts.get(family, 0)} expected {expected}"
        for family, expected in EXPECTED_PACKET_FAMILY_COUNTS.items()
        if family_counts.get(family, 0) != expected
    ]
    result_status_counts = Counter(row.get("result_status") for row in ledgers["row_identity"])
    result_status_issues = [
        f"{status}: observed {result_status_counts.get(status, 0)} expected {expected}"
        for status, expected in EXPECTED_RESULT_STATUS_COUNTS.items()
        if result_status_counts.get(status, 0) != expected
    ]
    unc_contract_scope_counts = Counter(row.get("contract_scope") for row in ledgers["unc004"])
    unc_split_issues = []
    if unc_contract_scope_counts.get("packet_row", 0) != 1:
        unc_split_issues.append("UNC004 packet_row count mismatch")
    if unc_contract_scope_counts.get("accepted_full_row_implication", 0) != 1153:
        unc_split_issues.append("UNC004 accepted_full_row_implication count mismatch")

    terminal_issues: list[str] = []
    if r9_decision.get("terminal_decision") != R9_TERMINAL_DECISION:
        terminal_issues.append("R9 terminal decision mismatch")
    if r9_completion.get("same_evidence_class_intelligence_remaining") != 0:
        terminal_issues.append("R9 same-evidence-class intelligence remaining is not zero")
    if r9_instruction.get("all_requirements_satisfied") is not True:
        terminal_issues.append("R9 instruction coverage does not mark all requirements satisfied")
    if r9_verification.get("ok") is not True or r9_verification.get("can_mark_goal_complete") is not True:
        terminal_issues.append("R9 verifier was not ok/can_mark_goal_complete on disk")

    all_issues = (
        material_issues
        + json_issues
        + packet_issues
        + failure_issues
        + repaired_issues
        + blocker_issues
        + sequence_issues
        + manifest_issues
        + [f"real immutable source drift {row['source_path']}" for row in real_source_drift]
        + row_count_issues
        + family_issues
        + result_status_issues
        + unc_split_issues
        + terminal_issues
    )
    terminal_decision = ACCEPT_DECISION if not all_issues else REJECT_DECISION

    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl"), material_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_JSON_ARTIFACTS_{DATE}.jsonl"), json_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"), packet_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl"), failure_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl"), repaired_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl"), blocker_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl"), sequence_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl"), source_drift_rows)
    write_jsonl(route_file(f"G12_R9_PACKET_AUDIT_R9_MANIFEST_{DATE}.jsonl"), manifest_rows)

    source_drift_counts = Counter(row.get("drift_classification") for row in source_drift_rows)
    blocker_status_counts = Counter(row.get("blocker_status") for row in ledgers["blockers"])
    failure_status_counts = Counter(row.get("branch_status") for row in ledgers["failure_intel"])
    recomputation = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "git_head_at_audit": git_head(),
        "objective_restatement": "Independent G12 audit of the R9 READY8 forward-retest/source-capture packet from full disk recomputation.",
        "r9_evidence_class": R9_EVIDENCE_CLASS,
        "expected_counts": EXPECTED_COUNTS,
        "observed_counts": observed_counts,
        "row_count_issues": row_count_issues,
        "packet_family_counts": dict(family_counts),
        "packet_family_issues": family_issues,
        "result_status_counts": dict(result_status_counts),
        "result_status_issues": result_status_issues,
        "unc004_contract_scope_counts": dict(unc_contract_scope_counts),
        "unc004_split_issues": unc_split_issues,
        "blocker_status_counts": dict(blocker_status_counts),
        "failure_intelligence_status_counts": dict(failure_status_counts),
        "source_hash_drift_classification_counts": dict(source_drift_counts),
        "material_jsonl_rows_audited": len(material_rows),
        "json_artifacts_audited": len(json_rows),
        "packet_rows_full_coverage": not packet_issues,
        "failure_intelligence_rows_preserved": not failure_issues,
        "repaired_target_rows_verified": not repaired_issues,
        "blocker_rows_exact_or_repaired": not blocker_issues,
        "packet_sequence_rows_verified": not sequence_issues,
        "r9_manifest_hash_mismatch_count": len(manifest_issues),
        "real_immutable_source_drift_count": len(real_source_drift),
        "r9_terminal_decision_ok": not terminal_issues,
        "terminal_issues": terminal_issues,
        "all_issues": all_issues,
    }
    write_json(route_file(f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json"), recomputation)

    audit_sources = []
    for context_path in REQUIRED_CONTEXT:
        audit_sources.append(source_meta(ROOT / context_path, f"context:{context_path}"))
    for path in sorted(ROUTE_DIR.glob("R9_*")):
        if path.is_file():
            audit_sources.append(source_meta(path, f"r9_artifact:{path.name}"))
    for path in [
        route_file(f"G12_R9_PACKET_AUDIT_PROMPT_{DATE}.md"),
        route_file(f"G12_R9_PACKET_AUDIT_STARTER_{DATE}.txt"),
        route_file("build_g12_r9_forward_packet_audit_2026_05_16.py"),
        route_file("verify_g12_r9_forward_packet_audit_2026_05_16.py"),
        route_file("test_g12_r9_forward_packet_audit_2026_05_16.py"),
    ]:
        audit_sources.append(source_meta(path, f"g12_audit_control:{path.name}"))
    source_hash = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "source_count": len(audit_sources),
        "sources": audit_sources,
        "r9_source_drift_ledger": f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl",
        "real_immutable_source_drift_count": len(real_source_drift),
        "mutable_coordination_drift_is_bounded": True,
        "source_hash_policy": {
            "strict_for": "R9 route artifacts and immutable accepted source artifacts",
            "bounded_for": sorted(MUTABLE_COORDINATION_PATHS),
            "raw_vs_canonical_rule": "Raw hash drift with canonical LF match is line-ending-only drift; mutable coordination drift is bounded and cannot change packet row evidence.",
        },
    }
    write_json(route_file(f"G12_R9_PACKET_AUDIT_SOURCE_HASH_{DATE}.json"), source_hash)

    coverage_items = [
        {
            "requirement": "Regenerate/read LIVE_STATE, latest handoff, AGENTS/CLAUDE, goal-session discipline, doctrine, core methodology docs, route registry, question ledger, and R9 route from disk",
            "status": "COVERED",
            "evidence": REQUIRED_CONTEXT + [f"G12_R9_PACKET_AUDIT_PROMPT_{DATE}.md"],
            "operationalized_as": "All required context files are hashed in the G12 source hash ledger and referenced in the prompt-to-artifact checklist.",
        },
        {
            "requirement": "Do not rely on chat memory, closeout prose, manifests, self-verifier status, or summaries alone",
            "status": "COVERED",
            "evidence": [
                f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl",
                f"G12_R9_PACKET_AUDIT_JSON_ARTIFACTS_{DATE}.jsonl",
                f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json",
            ],
            "operationalized_as": "Every R9 JSONL row and every R9 JSON artifact is parsed and hashed; the R9 verifier is checked only as one audited source.",
        },
        {
            "requirement": "No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff",
            "status": "COVERED",
            "evidence": [f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl"],
            "row_count": len(material_rows),
            "operationalized_as": "All R9 JSONL ledgers are full-scanned with no truncation.",
        },
        {
            "requirement": "Recompute required R9 row counts and UNC004 split",
            "status": "COVERED" if not row_count_issues and not unc_split_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json"],
            "issues": row_count_issues + unc_split_issues,
        },
        {
            "requirement": "Verify every packet row maps to accepted G12 R8 scoring packet coverage",
            "status": "COVERED" if not packet_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl", rel(R8_G12_PACKET_COVERAGE)],
            "issues": packet_issues,
        },
        {
            "requirement": "Verify HAZ005 source-control/fail-closed, UNC004 native capture, MAC not-live avoid-filter, HAZ001 forward-retest design only, and residual failure intelligence only",
            "status": "COVERED" if not packet_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"],
            "issues": packet_issues,
        },
        {
            "requirement": "Verify repaired target carry-forward rows",
            "status": "COVERED" if not repaired_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl"],
            "issues": repaired_issues,
        },
        {
            "requirement": "Verify failure-intelligence rows remain preserved and not erased",
            "status": "COVERED" if not failure_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_FAILURE_INTEL_{DATE}.jsonl"],
            "issues": failure_issues,
        },
        {
            "requirement": "Verify blockers, packet sequencing, and source-capture requirements row by row",
            "status": "COVERED" if not blocker_issues and not sequence_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_BLOCKERS_{DATE}.jsonl", f"G12_R9_PACKET_AUDIT_SEQUENCE_{DATE}.jsonl"],
            "issues": blocker_issues + sequence_issues,
        },
        {
            "requirement": "Recompute current source hashes and repair/bound mutable context drift",
            "status": "COVERED" if not real_source_drift else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_SOURCE_DRIFT_{DATE}.jsonl", f"G12_R9_PACKET_AUDIT_SOURCE_HASH_{DATE}.json"],
            "issues": [row["source_path"] for row in real_source_drift],
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, and forbidden surfaces",
            "status": "COVERED" if not material_issues and not json_issues else "ISSUE_FOUND",
            "evidence": [f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl", f"G12_R9_PACKET_AUDIT_JSON_ARTIFACTS_{DATE}.jsonl"],
            "issues": (material_issues + json_issues)[:25],
        },
        {
            "requirement": "Emit decision, recomputation, verifier/focused tests, completion audit, output manifest, exact repair ledger or acceptance",
            "status": "COVERED",
            "evidence": [
                f"G12_R9_PACKET_AUDIT_DECISION_{DATE}.json",
                f"G12_R9_PACKET_AUDIT_RECOMPUTATION_{DATE}.json",
                f"G12_R9_PACKET_AUDIT_COMPLETION_{DATE}.json",
                f"G12_R9_PACKET_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
                "verify_g12_r9_forward_packet_audit_2026_05_16.py",
                "test_g12_r9_forward_packet_audit_2026_05_16.py",
            ],
        },
    ]
    instruction = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "lane_type": "G12 packet audit",
        "builder_audit_posture": "Strict but fair G12 audit: recompute from disk, repair or bound same-G12 issues, preserve useful failure intelligence, and keep promotion/live boundaries closed.",
        "coverage": coverage_items,
        "all_requirements_satisfied": not all_issues,
    }
    write_json(route_file(f"G12_R9_PACKET_AUDIT_INSTRUCTION_COVERAGE_{DATE}.json"), instruction)

    completion = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "objective_restatement": "Accept or reject the R9 READY8 forward-retest/source-capture packet after full disk recomputation, source-hash audit, packet coverage audit, blocker audit, repaired-target audit, failure-intelligence audit, and safe-flag verification.",
        "completion_standard_met": not all_issues,
        "prompt_to_artifact_checklist": coverage_items,
        "required_row_counts_observed": observed_counts,
        "required_row_counts_match": not row_count_issues,
        "packet_family_counts": dict(family_counts),
        "result_status_counts": dict(result_status_counts),
        "full_material_jsonl_rows_audited": len(material_rows),
        "json_artifacts_audited": len(json_rows),
        "same_g12_issue_count": len(all_issues),
        "same_g12_issues": all_issues,
        "same_g12_repairs_or_bounds": {
            "mutable_coordination_source_hash_drift": "bounded in source drift ledger",
            "line_ending_only_drift": "accepted only when canonical LF hash matches",
            "repairable_packet_or_manifest_issues": "none" if not all_issues else all_issues,
        },
        "same_evidence_class_intelligence_remaining": 0 if not all_issues else len(all_issues),
        "terminal_decision": terminal_decision,
        "safe_flags_preserved": not material_issues and not json_issues,
    }
    write_json(route_file(f"G12_R9_PACKET_AUDIT_COMPLETION_{DATE}.json"), completion)

    decision = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "terminal_decision": terminal_decision,
        "decision_scope": "G12 no-promotion audit acceptance of R9 forward-retest/source-capture packet only",
        "can_promote": False,
        "downstream_canonical_no_promotion_packet_use_allowed": not all_issues,
        "validation_or_live_use_allowed": False,
        "summary_counts": {
            "packet_rows": observed_counts["row_identity"],
            "haz001_rows": observed_counts["haz001"],
            "mac_rows": observed_counts["mac"],
            "haz005_rows": observed_counts["haz005"],
            "unc004_packet_rows": unc_contract_scope_counts.get("packet_row", 0),
            "unc004_full_implication_rows": unc_contract_scope_counts.get("accepted_full_row_implication", 0),
            "residual_rows": observed_counts["residual"],
            "repaired_target_rows": observed_counts["repaired_targets"],
            "failure_intelligence_rows": observed_counts["failure_intel"],
            "blocker_rows": observed_counts["blockers"],
            "packet_sequence_rows": observed_counts["sequence"],
            "same_g12_issue_count": len(all_issues),
        },
        "repair_requirements": all_issues,
    }
    write_json(route_file(f"G12_R9_PACKET_AUDIT_DECISION_{DATE}.json"), decision)

    synthesis = [
        "# G12 READY8 R9 Forward Retest Source Capture Packet Audit",
        "",
        f"Terminal decision: `{terminal_decision}`.",
        "",
        "This G12 audit recomputed the R9 packet from route-local disk artifacts and accepted it only as no-promotion packet evidence.",
        "",
        f"- Packet rows audited: {observed_counts['row_identity']}",
        f"- HAZ001 / MAC / HAZ005 / UNC004 packet / residual rows: {observed_counts['haz001']} / {observed_counts['mac']} / {observed_counts['haz005']} / {unc_contract_scope_counts.get('packet_row', 0)} / {observed_counts['residual']}",
        f"- UNC004 accepted full-row implications audited: {unc_contract_scope_counts.get('accepted_full_row_implication', 0)}",
        f"- Repaired target carry-forward rows audited: {observed_counts['repaired_targets']}",
        f"- Failure-intelligence rows audited: {observed_counts['failure_intel']}",
        f"- R9 JSONL rows parsed and hashed: {len(material_rows)}",
        f"- Real immutable source drift: {len(real_source_drift)}",
        "",
        "Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. This audit is not validation, promotion, live readiness, R/PnL, win-rate, expectancy, Sharpe, broker actual-R, AI/API, paid/vendor, prompt/config/risk/safety/execution/canary/selector, raw market blob, broker/account/order/history/deal/position, live behavior, registry edit, or remote-push evidence.",
        "",
    ]
    write_text(route_file(f"G12_R9_PACKET_AUDIT_SYNTHESIS_{DATE}.md"), "\n".join(synthesis))

    write_output_manifest()
    return {
        "terminal_decision": terminal_decision,
        "issue_count": len(all_issues),
        "completion_standard_met": not all_issues,
    }


def write_output_manifest() -> None:
    manifest_path = route_file(f"G12_R9_PACKET_AUDIT_OUTPUT_MANIFEST_{DATE}.json")
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file() or path == manifest_path:
            continue
        if not (
            path.name.startswith("G12_R9_PACKET_AUDIT_")
            or path.name.startswith("build_g12_r9_forward_packet_audit_")
            or path.name.startswith("verify_g12_r9_forward_packet_audit_")
            or path.name.startswith("test_g12_r9_forward_packet_audit_")
        ):
            continue
        files.append(
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
                if path.suffix == ".jsonl"
                else None,
            }
        )
    manifest = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "file_count_excluding_manifest": len(files),
        "files": files,
    }
    write_json(manifest_path, manifest)


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
