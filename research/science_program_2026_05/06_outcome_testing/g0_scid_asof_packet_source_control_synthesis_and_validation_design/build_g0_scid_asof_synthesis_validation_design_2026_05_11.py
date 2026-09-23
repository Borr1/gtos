"""Build the G0 SCID as-of source-control synthesis and validation design route.

This route is design-only. It reconciles the accepted G12 SCID as-of packet
and freezes the next sealed-validation design controls without opening
validation execution, result/path labels, scoring, AI/API, broker/account
evidence, promotion, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
PREFIX = "G0_SCID_ASOF"
ROUTE_ID = "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN"
EVIDENCE_CLASS = "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_ONLY"
SCHEMA_VERSION = "g0_scid_asof_synthesis_validation_design_v1"
TERMINAL_DECISION = "ACCEPT_G0_SOURCE_CONTROL_SYNTHESIS_AND_SEALED_VALIDATION_DESIGN_PACKET_ONLY"

CONTROLLING_PROMPT = (
    PROMPT_DIR
    / "G0_SCID_ASOF_PACKET_SOURCE_CONTROL_SYNTHESIS_AND_VALIDATION_DESIGN_GOAL_PROMPT_2026-05-11.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_GOAL_PROMPT_2026-05-11.md"
)

OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
G12_PACKET_AUDIT_DIR = (
    OUTCOME_ROOT / "g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit"
)
PACKET_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
G12_CONTRACT_AUDIT_DIR = (
    OUTCOME_ROOT / "g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit"
)
CONTRACT_DIR = OUTCOME_ROOT / "scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint"
G12_SCID_FREEZE_DIR = (
    OUTCOME_ROOT / "g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit"
)
SCID_FREEZE_DIR = OUTCOME_ROOT / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
G0_FPB_PARTITION_DIR = OUTCOME_ROOT / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
G0_FPB_SYNTHESIS_DIR = OUTCOME_ROOT / "g0_fpb_discovery_synthesis_control_route"
G12_FPB_RESULT_DIR = OUTCOME_ROOT / "g12_fpb_result_audit"
FPB_DISCOVERY_DIR = OUTCOME_ROOT / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
HISTORICAL_PROTOCOL = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "05_synthesis"
    / "HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md"
)

MANDATORY_INPUTS: dict[str, Path] = {
    "controlling_prompt": CONTROLLING_PROMPT,
    "g12_packet_decision_ledger": G12_PACKET_AUDIT_DIR
    / "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json",
    "g12_packet_completion_audit": G12_PACKET_AUDIT_DIR
    / "G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.json",
    "g12_packet_warning_repair_review": G12_PACKET_AUDIT_DIR
    / "G12_SCID_ASOF_PACKET_AUDIT_WARNING_REPAIR_REVIEW_2026-05-11.json",
    "g12_packet_duplicate_proxy_review": G12_PACKET_AUDIT_DIR
    / "G12_SCID_ASOF_PACKET_AUDIT_DUPLICATE_PROXY_REVIEW_2026-05-11.json",
    "g12_packet_discovery_baseline_review": G12_PACKET_AUDIT_DIR
    / "G12_SCID_ASOF_PACKET_AUDIT_DISCOVERY_BASELINE_REVIEW_2026-05-11.json",
    "packet_bar_manifest": PACKET_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json",
    "packet_candidate_manifest": PACKET_DIR
    / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json",
    "packet_candidate_rows": PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    "packet_duplicate_proxy_ledger": PACKET_DIR
    / "SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_2026-05-11.json",
    "packet_discovery_baseline_audit": PACKET_DIR
    / "SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_2026-05-11.json",
    "contract_decision_ledger": G12_CONTRACT_AUDIT_DIR
    / "G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_2026-05-11.json",
    "contract_completion_audit": G12_CONTRACT_AUDIT_DIR
    / "G12_SCID_ASOF_CONTRACT_AUDIT_COMPLETION_AUDIT_2026-05-11.json",
    "contract_bar_derivation": CONTRACT_DIR / "SCID_ASOF_BAR_DERIVATION_CONTRACT_2026-05-11.json",
    "contract_candidate_constraint": CONTRACT_DIR
    / "SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_2026-05-11.json",
    "contract_noleak_partition_audit": CONTRACT_DIR
    / "SCID_ASOF_NOLEAK_PARTITION_AUDIT_2026-05-11.json",
    "scid_freeze_reaudit_decision": G12_SCID_FREEZE_DIR
    / "G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-11.json",
    "scid_freeze_reaudit_source_rehash": G12_SCID_FREEZE_DIR
    / "G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.json",
    "scid_freeze_manifest": SCID_FREEZE_DIR
    / "FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json",
    "g0_fpb_discovery_exposure": G0_FPB_PARTITION_DIR
    / "G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_2026-05-11.json",
    "g0_fpb_baseline_packet": G0_FPB_PARTITION_DIR
    / "G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_2026-05-11.json",
    "g0_fpb_multiple_testing": G0_FPB_PARTITION_DIR
    / "G0_FPB_SEALED_PARTITION_SELECTION_BIAS_MULTIPLE_TESTING_CARRY_FORWARD_2026-05-11.json",
    "g0_fpb_synthesis_multiple_testing": G0_FPB_SYNTHESIS_DIR
    / "G0_FPB_SYNTHESIS_MULTIPLE_TESTING_LEDGER_2026-05-11.json",
    "g0_fpb_synthesis_route_ranking": G0_FPB_SYNTHESIS_DIR
    / "G0_FPB_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-11.json",
    "g12_fpb_result_audit": G12_FPB_RESULT_DIR / "G12_FPB_RESULT_AUDIT_2026-05-11.json",
    "fpb_discovery_completion_audit": FPB_DISCOVERY_DIR / "FPB_COMPLETION_AUDIT_2026-05-10.json",
    "fpb_discovery_baseline_control": FPB_DISCOVERY_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json",
    "historical_protocol_plan": HISTORICAL_PROTOCOL,
}

MANDATORY_DIRS: dict[str, Path] = {
    "g12_packet_audit_dir": G12_PACKET_AUDIT_DIR,
    "packet_dir": PACKET_DIR,
    "g12_contract_audit_dir": G12_CONTRACT_AUDIT_DIR,
    "contract_dir": CONTRACT_DIR,
    "g12_scid_freeze_reaudit_dir": G12_SCID_FREEZE_DIR,
    "scid_freeze_repair_dir": SCID_FREEZE_DIR,
    "g0_fpb_partition_dir": G0_FPB_PARTITION_DIR,
    "g0_fpb_discovery_synthesis_dir": G0_FPB_SYNTHESIS_DIR,
    "g12_fpb_result_audit_dir": G12_FPB_RESULT_DIR,
    "fpb_discovery_result_screen_dir": FPB_DISCOVERY_DIR,
}

EXPECTED = {
    "bar_row_count": 7567,
    "candidate_input_row_count": 3014,
    "accepted_scid_segment_count": 9,
    "candidate_denominator_group_count": 7,
    "discovery_exclusion_count": 365,
    "baseline_count": 4,
}

BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_scored_candidate_generation": False,
    "opens_replay_path_label_result_outcomes": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_promotion": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

PARTITIONS = [
    "SEALED_VALIDATION_CANDIDATE_DESIGN",
    "STRESS_ROBUSTNESS_CANDIDATE_DESIGN",
    "DISCOVERY_EXPOSED_EXCLUDED",
    "CONTAMINATED_EXCLUDED",
    "FORBIDDEN_FOR_THIS_EVIDENCE_CLASS",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT = utc_now()


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_obj(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_git(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": "git " + " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip().splitlines(),
        "stderr": proc.stderr.strip().splitlines(),
    }


def safe_payload(artifact_family: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": GENERATED_AT,
        **SAFE_FLAGS,
        **body,
    }


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> Path:
    path = ROUTE_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
    return path


def write_md(name: str, text: str) -> Path:
    path = ROUTE_DIR / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def path_inventory(path: Path) -> dict[str, Any]:
    if path.is_file():
        return {
            "path": repo_path(path),
            "exists": True,
            "type": "file",
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
    if not path.exists():
        return {"path": repo_path(path), "exists": False, "type": "missing"}
    files = sorted(p for p in path.rglob("*") if p.is_file())
    file_rows = [
        {
            "path": repo_path(file),
            "sha256": sha256_file(file),
            "size_bytes": file.stat().st_size,
        }
        for file in files
    ]
    return {
        "path": repo_path(path),
        "exists": True,
        "type": "directory",
        "file_count": len(file_rows),
        "files": file_rows,
        "tree_sha256": sha256_obj(file_rows),
    }


def dirty_scope_audit() -> dict[str, Any]:
    status = run_git(["status", "--short"])
    scoped_prefixes = [
        "research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_GOAL_PROMPT_2026-05-11.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    ]
    forbidden_live_prefixes = (
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "run_agent.py",
    )
    raw_market_suffixes = (
        ".scid",
        ".depth",
        ".parquet",
        ".csv",
        ".jsonl.gz",
        ".bin",
        ".dly",
    )
    rows: list[dict[str, Any]] = []
    for line in status["stdout"]:
        path = line[3:] if len(line) > 3 else line
        normalized = path.replace("\\", "/")
        scoped = any(normalized.startswith(prefix) for prefix in scoped_prefixes)
        rows.append(
            {
                "status": line[:2],
                "path": normalized,
                "audit_scope": "SCOPED_TO_THIS_G0_ROUTE" if scoped else "UNRELATED_EXISTING_DIRT_INFO_ONLY",
                "forbidden_live_surface_path": normalized.startswith(forbidden_live_prefixes),
                "raw_market_extension": normalized.endswith(raw_market_suffixes),
            }
        )
    scoped_rows = [row for row in rows if row["audit_scope"] == "SCOPED_TO_THIS_G0_ROUTE"]
    return {
        "git_status_returncode": status["returncode"],
        "git_status_stderr": status["stderr"],
        "entries": rows,
        "scoped_entries": scoped_rows,
        "summary": {
            "dirty_entry_count": len(rows),
            "scoped_entry_count": len(scoped_rows),
            "unrelated_dirty_entry_count": len(rows) - len(scoped_rows),
            "no_forbidden_live_surface_in_scoped_entries": not any(
                row["forbidden_live_surface_path"] for row in scoped_rows
            ),
            "no_raw_market_blobs_in_scoped_entries": not any(row["raw_market_extension"] for row in scoped_rows),
        },
    }


def partition_for_row(row: dict[str, Any]) -> tuple[str, str]:
    key = row["duplicate_key"]
    bucket = int(key[:8], 16) % 5
    if bucket == 0:
        return (
            "STRESS_ROBUSTNESS_CANDIDATE_DESIGN",
            "deterministic_duplicate_key_mod5_stress_reserve_for_robustness_and_negative_controls",
        )
    return (
        "SEALED_VALIDATION_CANDIDATE_DESIGN",
        "accepted_primary_economic_group_asof_input_only_no_discovery_exposure",
    )


def build_row_partition(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    partition_rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidate_rows, start=1):
        assignment, reason = partition_for_row(row)
        included_hashes = row.get("included_bar_hashes", [])
        partition_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "candidate_input_row_id": row["candidate_input_row_id"],
                "source_row_id": row["candidate_input_row_id"],
                "source_packet_row_hash": row["row_hash"],
                "symbol": row["symbol"],
                "source_file_name": row["source_file_name"],
                "canonical_economic_group": row["canonical_economic_group"],
                "decision_asof_utc": row["decision_asof_utc"],
                "bar_window_start_utc": row["bar_window_start_utc"],
                "bar_window_end_utc": row["bar_window_end_utc"],
                "included_bar_hashes": included_hashes,
                "included_bar_hash_count": len(included_hashes),
                "included_bar_hashes_sha256": sha256_obj(included_hashes),
                "partition_assignment": assignment,
                "reason_code": reason,
                "duplicate_proxy_denominator_key": row["duplicate_key"],
                "duplicate_key_fields": row["duplicate_key_fields"],
                "discovery_exposure_flag": False,
                "allowed_future_use": [
                    "future_g12_design_audit_review",
                    "future_validation_execution_only_after_g12_design_audit_acceptance",
                    "future_stress_robustness_if_partition_assignment_allows",
                ],
                "forbidden_future_use": [
                    "current_lane_validation_execution",
                    "current_lane_scored_candidate_generation",
                    "current_lane_replay_path_label_result_outcomes",
                    "current_lane_performance_or_cost_scoring",
                    "broker_account_order_history_deal_position_evidence",
                    "promotion_or_live_behavior_change",
                ],
                "safe_flags": {
                    "promotion_verdict": "NO_PROMOTION_VERDICT",
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "live_effect": False,
                },
                "row_partition_sequence": index,
            }
        )
    return partition_rows


def common_input_summary() -> dict[str, Any]:
    return {
        "mandatory_inputs": {key: path_inventory(path) for key, path in MANDATORY_INPUTS.items()},
        "mandatory_directories": {key: path_inventory(path) for key, path in MANDATORY_DIRS.items()},
    }


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)

    git_head = run_git(["rev-parse", "--short", "HEAD"])
    git_log = run_git(["log", "-6", "--oneline"])
    dirty_audit = dirty_scope_audit()
    input_summary = common_input_summary()

    packet_decision = load_json(MANDATORY_INPUTS["g12_packet_decision_ledger"])
    packet_completion = load_json(MANDATORY_INPUTS["g12_packet_completion_audit"])
    warning_review = load_json(MANDATORY_INPUTS["g12_packet_warning_repair_review"])
    duplicate_review = load_json(MANDATORY_INPUTS["g12_packet_duplicate_proxy_review"])
    discovery_review = load_json(MANDATORY_INPUTS["g12_packet_discovery_baseline_review"])
    bar_manifest = load_json(MANDATORY_INPUTS["packet_bar_manifest"])
    candidate_manifest = load_json(MANDATORY_INPUTS["packet_candidate_manifest"])
    duplicate_ledger = load_json(MANDATORY_INPUTS["packet_duplicate_proxy_ledger"])
    discovery_audit = load_json(MANDATORY_INPUTS["packet_discovery_baseline_audit"])
    contract_decision = load_json(MANDATORY_INPUTS["contract_decision_ledger"])
    candidate_rows = load_jsonl(MANDATORY_INPUTS["packet_candidate_rows"])
    row_partition = build_row_partition(candidate_rows)

    partition_counts = Counter(row["partition_assignment"] for row in row_partition)
    group_counts = Counter(row["canonical_economic_group"] for row in row_partition)
    symbol_counts = Counter(row["symbol"] for row in row_partition)
    source_counts = Counter(row["source_file_name"] for row in row_partition)

    exact_count_checks = [
        {
            "check_id": "source_control_bar_rows",
            "expected": EXPECTED["bar_row_count"],
            "actual": bar_manifest.get("bar_row_count"),
            "source": repo_path(MANDATORY_INPUTS["packet_bar_manifest"]),
            "status": "PASS" if bar_manifest.get("bar_row_count") == EXPECTED["bar_row_count"] else "FAIL",
        },
        {
            "check_id": "candidate_generator_input_only_rows",
            "expected": EXPECTED["candidate_input_row_count"],
            "actual": len(candidate_rows),
            "source": repo_path(MANDATORY_INPUTS["packet_candidate_rows"]),
            "status": "PASS" if len(candidate_rows) == EXPECTED["candidate_input_row_count"] else "FAIL",
        },
        {
            "check_id": "accepted_bounded_scid_segments",
            "expected": EXPECTED["accepted_scid_segment_count"],
            "actual": len(bar_manifest.get("segment_scan_summaries", [])),
            "source": repo_path(MANDATORY_INPUTS["packet_bar_manifest"]),
            "status": "PASS"
            if len(bar_manifest.get("segment_scan_summaries", [])) == EXPECTED["accepted_scid_segment_count"]
            else "FAIL",
        },
        {
            "check_id": "candidate_denominator_economic_groups",
            "expected": EXPECTED["candidate_denominator_group_count"],
            "actual": len(duplicate_ledger.get("candidate_counts_by_group", {})),
            "source": repo_path(MANDATORY_INPUTS["packet_duplicate_proxy_ledger"]),
            "status": "PASS"
            if len(duplicate_ledger.get("candidate_counts_by_group", {}))
            == EXPECTED["candidate_denominator_group_count"]
            else "FAIL",
        },
        {
            "check_id": "discovery_exclusions",
            "expected": EXPECTED["discovery_exclusion_count"],
            "actual": discovery_audit.get("selected_discovery_source_count"),
            "source": repo_path(MANDATORY_INPUTS["packet_discovery_baseline_audit"]),
            "status": "PASS"
            if discovery_audit.get("selected_discovery_source_count") == EXPECTED["discovery_exclusion_count"]
            else "FAIL",
        },
        {
            "check_id": "adversarial_baselines",
            "expected": EXPECTED["baseline_count"],
            "actual": len(discovery_audit.get("adversarial_baseline_ids", [])),
            "source": repo_path(MANDATORY_INPUTS["packet_discovery_baseline_audit"]),
            "status": "PASS"
            if sorted(discovery_audit.get("adversarial_baseline_ids", [])) == sorted(BASELINES)
            else "FAIL",
        },
    ]
    all_counts_reconciled = all(row["status"] == "PASS" for row in exact_count_checks)
    row_partition_path = write_jsonl(
        f"{PREFIX}_ROW_PARTITION_LEDGER_{DATE_TAG}.jsonl",
        row_partition,
    )

    context_anchor_json = safe_payload(
        "synthesis_context_anchor",
        {
            "controlling_prompt_path": repo_path(CONTROLLING_PROMPT),
            "current_head": git_head["stdout"][0] if git_head["stdout"] else None,
            "recent_commits": git_log["stdout"],
            "dirty_state_summary": dirty_audit["summary"],
            "evidence_class_boundary": {
                "allowed": [
                    "source_control_evidence_chain_synthesis",
                    "row_partition_design",
                    "no_leak_duplicate_proxy_denominator_design",
                    "adversarial_baseline_and_robustness_planning",
                    "next_g12_design_audit_prompt",
                ],
                "forbidden": [
                    "validation_execution",
                    "scored_candidate_generation",
                    "replay_path_label_result_outcomes",
                    "performance_or_cost_scoring",
                    "promotion",
                    "ai_api",
                    "paid_vendor_access",
                    "broker_account_order_history_deal_position_evidence",
                    "raw_market_data_blob_commit",
                    "remote_push",
                    "prompt_config_risk_safety_execution_canary_selector_edits",
                    "live_restarts_or_live_behavior_changes",
                ],
            },
            **input_summary,
        },
    )
    write_json(f"{PREFIX}_SYNTHESIS_CONTEXT_ANCHOR_{DATE_TAG}.json", context_anchor_json)
    write_md(
        f"{PREFIX}_SYNTHESIS_CONTEXT_ANCHOR_{DATE_TAG}.md",
        "# G0 SCID As-Of Synthesis Context Anchor\n\n"
        f"- Route: `{ROUTE_ID}`\n"
        f"- Evidence class: `{EVIDENCE_CLASS}`\n"
        f"- Controlling prompt: `{repo_path(CONTROLLING_PROMPT)}`\n"
        f"- HEAD at build: `{context_anchor_json['current_head']}`\n"
        f"- Dirty scoped entries: `{dirty_audit['summary']['scoped_entry_count']}`\n"
        "- Boundary: source-control synthesis and sealed-validation design only; no validation execution, "
        "result/path labels, scoring, AI/API, broker evidence, promotion, or live behavior.\n",
    )

    decision_ledger = safe_payload(
        "synthesis_decision_ledger",
        {
            "terminal_decision": TERMINAL_DECISION,
            "accepted_g12_terminal_decision": packet_decision.get("terminal_decision"),
            "accepted_source_control_packet_only": packet_decision.get("accepted_source_control_packet_only"),
            "accepted_validation_execution": False,
            "accepted_scored_candidate_generation": False,
            "accepted_replay_path_label_result_outcomes": False,
            "accepted_performance_or_cost_scoring": False,
            "accepted_promotion": False,
            "design_acceptance_blockers": []
            if all_counts_reconciled
            and packet_decision.get("terminal_blockers") == []
            and packet_decision.get("terminal_decision")
            == "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY"
            else ["accepted_packet_reconciliation_failed"],
            "required_design_question_answers": [
                {
                    "question_id": "Q1",
                    "ledger": f"{PREFIX}_ROW_PARTITION_LEDGER_{DATE_TAG}.jsonl",
                    "answer_status": "machine_checkable_row_level_coverage",
                },
                {
                    "question_id": "Q2",
                    "ledger": f"{PREFIX}_VALIDATION_DESIGN_RULEBOOK_{DATE_TAG}.json",
                    "answer_status": "partition_status_freeze",
                },
                {
                    "question_id": "Q3",
                    "ledger": f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_RULES_{DATE_TAG}.json",
                    "answer_status": "duplicate_proxy_denominator_freeze",
                },
                {
                    "question_id": "Q4",
                    "ledger": f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_RULES_{DATE_TAG}.json",
                    "answer_status": "gc_over_mgc_and_ym_over_mym_policy_freeze",
                },
                {
                    "question_id": "Q5",
                    "ledger": f"{PREFIX}_NOLEAK_FIELD_CONTRACT_{DATE_TAG}.json",
                    "answer_status": "allowlist_and_forbidden_scan_freeze",
                },
                {
                    "question_id": "Q6",
                    "ledger": f"{PREFIX}_VALIDATION_DESIGN_RULEBOOK_{DATE_TAG}.json",
                    "answer_status": "candidate_generation_constraints_freeze",
                },
                {
                    "question_id": "Q7",
                    "ledger": f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json",
                    "answer_status": "hypothesis_family_route_freeze",
                },
                {
                    "question_id": "Q8",
                    "ledger": f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json",
                    "answer_status": "anti_boxing_route_freeze",
                },
                {
                    "question_id": "Q9",
                    "ledger": f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json",
                    "answer_status": "science_horizon_family_coverage",
                },
                {
                    "question_id": "Q10",
                    "ledger": f"{PREFIX}_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_{DATE_TAG}.json",
                    "answer_status": "baseline_placebo_negative_control_freeze",
                },
                {
                    "question_id": "Q11",
                    "ledger": f"{PREFIX}_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_{DATE_TAG}.json",
                    "answer_status": "robustness_stress_plan_freeze",
                },
                {
                    "question_id": "Q12",
                    "ledger": f"{PREFIX}_MULTIPLE_TESTING_DEBT_LEDGER_{DATE_TAG}.json",
                    "answer_status": "multiple_testing_debt_carry_forward",
                },
                {
                    "question_id": "Q13",
                    "ledger": f"{PREFIX}_FALSIFICATION_STOP_CONDITIONS_{DATE_TAG}.json",
                    "answer_status": "falsification_stop_freeze",
                },
                {
                    "question_id": "Q14",
                    "ledger": repo_path(NEXT_G12_PROMPT),
                    "answer_status": "next_g12_design_audit_only",
                },
            ],
        },
    )
    write_json(f"{PREFIX}_SYNTHESIS_DECISION_LEDGER_{DATE_TAG}.json", decision_ledger)

    reconciliation = safe_payload(
        "accepted_packet_reconciliation",
        {
            "terminal_decision": packet_decision.get("terminal_decision"),
            "exact_count_checks": exact_count_checks,
            "all_counts_reconciled": all_counts_reconciled,
            "candidate_counts_by_group": duplicate_ledger.get("candidate_counts_by_group", {}),
            "bar_counts_by_symbol": bar_manifest.get("bar_counts_by_symbol", {}),
            "accepted_bounded_scid_segments": [
                {
                    "symbol": row.get("symbol"),
                    "source_file_name": row.get("source_file_name"),
                    "canonical_economic_group": row.get("canonical_economic_group"),
                    "decision_asof_utc": row.get("decision_asof_utc"),
                    "dense_bar_count": row.get("dense_bar_count"),
                    "record_present_bar_count": row.get("record_present_bar_count"),
                    "empty_or_gap_bar_count": row.get("empty_or_gap_bar_count"),
                    "records_read_matches_manifest": row.get("records_read_matches_manifest"),
                }
                for row in bar_manifest.get("segment_scan_summaries", [])
            ],
            "warnings_repaired": {
                "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW": warning_review.get("checks", {}).get(
                    "forbidden_warning_id_repaired"
                )
                and warning_review.get("checks", {}).get("bar_window_fields_allowed")
                and warning_review.get("checks", {}).get("true_forbidden_examples_rejected"),
                "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE": warning_review.get("checks", {}).get(
                    "hard_floor_warning_id_repaired"
                )
                and warning_review.get("checks", {}).get("hard_floor_required_cases_covered"),
            },
            "terminal_blockers": packet_decision.get("terminal_blockers", []),
            "no_terminal_packet_blockers": packet_decision.get("terminal_blockers", []) == [],
            "safe_flags_closed_in_accepted_packet": {
                "promotion_verdict": packet_decision.get("promotion_verdict"),
                "validation_safe": packet_decision.get("validation_safe"),
                "outcome_review_opened": packet_decision.get("outcome_review_opened"),
                "live_effect": packet_decision.get("live_effect"),
            },
            "source_refs": {
                "decision_ledger": repo_path(MANDATORY_INPUTS["g12_packet_decision_ledger"]),
                "completion_audit": repo_path(MANDATORY_INPUTS["g12_packet_completion_audit"]),
                "bar_manifest": repo_path(MANDATORY_INPUTS["packet_bar_manifest"]),
                "candidate_manifest": repo_path(MANDATORY_INPUTS["packet_candidate_manifest"]),
                "duplicate_proxy": repo_path(MANDATORY_INPUTS["packet_duplicate_proxy_ledger"]),
                "discovery_baseline": repo_path(MANDATORY_INPUTS["packet_discovery_baseline_audit"]),
            },
        },
    )
    write_json(f"{PREFIX}_ACCEPTED_PACKET_RECONCILIATION_{DATE_TAG}.json", reconciliation)

    noleak_contract = safe_payload(
        "noleak_field_contract",
        {
            "candidate_input_allowed_fields": sorted(candidate_rows[0].keys()),
            "candidate_input_allowed_field_count": len(candidate_rows[0].keys()),
            "future_validation_allowlist_policy": "future validation may inherit only as-of source-control fields; any result/path/broker/outcome fields require a separate accepted evidence-class gate",
            "forbidden_candidate_field_tokens": [
                "actual_r",
                "account",
                "broker",
                "cost",
                "deal",
                "expectancy",
                "history",
                "label",
                "order",
                "path",
                "performance",
                "pnl",
                "position",
                "profit",
                "result",
                "score",
                "slippage",
                "win",
            ],
            "explicit_allowed_control_tokens": [
                "candidate_input_only_status",
                "bar_window_start_utc",
                "bar_window_end_utc",
                "forbidden_future_use",
                "opens_result_scoring",
                "opens_broker_account_order_history_deal_position_evidence",
            ],
            "scan_scope": "candidate_input_rows_and_row_partition_candidate_derived_fields_only",
            "current_packet_forbidden_scan_clean": candidate_manifest.get("candidate_summary", {}).get(
                "all_forbidden_scans_pass"
            )
            is True,
            "future_validation_scan_rules": [
                "scan field names tokenized by snake_case and phrase list before validation execution",
                "allow bar_window_start_utc and bar_window_end_utc despite win substring",
                "reject post-outcome path/result/broker/account/order/deal/position/performance/cost fields unless a separate evidence class accepts them",
                "fail closed on unknown fields not present in this contract",
            ],
        },
    )
    write_json(f"{PREFIX}_NOLEAK_FIELD_CONTRACT_{DATE_TAG}.json", noleak_contract)

    duplicate_rules = safe_payload(
        "duplicate_proxy_denominator_rules",
        {
            "primary_future_validation_denominator": "duplicate_proxy_denominator_key",
            "secondary_diagnostics": [
                "candidate_input_row_id",
                "canonical_economic_group",
                "symbol_session_window",
                "decision_asof_utc",
            ],
            "candidate_denominator_economic_groups": duplicate_ledger.get("candidate_counts_by_group", {}),
            "candidate_denominator_group_count": len(duplicate_ledger.get("candidate_counts_by_group", {})),
            "bar_layer_preserved_sources": duplicate_ledger.get("bar_rows_preserve_all_9_sources", []),
            "candidate_primary_sources": duplicate_ledger.get("candidate_rows_count_primary_sources_only", []),
            "primary_counting_source_by_group": duplicate_ledger.get("primary_counting_source_by_group", {}),
            "secondary_proxy_sources_excluded_from_candidate_denominator": duplicate_ledger.get(
                "secondary_proxy_sources_excluded_from_candidate_denominator", []
            ),
            "proxy_policy": [
                "preserve all 9 SCID sources as source bars and context",
                "count candidates under 7 primary canonical economic groups",
                "XAUUSD uses GC over MGC as denominator source",
                "US30 uses YM over MYM as denominator source",
                "secondary proxies may annotate source context but cannot add denominator rows",
            ],
            "row_partition_duplicate_key_unique_count": len({row["duplicate_proxy_denominator_key"] for row in row_partition}),
            "row_partition_candidate_row_count": len(row_partition),
            "duplicate_key_collisions": len(row_partition)
            - len({row["duplicate_proxy_denominator_key"] for row in row_partition}),
        },
    )
    write_json(f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_RULES_{DATE_TAG}.json", duplicate_rules)

    validation_rulebook = safe_payload(
        "validation_design_rulebook",
        {
            "terminal_boundary": "DESIGN_ONLY_REQUIRES_G12_ACCEPTANCE_BEFORE_VALIDATION_EXECUTION",
            "row_partition_assignments_allowed": PARTITIONS,
            "row_partition_counts": dict(sorted(partition_counts.items())),
            "row_partition_policy": {
                "SEALED_VALIDATION_CANDIDATE_DESIGN": "eligible input-only rows for future sealed validation after G12 design audit acceptance",
                "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": "input-only rows reserved for future robustness, placebo, perturbation, and negative-control work",
                "DISCOVERY_EXPOSED_EXCLUDED": "not used by accepted candidate packet; 365 discovery-source exclusions remain in separate contaminated ledger",
                "CONTAMINATED_EXCLUDED": "fail-closed status for any future row found to overlap discovery/result/outcome exposure",
                "FORBIDDEN_FOR_THIS_EVIDENCE_CLASS": "fail-closed status for any row requiring validation/result/broker/live evidence",
            },
            "candidate_generation_constraints_to_freeze": [
                "source segment byte ranges and source hashes fixed before candidate generation",
                "M15 left-closed/right-open interval policy",
                "bar_end_exclusive_utc must be <= decision_asof_utc",
                "empty/gap bars fail closed and cannot become candidate eligible",
                "candidate rows remain CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION",
                "duplicate_key_fields stay frozen before validation",
                "no scored candidate, path label, replay result, or broker/account field may enter the packet",
            ],
            "discovery_exclusions": {
                "count": discovery_audit.get("selected_discovery_source_count"),
                "policy": "outside future sealed validation; usable only as discovery/context/stress after explicit design",
                "source_ref": repo_path(MANDATORY_INPUTS["packet_discovery_baseline_audit"]),
            },
            "planned_metric_families_design_only": [
                "expectancy_family",
                "win_rate_family",
                "profit_factor_family",
                "drawdown_family",
                "time_under_water_family",
                "tail_behavior_family",
                "cost_spread_slippage_stress_family",
                "regime_slice_family",
            ],
            "metric_family_status": "names_only_no_computation_no_scoring_in_this_lane",
            "future_gate_required": repo_path(NEXT_G12_PROMPT),
        },
    )
    write_json(f"{PREFIX}_VALIDATION_DESIGN_RULEBOOK_{DATE_TAG}.json", validation_rulebook)

    baseline_plan = safe_payload(
        "adversarial_baseline_and_robustness_plan",
        {
            "four_adversarial_baselines_preserved": BASELINES,
            "baseline_count": len(BASELINES),
            "baseline_source_refs": {
                "packet_discovery_audit": repo_path(MANDATORY_INPUTS["packet_discovery_baseline_audit"]),
                "g0_fpb_baseline_packet": repo_path(MANDATORY_INPUTS["g0_fpb_baseline_packet"]),
                "fpb_discovery_baseline_control": repo_path(MANDATORY_INPUTS["fpb_discovery_baseline_control"]),
            },
            "placebo_and_negative_controls_required": [
                "random_session_control",
                "shifted_entry_control",
                "simple_momentum_continuation_control",
                "simple_mean_reversion_control",
                "session_only_control",
                "volatility_only_control",
                "duplicate_proxy_shuffle_control",
                "source_segment_shuffle_control",
            ],
            "robustness_tests_required_before_promotion_discussion": [
                "purged_embargoed_time_splits",
                "walk_forward_plan",
                "symbol_holdout",
                "session_holdout",
                "regime_holdout",
                "delayed_entry_perturbation",
                "delayed_exit_perturbation",
                "spread_cost_stress_design",
                "random_missed_trade_stress_design",
                "outlier_removal",
                "best_window_removal",
                "duplicate_concentration_diagnostics",
                "proxy_source_concentration_diagnostics",
                "same_bar_or_gap_fail_closed_diagnostics",
            ],
            "all_tests_status": "DESIGN_ONLY_NOT_EXECUTED",
        },
    )
    write_json(f"{PREFIX}_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_{DATE_TAG}.json", baseline_plan)

    multiple_testing = safe_payload(
        "multiple_testing_debt_ledger",
        {
            "debt_sources_read": [
                repo_path(MANDATORY_INPUTS["g0_fpb_multiple_testing"]),
                repo_path(MANDATORY_INPUTS["g0_fpb_synthesis_multiple_testing"]),
                repo_path(MANDATORY_INPUTS["g12_fpb_result_audit"]),
                repo_path(MANDATORY_INPUTS["fpb_discovery_completion_audit"]),
            ],
            "known_discovery_families": [
                "adjacent_range_compression_breakout",
                "ob_retest",
                "opening_drive_no_fill_lifecycle",
                "fvg_fill",
                "liquidity_stop_run_context",
                "session_kz_sweep",
                "breaker_re_entry",
                "baseline_random_session_control",
                "baseline_shifted_entry_control",
                "baseline_momentum_continuation",
                "baseline_mean_reversion",
            ],
            "debt_policy": [
                "future validation must carry FPB discovery family count and rejected/deferred branch count",
                "future G12 audit must verify variant count before result opening",
                "same packet may not tune thresholds and validate on the same partition",
                "report DSR/PBO/effective-N diagnostics only in the future validation/result evidence class",
                "this G0 lane computes no p-values, effect sizes, R, PnL, win-rate, expectancy, performance, cost, or slippage outcomes",
            ],
            "selection_rule_freeze": "candidate packet route is source-control only; future hypothesis families must be preregistered before opening outcomes",
            "status": "DEBT_RECORDED_NO_RESULT_INTERPRETATION",
        },
    )
    write_json(f"{PREFIX}_MULTIPLE_TESTING_DEBT_LEDGER_{DATE_TAG}.json", multiple_testing)

    science_horizon = safe_payload(
        "science_horizon_route_ledger",
        {
            "anti_boxing_rule": "do not reduce this validation design to OB-only; packet can support broader source-safe hypothesis families after G12 design audit",
            "families": [
                {
                    "family": "path_geometry_and_structural_distance",
                    "from_packet_status": "REPRESENTABLE_FROM_ASOF_BAR_HASH_WINDOWS_WITH_FUTURE_FEATURE_CONTRACT",
                    "requires_source_expansion": False,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "session_kill_zone_calendar_time_of_day",
                    "from_packet_status": "REPRESENTABLE_FROM_DECISION_ASOF_AND_SYMBOL_SESSION_RULES",
                    "requires_source_expansion": False,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "volatility_clustering_first_passage_tail_hazard_timing",
                    "from_packet_status": "PARTIALLY_REPRESENTABLE_FROM_M15_SOURCE_BARS",
                    "requires_source_expansion": True,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "market_microstructure_and_scid_source_proxies",
                    "from_packet_status": "SCID_SOURCE_PROXY_CONTEXT_ONLY_NO_ORDERBOOK_OR_BROKER_FILL_TRUTH",
                    "requires_source_expansion": True,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "liquidity_trapped_trader_stop_cascade",
                    "from_packet_status": "HYPOTHESIS_DESIGN_ONLY_FROM_SOURCE_BARS_AND_FUTURE_STRUCTURAL_FEATURES",
                    "requires_source_expansion": True,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "regime_and_cross_market_context",
                    "from_packet_status": "PARTIAL_CONTEXT_FROM_SYMBOL_GROUPS_AND_TIME; CROSS_MARKET_JOIN_NEEDS_CONTRACT",
                    "requires_source_expansion": True,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "execution_cost_realism",
                    "from_packet_status": "DESIGN_ONLY; NO BROKER OR COST EVIDENCE IN THIS LANE",
                    "requires_source_expansion": True,
                    "forbidden_until_separate_contract": True,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "ml_meta_labeling_and_adversarial_baselines",
                    "from_packet_status": "FEATURE_AND_BASELINE_DESIGN_ONLY; NO LABELS OPENED",
                    "requires_source_expansion": True,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
                {
                    "family": "current_gtos_ob_mechanism_comparator",
                    "from_packet_status": "COMPARATOR_ONLY_NOT_BOXING_LIMIT",
                    "requires_source_expansion": False,
                    "forbidden_until_separate_contract": False,
                    "claim_status": "NO_CLAIM_WORKS",
                },
            ],
        },
    )
    write_json(f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json", science_horizon)

    falsification = safe_payload(
        "falsification_stop_conditions",
        {
            "future_lane_stop_conditions": [
                "any accepted packet count differs from 7567 bars, 3014 candidate rows, 9 segments, 7 denominator groups, 365 exclusions, or 4 baselines",
                "any candidate row appears zero times or more than once in the row partition ledger",
                "any row needs a result/path-label/broker/order/account field before G12 design acceptance",
                "any GC/MGC or YM/MYM proxy row inflates denominator count",
                "any discovery-exposed or contaminated source enters sealed validation",
                "any same evidence-class blocker remains vague instead of exact source/control requirement",
                "any validation execution prompt is emitted before G12 design audit acceptance",
                "any prompt/config/risk/safety/execution/canary/selector/live behavior edit appears in scoped diff",
                "any future result lane attempts self-rescue with post-hoc thresholds after opening outcomes",
            ],
            "interpretation_rule": "future validation lane must pause or route back to source-control repair when a stop condition fires",
            "status": "DESIGN_ONLY_NOT_EXECUTED",
        },
    )
    write_json(f"{PREFIX}_FALSIFICATION_STOP_CONDITIONS_{DATE_TAG}.json", falsification)

    redteam = safe_payload(
        "saturation_redteam_ledger",
        {
            "redteam_questions": [
                {
                    "question": "What exact mistake would make input-only source-control rows look like validation rows?",
                    "answer": "Treating candidate_input_only_status as a result status or adding path/result/broker fields to row partitions. The no-leak contract and verifier scan row-derived fields and keep validation_safe=false.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What exact duplicate/proxy mistake could inflate sample size?",
                    "answer": "Counting XAUUSD_GC and XAUUSD_MGC, or US30_YM and US30_MYM, separately. The denominator is duplicate_proxy_denominator_key under seven economic groups with GC and YM as primary sources.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What exact discovery exposure could leak into sealed validation?",
                    "answer": "The 365 FPB discovery-source exclusions or their selected source hashes entering future validation. This route keeps those rows outside the 3014 candidate packet and records them as contaminated for validation.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What exact field would be leakage?",
                    "answer": "Any post-outcome, broker-realized, hidden-label, path-label, future-context, cost, slippage, account, order, deal, position, result, score, PnL, or performance field in candidate rows.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What exact row, source, or segment mismatch would invalidate the packet?",
                    "answer": "Any count mismatch against 7567 bars, 3014 candidates, 9 segments, 7 denominator groups, 365 exclusions, four baselines, repaired warnings, or nonzero terminal blockers.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What dirty-worktree or live-runtime file could confuse scope?",
                    "answer": "Existing src, pipeline_state, knowledge_base, data/account_history, and shadow_logs dirt. Dirty audit records those as unrelated info only; scoped diff is restricted to this G0 route, next G12 prompt, and context refresh files.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What exact evidence-class gate is required before validation execution?",
                    "answer": "The emitted G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT prompt must accept this design. No runnable validation execution prompt is emitted here.",
                    "same_evidence_class_gap_remaining": False,
                },
                {
                    "question": "What same-evidence-class ambiguity remains?",
                    "answer": "None known after direct reconciliation and row-level partitioning. Future outcome labels, broker evidence, cost scoring, and promotion are separate evidence classes by design, not unresolved G0 work.",
                    "same_evidence_class_gap_remaining": False,
                },
            ],
            "remaining_same_evidence_class_gaps": [],
            "remaining_vague_blockers": [],
        },
    )
    write_json(f"{PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json", redteam)

    next_ranking = safe_payload(
        "next_route_ranking",
        {
            "ranked_routes": [
                {
                    "rank": 1,
                    "route": "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT",
                    "prompt_path": repo_path(NEXT_G12_PROMPT),
                    "reason": "required independent design audit before validation execution or result scoring can open",
                    "opens_validation_execution": False,
                },
                {
                    "rank": 2,
                    "route": "DORMANT_FUTURE_VALIDATION_EXECUTION_SKETCH",
                    "prompt_path": None,
                    "reason": "may be drafted only after G12 design-audit acceptance; not emitted by this route",
                    "opens_validation_execution": False,
                },
                {
                    "rank": 3,
                    "route": "SOURCE_CONTROL_REPAIR_IF_G12_REJECTS",
                    "prompt_path": None,
                    "reason": "fallback if G12 design audit finds count, partition, no-leak, duplicate, or proxy defect",
                    "opens_validation_execution": False,
                },
            ],
            "active_next_route": "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT",
            "validation_execution_prompt_emitted": False,
        },
    )
    write_json(f"{PREFIX}_NEXT_ROUTE_RANKING_{DATE_TAG}.json", next_ranking)
    write_md(
        f"{PREFIX}_NEXT_ROUTE_RANKING_{DATE_TAG}.md",
        "# G0 SCID As-Of Next Route Ranking\n\n"
        "1. `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT` - independent audit of this design packet only.\n"
        "2. Dormant future validation execution sketch - not emitted and not active until G12 accepts the design.\n"
        "3. Source-control repair - fallback if G12 rejects counts, partition, no-leak, duplicate, or proxy rules.\n\n"
        "`NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.\n",
    )

    prompt_text = f"""# G12 SCID As-Of Sealed Validation Design Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: G12 audit of G0 SCID as-of sealed-validation design only
