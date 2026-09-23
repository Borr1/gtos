from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
SELECTED = ROUTE_DIR / "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_LEDGER.jsonl"
BROKER = ROUTE_DIR / "FRIDAY_EXECUTION_POLICY_BROKER_READY_LEDGER.jsonl"
TRAILING = ROUTE_DIR / "FRIDAY_REAL_TRAILING_SIMULATION_LEDGER.jsonl"
SUMMARY = ROUTE_DIR / "FRIDAY_POLICY_ROUTER_REDESIGN_SUMMARY.json"
EXPECTED_SELECTED = 328 * 18
EXPECTED_BROKER = 9 * 18


def count(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip()) if path.exists() else 0


def main() -> int:
    issues = []
    selected_rows = count(SELECTED)
    broker_rows = count(BROKER)
    trailing_rows = count(TRAILING)
    if selected_rows != EXPECTED_SELECTED:
        issues.append({"code": "selected_policy_row_count_mismatch", "expected": EXPECTED_SELECTED, "actual": selected_rows})
    if broker_rows != EXPECTED_BROKER:
        issues.append({"code": "broker_ready_policy_row_count_mismatch", "expected": EXPECTED_BROKER, "actual": broker_rows})
    if trailing_rows <= 0:
        issues.append({"code": "missing_trailing_rows"})
    if not SUMMARY.exists() or SUMMARY.stat().st_size <= 0:
        issues.append({"code": "missing_policy_summary"})
    else:
        json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = {"ok": not issues, "issues": issues, "selected_rows": selected_rows, "broker_rows": broker_rows, "trailing_rows": trailing_rows}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
