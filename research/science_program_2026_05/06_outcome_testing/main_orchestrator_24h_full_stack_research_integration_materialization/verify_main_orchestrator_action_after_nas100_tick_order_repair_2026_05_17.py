"""Verify NAS100 tick-order repair materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

TARGET_ROW_ID = "MAIN-ORCH24-ACTION-SRCM15-00834"
TARGET_CANDIDATE_ID = "NAS100_2026-05-04T10:30:00+00:00"
REPAIRED_BRANCH = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_TICK_ORDER_REPAIRED_TP_BEFORE_SL_PROXY"

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_VERIFICATION_RESULT_{DATE}.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def require(condition: bool, issues: list[str], message: str) -> None:
    if not condition:
        issues.append(message)


def parse_utc(value: str | None) -> pd.Timestamp | None:
    if not value:
        return None
    return pd.Timestamp(value).tz_convert("UTC")


def main() -> None:
    issues: list[str] = []
    before_rows = read_jsonl(INPUT_LEDGER)
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    require(len(rows) == 3426, issues, f"expected 3426 rows, got {len(rows)}")
    require([row.get("row_id") for row in before_rows] == [row.get("row_id") for row in rows], issues, "row identity/order changed")

    before_counts = Counter(row.get("action_class") for row in before_rows)
    counts = Counter(row.get("action_class") for row in rows)
    require(before_counts.get("PRESERVE_REQUIREMENT") == 10, issues, f"unexpected input preserve count {before_counts.get('PRESERVE_REQUIREMENT')}")
    require(counts.get("PRESERVE_REQUIREMENT") == 9, issues, f"preserve requirement count should be 9, got {counts.get('PRESERVE_REQUIREMENT')}")
    require(counts.get("IMPLEMENT_DEFAULT_OFF") == before_counts.get("IMPLEMENT_DEFAULT_OFF", 0) + 1, issues, "implementation count did not increase by 1")
    require(counts.get("REDESIGN") == before_counts.get("REDESIGN"), issues, "redesign count changed")
    require(counts.get("KILL") == before_counts.get("KILL"), issues, "kill count changed")
    require(counts.get("KEEP") == before_counts.get("KEEP"), issues, "keep count changed")

    before_proxy = proxy_summary(before_rows)
    after_proxy = proxy_summary(rows)
    require(before_proxy == (709, 32.19811387), issues, f"unexpected input proxy state {before_proxy}")
    require(after_proxy == (710, 33.19811387), issues, f"unexpected output proxy state {after_proxy}")

    before_by_id = {row.get("row_id"): row for row in before_rows}
    by_id = {row.get("row_id"): row for row in rows}
    before_target = before_by_id.get(TARGET_ROW_ID)
    target = by_id.get(TARGET_ROW_ID)
    require(before_target is not None and target is not None, issues, "target row missing")
    if target:
        require(before_target.get("candidate_id") == TARGET_CANDIDATE_ID, issues, "input target candidate changed")
        require(target.get("candidate_id") == TARGET_CANDIDATE_ID, issues, "target candidate changed")
        require(target.get("action_class") == "IMPLEMENT_DEFAULT_OFF", issues, f"target action wrong: {target.get('action_class')}")
        require(target.get("branch_decision") == REPAIRED_BRANCH, issues, f"target branch wrong: {target.get('branch_decision')}")
        require(target.get("after_proxy_r") == 1.0, issues, f"target proxy R wrong: {target.get('after_proxy_r')}")
        require(target.get("proxy_r_delta") == 1.0, issues, f"target proxy delta wrong: {target.get('proxy_r_delta')}")
        require(target.get("exact_r") is None, issues, "target must not claim exact R")
        require(target.get("underlying_intelligence_preserved") is True, issues, "target intelligence not preserved")
        require(bool(target.get("missed_opportunity_audit")), issues, "target missed-opportunity audit missing")
        require(target.get("current_claim_proxy_counted") is True, issues, "target proxy counted flag missing")
        require(
            target.get("opportunity_downstream_paths") == [
                "entry-offset merge",
                "context feature",
                "source requirement",
                "broader system component",
            ],
            issues,
            f"target downstream paths wrong: {target.get('opportunity_downstream_paths')}",
        )
        tick = target.get("tick_order_repair") or {}
        entry_time = parse_utc((tick.get("entry_touch") or {}).get("ts_utc"))
        tp_time = parse_utc((tick.get("tp_touch") or {}).get("ts_utc"))
        sl_time = parse_utc((tick.get("sl_touch") or {}).get("ts_utc"))
        require(entry_time is not None and tp_time is not None and sl_time is not None, issues, "tick event timestamps missing")
        if entry_time is not None and tp_time is not None and sl_time is not None:
            require(entry_time < tp_time < sl_time, issues, f"tick order is not entry<TP<SL: {entry_time}, {tp_time}, {sl_time}")
        require(tick.get("terminal_event") == "TP_BEFORE_SL_AFTER_ENTRY", issues, f"tick terminal wrong: {tick.get('terminal_event')}")
        require(tick.get("entry_trigger_basis") == "SHORT_SELL_LIMIT_BID_GE_ENTRY", issues, "entry trigger basis wrong")
        require(tick.get("tp_trigger_basis") == "SHORT_POSITION_TP_ASK_LE_TP_AFTER_FILL", issues, "TP trigger basis wrong")
        require(tick.get("sl_trigger_basis") == "SHORT_POSITION_SL_ASK_GE_SL_AFTER_FILL", issues, "SL trigger basis wrong")
        require(tick.get("pre_entry_target_area_touch_not_counted") is True, issues, "pre-entry target touch should be recorded and not counted")
        require(tick.get("tick_order_proxy_r") == 1.0, issues, "tick order proxy R wrong")
        require(bool(tick.get("tick_source_sha256")), issues, "tick source sha256 missing")
        require(tick.get("decision_minute_tick_rows", 0) > 0, issues, "decision minute tick rows missing")
        require(tick.get("decision_minute_bid_max", 0) < target.get("entry_price", 0), issues, "decision minute should be below entry, confirming no fill at decision timestamp")

    unchanged_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("row_id") != TARGET_ROW_ID
        and {
            key: value
            for key, value in row.items()
            if key != "nas100_tick_order_repair_status"
        }
        != {
            key: value
            for key, value in before_by_id[row.get("row_id")].items()
            if key != "nas100_tick_order_repair_status"
        }
    ]
    require(not unchanged_diffs, issues, f"non-target rows changed: {unchanged_diffs[:5]}")

    remaining_preserve = [row for row in rows if row.get("action_class") == "PRESERVE_REQUIREMENT"]
    require(len(remaining_preserve) == 9, issues, f"expected 9 remaining preserve rows, got {len(remaining_preserve)}")
    require(
        Counter(row.get("branch_decision") for row in remaining_preserve)
        == Counter({"PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR": 9}),
        issues,
        f"unexpected remaining preserve branches {Counter(row.get('branch_decision') for row in remaining_preserve)}",
    )
    require(
        not any(safe_float(row.get("after_proxy_r")) is not None for row in remaining_preserve),
        issues,
        "remaining preserve rows should not carry counted numeric proxy R",
    )
    require(
        not any(row.get("branch_decision") == "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED" for row in rows),
        issues,
        "structural tick-order preserve branch still remains",
    )

    missing_audit = sum(
        1
        for row in rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    missing_intel = sum(
        1
        for row in rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and row.get("underlying_intelligence_preserved") is not True
    )
    require(missing_audit == 0, issues, f"missing missed-opportunity audits after repair: {missing_audit}")
    require(missing_intel == 0, issues, f"missing underlying-intelligence preservation after repair: {missing_intel}")
    require(summary.get("nas100_tick_order_rows_repaired") == 1, issues, "summary repaired count wrong")
    require(summary.get("nas100_tick_order_proxy_r_added") == 1.0, issues, "summary proxy R added wrong")
    require(summary.get("numeric_proxy_rows_after") == 710, issues, "summary numeric proxy rows wrong")
    require(summary.get("proxy_r_sum_after") == 33.19811387, issues, "summary proxy sum wrong")
    require(summary.get("remaining_preserve_requirement_rows") == 9, issues, "summary remaining preserve count wrong")
    require(summary.get("remaining_tick_order_preserve_rows") == 0, issues, "summary remaining tick-order preserve count wrong")
    require(summary.get("remaining_numeric_preserve_requirement_rows") == 0, issues, "summary remaining numeric preserve count wrong")
    require(manifest.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True, issues, "manifest safe flag missing")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": after_proxy[0],
        "proxy_r_sum_after": after_proxy[1],
        "nas100_tick_order_rows_repaired": summary.get("nas100_tick_order_rows_repaired"),
        "nas100_tick_order_proxy_r_added": summary.get("nas100_tick_order_proxy_r_added"),
        "nas100_tick_order_entry_touch_utc": summary.get("nas100_tick_order_entry_touch_utc"),
        "nas100_tick_order_tp_touch_utc": summary.get("nas100_tick_order_tp_touch_utc"),
        "nas100_tick_order_sl_touch_utc": summary.get("nas100_tick_order_sl_touch_utc"),
        "remaining_preserve_requirement_rows": summary.get("remaining_preserve_requirement_rows"),
        "remaining_tick_order_preserve_rows": summary.get("remaining_tick_order_preserve_rows"),
        "remaining_numeric_preserve_requirement_rows": summary.get("remaining_numeric_preserve_requirement_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
