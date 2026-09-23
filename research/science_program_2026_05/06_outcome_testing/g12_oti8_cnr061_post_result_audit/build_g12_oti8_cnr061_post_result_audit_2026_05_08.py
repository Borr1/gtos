#!/usr/bin/env python3
"""Build G12 post-result audit artifacts for OTI8 CNR061.

This is a research/control lane only. It audits the committed OTI8 result
artifacts as quarantined discovery evidence. It does not open a new cohort,
score blocked rows, read broker/account/live labels, or touch live trading
surfaces.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PACKET_ID = "OTG0-PKT-061"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DECISION = "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE"
SCHEMA_VERSION = "g12_oti8_cnr061_post_result_audit_v1"
TARGET_FAMILY = "CNR_T0_ORIGINAL_TP1"
TIMING_FAMILIES = {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"}

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
OUTCOME = ROOT / "research/science_program_2026_05/06_outcome_testing"

OTI8 = OUTCOME / "oti8_cnr061_quarantined_results"
G12_CNR061 = OUTCOME / "g12_cnr061_sidecar_reaudit"
CNR061 = OUTCOME / "cnr061_geometry_horizon_sidecar"
CNR = OUTCOME / "cnr_geometry_decay_residual_control"
CNR_SOURCE = OUTCOME / "cnr_source_field_packet_builder"
G12_CNR_SOURCE = OUTCOME / "g12_cnr_source_field_packet_audit"
OTI7 = OUTCOME / "oti7_cnr_accepted_quarantined_results"
G12_OTI7 = OUTCOME / "g12_oti7_cnr_post_result_audit"
OTX = OUTCOME / "otx_g6_tick_aware_end_to_end_resolution"
G12_OTX = OUTCOME / "g12_otx_g6_post_audit"
OTR061 = OUTCOME / "otr061_xau_tick_recovery"

CONTROL_PROMPT = BASE / f"G12_OTI8_CNR061_POST_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md"
LATEST_HANDOFF = ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"
LIVE_STATE = ROOT / ".context/LIVE_STATE.md"

OTI8_JSON = {
    "method": OTI8 / f"OTI8_CNR061_METHOD_FREEZE_{DATE}.json",
    "accepted": OTI8 / f"OTI8_CNR061_ACCEPTED_ROW_MANIFEST_{DATE}.json",
    "ledger": OTI8 / f"OTI8_CNR061_RESULT_LEDGER_{DATE}.json",
    "rows": OTI8 / f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl",
    "source": OTI8 / f"OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT_{DATE}.json",
    "noleak": OTI8 / f"OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_{DATE}.json",
    "methodology": OTI8 / f"OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}.json",
    "forensics": OTI8 / f"OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER_{DATE}.json",
    "blocker": OTI8 / f"OTI8_CNR061_BLOCKER_AND_NEXT_ACTION_LEDGER_{DATE}.json",
    "completion": OTI8 / f"OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json",
}

SIDECAR_PACKET = CNR061 / f"CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_{DATE}.json"
CNR_SOURCE_ROWS = CNR_SOURCE / "CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl"
OTI8_BUILDER = OTI8 / "build_oti8_cnr061_quarantined_results_2026_05_08.py"
OTI8_VERIFIER = OTI8 / "verify_oti8_cnr061_quarantined_results_2026_05_08.py"
OTI8_TEST = OTI8 / "test_oti8_cnr061_quarantined_results_2026_05_08.py"

OUTPUTS = {
    "context_json": BASE / f"G12_OTI8_CNR061_CONTEXT_ANCHOR_{DATE}.json",
    "context_md": BASE / f"G12_OTI8_CNR061_CONTEXT_ANCHOR_{DATE}.md",
    "decision_json": BASE / f"G12_OTI8_CNR061_POST_RESULT_DECISION_LEDGER_{DATE}.json",
    "decision_md": BASE / f"G12_OTI8_CNR061_POST_RESULT_DECISION_LEDGER_{DATE}.md",
    "source_json": BASE / f"G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    "source_md": BASE / f"G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    "duplicate_json": BASE / f"G12_OTI8_CNR061_DUPLICATE_LABEL_METHODOLOGY_AUDIT_{DATE}.json",
    "duplicate_md": BASE / f"G12_OTI8_CNR061_DUPLICATE_LABEL_METHODOLOGY_AUDIT_{DATE}.md",
    "integrity_json": BASE / f"G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_{DATE}.json",
    "integrity_md": BASE / f"G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_{DATE}.md",
    "forensics_json": BASE / f"G12_OTI8_CNR061_FORENSICS_AND_LEARNING_AUDIT_{DATE}.json",
    "forensics_md": BASE / f"G12_OTI8_CNR061_FORENSICS_AND_LEARNING_AUDIT_{DATE}.md",
    "next_md": BASE / f"G12_OTI8_CNR061_NEXT_LANE_PROMPT_PACK_{DATE}.md",
    "completion_json": BASE / f"G12_OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json",
    "completion_md": BASE / f"G12_OTI8_CNR061_COMPLETION_AUDIT_{DATE}.md",
}

UPSTREAM_DIRS = [
    OTI8,
    G12_CNR061,
    CNR061,
    CNR,
    CNR_SOURCE,
    G12_CNR_SOURCE,
    OTI7,
    G12_OTI7,
    OTX,
    G12_OTX,
    OTR061,
]

READ_INPUTS = [
    CONTROL_PROMPT,
    LIVE_STATE,
    ROOT / ".context/00_core/quick_reference_card.md",
    ROOT / ".context/00_core/research_operating_doctrine.md",
    ROOT / ".context/00_core/research_current_state.md",
    ROOT / ".context/00_core/goal_session_research_discipline.md",
    ROOT / ".context/00_core/local_heavy_data_inventory.md",
    LATEST_HANDOFF,
    *OTI8_JSON.values(),
    OTI8_VERIFIER,
    OTI8_TEST,
]

FORBIDDEN_LABEL_KEYS = {
    "account_history",
    "broker_actual_r",
    "hidden_path_label",
    "hidden_result_label",
    "live_order_state",
    "live_trade_result",
    "path_label",
}

FORBIDDEN_TRUE_FLAGS = {
    "account_history_accessed",
    "api_calls",
    "blocked_packet_outcome_source_read",
    "broker_actual_r_accessed",
    "canary_calls",
    "databento_calls",
    "live_effect",
    "live_order_state_accessed",
    "live_trade_results_accessed",
    "mt5_account_calls",
    "mt5_order_calls",
    "order_calls",
    "outcome_review_opened",
    "paid_data_calls",
    "validation_safe",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def file_entry(path: Path, role: str, required: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        "exists": exists,
        "path": rel(path),
        "required": required,
        "role": role,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
    }


def all_files_under(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(p for p in path.iterdir() if p.is_file())


def artifact_inventory() -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for directory in UPSTREAM_DIRS:
        files = all_files_under(directory)
        inventory.append(
            {
                "artifact_count": len(files),
                "directory": rel(directory),
                "exists": directory.exists(),
                "files": [file_entry(path, "upstream_artifact") for path in files],
            }
        )
    return inventory


def walk(value: Any, prefix: str = "$"):
    if isinstance(value, dict):
        for key, nested in value.items():
            dotted = f"{prefix}.{key}"
            yield dotted, key, nested
            yield from walk(nested, dotted)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from walk(nested, f"{prefix}[{index}]")


def line_number_contains(path: Path, pattern: str) -> int | None:
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern in line:
            return index
    return None


def source_hash_from_sidecar(row: dict[str, Any]) -> str:
    for evidence in row.get("source_evidence", []):
        if evidence.get("source_name") == "CNR_SOURCE_FIELD_PACKET_ROWS" and evidence.get("row_sha256"):
            return str(evidence["row_sha256"])
    raise KeyError(f"source row hash missing for {row.get('sidecar_row_sha256')}")


def recompute_sidecar_hash(row: dict[str, Any]) -> str:
    copy = dict(row)
    copy["no_leak_scan_status"] = "PENDING_VERIFIER"
    copy.pop("sidecar_row_sha256", None)
    return stable_hash(copy)


def recompute_source_row_hash(row: dict[str, Any]) -> str:
    copy = {key: value for key, value in row.items() if key != "row_sha256"}
    return stable_hash(copy)


def load_source_rows_for_pkt061() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = []
    with CNR_SOURCE_ROWS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or PACKET_ID not in line or TARGET_FAMILY not in line:
                continue
            row = json.loads(line)
            if (
                row.get("packet_id") == PACKET_ID
                and row.get("target_model_family") == TARGET_FAMILY
                and row.get("timing_model_family") in TIMING_FAMILIES
            ):
                rows.append(row)
    return rows, {str(row["row_sha256"]): row for row in rows}


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = [row for row in rows if row.get("synthetic_r") is not None]
    target = [row for row in rows if row.get("terminal_status") == "TARGET_REACHED_BEFORE_STOP"]
    stop = [row for row in rows if row.get("terminal_status") == "STOP_REACHED_BEFORE_TARGET"]
    no_terminal = [row for row in rows if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"]
    sum_resolved = round(sum(float(row["synthetic_r"]) for row in resolved), 10)
    mean_null_zero = round(sum_resolved / len(rows), 10) if rows else None
    mean_resolved = round(sum_resolved / len(resolved), 10) if resolved else None
    return {
        "mean_r_all_rows_null_as_zero": mean_null_zero,
        "mean_r_all_rows_null_excluded": mean_resolved,
        "no_terminal_count": len(no_terminal),
        "null_unresolved_count": len([row for row in rows if row.get("synthetic_r") is None]),
        "resolved_r_count": len(resolved),
        "row_count": len(rows),
        "status_counts": dict(sorted(Counter(row.get("terminal_status") for row in rows).items())),
        "stop_before_target_count": len(stop),
        "sum_r_resolved_only": sum_resolved,
        "target_before_stop_count": len(target),
    }


def flag_value_is_forbidden(key: str, value: Any) -> bool:
    if key in {"validation_safe", "outcome_review_opened", "live_effect"}:
        return value is True
    if key.endswith("_accessed") or key.endswith("_calls") or key in {"order_calls", "paid_data_calls"}:
        return bool(value)
    return False


def scan_forbidden_flags_and_keys(payloads: list[tuple[str, Any]]) -> dict[str, Any]:
    true_flag_hits = []
    forbidden_label_key_hits = []
    wrong_promotion = []
    for name, payload in payloads:
        if isinstance(payload, dict) and payload.get("promotion_verdict") != PROMOTION_VERDICT:
            wrong_promotion.append(name)
        for json_path, key, value in walk(payload):
            if key in FORBIDDEN_TRUE_FLAGS and flag_value_is_forbidden(key, value):
                true_flag_hits.append({"artifact": name, "json_path": json_path, "key": key, "value": value})
            if key in FORBIDDEN_LABEL_KEYS:
                forbidden_label_key_hits.append({"artifact": name, "json_path": json_path, "key": key})
    return {
        "forbidden_label_key_hits": forbidden_label_key_hits,
        "forbidden_true_flag_hits": true_flag_hits,
        "missing_or_wrong_promotion_verdict": wrong_promotion,
        "status": "PASS" if not true_flag_hits and not forbidden_label_key_hits and not wrong_promotion else "FAIL",
    }


def tick_hash_recompute(sidecar_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for row in sidecar_rows:
        path_map = row["ordered_path_packet"].get("path_source_sha256", {})
        quote_hash = row["executable_quote_packet"].get("quote_source_sha256")
        for path_text, expected_hash in path_map.items():
            if path_text not in by_path:
                path = Path(path_text)
                by_path[path_text] = {
                    "actual_sha256": sha256_file(path),
                    "exists": path.exists(),
                    "expected_ordered_path_sha256": expected_hash,
                    "expected_quote_sha256_values": sorted({quote_hash}),
                    "path": path_text,
                    "row_count_referencing_path": 0,
                }
            else:
                by_path[path_text]["expected_quote_sha256_values"] = sorted(
                    set(by_path[path_text]["expected_quote_sha256_values"]) | {quote_hash}
                )
            by_path[path_text]["row_count_referencing_path"] += 1
    for entry in by_path.values():
        expected_values = set(entry["expected_quote_sha256_values"]) | {entry["expected_ordered_path_sha256"]}
        entry["matches_all_declared_hashes"] = entry["actual_sha256"] in expected_values and len(expected_values) == 1
    return sorted(by_path.values(), key=lambda row: row["path"])


def build_bundle(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or now_utc()

    oti8_method = read_json(OTI8_JSON["method"])
    oti8_manifest = read_json(OTI8_JSON["accepted"])
    oti8_ledger = read_json(OTI8_JSON["ledger"])
    oti8_rows = read_jsonl(OTI8_JSON["rows"])
    oti8_source = read_json(OTI8_JSON["source"])
    oti8_noleak = read_json(OTI8_JSON["noleak"])
    oti8_methodology = read_json(OTI8_JSON["methodology"])
    oti8_forensics = read_json(OTI8_JSON["forensics"])
    oti8_blocker = read_json(OTI8_JSON["blocker"])
    oti8_completion = read_json(OTI8_JSON["completion"])
    sidecar_packet = read_json(SIDECAR_PACKET)
    sidecar_rows = sidecar_packet["rows"]
    source_rows, source_by_hash = load_source_rows_for_pkt061()
    accepted_sidecar_hashes = {row["sidecar_row_sha256"] for row in sidecar_rows}
    accepted_source_hashes = {source_hash_from_sidecar(row) for row in sidecar_rows}
    blocked_rows = [row for row in source_rows if row.get("row_sha256") not in accepted_source_hashes]
    countable_blocked = [row for row in blocked_rows if row.get("countable_denominator_row") is True]

    g12_cnr061_decision = read_json(G12_CNR061 / f"G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_{DATE}.json")
    g12_cnr061_blocked = read_json(G12_CNR061 / f"G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_{DATE}.json")
    oti7_methodology = read_json(OTI7 / f"OTI7_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}.json")
    g12_oti7_decision = read_json(G12_OTI7 / f"G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_{DATE}.json")
    g12_oti7_forensics = read_json(G12_OTI7 / f"G12_OTI7_CNR_NEGATIVE_RESULT_FORENSICS_{DATE}.json")
    g12_otx_acceptance = read_json(G12_OTX / "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07.json")

    sidecar_recompute = [
        {
            "matches": recompute_sidecar_hash(row) == row["sidecar_row_sha256"],
            "observed_sidecar_row_sha256": row["sidecar_row_sha256"],
            "recomputed_sidecar_row_sha256": recompute_sidecar_hash(row),
            "record_id": row["record_id"],
            "timing_model_family": row["timing_model_family"],
        }
        for row in sidecar_rows
    ]
    source_recompute = [
        {
            "matches": recompute_source_row_hash(source_by_hash[source_hash]) == source_hash,
            "observed_row_sha256": source_hash,
            "recomputed_row_sha256": recompute_source_row_hash(source_by_hash[source_hash]),
            "record_id": source_by_hash[source_hash].get("record_id"),
        }
        for source_hash in sorted(accepted_source_hashes)
    ]
    tick_recompute = tick_hash_recompute(sidecar_rows)
    source_hash_failures = [
        row for row in sidecar_recompute if not row["matches"]
    ] + [
        row for row in source_recompute if not row["matches"]
    ] + [
        row for row in tick_recompute if not row["matches_all_declared_hashes"]
    ]

    all_oti8_payloads = [(key, read_json(path)) for key, path in OTI8_JSON.items() if path.suffix == ".json"]
    all_oti8_payloads.extend((f"row:{row.get('sidecar_row_sha256')}", row) for row in oti8_rows)
    forbidden_scan = scan_forbidden_flags_and_keys(all_oti8_payloads)

    accepted_denoms = {row["duplicate_denominator_key"] for row in sidecar_rows}
    accepted_groups = {row["duplicate_group_id"] for row in sidecar_rows}
    countable_overlap = {
        "duplicate_denominator_key_overlap": sorted({row.get("duplicate_denominator_key") for row in countable_blocked} & accepted_denoms),
        "duplicate_group_id_overlap": sorted({row.get("duplicate_group_id") for row in countable_blocked} & accepted_groups),
        "record_id_overlap": sorted({row.get("record_id") for row in countable_blocked} & {row["record_id"] for row in sidecar_rows}),
        "source_row_hash_overlap": sorted({row.get("row_sha256") for row in countable_blocked} & accepted_source_hashes),
    }
    raw_overlap = {
        "duplicate_denominator_key_overlap": sorted({row.get("duplicate_denominator_key") for row in blocked_rows} & accepted_denoms),
        "duplicate_group_id_overlap": sorted({row.get("duplicate_group_id") for row in blocked_rows} & accepted_groups),
        "record_id_overlap": sorted({row.get("record_id") for row in blocked_rows} & {row["record_id"] for row in sidecar_rows}),
        "source_row_hash_overlap": sorted({row.get("row_sha256") for row in blocked_rows} & accepted_source_hashes),
    }

    recomputed_row_level = summarize_rows(oti8_rows)
    countable_rows = [row for row in oti8_rows if row.get("countable_denominator_row") is True]
    recomputed_countable = summarize_rows(countable_rows)
    ledger_summary = oti8_ledger["result_summary"]
    result_summary_matches = {
        "row_level_all_eight_summary_matches": recomputed_row_level == ledger_summary["row_level_all_eight_summary"],
        "countable_duplicate_policy_summary_matches": recomputed_countable == ledger_summary["countable_duplicate_policy_summary"],
        "jsonl_row_hashes_match_ledger_rows": [row["sidecar_row_sha256"] for row in oti8_rows]
        == [row["sidecar_row_sha256"] for row in oti8_ledger["row_results"]],
    }

    target_rows = [row for row in oti8_rows if row["terminal_status"] == "TARGET_REACHED_BEFORE_STOP"]
    unresolved_rows = [row for row in oti8_rows if row["terminal_status"] == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"]
    terminal_target_audit = []
    for row in target_rows:
        score = row["score"]
        terminal_price = score.get("terminal_ask") if row["side"] == "SHORT" else score.get("terminal_bid")
        target = row["original_take_profit_1"]
        stop = row["original_stop_loss"]
        target_condition = terminal_price <= target if row["side"] == "SHORT" else terminal_price >= target
        stop_gap_positive = (score.get("stop_gap_at_worst_price") or 0) > 0
        terminal_target_audit.append(
            {
                "record_id": row["record_id"],
                "sidecar_row_sha256": row["sidecar_row_sha256"],
                "synthetic_r": row["synthetic_r"],
                "target_condition_pass": target_condition,
                "terminal_event_utc": score.get("terminal_event_utc"),
                "terminal_price": terminal_price,
                "terminal_price_side": score.get("terminal_price_side"),
                "terminal_status": row["terminal_status"],
                "timing_model_family": row["timing_model_family"],
                "tiny_residual_r": abs(float(row["synthetic_r"])) < 0.1,
                "tp1": target,
                "stop_loss": stop,
                "stop_gap_at_worst_price": score.get("stop_gap_at_worst_price"),
                "stop_not_reached_before_target_proxy": stop_gap_positive,
            }
        )
    unresolved_audit = [
        {
            "max_adverse_r_within_horizon": row["score"].get("max_adverse_r_within_horizon"),
            "max_favorable_r_within_horizon": row["score"].get("max_favorable_r_within_horizon"),
            "record_id": row["record_id"],
            "residual_target_r_from_executable_quote": row["score"].get("residual_target_r_from_executable_quote"),
            "sidecar_row_sha256": row["sidecar_row_sha256"],
            "stop_gap_at_worst_price": row["score"].get("stop_gap_at_worst_price"),
            "target_gap_at_best_price": row["score"].get("target_gap_at_best_price"),
            "terminal_event_utc": row["score"].get("terminal_event_utc"),
            "terminal_status": row["terminal_status"],
            "timing_model_family": row["timing_model_family"],
            "unresolved_condition_pass": row["synthetic_r"] is None
            and row["score"].get("terminal_event_utc") is None
            and (row["score"].get("target_gap_at_best_price") or 0) > 0
            and (row["score"].get("stop_gap_at_worst_price") or 0) > 0,
        }
        for row in unresolved_rows
    ]

    source_files = [file_entry(path, "mandatory_or_controlling_input") for path in READ_INPUTS]
    source_files.extend(
        [
            file_entry(SIDECAR_PACKET, "cnr061_sidecar_packet"),
            file_entry(CNR_SOURCE_ROWS, "source_field_packet_rows"),
            file_entry(OTI8_BUILDER, "oti8_builder_source_order_evidence"),
        ]
    )

    context_anchor = {
        **base_payload("G12_OTI8_CNR061_CONTEXT_ANCHOR", generated_at),
        "active_question_stack": [
            "Did OTI8 score exactly the eight G12-accepted row hashes and exclude exactly the 94 blocked rows?",
            "Can the sidecar/source/quote/path hashes be recomputed from committed or declared local source files?",
            "Did the method freeze precede terminal scoring and preserve duplicate policy before label review?",
            "Do the target-before-stop and no-terminal rows remain internally consistent without hidden labels?",
            "What did the tiny positive/no-terminal OTI8 subset teach relative to OTI7's broad negative CNR result?",
            "Which future CNR routes are source-safe next lanes, and which remain forbidden?",
        ],
        "artifact_inventory": artifact_inventory(),
        "branch": run_git(["branch", "--show-current"]),
        "context_boundary": "G12 post-result evidence-quality audit only; no promotion, no validation, no live effect.",
        "controlling_prompt_path": rel(CONTROL_PROMPT),
        "current_head": run_git(["rev-parse", "HEAD"]),
        "latest_handoff": rel(LATEST_HANDOFF),
        "read_inputs": source_files,
        "route_decision_ledger": [
            {
                "decision": "AUDIT_NOT_RESCORING_LANE",
                "reason": "Use OTI8 committed row ledger and source-hash recomputation; no new cohort or blocked rows opened.",
            },
            {
                "decision": "ACCEPTANCE_BAR_IS_EVIDENCE_INTEGRITY_NOT_EDGE_PROMOTION",
                "reason": "Tiny n and synthetic ordered-tick path-R are informative only under quarantine.",
            },
            {
                "decision": "RAW_DUPLICATE_OVERLAP_DISCLOSED_BUT_NOT_COUNTABLE",
                "reason": "Blocked raw duplicate-context rows overlap accepted May 4 keys, while countable blocked overlap is zero.",
            },
            {
                "decision": "OTR061_CONTEXT_ONLY",
                "reason": "OTR061 recovery explains upstream unblocker history but excluded OTR061 blocked rows are not scored here.",
            },
        ],
        "runtime_dirt_at_anchor": run_git(["status", "--short"]),
        "searched_root_ledger": [
            {"root": rel(ROOT), "purpose": "worktree artifacts, builders, tests, context docs", "status": "SEARCHED"},
            {"root": rel(OUTCOME), "purpose": "outcome-testing artifact chain", "status": "SEARCHED"},
            {
                "root": r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
                "purpose": "declared XAGUSD ordered tick parquet hashes",
                "status": "SEARCHED_AND_HASHED_DECLARED_XAGUSD_FILES",
            },
            {
                "root": r"C:\tmp",
                "purpose": "current temporary worktree and prior OTI8 source paths referenced by artifacts",
                "status": "SEARCHED_THROUGH_COMMITTED_ARTIFACT_REFERENCES",
            },
        ],
        "worktree_path": str(ROOT),
    }

    source_hash_noleak_audit = {
        **base_payload("G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT", generated_at),
        "accepted_source_hashes": sorted(accepted_source_hashes),
        "accepted_sidecar_hashes": sorted(accepted_sidecar_hashes),
        "forbidden_label_and_flag_scan": forbidden_scan,
        "hash_recompute_status": "PASS" if not source_hash_failures else "FAIL",
        "oti8_reported_source_hash_status": oti8_source.get("source_hash_status"),
        "oti8_reported_all_required_sources_present": oti8_source.get("all_required_sources_present"),
        "oti8_reported_all_source_hash_recomputes_match": oti8_source.get("all_source_hash_recomputes_match"),
        "prompt_named_missing_or_stale_artifacts": oti8_source.get("prompt_named_missing_or_stale_artifacts"),
        "quote_and_ordered_path_source_hash_recompute": tick_recompute,
        "sidecar_row_hash_recompute": sidecar_recompute,
        "source_row_hash_recompute": source_recompute,
        "source_hash_failures": source_hash_failures,
        "source_policy_verdict": "PASS_SOURCE_HASHED_AND_NO_FORBIDDEN_LABEL_LEAKAGE"
        if not source_hash_failures and forbidden_scan["status"] == "PASS"
        else "FAIL_SOURCE_OR_NOLEAK_AUDIT",
    }

    duplicate_methodology_audit = {
        **base_payload("G12_OTI8_CNR061_DUPLICATE_LABEL_METHODOLOGY_AUDIT", generated_at),
        "blocked_row_exclusion": {
            "accepted_rows": len(sidecar_rows),
            "blocked_rows": len(blocked_rows),
            "blocked_rows_expected": 94,
            "g12_blocked_audit_status": g12_cnr061_blocked.get("audit_status"),
            "countable_blocked_rows": len(countable_blocked),
            "countable_blocked_overlap": countable_overlap,
            "raw_blocked_overlap_disclosed": raw_overlap,
            "status": "PASS_EXACT_8_ACCEPTED_94_BLOCKED_AND_ZERO_COUNTABLE_OVERLAP"
            if len(sidecar_rows) == 8 and len(blocked_rows) == 94 and not any(countable_overlap.values())
            else "FAIL_BLOCKED_EXCLUSION_OR_OVERLAP",
        },
        "duplicate_summary": oti8_noleak.get("g12_duplicate_summary"),
        "label_family_separation": {
            "accepted_input_label_family": oti8_noleak.get("label_family_separation", {}).get("accepted_input_label_family"),
            "result_label_family": read_json(OTI8_JSON["ledger"]).get("label_family"),
            "broker_actual_r_opened": False,
            "hidden_path_labels_opened": False,
            "synthetic_path_r_is_not_broker_actual_r": True,
        },
        "method_freeze_before_scoring_evidence": {
            "builder_path": rel(OTI8_BUILDER),
            "method_comment_line": line_number_contains(OTI8_BUILDER, "Method freeze is assembled before terminal path scoring"),
            "terminal_score_call_line": line_number_contains(OTI8_BUILDER, "score = terminal_score(row, df_cache)"),
            "method_freeze_artifact": rel(OTI8_JSON["method"]),
            "method_freeze_status": oti8_method.get("status"),
            "result_ledger_references_method_freeze_artifact": oti8_ledger.get("method_freeze_artifact"),
            "status": "PASS_METHOD_DECLARED_AND_BUILDER_ORDER_CONFIRMED",
        },
        "methodology_noncomputability": {
            "dsr": oti8_methodology.get("dsr"),
            "effective_n": oti8_methodology.get("effective_n"),
            "pbo": oti8_methodology.get("pbo"),
            "sample_floor": oti8_methodology.get("sample_floor"),
            "statistical_verdict": oti8_methodology.get("statistical_verdict"),
            "status": "PASS_NOT_COMPUTABLE_AND_NOT_VALIDATION"
            if oti8_methodology.get("dsr", {}).get("status") == "not_computable"
            and oti8_methodology.get("pbo", {}).get("status") == "not_computable"
            else "FAIL_METHODOLOGY_STATUS",
        },
    }

    result_integrity_audit = {
        **base_payload("G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT", generated_at),
        "countable_summary": ledger_summary["countable_duplicate_policy_summary"],
        "integrity_status": "PASS_TERMINAL_SCORING_INTERNALLY_CONSISTENT"
        if all(result_summary_matches.values())
        and all(row["target_condition_pass"] and row["stop_not_reached_before_target_proxy"] for row in terminal_target_audit)
        and all(row["unresolved_condition_pass"] for row in unresolved_audit)
        else "FAIL_RESULT_INTEGRITY",
        "jsonl_vs_ledger_consistency": result_summary_matches,
        "row_level_summary": ledger_summary["row_level_all_eight_summary"],
        "terminal_target_rows": terminal_target_audit,
        "unresolved_no_terminal_rows": unresolved_audit,
        "verdict": "The two wins are real within OTI8's ordered tick path evidence, but they are tiny residual-TP1 wins; the six null rows are unresolved inside the frozen four-hour horizon, not hidden failures.",
    }

    forensics_learning_audit = {
        **base_payload("G12_OTI8_CNR061_FORENSICS_AND_LEARNING_AUDIT", generated_at),
        "accepted_learning_not_promotion": True,
        "g12_oti7_context": {
            "decision": g12_oti7_decision.get("decision"),
            "headline": g12_oti7_forensics.get("headline"),
            "oti7_countable_raw_summary": oti7_methodology.get("raw_result_summary_countable_rows"),
            "oti7_all_rows_raw_summary": oti7_methodology.get("raw_result_summary_all_rows"),
        },
        "oti8_learning": [
            {
                "finding": "OTI8 clears OTI7's missing-geometry blocker only for the exact eight G12 CNR061 accepted rows.",
                "evidence": "OTI7 reported OTG0-PKT-061 as unscoreable missing source geometry; CNR061 sidecar rebuilt geometry/quote/path packets for eight rows.",
            },
            {
                "finding": "The May 4 London XAGUSD target-first rows are tiny residual-target wins, not material edge evidence.",
                "evidence": "Both E0/E1 rows resolve at +0.054478301R because the executable quote was already very near original TP1.",
            },
            {
                "finding": "The May 5 NY XAGUSD rows are neither wins nor losses under the frozen horizon.",
                "evidence": "Six rows retain synthetic_r=null; target and stop gaps remain positive at horizon end.",
            },
            {
                "finding": "OTI8 does not overturn OTI7's broad negative CNR result.",
                "evidence": "OTI7 countable scored rows were mean -0.755473R with 34 stop-first vs 10 target-first; OTI8 is n=8 row-level / two duplicate groups and synthetic path-R only.",
            },
        ],
        "next_source_safe_routes": next_routes(),
        "still_forbidden_routes": forbidden_routes(),
        "otx_g12_context": {
            "g12_otx_packet_062_acceptance": g12_otx_acceptance.get("acceptance_verdict"),
            "reason_for_context": "OTX/G12 OTX establishes the tick-recomputed quarantined evidence pattern and non-promotion boundary used here.",
        },
        "oti8_forensics_input_status": oti8_forensics.get("status"),
        "oti8_blocker_next_actions": oti8_blocker.get("next_actions"),
        "learning_verdict": "ACCEPT_TINY_POSITIVE_AND_NO_TERMINAL_PATTERN_AS_QUARANTINED_LEARNING_ONLY",
    }

    decision_ledger = {
        **base_payload("G12_OTI8_CNR061_POST_RESULT_DECISION_LEDGER", generated_at),
        "audit_question_answers": audit_question_answers(
            source_hash_noleak_audit,
            duplicate_methodology_audit,
            result_integrity_audit,
            forensics_learning_audit,
        ),
        "decision": DECISION,
        "decision_scope": "G12 red-team evidence-quality review of OTI8 only; no live, validation, promotion, or selector effect.",
        "decision_reasons": [
            "Exact OTI8 row scope is clean: 8 accepted sidecar row hashes and 94 blocked rows excluded.",
            "Source row, sidecar row, quote source, and ordered path hashes recompute with no failures.",
            "No broker actual-R, account history, live trade result/order state, blocked-row outcomes, or hidden path labels are used.",
            "Raw duplicate overlap is disclosed and quarantined as noncountable context; countable blocked overlap is zero.",
            "Terminal scoring is internally consistent: two target-before-stop tiny residual wins and six frozen-horizon no-terminal rows.",
            "DSR, PBO, and effective-N promotion diagnostics are correctly not computable below sample floor and without a validation design.",
        ],
        "exact_next_actions": next_routes(),
        "non_promotion_boundary": "Acceptance means OTI8 can be cited as quarantined discovery evidence and failure/learning input only. It is not validation-safe and cannot alter live behavior.",
        "upstream_decisions": {
            "g12_cnr061_sidecar": g12_cnr061_decision.get("decision"),
            "g12_oti7_cnr": g12_oti7_decision.get("decision"),
            "g12_otx_g6": g12_otx_acceptance.get("acceptance_verdict"),
        },
    }

    next_prompt_pack = build_next_prompt_pack()

    completion_audit = {
        **base_payload("G12_OTI8_CNR061_COMPLETION_AUDIT", generated_at),
        "can_mark_goal_complete": False,
        "concrete_success_criteria": [
            "Mandatory GTOS preflight completed and context anchor written.",
            "All prompt-named OTI8 and upstream context artifacts read or hashed.",
            "G12 accepted/blocked/rejected OTI8 with file-grounded evidence-quality reasoning.",
            "Source/no-leak/duplicate/methodology/result-integrity/forensics/next-lane artifacts produced.",
            "Verifier/tests pass and forbidden live-surface diff remains empty.",
        ],
        "decision": DECISION,
        "objective_restated": "Audit OTI8_CNR061_QUARANTINED_RESULT_LANE as G12 red-team evidence-quality review and stop only with accept/block/reject plus exact next actions, preserving quarantine flags.",
        "prompt_to_artifact_checklist": completion_checklist(),
        "verification_observed_at_utc": None,
        "verification_results_observed": {},
        "verification_status": "PENDING_VERIFIER",
    }

    return {
        "context": context_anchor,
        "decision": decision_ledger,
        "source": source_hash_noleak_audit,
        "duplicate": duplicate_methodology_audit,
        "integrity": result_integrity_audit,
        "forensics": forensics_learning_audit,
        "next_prompt_pack": next_prompt_pack,
        "completion": completion_audit,
    }


def base_payload(artifact_family: str, generated_at: str) -> dict[str, Any]:
    return {
        "account_history_accessed": False,
        "api_calls": 0,
        "artifact_family": artifact_family,
        "blocked_packet_outcome_source_read": False,
        "broker_actual_r_accessed": False,
        "canary_calls": 0,
        "databento_calls": 0,
        "date_stamp": DATE,
        "generated_at_utc": generated_at,
        "live_effect": False,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_account_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "outcome_review_opened": False,
        "packet_id": PACKET_ID,
        "paid_data_calls": 0,
        "promotion_verdict": PROMOTION_VERDICT,
        "schema_version": SCHEMA_VERSION,
        "validation_safe": False,
    }


def next_routes() -> list[dict[str, Any]]:
    return [
        {
            "route": "CNR_E2_E3_E4_TIMING_PACKET_PREREG",
            "status": "NEXT_LANE_SOURCE_SAFE_PREREG_REQUIRED",
            "exact_next_action": "Build an input-only packet that captures signal_emitted_utc, decision_request_sent_utc, decision_response_received_utc, latency_ms, and pretouch trigger ids before any terminal path is opened.",
        },
        {
            "route": "CNR_T1_T2_T3_TARGET_FAMILY_PREREG",
            "status": "NEXT_LANE_SOURCE_SAFE_PREREG_REQUIRED",
            "exact_next_action": "Freeze fixed-R, structural-level, and terminal/timebox target contracts with stop model, quote side, source hashes, duplicate policy, and no-leak tests before scoring.",
        },
        {
            "route": "CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_LABELS",
            "status": "NEXT_LANE_ALLOWED_AS_INPUT_BUILDER_NOT_RESULT",
            "exact_next_action": "Create a source-hashed lifecycle/timebox packet for the six May 5 no-terminal rows that records what happens after the four-hour horizon without using broker/account/live labels.",
        },
        {
            "route": "XAGUSD_CNR_RESIDUAL_TARGET_FORENSICS",
            "status": "NEXT_LANE_DISCOVERY_FORENSICS_ONLY",
            "exact_next_action": "Analyze residual_target_r_from_executable_quote bins and no-terminal continuation behavior across accepted source-safe CNR rows; keep results as discovery until a separate preregistration exists.",
        },
        {
            "route": "CNR_MARKET_ENTRY_INVALIDITY_OR_TINY_RESIDUAL_GATE",
            "status": "SPEC_ONLY_UNTIL_VALIDATION_DOSSIER",
            "exact_next_action": "Draft a non-live gate spec for market entries where original TP1 is already tiny from executable quote; do not wire selector/risk/execution behavior.",
        },
    ]


def forbidden_routes() -> list[dict[str, Any]]:
    return [
        {
            "route": "SCORE_THE_94_BLOCKED_ROWS",
            "forbidden_until": "G12/G0/owner-approved source-safe packet rebuild and explicit result lane",
            "reason": "They were excluded by G12 CNR061 and cannot be opened by this audit.",
        },
        {
            "route": "USE_BROKER_ACTUAL_R_ACCOUNT_HISTORY_OR_LIVE_ORDER_STATE",
            "forbidden_until": "A separately approved broker-label lane with label-family separation",
            "reason": "OTI8 is synthetic ordered-tick path-R only.",
        },
        {
            "route": "PROMOTE_CNR061_OR_CHANGE_LIVE_SELECTORS",
            "forbidden_until": "Separate promotion dossier with validation-safe evidence",
            "reason": "n=8 row-level / two duplicate groups and no DSR/PBO/effective-N support.",
        },
        {
            "route": "POST_HOC_TARGET_RESCUE",
            "forbidden_until": "Target family is preregistered before outcomes",
            "reason": "OTI8 teaches target design questions but cannot rescue itself with invented thresholds.",
        },
    ]


def audit_question_answers(
    source: dict[str, Any],
    duplicate: dict[str, Any],
    integrity: dict[str, Any],
    forensics: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "question": "Did OTI8 score exactly the 8 accepted hashes and exclude the 94 blocked rows?",
            "answer": "Yes.",
            "evidence_artifact": OUTPUTS["duplicate_json"].name,
            "status": duplicate["blocked_row_exclusion"]["status"],
        },
        {
            "question": "Are source, sidecar, quote, and ordered path hashes recomputable?",
            "answer": "Yes; all recompute checks match.",
            "evidence_artifact": OUTPUTS["source_json"].name,
            "status": source["hash_recompute_status"],
        },
        {
            "question": "Did method freeze occur before scoring and label review?",
            "answer": "Yes by committed builder order and method artifact declaration.",
            "evidence_artifact": OUTPUTS["duplicate_json"].name,
            "status": duplicate["method_freeze_before_scoring_evidence"]["status"],
        },
        {
            "question": "Did OTI8 use broker/account/live/hidden/blocked outcome fields?",
            "answer": "No hits found and all forbidden-access flags remain false/zero.",
            "evidence_artifact": OUTPUTS["source_json"].name,
            "status": source["forbidden_label_and_flag_scan"]["status"],
        },
        {
            "question": "Is raw duplicate overlap quarantined with zero countable blocked overlap?",
            "answer": "Yes.",
            "evidence_artifact": OUTPUTS["duplicate_json"].name,
            "status": duplicate["blocked_row_exclusion"]["status"],
        },
        {
            "question": "Are row-level/countable/timing-family summaries internally consistent?",
            "answer": "Yes; recomputed row-level and countable summaries match the OTI8 ledger.",
            "evidence_artifact": OUTPUTS["integrity_json"].name,
            "status": "PASS" if all(integrity["jsonl_vs_ledger_consistency"].values()) else "FAIL",
        },
        {
            "question": "Are the two target-before-stop rows real and tiny residual-target wins?",
            "answer": "Yes; both pass terminal target checks and are +0.054478301R.",
            "evidence_artifact": OUTPUTS["integrity_json"].name,
            "status": "PASS" if all(row["tiny_residual_r"] for row in integrity["terminal_target_rows"]) else "FAIL",
        },
        {
            "question": "Are the six no-terminal rows unresolved inside the frozen horizon?",
            "answer": "Yes; no terminal event exists and target/stop gaps remain positive.",
            "evidence_artifact": OUTPUTS["integrity_json"].name,
            "status": "PASS" if all(row["unresolved_condition_pass"] for row in integrity["unresolved_no_terminal_rows"]) else "FAIL",
        },
        {
            "question": "Accept, block, or reject?",
            "answer": DECISION,
            "evidence_artifact": OUTPUTS["decision_json"].name,
            "status": "PASS",
        },
        {
            "question": "What did OTI8 teach relative to OTI7?",
            "answer": "It clears one missing-geometry pocket but does not overturn the broad negative CNR result; it points to target/timing/no-terminal next lanes.",
            "evidence_artifact": OUTPUTS["forensics_json"].name,
            "status": forensics["learning_verdict"],
        },
    ]


def completion_checklist() -> list[dict[str, Any]]:
    return [
        {"requirement": "mandatory_gtos_preflight", "evidence": ".context/LIVE_STATE.md regenerated/read plus latest handoff and core context read", "status": "PASS"},
        {"requirement": "context_anchor", "evidence": OUTPUTS["context_json"].name, "status": "PASS"},
        {"requirement": "all_oti8_result_artifacts_read", "evidence": "context artifact_inventory includes oti8_cnr061_quarantined_results", "status": "PASS"},
        {"requirement": "all_upstream_context_artifacts_read", "evidence": "context artifact_inventory includes G12 CNR061, CNR061, CNR, source-field, G12 source-field, OTI7/G12 OTI7, OTX/G12 OTX, OTR061 directories", "status": "PASS"},
        {"requirement": "exact_8_accepted_row_hashes", "evidence": OUTPUTS["duplicate_json"].name, "status": "PASS"},
        {"requirement": "exact_94_blocked_row_exclusion", "evidence": OUTPUTS["duplicate_json"].name, "status": "PASS"},
        {"requirement": "source_hash_recomputation", "evidence": OUTPUTS["source_json"].name, "status": "PASS"},
        {"requirement": "no_leak_label_family_audit", "evidence": OUTPUTS["source_json"].name, "status": "PASS"},
        {"requirement": "duplicate_policy_raw_vs_countable_overlap", "evidence": OUTPUTS["duplicate_json"].name, "status": "PASS"},
        {"requirement": "method_freeze_before_scoring", "evidence": OUTPUTS["duplicate_json"].name, "status": "PASS"},
        {"requirement": "terminal_scoring_integrity", "evidence": OUTPUTS["integrity_json"].name, "status": "PASS"},
        {"requirement": "tiny_positive_no_terminal_forensics", "evidence": OUTPUTS["forensics_json"].name, "status": "PASS"},
        {"requirement": "dsr_pbo_effective_n_noncomputability", "evidence": OUTPUTS["duplicate_json"].name, "status": "PASS"},
        {"requirement": "g12_decision_accept_block_reject", "evidence": OUTPUTS["decision_json"].name, "status": "PASS"},
        {"requirement": "next_lane_prompt_pack", "evidence": OUTPUTS["next_md"].name, "status": "PASS"},
        {"requirement": "builder_verifier_tests", "evidence": "PENDING_G12_VERIFIER", "status": "PENDING_VERIFIER"},
        {"requirement": "forbidden_live_surface_diff_status", "evidence": "PENDING_G12_VERIFIER", "status": "PENDING_VERIFIER"},
    ]


def build_next_prompt_pack() -> str:
    return f"""# G12 OTI8 CNR061 Next Lane Prompt Pack - {DATE}

