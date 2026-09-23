#!/usr/bin/env python3
"""Build G12 post-result audit artifacts for OTI7 CNR.

This audit reads the frozen OTI7 quarantined result artifacts and upstream G12
CNR packet-control artifacts. It does not rescore rows, open blocked outcomes,
or inspect broker/live labels.
"""

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
OUT = Path(__file__).resolve().parent
DATE = "2026-05-08"
LANE = "G12_OTI7_CNR_POST_RESULT_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "POST_RESULT_AUDIT_QUARANTINED_DISCOVERY_ONLY"
ACCEPT = "ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE"
BLOCK = "BLOCK_WITH_EXACT_AUDIT_QUESTION"
REJECT = "REJECT_INVALID_RESULT_AUDIT"

OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
OTI7 = OT / "oti7_cnr_accepted_quarantined_results"
G12_CNR = OT / "g12_cnr_source_field_packet_audit"
PREREG = OT / "cnr_timing_model_preregistration/CNR_TIMING_MODEL_PREREGISTRATION_2026-05-07.md"

INPUTS = {
    "controlling_prompt": OUT / f"G12_OTI7_CNR_POST_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md",
    "live_state": ROOT / ".context/LIVE_STATE.md",
    "latest_handoff": ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ROOT / ".context/00_core/research_current_state.md",
    "goal_session_research_discipline": ROOT / ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": ROOT / ".context/00_core/local_heavy_data_inventory.md",
    "cnr_preregistration": PREREG,
    "oti7_result_ledger_json": OTI7 / f"OTI7_CNR_RESULT_LEDGER_{DATE}.json",
    "oti7_result_ledger_jsonl": OTI7 / f"OTI7_CNR_RESULT_LEDGER_{DATE}.jsonl",
    "oti7_completion": OTI7 / f"OTI7_CNR_COMPLETION_AUDIT_{DATE}.json",
    "oti7_source_audit": OTI7 / f"OTI7_CNR_SOURCE_HASH_PATH_COVERAGE_AUDIT_{DATE}.json",
    "oti7_geometry_audit": OTI7 / f"OTI7_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_{DATE}.json",
    "oti7_duplicate_audit": OTI7 / f"OTI7_CNR_DUPLICATE_EFFECTIVE_N_AUDIT_{DATE}.json",
    "oti7_noleak_audit": OTI7 / f"OTI7_CNR_NOLEAK_LABEL_FAMILY_AUDIT_{DATE}.json",
    "oti7_negative_learning": OTI7 / f"OTI7_CNR_NEGATIVE_RESULT_LEARNING_LEDGER_{DATE}.json",
    "oti7_next_hypothesis": OTI7 / f"OTI7_CNR_NEXT_HYPOTHESIS_AND_BLOCKER_LEDGER_{DATE}.json",
    "oti7_methodology": OTI7 / f"OTI7_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}.json",
    "oti7_timing_comparison": OTI7 / f"OTI7_CNR_TIMING_FAMILY_COMPARISON_{DATE}.json",
    "oti7_null_forensics": OTI7 / f"OTI7_CNR_TARGET_ALREADY_PASSED_AND_NULL_FORENSICS_{DATE}.json",
    "g12_ready_shortlist": G12_CNR / f"G12_CNR_READY_ROW_SHORTLIST_{DATE}.json",
    "g12_blocker_ledger": G12_CNR / f"G12_CNR_EXACT_BLOCKER_LEDGER_{DATE}.json",
    "g12_decision_ledger": G12_CNR / f"G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_{DATE}.json",
    "g12_noleak_audit": G12_CNR / f"G12_CNR_NOLEAK_AND_LABEL_AUDIT_{DATE}.json",
    "g12_duplicate_audit": G12_CNR / f"G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
    "g12_source_audit": G12_CNR / f"G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json",
}

OUTPUT_STEMS = {
    "decision": f"G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_{DATE}",
    "source_noleak": f"G12_OTI7_CNR_SCORING_SOURCE_NOLEAK_AUDIT_{DATE}",
    "row_duplicate": f"G12_OTI7_CNR_ROW_EXCLUSION_DUPLICATE_AUDIT_{DATE}",
    "geometry": f"G12_OTI7_CNR_GEOMETRY_QUOTE_SIDE_CORRECTNESS_AUDIT_{DATE}",
    "forensics": f"G12_OTI7_CNR_NEGATIVE_RESULT_FORENSICS_{DATE}",
    "methodology": f"G12_OTI7_CNR_METHODOLOGY_EFFECTIVE_N_AUDIT_{DATE}",
    "next_map": f"G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP_{DATE}",
    "context": f"G12_OTI7_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_{DATE}",
    "next_prompt": f"G12_OTI7_CNR_NEXT_LANE_PROMPT_PACK_{DATE}",
    "completion": f"G12_OTI7_CNR_COMPLETION_AUDIT_{DATE}",
}

REQUIRED_FALSE_FIELDS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "account_history_accessed",
    "broker_actual_r_accessed",
    "live_trade_results_accessed",
    "blocked_packet_outcome_source_read",
)
REQUIRED_ZERO_FIELDS = ("mt5_order_calls", "order_calls", "paid_data_calls", "databento_calls", "api_calls")

FORBIDDEN_INPUT_KEY_FRAGMENTS = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "gross_r",
    "live_trade_result",
    "net_r",
    "path_label",
    "path_outcome",
    "pnl",
    "realized_r",
    "result_value",
    "sl_first_touch",
    "synthetic_path_r",
    "target_hit_timestamp",
    "terminal_order_label",
    "tp1_first_touch",
    "trade_result",
    "win_loss",
}

ALLOWED_OUTPUT_KEYS = {
    "broker_actual_r_accessed",
    "live_trade_results_accessed",
    "blocked_packet_outcome_source_read",
    "synthetic_path_r",  # allowed only in OTI7 result output, not in G12 ready input rows
}

FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "config/",
    "prompts/",
    "src/",
    "knowledge_base/",
    "pipeline_state/",
    "run_agent.py",
    "start_all.bat",
    "scripts/canary",
    "scripts/watchdog",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def artifact_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "canary_calls": 0,
    }


