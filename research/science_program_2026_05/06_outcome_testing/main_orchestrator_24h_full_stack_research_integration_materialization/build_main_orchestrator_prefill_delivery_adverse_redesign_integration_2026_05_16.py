"""Materialize prefill delivery adverse-redesign decisions.

This plate joins the current prefill delivery path audit with the already
verified 0.50R entry-offset scorer outputs. It keeps the prefill family as a
redesign/source-capture surface, not a live entry change or promotion claim.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
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

PREFILL_AUDIT = REPO_ROOT / "shadow_logs/prefill_delivery_path_audit.jsonl"
ENTRY_OFFSET_DECISIONS = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_LEDGER_{DATE}.jsonl"
ENTRY_OFFSET_SCORER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_{DATE}.jsonl"
FORWARD_CAPTURE = REPO_ROOT / "src/research_infra/forward_capture.py"
TEST_FORWARD_CAPTURE = REPO_ROOT / "tests/test_forward_capture_shadow_loggers.py"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_OUTPUT_MANIFEST_{DATE}.json"


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
    with path.open("r", encoding="utf-8", errors="replace") as handle:
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
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[tuple[str, int], dict[str, Any]]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        asof = str(
            row.get("latest_resolution_asof_utc")
            or row.get("asof_latest_candle_utc")
            or row.get("created_at_utc")
            or row.get("backfilled_at_utc")
            or ""
        )
        key = (asof, int(row.get("_source_line_no") or 0))
        previous = latest.get(candidate_id)
        if previous is None or key >= previous[0]:
            latest[candidate_id] = (key, row)
    return {candidate_id: item[1] for candidate_id, item in latest.items()}


def delivery_state(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("delivery_leg_state")
    return value if isinstance(value, dict) else {}


def is_prefill_adverse_no_fill(row: dict[str, Any]) -> bool:
    state = delivery_state(row)
    return (
        state.get("delivery_leg_direction_derived") == "MOVED_AWAY_FROM_ENTRY_TOWARD_TP_AREA_WITHOUT_FILL"
        or row.get("path_label") == "continued_without_entry_touch_to_tp_area"
    )


def implementation_for(
    *,
    prefill_row: dict[str, Any],
    entry_decision: dict[str, Any] | None,
    entry_scorer: dict[str, Any] | None,
) -> dict[str, Any]:
    adverse = is_prefill_adverse_no_fill(prefill_row)
    if not adverse:
        return {
            "action_class": "KEEP",
            "branch_decision": "KEEP_NOT_PREFILL_ADVERSE_NO_FILL_DENOMINATOR",
            "implementation_candidate": "NONE_ENTRY_TOUCHED_OR_NOT_PREFILL_ADVERSE_DELIVERY",
            "score_status": "NOT_APPLICABLE",
            "outcome_status": "NOT_SCORED",
            "selected_proxy_r": None,
            "proxy_delta": None,
        }
    if not entry_decision or not entry_scorer:
        return {
            "action_class": "SOURCE_REPAIR",
            "branch_decision": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_JOIN_MISSING",
            "implementation_candidate": "REPAIR_PREFILL_TO_ENTRY_OFFSET_LEDGER_JOIN",
            "score_status": "SOURCE_REPAIR_REQUIRED",
            "outcome_status": "NOT_SCORED",
            "selected_proxy_r": None,
            "proxy_delta": None,
        }
    entry_branch = str(entry_decision.get("branch_decision") or "")
    scorer_proxy = safe_float(entry_scorer.get("strategy_proxy_r"))
    base = {
        "score_status": entry_scorer.get("score_status"),
        "outcome_status": entry_scorer.get("outcome_status"),
        "selected_proxy_r": scorer_proxy,
        "proxy_delta": scorer_proxy,
    }
    if entry_branch == "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER":
        return {
            **base,
            "action_class": "IMPLEMENT_DEFAULT_OFF",
            "branch_decision": "IMPLEMENT_DEFAULT_OFF_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER",
            "implementation_candidate": "PREFILL_ADVERSE_NO_FILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER",
        }
    if entry_branch == "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL":
        return {
            **base,
            "action_class": "REDESIGN",
            "branch_decision": "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL",
            "implementation_candidate": "PREFILL_ADVERSE_NO_FILL_FAR_MISS_RETEST_CONTROL",
        }
    if entry_branch == "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL":
        return {
            **base,
            "action_class": "KILL",
            "branch_decision": "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
            "implementation_candidate": "NONE_PREFILL_FAR_MISS_050R_NO_FILL",
        }
    if entry_branch == "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER":
        return {
            **base,
            "action_class": "SOURCE_REPAIR",
            "branch_decision": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_TICK_REPLAY",
            "implementation_candidate": "REPAIR_TICK_PARQUET_SOURCE_BEFORE_PREFILL_SCORING",
        }
    return {
        **base,
        "action_class": "SOURCE_REPAIR",
        "branch_decision": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_DECISION_UNMAPPED",
        "implementation_candidate": "MAP_PREFILL_ENTRY_OFFSET_DECISION_BRANCH",
    }


def build_rows() -> list[dict[str, Any]]:
    prefill = latest_by_candidate(read_jsonl(PREFILL_AUDIT))
    decisions = latest_by_candidate(read_jsonl(ENTRY_OFFSET_DECISIONS))
    scorers = latest_by_candidate(read_jsonl(ENTRY_OFFSET_SCORER))
    generated = utc_now()
    out: list[dict[str, Any]] = []
    for candidate_id, prefill_row in sorted(prefill.items()):
        entry_decision = decisions.get(candidate_id)
        entry_scorer = scorers.get(candidate_id)
        impl = implementation_for(
            prefill_row=prefill_row,
            entry_decision=entry_decision,
            entry_scorer=entry_scorer,
        )
        state = delivery_state(prefill_row)
        row = {
            "row_id": f"MAIN-ORCH24-PREFILL-ADVERSE-REDESIGN-{len(out) + 1:05d}",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "candidate_id": candidate_id,
            "symbol": prefill_row.get("symbol"),
            "side": prefill_row.get("side"),
            "framework": prefill_row.get("framework"),
            "session": prefill_row.get("session"),
            "decision_time_utc": prefill_row.get("decision_time_utc"),
            "latest_resolution_asof_utc": prefill_row.get("latest_resolution_asof_utc"),
            "prefill_source_line_no": prefill_row.get("_source_line_no"),
            "entry_decision_source_line_no": entry_decision.get("_source_line_no") if entry_decision else None,
            "entry_scorer_source_line_no": entry_scorer.get("_source_line_no") if entry_scorer else None,
            "prefill_adverse_no_fill_denominator": is_prefill_adverse_no_fill(prefill_row),
            "path_label": prefill_row.get("path_label"),
            "path_outcome_status": prefill_row.get("path_outcome_status"),
            "delivery_leg_direction_derived": state.get("delivery_leg_direction_derived"),
            "delivery_leg_source_status": state.get("source_status"),
            "entry_retest_redesign_bucket": entry_decision.get("entry_retest_redesign_bucket") if entry_decision else None,
            "entry_touch_distance_status": entry_decision.get("entry_touch_distance_status") if entry_decision else None,
            "m15_nearest_distance_to_entry_r": entry_decision.get("m15_nearest_distance_to_entry_r") if entry_decision else None,
            "entry_offset_branch_decision": entry_decision.get("branch_decision") if entry_decision else None,
            "entry_offset_action_class": entry_decision.get("action_class") if entry_decision else None,
            "entry_offset_scorer_status": entry_scorer.get("strategy_status") if entry_scorer else None,
            "entry_offset_scorer_proxy_r": safe_float(entry_scorer.get("strategy_proxy_r")) if entry_scorer else None,
            "exact_r": None,
            "previous_prefill_proxy_r": None,
            "safe_flags": SAFE_FLAGS,
            "no_shadow_log_append": True,
            "no_live_behavior": True,
            **impl,
        }
        out.append(row)
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric = [value for row in rows if (value := safe_float(row.get("selected_proxy_r"))) is not None]
    grouped_proxy: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = safe_float(row.get("selected_proxy_r"))
        if value is not None:
            grouped_proxy[str(row.get("branch_decision"))].append(value)
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION",
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "exact_r_rows": sum(1 for row in rows if row.get("exact_r") is not None),
        "prefill_adverse_no_fill_rows": sum(1 for row in rows if row.get("prefill_adverse_no_fill_denominator")),
        "non_prefill_denominator_rows": sum(1 for row in rows if not row.get("prefill_adverse_no_fill_denominator")),
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": round(sum(numeric), 8),
        "proxy_r_mean": None if not numeric else sum(numeric) / len(numeric),
        "previous_numeric_proxy_rows": 0,
        "previous_proxy_r_sum": 0.0,
        "numeric_proxy_row_delta": len(numeric),
        "proxy_r_sum_delta": round(sum(numeric), 8),
        "action_class_counts": dict(Counter(str(row.get("action_class")) for row in rows)),
        "branch_decision_counts": dict(Counter(str(row.get("branch_decision")) for row in rows)),
        "entry_retest_redesign_bucket_counts": dict(Counter(str(row.get("entry_retest_redesign_bucket")) for row in rows)),
        "path_label_counts": dict(Counter(str(row.get("path_label")) for row in rows)),
        "proxy_r_sum_by_branch_decision": {
            key: round(sum(values), 8) for key, values in sorted(grouped_proxy.items())
        },
        "plate_decision": "PREFILL_DELIVERY_ADVERSE_NO_FILL_ROWS_INTEGRATED_WITH_ENTRY_OFFSET_050R_SCORER_DECISIONS",
        "claim_boundary": (
            "Prefill adverse-delivery rows are routed to current entry-offset redesign decisions. "
            "Proxy R is from spread-aware tick replay where available; no live entry, broker, promotion, "
            "or validation-safe claim is opened."
        ),
        "safe_flags": SAFE_FLAGS,
    }


def file_ref(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def main() -> None:
    rows = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    summary = summarize(rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            "prefill_audit": file_ref(PREFILL_AUDIT),
            "entry_offset_decisions": file_ref(ENTRY_OFFSET_DECISIONS),
            "entry_offset_scorer": file_ref(ENTRY_OFFSET_SCORER),
            "forward_capture": file_ref(FORWARD_CAPTURE),
            "test_forward_capture": file_ref(TEST_FORWARD_CAPTURE),
        },
        "outputs": {
            "ledger": file_ref(OUTPUT_LEDGER),
            "summary": file_ref(OUTPUT_SUMMARY),
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
