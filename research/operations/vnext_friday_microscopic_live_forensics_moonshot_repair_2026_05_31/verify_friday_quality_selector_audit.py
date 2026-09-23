from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
LEDGER = ROUTE_DIR / "FRIDAY_QUALITY_SELECTOR_AUDIT_LEDGER.jsonl"
SUMMARY = ROUTE_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"
MECHANISMS = ROUTE_DIR / "FRIDAY_MOONSHOT_MECHANISM_EXPANSION_LEDGER.jsonl"
SPEC = ROUTE_DIR / "FRIDAY_META_SELECTOR_CANDIDATE_SPEC.md"
EXPECTED_ROWS = 328


def count(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip()) if path.exists() else 0


def main() -> int:
    issues = []
    rows = count(LEDGER)
    if rows != EXPECTED_ROWS:
        issues.append({"code": "quality_row_count_mismatch", "expected": EXPECTED_ROWS, "actual": rows})
    if count(MECHANISMS) <= 0:
        issues.append({"code": "missing_mechanism_rows"})
    if not SPEC.exists() or SPEC.stat().st_size <= 0:
        issues.append({"code": "missing_meta_selector_spec"})
    if not SUMMARY.exists() or SUMMARY.stat().st_size <= 0:
        issues.append({"code": "missing_quality_summary"})
    else:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        if summary.get("broad_selected_replay", {}).get("selected_rows_scanned") != 289600:
            issues.append({"code": "broad_selected_row_count_mismatch", "actual": summary.get("broad_selected_replay", {}).get("selected_rows_scanned")})
        if "weekend" in str(summary.get("config", {}).get("evidence_path", "")).lower():
            issues.append({"code": "config_still_points_to_weekend_selector_evidence"})
    result = {"ok": not issues, "issues": issues, "rows": rows, "mechanism_rows": count(MECHANISMS)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
