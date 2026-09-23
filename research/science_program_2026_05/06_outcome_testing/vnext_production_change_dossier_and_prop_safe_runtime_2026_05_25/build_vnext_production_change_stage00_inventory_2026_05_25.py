from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

try:
    import yaml
except Exception:  # pragma: no cover - checked in verifier output
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_ID = "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25"
ROUTE_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25"
)
REPLAY_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_PRODUCTION_CHANGE_DOSSIER_AND_PROP_SAFE_RUNTIME_GOAL_PROMPT_2026-05-25.md"
)
STARTER_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_PRODUCTION_CHANGE_DOSSIER_AND_PROP_SAFE_RUNTIME_STARTER_2026-05-25.txt"
)
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json"
INVENTORY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_INPUT_INVENTORY_2026-05-25.json"

STAGES = [
    "STAGE_00_INPUT_INVENTORY",
    "STAGE_01_DECISION_SURFACE_GROUPING",
    "STAGE_02_PROMOTION_IMPLEMENTATION",
    "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION",
    "STAGE_04_MIXED_RESOLUTION",
    "STAGE_05_PROP_SAFE_SELECTOR",
    "STAGE_06_LTF_ENTRY_NOFILL_ENGINE",
    "STAGE_07_AI_POLICY",
    "STAGE_08_AI_SUPERVISOR",
    "STAGE_09_FORWARD_ONLY_REPLAY",
    "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER",
]

REQUIRED_REPLAY_ARTIFACTS = {
    "terminal_final_report": "VNEXT_FULL_REPLAY_FINAL_REPORT_2026-05-24.md",
    "terminal_verification_result": "VNEXT_FULL_REPLAY_FINAL_VERIFICATION_RESULT_2026-05-24.json",
    "terminal_session_state": "VNEXT_FULL_REPLAY_SESSION_STATE_2026-05-24.json",
    "terminal_completion_audit": "VNEXT_FULL_REPLAY_COMPLETION_AUDIT_2026-05-24.json",
    "terminal_output_manifest": "VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_2026-05-24.json",
    "terminal_final_packaging_manifest": "VNEXT_FULL_REPLAY_FINAL_PACKAGING_MANIFEST_2026-05-24.json",
    "final_decision_map": "VNEXT_FULL_REPLAY_FINAL_DECISION_MAP_2026-05-24.jsonl",
    "terminal_decision_ledger": "VNEXT_FULL_REPLAY_TERMINAL_DECISION_LEDGER_2026-05-24.jsonl",
    "promotion_kill_repair_map": "VNEXT_FULL_REPLAY_PROMOTION_KILL_REPAIR_MAP_2026-05-24.json",
    "metrics_summary": "VNEXT_FULL_REPLAY_METRICS_SUMMARY_2026-05-24.json",
    "prop_metrics_summary": "VNEXT_FULL_REPLAY_PROP_FIRM_METRICS_2026-05-24.json",
    "prop_metrics_ledger": "VNEXT_FULL_REPLAY_PROP_FIRM_METRICS_2026-05-24.jsonl",
    "mixed_resolution_summary": "VNEXT_FULL_REPLAY_MIXED_RESOLUTION_SUMMARY_2026-05-24.json",
    "mixed_resolution_ledger": "VNEXT_FULL_REPLAY_MIXED_RESOLUTION_LEDGER_2026-05-24.jsonl",
    "line_accountability_audit": "VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_2026-05-24.jsonl",
    "active_question_ledger": "VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_2026-05-24.jsonl",
    "ablation_metrics_ledger": "VNEXT_FULL_REPLAY_ABLATION_METRICS_LEDGER_2026-05-24.jsonl",
    "ablation_ledger": "VNEXT_FULL_REPLAY_ABLATION_LEDGER_2026-05-24.jsonl",
    "robustness_ledger": "VNEXT_FULL_REPLAY_ROBUSTNESS_LEDGER_2026-05-24.jsonl",
    "robustness_prop_metrics_ledger": "VNEXT_FULL_REPLAY_ROBUSTNESS_PROP_METRICS_LEDGER_2026-05-24.jsonl",
    "behavioral_forensics_ledger": "VNEXT_FULL_REPLAY_BEHAVIORAL_FORENSICS_LEDGER_2026-05-24.jsonl",
    "nofill_pending_lifecycle_ledger": "VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_2026-05-24.jsonl",
    "path_outcome_r_ledger": "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl",
    "m15_vs_ltf_disagreement_ledger": "VNEXT_FULL_REPLAY_M15_VS_LTF_DISAGREEMENT_LEDGER_2026-05-24.jsonl",
    "missed_winner_avoided_loser_ledger": "VNEXT_FULL_REPLAY_MISSED_WINNER_AVOIDED_LOSER_LEDGER_2026-05-24.jsonl",
    "runtime_trace_ledger": "VNEXT_FULL_REPLAY_RUNTIME_TRACE_LEDGER_2026-05-24.jsonl",
    "runtime_event_cache_ledger": "VNEXT_FULL_REPLAY_RUNTIME_EVENT_CACHE_LEDGER_2026-05-24.jsonl",
    "runtime_artifact_load_ledger": "VNEXT_FULL_REPLAY_RUNTIME_ARTIFACT_LOAD_LEDGER_2026-05-24.jsonl",
    "source_repair_proof_ledger": "VNEXT_FULL_REPLAY_SOURCE_REPAIR_PROOF_LEDGER_2026-05-24.jsonl",
    "candidate_generation_ledger": "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_LEDGER_2026-05-24.jsonl",
    "denominator_disposition_ledger": "VNEXT_FULL_REPLAY_DENOMINATOR_DISPOSITION_LEDGER_2026-05-24.jsonl",
    "market_state_packet_ledger": "VNEXT_FULL_REPLAY_MARKET_STATE_PACKET_LEDGER_2026-05-24.jsonl",
    "market_state_ledger": "VNEXT_FULL_REPLAY_MARKET_STATE_LEDGER_2026-05-24.jsonl",
    "dominance_and_pollution_ledger": "VNEXT_FULL_REPLAY_DOMINANCE_AND_POLLUTION_LEDGER_2026-05-24.jsonl",
    "null_unknown_field_audit": "VNEXT_FULL_REPLAY_NULL_UNKNOWN_FIELD_AUDIT_2026-05-24.jsonl",
    "source_acquisition_ledger": "VNEXT_FULL_REPLAY_SOURCE_ACQUISITION_LEDGER_2026-05-24.jsonl",
    "runtime_artifact_coverage_ledger": "VNEXT_FULL_REPLAY_RUNTIME_ARTIFACT_COVERAGE_LEDGER_2026-05-24.jsonl",
}

