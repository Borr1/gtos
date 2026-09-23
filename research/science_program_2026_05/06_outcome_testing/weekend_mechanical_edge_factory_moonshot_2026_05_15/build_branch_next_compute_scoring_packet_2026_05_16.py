#!/usr/bin/env python3
"""Build a full-denominator next-compute scoring packet.

The full outcome synthesis establishes branch facts. This packet converts those
facts into same-resource next-compute score rows without dropping branches or
turning proxy metrics into validation claims.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

FULL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_RESULT_2026-05-16.json"
FULL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
FULL_ACTION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_ACTION_MATRIX_LEDGER_2026-05-16.jsonl"
FULL_NEXT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_NEXT_COMPUTE_LEDGER_2026-05-16.jsonl"
SOURCE_STRESS_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_STRESS_SUPPORT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_SUPPORT_LEDGER_2026-05-16.jsonl"
M15_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
M15_PROXY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
M1_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
M1_PROXY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
POSITIVE_REPLAY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_REPLAY_SPEC_LEDGER_2026-05-16.jsonl"
ENTRY_REDESIGN = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ADVERSE_REDESIGN = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_RESULT_2026-05-16.json"
BRANCH_SCORE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_BRANCH_LEDGER_2026-05-16.jsonl"
ACTION_SCORE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_ACTION_FAMILY_LEDGER_2026-05-16.jsonl"
SOURCE_RISK_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_SOURCE_RISK_ROUTER_LEDGER_2026-05-16.jsonl"
M15_SCORE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_M15_INTERVAL_LEDGER_2026-05-16.jsonl"
M1_CONFLICT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_M1_CONFLICT_LEDGER_2026-05-16.jsonl"
POSITIVE_SCORE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch next-compute scoring packet only. It converts the full 386-branch "
    "outcome synthesis into same-resource proxy score vectors and family score "
    "ledgers for source stress, M15 interval, M1 support conflict, positive "
    "replay, and entry/adverse redesign. Scores are mechanical triage/proxy "
    "metrics, not broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, promotion, or live behavior claims."
)

TRIAGE_FORMULA = (
    "mechanical_triage_score_proxy = conservative_rstyle_or_midpoint + "
    "0.50 * same_route_peer_delta - source_penalty - ambiguity_penalty - "
    "concentration_penalty. This is a deterministic branch-local priority "
    "proxy only; it is not realized expectancy."
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
            except json.JSONDecodeError:
                rows.append({"_parse_error": True, "_line_no": line_no, "_source_path": str(path)})
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id") is not None}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id") is not None:
            grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


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


def round_or_none(value: float | None, digits: int = 6) -> float | None:
    return round(value, digits) if value is not None else None


def concentration_max_share(row: dict[str, Any]) -> float | None:
    values = []
    for info in (row.get("concentration_summary") or {}).values():
        share = fnum((info or {}).get("branch_share"))
        if share is not None:
            values.append(share)
    return max(values) if values else None


def source_penalty(row: dict[str, Any]) -> float:
    status = row.get("source_execution_class")
    if status == "SOURCE_EXACT_UNAVAILABLE_STRESS_OR_ACQUIRE":
        return 0.25
    if status == "SOURCE_M1_SPREAD_PROXY_COMPUTABLE_NOW":
        return 0.10
    if status == "SOURCE_BINDING_ONLY_NO_SCALAR":
        return 0.05
    return 0.0


def ambiguity_penalty(row: dict[str, Any]) -> float:
    status = row.get("ambiguity_status")
    if status == "HIGH_ORDERING_AMBIGUITY":
        return 0.20
    if status == "SOME_ORDERING_AMBIGUITY":
        return 0.10
    return 0.0


def concentration_penalty(row: dict[str, Any]) -> float:
    status = row.get("effective_n_concentration_class")
    if status == "UNDERPOWERED_EFFECTIVE_N_LT_20":
        return 0.25
    if status in {"CONCENTRATION_HIGH_SYMBOL_OR_ROUTE_SHARE", "DUPLICATE_INFLATION_HIGH_MATERIAL_ROWS_OVER_EVENTS"}:
        return 0.15
    return 0.0


def score_direction(lower: float | None, midpoint: float | None, upper: float | None) -> str:
    if lower is None and midpoint is None and upper is None:
        return "NO_SCALAR_BINDING_SCOPE"
    if lower is not None and lower > 0:
        return "CONSERVATIVE_POSITIVE_PROXY"
    if upper is not None and upper < 0:
        return "CONSERVATIVE_NEGATIVE_PROXY"
    if midpoint is not None and midpoint > 0:
        return "MIDPOINT_POSITIVE_INTERVAL_RISK"
    if midpoint is not None and midpoint < 0:
        return "MIDPOINT_NEGATIVE_INTERVAL_RISK"
    return "INTERVAL_STRADDLES_OR_NEUTRAL"


def triage(row: dict[str, Any]) -> dict[str, Any]:
    lower = fnum(row.get("rstyle_lower_mean"))
    midpoint = fnum(row.get("rstyle_midpoint_mean"))
    upper = fnum(row.get("rstyle_upper_mean"))
    conservative = lower if lower is not None else midpoint
    peer_delta = fnum((row.get("pass_control_delta") or {}).get("same_route_peer_delta"))
    source = source_penalty(row)
    ambiguity = ambiguity_penalty(row)
    concentration = concentration_penalty(row)
    score = None
    if conservative is not None:
        score = conservative + 0.5 * (peer_delta or 0.0) - source - ambiguity - concentration
    width = (upper - lower) if upper is not None and lower is not None else None
    return {
        "mechanical_triage_score_proxy": round_or_none(score),
        "score_direction_class": score_direction(lower, midpoint, upper),
        "conservative_rstyle_proxy": round_or_none(conservative),
        "rstyle_midpoint_proxy": round_or_none(midpoint),
        "rstyle_interval_width": round_or_none(width),
        "same_route_peer_delta": round_or_none(peer_delta),
        "source_penalty": source,
        "ambiguity_penalty": ambiguity,
        "concentration_penalty": concentration,
        "formula": TRIAGE_FORMULA,
    }


def family_action_score(family: str, branch: dict[str, Any], related: dict[str, Any]) -> dict[str, Any]:
    triage_info = triage(branch)
    base_score = fnum(triage_info.get("mechanical_triage_score_proxy"))
    action_class = related.get("action_class") or related.get("deep_class") or "NO_ACTION_CLASS"
    if family == "SOURCE":
        if branch.get("source_stress_status") == "SOURCE_STRESS_DESCRIPTOR_FLIPS_TARGET_STOP":
            family_score = (base_score or 0.0) - 0.25
            score_class = "SOURCE_STRESS_FLIP_SCORE_REQUIRES_ROUTER_OR_ACQUISITION"
        elif branch.get("source_execution_class") == "SOURCE_EXACT_CLEAN_COMPUTABLE_NOW":
            family_score = base_score
            score_class = "SOURCE_EXACT_CLEAN_SCORE_USABLE_AS_PROXY"
        else:
            family_score = base_score
            score_class = "SOURCE_PROXY_OR_BINDING_SCORE_PRESERVED"
    elif family == "ORDERING":
        if str(branch.get("m1_support_vs_branch_status", "")).startswith("M1_SUPPORT_ALL_POSITIVE_BUT_BRANCH"):
            family_score = (base_score or 0.0) + 0.20
            score_class = "ORDERING_M1_SUPPORT_CONFLICT_NEEDS_SPLIT"
        elif branch.get("m15_interval_status") in {"INTERVAL_ALL_POSITIVE", "INTERVAL_ALL_NEGATIVE", "INTERVAL_STRADDLES_ZERO"}:
            family_score = base_score
            score_class = "ORDERING_M15_INTERVAL_SCORE_PRESERVED"
        else:
            family_score = base_score
            score_class = "ORDERING_SCORE_ALREADY_COLLAPSED_OR_BINDING"
    elif family == "ENTRY":
        family_score = base_score
        score_class = "ENTRY_REDESIGN_SCORE_FROM_FILLABILITY_CONTEXT"
    elif family == "ADVERSE":
        family_score = base_score
        if branch.get("target_stop_result") == "STOP_FIRST_PROXY_DOMINANT":
            score_class = "ADVERSE_STOP_FIRST_AVOID_OR_REDESIGN_SCORE"
        else:
            score_class = "ADVERSE_SCORE_NO_STOP_FIRST_DOMINANCE"
    elif family == "POSITIVE":
        if related.get("layer_context") is True or branch.get("branch_result_class") == "POSITIVE_RSTYLE_PROXY_MIDPOINT":
            family_score = base_score
            score_class = "POSITIVE_REPLAY_OR_CHALLENGER_SCORE"
        else:
            family_score = None
            score_class = "POSITIVE_NO_CHALLENGER_SCORE_SCOPE"
    else:
        family_score = base_score
        score_class = "UNKNOWN_FAMILY_SCORE"
    return {
        "action_class": action_class,
        "family_score_proxy": round_or_none(family_score),
        "family_score_class": score_class,
        "base_mechanical_triage_score_proxy": triage_info.get("mechanical_triage_score_proxy"),
    }


def source_manifest_rows(paths: list[Path]) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rel = path.relative_to(REPO).as_posix()
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-NEXT-SCORE-SRC-{index:04d}",
                "path": rel,
                "sha256": sha256_file(path) if path.exists() else None,
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Next-Compute Scoring Packet",
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
    lines.extend(["", "## Score Distributions", ""])
    for category in [
        "next_computation_class",
        "score_direction_class",
        "source_risk_score_class",
        "m15_interval_score_class",
        "m1_conflict_score_class",
        "positive_replay_score_class",
        "entry_adverse_score_class",
    ]:
        lines.append(f"### {category}")
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    lines.extend(
        [
            "## Continuation",
            "",
            "This packet is the next execution/scoring layer, not completion. It routes every branch to concrete same-resource score vectors that can be consumed by source-stress routers, M15/M1 interval splitters, positive challenger replay scoring, and entry/adverse redesign scoring.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {
        "schema": "weekend_mechanical_edge_factory_output_manifest_v1",
        "artifacts": [],
    }
    output_paths = [
        RESULT_PATH,
        BRANCH_SCORE_LEDGER,
        ACTION_SCORE_LEDGER,
        SOURCE_RISK_LEDGER,
        M15_SCORE_LEDGER,
        M1_CONFLICT_LEDGER,
        POSITIVE_SCORE_LEDGER,
        ENTRY_ADVERSE_LEDGER,
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
                "type": "branch_next_compute_scoring_packet",
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
    row = {
        "timestamp_utc": generated_at,
        "event_type": "branch_next_compute_scoring_packet_built",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    full_result = read_json(FULL_RESULT)
    full_rows = read_jsonl(FULL_BRANCH)
    full_actions = read_jsonl(FULL_ACTION)
    full_next = read_jsonl(FULL_NEXT)
    source_rows_in = read_jsonl(SOURCE_STRESS_BRANCH)
    source_support_rows = read_jsonl(SOURCE_STRESS_SUPPORT)
    m15_rows_in = read_jsonl(M15_BRANCH)
    m15_proxy_rows = read_jsonl(M15_PROXY)
    m1_rows_in = read_jsonl(M1_BRANCH)
    m1_proxy_rows = read_jsonl(M1_PROXY)
    positive_rows_in = read_jsonl(POSITIVE_REPLAY)
    entry_rows_in = read_jsonl(ENTRY_REDESIGN)
    adverse_rows_in = read_jsonl(ADVERSE_REDESIGN)

    full_by_id = by_branch(full_rows)
    next_by_id = by_branch(full_next)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m15_proxy_by_id = group_by_branch(m15_proxy_rows)
    m1_by_id = by_branch(m1_rows_in)
    m1_proxy_by_id = group_by_branch(m1_proxy_rows)
    positive_by_id = by_branch(positive_rows_in)
    entry_by_id = by_branch(entry_rows_in)
    adverse_by_id = by_branch(adverse_rows_in)
    source_support_by_id = group_by_branch(source_support_rows)
    actions_by_id = group_by_branch(full_actions)

    source_manifest, source_manifest_hash = source_manifest_rows(
        [
            FULL_RESULT,
            FULL_BRANCH,
            FULL_ACTION,
            FULL_NEXT,
            SOURCE_STRESS_BRANCH,
            SOURCE_STRESS_SUPPORT,
            M15_BRANCH,
            M15_PROXY,
            M1_BRANCH,
            M1_PROXY,
            POSITIVE_REPLAY,
            ENTRY_REDESIGN,
            ADVERSE_REDESIGN,
            Path(__file__).resolve(),
        ]
    )

    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)
    branch_score_rows: list[dict[str, Any]] = []
    action_score_rows: list[dict[str, Any]] = []
    source_risk_rows: list[dict[str, Any]] = []
    m15_score_rows: list[dict[str, Any]] = []
    m1_conflict_rows: list[dict[str, Any]] = []
    positive_score_rows: list[dict[str, Any]] = []
    entry_adverse_rows: list[dict[str, Any]] = []

    for index, branch_id in enumerate(sorted(full_by_id, key=branch_sort_key), 1):
        branch = full_by_id[branch_id]
        source = source_by_id.get(branch_id)
        m15 = m15_by_id.get(branch_id)
        m1 = m1_by_id.get(branch_id)
        positive = positive_by_id.get(branch_id)
        entry = entry_by_id.get(branch_id, {})
        adverse = adverse_by_id.get(branch_id, {})
        next_row = next_by_id.get(branch_id, {})
        triage_info = triage(branch)
        max_share = concentration_max_share(branch)

        branch_score_class = triage_info["score_direction_class"]
        if branch.get("next_computation_class") == "SOURCE_STRESS_RISK_ROUTER_OR_ACQUISITION_NEXT":
            branch_score_class = "SOURCE_STRESS_ROUTER_SCORE_REQUIRED"
        elif branch.get("next_computation_class", "").startswith("M15_INTERVAL"):
            branch_score_class = "M15_INTERVAL_SCORE_REQUIRED"
        elif branch.get("next_computation_class", "").startswith("M1_FILL_BAR"):
            branch_score_class = "M1_SUPPORT_CONFLICT_OR_TARGET_SCORE_REQUIRED"
        elif branch.get("next_computation_class") == "POSITIVE_CHALLENGER_REPLAY_SCORE_NEXT":
            branch_score_class = "POSITIVE_CHALLENGER_REPLAY_SCORE_REQUIRED"
        elif branch.get("next_computation_class") in {
            "ENTRY_GEOMETRY_REDESIGN_SCORE_NEXT",
            "ADVERSE_STOP_FIRST_AVOID_REDESIGN_SCORE_NEXT",
        }:
            branch_score_class = "ENTRY_ADVERSE_REDESIGN_SCORE_REQUIRED"

        branch_score_row = {
            "next_compute_score_id": f"OHLC-GTOS-NEXT-SCORE-BRANCH-{index:05d}",
            "branch_queue_id": branch_id,
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "next_computation_class": branch.get("next_computation_class"),
            "branch_priority": branch.get("branch_priority") or next_row.get("branch_priority"),
            "branch_result_class": branch.get("branch_result_class"),
            "sealed_or_proxy_outcome_status": branch.get("sealed_or_proxy_outcome_status"),
            "target_stop_result": branch.get("target_stop_result"),
            "target_stop_reward_to_risk_ratio": branch.get("target_stop_reward_to_risk_ratio"),
            "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
            "expectancy_style_proxy_method": branch.get("expectancy_style_proxy_method"),
            "pass_control_delta_status": branch.get("pass_control_delta_status"),
            "same_route_peer_delta": (branch.get("pass_control_delta") or {}).get("same_route_peer_delta"),
            "cost_sensitivity_proxy_status": branch.get("cost_sensitivity_proxy_status"),
            "source_execution_class": branch.get("source_execution_class"),
            "ordering_execution_class": branch.get("ordering_execution_class"),
            "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
            "concentration_max_branch_share": round_or_none(max_share, 9),
            "source_confidence_status": branch.get("source_confidence_status"),
            "ambiguity_status": branch.get("ambiguity_status"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "mechanical_score_vector": triage_info,
            "branch_next_score_class": branch_score_class,
            "source_layer_presence": branch.get("source_layer_presence"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": source_manifest_hash,
        }
        branch_score_rows.append(branch_score_row)

        for action_index, action in enumerate(actions_by_id.get(branch_id, []), 1):
            family = str(action.get("action_family"))
            action_score = family_action_score(family, branch, action)
            action_score_rows.append(
                {
                    "next_compute_action_score_id": f"OHLC-GTOS-NEXT-SCORE-ACTION-{index:05d}-{action_index:02d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "action_family": family,
                    "next_computation_class": branch.get("next_computation_class"),
                    **action_score,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": source_manifest_hash,
                }
            )

        if source:
            lower = fnum(source.get("rstyle_lower_mean"))
            midpoint = fnum(source.get("rstyle_midpoint_mean"))
            upper = fnum(source.get("rstyle_upper_mean"))
            width = (upper - lower) if upper is not None and lower is not None else None
            support = source_support_by_id.get(branch_id, [])
            source_score_class = "SOURCE_STRESS_FLIP_CONSERVATIVE_NEGATIVE_OR_STRADDLE"
            if lower is not None and lower > 0:
                source_score_class = "SOURCE_STRESS_FLIP_BUT_CONSERVATIVE_POSITIVE"
            elif upper is not None and upper < 0:
                source_score_class = "SOURCE_STRESS_FLIP_CONSERVATIVE_NEGATIVE"
            source_risk_rows.append(
                {
                    "source_risk_router_score_id": f"OHLC-GTOS-NEXT-SCORE-SOURCE-{len(source_risk_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "source_risk_score_class": source_score_class,
                    "branch_stress_class": source.get("branch_stress_class"),
                    "descriptor_split_counts": source.get("descriptor_split_counts"),
                    "source_support_rows": len(support),
                    "source_support_descriptor_classes": compact_counter(Counter(row.get("descriptor_split_class") for row in support)),
                    "stress_lower_mean": lower,
                    "stress_midpoint_mean": midpoint,
                    "stress_upper_mean": upper,
                    "stress_interval_width": round_or_none(width),
                    "risk_router_implication": "DO_NOT_SCALAR_COLLAPSE_LOW_HIGH_SPREAD_FLIP__ROUTE_BY_SOURCE_OR_COST",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": source_manifest_hash,
                }
            )

        if m15:
            lower = fnum(m15.get("interval_rstyle_lower_mean"))
            midpoint = fnum(m15.get("interval_rstyle_midpoint_mean"))
            upper = fnum(m15.get("interval_rstyle_upper_mean"))
            width = (upper - lower) if upper is not None and lower is not None else None
            m15_class = {
                "INTERVAL_ALL_POSITIVE": "M15_TARGET_FIRST_CHALLENGER_SCORE",
                "INTERVAL_ALL_NEGATIVE": "M15_STOP_FIRST_AVOID_SCORE",
                "INTERVAL_STRADDLES_ZERO": "M15_BOUNDS_ROUTER_SCORE",
            }.get(str(m15.get("interval_sign_class")), "M15_INTERVAL_SCORE_UNKNOWN")
            m15_score_rows.append(
                {
                    "m15_interval_score_id": f"OHLC-GTOS-NEXT-SCORE-M15-{len(m15_score_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "m15_interval_score_class": m15_class,
                    "interval_sign_class": m15.get("interval_sign_class"),
                    "interval_lower_mean": lower,
                    "interval_midpoint_mean": midpoint,
                    "interval_upper_mean": upper,
                    "interval_width": round_or_none(width),
                    "proxy_variant_count": len(m15_proxy_by_id.get(branch_id, [])),
                    "proxy_variant_values": {
                        row.get("proxy_variant"): row.get("proxy_rstyle_value")
                        for row in m15_proxy_by_id.get(branch_id, [])
                    },
                    "exact_chronology_claim": False,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": source_manifest_hash,
                }
            )

        if m1:
            branch_mid = fnum(m1.get("interval_rstyle_midpoint_mean"))
            support_mid = fnum(m1.get("support_component_midpoint_mean"))
            conflict_delta = (support_mid - branch_mid) if support_mid is not None and branch_mid is not None else None
            if m1.get("m1_support_interval_sign_class") == "INTERVAL_ALL_POSITIVE" and m1.get("branch_aggregate_interval_sign_class") != "INTERVAL_ALL_POSITIVE":
                conflict_class = "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT"
            elif m1.get("branch_aggregate_interval_sign_class") == "INTERVAL_ALL_POSITIVE":
                conflict_class = "M1_SUPPORT_AND_BRANCH_TARGET_STABLE"
            else:
                conflict_class = "M1_SUPPORT_BRANCH_RELATION_OTHER"
            m1_conflict_rows.append(
                {
                    "m1_conflict_score_id": f"OHLC-GTOS-NEXT-SCORE-M1-{len(m1_conflict_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "m1_conflict_score_class": conflict_class,
                    "branch_aggregate_interval_sign_class": m1.get("branch_aggregate_interval_sign_class"),
                    "m1_support_interval_sign_class": m1.get("m1_support_interval_sign_class"),
                    "m1_support_resolution_class": m1.get("m1_support_resolution_class"),
                    "branch_midpoint_mean": branch_mid,
                    "m1_support_midpoint_mean": support_mid,
                    "m1_support_minus_branch_midpoint": round_or_none(conflict_delta),
                    "proxy_variant_count": len(m1_proxy_by_id.get(branch_id, [])),
                    "fill_bar_order_unresolved_rows": m1.get("fill_bar_order_unresolved_rows"),
                    "support_conservative_source_fail_rows": m1.get("support_conservative_source_fail_rows"),
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": source_manifest_hash,
                }
            )

        if positive:
            lower = fnum(positive.get("rstyle_lower_mean"))
            midpoint = fnum(positive.get("rstyle_midpoint_mean"))
            upper = fnum(positive.get("rstyle_upper_mean"))
            replayable = positive.get("positive_replayable_now") is True
            if replayable and lower is not None and lower > 0:
                positive_class = "POSITIVE_REPLAYABLE_CONSERVATIVE_POSITIVE_PROXY"
            elif replayable and midpoint is not None and midpoint > 0:
                positive_class = "POSITIVE_REPLAYABLE_MIDPOINT_POSITIVE_PROXY"
            elif replayable:
                positive_class = "POSITIVE_REPLAYABLE_WEAK_OR_MIXED_PROXY"
            else:
                positive_class = "POSITIVE_STRESS_OR_SOURCE_REPAIR_FIRST"
            positive_score_rows.append(
                {
                    "positive_replay_score_id": f"OHLC-GTOS-NEXT-SCORE-POSITIVE-{len(positive_score_rows) + 1:05d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "positive_replay_score_class": positive_class,
                    "positive_challenger_class": positive.get("positive_challenger_class"),
                    "positive_replay_status": positive.get("positive_replay_status"),
                    "positive_replayable_now": replayable,
                    "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class"),
                    "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class"),
                    "positive_lower_mean": lower,
                    "positive_midpoint_mean": midpoint,
                    "positive_upper_mean": upper,
                    "same_route_peer_delta": positive.get("same_route_peer_delta"),
                    "surface_file_status": positive.get("surface_file_status"),
                    "proposed_branch_local_code_surface": positive.get("proposed_branch_local_code_surface"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": source_manifest_hash,
                }
            )

        entry_class = entry.get("entry_geometry_retest_class") or "ENTRY_NO_CONTEXT"
        adverse_class = adverse.get("adverse_stop_first_class") or "ADVERSE_NO_CONTEXT"
        if str(adverse_class).startswith("STOP_FIRST") and str(entry_class).startswith(("FAR_", "WITHIN_", "NEAR_", "MIXED_")):
            entry_adverse_class = "ENTRY_AND_ADVERSE_REDESIGN_BOTH_ACTIVE"
        elif str(adverse_class).startswith("STOP_FIRST"):
            entry_adverse_class = "ADVERSE_REDESIGN_ACTIVE"
        elif str(entry_class).startswith(("FAR_", "WITHIN_", "NEAR_", "MIXED_")):
            entry_adverse_class = "ENTRY_REDESIGN_ACTIVE"
        else:
            entry_adverse_class = "ENTRY_ADVERSE_NO_REDESIGN_SCORE_SCOPE"
        entry_adverse_rows.append(
            {
                "entry_adverse_score_id": f"OHLC-GTOS-NEXT-SCORE-ENTRY-ADVERSE-{index:05d}",
                "branch_queue_id": branch_id,
                "route_candidate_id": branch.get("route_candidate_id"),
                "symbol": branch.get("symbol"),
                "route_session": branch.get("route_session"),
                "side": branch.get("side"),
                "entry_variant": branch.get("entry_variant"),
                "target_stop_contract_id": branch.get("target_stop_contract_id"),
                "entry_adverse_score_class": entry_adverse_class,
                "entry_geometry_retest_class": entry_class,
                "entry_redesign_action_class": entry.get("entry_redesign_action_class"),
                "adverse_stop_first_class": adverse_class,
                "adverse_redesign_action_class": adverse.get("adverse_redesign_action_class"),
                "no_fill_or_unfilled_rows": entry.get("no_fill_or_unfilled_rows"),
                "target_first_rows": entry.get("target_first_rows"),
                "stop_first_rows": entry.get("stop_first_rows"),
                "same_route_peer_delta": entry.get("same_route_peer_delta"),
                "rstyle_midpoint_mean": entry.get("rstyle_midpoint_mean"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": source_manifest_hash,
            }
        )

        for category, value in [
            ("next_computation_class", branch.get("next_computation_class")),
            ("branch_priority", branch_score_row.get("branch_priority")),
            ("branch_result_class", branch.get("branch_result_class")),
            ("target_stop_result", branch.get("target_stop_result")),
            ("score_direction_class", triage_info.get("score_direction_class")),
            ("branch_next_score_class", branch_score_class),
            ("source_execution_class", branch.get("source_execution_class")),
            ("ordering_execution_class", branch.get("ordering_execution_class")),
            ("effective_n_concentration_class", branch.get("effective_n_concentration_class")),
            ("source_confidence_status", branch.get("source_confidence_status")),
            ("ambiguity_status", branch.get("ambiguity_status")),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in action_score_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_score_class"][row.get("family_score_class")] += 1
    for row in source_risk_rows:
        bucket_counters["source_risk_score_class"][row.get("source_risk_score_class")] += 1
    for row in m15_score_rows:
        bucket_counters["m15_interval_score_class"][row.get("m15_interval_score_class")] += 1
    for row in m1_conflict_rows:
        bucket_counters["m1_conflict_score_class"][row.get("m1_conflict_score_class")] += 1
    for row in positive_score_rows:
        bucket_counters["positive_replay_score_class"][row.get("positive_replay_score_class")] += 1
    for row in entry_adverse_rows:
        bucket_counters["entry_adverse_score_class"][row.get("entry_adverse_score_class")] += 1

    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-NEXT-SCORE-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": source_manifest_hash,
                }
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-NEXT-SCORE-QUESTION-001",
            "question": "Which source-stress branches should become risk-router/acquisition rows before scalar comparison?",
            "answer_route": "Use the source risk router ledger and preserve low/high spread flip classes.",
        },
        {
            "question_id": "OHLC-GTOS-NEXT-SCORE-QUESTION-002",
            "question": "Which M15 interval branches are target-first challengers, stop-first avoids, or bounds routers?",
            "answer_route": "Use the M15 interval score ledger; exact chronology remains false.",
        },
        {
            "question_id": "OHLC-GTOS-NEXT-SCORE-QUESTION-003",
            "question": "Where does M1 support contradict the branch aggregate and require split scoring?",
            "answer_route": "Use the M1 conflict ledger and m1_support_minus_branch_midpoint.",
        },
        {
            "question_id": "OHLC-GTOS-NEXT-SCORE-QUESTION-004",
            "question": "Which positive challenger branches are replayable now versus source-stress first?",
            "answer_route": "Use the positive replay score ledger and modifier classes.",
        },
        {
            "question_id": "OHLC-GTOS-NEXT-SCORE-QUESTION-005",
            "question": "Which entry/adverse branches require redesign scoring rather than passive notes?",
            "answer_route": "Use the entry/adverse score ledger for all 386 branches.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "not_completion": True,
                "source_manifest_hash": source_manifest_hash,
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "triage_formula": TRIAGE_FORMULA,
        "counts": {
            "input_full_branch_rows": len(full_rows),
            "input_full_action_rows": len(full_actions),
            "input_full_next_rows": len(full_next),
            "input_source_stress_branch_rows": len(source_rows_in),
            "input_source_stress_support_rows": len(source_support_rows),
            "input_m15_branch_rows": len(m15_rows_in),
            "input_m15_proxy_rows": len(m15_proxy_rows),
            "input_m1_branch_rows": len(m1_rows_in),
            "input_m1_proxy_rows": len(m1_proxy_rows),
            "input_positive_replay_rows": len(positive_rows_in),
            "input_entry_branch_rows": len(entry_rows_in),
            "input_adverse_branch_rows": len(adverse_rows_in),
            "branch_score_rows": len(branch_score_rows),
            "action_family_score_rows": len(action_score_rows),
            "source_risk_router_rows": len(source_risk_rows),
            "m15_interval_score_rows": len(m15_score_rows),
            "m1_conflict_score_rows": len(m1_conflict_rows),
            "positive_replay_score_rows": len(positive_score_rows),
            "entry_adverse_score_rows": len(entry_adverse_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_full_synthesis_counts": full_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_score_denominator_preserved": len(branch_score_rows) == 386,
            "action_family_count_per_branch": 5,
            "source_risk_router_scope": len(source_risk_rows),
            "m15_interval_score_scope": len(m15_score_rows),
            "m1_conflict_score_scope": len(m1_conflict_rows),
            "positive_replay_score_scope": len(positive_score_rows),
            "entry_adverse_score_scope": len(entry_adverse_rows),
        },
        "source_manifest_hash": source_manifest_hash,
    }

    for path, rows in [
        (BRANCH_SCORE_LEDGER, branch_score_rows),
        (ACTION_SCORE_LEDGER, action_score_rows),
        (SOURCE_RISK_LEDGER, source_risk_rows),
        (M15_SCORE_LEDGER, m15_score_rows),
        (M1_CONFLICT_LEDGER, m1_conflict_rows),
        (POSITIVE_SCORE_LEDGER, positive_score_rows),
        (ENTRY_ADVERSE_LEDGER, entry_adverse_rows),
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
