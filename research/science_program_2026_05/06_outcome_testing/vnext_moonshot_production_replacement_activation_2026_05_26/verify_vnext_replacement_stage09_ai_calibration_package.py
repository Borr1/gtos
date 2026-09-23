from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

AI_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_{DATE}.json"
PROMPT_PACK = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_PROMPT_PACK_{DATE}.jsonl"
SPEND_REQUEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_SPEND_REQUEST_{DATE}.md"
OUTPUT_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_VERIFIER_{DATE}.json"

FORBIDDEN_PACKET_KEYS = {
    "accepted_losers",
    "accepted_winners",
    "account_loss_rate",
    "be_after_trigger_final_r",
    "best_expectancy_r",
    "best_pass_probability_proxy",
    "best_total_r",
    "blocked_negative_r",
    "blocked_positive_r",
    "condition_vs_fixed_delta_r",
    "condition_vs_global_be_delta_r",
    "condition_vs_live_current_delta_r",
    "conservative_ambiguous_r",
    "expectancy_r",
    "exit_reason",
    "exit_time_utc",
    "final_r",
    "gross_loss_r",
    "gross_win_r",
    "legacy_final_r",
    "live_current_j46_j49_final_r",
    "live_exit_reason",
    "mae_r",
    "mfe_r",
    "missed_winners",
    "optimistic_ambiguous_r",
    "pass_probability_proxy",
    "pending_lifecycle_state",
    "policy_reversal_bucket",
    "post_trade_equity",
    "profit_factor",
    "selected_policy_final_r",
    "selected_vs_fixed_delta_r",
    "selected_vs_live_delta_r",
    "simulated_r",
    "terminal_order_raw",
    "terminal_outcome",
    "total_r",
    "win_rate",
}