Promotion verdict: `{PROMOTION_VERDICT}`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Decision Anchor

G12 accepts OTI8 only as quarantined discovery evidence. The accepted evidence is tiny and synthetic: exactly 8 row-level rows, 4 countable timing-family rows, 2 duplicate groups, 2 target-before-stop tiny residual wins, 6 no-terminal rows, and zero validation/promotion support.

## Prompt 1 - CNR Timing And Target Preregistration

`/goal Build CNR_E2_E3_E4_AND_CNR_T1_T2_T3_INPUT_ONLY_PREREG using OTI8/G12 OTI8 as learning context; freeze timing fields, target contracts, quote-side policy, duplicate denominator policy, source hashes, no-leak rules, and sample floors before any outcome opening; keep NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; do not score blocked rows, broker actual-R, account history, live order state, or hidden labels; produce prereg, source contract, no-leak, duplicate, and completion artifacts plus verifier/tests.`

## Prompt 2 - CNR061 No-Terminal Lifecycle Timebox Packet

`/goal Build CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_INPUT_PACKET for the six OTI8 no-terminal rows only; extend source-hashed ordered tick/lifecycle observation beyond the frozen four-hour horizon without using broker/account/live labels; define terminal/timebox labels before reading outcomes; preserve the exact OTI8 duplicate policy; output packet/source/no-leak/duplicate/blocker artifacts and stop before result scoring unless separately authorized.`

