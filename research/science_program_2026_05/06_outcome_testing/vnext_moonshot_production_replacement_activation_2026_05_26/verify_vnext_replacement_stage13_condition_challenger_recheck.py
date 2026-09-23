from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_final_full_selector_condition_challenger_recheck_verifier"
EXPLICIT_24H_SESSION_SYMBOLS = {"BTCUSD", "ETHUSD"}
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

SUMMARY_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_SUMMARY_{DATE}.json"
)
LEDGER_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_LEDGER_{DATE}.jsonl"
)
BLOCKER_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_BLOCKER_LEDGER_{DATE}.jsonl"
)
CELL_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_CELL_LEDGER_{DATE}.jsonl"
)
FINAL_SELECTOR_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
)
FINAL_SELECTOR_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_LEDGER_{DATE}.jsonl"
)
BROADER_ALLOWLIST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
)
BROADER_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_{DATE}.json"
)
OUTPUT_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_VERIFIER_{DATE}.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_positive(metrics: dict[str, Any]) -> bool:
    return (
        int(metrics.get("performance_rows") or 0) > 0
        and metrics.get("expectancy_r") is not None
        and metrics.get("profit_factor") is not None
    )


def final_selector_activated_broader_groups() -> int:
    if not FINAL_SELECTOR_LEDGER.exists():
        return 0
    count = 0
    for row in iter_jsonl(FINAL_SELECTOR_LEDGER):
        if (
            row.get("row_type") == "broader_origin_group_decision"
            and row.get("final_action") == "activate_broader_origin_group"
        ):
            count += 1
    return count


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []

    missing = [
        path for path in (
            SUMMARY_PATH,
            LEDGER_PATH,
            BLOCKER_PATH,
            CELL_PATH,
            FINAL_SELECTOR_SUMMARY,
            FINAL_SELECTOR_LEDGER,
            BROADER_ALLOWLIST,
            BROADER_SUMMARY,
        )
        if not path.exists()
    ]
    if missing:
        failures.extend(f"missing_required_file:{rel(path)}" for path in missing)
        summary: dict[str, Any] = {}
        final_summary: dict[str, Any] = {}
        ledger_rows: list[dict[str, Any]] = []
        blocker_rows: list[dict[str, Any]] = []
        cell_rows: list[dict[str, Any]] = []
    else:
        summary = read_json(SUMMARY_PATH)
        final_summary = read_json(FINAL_SELECTOR_SUMMARY)
        ledger_rows = list(iter_jsonl(LEDGER_PATH))
        blocker_rows = list(iter_jsonl(BLOCKER_PATH))
        cell_rows = list(iter_jsonl(CELL_PATH))

    expected_old = int((final_summary or {}).get("old_three_selected_rows") or 0)
    expected_broader = int((final_summary or {}).get("broader_origin_selected_rows") or 0)
    expected_combined = int((final_summary or {}).get("combined_selected_rows") or 0)

    component_counts = Counter(str(row.get("denominator_component")) for row in ledger_rows)
    status_counts = Counter(str(row.get("condition_recheck_status")) for row in ledger_rows)
    policy_counts = Counter(str(row.get("condition_selected_policy")) for row in ledger_rows if row.get("condition_recheck_status") == "computed")
    blocker_counts = Counter(str(row.get("condition_blocker_class")) for row in blocker_rows)

    if len(ledger_rows) != expected_combined:
        failures.append(f"combined_denominator_rows_silently_dropped:{len(ledger_rows)}!={expected_combined}")
    if component_counts.get("old_three", 0) != expected_old:
        failures.append(f"old_three_denominator_rows_silently_dropped:{component_counts.get('old_three', 0)}!={expected_old}")
    if component_counts.get("broader_origin", 0) != expected_broader:
        failures.append(f"broader_denominator_rows_silently_dropped:{component_counts.get('broader_origin', 0)}!={expected_broader}")

    summary_expected = (summary.get("denominator_rows_expected") or {})
    summary_written = (summary.get("denominator_rows_written") or {})
    if summary_expected.get("combined") != expected_combined:
        failures.append("summary_expected_combined_rows_mismatch_final_selector")
    if summary_written.get("combined") != len(ledger_rows):
        failures.append("summary_written_combined_rows_mismatch_ledger")
    if summary_written.get("blocker_rows") != len(blocker_rows):
        failures.append("summary_blocker_rows_mismatch_blocker_ledger")

    broader_rows = [row for row in ledger_rows if row.get("denominator_component") == "broader_origin"]
    if expected_broader > 0:
        if not broader_rows:
            failures.append("broader_rows_exist_without_condition_recheck")
        missing_recheck = [
            row.get("source_row_id")
            for row in broader_rows
            if row.get("condition_recheck_status") not in {"computed", "blocked"}
        ]
        if missing_recheck:
            failures.append(f"broader_condition_recheck_status_missing:{len(missing_recheck)}")
        stale_session_rows = [
            row.get("source_row_id")
            for row in broader_rows
            if row.get("session_bucket") == "missing_session"
            or (
                row.get("session_bucket") == "off_configured_session"
                and row.get("symbol") not in EXPLICIT_24H_SESSION_SYMBOLS
            )
        ]
        if stale_session_rows:
            failures.append(f"broader_condition_denominator_contains_stale_pseudo_sessions:{len(stale_session_rows)}")

    computed_without_final_r = [
        row.get("source_row_id")
        for row in ledger_rows
        if row.get("condition_recheck_status") == "computed"
        and row.get("condition_selected_policy")
        and row.get("condition_selected_policy_final_r") is None
    ]
    if computed_without_final_r:
        failures.append(f"condition_selected_policy_lacks_final_r:{len(computed_without_final_r)}")

    computed_missing_policy = [
        row.get("source_row_id")
        for row in ledger_rows
        if row.get("condition_recheck_status") == "computed"
        and not row.get("condition_selected_policy")
    ]
    if computed_missing_policy:
        failures.append(f"computed_condition_row_missing_selected_policy:{len(computed_missing_policy)}")

    blocker_ledger_ids = {row.get("source_row_id") for row in blocker_rows}
    ledger_blocker_ids = {
        row.get("source_row_id")
        for row in ledger_rows
        if row.get("condition_recheck_status") == "blocked"
    }
    if blocker_ledger_ids != ledger_blocker_ids:
        failures.append(
            f"blocker_ledger_not_row_level_exact:{len(blocker_ledger_ids)}!={len(ledger_blocker_ids)}"
        )

    final_broader_group_count = final_selector_activated_broader_groups()
    if final_broader_group_count != int(summary.get("final_selector_activated_broader_group_count") or -1):
        failures.append("final_selector_broader_group_count_mismatch")
    allowlist = read_json(BROADER_ALLOWLIST) if BROADER_ALLOWLIST.exists() else {}
    allowlist_count = len(allowlist.get("entries") or [])
    if allowlist_count != int(summary.get("allowlist_broader_group_count") or -1):
        failures.append("allowlist_group_count_mismatch")

    cohort_metrics = summary.get("cohort_metrics") or {}
    for name in ("old_three", "broader_origin", "combined"):
        record = cohort_metrics.get(name) or {}
        if record.get("denominator_rows") != (
            expected_old if name == "old_three" else expected_broader if name == "broader_origin" else expected_combined
        ):
            failures.append(f"cohort_denominator_mismatch:{name}")
        condition_metrics = record.get("condition_challenger_on_computable_rows") or {}
        be_metrics = record.get("be_baseline_on_condition_computable_rows") or {}
        if int(record.get("condition_computed_rows") or 0) > 0:
            if not metric_positive(condition_metrics):
                failures.append(f"cohort_condition_metrics_incomplete:{name}")
            if not metric_positive(be_metrics):
                failures.append(f"cohort_be_metrics_incomplete:{name}")
        if "condition_vs_be_delta_on_computable_rows" not in record:
            failures.append(f"cohort_delta_missing:{name}")

    if not cell_rows:
        failures.append("missing_family_symbol_session_side_cell_rows")
    else:
        bad_cells = [
            row.get("condition_cell_id")
            for row in cell_rows
            if not all(row.get(field) not in (None, "") for field in ("family", "symbol", "session_bucket", "side"))
        ]
        if bad_cells:
            failures.append(f"cell_rows_missing_required_dimensions:{len(bad_cells)}")

    gate = summary.get("condition_activation_gate") or {}
    gate_checks = gate.get("gate_checks") or {}
    gate_passed = bool(gate.get("gate_passed"))
    decision = gate.get("condition_activation_decision")
    if gate_passed and decision != "enable_condition_challenger":
        failures.append("condition_gate_passed_but_not_enabled")
    if not gate_passed and decision != "keep_condition_disabled":
        failures.append("condition_gate_failed_but_not_disabled")
    runtime_state = summary.get("condition_runtime_state") or {}
    if runtime_state.get("condition_challenger_enabled") is not False:
        failures.append("condition_runtime_state_not_disabled")
    if runtime_state.get("apply_to_execution") is not False:
        failures.append("condition_apply_to_execution_not_disabled")
    if gate_checks and decision == "enable_condition_challenger":
        for required in (
            "full_denominator_condition_final_r_available",
            "total_r_beaten",
            "expectancy_beaten",
            "profit_factor_beaten",
            "win_rate_beaten",
            "chrono_oof_splits_nonnegative",
        ):
            if gate_checks.get(required) is not True:
                failures.append(f"condition_enabled_without_gate_check:{required}")

    chrono = summary.get("chrono_oof_splits") or {}
    for name in ("old_three", "broader_origin", "combined"):
        split = chrono.get(name) or {}
        if int((cohort_metrics.get(name) or {}).get("condition_computed_rows") or 0) > 0:
            if not split.get("fold_results"):
                failures.append(f"missing_chrono_oof_splits:{name}")
            else:
                for fold in split["fold_results"]:
                    delta = (fold.get("condition_vs_be_delta") or {}).get("expectancy_r_delta")
                    if delta is None:
                        failures.append(f"chrono_fold_missing_delta:{name}:{fold.get('fold_index')}")

    result = {
        "schema_version": "vnext_replacement_stage13_condition_challenger_recheck_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "checked_files": {
            "summary": rel(SUMMARY_PATH),
            "ledger": rel(LEDGER_PATH),
            "blockers": rel(BLOCKER_PATH),
            "cells": rel(CELL_PATH),
            "final_selector_summary": rel(FINAL_SELECTOR_SUMMARY),
            "final_selector_ledger": rel(FINAL_SELECTOR_LEDGER),
            "broader_allowlist": rel(BROADER_ALLOWLIST),
            "broader_summary": rel(BROADER_SUMMARY),
        },
        "expected_rows": {
            "old_three": expected_old,
            "broader_origin": expected_broader,
            "combined": expected_combined,
        },
        "observed_component_counts": dict(sorted(component_counts.items())),
        "condition_status_counts": dict(sorted(status_counts.items())),
        "condition_policy_counts": dict(sorted(policy_counts.items())),
        "condition_blocker_counts": dict(sorted(blocker_counts.items())),
        "cell_rows": len(cell_rows),
        "condition_activation_gate": gate,
        "combined_metrics": (cohort_metrics.get("combined") or {}),
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
