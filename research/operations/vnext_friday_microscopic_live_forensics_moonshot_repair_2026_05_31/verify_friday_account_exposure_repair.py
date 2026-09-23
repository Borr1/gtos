"""Verify Friday Stage10 account-exposure repair artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUTE = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
ACCOUNT = ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_LEDGER.jsonl"
PROP = ROUTE / "FRIDAY_PROP_DEFERRAL_REPAIR_LEDGER.jsonl"
AUDIT = ROUTE / "FRIDAY_CONCURRENCY_CAP_STALENESS_AUDIT.json"
SUMMARY = ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_SUMMARY.json"
OUT = ROUTE / "FRIDAY_ACCOUNT_EXPOSURE_RISK_VERIFICATION.json"


def count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def rows(path: Path):
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def main() -> int:
    issues = []
    account_rows = count(ACCOUNT)
    prop_rows = count(PROP)
    if account_rows != 328:
        issues.append({"code": "account_ledger_row_count_mismatch", "expected": 328, "actual": account_rows})
    if prop_rows != 45:
        issues.append({"code": "prop_repair_row_count_mismatch", "expected": 45, "actual": prop_rows})
    if not AUDIT.exists():
        issues.append({"code": "missing_concurrency_audit"})
        audit = {}
    else:
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if not SUMMARY.exists():
        issues.append({"code": "missing_account_summary"})
        summary = {}
    else:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    unexplained = [row.get("trade_id") for row in rows(PROP) if not row.get("deferral_explained")]
    if unexplained:
        issues.append({"code": "unexplained_prop_deferrals", "trade_ids": unexplained[:20], "count": len(unexplained)})
    unrepaired = [
        row.get("trade_id")
        for row in rows(PROP)
        if row.get("current_code_repair_status") != "repaired_projection_only_before_dynamic_then_terminal_after_geometry"
    ]
    if unrepaired:
        issues.append({"code": "prop_deferral_repair_status_unexpected", "trade_ids": unrepaired[:20], "count": len(unrepaired)})
    if int(audit.get("count_or_concurrency_refusal_rows") or 0) != 0:
        issues.append({"code": "unexpected_count_or_concurrency_refusals", "count": audit.get("count_or_concurrency_refusal_rows")})
    if int(summary.get("prop_deferrals_explained") or 0) != 45:
        issues.append({"code": "summary_prop_deferrals_not_all_explained", "actual": summary.get("prop_deferrals_explained")})
    result = {
        "schema_version": "friday_account_exposure_risk_verification_v1",
        "ok": not issues,
        "issues": issues,
        "account_rows": account_rows,
        "prop_repair_rows": prop_rows,
        "count_or_concurrency_refusal_rows": audit.get("count_or_concurrency_refusal_rows"),
        "prop_deferrals_explained": summary.get("prop_deferrals_explained"),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