Evidence class: `G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_ONLY`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit the G0 SCID as-of source-control synthesis and sealed-validation design packet under:

`research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/`

This audit must decide whether the design packet is acceptable as design-only control evidence before any validation execution or result scoring can open.

## Mandatory Boundaries

Forbidden: validation execution, scored candidate generation, replay/path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blob commits, remote push, prompt/config/risk/safety/execution/canary/selector edits, live restarts, or live behavior changes.

## Required Audit Checks

- Reconcile exact accepted packet counts: `7,567` bars, `3,014` candidate input-only rows, `9` SCID segments, `7` denominator economic groups, `365` discovery exclusions, and four adversarial baselines.
- Verify terminal G12 packet decision remains `ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY`.
- Verify both repaired warnings remain closed: `FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW` and `TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE`.
- Verify every `3,014` candidate input row appears exactly once in `G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl`.
- Verify row partitions, duplicate/proxy denominator rules, no-leak field contract, science-horizon anti-boxing, multiple-testing debt, robustness plan, falsification stops, and saturation red-team are machine-checkable.
- Verify the next route is this G12 design audit only, not validation execution.
- Verify scoped diff contains no forbidden live-surface or raw market-data blob changes.
- Run the route verifier and focused tests.

## Terminal Decisions

Allowed terminal decisions:

