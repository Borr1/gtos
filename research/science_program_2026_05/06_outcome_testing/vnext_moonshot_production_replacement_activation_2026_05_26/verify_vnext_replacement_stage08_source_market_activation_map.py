from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

MOONSHOT_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STAGE07_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_CLOSURE_SUMMARY_{DATE}.json"
MOONSHOT_FORWARD_REQUIREMENTS = MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_{DATE}.jsonl"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

OUTPUT_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
OUTPUT_CAPTURE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SOURCE_CAPTURE_REQUIREMENTS_{DATE}.jsonl"
OUTPUT_EXCLUSIONS = ROUTE_DIR / f"VNEXT_REPLACEMENT_ACTIVATION_EXCLUSION_LEDGER_{DATE}.jsonl"
OUTPUT_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_SOURCE_MARKET_ACTIVATION_VERIFIER_{DATE}.json"
BROKER_ONBOARDING_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_VERIFIER_{DATE}.json"
BROKER_ONBOARDING_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_LEDGER_{DATE}.jsonl"

LIVE_DEPLOYMENT_SYMBOLS = {
    "GBPJPY",
    "GBPUSD",
    "NAS100",
    "US30_cash",
    "USDJPY",
    "XAGUSD",
    "XAUUSD",
}

REQUIRED_SOURCE_RULES = {
    "broker_market_onboarding",
    "broker_native_live_feed",
    "missing_source",
    "mt5_ohlc_csv",
    "sierra_scid_or_export",
    "tick_parquet",
}

