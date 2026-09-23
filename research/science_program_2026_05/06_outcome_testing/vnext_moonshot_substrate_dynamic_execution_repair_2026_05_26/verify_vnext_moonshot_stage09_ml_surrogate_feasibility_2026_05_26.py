from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

SPEC = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_LABEL_DATASET_SPEC_{DATE_ID}.md"
FEATURE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE_ID}.jsonl"
RESULTS = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_CHALLENGER_RESULTS_{DATE_ID}.json"
LEAKAGE_AUDIT = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_LEAKAGE_AUDIT_LEDGER_{DATE_ID}.jsonl"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE09_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_LABELS = {
    "label_dynamic_r_live_current",
    "label_dynamic_positive",
    "label_stop_first_risk",
    "label_no_fill_risk",
    "label_candidate_origin_family",
    "label_prop_attempt_success_proxy",
    "label_source_completeness",
    "label_ai_call_need",
    "label_execution_policy_recommendation",
}

FORBIDDEN_FEATURE_FIELDS = {
    "legacy_final_r",
    "live_current_j46_j49_final_r",
    "be_after_trigger_final_r",
    "trailing_runner_final_r",
    "mfe_r",
    "mae_r",
    "policy_results",
    "terminal_outcome",
    "pending_lifecycle_state",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
                if limit is not None and len(rows) >= limit:
                    break
    return rows


def count_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def main() -> None:
    failures: list[str] = []
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    sample_rows = load_jsonl(FEATURE_LEDGER, limit=1000) if FEATURE_LEDGER.exists() else []
    audit_rows = load_jsonl(LEAKAGE_AUDIT) if LEAKAGE_AUDIT.exists() else []
    feature_count = count_jsonl(FEATURE_LEDGER) if FEATURE_LEDGER.exists() else 0

    if not SPEC.exists() or SPEC.stat().st_size < 1000:
        failures.append("dataset spec missing or too small")
    if feature_count <= 0:
        failures.append("feature ledger has no rows")
    if results.get("feature_ledger_rows") != feature_count:
        failures.append("results feature_ledger_rows mismatch")
    if not sample_rows:
        failures.append("feature ledger sample missing")
    for row in sample_rows:
        missing = REQUIRED_LABELS - set(row)
        if missing:
            failures.append(f"feature row missing required labels: {sorted(missing)}")
            break
        feature_columns = set((row.get("feature_columns") or {}).keys())
        leaked = sorted(FORBIDDEN_FEATURE_FIELDS & feature_columns)
        if leaked:
            failures.append(f"forbidden outcome fields present in feature_columns: {leaked}")
            break
        if row.get("fixed_1_5r_used_as_activation_truth") is not False:
            failures.append("fixed 1.5R guard not false on feature row")
            break
    time_splits = Counter(row.get("split_time") for row in sample_rows)
    if not time_splits:
        failures.append("time split labels missing from feature ledger")
    audit_ids = {row.get("audit_id") for row in audit_rows}
    for required in {
        "feature_column_forbidden_field_scan",
        "split_counts",
        "feature_null_and_concentration",
        "label_distribution",
        "local_ml_tool_availability",
        "activation_truth_guard",
    }:
        if required not in audit_ids:
            failures.append(f"missing leakage audit row: {required}")
    forbidden_scan = next((row for row in audit_rows if row.get("audit_id") == "feature_column_forbidden_field_scan"), {})
    if forbidden_scan.get("status") != "pass":
        failures.append("forbidden feature scan did not pass")
    if results.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("paid API/vendor calls were made")
    if results.get("fixed_1_5r_used_as_activation_truth") is not False:
        failures.append("fixed 1.5R activation guard failed in results")
    if not results.get("ml_shadow_only_until_sealed_validation_and_owner_approval"):
        failures.append("ML shadow-only guard missing")
    if not results.get("dependency_free_baselines", {}).get("classification"):
        failures.append("dependency-free classification baselines missing")
    if not results.get("dependency_free_baselines", {}).get("regression"):
        failures.append("dependency-free regression baselines missing")
    if "sklearn" not in results.get("installed_local_ml_tools", {}):
        failures.append("local ML tool availability missing sklearn key")
    if not results.get("sklearn_challengers"):
        failures.append("sklearn challenger attempt not recorded")
    if not results.get("lightgbm_challengers"):
        failures.append("lightgbm challenger attempt not recorded")
    if state.get("first_incomplete_invariant") != "STAGE_10_DEFAULT_OFF_RUNTIME_INTEGRATION":
        failures.append("route state did not advance to Stage10")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "feature_rows": feature_count,
        "sample_time_split_counts": dict(sorted(time_splits.items())),
        "audit_rows": len(audit_rows),
        "dependency_free_classification_results": len(results.get("dependency_free_baselines", {}).get("classification", [])),
        "dependency_free_regression_results": len(results.get("dependency_free_baselines", {}).get("regression", [])),
        "sklearn_challenger_results": len(results.get("sklearn_challengers", [])),
        "lightgbm_challenger_results": len(results.get("lightgbm_challengers", [])),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