RUNTIME_SURFACE_PATHS = [
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "src/components/primary_analyzer.py",
    "src/components/permissions.py",
    "src/components/market_state.py",
    "config/agent_config.yaml",
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_primary_analyzer.py",
    "tests/test_side_aware_sizing.py",
    "tests/test_verify_shadow_log_integrity.py",
]

SHADOW_LOG_PATHS = [
    "shadow_logs/malformed_responses.jsonl",
    "shadow_logs/candidate_ltf_path_order.jsonl",
    "shadow_logs/pending_limit_lifecycle.jsonl",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl",
    "shadow_logs/ai_narrowing_policy_shadow_evaluations.jsonl",
    "shadow_logs/candidate_path_contract_audit.jsonl",
    "shadow_logs/nofill_forward_source_capture.jsonl",
    "shadow_logs/opportunity_lifecycle_audit.jsonl",
    "shadow_logs/live_candidate_opportunity_clusters.jsonl",
    "shadow_logs/live_candidate_strategy_rollups.jsonl",
    "shadow_logs/source_diagnostic_intelligence.jsonl",
    "shadow_logs/proxy_blocker_status.jsonl",
    "shadow_logs/external_source_blocker_status.jsonl",
    "shadow_logs/gtos_vnext_runtime_decisions.jsonl",
]

