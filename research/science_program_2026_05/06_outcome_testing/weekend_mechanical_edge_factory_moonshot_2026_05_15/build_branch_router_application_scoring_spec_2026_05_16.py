#!/usr/bin/env python3
"""Apply branch-local routers into concrete scoring/spec ledgers.

This is the computation layer after the follow-up packet and router modules.
It does not leave router classes as labels: every branch receives a concrete
numeric spec vector, every family ledger receives family-specific lower-level
metrics, and all rows keep the exact source/ordering/fillability limits.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.branch_entry_adverse_redesign_router import (  # noqa: E402
    classify_entry_adverse_redesign,
)
from src.research_infra.branch_m15_interval_router import classify_m15_interval  # noqa: E402
from src.research_infra.branch_m1_conflict_router import classify_m1_conflict  # noqa: E402
from src.research_infra.branch_positive_challenger_router import classify_positive_replay  # noqa: E402
from src.research_infra.branch_source_router import classify_source_router  # noqa: E402


FOLLOWUP_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_PACKET_RESULT_2026-05-16.json"
FOLLOWUP_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_BRANCH_LEDGER_2026-05-16.jsonl"
FOLLOWUP_ACTION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_FAMILY_ACTION_LEDGER_2026-05-16.jsonl"
FOLLOWUP_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_SOURCE_ROUTER_LEDGER_2026-05-16.jsonl"
FOLLOWUP_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_M15_LEDGER_2026-05-16.jsonl"
FOLLOWUP_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_M1_LEDGER_2026-05-16.jsonl"
FOLLOWUP_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_POSITIVE_LEDGER_2026-05-16.jsonl"
FOLLOWUP_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
FOLLOWUP_BINDING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FOLLOWUP_COMPUTATION_BINDING_PRESERVE_LEDGER_2026-05-16.jsonl"
FULL_OUTCOME_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"

SOURCE_ROUTER_MODULE = REPO / "src/research_infra/branch_source_router.py"
M15_ROUTER_MODULE = REPO / "src/research_infra/branch_m15_interval_router.py"
M1_ROUTER_MODULE = REPO / "src/research_infra/branch_m1_conflict_router.py"
POSITIVE_ROUTER_MODULE = REPO / "src/research_infra/branch_positive_challenger_router.py"
ENTRY_ADVERSE_ROUTER_MODULE = REPO / "src/research_infra/branch_entry_adverse_redesign_router.py"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_FAMILY_LEDGER_2026-05-16.jsonl"
SOURCE_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_SOURCE_LEDGER_2026-05-16.jsonl"
M15_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_M15_LEDGER_2026-05-16.jsonl"
M1_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_M1_LEDGER_2026-05-16.jsonl"
POSITIVE_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_POSITIVE_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BINDING_SPEC_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_BINDING_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch router-application scoring spec only. It applies branch-local "
    "research router modules to all follow-up rows and computes same-resource "
    "proxy/spec metrics for source stress, M15 intervals, M1 support conflict, "
    "positive replay, and entry/adverse redesign. It does not change live "
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


def inum(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def round_or_none(value: Any, digits: int = 6) -> float | None:
    value_float = fnum(value)
    return round(value_float, digits) if value_float is not None else None


def subtract_or_none(left: Any, right: Any) -> float | None:
    left_value = fnum(left)
    right_value = fnum(right)
    if left_value is None or right_value is None:
        return None
    return round(left_value - right_value, 6)


def ratio_or_none(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 9)


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
                "source_manifest_id": f"OHLC-GTOS-ROUTER-APP-SRC-{index:04d}",
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


def source_spec_score(source: dict[str, Any] | None, source_class: str) -> tuple[float | None, str, str]:
    if not source:
        return None, "SOURCE_SPEC_NOT_APPLICABLE", "SOURCE_NOT_EXPORTED"
    lower = fnum(source.get("stress_lower_mean"))
    mid = fnum(source.get("stress_midpoint_mean"))
    upper = fnum(source.get("stress_upper_mean"))
    width = subtract_or_none(upper, lower)
    if lower is None and mid is None:
        return None, "SOURCE_SPEC_MISSING_STRESS_BOUNDS", "ACQUIRE_SOURCE_OR_PRESERVE_UPSTREAM_PROXY"
    if source_class == "SOURCE_COST_SENSITIVE_RISK_ROUTER_ACQUIRE_EXACT_OR_CAP_COST_MODEL":
        return round_or_none(lower), "SOURCE_COST_CAPPED_LOWER_BOUND_SCORE", "USE_LOWER_BOUND_UNTIL_EXACT_SPREAD_SOURCE_REPAIRED"
    if source_class == "SOURCE_CONSERVATIVE_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE":
        return round_or_none(lower if lower is not None else mid), "SOURCE_NEGATIVE_AVOID_SCORE", "AVOID_OR_ACQUIRE_EXACT_SOURCE_BEFORE_RETEST"
    if width is not None and width > 0:
        return round_or_none(mid), "SOURCE_STRADDLE_MIDPOINT_WITH_BOUNDS_SCORE", "SPLIT_COST_MODEL_OR_KEEP_BOUNDS_ROUTER"
    return round_or_none(mid), "SOURCE_STRESS_MIDPOINT_SCORE", "PRESERVE_SOURCE_STRESS_SCORE"


def m15_spec_score(m15: dict[str, Any] | None, m15_class: str) -> tuple[float | None, str, str]:
    if not m15:
        return None, "M15_SPEC_NOT_APPLICABLE", "M15_NOT_EXPORTED"
    lower = fnum(m15.get("interval_lower_mean"))
    mid = fnum(m15.get("interval_midpoint_mean"))
    upper = fnum(m15.get("interval_upper_mean"))
    if m15_class == "M15_TARGET_FIRST_CHALLENGER_INTERVAL_COMPUTED":
        return round_or_none(lower), "M15_TARGET_FIRST_CONSERVATIVE_BOUND_SCORE", "CHALLENGER_ONLY_IF_LOWER_BOUND_REMAINS_POSITIVE"
    if m15_class == "M15_STOP_FIRST_AVOID_OR_REDESIGN_INTERVAL_COMPUTED":
        return round_or_none(lower if lower is not None else mid), "M15_STOP_FIRST_AVOID_BOUND_SCORE", "AVOID_OR_REDESIGN_UNLESS_INTRABAR_SOURCE_REPAIRS"
    if lower is not None and upper is not None and lower <= 0 <= upper:
        return round_or_none(mid), "M15_STRADDLE_BOUNDS_ROUTER_SCORE", "KEEP_TARGET_FIRST_STOP_FIRST_BOUNDS_SPLIT"
    return round_or_none(mid), "M15_INTERVAL_MIDPOINT_SCORE", "PRESERVE_M15_INTERVAL_SCORE"


def m1_spec_score(m1: dict[str, Any] | None, m1_class: str) -> tuple[float | None, str, str]:
    if not m1:
        return None, "M1_SPEC_NOT_APPLICABLE", "M1_NOT_EXPORTED"
    branch_mid = fnum(m1.get("branch_midpoint_mean"))
    support_mid = fnum(m1.get("m1_support_midpoint_mean"))
    if branch_mid is None and support_mid is None:
        return None, "M1_SPEC_MISSING_MIDPOINTS", "PRESERVE_M1_SOURCE_REQUIREMENT"
    if branch_mid is None:
        return round_or_none(support_mid), "M1_SUPPORT_ONLY_SCORE", "USE_SUPPORT_PROXY_AND_PRESERVE_BRANCH_GAP"
    if support_mid is None:
        return round_or_none(branch_mid), "M1_BRANCH_ONLY_SCORE", "USE_BRANCH_PROXY_AND_PRESERVE_SUPPORT_GAP"
    support_adjusted = branch_mid + 0.50 * (support_mid - branch_mid)
    if m1_class == "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT_SPLIT_COMPUTED":
        return round(support_adjusted, 6), "M1_SUPPORT_BRANCH_HALFSTEP_CONFLICT_SCORE", "SPLIT_SUPPORT_POSITIVE_FROM_BRANCH_AGGREGATE"
    return round_or_none(support_mid), "M1_SUPPORT_TARGET_STABLE_SCORE", "SCORE_SUPPORT_STABLE_CHALLENGER"


def positive_modifier_penalty(positive: dict[str, Any] | None) -> float:
    if not positive:
        return 0.0
    penalty = 0.0
    if positive.get("positive_control_delta_modifier_class") == "CONTROL_DELTA_ADVERSE_OR_BELOW_ROUTE_PEERS":
        penalty += 0.10
    if positive.get("positive_concentration_modifier_class") == "CONCENTRATION_OR_EFFECTIVE_N_STRESSED":
        penalty += 0.10
    return round(penalty, 6)


def positive_spec_score(positive: dict[str, Any] | None, positive_class: str) -> tuple[float | None, str, str, float]:
    if not positive:
        return None, "POSITIVE_SPEC_NOT_APPLICABLE", "POSITIVE_NOT_EXPORTED", 0.0
    penalty = positive_modifier_penalty(positive)
    lower = fnum(positive.get("positive_lower_mean"))
    mid = fnum(positive.get("positive_midpoint_mean"))
    if positive_class == "POSITIVE_REPLAY_NOW_PROXY_OR_EXACT_REPAIR_COMPUTED":
        base = lower if lower is not None else mid
        score_class = "POSITIVE_REPLAY_CONSERVATIVE_ADJUSTED_SCORE"
        action = "REPLAY_NOW_WITH_CONTROL_AND_CONCENTRATION_PENALTY"
    else:
        base = mid
        score_class = "POSITIVE_REPAIR_FIRST_STRESS_GATED_SCORE"
        action = "REPAIR_SOURCE_OR_STRESS_BEFORE_REPLAY"
    if base is None:
        return None, "POSITIVE_SPEC_MISSING_PROXY", action, penalty
    return round(base - penalty, 6), score_class, action, penalty


def entry_adverse_spec_score(entry: dict[str, Any] | None, entry_class: str) -> tuple[float | None, str, str, dict[str, Any]]:
    if not entry:
        return None, "ENTRY_ADVERSE_SPEC_MISSING", "ENTRY_ADVERSE_NOT_EXPORTED", {}
    target_first = inum(entry.get("target_first_rows"))
    stop_first = inum(entry.get("stop_first_rows"))
    no_fill = inum(entry.get("no_fill_or_unfilled_rows"))
    total = target_first + stop_first + no_fill
    target_rate = ratio_or_none(target_first, total)
    stop_rate = ratio_or_none(stop_first, total)
    no_fill_rate = ratio_or_none(no_fill, total)
    fillability_rate = ratio_or_none(target_first + stop_first, total)
    redesign_pressure = None
    if target_rate is not None and stop_rate is not None and no_fill_rate is not None:
        redesign_pressure = round(stop_rate + no_fill_rate - target_rate, 6)
    if entry_class == "ENTRY_AND_ADVERSE_REDESIGN_COMPUTED":
        score_class = "ENTRY_ADVERSE_REDESIGN_PRESSURE_SCORE"
        action = "REDESIGN_ENTRY_AND_ADVERSE_STOP_FIRST_GEOMETRY"
    elif entry_class == "ENTRY_REDESIGN_COMPUTED_ADVERSE_PRESERVED":
        score_class = "ENTRY_REDESIGN_FILLABILITY_SCORE"
        action = "REDESIGN_ENTRY_GEOMETRY_AND_PRESERVE_ADVERSE_CONTEXT"
    else:
        score_class = "ENTRY_ADVERSE_PRESERVE_SCORE"
        action = "PRESERVE_NO_REDESIGN_SCOPE"
    metrics = {
        "target_first_rate": target_rate,
        "stop_first_rate": stop_rate,
        "no_fill_or_unfilled_rate": no_fill_rate,
        "fillability_rate": fillability_rate,
        "redesign_pressure_score": redesign_pressure,
    }
    return redesign_pressure, score_class, action, metrics


def branch_application_class(primary_family: str, score: float | None, branch: dict[str, Any]) -> str:
    if primary_family == "BINDING":
        return "BINDING_PRESERVE_NO_SCALAR_APPLICATION"
    if score is None:
        return f"{primary_family}_APPLICATION_SOURCE_OR_GEOMETRY_MISSING"
    if score > 0 and branch.get("sealed_proxy_class") in {"SEALED_POINT_POSITIVE", "SEALED_INTERVAL_ALL_POSITIVE"}:
        return f"{primary_family}_APPLICATION_POSITIVE_SCORE_AND_SEALED_POSITIVE"
    if score > 0:
        return f"{primary_family}_APPLICATION_POSITIVE_SCORE_WITH_RESIDUAL_LIMITS"
    if score < 0:
        return f"{primary_family}_APPLICATION_NEGATIVE_SCORE_AVOID_OR_REDESIGN"
    return f"{primary_family}_APPLICATION_ZERO_SCORE_BOUNDS_SPLIT"


def implementation_implication(primary_family: str, branch_class: str, branch: dict[str, Any]) -> str:
    if primary_family == "SOURCE":
        return "branch_local_source_cost_router_or_exact_source_acquisition_spec"
    if primary_family == "M15":
        return "branch_local_m15_target_stop_bounds_selector_spec"
    if primary_family == "M1":
        return "branch_local_m1_support_conflict_split_selector_spec"
    if primary_family == "POSITIVE":
        return "branch_local_positive_challenger_replay_spec"
    if primary_family == "ENTRY_ADVERSE":
        return "branch_local_entry_adverse_redesign_spec"
    if "BINDING" in branch_class:
        return "preserve_targetstop_na_binding_no_scalar_implementation"
    return str(branch.get("next_branch_local_surface") or "research_artifact_only")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Router-Application Scoring Spec",
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
        "branch_router_application_class",
        "router_application_score_class",
        "source_router_followup_class",
        "m15_followup_class",
        "m1_followup_class",
        "positive_followup_class",
        "entry_adverse_followup_class",
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
        FAMILY_SPEC_LEDGER,
        SOURCE_SPEC_LEDGER,
        M15_SPEC_LEDGER,
        M1_SPEC_LEDGER,
        POSITIVE_SPEC_LEDGER,
        ENTRY_ADVERSE_SPEC_LEDGER,
        BINDING_SPEC_LEDGER,
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
                "type": "branch_router_application_scoring_spec",
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
                    "event_type": "branch_router_application_scoring_spec_built",
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
    followup_result = read_json(FOLLOWUP_RESULT)
    branch_rows_in = read_jsonl(FOLLOWUP_BRANCH)
    action_rows_in = read_jsonl(FOLLOWUP_ACTION)
    source_rows_in = read_jsonl(FOLLOWUP_SOURCE)
    m15_rows_in = read_jsonl(FOLLOWUP_M15)
    m1_rows_in = read_jsonl(FOLLOWUP_M1)
    positive_rows_in = read_jsonl(FOLLOWUP_POSITIVE)
    entry_rows_in = read_jsonl(FOLLOWUP_ENTRY_ADVERSE)
    binding_rows_in = read_jsonl(FOLLOWUP_BINDING)
    full_rows_in = read_jsonl(FULL_OUTCOME_BRANCH)

    branch_by_id = by_branch(branch_rows_in)
    action_by_id = group_by_branch(action_rows_in)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m1_by_id = by_branch(m1_rows_in)
    positive_by_id = by_branch(positive_rows_in)
    entry_by_id = by_branch(entry_rows_in)
    binding_by_id = by_branch(binding_rows_in)
    full_by_id = by_branch(full_rows_in)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            FOLLOWUP_RESULT,
            FOLLOWUP_BRANCH,
            FOLLOWUP_ACTION,
            FOLLOWUP_SOURCE,
            FOLLOWUP_M15,
            FOLLOWUP_M1,
            FOLLOWUP_POSITIVE,
            FOLLOWUP_ENTRY_ADVERSE,
            FOLLOWUP_BINDING,
            FULL_OUTCOME_BRANCH,
            SOURCE_ROUTER_MODULE,
            M15_ROUTER_MODULE,
            M1_ROUTER_MODULE,
            POSITIVE_ROUTER_MODULE,
            ENTRY_ADVERSE_ROUTER_MODULE,
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
        full = full_by_id.get(branch_id, {})
        source = source_by_id.get(branch_id)
        m15 = m15_by_id.get(branch_id)
        m1 = m1_by_id.get(branch_id)
        positive = positive_by_id.get(branch_id)
        entry = entry_by_id.get(branch_id)

        source_classified = classify_source_router(source)
        m15_classified = classify_m15_interval(m15)
        m1_classified = classify_m1_conflict(m1)
        positive_classified = classify_positive_replay(positive)
        entry_classified = classify_entry_adverse_redesign(entry)

        source_score, source_score_class, source_action = source_spec_score(
            source, source_classified["source_router_followup_class"]
        )
        m15_score, m15_score_class, m15_action = m15_spec_score(m15, m15_classified["m15_followup_class"])
        m1_score, m1_score_class, m1_action = m1_spec_score(m1, m1_classified["m1_followup_class"])
        positive_score, positive_score_class, positive_action, positive_penalty = positive_spec_score(
            positive, positive_classified["positive_followup_class"]
        )
        entry_score, entry_score_class, entry_action, entry_metrics = entry_adverse_spec_score(
            entry, entry_classified["entry_adverse_followup_class"]
        )

        score_by_family = {
            "SOURCE": source_score,
            "M15": m15_score,
            "M1": m1_score,
            "POSITIVE": positive_score,
            "ENTRY_ADVERSE": entry_score,
            "BINDING": None,
        }
        score_class_by_family = {
            "SOURCE": source_score_class,
            "M15": m15_score_class,
            "M1": m1_score_class,
            "POSITIVE": positive_score_class,
            "ENTRY_ADVERSE": entry_score_class,
            "BINDING": "BINDING_NO_SCALAR_SCORE",
        }
        action_by_family = {
            "SOURCE": source_action,
            "M15": m15_action,
            "M1": m1_action,
            "POSITIVE": positive_action,
            "ENTRY_ADVERSE": entry_action,
            "BINDING": "PRESERVE_BINDING_NO_SCALAR_FILL",
        }

        primary_family = str(branch.get("primary_export_family"))
        router_score = score_by_family.get(primary_family)
        router_score_class = score_class_by_family.get(primary_family, "UNKNOWN_PRIMARY_SCORE_CLASS")
        router_action = action_by_family.get(primary_family, "UNKNOWN_PRIMARY_ACTION")
        branch_class = branch_application_class(primary_family, router_score, branch)
        impl_implication = implementation_implication(primary_family, branch_class, branch)

        base = common_base(branch)
        branch_rows.append(
            {
                **base,
                "router_application_branch_id": f"OHLC-GTOS-ROUTER-APP-BRANCH-{len(branch_rows) + 1:05d}",
                "primary_export_family": primary_family,
                "primary_export_class": branch.get("primary_export_class"),
                "next_computation_class": branch.get("next_computation_class"),
                "branch_primary_followup_class": branch.get("branch_primary_followup_class"),
                "branch_router_application_class": branch_class,
                "router_application_score": round_or_none(router_score),
                "router_application_score_class": router_score_class,
                "router_application_action": router_action,
                "router_application_formula": (
                    "family-specific lower-level proxy: source lower/cost bound, "
                    "M15 interval bound, M1 support half-step, positive modifier-adjusted "
                    "conservative replay, or entry/adverse redesign pressure"
                ),
                "same_resource_computable_status": branch.get("same_resource_computable_status"),
                "next_branch_local_surface": branch.get("next_branch_local_surface"),
                "sealed_or_proxy_outcome_status": branch.get("sealed_or_proxy_outcome_status"),
                "sealed_proxy_class": branch.get("sealed_proxy_class"),
                "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
                "expectancy_style_proxy_method": branch.get("expectancy_style_proxy_method"),
                "expectancy_style_proxy_value": branch.get("rstyle_midpoint_mean"),
                "target_stop_result": branch.get("target_stop_result"),
                "pass_control_delta_status": branch.get("pass_control_delta_status"),
                "cost_sensitivity_proxy_status": branch.get("cost_sensitivity_proxy_status"),
                "duplicate_effective_n": full.get("duplicate_effective_n"),
                "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
                "concentration_summary": full.get("concentration_summary"),
                "source_confidence_status": branch.get("source_confidence_status"),
                "ambiguity_status": branch.get("ambiguity_status"),
                "implementation_implication": impl_implication,
                "exact_failure_cause": branch.get("exact_failure_cause"),
                "exact_success_cause": branch.get("exact_success_cause"),
                "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
                "source_router_followup_class": source_classified["source_router_followup_class"],
                "source_stress_interval_sign_class": source_classified["source_stress_interval_sign_class"],
                "source_spec_score": round_or_none(source_score),
                "m15_followup_class": m15_classified["m15_followup_class"],
                "m15_interval_sign_class": m15_classified["m15_interval_sign_class"],
                "m15_spec_score": round_or_none(m15_score),
                "m1_followup_class": m1_classified["m1_followup_class"],
                "m1_branch_midpoint_sign_class": m1_classified["m1_branch_midpoint_sign_class"],
                "m1_support_midpoint_sign_class": m1_classified["m1_support_midpoint_sign_class"],
                "m1_spec_score": round_or_none(m1_score),
                "positive_followup_class": positive_classified["positive_followup_class"],
                "positive_interval_sign_class": positive_classified["positive_interval_sign_class"],
                "positive_modifier_class": positive_classified["positive_modifier_class"],
                "positive_spec_score": round_or_none(positive_score),
                "entry_adverse_followup_class": entry_classified["entry_adverse_followup_class"],
                "entry_target_stop_balance_class": entry_classified["entry_target_stop_balance_class"],
                "entry_adverse_spec_score": round_or_none(entry_score),
                "source_export_present": source is not None,
                "m15_export_present": m15 is not None,
                "m1_export_present": m1 is not None,
                "positive_export_present": positive is not None,
                "entry_adverse_export_present": entry is not None,
                "export_action_count": branch.get("export_action_count"),
                "family_action_count": len(action_by_id.get(branch_id, [])),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )

        if source:
            lower = fnum(source.get("stress_lower_mean"))
            upper = fnum(source.get("stress_upper_mean"))
            source_rows.append(
                {
                    **common_base(source),
                    "source_spec_id": f"OHLC-GTOS-ROUTER-APP-SOURCE-{len(source_rows) + 1:05d}",
                    **source_classified,
                    "source_export_class": source.get("source_export_class"),
                    "source_risk_score_class": source.get("source_risk_score_class"),
                    "branch_stress_class": source.get("branch_stress_class"),
                    "source_spec_score": round_or_none(source_score),
                    "source_spec_score_class": source_score_class,
                    "source_spec_action": source_action,
                    "stress_lower_mean": source.get("stress_lower_mean"),
                    "stress_midpoint_mean": source.get("stress_midpoint_mean"),
                    "stress_upper_mean": source.get("stress_upper_mean"),
                    "stress_interval_width": source.get("stress_interval_width"),
                    "computed_cost_sensitivity_span": subtract_or_none(upper, lower),
                    "source_support_rows": source.get("source_support_rows"),
                    "exact_source_requirement_status": source.get("acquisition_or_proxy_requirement"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if m15:
            lower = fnum(m15.get("interval_lower_mean"))
            upper = fnum(m15.get("interval_upper_mean"))
            m15_rows.append(
                {
                    **common_base(m15),
                    "m15_spec_id": f"OHLC-GTOS-ROUTER-APP-M15-{len(m15_rows) + 1:05d}",
                    **m15_classified,
                    "m15_export_class": m15.get("m15_export_class"),
                    "m15_interval_score_class": m15.get("m15_interval_score_class"),
                    "m15_spec_score": round_or_none(m15_score),
                    "m15_spec_score_class": m15_score_class,
                    "m15_spec_action": m15_action,
                    "interval_lower_mean": m15.get("interval_lower_mean"),
                    "interval_midpoint_mean": m15.get("interval_midpoint_mean"),
                    "interval_upper_mean": m15.get("interval_upper_mean"),
                    "interval_width": m15.get("interval_width"),
                    "computed_target_first_minus_stop_first_span": subtract_or_none(upper, lower),
                    "proxy_variant_count": m15.get("proxy_variant_count"),
                    "exact_chronology_claim": False,
                    "chronology_requirement": m15.get("chronology_requirement"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if m1:
            branch_mid = fnum(m1.get("branch_midpoint_mean"))
            support_mid = fnum(m1.get("m1_support_midpoint_mean"))
            support_adjusted = None
            if branch_mid is not None and support_mid is not None:
                support_adjusted = round(branch_mid + 0.50 * (support_mid - branch_mid), 6)
            m1_rows.append(
                {
                    **common_base(m1),
                    "m1_spec_id": f"OHLC-GTOS-ROUTER-APP-M1-{len(m1_rows) + 1:05d}",
                    **m1_classified,
                    "m1_export_class": m1.get("m1_export_class"),
                    "m1_conflict_score_class": m1.get("m1_conflict_score_class"),
                    "m1_spec_score": round_or_none(m1_score),
                    "m1_spec_score_class": m1_score_class,
                    "m1_spec_action": m1_action,
                    "branch_midpoint_mean": m1.get("branch_midpoint_mean"),
                    "m1_support_midpoint_mean": m1.get("m1_support_midpoint_mean"),
                    "m1_support_minus_branch_midpoint": m1.get("m1_support_minus_branch_midpoint"),
                    "support_adjusted_midpoint": support_adjusted,
                    "m1_support_resolution_class": m1.get("m1_support_resolution_class"),
                    "proxy_variant_count": m1.get("proxy_variant_count"),
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
                    "ordering_requirement": m1.get("ordering_requirement"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if positive:
            lower = fnum(positive.get("positive_lower_mean"))
            mid = fnum(positive.get("positive_midpoint_mean"))
            upper = fnum(positive.get("positive_upper_mean"))
            positive_rows.append(
                {
                    **common_base(positive),
                    "positive_spec_id": f"OHLC-GTOS-ROUTER-APP-POSITIVE-{len(positive_rows) + 1:05d}",
                    **positive_classified,
                    "positive_export_class": positive.get("positive_export_class"),
                    "positive_replay_score_class": positive.get("positive_replay_score_class"),
                    "positive_spec_score": round_or_none(positive_score),
                    "positive_spec_score_class": positive_score_class,
                    "positive_spec_action": positive_action,
                    "positive_modifier_penalty": positive_penalty,
                    "positive_lower_mean": positive.get("positive_lower_mean"),
                    "positive_midpoint_mean": positive.get("positive_midpoint_mean"),
                    "positive_upper_mean": positive.get("positive_upper_mean"),
                    "positive_interval_width": subtract_or_none(upper, lower),
                    "positive_adjusted_lower": round_or_none(lower - positive_penalty if lower is not None else None),
                    "positive_adjusted_midpoint": round_or_none(mid - positive_penalty if mid is not None else None),
                    "positive_replayable_now": positive.get("positive_replayable_now"),
                    "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class"),
                    "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if entry:
            entry_rows.append(
                {
                    **common_base(entry),
                    "entry_adverse_spec_id": f"OHLC-GTOS-ROUTER-APP-ENTRY-ADVERSE-{len(entry_rows) + 1:05d}",
                    **entry_classified,
                    "entry_adverse_export_class": entry.get("entry_adverse_export_class"),
                    "entry_adverse_score_class": entry.get("entry_adverse_score_class"),
                    "entry_adverse_spec_score": round_or_none(entry_score),
                    "entry_adverse_spec_score_class": entry_score_class,
                    "entry_adverse_spec_action": entry_action,
                    "target_first_rows": entry.get("target_first_rows"),
                    "stop_first_rows": entry.get("stop_first_rows"),
                    "no_fill_or_unfilled_rows": entry.get("no_fill_or_unfilled_rows"),
                    "target_first_rate": entry_metrics.get("target_first_rate"),
                    "stop_first_rate": entry_metrics.get("stop_first_rate"),
                    "no_fill_or_unfilled_rate": entry_metrics.get("no_fill_or_unfilled_rate"),
                    "fillability_rate": entry_metrics.get("fillability_rate"),
                    "redesign_pressure_score": entry_metrics.get("redesign_pressure_score"),
                    "entry_geometry_retest_class": entry.get("entry_geometry_retest_class"),
                    "entry_redesign_action_class": entry.get("entry_redesign_action_class"),
                    "adverse_stop_first_class": entry.get("adverse_stop_first_class"),
                    "adverse_redesign_action_class": entry.get("adverse_redesign_action_class"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if binding_by_id.get(branch_id):
            binding = binding_by_id[branch_id]
            binding_rows.append(
                {
                    **common_base(binding),
                    "binding_spec_id": f"OHLC-GTOS-ROUTER-APP-BINDING-{len(binding_rows) + 1:05d}",
                    "binding_preserve_status": binding.get("binding_preserve_status"),
                    "no_scalar_fill": True,
                    "mechanical_triage_score_proxy": None,
                    "router_application_score": None,
                    "rstyle_lower_mean": None,
                    "rstyle_midpoint_mean": None,
                    "rstyle_upper_mean": None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        family_score_lookup = {
            "SOURCE": source_score,
            "ORDERING": m15_score if m15 else m1_score,
            "ENTRY": entry_score,
            "ADVERSE": entry_score,
            "POSITIVE": positive_score,
        }
        family_class_lookup = {
            "SOURCE": source_score_class,
            "ORDERING": m15_score_class if m15 else m1_score_class,
            "ENTRY": entry_score_class,
            "ADVERSE": entry_score_class,
            "POSITIVE": positive_score_class,
        }
        family_action_lookup = {
            "SOURCE": source_action,
            "ORDERING": m15_action if m15 else m1_action,
            "ENTRY": entry_action,
            "ADVERSE": entry_action,
            "POSITIVE": positive_action,
        }
        for action in sorted(action_by_id.get(branch_id, []), key=lambda row: row.get("followup_family_action_id") or ""):
            family = action.get("action_family")
            family_rows.append(
                {
                    **common_base(action),
                    "family_spec_id": f"OHLC-GTOS-ROUTER-APP-FAMILY-{len(family_rows) + 1:05d}",
                    "followup_family_action_id": action.get("followup_family_action_id"),
                    "action_family": family,
                    "family_followup_class": action.get("family_followup_class"),
                    "family_spec_score": round_or_none(family_score_lookup.get(family)),
                    "family_spec_score_class": family_class_lookup.get(family, "UNKNOWN_FAMILY_SPEC_SCORE_CLASS"),
                    "family_spec_action": family_action_lookup.get(family, "UNKNOWN_FAMILY_SPEC_ACTION"),
                    "family_score_proxy_from_prior_packet": action.get("family_score_proxy"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for category, value in [
            ("primary_export_family", primary_family),
            ("primary_export_class", branch.get("primary_export_class")),
            ("branch_router_application_class", branch_class),
            ("router_application_score_class", router_score_class),
            ("router_application_action", router_action),
            ("sealed_proxy_class", branch.get("sealed_proxy_class")),
            ("target_stop_result", branch.get("target_stop_result")),
            ("pass_control_delta_status", branch.get("pass_control_delta_status")),
            ("cost_sensitivity_proxy_status", branch.get("cost_sensitivity_proxy_status")),
            ("effective_n_concentration_class", branch.get("effective_n_concentration_class")),
            ("source_confidence_status", branch.get("source_confidence_status")),
            ("ambiguity_status", branch.get("ambiguity_status")),
            ("implementation_implication", impl_implication),
            ("source_router_followup_class", source_classified["source_router_followup_class"]),
            ("source_stress_interval_sign_class", source_classified["source_stress_interval_sign_class"]),
            ("m15_followup_class", m15_classified["m15_followup_class"]),
            ("m15_interval_sign_class", m15_classified["m15_interval_sign_class"]),
            ("m1_followup_class", m1_classified["m1_followup_class"]),
            ("m1_branch_midpoint_sign_class", m1_classified["m1_branch_midpoint_sign_class"]),
            ("m1_support_midpoint_sign_class", m1_classified["m1_support_midpoint_sign_class"]),
            ("positive_followup_class", positive_classified["positive_followup_class"]),
            ("positive_modifier_class", positive_classified["positive_modifier_class"]),
            ("entry_adverse_followup_class", entry_classified["entry_adverse_followup_class"]),
            ("entry_target_stop_balance_class", entry_classified["entry_target_stop_balance_class"]),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in family_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_spec_score_class"][row.get("family_spec_score_class")] += 1
    for row in source_rows:
        bucket_counters["source_spec_score_class"][row.get("source_spec_score_class")] += 1
    for row in m15_rows:
        bucket_counters["m15_spec_score_class"][row.get("m15_spec_score_class")] += 1
    for row in m1_rows:
        bucket_counters["m1_spec_score_class"][row.get("m1_spec_score_class")] += 1
    for row in positive_rows:
        bucket_counters["positive_spec_score_class"][row.get("positive_spec_score_class")] += 1
    for row in entry_rows:
        bucket_counters["entry_adverse_spec_score_class"][row.get("entry_adverse_spec_score_class")] += 1
    for row in binding_rows:
        bucket_counters["binding_preserve_status"][row.get("binding_preserve_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-ROUTER-APP-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-ROUTER-APP-QUESTION-001",
            "question": "Which branches now have a family-specific router score versus a no-scalar binding?",
            "answer_route": "Use router_application_score, router_application_score_class, and branch_router_application_class.",
        },
        {
            "question_id": "OHLC-GTOS-ROUTER-APP-QUESTION-002",
            "question": "Which source rows should be cost-capped, avoided, or split by low/high stress bounds?",
            "answer_route": "Use source_spec_score_class, computed_cost_sensitivity_span, and source_spec_action.",
        },
        {
            "question_id": "OHLC-GTOS-ROUTER-APP-QUESTION-003",
            "question": "Which M15 interval rows are target-first challengers, stop-first avoid/redesign rows, or bounds routers?",
            "answer_route": "Use m15_spec_score_class, interval bounds, and exact_chronology_claim=false.",
        },
        {
            "question_id": "OHLC-GTOS-ROUTER-APP-QUESTION-004",
            "question": "Which M1 rows are support-stable versus support/branch conflict half-step splits?",
            "answer_route": "Use support_adjusted_midpoint, m1_spec_score_class, and support/branch sign classes.",
        },
        {
            "question_id": "OHLC-GTOS-ROUTER-APP-QUESTION-005",
            "question": "Which positive challenger rows survive control/concentration penalties as replay specs?",
            "answer_route": "Use positive_adjusted_lower, positive_adjusted_midpoint, and positive_modifier_penalty.",
        },
        {
            "question_id": "OHLC-GTOS-ROUTER-APP-QUESTION-006",
            "question": "Which entry/adverse branches are dominated by stop-first/no-fill pressure and need redesign?",
            "answer_route": "Use target/stop/no-fill rates and redesign_pressure_score.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "not_completion": True,
                "source_manifest_hash": manifest_hash,
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ROUTER_APPLICATION_SCORING_SPEC",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_followup_rows": len(branch_rows_in),
            "input_family_action_followup_rows": len(action_rows_in),
            "input_source_router_followup_rows": len(source_rows_in),
            "input_m15_followup_rows": len(m15_rows_in),
            "input_m1_followup_rows": len(m1_rows_in),
            "input_positive_followup_rows": len(positive_rows_in),
            "input_entry_adverse_followup_rows": len(entry_rows_in),
            "input_binding_preserve_rows": len(binding_rows_in),
            "input_full_outcome_branch_rows": len(full_rows_in),
            "branch_router_application_rows": len(branch_rows),
            "family_spec_rows": len(family_rows),
            "source_spec_rows": len(source_rows),
            "m15_spec_rows": len(m15_rows),
            "m1_spec_rows": len(m1_rows),
            "positive_spec_rows": len(positive_rows),
            "entry_adverse_spec_rows": len(entry_rows),
            "binding_preserve_spec_rows": len(binding_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_followup_counts": followup_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_denominator_preserved": len(branch_rows) == 386,
            "family_spec_rows_per_branch": 5,
            "source_scope": len(source_rows),
            "m15_scope": len(m15_rows),
            "m1_scope": len(m1_rows),
            "positive_scope": len(positive_rows),
            "entry_adverse_scope": len(entry_rows),
            "binding_scope": len(binding_rows),
            "router_modules_hashed": 5,
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_SPEC_LEDGER, family_rows),
        (SOURCE_SPEC_LEDGER, source_rows),
        (M15_SPEC_LEDGER, m15_rows),
        (M1_SPEC_LEDGER, m1_rows),
        (POSITIVE_SPEC_LEDGER, positive_rows),
        (ENTRY_ADVERSE_SPEC_LEDGER, entry_rows),
        (BINDING_SPEC_LEDGER, binding_rows),
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