REQUIRED_SCHEMA_KEYS = {
    "confidence",
    "decision",
    "disallowed_fields_used",
    "reason_codes",
    "recommended_ai_role",
    "required_context_fields_used",
    "risk_notes",
    "schema_version",
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


def _scan_forbidden_keys(data: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_l = str(key).lower()
            if key_l in FORBIDDEN_PACKET_KEYS or key_l.endswith("_r") or key_l.endswith("_outcome"):
                hits.append(f"{path}.{key}")
            hits.extend(_scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            hits.extend(_scan_forbidden_keys(value, f"{path}[{index}]"))
    return hits


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    failures: list[str] = []
    warnings: list[str] = []

    ai_manifest = _read_json(AI_MANIFEST)
    prompt_rows = _read_jsonl(PROMPT_PACK)
    state = _read_json(STATE_PATH)
    route_manifest = _read_json(MANIFEST_PATH)
    spend_request = SPEND_REQUEST.read_text(encoding="utf-8")

    expected_rows = int(ai_manifest["prompt_pack"]["packet_rows"])
    if len(prompt_rows) != expected_rows:
        failures.append(f"prompt pack row count mismatch: {len(prompt_rows)} != {expected_rows}")
    if ai_manifest["prompt_pack"]["sha256"] != _sha256(PROMPT_PACK):
        failures.append("prompt pack sha256 does not match manifest")

    cache_keys = [row.get("cache_key") for row in prompt_rows]
    if len(cache_keys) != len(set(cache_keys)):
        failures.append("prompt pack cache keys are not unique")
    if int(ai_manifest["response_cache_manifest"]["cache_key_count"]) != len(set(cache_keys)):
        failures.append("cache key count in manifest does not match prompt pack")

    selected_counter: Counter[str] = Counter()
    for row in prompt_rows:
        if row.get("no_paid_call_made") is not True:
            failures.append(f"paid-call flag not false/blocked in row {row.get('packet_id')}")
        if row.get("forbidden_outcome_fields_excluded") is not True:
            failures.append(f"forbidden outcome exclusion flag missing in row {row.get('packet_id')}")
        if row.get("model_id") != ai_manifest["model_binding"]["primary_model"]:
            failures.append(f"model id mismatch in row {row.get('packet_id')}")
        if row.get("model_effort") != ai_manifest["model_binding"]["primary_effort"]:
            failures.append(f"model effort mismatch in row {row.get('packet_id')}")
        prompt_payload = row.get("prompt_payload")
        if not isinstance(prompt_payload, dict):
            failures.append(f"missing prompt payload in row {row.get('packet_id')}")
            continue
        schema = prompt_payload.get("response_schema", {})
        missing_schema = sorted(REQUIRED_SCHEMA_KEYS - set(schema))
        if missing_schema:
            failures.append(f"response schema missing {missing_schema} in row {row.get('packet_id')}")
        selected_counter.update(row.get("selected_strata") or [])
        forbidden_hits = _scan_forbidden_keys(prompt_payload)
        if forbidden_hits:
            failures.append(f"forbidden fields in row {row.get('packet_id')}: {forbidden_hits[:8]}")
        source_complete = (
            prompt_payload.get("candidate_context", {})
            .get("market_source_activation", {})
            .get("source_window_complete")
        )
        if not isinstance(source_complete, bool):
            failures.append(f"source_window_complete is not boolean in row {row.get('packet_id')}")

    if dict(sorted(selected_counter.items())) != ai_manifest["selected_stratum_counts"]:
        failures.append("selected stratum counts do not match prompt pack rows")
    covered = set(ai_manifest["covered_strata"])
    unavailable = {row["stratum"] for row in ai_manifest["unavailable_strata"]}
    mandatory = set(ai_manifest["mandatory_strata"])
    if covered | unavailable != mandatory:
        failures.append("covered plus unavailable strata does not equal mandatory strata")
    if "prop_near_boundary_ev_stream" not in unavailable:
        warnings.append("prop_near_boundary_ev_stream is not unavailable; verify Stage05 gained per-trade prop attempt data")

    ai_state = ai_manifest["ai_call_execution_state"]
    if ai_state.get("paid_api_or_vendor_calls_made") != 0:
        failures.append("AI manifest records paid calls")
    if ai_state.get("route_state_budget_cap_usd") is not None:
        failures.append("AI manifest unexpectedly has a route-state budget cap")
    if ai_manifest["spend_plan"].get("run_when_budget_cap_absent") is not False:
        failures.append("spend plan allows run without budget cap")
    if float(ai_manifest["spend_plan"]["estimated_usd_claude_sonnet_4_6_offline_rate"]) > float(
        ai_manifest["spend_plan"]["hard_cap_requested_usd"]
    ):
        failures.append("estimated spend exceeds requested hard cap")
    if "$5.00" not in spend_request:
        failures.append("spend request does not state the hard cap")

    if state.get("current_stage") != "stage_10_ml_and_monitoring_integration":
        failures.append("route state did not advance to Stage10")
    if state.get("first_incomplete_invariant") != "stage_10_ml_and_monitoring_integration_pending":
        failures.append("route state first incomplete invariant is not Stage10 pending")
    if state.get("budget_cap_state", {}).get("route_state_budget_cap_usd") is not None:
        failures.append("route state budget cap should remain null")
    evidence = state.get("evidence_rows_scanned", {})
    if evidence.get("stage09_candidate_rows_scanned") != ai_manifest["sampling_method"]["candidate_rows_scanned"]:
        failures.append("state Stage09 candidate rows scanned mismatch")
    if evidence.get("stage09_ai_prompt_packet_rows") != len(prompt_rows):
        failures.append("state Stage09 prompt row count mismatch")
    if evidence.get("stage09_paid_calls_made") != 0:
        failures.append("state records paid calls")

    route_outputs = {row.get("path") for row in route_manifest.get("outputs", [])}
    for path in (AI_MANIFEST.name, PROMPT_PACK.name, SPEND_REQUEST.name):
        if path not in route_outputs:
            failures.append(f"output manifest missing {path}")

    status = "passed" if not failures else "failed"
    verifier = {
        "covered_strata": sorted(covered),
        "failures": failures,
        "generated_at_utc": generated_at,
        "ledger_hashes": {
            AI_MANIFEST.name: _sha256(AI_MANIFEST),
            PROMPT_PACK.name: _sha256(PROMPT_PACK),
            SPEND_REQUEST.name: _sha256(SPEND_REQUEST),
        },
        "paid_api_or_vendor_calls_made": 0,
        "prompt_rows": len(prompt_rows),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage09_ai_calibration_verifier_v1",
        "stage_id": "stage_09_ai_calibration_package",
        "status": status,
        "unavailable_strata": sorted(unavailable),
        "warnings": warnings,
    }
    _write_json(OUTPUT_VERIFIER, verifier)

    _upsert_manifest_output(
        route_manifest,
        {"path": OUTPUT_VERIFIER.name, "result": status, "stage": "stage_09", "status": "created"},
    )
    route_manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, route_manifest)

    evidence["stage09_verifier_prompt_rows_scanned"] = len(prompt_rows)
    _append_test_result(state, _rel(Path(__file__)), status, generated_at)
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_09_ai_calibration_verifier_completed",
            "generated_at_utc": generated_at,
            "prompt_rows": len(prompt_rows),
            "result": status,
            "route_id": ROUTE_ID,
            "stage_id": "stage_09_ai_calibration_package",
        }
    )

    print(json.dumps({"prompt_rows": len(prompt_rows), "status": status, "warnings": warnings}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
