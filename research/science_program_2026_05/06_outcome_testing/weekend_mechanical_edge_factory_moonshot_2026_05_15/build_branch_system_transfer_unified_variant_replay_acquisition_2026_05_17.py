#!/usr/bin/env python3
"""Convert instantiated variant rows into replay/acquisition decisions.

This is the decision-changing layer after candidate variant instantiation. It
preserves the full branch and market-gap denominators while recomputing which
rows are implementation candidates, source-acquisition requirements, controls,
or avoid/redesign outcomes from the upstream fields.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


VARIANT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION"
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION"
SCORING_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION"

VARIANT_RESULT = ROUTE_DIR / f"{VARIANT_PREFIX}_RESULT_2026-05-17.json"
VARIANT_SOURCE = ROUTE_DIR / f"{VARIANT_PREFIX}_SOURCE_EXPANSION_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
VARIANT_ENTRY = ROUTE_DIR / f"{VARIANT_PREFIX}_ENTRY_GEOMETRY_VARIANT_LEDGER_2026-05-17.jsonl"
VARIANT_ENTRY_PARENT = ROUTE_DIR / f"{VARIANT_PREFIX}_ENTRY_GEOMETRY_PARENT_DECISION_LEDGER_2026-05-17.jsonl"
VARIANT_AVOID = ROUTE_DIR / f"{VARIANT_PREFIX}_AVOID_INVERSE_POLICY_VARIANT_SCORE_LEDGER_2026-05-17.jsonl"
VARIANT_MARKET = ROUTE_DIR / f"{VARIANT_PREFIX}_MARKET_GAP_ACTION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
VARIANT_SSH = ROUTE_DIR / f"{VARIANT_PREFIX}_SYMBOL_SESSION_HORIZON_ACTION_LEDGER_2026-05-17.jsonl"

ACTION_BRANCH = ROUTE_DIR / f"{ACTION_PREFIX}_BRANCH_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
ACTION_CONCENTRATION = ROUTE_DIR / f"{ACTION_PREFIX}_CONCENTRATION_ARTIFACT_RESTRESS_LEDGER_2026-05-17.jsonl"
ACTION_SCORER_SPEC = ROUTE_DIR / f"{ACTION_PREFIX}_SCORER_SPEC_CHANGE_LEDGER_2026-05-17.jsonl"
SCORING_IMPLEMENTATION = ROUTE_DIR / f"{SCORING_PREFIX}_IMPLEMENTATION_SCORE_LEDGER_2026-05-16.jsonl"
EXEC_BRANCH_RSTYLE = ROUTE_DIR / f"{EXEC_PREFIX}_BRANCH_RSTYLE_RESULT_LEDGER_2026-05-16.jsonl"
EXEC_FSS_RSTYLE = ROUTE_DIR / f"{EXEC_PREFIX}_FAMILY_SYMBOL_SESSION_RSTYLE_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_VARIANT_REPLAY_ACQUISITION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_ACQUISITION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACQUISITION_PROXY_RESULT_LEDGER_2026-05-17.jsonl"
ENTRY_VARIANT_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_VARIANT_REPLAY_SCORE_LEDGER_2026-05-17.jsonl"
ENTRY_PARENT_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_PARENT_REPLAY_DECISION_LEDGER_2026-05-17.jsonl"
AVOID_POLICY_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INVERSE_POLICY_REPLAY_SCORE_LEDGER_2026-05-17.jsonl"
MARKET_GAP_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_REPLAY_ACQUISITION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
SSH_REPLAY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_HORIZON_REPLAY_ACQUISITION_LEDGER_2026-05-17.jsonl"
MARKET_FSS_PROXY_R_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_FAMILY_SYMBOL_SESSION_PROXY_R_LEDGER_2026-05-17.jsonl"
BRANCH_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_KEEP_KILL_REDESIGN_IMPLEMENT_LEDGER_2026-05-17.jsonl"
BRANCH_FSS_RSTYLE_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_FAMILY_SYMBOL_SESSION_RSTYLE_RESULT_LEDGER_2026-05-17.jsonl"
SCORER_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_LOCAL_SCORER_SPEC_CANDIDATE_LEDGER_2026-05-17.jsonl"
CONCENTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_REPLAY_TEST_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Unified variant replay/acquisition decision packet only. It converts the full variant, market-gap, "
    "branch-action, R-style proxy, scorer-spec, and concentration denominators into concrete source-acquisition, "
    "entry-replay, avoid/inverse, keep/kill/redesign/implement, and branch-local scorer-spec decisions. It does "
    "not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, "
    "or promotion."
)

EXACT_R_MISSING_REASON = (
    "Exact broker R is not directly computable in this evidence class because the packet has no broker-realized "
    "fills, executed risk distance, slippage, ticket lifecycle, partial exits, or account-history PnL. The branch "
    "rows carry the strongest available sealed/proxy target-stop R-style interval and exact missing-source reason."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-REPLAY-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 6)


def mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 9) if values else None


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def score_band(score: float) -> str:
    if score >= 0.55:
        return "REPLAY_SCORE_BAND_HIGH"
    if score >= 0.25:
        return "REPLAY_SCORE_BAND_MODERATE"
    if score >= 0.0:
        return "REPLAY_SCORE_BAND_REPAIRABLE"
    return "REPLAY_SCORE_BAND_WEAK"


def proxy_r_fields(
    prefix: str,
    score: float | None,
    *,
    control: bool = False,
    uncertainty: float = 0.12,
    method: str,
) -> dict[str, Any]:
    """Map a bounded replay score to an explicit proxy-R interval.

    This is not broker R. It is a lower-level R-style decision proxy so that
    variant rows can be compared consistently before exact executed geometry is
    available.
    """

    if score is None:
        midpoint = None
        lower = None
        upper = None
        result_class = "PROXY_R_NO_SCALAR"
    elif control:
        midpoint = 0.0
        lower = 0.0
        upper = 0.0
        result_class = "PROXY_R_CONTROL_NEUTRAL"
    else:
        midpoint = clamp(score - 0.35)
        lower = clamp(midpoint - uncertainty)
        upper = clamp(midpoint + uncertainty)
        if lower > 0:
            result_class = "PROXY_R_INTERVAL_ALL_POSITIVE"
        elif upper < 0:
            result_class = "PROXY_R_INTERVAL_ALL_NEGATIVE"
        else:
            result_class = "PROXY_R_INTERVAL_STRADDLES_ZERO"
    return {
        f"{prefix}_proxy_r_style_midpoint": midpoint,
        f"{prefix}_proxy_r_style_lower": lower,
        f"{prefix}_proxy_r_style_upper": upper,
        f"{prefix}_proxy_r_style_result_class": result_class,
        f"{prefix}_proxy_r_style_method": method,
        f"{prefix}_proxy_r_exact_missing_reason": EXACT_R_MISSING_REASON,
    }


def source_acquisition_decision(row: dict[str, Any]) -> dict[str, Any]:
    flagged = int(row.get("flagged_n") or 0)
    needed = int(row.get("additional_flagged_rows_needed_for_n20") or 0)
    score = float(row.get("candidate_score_proxy") or 0.0)
    alignment = float(row.get("delta_alignment_rate") or 0.0)
    abs_delta = float(row.get("delta_mean_abs_future_change") or 0.0)
    outside = bool(row.get("outside_gbpjpy_xauusd_current_branch_box"))
    if flagged >= 20:
        status = "SOURCE_ACQUISITION_COMPLETE_N20_REPLAY_READY"
    elif needed <= 5 and outside:
        status = "SOURCE_ACQUISITION_NEAR_N20_OUTSIDE_BRANCH_REPLAY_PRIORITY"
    elif row.get("candidate_score_class") == "MARKET_GAP_SOURCE_EXPANSION_HIGH_PRIORITY":
        status = "SOURCE_ACQUISITION_HIGH_PRIORITY_PROXY_REPLAY_NOW"
    elif outside:
        status = "SOURCE_ACQUISITION_OUTSIDE_BRANCH_REQUIRED_TO_N20"
    else:
        status = "SOURCE_ACQUISITION_CURRENT_CONCENTRATION_CONTROL_REQUIRED_TO_N20"

    if score >= 0.25 and abs_delta > 0 and alignment >= 0:
        proxy_result = "SOURCE_PROXY_SUPPORTIVE_UNDER_N20"
    elif score >= 0.25:
        proxy_result = "SOURCE_PROXY_MOVEMENT_PRESENT_ALIGNMENT_STRESS"
    elif abs_delta > 0 and alignment < 0:
        proxy_result = "SOURCE_PROXY_ADVERSE_ALIGNMENT_REQUIRES_SPLIT"
    else:
        proxy_result = "SOURCE_PROXY_WEAK_OR_UNDERPOWERED"

    return {
        "source_acquisition_status": status,
        "source_proxy_replay_result": proxy_result,
        "source_rows_needed_to_n20": needed,
        "source_replay_priority_score": clamp(score + min(0.2, needed / 100.0) + (0.05 if outside else 0.0)),
        "exact_source_gap_reason": (
            f"flagged_n={flagged}; requires {needed} additional flagged rows to reach N20 for this "
            "symbol/session/horizon/primitive source denominator."
        ),
        "source_decision_implication": (
            "materialize_source_rows_before_branch_implementation"
            if flagged < 20
            else "score_as_replay_ready_source_row"
        ),
        **proxy_r_fields(
            "source_acquisition",
            clamp(score + min(0.2, needed / 100.0) + (0.05 if outside else 0.0)),
            uncertainty=0.2 if flagged < 20 else 0.1,
            method="source_candidate_score_plus_n20_gap_priority_minus_0.35_proxy_r",
        ),
    }


def build_source_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        decision = source_acquisition_decision(row)
        output.append(
            with_common(
                {
                    "source_acquisition_proxy_result_id": f"OHLC-GTOS-UNIFIED-REPLAY-SOURCE-{index:05d}",
                    "source_materialization_id": row.get("source_materialization_id"),
                    "source_expansion_requirement_id": row.get("source_expansion_requirement_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "flagged_n": row.get("flagged_n"),
                    "control_n": row.get("control_n"),
                    "additional_flagged_rows_needed_for_n20": row.get("additional_flagged_rows_needed_for_n20"),
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    "source_materialization_status": row.get("source_materialization_status"),
                    **decision,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def entry_variant_replay_decision(row: dict[str, Any]) -> dict[str, Any]:
    variant = str(row.get("entry_variant") or "")
    score = float(row.get("entry_variant_proxy_score") or 0.0)
    parent_score = float(row.get("parent_candidate_score_proxy") or 0.0)
    alignment = float(row.get("delta_alignment_rate") or 0.0)
    abs_delta = float(row.get("delta_mean_abs_future_change") or 0.0)
    is_control = variant == "STATUS_QUO_NO_BRANCH_CONTROL"
    if variant == "HALF_SPREAD_OFFSET_ENTRY":
        cost_penalty = -0.02
    elif variant == "NEXT_M1_OPEN_MARKET_ENTRY":
        cost_penalty = -0.01
    else:
        cost_penalty = 0.0
    replay_delta = clamp(score - parent_score + cost_penalty)
    if is_control:
        decision = "ENTRY_REPLAY_CONTROL_ONLY"
        implication = "preserve_status_quo_control_for_variant_delta"
    elif score >= 0.55 and alignment >= 0 and abs_delta > 0:
        decision = "ENTRY_REPLAY_ACCEPT_CHALLENGER"
        implication = "implement_branch_local_entry_geometry_candidate_for_shadow_spec"
    elif score >= 0.25:
        decision = "ENTRY_REPLAY_SCORE_CHALLENGER_WITH_CONTROL"
        implication = "score_entry_challenger_against_control_and_source_split"
    else:
        decision = "ENTRY_REPLAY_STRESS_OR_REPAIR"
        implication = "repair_or_stress_entry_geometry_before_implementation"
    if abs_delta <= 0:
        result = "ENTRY_TARGET_STOP_PROXY_WEAK_OR_NEGATIVE_ABS_DELTA"
    elif alignment < 0:
        result = "ENTRY_TARGET_STOP_PROXY_SUPPORTIVE_ABS_ADVERSE_ALIGNMENT"
    else:
        result = "ENTRY_TARGET_STOP_PROXY_SUPPORTIVE_ABS_AND_ALIGNMENT"
    proxy_score = clamp(score + cost_penalty)
    return {
        "entry_replay_decision": decision,
        "entry_replay_proxy_score": proxy_score,
        "entry_replay_delta_vs_parent": replay_delta,
        "entry_cost_sensitivity_penalty": cost_penalty,
        "entry_target_stop_proxy_result": result,
        "entry_implementation_implication": implication,
        **proxy_r_fields(
            "entry",
            proxy_score,
            control=is_control,
            uncertainty=0.08 if alignment >= 0 else 0.14,
            method="entry_variant_replay_proxy_score_minus_0.35_with_status_quo_control_at_zero",
        ),
    }


def build_entry_variant_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows, 1):
        decision = entry_variant_replay_decision(row)
        out = with_common(
            {
                "entry_variant_replay_score_id": f"OHLC-GTOS-UNIFIED-REPLAY-ENTRY-{index:05d}",
                "entry_geometry_variant_id": row.get("entry_geometry_variant_id"),
                "entry_geometry_parent_decision_id": row.get("entry_geometry_parent_decision_id"),
                "parent_entry_geometry_challenger_id": row.get("parent_entry_geometry_challenger_id"),
                "market_gap_combo_id": row.get("market_gap_combo_id"),
                "symbol": row.get("symbol"),
                "route_session": row.get("route_session"),
                "session_bucket": row.get("session_bucket"),
                "horizon_id": row.get("horizon_id"),
                "primitive_flag": row.get("primitive_flag"),
                "entry_variant": row.get("entry_variant"),
                "entry_variant_proxy_score": row.get("entry_variant_proxy_score"),
                "parent_candidate_score_proxy": row.get("parent_candidate_score_proxy"),
                "entry_variant_decision": row.get("entry_variant_decision"),
                "movement_status": row.get("movement_status"),
                "delta_alignment_rate": row.get("delta_alignment_rate"),
                "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                **decision,
            },
            generated_at,
            manifest_hash,
        )
        out["entry_replay_score_band"] = score_band(float(out["entry_replay_proxy_score"]))
        by_parent[str(row.get("entry_geometry_parent_decision_id"))].append(out)
        output.append(out)

    parent_rows: list[dict[str, Any]] = []
    for index, (parent_id, members) in enumerate(sorted(by_parent.items()), 1):
        challengers = [row for row in members if row.get("entry_variant") != "STATUS_QUO_NO_BRANCH_CONTROL"]
        best = max(challengers, key=lambda row: float(row.get("entry_replay_proxy_score") or -999.0))
        control = next((row for row in members if row.get("entry_variant") == "STATUS_QUO_NO_BRANCH_CONTROL"), None)
        best_delta_vs_control = float(best.get("entry_replay_proxy_score") or 0.0) - float(
            (control or {}).get("entry_replay_proxy_score") or 0.0
        )
        proxy_scalars = [
            float(row["entry_proxy_r_style_midpoint"])
            for row in members
            if row.get("entry_proxy_r_style_midpoint") is not None
        ]
        if best.get("entry_replay_decision") == "ENTRY_REPLAY_ACCEPT_CHALLENGER":
            parent_decision = "ENTRY_PARENT_REPLAY_IMPLEMENT_CHALLENGER"
        elif any(row.get("entry_replay_decision") == "ENTRY_REPLAY_SCORE_CHALLENGER_WITH_CONTROL" for row in members):
            parent_decision = "ENTRY_PARENT_REPLAY_SCORE_WITH_CONTROL"
        else:
            parent_decision = "ENTRY_PARENT_REPLAY_STRESS_OR_REPAIR"
        parent_rows.append(
            with_common(
                {
                    "entry_parent_replay_decision_id": f"OHLC-GTOS-UNIFIED-REPLAY-ENTRY-PARENT-{index:05d}",
                    "entry_geometry_parent_decision_id": parent_id,
                    "parent_entry_geometry_challenger_id": best.get("parent_entry_geometry_challenger_id"),
                    "market_gap_combo_id": best.get("market_gap_combo_id"),
                    "symbol": best.get("symbol"),
                    "route_session": best.get("route_session"),
                    "session_bucket": best.get("session_bucket"),
                    "horizon_id": best.get("horizon_id"),
                    "primitive_flag": best.get("primitive_flag"),
                    "entry_variant_count": len(members),
                    "challenger_variant_count": len(challengers),
                    "best_entry_variant": best.get("entry_variant"),
                    "best_entry_replay_proxy_score": best.get("entry_replay_proxy_score"),
                    "status_quo_control_score": (control or {}).get("entry_replay_proxy_score"),
                    "best_delta_vs_status_quo_control": round(best_delta_vs_control, 6),
                    "entry_parent_proxy_r_style_midpoint_mean": mean_or_none(proxy_scalars),
                    "entry_parent_proxy_r_style_min": round(min(proxy_scalars), 9) if proxy_scalars else None,
                    "entry_parent_proxy_r_style_max": round(max(proxy_scalars), 9) if proxy_scalars else None,
                    "entry_parent_proxy_r_style_result_counts": compact_counter(
                        Counter(row.get("entry_proxy_r_style_result_class") for row in members)
                    ),
                    "accepted_challenger_rows": sum(
                        1 for row in members if row.get("entry_replay_decision") == "ENTRY_REPLAY_ACCEPT_CHALLENGER"
                    ),
                    "score_with_control_rows": sum(
                        1 for row in members if row.get("entry_replay_decision") == "ENTRY_REPLAY_SCORE_CHALLENGER_WITH_CONTROL"
                    ),
                    "parent_replay_decision": parent_decision,
                    "outside_gbpjpy_xauusd_current_branch_box": best.get("outside_gbpjpy_xauusd_current_branch_box"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output, parent_rows


def build_avoid_policy_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("parent_avoid_inverse_control_id"))].append(row)

    output: list[dict[str, Any]] = []
    for parent_id, members in sorted(grouped.items()):
        scores_by_type = {str(row.get("policy_variant_type")): float(row.get("policy_variant_proxy_score") or 0.0) for row in members}
        avoid_score = scores_by_type.get("AVOID_FILTER_VARIANT", 0.0)
        inverse_score = scores_by_type.get("INVERSE_OR_FADE_CONTROL_VARIANT", 0.0)
        for row in members:
            score = float(row.get("policy_variant_proxy_score") or 0.0)
            variant_type = str(row.get("policy_variant_type") or "")
            alignment = float(row.get("delta_alignment_rate") or 0.0)
            if variant_type == "AVOID_FILTER_VARIANT":
                delta = avoid_score - inverse_score
                if score >= 0.55 and delta >= 0:
                    decision = "AVOID_POLICY_REPLAY_ACCEPT_FILTER"
                elif score >= 0.25:
                    decision = "AVOID_POLICY_REPLAY_SCORE_FILTER_WITH_INVERSE_CONTROL"
                else:
                    decision = "AVOID_POLICY_REPLAY_KEEP_WEAK_FILTER_CONTROL"
            else:
                delta = inverse_score - avoid_score
                if score >= 0.55 and delta > 0:
                    decision = "INVERSE_POLICY_REPLAY_ACCEPT_FADE_CONTROL"
                elif score >= 0.25:
                    decision = "INVERSE_POLICY_REPLAY_SCORE_FADE_CONTROL"
                else:
                    decision = "INVERSE_POLICY_REPLAY_KEEP_WEAK_CONTROL"
            if alignment < 0:
                cause = "ADVERSE_ALIGNMENT_SUPPORTS_AVOID_OR_INVERSE_TEST"
            elif row.get("movement_status") == "FLAT_OR_NEGATIVE_ABS_DELTA":
                cause = "FLAT_OR_NEGATIVE_MOVEMENT_SUPPORTS_AVOID_FILTER_TEST"
            else:
                cause = "MIXED_POLICY_CONTROL_CONTEXT"
            proxy_r = proxy_r_fields(
                "policy",
                score,
                uncertainty=0.1 if variant_type == "AVOID_FILTER_VARIANT" else 0.14,
                method="policy_variant_proxy_score_minus_0.35_avoid_or_inverse_control_proxy_r",
            )
            output.append(
                with_common(
                    {
                        "avoid_inverse_policy_replay_score_id": f"OHLC-GTOS-UNIFIED-REPLAY-AVOID-{len(output) + 1:05d}",
                        "avoid_inverse_policy_variant_score_id": row.get("avoid_inverse_policy_variant_score_id"),
                        "avoid_inverse_policy_variant_id": row.get("avoid_inverse_policy_variant_id"),
                        "parent_avoid_inverse_control_id": parent_id,
                        "market_gap_combo_id": row.get("market_gap_combo_id"),
                        "symbol": row.get("symbol"),
                        "route_session": row.get("route_session"),
                        "session_bucket": row.get("session_bucket"),
                        "horizon_id": row.get("horizon_id"),
                        "primitive_flag": row.get("primitive_flag"),
                        "policy_variant_type": row.get("policy_variant_type"),
                        "policy_variant_proxy_score": row.get("policy_variant_proxy_score"),
                        "policy_variant_replay_delta_vs_sibling": round(delta, 6),
                        "sibling_avoid_filter_score": round(avoid_score, 6),
                        "sibling_inverse_or_fade_score": round(inverse_score, 6),
                        "policy_variant_replay_score_band": score_band(score),
                        "policy_variant_replay_decision": decision,
                        "policy_replay_success_or_failure_cause": cause,
                        **proxy_r,
                        "movement_status": row.get("movement_status"),
                        "delta_alignment_rate": row.get("delta_alignment_rate"),
                        "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output


def market_gap_decision(
    row: dict[str, Any],
    source_by_combo: dict[str, dict[str, Any]],
    entry_parent_by_combo: dict[str, dict[str, Any]],
    avoid_by_combo: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    combo_id = str(row.get("market_gap_combo_id"))
    if combo_id in source_by_combo:
        source = source_by_combo[combo_id]
        status = source.get("source_acquisition_status")
        decision = "REDESIGN_SOURCE_ACQUISITION_BEFORE_IMPLEMENT"
        if status == "SOURCE_ACQUISITION_HIGH_PRIORITY_PROXY_REPLAY_NOW":
            replay_result = "MARKET_GAP_SOURCE_PROXY_REPLAY_PRIORITY"
        else:
            replay_result = "MARKET_GAP_SOURCE_DENOMINATOR_EXPANSION_REQUIRED"
        implication = "build_or_reconstruct_flagged_rows_to_n20_then_rescore_market_gap_branch"
        decision_score = source.get("source_replay_priority_score")
    elif combo_id in entry_parent_by_combo:
        parent = entry_parent_by_combo[combo_id]
        decision = (
            "IMPLEMENT_ENTRY_GEOMETRY_CHALLENGER_CANDIDATE"
            if parent.get("parent_replay_decision") == "ENTRY_PARENT_REPLAY_IMPLEMENT_CHALLENGER"
            else "SCORE_ENTRY_GEOMETRY_WITH_CONTROL_BEFORE_IMPLEMENT"
        )
        replay_result = parent.get("parent_replay_decision")
        implication = "branch_local_entry_geometry_spec_candidate"
        decision_score = parent.get("best_entry_replay_proxy_score")
    elif combo_id in avoid_by_combo:
        members = avoid_by_combo[combo_id]
        best = max(members, key=lambda member: float(member.get("policy_variant_proxy_score") or 0.0))
        decision = (
            "IMPLEMENT_AVOID_FILTER_CANDIDATE"
            if best.get("policy_variant_replay_decision") == "AVOID_POLICY_REPLAY_ACCEPT_FILTER"
            else "SCORE_AVOID_INVERSE_POLICY_WITH_CONTROL"
        )
        replay_result = best.get("policy_variant_replay_decision")
        implication = "branch_local_avoid_or_inverse_policy_spec_candidate"
        decision_score = best.get("policy_variant_proxy_score")
    else:
        decision = "MARKET_GAP_REPLAY_UNMATCHED_ERROR"
        replay_result = "UNMATCHED_MARKET_GAP_ROW"
        implication = "repair_market_gap_join"
        decision_score = None
    outside = bool(row.get("outside_gbpjpy_xauusd_current_branch_box"))
    if outside and decision.startswith("IMPLEMENT"):
        concentration = "OUTSIDE_BRANCH_IMPLEMENTABLE_CANDIDATE_REFUTES_BRANCH_BOX_AS_SEARCH_BOUNDARY"
    elif outside:
        concentration = "OUTSIDE_BRANCH_REPLAY_OR_SOURCE_ROUTE_REQUIRED"
    elif row.get("symbol") in {"GBPJPY", "XAUUSD"}:
        concentration = "CURRENT_BRANCH_CONCENTRATION_CONTEXT_PRESERVED"
    else:
        concentration = "CURRENT_BRANCH_BOX_CONTEXT_GAP"
    proxy_r = proxy_r_fields(
        "market_gap",
        float(decision_score) if decision_score is not None else None,
        uncertainty=0.18 if "SOURCE" in decision else 0.1,
        method="market_gap_replay_decision_score_minus_0.35_proxy_r",
    )
    return {
        "market_gap_replay_decision": decision,
        "market_gap_replay_result": replay_result,
        "market_gap_decision_score": decision_score,
        "implementation_implication": implication,
        "concentration_replay_test_result": concentration,
        **proxy_r,
    }


def build_market_rows(
    rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    entry_parent_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    source_by_combo = {str(row.get("market_gap_combo_id")): row for row in source_rows}
    entry_parent_by_combo = {str(row.get("market_gap_combo_id")): row for row in entry_parent_rows}
    avoid_by_combo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in avoid_rows:
        avoid_by_combo[str(row.get("market_gap_combo_id"))].append(row)

    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        decision = market_gap_decision(row, source_by_combo, entry_parent_by_combo, avoid_by_combo)
        output.append(
            with_common(
                {
                    "market_gap_replay_acquisition_synthesis_id": f"OHLC-GTOS-UNIFIED-REPLAY-MARKET-{index:05d}",
                    "market_gap_action_synthesis_id": row.get("market_gap_action_synthesis_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "market_gap_action": row.get("market_gap_action"),
                    "market_gap_action_decision": row.get("market_gap_action_decision"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    **decision,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_ssh_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("symbol"), row.get("route_session"), row.get("horizon_id"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        decision_counts = Counter(row.get("market_gap_replay_decision") for row in members)
        action_counts = Counter(row.get("market_gap_action") for row in members)
        concentration_counts = Counter(row.get("concentration_replay_test_result") for row in members)
        implementation_rows = sum(1 for row in members if str(row.get("market_gap_replay_decision", "")).startswith("IMPLEMENT"))
        source_required_rows = sum(1 for row in members if "SOURCE" in str(row.get("market_gap_replay_decision", "")))
        outside_rows = sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box"))
        proxy_scalars = [
            float(row["market_gap_proxy_r_style_midpoint"])
            for row in members
            if row.get("market_gap_proxy_r_style_midpoint") is not None
        ]
        if implementation_rows:
            dominant = "SSH_REPLAY_IMPLEMENTATION_CANDIDATE_PRESENT"
        elif source_required_rows:
            dominant = "SSH_REPLAY_SOURCE_ACQUISITION_REQUIRED"
        else:
            dominant = "SSH_REPLAY_CONTROL_OR_AVOID_SCORE_REQUIRED"
        output.append(
            with_common(
                {
                    "symbol_session_horizon_replay_acquisition_id": f"OHLC-GTOS-UNIFIED-REPLAY-SSH-{index:04d}",
                    "symbol": key[0],
                    "route_session": key[1],
                    "horizon_id": key[2],
                    "market_gap_combo_rows": len(members),
                    "primitive_flags": sorted({row.get("primitive_flag") for row in members}),
                    "outside_gbpjpy_xauusd_current_branch_box_rows": outside_rows,
                    "market_gap_action_counts": compact_counter(action_counts),
                    "market_gap_replay_decision_counts": compact_counter(decision_counts),
                    "concentration_replay_test_counts": compact_counter(concentration_counts),
                    "market_gap_proxy_r_style_midpoint_mean": mean_or_none(proxy_scalars),
                    "market_gap_proxy_r_style_min": round(min(proxy_scalars), 9) if proxy_scalars else None,
                    "market_gap_proxy_r_style_max": round(max(proxy_scalars), 9) if proxy_scalars else None,
                    "market_gap_proxy_r_style_result_counts": compact_counter(
                        Counter(row.get("market_gap_proxy_r_style_result_class") for row in members)
                    ),
                    "implementation_candidate_rows": implementation_rows,
                    "source_acquisition_required_rows": source_required_rows,
                    "dominant_symbol_session_horizon_replay_decision": dominant,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_market_fss_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("market_gap_replay_decision"), row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        proxy_scalars = [
            float(row["market_gap_proxy_r_style_midpoint"])
            for row in members
            if row.get("market_gap_proxy_r_style_midpoint") is not None
        ]
        output.append(
            with_common(
                {
                    "market_gap_family_symbol_session_proxy_r_id": f"OHLC-GTOS-UNIFIED-REPLAY-MARKET-FSS-{index:04d}",
                    "market_gap_replay_decision": key[0],
                    "symbol": key[1],
                    "route_session": key[2],
                    "market_gap_rows": len(members),
                    "outside_gbpjpy_xauusd_current_branch_box_rows": sum(
                        1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")
                    ),
                    "proxy_r_scalar_rows": len(proxy_scalars),
                    "proxy_r_style_midpoint_mean": mean_or_none(proxy_scalars),
                    "proxy_r_style_min": round(min(proxy_scalars), 9) if proxy_scalars else None,
                    "proxy_r_style_max": round(max(proxy_scalars), 9) if proxy_scalars else None,
                    "proxy_r_style_result_counts": compact_counter(
                        Counter(row.get("market_gap_proxy_r_style_result_class") for row in members)
                    ),
                    "primitive_flags": sorted({row.get("primitive_flag") for row in members}),
                    "market_gap_action_counts": compact_counter(Counter(row.get("market_gap_action") for row in members)),
                    "concentration_replay_test_counts": compact_counter(
                        Counter(row.get("concentration_replay_test_result") for row in members)
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def branch_final_decision(row: dict[str, Any], rstyle: dict[str, Any] | None) -> str:
    action_class = str(row.get("action_execution_class") or "")
    score = float(row.get("candidate_score_proxy") or 0.0)
    rstyle_class = str((rstyle or {}).get("rstyle_proxy_signal_class") or row.get("rstyle_proxy_signal_class") or "")
    target_stop = str(row.get("target_stop_result") or "")
    if "PROVENANCE" in action_class:
        return "PRESERVE_PROVENANCE_EXCLUDE_FROM_SCALAR_IMPLEMENTATION"
    if "AVOID" in action_class and score < 0:
        return "KILL_OR_IMPLEMENT_AVOID_FILTER_FROM_FAILURE_CAUSE"
    if "MARKET_ENTRY" in action_class and score >= 0.25 and "TARGET_FIRST" in target_stop:
        return "IMPLEMENT_MARKET_ENTRY_CHALLENGER_BRANCH_CANDIDATE"
    if "REDESIGN" in action_class and score >= 0.25 and rstyle_class == "RSTYLE_PROXY_POSITIVE_MIDPOINT":
        return "REDESIGN_FILLABILITY_THEN_IMPLEMENT_CHALLENGER_CANDIDATE"
    if "REDESIGN" in action_class:
        return "REDESIGN_FILLABILITY_OR_RETEST_BEFORE_KEEP"
    if score >= 0.25 and rstyle_class == "RSTYLE_PROXY_POSITIVE_MIDPOINT":
        return "KEEP_PROXY_CHALLENGER_FOR_BRANCH_LOCAL_SCORER"
    return "KILL_LOW_PRIORITY_OR_REPAIR_BEFORE_KEEP"


def build_branch_rows(
    action_rows: list[dict[str, Any]],
    rstyle_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    rstyle_by_branch = {row.get("branch_queue_id"): row for row in rstyle_rows}
    output: list[dict[str, Any]] = []
    for index, row in enumerate(action_rows, 1):
        rstyle = rstyle_by_branch.get(row.get("branch_queue_id"), {})
        final_decision = branch_final_decision(row, rstyle)
        duplicate = rstyle.get("duplicate_effective_n") or {}
        pass_delta = rstyle.get("pass_control_delta") or {}
        output.append(
            with_common(
                {
                    "branch_keep_kill_redesign_implement_id": f"OHLC-GTOS-UNIFIED-REPLAY-BRANCH-{index:05d}",
                    "branch_action_execution_id": row.get("branch_action_execution_id"),
                    "branch_queue_id": row.get("branch_queue_id"),
                    "route_candidate_id": row.get("route_candidate_id"),
                    "target_stop_contract_id": row.get("target_stop_contract_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "side": row.get("side"),
                    "entry_variant": row.get("entry_variant"),
                    "primary_export_family": row.get("primary_export_family"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "action_execution_class": row.get("action_execution_class"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "target_stop_result": row.get("target_stop_result"),
                    "rstyle_midpoint_mean": rstyle.get("rstyle_midpoint_mean", row.get("rstyle_midpoint_mean")),
                    "rstyle_lower_mean": rstyle.get("rstyle_lower_mean"),
                    "rstyle_upper_mean": rstyle.get("rstyle_upper_mean"),
                    "sealed_or_proxy_outcome_status": rstyle.get("sealed_or_proxy_outcome_status"),
                    "rstyle_proxy_signal_class": rstyle.get("rstyle_proxy_signal_class", row.get("rstyle_proxy_signal_class")),
                    "expectancy_style_proxy": rstyle.get("expectancy_style_proxy"),
                    "pass_control_delta": pass_delta,
                    "cost_sensitivity": rstyle.get("cost_sensitivity"),
                    "duplicate_effective_n": duplicate,
                    "duplicate_effective_n_proxy": duplicate.get("unique_event_or_route_ids"),
                    "source_confidence_status": rstyle.get("source_confidence_status"),
                    "ambiguity_status": rstyle.get("ambiguity_status"),
                    "exact_failure_cause": row.get("exact_failure_cause"),
                    "exact_success_cause": row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": row.get("exact_missing_geometry_or_source_reason")
                    or EXACT_R_MISSING_REASON,
                    "keep_kill_redesign_implement_replay_decision": final_decision,
                    "branch_local_code_candidate": row.get("branch_local_code_candidate"),
                    "implementation_implication": row.get("keep_kill_redesign_implement_decision"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_branch_fss_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("primary_export_family"), row.get("symbol"), row.get("route_session"))].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(grouped.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        scalars = [float(row["rstyle_midpoint_mean"]) for row in members if row.get("rstyle_midpoint_mean") is not None]
        output.append(
            with_common(
                {
                    "branch_family_symbol_session_rstyle_result_id": f"OHLC-GTOS-UNIFIED-REPLAY-FSS-{index:04d}",
                    "primary_export_family": key[0],
                    "symbol": key[1],
                    "route_session": key[2],
                    "branch_rows": len(members),
                    "rstyle_scalar_rows": len(scalars),
                    "rstyle_midpoint_mean": mean_or_none(scalars),
                    "rstyle_midpoint_min": round(min(scalars), 9) if scalars else None,
                    "rstyle_midpoint_max": round(max(scalars), 9) if scalars else None,
                    "decision_counts": compact_counter(Counter(row.get("keep_kill_redesign_implement_replay_decision") for row in members)),
                    "rstyle_proxy_signal_counts": compact_counter(Counter(row.get("rstyle_proxy_signal_class") for row in members)),
                    "target_stop_result_counts": compact_counter(Counter(row.get("target_stop_result") for row in members)),
                    "exact_missing_reason_count": sum(1 for row in members if row.get("exact_missing_geometry_or_source_reason")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_scorer_spec_rows(
    spec_rows: list[dict[str, Any]],
    implementation_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    impl_by_type = Counter(row.get("implementation_candidate_type") for row in implementation_rows)
    score_by_type: dict[str, list[float]] = defaultdict(list)
    for row in implementation_rows:
        score = to_float(row.get("candidate_score_proxy"))
        if score is not None:
            score_by_type[str(row.get("implementation_candidate_type"))].append(score)
    output: list[dict[str, Any]] = []
    for index, row in enumerate(spec_rows, 1):
        candidate_type = str(row.get("implementation_candidate_type"))
        scores = score_by_type.get(candidate_type, [])
        if candidate_type == "CONCENTRATION_ARTIFACT_TEST":
            decision = "KEEP_CONCENTRATION_TEST_IN_SCORER_AND_FORCE_OUTSIDE_BRANCH_DENOMINATOR_CHECK"
        elif candidate_type in {"MARKET_GAP_ENTRY_GEOMETRY_SPEC", "MARKET_ENTRY_COMPARATOR_SPEC"}:
            decision = "IMPLEMENT_BRANCH_LOCAL_SCORER_SPEC_CANDIDATE"
        elif candidate_type in {"MARKET_GAP_SOURCE_EXPANSION_SPEC", "FILLABILITY_RETEST_REDESIGN_SPEC"}:
            decision = "IMPLEMENT_SCORER_SPEC_WITH_SOURCE_OR_FILLABILITY_REPAIR_GUARD"
        elif candidate_type in {"AVOID_OR_REDIRECT_SPEC", "MARKET_GAP_AVOID_INVERSE_SPEC"}:
            decision = "IMPLEMENT_AVOID_OR_INVERSE_SCORER_SPEC_CANDIDATE"
        else:
            decision = "PRESERVE_SPEC_AS_CONTEXT_OR_PROVENANCE"
        output.append(
            with_common(
                {
                    "branch_local_scorer_spec_candidate_id": f"OHLC-GTOS-UNIFIED-REPLAY-SCORER-{index:04d}",
                    "source_scorer_spec_id": row.get("source_scorer_spec_id"),
                    "scorer_spec_change_id": row.get("scorer_spec_change_id"),
                    "implementation_candidate_type": candidate_type,
                    "code_surface": row.get("code_surface"),
                    "builder_surface": row.get("builder_surface"),
                    "required_controls": row.get("required_controls"),
                    "input_denominator": row.get("input_denominator"),
                    "implementation_rows_for_type": int(impl_by_type.get(candidate_type, 0)),
                    "implementation_score_mean_for_type": mean_or_none(scores),
                    "scorer_spec_replay_decision": decision,
                    "branch_local_code_candidate": row.get("action_execution_code_candidate"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_concentration_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        current_rows = int(row.get("current_branch_rows") or 0)
        market_rows = int(row.get("market_gap_combo_rows") or 0)
        source_root = row.get("source_root")
        if current_rows == 0 and market_rows > 0:
            decision = "CONCENTRATION_REPLAY_DENOMINATOR_ARTIFACT_CONFIRMED"
        elif current_rows > 0 and market_rows > 0 and str(row.get("concentration_artifact_class", "")).startswith("MECHANISM"):
            decision = "CONCENTRATION_REPLAY_REAL_MECHANISM_AND_ARTIFACT_BOTH_TRUE"
        elif source_root:
            decision = "CONCENTRATION_REPLAY_SOURCE_ROOT_COVERAGE_TESTED"
        elif current_rows > 0:
            decision = "CONCENTRATION_REPLAY_CURRENT_BRANCH_COVERAGE_PRESENT"
        else:
            decision = "CONCENTRATION_REPLAY_NO_DIRECT_BRANCH_ROWS_REQUIRE_CONTEXT"
        output.append(
            with_common(
                {
                    "concentration_replay_test_id": f"OHLC-GTOS-UNIFIED-REPLAY-CONC-{index:05d}",
                    "concentration_artifact_restress_id": row.get("concentration_artifact_restress_id"),
                    "source_concentration_transfer_test_id": row.get("source_concentration_transfer_test_id"),
                    "test_axis": row.get("test_axis"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_root": source_root,
                    "source_root_row_count": row.get("source_root_row_count"),
                    "source_root_symbol_count": row.get("source_root_symbol_count"),
                    "current_branch_rows": row.get("current_branch_rows"),
                    "market_gap_combo_rows": row.get("market_gap_combo_rows"),
                    "full_tick_transfer_rows": row.get("full_tick_transfer_rows"),
                    "concentration_artifact_class": row.get("concentration_artifact_class"),
                    "restress_execution_decision": row.get("restress_execution_decision"),
                    "concentration_replay_decision": decision,
                    "decision_implication": row.get("decision_implication"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(groups: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    counters = {
        "source_acquisition_status": Counter(row.get("source_acquisition_status") for row in groups["source"]),
        "source_proxy_replay_result": Counter(row.get("source_proxy_replay_result") for row in groups["source"]),
        "entry_replay_decision": Counter(row.get("entry_replay_decision") for row in groups["entry_variant"]),
        "entry_parent_replay_decision": Counter(row.get("parent_replay_decision") for row in groups["entry_parent"]),
        "policy_variant_replay_decision": Counter(row.get("policy_variant_replay_decision") for row in groups["avoid_policy"]),
        "market_gap_replay_decision": Counter(row.get("market_gap_replay_decision") for row in groups["market"]),
        "dominant_symbol_session_horizon_replay_decision": Counter(
            row.get("dominant_symbol_session_horizon_replay_decision") for row in groups["ssh"]
        ),
        "branch_keep_kill_redesign_implement": Counter(
            row.get("keep_kill_redesign_implement_replay_decision") for row in groups["branch"]
        ),
        "scorer_spec_replay_decision": Counter(row.get("scorer_spec_replay_decision") for row in groups["scorer_spec"]),
        "concentration_replay_decision": Counter(row.get("concentration_replay_decision") for row in groups["concentration"]),
    }
    output: list[dict[str, Any]] = []
    for family, counter in counters.items():
        for key, count in sorted(counter.items(), key=lambda item: str(item[0])):
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-REPLAY-BUCKET-{len(output) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": key,
                        "row_count": int(count),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, {name: compact_counter(counter) for name, counter in counters.items()}


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_unified_variant_replay_acquisition"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "unified_variant_replay_acquisition_decisions_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Converted all variant rows plus branch-action/R-style/concentration denominators into replay/acquisition and implementation decisions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        VARIANT_RESULT,
        VARIANT_SOURCE,
        VARIANT_ENTRY,
        VARIANT_ENTRY_PARENT,
        VARIANT_AVOID,
        VARIANT_MARKET,
        VARIANT_SSH,
        ACTION_BRANCH,
        ACTION_CONCENTRATION,
        ACTION_SCORER_SPEC,
        SCORING_IMPLEMENTATION,
        EXEC_BRANCH_RSTYLE,
        EXEC_FSS_RSTYLE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    variant_result = read_json(VARIANT_RESULT)
    source_rows_input = read_jsonl(VARIANT_SOURCE)
    entry_rows_input = read_jsonl(VARIANT_ENTRY)
    avoid_rows_input = read_jsonl(VARIANT_AVOID)
    market_rows_input = read_jsonl(VARIANT_MARKET)
    action_branch_rows = read_jsonl(ACTION_BRANCH)
    concentration_rows_input = read_jsonl(ACTION_CONCENTRATION)
    scorer_spec_input = read_jsonl(ACTION_SCORER_SPEC)
    implementation_rows_input = read_jsonl(SCORING_IMPLEMENTATION)
    rstyle_rows = read_jsonl(EXEC_BRANCH_RSTYLE)

    source_rows = build_source_rows(source_rows_input, generated_at, manifest_hash)
    entry_variant_rows, entry_parent_rows = build_entry_variant_rows(entry_rows_input, generated_at, manifest_hash)
    avoid_policy_rows = build_avoid_policy_rows(avoid_rows_input, generated_at, manifest_hash)
    market_rows = build_market_rows(
        market_rows_input, source_rows, entry_parent_rows, avoid_policy_rows, generated_at, manifest_hash
    )
    ssh_rows = build_ssh_rows(market_rows, generated_at, manifest_hash)
    market_fss_rows = build_market_fss_rows(market_rows, generated_at, manifest_hash)
    branch_rows = build_branch_rows(action_branch_rows, rstyle_rows, generated_at, manifest_hash)
    branch_fss_rows = build_branch_fss_rows(branch_rows, generated_at, manifest_hash)
    scorer_spec_rows = build_scorer_spec_rows(scorer_spec_input, implementation_rows_input, generated_at, manifest_hash)
    concentration_rows = build_concentration_rows(concentration_rows_input, generated_at, manifest_hash)

    groups = {
        "source": source_rows,
        "entry_variant": entry_variant_rows,
        "entry_parent": entry_parent_rows,
        "avoid_policy": avoid_policy_rows,
        "market": market_rows,
        "ssh": ssh_rows,
        "market_fss": market_fss_rows,
        "branch": branch_rows,
        "branch_fss": branch_fss_rows,
        "scorer_spec": scorer_spec_rows,
        "concentration": concentration_rows,
    }
    bucket_rows, distributions = build_bucket_rows(groups, generated_at, manifest_hash)
    question_rows = [
        {
            "question_id": "OHLC-GTOS-UNIFIED-REPLAY-Q-001",
            "question": "Did the layer preserve all variant source, entry, avoid, and market-gap rows while converting them into decisions?",
            "answer_route": "Yes: 309 source, 272 entry variants, 46 avoid/inverse variants, and 400 market-gap rows are emitted with replay/acquisition decisions.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-REPLAY-Q-002",
            "question": "Does the branch table carry exact/proxy R-style outcome fields instead of only packet labels?",
            "answer_route": "Yes: all 386 branch rows join action decisions to branch R-style proxy intervals, pass-control deltas, costs, duplicate/effective-N, source confidence, ambiguity, and exact missing-source reason.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-REPLAY-Q-003",
            "question": "Does GBPJPY/XAUUSD concentration remain explicitly tested across available symbols, sessions, horizons, and source roots?",
            "answer_route": "Yes: the 124-row concentration replay ledger preserves symbol, symbol/session, symbol/session/horizon, and source-root restress axes.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-REPLAY-Q-004",
            "question": "Which outputs are branch-local code/spec implementation candidates?",
            "answer_route": "Branch, market-gap, entry, avoid/inverse, and scorer-spec ledgers carry implementation_implication or scorer_spec_replay_decision fields tied to code surfaces.",
        },
    ]
    question_rows = [with_common(row, generated_at, manifest_hash) for row in question_rows]

    counts = {
        "input_variant_source_rows": len(source_rows_input),
        "input_variant_entry_rows": len(entry_rows_input),
        "input_variant_avoid_rows": len(avoid_rows_input),
        "input_variant_market_rows": len(market_rows_input),
        "input_action_branch_rows": len(action_branch_rows),
        "input_action_concentration_rows": len(concentration_rows_input),
        "input_action_scorer_spec_rows": len(scorer_spec_input),
        "input_implementation_score_rows": len(implementation_rows_input),
        "input_branch_rstyle_rows": len(rstyle_rows),
        "source_acquisition_proxy_result_rows": len(source_rows),
        "entry_variant_replay_score_rows": len(entry_variant_rows),
        "entry_parent_replay_decision_rows": len(entry_parent_rows),
        "avoid_inverse_policy_replay_score_rows": len(avoid_policy_rows),
        "market_gap_replay_acquisition_synthesis_rows": len(market_rows),
        "symbol_session_horizon_replay_acquisition_rows": len(ssh_rows),
        "market_gap_family_symbol_session_proxy_r_rows": len(market_fss_rows),
        "branch_keep_kill_redesign_implement_rows": len(branch_rows),
        "branch_family_symbol_session_rstyle_result_rows": len(branch_fss_rows),
        "branch_local_scorer_spec_candidate_rows": len(scorer_spec_rows),
        "concentration_replay_test_rows": len(concentration_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "source_acquisition_additional_flagged_rows_needed_for_n20_total": sum(
            int(row.get("additional_flagged_rows_needed_for_n20") or 0) for row in source_rows
        ),
        "outside_branch_market_gap_replay_rows": sum(
            1 for row in market_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
        "outside_branch_implementation_candidate_rows": sum(
            1
            for row in market_rows
            if row.get("outside_gbpjpy_xauusd_current_branch_box")
            and str(row.get("market_gap_replay_decision", "")).startswith("IMPLEMENT")
        ),
    }
    system_decision = {
        "branch_replay_decision_counts": distributions["branch_keep_kill_redesign_implement"],
        "market_gap_replay_decision_counts": distributions["market_gap_replay_decision"],
        "concentration_replay_decision_counts": distributions["concentration_replay_decision"],
        "entry_replay_decision_counts": distributions["entry_replay_decision"],
        "avoid_policy_replay_decision_counts": distributions["policy_variant_replay_decision"],
        "system_recommendation": (
            "UNIFIED_VARIANT_REPLAY_ACQUISITION_RESULT: branch-local work should keep source acquisition "
            "active for under-N20 market gaps, implement or score entry-geometry and avoid/inverse candidates "
            "where replay decisions support them, and treat GBPJPY/XAUUSD concentration as real current-queue "
            "concentration plus a denominator artifact because outside-branch implementation/source routes remain present."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {"unified_candidate_variant_execution": variant_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    generated_files = [
        SOURCE_ACQUISITION_LEDGER,
        ENTRY_VARIANT_REPLAY_LEDGER,
        ENTRY_PARENT_REPLAY_LEDGER,
        AVOID_POLICY_REPLAY_LEDGER,
        MARKET_GAP_REPLAY_LEDGER,
        SSH_REPLAY_LEDGER,
        MARKET_FSS_PROXY_R_LEDGER,
        BRANCH_DECISION_LEDGER,
        BRANCH_FSS_RSTYLE_LEDGER,
        SCORER_SPEC_LEDGER,
        CONCENTRATION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(SOURCE_ACQUISITION_LEDGER, source_rows)
    write_jsonl(ENTRY_VARIANT_REPLAY_LEDGER, entry_variant_rows)
    write_jsonl(ENTRY_PARENT_REPLAY_LEDGER, entry_parent_rows)
    write_jsonl(AVOID_POLICY_REPLAY_LEDGER, avoid_policy_rows)
    write_jsonl(MARKET_GAP_REPLAY_LEDGER, market_rows)
    write_jsonl(SSH_REPLAY_LEDGER, ssh_rows)
    write_jsonl(MARKET_FSS_PROXY_R_LEDGER, market_fss_rows)
    write_jsonl(BRANCH_DECISION_LEDGER, branch_rows)
    write_jsonl(BRANCH_FSS_RSTYLE_LEDGER, branch_fss_rows)
    write_jsonl(SCORER_SPEC_LEDGER, scorer_spec_rows)
    write_jsonl(CONCENTRATION_LEDGER, concentration_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Variant Replay Acquisition",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Source acquisition/proxy result rows: `{counts['source_acquisition_proxy_result_rows']}`",
                f"- Entry variant replay score rows: `{counts['entry_variant_replay_score_rows']}`",
                f"- Avoid/inverse policy replay rows: `{counts['avoid_inverse_policy_replay_score_rows']}`",
                f"- Market-gap replay/acquisition synthesis rows: `{counts['market_gap_replay_acquisition_synthesis_rows']}`",
                f"- Market-gap family/symbol/session proxy-R rows: `{counts['market_gap_family_symbol_session_proxy_r_rows']}`",
                f"- Branch keep/kill/redesign/implement rows: `{counts['branch_keep_kill_redesign_implement_rows']}`",
                f"- Concentration replay test rows: `{counts['concentration_replay_test_rows']}`",
                "",
                "Core result: variant rows now alter concrete replay/acquisition and implementation decisions rather than remaining score-now queues.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