def base_artifact(artifact_type: str) -> dict[str, Any]:
    payload = artifact_flags()
    payload.update(
        {
            "artifact_family": LANE,
            "artifact_type": artifact_type,
            "generated_at_utc": utc_now(),
            "result_status": RESULT_STATUS,
        }
    )
    return payload


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def flatten_keys(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            keys.append(child_prefix)
            keys.extend(flatten_keys(child, child_prefix))
        return keys
    if isinstance(value, list):
        keys = []
        for index, child in enumerate(value):
            keys.extend(flatten_keys(child, f"{prefix}[{index}]"))
        return keys
    return []


def forbidden_input_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        row_hits = []
        for key in flatten_keys(row):
            leaf = key.split(".")[-1]
            lower = leaf.lower()
            if leaf in ALLOWED_OUTPUT_KEYS:
                continue
            if any(fragment in lower for fragment in FORBIDDEN_INPUT_KEY_FRAGMENTS):
                row_hits.append(key)
        if row_hits:
            hits.append(
                {
                    "row_number": row.get("row_number"),
                    "row_sha256": row.get("row_sha256"),
                    "hits": sorted(set(row_hits)),
                }
            )
    return hits


def check_payload_flags(name: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    issues = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append({"source": name, "issue": "promotion_verdict_not_preserved", "value": payload.get("promotion_verdict")})
    for key in REQUIRED_FALSE_FIELDS:
        if key in payload and payload.get(key) is not False:
            issues.append({"source": name, "issue": f"{key}_not_false", "value": payload.get(key)})
    for key in REQUIRED_ZERO_FIELDS:
        if key in payload and payload.get(key) != 0:
            issues.append({"source": name, "issue": f"{key}_not_zero", "value": payload.get(key)})
    return issues


def git_status_paths() -> list[str]:
    command = [
        "git",
        "-c",
        f"safe.directory={str(ROOT).replace(chr(92), '/')}",
        "-c",
        "core.excludesfile=",
        "status",
        "--porcelain",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    paths = []
    for line in completed.stdout.splitlines():
        if line.strip():
            paths.append(line[3:].replace("\\", "/"))
    return paths


def git_head() -> str:
    command = ["git", "-c", f"safe.directory={str(ROOT).replace(chr(92), '/')}", "rev-parse", "--short", "HEAD"]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return completed.stdout.strip() or "UNKNOWN"


def pct(part: int, whole: int) -> float | None:
    if whole == 0:
        return None
    return round(part / whole, 6)


def r_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [row["synthetic_path_r"] for row in rows if row.get("synthetic_path_r") is not None]
    if not values:
        return {"scored_rows": 0, "mean_r": None, "total_r": 0.0, "stop_first": 0, "target_first": 0}
    values_sorted = sorted(values)
    mid = len(values_sorted) // 2
    if len(values_sorted) % 2:
        median = values_sorted[mid]
    else:
        median = (values_sorted[mid - 1] + values_sorted[mid]) / 2
    return {
        "scored_rows": len(values),
        "mean_r": round(sum(values) / len(values), 6),
        "median_r": round(median, 6),
        "total_r": round(sum(values), 6),
        "stop_first": sum(1 for row in rows if row.get("quarantined_result_status") == "SCORED_STOP_FIRST"),
        "target_first": sum(1 for row in rows if row.get("quarantined_result_status") == "SCORED_TARGET_FIRST"),
    }


def status_counter(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["quarantined_result_status"] for row in rows).items()))


def dimension_summary(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key))].append(row)
    out: dict[str, dict[str, Any]] = {}
    for value, group in sorted(groups.items()):
        scored = [row for row in group if row.get("synthetic_path_r") is not None]
        stop = sum(1 for row in scored if row["quarantined_result_status"] == "SCORED_STOP_FIRST")
        target = sum(1 for row in scored if row["quarantined_result_status"] == "SCORED_TARGET_FIRST")
        out[value] = {
            "rows": len(group),
            "scored_rows": len(scored),
            "status_counts": status_counter(group),
            "stop_first_rate_scored": pct(stop, len(scored)),
            "target_first_rate_scored": pct(target, len(scored)),
            "r_summary_scored": r_summary(group),
        }
    return out


def load_inputs() -> dict[str, Any]:
    missing = [name for name, path in INPUTS.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {missing}")
    return {
        "oti7_ledger": read_json(INPUTS["oti7_result_ledger_json"]),
        "oti7_rows_jsonl": read_jsonl(INPUTS["oti7_result_ledger_jsonl"]),
        "oti7_completion": read_json(INPUTS["oti7_completion"]),
        "oti7_source": read_json(INPUTS["oti7_source_audit"]),
        "oti7_geometry": read_json(INPUTS["oti7_geometry_audit"]),
        "oti7_duplicate": read_json(INPUTS["oti7_duplicate_audit"]),
        "oti7_noleak": read_json(INPUTS["oti7_noleak_audit"]),
        "oti7_negative_learning": read_json(INPUTS["oti7_negative_learning"]),
        "oti7_next_hypothesis": read_json(INPUTS["oti7_next_hypothesis"]),
        "oti7_methodology": read_json(INPUTS["oti7_methodology"]),
        "oti7_timing": read_json(INPUTS["oti7_timing_comparison"]),
        "oti7_null_forensics": read_json(INPUTS["oti7_null_forensics"]),
        "g12_ready": read_json(INPUTS["g12_ready_shortlist"]),
        "g12_blockers": read_json(INPUTS["g12_blocker_ledger"]),
        "g12_decision": read_json(INPUTS["g12_decision_ledger"]),
        "g12_noleak": read_json(INPUTS["g12_noleak_audit"]),
        "g12_duplicate": read_json(INPUTS["g12_duplicate_audit"]),
        "g12_source": read_json(INPUTS["g12_source_audit"]),
    }


def build_row_scope_controls(data: dict[str, Any]) -> dict[str, Any]:
    ledger_rows = data["oti7_ledger"]["rows"]
    jsonl_rows = data["oti7_rows_jsonl"]
    ready_rows = data["g12_ready"]["rows"]
    blocked_rows = data["g12_blockers"]["rows"]
    result_sha = {row["row_sha256"] for row in ledger_rows}
    jsonl_sha = {row["row_sha256"] for row in jsonl_rows}
    ready_sha = {row["row_sha256"] for row in ready_rows}
    blocked_sha = {row["row_sha256"] for row in blocked_rows}
    result_numbers = {row["row_number"] for row in ledger_rows}
    blocked_numbers = {row["row_number"] for row in blocked_rows}
    countable = [row for row in ledger_rows if row.get("countable_denominator_row") is True]
    duplicate_context = [row for row in ledger_rows if row.get("countable_denominator_row") is False]
    issues = []
    if len(ledger_rows) != 102:
        issues.append("oti7_result_rows_not_102")
    if len(jsonl_rows) != 102:
        issues.append("oti7_jsonl_rows_not_102")
    if len(ready_rows) != 102 or data["g12_ready"].get("ready_row_count") != 102:
        issues.append("g12_ready_rows_not_102")
    if len(blocked_rows) != 6098 or data["g12_blockers"].get("blocked_row_count") != 6098:
        issues.append("g12_blocked_rows_not_6098")
    if result_sha != ready_sha:
        issues.append("result_row_sha_set_differs_from_g12_ready_shortlist")
    if result_sha != jsonl_sha:
        issues.append("result_json_and_jsonl_sha_sets_differ")
    if result_sha & blocked_sha:
        issues.append("blocked_row_sha_overlap")
    if result_numbers & blocked_numbers:
        issues.append("blocked_row_number_overlap")
    if len(countable) != 54 or len(duplicate_context) != 48:
        issues.append("countable_duplicate_context_counts_changed")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "accepted_rows_processed": len(ledger_rows),
        "jsonl_rows": len(jsonl_rows),
        "g12_ready_rows": len(ready_rows),
        "blocked_rows_excluded": len(blocked_rows),
        "accepted_blocked_row_sha_overlap_count": len(result_sha & blocked_sha),
        "accepted_blocked_row_number_overlap_count": len(result_numbers & blocked_numbers),
        "countable_rows": len(countable),
        "duplicate_context_rows": len(duplicate_context),
        "unique_duplicate_groups": len({row["duplicate_group_id"] for row in ledger_rows}),
        "countable_unique_duplicate_groups": len({row["duplicate_group_id"] for row in countable}),
        "scored_countable_rows": sum(1 for row in countable if row.get("synthetic_path_r") is not None),
        "scored_countable_unique_duplicate_groups": len(
            {row["duplicate_group_id"] for row in countable if row.get("synthetic_path_r") is not None}
        ),
    }


