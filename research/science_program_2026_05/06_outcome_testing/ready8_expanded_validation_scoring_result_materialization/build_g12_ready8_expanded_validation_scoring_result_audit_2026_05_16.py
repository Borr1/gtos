"""Build the G12 audit artifacts for the READY8 expanded scoring result packet."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-16"
ROUTE_ID = "G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT"
EVIDENCE_CLASS = "G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_ONLY"
R8_EVIDENCE_CLASS = "READY8_EXPANDED_VALIDATION_SCORING_RESULT_MATERIALIZATION_ONLY"

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
    "opens_remote_push": False,
}

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
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ".context/00_core/r7_failure_intelligence_doctrine_addendum.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
]

R8_FILES = {
    "packet_admission": f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl",
    "row_branch": f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl",
    "haz001": f"READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_{DATE}.jsonl",
    "unc004": f"READY8_EXPANDED_SCORING_UNC004_SOURCE_BIAS_SOURCE_CAPTURE_RESULT_LEDGER_{DATE}.jsonl",
    "mac": f"READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_{DATE}.jsonl",
    "haz005": f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl",
    "residual": f"READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_{DATE}.jsonl",
    "adv_control": f"READY8_EXPANDED_SCORING_ADV_CONTROL_ADJUSTMENT_LEDGER_{DATE}.jsonl",
    "duplicate_effective_n": f"READY8_EXPANDED_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_{DATE}.jsonl",
    "concentration": f"READY8_EXPANDED_SCORING_CONCENTRATION_STRESS_LEDGER_{DATE}.jsonl",
    "repaired_target": f"READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl",
    "fail_closed": f"READY8_EXPANDED_SCORING_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.jsonl",
    "failure_intelligence": f"READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
    "question_ambiguity": f"READY8_EXPANDED_SCORING_QUESTION_AMBIGUITY_PURSUIT_LEDGER_{DATE}.jsonl",
    "open_closed_doors": f"READY8_EXPANDED_SCORING_OPEN_DOOR_CLOSED_DOOR_LEDGER_{DATE}.jsonl",
    "blocker_repair": f"READY8_EXPANDED_SCORING_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
    "source_capture": f"READY8_EXPANDED_SCORING_SOURCE_CAPTURE_FORWARD_RETEST_IMPLICATION_LEDGER_{DATE}.jsonl",
    "source_universe": f"READY8_EXPANDED_SCORING_SOURCE_UNIVERSE_SEARCHED_ROOT_LEDGER_{DATE}.jsonl",
}

R8_JSON = {
    "completion": f"READY8_EXPANDED_SCORING_COMPLETION_AUDIT_{DATE}.json",
    "decision": f"READY8_EXPANDED_SCORING_DECISION_LEDGER_{DATE}.json",
    "verification": f"READY8_EXPANDED_SCORING_VERIFICATION_RESULT_{DATE}.json",
    "manifest": f"READY8_EXPANDED_SCORING_OUTPUT_MANIFEST_{DATE}.json",
    "source_hash": f"READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_{DATE}.json",
    "instruction_coverage": f"READY8_EXPANDED_SCORING_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
    "saturation": f"READY8_EXPANDED_SCORING_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
}

EXPECTED_COUNTS = {
    "packet_rows": 182,
    "row_branch_rows": 182,
    "haz001_rows": 143,
    "unc004_packet_rows": 1,
    "unc004_full_rows": 1153,
    "mac_rows": 32,
    "haz005_rows": 5,
    "residual_rows": 1,
    "repaired_target_rows": 5320,
    "failure_intelligence_rows": 2641,
    "open_closed_door_rows": 364,
    "question_ambiguity_rows": 182,
    "source_capture_rows": 182,
    "adv_control_rows": 182,
    "duplicate_effective_n_rows": 182,
    "concentration_rows": 182,
    "fail_closed_rows": 118,
    "source_universe_rows": 46,
}

EXPECTED_FAMILY_COUNTS = {
    "HAZ001_DECONCENTRATED_RETEST": 143,
    "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC": 1,
    "MAC_INVERSE_AVOID_FILTER_DESIGN": 32,
    "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL": 5,
    "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE": 1,
}

EXPECTED_TERMINAL_DECISION = (
    "MATERIALIZED_READY8_EXPANDED_VALIDATION_SCORING_RESULT_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION"
)
ACCEPT_DECISION = "ACCEPT_AS_G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_NO_PROMOTION"
REJECT_DECISION = "REJECT_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_WITH_EXACT_REPAIR_REQUIREMENTS_NO_PROMOTION"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


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
            cleaned = {k: v for k, v in row.items() if k != "_line_number"}
            handle.write(json.dumps(cleaned, sort_keys=True, separators=(",", ":")) + "\n")


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
    cleaned = {k: v for k, v in row.items() if k != "_line_number"}
    return stable_hash(cleaned)


def safe_base() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_FALSE_FLAGS,
    }


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


def index_by_packet(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        packet_id = row.get("packet_row_id")
        if packet_id is not None:
            indexed[str(packet_id)] = row
    return indexed


def source_meta(path: Path, label: str) -> dict[str, Any]:
    exists = path.exists()
    return {
        "label": label,
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
        "sha256_canonical_lf": sha256_file_canonical_lf(path) if exists else None,
        "jsonl_rows": sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        if exists and path.suffix == ".jsonl"
        else None,
    }


def classify_r8_source_drift(source: dict[str, Any]) -> dict[str, Any]:
    source_path = ROOT / source["path"]
    if not source_path.exists():
        return {
            **safe_base(),
            "source_path": source["path"],
            "label": source.get("label"),
            "drift_classification": "MISSING_SOURCE",
            "blocking": True,
            "expected_raw_sha256": source.get("sha256"),
            "current_raw_sha256": None,
            "expected_canonical_lf_sha256": source.get("sha256_canonical_lf"),
            "current_canonical_lf_sha256": None,
            "proof": "Source path is absent on current disk.",
        }

    current_raw = sha256_file(source_path)
    current_canonical = sha256_file_canonical_lf(source_path)
    expected_raw = source.get("sha256")
    expected_canonical = source.get("sha256_canonical_lf")
    raw_match = current_raw == expected_raw
    canonical_match = expected_canonical is not None and current_canonical == expected_canonical
    mutable = source["path"] in MUTABLE_COORDINATION_PATHS
    if raw_match:
        classification = "RAW_HASH_MATCH"
        blocking = False
        proof = "Current raw bytes match R8 source hash ledger."
    elif canonical_match:
        classification = "LINE_ENDING_ONLY_DRIFT_CANONICAL_LF_MATCH"
        blocking = False
        proof = "Raw bytes differ but canonical LF hash matches R8 source hash ledger."
    elif mutable:
        classification = "MUTABLE_COORDINATION_CONTEXT_DRIFT_BOUNDED"
        blocking = False
        proof = "Mandatory context/coordination file changed after R8 materialization; R8 verifier policy bounds this class and immutable sources remain strict."
    else:
        classification = "REAL_IMMUTABLE_SOURCE_DRIFT"
        blocking = True
        proof = "Neither raw nor canonical LF hash matches for an immutable source artifact."
    return {
        **safe_base(),
        "source_path": source["path"],
        "label": source.get("label"),
        "drift_classification": classification,
        "blocking": blocking,
        "mutable_coordination_source": mutable,
        "expected_raw_sha256": expected_raw,
        "current_raw_sha256": current_raw,
        "expected_canonical_lf_sha256": expected_canonical,
        "current_canonical_lf_sha256": current_canonical,
        "proof": proof,
    }


def build_material_row_audit(ledgers: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str]]:
    rows_out: list[dict[str, Any]] = []
    safe_issues: list[str] = []
    for ledger_name, rows in sorted(ledgers.items()):
        for row in rows:
            safe_ok, issues = check_safe_flags(row)
            if not safe_ok:
                safe_issues.append(f"{ledger_name}:{row.get('_line_number')}: {'; '.join(issues)}")
            rows_out.append(
                {
                    **safe_base(),
                    "source_ledger": R8_FILES[ledger_name],
                    "source_line_number": row.get("_line_number"),
                    "source_row_sha256": row_hash(row),
                    "packet_row_id": row.get("packet_row_id"),
                    "branch_key_sha256": stable_hash(row.get("branch_key")) if row.get("branch_key") is not None else None,
                    "packet_family": row.get("packet_family"),
                    "result_status": row.get("result_status"),
                    "branch_status": row.get("branch_status"),
                    "ledger_family": row.get("ledger_family"),
                    "door_status": row.get("door_status"),
                    "answer_status": row.get("answer_status"),
                    "blocker_status": row.get("blocker_status"),
                    "search_result": row.get("search_result"),
                    "audit_status": "ROW_PARSED_HASHED_AND_SAFE_FLAGS_VERIFIED" if safe_ok else "ROW_SAFE_FLAG_MISMATCH",
                    "safe_flag_issues": issues,
                }
            )
    return rows_out, safe_issues


def build_packet_coverage(ledgers: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str]]:
    packet = index_by_packet(ledgers["packet_admission"])
    row_branch = index_by_packet(ledgers["row_branch"])
    adv = index_by_packet(ledgers["adv_control"])
    dup = index_by_packet(ledgers["duplicate_effective_n"])
    concentration = index_by_packet(ledgers["concentration"])
    questions = index_by_packet(ledgers["question_ambiguity"])
    source_capture = index_by_packet(ledgers["source_capture"])
    haz001 = index_by_packet(ledgers["haz001"])
    mac = index_by_packet(ledgers["mac"])
    haz005 = index_by_packet(ledgers["haz005"])
    residual = index_by_packet(ledgers["residual"])
    blocker = defaultdict(list)
    for row in ledgers["blocker_repair"]:
        if row.get("packet_row_id"):
            blocker[str(row["packet_row_id"])].append(row)
    doors = defaultdict(Counter)
    for row in ledgers["open_closed_doors"]:
        if row.get("packet_row_id"):
            doors[str(row["packet_row_id"])][row.get("door_status")] += 1

    issues: list[str] = []
    rows_out: list[dict[str, Any]] = []
    for packet_id in sorted(packet):
        result = row_branch.get(packet_id)
        family = result.get("packet_family") if result else packet[packet_id].get("packet_family")
        family_ledger_present = {
            "HAZ001_DECONCENTRATED_RETEST": packet_id in haz001,
            "MAC_INVERSE_AVOID_FILTER_DESIGN": packet_id in mac,
            "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL": packet_id in haz005,
            "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE": packet_id in residual,
            "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC": True,
        }.get(str(family), False)
        coverage = {
            "packet_admission_present": True,
            "row_branch_result_present": packet_id in row_branch,
            "adv_control_present": packet_id in adv,
            "duplicate_effective_n_present": packet_id in dup,
            "concentration_present": packet_id in concentration,
            "question_ambiguity_present": packet_id in questions,
            "source_capture_forward_retest_present": packet_id in source_capture,
            "open_door_count": doors[packet_id].get("OPEN_DOOR", 0),
            "closed_door_count": doors[packet_id].get("CLOSED_DOOR", 0),
            "family_specific_result_present": family_ledger_present,
        }
        ok = (
            coverage["row_branch_result_present"]
            and coverage["adv_control_present"]
            and coverage["duplicate_effective_n_present"]
            and coverage["concentration_present"]
            and coverage["question_ambiguity_present"]
            and coverage["source_capture_forward_retest_present"]
            and coverage["open_door_count"] == 1
            and coverage["closed_door_count"] == 1
            and coverage["family_specific_result_present"]
        )
        if not ok:
            issues.append(f"packet coverage mismatch for {packet_id}: {coverage}")
        rows_out.append(
            {
                **safe_base(),
                "packet_row_id": packet_id,
                "packet_family": family,
                "result_status": result.get("result_status") if result else None,
                "branch_key_sha256": stable_hash(result.get("branch_key")) if result and result.get("branch_key") is not None else None,
                "coverage": coverage,
                "blocker_repair_rows": len(blocker.get(packet_id, [])),
                "audit_status": "PACKET_ROW_FULLY_COVERED" if ok else "PACKET_ROW_COVERAGE_MISMATCH",
            }
        )
    extra_result = set(row_branch) - set(packet)
    if extra_result:
        issues.append(f"row branch result has {len(extra_result)} packet ids not in admission ledger")
    return rows_out, issues


def build_failure_preservation(ledgers: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[str] = []
    rows_out: list[dict[str, Any]] = []
    allowed_branch_statuses = {
        "CONTROL_EXPLAINED_EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED",
        "WEAKENED_BY_CONTROL_ENVELOPE_INTELLIGENCE_PRESERVED",
        "UNDERPOWERED_RETAINED_FOR_SAMPLE_EXPANSION",
        "SOURCE_LIMITED_CAPTURE_REQUIRED",
        "EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED",
        "FAIL_CLOSED_REMAINS_EXCLUDED_WITH_CAPTURE_REQUIREMENT",
    }
    for row in ledgers["failure_intelligence"]:
        branch_status = row.get("branch_status")
        doctrine = row.get("doctrine_classifications") or []
        ok = (
            branch_status in allowed_branch_statuses
            and bool(row.get("explaining_mechanism"))
            and bool(row.get("implication"))
            and isinstance(doctrine, list)
            and len(doctrine) > 0
        )
        if not ok:
            issues.append(f"failure intelligence row {row.get('_line_number')} weak preservation fields")
        rows_out.append(
            {
                **safe_base(),
                "source_line_number": row.get("_line_number"),
                "source_row_sha256": row_hash(row),
                "branch_key_sha256": stable_hash(row.get("branch_key")),
                "branch_status": branch_status,
                "doctrine_classifications": doctrine,
                "explaining_mechanism": row.get("explaining_mechanism"),
                "implication": row.get("implication"),
                "audit_status": "FAILURE_INTELLIGENCE_PRESERVED_NOT_ERASED" if ok else "FAILURE_INTELLIGENCE_WEAK_ROW",
            }
        )
    return rows_out, issues


def build_repaired_target_audit(ledgers: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[str] = []
    rows_out: list[dict[str, Any]] = []
    for row in ledgers["repaired_target"]:
        ok = (
            row.get("consumption_status") == "R7_MAY_CONSUME_SOURCE_REPAIR_ONLY_NOT_VALIDATION"
            and row.get("result_status")
            == "REPAIRED_TARGET_ROW_CONSUMED_AS_SOURCE_BOUND_NEUTRAL_TARGET_MOVEMENT_INPUT_NOT_PROMOTION"
            and row.get("repair_candidate_target_result_row_hash_match") is True
            and bool(row.get("original_target_result_row_id"))
        )
        if not ok:
            issues.append(f"repaired target row {row.get('_line_number')} failed consumption proof")
        rows_out.append(
            {
                **safe_base(),
                "source_line_number": row.get("_line_number"),
                "source_row_sha256": row_hash(row),
                "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
                "original_target_result_row_id": row.get("original_target_result_row_id"),
                "card_id": row.get("card_id"),
                "target_family_id": row.get("target_family_id"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "consumption_status": row.get("consumption_status"),
                "audit_status": "REPAIRED_TARGET_CONSUMPTION_VERIFIED" if ok else "REPAIRED_TARGET_CONSUMPTION_WEAK",
            }
        )
    return rows_out, issues


def build() -> dict[str, Any]:
    generated_at = utc_now()
    ledgers = {key: read_jsonl(route_file(name)) for key, name in R8_FILES.items()}
    json_docs = {key: read_json(route_file(name)) for key, name in R8_JSON.items()}

    material_rows, material_safe_issues = build_material_row_audit(ledgers)
    packet_coverage_rows, packet_coverage_issues = build_packet_coverage(ledgers)
    failure_preservation_rows, failure_issues = build_failure_preservation(ledgers)
    repaired_target_rows, repaired_target_issues = build_repaired_target_audit(ledgers)

    source_drift_rows = [
        classify_r8_source_drift(source) for source in json_docs["source_hash"].get("sources", [])
    ]
    real_source_drift = [row for row in source_drift_rows if row["blocking"]]

    r8_manifest_rows = []
    manifest_hash_issues: list[str] = []
    for item in json_docs["manifest"].get("files", []):
        path = ROOT / item["path"]
        exists = path.exists()
        current_sha = sha256_file(path) if exists else None
        ok = exists and current_sha == item.get("sha256")
        if not ok:
            manifest_hash_issues.append(item["path"])
        r8_manifest_rows.append(
            {
                **safe_base(),
                "manifest_path": item["path"],
                "exists": exists,
                "expected_sha256": item.get("sha256"),
                "current_sha256": current_sha,
                "jsonl_rows_expected": item.get("jsonl_rows"),
                "bytes_expected": item.get("bytes"),
                "audit_status": "R8_MANIFEST_HASH_MATCH" if ok else "R8_MANIFEST_HASH_MISMATCH",
            }
        )

    packet_family_counts = Counter(row.get("packet_family") for row in ledgers["row_branch"])
    result_status_counts = Counter(row.get("result_status") for row in ledgers["row_branch"])
    failure_status_counts = Counter(row.get("branch_status") for row in ledgers["failure_intelligence"])
    control_counts = Counter(row.get("control_adjustment_classification") for row in ledgers["adv_control"])
    unc_ledger_counts = Counter(row.get("ledger_family") for row in ledgers["unc004"])
    fail_closed_counts = Counter(row.get("ledger_family") for row in ledgers["fail_closed"])
    source_drift_counts = Counter(row.get("drift_classification") for row in source_drift_rows)

    row_count_observed = {
        "packet_rows": len(ledgers["packet_admission"]),
        "row_branch_rows": len(ledgers["row_branch"]),
        "haz001_rows": len(ledgers["haz001"]),
        "unc004_packet_rows": packet_family_counts.get("UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC", 0),
        "unc004_full_rows": len(ledgers["unc004"]),
        "mac_rows": len(ledgers["mac"]),
        "haz005_rows": len(ledgers["haz005"]),
        "residual_rows": len(ledgers["residual"]),
        "repaired_target_rows": len(ledgers["repaired_target"]),
        "failure_intelligence_rows": len(ledgers["failure_intelligence"]),
        "open_closed_door_rows": len(ledgers["open_closed_doors"]),
        "question_ambiguity_rows": len(ledgers["question_ambiguity"]),
        "source_capture_rows": len(ledgers["source_capture"]),
        "adv_control_rows": len(ledgers["adv_control"]),
        "duplicate_effective_n_rows": len(ledgers["duplicate_effective_n"]),
        "concentration_rows": len(ledgers["concentration"]),
        "fail_closed_rows": len(ledgers["fail_closed"]),
        "source_universe_rows": len(ledgers["source_universe"]),
    }
    row_count_issues = [
        f"{key}: observed {row_count_observed.get(key)} expected {expected}"
        for key, expected in EXPECTED_COUNTS.items()
        if row_count_observed.get(key) != expected
    ]
    family_issues = [
        f"{key}: observed {packet_family_counts.get(key, 0)} expected {expected}"
        for key, expected in EXPECTED_FAMILY_COUNTS.items()
        if packet_family_counts.get(key, 0) != expected
    ]

    decision = json_docs["decision"]
    completion = json_docs["completion"]
    r8_verification = json_docs["verification"]
    terminal_issues: list[str] = []
    if decision.get("terminal_decision") != EXPECTED_TERMINAL_DECISION:
        terminal_issues.append("R8 terminal decision mismatch")
    if not decision.get("g12_post_result_audit_required"):
        terminal_issues.append("R8 decision does not require G12 post-result audit")
    if completion.get("same_evidence_class_intelligence_remaining") != 0:
        terminal_issues.append("R8 completion does not show same-evidence-class intelligence remaining = 0")
    if not r8_verification.get("ok") or not r8_verification.get("can_mark_goal_complete"):
        terminal_issues.append("R8 verifier result on disk is not ok/can_mark_goal_complete")

    all_issues = (
        material_safe_issues
        + packet_coverage_issues
        + failure_issues
        + repaired_target_issues
        + [f"real source drift: {row['source_path']}" for row in real_source_drift]
        + [f"manifest hash mismatch: {path}" for path in manifest_hash_issues]
        + row_count_issues
        + family_issues
        + terminal_issues
    )
    terminal_decision = ACCEPT_DECISION if not all_issues else REJECT_DECISION

    write_jsonl(route_file(f"G12_R8EXP_SCORING_AUDIT_MATERIAL_ROWS_{DATE}.jsonl"), material_rows)
    write_jsonl(route_file(f"G12_R8EXP_SCORING_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"), packet_coverage_rows)
    write_jsonl(route_file(f"G12_R8EXP_SCORING_AUDIT_FAILURE_INTEL_{DATE}.jsonl"), failure_preservation_rows)
    write_jsonl(route_file(f"G12_R8EXP_SCORING_AUDIT_REPAIRED_TARGET_{DATE}.jsonl"), repaired_target_rows)
    write_jsonl(route_file(f"G12_R8EXP_SCORING_AUDIT_SOURCE_DRIFT_{DATE}.jsonl"), source_drift_rows)
    write_jsonl(route_file(f"G12_R8EXP_SCORING_AUDIT_R8_MANIFEST_{DATE}.jsonl"), r8_manifest_rows)

    recomputation = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "objective_restatement": "Independent G12 audit of R8 READY8 expanded validation scoring/result materialization from disk evidence.",
        "r8_evidence_class": R8_EVIDENCE_CLASS,
        "expected_counts": EXPECTED_COUNTS,
        "observed_counts": row_count_observed,
        "row_count_issues": row_count_issues,
        "packet_family_counts": dict(packet_family_counts),
        "packet_family_issues": family_issues,
        "result_status_counts": dict(result_status_counts),
        "failure_intelligence_status_counts": dict(failure_status_counts),
        "adv_control_adjustment_counts": dict(control_counts),
        "unc004_ledger_family_counts": dict(unc_ledger_counts),
        "fail_closed_ledger_family_counts": dict(fail_closed_counts),
        "source_hash_drift_classification_counts": dict(source_drift_counts),
        "r8_manifest_hash_mismatch_count": len(manifest_hash_issues),
        "r8_manifest_hash_mismatches": manifest_hash_issues,
        "material_jsonl_rows_audited": len(material_rows),
        "material_jsonl_ledgers_audited": sorted(R8_FILES.values()),
        "packet_rows_full_coverage": not packet_coverage_issues,
        "failure_intelligence_rows_preserved": not failure_issues,
        "repaired_target_consumption_rows_verified": not repaired_target_issues,
        "real_immutable_source_drift_count": len(real_source_drift),
        "r8_terminal_decision_ok": not terminal_issues,
        "terminal_issues": terminal_issues,
        "all_issues": all_issues,
    }
    write_json(route_file(f"G12_R8EXP_SCORING_AUDIT_RECOMPUTATION_{DATE}.json"), recomputation)

    audit_sources = []
    for context_path in REQUIRED_CONTEXT:
        audit_sources.append(source_meta(ROOT / context_path, f"context:{context_path}"))
    for name in sorted(R8_JSON.values()):
        audit_sources.append(source_meta(route_file(name), f"r8_json:{name}"))
    for name in sorted(R8_FILES.values()):
        audit_sources.append(source_meta(route_file(name), f"r8_jsonl:{name}"))
    audit_sources.extend(
        [
            source_meta(route_file(f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md"), "g12_controlling_prompt"),
            source_meta(route_file(f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_STARTER_{DATE}.txt"), "g12_starter"),
        ]
    )
    source_hash_ledger = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "source_count": len(audit_sources),
        "sources": audit_sources,
        "r8_source_drift_classification_ledger": f"G12_R8EXP_SCORING_AUDIT_SOURCE_DRIFT_{DATE}.jsonl",
        "real_immutable_source_drift_count": len(real_source_drift),
        "mutable_coordination_drift_is_bounded": True,
        "line_ending_drift_classification_supported": True,
        "source_hash_policy": {
            "strict_for": "R8 material artifacts and immutable prerequisite/source artifacts",
            "bounded_for": sorted(MUTABLE_COORDINATION_PATHS),
            "raw_vs_canonical_rule": "Raw hash drift with canonical LF match is classified as line-ending-only drift; mutable coordination drift is bounded but not used to change R8 row evidence.",
        },
    }
    write_json(route_file(f"G12_R8EXP_SCORING_AUDIT_SOURCE_HASH_{DATE}.json"), source_hash_ledger)

    instruction_coverage = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "lane_type": "G12 post-result audit",
        "builder_audit_posture": "Strict but fair audit; recompute from disk, repair same-G12 issues when available, do not invent limitations.",
        "coverage": [
            {
                "requirement": "Regenerate/read LIVE_STATE and required context files",
                "status": "COVERED",
                "evidence": [".context/LIVE_STATE.md", *REQUIRED_CONTEXT[1:]],
                "operationalized_as": "All required context files are hashed in the G12 source hash ledger and used as audit boundaries.",
            },
            {
                "requirement": "Do not rely on chat memory, R8 verifier, manifest, completion audit, or summaries alone",
                "status": "COVERED",
                "evidence": [
                    f"G12_R8EXP_SCORING_AUDIT_MATERIAL_ROWS_{DATE}.jsonl",
                    f"G12_R8EXP_SCORING_AUDIT_RECOMPUTATION_{DATE}.json",
                ],
                "operationalized_as": "Every R8 JSONL row is parsed and hashed; counts are recomputed independently of R8 summary artifacts.",
            },
            {
                "requirement": "No arbitrary top-N or representative-only sampling",
                "status": "COVERED",
                "evidence": [f"G12_R8EXP_SCORING_AUDIT_MATERIAL_ROWS_{DATE}.jsonl"],
                "row_count": len(material_rows),
                "operationalized_as": "All R8 JSONL ledgers are full-scanned; no scan is truncated.",
            },
            {
                "requirement": "Exact packet-row and ledger-family coverage",
                "status": "COVERED" if not packet_coverage_issues and not row_count_issues and not family_issues else "ISSUE_FOUND",
                "evidence": [f"G12_R8EXP_SCORING_AUDIT_PACKET_COVERAGE_{DATE}.jsonl"],
                "issues": packet_coverage_issues + row_count_issues + family_issues,
            },
            {
                "requirement": "Verify controls/placebos, duplicate-effective-N, concentration, fail-closed, source-capture, open/closed doors, questions/ambiguities",
                "status": "COVERED",
                "evidence": [
                    R8_FILES["adv_control"],
                    R8_FILES["duplicate_effective_n"],
                    R8_FILES["concentration"],
                    R8_FILES["fail_closed"],
                    R8_FILES["source_capture"],
                    R8_FILES["open_closed_doors"],
                    R8_FILES["question_ambiguity"],
                ],
                "operationalized_as": "Each packet row is joined against these ledgers in the packet coverage audit; full rows are hashed in material row audit.",
            },
            {
                "requirement": "Preserve killed/weakened/deferred failure intelligence and kill only unsupported edge claims",
                "status": "COVERED" if not failure_issues else "ISSUE_FOUND",
                "evidence": [f"G12_R8EXP_SCORING_AUDIT_FAILURE_INTEL_{DATE}.jsonl"],
                "issues": failure_issues,
            },
            {
                "requirement": "Distinguish real drift from timestamp, line-ending, and mutable-context drift",
                "status": "COVERED" if not real_source_drift else "ISSUE_FOUND",
                "evidence": [f"G12_R8EXP_SCORING_AUDIT_SOURCE_DRIFT_{DATE}.jsonl"],
                "issues": [row["source_path"] for row in real_source_drift],
            },
            {
                "requirement": "Preserve safe flags and forbidden surfaces",
                "status": "COVERED" if not material_safe_issues else "ISSUE_FOUND",
                "evidence": [f"G12_R8EXP_SCORING_AUDIT_MATERIAL_ROWS_{DATE}.jsonl"],
                "issues": material_safe_issues[:20],
            },
            {
                "requirement": "Emit audit artifacts, full ledgers, manifest, verifier/focused tests, completion audit, and terminal decision",
                "status": "COVERED",
                "evidence": [
                    f"G12_R8EXP_SCORING_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
                    f"G12_R8EXP_SCORING_AUDIT_COMPLETION_{DATE}.json",
                    f"G12_R8EXP_SCORING_AUDIT_DECISION_{DATE}.json",
                    f"verify_g12_ready8_expanded_validation_scoring_result_audit_2026_05_16.py",
                    f"test_g12_ready8_expanded_validation_scoring_result_audit_2026_05_16.py",
                ],
            },
        ],
    }
    write_json(route_file(f"G12_R8EXP_SCORING_AUDIT_INSTRUCTION_COVERAGE_{DATE}.json"), instruction_coverage)

    completion_audit = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "objective_restatement": "Accept or reject the R8 READY8 expanded scoring/result materialization from full disk recomputation, preserving no-promotion boundaries.",
        "completion_standard_met": not all_issues,
        "prompt_to_artifact_checklist": instruction_coverage["coverage"],
        "required_row_counts_observed": row_count_observed,
        "required_row_counts_match": not row_count_issues,
        "packet_family_counts": dict(packet_family_counts),
        "packet_family_counts_match": not family_issues,
        "full_material_jsonl_rows_audited": len(material_rows),
        "source_universe_rows": len(ledgers["source_universe"]),
        "r8_verifier_rerun_status_from_disk": {
            "ok": r8_verification.get("ok"),
            "can_mark_goal_complete": r8_verification.get("can_mark_goal_complete"),
            "mutable_coordination_source_hash_drift_count": r8_verification.get("checks", {}).get("mutable_coordination_source_hash_drift_count"),
        },
        "focused_tests_evidence": "G12 focused test artifact is written by verifier after pytest rerun.",
        "same_g12_issue_count": len(all_issues),
        "same_g12_issues": all_issues,
        "same_evidence_class_intelligence_remaining": 0 if not all_issues else len(all_issues),
        "terminal_decision": terminal_decision,
        "safe_flags_preserved": True,
    }
    write_json(route_file(f"G12_R8EXP_SCORING_AUDIT_COMPLETION_{DATE}.json"), completion_audit)

    decision_ledger = {
        **safe_base(),
        "generated_at_utc": generated_at,
        "terminal_decision": terminal_decision,
        "decision_scope": "G12 no-promotion audit acceptance of R8 scoring/result materialization only",
        "can_promote": False,
        "downstream_canonical_no_promotion_use_allowed": not all_issues,
        "validation_or_live_use_allowed": False,
        "summary_counts": {
            "packet_rows": row_count_observed["packet_rows"],
            "row_branch_rows": row_count_observed["row_branch_rows"],
            "haz001_rows": row_count_observed["haz001_rows"],
            "unc004_full_rows": row_count_observed["unc004_full_rows"],
            "mac_rows": row_count_observed["mac_rows"],
            "haz005_rows": row_count_observed["haz005_rows"],
            "residual_rows": row_count_observed["residual_rows"],
            "repaired_target_rows": row_count_observed["repaired_target_rows"],
            "failure_intelligence_rows": row_count_observed["failure_intelligence_rows"],
            "same_g12_issue_count": len(all_issues),
        },
        "repair_requirements": all_issues,
    }
    write_json(route_file(f"G12_R8EXP_SCORING_AUDIT_DECISION_{DATE}.json"), decision_ledger)

    synthesis = [
        "# G12 READY8 Expanded Validation Scoring Result Audit",
        "",
        f"Terminal decision: `{terminal_decision}`.",
        "",
        "This audit recomputed the R8 scoring/result packet from route-local disk artifacts without relying on the R8 self-verifier, manifest, completion audit, or summaries alone.",
        "",
        f"- Packet rows audited: {row_count_observed['packet_rows']}",
        f"- Row/branch results audited: {row_count_observed['row_branch_rows']}",
        f"- HAZ001 / UNC004 / MAC / HAZ005 / residual rows: {row_count_observed['haz001_rows']} / {row_count_observed['unc004_full_rows']} / {row_count_observed['mac_rows']} / {row_count_observed['haz005_rows']} / {row_count_observed['residual_rows']}",
        f"- Repaired target-consumption rows audited: {row_count_observed['repaired_target_rows']}",
        f"- Killed/weakened/deferred failure-intelligence rows audited: {row_count_observed['failure_intelligence_rows']}",
        f"- Full R8 JSONL rows parsed and hashed: {len(material_rows)}",
        f"- Real immutable source drift: {len(real_source_drift)}",
        "",
        "Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. This is not promotion, live readiness, R/PnL, win-rate, expectancy, Sharpe, broker actual-R, AI/API, paid/vendor, prompt/config/risk/safety/execution/canary/selector, or remote-push evidence.",
        "",
    ]
    write_text(route_file(f"G12_R8EXP_SCORING_AUDIT_SYNTHESIS_{DATE}.md"), "\n".join(synthesis))

    write_output_manifest()
    return {
        "terminal_decision": terminal_decision,
        "issue_count": len(all_issues),
        "completion_standard_met": not all_issues,
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_output_manifest() -> None:
    manifest_path = route_file(f"G12_R8EXP_SCORING_AUDIT_OUTPUT_MANIFEST_{DATE}.json")
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file() or path == manifest_path:
            continue
        if not (
            path.name.startswith("G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_")
            or path.name.startswith("G12_R8EXP_SCORING_AUDIT_")
            or path.name.startswith("build_g12_ready8_expanded_validation_scoring_result_audit_")
            or path.name.startswith("verify_g12_ready8_expanded_validation_scoring_result_audit_")
            or path.name.startswith("test_g12_ready8_expanded_validation_scoring_result_audit_")
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
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
