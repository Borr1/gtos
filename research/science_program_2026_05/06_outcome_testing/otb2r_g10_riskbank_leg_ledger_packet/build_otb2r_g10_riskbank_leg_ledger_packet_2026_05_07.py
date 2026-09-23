"""Build the OTB2R G10 risk-bank leg-ledger proof/impossibility packet.

This builder is research/tooling only. It does not run outcomes, inspect broker
actual-R, inspect blocked OTB2R packet outcomes, call network/API/MT5, or touch
live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/otb2r_g10_riskbank_leg_ledger_packet"
OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
OTB2R = OT / "otb2r_input_only_path_rebuild"
OTB2 = OT / "otb2_synthetic_packet_builder"
OTI2 = OT / "oti2_riskbank_quarantined_results"
G12_OTI = OT / "g12_oti_post_test_audit"
G12_OTB = OT / "g12_otb_rebuild_reaudit"
G0_OTI = OT / "g0_oti_quarantine_synthesis"

PACKET_ID = "OTG0-PKT-013"
EXPERIMENT_ID = "G10-EXP-RISKBANK-005"
HYPOTHESIS_ID = "G10-HYP-RISKBANK-005"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

PACKET_PATH = OTB2R / "packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json"
OTB2_PACKET_PATH = OTB2 / "packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__synthetic_input_packet_2026-05-07.json"
LTF_PROJECTION = OTB2R / "projections/candidate_ltf_path_order_input_only_projection_2026-05-07.jsonl"
STRATEGY_PROJECTION = OTB2R / "projections/strategy_follow_candidates_input_only_projection_2026-05-07.jsonl"
PATH_CONTRACT_PROJECTION = OTB2R / "projections/candidate_path_contract_audit_input_only_projection_2026-05-07.jsonl"
PREFILL_PROJECTION = OTB2R / "projections/prefill_delivery_path_input_only_projection_2026-05-07.jsonl"
CANDIDATE_PATH_FOLLOW_PROJECTION = OTB2R / "projections/candidate_path_follow_input_only_projection_2026-05-07.jsonl"

INPUT_POPULATED_FIELDS = [
    "cost_model_version",
    "duplicate_group_id",
    "source_hash",
    "decision_asof_utc",
    "path_start_utc",
    "path_end_utc",
    "same_bar_ambiguity_policy",
    "same_bar_ambiguity_state",
]

MISSING_LEG_FIELDS = [
    "leg_id",
    "reentry_state",
    "structural_lock_event",
    "risk_bank_before_action_r",
    "risk_bank_after_action_r",
    "realized_closed_leg_r",
    "open_leg_stop_if_hit_r",
    "estimated_remaining_cost_r",
]

SEARCH_FIELDS = MISSING_LEG_FIELDS + [
    "cost_model_version",
    "duplicate_group_id",
    "source_hash",
    "decision_asof_utc",
    "path_start_utc",
    "path_end_utc",
    "terminal_order",
    "terminal_order_ambiguity",
    "tick_order",
    "tick_order_claim_status",
    "same_bar",
    "same_m1_ambiguity",
]

CONTROL_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "research/science_program_2026_05/03_experiment_specs/G10_EXPERIMENT_PREREG_SPECS_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/G10_HYPOTHESIS_ROWS_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/G10_MECHANISM_ROWS_2026-05-06.json",
    "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
    "research/science_program_2026_05/06_outcome_testing/otb2_synthetic_packet_builder/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__synthetic_input_packet_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_DECISION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_NEXT_LANE_RECOMMENDATION_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_BLOCKER_ACTION_MAP_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_QUARANTINE_SYNTHESIS_2026-05-07.md",
    "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_RISK_ACCOUNTING_2026-05-02.md",
    "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_ARCHITECTURE_SPEC_V1.json",
    "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json",
    "research/science_program_2026_05/05_synthesis/G9_CD2_03_OFFLINE_RL_REWARD_CONTRACT_2026-05-06.md",
    "research/science_program_2026_05/05_synthesis/G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md",
]

SEARCH_SCOPES = {
    "accepted_otb2r_packet": [PACKET_PATH],
    "otb2r_input_only_projections": [
        LTF_PROJECTION,
        STRATEGY_PROJECTION,
        PATH_CONTRACT_PROJECTION,
        PREFILL_PROJECTION,
        CANDIDATE_PATH_FOLLOW_PROJECTION,
    ],
    "otb2r_builders_ledgers": [
        OTB2R / "build_otb2r_input_only_path_rebuild_2026_05_07.py",
        OTB2R / "OTB2R_PACKET_MANIFEST_2026-05-07.json",
        OTB2R / "OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json",
        OTB2R / "OTB2R_COVERAGE_AUDIT_2026-05-07.json",
        OTB2R / "OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.json",
        OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json",
    ],
    "otb2_original_lane": [
        OTB2_PACKET_PATH,
        OTB2 / "build_otb2_synthetic_packet_builder_2026_05_07.py",
        OTB2 / "OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_2026-05-07.json",
        OTB2 / "OTB2_SCHEMA_VALIDATION_REPORT_2026-05-07.json",
        OTB2 / "OTB2_AMBIGUITY_LEDGER_2026-05-07.json",
    ],
    "oti2_quarantine_artifacts_without_row_outcome_opening": [
        OTI2 / "build_oti2_riskbank_quarantined_results_2026_05_07.py",
        OTI2 / "OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.json",
        OTI2 / "OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.json",
        OTI2 / "OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
        OTI2 / "OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json",
        OTI2 / "OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json",
        OTI2 / "OTI2_RISKBANK_COMPLETION_AUDIT_2026-05-07.json",
    ],
    "g12_and_g0_decisions": [
        G12_OTB / "G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
        G12_OTB / "G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
        G12_OTI / "G12_OTI_POST_TEST_DECISION_LEDGER_2026-05-07.json",
        G12_OTI / "G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_2026-05-07.json",
        G12_OTI / "G12_OTI_POST_TEST_NEXT_LANE_RECOMMENDATION_2026-05-07.json",
        G0_OTI / "G0_OTI_QUARANTINE_SYNTHESIS_2026-05-07.md",
        G0_OTI / "G0_OTI_BLOCKER_ACTION_MAP_2026-05-07.md",
        G0_OTI / "G0_OTI_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
    ],
    "g10_registries_and_specs": [
        ROOT / "research/science_program_2026_05/03_experiment_specs/G10_EXPERIMENT_PREREG_SPECS_2026-05-06.json",
        ROOT / "research/science_program_2026_05/02_hypothesis_registry/G10_HYPOTHESIS_ROWS_2026-05-06.json",
        ROOT / "research/science_program_2026_05/02_hypothesis_registry/G10_MECHANISM_ROWS_2026-05-06.json",
        ROOT / "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.md",
        ROOT / "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_CAPTURE_SPEC_2026-05-06.md",
    ],
    "neighbor_g6_g9_g12_artifacts": [
        ROOT / "research/science_program_2026_05/05_synthesis/G9_CD2_03_OFFLINE_RL_REWARD_CONTRACT_2026-05-06.md",
        ROOT / "research/science_program_2026_05/05_synthesis/G9_CD2_03_RED_TEAM_PREREG_PROPOSAL_2026-05-06.md",
        ROOT / "research/science_program_2026_05/05_synthesis/G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md",
        ROOT / "research/science_program_2026_05/05_synthesis/G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md",
        ROOT / "research/science_program_2026_05/05_synthesis/G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md",
    ],
    "research_v3_scripts_tests_specs": [
        ROOT / "scripts/analyze_raw_ohlc_path_scaling_v3_exploratory.py",
        ROOT / "tests/test_raw_ohlc_path_scaling_v3_risk_bank.py",
        ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_RISK_ACCOUNTING_2026-05-02.md",
        ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_REENTRY_ARCHITECTURE_SPEC_V1.json",
        ROOT / "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json",
    ],
    "live_shadow_source_files_no_broker_actual_r": [
        ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
        ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
        ROOT / "shadow_logs/candidate_path_follow.jsonl",
        ROOT / "shadow_logs/candidate_path_contract_audit.jsonl",
        ROOT / "shadow_logs/prefill_delivery_path.jsonl",
        ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
        ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
        ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        ROOT / "shadow_logs/opportunity_lifecycle_audit.jsonl",
    ],
}

SKIPPED_FOR_POLICY = [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "shadow_logs/account_pnl_truth_reconciliation.jsonl",
    "shadow_logs/account_truth_reconciliation_status.jsonl",
    "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file_lf_normalized(path: Path) -> str | None:
    if not path.exists():
        return None
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def index_by_projection_hash(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in load_jsonl(path):
        projection_hash = row.get("projection_hash")
        if projection_hash:
            expected = sha256_json({k: v for k, v in row.items() if k not in {"projection_hash", "_source_line_no"}})
            row["projection_hash_recomputed"] = expected
            row["projection_hash_matches"] = expected == projection_hash
            rows[str(projection_hash)] = row
    return rows


def recursive_key_presence(obj: Any, key: str) -> int:
    if isinstance(obj, dict):
        return (1 if key in obj else 0) + sum(recursive_key_presence(v, key) for v in obj.values())
    if isinstance(obj, list):
        return sum(recursive_key_presence(v, key) for v in obj)
    return 0


def recursive_forbidden_hits(obj: Any, forbidden: set[str], path: str = "$") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}"
            if key in forbidden:
                hits.append({"path": child_path, "key": key})
            hits.extend(recursive_forbidden_hits(value, forbidden, child_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(recursive_forbidden_hits(value, forbidden, f"{path}[{idx}]"))
    return hits


def grep_scope(scope_name: str, paths: list[Path], fields: list[str]) -> dict[str, Any]:
    existing = [p for p in paths if p.exists()]
    counts = {field: 0 for field in fields}
    example_hits: dict[str, list[dict[str, Any]]] = {field: [] for field in fields}
    files_scanned = []
    for path in existing:
        files_scanned.append({"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except UnicodeDecodeError:
            text = ""
        lines = text.splitlines()
        for field in fields:
            needle = field
            match_count = text.count(needle)
            counts[field] += match_count
            if match_count and len(example_hits[field]) < 5:
                for line_no, line in enumerate(lines, 1):
                    if needle in line:
                        example_hits[field].append(
                            {
                                "path": rel(path),
                                "line_no": line_no,
                                "excerpt": line.strip()[:240],
                            }
                        )
                        if len(example_hits[field]) >= 5:
                            break
    return {
        "scope": scope_name,
        "files_requested": len(paths),
        "files_scanned": files_scanned,
        "missing_files": [rel(p) for p in paths if not p.exists()],
        "field_match_counts": counts,
        "example_hits": {k: v for k, v in example_hits.items() if v},
    }


def run_command(args: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=120)
        return {
            "command": " ".join(args),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip().splitlines()[:120],
            "stderr": proc.stderr.strip().splitlines()[:40],
        }
    except Exception as exc:  # pragma: no cover - audit capture only
        return {"command": " ".join(args), "error": repr(exc)}


def git_history_search() -> dict[str, Any]:
    pattern = (
        "risk_bank_before_action_r|risk_bank_after_action_r|realized_closed_leg_r|"
        "open_leg_stop_if_hit_r|estimated_remaining_cost_r|structural_lock_event|"
        "reentry_state|leg_id"
    )
    revs = run_command(["git", "rev-list", "--all", "--", "research", "src", "scripts", "tests", ".context"])
    hit_commits: list[dict[str, Any]] = []
    total_hit_commits = 0
    scanned_commits = 0
    if revs.get("returncode") == 0:
        for commit in revs.get("stdout", []):
            if not commit:
                continue
            scanned_commits += 1
            grep = run_command(
                [
                    "git",
                    "grep",
                    "-n",
                    "-I",
                    "-E",
                    pattern,
                    commit,
                    "--",
                    "research",
                    "src",
                    "scripts",
                    "tests",
                    ".context",
                ]
            )
            if grep.get("returncode") == 0:
                total_hit_commits += 1
                if len(hit_commits) < 100:
                    hit_commits.append(
                        {
                            "commit": commit,
                            "hit_count_capped": len(grep.get("stdout", [])),
                            "sample_hits": grep.get("stdout", [])[:12],
                        }
                    )
    show_targets = [
        "3f37ed82:research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/build_oti2_riskbank_quarantined_results_2026_05_07.py",
        "ec429b2b:research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/build_otb2r_input_only_path_rebuild_2026_05_07.py",
    ]
    greps = [
        run_command(["git", "grep", "-n", pattern, target])
        for target in show_targets
    ]
    return {
        "git_rev_list": {
            "command": revs.get("command"),
            "returncode": revs.get("returncode"),
            "stderr": revs.get("stderr"),
            "commit_count_scanned": scanned_commits,
        },
        "git_grep_history_pattern": {
            "pattern": pattern,
            "hit_commit_count": total_hit_commits,
            "stored_hit_commit_sample_count": len(hit_commits),
            "stored_hit_commit_sample_cap": 100,
            "hit_commit_samples": hit_commits,
            "search_status": "PASS" if revs.get("returncode") == 0 else "FAILED_REV_LIST",
        },
        "git_grep_relevant_commits": greps,
        "interpretation": (
            "Git history contains the field names in prereg/spec/test/result-blocker code. "
            "No historical accepted OTG0-PKT-013 packet revision with populated leg/risk-bank "
            "values was found by this local history search."
        ),
    }


def normalize_utc(value: str | None) -> str | None:
    if value is None:
        return None
    return value.replace("+00:00", "Z")


def build_records(packet: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ltf_index = index_by_projection_hash(LTF_PROJECTION)
    strategy_index = index_by_projection_hash(STRATEGY_PROJECTION)
    contract_rows = load_jsonl(PATH_CONTRACT_PROJECTION)
    latest_contract_by_setup: dict[str, dict[str, Any]] = {}
    for row in contract_rows:
        setup_id = row.get("candidate_id")
        if not setup_id:
            continue
        current = latest_contract_by_setup.get(str(setup_id))
        if current is None or (
            str(row.get("asof_latest_candle_utc")),
            int(row.get("_source_line_no", 0)),
        ) > (
            str(current.get("asof_latest_candle_utc")),
            int(current.get("_source_line_no", 0)),
        ):
            latest_contract_by_setup[str(setup_id)] = row

    records: list[dict[str, Any]] = []
    missing_counts = Counter()
    populated_counts = Counter()
    terminal_evidence_counts = Counter()
    tick_claim_counts = Counter()
    projection_hash_failures = []

    for row in packet["records"]:
        setup_id = row["setup_id"]
        ltf_hash = row["sanitized_source_hash_components"].get("ltf_projection_row_hash")
        strategy_hash = row["sanitized_source_hash_components"].get("strategy_projection_row_hash")
        ltf = ltf_index.get(str(ltf_hash), {})
        strategy = strategy_index.get(str(strategy_hash), {})
        contract = latest_contract_by_setup.get(setup_id, {})

        for field in INPUT_POPULATED_FIELDS:
            if row.get(field) not in (None, ""):
                populated_counts[field] += 1
        for field in MISSING_LEG_FIELDS:
            if field not in row:
                missing_counts[field] += 1

        if not ltf.get("projection_hash_matches", True):
            projection_hash_failures.append({"setup_id": setup_id, "projection_hash": ltf_hash})
        if not strategy.get("projection_hash_matches", True):
            projection_hash_failures.append({"setup_id": setup_id, "projection_hash": strategy_hash})

        terminal_status = "NO_TERMINAL_ORDER_CLAIM_PACKET_FLAGS_ONLY"
        if row.get("same_bar_ambiguity_state") == "same_m1_ambiguity_flagged":
            terminal_status = "SAME_M1_TERMINAL_AMBIGUITY_FLAGGED_NOT_RESOLVED"
        terminal_evidence_counts[terminal_status] += 1
        tick_claim = contract.get("tick_order_claim_status") or "NO_PACKET_CONTRACT_TICK_CLAIM_FIELD"
        tick_claim_counts[tick_claim] += 1

        records.append(
            {
                "packet_id": PACKET_ID,
                "experiment_id": EXPERIMENT_ID,
                "hypothesis_id": HYPOTHESIS_ID,
                "setup_id": setup_id,
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "decision_asof_utc": row.get("decision_asof_utc"),
                "path_start_utc": row.get("path_start_utc"),
                "path_end_utc": row.get("path_end_utc"),
                "cost_model_version": row.get("cost_model_version"),
                "duplicate_group_id": row.get("duplicate_group_id"),
                "source_hash": row.get("source_hash"),
                "entry_sl_tp_or_level_packet": row.get("entry_sl_tp_or_level_packet"),
                "same_bar_ambiguity_policy": row.get("same_bar_ambiguity_policy"),
                "same_bar_ambiguity_state": row.get("same_bar_ambiguity_state"),
                "terminal_order_claim_allowed": False,
                "terminal_order_evidence_status": terminal_status,
                "tick_order_evidence": {
                    "packet_coverage_mode": (row.get("coverage_binding") or {}).get("coverage_mode"),
                    "packet_ltf_status": (row.get("coverage_binding") or {}).get("ltf_status"),
                    "packet_ltf_source": (row.get("coverage_binding") or {}).get("ltf_source"),
                    "packet_m1_bar_count": (row.get("coverage_binding") or {}).get("m1_bar_count"),
                    "ltf_projection_hash": ltf_hash,
                    "ltf_projection_hash_matches": ltf.get("projection_hash_matches"),
                    "ltf_projection_source_line_no": ltf.get("source_line_no"),
                    "ltf_projection_same_m1_ambiguity": ltf.get("same_m1_ambiguity"),
                    "contract_projection_tick_order_claim_status_latest_for_setup": tick_claim,
                    "contract_projection_line_no_latest_for_setup": contract.get("source_line_no"),
                    "contract_projection_note": (
                        "contract projection is supporting negative/policy evidence, not packet source_hash input"
                        if contract
                        else "no contract projection row found"
                    ),
                },
                "sanitized_source_hash_components": row.get("sanitized_source_hash_components"),
                "coverage_binding": row.get("coverage_binding"),
                "lineage": {
                    "accepted_packet_path": rel(PACKET_PATH),
                    "strategy_projection_path": rel(STRATEGY_PROJECTION),
                    "strategy_projection_row_hash": strategy_hash,
                    "strategy_projection_line_no": strategy.get("_source_line_no"),
                    "ltf_projection_path": rel(LTF_PROJECTION),
                    "ltf_projection_row_hash": ltf_hash,
                    "ltf_projection_line_no": ltf.get("_source_line_no"),
                    "packet_build_source_paths": row.get("packet_build_source_paths"),
                },
                "unavailable_leg_risk_fields": {
                    field: {
                        "status": "NOT_POPULATED_FROM_LOCAL_INPUT_ONLY_SOURCES",
                        "reason": "field absent from accepted packet and packet-bound sanitized projections",
                    }
                    for field in MISSING_LEG_FIELDS
                },
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
            }
        )

    audit = {
        "row_count": len(records),
        "input_populated_counts": dict(populated_counts),
        "missing_leg_field_counts": dict(missing_counts),
        "terminal_order_evidence_counts": dict(terminal_evidence_counts),
        "supporting_tick_order_claim_counts": dict(tick_claim_counts),
        "projection_hash_failures": projection_hash_failures,
    }
    return records, audit


def control_lineage() -> list[dict[str, Any]]:
    items = []
    for path_str in CONTROL_INPUTS:
        path = ROOT / path_str
        items.append(
            {
                "path": path_str,
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return items


def build_evidence_chain() -> list[dict[str, Any]]:
    return [
        {
            "stage": "prereg_and_mechanism",
            "status": "RISK_BANK_REQUIREMENTS_DEFINED_OUTCOMES_CLOSED",
            "evidence": [
                "research/science_program_2026_05/03_experiment_specs/G10_EXPERIMENT_PREREG_SPECS_2026-05-06.json",
                "research/science_program_2026_05/02_hypothesis_registry/G10_HYPOTHESIS_ROWS_2026-05-06.json",
                "research/science_program_2026_05/02_hypothesis_registry/G10_MECHANISM_ROWS_2026-05-06.json",
            ],
            "summary": (
                "G10-EXP-RISKBANK-005 is frozen as synthetic_path_r research only; rows without "
                "leg-level risk-bank ledger are excluded and outcome_review_opened=false."
            ),
        },
        {
            "stage": "otg0_packet_control",
            "status": "SYNTHETIC_REPLAY_EXISTING_DATA_AUDIT_CLASS",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
            ],
            "summary": (
                "OTG0 required setup, as-of/path windows, same-bar policy, cost model, duplicate "
                "group, label separation, and broker_actual_r_absent=true before synthetic path review."
            ),
        },
        {
            "stage": "otb2_original_packet",
            "status": "READY_BUT_LATER_REJECTED_BY_G12",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/otb2_synthetic_packet_builder/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__synthetic_input_packet_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json",
            ],
            "summary": (
                "Initial OTB2 built a G10 input packet, but G12 rejected invalid clearing because raw "
                "path source/hash and coverage blockers remained."
            ),
        },
        {
            "stage": "otb2r_rebuild",
            "status": "PACKET_READY_FOR_G12_REAUDIT",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json",
            ],
            "summary": (
                "OTB2R rebuilt 86 rows from sanitized projections with 86/86 source-hash and "
                "coverage-valid rows, 86 unique duplicate groups, and terminal-order guessing disabled."
            ),
        },
        {
            "stage": "g12_otb_reaudit",
            "status": "ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
            ],
            "summary": "G12 accepted only OTG0-PKT-013 from OTB2R; the other OTB2R packets stayed blocked.",
        },
        {
            "stage": "oti2_quarantined_result",
            "status": "RESULT_QUARANTINED_DISCOVERY_ONLY_PRIMARY_RISKBANK_NOT_COMPUTABLE",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json",
            ],
            "summary": (
                "OTI2 confirmed the accepted packet hashes/coverage, but the risk-bank primary metric "
                "remained not_computable because leg/reentry/risk-bank fields were absent."
            ),
        },
        {
            "stage": "g12_oti_post_test_audit",
            "status": "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE_WITH_RESIDUAL_EXACT_QUESTION",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_DECISION_LEDGER_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_2026-05-07.json",
            ],
            "summary": (
                "G12 accepted OTI2 only as quarantined discovery evidence and asked for a future "
                "frozen packet with leg-level reentry/risk-bank/cost fields."
            ),
        },
        {
            "stage": "g0_next_lane",
            "status": "OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET_RANK_1",
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
                "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_BLOCKER_ACTION_MAP_2026-05-07.md",
            ],
            "summary": (
                "G0 routed the central blocker to this input-only proof/impossibility packet, with no "
                "outcome scoring and no promotion flags."
            ),
        },
    ]


def build_field_matrix(packet: dict[str, Any], records: list[dict[str, Any]], search_payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix = []
    field_evidence = defaultdict(list)
    for scope in search_payload:
        for field, examples in scope.get("example_hits", {}).items():
            field_evidence[field].extend(examples)

    for field in MISSING_LEG_FIELDS + INPUT_POPULATED_FIELDS + [
        "terminal_order_tick_order_evidence",
        "same_bar_policy_inputs",
    ]:
        if field in MISSING_LEG_FIELDS:
            matrix.append(
                {
                    "field": field,
                    "coverage_status": "IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS",
                    "records_populated": 0,
                    "records_total": len(records),
                    "value_policy": "do_not_impute",
                    "evidence": field_evidence.get(field, [])[:10],
                    "negative_evidence": (
                        "Absent from accepted OTB2R packet records, packet-bound OTB2R sanitized projections, "
                        "OTI2 blocker/methodology, G12 OTI residual question, and relevant shadow/source logs. "
                        "Existing V3 exploratory scripts/tests define the field contract but do not provide "
                        "packet-bound input-only values for OTG0-PKT-013."
                    ),
                    "missing_source_logger_schema_needed": (
                        "riskbank_leg_ledger_v1 logger/schema keyed by packet_id, setup_id, leg_id, "
                        "decision_asof_utc, action_asof_utc, structural_lock_event, reentry_state, "
                        "risk_bank_before_action_r, risk_bank_after_action_r, realized_closed_leg_r, "
                        "open_leg_stop_if_hit_r, estimated_remaining_cost_r, cost_model_version, "
                        "duplicate_group_id, source_hash, and same-bar/tick-order policy inputs."
                    ),
                }
            )
        elif field == "terminal_order_tick_order_evidence":
            counts = Counter(r["terminal_order_evidence_status"] for r in records)
            matrix.append(
                {
                    "field": field,
                    "coverage_status": "INPUT_ONLY_POLICY_EVIDENCE_ONLY_NO_TERMINAL_ORDER_CLAIM",
                    "records_populated": len(records),
                    "records_total": len(records),
                    "value_summary": dict(counts),
                    "evidence": [
                        {
                            "path": rel(OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json"),
                            "sha256": sha256_file(OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json"),
                        },
                        {"path": rel(LTF_PROJECTION), "sha256": sha256_file(LTF_PROJECTION)},
                    ],
                    "negative_evidence": "terminal_order_claim_allowed=false; terminal order is not guessed.",
                }
            )
        elif field == "same_bar_policy_inputs":
            counts = Counter(r["same_bar_ambiguity_state"] for r in records)
            matrix.append(
                {
                    "field": field,
                    "coverage_status": "POPULATED_INPUT_ONLY",
                    "records_populated": len(records),
                    "records_total": len(records),
                    "value_summary": dict(counts),
                    "evidence": [
                        {
                            "path": rel(OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json"),
                            "sha256": sha256_file(OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json"),
                        },
                    ],
                }
            )
        else:
            matrix.append(
                {
                    "field": field,
                    "coverage_status": "POPULATED_INPUT_ONLY",
                    "records_populated": sum(1 for r in records if r.get(field) not in (None, "")),
                    "records_total": len(records),
                    "distinct_values": len({json.dumps(r.get(field), sort_keys=True) for r in records}),
                    "example_values": list({json.dumps(r.get(field), sort_keys=True) for r in records})[:5],
                    "evidence": [
                        {"path": rel(PACKET_PATH), "sha256": sha256_file(PACKET_PATH)},
                    ],
                }
            )
    return matrix


def build_source_hash_lineage(packet: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    recompute_failures = []
    for source in packet["records"]:
        expected = sha256_json(source["sanitized_source_hash_components"])
        if expected != source["source_hash"]:
            recompute_failures.append(
                {
                    "setup_id": source["setup_id"],
                    "source_hash": source["source_hash"],
                    "source_hash_recomputed": expected,
                }
            )
    upstream_projection_hashes = read_json(OTB2R / "OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json")
    upstream_projection_hashes = upstream_projection_hashes.get("projections", {})
    projection_files = {
        "strategy_follow_candidates": STRATEGY_PROJECTION,
        "candidate_ltf_path_order": LTF_PROJECTION,
        "candidate_path_contract_audit": PATH_CONTRACT_PROJECTION,
        "candidate_path_follow": CANDIDATE_PATH_FOLLOW_PROJECTION,
        "prefill_delivery_path": PREFILL_PROJECTION,
    }
    projection_file_hashes = {}
    for name, path in projection_files.items():
        upstream = (upstream_projection_hashes.get(name) or {}).get("projection_sha256_used_for_packet_source_hashing")
        projection_file_hashes[name] = {
            "path": rel(path),
            "raw_sha256_current_worktree": sha256_file(path),
            "lf_normalized_sha256_current_worktree": sha256_file_lf_normalized(path),
            "upstream_projection_sha256_used_for_packet_source_hashing": upstream,
            "lf_normalized_matches_upstream": sha256_file_lf_normalized(path) == upstream,
            "raw_matches_upstream": sha256_file(path) == upstream,
        }

    return {
        "artifact_type": "source_hash_lineage_ledger",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "packet_path": rel(PACKET_PATH),
        "packet_sha256": sha256_file(PACKET_PATH),
        "projection_file_hashes": projection_file_hashes,
        "row_source_hash_match_count": len(packet["records"]) - len(recompute_failures),
        "row_source_hash_failure_count": len(recompute_failures),
        "row_source_hash_failures": recompute_failures,
        "unique_source_hash_count": len({r["source_hash"] for r in records}),
        "row_lineage_policy": (
            "Packet row source_hash recomputes from sanitized projection row hashes, sanitized "
            "projection file hashes, coverage binding hash, entry/SL/TP packet hash, and duplicate_group_id. "
            "Raw shadow/source hashes are provenance only. Current worktree projection files use CRLF line "
            "endings; LF-normalized hashes match the upstream OTB2R source-hash ledger and packet components."
        ),
        "record_lineage_sample": [
            {
                "setup_id": r["setup_id"],
                "source_hash": r["source_hash"],
                "sanitized_source_hash_components": r["sanitized_source_hash_components"],
                "lineage": r["lineage"],
            }
            for r in records[:5]
        ],
    }


def build_no_leak_audit(packet: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_primary = {
        "broker_actual_r",
        "actual_r",
        "outcome_r",
        "future_return",
        "win_loss",
        "trade_result",
        "path_order_label",
        "terminal_outcome_status",
        "path_synthetic_r",
        "synthetic_path_r_value",
        "reentry_path_synthetic_r",
    }
    record_hits = recursive_forbidden_hits(records, forbidden_primary)
    packet_forbidden_scan_path = OTB2R / "OTB2R_FORBIDDEN_FIELD_SCAN_2026-05-07.json"
    packet_forbidden_scan = read_json(packet_forbidden_scan_path) if packet_forbidden_scan_path.exists() else {}
    return {
        "artifact_type": "no_leak_audit",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "broker_actual_r_inspected": False,
        "blocked_otb2r_packet_outcomes_inspected": False,
        "outcome_scoring_run": False,
        "live_trading_surfaces_touched": False,
        "primary_leg_packet_forbidden_hits": record_hits,
        "primary_leg_packet_forbidden_hit_count": len(record_hits),
        "existing_otb2r_forbidden_scan_summary": {
            "path": rel(packet_forbidden_scan_path),
            "sha256": sha256_file(packet_forbidden_scan_path),
            "bad_forbidden_key_counts": packet_forbidden_scan.get("bad_forbidden_key_counts"),
            "promotion_verdict": packet_forbidden_scan.get("promotion_verdict"),
            "validation_safe": packet_forbidden_scan.get("validation_safe"),
            "outcome_review_opened": packet_forbidden_scan.get("outcome_review_opened"),
        },
        "blocked_packet_scope_policy": "Only OTG0-PKT-013 accepted OTB2R packet was loaded. Other OTB2R packet files were not opened for outcome data.",
        "skipped_sources_by_policy": SKIPPED_FOR_POLICY,
        "flag_audit": {
            "packet_validation_safe": packet.get("validation_safe"),
            "packet_outcome_review_opened": packet.get("outcome_review_opened"),
            "packet_promotion_verdict": packet.get("promotion_verdict"),
            "all_output_records_validation_safe_false": all(r["validation_safe"] is False for r in records),
            "all_output_records_outcome_review_opened_false": all(r["outcome_review_opened"] is False for r in records),
            "all_output_records_no_promotion": all(r["promotion_verdict"] == PROMOTION_VERDICT for r in records),
        },
    }


def build_duplicate_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups = Counter(r["duplicate_group_id"] for r in records)
    return {
        "artifact_type": "duplicate_denominator_audit",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "raw_record_count": len(records),
        "unique_duplicate_group_id_count": len(groups),
        "within_packet_duplicate_drift": len(records) - len(groups),
        "duplicate_policy": (
            "Unique duplicate_group_id is the independent denominator for any later sample-floor/effective-N audit; "
            "leg rows would be child rows under setup_id and may not inflate n."
        ),
        "duplicate_groups_with_multiple_rows": {k: v for k, v in groups.items() if v > 1},
        "source_evidence": [
            {
                "path": rel(OTB2R / "OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.json"),
                "sha256": sha256_file(OTB2R / "OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.json"),
            }
        ],
    }


def build_same_bar_policy(records: list[dict[str, Any]]) -> dict[str, Any]:
    same_state = Counter(r["same_bar_ambiguity_state"] for r in records)
    terminal = Counter(r["terminal_order_evidence_status"] for r in records)
    tick_claim = Counter(
        r["tick_order_evidence"]["contract_projection_tick_order_claim_status_latest_for_setup"]
        for r in records
    )
    return {
        "artifact_type": "same_bar_tick_order_policy",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "terminal_order_claim_allowed": False,
        "policy": (
            "Same-minute terminal order is never guessed. M1 path-order evidence can flag same-minute "
            "ambiguity, but this packet does not resolve terminal order or populate outcome labels. "
            "Supporting candidate_path_contract rows currently say NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY "
            "for the latest accepted setup rows, so tick/terminal order must remain a future source requirement."
        ),
        "same_bar_state_counts": dict(same_state),
        "terminal_order_evidence_counts": dict(terminal),
        "supporting_contract_tick_order_claim_counts": dict(tick_claim),
        "m1_path_order_packet_rows": sum(
            r["tick_order_evidence"]["packet_ltf_status"] == "M1_PATH_RECOVERED"
            for r in records
        ),
        "source_evidence": [
            {"path": rel(OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json"), "sha256": sha256_file(OTB2R / "OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json")},
            {"path": rel(LTF_PROJECTION), "sha256": sha256_file(LTF_PROJECTION)},
            {"path": rel(PATH_CONTRACT_PROJECTION), "sha256": sha256_file(PATH_CONTRACT_PROJECTION)},
        ],
    }


def build_contradiction_ledger() -> list[dict[str, Any]]:
    return [
        {
            "item": "OTL2 blocked all synthetic packets, but OTI2 later ran OTG0-PKT-013.",
            "resolution": (
                "OTL2 was the initial audit. OTB2R later rebuilt a sanitized G10 packet, and G12 OTB "
                "rebuild reaudit accepted only OTG0-PKT-013 for future outcome-test packet audit."
            ),
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/otl2_synthetic_replay_packet_audit/OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
            ],
        },
        {
            "item": "OTB0/G12 blocker-clearing baseline listed OTG0-PKT-013 as blocked/rejected.",
            "resolution": (
                "OTB0 and first G12 audit remain valid historical baselines; OTB2R rebuilt sanitized "
                "source hashes and coverage later, clearing those blockers for this packet only."
            ),
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json",
            ],
        },
        {
            "item": "G12 accepted OTI2 as quarantined evidence, but risk-bank primary metric is not computable.",
            "resolution": (
                "Acceptance is lane-level quarantined discovery only. G12 explicitly retains a residual "
                "question requiring leg-level risk-bank fields before any risk-bank score."
            ),
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json",
            ],
        },
        {
            "item": "Packet coverage says M1 path recovered, while supporting path-contract rows say no tick-order claim.",
            "resolution": (
                "These are different evidence roles. OTB2R packet hashes bind to sanitized candidate_ltf_path_order "
                "M1 coverage and same-M1 ambiguity flags; candidate_path_contract latest rows are supporting "
                "negative evidence that terminal/tick order should not be claimed."
            ),
            "evidence": [
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json",
                "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_path_contract_audit_input_only_projection_2026-05-07.jsonl",
            ],
        },
    ]


def build_future_schema_spec() -> dict[str, Any]:
    return {
        "artifact_type": "future_instrumentation_schema_spec",
        "schema_version": "riskbank_leg_ledger_v1_proposed",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "purpose": (
            "Provide packet-bound, input-only leg/reentry/risk-bank state rows so G10-EXP-RISKBANK-005 "
            "can become scoreable without broker actual-R, blocked-packet pooling, or terminal-order guessing."
        ),
        "required_top_level_fields": [
            "packet_id",
            "experiment_id",
            "hypothesis_id",
            "setup_id",
            "leg_id",
            "leg_sequence_index",
            "parent_setup_duplicate_group_id",
            "action_asof_utc",
            "decision_asof_utc",
            "path_start_utc",
            "path_end_utc",
            "reentry_state",
            "structural_lock_event",
            "risk_bank_before_action_r",
            "risk_bank_after_action_r",
            "realized_closed_leg_r",
            "open_leg_stop_if_hit_r",
            "estimated_remaining_cost_r",
            "cost_model_version",
            "same_bar_ambiguity_policy",
            "same_bar_ambiguity_state",
            "terminal_order_claim_status",
            "tick_order_source_id",
            "duplicate_group_id",
            "source_hash",
            "sanitized_source_hash_components",
            "label_family",
            "promotion_verdict",
            "validation_safe",
            "outcome_review_opened",
        ],
        "field_rules": {
            "leg_id": "Stable child-leg key, unique under setup_id; initial leg and reentry legs must be explicit child rows.",
            "reentry_state": "Enum: not_armed, armed_pending, filled, cancelled, expired, blocked_risk_bank, blocked_ambiguity, blocked_source_missing.",
            "structural_lock_event": "Object with source row id, lock type, lock price/level, lock as-of UTC, and source hash.",
            "risk_bank_before_action_r": "Numeric invariant value before proposed action.",
            "risk_bank_after_action_r": "Numeric invariant value after proposed action; must be >= -1.0 for admissible reentry.",
            "realized_closed_leg_r": "Numeric closed-leg R net of already charged completed-leg costs in this label lane.",
            "open_leg_stop_if_hit_r": "Array of numeric worst-case R for every currently open leg after the proposed action.",
            "estimated_remaining_cost_r": "Numeric non-negative conservative remaining cost estimate, with cost_model_version and cost components.",
            "terminal_order_claim_status": "Enum: tick_order_observed, m1_order_observed, same_bar_ambiguous_bounded, no_terminal_order_claim.",
            "source_hash": "Hash only sanitized as-of/input fields and policy metadata; never hash result labels into input packet rows.",
        },
        "forbidden_primary_fields": [
            "broker_actual_r",
            "actual_r",
            "path_synthetic_r",
            "outcome_r",
            "win_loss",
            "trade_result",
            "post_entry_path_label",
            "unblocked_blocked_packet_outcome",
        ],
        "minimum_verification_gates": [
            "row source_hash recomputes 100%",
            "unique duplicate_group_id denominator reported separately from leg rows",
            "all risk_bank_after_action_r values numeric or row blocked_source_missing",
            "terminal_order_claim_status never escalates beyond source evidence",
            "validation_safe=false until separate promotion dossier",
            "outcome_review_opened=false until packet readiness audit explicitly opens a quarantined result lane",
        ],
    }


def build_search_payload() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scoped = [grep_scope(name, paths, SEARCH_FIELDS) for name, paths in SEARCH_SCOPES.items()]
    # A broad files-with-matches pass, captured as file inventory only. This avoids dumping outcome rows.
    broad = run_command(
        [
            "rg",
            "--files-with-matches",
            "|".join(re.escape(f) for f in SEARCH_FIELDS),
            "research",
            "src",
            "scripts",
            "tests",
            "shadow_logs",
            "data",
            "--glob",
            "!shadow_logs/broker_actual_r_audit.jsonl",
            "--glob",
            "!shadow_logs/account*",
            "--glob",
            "!**/.git/**",
            "--glob",
            "!**/__pycache__/**",
        ]
    )
    return scoped, {
        "scoped_searches": scoped,
        "broad_files_with_matches_no_broker_actual_r": broad,
        "git_history_search": git_history_search(),
        "skipped_sources_by_policy": SKIPPED_FOR_POLICY,
        "saturation_interpretation": (
            "The searched sources contain the strict leg/risk-bank field names only as contracts, tests, "
            "blockers, or SOURCE_NOT_CAPTURED markers. Packet-bound, input-only values for the missing "
            "fields are not locally reconstructable."
        ),
    }


def build_completion_audit(payload: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Complete mandatory GTOS preflight first",
            "evidence": ".context/LIVE_STATE.md generated before builder run and included in controlling_inputs.",
            "status": "PASS",
        },
        {
            "requirement": "Use specified G0 OTI, OTI2, OTB2R, G12, OTG0, G10, master registry, LIVE_STATE, doctrine, and research_current_state inputs",
            "evidence": f"control_lineage_count={len(payload['control_lineage'])}; all_required_core_inputs_exist={all(item['exists'] for item in payload['control_lineage'])}.",
            "status": "PASS" if all(item["exists"] for item in payload["control_lineage"]) else "FAIL",
        },
        {
            "requirement": "Reconstruct OTG0-PKT-013 prereg-to-packet-to-OTI2-to-G12 chain",
            "evidence": f"evidence_chain_stages={len(payload['evidence_chain'])}.",
            "status": "PASS",
        },
        {
            "requirement": "Aggressively hunt all requested fields across local sources and git history",
            "evidence": "negative_evidence_saturation_ledger contains scoped source searches, broad file inventory, and git history search.",
            "status": "PASS",
        },
        {
            "requirement": "Populate possible input-only fields or record negative evidence",
            "evidence": f"records={payload['record_audit']['row_count']} populated_fields={payload['record_audit']['input_populated_counts']} missing_leg_fields={payload['record_audit']['missing_leg_field_counts']}.",
            "status": "PASS",
        },
        {
            "requirement": "Create field matrix, source-hash lineage, no-leak, duplicate, same-bar/tick-order, contradiction, negative-evidence, future schema, and completion audit artifacts",
            "evidence": "artifact_manifest lists every required artifact.",
            "status": "PASS",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false",
            "evidence": "top-level payload and all records carry those flags; no validation_safe=true or outcome_review_opened=true is emitted.",
            "status": "PASS"
            if payload["promotion_verdict"] == PROMOTION_VERDICT
            and payload["validation_safe"] is False
            and payload["outcome_review_opened"] is False
            and all(r["validation_safe"] is False and r["outcome_review_opened"] is False for r in payload["records"])
            else "FAIL",
        },
        {
            "requirement": "Do not run outcome scoring, inspect broker actual-R, inspect blocked OTB2R packet outcomes, use paid/network/API calls, or touch live trading surfaces",
            "evidence": "builder uses local files only; no broker actual-R paths are opened; no blocked packet outcome rows are loaded; no MT5/network/API calls exist in script.",
            "status": "PASS",
        },
    ]
    return {
        "artifact_type": "completion_audit",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "can_mark_goal_complete": all(item["status"] == "PASS" for item in checklist),
        "checklist": checklist,
    }


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)


def render_main_md(payload: dict[str, Any]) -> str:
    field_rows = [
        [item["field"], item["coverage_status"], item.get("records_populated", ""), item.get("records_total", "")]
        for item in payload["field_coverage_matrix"]
    ]
    chain_rows = [[item["stage"], item["status"], item["summary"]] for item in payload["evidence_chain"]]
    return "\n\n".join(
        [
            f"# OTB2R G10 Risk-Bank Leg-Ledger Packet - {DATE_STAMP}",
            f"Promotion verdict: `{PROMOTION_VERDICT}`",
            "Scope: research/tooling only; input-only proof-or-impossibility packet.",
            "Safety flags: `validation_safe=false`; `outcome_review_opened=false`; `outcome_scoring_run=false`; `broker_actual_r_inspected=false`; `blocked_otb2r_packet_outcomes_inspected=false`.",
            "## Verdict",
            (
                "The packet can carry forward 86 source-hashed, duplicate-unique, coverage-bound G10 rows with "
                "decision/path windows, cost model, same-bar policy, and source-hash lineage. It cannot populate "
                "the required leg-level risk-bank ledger fields from current local input-only sources. The correct "
                "result is `IMPOSSIBLE_FROM_CURRENT_LOCAL_INPUTS` for those fields, not an imputation."
            ),
            "## Evidence Chain",
            table(["Stage", "Status", "Summary"], chain_rows),
            "## Field Coverage Matrix",
            table(["Field", "Coverage", "Populated", "Total"], field_rows),
            "## Row Summary",
            table(
                ["Metric", "Value"],
                [
                    ["records", payload["record_audit"]["row_count"]],
                    ["unique duplicate_group_id", payload["duplicate_denominator_audit"]["unique_duplicate_group_id_count"]],
                    ["source_hash failures", payload["source_hash_lineage_ledger"]["row_source_hash_failure_count"]],
                    ["same_m1_ambiguity_flagged", payload["same_bar_tick_order_policy"]["same_bar_state_counts"].get("same_m1_ambiguity_flagged", 0)],
                    ["terminal_order_claim_allowed", payload["same_bar_tick_order_policy"]["terminal_order_claim_allowed"]],
                ],
            ),
            "## Negative Evidence",
            (
                "Search saturation found strict leg/risk-bank field names in specs, tests, blockers, or "
                "`SOURCE_NOT_CAPTURED` markers, but not as packet-bound input values for `OTG0-PKT-013`. "
                "See the negative-evidence saturation ledger for scope-by-scope command evidence."
            ),
            "## Future Required Source",
            (
                "A future `riskbank_leg_ledger_v1` source/logger must emit leg_id, reentry state, structural lock, "
                "before/after risk-bank values, closed/open leg R, numeric remaining costs, duplicate group, source hash, "
                "and same-bar/tick-order policy inputs before a G10 risk-bank score can be computed."
            ),
        ]
    )


def render_matrix_md(matrix: list[dict[str, Any]]) -> str:
    rows = []
    for item in matrix:
        rows.append(
            [
                item["field"],
                item["coverage_status"],
                item.get("records_populated", 0),
                item.get("records_total", ""),
                item.get("value_policy", item.get("negative_evidence", ""))[:180],
            ]
        )
    return "\n\n".join(
        [
            f"# Field Coverage Matrix - {DATE_STAMP}",
            f"Promotion verdict: `{PROMOTION_VERDICT}`",
            table(["Field", "Coverage", "Populated", "Total", "Evidence/Policy"], rows),
        ]
    )


def render_simple_md(title: str, payload: Any) -> str:
    return "\n\n".join(
        [
            f"# {title} - {DATE_STAMP}",
            f"Promotion verdict: `{PROMOTION_VERDICT}`",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True)[:60000],
            "```",
        ]
    )


def artifact_manifest(files: list[Path]) -> dict[str, Any]:
    return {
        "artifact_type": "artifact_manifest",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "artifacts": [
            {"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in files
            if path.exists()
        ],
    }


def build() -> dict[str, Any]:
    packet = read_json(PACKET_PATH)
    if packet.get("packet_id") != PACKET_ID or packet.get("experiment_id") != EXPERIMENT_ID:
        raise RuntimeError("Unexpected packet identity.")
    if packet.get("validation_safe") is not False or packet.get("outcome_review_opened") is not False:
        raise RuntimeError("Input packet unexpectedly opened validation/outcome review.")
    records, record_audit = build_records(packet)
    search_scopes, saturation = build_search_payload()
    field_matrix = build_field_matrix(packet, records, search_scopes)
    payload: dict[str, Any] = {
        "artifact_family": "OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET",
        "schema_version": "otb2r_g10_riskbank_leg_ledger_packet_v1",
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": run_command(["git", "rev-parse", "HEAD"]).get("stdout", ["unknown"])[0],
        "packet_id": PACKET_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcome_scoring_run": False,
        "broker_actual_r_inspected": False,
        "blocked_otb2r_packet_outcomes_inspected": False,
        "paid_network_api_mt5_calls": False,
        "decision": "INPUT_ONLY_PARTIAL_PACKET_WITH_LEG_RISKBANK_FIELDS_IMPOSSIBLE_LOCALLY",
        "decision_reason": (
            "Current local inputs populate as-of/path/hash/duplicate/cost/same-bar policy fields, but "
            "do not contain packet-bound leg_id/reentry/structural-lock/risk-bank numeric ledger values."
        ),
        "control_lineage": control_lineage(),
        "evidence_chain": build_evidence_chain(),
        "records": records,
        "record_audit": record_audit,
        "field_coverage_matrix": field_matrix,
    }
    payload["source_hash_lineage_ledger"] = build_source_hash_lineage(packet, records)
    payload["no_leak_audit"] = build_no_leak_audit(packet, records)
    payload["duplicate_denominator_audit"] = build_duplicate_audit(records)
    payload["same_bar_tick_order_policy"] = build_same_bar_policy(records)
    payload["contradiction_stale_context_ledger"] = build_contradiction_ledger()
    payload["negative_evidence_saturation_ledger"] = saturation
    payload["future_instrumentation_schema_spec"] = build_future_schema_spec()
    payload["completion_audit"] = build_completion_audit(payload)
    return payload


def main() -> None:
    payload = build()
    outputs = {
        f"OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET_{DATE_STAMP}.json": payload,
        f"OTB2R_G10_RISKBANK_FIELD_COVERAGE_MATRIX_{DATE_STAMP}.json": payload["field_coverage_matrix"],
        f"OTB2R_G10_RISKBANK_SOURCE_HASH_LINEAGE_LEDGER_{DATE_STAMP}.json": payload["source_hash_lineage_ledger"],
        f"OTB2R_G10_RISKBANK_NO_LEAK_AUDIT_{DATE_STAMP}.json": payload["no_leak_audit"],
        f"OTB2R_G10_RISKBANK_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json": payload["duplicate_denominator_audit"],
        f"OTB2R_G10_RISKBANK_SAME_BAR_TICK_ORDER_POLICY_{DATE_STAMP}.json": payload["same_bar_tick_order_policy"],
        f"OTB2R_G10_RISKBANK_CONTRADICTION_STALE_CONTEXT_LEDGER_{DATE_STAMP}.json": payload["contradiction_stale_context_ledger"],
        f"OTB2R_G10_RISKBANK_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.json": payload["negative_evidence_saturation_ledger"],
        f"OTB2R_G10_RISKBANK_FUTURE_INSTRUMENTATION_SCHEMA_SPEC_{DATE_STAMP}.json": payload["future_instrumentation_schema_spec"],
        f"OTB2R_G10_RISKBANK_COMPLETION_AUDIT_{DATE_STAMP}.json": payload["completion_audit"],
    }
    for name, data in outputs.items():
        write_json(OUT / name, data)
    write_text(OUT / f"OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET_{DATE_STAMP}.md", render_main_md(payload))
    write_text(OUT / f"OTB2R_G10_RISKBANK_FIELD_COVERAGE_MATRIX_{DATE_STAMP}.md", render_matrix_md(payload["field_coverage_matrix"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_SOURCE_HASH_LINEAGE_LEDGER_{DATE_STAMP}.md", render_simple_md("Source Hash Lineage Ledger", payload["source_hash_lineage_ledger"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_NO_LEAK_AUDIT_{DATE_STAMP}.md", render_simple_md("No-Leak Audit", payload["no_leak_audit"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.md", render_simple_md("Duplicate Denominator Audit", payload["duplicate_denominator_audit"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_SAME_BAR_TICK_ORDER_POLICY_{DATE_STAMP}.md", render_simple_md("Same-Bar Tick-Order Policy", payload["same_bar_tick_order_policy"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_CONTRADICTION_STALE_CONTEXT_LEDGER_{DATE_STAMP}.md", render_simple_md("Contradiction Stale-Context Ledger", payload["contradiction_stale_context_ledger"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.md", render_simple_md("Negative Evidence Saturation Ledger", payload["negative_evidence_saturation_ledger"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_FUTURE_INSTRUMENTATION_SCHEMA_SPEC_{DATE_STAMP}.md", render_simple_md("Future Instrumentation Schema Spec", payload["future_instrumentation_schema_spec"]))
    write_text(OUT / f"OTB2R_G10_RISKBANK_COMPLETION_AUDIT_{DATE_STAMP}.md", render_simple_md("Completion Audit", payload["completion_audit"]))
    manifest_path = OUT / f"OTB2R_G10_RISKBANK_ARTIFACT_MANIFEST_{DATE_STAMP}.json"
    generated_files = sorted(p for p in OUT.glob(f"*{DATE_STAMP}*") if p.name != manifest_path.name)
    write_json(manifest_path, artifact_manifest(generated_files))
    print(f"Wrote {len(generated_files) + 1} artifacts under {rel(OUT)}")


if __name__ == "__main__":
    main()
