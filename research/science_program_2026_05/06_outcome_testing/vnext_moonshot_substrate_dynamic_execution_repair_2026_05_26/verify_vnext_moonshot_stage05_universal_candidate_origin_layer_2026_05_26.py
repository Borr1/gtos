from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

REGISTRY = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE_ID}.jsonl"
BOXING = ROUTE_DIR / f"VNEXT_MOONSHOT_CANDIDATE_ORIGIN_BOXING_AUDIT_LEDGER_{DATE_ID}.jsonl"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_SUMMARY_{DATE_ID}.json"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REPORT_{DATE_ID}.md"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE05_VERIFICATION_RESULT_{DATE_ID}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    failures = []
    registry_rows = load_jsonl(REGISTRY) if REGISTRY.exists() else []
    boxing_rows = load_jsonl(BOXING) if BOXING.exists() else []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    names = {row.get("name") for row in registry_rows}
    categories = {row.get("category") for row in registry_rows}
    required_names = {
        "ob_retest",
        "fvg_fill",
        "breaker_re_entry",
        "liquidity_sweep_reclaim",
        "continuation_no_retrace",
        "nofill_reprice_reentry",
        "orderflow_depth_imbalance_proxy",
        "news_volatility_reprice",
        "cross_asset_lead_lag",
        "path_hazard_early_failure",
    }
    missing_names = sorted(required_names - names)
    if missing_names:
        failures.append(f"missing origin families: {missing_names}")
    if len(registry_rows) < 15:
        failures.append(f"registry too small: {len(registry_rows)}")
    if len(boxing_rows) <= len(registry_rows):
        failures.append("boxing audit should include current behavior plus registry rows")
    if "current_gtos_framework" not in categories:
        failures.append("current baseline frameworks missing")
    if len(categories) < 8:
        failures.append(f"too few non-boxed categories: {len(categories)}")
    if any(not row.get("default_off") for row in registry_rows):
        failures.append("registry contains a non-default-off row")
    if summary.get("first_incomplete_invariant_after_stage05") != "STAGE_06_MARKET_AWARENESS_ENRICHMENT":
        failures.append("summary did not advance to Stage06")
    if state.get("first_incomplete_invariant") != "STAGE_06_MARKET_AWARENESS_ENRICHMENT":
        failures.append("state did not advance to Stage06")
    if not REPORT.exists() or REPORT.stat().st_size < 300:
        failures.append("Stage05 report missing or too small")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "origin_registry_rows": len(registry_rows),
        "boxing_audit_rows": len(boxing_rows),
        "registered_categories": sorted(categories),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
