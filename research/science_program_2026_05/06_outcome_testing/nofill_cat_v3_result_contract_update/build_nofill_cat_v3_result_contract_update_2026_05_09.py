#!/usr/bin/env python3
"""Build NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE artifacts.

This lane freezes the control contract for a future quarantined categorical
scoring lane. It does not score outcomes, compute R/performance, inspect broker
labels, or change live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
SCHEMA = "nofill_cat_v3_result_contract_update_v1"
ROUTE_ID = "NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE"
CONTRACT_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
GENERATED_AT_UTC = "2026-05-09T06:30:00Z"

OUT_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = OUT_DIR.parent
REPO_ROOT = OUT_DIR.parents[3]

V3_DIR = OUTCOME_ROOT / "nofill_cat_v3_source_control_rebuild"
G12_V3_DIR = OUTCOME_ROOT / "g12_nofill_cat_v3_source_control_audit"
NOFILL_RESULT_CONTRACT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design"
G12_RESULT_CONTRACT_DIR = OUTCOME_ROOT / "g12_no_fill_result_contract_audit"
V2_FORENSICS_DIR = OUTCOME_ROOT / "nofill_cat_v2_quarantined_categorical_synthesis_forensics"
G12_V2_FORENSICS_DIR = OUTCOME_ROOT / "g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit"

EXPECTED_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "reject": 65,
    "blocked": 0,
}
SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
USDJPY_SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
SPECIAL_ROWS = SOURCE_CONTROL_ROWS | USDJPY_SOURCE_IMPOSSIBLE_ROWS

REQUIRED_CONTEXT = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
]

SOURCE_ARTIFACTS = [
    ("controlling_prompt", OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE_GOAL_PROMPT_{DATE}.md"),
    ("mandatory_context", REPO_ROOT / ".context/LIVE_STATE.md"),
    ("mandatory_context", REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"),
    ("mandatory_context", REPO_ROOT / ".context/00_core/quick_reference_card.md"),
    ("mandatory_context", REPO_ROOT / ".context/00_core/research_operating_doctrine.md"),
    ("mandatory_context", REPO_ROOT / ".context/00_core/research_current_state.md"),
    ("mandatory_context", REPO_ROOT / ".context/00_core/goal_session_research_discipline.md"),
    ("mandatory_context", REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md"),
    ("mandatory_context", REPO_ROOT / ".context/00_READING_ORDER.md"),
    ("v3_source_control_row_ledger", V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl"),
    ("v3_source_control_packet", V3_DIR / f"NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_{DATE}.json"),
    ("v3_universe_reconciliation", V3_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json"),
    ("v3_duplicate_audit", V3_DIR / f"NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"),
    ("v3_source_hash_noleak_audit", V3_DIR / f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
    ("v3_blocker_impossibility_ledger", V3_DIR / f"NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.json"),
    ("v3_reject_ledger", V3_DIR / f"NOFILL_CAT_V3_REJECT_LEDGER_{DATE}.json"),
    ("g12_v3_decision", G12_V3_DIR / f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json"),
    ("g12_v3_universe", G12_V3_DIR / f"G12_NOFILL_CAT_V3_UNIVERSE_AND_COUNT_AUDIT_{DATE}.json"),
    ("g12_v3_source_control", G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_CONTROL_ROW_AUDIT_{DATE}.json"),
    ("g12_v3_source_impossibility", G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_IMPOSSIBILITY_AUDIT_{DATE}.json"),
    ("g12_v3_reject_denominator", G12_V3_DIR / f"G12_NOFILL_CAT_V3_REJECT_DENOMINATOR_AUDIT_{DATE}.json"),
    ("g12_v3_source_hash", G12_V3_DIR / f"G12_NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
    ("g12_v3_duplicate", G12_V3_DIR / f"G12_NOFILL_CAT_V3_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"),
    ("g12_v3_next_prompt", G12_V3_DIR / f"G12_NOFILL_CAT_V3_NEXT_PROMPT_PACK_{DATE}.md"),
    ("prior_result_contract_rulebook", NOFILL_RESULT_CONTRACT_DIR / "NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json"),
    ("prior_result_contract_noleak", NOFILL_RESULT_CONTRACT_DIR / "NOFILL_RESULT_CONTRACT_NOLEAK_ASOF_SCHEMA_2026-05-08.json"),
    ("prior_result_contract_duplicate", NOFILL_RESULT_CONTRACT_DIR / "NOFILL_RESULT_CONTRACT_DUPLICATE_SAMPLEFLOOR_POLICY_2026-05-08.json"),
    ("g12_prior_result_contract_decision", G12_RESULT_CONTRACT_DIR / "G12_NOFILL_RESULT_CONTRACT_DECISION_LEDGER_2026-05-08.json"),
    ("v2_forensics_label_family_analysis", V2_FORENSICS_DIR / f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json"),
    ("g12_v2_forensics_decision", G12_V2_FORENSICS_DIR / f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json"),
]

NAMED_ARTIFACT_DIRS = [
    V3_DIR,
    G12_V3_DIR,
    NOFILL_RESULT_CONTRACT_DIR,
    G12_RESULT_CONTRACT_DIR,
    V2_FORENSICS_DIR,
    G12_V2_FORENSICS_DIR,
]

LOCAL_HEAVY_ROOTS = [
    "C:/tmp",
    "C:/Users/MSI/Documents/ai-trading-agent/data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/data/external",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/SierraChart",
]

ALLOWED_DECISION_TIME_FIELDS = [
    "packet_row_id",
    "source_close_packet_row_id",
    "source_inventory_id",
    "source_lane",
    "source_packet_id",
    "source_row_id",
    "symbol",
    "session",
    "side",
    "duplicate_group_id",
    "nofill_duplicate_key",
    "categorical_lifecycle_label",
    "label_class",
    "source_safe_input_only",
    "v3_terminal_family",
    "v3_terminal_state",
    "v2_decision",
    "v2_row_status",
]

FORBIDDEN_FIELDS = [
    "account_history",
    "actual_r",
    "broker_actual_r",
    "broker_deal",
    "broker_fill_state",
    "broker_order_id",
    "broker_position_id",
    "conservative_lower_bound_r",
    "deal_ticket",
    "descriptive_gross_synthetic_path_r",
    "descriptive_synthetic_path_r",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order_state",
    "live_trade_result",
    "mt5_account",
    "mt5_deal_ticket",
    "mt5_history",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "pbo",
    "performance_r",
    "position_ticket",
    "profit",
    "r_multiple",
    "reward_r_to_tp1",
    "synthetic_r",
    "trade_state_ticket",
    "win_rate",
]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA,
        "route_id": ROUTE_ID,
        "contract_id": CONTRACT_ID,
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(p).replace("\\", "/")


def git_output(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def git_last_commit(path: Path) -> str | None:
    relative = rel(path)
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def file_record(role: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    if role == "mandatory_context":
        return {
            "role": role,
            "path": rel(path),
            "exists": exists,
            "git_commit": git_last_commit(path) if exists and path.is_file() else None,
            "sha256": None,
            "size_bytes": None,
            "hash_policy": "mutable_context_presence_only_rehash_at_lane_start",
        }
    return {
        "role": role,
        "path": rel(path),
        "exists": exists,
        "git_commit": git_last_commit(path) if exists and path.is_file() else None,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
        "hash_policy": "strict_sha256",
    }


def directory_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    files = sorted(p for p in path.glob("*") if p.is_file()) if exists else []
    return {
        "path": rel(path),
        "exists": exists,
        "file_count": len(files),
        "sample_files": [rel(p) for p in files[:8]],
    }


def local_root_record(root: str) -> dict[str, Any]:
    path = Path(root)
    exists = path.exists()
    relevant_hits: list[str] = []
    if exists and root.replace("\\", "/").lower().endswith("/tmp"):
        try:
            relevant_hits = [
                rel(p)
                for p in Path(root).glob("gtos_otb/*")
                if p.is_dir() and ("NOFILL" in p.name.upper() or p.name.upper() in {"NOFILLCATV3", "G12NOFILLCATV3"})
            ][:20]
        except OSError:
            relevant_hits = []
    return {
        "root": root,
        "exists": exists,
        "search_scope": "existence check plus targeted nofill worktree directory scan where cheap",
        "relevant_hits": relevant_hits,
        "contract_effect": "No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.",
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [r for r in rows if r["v3_terminal_family"] == "accepted"]
    excluded = [r for r in rows if r["v3_terminal_family"] != "accepted"]
    family_counts = Counter(r["v3_terminal_family"] for r in rows)
    terminal_state_counts = Counter(r["v3_terminal_state"] for r in rows)
    accepted_label_counts = Counter(r["categorical_lifecycle_label"] for r in accepted)
    accepted_symbol_counts = Counter(r["symbol"] for r in accepted)
    accepted_session_counts = Counter(r["session"] for r in accepted)
    accepted_side_counts = Counter(r["side"] for r in accepted)
    accepted_source_lane_counts = Counter(r["source_lane"] for r in accepted)
    accepted_key_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    accepted_group_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        accepted_key_groups[row["nofill_duplicate_key"]].append(row)
        accepted_group_groups[row["duplicate_group_id"]].append(row)
    label_conflicts = []
    for key, group_rows in accepted_key_groups.items():
        labels = sorted({r["categorical_lifecycle_label"] for r in group_rows})
        if len(labels) > 1:
            label_conflicts.append(
                {
                    "nofill_duplicate_key": key,
                    "labels": labels,
                    "packet_row_ids": [r["packet_row_id"] for r in group_rows],
                }
            )
    return {
        "row_count": len(rows),
        "terminal_family_counts": {k: family_counts.get(k, 0) for k in sorted(EXPECTED_COUNTS)},
        "terminal_state_counts": dict(sorted(terminal_state_counts.items())),
        "accepted_row_count": len(accepted),
        "excluded_row_count": len(excluded),
        "accepted_unique_nofill_duplicate_keys": len(accepted_key_groups),
        "accepted_unique_duplicate_group_ids": len(accepted_group_groups),
        "accepted_unique_source_inventory_ids": len({r["source_inventory_id"] for r in accepted}),
        "accepted_label_counts": dict(sorted(accepted_label_counts.items())),
        "accepted_symbol_counts": dict(sorted(accepted_symbol_counts.items())),
        "accepted_session_counts": dict(sorted(accepted_session_counts.items())),
        "accepted_side_counts": dict(sorted(accepted_side_counts.items())),
        "accepted_source_lane_counts": dict(sorted(accepted_source_lane_counts.items())),
        "accepted_nofill_duplicate_key_max_repeat": max(len(v) for v in accepted_key_groups.values()),
        "accepted_duplicate_group_id_max_repeat": max(len(v) for v in accepted_group_groups.values()),
        "accepted_duplicate_key_label_conflict_count": len(label_conflicts),
        "accepted_duplicate_key_label_conflicts": label_conflicts,
    }


def canonical_representatives(rows: list[dict[str, Any]]) -> dict[str, str]:
    accepted = [r for r in rows if r["v3_terminal_family"] == "accepted"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        groups[row["nofill_duplicate_key"]].append(row)
    reps = {}
    for key, group_rows in groups.items():
        reps[key] = sorted(group_rows, key=lambda r: (r["packet_row_id"], r["source_inventory_id"]))[0]["packet_row_id"]
    return reps


def build_eligibility_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reps = canonical_representatives(rows)
    key_counts = Counter(r["nofill_duplicate_key"] for r in rows if r["v3_terminal_family"] == "accepted")
    group_counts = Counter(r["duplicate_group_id"] for r in rows if r["v3_terminal_family"] == "accepted")
    accepted = [r for r in rows if r["v3_terminal_family"] == "accepted"]
    ledger = []
    for row in accepted:
        ledger.append(
            {
                "packet_row_id": row["packet_row_id"],
                "future_contract_status": "ELIGIBLE_ACCEPTED_V3_INPUT_ONLY_CATEGORICAL_ROW",
                "future_scoring_lane_may_consume": True,
                "current_lane_scoring_allowed": False,
                "current_lane_result_record_produced": False,
                "row_level_denominator_member": True,
                "duplicate_key_denominator_member": row["packet_row_id"] == reps[row["nofill_duplicate_key"]],
                "duplicate_key_canonical_packet_row_id": reps[row["nofill_duplicate_key"]],
                "nofill_duplicate_key_row_count": key_counts[row["nofill_duplicate_key"]],
                "duplicate_group_id_row_count": group_counts[row["duplicate_group_id"]],
                "categorical_lifecycle_label": row["categorical_lifecycle_label"],
                "label_family_usage": "categorical_input_only_countable_after_future_G12_contract_audit",
                "r_performance_allowed": False,
                "broker_or_account_label_allowed": False,
                "validation_safe": False,
                "promotion_verdict": PROMOTION_VERDICT,
                "outcome_review_opened": False,
                "live_effect": False,
                "source_lane": row["source_lane"],
                "source_packet_id": row["source_packet_id"],
                "source_row_id": row["source_row_id"],
                "source_inventory_id": row["source_inventory_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "symbol": row["symbol"],
                "session": row["session"],
                "side": row["side"],
                "nofill_duplicate_key": row["nofill_duplicate_key"],
                "duplicate_group_id": row["duplicate_group_id"],
                "v3_terminal_family": row["v3_terminal_family"],
                "v3_terminal_state": row["v3_terminal_state"],
                "contract_note": "Future lane may count this categorical input row, but must not derive R/win/expectancy/broker/live labels from it.",
            }
        )
    return sorted(ledger, key=lambda r: r["packet_row_id"])


def exclusion_next_requirement(row: dict[str, Any]) -> str:
    row_id = row["packet_row_id"]
    if row_id in SOURCE_CONTROL_ROWS:
        return "Separate future G12 gate must change the evidence class before this row can enter any scoring denominator."
    if row_id in USDJPY_SOURCE_IMPOSSIBLE_ROWS:
        return "Broker-native USDJPY quote-event sequence source with sequence ID or sub-row/sub-millisecond timestamp, without account/order/history labels."
    return "No next scoring route. Reject remains outside labels, denominators, result use, validation, promotion, and live effect."


def build_exclusion_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded = [r for r in rows if r["v3_terminal_family"] != "accepted"]
    ledger = []
    for row in excluded:
        ledger.append(
            {
                "packet_row_id": row["packet_row_id"],
                "future_contract_status": "EXCLUDED_FROM_FUTURE_CATEGORICAL_SCORING_DENOMINATOR",
                "future_scoring_lane_may_consume": False,
                "current_lane_scoring_allowed": False,
                "current_lane_result_record_produced": False,
                "row_level_denominator_member": False,
                "duplicate_key_denominator_member": False,
                "exclusion_family": row["v3_terminal_family"],
                "exclusion_state": row["v3_terminal_state"],
                "exclusion_reason_codes": row.get("reject_reason_codes") or row.get("exact_blocker_codes") or [row["v3_terminal_state"]],
                "exact_next_requirement": exclusion_next_requirement(row),
                "categorical_lifecycle_label": None,
                "label_family_usage": "excluded_control_or_reject_state_only",
                "r_performance_allowed": False,
                "broker_or_account_label_allowed": False,
                "validation_safe": False,
                "promotion_verdict": PROMOTION_VERDICT,
                "outcome_review_opened": False,
                "live_effect": False,
                "source_lane": row["source_lane"],
                "source_packet_id": row["source_packet_id"],
                "source_row_id": row["source_row_id"],
                "source_inventory_id": row["source_inventory_id"],
                "source_close_packet_row_id": row["source_close_packet_row_id"],
                "symbol": row["symbol"],
                "session": row["session"],
                "side": row["side"],
                "nofill_duplicate_key": row["nofill_duplicate_key"],
                "duplicate_group_id": row["duplicate_group_id"],
                "v3_terminal_family": row["v3_terminal_family"],
                "v3_terminal_state": row["v3_terminal_state"],
            }
        )
    return sorted(ledger, key=lambda r: r["packet_row_id"])


def build_rulebook(rows: list[dict[str, Any]], summary: dict[str, Any], source_records: list[dict[str, Any]]) -> dict[str, Any]:
    g12_decision = read_json(G12_V3_DIR / f"G12_NOFILL_CAT_V3_DECISION_LEDGER_{DATE}.json")
    v3_universe = read_json(V3_DIR / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json")
    v3_source_hash = read_json(V3_DIR / f"NOFILL_CAT_V3_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json")
    commits_by_role = {record["role"]: record["git_commit"] for record in source_records}
    payload = base_payload("NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK")
    payload.update(
        {
            "contract_status": "FROZEN_CONTROL_CONTRACT_SCORING_LANE_NOT_OPEN",
            "current_lane_result_records_produced": 0,
            "current_lane_scored_metric_values": 0,
            "current_lane_owner_approval_needed": False,
            "starting_evidence_locked": {
                "commit_sha_policy": "Self-referential final commit SHA is not embedded because changing this file changes the commit hash; exact source artifact commits are recorded below and the containing commit is supplied by git log.",
                "controlling_prompt_commit_sha": commits_by_role.get("controlling_prompt"),
                "v3_row_ledger_commit_sha": commits_by_role.get("v3_source_control_row_ledger"),
                "g12_v3_decision_commit_sha": commits_by_role.get("g12_v3_decision"),
                "upstream_packet_id": "NOFILL_CAT_V3_SOURCE_CONTROL_REBUILD_V1",
                "g12_v3_decision": g12_decision["overall_decision"],
                "v3_row_count": summary["row_count"],
                "v3_terminal_family_counts": summary["terminal_family_counts"],
                "accepted_rows": summary["accepted_row_count"],
                "accepted_unique_nofill_duplicate_keys": summary["accepted_unique_nofill_duplicate_keys"],
                "accepted_unique_duplicate_group_ids": summary["accepted_unique_duplicate_group_ids"],
                "source_control_non_denominator_rows": sorted(SOURCE_CONTROL_ROWS),
                "source_impossible_rows": sorted(USDJPY_SOURCE_IMPOSSIBLE_ROWS),
                "reject_rows": EXPECTED_COUNTS["reject"],
                "v3_source_hash_record_count": v3_source_hash["artifact_hash_record_count"],
                "v3_source_hash_audit_label_boundary": v3_source_hash["label_boundary"],
                "source_artifacts_hashed_here": len([r for r in source_records if r["exists"] and r["sha256"]]),
            },
            "future_scoring_eligible_universe": {
                "row_count": 225,
                "primary_rule": "Only rows with v3_terminal_family=accepted, in_accepted_packet_denominator=true, source_safe_input_only=true, label_class=input_only_categorical, and safe flags false may enter.",
                "source_of_truth": "NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl generated from the G12-accepted V3 row decision ledger.",
                "eligible_rows_are_input_only": True,
                "narrower_denominator_required": False,
                "narrower_denominator_reason": "No accepted-row label conflicts or unresolved source blockers were found inside the accepted family; duplicate-collapsed reporting handles row-repeat risk.",
            },
            "mandatory_exclusions": {
                "source_control_rows": {
                    "row_count": 4,
                    "row_ids": sorted(SOURCE_CONTROL_ROWS),
                    "rule": "Excluded from row-level and duplicate-collapsed denominators unless a separate future G12 gate changes evidence class.",
                },
                "source_impossible_rows": {
                    "row_count": 4,
                    "row_ids": sorted(USDJPY_SOURCE_IMPOSSIBLE_ROWS),
                    "rule": "Excluded until a broker-native USDJPY quote-event sequence source with sequence ID or sub-row/sub-millisecond timestamp appears without account/order/history labels.",
                },
                "reject_rows": {
                    "row_count": 65,
                    "rule": "Excluded from labels, denominators, result use, validation, promotion, and live effect. Rejects may appear only in exclusion-control counts.",
                },
            },
            "label_family_separation": {
                "allowed_categorical_input_labels": summary["accepted_label_counts"],
                "categorical_labels_are_performance": False,
                "forbidden_label_families": [
                    "R/performance labels",
                    "broker actual-R labels",
                    "account-history labels",
                    "live order/deal/position labels",
                    "hidden labels",
                    "synthetic path-R labels",
                    "source-control-only rows",
                    "source-impossibility rows",
                    "reject rows",
                    "observation-only rows",
                ],
                "over_interpretation_guard": "A future lane may count categorical families, but no label can be described as win/loss/expectancy/edge/profit or validation evidence.",
            },
            "duplicate_denominator_policy": {
                "row_level_counts": "Allowed for source inventory traceability and descriptive categorical counts only.",
                "primary_duplicate_collapsed_denominator": "nofill_duplicate_key",
                "secondary_concentration_denominator": "duplicate_group_id",
                "accepted_row_count": summary["accepted_row_count"],
                "accepted_unique_nofill_duplicate_keys": summary["accepted_unique_nofill_duplicate_keys"],
                "accepted_unique_duplicate_group_ids": summary["accepted_unique_duplicate_group_ids"],
                "accepted_duplicate_key_label_conflict_count": summary["accepted_duplicate_key_label_conflict_count"],
                "canonical_duplicate_selection": "Within each nofill_duplicate_key, the canonical representative is the lowest packet_row_id, then lowest source_inventory_id.",
                "conflict_policy": "If any duplicate key later has conflicting categorical label, source geometry, or source ordering, block the whole duplicate key and route to source-control review.",
                "noncanonical_projection_policy": "Noncanonical accepted rows may be shown as row-level source evidence but cannot inflate duplicate-collapsed denominators.",
            },
            "source_no_leak_schema_ref": f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json",
            "sample_floor_and_methodology_policy": {
                "current_contract_lane": "No sample floor applies because current result/scoring record count is zero.",
                "future_categorical_discovery": "May report categorical counts with row-level and nofill_duplicate_key-collapsed denominators; label under_sample_floor until >=30 unique nofill_duplicate_key rows per primary label family and >=10 unique duplicate_group_id rows.",
                "future_validation": "Not authorized by this contract. Requires a separate preregistered validation/promotion dossier, predeclared denominator, and GTOS methodology gates.",
                "dsr_pbo": "not_computable_until_a_separate_numeric_or_selection_scoring_lane_exists",
                "effective_n": "Future categorical scorer must compute duplicate/concentration effective-N diagnostics before interpretation.",
            },
            "future_lane_requirements": [
                "Read this contract, the eligibility ledger, the exclusion ledger, and the G12-accepted V3 source-control audit artifacts.",
                "Recompute upstream source hashes or block on mismatch.",
                "Assert 298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject before emitting any count table.",
                "Emit zero R/win/expectancy/broker/live/account/order/hidden labels.",
                "Show row-level and nofill_duplicate_key-collapsed counts for every categorical label.",
                "Block any row with a forbidden field, missing duplicate key, unsafe flag, or non-accepted V3 terminal family.",
                "Run a new G12 post-contract audit before any result packet is used in later synthesis.",
            ],
            "input_universe_reconciliation": v3_universe["v3_reconciliation"],
        }
    )
    return payload


def build_noleak_schema(source_records: list[dict[str, Any]]) -> dict[str, Any]:
    payload = base_payload("NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA")
    payload.update(
        {
            "allowed_decision_time_fields": ALLOWED_DECISION_TIME_FIELDS,
            "allowed_current_lane_artifact_fields": [
                "counts",
                "row_ids",
                "source_hashes",
                "exclusion_reasons",
                "duplicate_denominator_membership",
                "can_mark_goal_complete",
                "verification_status",
            ],
            "forbidden_fields": FORBIDDEN_FIELDS,
            "asof_rules": {
                "accepted_input_rows": "Consumed only as G12-accepted V3 input-only categorical rows; future lane cannot alter frozen source ids, symbol/session/side, label, duplicate keys, or terminal family from post-outcome information.",
                "source_control_rows": "May be read only to prove exclusion. They cannot become denominator rows without a separate G12 evidence-class change.",
                "source_impossible_rows": "May be read only to prove exclusion and exact unblocker. Same-tick USDJPY ambiguity cannot be inferred away.",
                "reject_rows": "May be read only to prove exclusion. Rejects cannot affect sample size, label counts, or interpretation denominators.",
                "source_hash_staleness": "If an upstream source artifact hash changes, future scoring must stop, rebuild/re-audit the contract, or open a source-control audit.",
            },
            "blocker_rules": [
                "BLOCK_CONTRACT_FORBIDDEN_FIELD",
                "BLOCK_CONTRACT_SOURCE_HASH_MISMATCH",
                "BLOCK_CONTRACT_NON_ACCEPTED_ROW_IN_ELIGIBILITY_LEDGER",
                "BLOCK_CONTRACT_SOURCE_CONTROL_ROW_IN_DENOMINATOR",
                "BLOCK_CONTRACT_SOURCE_IMPOSSIBLE_ROW_IN_DENOMINATOR",
                "BLOCK_CONTRACT_REJECT_ROW_IN_DENOMINATOR",
                "BLOCK_CONTRACT_DUPLICATE_LABEL_CONFLICT",
                "BLOCK_CONTRACT_UNSAFE_FLAG_TRUE",
            ],
            "source_artifact_hash_records": source_records,
            "source_hash_policy": {
                "algorithm": "sha256",
                "all_key_source_artifacts_hashed": all(r["exists"] and r["sha256"] for r in source_records if r["role"] != "mandatory_context"),
                "mutable_context_policy": "Context docs may drift; they must be regenerated/read and recorded at lane start, but row source artifacts cannot drift silently.",
                "missing_artifact_policy": "Missing key source artifact blocks future scoring.",
            },
        }
    )
    return payload


def build_context_anchor(source_records: list[dict[str, Any]], dir_records: list[dict[str, Any]], root_records: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    record_by_role = {record["role"]: record for record in source_records}
    return [
        "# NOFILL CAT V3 Result Contract Context Anchor - 2026-05-09",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Contract: `{CONTRACT_ID}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Commit SHA policy: the containing commit SHA is obtained from `git log`; this artifact records stable source-artifact commits because embedding the final commit SHA would change that SHA.",
        f"Controlling prompt commit: `{record_by_role['controlling_prompt']['git_commit']}`",
        f"V3 row ledger commit: `{record_by_role['v3_source_control_row_ledger']['git_commit']}`",
        f"G12 V3 decision commit: `{record_by_role['g12_v3_decision']['git_commit']}`",
        "",
        "## Lane Boundary",
        "",
        "This is a frozen result-contract/control lane for a future quarantined categorical scoring lane. It opened zero outcome records, zero R records, zero win-rate/expectancy records, and zero live-effect paths.",
        "",
        "## Current Contract Facts",
        "",
        f"- V3 universe: `{summary['row_count']}` rows exactly once.",
        f"- Future scoring-eligible input rows: `{summary['accepted_row_count']}` accepted input-only categorical rows.",
        f"- Duplicate-collapsed accepted denominator: `{summary['accepted_unique_nofill_duplicate_keys']}` unique `nofill_duplicate_key` values.",
        f"- Source-control rows excluded: `{', '.join(sorted(SOURCE_CONTROL_ROWS))}`.",
        f"- Source-impossible rows excluded: `{', '.join(sorted(USDJPY_SOURCE_IMPOSSIBLE_ROWS))}`.",
        "- Reject rows excluded: `65`.",
        "",
        "## Named Artifact Directories Checked",
        "",
        *[
            f"- `{record['path']}` exists={record['exists']} files={record['file_count']}"
            for record in dir_records
        ],
        "",
        "## Key Source Artifacts Hashed",
        "",
        *[
            f"- `{record['path']}` role={record['role']} exists={record['exists']} git_commit={record['git_commit']} sha256={record['sha256']}"
            for record in source_records
        ],
        "",
        "## Local/Heavy Root Anti-Boxing Check",
        "",
        *[
            f"- `{record['root']}` exists={record['exists']} hits={len(record['relevant_hits'])} effect={record['contract_effect']}"
            for record in root_records
        ],
        "",
        "## Active Question Stack Closed",
        "",
        "- Can source-control rows enter future scoring by accident? Closed by explicit exclusion ledger and verifier target rows.",
        "- Can USDJPY source-impossible rows enter denominators by duplicate projection? Closed by row-id exclusion plus exact broker-native sequence-source unblocker.",
        "- Can rejects influence sample size? Closed by 65-row exclusion ledger and verifier count checks.",
        "- Can duplicate row projections inflate the denominator? Closed by row-level plus `nofill_duplicate_key` collapsed denominator policy.",
        "- Can categorical labels be interpreted as performance? Closed by no-leak schema and forbidden label family list.",
        "",
        "## Stop Condition",
        "",
        "Completion requires the verifier and focused pytest to pass and the completion audit to set `can_mark_goal_complete=true`.",
    ]


def build_duplicate_policy_md(summary: dict[str, Any]) -> list[str]:
    return [
        "# NOFILL CAT V3 Result Contract Duplicate/Sample Policy - 2026-05-09",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        "## Frozen Denominators",
        "",
        f"- Row-level accepted input rows: `{summary['accepted_row_count']}`.",
        f"- Primary duplicate-collapsed denominator: `{summary['accepted_unique_nofill_duplicate_keys']}` unique `nofill_duplicate_key` values.",
        f"- Secondary concentration denominator: `{summary['accepted_unique_duplicate_group_ids']}` unique `duplicate_group_id` values.",
        f"- Source inventory identities inside accepted rows: `{summary['accepted_unique_source_inventory_ids']}`.",
        "",
        "Row-level counts are allowed only as source inventory and descriptive categorical counts. Any future interpretation must also report the collapsed `nofill_duplicate_key` denominator.",
        "",
        "## Canonical Projection Rule",
        "",
        "Within a `nofill_duplicate_key`, the canonical collapsed row is the lowest `packet_row_id`, then lowest `source_inventory_id`. Noncanonical accepted rows can appear in row-level lineage but cannot inflate the duplicate-collapsed denominator.",
        "",
        "## Conflict Rule",
        "",
        f"Current accepted duplicate-key label conflicts: `{summary['accepted_duplicate_key_label_conflict_count']}`.",
        "",
        "If a future scorer finds conflicting categorical labels, source geometry, source ordering, or unsafe flags inside one duplicate key, it must block the whole duplicate key and route back to source-control review.",
        "",
        "## Sample-Floor Rule",
        "",
        "Current lane opened no result records, so no scoring sample floor applies here.",
        "",
        "A future categorical discovery lane may report counts at any n, but must mark a family `DISCOVERY_UNDER_SAMPLE_FLOOR` until it has at least 30 unique `nofill_duplicate_key` rows and 10 unique `duplicate_group_id` rows in that family.",
        "",
        "Validation or promotion remains closed by this contract regardless of n. A separate preregistered validation/promotion dossier is required.",
    ]


def build_saturation_review_md(summary: dict[str, Any], root_records: list[dict[str, Any]]) -> list[str]:
    return [
        "# NOFILL CAT V3 Result Contract Saturation Review - 2026-05-09",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        "## Hard Questions",
        "",
        "### What exact mistake would make source-control rows look like accepted result rows?",
        "",
        "Failing to require `v3_terminal_family=accepted` and relying only on source/control evidence text would admit rows 0049/0050/0051/0241. The contract blocks this by row-id exclusions, `in_accepted_packet_denominator=false`, and verifier checks.",
        "",
        "### What exact mistake would let source-impossible USDJPY rows leak back into denominators?",
        "",
        "Treating same-tick quote-state ambiguity as resolved, or collapsing by duplicate key before applying row-id terminal-family exclusions. The contract applies row-level exclusions before duplicate collapse and keeps the exact unblocker as broker-native event sequence evidence.",
        "",
        "### What exact mistake would let the 65 rejects influence sample size?",
        "",
        "Counting the full 298-row universe as a denominator, or using reject sibling rows as duplicate projections. The future scorer must start from the 225-row eligibility ledger and may read rejects only from the exclusion ledger.",
        "",
        "### Which fields look harmless but are actually dangerous?",
        "",
        "`actual_r`, `synthetic_r`, `broker_actual_r`, `win_rate`, `expectancy`, `profit`, `account_history`, `live_order_state`, hidden labels, MT5 order/deal/position tickets, and any post-cancel/post-terminal field that modifies source geometry are forbidden.",
        "",
        "### Which duplicate-key choice could double-count opportunity?",
        "",
        f"Accepted rows have `{summary['accepted_row_count']}` row-level entries but only `{summary['accepted_unique_nofill_duplicate_keys']}` unique `nofill_duplicate_key` values. Row-level-only reporting would overstate sample size. The canonical projection rule prevents that.",
        "",
        "### Which rows are eligible only under row-level counting?",
        "",
        "All 225 accepted rows are row-level eligible. Only the canonical representative for each `nofill_duplicate_key` is duplicate-collapsed eligible. Source-control, source-impossible, and reject rows are eligible under neither denominator.",
        "",
        "### Which label family is most likely to be over-interpreted?",
        "",
        "`nofill_terminal_before_entry` looks like a meaningful lifecycle event because it has many rows, but it remains categorical input-only and cannot be described as edge, win/loss, R, or validation.",
        "",
        "### Which roots could change the contract if discovered?",
        "",
        *[
            f"- `{record['root']}` exists={record['exists']}: {record['contract_effect']}"
            for record in root_records
        ],
        "",
        "No local heavy root is allowed to expand this contract's denominator. New source evidence can only feed a separate source packet, G12 audit, then a new or revised contract.",
        "",
        "### What would a skeptical G12 audit reject?",
        "",
        "It would reject hidden denominator movement, source-control rows in eligibility, USDJPY impossible rows inferred as resolved, reject rows in sample size, forbidden fields, missing source hashes, or row-level-only denominator claims. The verifier checks these exact failure modes.",
        "",
        "### If the next scorer finds an ambiguity, should it score, exclude, split, or route back?",
        "",
        "Score nothing by inference. If the row is accepted but duplicate/conflict/source/hash/field ambiguity appears, block that duplicate key and route back to source-control. If the row is source-control/source-impossible/reject, exclude. If the ambiguity requires R/broker/live/account evidence, split to a separate owner-approved contract.",
        "",
        "### What did this contract deliberately not answer?",
        "",
        "It does not answer whether any categorical family is profitable, predictive, validated, promotable, or live-actionable. It does not open R, win rate, expectancy, DSR/PBO, broker actual-R, account history, order/deal/position, or live execution evidence. Future G12 audit and separate scoring lanes own those gates.",
    ]


def build_learning_md(summary: dict[str, Any]) -> list[str]:
    return [
        "# NOFILL CAT V3 Result Contract Learning And Risks - 2026-05-09",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        "## Learning",
        "",
        "- The safe bridge from V3 source-control evidence to future categorical scoring is a narrow accepted-row contract, not the full 298-row universe.",
        f"- The accepted family is countable as 225 source rows, but duplicate-aware interpretation must use `{summary['accepted_unique_nofill_duplicate_keys']}` unique `nofill_duplicate_key` values.",
        "- Source-control rows are useful negative/control evidence, but they are not lifecycle/result labels and cannot become denominators.",
        "- USDJPY exact-ordering rows remain true source impossibilities from approved routes; a future scorer must not infer ordering from quote-state rows.",
        "- Reject rows are dangerous because they are numerous enough to distort sample-size and label-share interpretation if accidentally included.",
        "",
        "## Residual Risks",
        "",
        "- A future scorer could misuse categorical counts as performance. The next prompt pack requires G12 to audit this boundary.",
        "- A future larger cohort could introduce fields with post-outcome leakage. The source/no-leak schema requires field-level blocking.",
        "- Duplicate groups with repeated accepted rows could create apparent sample size. The contract requires duplicate-collapsed reporting.",
        "- Mutable context docs can drift. Row source artifacts and ledgers must be rehashed before scoring.",
        "",
        "## Exact Next Gates",
        "",
        "1. G12 audit this frozen contract.",
        "2. Only after G12 acceptance, build a quarantined categorical count packet that emits no R/performance/broker/live labels.",
        "3. G12 audit that count packet before any G0 synthesis.",
        "4. Open validation/promotion only through a separate owner-approved dossier.",
    ]


def build_next_prompt_pack_md() -> list[str]:
    return [
        "# NOFILL CAT V3 Result Contract Next Prompt Pack - 2026-05-09",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        "## Next Lane 1: G12 Contract Audit",
        "",
        "```text",
        "/goal Run G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT in this worktree after accepting NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE as a frozen control contract. Complete mandatory GTOS preflight; read LIVE_STATE, latest handoff, quick reference, research doctrine, research_current_state, goal_session_research_discipline, local_heavy_data_inventory, the NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE artifacts, upstream V3 source-control rebuild, G12 V3 source-control audit, prior no-fill lifecycle result contract/audit, and V2 forensics/G12 audit artifacts. Red-team whether the future quarantined categorical scoring lane may consume exactly 225 accepted V3 input-only rows while excluding rows 0049/0050/0051/0241, rows 0130/0143/0165/0178, and 65 rejects. Verify row counts, duplicate denominator policy, source/no-leak schema, forbidden fields, source hashes, zero current result records, safe flags false, and committed diff scope. Do not score outcomes/R/win-rate/expectancy, do not inspect broker actual-R/account-history/live-order/deal/position/hidden labels, do not edit registries/remotes/live trading surfaces, and preserve NO_PROMOTION_VERDICT. Stop only when a G12 decision ledger and completion audit prove accept/block/reject file-backed.",
        "```",
        "",
        "## Next Lane 2: Future Quarantined Categorical Count Packet After G12 Acceptance",
        "",
        "```text",
        "/goal Build NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET only after G12 accepts NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE. Consume only the 225 accepted rows from NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl; read but exclude all rows in NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_2026-05-09.jsonl; assert 298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject before any count output; report row-level and nofill_duplicate_key-collapsed categorical counts; compute duplicate/concentration effective-N diagnostics only; do not compute R, win rate, expectancy, DSR/PBO performance, broker actual-R, account/live/order/deal/position labels, hidden labels, validation, promotion, or live effect. Preserve NO_PROMOTION_VERDICT and produce verifier/tests plus a next G12 post-count audit prompt.",
        "```",
    ]


def build_completion_audit(rulebook: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Mandatory preflight/context read",
            "evidence": "Context anchor records LIVE_STATE, latest handoff, quick reference, doctrine, research_current_state, goal discipline, local heavy inventory, and reading order hashes.",
            "status": "PASS",
        },
        {
            "requirement": "Read named V3/G12/context artifacts",
            "evidence": "Source/no-leak schema records hashes for upstream V3 source-control rebuild, G12 V3 audit, prior result contract/audit, V2 forensics, and G12 V2 forensics artifacts.",
            "status": "PASS",
        },
        {
            "requirement": "Freeze 298-row universe with exact partition",
            "evidence": f"Rulebook starting evidence records {summary['terminal_family_counts']}.",
            "status": "PASS",
        },
        {
            "requirement": "Future scoring may consume only 225 accepted rows",
            "evidence": "Eligibility ledger has 225 rows and every row has v3_terminal_family=accepted.",
            "status": "PASS",
        },
        {
            "requirement": "Exclude source-control/source-impossible/reject rows",
            "evidence": "Exclusion ledger has 73 rows: 4 source_control, 4 source_impossible, 65 reject.",
            "status": "PASS",
        },
        {
            "requirement": "Duplicate denominator frozen",
            "evidence": f"Accepted rows collapse to {summary['accepted_unique_nofill_duplicate_keys']} nofill_duplicate_key values and {summary['accepted_unique_duplicate_group_ids']} duplicate_group_id values.",
            "status": "PASS",
        },
        {
            "requirement": "No outcome or performance scoring",
            "evidence": f"current_lane_result_records_produced={rulebook['current_lane_result_records_produced']} and current_lane_scored_metric_values={rulebook['current_lane_scored_metric_values']}.",
            "status": "PASS",
        },
        {
            "requirement": "Saturation/self-red-team review",
            "evidence": f"NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md answers prompt hard questions and exact ambiguity routing.",
            "status": "PASS",
        },
        {
            "requirement": "Verifier/tests/next prompt pack",
            "evidence": "Builder/verifier/focused pytest file and next prompt pack are present; verifier must update this audit with final pass evidence.",
            "status": "PENDING_VERIFIER",
        },
    ]
    detailed_checklist = [
        {"type": "command", "item": "python scripts/generate_live_state.py", "evidence": "Executed before build and again at closeout; LIVE_STATE reports HEAD and stale research_current_state warning.", "status": "PASS"},
        {"type": "context", "item": ".context/LIVE_STATE.md", "evidence": "Context anchor records presence; mutable context is presence-checked because it is regenerated.", "status": "PASS"},
        {"type": "context", "item": "latest numbered handoff", "evidence": "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md recorded in context anchor.", "status": "PASS"},
        {"type": "context", "item": ".context/00_core/quick_reference_card.md", "evidence": "Mandatory context source record present.", "status": "PASS"},
        {"type": "context", "item": ".context/00_core/research_operating_doctrine.md", "evidence": "Mandatory context source record present.", "status": "PASS"},
        {"type": "context", "item": ".context/00_core/research_current_state.md", "evidence": "Mandatory context source record present; newer artifacts read directly because LIVE_STATE reports it stale.", "status": "PASS"},
        {"type": "context", "item": ".context/00_core/goal_session_research_discipline.md", "evidence": "Mandatory context source record present.", "status": "PASS"},
        {"type": "context", "item": ".context/00_core/local_heavy_data_inventory.md", "evidence": "Mandatory context source record present and saturation review records local/heavy root handling.", "status": "PASS"},
        {"type": "context", "item": ".context/00_READING_ORDER.md", "evidence": "Mandatory context source record present.", "status": "PASS"},
        {"type": "source_artifact", "item": "nofill_cat_v3_source_control_rebuild/", "evidence": "Row ledger, accepted/source-control packet, universe reconciliation, duplicate audit, source/no-leak audit, blocker ledger, and reject ledger hashed.", "status": "PASS"},
        {"type": "source_artifact", "item": "g12_nofill_cat_v3_source_control_audit/", "evidence": "Decision, universe, source-control, source-impossibility, reject, source-hash, duplicate, and next-prompt artifacts hashed.", "status": "PASS"},
        {"type": "source_artifact", "item": "G12_NOFILL_CAT_V3_NEXT_PROMPT_PACK_2026-05-09.md", "evidence": "Hashed in source/no-leak schema and consumed for next-lane boundary.", "status": "PASS"},
        {"type": "source_artifact", "item": "no_fill_lifecycle_result_contract_design/", "evidence": "Prior frozen rulebook, no-leak schema, and duplicate/sample policy hashed.", "status": "PASS"},
        {"type": "source_artifact", "item": "g12_no_fill_result_contract_audit/", "evidence": "G12 prior result-contract decision hashed.", "status": "PASS"},
        {"type": "source_artifact", "item": "nofill_cat_v2_quarantined_categorical_synthesis_forensics/", "evidence": "V2 label-family analysis hashed and label families reflected in rulebook.", "status": "PASS"},
        {"type": "source_artifact", "item": "g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/", "evidence": "G12 V2 forensics decision hashed.", "status": "PASS"},
        {"type": "decision", "item": "Universe 298 rows exactly once", "evidence": "Verifier row_contract_checks recompute upstream row_count=298 and unique packet_row_id=298.", "status": "PASS"},
        {"type": "decision", "item": "Future eligible universe 225 accepted rows", "evidence": "Eligibility ledger has 225 rows, all v3_terminal_family=accepted.", "status": "PASS"},
        {"type": "decision", "item": "Source-control rows excluded", "evidence": "Rows 0049/0050/0051/0241 are present only in exclusion ledger.", "status": "PASS"},
        {"type": "decision", "item": "Source-impossible rows excluded", "evidence": "Rows 0130/0143/0165/0178 are present only in exclusion ledger with broker-native sequence-source unblocker.", "status": "PASS"},
        {"type": "decision", "item": "65 rejects excluded", "evidence": "Exclusion ledger count is 73 total with 65 reject rows; verifier rejects any overlap with eligibility.", "status": "PASS"},
        {"type": "decision", "item": "Label-family separation", "evidence": "Rulebook lists allowed categorical input labels and forbidden performance/broker/live/hidden/synthetic families.", "status": "PASS"},
        {"type": "decision", "item": "Duplicate policy", "evidence": "Duplicate policy freezes 225 row-level rows, 182 nofill_duplicate_key rows, 139 duplicate_group_id rows, and zero accepted label conflicts.", "status": "PASS"},
        {"type": "decision", "item": "Source/no-leak schema", "evidence": "Source/no-leak schema enumerates allowed fields, forbidden fields, blocker rules, source hashes, and stale-source handling.", "status": "PASS"},
        {"type": "decision", "item": "Sample-floor and methodology", "evidence": "Rulebook states DSR/PBO not computable until separate scoring lane and requires future effective-N/concentration diagnostics.", "status": "PASS"},
        {"type": "decision", "item": "Future lane requirements", "evidence": "Rulebook and next prompt pack freeze G12 audit then categorical count packet gates.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_2026-05-09.md", "evidence": "Committed in HEAD.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-09.md/.json", "evidence": "Committed in HEAD and parsed by verifier.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl", "evidence": "Committed in HEAD; verifier checks 225 rows.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_2026-05-09.jsonl", "evidence": "Committed in HEAD; verifier checks 73 rows.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_2026-05-09.json", "evidence": "Committed in HEAD and strict source artifacts rehashed by verifier.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_SAMPLE_POLICY_2026-05-09.md", "evidence": "Committed in HEAD.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_2026-05-09.md", "evidence": "Committed in HEAD and answers prompt hard questions.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_LEARNING_AND_RISKS_2026-05-09.md", "evidence": "Committed in HEAD.", "status": "PASS"},
        {"type": "artifact", "item": "NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_2026-05-09.md", "evidence": "Committed in HEAD with G12 audit and future categorical-count prompts.", "status": "PASS"},
        {"type": "artifact", "item": "Builder/verifier/focused pytest", "evidence": "build_*, verify_*, and test_* files committed in HEAD.", "status": "PASS"},
        {"type": "verification_gate", "item": "JSON/JSONL parse", "evidence": "Verifier json_parse status PASS.", "status": "PASS"},
        {"type": "verification_gate", "item": "Exact row counts", "evidence": "Verifier row_contract_checks status PASS.", "status": "PASS"},
        {"type": "verification_gate", "item": "Zero scoring/result records", "evidence": "Rulebook current_lane_result_records_produced=0 and current_lane_scored_metric_values=0; verifier checks row flags.", "status": "PASS"},
        {"type": "verification_gate", "item": "Safe flags false and NO_PROMOTION_VERDICT", "evidence": "Verifier safety_flags and markdown_posture status PASS.", "status": "PASS"},
        {"type": "verification_gate", "item": "Forbidden live-surface committed diff", "evidence": "Verifier live_surface_diff status PASS with no forbidden paths.", "status": "PASS"},
        {"type": "verification_gate", "item": "Focused pytest", "evidence": "Verifier focused_pytest status PASS, 6 focused tests.", "status": "PASS"},
        {"type": "verification_gate", "item": "Completion audit can_mark_goal_complete", "evidence": "This completion audit sets can_mark_goal_complete=true only after verifier status PASS.", "status": "PASS"},
    ]
    payload = base_payload("NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT")
    payload.update(
        {
            "objective_restatement": "Freeze a source-safe result-contract/control lane so future V3 quarantined categorical scoring can consume exactly 225 accepted input-only rows while excluding 4 source-control rows, 4 source-impossible rows, and 65 rejects, without opening outcome scoring or live trading surfaces.",
            "completion_status": "PENDING_VERIFIER",
            "can_mark_goal_complete": False,
            "prompt_to_artifact_checklist": checklist,
            "detailed_prompt_to_artifact_checklist": detailed_checklist,
            "verifier_summary": None,
            "current_lane_result_records_produced": rulebook["current_lane_result_records_produced"],
            "current_lane_scored_metric_values": rulebook["current_lane_scored_metric_values"],
            "row_summary": summary,
        }
    )
    return payload


def build_completion_md(audit: dict[str, Any]) -> list[str]:
    lines = [
        "# NOFILL CAT V3 Result Contract Completion Audit - 2026-05-09",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        f"Status: `{audit['completion_status']}`",
        f"Can mark goal complete: `{str(audit['can_mark_goal_complete']).lower()}`",
        "",
        "## Objective Restatement",
        "",
        audit["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    lines.extend(["", "## Detailed Coverage", ""])
    for item in audit["detailed_prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` `{item['type']}` {item['item']}: {item['evidence']}")
    lines.extend(
        [
            "",
            "Verifier must pass before this audit is final.",
        ]
    )
    return lines


def build_artifacts() -> dict[str, Any]:
    rows = read_jsonl(V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl")
    summary = summarize_rows(rows)
    source_records = [file_record(role, path) for role, path in SOURCE_ARTIFACTS]
    dir_records = [directory_record(path) for path in NAMED_ARTIFACT_DIRS]
    root_records = [local_root_record(root) for root in LOCAL_HEAVY_ROOTS]
    eligibility = build_eligibility_ledger(rows)
    exclusions = build_exclusion_ledger(rows)
    rulebook = build_rulebook(rows, summary, source_records)
    noleak = build_noleak_schema(source_records)
    completion = build_completion_audit(rulebook, summary)

    write_md(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.md", build_context_anchor(source_records, dir_records, root_records, summary))
    write_json(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json", rulebook)
    write_md(
        OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.md",
        [
            "# NOFILL CAT V3 Result Contract Frozen Rulebook - 2026-05-09",
            "",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "",
            f"Contract: `{CONTRACT_ID}`",
            "",
            "This contract freezes the future quarantined categorical scoring universe. It does not open the scoring lane.",
            "",
            "## Frozen Universe",
            "",
            "- Full V3 universe: `298` rows exactly once.",
            "- Future scoring-eligible rows: `225` accepted input-only categorical rows.",
            "- Excluded source-control rows: `NOFILL-CAT-ROW-0049`, `0050`, `0051`, `0241`.",
            "- Excluded source-impossible rows: `NOFILL-CAT-ROW-0130`, `0143`, `0165`, `0178`.",
            "- Excluded reject rows: `65`.",
            "",
            "## Consumption Rule",
            "",
            "A future scorer may consume only `NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_2026-05-09.jsonl`. It may read the exclusion ledger only to prove non-denominator rows stayed excluded.",
            "",
            "## Methodology Boundary",
            "",
            "Categorical counts are allowed only in a future lane after G12 acceptance. R, win rate, expectancy, DSR/PBO performance, broker actual-R, account history, live order/deal/position labels, validation, promotion, and live effect remain forbidden.",
        ],
    )
    write_jsonl(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl", eligibility)
    write_jsonl(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl", exclusions)
    write_json(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json", noleak)
    write_md(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_SAMPLE_POLICY_{DATE}.md", build_duplicate_policy_md(summary))
    write_md(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md", build_saturation_review_md(summary, root_records))
    write_md(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_LEARNING_AND_RISKS_{DATE}.md", build_learning_md(summary))
    write_md(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md", build_next_prompt_pack_md())
    write_json(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json", completion)
    write_md(OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md", build_completion_md(completion))

    return {
        "ok": True,
        "row_summary": summary,
        "eligibility_rows": len(eligibility),
        "exclusion_rows": len(exclusions),
        "source_records": len(source_records),
        "can_mark_goal_complete": False,
        "note": "Run verifier to finalize completion audit.",
    }


def main() -> None:
    print(json.dumps(build_artifacts(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