COUNTER_FIELDS = {
    "action",
    "action_class",
    "baseline_decision",
    "decision",
    "decision_class",
    "decision_source",
    "evidence_family",
    "fill_or_no_fill_state",
    "framework",
    "group_scope",
    "implementation_decision",
    "market_timeframe",
    "mixed_resolution_class",
    "next_required_action",
    "path_source_mode",
    "phase_target",
    "recommended_runtime_action",
    "route_family",
    "runtime_mode",
    "scenario",
    "schema_version",
    "session_bucket",
    "side",
    "source_component",
    "source_mode",
    "stage_id",
    "surface",
    "symbol",
    "target_stop_order_class",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def io_path(path: Path) -> Path:
    if sys.platform != "win32":
        return path
    resolved = path.resolve()
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    return Path("\\\\?\\" + text)


def path_exists(path: Path) -> bool:
    return io_path(path).exists()


def path_stat_size(path: Path) -> int | None:
    if not path_exists(path):
        return None
    return io_path(path).stat().st_size


def sha256_file(path: Path) -> str | None:
    local = io_path(path)
    if not local.exists() or not local.is_file():
        return None
    h = hashlib.sha256()
    with local.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def first_rows(iterator: Iterable[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iterator:
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def is_chunk_index_row(row: dict[str, Any]) -> bool:
    return {"chunk_path", "row_count", "sha256", "shard_status"}.issubset(row)


def safe_counter_value(value: Any) -> str:
    if value is None:
        return "<NULL>"
    if value == "":
        return "<BLANK>"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True)[:500]


def scan_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    row_count = 0
    key_counts: Counter[str] = Counter()
    null_counts: Counter[str] = Counter()
    blank_counts: Counter[str] = Counter()
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    samples: list[dict[str, Any]] = []
    numeric_sums: Counter[str] = Counter()

    for row in rows:
        row_count += 1
        if len(samples) < 3:
            samples.append(row)
        for key, value in row.items():
            key_counts[key] += 1
            if value is None:
                null_counts[key] += 1
            elif value == "":
                blank_counts[key] += 1
            if key in COUNTER_FIELDS:
                counters[key][safe_counter_value(value)] += 1
        r_metrics = row.get("r_metrics")
        if isinstance(r_metrics, dict):
            for key in (
                "denominator_count",
                "performance_count",
                "excluded_count",
                "null_r_count",
                "win_count",
                "loss_count",
                "zero_count",
                "total_r",
            ):
                value = r_metrics.get(key)
                if isinstance(value, (int, float)):
                    numeric_sums[f"r_metrics.{key}"] += float(value)
        for key in (
            "candidate_count",
            "counterfactual_change_count",
            "trade_count",
            "max_loss_streak",
            "calendar_clustering_max_trades_day",
        ):
            value = row.get(key)
            if isinstance(value, (int, float)):
                numeric_sums[key] += float(value)

    return {
        "row_count": row_count,
        "schema_keys": sorted(key_counts),
        "key_presence_counts": dict(sorted(key_counts.items())),
        "null_counts": {k: v for k, v in sorted(null_counts.items()) if v},
        "blank_counts": {k: v for k, v in sorted(blank_counts.items()) if v},
        "status_distributions": {
            key: dict(sorted(counter.items()))
            for key, counter in sorted(counters.items())
            if counter
        },
        "numeric_sums": dict(sorted(numeric_sums.items())),
        "sample_rows": samples,
    }


def summarize_jsonl_artifact(path: Path, *, scan_logical_rows: bool) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "kind": "jsonl",
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path),
    }
    if not path.exists():
        summary["status"] = "missing"
        return summary

    index_rows = list(iter_jsonl(path))
    summary["physical_line_count"] = len(index_rows)
    summary["physical_schema_keys"] = sorted({key for row in index_rows for key in row})
    summary["physical_sample_rows"] = index_rows[:3]
    if index_rows and all(is_chunk_index_row(row) for row in index_rows):
        summary["kind"] = "jsonl_chunk_index"
        summary["chunk_count"] = len(index_rows)
        summary["chunk_row_count_sum"] = sum(int(row.get("row_count") or 0) for row in index_rows)
        summary["chunk_status_counts"] = dict(Counter(row.get("shard_status") for row in index_rows))
        summary["source_path_counts"] = dict(Counter(row.get("source_path") for row in index_rows))
        missing_chunks: list[str] = []
        sha_mismatch_chunks: list[dict[str, str | None]] = []
        chunk_rows: list[dict[str, Any]] = []
        for index_row in index_rows:
            chunk_path = REPO_ROOT / str(index_row["chunk_path"])
            if not path_exists(chunk_path):
                missing_chunks.append(rel(chunk_path))
                continue
            actual_sha = sha256_file(chunk_path)
            if actual_sha != index_row.get("sha256"):
                sha_mismatch_chunks.append(
                    {
                        "chunk_path": rel(chunk_path),
                        "expected_sha256": index_row.get("sha256"),
                        "actual_sha256": actual_sha,
                    }
                )
            if len(chunk_rows) < 3:
                try:
                    chunk_rows.extend(first_rows(iter_gzip_jsonl(chunk_path), 3 - len(chunk_rows)))
                except Exception as exc:
                    summary.setdefault("chunk_sample_errors", []).append(
                        {"chunk_path": rel(chunk_path), "error": str(exc)}
                    )
        summary["missing_chunks"] = missing_chunks
        summary["sha_mismatch_chunks"] = sha_mismatch_chunks
        summary["logical_sample_rows"] = chunk_rows[:3]
        if scan_logical_rows:
            def logical_rows() -> Iterable[dict[str, Any]]:
                for index_row in index_rows:
                    chunk_path = REPO_ROOT / str(index_row["chunk_path"])
                    if path_exists(chunk_path):
                        yield from iter_gzip_jsonl(chunk_path)

            summary["logical_scan"] = scan_rows(logical_rows())
    else:
        summary["logical_scan"] = scan_rows(index_rows) if scan_logical_rows else {}
    return summary


