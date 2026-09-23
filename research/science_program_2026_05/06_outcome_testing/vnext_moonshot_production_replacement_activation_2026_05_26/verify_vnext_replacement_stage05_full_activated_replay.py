from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_05_full_activated_historical_replay"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE_ID}.json"
SHARD_MANIFEST_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE_ID}.jsonl"
)
HASH_MANIFEST_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_HASH_MANIFEST_{DATE_ID}.json"
)
VERIFIER_PATH = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE_ID}.json"
)
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE_ID}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE_ID}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE_ID}.jsonl"
FULL_CANDIDATE_SUMMARY = (
    FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
)
MOONSHOT_DYNAMIC_SUMMARY = (
    MOONSHOT_DIR / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fnum(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def add_total(totals: defaultdict[str, float], key: str, value: Any) -> None:
    number = fnum(value)
    if number is not None:
        totals[key] += number


def update_output_manifest() -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    entry = {
        "path": "VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_2026-05-26.json",
        "stage": "stage_05",
        "status": "created",
    }
    if isinstance(outputs, list):
        for index, item in enumerate(outputs):
            if isinstance(item, dict) and item.get("path") == entry["path"]:
                outputs[index] = entry
                break
        else:
            outputs.append(entry)
    elif isinstance(outputs, dict):
        outputs["stage05_full_activated_replay_verifier"] = rel(VERIFIER_PATH)
    manifest["last_updated_utc"] = utc_now()
    write_json(OUTPUT_MANIFEST, manifest)


def update_state(result: dict[str, Any]) -> None:
    state = read_json(STATE_PATH)
    state.setdefault("tests_verifiers_run", []).append(
        {
            "command": rel(Path(__file__)),
            "result": result["status"],
            "timestamp_utc": result["generated_at_utc"],
        }
    )
    state.setdefault("evidence_rows_scanned", {})[
        "stage05_verifier_rows_scanned"
    ] = result["scan_counts"]["output_rows_scanned"]
    write_json(STATE_PATH, state)


def main() -> None:
    summary = read_json(SUMMARY_PATH)
    full_candidate_summary = read_json(FULL_CANDIDATE_SUMMARY)
    dynamic_summary = read_json(MOONSHOT_DYNAMIC_SUMMARY)
    shard_rows = list(iter_jsonl(SHARD_MANIFEST_PATH))
    failures: list[str] = []
    warnings: list[str] = []
    output_rows = 0
    dynamic_available_rows = 0
    activated_effect_rows = 0
    unique_candidate_ids: set[str] = set()
    disposition_counts: Counter[str] = Counter()
    framework_counts: Counter[str] = Counter()
    path_mode_counts: Counter[str] = Counter()
    nested_source_mode_counts: Counter[str] = Counter()
    path_truth_status_counts: Counter[str] = Counter()
    activated_selected_policy_counts: Counter[str] = Counter()
    condition_selected_policy_counts: Counter[str] = Counter()
    totals: defaultdict[str, float] = defaultdict(float)
    fixed_as_activation_rows = 0
    old_live_as_activation_rows = 0
    live_or_broker_surface_rows = 0
    paid_ai_rows = 0
    missing_hash_count = 0

    for manifest_row in shard_rows:
        output_path = REPO_ROOT / manifest_row["output_chunk_path"]
        if not output_path.exists():
            failures.append(f"missing_output_shard:{manifest_row['output_chunk_path']}")
            continue
        if sha256_file(output_path) != manifest_row["output_sha256"]:
            failures.append(f"output_sha_mismatch:{manifest_row['output_chunk_path']}")
        row_count = 0
        for row in iter_gzip_jsonl(output_path):
            row_count += 1
            output_rows += 1
            candidate_id = row.get("candidate_id")
            if candidate_id:
                unique_candidate_ids.add(candidate_id)
            if row.get("no_live_trading_or_broker_mutation") is not True:
                live_or_broker_surface_rows += 1
            if (row.get("ai_policy_scenario") or {}).get("paid_ai_or_vendor_call") is True:
                paid_ai_rows += 1
            disposition = str(row.get("activated_replay_disposition"))
            disposition_counts[disposition] += 1
            framework_counts[str(row.get("framework"))] += 1
            dynamic = row.get("dynamic_policy_replay") or {}
            if dynamic.get("available") is True:
                dynamic_available_rows += 1
            activated = row.get("activated_default_router_projection") or {}
            selected_policy = activated.get("selected_policy")
            if activated.get("activated_runtime_effect_would_apply") is True:
                activated_effect_rows += 1
                activated_selected_policy_counts[str(selected_policy)] += 1
                if selected_policy == "legacy_fixed_1.5r":
                    fixed_as_activation_rows += 1
                if selected_policy == "live_current_j46_j49":
                    old_live_as_activation_rows += 1
                add_total(totals, "activated_runtime_effect_total_r", activated.get("selected_policy_final_r"))
            condition = row.get("condition_router_projection") or {}
            if condition.get("available") is True:
                condition_selected_policy_counts[str(condition.get("selected_policy"))] += 1
                add_total(totals, "condition_router_total_r", condition.get("selected_policy_final_r"))
            add_total(
                totals,
                "old_gtos_live_current_j46_j49_total_r",
                (row.get("old_gtos_current_shadow") or {}).get("final_r"),
            )
            add_total(
                totals,
                "legacy_fixed_1_5r_total_r",
                (row.get("legacy_fixed_1_5r_comparator") or {}).get("final_r"),
            )
            add_total(
                totals,
                "moonshot_be_after_trigger_total_r",
                (row.get("moonshot_be_after_trigger") or {}).get("final_r"),
            )
            for mode, path_row in (row.get("path_modes") or {}).items():
                if path_row is None:
                    continue
                path_mode_counts[mode] += 1
                nested_source_mode_counts[str(path_row.get("source_mode"))] += 1
                path_truth_status_counts[str(path_row.get("price_path_truth_status"))] += 1
                if path_row.get("source_sha256") in (None, "") and path_row.get(
                    "source_mode"
                ) not in {"MISSING_SOURCE", None}:
                    missing_hash_count += 1
        if row_count != manifest_row["output_rows"]:
            failures.append(
                f"row_count_mismatch:{manifest_row['output_chunk_path']}:{row_count}!={manifest_row['output_rows']}"
            )

    expected_candidates = full_candidate_summary["counts"]["candidate_rows"]
    expected_dynamic = dynamic_summary["replayable_candidate_rows"]
    if len(shard_rows) != 45:
        failures.append(f"shard_count_not_45:{len(shard_rows)}")
    if output_rows != expected_candidates:
        failures.append(f"candidate_coverage_mismatch:{output_rows}!={expected_candidates}")
    if len(unique_candidate_ids) != expected_candidates:
        failures.append(
            f"unique_candidate_id_mismatch:{len(unique_candidate_ids)}!={expected_candidates}"
        )
    if dynamic_available_rows != expected_dynamic:
        failures.append(f"dynamic_replay_row_mismatch:{dynamic_available_rows}!={expected_dynamic}")
    if dynamic_available_rows != summary["coverage"]["dynamic_policy_replay_rows"]:
        failures.append("summary_dynamic_count_mismatch")
    if activated_effect_rows != summary["coverage"]["activated_runtime_effect_rows"]:
        failures.append("summary_activated_effect_count_mismatch")
    if fixed_as_activation_rows:
        failures.append(f"fixed_1_5r_used_as_activation_truth:{fixed_as_activation_rows}")
    if old_live_as_activation_rows:
        failures.append(f"old_gtos_live_policy_used_as_activation_truth:{old_live_as_activation_rows}")
    if live_or_broker_surface_rows:
        failures.append(f"live_or_broker_surface_rows:{live_or_broker_surface_rows}")
    if paid_ai_rows:
        failures.append(f"paid_ai_rows:{paid_ai_rows}")
    required_modes = {"bar_close_m15", "m1_path_aware", "m5_path_aware", "tick_or_sierra_path_aware"}
    missing_modes = sorted(required_modes - set(path_mode_counts))
    if missing_modes:
        failures.append(f"nested_source_modes_missing:{missing_modes}")
    if nested_source_mode_counts.get("LOCAL_TICK_PARQUET", 0) <= 0:
        failures.append("tick_or_sierra_source_mode_collapsed")
    if nested_source_mode_counts.get("OHLC_M1_CSV", 0) <= 0:
        failures.append("m1_source_mode_collapsed")
    if nested_source_mode_counts.get("OHLC_M5_CSV", 0) <= 0:
        failures.append("m5_source_mode_collapsed")
    if missing_hash_count:
        warnings.append(f"source_rows_without_hash:{missing_hash_count}")
    activated_expectancy = (
        totals["activated_runtime_effect_total_r"] / activated_effect_rows
        if activated_effect_rows
        else None
    )
    if activated_expectancy is not None and activated_expectancy <= 0:
        warnings.append(
            "activated_source_bound_primary_rows_have_nonpositive_expectancy_stage12_must_not_apply_overlay"
        )

    result = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_full_activated_replay_verifier_v1",
        "generated_at_utc": utc_now(),
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "warnings": warnings,
        "scan_counts": {
            "shards_scanned": len(shard_rows),
            "output_rows_scanned": output_rows,
            "unique_candidate_ids": len(unique_candidate_ids),
            "dynamic_available_rows": dynamic_available_rows,
            "activated_effect_rows": activated_effect_rows,
        },
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "framework_counts": dict(sorted(framework_counts.items())),
        "nested_path_mode_counts": dict(sorted(path_mode_counts.items())),
        "nested_source_mode_counts": dict(sorted(nested_source_mode_counts.items())),
        "path_truth_status_counts": dict(sorted(path_truth_status_counts.items())),
        "activated_selected_policy_counts": dict(sorted(activated_selected_policy_counts.items())),
        "condition_selected_policy_counts": dict(sorted(condition_selected_policy_counts.items())),
        "scenario_totals_recomputed": dict(sorted(totals.items())),
        "scenario_expectancy_recomputed": {
            "old_gtos_live_current_j46_j49_all_replayable": totals[
                "old_gtos_live_current_j46_j49_total_r"
            ]
            / dynamic_available_rows
            if dynamic_available_rows
            else None,
            "legacy_fixed_1_5r_comparator_all_replayable": totals[
                "legacy_fixed_1_5r_total_r"
            ]
            / dynamic_available_rows
            if dynamic_available_rows
            else None,
            "moonshot_be_after_trigger_all_replayable": totals[
                "moonshot_be_after_trigger_total_r"
            ]
            / dynamic_available_rows
            if dynamic_available_rows
            else None,
            "condition_router_all_replayable": totals["condition_router_total_r"]
            / dynamic_available_rows
            if dynamic_available_rows
            else None,
            "activated_runtime_effect_source_bound_primary_only": activated_expectancy,
        },
        "hash_manifest_path": rel(HASH_MANIFEST_PATH),
        "summary_path": rel(SUMMARY_PATH),
        "verifier_path": rel(VERIFIER_PATH),
    }
    write_json(VERIFIER_PATH, result)
    update_output_manifest()
    update_state(result)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "timestamp_utc": result["generated_at_utc"],
            "status": f"verifier_{result['status']}",
            "failures": failures,
            "warnings": warnings,
            "rows_scanned": output_rows,
        },
    )
    print(json.dumps({"status": result["status"], "rows": output_rows, "warnings": warnings}, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