- `ACCEPT_G0_SCID_ASOF_SEALED_VALIDATION_DESIGN_PACKET_ONLY`
- `REJECT_ROUTE_TO_SOURCE_CONTROL_REPAIR`

Acceptance is design-only. It must not open validation execution, result scoring, promotion, or live behavior.
"""
    NEXT_G12_PROMPT.write_text(prompt_text, encoding="utf-8")

    artifact_files = [
        f"{PREFIX}_SYNTHESIS_CONTEXT_ANCHOR_{DATE_TAG}.md",
        f"{PREFIX}_SYNTHESIS_CONTEXT_ANCHOR_{DATE_TAG}.json",
        f"{PREFIX}_SYNTHESIS_DECISION_LEDGER_{DATE_TAG}.json",
        f"{PREFIX}_ACCEPTED_PACKET_RECONCILIATION_{DATE_TAG}.json",
        f"{PREFIX}_ROW_PARTITION_LEDGER_{DATE_TAG}.jsonl",
        f"{PREFIX}_VALIDATION_DESIGN_RULEBOOK_{DATE_TAG}.json",
        f"{PREFIX}_NOLEAK_FIELD_CONTRACT_{DATE_TAG}.json",
        f"{PREFIX}_DUPLICATE_PROXY_DENOMINATOR_RULES_{DATE_TAG}.json",
        f"{PREFIX}_ADVERSARIAL_BASELINE_AND_ROBUSTNESS_PLAN_{DATE_TAG}.json",
        f"{PREFIX}_MULTIPLE_TESTING_DEBT_LEDGER_{DATE_TAG}.json",
        f"{PREFIX}_SCIENCE_HORIZON_ROUTE_LEDGER_{DATE_TAG}.json",
        f"{PREFIX}_FALSIFICATION_STOP_CONDITIONS_{DATE_TAG}.json",
        f"{PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
        f"{PREFIX}_NEXT_ROUTE_RANKING_{DATE_TAG}.md",
        f"{PREFIX}_NEXT_ROUTE_RANKING_{DATE_TAG}.json",
    ]
    completion_checklist = [
        {
            "requirement": "mandatory inputs read or exact blockers recorded",
            "artifact": f"{PREFIX}_SYNTHESIS_CONTEXT_ANCHOR_{DATE_TAG}.json",
            "status": "DONE"
            if all(row.get("exists") for row in input_summary["mandatory_inputs"].values())
            and all(row.get("exists") for row in input_summary["mandatory_directories"].values())
            else "FAIL",
        },
        {
            "requirement": "accepted packet evidence chain reconciled with exact counts",
            "artifact": f"{PREFIX}_ACCEPTED_PACKET_RECONCILIATION_{DATE_TAG}.json",
            "status": "DONE" if all_counts_reconciled else "FAIL",
        },
        {
            "requirement": "3014 candidate input rows appear exactly once in row partition ledger",
            "artifact": f"{PREFIX}_ROW_PARTITION_LEDGER_{DATE_TAG}.jsonl",
            "status": "DONE"
            if len(row_partition) == EXPECTED["candidate_input_row_count"]
            and len({row["candidate_input_row_id"] for row in row_partition}) == len(row_partition)
            else "FAIL",
        },
        {
            "requirement": "no validation execution or forbidden evidence class opened",
            "artifact": f"{PREFIX}_SYNTHESIS_DECISION_LEDGER_{DATE_TAG}.json",
            "status": "DONE",
        },
        {
            "requirement": "partition, denominator, no-leak, adversarial baseline, robustness, multiple-testing, science-horizon, and stop-condition rules frozen",
            "artifact": "design ledgers",
            "status": "DONE",
        },
        {
            "requirement": "next route is G12 design audit prompt only",
            "artifact": repo_path(NEXT_G12_PROMPT),
            "status": "DONE" if NEXT_G12_PROMPT.exists() else "FAIL",
        },
        {
            "requirement": "safe flags closed",
            "artifact": "all generated json ledgers",
            "status": "DONE",
        },
    ]
    can_mark_goal_complete_pre_verifier = all(item["status"] == "DONE" for item in completion_checklist)
    completion_json = safe_payload(
        "completion_audit",
        {
            "objective_restatement": "Synthesize accepted G12 SCID as-of packet source-control evidence and design the strongest next sealed-validation route without executing validation or scoring.",
            "prompt_to_artifact_checklist": completion_checklist,
            "row_partition_summary": {
                "row_count": len(row_partition),
                "unique_candidate_input_row_ids": len({row["candidate_input_row_id"] for row in row_partition}),
                "partition_counts": dict(sorted(partition_counts.items())),
                "group_counts": dict(sorted(group_counts.items())),
                "symbol_counts": dict(sorted(symbol_counts.items())),
                "source_counts": dict(sorted(source_counts.items())),
                "row_partition_sha256": sha256_file(row_partition_path),
            },
            "dirty_scope_audit": dirty_audit,
            "completion_standard_satisfied": can_mark_goal_complete_pre_verifier,
            "can_mark_goal_complete": False,
            "can_mark_goal_complete_reason": "standalone verifier must emit ok=true and can_mark_goal_complete=true after this builder",
        },
    )
    write_json(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion_json)
    write_md(
        f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
        "# G0 SCID As-Of Completion Audit\n\n"
        f"- Exact-count reconciliation: `{all_counts_reconciled}`\n"
        f"- Row partition rows: `{len(row_partition)}`\n"
        f"- Partition counts: `{dict(sorted(partition_counts.items()))}`\n"
        "- Verification state: pending standalone verifier result.\n"
        "- Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n",
    )

    manifest = safe_payload(
        "output_manifest",
        {
            "artifacts": [
                {
                    "path": repo_path(ROUTE_DIR / name),
                    "sha256": sha256_file(ROUTE_DIR / name),
                    "exists": (ROUTE_DIR / name).exists(),
                }
                for name in artifact_files
                + [
                    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
                    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
                ]
            ],
            "next_prompt": {"path": repo_path(NEXT_G12_PROMPT), "sha256": sha256_file(NEXT_G12_PROMPT)},
        },
    )
    write_json(f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", manifest)

    return {
        "ok": can_mark_goal_complete_pre_verifier,
        "route_dir": repo_path(ROUTE_DIR),
        "row_partition_rows": len(row_partition),
        "partition_counts": dict(sorted(partition_counts.items())),
        "next_prompt": repo_path(NEXT_G12_PROMPT),
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