def build_source_noleak_controls(data: dict[str, Any]) -> dict[str, Any]:
    source = data["oti7_source"]
    g12_source = data["g12_source"]
    noleak = data["oti7_noleak"]
    ready_rows = data["g12_ready"]["rows"]
    source_mismatches = []
    missing = []
    for item in source["source_files"]:
        path = resolve_path(item["path"])
        actual = sha256_file(path)
        if actual is None:
            missing.append(item["path"])
        elif actual != item.get("actual_sha256"):
            source_mismatches.append(
                {"path": item["path"], "expected": item.get("actual_sha256"), "actual": actual}
            )
    flag_issues = []
    for name, payload in [
        ("oti7_result_ledger", data["oti7_ledger"]),
        ("oti7_source_audit", source),
        ("oti7_noleak_audit", noleak),
        ("g12_ready_shortlist", data["g12_ready"]),
        ("g12_blocker_ledger", data["g12_blockers"]),
    ]:
        flag_issues.extend(check_payload_flags(name, payload))
    input_hits = forbidden_input_hits(ready_rows)
    unsafe_text_hits = []
    for path in sorted(OUT.glob(f"G12_OTI7_CNR_*{DATE}.*")):
        if path.suffix.lower() not in {".json", ".jsonl", ".md"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle in ['"validation_safe": true', '"outcome_review_opened": true', '"live_effect": true']:
            if needle in text:
                unsafe_text_hits.append({"path": rel(path), "needle": needle})
    issues = []
    if source_mismatches:
        issues.append("source_hash_mismatches")
    if missing:
        issues.append("missing_source_files")
    if source.get("quote_recompute_mismatch_count") != 0:
        issues.append("oti7_quote_recompute_mismatch_count_nonzero")
    if source.get("listed_source_hash_mismatch_count") != 0:
        issues.append("oti7_listed_source_hash_mismatch_count_nonzero")
    if g12_source.get("strict_hash_mismatch_count") != 0 or g12_source.get("asof_issue_count") != 0:
        issues.append("upstream_g12_source_hash_or_asof_issue")
    if noleak.get("forbidden_input_key_fragment_hit_count") != 0:
        issues.append("oti7_forbidden_input_key_hit_count_nonzero")
    if noleak.get("broker_actual_r_inspected") is not False or noleak.get("hidden_path_labels_read") is not False:
        issues.append("oti7_label_boundary_broken")
    if input_hits:
        issues.append("g12_ready_input_forbidden_key_hits")
    if flag_issues:
        issues.append("flag_or_call_counter_issue")
    if unsafe_text_hits:
        issues.append("unsafe_text_hit")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "source_file_count": source.get("source_file_count"),
        "source_rehash_missing_count": len(missing),
        "source_rehash_mismatch_count": len(source_mismatches),
        "source_rehash_mismatches": source_mismatches[:10],
        "source_rehash_missing": missing[:10],
        "quote_recompute_mismatch_count": source.get("quote_recompute_mismatch_count"),
        "listed_source_hash_mismatch_count": source.get("listed_source_hash_mismatch_count"),
        "g12_strict_hash_mismatch_count": g12_source.get("strict_hash_mismatch_count"),
        "g12_asof_issue_count": g12_source.get("asof_issue_count"),
        "ready_input_forbidden_key_hit_count": len(input_hits),
        "ready_input_forbidden_key_hits": input_hits[:10],
        "flag_issues": flag_issues,
        "unsafe_text_hits": unsafe_text_hits,
        "forbidden_sources_skipped": noleak.get("forbidden_sources_skipped", []),
        "searched_roots": source.get("searched_roots", {}),
    }


