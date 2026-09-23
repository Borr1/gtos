"""Verify strategy registry metadata refresh after tick structural source repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_SUMMARY_2026-05-17.json"
MANIFEST = ROUTE_DIR / "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_OUTPUT_MANIFEST_2026-05-17.json"
RESULT = ROUTE_DIR / "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_VERIFICATION_RESULT_2026-05-17.json"
INPUT_TICK_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_SUMMARY_2026-05-17.json"

EXPECTED_STRATEGIES = {
    "V2_STRUCT_SWING_PROTECTED": {
        "rows": 190,
        "numeric_proxy_rows": 87,
        "proxy_r_sum": 36.5,
        "action_counts": {"IMPLEMENT_DEFAULT_OFF": 115, "KILL": 75},
    },
    "V2_STRUCT_FVG_MID_EDGE": {
        "rows": 3,
        "numeric_proxy_rows": 1,
        "proxy_r_sum": -1.0,
        "action_counts": {"IMPLEMENT_DEFAULT_OFF": 3},
    },
    "V3_FVG_ONLY_RESCUE_RISK_BANK": {
        "rows": 3,
        "numeric_proxy_rows": 1,
        "proxy_r_sum": -1.0,
        "action_counts": {"IMPLEMENT_DEFAULT_OFF": 3},
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no} invalid JSONL: {exc}") from exc
            rows.append(row)
    return rows


def close_enough(left: Any, right: float, tolerance: float = 1e-8) -> bool:
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return False


def main() -> None:
    failures: list[str] = []
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    tick_summary = read_json(INPUT_TICK_SUMMARY)
    rows = read_jsonl(LEDGER)
    by_strategy = {row.get("strategy_id"): row for row in rows}

    if summary.get("rows") != len(EXPECTED_STRATEGIES):
        failures.append(f"summary rows expected {len(EXPECTED_STRATEGIES)}, got {summary.get('rows')}")
    if len(rows) != len(EXPECTED_STRATEGIES):
        failures.append(f"ledger rows expected {len(EXPECTED_STRATEGIES)}, got {len(rows)}")
    if summary.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("strategy registry metadata still has stale source-repair tokens")
    if summary.get("metadata_refresh_proxy_row_delta") != 0:
        failures.append("metadata refresh unexpectedly changed proxy row count")
    if summary.get("metadata_refresh_proxy_r_sum_delta") != 0.0:
        failures.append("metadata refresh unexpectedly changed proxy R sum")
    if summary.get("exact_r_rows") != 0:
        failures.append("metadata refresh opened exact-R rows")
    if summary.get("tick_source_repair_rows_before") != tick_summary.get("target_rows_before"):
        failures.append("tick source-repair before count does not match input tick summary")
    if summary.get("tick_source_repair_rows_after") != 0:
        failures.append("tick source-repair after count is not zero")

    for strategy_id, expected in EXPECTED_STRATEGIES.items():
        row = by_strategy.get(strategy_id)
        if not row:
            failures.append(f"missing strategy row {strategy_id}")
            continue
        if row.get("stale_metadata_tokens"):
            failures.append(f"{strategy_id} has stale metadata tokens {row.get('stale_metadata_tokens')}")
        if "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR" not in str(row.get("decision_evidence") or ""):
            failures.append(f"{strategy_id} decision evidence does not cite tick structural repair")
        if row.get("current_target_rows") != expected["rows"]:
            failures.append(
                f"{strategy_id} rows expected {expected['rows']}, got {row.get('current_target_rows')}"
            )
        if row.get("current_numeric_proxy_rows") != expected["numeric_proxy_rows"]:
            failures.append(
                f"{strategy_id} numeric rows expected {expected['numeric_proxy_rows']}, got {row.get('current_numeric_proxy_rows')}"
            )
        if not close_enough(row.get("current_proxy_r_sum"), expected["proxy_r_sum"]):
            failures.append(
                f"{strategy_id} proxy sum expected {expected['proxy_r_sum']}, got {row.get('current_proxy_r_sum')}"
            )
        for action, count in expected["action_counts"].items():
            if row.get("current_action_counts", {}).get(action) != count:
                failures.append(
                    f"{strategy_id} action {action} expected {count}, got {row.get('current_action_counts', {}).get(action)}"
                )
        if row.get("exact_r_rows") != 0:
            failures.append(f"{strategy_id} opened exact-R rows")
        if row.get("safe_flags", {}).get("live_effect") is not False:
            failures.append(f"{strategy_id} live_effect safe flag changed")

    manifest_counts = manifest.get("summary_counts", {})
    if manifest_counts.get("rows") != summary.get("rows"):
        failures.append("manifest row count does not match summary")
    if manifest_counts.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("manifest stale-token count is nonzero")
    for name, payload in manifest.get("inputs", {}).items():
        if not payload.get("exists"):
            failures.append(f"manifest input missing: {name}")
    for name, payload in manifest.get("outputs", {}).items():
        path = Path(payload.get("path", ""))
        if not path.exists():
            failures.append(f"manifest output missing: {name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "rows": len(rows),
        "metadata_rows_with_stale_tokens": summary.get("metadata_rows_with_stale_tokens"),
        "tick_source_repair_rows_after": summary.get("tick_source_repair_rows_after"),
        "metadata_refresh_proxy_row_delta": summary.get("metadata_refresh_proxy_row_delta"),
        "metadata_refresh_proxy_r_sum_delta": summary.get("metadata_refresh_proxy_r_sum_delta"),
        "exact_r_rows": summary.get("exact_r_rows"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
