from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
MICRO_LEDGER = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl"
WINNER_LEDGER = ROUTE_DIR / "FRIDAY_WINNER_ANATOMY_LEDGER.jsonl"
LOSER_LEDGER = ROUTE_DIR / "FRIDAY_LOSER_ANATOMY_LEDGER.jsonl"
STUCK_LEDGER = ROUTE_DIR / "FRIDAY_STUCK_CANDIDATE_LEDGER.jsonl"
MFE_MAE_LEDGER = ROUTE_DIR / "FRIDAY_MFE_MAE_TIMING_LEDGER.jsonl"
SUMMARY_MD = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_SUMMARY.md"
VERIFICATION = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_VERIFICATION.json"
EXPECTED_ROWS = 328
FRIDAY_CLOSE = "2026-05-29T21:00:00+00:00"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> int:
    issues = []
    required = [MICRO_LEDGER, WINNER_LEDGER, LOSER_LEDGER, STUCK_LEDGER, MFE_MAE_LEDGER, SUMMARY_MD, VERIFICATION]
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    rows = read_jsonl(MICRO_LEDGER) if MICRO_LEDGER.exists() else []
    mfe_rows = read_jsonl(MFE_MAE_LEDGER) if MFE_MAE_LEDGER.exists() else []
    if len(rows) != EXPECTED_ROWS:
        issues.append({"code": "micro_row_count_mismatch", "expected": EXPECTED_ROWS, "actual": len(rows)})
    if len(mfe_rows) != EXPECTED_ROWS:
        issues.append({"code": "mfe_mae_row_count_mismatch", "expected": EXPECTED_ROWS, "actual": len(mfe_rows)})
    if sum(1 for row in rows if row.get("price_source") == "tick_bid_ask") != EXPECTED_ROWS:
        issues.append({"code": "not_all_rows_tick_backed"})
    if any((row.get("price_source_last_utc") or "") >= FRIDAY_CLOSE for row in rows):
        issues.append({"code": "price_source_leaks_after_friday_close"})
    if any(not row.get("terminal_path_class") for row in rows):
        issues.append({"code": "missing_terminal_path_class"})
    if sum(1 for row in rows if row.get("actually_placed")) != 8:
        issues.append({"code": "placed_row_count_mismatch", "expected": 8, "actual": sum(1 for row in rows if row.get("actually_placed"))})
    if any(not all((row.get("mso_context_compact") or {}).get(tf, {}).get("available") for tf in ("D1", "H4", "H1", "M15")) for row in rows):
        issues.append({"code": "missing_mso_timeframe_context"})
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8")) if VERIFICATION.exists() else {}
    if verification and verification.get("ok") is not True:
        issues.append({"code": "stored_verification_not_ok", "issue_count": verification.get("issue_count")})
    result = {"ok": not issues, "issues": issues, "rows": len(rows), "mfe_mae_rows": len(mfe_rows)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
