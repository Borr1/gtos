#!/usr/bin/env python3
"""Build source-stress, ordering-collapse, and positive-challenger deep packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SYNTH_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_RESULT_2026-05-16.json"
SYNTH_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
SYNTH_SOURCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_SOURCE_STRESS_ACTION_LEDGER_2026-05-16.jsonl"
SYNTH_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ORDERING_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
SYNTH_POSITIVE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_POSITIVE_CHALLENGER_COMPARISON_LEDGER_2026-05-16.jsonl"

SOURCE_REPAIR_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_EXACT_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_EXACT_SPREAD_ROUTE_LEDGER_2026-05-16.jsonl"
AMBIGUITY_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_BRANCH_CLASSIFICATION_LEDGER_2026-05-16.jsonl"
AMBIGUITY_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ORDERING_ROUTE_LEDGER_2026-05-16.jsonl"
AMBIGUITY_INTERVAL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_INTERVAL_PRESERVATION_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_BINDING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_TARGETSTOP_NA_BINDING_LEDGER_2026-05-16.jsonl"

EXACT_SPREAD_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
M1_SPREAD_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
RECOVERED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH_LEDGER_2026-05-16.jsonl"
SIERRA_SOURCE_MANIFEST_PATH = ROUTE_DIR / "SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_2026-05-16.json"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP_RESULT_2026-05-16.json"
SOURCE_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UNAVAILABLE_ACQUISITION_LEDGER_2026-05-16.jsonl"
SOURCE_PROXY_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_PROXY_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"
ZERO_TO_SPREAD_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ZERO_TO_SPREAD_M1_REPLAY_IMPLICATION_LEDGER_2026-05-16.jsonl"
EXACT_REPAIR_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_EXACT_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"
ORDERING_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ORDERING_COLLAPSE_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
M1_CHRONOLOGICAL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_CHRONOLOGICAL_COLLAPSE_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_INTERVAL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"
M15_ONLY_INTERVAL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_ONLY_INTERVAL_ROUTE_LEDGER_2026-05-16.jsonl"
RECOVERED_PROXY_NO_M1_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RECOVERED_PROXY_NO_M1_KEY_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_PRESERVE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_TARGETSTOP_NA_BINDING_PRESERVATION_LEDGER_2026-05-16.jsonl"
POSITIVE_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
POSITIVE_SCOPE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_SCOPE_COMPARISON_LEDGER_2026-05-16.jsonl"
POSITIVE_MODIFIER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CONTROL_CONCENTRATION_MODIFIER_LEDGER_2026-05-16.jsonl"
POSITIVE_CROSS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_SOURCE_ORDERING_CROSS_LEDGER_2026-05-16.jsonl"
POSITIVE_IMPL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Source/order/positive deep branch packet only. It preserves all 386 "
    "historical proxy branches and decomposes source repair/stress, ordering "
    "collapse/interval, and positive challenger modifiers without live, broker, "
    "promotion, win-rate, PnL, or realized expectancy claims."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no, "_source_path": str(path)}


def rows(path: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path) or [])


def write_jsonl(path: Path, output_rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def norm(value: Any) -> str:
    if value is None:
        return "None"
    try:
        return f"{float(value):.10g}"
    except (TypeError, ValueError):
        return str(value)


def branch_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        norm(row.get("route_candidate_id")),
        norm(row.get("entry_variant")),
        norm(row.get("target_stop_contract_id")),
        norm(row.get("symbol")),
        norm(row.get("side")),
        norm(row.get("target_multiple")),
        norm(row.get("stop_multiple")),
    )


def compact_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (norm(row.get("route_candidate_id")), norm(row.get("entry_variant")), norm(row.get("target_stop_contract_id")))


def group_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def group_many_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def group_by_key(input_rows: list[dict[str, Any]]) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[branch_key(row)].append(row)
    return grouped


def group_by_compact_key(input_rows: list[dict[str, Any]]) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[compact_key(row)].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def join_diagnostic(base_keys: set[tuple[str, ...]], grouped: dict[tuple[str, ...], list[dict[str, Any]]], policy: str) -> dict[str, Any]:
    input_rows = sum(len(values) for values in grouped.values())
    matched_rows = sum(len(values) for key, values in grouped.items() if key in base_keys)
    return {
        "join_key_policy": policy,
        "input_rows": input_rows,
        "matched_rows_to_386_branch_keys": matched_rows,
        "unmatched_rows_to_386_branch_keys": input_rows - matched_rows,
        "matched_branch_keys": sum(1 for key in base_keys if grouped.get(key)),
    }


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        SYNTH_RESULT_PATH,
        SYNTH_BRANCH_PATH,
        SYNTH_SOURCE_PATH,
        SYNTH_ORDERING_PATH,
        SYNTH_POSITIVE_PATH,
        SOURCE_REPAIR_BRANCH_PATH,
        SOURCE_EXACT_ROUTE_PATH,
        AMBIGUITY_BRANCH_PATH,
        AMBIGUITY_ORDERING_PATH,
        AMBIGUITY_INTERVAL_PATH,
        TARGETSTOP_NA_BINDING_PATH,
        EXACT_SPREAD_DELTA_PATH,
        EXACT_SPREAD_UNAVAILABLE_PATH,
        M1_SPREAD_REPLAY_PATH,
        M1_FILL_BAR_STRESS_PATH,
        PATH_AMBIGUITY_PATH,
        RECOVERED_PATH,
        SIERRA_SOURCE_MANIFEST_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-SRC-ORD-POS-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def source_deep_action(source_cls: str) -> tuple[str, str, str]:
    if source_cls == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        return ("SOURCE_UNAVAILABLE_ACQUIRE_OR_STRESS", "SOURCE_UNAVAILABLE_ACQUISITION_LEDGER", "Preserve low/high stress interval until current exact source is acquired or proven unavailable.")
    if source_cls == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_USE_M1_REPLAY":
        return ("SOURCE_ZERO_TO_SPREAD_REPLAY_IMPLICATION", "ZERO_TO_SPREAD_M1_REPLAY_IMPLICATION_LEDGER", "Use M1 spread-adjusted replay; never mix zero-cost descriptors with spread-adjusted descriptors.")
    if source_cls == "EXACT_SPREAD_RECOMPUTED_USE_REPAIRED_DESCRIPTOR":
        return ("SOURCE_EXACT_REPAIR_RECOMPUTED_READY", "EXACT_REPAIR_BRANCH_LEDGER", "Use repaired exact-spread descriptor in research harnesses.")
    if source_cls == "CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED":
        return ("SOURCE_EXACT_CLEAN_PRESERVED", "EXACT_REPAIR_BRANCH_LEDGER", "Preserve clean exact-source descriptor.")
    return ("SOURCE_TARGETSTOP_NA_BINDING_ONLY", "EXACT_REPAIR_BRANCH_LEDGER", "Bind target/stop NA rows to provenance/signature scope only.")


def ordering_deep_action(ordering_cls: str) -> tuple[str, str, str, bool]:
    if ordering_cls == "M1_CHRONOLOGICAL_COLLAPSE_AVAILABLE":
        return ("ORDERING_M1_CHRONOLOGICAL_COLLAPSE", "M1_CHRONOLOGICAL_COLLAPSE_LEDGER", "Use existing M1 chronology as current collapse source.", False)
    if ordering_cls == "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED":
        return ("ORDERING_M1_FILL_BAR_STRESS_INTERVAL", "M1_FILL_BAR_STRESS_INTERVAL_LEDGER", "Preserve conservative/optimistic M1 fill-bar interval.", False)
    if ordering_cls == "M15_INTERVAL_ONLY_NO_M1_SOURCE":
        return ("ORDERING_M15_ONLY_INTERVAL_ROUTE", "M15_ONLY_INTERVAL_ROUTE_LEDGER", "Keep M15-only ordering as non-exact interval/proxy route.", True)
    if ordering_cls == "RECOVERED_PROXY_ONLY_NO_M1_KEY":
        return ("ORDERING_RECOVERED_PROXY_NO_M1_KEY", "RECOVERED_PROXY_NO_M1_KEY_LEDGER", "Preserve recovered proxy and route key/source repair.", False)
    if ordering_cls == "TARGETSTOP_NA_BINDING_ONLY":
        return ("ORDERING_TARGETSTOP_NA_BINDING_PRESERVE", "TARGETSTOP_NA_BINDING_PRESERVATION_LEDGER", "Preserve target/stop NA binding rows.", False)
    return ("ORDERING_NO_COLLAPSE_REQUIRED", "ORDERING_COLLAPSE_DEEP_BRANCH_LEDGER", "No ordering collapse is required by current source.", False)


def positive_deep_action(positive_cls: str, control_mod: str, concentration_mod: str) -> tuple[str, str]:
    if positive_cls == "POSITIVE_AFTER_EXACT_REPAIR":
        base = "POSITIVE_EXACT_REPAIR_COMPARISON"
    elif positive_cls == "POSITIVE_ZERO_TO_SPREAD_REPLAY_COMPARABLE":
        base = "POSITIVE_ZERO_TO_SPREAD_M1_REPLAY_COMPARISON"
    elif positive_cls == "POSITIVE_STRESS_INTERVAL_ONLY":
        base = "POSITIVE_STRESS_ONLY_NOT_SCALAR_COLLAPSED"
    else:
        base = "POSITIVE_NOT_IN_SCOPE_CONTROL_ROW_PRESERVED"
    modifier = f"{control_mod}__{concentration_mod}"
    return base, modifier


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifacts = [
        (Path(__file__).resolve(), "builder"),
        (RESULT_PATH, "result"),
        (SOURCE_DEEP_BRANCH_PATH, "source_stress_deep_branch_ledger"),
        (SOURCE_UNAVAILABLE_PATH, "source_unavailable_acquisition_ledger"),
        (SOURCE_PROXY_STRESS_PATH, "source_proxy_stress_interval_ledger"),
        (ZERO_TO_SPREAD_PATH, "zero_to_spread_m1_replay_implication_ledger"),
        (EXACT_REPAIR_BRANCH_PATH, "exact_repair_branch_ledger"),
        (ORDERING_DEEP_BRANCH_PATH, "ordering_collapse_deep_branch_ledger"),
        (M1_CHRONOLOGICAL_PATH, "m1_chronological_collapse_ledger"),
        (M1_FILL_BAR_INTERVAL_PATH, "m1_fill_bar_stress_interval_ledger"),
        (M15_ONLY_INTERVAL_PATH, "m15_only_interval_route_ledger"),
        (RECOVERED_PROXY_NO_M1_PATH, "recovered_proxy_no_m1_key_ledger"),
        (TARGETSTOP_NA_PRESERVE_PATH, "targetstop_na_binding_preservation_ledger"),
        (POSITIVE_DEEP_BRANCH_PATH, "positive_challenger_deep_branch_ledger"),
        (POSITIVE_SCOPE_PATH, "positive_scope_comparison_ledger"),
        (POSITIVE_MODIFIER_PATH, "positive_control_concentration_modifier_ledger"),
        (POSITIVE_CROSS_PATH, "positive_source_ordering_cross_ledger"),
        (POSITIVE_IMPL_PATH, "positive_implementation_candidate_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SOURCE_MANIFEST_LEDGER_PATH, "source_manifest_ledger"),
        (SUMMARY_PATH, "summary"),
    ]
    artifact_names = {path.name for path, _ in artifacts}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in artifacts[1:]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_source_ordering_positive_deep",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path, _ in artifacts}
    manifest["artifacts"] = [row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths]
    for path, artifact_type in artifacts:
        manifest["artifacts"].append({"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": artifact_type})
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "event_type": "branch_source_ordering_positive_deep_packet_built",
        "artifact": RESULT_PATH.name,
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = ["# Source/Ordering/Positive Deep Packet", "", f"Generated UTC: `{result['generated_utc']}`", "", "## Boundary", "", CLAIM_BOUNDARY, "", "## Counts", ""]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in ["source_stress_action_class", "ordering_collapse_action_class", "positive_challenger_class", "positive_deep_action_class"]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"][category].items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    synth_result = read_json(SYNTH_RESULT_PATH)
    branch_rows = rows(SYNTH_BRANCH_PATH)
    base_full_keys = {branch_key(row) for row in branch_rows}
    base_compact_keys = {compact_key(row) for row in branch_rows}
    source_by_branch = group_by_branch(rows(SYNTH_SOURCE_PATH))
    ordering_by_branch = group_by_branch(rows(SYNTH_ORDERING_PATH))
    positive_by_branch = group_by_branch(rows(SYNTH_POSITIVE_PATH))
    source_repair_by_branch = group_by_branch(rows(SOURCE_REPAIR_BRANCH_PATH))
    ambiguity_by_branch = group_by_branch(rows(AMBIGUITY_BRANCH_PATH))
    ambiguity_interval_by_branch = group_by_branch(rows(AMBIGUITY_INTERVAL_PATH))
    targetstop_binding_by_branch = group_many_by_branch(rows(TARGETSTOP_NA_BINDING_PATH))

    exact_delta_by_compact = group_by_compact_key(rows(EXACT_SPREAD_DELTA_PATH))
    path_ambiguity_by_compact = group_by_compact_key(rows(PATH_AMBIGUITY_PATH))
    exact_unavailable_by_key = group_by_key(rows(EXACT_SPREAD_UNAVAILABLE_PATH))
    m1_replay_by_key = group_by_key(rows(M1_SPREAD_REPLAY_PATH))
    fill_bar_by_key = group_by_key(rows(M1_FILL_BAR_STRESS_PATH))
    recovered_by_key = group_by_key(rows(RECOVERED_PATH))
    join_diagnostics = {
        "exact_spread_delta": join_diagnostic(base_compact_keys, exact_delta_by_compact, "compact_route_entry_targetstop"),
        "path_ambiguity": join_diagnostic(base_compact_keys, path_ambiguity_by_compact, "compact_route_entry_targetstop"),
        "exact_spread_unavailable": join_diagnostic(base_full_keys, exact_unavailable_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "m1_spread_replay": join_diagnostic(base_full_keys, m1_replay_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "m1_fill_bar_stress": join_diagnostic(base_full_keys, fill_bar_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "recovered_unfilled": join_diagnostic(base_full_keys, recovered_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
    }

    source_deep_rows: list[dict[str, Any]] = []
    source_unavailable_rows: list[dict[str, Any]] = []
    source_proxy_stress_rows: list[dict[str, Any]] = []
    zero_to_spread_rows: list[dict[str, Any]] = []
    exact_repair_rows: list[dict[str, Any]] = []
    ordering_deep_rows: list[dict[str, Any]] = []
    m1_chrono_rows: list[dict[str, Any]] = []
    m1_fill_interval_rows: list[dict[str, Any]] = []
    m15_only_rows: list[dict[str, Any]] = []
    recovered_no_m1_rows: list[dict[str, Any]] = []
    targetstop_na_rows: list[dict[str, Any]] = []
    positive_deep_rows: list[dict[str, Any]] = []
    positive_scope_rows: list[dict[str, Any]] = []
    positive_modifier_rows: list[dict[str, Any]] = []
    positive_cross_counter: Counter[tuple[str, str, str]] = Counter()
    positive_impl_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    edge_counter: Counter[str] = Counter()

    for index, branch in enumerate(branch_rows, 1):
        branch_id = str(branch.get("branch_queue_id"))
        key = branch_key(branch)
        ckey = compact_key(branch)
        source = source_by_branch.get(branch_id, {})
        ordering = ordering_by_branch.get(branch_id, {})
        positive = positive_by_branch.get(branch_id, {})
        repair = source_repair_by_branch.get(branch_id, {})
        ambiguity = ambiguity_by_branch.get(branch_id, {})
        interval = ambiguity_interval_by_branch.get(branch_id, {})
        source_cls = str(branch.get("source_stress_action_class"))
        ordering_cls = str(branch.get("ordering_collapse_action_class"))
        positive_cls = str(branch.get("positive_challenger_class"))
        source_action, source_ledger, source_note = source_deep_action(source_cls)
        ordering_action, ordering_ledger, ordering_note, m15_non_exact = ordering_deep_action(ordering_cls)
        control_mod = str(branch.get("positive_control_delta_modifier_class") or positive.get("positive_control_delta_modifier_class"))
        conc_mod = str(branch.get("positive_concentration_modifier_class") or positive.get("positive_concentration_modifier_class"))
        positive_action, positive_modifier = positive_deep_action(positive_cls, control_mod, conc_mod)
        common = {
            "branch_queue_id": branch_id,
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
        }
        source_record = {
            "source_stress_deep_branch_id": f"OHLC-GTOS-SRC-ORD-POS-SOURCE-{index:05d}",
            **common,
            "source_stress_action_class": source_cls,
            "source_deep_action_class": source_action,
            "source_deep_output_route": source_ledger,
            "source_deep_note": source_note,
            "repair_feasibility_class": repair.get("repair_feasibility_class"),
            "source_repair_route_class": repair.get("source_repair_route_class"),
            "exact_spread_descriptor_delta_rows": len(exact_delta_by_compact.get(ckey, [])),
            "exact_spread_unavailable_stress_rows": len(exact_unavailable_by_key.get(key, [])),
            "m1_spread_adjusted_replay_rows": len(m1_replay_by_key.get(key, [])),
            "m1_fill_bar_stress_rows": len(fill_bar_by_key.get(key, [])),
            "sierra_depth_manifest_context": source.get("sierra_depth_manifest_context"),
        }
        source_deep_rows.append(source_record)
        if source_cls == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
            source_unavailable_rows.append({**source_record, "unavailable_support_rows": len(exact_unavailable_by_key.get(key, [])), "acquisition_status": "CURRENT_EXACT_SPREAD_SOURCE_UNAVAILABLE_STRESS_BOUNDED"})
            source_proxy_stress_rows.append({**source_record, "stress_interval_policy": "LOW_HIGH_SPREAD_BOUNDS_ONLY_NO_SCALAR_COLLAPSE"})
            edge_counter["exact_unavailable_rows_stress_bounded"] += 1
        elif source_cls == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_USE_M1_REPLAY":
            zero_to_spread_rows.append({**source_record, "m1_replay_policy": "USE_SPREAD_ADJUSTED_M1_REPLAY_NOT_ZERO_COST_DESCRIPTOR"})
        else:
            exact_repair_rows.append({**source_record, "exact_repair_policy": "RECOMPUTED_OR_CLEAN_OR_BINDING_SOURCE_PRESERVED"})

        ordering_record = {
            "ordering_collapse_deep_branch_id": f"OHLC-GTOS-SRC-ORD-POS-ORDER-{index:05d}",
            **common,
            "ordering_collapse_action_class": ordering_cls,
            "ordering_deep_action_class": ordering_action,
            "ordering_deep_output_route": ordering_ledger,
            "ordering_deep_note": ordering_note,
            "m15_only_is_exact_chronology": False if m15_non_exact else None,
            "ambiguity_collapse_class": ambiguity.get("ambiguity_collapse_class"),
            "interval_preservation_class": ambiguity.get("interval_preservation_class"),
            "interval_rstyle_lower_mean": interval.get("rstyle_lower_mean"),
            "interval_rstyle_midpoint_mean": interval.get("rstyle_midpoint_mean"),
            "interval_rstyle_upper_mean": interval.get("rstyle_upper_mean"),
            "path_ambiguity_rows": len(path_ambiguity_by_compact.get(ckey, [])),
            "m1_replay_rows": len(m1_replay_by_key.get(key, [])),
            "m1_fill_bar_stress_rows": len(fill_bar_by_key.get(key, [])),
            "recovered_signature_path_rows": len(recovered_by_key.get(key, [])),
        }
        ordering_deep_rows.append(ordering_record)
        if ordering_cls == "M1_CHRONOLOGICAL_COLLAPSE_AVAILABLE":
            m1_chrono_rows.append(ordering_record)
        elif ordering_cls == "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED":
            m1_fill_interval_rows.append({**ordering_record, "interval_policy": "CONSERVATIVE_OPTIMISTIC_BOUNDS_PRESERVED"})
        elif ordering_cls == "M15_INTERVAL_ONLY_NO_M1_SOURCE":
            m15_only_rows.append({**ordering_record, "m15_only_proxy_variants": ["STOP_FIRST_BOUND", "TARGET_FIRST_BOUND", "MIDPOINT", "CLOSE_DIRECTION_PROXY"], "exact_chronology_claim": False})
        elif ordering_cls == "RECOVERED_PROXY_ONLY_NO_M1_KEY":
            recovered_no_m1_rows.append(ordering_record)
            edge_counter["recovered_without_m1_key"] += 1
        elif ordering_cls == "TARGETSTOP_NA_BINDING_ONLY":
            targetstop_na_rows.extend(targetstop_binding_by_branch.get(branch_id, []))
            edge_counter["targetstop_na_preserved"] += 1
        if ambiguity.get("interval_preservation_class") == "INTERVAL_STRADDLES_ZERO":
            edge_counter["interval_straddles_preserved"] += 1

        positive_record = {
            "positive_challenger_deep_branch_id": f"OHLC-GTOS-SRC-ORD-POS-POSITIVE-{index:05d}",
            **common,
            "positive_challenger_class": positive_cls,
            "positive_deep_action_class": positive_action,
            "positive_control_delta_modifier_class": control_mod,
            "positive_concentration_modifier_class": conc_mod,
            "positive_combined_modifier_class": positive_modifier,
            "same_route_peer_delta": branch.get("same_route_peer_delta") or positive.get("same_route_peer_delta"),
            "same_route_peer_count": branch.get("same_route_peer_count") or positive.get("same_route_peer_count"),
            "source_stress_action_class": source_cls,
            "ordering_collapse_action_class": ordering_cls,
            "implementation_prerequisite": source_action if "STRESS" in positive_action or "ZERO_TO_SPREAD" in positive_action else ordering_action,
        }
        positive_deep_rows.append(positive_record)
        positive_scope_rows.append({**positive_record, "positive_scope_status": "POSITIVE_PROXY_MIDPOINT" if positive_cls != "NOT_POSITIVE_CHALLENGER_SCOPE" else "NON_POSITIVE_CONTROL_RETAINED"})
        positive_modifier_rows.append({**positive_record, "modifier_preservation_status": "CONTROL_AND_CONCENTRATION_MODIFIERS_ATTACHED"})
        positive_cross_counter[(positive_cls, source_cls, ordering_cls)] += 1
        if positive_cls != "NOT_POSITIVE_CHALLENGER_SCOPE":
            positive_impl_rows.append(positive_record)

        for category, value in {
            "source_stress_action_class": source_cls,
            "source_deep_action_class": source_action,
            "ordering_collapse_action_class": ordering_cls,
            "ordering_deep_action_class": ordering_action,
            "positive_challenger_class": positive_cls,
            "positive_deep_action_class": positive_action,
            "positive_control_delta_modifier_class": control_mod,
            "positive_concentration_modifier_class": conc_mod,
        }.items():
            bucket_counters[category][str(value)] += 1

    positive_cross_rows = []
    for (positive_cls, source_cls, ordering_cls), count in sorted(positive_cross_counter.items()):
        positive_cross_rows.append(
            {
                "positive_source_ordering_cross_id": f"OHLC-GTOS-SRC-ORD-POS-CROSS-{len(positive_cross_rows) + 1:04d}",
                "positive_challenger_class": positive_cls,
                "source_stress_action_class": source_cls,
                "ordering_collapse_action_class": ordering_cls,
                "branch_count": int(count),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-SRC-ORD-POS-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "branch_count": int(count),
                    "branch_share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )
    edge_counter["m1_fill_bar_source_fail_closed_rows_carried"] = synth_result.get("edge_checks", {}).get("m1_fill_bar_source_fail_closed_rows_carried", 0)
    question_rows = [
        {"question_id": "OHLC-GTOS-SRC-ORD-POS-QUESTION-001", "question": "Which source rows can use exact repair, M1 replay proxy, or only stress bounds?", "answer_route": "Use source-stress deep ledgers."},
        {"question_id": "OHLC-GTOS-SRC-ORD-POS-QUESTION-002", "question": "Which ordering rows collapse with M1, preserve M1 interval, or remain M15-only non-exact?", "answer_route": "Use ordering-collapse deep ledgers."},
        {"question_id": "OHLC-GTOS-SRC-ORD-POS-QUESTION-003", "question": "Which positive rows remain comparable after source/order/control/concentration modifiers?", "answer_route": "Use positive challenger deep and modifier ledgers."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})
    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_synthesis_rows": len(branch_rows),
            "source_stress_deep_branch_rows": len(source_deep_rows),
            "source_unavailable_acquisition_rows": len(source_unavailable_rows),
            "source_proxy_stress_interval_rows": len(source_proxy_stress_rows),
            "zero_to_spread_m1_replay_implication_rows": len(zero_to_spread_rows),
            "exact_repair_branch_rows": len(exact_repair_rows),
            "ordering_collapse_deep_branch_rows": len(ordering_deep_rows),
            "m1_chronological_collapse_rows": len(m1_chrono_rows),
            "m1_fill_bar_stress_interval_rows": len(m1_fill_interval_rows),
            "m15_only_interval_route_rows": len(m15_only_rows),
            "recovered_proxy_no_m1_key_rows": len(recovered_no_m1_rows),
            "targetstop_na_binding_preservation_rows": len(targetstop_na_rows),
            "positive_challenger_deep_branch_rows": len(positive_deep_rows),
            "positive_scope_comparison_rows": len(positive_scope_rows),
            "positive_control_concentration_modifier_rows": len(positive_modifier_rows),
            "positive_source_ordering_cross_rows": len(positive_cross_rows),
            "positive_implementation_candidate_rows": len(positive_impl_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "edge_checks": compact_counter(edge_counter),
        "join_diagnostics": join_diagnostics,
        "source_manifest_hash": manifest_hash,
    }
    for path, output_rows in [
        (SOURCE_DEEP_BRANCH_PATH, source_deep_rows),
        (SOURCE_UNAVAILABLE_PATH, source_unavailable_rows),
        (SOURCE_PROXY_STRESS_PATH, source_proxy_stress_rows),
        (ZERO_TO_SPREAD_PATH, zero_to_spread_rows),
        (EXACT_REPAIR_BRANCH_PATH, exact_repair_rows),
        (ORDERING_DEEP_BRANCH_PATH, ordering_deep_rows),
        (M1_CHRONOLOGICAL_PATH, m1_chrono_rows),
        (M1_FILL_BAR_INTERVAL_PATH, m1_fill_interval_rows),
        (M15_ONLY_INTERVAL_PATH, m15_only_rows),
        (RECOVERED_PROXY_NO_M1_PATH, recovered_no_m1_rows),
        (TARGETSTOP_NA_PRESERVE_PATH, targetstop_na_rows),
        (POSITIVE_DEEP_BRANCH_PATH, positive_deep_rows),
        (POSITIVE_SCOPE_PATH, positive_scope_rows),
        (POSITIVE_MODIFIER_PATH, positive_modifier_rows),
        (POSITIVE_CROSS_PATH, positive_cross_rows),
        (POSITIVE_IMPL_PATH, positive_impl_rows),
        (BUCKET_PATH, bucket_rows),
        (QUESTION_PATH, question_rows),
        (SOURCE_MANIFEST_LEDGER_PATH, source_rows),
    ]:
        write_jsonl(path, output_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