def summarize_path(path: Path, *, scan_logical_rows: bool = False) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return summarize_jsonl_artifact(path, scan_logical_rows=scan_logical_rows)
    summary: dict[str, Any] = {
        "path": rel(path),
        "exists": path_exists(path),
        "kind": suffix.lstrip(".") or "file",
        "bytes": path_stat_size(path),
        "sha256": sha256_file(path),
    }
    if not path_exists(path):
        summary["status"] = "missing"
        return summary
    if suffix == ".json":
        payload = read_json(path)
        summary["json_top_level_type"] = type(payload).__name__
        if isinstance(payload, dict):
            summary["json_keys"] = sorted(payload)
            summary["selected_values"] = {
                key: payload.get(key)
                for key in (
                    "completion_status",
                    "completion_boundary",
                    "route_id",
                    "stage_id",
                    "goal_complete",
                    "first_incomplete_invariant",
                    "final_decision_counts",
                    "stage_counts",
                    "counts",
                    "prop_metric_decision_counts",
                    "mixed_resolution_class_counts",
                    "ok",
                    "failures",
                )
                if key in payload
            }
        elif isinstance(payload, list):
            summary["json_list_length"] = len(payload)
    elif suffix == ".md" or suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
        summary["line_count"] = text.count("\n") + (1 if text else 0)
        summary["first_400_chars"] = text[:400]
    return summary


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()


def line_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    with path.open("rb") as f:
        return sum(1 for _ in f)


def runtime_surface_inventory() -> list[dict[str, Any]]:
    surfaces = []
    for raw_path in RUNTIME_SURFACE_PATHS:
        path = REPO_ROOT / raw_path
        item = {
            "path": raw_path,
        "exists": path_exists(path),
        "bytes": path_stat_size(path),
        "sha256": sha256_file(path),
        "line_count": line_count(path),
    }
        if path_exists(path) and path.suffix == ".py":
            text = path.read_text(encoding="utf-8", errors="replace")
            names = []
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("class "):
                    names.append(stripped.split("(")[0].rstrip(":"))
            item["top_level_defs_or_classes_sample"] = names[:200]
            item["vnext_match_count"] = text.count("vnext") + text.count("gtos_vnext")
        surfaces.append(item)
    return surfaces


def config_inventory() -> dict[str, Any]:
    path = REPO_ROOT / "config/agent_config.yaml"
    result: dict[str, Any] = {
        "path": "config/agent_config.yaml",
        "exists": path_exists(path),
        "sha256": sha256_file(path),
        "yaml_available": yaml is not None,
    }
    if not path_exists(path) or yaml is None:
        return result
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    block = cfg.get("gtos_vnext_runtime", {}) if isinstance(cfg, dict) else {}
    result["gtos_vnext_runtime_selected"] = {
        key: block.get(key)
        for key in (
            "enabled",
            "mode",
            "apply_to_execution",
            "pre_ai_enabled",
            "pre_ai_apply_to_ai_call",
            "risk_adjustment_enabled",
            "risk_zero_blocks_execution",
            "pending_policy_enabled",
            "decision_log_path",
        )
    }
    artifact_paths = [str(p) for p in block.get("artifact_paths", [])]
    result["gtos_vnext_runtime_artifact_path_count"] = len(artifact_paths)
    artifact_items = []
    for artifact_path in artifact_paths:
        artifact_abs = REPO_ROOT / artifact_path
        artifact_items.append(
            {
                "path": artifact_path,
                "exists": path_exists(artifact_abs),
                "sha256": sha256_file(artifact_abs),
                "bytes": path_stat_size(artifact_abs),
            }
        )
    result["gtos_vnext_runtime_artifact_paths"] = artifact_items
    result["missing_runtime_artifact_paths"] = [
        item["path"] for item in result["gtos_vnext_runtime_artifact_paths"] if not item["exists"]
    ]
    ai_narrowing = cfg.get("ai_narrowing", {}) if isinstance(cfg, dict) else {}
    result["ai_narrowing_selected"] = {
        key: ai_narrowing.get(key)
        for key in (
            "enabled",
            "mode",
            "apply_to_execution",
            "shadow_evaluation_log",
        )
        if key in ai_narrowing
    }
    risk = cfg.get("risk", {}) if isinstance(cfg, dict) else {}
    result["risk_selected"] = {
        key: risk.get(key)
        for key in (
            "risk_per_trade_pct",
            "max_daily_loss_pct",
            "max_concurrent",
            "max_trades_per_kill_zone_enabled",
            "max_trades_per_kill_zone",
        )
    }
    return result


