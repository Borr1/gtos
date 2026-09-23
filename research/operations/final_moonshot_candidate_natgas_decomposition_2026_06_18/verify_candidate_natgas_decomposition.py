#!/usr/bin/env python3
"""Verify ASIA PDL NATGAS decomposition artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
RESULT = ROUTE_DIR / "ASIA_PDL_FADE_NATGAS_DECOMPOSITION_RESULT.json"
BRIDGE = ROUTE_DIR / "MT5_NATGAS_BRIDGE_READONLY_SNAPSHOT.json"
DAILY = ROUTE_DIR / "ASIA_PDL_FADE_EX_NATGAS_DAILY_SERIES.json"
VERIFY_OUT = ROUTE_DIR / "ASIA_PDL_FADE_NATGAS_DECOMPOSITION_VERIFICATION_RESULT.json"


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def main() -> int:
    result = _read_json(RESULT)
    bridge = _read_json(BRIDGE)
    daily = _read_json(DAILY)
    issues: list[dict[str, Any]] = []

    def issue(code: str, message: str, **extra: Any) -> None:
        row = {"code": code, "message": message}
        row.update(extra)
        issues.append(row)

    if result.get("decision") != "SPLIT_NATGAS_FROM_ASIA_PDL_FADE__DEPLOYABLE_EX_NATGAS_SURFACE_READY":
        issue("DECISION", "Unexpected NATGAS decomposition decision.", got=result.get("decision"))
    if result.get("excluded_cost_repair_symbols") != ["NATGAS_cash"]:
        issue("EXCLUDED_SYMBOLS", "NATGAS_cash must be the explicit excluded cost-repair lane.")
    if result.get("deployable_surface_symbol_count") != 30:
        issue("SURFACE_COUNT", "Deployable ex-NATGAS surface must contain 30 symbols.", got=result.get("deployable_surface_symbol_count"))
    if result.get("natgas_hard_drop_guard_present") is not True:
        issue("HARD_DROP_GUARD", "Admission hard-drop guard must still include NATGAS_cash.")
    if float(result.get("tick_spread_floor_R") or 0.0) < float(result.get("tick_spread_floor_untradeable_R") or 1.0):
        issue("TICK_FLOOR", "NATGAS tick floor must remain above the untradeable threshold unless a new revival route proves otherwise.")
    if (result.get("natgas_only") or {}).get("raw_trade", {}).get("n") != 18:
        issue("NATGAS_TRADE_COUNT", "NATGAS split trade count changed unexpectedly.")
    if ((result.get("natgas_only") or {}).get("splits", {}).get("train") or {}).get("n") != 0:
        issue("NATGAS_TRAIN_SAMPLE", "NATGAS should still have no train sample in this sleeve.")
    sealed_mean = ((result.get("natgas_only") or {}).get("splits", {}).get("sealed") or {}).get("meanR")
    if sealed_mean is None or float(sealed_mean) >= 0.0:
        issue("NATGAS_SEALED_DAMAGE", "NATGAS sealed split must remain negative in this proof.")
    ex = result.get("ex_natgas") or {}
    if ex.get("raw_trade", {}).get("n") != 7524:
        issue("EX_NATGAS_TRADE_COUNT", "Ex-NATGAS trade count changed unexpectedly.", got=ex.get("raw_trade", {}).get("n"))
    if ex.get("every_split_positive") is not True:
        issue("EX_NATGAS_SPLITS", "Ex-NATGAS surface must remain every-split positive.")
    if len(daily) != 2571:
        issue("EX_NATGAS_DAILY_COUNT", "Ex-NATGAS daily series count changed unexpectedly.", got=len(daily))
    if bridge.get("read_only") is not True or bridge.get("orderflow_used") is not False:
        issue("BRIDGE_BOUNDARY", "Bridge snapshot must remain read-only and orderflow-free.")
    if bridge.get("native_symbol") != "NATGAS.cash":
        issue("BRIDGE_SYMBOL", "Bridge snapshot must be for NATGAS.cash.", got=bridge.get("native_symbol"))
    if bridge.get("bridge_reachable") is not True:
        issue("BRIDGE_REACHABLE", "Current NATGAS bridge snapshot should be reachable.", error=bridge.get("error"))
    if bridge.get("tick_sample_rows", 0) <= 0:
        issue("BRIDGE_TICK_SAMPLE", "Current bridge snapshot should include a recent tick sample.")

    payload = {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.verification.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "decision": "PASS_NATGAS_DECOMPOSITION_PROOF" if not issues else "FAIL_REPAIR_NATGAS_DECOMPOSITION_PROOF",
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    VERIFY_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "issue_count": len(issues), "decision": payload["decision"]}, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
