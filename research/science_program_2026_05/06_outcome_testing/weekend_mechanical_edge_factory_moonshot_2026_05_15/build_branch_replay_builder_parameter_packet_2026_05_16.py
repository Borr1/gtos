#!/usr/bin/env python3
"""Build executable research-builder parameters from branch work units."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

MATRIX_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_RESULT_2026-05-16.json"
MATRIX_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_BRANCH_LEDGER_2026-05-16.jsonl"
MATRIX_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_FAMILY_LEDGER_2026-05-16.jsonl"
MATRIX_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_SOURCE_LEDGER_2026-05-16.jsonl"
MATRIX_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_M15_LEDGER_2026-05-16.jsonl"
MATRIX_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_M1_LEDGER_2026-05-16.jsonl"
MATRIX_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_POSITIVE_LEDGER_2026-05-16.jsonl"
MATRIX_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
MATRIX_BINDING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_BINDING_LEDGER_2026-05-16.jsonl"
MATRIX_WORK_UNIT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_REPLAY_DECISION_MATRIX_WORK_UNIT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
SOURCE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_SOURCE_LEDGER_2026-05-16.jsonl"
M15_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_M15_LEDGER_2026-05-16.jsonl"
M1_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_M1_LEDGER_2026-05-16.jsonl"
POSITIVE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_POSITIVE_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BINDING_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_BINDING_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch replay-builder parameter packet only. It converts decision-matrix "
    "work units into executable research-builder parameter rows for source, "
    "M15, M1, positive, and entry/adverse families. It does not change live "
    "behavior and does not claim broker R/PnL, realized expectancy, win-rate, "
    "live-readiness, promotion, or live effect."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id") is not None}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id") is not None:
            grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        return (branch_id.rsplit("-", 1)[0], int(branch_id.rsplit("-", 1)[1]))
    except (ValueError, IndexError):
        return (branch_id, 0)


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Any, digits: int = 6) -> float | None:
    value_float = fnum(value)
    return round(value_float, digits) if value_float is not None else None


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def common_base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_queue_id": row.get("branch_queue_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
    }


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPLAY-PARAM-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def source_policy(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "source_builder_policy": "SOURCE_NOT_IN_SCOPE",
            "source_builder_parameter_score": None,
            "source_exact_acquisition_required": False,
            "source_cost_cap_required": False,
        }
    req = row.get("source_requirement")
    if req == "ACQUIRE_EXACT_SOURCE_OR_USE_COST_CAP_LOWER_BOUND_BEFORE_REPLAY":
        policy = "USE_COST_CAP_LOWER_BOUND_AND_ACQUIRE_EXACT_SOURCE"
        exact = True
        cap = True
    elif req == "AVOID_OR_REPAIR_EXACT_SOURCE_BEFORE_REPLAY":
        policy = "AVOID_UNTIL_EXACT_SOURCE_REPAIR"
        exact = True
        cap = False
    elif req == "SPLIT_LOW_HIGH_COST_BOUNDS_AND_ACQUIRE_EXACT_SOURCE":
        policy = "SPLIT_LOW_HIGH_COST_BOUNDS_AND_ACQUIRE_SOURCE"
        exact = True
        cap = False
    else:
        policy = "SOURCE_CONTEXT_ONLY"
        exact = False
        cap = False
    return {
        "source_builder_policy": policy,
        "source_builder_parameter_score": row.get("source_spec_score"),
        "source_cost_sensitivity_span": row.get("computed_cost_sensitivity_span"),
        "source_exact_acquisition_required": exact,
        "source_cost_cap_required": cap,
    }


def m15_policy(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"m15_builder_policy": "M15_NOT_IN_SCOPE", "m15_builder_parameter_score": None}
    req = row.get("m15_requirement")
    if "TARGET_FIRST_CHALLENGER" in str(req):
        policy = "TARGET_FIRST_CONSERVATIVE_BOUND_SELECTOR"
    elif "STOP_FIRST_AVOID" in str(req):
        policy = "STOP_FIRST_AVOID_OR_REDESIGN_SELECTOR"
    elif "BOUNDS" in str(req):
        policy = "TARGET_STOP_BOUNDS_SPLIT_SELECTOR"
    else:
        policy = "M15_SIDE_CAR_CONTEXT_SELECTOR"
    return {
        "m15_builder_policy": policy,
        "m15_builder_parameter_score": row.get("m15_spec_score"),
        "m15_interval_lower_mean": row.get("interval_lower_mean"),
        "m15_interval_midpoint_mean": row.get("interval_midpoint_mean"),
        "m15_interval_upper_mean": row.get("interval_upper_mean"),
        "m15_exact_chronology_claim": False,
    }


def m1_policy(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"m1_builder_policy": "M1_NOT_IN_SCOPE", "m1_builder_parameter_score": None}
    req = row.get("m1_requirement")
    if "AGGREGATE_SPLIT" in str(req):
        policy = "SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT"
    elif "STABLE_CHALLENGER" in str(req):
        policy = "SUPPORT_STABLE_CHALLENGER_SELECTOR"
    elif "SIDE_CAR" in str(req):
        policy = "M1_SIDE_CAR_CONTEXT_SELECTOR"
    else:
        policy = "M1_CONTEXT_SELECTOR"
    return {
        "m1_builder_policy": policy,
        "m1_builder_parameter_score": row.get("m1_spec_score"),
        "m1_support_adjusted_midpoint": row.get("support_adjusted_midpoint"),
        "m1_exact_chronology_claim": False,
        "m1_tick_ordering_exact": False,
    }


def positive_policy(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"positive_builder_policy": "POSITIVE_NOT_IN_SCOPE", "positive_builder_parameter_score": None}
    req = row.get("positive_requirement")
    if str(req).startswith("POSITIVE_REPLAY_NOW"):
        policy = "REPLAY_NOW_WITH_MODIFIER_PENALTIES"
    elif "REPAIR_FIRST" in str(req):
        policy = "REPAIR_SOURCE_OR_STRESS_BEFORE_REPLAY"
    elif "SIDE_CAR_REPLAY" in str(req):
        policy = "POSITIVE_SIDE_CAR_REPLAY_CONTEXT"
    else:
        policy = "POSITIVE_CONTEXT_SELECTOR"
    return {
        "positive_builder_policy": policy,
        "positive_builder_parameter_score": row.get("positive_spec_score"),
        "positive_replayable_now": row.get("positive_replayable_now"),
        "positive_modifier_penalty": row.get("positive_modifier_penalty"),
        "positive_adjusted_lower": row.get("positive_adjusted_lower"),
        "positive_adjusted_midpoint": row.get("positive_adjusted_midpoint"),
    }


def entry_policy(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {"entry_adverse_builder_policy": "ENTRY_ADVERSE_NOT_IN_SCOPE", "entry_adverse_builder_parameter_score": None}
    req = row.get("entry_adverse_requirement")
    if "BOTH_REDESIGN" in str(req) or "ENTRY_AND_ADVERSE" in str(req):
        policy = "ENTRY_AND_ADVERSE_REDESIGN_PRESSURE_SELECTOR"
    elif "ENTRY_REDESIGN" in str(req):
        policy = "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR"
    elif "PRESERVE" in str(req):
        policy = "ENTRY_ADVERSE_PRESERVE_CONTEXT"
    else:
        policy = "ENTRY_ADVERSE_CONTEXT_SELECTOR"
    return {
        "entry_adverse_builder_policy": policy,
        "entry_adverse_action_scope": (
            "ENTRY_AND_ADVERSE_REDESIGN"
            if policy == "ENTRY_AND_ADVERSE_REDESIGN_PRESSURE_SELECTOR"
            else "ENTRY_REDESIGN_ADVERSE_PRESERVE"
            if policy == "ENTRY_REDESIGN_ADVERSE_PRESERVE_SELECTOR"
            else "ENTRY_ADVERSE_PRESERVE"
            if policy == "ENTRY_ADVERSE_PRESERVE_CONTEXT"
            else "ENTRY_ADVERSE_CONTEXT"
        ),
        "entry_adverse_builder_parameter_score": row.get("entry_adverse_spec_score"),
        "target_first_rate": row.get("target_first_rate"),
        "stop_first_rate": row.get("stop_first_rate"),
        "no_fill_or_unfilled_rate": row.get("no_fill_or_unfilled_rate"),
        "fillability_rate": row.get("fillability_rate"),
        "redesign_pressure_score": row.get("redesign_pressure_score"),
    }


def branch_primary_policy(branch: dict[str, Any], policies: dict[str, dict[str, Any]]) -> tuple[str, float | None]:
    family = branch.get("primary_export_family")
    if family == "SOURCE":
        return str(policies["source"].get("source_builder_policy")), policies["source"].get("source_builder_parameter_score")
    if family == "M15":
        return str(policies["m15"].get("m15_builder_policy")), policies["m15"].get("m15_builder_parameter_score")
    if family == "M1":
        return str(policies["m1"].get("m1_builder_policy")), policies["m1"].get("m1_builder_parameter_score")
    if family == "POSITIVE":
        return str(policies["positive"].get("positive_builder_policy")), policies["positive"].get("positive_builder_parameter_score")
    if family == "ENTRY_ADVERSE":
        return str(policies["entry"].get("entry_adverse_builder_policy")), policies["entry"].get("entry_adverse_builder_parameter_score")
    return "BINDING_PROVENANCE_PRESERVE_NO_PARAMETERS", None


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Replay-Builder Parameter Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Key Distributions", ""])
    for category in [
        "primary_export_family",
        "primary_builder_policy",
        "source_builder_policy",
        "m15_builder_policy",
        "m1_builder_policy",
        "positive_builder_policy",
        "entry_adverse_builder_policy",
    ]:
        lines.append(f"### {category}")
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {
        "schema": "weekend_mechanical_edge_factory_output_manifest_v1",
        "artifacts": [],
    }
    output_paths = [
        RESULT_PATH,
        BRANCH_LEDGER,
        FAMILY_LEDGER,
        SOURCE_LEDGER,
        M15_LEDGER,
        M1_LEDGER,
        POSITIVE_LEDGER,
        ENTRY_ADVERSE_LEDGER,
        BINDING_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    output_path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    artifacts = [item for item in manifest.get("artifacts", []) if item.get("path") not in output_path_strings]
    for path in output_paths:
        artifacts.append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_replay_builder_parameter_packet",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["artifacts"] = artifacts
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_replay_builder_parameter_packet_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )


def main() -> int:
    generated_at = now_utc()
    matrix_result = read_json(MATRIX_RESULT)
    branch_rows_in = read_jsonl(MATRIX_BRANCH)
    family_rows_in = read_jsonl(MATRIX_FAMILY)
    source_rows_in = read_jsonl(MATRIX_SOURCE)
    m15_rows_in = read_jsonl(MATRIX_M15)
    m1_rows_in = read_jsonl(MATRIX_M1)
    positive_rows_in = read_jsonl(MATRIX_POSITIVE)
    entry_rows_in = read_jsonl(MATRIX_ENTRY_ADVERSE)
    binding_rows_in = read_jsonl(MATRIX_BINDING)
    work_rows_in = read_jsonl(MATRIX_WORK_UNIT)

    branch_by_id = by_branch(branch_rows_in)
    family_by_id = group_by_branch(family_rows_in)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m1_by_id = by_branch(m1_rows_in)
    positive_by_id = by_branch(positive_rows_in)
    entry_by_id = by_branch(entry_rows_in)
    binding_by_id = by_branch(binding_rows_in)
    work_by_id = by_branch(work_rows_in)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            MATRIX_RESULT,
            MATRIX_BRANCH,
            MATRIX_FAMILY,
            MATRIX_SOURCE,
            MATRIX_M15,
            MATRIX_M1,
            MATRIX_POSITIVE,
            MATRIX_ENTRY_ADVERSE,
            MATRIX_BINDING,
            MATRIX_WORK_UNIT,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    m15_rows: list[dict[str, Any]] = []
    m1_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    binding_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for branch_id in sorted(branch_by_id, key=branch_sort_key):
        branch = branch_by_id[branch_id]
        source = source_by_id.get(branch_id)
        m15 = m15_by_id.get(branch_id)
        m1 = m1_by_id.get(branch_id)
        positive = positive_by_id.get(branch_id)
        entry = entry_by_id.get(branch_id)
        binding = binding_by_id.get(branch_id)
        work = work_by_id.get(branch_id, {})

        policies = {
            "source": source_policy(source),
            "m15": m15_policy(m15),
            "m1": m1_policy(m1),
            "positive": positive_policy(positive),
            "entry": entry_policy(entry),
        }
        primary_policy, primary_score = branch_primary_policy(branch, policies)

        branch_record = {
            **common_base(branch),
            "replay_builder_parameter_branch_id": f"OHLC-GTOS-REPLAY-PARAM-BRANCH-{len(branch_rows) + 1:05d}",
            "matrix_branch_id": branch.get("matrix_branch_id"),
            "work_unit_id": work.get("work_unit_id"),
            "primary_export_family": branch.get("primary_export_family"),
            "primary_export_class": branch.get("primary_export_class"),
            "immediate_action_class": branch.get("immediate_action_class"),
            "immediate_action_subclass": branch.get("immediate_action_subclass"),
            "replay_builder_class": branch.get("replay_builder_class"),
            "replay_builder_surface": branch.get("replay_builder_surface"),
            "work_unit_status": branch.get("work_unit_status"),
            "same_resource_execution_status": branch.get("same_resource_execution_status"),
            "source_requirement": branch.get("source_requirement"),
            "m15_requirement": branch.get("m15_requirement"),
            "m1_requirement": branch.get("m1_requirement"),
            "positive_requirement": branch.get("positive_requirement"),
            "entry_adverse_requirement": branch.get("entry_adverse_requirement"),
            "primary_builder_policy": primary_policy,
            "primary_builder_parameter_score": round_or_none(primary_score),
            "proxy_actionability_score": branch.get("proxy_actionability_score"),
            "source_builder_policy": policies["source"].get("source_builder_policy"),
            "m15_builder_policy": policies["m15"].get("m15_builder_policy"),
            "m1_builder_policy": policies["m1"].get("m1_builder_policy"),
            "positive_builder_policy": policies["positive"].get("positive_builder_policy"),
            "entry_adverse_builder_policy": policies["entry"].get("entry_adverse_builder_policy"),
            "entry_adverse_action_scope": policies["entry"].get("entry_adverse_action_scope"),
            "source_exact_acquisition_required": policies["source"].get("source_exact_acquisition_required"),
            "source_cost_cap_required": policies["source"].get("source_cost_cap_required"),
            "m15_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "positive_replayable_now": policies["positive"].get("positive_replayable_now"),
            "entry_adverse_redesign_pressure_score": policies["entry"].get("redesign_pressure_score"),
            "target_stop_result": branch.get("target_stop_result"),
            "sealed_proxy_class": branch.get("sealed_proxy_class"),
            "sealed_or_proxy_outcome_status": branch.get("sealed_or_proxy_outcome_status"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(branch_record)

        if source:
            source_rows.append({**common_base(source), "source_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-SOURCE-{len(source_rows) + 1:05d}", "matrix_branch_id": branch.get("matrix_branch_id"), "source_decision_id": source.get("source_decision_id"), "source_decision_class": source.get("source_decision_class"), **policies["source"], "source_requirement": source.get("source_requirement"), "source_spec_score_class": source.get("source_spec_score_class"), "source_support_rows": source.get("source_support_rows"), "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if m15:
            m15_rows.append({**common_base(m15), "m15_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-M15-{len(m15_rows) + 1:05d}", "matrix_branch_id": branch.get("matrix_branch_id"), "m15_decision_id": m15.get("m15_decision_id"), "m15_followup_class": m15.get("m15_followup_class"), **policies["m15"], "m15_requirement": m15.get("m15_requirement"), "m15_spec_score_class": m15.get("m15_spec_score_class"), "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if m1:
            m1_rows.append({**common_base(m1), "m1_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-M1-{len(m1_rows) + 1:05d}", "matrix_branch_id": branch.get("matrix_branch_id"), "m1_decision_id": m1.get("m1_decision_id"), "m1_followup_class": m1.get("m1_followup_class"), **policies["m1"], "m1_requirement": m1.get("m1_requirement"), "m1_spec_score_class": m1.get("m1_spec_score_class"), "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if positive:
            positive_rows.append({**common_base(positive), "positive_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-POSITIVE-{len(positive_rows) + 1:05d}", "matrix_branch_id": branch.get("matrix_branch_id"), "positive_decision_id": positive.get("positive_decision_id"), "positive_followup_class": positive.get("positive_followup_class"), **policies["positive"], "positive_requirement": positive.get("positive_requirement"), "positive_spec_score_class": positive.get("positive_spec_score_class"), "positive_modifier_class": branch.get("positive_modifier_class"), "positive_control_delta_modifier_class": branch.get("positive_control_delta_modifier_class"), "positive_concentration_modifier_class": branch.get("positive_concentration_modifier_class"), "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if entry:
            entry_rows.append({**common_base(entry), "entry_adverse_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-ENTRY-ADVERSE-{len(entry_rows) + 1:05d}", "matrix_branch_id": branch.get("matrix_branch_id"), "entry_adverse_decision_id": entry.get("entry_adverse_decision_id"), "entry_adverse_followup_class": entry.get("entry_adverse_followup_class"), **policies["entry"], "entry_adverse_requirement": entry.get("entry_adverse_requirement"), "entry_adverse_spec_score_class": entry.get("entry_adverse_spec_score_class"), "entry_target_stop_balance_class": branch.get("entry_target_stop_balance_class"), "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})
        if binding:
            binding_rows.append({**common_base(binding), "binding_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-BINDING-{len(binding_rows) + 1:05d}", "matrix_branch_id": branch.get("matrix_branch_id"), "binding_decision_id": binding.get("binding_decision_id"), "binding_preserve_status": binding.get("binding_preserve_status"), "binding_builder_policy": "BINDING_PROVENANCE_PRESERVE_NO_PARAMETERS", "no_scalar_fill": True, "primary_builder_parameter_score": None, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

        family_policy_lookup = {
            "SOURCE": policies["source"].get("source_builder_policy"),
            "ORDERING": policies["m15"].get("m15_builder_policy") if m15 else policies["m1"].get("m1_builder_policy"),
            "ENTRY": policies["entry"].get("entry_adverse_builder_policy"),
            "ADVERSE": policies["entry"].get("entry_adverse_builder_policy"),
            "POSITIVE": policies["positive"].get("positive_builder_policy"),
        }
        for family_row in sorted(family_by_id.get(branch_id, []), key=lambda row: row.get("family_decision_id") or ""):
            family = family_row.get("action_family")
            family_rows.append(
                {
                    **common_base(family_row),
                    "family_parameter_id": f"OHLC-GTOS-REPLAY-PARAM-FAMILY-{len(family_rows) + 1:05d}",
                    "matrix_branch_id": branch.get("matrix_branch_id"),
                    "family_decision_id": family_row.get("family_decision_id"),
                    "family_spec_id": family_row.get("family_spec_id"),
                    "action_family": family,
                    "family_decision_class": family_row.get("family_decision_class"),
                    "family_spec_score": family_row.get("family_spec_score"),
                    "family_builder_policy": family_policy_lookup.get(family),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for category, value in [
            ("primary_export_family", branch.get("primary_export_family")),
            ("primary_builder_policy", primary_policy),
            ("source_builder_policy", policies["source"].get("source_builder_policy")),
            ("m15_builder_policy", policies["m15"].get("m15_builder_policy")),
            ("m1_builder_policy", policies["m1"].get("m1_builder_policy")),
            ("positive_builder_policy", policies["positive"].get("positive_builder_policy")),
            ("entry_adverse_builder_policy", policies["entry"].get("entry_adverse_builder_policy")),
            ("work_unit_status", branch.get("work_unit_status")),
            ("immediate_action_class", branch.get("immediate_action_class")),
            ("replay_builder_class", branch.get("replay_builder_class")),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in family_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_builder_policy"][row.get("family_builder_policy")] += 1
    for row in source_rows:
        bucket_counters["source_builder_policy_subset"][row.get("source_builder_policy")] += 1
    for row in m15_rows:
        bucket_counters["m15_builder_policy_subset"][row.get("m15_builder_policy")] += 1
    for row in m1_rows:
        bucket_counters["m1_builder_policy_subset"][row.get("m1_builder_policy")] += 1
    for row in positive_rows:
        bucket_counters["positive_builder_policy_subset"][row.get("positive_builder_policy")] += 1
    for row in entry_rows:
        bucket_counters["entry_adverse_builder_policy_subset"][row.get("entry_adverse_builder_policy")] += 1
    for row in binding_rows:
        bucket_counters["binding_builder_policy"][row.get("binding_builder_policy")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append({"bucket_id": f"OHLC-GTOS-REPLAY-PARAM-BUCKET-{len(bucket_rows) + 1:05d}", "bucket_category": category, "bucket": str(bucket), "row_count": int(count), "share": round(count / total, 9) if total else None, "safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    question_rows = [
        {"question_id": "OHLC-GTOS-REPLAY-PARAM-QUESTION-001", "question": "Which full-denominator branches now have executable research-builder parameter policies?", "answer_route": "Use branch parameter rows and primary_builder_policy."},
        {"question_id": "OHLC-GTOS-REPLAY-PARAM-QUESTION-002", "question": "Which source rows need exact acquisition, cost-cap lower-bound replay, avoid repair, or split bounds?", "answer_route": "Use source_builder_policy and source_cost_cap_required/source_exact_acquisition_required."},
        {"question_id": "OHLC-GTOS-REPLAY-PARAM-QUESTION-003", "question": "Which M15/M1 rows become target/stop bounds selectors or support-conflict selectors?", "answer_route": "Use m15_builder_policy and m1_builder_policy with exact chronology/tick flags false."},
        {"question_id": "OHLC-GTOS-REPLAY-PARAM-QUESTION-004", "question": "Which positive and entry/adverse rows have replay/repair/redesign parameter policies?", "answer_route": "Use positive_builder_policy and entry_adverse_builder_policy with modifier and redesign fields."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_matrix_branch_rows": len(branch_rows_in),
            "input_matrix_family_rows": len(family_rows_in),
            "input_matrix_source_rows": len(source_rows_in),
            "input_matrix_m15_rows": len(m15_rows_in),
            "input_matrix_m1_rows": len(m1_rows_in),
            "input_matrix_positive_rows": len(positive_rows_in),
            "input_matrix_entry_adverse_rows": len(entry_rows_in),
            "input_matrix_binding_rows": len(binding_rows_in),
            "input_matrix_work_unit_rows": len(work_rows_in),
            "branch_parameter_rows": len(branch_rows),
            "family_parameter_rows": len(family_rows),
            "source_parameter_rows": len(source_rows),
            "m15_parameter_rows": len(m15_rows),
            "m1_parameter_rows": len(m1_rows),
            "positive_parameter_rows": len(positive_rows),
            "entry_adverse_parameter_rows": len(entry_rows),
            "binding_parameter_rows": len(binding_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_matrix_counts": matrix_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_denominator_preserved": len(branch_rows) == 386,
            "family_rows_per_branch": 5,
            "source_scope": len(source_rows),
            "m15_scope": len(m15_rows),
            "m1_scope": len(m1_rows),
            "positive_scope": len(positive_rows),
            "entry_adverse_scope": len(entry_rows),
            "binding_scope": len(binding_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_LEDGER, family_rows),
        (SOURCE_LEDGER, source_rows),
        (M15_LEDGER, m15_rows),
        (M1_LEDGER, m1_rows),
        (POSITIVE_LEDGER, positive_rows),
        (ENTRY_ADVERSE_LEDGER, entry_rows),
        (BINDING_LEDGER, binding_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
