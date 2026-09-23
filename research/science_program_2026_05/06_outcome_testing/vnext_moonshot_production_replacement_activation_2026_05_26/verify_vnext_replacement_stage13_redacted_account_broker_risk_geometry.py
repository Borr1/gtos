from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_redacted_account_broker_risk_geometry_verifier"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]

BROKER_ONBOARDING_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_LEDGER_{DATE}.jsonl"
REPAIRED_BRANCH_ALLOWLIST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_REPAIRED_BRANCH_ALLOWLIST_{DATE}.json"
BROADER_ORIGIN_ALLOWLIST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"

BROKER_SPEC_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_SPEC_LEDGER_{DATE}.jsonl"
EFFECTIVE_CONFIG_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_EFFECTIVE_CONFIG_LEDGER_{DATE}.jsonl"
SELECTED_CELL_RISK_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_{DATE}.json"
OUTPUT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_VERIFIER_{DATE}.json"

REQUIRED_BROKER_FIELDS = (
    "digits",
    "spread",
    "trade_tick_size",
    "trade_tick_value",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "trade_contract_size",
    "volume_min",
    "volume_step",
    "volume_max",
    "trade_stops_level",
    "trade_freeze_level",
    "point",
    "trade_exemode",
    "filling_mode",
    "order_mode",
    "trade_calc_mode",
    "expiration_mode",
)

EXECUTION_CRITICAL_UNRESOLVED_PREFIXES = (
    "digits_",
    "filling_mode_",
    "order_mode_",
    "price_rounding_",
    "lot_rounding_",
    "spread_p95_",
)

EXECUTION_CRITICAL_UNRESOLVED_EXACT = {
    "eligible_symbol_has_missing_broker_geometry_field_no_default_substitution_allowed",
    "old_three_repaired_branch_allowlist_side_not_dimensioned",
    "selected_cell_sl_distance_distribution_missing_or_incomplete",
}


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def positive_number(value: Any) -> bool:
    try:
        return value is not None and float(value) > 0.0
    except (TypeError, ValueError):
        return False


def field_present(row: dict[str, Any], field: str) -> bool:
    return field in row and row.get(field) is not None


