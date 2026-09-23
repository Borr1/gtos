from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_vnext_moonshot_lane07_broker_truth_cost_calibration as lane07


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    except (OSError, json.JSONDecodeError):
        return []
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_route() -> dict[str, Any]:
    issues: list[str] = []
    required = [
        "context_anchor",
        "schema",
        "source_coverage",
        "dependency_state",
        "symbol_spec",
        "broker_truth",
        "cost_calibration",
        "source_gap",
        "downstream_contract",
        "source_use_state",
        "runtime_effect_boundary",
        "completion_audit",
        "manifest",
        "focused_test_result",
    ]
    for name in required:
        path = lane07.OUTPUTS[name]
        if not path.exists():
            issues.append(f"missing_output:{name}:{lane07.rel(path)}")
        elif path.stat().st_size == 0:
            issues.append(f"empty_output:{name}:{lane07.rel(path)}")

    focused_test_path = lane07.OUTPUTS["focused_test_result"]
    if focused_test_path.exists() and focused_test_path.stat().st_size > 0:
        try:
            root = ET.parse(focused_test_path).getroot()
            suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
            failures = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
            errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
            skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
            tests = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
            if tests == 0 or failures or errors:
                issues.append(
                    "focused_test_result_not_clean:"
                    f"tests={tests} failures={failures} errors={errors} skipped={skipped}"
                )
        except (ET.ParseError, OSError, ValueError) as exc:
            issues.append(f"focused_test_result_unreadable:{exc}")

    symbol_rows = read_jsonl(lane07.OUTPUTS["symbol_spec"])
    broker_truth_rows = read_jsonl(lane07.OUTPUTS["broker_truth"])
    cost_rows = read_jsonl(lane07.OUTPUTS["cost_calibration"])
    gap_rows = read_jsonl(lane07.OUTPUTS["source_gap"])
    source_rows = read_jsonl(lane07.OUTPUTS["source_coverage"])
    dep_rows = read_jsonl(lane07.OUTPUTS["dependency_state"])
    downstream = read_json(lane07.OUTPUTS["downstream_contract"], {})
    boundary = read_json(lane07.OUTPUTS["runtime_effect_boundary"], {})

    symbols = {row.get("symbol") for row in symbol_rows}
    missing_symbols = sorted(set(lane07.ACTIVE_SYMBOLS) - symbols)
    extra_symbols = sorted(symbols - set(lane07.ACTIVE_SYMBOLS))
    if len(symbol_rows) != len(lane07.ACTIVE_SYMBOLS) or missing_symbols or extra_symbols:
        issues.append(f"symbol_coverage_invalid:rows={len(symbol_rows)} missing={missing_symbols} extra={extra_symbols}")

    spread_symbols = {
        row.get("symbol")
        for row in cost_rows
        if row.get("row_type") == "symbol_spread_snapshot_cost_proxy"
    }
    if spread_symbols != set(lane07.ACTIVE_SYMBOLS):
        issues.append(f"spread_snapshot_symbols_invalid:missing={sorted(set(lane07.ACTIVE_SYMBOLS)-spread_symbols)}")

    row_types = {row.get("row_type") for row in broker_truth_rows}
    for expected in {
        "mt5_account_snapshot",
        "mt5_history_order",
        "mt5_history_deal",
        "mt5_open_position",
        "lane06_lifecycle_reconciliation",
        "lane06_projected_vs_broker_reconciliation",
        "lane06_manual_intervention",
    }:
        if expected not in row_types:
            issues.append(f"missing_broker_truth_row_type:{expected}")

    if not any(
        row.get("row_type") == "mt5_history_order"
        and (row.get("raw") or {}).get("comment") == "preflight_test"
        for row in broker_truth_rows
    ):
        issues.append("missing_non_vnext_preflight_history_order_classification")

    if not any(
        row.get("row_type") == "lane06_projected_vs_broker_reconciliation"
        and (row.get("raw") or {}).get("reconciliation_status")
        == "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
        for row in broker_truth_rows
    ):
        issues.append("missing_false_close_broker_contradiction_truth")

    cost_types = {row.get("row_type") for row in cost_rows}
    for expected in {
        "broker_real_trade_cost",
        "runtime_slippage_spread_event",
        "symbol_spread_snapshot_cost_proxy",
        "symbol_commission_swap_observation",
    }:
        if expected not in cost_types:
            issues.append(f"missing_cost_row_type:{expected}")

    broker_real_cost_rows = [row for row in cost_rows if row.get("row_type") == "broker_real_trade_cost"]
    if len(broker_real_cost_rows) < 8:
        issues.append(f"broker_real_trade_cost_rows_too_low:{len(broker_real_cost_rows)}")

    if not any(
        row.get("row_type") == "symbol_commission_swap_observation"
        and row.get("symbol") == "XAUUSD"
        and row.get("entry_commission_per_lot_observed") is not None
        for row in cost_rows
    ):
        issues.append("missing_xauusd_observed_commission_calibration")

    if not any(
        row.get("symbol") == "NAS100"
        and row.get("row_type") == "symbol_commission_swap_observation"
        for row in cost_rows
    ):
        issues.append("missing_nas100_commission_swap_observation")

    session_gap_symbols = {
        row.get("symbol")
        for row in gap_rows
        if row.get("field") == "broker_trading_sessions_by_weekday"
    }
    if session_gap_symbols != set(lane07.ACTIVE_SYMBOLS):
        issues.append(
            "session_gap_coverage_invalid:"
            f"missing={sorted(set(lane07.ACTIVE_SYMBOLS)-session_gap_symbols)}"
        )

    if not any(
        row.get("field") == "current_workstation_mt5_server_access"
        and "NOT_EXECUTED" in str(row.get("status"))
        for row in gap_rows
    ):
        issues.append("missing_current_workstation_mt5_server_access_boundary_gap")

    nonblocking_downstream_deps = {
        row.get("dependency"): row
        for row in dep_rows
        if row.get("expected_present_for_lane07_completion") is False
        and row.get("blocking_downstream") is False
        and "not_blocking" in str(row.get("disposition"))
    }
    for dep in {
        "moonshot_lane05_feature_store_v1",
        "moonshot_lane06_label_store_v1",
        "moonshot_lane08_digital_twin_replay_engine",
    }:
        row = nonblocking_downstream_deps.get(dep)
        if not row:
            issues.append(f"missing_nonblocking_downstream_dependency_row:{dep}")
        elif row.get("status") not in {"absent", "present_incomplete", "present_complete"}:
            issues.append(f"invalid_downstream_dependency_status:{dep}:{row.get('status')}")

    consumers = set((downstream.get("consumers") or {}).keys())
    expected_consumers = {
        "feature_store",
        "label_store",
        "digital_twin_replay",
        "scheduler",
        "execution_policy",
        "command_center",
        "telegram_truth",
    }
    if not expected_consumers.issubset(consumers):
        issues.append(f"missing_downstream_consumers:{sorted(expected_consumers-consumers)}")

    forbidden = boundary.get("forbidden_surface_attestation") or {}
    if any(bool(value) for value in forbidden.values()):
        issues.append("runtime_effect_boundary_contains_forbidden_surface_true")

    if len(source_rows) < 30:
        issues.append(f"source_coverage_rows_too_low:{len(source_rows)}")

    result = {
        "schema_version": "lane07_verification_result_v1",
        "route_id": lane07.ROUTE_ID,
        "generated_at_utc": now_iso(),
        "ok": not issues,
        "issues": issues,
        "counts": {
            "symbol_rows": len(symbol_rows),
            "broker_truth_rows": len(broker_truth_rows),
            "cost_rows": len(cost_rows),
            "gap_rows": len(gap_rows),
            "source_coverage_rows": len(source_rows),
            "dependency_rows": len(dep_rows),
        },
    }
    write_json(lane07.OUTPUTS["verification"], result)

    audit = read_json(lane07.OUTPUTS["completion_audit"], {})
    if audit:
        audit["verification"] = result
        for req in audit.get("requirements") or []:
            if req.get("requirement") == "verifier_and_focused_tests":
                req["status"] = "complete" if result["ok"] else "verification_failed"
                req["evidence"] = [
                    lane07.rel(lane07.OUTPUTS["verification"]),
                    lane07.rel(lane07.OUTPUTS["focused_test_result"]),
                ]
            if req.get("requirement") == "scoped_commit":
                req["status"] = "pending_after_verification"
        write_json(lane07.OUTPUTS["completion_audit"], audit)
    lane07.write_manifest(now_iso())
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route()
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
