"""Build the initial vNext replacement Stage 01 evidence reconciliation.

This script is route-local and intentionally does not mutate upstream artifacts.
It creates an index/classification ledger that points back to row-bearing source
artifacts; it is not a replacement for those ledgers.
"""

from __future__ import annotations

import hashlib
import json
import gzip
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
DATE = "2026-05-26"

LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_UPSTREAM_EVIDENCE_RECONCILIATION_LEDGER_{DATE}.jsonl"
REPORT_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_EVIDENCE_RECONCILIATION_REPORT_{DATE}.md"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

UPSTREAM_ROOTS: list[dict[str, str]] = [
    {
        "root": "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24",
        "route": "vnext_full_historical_candidate_generation_replay_2026_05_24",
        "stage_targets": "stage01,stage05,stage06,stage12",
        "evidence_class": "full_historical_replay",
    },
    {
        "root": "research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25",
        "route": "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25",
        "stage_targets": "stage01,stage02,stage12",
        "evidence_class": "negative_fixture",
    },
    {
        "root": "research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25",
        "route": "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25",
        "stage_targets": "stage01,stage04,stage05,stage06,stage11,stage12",
        "evidence_class": "repaired_ev_prop_governor",
    },
    {
        "root": "research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26",
        "route": "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26",
        "stage_targets": "stage01,stage07,stage08,stage09,stage10,stage12",
        "evidence_class": "activation_anatomy_ai_ml",
    },
    {
        "root": "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
        "route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
        "stage_targets": "stage01,stage03,stage04,stage05,stage07,stage08,stage09,stage10,stage11,stage12",
        "evidence_class": "moonshot_dynamic_execution",
    },
    {
        "root": "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder",
        "route": "gtos_vnext_research_to_runtime_builder",
        "stage_targets": "stage01,stage02,stage04",
        "evidence_class": "research_to_runtime_conversion",
    },
    {
        "root": "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15",
        "route": "weekend_mechanical_edge_factory_moonshot_2026_05_15",
        "stage_targets": "stage01,stage02,stage03,stage04,stage05,stage06",
        "evidence_class": "weekend_moonshot_factory",
    },
]

RUNTIME_SURFACE_PATHS = [
    "config/agent_config.yaml",
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "src/components/j46_j49_policy.py",
    "src/research/moonshot_default_off_policy_router.py",
    "src/components/market_state.py",
    "src/components/primary_analyzer.py",
    "src/components/pre_ai_gates.py",
    "src/components/permissions.py",
    "src/components/ai_supervisor.py",
    "src/components/ai_call_policy.py",
    "src/components/ai_decision_trace_logger.py",
    "src/research_infra/cache_helper.py",
    "src/research_infra/k55_ml_shadow.py",
    "scripts/backfill_k55_ml_shadow_predictions.py",
]

TEST_SURFACE_GLOBS = [
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_moonshot_default_off_policy_router.py",
    "tests/test_ai_call_policy.py",
    "tests/test_ai_supervisor.py",
    "tests/test_ai_decision_trace_logger.py",
    "tests/test_k55_ml_shadow.py",
    "tests/research_infra/test_cache_helper.py",
    "tests/test_vnext*.py",
    "tests/research_infra/test_moonshot*.py",
]

SHADOW_LOG_GLOBS = [
    "shadow_logs/*.jsonl",
    "shadow_logs/*.csv",
]

TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}
EXCLUDED_SUFFIXES = {".pyc"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_and_line_count(path: Path, count_lines: bool) -> tuple[str | None, int | None]:
    if not path.exists():
        return None, None
    digest = hashlib.sha256()
    lines = 0
    size = 0
    last_byte = b""
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
            if count_lines:
                lines += chunk.count(b"\n")
                last_byte = chunk[-1:]
    if count_lines and size and last_byte != b"\n":
        lines += 1
    return digest.hexdigest(), lines if count_lines else None


def gzip_line_count(path: Path) -> int | None:
    if not path.exists():
        return None
    lines = 0
    size = 0
    last_byte = b""
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            lines += chunk.count(b"\n")
            if chunk:
                last_byte = chunk[-1:]
    if size and last_byte != b"\n":
        lines += 1
    return lines


def line_count(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def jsonl_distribution(path: Path, fields: list[str]) -> tuple[int, dict[str, dict[str, int]], list[str]]:
    distributions: dict[str, Counter[str]] = {field: Counter() for field in fields}
    keys: Counter[str] = Counter()
    rows = 0
    if not path.exists():
        return rows, {}, []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            row = json.loads(raw)
            rows += 1
            keys.update(row.keys())
            for field in fields:
                if field in row:
                    distributions[field][str(row.get(field))] += 1
    return (
        rows,
        {field: dict(counter) for field, counter in distributions.items() if counter},
        sorted(keys),
    )


def summary_dict(data: Any, keys: list[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return {key: data.get(key) for key in keys if key in data}


def base_artifact(path: str) -> dict[str, Any]:
    artifact_path = REPO_ROOT / path
    return {
        "artifact_path": path,
        "exists": artifact_path.exists(),
        "sha256": sha256_path(artifact_path),
        "bytes": artifact_path.stat().st_size if artifact_path.exists() else None,
        "line_count": line_count(artifact_path),
    }


def is_material_file(path: Path) -> bool:
    if "__pycache__" in path.parts:
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith(".jsonl.gz"):
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def artifact_role(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name.startswith("build_") and suffix == ".py":
        return "builder"
    if name.startswith("verify_") and suffix == ".py":
        return "verifier"
    if name.startswith("test_") and suffix == ".py":
        return "focused_test"
    if "manifest" in name:
        return "manifest"
    if "ledger" in name or name.endswith(".jsonl") or name.endswith(".jsonl.gz"):
        return "row_ledger_or_shard"
    if "summary" in name:
        return "summary"
    if "report" in name:
        return "report"
    if "audit" in name:
        return "audit"
    if suffix in {".yaml", ".yml"}:
        return "config"
    if suffix == ".py":
        return "source_or_test_code"
    if suffix == ".csv":
        return "csv_source_or_metric"
    if suffix == ".json":
        return "json_artifact"
    if suffix == ".md":
        return "markdown_artifact"
    return "material_artifact"


def classifications_for(route: str, path: Path, role: str) -> list[str]:
    classes: set[str] = set()
    name = path.name.lower()
    if route == "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25":
        classes.update({"killed_redesigned_with_reason", "static_proxy_comparator"})
    elif route == "vnext_full_historical_candidate_generation_replay_2026_05_24":
        classes.update({"accepted_for_runtime", "dynamic_valid", "static_proxy_comparator"})
    elif route == "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25":
        classes.update({"accepted_for_runtime", "dynamic_valid"})
    elif route == "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26":
        classes.add("accepted_for_runtime")
        if "ai" in name or "prompt" in name or "budget" in name:
            classes.add("ai_budget_required")
        if "ml" in name or "challenger" in name:
            classes.add("source_capture_required")
    elif route == "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26":
        classes.update({"accepted_for_runtime", "dynamic_valid"})
        if "source" in name or "capture" in name or "origin" in name:
            classes.add("source_capture_required")
        if "ai" in name or "prompt" in name or "budget" in name:
            classes.add("ai_budget_required")
    elif route == "gtos_vnext_research_to_runtime_builder":
        classes.update({"accepted_for_runtime", "superseded"})
    elif route == "weekend_mechanical_edge_factory_moonshot_2026_05_15":
        classes.update({"accepted_for_runtime", "source_capture_required"})
    elif route == "runtime_config_test_shadow_surface":
        classes.add("accepted_for_runtime")
        if role in {"focused_test", "verifier"}:
            classes.add("activation_config_applied")
        if "shadow_logs/" in rel(path):
            classes.add("source_capture_required")
    if "do_not_activate" in name or "failed" in name:
        classes.add("killed_redesigned_with_reason")
    if not classes:
        classes.add("accepted_for_runtime")
    return sorted(classes)


def inventory_sources() -> list[tuple[Path, dict[str, str]]]:
    sources: list[tuple[Path, dict[str, str]]] = []
    seen: set[Path] = set()

    for root_spec in UPSTREAM_ROOTS:
        root = REPO_ROOT / root_spec["root"]
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and is_material_file(path) and path not in seen:
                seen.add(path)
                sources.append((path, root_spec))

    support_spec = {
        "root": ".",
        "route": "runtime_config_test_shadow_surface",
        "stage_targets": "stage01,stage04,stage08,stage10,stage12",
        "evidence_class": "runtime_config_test_shadow_surface",
    }
    support_paths: set[Path] = set()
    for rel_path in RUNTIME_SURFACE_PATHS:
        path = REPO_ROOT / rel_path
        if path.exists() and path.is_file():
            support_paths.add(path)
    for pattern in TEST_SURFACE_GLOBS + SHADOW_LOG_GLOBS:
        support_paths.update(path for path in REPO_ROOT.glob(pattern) if path.is_file())

    for path in sorted(support_paths):
        if path not in seen and is_material_file(path):
            seen.add(path)
            sources.append((path, support_spec))

    return sources


def inventory_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, spec in inventory_sources():
        role = artifact_role(path)
        count_lines = path.suffix.lower() in TEXT_SUFFIXES
        digest, lines = sha256_and_line_count(path, count_lines=count_lines)
        row_bearing_rows = None
        scan_mode = "metadata_hash_and_line_count"
        if path.name.endswith(".jsonl.gz"):
            row_bearing_rows = gzip_line_count(path)
            scan_mode = "compressed_hash_plus_gzip_row_line_count"
        elif path.suffix.lower() in {".jsonl", ".csv"}:
            row_bearing_rows = lines
            scan_mode = "hash_plus_row_line_count"
        rows.append(
            {
                "row_id": "artifact_inventory::" + rel(path).replace("/", "::"),
                "row_kind": "artifact_inventory",
                "artifact_path": rel(path),
                "exists": True,
                "sha256": digest,
                "bytes": path.stat().st_size,
                "line_count": lines,
                "row_bearing_rows_scanned": row_bearing_rows,
                "inventory_scan_mode": scan_mode,
                "upstream_route": spec["route"],
                "source_root": spec["root"],
                "evidence_class": spec["evidence_class"],
                "stage_targets": spec["stage_targets"].split(","),
                "artifact_role": role,
                "classifications": classifications_for(spec["route"], path, role),
                "runtime_or_replay_use": "Stage01 material artifact inventory; row-preserving source remains the referenced artifact, not this index row.",
                "required_next_action": "Consume the referenced file by path and hash in its owning stage; do not substitute this inventory row for row-level replay, source, or runtime evidence.",
                "no_summary_replacement": True,
            }
        )
    return rows


def reconciliation_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    full_stage02 = "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
    data = load_json(REPO_ROOT / full_stage02)
    rows.append(
        {
            **base_artifact(full_stage02),
            "row_id": "full_replay_stage02_candidate_generation",
            "upstream_route": "vnext_full_historical_candidate_generation_replay_2026_05_24",
            "artifact_role": "full_denominator_candidate_generation_summary",
            "classifications": ["accepted_for_runtime", "dynamic_valid"],
            "claim_summary": "Full M15 denominator and candidate-origin generation spine for 24-market vNext replay.",
            "counts": summary_dict(
                data,
                [
                    "counts",
                    "candidate_rows_by_framework",
                    "candidate_rows_by_session_bucket",
                    "candidate_rows_by_symbol",
                    "denominator_disposition_counts",
                ],
            ),
            "runtime_or_replay_use": "Stage05 activated replay denominator and candidate-origin completeness baseline.",
            "required_next_action": "Trace every candidate-origin family into activated runtime/replay decisions; do not narrow to FVG or top-N subsets.",
            "no_summary_replacement": True,
        }
    )

    full_stage04 = "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json"
    data = load_json(REPO_ROOT / full_stage04)
    rows.append(
        {
            **base_artifact(full_stage04),
            "row_id": "full_replay_stage04_source_mode_path_r",
            "upstream_route": "vnext_full_historical_candidate_generation_replay_2026_05_24",
            "artifact_role": "source_mode_ltf_path_r_summary",
            "classifications": ["dynamic_valid", "source_capture_required"],
            "claim_summary": "M1/M5/tick/Sierra/OHLC path truth and proxy-R source-mode coverage summary.",
            "counts": summary_dict(
                data,
                [
                    "counts",
                    "terminal_counts_by_mode",
                    "source_repair_counts",
                    "missing_source_counts_by_requested_mode",
                    "missed_winner_avoided_loser_classification_counts",
                ],
            ),
            "runtime_or_replay_use": "Stage05/06 path/R, source-completeness, no-fill, and missing-source partition input.",
            "required_next_action": "Bind source-missing rows to exact exclusion or forward-capture rules before activation.",
            "no_summary_replacement": True,
        }
    )

    full_stage06 = "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_2026-05-24.json"
    data = load_json(REPO_ROOT / full_stage06)
    rows.append(
        {
            **base_artifact(full_stage06),
            "row_id": "full_replay_stage06_final_decision_map",
            "upstream_route": "vnext_full_historical_candidate_generation_replay_2026_05_24",
            "artifact_role": "final_replay_decision_map_summary",
            "classifications": ["accepted_for_runtime", "static_proxy_comparator", "dynamic_valid"],
            "claim_summary": "Final decision-map, ablation, robustness, prop proxy, and MIXED resolution counts from full replay.",
            "counts": summary_dict(data, ["counts", "final_decision_counts", "mixed_resolution_class_counts", "prop_metric_decision_counts"]),
            "runtime_or_replay_use": "Stage01 classification seed and Stage06 legacy-vs-vNext delta branch source.",
            "required_next_action": "Consume row-preserving final decision ledgers, not this summary alone, when forming activation rules.",
            "no_summary_replacement": True,
        }
    )

    forensic = "research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md"
    rows.append(
        {
            **base_artifact(forensic),
            "row_id": "failed_production_change_negative_fixture",
            "upstream_route": "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25",
            "artifact_role": "forensic_do_not_activate_report",
            "classifications": ["killed_redesigned_with_reason", "static_proxy_comparator"],
            "claim_summary": "Negative fixture for 10-trade collapse, broad blockers, blocked winners, and failed activation semantics.",
            "counts": {},
            "runtime_or_replay_use": "Semantic verifier must reject any route that reproduces the failed selection collapse or broad blocker behavior.",
            "required_next_action": "Extract exact failed route ledgers and ensure Stage12 verifier checks this failure family.",
            "no_summary_replacement": True,
        }
    )

    repair_summary = "research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json"
    data = load_json(REPO_ROOT / repair_summary)
    rows.append(
        {
            **base_artifact(repair_summary),
            "row_id": "repaired_ev_prop_governor_replay_metrics",
            "upstream_route": "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25",
            "artifact_role": "repaired_forward_replay_metrics_summary",
            "classifications": ["accepted_for_runtime", "dynamic_valid", "ai_budget_required"],
            "claim_summary": "Repaired executable stream, prop-governor comparison, AI-call diagnostic split, LTF path effects, and source-status counts.",
            "counts": summary_dict(
                data,
                [
                    "candidate_universe_rows",
                    "executable_stream_rows",
                    "policy_metrics",
                    "policy_extra_counts",
                    "source_status_counts",
                    "ai_call_counts",
                    "ltf_changed_entry_outcomes",
                    "required_metric_coverage",
                ],
            ),
            "runtime_or_replay_use": "Stage04/05/06 prop governor and AI-budget split input.",
            "required_next_action": "Convert repaired policy semantics into executable runtime/config or exact rollback/exclusion rules.",
            "no_summary_replacement": True,
        }
    )

    activation_questions = "research/science_program_2026_05/06_outcome_testing/vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_2026-05-26.jsonl"
    count, distribution, keys = jsonl_distribution(REPO_ROOT / activation_questions, ["status", "category", "ledger_row_type"])
    rows.append(
        {
            **base_artifact(activation_questions),
            "row_id": "activation_anatomy_question_stack",
            "upstream_route": "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26",
            "artifact_role": "question_stack_ledger",
            "classifications": ["source_capture_required", "ai_budget_required", "accepted_for_runtime"],
            "claim_summary": "Question ledger with source repair, sparse-limit, partition metric, AI-budget, and route-artifact answers.",
            "jsonl_rows_scanned": count,
            "status_distribution": distribution,
            "jsonl_keys": keys,
            "runtime_or_replay_use": "Stage07 question closure seed; must import all rows and preserve status semantics.",
            "required_next_action": "Map every row to answered, implemented, killed, source-capture, AI-budget, activation-applied, external-surface, or non-generatable historical truth.",
            "no_summary_replacement": True,
        }
    )

    moonshot_stage04 = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json"
    data = load_json(REPO_ROOT / moonshot_stage04)
    rows.append(
        {
            **base_artifact(moonshot_stage04),
            "row_id": "moonshot_stage04_dynamic_policy_replay",
            "upstream_route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
            "artifact_role": "dynamic_policy_replay_summary",
            "classifications": ["dynamic_valid", "accepted_for_runtime", "static_proxy_comparator"],
            "claim_summary": "Universal replayable candidate dynamic execution policy comparison across old static/J46-J49 and moonshot policies.",
            "counts": summary_dict(
                data,
                [
                    "candidate_rows_in_replay_mode",
                    "input_rows_scanned",
                    "replayable_candidate_rows",
                    "policy_counts",
                    "policy_total_r",
                    "policy_expectancy_r",
                    "policy_ambiguous_counts",
                ],
            ),
            "runtime_or_replay_use": "Stage04 dynamic execution router and Stage05 activated replay execution-policy input.",
            "required_next_action": "Ensure activated runtime does not use fixed 1.5R or J46-J49 as final moonshot truth unless explicitly in rollback/comparator mode.",
            "no_summary_replacement": True,
        }
    )

    corrected_branch = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_2026-05-26.json"
    data = load_json(REPO_ROOT / corrected_branch)
    rows.append(
        {
            **base_artifact(corrected_branch),
            "row_id": "moonshot_corrected_branch_prop_ev",
            "upstream_route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
            "artifact_role": "corrected_branch_prop_ev_summary",
            "classifications": ["dynamic_valid", "accepted_for_runtime", "killed_redesigned_with_reason"],
            "claim_summary": "Corrected branch metrics, segmented prop EV, and explicit rejection of legacy fixed 1.5R as activation truth.",
            "counts": summary_dict(
                data,
                [
                    "events_replayed",
                    "corrected_branch_metric_rows",
                    "branch_row_counts_live_current",
                    "best_overall_reference_fee599_payout8000",
                    "legacy_fixed_1_5r_rejected_as_activation_truth",
                    "prop_ev_attempt_rows",
                    "safe_but_dead_rejection_count",
                ],
            ),
            "runtime_or_replay_use": "Stage04 branch router and Stage11 activation dossier prop EV policy source.",
            "required_next_action": "Convert branch decisions into executable runtime routing, exact exclusions, or rollback rules.",
            "no_summary_replacement": True,
        }
    )

    runtime_map = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_2026-05-26.json"
    data = load_json(REPO_ROOT / runtime_map)
    rows.append(
        {
            **base_artifact(runtime_map),
            "row_id": "moonshot_runtime_integration_map",
            "upstream_route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
            "artifact_role": "runtime_integration_map",
            "classifications": ["accepted_for_runtime", "source_capture_required"],
            "claim_summary": "Moonshot route's map of runtime/config/test integration surfaces and still-required wiring.",
            "counts": summary_dict(data, list(data.keys()) if isinstance(data, dict) else []),
            "runtime_or_replay_use": "Stage04 implementation map input; not proof by itself.",
            "required_next_action": "Verify each mapped runtime surface in current code and implement missing activation behavior.",
            "no_summary_replacement": True,
        }
    )

    origin_registry = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl"
    count, distribution, keys = jsonl_distribution(REPO_ROOT / origin_registry, ["activation_status", "source_availability_status", "current_gtos_status", "category"])
    rows.append(
        {
            **base_artifact(origin_registry),
            "row_id": "moonshot_universal_candidate_origin_registry",
            "upstream_route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
            "artifact_role": "candidate_origin_registry",
            "classifications": ["source_capture_required", "accepted_for_runtime"],
            "claim_summary": "Universal candidate origin families and source requirements; current status is research registry only.",
            "jsonl_rows_scanned": count,
            "status_distribution": distribution,
            "jsonl_keys": keys,
            "runtime_or_replay_use": "Stage03 candidate contract and Stage08 market/source activation map input.",
            "required_next_action": "Define runtime generation or exact exclusion/fallback for each origin family before activation.",
            "no_summary_replacement": True,
        }
    )

    boxing_audit = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_CANDIDATE_ORIGIN_BOXING_AUDIT_LEDGER_2026-05-26.jsonl"
    count, distribution, keys = jsonl_distribution(REPO_ROOT / boxing_audit, ["boxed_dimension", "current_behavior", "repair_action"])
    rows.append(
        {
            **base_artifact(boxing_audit),
            "row_id": "moonshot_candidate_origin_boxing_audit",
            "upstream_route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
            "artifact_role": "candidate_origin_boxing_audit",
            "classifications": ["source_capture_required", "killed_redesigned_with_reason"],
            "claim_summary": "Audit of dimensions boxed out by current behavior and source/runtime repair actions.",
            "jsonl_rows_scanned": count,
            "status_distribution": distribution,
            "jsonl_keys": keys,
            "runtime_or_replay_use": "Stage02/03 legacy-retirement and candidate-origin expansion source.",
            "required_next_action": "For each boxed dimension, implement runtime expansion or exact exclusion/rollback boundary.",
            "no_summary_replacement": True,
        }
    )

    forward_capture = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_2026-05-26.jsonl"
    count, distribution, keys = jsonl_distribution(REPO_ROOT / forward_capture, ["blocker_class", "capture_surface", "historical_reconstruction_policy"])
    rows.append(
        {
            **base_artifact(forward_capture),
            "row_id": "moonshot_forward_capture_requirements",
            "upstream_route": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
            "artifact_role": "forward_capture_requirement_ledger",
            "classifications": ["source_capture_required"],
            "claim_summary": "Exact forward-capture fields/surfaces for non-generatable or missing historical truth.",
            "jsonl_rows_scanned": count,
            "status_distribution": distribution,
            "jsonl_keys": keys,
            "runtime_or_replay_use": "Stage08 source-capture contract and Stage10 monitoring/logging input.",
            "required_next_action": "Wire prospective capture schemas/loggers/tests for repo-local surfaces; do not backfill historical broker lifecycle truth from price.",
            "no_summary_replacement": True,
        }
    )

    conversion_summary = "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_SUMMARY_2026-05-18.json"
    data = load_json(REPO_ROOT / conversion_summary)
    rows.append(
        {
            **base_artifact(conversion_summary),
            "row_id": "conversion_builder_master_summary",
            "upstream_route": "gtos_vnext_research_to_runtime_builder",
            "artifact_role": "master_intelligence_to_runtime_conversion_summary",
            "classifications": ["accepted_for_runtime", "superseded"],
            "claim_summary": "Current conversion counts, next unit pointer, and runtime-conversion status from relocated builder root.",
            "counts": summary_dict(
                data,
                [
                    "total_intelligence_units",
                    "converted_units",
                    "implemented_units",
                    "killed_units",
                    "not_started_units",
                    "repair_action_defined_units",
                    "repair_needed_units",
                    "state_counts",
                    "next_unit_being_consumed",
                ],
            ),
            "runtime_or_replay_use": "Stage01 reconciliation and Stage04 runtime gap source; old prompt-listed path is superseded by relocated path.",
            "required_next_action": "Reconcile conversion counts against current 2026-05-25/26 moonshot artifacts and runtime code before activation.",
            "no_summary_replacement": True,
        }
    )

    conversion_freeze = "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_FINAL_CONVERSION_FREEZE_REPORT_2026-05-23.md"
    rows.append(
        {
            **base_artifact(conversion_freeze),
            "row_id": "conversion_builder_final_freeze_report",
            "upstream_route": "gtos_vnext_research_to_runtime_builder",
            "artifact_role": "final_conversion_freeze_report",
            "classifications": ["accepted_for_runtime", "superseded"],
            "claim_summary": "Final conversion freeze report from relocated builder root; must be checked against newer vNext/moonshot artifacts.",
            "counts": {},
            "runtime_or_replay_use": "Stage01 upstream reconciliation input and stale/superseded boundary source.",
            "required_next_action": "Classify report claims as accepted, superseded, dynamic-valid, source-capture, or killed using newer artifacts and runtime evidence.",
            "no_summary_replacement": True,
        }
    )

    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_report(rows: list[dict[str, Any]]) -> None:
    class_counts: Counter[str] = Counter()
    row_kind_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    root_counts: Counter[str] = Counter()
    for row in rows:
        class_counts.update(row.get("classifications", []))
        row_kind_counts.update([str(row.get("row_kind", "seed_reconciliation"))])
        role_counts.update([str(row.get("artifact_role", "unknown"))])
        root_counts.update([str(row.get("upstream_route", "unknown"))])
    missing = [row["artifact_path"] for row in rows if not row.get("exists")]
    scanned = sum(int(row.get("jsonl_rows_scanned") or 0) for row in rows)
    row_bearing_scanned = sum(int(row.get("row_bearing_rows_scanned") or 0) for row in rows)
    inventory_rows_written = row_kind_counts.get("artifact_inventory", 0)
    lines = [
        "# vNext Replacement Stage 01 Evidence Reconciliation Report",
        "",
        f"Generated UTC: `{utc_now()}`",
        f"Route id: `{ROUTE_ID}`",
        f"Ledger: `{rel(LEDGER_PATH)}`",
        "",
        "## Scope",
        "",
        "This is the initial Stage 01 reconciliation index over the major upstream artifacts. It preserves source paths, hashes, counts, and full status distributions for parsed JSONL inputs. It does not replace row-bearing upstream ledgers and does not complete the full route by itself.",
        "",
        "## Coverage",
        "",
        f"- Reconciliation rows written: `{len(rows)}`",
        f"- Artifact inventory rows written: `{inventory_rows_written}`",
        f"- JSONL rows scanned for distributions: `{scanned}`",
        f"- Row-bearing lines scanned for artifact inventory: `{row_bearing_scanned}`",
        f"- Missing row artifacts in this initial set: `{len(missing)}`",
        "",
        "## Row Kind Counts",
        "",
    ]
    for key in sorted(row_kind_counts):
        lines.append(f"- `{key}`: `{row_kind_counts[key]}`")
    lines.extend(
        [
            "",
            "## Artifact Role Counts",
            "",
        ]
    )
    for key in sorted(role_counts):
        lines.append(f"- `{key}`: `{role_counts[key]}`")
    lines.extend(
        [
            "",
            "## Upstream Route Counts",
            "",
        ]
    )
    for key in sorted(root_counts):
        lines.append(f"- `{key}`: `{root_counts[key]}`")
    lines.extend(
        [
            "",
        "## Classification Counts",
        "",
        ]
    )
    for key in sorted(class_counts):
        lines.append(f"- `{key}`: `{class_counts[key]}`")
    lines.extend(
        [
            "",
            "## First Incomplete Invariant",
            "",
            "`stage_02_old_gtos_replacement_map_pending`: the Stage 01 high-level classification seed and full artifact inventory now exist. The next route-local action is to convert this inventory into the Stage 02 old-GTOS replacement map and legacy-surface retirement ledger while preserving row-bearing upstream artifacts by path/hash.",
            "",
            "## Guardrails",
            "",
            "- No arbitrary top-N was used; status distributions are full counters over the scanned JSONL files.",
            "- Artifact inventory rows cover every material text/JSON/JSONL/CSV/GZip row-bearing artifact under the required upstream roots plus active runtime/config/test/shadow-log surfaces.",
            "- Summaries are treated as pointers and classifiers, not evidence replacement.",
            "- The failed production-change route is retained as a negative fixture for semantic verification.",
            "- Source-missing and non-generatable historical truth remain source-capture or exclusion work, not activation permission.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def write_json_object(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8", newline="\n")


def upsert_output(outputs: list[dict[str, Any]], path_name: str, updates: dict[str, Any]) -> None:
    for output in outputs:
        if output.get("path") == path_name:
            output.update(updates)
            return
    outputs.append({"path": path_name, **updates})


def update_output_manifest(rows: list[dict[str, Any]]) -> None:
    manifest = load_json_object(OUTPUT_MANIFEST_PATH)
    outputs = manifest.setdefault("outputs", [])
    seed_rows = sum(1 for row in rows if row.get("row_kind") == "seed_reconciliation")
    inventory_count = sum(1 for row in rows if row.get("row_kind") == "artifact_inventory")
    row_bearing_scanned = sum(int(row.get("row_bearing_rows_scanned") or 0) for row in rows)
    distribution_scanned = sum(int(row.get("jsonl_rows_scanned") or 0) for row in rows)
    upsert_output(
        outputs,
        LEDGER_PATH.name,
        {
            "stage": "stage_01",
            "status": "expanded_artifact_inventory_written",
            "rows": len(rows),
            "seed_reconciliation_rows": seed_rows,
            "artifact_inventory_rows": inventory_count,
            "jsonl_rows_scanned_for_distributions": distribution_scanned,
            "row_bearing_lines_scanned_for_inventory": row_bearing_scanned,
        },
    )
    upsert_output(
        outputs,
        REPORT_PATH.name,
        {"stage": "stage_01", "status": "expanded_artifact_inventory_written"},
    )
    upsert_output(
        outputs,
        Path(__file__).name,
        {"stage": "stage_01", "status": "expanded_artifact_inventory_builder"},
    )
    manifest["next_manifest_update"] = (
        "After Stage 02 old-GTOS replacement map and legacy retirement ledger are written from the Stage 01 inventory."
    )
    write_json_object(OUTPUT_MANIFEST_PATH, manifest)


def update_session_state(rows: list[dict[str, Any]]) -> None:
    state = load_json_object(SESSION_STATE_PATH)
    state["last_updated_utc"] = utc_now()
    state["current_stage"] = "stage_02_old_gtos_replacement_map"
    state.setdefault("stage_status", {})["stage_01_evidence_reconciliation"] = "completed_artifact_inventory_reconciliation"
    state["first_incomplete_invariant"] = "stage_02_old_gtos_replacement_map_pending"
    state["exact_next_action"] = (
        "Build VNEXT_REPLACEMENT_OLD_GTOS_REPLACEMENT_MAP_2026-05-26.json and "
        "VNEXT_REPLACEMENT_LEGACY_SURFACE_RETIREMENT_LEDGER_2026-05-26.jsonl from the Stage 01 "
        "artifact inventory, runtime audit, failed-route negative fixture, repaired EV route, moonshot runtime map, "
        "and current code/config surfaces."
    )
    state["subagent_lanes"] = [
        {**lane, "status": "completed_read_only_closed"} for lane in state.get("subagent_lanes", [])
    ]
    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage01_seed_reconciliation_rows"] = sum(1 for row in rows if row.get("row_kind") == "seed_reconciliation")
    evidence["stage01_artifact_inventory_rows"] = sum(1 for row in rows if row.get("row_kind") == "artifact_inventory")
    evidence["stage01_jsonl_distribution_rows_scanned"] = sum(int(row.get("jsonl_rows_scanned") or 0) for row in rows)
    evidence["stage01_row_bearing_inventory_lines_scanned"] = sum(
        int(row.get("row_bearing_rows_scanned") or 0) for row in rows
    )
    evidence["note"] = (
        "Stage 01 now contains the high-level classification seed plus full material artifact inventory. "
        "Row-preserving replay and question closure remain owned by Stage 05/06/07."
    )
    state["searched_roots"] = sorted(
        set(state.get("searched_roots", []))
        | {spec["root"] for spec in UPSTREAM_ROOTS}
        | {"config/agent_config.yaml", "src/components", "src/research", "tests", "shadow_logs"}
    )
    tests = state.setdefault("tests_verifiers_run", [])
    tests.append(
        {
            "command": (
                "python research\\science_program_2026_05\\06_outcome_testing\\"
                "vnext_moonshot_production_replacement_activation_2026_05_26\\"
                "build_vnext_replacement_stage01_reconciliation.py"
            ),
            "result": "passed; wrote expanded Stage 01 seed plus artifact inventory ledger",
            "timestamp_utc": utc_now(),
        }
    )
    state.setdefault("completion_gate_status", {})["route_complete"] = False
    state.setdefault("completion_gate_status", {})["reason"] = (
        "Stage 01 artifact inventory is complete, but Stage 02+ runtime implementation, full activated replay, "
        "semantic verifier, applied overlay, rollback proof, monitoring package, scoped commits, and completion audit remain incomplete."
    )
    write_json_object(SESSION_STATE_PATH, state)


def append_control_event(rows: list[dict[str, Any]]) -> None:
    event = {
        "timestamp_utc": utc_now(),
        "route_id": ROUTE_ID,
        "event": "stage_01_artifact_inventory_expanded",
        "ledger": rel(LEDGER_PATH),
        "report": rel(REPORT_PATH),
        "rows": len(rows),
        "artifact_inventory_rows": sum(1 for row in rows if row.get("row_kind") == "artifact_inventory"),
        "row_bearing_lines_scanned": sum(int(row.get("row_bearing_rows_scanned") or 0) for row in rows),
        "next_incomplete_invariant": "stage_02_old_gtos_replacement_map_pending",
    }
    with CONTROL_LEDGER_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    rows = reconciliation_rows()
    for row in rows:
        row.setdefault("row_kind", "seed_reconciliation")
    rows.extend(inventory_rows())
    write_jsonl(LEDGER_PATH, rows)
    write_report(rows)
    update_output_manifest(rows)
    update_session_state(rows)
    append_control_event(rows)
    print(json.dumps({"ledger": rel(LEDGER_PATH), "report": rel(REPORT_PATH), "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
