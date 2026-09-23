from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage00_inventory_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage00", MODULE_PATH)
stage00 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage00)

REPO_ROOT = stage00.REPO_ROOT
ROUTE_ID = stage00.ROUTE_ID
ROUTE_DIR = stage00.ROUTE_DIR
REPLAY_DIR = stage00.REPLAY_DIR
STATE_PATH = stage00.STATE_PATH
INVENTORY_PATH = stage00.INVENTORY_PATH
DECISION_SURFACE_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_DECISION_SURFACE_LEDGER_2026-05-25.jsonl"
)
IMPLEMENTATION_PLAN_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_IMPLEMENTATION_PLAN_2026-05-25.md"
)
STAGE01_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE01_VERIFICATION_RESULT_2026-05-25.json"
)

EXPECTED_FINAL_DECISION_COUNTS = {
    "KEEP_SHADOW": 5443,
    "KEEP_SHADOW_OR_GUARD_ONLY": 272,
    "KILL_OR_REDESIGN_BEFORE_USE": 858,
    "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER": 982,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage00.rel(path)


def stable_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage00.atomic_json_write(REPO_ROOT / path if not path.is_absolute() else path, payload)


def iter_chunk_index_rows(path: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        meta = json.loads(line)
        chunk_path = REPO_ROOT / str(meta["chunk_path"])
        with gzip.open(stage00.io_path(chunk_path), "rt", encoding="utf-8") as f:
            for row_line in f:
                if row_line.strip():
                    yield meta, json.loads(row_line)


def final_decision_rows() -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    return iter_chunk_index_rows(REPO_ROOT / REPLAY_DIR / "VNEXT_FULL_REPLAY_FINAL_DECISION_MAP_2026-05-24.jsonl")


def mixed_resolution_rows() -> Iterable[dict[str, Any]]:
    path = REPO_ROOT / REPLAY_DIR / "VNEXT_FULL_REPLAY_MIXED_RESOLUTION_LEDGER_2026-05-24.jsonl"
    for _meta, row in iter_chunk_index_rows(path):
        yield row


def target_for_row(row: dict[str, Any]) -> dict[str, Any]:
    surface = str(row.get("surface") or "unmatched_unknown_surface")
    source_component = str(row.get("source_component") or "")
    action_class = str(row.get("action_class") or "")
    implementation_decision = str(row.get("implementation_decision") or "")

    target_files = {"src/components/gtos_vnext_runtime.py", "config/agent_config.yaml", "tests/test_gtos_vnext_runtime.py"}
    target_functions = {"load_vnext_evidence_index", "evaluate_vnext_event", "evaluate_vnext_route_event"}
    required_stages: set[str] = set()
    runtime_surface = "route_decision_scorer_filter_router"
    expected_effects: set[str] = {"route_pressure_and_non_override_guard"}

    if surface == "pre_ai_decision":
        runtime_surface = "pre_ai_route_selector_and_ai_narrowing"
        target_files.update({"src/components/orchestrator.py", "src/components/primary_analyzer.py"})
        target_functions.update({"evaluate_pre_ai_vnext", "format_vnext_ai_role_context_for_prompt"})
        required_stages.update({"STAGE_02_PROMOTION_IMPLEMENTATION", "STAGE_07_AI_POLICY"})
        expected_effects.update({"skip_or_narrow_ai_call_when_activation_allows"})
    elif surface == "risk_adjustment":
        runtime_surface = "risk_adjustment_and_prop_safe_selector"
        target_files.update({"src/components/orchestrator.py", "src/components/permissions.py"})
        target_functions.update({"apply_vnext_risk_adjustment", "vnext_blocks_execution"})
        required_stages.update({"STAGE_02_PROMOTION_IMPLEMENTATION", "STAGE_05_PROP_SAFE_SELECTOR"})
        expected_effects.update({"risk_multiplier_or_zero_risk_block"})
    elif surface == "pending_policy":
        runtime_surface = "pending_policy_nofill_limit_market_selector"
        target_files.update({"src/components/orchestrator.py"})
        target_functions.update({"evaluate_vnext_pending_policy", "attach_vnext_pending_policy_to_record"})
        required_stages.update({"STAGE_02_PROMOTION_IMPLEMENTATION", "STAGE_06_LTF_ENTRY_NOFILL_ENGINE"})
        expected_effects.update({"pending_limit_skip_market_entry_or_adaptive_entry"})
    elif surface == "path_nofill_pending_lifecycle" or "nofill" in source_component or "pending" in action_class:
        runtime_surface = "ltf_path_nofill_pending_lifecycle_engine"
        target_files.update({"src/components/orchestrator.py", "src/components/market_state.py"})
        target_functions.update({"evaluate_vnext_pending_policy", "build_vnext_pre_ai_event"})
        required_stages.update({"STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION", "STAGE_06_LTF_ENTRY_NOFILL_ENGINE"})
        expected_effects.update({"path_aware_entry_skip_expiry_or_no_fill_guard"})
    elif surface == "unmatched_unknown_surface":
        runtime_surface = "legacy_no_match_non_override_guard"
        target_functions.update({"normalize_event", "_row_matches_event_filters"})
        required_stages.add("STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION")
        expected_effects.update({"unknown_legacy_rows_cannot_create_trade_pressure"})

    if "rejected_candidate" in source_component or "l2_" in source_component:
        required_stages.update({"STAGE_02_PROMOTION_IMPLEMENTATION", "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"})
        expected_effects.update({"rejected_candidate_value_mining_or_rejection_guard"})
    if implementation_decision == "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER":
        required_stages.add("STAGE_02_PROMOTION_IMPLEMENTATION")
    elif implementation_decision == "KILL_OR_REDESIGN_BEFORE_USE":
        required_stages.add("STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION")
    elif implementation_decision == "KEEP_SHADOW_OR_GUARD_ONLY":
        required_stages.add("STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION")
    else:
        required_stages.add("STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION")

    if "mixed" in action_class.lower() or row.get("baseline_decision") == "MIXED":
        required_stages.add("STAGE_04_MIXED_RESOLUTION")
    if any(token in action_class.lower() for token in ("malformed", "ai", "schema")):
        required_stages.update({"STAGE_07_AI_POLICY", "STAGE_08_AI_SUPERVISOR"})

    return {
        "runtime_surface": runtime_surface,
        "target_files": sorted(target_files),
        "target_functions": sorted(target_functions),
        "required_stages": sorted(required_stages),
        "expected_runtime_effects": sorted(expected_effects),
    }


def implementation_action(row: dict[str, Any]) -> str:
    decision = row.get("implementation_decision")
    if decision == "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER":
        return "promote_into_activation_gated_runtime_behavior"
    if decision == "KILL_OR_REDESIGN_BEFORE_USE":
        return "enforce_kill_redesign_or_non_override_guard"
    if decision == "KEEP_SHADOW_OR_GUARD_ONLY":
        return "enforce_guard_only_no_silent_pressure"
    return "verify_shadow_only_no_runtime_pressure"


def group_key(row: dict[str, Any], target: dict[str, Any]) -> tuple[str, ...]:
    return (
        target["runtime_surface"],
        str(row.get("surface") or "unmatched_unknown_surface"),
        str(row.get("source_component") or "unknown_component"),
        str(row.get("action_class") or "unknown_action_class"),
        str(row.get("implementation_decision") or "UNKNOWN_DECISION"),
        str(row.get("runtime_mode") or "unknown_runtime_mode"),
        str(row.get("baseline_decision") or "unknown_baseline_decision"),
        str(row.get("evidence_family") or "unknown_evidence_family"),
    )


def merge_counter(target: Counter[str], value: Any) -> None:
    target[str(value if value is not None else "<NULL>")] += 1


def build_groups() -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    included_row_ids: set[str] = set()

    for meta, row in final_decision_rows():
        target = target_for_row(row)
        key = group_key(row, target)
        if key not in groups:
            group_id = "surf01_" + stable_hash("|".join(key))
            groups[key] = {
                "schema_version": "vnext_production_change_decision_surface_group_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_DECISION_SURFACE_GROUPING",
                "group_id": group_id,
                "group_key": {
                    "runtime_surface": key[0],
                    "surface": key[1],
                    "source_component": key[2],
                    "action_class": key[3],
                    "implementation_decision": key[4],
                    "runtime_mode": key[5],
                    "baseline_decision": key[6],
                    "evidence_family": key[7],
                },
                "implementation_action": implementation_action(row),
                "target_files": target["target_files"],
                "target_functions": target["target_functions"],
                "required_stages": target["required_stages"],
                "expected_runtime_effects": target["expected_runtime_effects"],
                "required_replay_shard": f"{key[0]}::{key[2]}::{key[3]}",
                "source_chunk_paths": set(),
                "source_chunk_sha256": set(),
                "decision_map_row_ids": [],
                "source_metric_row_ids": [],
                "example_row_links": [],
                "counts": {
                    "rows": 0,
                    "candidate_count_sum": 0,
                    "counterfactual_change_count_sum": 0,
                },
                "distributions": defaultdict(Counter),
                "r_metric_sums": Counter(),
                "pollution_row_sums": Counter(),
                "null_or_unknown_fields": Counter(),
                "mixed_resolution_class_counts": Counter(),
            }
        group = groups[key]
        row_id = row.get("decision_map_row_id")
        if row_id:
            included_row_ids.add(str(row_id))
            group["decision_map_row_ids"].append(row_id)
        if row.get("source_metric_row_id"):
            group["source_metric_row_ids"].append(row["source_metric_row_id"])
        group["source_chunk_paths"].add(meta.get("chunk_path"))
        group["source_chunk_sha256"].add(meta.get("sha256"))
        group["counts"]["rows"] += 1
        group["counts"]["candidate_count_sum"] += int(row.get("candidate_count") or 0)
        group["counts"]["counterfactual_change_count_sum"] += int(row.get("counterfactual_change_count") or 0)
        for field in (
            "implementation_decision",
            "baseline_decision",
            "surface",
            "source_component",
            "action_class",
            "evidence_family",
            "runtime_mode",
            "symbol",
            "session_bucket",
            "side",
            "framework",
            "next_required_action",
        ):
            merge_counter(group["distributions"][field], row.get(field))
        for field, value in row.items():
            is_unknown_scalar = isinstance(value, str) and value in {
                "unknown_component",
                "unknown_action_class",
            }
            if value is None or value == "" or is_unknown_scalar:
                group["null_or_unknown_fields"][field] += 1
        r_metrics = row.get("r_metrics") or {}
        if isinstance(r_metrics, dict):
            for metric, value in r_metrics.items():
                if isinstance(value, (int, float)):
                    group["r_metric_sums"][metric] += float(value)
        pollution = row.get("pollution_row_sums") or {}
        if isinstance(pollution, dict):
            for metric, value in pollution.items():
                if isinstance(value, (int, float)):
                    group["pollution_row_sums"][metric] += int(value)
        for link in row.get("example_row_links", [])[:2]:
            if len(group["example_row_links"]) < 10:
                group["example_row_links"].append(link)

    mixed_lookup: dict[tuple[str, str, str, str, str], Counter[str]] = defaultdict(Counter)
    for row in mixed_resolution_rows():
        key = (
            str(row.get("surface") or "unmatched_unknown_surface"),
            str(row.get("source_component") or "unknown_component"),
            str(row.get("action_class") or "unknown_action_class"),
            str(row.get("runtime_mode") or "unknown_runtime_mode"),
            str(row.get("side") or "<NULL>"),
        )
        mixed_lookup[key][str(row.get("resolution_class") or "<NULL>")] += 1

    materialized_groups: list[dict[str, Any]] = []
    for key, group in groups.items():
        group_key_payload = group["group_key"]
        side_counts = group["distributions"]["side"]
        for side in side_counts:
            lookup_key = (
                group_key_payload["surface"],
                group_key_payload["source_component"],
                group_key_payload["action_class"],
                group_key_payload["runtime_mode"],
                side,
            )
            group["mixed_resolution_class_counts"].update(mixed_lookup.get(lookup_key, {}))
        group["source_chunk_paths"] = sorted(v for v in group["source_chunk_paths"] if v)
        group["source_chunk_sha256"] = sorted(v for v in group["source_chunk_sha256"] if v)
        group["source_metric_row_ids"] = sorted(set(group["source_metric_row_ids"]))
        group["distributions"] = {
            field: dict(sorted(counter.items()))
            for field, counter in sorted(group["distributions"].items())
        }
        group["r_metric_sums"] = dict(sorted(group["r_metric_sums"].items()))
        group["pollution_row_sums"] = dict(sorted(group["pollution_row_sums"].items()))
        group["null_or_unknown_fields"] = dict(sorted(group["null_or_unknown_fields"].items()))
        group["mixed_resolution_class_counts"] = dict(
            sorted(group["mixed_resolution_class_counts"].items())
        )
        materialized_groups.append(group)

    materialized_groups.sort(
        key=lambda item: (
            item["group_key"]["runtime_surface"],
            item["group_key"]["implementation_decision"],
            item["group_key"]["source_component"],
            item["group_key"]["action_class"],
        )
    )
    return materialized_groups


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    target = REPO_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")
    tmp.replace(target)


def summarize_groups(groups: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts: Counter[str] = Counter()
    surface_counts: Counter[str] = Counter()
    runtime_surface_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    row_sum = 0
    decision_row_id_counts: Counter[str] = Counter()
    for group in groups:
        row_sum += group["counts"]["rows"]
        decision_row_id_counts.update(str(row_id) for row_id in group["decision_map_row_ids"])
        for decision, count in group["distributions"]["implementation_decision"].items():
            decision_counts[decision] += count
        surface_counts[group["group_key"]["surface"]] += group["counts"]["rows"]
        runtime_surface_counts[group["group_key"]["runtime_surface"]] += group["counts"]["rows"]
        for stage in group["required_stages"]:
            stage_counts[stage] += group["counts"]["rows"]
    duplicate_row_ids = {
        row_id: count
        for row_id, count in sorted(decision_row_id_counts.items())
        if count > 1
    }
    return {
        "schema_version": "vnext_production_change_stage01_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "group_count": len(groups),
        "decision_map_row_count": row_sum,
        "unique_decision_map_row_ids": len(decision_row_id_counts),
        "duplicate_decision_map_row_id_count": len(duplicate_row_ids),
        "duplicate_decision_map_row_id_extra_instances": sum(
            count - 1 for count in duplicate_row_ids.values()
        ),
        "duplicate_decision_map_row_ids": duplicate_row_ids,
        "implementation_decision_counts": dict(sorted(decision_counts.items())),
        "surface_row_counts": dict(sorted(surface_counts.items())),
        "runtime_surface_row_counts": dict(sorted(runtime_surface_counts.items())),
        "required_stage_row_counts": dict(sorted(stage_counts.items())),
        "ledger_path": rel(REPO_ROOT / DECISION_SURFACE_LEDGER_PATH),
    }


def update_state(summary: dict[str, Any]) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_stage"] = "STAGE_02_PROMOTION_IMPLEMENTATION"
    state["stage_status_table"]["STAGE_01_DECISION_SURFACE_GROUPING"] = "complete"
    state["stage_status_table"]["STAGE_02_PROMOTION_IMPLEMENTATION"] = "in_progress"
    state["active_invariant"] = "implement_promoted_decision_surface_groups"
    state["first_incomplete_invariant"] = "STAGE_02_PROMOTION_IMPLEMENTATION"
    state["exact_next_action"] = (
        "Implement promoted decision-surface groups from "
        "VNEXT_PRODUCTION_CHANGE_DECISION_SURFACE_LEDGER_2026-05-25.jsonl, "
        "starting with activation-gated route/risk/pending/pre-AI surfaces whose "
        "implementation_decision is PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER."
    )
    state["output_artifact_paths"]["decision_surface_ledger"] = rel(
        REPO_ROOT / DECISION_SURFACE_LEDGER_PATH
    )
    state["output_artifact_paths"]["implementation_plan"] = rel(
        REPO_ROOT / IMPLEMENTATION_PLAN_PATH
    )
    state["output_artifact_paths"]["stage01_verification_result"] = rel(
        REPO_ROOT / STAGE01_VERIFICATION_RESULT_PATH
    )
    state["rows_groups_processed"]["stage01_groups_processed"] = summary["group_count"]
    state["rows_groups_processed"]["stage01_decision_map_rows_grouped"] = summary[
        "decision_map_row_count"
    ]
    state["row_count_hash_coverage"]["stage01_group_count"] = summary["group_count"]
    state["row_count_hash_coverage"]["stage01_runtime_surface_row_counts"] = summary[
        "runtime_surface_row_counts"
    ]
    state["row_count_hash_coverage"]["stage01_required_stage_row_counts"] = summary[
        "required_stage_row_counts"
    ]
    stage00.atomic_json_write(state_path, state)


def write_plan(summary: dict[str, Any], groups: list[dict[str, Any]]) -> None:
    lines = [
        "# vNext Production Change Implementation Plan - Stage 01",
        "",
        f"Created: {summary['created_at_utc']}",
        f"Route: `{ROUTE_ID}`",
        "",
        "Stage 01 grouped every terminal final decision-map row into runtime surfaces. "
        "The full machine-readable ledger is the authority; this plan is a readable index.",
        "",
        "## Coverage",
        "",
        f"- Decision-map rows grouped: `{summary['decision_map_row_count']}`",
        f"- Unique decision-map row ids: `{summary['unique_decision_map_row_ids']}`",
        f"- Runtime surface groups: `{summary['group_count']}`",
        f"- Ledger: `{summary['ledger_path']}`",
        "",
        "## Implementation Decision Counts",
        "",
    ]
    for decision, count in summary["implementation_decision_counts"].items():
        lines.append(f"- `{decision}`: `{count}`")
    lines.extend(["", "## Runtime Surface Row Counts", ""])
    for surface, count in summary["runtime_surface_row_counts"].items():
        lines.append(f"- `{surface}`: `{count}`")
    lines.extend(["", "## Stage Routing", ""])
    for stage, count in summary["required_stage_row_counts"].items():
        lines.append(f"- `{stage}`: `{count}` row-touch count across grouped surfaces")
    lines.extend(["", "## Next Invariant", ""])
    lines.append(
        "Implement `PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER` groups first from the ledger. "
        "Do not run final replay until grouped implementation surfaces are complete."
    )
    lines.extend(["", "## Group Ids", ""])
    for group in groups:
        g = group["group_key"]
        lines.append(
            f"- `{group['group_id']}` rows=`{group['counts']['rows']}` "
            f"decision=`{g['implementation_decision']}` surface=`{g['runtime_surface']}` "
            f"component=`{g['source_component']}` action=`{g['action_class']}`"
        )
    atomic_text_write(REPO_ROOT / IMPLEMENTATION_PLAN_PATH, "\n".join(lines) + "\n")


def verify(groups: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if summary["decision_map_row_count"] != 7555:
        failures.append(f"grouped rows expected 7555 got {summary['decision_map_row_count']}")
    unique_plus_duplicates = (
        summary["unique_decision_map_row_ids"]
        + summary["duplicate_decision_map_row_id_extra_instances"]
    )
    if unique_plus_duplicates != 7555:
        failures.append(
            "decision row id accounting does not reconcile to 7555 row instances: "
            f"{unique_plus_duplicates}"
        )
    if summary["implementation_decision_counts"] != EXPECTED_FINAL_DECISION_COUNTS:
        failures.append(
            f"implementation decision counts mismatch {summary['implementation_decision_counts']}"
        )
    if not groups:
        failures.append("no decision surface groups written")
    if not any(
        group["group_key"]["implementation_decision"] == "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER"
        for group in groups
    ):
        failures.append("no promoted groups found")
    return failures


def main() -> int:
    groups = build_groups()
    summary = summarize_groups(groups)
    failures = verify(groups, summary)
    write_jsonl(DECISION_SURFACE_LEDGER_PATH, groups)
    write_plan(summary, groups)
    if not failures:
        update_state(summary)
    result = {
        "schema_version": "vnext_production_change_stage01_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary": summary,
        "first_incomplete_invariant": (
            "STAGE_02_PROMOTION_IMPLEMENTATION" if not failures else "STAGE_01_DECISION_SURFACE_GROUPING"
        ),
    }
    atomic_json_write(STAGE01_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
