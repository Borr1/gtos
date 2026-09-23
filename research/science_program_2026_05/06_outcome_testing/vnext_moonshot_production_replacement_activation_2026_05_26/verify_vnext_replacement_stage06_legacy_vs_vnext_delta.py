from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
DATE = "2026-05-26"

SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_SUMMARY_{DATE}.json"
LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_LEDGER_{DATE}.jsonl"
REPORT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_REPORT_{DATE}.md"
STAGE05_SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_VERIFIER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
VERIFIER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"

REQUIRED_SCENARIOS = {
    "old_gtos_live_current_j46_j49": "old_gtos_live_current_j46_j49_all_replayable",
    "legacy_fixed_1_5r_comparator": "legacy_fixed_1_5r_comparator_all_replayable",
    "moonshot_be_after_trigger": "moonshot_be_after_trigger_all_replayable",
    "condition_router_challenger": "condition_router_all_replayable",
    "activated_default_source_bound_primary": "activated_runtime_effect_source_bound_primary_only",
}

REQUIRED_DIMENSIONS = {
    "overall",
    "symbol",
    "framework",
    "candidate_origin_family",
    "session_bucket",
    "year",
    "month",
    "week",
    "day",
    "source_window_complete",
    "activated_replay_disposition",
    "activated_selected_policy",
    "condition_selected_policy",
    "timeout_behavior",
    "nofill_behavior",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _float_close(a: Any, b: Any, tolerance: float = 1e-9) -> bool:
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), rel_tol=tolerance, abs_tol=tolerance)


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_test_result(state: dict[str, Any], result: dict[str, Any]) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    command = result.get("command")
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append(result)


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    required_paths = [
        SUMMARY_PATH,
        LEDGER_PATH,
        REPORT_PATH,
        STAGE05_SUMMARY_PATH,
        STAGE05_VERIFIER_PATH,
        STATE_PATH,
        MANIFEST_PATH,
    ]
    for path in required_paths:
        if not path.exists():
            failures.append(f"missing_required_path:{path.name}")

    if failures:
        result = {
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": "stage_06_legacy_vs_vnext_delta",
            "status": "failed",
            "failures": failures,
            "warnings": warnings,
        }
        _write_json(VERIFIER_PATH, result)
        return 1

    summary = _read_json(SUMMARY_PATH)
    stage05_summary = _read_json(STAGE05_SUMMARY_PATH)
    stage05_verifier = _read_json(STAGE05_VERIFIER_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    manifest = _read_json(MANIFEST_PATH)
    state = _read_json(STATE_PATH)

    stage05_coverage = stage05_summary.get("coverage", stage05_summary)
    expected_candidate_rows = int(stage05_coverage["candidate_rows"])
    expected_candidate_delta_rows = int(summary["output_rows"]["candidate_delta_rows"])
    expected_aggregate_delta_rows = int(summary["output_rows"]["aggregate_delta_rows"])
    expected_ledger_rows = int(summary["output_rows"]["delta_ledger_rows"])

    if expected_candidate_rows != 253234:
        failures.append(f"unexpected_stage05_candidate_rows:{expected_candidate_rows}")
    if expected_candidate_delta_rows != expected_candidate_rows:
        failures.append(
            f"candidate_delta_rows_do_not_match_stage05:{expected_candidate_delta_rows}!={expected_candidate_rows}"
        )
    if expected_ledger_rows != expected_candidate_delta_rows + expected_aggregate_delta_rows:
        failures.append("summary_delta_ledger_rows_not_candidate_plus_aggregate")
    if set(summary.get("aggregate_dimensions", [])) != REQUIRED_DIMENSIONS:
        failures.append("summary_aggregate_dimensions_mismatch")
    if set(summary.get("scenario_counts", {})) != set(REQUIRED_SCENARIOS):
        failures.append("summary_scenario_set_mismatch")

    digest = hashlib.sha256()
    record_counts: Counter[str] = Counter()
    candidate_ids: set[str] = set()
    candidate_scenario_presence: Counter[str] = Counter()
    aggregate_dimensions: Counter[str] = Counter()
    aggregate_scenarios: Counter[str] = Counter()
    overall_rows: dict[str, dict[str, Any]] = {}
    source_window_values: Counter[str] = Counter()
    no_live_mutation_false_rows = 0
    candidate_required_key_failures = 0

    candidate_required_keys = {
        "candidate_id",
        "symbol",
        "framework",
        "candidate_origin_family",
        "old_gtos_live_current_j46_j49_r",
        "legacy_fixed_1_5r_r",
        "moonshot_be_after_trigger_r",
        "condition_router_r",
        "activated_default_source_bound_primary_r",
        "activated_replay_disposition",
        "no_live_trading_or_broker_mutation",
    }

    with LEDGER_PATH.open("rb") as handle:
        for raw in handle:
            digest.update(raw)
            row = json.loads(raw.decode("utf-8"))
            record_type = row.get("record_type")
            record_counts[record_type] += 1
            if row.get("route_id") != ROUTE_ID:
                failures.append("route_id_mismatch")
                break
            if row.get("stage_id") != "stage_06_legacy_vs_vnext_delta":
                failures.append("stage_id_mismatch")
                break

            if record_type == "candidate_delta":
                if row.get("schema_version") != "vnext_replacement_stage06_candidate_delta_v1":
                    failures.append("candidate_schema_version_mismatch")
                    break
                if not candidate_required_keys.issubset(row):
                    candidate_required_key_failures += 1
                candidate_ids.add(str(row.get("candidate_id")))
                source_window_values[str(row.get("source_window_complete"))] += 1
                if row.get("no_live_trading_or_broker_mutation") is not True:
                    no_live_mutation_false_rows += 1
                for scenario in REQUIRED_SCENARIOS:
                    candidate_scenario_presence[scenario] += 1
            elif record_type == "aggregate_delta":
                if row.get("schema_version") != "vnext_replacement_stage06_aggregate_delta_v1":
                    failures.append("aggregate_schema_version_mismatch")
                    break
                dim = str(row.get("dimension_type"))
                scenario = str(row.get("scenario"))
                aggregate_dimensions[dim] += 1
                aggregate_scenarios[scenario] += 1
                if dim == "overall":
                    overall_rows[scenario] = row
            else:
                failures.append(f"unexpected_record_type:{record_type}")
                break

    ledger_sha256 = digest.hexdigest()
    if ledger_sha256 != summary.get("ledger_sha256"):
        failures.append("ledger_sha256_mismatch")
    if record_counts["candidate_delta"] != expected_candidate_delta_rows:
        failures.append(
            f"candidate_delta_row_count_mismatch:{record_counts['candidate_delta']}!={expected_candidate_delta_rows}"
        )
    if record_counts["aggregate_delta"] != expected_aggregate_delta_rows:
        failures.append(
            f"aggregate_delta_row_count_mismatch:{record_counts['aggregate_delta']}!={expected_aggregate_delta_rows}"
        )
    if sum(record_counts.values()) != expected_ledger_rows:
        failures.append(f"ledger_row_count_mismatch:{sum(record_counts.values())}!={expected_ledger_rows}")
    if len(candidate_ids) != expected_candidate_delta_rows:
        failures.append(f"candidate_id_uniqueness_mismatch:{len(candidate_ids)}!={expected_candidate_delta_rows}")
    if candidate_required_key_failures:
        failures.append(f"candidate_required_key_failures:{candidate_required_key_failures}")
    if no_live_mutation_false_rows:
        failures.append(f"no_live_trading_or_broker_mutation_false_rows:{no_live_mutation_false_rows}")
    if set(overall_rows) != set(REQUIRED_SCENARIOS):
        failures.append("overall_scenario_rows_missing")
    if set(aggregate_dimensions) != REQUIRED_DIMENSIONS:
        failures.append("aggregate_dimension_rows_missing")

    for scenario, count in summary.get("scenario_counts", {}).items():
        if int(count) != expected_candidate_delta_rows:
            failures.append(f"summary_scenario_count_not_full_candidate_universe:{scenario}:{count}")
        if candidate_scenario_presence.get(scenario) != expected_candidate_delta_rows:
            failures.append(f"candidate_scenario_presence_mismatch:{scenario}")

    stage05_totals = stage05_coverage["scenario_total_r"]
    stage05_expectancies = stage05_coverage["scenario_expectancy_r"]
    for scenario, stage05_key in REQUIRED_SCENARIOS.items():
        row = overall_rows.get(scenario)
        if not row:
            continue
        if not _float_close(row.get("total_r"), stage05_totals.get(stage05_key), tolerance=1e-6):
            failures.append(f"overall_total_r_mismatch:{scenario}")
        if not _float_close(row.get("expectancy_r"), stage05_expectancies.get(stage05_key), tolerance=1e-12):
            failures.append(f"overall_expectancy_mismatch:{scenario}")
        if int(row.get("candidate_count", -1)) != expected_candidate_delta_rows:
            failures.append(f"overall_candidate_count_mismatch:{scenario}")

    activated_overall = overall_rows.get("activated_default_source_bound_primary", {})
    if float(activated_overall.get("expectancy_r", 0.0)) >= 0:
        failures.append("activated_default_projection_not_negative_expected_warning_missing_or_changed")
    else:
        warnings.append("activated_default_source_bound_primary_negative_expectancy_must_block_overlay_without_repair")

    required_warning = "activated_source_bound_primary_rows_have_nonpositive_expectancy_stage12_must_not_apply_overlay"
    if required_warning not in summary.get("stage05_warning_carried_forward", []):
        failures.append("stage05_activation_warning_not_carried_forward_in_summary")
    if required_warning not in stage05_verifier.get("warnings", []):
        failures.append("stage05_verifier_warning_missing")
    if "Stage12 must fail any production activation overlay" not in report_text:
        failures.append("report_activation_warning_missing")

    manifest_paths = {row.get("path") for row in manifest.get("outputs", [])}
    for required_name in [LEDGER_PATH.name, REPORT_PATH.name, SUMMARY_PATH.name]:
        if required_name not in manifest_paths:
            failures.append(f"manifest_missing_stage06_output:{required_name}")

    status = "passed" if not failures else "failed"
    result = {
        "aggregate_dimension_counts": dict(sorted(aggregate_dimensions.items())),
        "aggregate_scenario_counts": dict(sorted(aggregate_scenarios.items())),
        "candidate_delta_rows": record_counts["candidate_delta"],
        "candidate_id_unique_count": len(candidate_ids),
        "delta_ledger_rows": sum(record_counts.values()),
        "failures": failures,
        "generated_at_utc": generated_at,
        "ledger_sha256": ledger_sha256,
        "overall_scenario_metrics": {
            scenario: {
                "expectancy_r": row.get("expectancy_r"),
                "performance_count": row.get("performance_count"),
                "profit_factor": row.get("profit_factor"),
                "selected_count": row.get("selected_count"),
                "total_r": row.get("total_r"),
                "win_rate": row.get("win_rate"),
            }
            for scenario, row in sorted(overall_rows.items())
        },
        "record_type_counts": dict(record_counts),
        "route_id": ROUTE_ID,
        "source_window_value_counts": dict(source_window_values),
        "stage_id": "stage_06_legacy_vs_vnext_delta",
        "status": status,
        "warnings": warnings,
    }
    _write_json(VERIFIER_PATH, result)

    if status == "passed":
        _upsert_manifest_output(
            manifest,
            {
                "path": VERIFIER_PATH.name,
                "stage": "stage_06",
                "status": "created",
                "result": "passed",
            },
        )
        manifest["last_updated_utc"] = generated_at
        _write_json(MANIFEST_PATH, manifest)

        state.setdefault("evidence_rows_scanned", {})["stage06_verifier_rows_scanned"] = sum(record_counts.values())
        _append_test_result(
            state,
            {
                "command": str(Path(__file__).relative_to(REPO_ROOT)),
                "result": "passed",
                "timestamp_utc": generated_at,
            },
        )
        state["last_updated_utc"] = generated_at
        _write_json(STATE_PATH, state)

    print(json.dumps({"rows": sum(record_counts.values()), "status": status, "warnings": warnings}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
