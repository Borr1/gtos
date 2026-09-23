#!/usr/bin/env python3
"""Verify stored candidate bridge spec/LTF work artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
TARGET_SYMBOLS = {
    "AUDUSD",
    "DASHUSD",
    "EURGBP",
    "EURUSD",
    "GBPUSD",
    "LTCUSD",
    "NATGAS_cash",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "XPDUSD",
    "XPTUSD",
    "XRPUSD",
    "XTZUSD",
}
M1_REPAIRED_SYMBOLS = {"XPDUSD", "XPTUSD", "XRPUSD"}
DUAL_BROKER_FX = {"AUDUSD", "EURGBP", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            data = json.loads(line)
            if not isinstance(data, dict):
                raise TypeError(f"{path}:{line_no} did not contain a JSON object")
            rows.append(data)
    return rows


def verify() -> dict[str, Any]:
    result = _read_json(ROUTE_DIR / "CANDIDATE_BRIDGE_SPEC_LTF_WORK_RESULT.json")
    capture = _read_json(ROUTE_DIR / "MT5_BRIDGE_SYMBOL_SPEC_CAPTURE.json")
    history = _read_json(ROUTE_DIR / "CANDIDATE_HISTORY_MANIFEST_SUMMARY.json")
    decisions = _read_jsonl(ROUTE_DIR / "CANDIDATE_BRIDGE_WORK_DECISION_LEDGER.jsonl")
    spec_rows = _read_jsonl(ROUTE_DIR / "MT5_BRIDGE_SYMBOL_SPEC_LEDGER.jsonl")

    bridge_symbols = {
        row["symbol"]
        for row in spec_rows
        if row.get("symbol_info_present") is True and row.get("trade_mode") == 4
    }
    m1_ready = {
        symbol
        for symbol in M1_REPAIRED_SYMBOLS
        if int((history.get(symbol, {}).get("M1") or {}).get("row_count") or 0) > 0
    }
    dual_broker_ready = {
        row["symbol"]
        for row in decisions
        if row.get("deployment_status") == "profile_patchable_dual_broker"
    }

    missing: list[str] = []
    if result.get("ok") is not True:
        missing.append("result_ok")
    if capture.get("read_only") is not True:
        missing.append("bridge_capture_read_only")
    if result.get("orderflow_used") is not False:
        missing.append("orderflow_false")
    if result.get("broker_or_order_mutation") is not False:
        missing.append("broker_order_mutation_false")
    if bridge_symbols != TARGET_SYMBOLS:
        missing.append("all_target_symbols_bridge_native")
    if m1_ready != M1_REPAIRED_SYMBOLS:
        missing.append("m1_repaired_symbols")
    if not DUAL_BROKER_FX.issubset(dual_broker_ready):
        missing.append("dual_broker_fx_patchable")
    if result.get("ltf_gap_count_after_bridge_export") != 0:
        missing.append("ltf_gap_count_zero")

    verification = {
        "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_work.verification.v1",
        "ok": not missing,
        "missing": missing,
        "bridge_native_symbol_count": len(bridge_symbols),
        "target_symbol_count": len(TARGET_SYMBOLS),
        "m1_repaired_symbols": sorted(m1_ready),
        "dual_broker_patchable_fx_symbols": sorted(dual_broker_ready & DUAL_BROKER_FX),
        "ltf_gap_count_after_bridge_export": result.get("ltf_gap_count_after_bridge_export"),
        "readiness_work_item_count_after_bridge_export": result.get("readiness_work_item_count_after_bridge_export"),
        "orderflow_used": result.get("orderflow_used"),
        "broker_or_order_mutation": result.get("broker_or_order_mutation"),
        "vps_process_touched": result.get("vps_process_touched"),
    }
    (ROUTE_DIR / "CANDIDATE_BRIDGE_SPEC_LTF_WORK_VERIFICATION_RESULT.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return verification


def main() -> int:
    verification = verify()
    print(json.dumps(verification, sort_keys=True))
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
