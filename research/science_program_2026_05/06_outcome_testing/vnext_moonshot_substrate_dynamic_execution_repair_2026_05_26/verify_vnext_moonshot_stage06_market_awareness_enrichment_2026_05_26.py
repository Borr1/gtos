from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

FEATURES = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE_ID}.jsonl"
FIELDS = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FIELD_CLASSIFICATION_LEDGER_{DATE_ID}.jsonl"
DISTRIBUTIONS = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_DISTRIBUTION_LEDGER_{DATE_ID}.jsonl"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_SUMMARY_{DATE_ID}.json"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_REPORT_{DATE_ID}.md"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE06_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_FIELD_CLASSES = {
    "decision_safe_asof",
    "post_outcome_label",
    "diagnostic_only",
    "source_provenance",
    "missing",
    "forward_capture_required",
    "forbidden_leakage",
}

REQUIRED_FEATURES = {
    "trend_state_20",
    "volatility_state_14_vs_50",
    "compression_expansion_state",
    "session_subwindow",
    "kill_zone_position",
    "weekday",
    "month",
    "quarter",
    "news_calendar_coverage_status",
    "liquidity_sweep_proxy_state",
    "orderflow_depth_proxy_status",
    "cross_asset_lead_lag_status",
    "spread_slippage_cost_status",
    "transfer_group",
    "mfe_r",
    "mae_r",
    "adverse_excursion_bucket",
    "policy_reversal_bucket",
    "mfe_mae_timing_status",
    "live_current_j46_j49_final_r",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def scan_features() -> tuple[int, Counter, set[str], bool]:
    count = 0
    source_status = Counter()
    seen_keys: set[str] = set()
    leakage_used = False
    with FEATURES.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            seen_keys.update(row.keys())
            source_status[row.get("source_path_feature_status")] += 1
            leakage_used = leakage_used or bool(row.get("forbidden_leakage_fields_used"))
    return count, source_status, seen_keys, leakage_used


def main() -> None:
    failures = []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    field_rows = load_jsonl(FIELDS) if FIELDS.exists() else []
    distribution_rows = load_jsonl(DISTRIBUTIONS) if DISTRIBUTIONS.exists() else []
    feature_count, source_status, feature_keys, leakage_used = scan_features() if FEATURES.exists() else (0, Counter(), set(), False)
    field_classes = {row.get("field_safety_class") for row in field_rows}
    distribution_scopes = {row.get("coverage_scope") for row in distribution_rows}

    if feature_count != summary.get("expected_stage04_replayable_rows"):
        failures.append(f"feature rows do not match Stage04 replayable rows: {feature_count} != {summary.get('expected_stage04_replayable_rows')}")
    if feature_count != summary.get("feature_rows"):
        failures.append("summary feature_rows mismatch")
    missing_classes = sorted(REQUIRED_FIELD_CLASSES - field_classes)
    if missing_classes:
        failures.append(f"missing field safety classes: {missing_classes}")
    missing_features = sorted(REQUIRED_FEATURES - feature_keys)
    if missing_features:
        failures.append(f"missing required feature keys: {missing_features}")
    if not any(scope == "denominator_all_replayable_m15_dynamic_rows" for scope in distribution_scopes):
        failures.append("denominator-wide distribution scope missing")
    if not any(str(scope).startswith("selected_positive_live_current_j46_j49") for scope in distribution_scopes):
        failures.append("selected-only live_current_j46_j49 positive scope missing")
    if not any(str(scope).startswith("full_stage04_terminal_counts::") for scope in distribution_scopes):
        failures.append("full Stage04 terminal distribution scopes missing")
    if leakage_used or summary.get("forbidden_leakage_fields_used"):
        failures.append("forbidden leakage fields used")
    if summary.get("forbidden_boundaries_crossed"):
        failures.append("forbidden boundaries crossed")
    if state.get("first_incomplete_invariant") != "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV":
        failures.append("state did not advance to Stage07")
    if not REPORT.exists() or REPORT.stat().st_size < 500:
        failures.append("Stage06 report missing or too small")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "feature_rows": feature_count,
        "field_classification_rows": len(field_rows),
        "distribution_rows": len(distribution_rows),
        "field_safety_classes": sorted(field_classes),
        "source_path_feature_status_counts": dict(sorted(source_status.items())),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