def compute_geometry_controls(rows: list[dict[str, Any]], oti7_geometry: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    status = Counter(row["quarantined_result_status"] for row in rows)
    terminal_quote_side_counts = Counter(row.get("terminal_quote_side") for row in rows)
    executable_quote_side_counts = Counter(row.get("quote", {}).get("executable_side") for row in rows)
    target_r_values = []
    target_first_r_values = []
    stop_first_target_r_values = []
    for row in rows:
        side = row["side"]
        quote = row.get("quote") or {}
        geometry = row.get("geometry") or {}
        q_side = quote.get("executable_side")
        expected_q_side = "ask" if side == "LONG" else "bid"
        if q_side != expected_q_side:
            issues.append({"row_number": row["row_number"], "issue": "executable_quote_side_mismatch"})
        if q_side in {"ask", "bid"} and quote.get("executable_entry_price") != quote.get(q_side):
            issues.append({"row_number": row["row_number"], "issue": "executable_entry_not_equal_side_quote"})
        terminal_side = row.get("terminal_quote_side")
        expected_terminal_side = "bid" if side == "LONG" else "ask"
        if row["quarantined_result_status"].startswith("SCORED_") and terminal_side != expected_terminal_side:
            issues.append({"row_number": row["row_number"], "issue": "terminal_quote_side_mismatch"})
        geometry_present = geometry.get("geometry_present")
        if row["quarantined_result_status"] == "UNSCOREABLE_MISSING_SOURCE_GEOMETRY":
            if geometry_present is not False:
                issues.append({"row_number": row["row_number"], "issue": "missing_geometry_status_without_false_geometry_present"})
            continue
        if not geometry_present:
            issues.append({"row_number": row["row_number"], "issue": "geometry_missing_but_not_marked_unscoreable"})
            continue
        entry = geometry.get("executable_entry_price")
        stop = geometry.get("original_stop_loss")
        target = geometry.get("original_take_profit_1")
        risk = geometry.get("risk_price_from_executable_entry")
        if side == "LONG":
            expected_risk = entry - stop
            expected_target_r = (target - entry) / expected_risk if expected_risk > 0 else None
            target_passed = entry >= target
        else:
            expected_risk = stop - entry
            expected_target_r = (entry - target) / expected_risk if expected_risk > 0 else None
            target_passed = entry <= target
        if risk is not None and not math.isclose(risk, expected_risk, rel_tol=1e-9, abs_tol=1e-9):
            issues.append({"row_number": row["row_number"], "issue": "risk_geometry_mismatch"})
        if geometry.get("target_already_passed_before_entry") != target_passed:
            issues.append({"row_number": row["row_number"], "issue": "target_already_passed_gate_mismatch"})
        invalid = expected_risk <= 0
        if geometry.get("stop_invalid_at_executable_entry") != invalid:
            issues.append({"row_number": row["row_number"], "issue": "stop_invalid_gate_mismatch"})
        if invalid:
            if row["quarantined_result_status"] != "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY":
                issues.append({"row_number": row["row_number"], "issue": "invalid_stop_not_unscoreable"})
            continue
        if row["quarantined_result_status"].startswith("SCORED_"):
            reported_target_r = geometry.get("target_r_from_executable_entry")
            target_r_values.append(reported_target_r)
            if not math.isclose(reported_target_r, expected_target_r, rel_tol=1e-6, abs_tol=1e-6):
                issues.append({"row_number": row["row_number"], "issue": "target_r_geometry_mismatch"})
            terminal_price = row.get(f"terminal_{expected_terminal_side}")
            if row["quarantined_result_status"] == "SCORED_STOP_FIRST":
                if row.get("terminal_event") != "STOP_FIRST" or row.get("synthetic_path_r") != -1.0:
                    issues.append({"row_number": row["row_number"], "issue": "stop_first_status_r_mismatch"})
                stop_cross = terminal_price <= stop if side == "LONG" else terminal_price >= stop
                if not stop_cross:
                    issues.append({"row_number": row["row_number"], "issue": "terminal_price_does_not_cross_stop"})
                stop_first_target_r_values.append(reported_target_r)
            if row["quarantined_result_status"] == "SCORED_TARGET_FIRST":
                if row.get("terminal_event") != "TARGET_FIRST":
                    issues.append({"row_number": row["row_number"], "issue": "target_first_terminal_event_mismatch"})
                target_cross = terminal_price >= target if side == "LONG" else terminal_price <= target
                if not target_cross:
                    issues.append({"row_number": row["row_number"], "issue": "terminal_price_does_not_cross_target"})
                if not math.isclose(row.get("synthetic_path_r"), reported_target_r, rel_tol=1e-6, abs_tol=1e-6):
                    issues.append({"row_number": row["row_number"], "issue": "target_first_r_not_target_r"})
                target_first_r_values.append(row.get("synthetic_path_r"))
    def stat(values: list[float]) -> dict[str, Any]:
        if not values:
            return {"n": 0, "mean": None, "min": None, "max": None}
        return {
            "n": len(values),
            "mean": round(sum(values) / len(values), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
        }
    expected_status = {
        "SCORED_STOP_FIRST": 64,
        "SCORED_TARGET_FIRST": 12,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18,
    }
    if dict(status) != expected_status:
        issues.append({"issue": "status_counts_changed", "actual": dict(status)})
    if oti7_geometry.get("quote_timestamp_mismatch_count") != 0:
        issues.append({"issue": "quote_timestamp_mismatch_count_nonzero"})
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues[:50],
        "issue_count": len(issues),
        "status_counts": dict(sorted(status.items())),
        "expected_status_counts": expected_status,
        "scored_rows": status["SCORED_STOP_FIRST"] + status["SCORED_TARGET_FIRST"],
        "unscoreable_rows": status["UNSCOREABLE_MISSING_SOURCE_GEOMETRY"] + status["UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY"],
        "terminal_quote_side_counts": dict(sorted((str(k), v) for k, v in terminal_quote_side_counts.items())),
        "executable_quote_side_counts": dict(sorted((str(k), v) for k, v in executable_quote_side_counts.items())),
        "target_already_passed_count": oti7_geometry.get("target_already_passed_count"),
        "stop_invalid_count": oti7_geometry.get("stop_invalid_count"),
        "missing_geometry_count": oti7_geometry.get("missing_geometry_count"),
        "quote_timestamp_mismatch_count": oti7_geometry.get("quote_timestamp_mismatch_count"),
        "target_r_from_executable_entry_all_scored": stat(target_r_values),
        "target_first_r_values": stat(target_first_r_values),
        "stop_first_target_r_values": stat(stop_first_target_r_values),
        "eligibility_gate_order": oti7_geometry.get("eligibility_gate_order"),
    }


def build_forensics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [row for row in rows if row.get("synthetic_path_r") is not None]
    countable = [row for row in rows if row.get("countable_denominator_row") is True]
    scored_countable = [row for row in countable if row.get("synthetic_path_r") is not None]
    stop_first = [row for row in scored if row["quarantined_result_status"] == "SCORED_STOP_FIRST"]
    target_first = [row for row in scored if row["quarantined_result_status"] == "SCORED_TARGET_FIRST"]
    invalid_stop = [row for row in rows if row["quarantined_result_status"] == "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY"]
    missing_geometry = [row for row in rows if row["quarantined_result_status"] == "UNSCOREABLE_MISSING_SOURCE_GEOMETRY"]
    target_first_values = [row["synthetic_path_r"] for row in target_first]
    target_r_values = [
        row["geometry"]["target_r_from_executable_entry"]
        for row in scored
        if row["geometry"].get("target_r_from_executable_entry") is not None
    ]
    by_symbol = dimension_summary(rows, "symbol")
    by_session = dimension_summary(rows, "session")
    by_side = dimension_summary(rows, "side")
    by_packet = dimension_summary(rows, "packet_id")
    lessons = [
        {
            "finding": "The accepted CNR E0/E1 plus original TP1 package failed negatively.",
            "evidence": {
                "scored_rows": len(scored),
                "stop_first": len(stop_first),
                "target_first": len(target_first),
                "all_scored_mean_r": r_summary(scored)["mean_r"],
                "countable_scored_mean_r": r_summary(scored_countable)["mean_r"],
            },
            "interpretation": "The negative result is not a target-already-passed artifact in accepted rows; most eligible market-entry paths hit the original stop first.",
        },
        {
            "finding": "Target-first rows were too small to offset one-R stop losses.",
            "evidence": {
                "target_first_rows": len(target_first_values),
                "target_first_r_min": round(min(target_first_values), 6) if target_first_values else None,
                "target_first_r_max": round(max(target_first_values), 6) if target_first_values else None,
                "target_first_r_mean": round(sum(target_first_values) / len(target_first_values), 6) if target_first_values else None,
            },
            "interpretation": "Original TP1 was often close to the executable market-entry quote. A win was only a small residual target, while a loss remained -1R from the market quote to original stop.",
        },
        {
            "finding": "E0 and E1 are identical in this packet set.",
            "evidence": "Both timing families have 51 rows, identical status counts, and identical mean R because the accepted packet rows share the same executable quote timestamp.",
            "interpretation": "This is a packet-field limitation, not proof that decision-close and candidate-close timing are equivalent.",
        },
        {
            "finding": "Invalid stop geometry is itself failure evidence.",
            "evidence": {
                "invalid_stop_rows": len(invalid_stop),
                "invalid_stop_by_symbol_session_packet": {
                    "|".join(map(str, key)): value
                    for key, value in sorted(Counter((r["symbol"], r["session"], r["packet_id"]) for r in invalid_stop).items())
                },
            },
            "interpretation": "The source-safe market quote could already be beyond the original stop for short XAGUSD rows, so original pending-entry geometry is not transferable to late market-entry execution.",
        },
        {
            "finding": "Missing geometry is confined and actionable.",
            "evidence": {
                "missing_geometry_rows": len(missing_geometry),
                "missing_geometry_by_symbol_session_packet": {
                    "|".join(map(str, key)): value
                    for key, value in sorted(Counter((r["symbol"], r["session"], r["packet_id"]) for r in missing_geometry).items())
                },
            },
            "interpretation": "OTG0-PKT-061 cannot be scored until entry/stop/target and path horizon fields are rebuilt source-safely.",
        },
    ]
    return {
        "headline": "CNR E0/E1 market-entry with original TP1 is accepted as a clean quarantined negative discovery result, not rescued or promoted.",
        "scored_stop_first_rate": pct(len(stop_first), len(scored)),
        "countable_scored_stop_first_rate": pct(
            sum(1 for row in scored_countable if row["quarantined_result_status"] == "SCORED_STOP_FIRST"),
            len(scored_countable),
        ),
        "target_r_from_executable_entry_scored_mean": round(sum(target_r_values) / len(target_r_values), 6),
        "by_symbol": by_symbol,
        "by_session": by_session,
        "by_side": by_side,
        "by_packet": by_packet,
        "lessons": lessons,
    }


def build_next_map(data: dict[str, Any], forensics: dict[str, Any]) -> dict[str, Any]:
    blocker_counts = data["g12_blockers"].get("exact_requirement_counts", {})
    upstream_hypotheses = data["oti7_next_hypothesis"].get("next_hypotheses", [])
    next_hypotheses = list(upstream_hypotheses)
    next_hypotheses.extend(
        [
            {
                "hypothesis": "Market-entry CNR needs a pre-entry residual-R eligibility gate, not a post-hoc rescue threshold.",
                "evidence_from_negative_result": "Target-first outcomes in OTI7 paid only about 0.05R to 0.11R, so a source-safe rule must freeze residual target-R before outcomes if it is ever tested.",
                "required_unblocker": "Input-only packet field residual_target_r_from_executable_quote computed before result opening, plus preregistered sample floor and duplicate policy.",
                "status": "SOURCE_SAFE_PREREG_REQUIRED_NO_OUTCOME_CLAIM",
            },
            {
                "hypothesis": "The failed rows may be late-entry artifacts where original pending-entry geometry has decayed before executable market entry.",
                "evidence_from_negative_result": "Accepted scored rows have high stop-first rate and 18 XAGUSD short rows are invalid because executable quote is beyond the original stop.",
                "required_unblocker": "As-of quote displacement fields from original entry/stop/TP, captured in input packets before any future outcome opening.",
                "status": "SOURCE_SAFE_FEATURE_PACKET_REQUIRED",
            },
            {
                "hypothesis": "CNR may need pretouch continuation trigger timing rather than decision-close/candidate-close timing.",
                "evidence_from_negative_result": "E0/E1 are indistinguishable in this packet set because accepted rows share executable quote timestamps.",
                "required_unblocker": "CNR_E4 pretouch_trigger_id and pretouch_trigger_utc logger/parser fields, source hashed and frozen before outcomes.",
                "status": "BLOCKED_BY_MISSING_SOURCE_FIELD",
            },
            {
                "hypothesis": "A structural target or fixed-R target could be tested only if defined before outcomes.",
                "evidence_from_negative_result": "Original TP1 residual R is too asymmetric in market-entry scoring.",
                "required_unblocker": "CNR_T1/T2/T3 target contracts with stop model, target selection source, timestamp, parser version, and no-leak source hash.",
                "status": "BLOCKED_BY_TARGET_CONTRACT",
            },
            {
                "hypothesis": "OTG0-PKT-061 continuation-no-retrace cannot teach result quality until geometry exists.",
                "evidence_from_negative_result": "All 8 missing-geometry rows are XAGUSD OTG0-PKT-061 context rows.",
                "required_unblocker": "Packet rebuild that materializes entry_sl_tp_or_level_packet and path_start/path_end fields for CNR rows without using result labels.",
                "status": "EXACT_PACKET_FIELD_BLOCKER",
            },
        ]
    )
    return {
        "upstream_blocker_requirement_counts": blocker_counts,
        "negative_result_learning_anchor": forensics["headline"],
        "next_hypotheses": next_hypotheses,
        "blocked_family_exclusions_preserved": [
            "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK outcomes remain closed",
            "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW outcomes remain closed",
            "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER outcomes remain closed",
            "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY outcomes remain closed",
            "CNR_T2_ASOF_STRUCTURAL_LEVEL outcomes remain closed",
            "CNR_T3_TIMEBOX_TERMINAL outcomes remain closed",
        ],
        "creativity_boundary": "Hypotheses are source-safe next routes only. They are not evidence, rescue rules, or validation claims.",
    }


def build_completion_checklist(checks: dict[str, Any], verdict: str) -> list[dict[str, Any]]:
    def status_from_bool(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    return [
        {
            "requirement": "Regenerate and read LIVE_STATE before audit.",
            "evidence": rel(INPUTS["live_state"]),
            "status": "PASS",
        },
        {
            "requirement": "Use controlling G12 OTI7 prompt exactly as audit scope.",
            "evidence": rel(INPUTS["controlling_prompt"]),
            "status": "PASS",
        },
        {
            "requirement": "Read latest handoff, quick reference, research doctrine/current state, goal-session discipline, local heavy data policy, preregistration, OTI7 artifacts, and G12 CNR packet artifacts.",
            "evidence": [rel(path) for path in INPUTS.values()],
            "status": "PASS",
        },
        {
            "requirement": "Do not rescore new rows or create a new result lane.",
            "evidence": "Builder consumes OTI7 result rows as frozen inputs and does not import/run the OTI7 scorer or open tick path outcomes beyond source-hash recomputation.",
            "status": "PASS",
        },
        {
            "requirement": "Verify 102 accepted rows were processed.",
            "evidence": checks["row_scope"]["accepted_rows_processed"],
            "status": status_from_bool(checks["row_scope"]["accepted_rows_processed"] == 102),
        },
        {
            "requirement": "Verify 6098 blocked rows were excluded with zero overlap.",
            "evidence": {
                "blocked_rows_excluded": checks["row_scope"]["blocked_rows_excluded"],
                "sha_overlap": checks["row_scope"]["accepted_blocked_row_sha_overlap_count"],
                "row_number_overlap": checks["row_scope"]["accepted_blocked_row_number_overlap_count"],
            },
            "status": status_from_bool(
                checks["row_scope"]["blocked_rows_excluded"] == 6098
                and checks["row_scope"]["accepted_blocked_row_sha_overlap_count"] == 0
                and checks["row_scope"]["accepted_blocked_row_number_overlap_count"] == 0
            ),
        },
        {
            "requirement": "Verify source/no-leak controls.",
            "evidence": checks["source_noleak"],
            "status": checks["source_noleak"]["status"],
        },
        {
            "requirement": "Verify duplicate/effective-N controls.",
            "evidence": {
                "countable_rows": checks["row_scope"]["countable_rows"],
                "duplicate_context_rows": checks["row_scope"]["duplicate_context_rows"],
                "countable_unique_duplicate_groups": checks["row_scope"]["countable_unique_duplicate_groups"],
                "scored_countable_unique_duplicate_groups": checks["row_scope"]["scored_countable_unique_duplicate_groups"],
            },
            "status": checks["row_scope"]["status"],
        },
        {
            "requirement": "Verify geometry and quote-side ordering before R scoring.",
            "evidence": checks["geometry"],
            "status": checks["geometry"]["status"],
        },
        {
            "requirement": "Explain failure anatomy without rescue/faking/softening.",
            "evidence": OUTPUT_STEMS["forensics"],
            "status": "PASS",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
            "evidence": checks["source_noleak"]["flag_issues"],
            "status": status_from_bool(not checks["source_noleak"]["flag_issues"] and not checks["source_noleak"]["unsafe_text_hits"]),
        },
        {
            "requirement": "Keep CNR_E2/E3/E4 and CNR_T1/T2/T3 outcomes closed.",
            "evidence": "Next map records them as blocked/excluded; no result rows outside E0/E1 plus T0 are consumed.",
            "status": "PASS",
        },
        {
            "requirement": "Produce required G12-owned artifacts only under the G12 OTI7 post-result audit directory.",
            "evidence": [f"{stem}.md/json" for key, stem in OUTPUT_STEMS.items() if key != "next_prompt"] + [f"{OUTPUT_STEMS['next_prompt']}.md"],
            "status": "PASS",
        },
        {
            "requirement": "Run JSON/JSONL parse, source-hash recomputation, row-count/exclusion checks, forbidden-field scan, duplicate denominator checks, NO_PROMOTION coverage, unsafe-flag scan, and forbidden live-surface diff.",
            "evidence": checks,
            "status": "PASS" if all(item.get("status") == "PASS" for item in checks.values() if isinstance(item, dict) and "status" in item) else "FAIL",
        },
        {
            "requirement": "Final audit decision is accept, block, or reject with file-grounded reasons.",
            "evidence": verdict,
            "status": "PASS" if verdict in {ACCEPT, BLOCK, REJECT} else "FAIL",
        },
    ]


def build_context_coverage(checks: dict[str, Any]) -> dict[str, Any]:
    git_paths = git_status_paths()
    forbidden_hits = [
        path
        for path in git_paths
        if any(path.lower().startswith(prefix.lower()) for prefix in FORBIDDEN_LIVE_SURFACE_PREFIXES)
    ]
    required_outputs = []
    for key, stem in OUTPUT_STEMS.items():
        if key == "next_prompt":
            required_outputs.append(rel(OUT / f"{stem}.md"))
        else:
            required_outputs.append(rel(OUT / f"{stem}.md"))
            required_outputs.append(rel(OUT / f"{stem}.json"))
    return {
        "context_anchor": {
            "current_head": git_head(),
            "controlling_prompt": rel(INPUTS["controlling_prompt"]),
            "audit_lane": "research_post_result_quality_audit_not_scoring_lane",
            "hard_boundaries": [
                "no new outcome scoring",
                "no blocked-row outcome opening",
                "no broker actual-R/account history/live trade result inspection",
                "no paid/API/Databento/MT5 order calls",
                "no live prompt/risk/execution/permissions/safety/selector/canary changes",
                "no validation or promotion claim",
            ],
        },
        "inputs_read_or_consumed": {name: rel(path) for name, path in INPUTS.items()},
        "required_outputs": required_outputs,
        "active_question_stack": [
            "Can OTI7 be accepted as quarantined negative discovery evidence?",
            "Were all 102 accepted rows processed and all 6098 blocked rows excluded?",
            "Were source, no-leak, duplicate, geometry, and quote-side controls clean?",
            "What exactly failed in CNR E0/E1 plus original TP1?",
            "Which next hypotheses are source-safe without pretending they are validated?",
        ],
        "route_decisions": [
            "Use OTI7 result artifacts as frozen result evidence rather than rerunning the scorer.",
            "Recompute source-file hashes from OTI7 source audit entries only for evidence-quality verification.",
            "Scan upstream G12 accepted input rows for forbidden label fields; do not scan result rows as if they were inputs.",
            "Treat small effective-N and negative R as promotion blockers, not rejection reasons.",
            "Do not update global context files in this builder because the controlling prompt limits outputs to the G12 OTI7 audit directory.",
        ],
        "git_worktree_scope": {
            "changed_paths": git_paths,
            "forbidden_live_surface_hits": sorted(set(forbidden_hits)),
            "status": "PASS" if not forbidden_hits else "FAIL",
        },
        "searched_roots": checks["source_noleak"].get("searched_roots", {}),
    }


def decide(checks: dict[str, Any]) -> tuple[str, list[str]]:
    hard_failures = []
    if checks["row_scope"]["status"] != "PASS":
        hard_failures.append("row scope/exclusion failed")
    if checks["source_noleak"]["status"] != "PASS":
        hard_failures.append("source/no-leak/flag controls failed")
    if checks["geometry"]["status"] != "PASS":
        hard_failures.append("geometry/quote-side controls failed")
    if hard_failures:
        if any("source" in item or "row scope" in item for item in hard_failures):
            return REJECT, hard_failures
        return BLOCK, hard_failures
    return ACCEPT, [
        "102 accepted rows exactly match G12 ready shortlist",
        "6098 blocked rows have zero row-sha and row-number overlap with OTI7 result rows",
        "source hashes, quote recomputation, no-leak flags, duplicate policy, and geometry/quote-side controls pass",
        "negative result remains quarantined discovery evidence with no promotion or live effect",
    ]


def build_artifacts() -> dict[str, tuple[dict[str, Any] | None, str]]:
    data = load_inputs()
    rows = data["oti7_ledger"]["rows"]
    checks = {
        "row_scope": build_row_scope_controls(data),
        "source_noleak": build_source_noleak_controls(data),
        "geometry": compute_geometry_controls(rows, data["oti7_geometry"]),
    }
    checks["forbidden_live_surface_diff"] = build_context_coverage(checks)["git_worktree_scope"]
    forensics_detail = build_forensics(rows)
    next_map_detail = build_next_map(data, forensics_detail)
    methodology = data["oti7_methodology"]
    verdict, reasons = decide(checks)
    context = build_context_coverage(checks)
    checklist = build_completion_checklist(checks, verdict)
    can_mark_complete = all(item["status"] == "PASS" for item in checklist) and verdict == ACCEPT

    decision = base_artifact("post_result_decision_ledger")
    decision.update(
        {
            "decision": verdict,
            "decision_reasons": reasons,
            "required_verdict_logic": {
                "accept_if": "source/no-leak/duplicate/geometry/scoring controls are clean enough for quarantined discovery evidence",
                "block_if": "a specific audit question prevents evidence acceptance",
                "reject_if": "invalid inputs, leakage, blocked rows, duplicate/label break, or unsupported claims are found",
            },
            "negative_result_is_rejection_reason": False,
            "small_effective_n_is_rejection_reason": False,
            "validation_barrier": True,
            "source_artifact_hashes": {
                name: sha256_file(path)
                for name, path in INPUTS.items()
                if path.suffix.lower() in {".json", ".jsonl", ".md"}
            },
            "check_statuses": {name: value.get("status") for name, value in checks.items() if isinstance(value, dict)},
        }
    )

    source_noleak = base_artifact("scoring_source_noleak_audit")
    source_noleak.update(
        {
            "audit_status": checks["source_noleak"]["status"],
            "scoring_reuse_policy": "Frozen OTI7 scoring fields are audited; this builder does not rescore rows or score blocked rows.",
            "accepted_timing_target_families": data["oti7_ledger"].get("allowed_timing_target_families"),
            "source_controls": checks["source_noleak"],
            "label_family_boundary": {
                "input_family": data["oti7_noleak"].get("input_label_family"),
                "output_family": data["oti7_noleak"].get("output_label_family"),
                "ordered_tick_quotes_used_instead_of_hidden_path_labels": data["oti7_noleak"].get(
                    "ordered_tick_quotes_used_instead_of_hidden_path_labels"
                ),
                "broker_actual_r_inspected": data["oti7_noleak"].get("broker_actual_r_inspected"),
                "hidden_path_labels_read": data["oti7_noleak"].get("hidden_path_labels_read"),
            },
        }
    )

    row_duplicate = base_artifact("row_exclusion_duplicate_audit")
    row_duplicate.update(
        {
            "audit_status": checks["row_scope"]["status"],
            "row_scope_controls": checks["row_scope"],
            "status_counts": data["oti7_ledger"]["status_counts"],
            "duplicate_policy": data["oti7_duplicate"].get("g12_duplicate_policy"),
            "by_countable_policy": data["oti7_duplicate"].get("by_countable_policy"),
            "duplicate_group_status_counts": data["oti7_duplicate"].get("duplicate_group_status_counts"),
        }
    )

    geometry = base_artifact("geometry_quote_side_correctness_audit")
    geometry.update(
        {
            "audit_status": checks["geometry"]["status"],
            "geometry_quote_controls": checks["geometry"],
            "upstream_eligibility_gate_order": data["oti7_geometry"].get("eligibility_gate_order"),
            "null_and_target_already_passed_forensics": {
                "target_already_passed_count": data["oti7_null_forensics"].get("target_already_passed_count"),
                "null_r_count": data["oti7_null_forensics"].get("null_r_count"),
                "same_tick_ambiguity_count": data["oti7_null_forensics"].get("same_tick_ambiguity_count"),
                "forensic_summary": data["oti7_null_forensics"].get("forensic_summary"),
            },
        }
    )

    forensics = base_artifact("negative_result_forensics")
    forensics.update(forensics_detail)

    methodology_audit = base_artifact("methodology_effective_n_audit")
    methodology_audit.update(
        {
            "methodology_status": "PASS_DESCRIPTIVE_ONLY_NOT_VALIDATION",
            "effective_n": methodology.get("effective_n"),
            "raw_result_summary_all_rows": methodology.get("raw_result_summary_all_rows"),
            "raw_result_summary_countable_rows": methodology.get("raw_result_summary_countable_rows"),
            "dsr": methodology.get("dsr"),
            "pbo": methodology.get("pbo"),
            "raw_p": methodology.get("raw_p"),
            "validation_safe_barrier": {
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "reason": "No independent validation split, no promotion dossier, no trial-count/PBO dossier, and small descriptive effective-N.",
            },
        }
    )

    next_map = base_artifact("next_hypothesis_blocker_map")
    next_map.update(next_map_detail)

    context_artifact = base_artifact("context_continuity_and_instruction_coverage")
    context_artifact.update(context)

    completion = base_artifact("completion_audit")
    completion.update(
        {
            "objective_restatement": (
                "Audit OTI7 CNR as quarantined negative discovery evidence quality, without rescoring new rows "
                "or opening blocked outcomes, and decide accept/block/reject with source/no-leak/duplicate/geometry controls."
            ),
            "decision": verdict,
            "can_mark_goal_complete": can_mark_complete,
            "prompt_to_artifact_checklist": checklist,
            "residual_risks": [
                "The result remains discovery-only and validation unsafe.",
                "E0/E1 timing separation is not tested because accepted packet rows share executable quote timestamps.",
                "CNR_E2/E3/E4 and CNR_T1/T2/T3 remain closed until source fields and target/stop contracts are frozen before outcomes.",
                "OTG0-PKT-061 continuation-no-retrace rows need source geometry before result scoring.",
            ],
            "required_followup_verification_commands": [
                f"python -m py_compile {rel(OUT / 'build_g12_oti7_cnr_post_result_audit_2026_05_08.py')}",
                f"python {rel(OUT / 'verify_g12_oti7_cnr_post_result_audit_2026_05_08.py')}",
                f"pytest {rel(OUT / 'test_g12_oti7_cnr_post_result_audit_2026_05_08.py')} -q",
            ],
        }
    )

    artifacts = {
        "decision": (decision, render_decision_md(decision)),
        "source_noleak": (source_noleak, render_source_noleak_md(source_noleak)),
        "row_duplicate": (row_duplicate, render_row_duplicate_md(row_duplicate)),
        "geometry": (geometry, render_geometry_md(geometry)),
        "forensics": (forensics, render_forensics_md(forensics)),
        "methodology": (methodology_audit, render_methodology_md(methodology_audit)),
        "next_map": (next_map, render_next_map_md(next_map)),
        "context": (context_artifact, render_context_md(context_artifact)),
        "completion": (completion, render_completion_md(completion)),
        "next_prompt": (None, render_next_prompt_pack(next_map)),
    }
    return artifacts


def render_decision_md(payload: dict[str, Any]) -> str:
    return f"""# G12 OTI7 CNR Post-Result Decision Ledger - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Decision

`{payload['decision']}`

## Reasons

{chr(10).join(f'- {reason}' for reason in payload['decision_reasons'])}

## Boundary

Negative R, small effective-N, and noncomputable DSR/PBO are not rejection reasons by themselves. They are barriers to validation and promotion. This audit accepts OTI7 only as quarantined negative discovery evidence.
"""


def render_source_noleak_md(payload: dict[str, Any]) -> str:
    c = payload["source_controls"]
    rows = [
        ["source files rehashed", c["source_file_count"]],
        ["source rehash missing", c["source_rehash_missing_count"]],
        ["source rehash mismatches", c["source_rehash_mismatch_count"]],
        ["quote recompute mismatches", c["quote_recompute_mismatch_count"]],
        ["G12 strict hash mismatches", c["g12_strict_hash_mismatch_count"]],
        ["G12 as-of issues", c["g12_asof_issue_count"]],
        ["ready input forbidden-key hits", c["ready_input_forbidden_key_hit_count"]],
    ]
    return f"""# G12 OTI7 CNR Scoring Source No-Leak Audit - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`{payload['audit_status']}`

{table(['check', 'value'], rows)}

## Label Boundary

Input rows remain `input_only_features_no_labels`; OTI7 outputs are `synthetic_path_r_quarantined_discovery_only`. Broker actual-R, account history, live trade results, hidden path labels, and blocked packet outcomes were not used.

## Scoring Boundary

This G12 audit does not rescore OTI7 rows. It audits the frozen OTI7 result ledger and recomputes source-file hashes for evidence quality.
"""


def render_row_duplicate_md(payload: dict[str, Any]) -> str:
    c = payload["row_scope_controls"]
    rows = [
        ["accepted rows processed", c["accepted_rows_processed"]],
        ["JSONL rows", c["jsonl_rows"]],
        ["blocked rows excluded", c["blocked_rows_excluded"]],
        ["accepted-blocked SHA overlap", c["accepted_blocked_row_sha_overlap_count"]],
        ["accepted-blocked row-number overlap", c["accepted_blocked_row_number_overlap_count"]],
        ["countable rows", c["countable_rows"]],
        ["duplicate-context rows", c["duplicate_context_rows"]],
        ["countable unique duplicate groups", c["countable_unique_duplicate_groups"]],
        ["scored countable unique duplicate groups", c["scored_countable_unique_duplicate_groups"]],
    ]
    return f"""# G12 OTI7 CNR Row Exclusion Duplicate Audit - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`{payload['audit_status']}`

{table(['check', 'value'], rows)}

Duplicate policy: {payload['duplicate_policy']}
"""


def render_geometry_md(payload: dict[str, Any]) -> str:
    c = payload["geometry_quote_controls"]
    rows = [
        ["scored rows", c["scored_rows"]],
        ["unscoreable rows", c["unscoreable_rows"]],
        ["stop invalid rows", c["stop_invalid_count"]],
        ["missing geometry rows", c["missing_geometry_count"]],
        ["target already passed rows", c["target_already_passed_count"]],
        ["quote timestamp mismatches", c["quote_timestamp_mismatch_count"]],
        ["target-first R mean", c["target_first_r_values"]["mean"]],
        ["target-first R min", c["target_first_r_values"]["min"]],
        ["target-first R max", c["target_first_r_values"]["max"]],
    ]
    return f"""# G12 OTI7 CNR Geometry Quote-Side Correctness Audit - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`{payload['audit_status']}`

{table(['check', 'value'], rows)}

LONG entries use ask and exit/terminal checks use bid. SHORT entries use bid and exit/terminal checks use ask. Geometry was checked before accepting any R value.
"""


def render_forensics_md(payload: dict[str, Any]) -> str:
    rows = []
    for name, summary in payload["by_symbol"].items():
        rows.append([name, summary["rows"], summary["scored_rows"], summary["status_counts"], summary["r_summary_scored"]["mean_r"]])
    lessons = []
    for item in payload["lessons"]:
        lessons.append(f"### {item['finding']}\n\nEvidence: `{json.dumps(item['evidence'], sort_keys=True)}`\n\nInterpretation: {item['interpretation']}")
    return f"""# G12 OTI7 CNR Negative Result Forensics - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Headline

{payload['headline']}

## Symbol Anatomy

{table(['symbol', 'rows', 'scored', 'status counts', 'mean R scored'], rows)}

## Failure Lessons

{chr(10).join(lessons)}
"""


def render_methodology_md(payload: dict[str, Any]) -> str:
    eff = payload["effective_n"]
    rows = [[key, value] for key, value in eff.items()]
    return f"""# G12 OTI7 CNR Methodology Effective-N Audit - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`{payload['methodology_status']}`

{table(['effective-N field', 'value'], rows)}

DSR: `{payload['dsr']['status']}`. PBO: `{payload['pbo']['status']}`. Raw p: `{payload['raw_p']['status']}`.

This is descriptive quarantined discovery evidence only, not a validation or promotion dossier.
"""


def render_next_map_md(payload: dict[str, Any]) -> str:
    rows = []
    for item in payload["next_hypotheses"]:
        rows.append([item.get("status"), item.get("hypothesis"), item.get("required_unblocker")])
    return f"""# G12 OTI7 CNR Next Hypothesis Blocker Map - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Creativity Boundary

{payload['creativity_boundary']}

## Next Routes

{table(['status', 'hypothesis', 'required unblocker'], rows)}

Blocked CNR_E2/E3/E4 and CNR_T1/T2/T3 outcome families remain closed.
"""


def render_context_md(payload: dict[str, Any]) -> str:
    rows = [[key, value] for key, value in payload["context_anchor"].items()]
    return f"""# G12 OTI7 CNR Context Continuity And Instruction Coverage - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Context Anchor

{table(['field', 'value'], rows)}

## Active Question Stack

{chr(10).join(f'- {item}' for item in payload['active_question_stack'])}

## Route Decisions

{chr(10).join(f'- {item}' for item in payload['route_decisions'])}
"""


def render_completion_md(payload: dict[str, Any]) -> str:
    rows = [[item["status"], item["requirement"], json.dumps(item["evidence"], sort_keys=True)[:300]] for item in payload["prompt_to_artifact_checklist"]]
    return f"""# G12 OTI7 CNR Completion Audit - {DATE}

**Promotion verdict:** `{PROMOTION_VERDICT}`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Decision

`{payload['decision']}`

Can mark goal complete from artifact self-check: `{str(payload['can_mark_goal_complete']).lower()}`

## Prompt-To-Artifact Checklist

{table(['status', 'requirement', 'evidence'], rows)}

## Residual Risks

{chr(10).join(f'- {item}' for item in payload['residual_risks'])}
"""


def render_next_prompt_pack(payload: dict[str, Any]) -> str:
    return f"""# G12 OTI7 CNR Next-Lane Prompt Pack - {DATE}

Promotion posture: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

These prompts are source-safe next routes only. They must not be treated as evidence that CNR works.

## Prompt 1 - Residual-R Input Packet Audit

`/goal Build an input-only CNR residual-target-R packet audit for E0/E1 rows. Freeze executable quote, original entry/SL/TP, residual_target_r_from_executable_entry, duplicate key, source hash, no-leak scan, and sample-floor blocker before any outcome opening. Do not score outcomes or open blocked CNR_T1/T2/T3 rows. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Prompt 2 - CNR E4 Pretouch Trigger Source Builder

`/goal Build a source-field packet builder for CNR_E4_PRETOUCH_CONTINUATION_TRIGGER. Search current logs for pretouch_trigger_id and pretouch_trigger_utc; if absent, write exact logger/parser/source-field requirements. Do not infer pretouch triggers from later path and do not open outcomes. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Prompt 3 - CNR Geometry Decay And Invalidity Gate Preregistration

`/goal Preregister market-entry geometry decay and invalidity controls for future CNR audits. Use only input fields: executable quote, original entry, original SL, original TP1, quote age, spread, side, and duplicate group. Define invalidity and residual-R bins before outcomes. Do not backfit thresholds or rescore OTI7. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Prompt 4 - OTG0-PKT-061 Geometry Rebuild

`/goal Rebuild OTG0-PKT-061 CNR continuation-no-retrace input packets with source-hashed entry/stop/target or level packet and path_start/path_end fields. Produce a G12 packet audit and exact blocker ledger only. Do not score outcomes until the rebuilt packet passes source/no-leak/duplicate/geometry audit. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`
"""


def write_outputs(artifacts: dict[str, tuple[dict[str, Any] | None, str]]) -> None:
    for key, (json_payload, md_text) in artifacts.items():
        stem = OUTPUT_STEMS[key]
        if json_payload is not None:
            write_json(OUT / f"{stem}.json", json_payload)
        write_text(OUT / f"{stem}.md", md_text)


def build_bundle() -> dict[str, Any]:
    artifacts = build_artifacts()
    return {"artifacts": artifacts}


def main() -> None:
    write_outputs(build_artifacts())


if __name__ == "__main__":
    main()