def shadow_log_inventory() -> list[dict[str, Any]]:
    output = []
    for raw_path in SHADOW_LOG_PATHS:
        path = REPO_ROOT / raw_path
        item = {
            "path": raw_path,
            "exists": path_exists(path),
            "bytes": path_stat_size(path),
            "sha256": sha256_file(path),
            "line_count": line_count(path),
        }
        if path_exists(path) and path.suffix == ".jsonl":
            samples = []
            keys: set[str] = set()
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        item.setdefault("parse_errors", []).append(str(exc))
                        break
                    keys.update(row)
                    if len(samples) < 3:
                        samples.append(row)
                    if len(samples) >= 3 and keys:
                        break
            item["sample_schema_keys"] = sorted(keys)
            item["sample_rows"] = samples
        output.append(item)
    return output


def build_inventory(scan_heavy: bool = True) -> dict[str, Any]:
    prompt = REPO_ROOT / PROMPT_PATH
    starter = REPO_ROOT / STARTER_PATH
    replay_artifacts: dict[str, Any] = {}
    heavy_roles = {
        "final_decision_map",
        "terminal_decision_ledger",
        "mixed_resolution_ledger",
        "prop_metrics_ledger",
        "ablation_metrics_ledger",
        "robustness_prop_metrics_ledger",
        "behavioral_forensics_ledger",
        "nofill_pending_lifecycle_ledger",
        "path_outcome_r_ledger",
        "m15_vs_ltf_disagreement_ledger",
        "missed_winner_avoided_loser_ledger",
        "runtime_trace_ledger",
        "runtime_artifact_load_ledger",
        "source_repair_proof_ledger",
        "candidate_generation_ledger",
        "denominator_disposition_ledger",
        "market_state_packet_ledger",
        "dominance_and_pollution_ledger",
    }
    for role, filename in REQUIRED_REPLAY_ARTIFACTS.items():
        replay_artifacts[role] = summarize_path(
            REPO_ROOT / REPLAY_DIR / filename,
            scan_logical_rows=(scan_heavy and role in heavy_roles),
        )

    metrics = replay_artifacts.get("metrics_summary", {}).get("selected_values", {})
    final_map_scan = replay_artifacts.get("final_decision_map", {}).get("logical_scan", {})
    prop_scan = replay_artifacts.get("prop_metrics_ledger", {}).get("logical_scan", {})
    inventory = {
        "schema_version": "vnext_production_change_input_inventory_stage00_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "current_git_head": git_output(["rev-parse", "HEAD"]),
        "git_status_short": git_output(["status", "--short"]).splitlines(),
        "prompt": {
            "path": rel(prompt),
            "exists": prompt.exists(),
            "sha256": sha256_file(prompt),
            "bytes": prompt.stat().st_size if prompt.exists() else None,
        },
        "starter": {
            "path": rel(starter),
            "exists": starter.exists(),
            "sha256": sha256_file(starter),
            "bytes": starter.stat().st_size if starter.exists() else None,
        },
        "replay_dir": {
            "path": rel(REPO_ROOT / REPLAY_DIR),
            "exists": (REPO_ROOT / REPLAY_DIR).exists(),
        },
        "replay_artifacts": replay_artifacts,
        "runtime_surfaces": runtime_surface_inventory(),
        "config": config_inventory(),
        "shadow_logs": shadow_log_inventory(),
        "stage00_checks": {
            "required_artifact_count": len(REQUIRED_REPLAY_ARTIFACTS),
            "missing_required_artifacts": [
                role for role, item in replay_artifacts.items() if not item.get("exists")
            ],
            "chunk_sha_mismatch_artifacts": [
                role for role, item in replay_artifacts.items() if item.get("sha_mismatch_chunks")
            ],
            "chunk_missing_artifacts": [
                role for role, item in replay_artifacts.items() if item.get("missing_chunks")
            ],
            "metrics_summary_stage_counts": metrics.get("stage_counts"),
            "metrics_summary_final_decision_counts": metrics.get("final_decision_counts"),
            "final_decision_map_logical_rows": final_map_scan.get("row_count"),
            "final_decision_map_decision_counts": (
                final_map_scan.get("status_distributions", {}).get("implementation_decision")
            ),
            "prop_metric_rows": prop_scan.get("row_count"),
            "prop_metric_decision_counts": (
                prop_scan.get("status_distributions", {}).get("implementation_decision")
            ),
            "missing_config_artifact_paths": config_inventory().get("missing_runtime_artifact_paths", []),
        },
    }
    return inventory


