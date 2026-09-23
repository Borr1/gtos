"""Build the vNext replay preregistration manifest.

This script is intentionally read-only with respect to GTOS runtime behavior.
It freezes the current config/runtime/artifact universe before any replay
outcome rows are generated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
BUILDER_ROUTE = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder"
)

PREREG_PATH = ROUTE_DIR / "VNEXT_REPLAY_PREREGISTRATION_MANIFEST_2026-05-24.json"
ARTIFACT_COVERAGE_PATH = (
    ROUTE_DIR / "VNEXT_REPLAY_RUNTIME_ARTIFACT_COVERAGE_LEDGER_2026-05-24.jsonl"
)
SOURCE_GAP_PATH = ROUTE_DIR / "VNEXT_REPLAY_SOURCE_GAP_LEDGER_2026-05-24.jsonl"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"

CONFIG_PATH = Path("config/agent_config.yaml")
RUNTIME_PATH = Path("src/components/gtos_vnext_runtime.py")
FREEZE_REPORT_PATH = BUILDER_ROUTE / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_REPORT_2026-05-23.md"
FREEZE_SUMMARY_PATH = BUILDER_ROUTE / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_SUMMARY_2026-05-23.json"
FREEZE_LEDGER_PATH = (
    BUILDER_ROUTE / "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_CLASSIFICATION_LEDGER_2026-05-23.jsonl"
)
MASTER_LEDGER_PATH = (
    BUILDER_ROUTE / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"
)
MASTER_SUMMARY_PATH = (
    BUILDER_ROUTE / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json"
)
BATCH_LEDGER_PATH = BUILDER_ROUTE / "GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"
BATCH_SUMMARY_PATH = BUILDER_ROUTE / "GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json"
OUTPUT_MANIFEST_SOURCE_PATH = BUILDER_ROUTE / "GTOS_VNEXT_OUTPUT_MANIFEST_2026-05-18.json"

REPLAY_MODES = [
    "current_config_shadow",
    "hypothetical_activated_vnext",
    "bar_close_m15",
    "m1_path_aware",
    "m5_path_aware",
    "tick_or_sierra_path_aware",
    "ohlc_only_proxy",
    "missing_source",
]

METRIC_FAMILIES = [
    "candidate_events",
    "evaluated_events",
    "skipped_events_by_reason",
    "decision_counts_follow_avoid_mixed_legacy",
    "matched_artifact_rows",
    "broad_blank_anchor_matches",
    "risk_multiplier_distribution",
    "zero_risk_blocks",
    "pre_ai_action_distribution",
    "ai_calls_allowed_skipped_narrowed",
    "entry_touch_fill_miss",
    "stop_first_target_first_timeout_ambiguous",
    "trade_count_win_rate_mean_median_total_r",
    "monthly_r_profit_factor_drawdown_loss_streak",
    "mfe_mae",
    "funded_phase_pass_and_breach_rates",
    "ablation_delta_by_family",
    "mixed_contribution_delta",
]

ABLATION_FAMILIES = [
    "current_baseline_vs_full_vnext",
    "current_default_off_shadow_vs_hypothetical_activated_vnext",
    "full_vnext_minus_each_major_evidence_family",
    "full_vnext_minus_legacy_v2_v3_v4_pressure",
    "full_vnext_without_mixed_pressure_context",
    "full_vnext_only_strong_follow_avoid",
    "m15_only_vs_m1_m5_tick_sierra_path_aware",
    "source_acquisition_guards_on_off_analysis_only",
    "nofill_pending_policy_on_off_analysis_only",
    "ai_route_narrowing_skip_effects",
    "risk_multiplier_zero_risk_block_effects",
    "entry_exit_trailing_partial_effects",
]

DATA_ROOTS = [
    "data/",
    "data/historical_2026/",
    "data/mt5_research_exports/",
    "data/sierrachart_exports/",
    "data/sierra_ohlcv_roots/",
    "data/ticks/",
    "shadow_logs/",
    "knowledge_base/",
    "research/science_program_2026_05/",
    "C:/tmp/",
    "C:/SierraChart/",
]

FORBIDDEN_SURFACES = [
    "live trading change",
    "broker/account/order/deal/position mutation",
    "production-change promotion",
    "paid API/vendor call without explicit owner approval",
    "remote push without explicit owner instruction",
    "outcome-aware runtime tuning",
]


def repo_path(path: Path | str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    if os.name == "nt":
        resolved = str(candidate.resolve(strict=False))
        if not resolved.startswith("\\\\?\\"):
            return Path("\\\\?\\" + resolved)
    return candidate


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def file_meta(path: Path | str, *, source_kind: str) -> dict[str, Any]:
    rel = str(Path(path).as_posix())
    abs_path = repo_path(path)
    exists = abs_path.exists()
    is_file = abs_path.is_file()
    first_bytes = b""
    if is_file:
        with abs_path.open("rb") as handle:
            first_bytes = handle.read(160)
    is_lfs_pointer = first_bytes.startswith(b"version https://git-lfs.github.com/spec/v1")
    return {
        "path": rel,
        "source_kind": source_kind,
        "exists": exists,
        "is_file": is_file,
        "bytes": abs_path.stat().st_size if is_file else None,
        "lines": line_count(abs_path) if is_file else None,
        "sha256": sha256_file(abs_path) if is_file else None,
        "is_lfs_pointer_file": is_lfs_pointer,
    }


def load_json(path: Path | str) -> Any:
    with repo_path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config() -> dict[str, Any]:
    with repo_path(CONFIG_PATH).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def stable_json_bytes(data: Any) -> bytes:
    return json.dumps(data, indent=2, sort_keys=True).encode("utf-8")


def stable_json_hash(data: Any) -> str:
    return hashlib.sha256(stable_json_bytes(data)).hexdigest()


def read_jsonl(path: Path | str) -> Iterable[dict[str, Any]]:
    with repo_path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def artifact_coverage_rows(artifact_paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen = Counter(artifact_paths)
    for index, path in enumerate(artifact_paths, start=1):
        meta = file_meta(path, source_kind="active_config_runtime_artifact")
        rows.append(
            {
                "schema_version": "vnext_replay_runtime_artifact_coverage_v1",
                "artifact_index": index,
                "artifact_path": meta["path"],
                "configured_duplicate_count": seen[path],
                "exists": meta["exists"],
                "bytes": meta["bytes"],
                "lines": meta["lines"],
                "sha256": meta["sha256"],
                "is_lfs_pointer_file": meta["is_lfs_pointer_file"],
                "coverage_status": "PRESENT_HASHED" if meta["exists"] else "MISSING_CONFIG_ARTIFACT",
                "runtime_pressure_source": "active_config_artifact_paths",
            }
        )
    return rows


def freeze_ledger_counts() -> dict[str, Any]:
    class_counts: Counter[str] = Counter()
    pressure_allowed = 0
    legacy_override_allowed = 0
    row_count = 0
    for row in read_jsonl(FREEZE_LEDGER_PATH):
        row_count += 1
        class_counts[str(row.get("freeze_class") or "")] += 1
        if row.get("runtime_pressure_allowed") is True:
            pressure_allowed += 1
        if row.get("legacy_support_override_allowed") is True:
            legacy_override_allowed += 1
    return {
        "rows": row_count,
        "freeze_class_counts": dict(sorted(class_counts.items())),
        "runtime_pressure_allowed_rows": pressure_allowed,
        "legacy_support_override_allowed_rows": legacy_override_allowed,
    }


def build_manifest() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cfg = load_config()
    runtime_cfg = cfg.get("gtos_vnext_runtime", {}) or {}
    artifact_paths = [str(path) for path in runtime_cfg.get("artifact_paths", [])]
    artifact_rows = artifact_coverage_rows(artifact_paths)
    missing_artifacts = [row for row in artifact_rows if not row["exists"]]
    freeze_summary = load_json(FREEZE_SUMMARY_PATH)
    master_summary = load_json(MASTER_SUMMARY_PATH)
    batch_summary = load_json(BATCH_SUMMARY_PATH)
    key_files = [
        CONFIG_PATH,
        RUNTIME_PATH,
        FREEZE_REPORT_PATH,
        FREEZE_SUMMARY_PATH,
        FREEZE_LEDGER_PATH,
        MASTER_LEDGER_PATH,
        MASTER_SUMMARY_PATH,
        BATCH_LEDGER_PATH,
        BATCH_SUMMARY_PATH,
        OUTPUT_MANIFEST_SOURCE_PATH,
    ]
    key_file_meta = [file_meta(path, source_kind="frozen_system_input") for path in key_files]
    manifest = {
        "schema_version": "vnext_replay_preregistration_manifest_v1",
        "generated_utc": utc_now(),
        "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
        "evidence_class": "frozen-current-vnext replay, path-aware simulation, ablation, MIXED resolution, and prop-firm measurement",
        "git": {
            "head": git_output(["rev-parse", "HEAD"]),
            "head_short": git_output(["rev-parse", "--short", "HEAD"]),
            "status_short": git_output(["status", "--short"]).splitlines(),
        },
        "context_lock": {
            "live_state_regenerated_before_manifest": True,
            "session_spine_path": (
                "research/science_program_2026_05/06_outcome_testing/"
                "gtos_vnext_replay_truth_engine/"
                "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
            ),
            "controlling_prompt_path": (
                "research/science_program_2026_05/04_goal_prompts/"
                "VNEXT_REPLAY_TRUTH_ENGINE_AND_SATURATED_ABLATION_GOAL_PROMPT_2026-05-24.md"
            ),
            "doctrine_files": [
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/orchestrator_successor_operating_brief.md",
                ".context/00_core/orchestrator_methodology_hardening_controls.md",
                ".context/00_core/parallel_goal_merge_playbook.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/local_heavy_data_inventory.md",
            ],
        },
        "frozen_system": {
            "config_path": str(CONFIG_PATH.as_posix()),
            "runtime_path": str(RUNTIME_PATH.as_posix()),
            "config_hash_sha256": file_meta(CONFIG_PATH, source_kind="frozen_system_input")["sha256"],
            "runtime_hash_sha256": file_meta(RUNTIME_PATH, source_kind="frozen_system_input")["sha256"],
            "runtime_enabled": bool(runtime_cfg.get("enabled")),
            "current_config_apply_to_execution": bool(runtime_cfg.get("apply_to_execution")),
            "current_config_pre_ai_enabled": bool(runtime_cfg.get("pre_ai_enabled")),
            "current_config_pre_ai_apply_to_ai_call": bool(
                runtime_cfg.get("pre_ai_apply_to_ai_call")
            ),
            "current_config_risk_adjustment_enabled": bool(
                runtime_cfg.get("risk_adjustment_enabled")
            ),
            "current_config_pending_policy_enabled": bool(runtime_cfg.get("pending_policy_enabled")),
            "current_config_conflict_resolution": runtime_cfg.get("conflict_resolution"),
            "pre_ai_route_timeframes": runtime_cfg.get("pre_ai_route_timeframes"),
            "post_l2_route_timeframes": runtime_cfg.get("post_l2_route_timeframes"),
            "pre_ai_route_horizons": runtime_cfg.get("pre_ai_route_horizons"),
            "post_l2_route_horizons": runtime_cfg.get("post_l2_route_horizons"),
            "pre_ai_route_frameworks": runtime_cfg.get("pre_ai_route_frameworks"),
        },
        "freeze_facts": {
            "freeze_summary": {
                "total_units": freeze_summary.get("total_units"),
                "pre_freeze_closed_units": freeze_summary.get("pre_freeze_closed_units"),
                "pre_freeze_open_not_started_units": freeze_summary.get(
                    "pre_freeze_open_not_started_units"
                ),
                "final_freeze_coverage_pct": freeze_summary.get("final_freeze_coverage_pct"),
                "generated_runtime_artifact_count": freeze_summary.get(
                    "generated_runtime_artifact_count"
                ),
                "generated_runtime_row_count": freeze_summary.get(
                    "generated_runtime_row_count"
                ),
                "runtime_decision_counts": freeze_summary.get("runtime_decision_counts"),
                "freeze_class_counts": freeze_summary.get("freeze_class_counts"),
            },
            "freeze_ledger_counts_recomputed": freeze_ledger_counts(),
            "master_state_counts": master_summary.get("state_counts"),
            "batch_executed_or_closed_wave_count": batch_summary.get(
                "executed_or_closed_wave_count"
            ),
            "batch_known_rows_represented": batch_summary.get("known_rows_represented"),
        },
        "key_file_hashes": key_file_meta,
        "runtime_artifact_universe": {
            "configured_artifact_path_count": len(artifact_paths),
            "existing_artifact_path_count": sum(1 for row in artifact_rows if row["exists"]),
            "missing_artifact_path_count": len(missing_artifacts),
            "duplicate_configured_path_count": sum(
                count - 1 for count in Counter(artifact_paths).values() if count > 1
            ),
            "total_existing_artifact_bytes": sum(row["bytes"] or 0 for row in artifact_rows),
            "total_existing_artifact_lines": sum(row["lines"] or 0 for row in artifact_rows),
            "coverage_ledger_path": str(ARTIFACT_COVERAGE_PATH.relative_to(REPO_ROOT).as_posix()),
            "artifact_path_list_hash_sha256": stable_json_hash(artifact_paths),
        },
        "data_universe_roots_to_inventory_next": DATA_ROOTS,
        "replay_modes_preregistered": REPLAY_MODES,
        "metric_families_preregistered": METRIC_FAMILIES,
        "ablation_families_preregistered": ABLATION_FAMILIES,
        "missing_data_policy": {
            "source_gap_is_not_terminal": True,
            "acquisition_ladder": [
                "repo-local files and committed manifests",
                "absolute local repo data roots",
                "prior worktrees and C:/tmp caches as leads",
                "Sierra/tick/OHLC local roots",
                "shadow/research artifacts and reconstruction/proxy routes",
                "read-only MT5 export paths when physically available and lane-permitted",
                "explicit owner approval before paid/API/vendor calls",
            ],
        },
        "forbidden_surfaces": FORBIDDEN_SURFACES,
        "baseline_activation_boundary": {
            "current_config_shadow": "Use active config exactly as read from disk.",
            "hypothetical_activated_vnext": (
                "Simulate execution-effect controls as enabled without changing production config."
            ),
            "production_config_mutation_allowed": False,
        },
    }
    source_gap_rows: list[dict[str, Any]] = []
    for row in missing_artifacts:
        source_gap_rows.append(
            {
                "schema_version": "vnext_replay_source_gap_v1",
                "gap_type": "missing_configured_runtime_artifact",
                "source_path": row["artifact_path"],
                "stage_id": "STAGE_01_PREREGISTER_SYSTEM_AND_DATA_UNIVERSE",
                "attempts_executed": [
                    "artifact path read from active config",
                    "filesystem existence check at repo-relative path",
                ],
                "terminal_status": "NOT_TERMINAL_CONTINUE_SOURCE_ACQUISITION",
                "next_action": "Resolve during STAGE_02 exhaustive source acquisition if still missing.",
            }
        )
    if not source_gap_rows:
        source_gap_rows.append(
            {
                "schema_version": "vnext_replay_source_gap_v1",
                "gap_type": "configured_runtime_artifacts",
                "stage_id": "STAGE_01_PREREGISTER_SYSTEM_AND_DATA_UNIVERSE",
                "attempts_executed": [
                    "artifact path read from active config",
                    "filesystem existence check at repo-relative path",
                    "sha256 hash and line count computed for every existing configured artifact",
                ],
                "terminal_status": "NO_MISSING_CONFIGURED_RUNTIME_ARTIFACTS_AT_PREREGISTRATION",
                "next_action": "Proceed to STAGE_02 data root inventory and market/source acquisition.",
            }
        )
    return manifest, artifact_rows, source_gap_rows


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_outputs() -> dict[str, Any]:
    manifest, artifact_rows, source_gap_rows = build_manifest()
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(PREREG_PATH, manifest)
    write_jsonl(ARTIFACT_COVERAGE_PATH, artifact_rows)
    write_jsonl(SOURCE_GAP_PATH, source_gap_rows)
    output_rows = [
        file_meta(PREREG_PATH.relative_to(REPO_ROOT), source_kind="generated_replay_output"),
        file_meta(
            ARTIFACT_COVERAGE_PATH.relative_to(REPO_ROOT),
            source_kind="generated_replay_output",
        ),
        file_meta(SOURCE_GAP_PATH.relative_to(REPO_ROOT), source_kind="generated_replay_output"),
    ]
    output_manifest = {
        "schema_version": "vnext_replay_output_manifest_v1",
        "generated_utc": utc_now(),
        "route_id": manifest["route_id"],
        "outputs": output_rows,
        "next_stage": "STAGE_02_EXHAUSTIVE_DATA_INVENTORY_AND_SOURCE_ACQUISITION",
    }
    write_json(OUTPUT_MANIFEST_PATH, output_manifest)
    return output_manifest


def check_outputs() -> None:
    expected_manifest, expected_artifact_rows, expected_gap_rows = build_manifest()
    existing_manifest = load_json(PREREG_PATH.relative_to(REPO_ROOT))
    volatile_keys = {"generated_utc"}
    for key in volatile_keys:
        expected_manifest.pop(key, None)
        existing_manifest.pop(key, None)
    if existing_manifest != expected_manifest:
        raise AssertionError("Preregistration manifest is stale; rerun builder without --check")
    existing_artifact_rows = list(read_jsonl(ARTIFACT_COVERAGE_PATH.relative_to(REPO_ROOT)))
    if existing_artifact_rows != expected_artifact_rows:
        raise AssertionError("Runtime artifact coverage ledger is stale")
    existing_gap_rows = list(read_jsonl(SOURCE_GAP_PATH.relative_to(REPO_ROOT)))
    if existing_gap_rows != expected_gap_rows:
        raise AssertionError("Source gap ledger is stale")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify existing outputs")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext replay preregistration check passed")
        return
    output_manifest = build_outputs()
    print(json.dumps(output_manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