GLOBAL_EXCLUSION_IDS = {
    "STAGE08-GLOBAL-DEFAULT-SOURCE-BOUND-PRIMARY",
    "STAGE08-GLOBAL-SOURCE-MISSING",
    "STAGE08-GLOBAL-SECONDARY-FRAMEWORK",
    "STAGE08-GLOBAL-DYNAMIC-EXCLUDED",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_line_number"] = line_number
                rows.append(row)
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    stage05 = _read_json(STAGE05_SUMMARY)
    stage05_verifier = _read_json(STAGE05_VERIFIER)
    stage06_verifier = _read_json(STAGE06_VERIFIER)
    stage07_summary = _read_json(STAGE07_SUMMARY)
    output_map = _read_json(OUTPUT_MAP)
    capture_rows = _read_jsonl(OUTPUT_CAPTURE)
    exclusion_rows = _read_jsonl(OUTPUT_EXCLUSIONS)
    forward_requirements = _read_jsonl(MOONSHOT_FORWARD_REQUIREMENTS)
    broker_onboarding_summary = _read_json(BROKER_ONBOARDING_SUMMARY)
    broker_onboarding_rows = _read_jsonl(BROKER_ONBOARDING_LEDGER)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)

    stage05_symbols = set(stage05["coverage"]["symbol_counts"])
    market_rows = output_map.get("markets", [])
    market_by_symbol = {row.get("symbol"): row for row in market_rows}
    if len(market_rows) != len(stage05_symbols):
        failures.append(f"market row count mismatch: {len(market_rows)} != {len(stage05_symbols)}")
    missing_symbols = sorted(stage05_symbols - set(market_by_symbol))
    extra_symbols = sorted(set(market_by_symbol) - stage05_symbols)
    if missing_symbols:
        failures.append(f"missing Stage05 symbols: {missing_symbols}")
    if extra_symbols:
        failures.append(f"extra market symbols: {extra_symbols}")

    candidate_sum = sum(int(row.get("candidate_rows", 0)) for row in market_rows)
    expected_candidate_rows = int(stage05["coverage"]["candidate_rows"])
    if candidate_sum != expected_candidate_rows:
        failures.append(f"candidate row sum mismatch: {candidate_sum} != {expected_candidate_rows}")
    if int(output_map.get("stage05_candidate_rows", -1)) != expected_candidate_rows:
        failures.append("output_map stage05_candidate_rows does not match Stage05 summary")

    onboarding_by_symbol = {row.get("symbol"): row for row in broker_onboarding_rows}
    if set(onboarding_by_symbol) != stage05_symbols:
        failures.append("broker onboarding ledger does not cover the exact Stage05 replay market universe")

    live_rows = {
        symbol
        for symbol, row in market_by_symbol.items()
        if row.get("activation_status") == "forward_capture_required_before_execution_activation"
        and row.get("broker_native_live_feed_available_now") is True
        and row.get("broker_market_onboarding", {}).get("eligible_for_vnext_activation") is True
    }
    expected_live_rows = set(broker_onboarding_summary.get("eligible_symbols", []))
    if live_rows != expected_live_rows:
        failures.append(
            f"broker-native eligibility mismatch: map={sorted(live_rows)} verifier={sorted(expected_live_rows)}"
        )
    if set(output_map.get("broker_native_activation_eligible_symbols", [])) != expected_live_rows:
        failures.append("broker_native_activation_eligible_symbols does not match onboarding verifier")
    if set(output_map.get("broker_live_deployment_symbols", [])) != expected_live_rows:
        failures.append("broker_live_deployment_symbols is not the broker-onboarding eligible set")

    if any(row.get("activation_status") == "excluded_until_broker_source_exists" for row in market_rows):
        failures.append("map still uses stale excluded_until_broker_source_exists classification")
    if any(row.get("legacy_live_deployment_symbol_list_is_activation_ceiling") is not False for row in market_rows):
        failures.append("one or more market rows still allow the legacy live deployment list as activation ceiling")

    pending_symbols = {
        symbol
        for symbol, row in market_by_symbol.items()
        if row.get("activation_status") == "broker_contract_verification_required_not_excluded"
    }
    if pending_symbols != set(broker_onboarding_summary.get("pending_symbols_not_excluded", [])):
        failures.append("pending-not-excluded market set does not match onboarding verifier")
    pending_exclusions = [
        row
        for row in exclusion_rows
        if row.get("symbol") in pending_symbols and row.get("exclusion_scope") == "market"
    ]
    if pending_exclusions:
        failures.append("pending broker verification markets were incorrectly written to the exclusion ledger")

    exact_excluded_symbols = set(broker_onboarding_summary.get("exact_excluded_symbols", []))
    market_exclusions = [row for row in exclusion_rows if row.get("exclusion_scope") == "market"]
    if {row.get("symbol") for row in market_exclusions} != exact_excluded_symbols:
        failures.append("market exclusion ledger is not limited to exact broker-onboarding exclusions")
    if int(output_map.get("exclusion_rows", -1)) != len(exclusion_rows):
        failures.append("output_map exclusion_rows does not match exclusion ledger")

    global_ids = {row.get("activation_exclusion_id") for row in exclusion_rows if row.get("exclusion_scope") != "market"}
    if global_ids != GLOBAL_EXCLUSION_IDS:
        failures.append(f"global exclusion ids mismatch: {sorted(global_ids)}")

    default_projection = stage06_verifier["overall_scenario_metrics"]["activated_default_source_bound_primary"]
    if float(default_projection["expectancy_r"]) >= 0.0:
        failures.append("Stage06 default source-bound primary projection is not negative")
    default_exclusion = next(
        (row for row in exclusion_rows if row.get("activation_exclusion_id") == "STAGE08-GLOBAL-DEFAULT-SOURCE-BOUND-PRIMARY"),
        None,
    )
    if not default_exclusion:
        failures.append("missing global exclusion for negative default source-bound primary projection")
    elif int(default_exclusion.get("candidate_rows", -1)) != int(default_projection["performance_count"]):
        failures.append("default projection exclusion row count does not match Stage06 performance_count")

    source_missing = next(
        (row for row in exclusion_rows if row.get("activation_exclusion_id") == "STAGE08-GLOBAL-SOURCE-MISSING"),
        None,
    )
    if not source_missing:
        failures.append("missing global missing-source exclusion")
    elif int(source_missing.get("candidate_rows", -1)) != int(stage05_verifier["nested_source_mode_counts"]["MISSING_SOURCE"]):
        failures.append("missing-source exclusion count does not match Stage05 verifier")

    secondary = next(
        (row for row in exclusion_rows if row.get("activation_exclusion_id") == "STAGE08-GLOBAL-SECONDARY-FRAMEWORK"),
        None,
    )
    if not secondary:
        failures.append("missing secondary-framework exclusion")
    elif int(secondary.get("candidate_rows", -1)) != int(stage05["coverage"]["secondary_framework_replay_only_rows"]):
        failures.append("secondary-framework exclusion count does not match Stage05 summary")

    dynamic_excluded = next(
        (row for row in exclusion_rows if row.get("activation_exclusion_id") == "STAGE08-GLOBAL-DYNAMIC-EXCLUDED"),
        None,
    )
    if not dynamic_excluded:
        failures.append("missing dynamic-excluded global exclusion")
    elif int(dynamic_excluded.get("candidate_rows", -1)) != int(stage05["coverage"]["disposition_counts"]["dynamic_policy_replay_excluded"]):
        failures.append("dynamic-excluded count does not match Stage05 summary")

    expected_capture_rows = len(forward_requirements) + 10 + len(pending_symbols)
    if len(capture_rows) != expected_capture_rows:
        failures.append(f"source-capture row count mismatch: {len(capture_rows)} != {expected_capture_rows}")
    if int(output_map.get("capture_requirement_rows", -1)) != len(capture_rows):
        failures.append("output_map capture_requirement_rows does not match capture ledger")
    imported_count = sum(1 for row in capture_rows if str(row.get("replacement_requirement_id", "")).startswith("STAGE08-IMPORTED-"))
    route_count = sum(1 for row in capture_rows if str(row.get("replacement_requirement_id", "")).startswith("STAGE08-ROUTE-"))
    if imported_count != len(forward_requirements):
        failures.append("imported capture requirement count does not match moonshot forward requirements")
    if route_count != 10:
        failures.append("route-local capture requirement count is not 10")
    broker_requirement_count = sum(
        1 for row in capture_rows if str(row.get("replacement_requirement_id", "")).startswith("STAGE08-BROKER-")
    )
    if broker_requirement_count != len(pending_symbols):
        failures.append("broker pending capture requirement count does not match pending-not-excluded market count")

    source_rules = set(output_map.get("source_handling_rules", {}))
    if not REQUIRED_SOURCE_RULES.issubset(source_rules):
        failures.append(f"missing source handling rules: {sorted(REQUIRED_SOURCE_RULES - source_rules)}")
    if output_map.get("nested_source_mode_counts") != stage05_verifier["nested_source_mode_counts"]:
        failures.append("nested source mode counts were not preserved from Stage05 verifier")
    if output_map.get("question_closure_rows_consumed") != stage07_summary["output_ledger_rows"]:
        failures.append("Stage07 question closure row count was not consumed exactly")
    if output_map.get("no_live_or_broker_mutation") is not True:
        failures.append("Stage08 map does not explicitly assert no live/broker mutation")

    if state.get("current_stage") == "stage_08_source_and_market_activation_map":
        failures.append("route state was reset to Stage08")
    if state.get("first_incomplete_invariant") == "stage_08_source_and_market_activation_map_pending":
        failures.append("route first_incomplete_invariant was reset to Stage08")
    evidence = state.get("evidence_rows_scanned", {})
    if evidence.get("stage08_market_rows") != len(market_rows):
        failures.append("state stage08_market_rows mismatch")
    if evidence.get("stage08_source_capture_requirement_rows") != len(capture_rows):
        failures.append("state stage08_source_capture_requirement_rows mismatch")
    if evidence.get("stage08_activation_exclusion_rows") != len(exclusion_rows):
        failures.append("state stage08_activation_exclusion_rows mismatch")
    if evidence.get("stage08_broker_verified_symbols") != len(expected_live_rows):
        failures.append("state stage08_broker_verified_symbols mismatch")
    if evidence.get("stage08_broker_pending_not_excluded_symbols") != len(pending_symbols):
        failures.append("state stage08_broker_pending_not_excluded_symbols mismatch")
    if evidence.get("stage08_broker_exact_excluded_symbols") != len(exact_excluded_symbols):
        failures.append("state stage08_broker_exact_excluded_symbols mismatch")

    manifest_by_path = {row.get("path"): row for row in manifest.get("outputs", [])}
    for required_path in (OUTPUT_MAP.name, OUTPUT_CAPTURE.name, OUTPUT_EXCLUSIONS.name, BROKER_ONBOARDING_SUMMARY.name, BROKER_ONBOARDING_LEDGER.name):
        if required_path not in manifest_by_path:
            failures.append(f"manifest missing {required_path}")

    for symbol, row in sorted(market_by_symbol.items()):
        if row.get("candidate_rows") != stage05["coverage"]["symbol_counts"][symbol]:
            failures.append(f"candidate count mismatch for {symbol}")
        if not row.get("primary_historical_source_paths"):
            warnings.append(f"{symbol} has no primary historical source path recorded")
        if row.get("broker_market_onboarding", {}).get("exact_exclusion_reason") and not str(row.get("activation_status", "")).startswith("excluded_"):
            failures.append(f"{symbol} has exact broker exclusion evidence but is not excluded")
        if row.get("activation_status") == "broker_contract_verification_required_not_excluded":
            warnings.append(f"{symbol} remains pending broker contract verification, not excluded")

    status = "passed" if not failures else "failed"
    verifier = {
        "candidate_rows_checked": candidate_sum,
        "capture_rows": len(capture_rows),
        "exclusion_rows": len(exclusion_rows),
        "failures": failures,
        "generated_at_utc": generated_at,
        "global_exclusion_ids": sorted(global_ids),
        "ledger_hashes": {
            BROKER_ONBOARDING_LEDGER.name: _sha256(BROKER_ONBOARDING_LEDGER),
            BROKER_ONBOARDING_SUMMARY.name: _sha256(BROKER_ONBOARDING_SUMMARY),
            OUTPUT_MAP.name: _sha256(OUTPUT_MAP),
            OUTPUT_CAPTURE.name: _sha256(OUTPUT_CAPTURE),
            OUTPUT_EXCLUSIONS.name: _sha256(OUTPUT_EXCLUSIONS),
        },
        "broker_native_activation_eligible_symbols_checked": sorted(live_rows),
        "broker_pending_not_excluded_symbols_checked": sorted(pending_symbols),
        "broker_exact_excluded_symbols_checked": sorted(exact_excluded_symbols),
        "legacy_live_deployment_symbols_not_activation_ceiling": sorted(LIVE_DEPLOYMENT_SYMBOLS),
        "market_rows": len(market_rows),
        "no_live_or_broker_mutation": True,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage08_source_market_activation_verifier_v1",
        "stage_id": "stage_08_source_and_market_activation_map",
        "status": status,
        "warnings": warnings,
    }
    _write_json(OUTPUT_VERIFIER, verifier)

    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_VERIFIER.name, "result": status, "stage": "stage_08", "status": "created"},
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence["stage08_verifier_market_rows_scanned"] = len(market_rows)
    evidence["stage08_verifier_source_capture_rows_scanned"] = len(capture_rows)
    evidence["stage08_verifier_exclusion_rows_scanned"] = len(exclusion_rows)
    _append_test_result(
        state,
        _rel(Path(__file__)),
        status,
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_08_source_market_activation_verifier_completed",
            "generated_at_utc": generated_at,
            "market_rows": len(market_rows),
            "result": status,
            "route_id": ROUTE_ID,
            "stage_id": "stage_08_source_and_market_activation_map",
        }
    )

    print(json.dumps({"markets": len(market_rows), "status": status, "warnings": warnings}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