def required_geometry_failures(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in REQUIRED_BROKER_FIELDS:
        if not field_present(row, field):
            failures.append(f"missing_{field}")
    for field in ("trade_tick_size", "trade_tick_value", "trade_contract_size", "volume_min", "volume_step", "volume_max", "point"):
        if field_present(row, field) and not positive_number(row.get(field)):
            failures.append(f"nonpositive_{field}")
    return failures


def execution_critical_unresolved(reasons: list[str]) -> list[str]:
    critical: list[str] = []
    for reason in reasons:
        if reason in EXECUTION_CRITICAL_UNRESOLVED_EXACT:
            critical.append(reason)
            continue
        if any(reason.startswith(prefix) for prefix in EXECUTION_CRITICAL_UNRESOLVED_PREFIXES):
            critical.append(reason)
    return sorted(set(critical))


def metric_positive(metrics: dict[str, Any]) -> bool:
    rows = int(metrics.get("performance_rows") or metrics.get("selected_count") or 0)
    return rows > 0 and positive_number(metrics.get("expectancy_r")) and positive_number(metrics.get("profit_factor"))


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []

    source_broker_rows = iter_jsonl(BROKER_ONBOARDING_LEDGER)
    repaired_allowlist = read_json(REPAIRED_BRANCH_ALLOWLIST)
    broader_allowlist = read_json(BROADER_ORIGIN_ALLOWLIST)
    broker_rows = iter_jsonl(BROKER_SPEC_LEDGER)
    config_rows = iter_jsonl(EFFECTIVE_CONFIG_LEDGER)
    risk_rows = iter_jsonl(SELECTED_CELL_RISK_LEDGER)
    summary = read_json(SUMMARY_PATH)

    for path, rows in (
        (BROKER_SPEC_LEDGER, broker_rows),
        (EFFECTIVE_CONFIG_LEDGER, config_rows),
        (SELECTED_CELL_RISK_LEDGER, risk_rows),
    ):
        if not rows:
            failures.append(f"missing_or_empty_output_ledger:{rel(path)}")
    if not summary:
        failures.append(f"missing_summary:{rel(SUMMARY_PATH)}")

    broker_by_symbol = {row.get("symbol"): row for row in broker_rows}
    config_by_symbol = {row.get("symbol"): row for row in config_rows}
    if len(broker_by_symbol) != len(broker_rows):
        failures.append("duplicate_symbol_in_broker_spec_ledger")
    if len(config_by_symbol) != len(config_rows):
        failures.append("duplicate_symbol_in_effective_config_ledger")

    expected_broker_rows = len(source_broker_rows)
    if broker_rows and len(broker_rows) != expected_broker_rows:
        failures.append(f"broker_spec_row_count_mismatch:{len(broker_rows)}!={expected_broker_rows}")
    if config_rows and len(config_rows) != len(broker_rows):
        failures.append(f"effective_config_row_count_mismatch:{len(config_rows)}!={len(broker_rows)}")

    expected_risk_rows = len(repaired_allowlist.get("entries") or []) + len(broader_allowlist.get("entries") or [])
    if risk_rows and len(risk_rows) != expected_risk_rows:
        failures.append(f"selected_cell_risk_row_count_mismatch:{len(risk_rows)}!={expected_risk_rows}")

    for rel_path, expected_hash in (summary.get("output_hashes") or {}).items():
        actual_hash = file_sha256(REPO_ROOT / rel_path)
        if expected_hash != actual_hash:
            failures.append(f"summary_output_hash_mismatch:{rel_path}:{actual_hash}!={expected_hash}")

    row_counts = summary.get("row_counts") or {}
    if row_counts:
        if row_counts.get("broker_spec_rows") != len(broker_rows):
            failures.append("summary_broker_spec_row_count_mismatch")
        if row_counts.get("effective_config_rows") != len(config_rows):
            failures.append("summary_effective_config_row_count_mismatch")
        if row_counts.get("selected_cell_risk_rows") != len(risk_rows):
            failures.append("summary_selected_cell_risk_row_count_mismatch")

    if "risk_rows_by_profile_risk_pct" in summary:
        failures.append("summary_has_ambiguous_profile_risk_count_field")
    configured_profile_counts = dict(
        Counter(str(row.get("configured_profile_risk_per_trade_pct")) for row in risk_rows)
    )
    effective_selected_cell_counts = dict(
        Counter(str(row.get("effective_risk_per_trade_pct")) for row in risk_rows)
    )
    if summary.get("risk_rows_by_configured_profile_risk_pct") != configured_profile_counts:
        failures.append("summary_configured_profile_risk_count_mismatch")
    if summary.get("risk_rows_by_effective_selected_cell_risk_pct") != effective_selected_cell_counts:
        failures.append("summary_effective_selected_cell_risk_count_mismatch")

    for symbol, row in broker_by_symbol.items():
        eligible = bool(row.get("eligible_for_vnext_activation"))
        unresolved = row.get("exact_unresolved_reasons") or []
        excluded = row.get("exact_excluded_reasons") or []
        if row.get("broker_field_default_used"):
            failures.append(f"broker_spec_uses_unverified_default:{symbol}")
        if eligible:
            if not row.get("broker_alias"):
                failures.append(f"eligible_broker_spec_missing_alias:{symbol}")
            if row.get("symbol_info_available") is not True:
                failures.append(f"eligible_broker_spec_symbol_info_unavailable:{symbol}")
            for issue in required_geometry_failures(row):
                failures.append(f"eligible_broker_spec_geometry_gap:{symbol}:{issue}")
        else:
            if not excluded:
                failures.append(f"excluded_broker_spec_missing_exact_reason:{symbol}")
        if unresolved:
            for reason in unresolved:
                if not isinstance(reason, str) or not reason:
                    failures.append(f"broker_spec_blank_unresolved_reason:{symbol}")

    for symbol, row in config_by_symbol.items():
        broker = broker_by_symbol.get(symbol)
        if not broker:
            failures.append(f"effective_config_missing_broker_spec_join:{symbol}")
            continue
        if broker.get("eligible_for_vnext_activation"):
            if row.get("uses_unverified_default"):
                failures.append(f"eligible_effective_config_uses_unverified_default:{symbol}")
            if not positive_number(row.get("effective_risk_per_trade_pct")):
                failures.append(f"eligible_effective_config_nonpositive_risk:{symbol}")
            if not positive_number(row.get("effective_price_rounding_increment")):
                failures.append(f"eligible_effective_config_missing_price_rounding:{symbol}")
            if not positive_number(row.get("effective_lot_rounding_step")):
                failures.append(f"eligible_effective_config_missing_lot_rounding:{symbol}")
            if row.get("required_broker_geometry_missing"):
                failures.append(f"eligible_effective_config_missing_broker_geometry:{symbol}")
        if row.get("uses_unverified_default") and not row.get("exact_unresolved_reasons"):
            failures.append(f"effective_config_unverified_default_without_exact_reason:{symbol}")

    risk_positive_count = 0
    for row in risk_rows:
        risk_pct = float(row.get("effective_risk_per_trade_pct") or 0.0)
        symbol = row.get("symbol")
        cell_id = row.get("risk_cell_id")
        broker = broker_by_symbol.get(symbol)
        config = config_by_symbol.get(symbol)
        reasons = row.get("exact_unresolved_or_excluded_reasons") or []
        metrics = row.get("metrics") or {}

        if not broker:
            failures.append(f"selected_cell_missing_broker_spec_row:{cell_id}:{symbol}")
        if not config:
            failures.append(f"selected_cell_missing_effective_config_row:{cell_id}:{symbol}")
        if row.get("uses_unverified_default"):
            failures.append(f"selected_cell_uses_unverified_default:{cell_id}:{symbol}")
        if row.get("stale_old_profile_risk_without_cell_evidence"):
            failures.append(f"selected_cell_stale_old_profile_risk_without_cell_evidence:{cell_id}:{symbol}")
        if risk_pct > 0:
            risk_positive_count += 1
            critical = execution_critical_unresolved([str(reason) for reason in reasons])
            if critical:
                failures.append(f"risk_positive_cell_with_execution_critical_unresolved_evidence:{cell_id}:{symbol}:{'|'.join(critical)}")
            if not broker or not broker.get("eligible_for_vnext_activation"):
                failures.append(f"risk_positive_cell_without_eligible_broker_spec:{cell_id}:{symbol}")
            if not row.get("broker_alias"):
                failures.append(f"risk_positive_cell_missing_alias:{cell_id}:{symbol}")
            if broker:
                for issue in required_geometry_failures(broker):
                    failures.append(f"risk_positive_cell_missing_broker_geometry:{cell_id}:{symbol}:{issue}")
            if not metric_positive(metrics):
                failures.append(f"risk_positive_cell_nonpositive_expectancy_or_pf:{cell_id}:{symbol}")
            if row.get("selector_cell_metrics_status") != "positive_selector_cell_metrics":
                failures.append(f"risk_positive_cell_missing_positive_selector_evidence:{cell_id}:{symbol}")
            if not positive_number(row.get("effective_price_rounding_increment")):
                failures.append(f"risk_positive_cell_missing_price_rounding:{cell_id}:{symbol}")
            if not positive_number(row.get("effective_lot_rounding_step")):
                failures.append(f"risk_positive_cell_missing_lot_rounding:{cell_id}:{symbol}")
            if not row.get("sl_distance_distribution"):
                failures.append(f"risk_positive_cell_missing_sl_distance_distribution:{cell_id}:{symbol}")
            if not (row.get("spread_slippage_sensitivity") or {}).get("spread_to_sl_p50_ratio") and (row.get("spread_slippage_sensitivity") or {}).get("spread_to_sl_p50_ratio") != 0:
                failures.append(f"risk_positive_cell_missing_spread_slippage_sensitivity:{cell_id}:{symbol}")
            if "vnext_cell_evidence_tier" not in str(row.get("risk_decision_basis") or ""):
                failures.append(f"risk_positive_cell_not_evidence_tier_derived:{cell_id}:{symbol}")
            if row.get("configured_profile_risk_per_trade_pct") == row.get("effective_risk_per_trade_pct") and row.get("stale_old_profile_risk_without_cell_evidence"):
                failures.append(f"risk_positive_cell_inherited_profile_risk:{cell_id}:{symbol}")
        else:
            if not reasons:
                failures.append(f"risk_zero_cell_without_exact_unresolved_or_excluded_reason:{cell_id}:{symbol}")
        if row.get("nonpositive_expectancy_or_pf_for_risk_gt_zero"):
            failures.append(f"risk_positive_cell_flagged_nonpositive_expectancy_or_pf:{cell_id}:{symbol}")
        if (
            (row.get("uses_unverified_default") or row.get("stale_old_profile_risk_without_cell_evidence"))
            and not reasons
        ):
            failures.append(f"selected_cell_flag_without_exact_reason:{cell_id}:{symbol}")

    selector_component_counts = Counter(row.get("selector_component") for row in risk_rows)
    if selector_component_counts.get("old_three_repaired_branch", 0) != len(repaired_allowlist.get("entries") or []):
        failures.append("old_three_repaired_branch_risk_count_mismatch")
    if selector_component_counts.get("broader_origin", 0) != len(broader_allowlist.get("entries") or []):
        failures.append("broader_origin_risk_count_mismatch")

    result = {
        "schema_version": "vnext_replacement_stage13_redacted_account_broker_risk_geometry_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "deterministic_verifier": False,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "checked_files": {
            "broker_spec_ledger": rel(BROKER_SPEC_LEDGER),
            "effective_config_ledger": rel(EFFECTIVE_CONFIG_LEDGER),
            "selected_cell_risk_ledger": rel(SELECTED_CELL_RISK_LEDGER),
            "summary": rel(SUMMARY_PATH),
            "source_broker_onboarding_ledger": rel(BROKER_ONBOARDING_LEDGER),
            "source_broader_origin_allowlist": rel(BROADER_ORIGIN_ALLOWLIST),
            "source_repaired_branch_allowlist": rel(REPAIRED_BRANCH_ALLOWLIST),
        },
        "output_hashes": {
            rel(BROKER_SPEC_LEDGER): file_sha256(BROKER_SPEC_LEDGER),
            rel(EFFECTIVE_CONFIG_LEDGER): file_sha256(EFFECTIVE_CONFIG_LEDGER),
            rel(SELECTED_CELL_RISK_LEDGER): file_sha256(SELECTED_CELL_RISK_LEDGER),
            rel(SUMMARY_PATH): file_sha256(SUMMARY_PATH),
        },
        "row_counts": {
            "source_broker_onboarding_rows": len(source_broker_rows),
            "broker_spec_rows": len(broker_rows),
            "effective_config_rows": len(config_rows),
            "selected_cell_risk_rows": len(risk_rows),
            "selected_cell_risk_positive_rows": risk_positive_count,
        },
        "broker_contract_status_counts": dict(Counter(row.get("broker_contract_status") for row in broker_rows)),
        "selector_component_counts": dict(selector_component_counts),
        "risk_rows_by_configured_profile_risk_pct": configured_profile_counts,
        "risk_rows_by_effective_selected_cell_risk_pct": effective_selected_cell_counts,
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