def build_state(inventory: dict[str, Any]) -> dict[str, Any]:
    dirty_paths = inventory.get("git_status_short", [])
    stage_status = {stage: "not_started" for stage in STAGES}
    stage_status["STAGE_00_INPUT_INVENTORY"] = "complete"
    stage_status["STAGE_01_DECISION_SURFACE_GROUPING"] = "in_progress"
    final_scan = inventory["replay_artifacts"]["final_decision_map"]["logical_scan"]
    return {
        "schema_version": "vnext_production_change_session_state_v1",
        "route_id": ROUTE_ID,
        "updated_at_utc": utc_now(),
        "current_stage": "STAGE_01_DECISION_SURFACE_GROUPING",
        "stage_status_table": stage_status,
        "active_invariant": "group_every_final_decision_map_row_by_runtime_surface",
        "first_incomplete_invariant": "STAGE_01_DECISION_SURFACE_GROUPING",
        "exact_next_action": (
            "Build VNEXT_PRODUCTION_CHANGE_DECISION_SURFACE_LEDGER_2026-05-25.jsonl "
            "from all 7,555 final decision-map rows and terminal aliases; group by "
            "surface/source_component/action_class/runtime target; map each group to "
            "promote/kill/redesign/guard/MIXED/source-repair/AI/supervisor/selector/LTF action."
        ),
        "current_git_head": inventory.get("current_git_head"),
        "dirty_tracked_paths": dirty_paths,
        "prompt_hash": inventory["prompt"]["sha256"],
        "starter_hash": inventory["starter"]["sha256"],
        "replay_artifact_hashes_used": {
            role: item.get("sha256") for role, item in inventory["replay_artifacts"].items()
        },
        "output_artifact_paths": {
            "session_state": rel(REPO_ROOT / STATE_PATH),
            "input_inventory": rel(REPO_ROOT / INVENTORY_PATH),
        },
        "verification_status": {
            "stage00_inventory_built": True,
            "stage00_missing_required_artifacts": inventory["stage00_checks"][
                "missing_required_artifacts"
            ],
            "stage00_chunk_sha_mismatch_artifacts": inventory["stage00_checks"][
                "chunk_sha_mismatch_artifacts"
            ],
            "stage00_chunk_missing_artifacts": inventory["stage00_checks"][
                "chunk_missing_artifacts"
            ],
        },
        "one_time_steers_applied": {
            "stage02_full_replay_one_time_steer": (
                inventory["replay_artifacts"]
                .get("metrics_summary", {})
                .get("selected_values", {})
                .get("stage02_one_time_steer_status")
            )
        },
        "conflicts_with_stale_context": [
            {
                "context": ".context/LIVE_STATE.md research_current_state freshness",
                "conflict": (
                    "LIVE_STATE reports research_current_state stale relative to "
                    "00b0ca8d6 production prompt commits; this route follows the "
                    "2026-05-25 prompt/starter and disk replay artifacts."
                ),
                "disposition": "follow_active_prompt_and_record_conflict",
            },
            {
                "context": "SESSION_63 handoff",
                "conflict": (
                    "SESSION_63 points to UNIT_001385 runtime-builder queue, but the "
                    "active 2026-05-25 production-change prompt supersedes old unit order."
                ),
                "disposition": "do_not_resume_old_unit_pointer_before_stage00_stage01",
            },
        ],
        "row_count_hash_coverage": {
            "final_decision_map_rows": final_scan.get("row_count"),
            "final_decision_map_decision_counts": final_scan.get("status_distributions", {}).get(
                "implementation_decision"
            ),
            "stage_counts": inventory["stage00_checks"].get("metrics_summary_stage_counts"),
            "runtime_config_artifact_paths": inventory["config"].get(
                "gtos_vnext_runtime_artifact_path_count"
            ),
            "runtime_config_missing_artifact_paths": inventory["config"].get(
                "missing_runtime_artifact_paths"
            ),
        },
        "rows_groups_processed": {
            "stage00_required_replay_artifacts": len(REQUIRED_REPLAY_ARTIFACTS),
            "stage00_runtime_surfaces": len(RUNTIME_SURFACE_PATHS),
            "stage00_shadow_logs": len(SHADOW_LOG_PATHS),
            "stage01_groups_processed": 0,
        },
        "implemented_surfaces": [],
        "killed_redesigned_surfaces": [],
        "guard_only_surfaces": [],
        "mixed_dispositions": {},
        "tests_run": [],
        "replay_shards_run": [],
        "failures": [],
        "repaired_failures": [],
        "remaining_executable_actions": [
            "STAGE_01 decision surface grouping",
            "STAGE_02 promotions implementation",
            "STAGE_03 kill/redesign/guard implementation",
            "STAGE_04 MIXED resolution",
            "STAGE_05 prop-safe selector",
            "STAGE_06 LTF entry/no-fill engine",
            "STAGE_07 AI policy",
            "STAGE_08 AI supervisor",
            "STAGE_09 forward-only replay",
            "STAGE_10 activation dossier and completion audit",
        ],
    }


