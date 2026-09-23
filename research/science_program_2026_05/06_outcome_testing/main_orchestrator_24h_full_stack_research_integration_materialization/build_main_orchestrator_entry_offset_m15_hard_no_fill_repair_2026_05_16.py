"""Close entry-offset source-repair rows with conservative M15 hard no-fill proof.

This builder does not infer fills from M15 distance. It only converts rows that
already have no-entry-touch LTF/M15 path evidence and stayed at least 1.0R away
from original entry into zero-R no-fill kills for the 0.50R entry-offset scorer.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
M15_HARD_NO_FILL_MIN_DISTANCE_R = 1.0
ENTRY_DECISION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_LEDGER_{DATE}.jsonl"
ENTRY_SCORER_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_{DATE}.jsonl"
PREFILL_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_LEDGER_{DATE}.jsonl"
TICK_RECOMPUTE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_{DATE}.jsonl"
PATH_FOLLOW = REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl"
LTF_PATH_ORDER = REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if previous_asof is None or (
            current_asof is not None
            and (current_asof > previous_asof or (current_asof == previous_asof and current_created >= previous_created))
        ):
            out[cid] = row
    return out


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_id")): row for row in rows if row.get("candidate_id")}


def is_hard_no_fill_repairable(entry_row: dict[str, Any], tick_row: dict[str, Any], ltf_row: dict[str, Any] | None) -> bool:
    nearest_r = safe_float(entry_row.get("m15_nearest_distance_to_entry_r"))
    return (
        entry_row.get("branch_decision") == "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER"
        and entry_row.get("entry_retest_redesign_bucket") == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"
        and nearest_r is not None
        and nearest_r >= M15_HARD_NO_FILL_MIN_DISTANCE_R
        and tick_row.get("path_outcome_status") == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
        and tick_row.get("ltf_terminal_outcome_status") == "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"
        and (ltf_row or {}).get("entry_first_touch_utc") in (None, "")
    )


def build_rows() -> list[dict[str, Any]]:
    generated = utc_now()
    entry_rows = read_jsonl(ENTRY_DECISION_LEDGER)
    scorer_rows = by_candidate(read_jsonl(ENTRY_SCORER_LEDGER))
    prefill_rows = by_candidate(read_jsonl(PREFILL_LEDGER))
    tick_rows = by_candidate(read_jsonl(TICK_RECOMPUTE_LEDGER))
    path_rows = latest_by_candidate(read_jsonl(PATH_FOLLOW))
    ltf_rows = latest_by_candidate(read_jsonl(LTF_PATH_ORDER))
    out: list[dict[str, Any]] = []
    for entry in entry_rows:
        cid = str(entry.get("candidate_id"))
        scorer = scorer_rows.get(cid, {})
        prefill = prefill_rows.get(cid, {})
        tick = tick_rows.get(cid, {})
        path = path_rows.get(cid, {})
        ltf = ltf_rows.get(cid)
        repairable = is_hard_no_fill_repairable(entry, tick, ltf)
        before_entry_action = entry.get("action_class")
        before_entry_branch = entry.get("branch_decision")
        before_scorer_status = scorer.get("strategy_status")
        before_scorer_proxy = safe_float(scorer.get("strategy_proxy_r"))
        before_prefill_action = prefill.get("action_class")
        before_prefill_branch = prefill.get("branch_decision")
        before_prefill_proxy = safe_float(prefill.get("selected_proxy_r"))
        after_entry_action = "KILL" if repairable else before_entry_action
        after_entry_branch = (
            "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
            if repairable
            else before_entry_branch
        )
        after_scorer_status = "KILLED_ENTRY_OFFSET_050R_M15_HARD_NO_FILL" if repairable else before_scorer_status
        after_score_status = (
            "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF"
            if repairable
            else scorer.get("score_status")
        )
        after_scorer_proxy = 0.0 if repairable else before_scorer_proxy
        after_prefill_action = "KILL" if repairable and before_prefill_action == "SOURCE_REPAIR" else before_prefill_action
        after_prefill_branch = (
            "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
            if repairable and before_prefill_action == "SOURCE_REPAIR"
            else before_prefill_branch
        )
        after_prefill_proxy = 0.0 if repairable and before_prefill_action == "SOURCE_REPAIR" else before_prefill_proxy
        out.append(
            {
                "row_id": f"MAIN-ORCH24-ENTRY-OFFSET-M15-HARD-NOFILL-{len(out) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "candidate_id": cid,
                "symbol": entry.get("symbol"),
                "broker_symbol": entry.get("broker_symbol"),
                "side": entry.get("side"),
                "framework": entry.get("framework"),
                "decision_time_utc": entry.get("decision_time_utc"),
                "asof_latest_candle_utc": entry.get("asof_latest_candle_utc"),
                "entry_retest_redesign_bucket": entry.get("entry_retest_redesign_bucket"),
                "m15_nearest_distance_to_entry_r": entry.get("m15_nearest_distance_to_entry_r"),
                "m15_hard_no_fill_min_distance_r": M15_HARD_NO_FILL_MIN_DISTANCE_R,
                "m15_hard_no_fill_repaired": repairable,
                "m15_hard_no_fill_proof_status": "PROVEN_NO_FILL_AT_050R_FROM_M15_LTF_RANGE" if repairable else "NOT_REPAIRED_OR_NOT_NEEDED",
                "path_outcome_status": tick.get("path_outcome_status"),
                "ltf_terminal_outcome_status": tick.get("ltf_terminal_outcome_status"),
                "latest_ltf_entry_first_touch_utc": (ltf or {}).get("entry_first_touch_utc"),
                "source_ohlc_range": path.get("source_ohlc_range"),
                "tick_source_status": entry.get("tick_source_status"),
                "tick_source_files": tick.get("tick_source_files"),
                "tick_source_read_error_files": tick.get("tick_source_read_error_files"),
                "before_entry_action_class": before_entry_action,
                "after_entry_action_class": after_entry_action,
                "before_entry_branch_decision": before_entry_branch,
                "after_entry_branch_decision": after_entry_branch,
                "before_entry_scorer_status": before_scorer_status,
                "after_entry_scorer_status": after_scorer_status,
                "before_entry_score_status": scorer.get("score_status"),
                "after_entry_score_status": after_score_status,
                "before_entry_proxy_r": before_scorer_proxy,
                "after_entry_proxy_r": after_scorer_proxy,
                "before_prefill_action_class": before_prefill_action,
                "after_prefill_action_class": after_prefill_action,
                "before_prefill_branch_decision": before_prefill_branch,
                "after_prefill_branch_decision": after_prefill_branch,
                "before_prefill_proxy_r": before_prefill_proxy,
                "after_prefill_proxy_r": after_prefill_proxy,
                "proxy_delta": (after_scorer_proxy or 0.0) - (before_scorer_proxy or 0.0),
                "exact_r": None,
                "safe_flags": SAFE_FLAGS,
                "no_shadow_log_append": True,
                "no_live_behavior": True,
            }
        )
    return out


def numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [value for row in rows if (value := safe_float(row.get(key))) is not None]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    before_values = numeric_values(rows, "before_entry_proxy_r")
    after_values = numeric_values(rows, "after_entry_proxy_r")
    before_prefill = numeric_values(rows, "before_prefill_proxy_r")
    after_prefill = numeric_values(rows, "after_prefill_proxy_r")
    repaired = [row for row in rows if row["m15_hard_no_fill_repaired"]]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR",
        "claim_boundary": (
            "M15 hard no-fill proof can only kill obvious no-fill 0.50R entry-offset rows. "
            "It cannot infer fills, TP-after-fill, live entries, broker actual R, or validation-safe performance."
        ),
        "rows": len(rows),
        "candidate_rows": len({row["candidate_id"] for row in rows}),
        "exact_r_rows": 0,
        "m15_hard_no_fill_repaired_rows": len(repaired),
        "repaired_candidate_ids": [row["candidate_id"] for row in repaired],
        "before_numeric_proxy_rows": len(before_values),
        "after_numeric_proxy_rows": len(after_values),
        "numeric_proxy_row_delta": len(after_values) - len(before_values),
        "before_proxy_r_sum": sum(before_values),
        "after_proxy_r_sum": sum(after_values),
        "proxy_r_sum_delta": sum(after_values) - sum(before_values),
        "before_prefill_numeric_proxy_rows": len(before_prefill),
        "after_prefill_numeric_proxy_rows": len(after_prefill),
        "prefill_numeric_proxy_row_delta": len(after_prefill) - len(before_prefill),
        "before_prefill_proxy_r_sum": sum(before_prefill),
        "after_prefill_proxy_r_sum": sum(after_prefill),
        "prefill_proxy_r_sum_delta": sum(after_prefill) - sum(before_prefill),
        "before_entry_action_class_counts": dict(Counter(str(row["before_entry_action_class"]) for row in rows)),
        "after_entry_action_class_counts": dict(Counter(str(row["after_entry_action_class"]) for row in rows)),
        "before_entry_branch_decision_counts": dict(Counter(str(row["before_entry_branch_decision"]) for row in rows)),
        "after_entry_branch_decision_counts": dict(Counter(str(row["after_entry_branch_decision"]) for row in rows)),
        "before_prefill_action_class_counts": dict(Counter(str(row["before_prefill_action_class"]) for row in rows)),
        "after_prefill_action_class_counts": dict(Counter(str(row["after_prefill_action_class"]) for row in rows)),
        "before_prefill_branch_decision_counts": dict(Counter(str(row["before_prefill_branch_decision"]) for row in rows)),
        "after_prefill_branch_decision_counts": dict(Counter(str(row["after_prefill_branch_decision"]) for row in rows)),
        "after_entry_scorer_status_counts": dict(Counter(str(row["after_entry_scorer_status"]) for row in rows)),
        "safe_flags": SAFE_FLAGS,
        "plate_decision": "ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_CLOSES_CURRENT_TICK_SOURCE_REPAIR_ROWS",
    }


def build_manifest(outputs: list[Path]) -> dict[str, Any]:
    inputs = [ENTRY_DECISION_LEDGER, ENTRY_SCORER_LEDGER, PREFILL_LEDGER, TICK_RECOMPUTE_LEDGER, PATH_FOLLOW, LTF_PATH_ORDER]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            path.name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in inputs
        },
        "outputs": {
            path.name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in outputs
        },
    }


def main() -> None:
    rows = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows))
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
