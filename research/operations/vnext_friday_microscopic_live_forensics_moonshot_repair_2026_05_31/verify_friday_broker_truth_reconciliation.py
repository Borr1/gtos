from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
LEDGER = ROUTE_DIR / "FRIDAY_PLACED_TRADE_AUTOPSY_LEDGER.jsonl"
SUMMARY = ROUTE_DIR / "FRIDAY_CANONICAL_EVENT_SUMMARY.json"
EXPECTED_ROWS = 8


def main() -> int:
    issues = []
    rows = 0
    if not LEDGER.exists() or LEDGER.stat().st_size <= 0:
        issues.append({"code": "missing_or_empty_ledger", "path": str(LEDGER)})
    else:
        with LEDGER.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows += 1
                    json.loads(line)
    if rows != EXPECTED_ROWS:
        issues.append({"code": "row_count_mismatch", "expected": EXPECTED_ROWS, "actual": rows})
    if not SUMMARY.exists() or SUMMARY.stat().st_size <= 0:
        issues.append({"code": "missing_or_empty_summary", "path": str(SUMMARY)})
    else:
        json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = {"ok": not issues, "issues": issues, "rows": rows}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