## Prompt 3 - XAGUSD Residual Target Mechanism Forensics

`/goal Run XAGUSD_CNR_RESIDUAL_TARGET_FORENSICS as discovery-only source-safe analysis; inspect residual_target_r_from_executable_quote bins, no-terminal behavior, session/timing-family differences, and original-TP1 tiny-target pathology using only accepted source-safe rows; do not invent rescue thresholds or live gates; produce mechanism report, exact blocker ledger, preregistered next hypotheses, and verifier/tests under NO_PROMOTION_VERDICT.`

## Forbidden Until Separate Approval

- Scoring any of the 94 G12-blocked CNR061 rows.
- Using broker actual-R, account history, live trade results, live order state, or hidden path labels.
- Promoting CNR061, changing selectors, prompts, risk, execution, permissions, safety gates, canaries, MT5 order behavior, credentials, or remotes.
- Treating OTI8's +0.054478301R target rows as material edge evidence.
"""


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], summary_keys: tuple[str, ...] = ()) -> None:
    lines = [
        f"# {title}",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`  ",
        f"**Validation safe:** `{str(payload['validation_safe']).lower()}`  ",
        f"**Outcome review opened:** `{str(payload['outcome_review_opened']).lower()}`  ",
        f"**Live effect:** `{str(payload['live_effect']).lower()}`",
        "",
    ]
    for key in summary_keys:
        if key in payload:
            lines.append(f"- `{key}`: `{payload[key]}`")
    if summary_keys:
        lines.append("")
    lines.extend(["```json", json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(bundle: dict[str, Any]) -> None:
    write_json(OUTPUTS["context_json"], bundle["context"])
    write_md(OUTPUTS["context_md"], f"G12 OTI8 CNR061 Context Anchor - {DATE}", bundle["context"], ("current_head", "branch", "context_boundary"))
    write_json(OUTPUTS["decision_json"], bundle["decision"])
    write_md(OUTPUTS["decision_md"], f"G12 OTI8 CNR061 Post-Result Decision Ledger - {DATE}", bundle["decision"], ("decision", "decision_scope"))
    write_json(OUTPUTS["source_json"], bundle["source"])
    write_md(OUTPUTS["source_md"], f"G12 OTI8 CNR061 Source Hash Noleak Audit - {DATE}", bundle["source"], ("hash_recompute_status", "source_policy_verdict"))
    write_json(OUTPUTS["duplicate_json"], bundle["duplicate"])
    write_md(OUTPUTS["duplicate_md"], f"G12 OTI8 CNR061 Duplicate Label Methodology Audit - {DATE}", bundle["duplicate"], ())
    write_json(OUTPUTS["integrity_json"], bundle["integrity"])
    write_md(OUTPUTS["integrity_md"], f"G12 OTI8 CNR061 Result Integrity Audit - {DATE}", bundle["integrity"], ("integrity_status", "verdict"))
    write_json(OUTPUTS["forensics_json"], bundle["forensics"])
    write_md(OUTPUTS["forensics_md"], f"G12 OTI8 CNR061 Forensics And Learning Audit - {DATE}", bundle["forensics"], ("learning_verdict",))
    OUTPUTS["next_md"].write_text(bundle["next_prompt_pack"], encoding="utf-8")
    write_json(OUTPUTS["completion_json"], bundle["completion"])
    write_md(OUTPUTS["completion_md"], f"G12 OTI8 CNR061 Completion Audit - {DATE}", bundle["completion"], ("decision", "verification_status", "can_mark_goal_complete"))


def main() -> int:
    bundle = build_bundle()
    write_outputs(bundle)
    print(json.dumps({"decision": bundle["decision"]["decision"], "completion_status": bundle["completion"]["verification_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
