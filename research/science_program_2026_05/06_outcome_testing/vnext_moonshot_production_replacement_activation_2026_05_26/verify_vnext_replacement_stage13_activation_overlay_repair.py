from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import yaml


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_activation_overlay_repair"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_REPAIRED_ACTIVATION_OVERLAY_SUMMARY_{DATE}.json"
LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_REPAIRED_ACTIVATION_OVERLAY_LEDGER_{DATE}.jsonl"
FAILURE_ENUMERATION = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_REPAIR_FAILURE_ENUMERATION_{DATE}.json"
)
STAGE11_OVERLAY = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
VERIFIER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_ACTIVATION_REPAIR_VERIFIER_{DATE}.json"
REQUIRED_ACTIVATED_FRAMEWORKS = {"breaker_re_entry", "fvg_fill", "ob_retest"}
REQUIRED_ACTIVATED_SYMBOLS = {
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "NAS100",
    "US30_cash",
    "USDJPY",
    "XAGUSD",
    "XAUUSD",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = utc_now()
    failures: list[str] = []
    warnings: list[str] = []

    for path in (SUMMARY_PATH, LEDGER_PATH, FAILURE_ENUMERATION, STAGE11_OVERLAY):
        if not path.exists():
            failures.append(f"missing_required_path:{path.name}")
    if failures:
        result = {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "generated_at_utc": generated_at,
            "status": "failed",
            "failures": failures,
            "warnings": warnings,
        }
        write_json(VERIFIER_PATH, result)
        return 1

    summary = read_json(SUMMARY_PATH)
    enumeration = read_json(FAILURE_ENUMERATION)
    overlay = yaml.safe_load(STAGE11_OVERLAY.read_text(encoding="utf-8")) or {}
    repaired = summary["repaired_overlay_metrics"]["be_after_trigger_repaired_overlay"]
    comparators = summary["comparator_metrics"]
    selector = summary["selector_contract"]

    ledger_rows = 0
    symbols = Counter()
    sessions = Counter()
    frameworks = Counter()
    source_windows = Counter()
    branch_labels = Counter()
    selected_policy_counts = Counter()
    same_bar_rows = 0
    non_follow_rows = 0
    broker_excluded_rows = 0
    off_kz_rows = 0
    nonpositive_delta_vs_old = 0
    for row in iter_jsonl(LEDGER_PATH):
        ledger_rows += 1
        symbols[str(row.get("symbol"))] += 1
        sessions[str(row.get("session_bucket"))] += 1
        frameworks[str(row.get("framework"))] += 1
        source_windows[str(row.get("source_window_complete"))] += 1
        branch_labels[str(row.get("branch_label"))] += 1
        selected_policy_counts[str(row.get("selected_policy"))] += 1
        if row.get("branch_label") != "FOLLOW":
            non_follow_rows += 1
        if str(row.get("symbol")) not in selector["broker_native_symbols_allowed"]:
            broker_excluded_rows += 1
        if not str(row.get("kill_zone_position") or "").startswith("in_"):
            off_kz_rows += 1
        if row.get("selected_policy") != "be_after_trigger":
            same_bar_rows += 1
        if row.get("delta_repaired_vs_old_gtos_r") is not None and float(
            row["delta_repaired_vs_old_gtos_r"]
        ) <= 0:
            nonpositive_delta_vs_old += 1

    if ledger_rows != repaired["selected_count"]:
        failures.append(f"ledger_rows_mismatch:{ledger_rows}!={repaired['selected_count']}")
    if ledger_rows <= 6479:
        failures.append(f"repaired_overlay_still_narrow_fvg_slice:{ledger_rows}")
    if ledger_rows < 20000:
        failures.append(f"repaired_overlay_trade_count_collapsed:{ledger_rows}")
    if repaired["expectancy_r"] <= 0:
        failures.append("repaired_overlay_nonpositive_expectancy")
    if repaired["profit_factor"] is None or repaired["profit_factor"] <= 1.0:
        failures.append("repaired_overlay_profit_factor_not_positive_ev")
    if repaired["win_rate"] is None or repaired["win_rate"] <= 0.5:
        failures.append("repaired_overlay_win_rate_not_above_half")
    if repaired["expectancy_r"] <= comparators["old_gtos_live_current_j46_j49"]["expectancy_r"]:
        failures.append("repaired_overlay_does_not_beat_old_gtos")
    if repaired["expectancy_r"] <= comparators["fixed_1_5r"]["expectancy_r"]:
        failures.append("repaired_overlay_does_not_beat_fixed_1_5r")
    if repaired["expectancy_r"] <= comparators["j46_j49"]["expectancy_r"]:
        failures.append("repaired_overlay_does_not_beat_j46_j49")
    if REQUIRED_ACTIVATED_FRAMEWORKS - set(frameworks):
        failures.append(
            "repaired_overlay_missing_activated_frameworks:"
            + ",".join(sorted(REQUIRED_ACTIVATED_FRAMEWORKS - set(frameworks)))
        )
    if REQUIRED_ACTIVATED_SYMBOLS - set(symbols):
        failures.append(
            "repaired_overlay_missing_activated_symbols:"
            + ",".join(sorted(REQUIRED_ACTIVATED_SYMBOLS - set(symbols)))
        )
    if len(symbols) < 8:
        failures.append(f"repaired_overlay_market_coverage_collapsed:{dict(symbols)}")
    if len(sessions) < 3:
        failures.append(f"repaired_overlay_session_coverage_collapsed:{dict(sessions)}")
    if non_follow_rows:
        failures.append(f"non_follow_rows_received_execution_effect:{non_follow_rows}")
    if broker_excluded_rows:
        failures.append(f"broker_excluded_rows_received_execution_effect:{broker_excluded_rows}")
    if off_kz_rows:
        failures.append(f"off_kz_rows_received_execution_effect:{off_kz_rows}")
    if same_bar_rows:
        failures.append(f"non_be_policy_rows_in_repaired_overlay:{same_bar_rows}")
    if selected_policy_counts.get("be_after_trigger", 0) != ledger_rows:
        failures.append("selected_policy_not_uniform_be_after_trigger")
    if source_windows.get("False", 0) <= 0:
        warnings.append("no_source_incomplete_rows_in_repaired_overlay_to_exercise_capture_monitoring")
    if selector["source_window_complete_required_for_selection"] is not False:
        failures.append("source_completeness_still_used_as_selection_rule")
    if set(selector.get("primary_frameworks", [])) != REQUIRED_ACTIVATED_FRAMEWORKS:
        failures.append("selector_contract_not_full_market_framework_set")
    if not enumeration.get("failing_stage12_semantic_gates"):
        failures.append("pre_repair_stage12_failure_enumeration_missing")

    overlay_repair = overlay.get("stage13_activation_repair", {})
    if overlay_repair.get("summary_path") != rel(SUMMARY_PATH):
        failures.append("overlay_missing_stage13_repair_summary_path")
    production_cfg = overlay["semantic_gated_production_activation_overlay_candidate"][
        "config"
    ]["gtos_vnext_runtime"]
    if production_cfg.get("moonshot_dynamic_execution_router_ordered_path_scope") != "selected_policy":
        failures.append("production_overlay_ordered_path_scope_not_selected_policy")
    if production_cfg.get("moonshot_dynamic_execution_router_source_window_complete_blocks_activation") is not False:
        failures.append("production_overlay_still_blocks_on_source_window_complete")
    if production_cfg.get("moonshot_dynamic_execution_router_require_configured_kill_zone") is not True:
        failures.append("production_overlay_does_not_require_configured_kill_zone")
    if set(production_cfg.get("moonshot_dynamic_execution_router_activated_frameworks", [])) != REQUIRED_ACTIVATED_FRAMEWORKS:
        failures.append("production_overlay_missing_full_market_activated_frameworks")

    if comparators["condition_router"]["expectancy_r"] > repaired["expectancy_r"]:
        warnings.append(
            "condition_router_raw_subset_expectancy_higher_but_stage11_prop_default_retains_be_after_trigger"
        )

    status = "passed" if not failures else "failed"
    result = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage13_activation_overlay_repair_verifier_v1",
        "generated_at_utc": generated_at,
        "status": status,
        "failures": failures,
        "warnings": warnings,
        "ledger_rows": ledger_rows,
        "repaired_overlay_metrics": repaired,
        "comparator_metrics": comparators,
        "symbol_counts": dict(sorted(symbols.items())),
        "framework_counts": dict(sorted(frameworks.items())),
        "session_counts": dict(sorted(sessions.items())),
        "source_window_counts": dict(sorted(source_windows.items())),
        "branch_label_counts": dict(sorted(branch_labels.items())),
        "selected_policy_counts": dict(sorted(selected_policy_counts.items())),
        "nonpositive_delta_vs_old_rows": nonpositive_delta_vs_old,
        "failure_enumeration_rows": len(enumeration.get("failing_stage12_semantic_gates", [])),
    }
    write_json(VERIFIER_PATH, result)

    manifest = read_json(MANIFEST_PATH)
    outputs = manifest.setdefault("outputs", [])
    entry = {"path": VERIFIER_PATH.name, "stage": "stage_13", "status": "created", "result": status}
    for index, existing in enumerate(outputs):
        if isinstance(existing, dict) and existing.get("path") == entry["path"]:
            outputs[index] = entry
            break
    else:
        outputs.append(entry)
    manifest["last_updated_utc"] = generated_at
    write_json(MANIFEST_PATH, manifest)

    state = read_json(STATE_PATH)
    state.setdefault("evidence_rows_scanned", {})[
        "stage13_repair_verifier_rows_scanned"
    ] = ledger_rows
    state.setdefault("tests_verifiers_run", []).append(
        {
            "command": rel(Path(__file__)),
            "result": status,
            "timestamp_utc": generated_at,
        }
    )
    state["last_updated_utc"] = generated_at
    write_json(STATE_PATH, state)

    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage13_activation_overlay_repair_verifier_completed",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": status,
            "rows_scanned": ledger_rows,
            "failures": failures,
            "warnings": warnings,
        },
    )
    print(json.dumps({"status": status, "rows": ledger_rows, "warnings": warnings}, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
