"""Repair the remaining NAS100 same-M1 structural row with local tick order.

The residual action ledger still has one structural preserve row where M1 bars
could not order entry/terminal events. Local NAS100 tick parquet is available
for the decision date, and the live mechanical shadow log carries the current
entry/stop/target geometry. This plate consumes both sources and converts the
row to a default-off proxy implementation candidate only when ticks show entry
first and TP before SL after fill. A pre-fill target touch is recorded but not
counted as trade R.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]

TARGET_ROW_ID = "MAIN-ORCH24-ACTION-SRCM15-00834"
TARGET_CANDIDATE_ID = "NAS100_2026-05-04T10:30:00+00:00"
TARGET_STRATEGY_ID = "V2_STRUCT_COMPOSITE_ANY"
TARGET_SYMBOL = "NAS100"

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_SUMMARY_{DATE}.json"

SHADOW_OUTCOMES = REPO_ROOT / "shadow_logs" / "live_mechanical_strategy_shadow_outcomes.jsonl"
TICK_PARQUET = REPO_ROOT / "data" / "ticks" / TARGET_SYMBOL / "2026-05-04.parquet"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

REPAIRED_BRANCH = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_TICK_ORDER_REPAIRED_TP_BEFORE_SL_PROXY"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "positive_rows": sum(value > 0 for value in values),
        "zero_rows": sum(value == 0 for value in values),
        "negative_rows": sum(value < 0 for value in values),
    }


def action_delta(before: Counter[str], after: Counter[str]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def iso_ts(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.isoformat().replace("+00:00", "Z")


def first_tick(df: pd.DataFrame, mask: pd.Series) -> dict[str, Any] | None:
    hit = df.loc[mask, ["ts_utc", "bid", "ask"]].head(1)
    if hit.empty:
        return None
    record = hit.iloc[0]
    return {
        "ts_utc": iso_ts(record["ts_utc"]),
        "bid": round(float(record["bid"]), 8),
        "ask": round(float(record["ask"]), 8),
    }


def require_tick(label: str, hit: dict[str, Any] | None) -> dict[str, Any]:
    if hit is None:
        raise ValueError(f"missing required tick event: {label}")
    return hit


def latest_shadow_geometry() -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    with SHADOW_OUTCOMES.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip() or TARGET_CANDIDATE_ID not in line:
                continue
            row = json.loads(line)
            if row.get("strategy_id") != TARGET_STRATEGY_ID:
                continue
            if row.get("symbol") != TARGET_SYMBOL or row.get("side") != "SHORT":
                continue
            row["_source_line_no"] = line_no
            matches.append(row)
    if not matches:
        raise ValueError(f"no shadow geometry rows found for {TARGET_CANDIDATE_ID} / {TARGET_STRATEGY_ID}")
    row = matches[-1]
    metrics = row.get("path_metrics") or {}
    required = ["entry_price", "stop_loss", "take_profit_1", "base_r_price"]
    missing = [key for key in required if safe_float(metrics.get(key)) is None]
    if missing:
        raise ValueError(f"latest shadow geometry missing numeric fields: {missing}")
    return {
        "source_line_no": row["_source_line_no"],
        "decision_time_utc": row.get("decision_time_utc") or TARGET_CANDIDATE_ID.removeprefix(f"{TARGET_SYMBOL}_"),
        "entry_price": float(metrics["entry_price"]),
        "stop_loss": float(metrics["stop_loss"]),
        "take_profit_1": float(metrics["take_profit_1"]),
        "base_r_price": float(metrics["base_r_price"]),
        "raw_path_metrics": metrics,
    }


def compute_tick_order(geometry: dict[str, Any]) -> dict[str, Any]:
    df = pd.read_parquet(TICK_PARQUET, columns=["ts_utc", "bid", "ask"])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)

    decision_time = pd.Timestamp(geometry["decision_time_utc"])
    if decision_time.tzinfo is None:
        decision_time = decision_time.tz_localize("UTC")
    else:
        decision_time = decision_time.tz_convert("UTC")

    entry = float(geometry["entry_price"])
    stop = float(geometry["stop_loss"])
    target = float(geometry["take_profit_1"])
    from_decision = df[df["ts_utc"] >= decision_time].copy()
    if from_decision.empty:
        raise ValueError("tick parquet has no ticks at or after decision time")

    entry_bid = require_tick("SHORT_SELL_LIMIT_BID_GE_ENTRY", first_tick(from_decision, from_decision["bid"] >= entry))
    entry_ask_alt = first_tick(from_decision, from_decision["ask"] >= entry)
    entry_time = pd.Timestamp(entry_bid["ts_utc"])
    post_fill = from_decision[from_decision["ts_utc"] >= entry_time].copy()

    tp_ask = require_tick("SHORT_TP_ASK_LE_TP_AFTER_ENTRY", first_tick(post_fill, post_fill["ask"] <= target))
    sl_ask = require_tick("SHORT_SL_ASK_GE_SL_AFTER_ENTRY", first_tick(post_fill, post_fill["ask"] >= stop))
    tp_bid_alt = first_tick(post_fill, post_fill["bid"] <= target)
    sl_bid_alt = first_tick(post_fill, post_fill["bid"] >= stop)
    pre_entry = from_decision[from_decision["ts_utc"] < entry_time]
    pre_entry_tp_ask = first_tick(pre_entry, pre_entry["ask"] <= target)
    pre_entry_tp_bid = first_tick(pre_entry, pre_entry["bid"] <= target)

    tp_time = pd.Timestamp(tp_ask["ts_utc"])
    sl_time = pd.Timestamp(sl_ask["ts_utc"])
    if not (entry_time < tp_time < sl_time):
        raise ValueError(
            "tick order is not entry->TP->SL under short quote convention: "
            f"entry={entry_bid['ts_utc']} tp={tp_ask['ts_utc']} sl={sl_ask['ts_utc']}"
        )

    decision_minute = from_decision[
        from_decision["ts_utc"] < decision_time + pd.Timedelta(minutes=1)
    ]

    return {
        "tick_source_path": str(TICK_PARQUET.relative_to(REPO_ROOT)),
        "tick_source_sha256": sha256_file(TICK_PARQUET),
        "tick_rows_total": int(len(df)),
        "tick_utc_min": iso_ts(df["ts_utc"].min()),
        "tick_utc_max": iso_ts(df["ts_utc"].max()),
        "decision_time_utc": iso_ts(decision_time),
        "decision_minute_tick_rows": int(len(decision_minute)),
        "decision_minute_bid_min": round(float(decision_minute["bid"].min()), 8),
        "decision_minute_bid_max": round(float(decision_minute["bid"].max()), 8),
        "decision_minute_ask_min": round(float(decision_minute["ask"].min()), 8),
        "decision_minute_ask_max": round(float(decision_minute["ask"].max()), 8),
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": target,
        "base_r_price": float(geometry["base_r_price"]),
        "entry_trigger_basis": "SHORT_SELL_LIMIT_BID_GE_ENTRY",
        "entry_touch": entry_bid,
        "entry_touch_alternate_ask_ge_entry": entry_ask_alt,
        "tp_trigger_basis": "SHORT_POSITION_TP_ASK_LE_TP_AFTER_FILL",
        "tp_touch": tp_ask,
        "tp_touch_alternate_bid_le_tp": tp_bid_alt,
        "sl_trigger_basis": "SHORT_POSITION_SL_ASK_GE_SL_AFTER_FILL",
        "sl_touch": sl_ask,
        "sl_touch_alternate_bid_ge_sl": sl_bid_alt,
        "pre_entry_target_area_touch_ask": pre_entry_tp_ask,
        "pre_entry_target_area_touch_bid": pre_entry_tp_bid,
        "pre_entry_target_area_touch_not_counted": pre_entry_tp_ask is not None or pre_entry_tp_bid is not None,
        "terminal_event_order": "ENTRY_THEN_TP_THEN_SL",
        "terminal_event": "TP_BEFORE_SL_AFTER_ENTRY",
        "tick_order_proxy_r": 1.0,
        "proxy_r_boundary": "LOCAL_TICK_QUOTE_PROXY_NOT_BROKER_ACTUAL_R",
    }


def repair_target_row(row: dict[str, Any], *, generated: str, geometry: dict[str, Any], tick_order: dict[str, Any]) -> None:
    original_branch = row.get("branch_decision")
    row["before_nas100_tick_order_repair_action_class"] = row.get("action_class")
    row["before_nas100_tick_order_repair_branch_decision"] = original_branch
    row["before_nas100_tick_order_repair_after_proxy_r"] = row.get("after_proxy_r")
    row["nas100_tick_order_repair_generated_utc"] = generated
    row["nas100_tick_order_repair_status"] = "REPAIRED_FROM_LOCAL_TICK_PARQUET"
    row["action_class"] = "IMPLEMENT_DEFAULT_OFF"
    row["branch_decision"] = REPAIRED_BRANCH
    row["implementation_decision"] = REPAIRED_BRANCH
    row["current_action"] = REPAIRED_BRANCH
    row["next_action"] = "DEFAULT_OFF_STRUCTURAL_SCORER_RECOMPUTE_WITH_TICK_ORDER_FEATURE"
    row["after_strategy_status"] = "IMPLEMENT_DEFAULT_OFF_TICK_ORDER_REPAIRED_PROXY_POSITIVE"
    row["after_score_status"] = "TICK_ORDER_REPAIRED_PROXY_TP_BEFORE_SL_AFTER_FILL"
    row["after_proxy_r"] = tick_order["tick_order_proxy_r"]
    row["proxy_r_delta"] = tick_order["tick_order_proxy_r"]
    row["current_claim_proxy_counted"] = True
    row["exact_r"] = None
    row["data_requirement_state"] = "TICK_ORDER_REPAIRED_FROM_LOCAL_TICK_PARQUET_PROXY_NOT_BROKER_ACTUAL"
    row["decision_evidence"] = "NAS100_TICK_PARQUET_REPAIRS_SAME_M1_AMBIGUITY_TP_AFTER_FILL_BEFORE_SL"
    row["scoring_boundary"] = "LOCAL_TICK_QUOTE_PROXY_R_NOT_BROKER_ACTUAL_R"
    row["implementation_candidate"] = "DEFAULT_OFF_STRUCTURAL_METADATA_TICK_ORDER_REPAIRED_PROXY"
    row["implementation_candidate_state"] = "DEFAULT_OFF_REQUIRES_SCORER_FEATURE_AND_FORWARD_SHADOW_RECOMPUTE"
    row["opportunity_preservation_status"] = "STRUCTURAL_SAME_M1_AMBIGUITY_REPAIRED_TO_ENTRY_OFFSET_OWNED_TICK_ORDER_PROXY"
    row["opportunity_proxy_r_reference"] = tick_order["tick_order_proxy_r"]
    row["opportunity_proxy_reference_status"] = "COUNTED_PROXY_FROM_LOCAL_TICK_ORDER_REPAIR"
    row["opportunity_owner_row_id"] = row.get("source_row_id")
    row["opportunity_owner_source_artifact"] = row.get("source_artifact")
    row["opportunity_not_independently_countable_reason"] = (
        "The prior M1 structural claim was not independently countable because entry and terminal events shared the "
        "same M1 timestamp; local NAS100 tick quotes now order fill, TP, and SL, so the repaired opportunity is "
        "counted only as default-off tick-order proxy R and not as broker-actual exact R."
    )
    row["opportunity_useful_mechanism"] = (
        "Same-M1 structural ambiguity can become an entry-offset/tick-order scorer feature: ignore pre-fill target "
        "touches, require fill first, and score TP/SL path with quote-side rules."
    )
    row["opportunity_downstream_paths"] = [
        "entry-offset merge",
        "context feature",
        "source requirement",
        "broader system component",
    ]
    row["underlying_intelligence_preserved"] = True
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_CURRENT_STRUCTURAL_SAME_M1_CLAIM_REPAIRED_TO_DEFAULT_OFF_PROXY",
        "current_claim": original_branch,
        "unsupported_reason": "M1_ONLY_PATH_ORDER_WAS_AMBIGUOUS_WITH_ENTRY_AND_TERMINAL_EVENT_IN_SAME_MINUTE",
        "what_was_tried": (
            "Strategy shadow geometry was joined to local NAS100 tick parquet; short quote-side entry, target, "
            "and stop triggers were recomputed from decision time and again after fill."
        ),
        "what_could_make_it_work": (
            "Broker execution history or live order/deal truth can promote this beyond local quote proxy; until "
            "then it remains default-off implementation evidence for structural tick-order scoring."
        ),
        "preserve_as": "ENTRY_OFFSET_OWNED_TICK_ORDER_SCORER_IMPLEMENTATION_CANDIDATE",
        "next_route": "SCORER_FEATURE_RECOMPUTE_AND_FORWARD_SHADOW_TICK_ORDER_CAPTURE",
        "path_status": {
            "entry_touch_utc": tick_order["entry_touch"]["ts_utc"],
            "tp_touch_utc": tick_order["tp_touch"]["ts_utc"],
            "sl_touch_utc": tick_order["sl_touch"]["ts_utc"],
            "pre_entry_target_area_touch_not_counted": tick_order["pre_entry_target_area_touch_not_counted"],
            "proxy_r": tick_order["tick_order_proxy_r"],
            "proxy_boundary": tick_order["proxy_r_boundary"],
        },
    }
    row["tick_order_repair"] = tick_order
    row["tick_order_repair_source_shadow_outcome_path"] = str(SHADOW_OUTCOMES.relative_to(REPO_ROOT))
    row["tick_order_repair_source_shadow_outcome_line"] = geometry["source_line_no"]
    row["tick_order_repair_shadow_path_metrics"] = geometry["raw_path_metrics"]
    row["entry_price"] = geometry["entry_price"]
    row["stop_loss"] = geometry["stop_loss"]
    row["take_profit_1"] = geometry["take_profit_1"]
    row["base_r_price"] = geometry["base_r_price"]
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    geometry = latest_shadow_geometry()
    tick_order = compute_tick_order(geometry)

    before_counts = Counter(str(row.get("action_class") or "") for row in source_rows)
    before_branch_counts = Counter(str(row.get("branch_decision") or "") for row in source_rows)
    before_proxy = proxy_summary(source_rows)
    output_rows: list[dict[str, Any]] = []
    touched: list[dict[str, Any]] = []

    for row in source_rows:
        new = dict(row)
        new.pop("_source_line_no", None)
        if new.get("row_id") == TARGET_ROW_ID:
            if new.get("candidate_id") != TARGET_CANDIDATE_ID:
                raise ValueError(f"target row candidate mismatch: {new.get('candidate_id')}")
            if new.get("branch_decision") != "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED":
                raise ValueError(f"target row branch mismatch: {new.get('branch_decision')}")
            repair_target_row(new, generated=generated, geometry=geometry, tick_order=tick_order)
            touched.append(new)
        else:
            new["nas100_tick_order_repair_status"] = "NOT_TARGET_ROW"
        output_rows.append(new)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_branch_counts = Counter(str(row.get("branch_decision") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    missing_audit = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    missing_intel = sum(
        1
        for row in output_rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and row.get("underlying_intelligence_preserved") is not True
    )

    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": input_summary.get("rows"),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if safe_float(row.get("exact_r")) is not None),
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "branch_counts_before_preserve_structural_tick_order": before_branch_counts.get(
            "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED", 0
        ),
        "branch_counts_after_preserve_structural_tick_order": after_branch_counts.get(
            "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED", 0
        ),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "nas100_tick_order_rows_repaired": len(touched),
        "nas100_tick_order_proxy_r_added": round(
            sum(float(row["after_proxy_r"]) for row in touched if safe_float(row.get("after_proxy_r")) is not None),
            8,
        ),
        "nas100_tick_order_target_row_id": TARGET_ROW_ID,
        "nas100_tick_order_candidate_id": TARGET_CANDIDATE_ID,
        "nas100_tick_order_source_tick_path": tick_order["tick_source_path"],
        "nas100_tick_order_source_tick_sha256": tick_order["tick_source_sha256"],
        "nas100_tick_order_shadow_outcome_line": geometry["source_line_no"],
        "nas100_tick_order_terminal_event": tick_order["terminal_event"],
        "nas100_tick_order_entry_touch_utc": tick_order["entry_touch"]["ts_utc"],
        "nas100_tick_order_tp_touch_utc": tick_order["tp_touch"]["ts_utc"],
        "nas100_tick_order_sl_touch_utc": tick_order["sl_touch"]["ts_utc"],
        "nas100_pre_entry_target_area_touch_not_counted": tick_order["pre_entry_target_area_touch_not_counted"],
        "remaining_preserve_requirement_rows": after_counts.get("PRESERVE_REQUIREMENT", 0),
        "remaining_no_scalar_preserve_rows": after_branch_counts.get("PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR", 0),
        "remaining_tick_order_preserve_rows": after_branch_counts.get(
            "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED",
            0,
        ),
        "remaining_numeric_preserve_requirement_rows": sum(
            1
            for row in output_rows
            if row.get("action_class") == "PRESERVE_REQUIREMENT" and safe_float(row.get("after_proxy_r")) is not None
        ),
        "redesign_preserve_kill_missing_audit_after": missing_audit,
        "redesign_preserve_kill_missing_underlying_intel_after": missing_intel,
        "rows_with_missed_opportunity_audit_after": sum(1 for row in output_rows if row.get("missed_opportunity_audit")),
        "rows_with_underlying_intelligence_preserved_after": sum(
            1 for row in output_rows if row.get("underlying_intelligence_preserved") is True
        ),
        "safe_flags": SAFE_FLAGS,
        "research_safety": {
            "changes_live_behavior": False,
            "changes_shadow_log_history": False,
            "changes_prompt_risk_selector_execution": False,
            "opens_exact_r": False,
            "opens_proxy_r": True,
        },
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any], outputs: list[Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "date": DATE,
        "description": "NAS100 same-M1 structural preserve row repaired with local tick order into default-off proxy R.",
        "generated_utc": summary["generated_utc"],
        "inputs": {
            "ledger": {"path": str(INPUT_LEDGER), "sha256": sha256_file(INPUT_LEDGER)},
            "summary": {"path": str(INPUT_SUMMARY), "sha256": sha256_file(INPUT_SUMMARY)},
            "shadow_outcomes": {"path": str(SHADOW_OUTCOMES), "sha256": sha256_file(SHADOW_OUTCOMES)},
            "tick_parquet": {"path": str(TICK_PARQUET), "sha256": sha256_file(TICK_PARQUET)},
        },
        "outputs": {
            path.name: {"path": str(path), "sha256": sha256_file(path)}
            for path in outputs
            if path.exists()
        },
        "key_counts": {
            "rows": summary["rows"],
            "nas100_tick_order_rows_repaired": summary["nas100_tick_order_rows_repaired"],
            "nas100_tick_order_proxy_r_added": summary["nas100_tick_order_proxy_r_added"],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
            "remaining_preserve_requirement_rows": summary["remaining_preserve_requirement_rows"],
            "remaining_tick_order_preserve_rows": summary["remaining_tick_order_preserve_rows"],
            "remaining_numeric_preserve_requirement_rows": summary["remaining_numeric_preserve_requirement_rows"],
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    write_json(OUTPUT_MANIFEST, build_manifest(summary, [OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