def verify_outputs(inventory: dict[str, Any], state: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    checks = inventory.get("stage00_checks", {})
    if checks.get("missing_required_artifacts"):
        failures.append(f"missing required artifacts: {checks['missing_required_artifacts']}")
    if checks.get("chunk_sha_mismatch_artifacts"):
        failures.append(f"chunk sha mismatches: {checks['chunk_sha_mismatch_artifacts']}")
    if checks.get("chunk_missing_artifacts"):
        failures.append(f"missing chunks: {checks['chunk_missing_artifacts']}")
    final_rows = checks.get("final_decision_map_logical_rows")
    if final_rows != 7555:
        failures.append(f"final decision map row count expected 7555 got {final_rows}")
    decision_counts = checks.get("final_decision_map_decision_counts") or {}
    expected_decisions = {
        "KEEP_SHADOW": 5443,
        "KEEP_SHADOW_OR_GUARD_ONLY": 272,
        "KILL_OR_REDESIGN_BEFORE_USE": 858,
        "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER": 982,
    }
    if decision_counts != expected_decisions:
        failures.append(f"final decision counts mismatch: {decision_counts}")
    prop_rows = checks.get("prop_metric_rows")
    if prop_rows != 24:
        failures.append(f"prop metric rows expected 24 got {prop_rows}")
    if state["stage_status_table"].get("STAGE_00_INPUT_INVENTORY") != "complete":
        failures.append("STAGE_00 not marked complete")
    if state["first_incomplete_invariant"] == "STAGE_00_INPUT_INVENTORY":
        failures.append("state still points at completed STAGE_00 as first incomplete invariant")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify existing outputs only")
    parser.add_argument(
        "--light",
        action="store_true",
        help="skip logical row scans for heavy chunked artifacts",
    )
    args = parser.parse_args(argv)

    if args.check:
        inventory = read_json(REPO_ROOT / INVENTORY_PATH)
        state = read_json(REPO_ROOT / STATE_PATH)
    else:
        inventory = build_inventory(scan_heavy=not args.light)
        state = build_state(inventory)
        atomic_json_write(REPO_ROOT / INVENTORY_PATH, inventory)
        atomic_json_write(REPO_ROOT / STATE_PATH, state)

    failures = verify_outputs(inventory, state)
    result = {
        "route_id": ROUTE_ID,
        "ok": not failures,
        "failures": failures,
        "inventory_path": rel(REPO_ROOT / INVENTORY_PATH),
        "state_path": rel(REPO_ROOT / STATE_PATH),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
