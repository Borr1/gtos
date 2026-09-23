#!/usr/bin/env python3
"""Run prequential research replay over Phase 3 truth-layer rows.

The strategy receives only an as-of observation projection. Scorer-only future
fields are attached after the strategy decision is locked. This is research-only
tooling and cannot emit an alpha promotion verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_truth_layer_controlled_hypotheses import (
    _as_float,
    _markdown_cell,
    _parse_datetime,
    _population_inclusion,
    _row_cohort_key,
    find_latest_input,
    iter_jsonl,
)


SCHEMA_VERSION = "truth_layer_prequential_replay_summary_v1"
DEFAULT_LAB_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_REPLAY_RESEARCH_LAB_SPEC_V1.json"
)
DEFAULT_STRATEGY_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_REPLAY_STRATEGY_PRIMARY_COHORTS_V1.json"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "truth_layer/prequential_replay"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_REPLAY_RESEARCH_LAB_REPORT_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
SUPPORTED_STRATEGIES = {"cohort_filter_v1", "field_rules_v1"}


def run_prequential_replay(
    *,
    input_path: str | Path,
    lab_spec_path: str | Path = DEFAULT_LAB_SPEC_PATH,
    strategy_spec_path: str | Path = DEFAULT_STRATEGY_SPEC_PATH,
    max_rows: int | None = None,
) -> dict[str, Any]:
    lab_spec = load_lab_spec(lab_spec_path)
    strategy_spec = load_strategy_spec(strategy_spec_path)
    observation_fields = observation_schema_fields(lab_spec)
    validate_strategy_references(strategy_spec, observation_fields)

    rows = list(iter_jsonl(input_path))
    order_diagnostics = input_order_diagnostics(rows, lab_spec)
    sorted_rows = sort_rows_for_replay(rows, lab_spec)
    if max_rows is not None:
        sorted_rows = sorted_rows[:max_rows]

    scorer = new_score_state()
    duplicate_keys = 0
    keys_seen: set[str] = set()
    invalid_clock_rows = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0
    external_asof_violations = 0
    forbidden_exposure_violations = 0
    decisions = Counter()
    decision_reasons = Counter()

    for replay_index, row in enumerate(sorted_rows, start=1):
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in keys_seen:
                duplicate_keys += 1
            keys_seen.add(key)
        if _parse_datetime(row.get(clock_field(lab_spec))) is None:
            invalid_clock_rows += 1
        if row.get("ai_call_attempted"):
            ai_attempted_rows += 1
        ai_call_count_sum += int(row.get("ai_call_count") or 0)
        if external_snapshot_after_candle(row):
            external_asof_violations += 1

        observation = project_observation(row, lab_spec)
        forbidden_exposure_violations += len(
            forbidden_observation_fields(observation, lab_spec)
        )
        decision = decide(strategy_spec, observation)
        action = str(decision.get("action") or "SKIP").upper()
        reason = str(decision.get("reason") or "unspecified")
        decisions[action] += 1
        decision_reasons[reason] += 1
        if action == "TAKE":
            add_scored_action(
                scorer,
                row=row,
                observation=observation,
                scoring_spec=lab_spec.get("scoring") or {},
                replay_index=replay_index,
            )

    integrity = integrity_summary(
        duplicate_keys=duplicate_keys,
        invalid_clock_rows=invalid_clock_rows,
        forbidden_exposure_violations=forbidden_exposure_violations,
        ai_attempted_rows=ai_attempted_rows,
        ai_call_count_sum=ai_call_count_sum,
        external_asof_violations=external_asof_violations,
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now().isoformat(),
        "input_jsonl": str(Path(input_path)),
        "input_sha256": sha256_file(input_path),
        "lab_spec_path": str(Path(lab_spec_path)),
        "lab_spec_sha256": sha256_file(lab_spec_path),
        "strategy_spec_path": str(Path(strategy_spec_path)),
        "strategy_spec_sha256": sha256_file(strategy_spec_path),
        "code_commit": git_commit_or_unknown(),
        "run_mode": strategy_spec.get("run_mode"),
        "evidence_class": strategy_spec.get("evidence_class"),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": (
            "Prequential historical replay does not compute DSR, PBO, or effective_N, "
            "and this strategy was not frozen before untouched future data."
        ),
        "rows_loaded": len(rows),
        "rows_replayed": len(sorted_rows),
        "unique_opportunity_keys": len(keys_seen),
        "duplicate_opportunity_keys": duplicate_keys,
        "invalid_clock_rows": invalid_clock_rows,
        "input_order_diagnostics": order_diagnostics,
        "external_asof_violations": external_asof_violations,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "forbidden_exposure_violations": forbidden_exposure_violations,
        "observation_schema": {
            "field_count": len(observation_fields),
            "fields": sorted(observation_fields),
            "forbidden_prefixes": forbidden_prefixes(lab_spec),
        },
        "strategy": strategy_summary(strategy_spec),
        "decision_counts": dict(sorted(decisions.items())),
        "decision_reasons": dict(sorted(decision_reasons.items())),
        "score": finalize_score(scorer),
        "integrity": integrity,
        "interpretation": [
            "This is live-like in the decision/information-flow sense: one observation is revealed, then a decision is locked, then outcome is scored.",
            "It is still historical same-dataset evidence unless paired with a predeclared untouched split or future prospective rows.",
            "No live trading logic, prompt, risk, execution, or production configuration was changed.",
        ],
    }
    return summary


def load_lab_spec(path: str | Path = DEFAULT_LAB_SPEC_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "truth_layer_historical_replay_lab_spec_v1":
        raise ValueError(f"unsupported replay lab schema: {payload.get('schema_version')!r}")
    if payload.get("promotion_verdict_allowed") is not False:
        raise ValueError("historical replay lab spec must set promotion_verdict_allowed=false")
    return payload


def load_strategy_spec(path: str | Path = DEFAULT_STRATEGY_SPEC_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "truth_layer_prequential_strategy_v1":
        raise ValueError(f"unsupported strategy schema: {payload.get('schema_version')!r}")
    if payload.get("promotion_verdict_allowed") is not False:
        raise ValueError("prequential strategy spec must set promotion_verdict_allowed=false")
    strategy_type = str(payload.get("strategy_type") or "")
    if strategy_type not in SUPPORTED_STRATEGIES:
        raise ValueError(f"unsupported strategy_type: {strategy_type!r}")
    return payload


def observation_schema_fields(lab_spec: Mapping[str, Any]) -> set[str]:
    projection = lab_spec.get("observation_projection") or {}
    fields = {str(field) for field in projection.get("allowed_direct_fields") or []}
    fields.update(str(field) for field in (projection.get("safe_aliases") or {}).keys())
    return fields


def project_observation(row: Mapping[str, Any], lab_spec: Mapping[str, Any]) -> dict[str, Any]:
    projection = lab_spec.get("observation_projection") or {}
    observation = {
        str(field): row.get(str(field))
        for field in projection.get("allowed_direct_fields") or []
    }
    aliases = projection.get("safe_aliases") or {}
    for alias in aliases:
        alias = str(alias)
        builder = ALIAS_BUILDERS.get(alias)
        if builder is None:
            raise ValueError(f"unsupported safe alias: {alias!r}")
        observation[alias] = builder(row)
    return observation


def validate_strategy_references(
    strategy_spec: Mapping[str, Any],
    observation_fields: set[str],
) -> None:
    strategy_type = str(strategy_spec.get("strategy_type") or "")
    if strategy_type == "cohort_filter_v1":
        if "cohort_key" not in observation_fields:
            raise ValueError("cohort_filter_v1 requires cohort_key in observation schema")
        if not strategy_spec.get("cohort_keys"):
            raise ValueError("cohort_filter_v1 requires non-empty cohort_keys")
        return
    if strategy_type == "field_rules_v1":
        rules = list(strategy_spec.get("rules") or [])
        if not rules:
            raise ValueError("field_rules_v1 requires non-empty rules")
        for rule in rules:
            field = str(rule.get("field") or "")
            if field not in observation_fields:
                raise ValueError(f"strategy references unavailable observation field: {field!r}")
        return
    raise ValueError(f"unsupported strategy_type: {strategy_type!r}")


def decide(strategy_spec: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, str]:
    strategy_type = str(strategy_spec.get("strategy_type") or "")
    policy = strategy_spec.get("decision_policy") or {}
    if strategy_type == "cohort_filter_v1":
        cohort_keys = {str(key) for key in strategy_spec.get("cohort_keys") or []}
        if str(observation.get("cohort_key") or "") in cohort_keys:
            return {
                "action": str(policy.get("match_action") or "TAKE"),
                "reason": "cohort_match",
            }
        return {
            "action": str(policy.get("non_match_action") or "SKIP"),
            "reason": "cohort_non_match",
        }
    if strategy_type == "field_rules_v1":
        rules = list(strategy_spec.get("rules") or [])
        match_policy = str(strategy_spec.get("match_policy") or "all").lower()
        results = [evaluate_rule(rule, observation) for rule in rules]
        matched = any(results) if match_policy == "any" else all(results)
        if matched:
            return {
                "action": str(policy.get("match_action") or "TAKE"),
                "reason": "field_rules_match",
            }
        return {
            "action": str(policy.get("non_match_action") or "SKIP"),
            "reason": "field_rules_non_match",
        }
    raise ValueError(f"unsupported strategy_type: {strategy_type!r}")


def evaluate_rule(rule: Mapping[str, Any], observation: Mapping[str, Any]) -> bool:
    field = str(rule.get("field") or "")
    op = str(rule.get("op") or "eq").lower()
    expected = rule.get("value")
    actual = observation.get(field)
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in set(expected or [])
    if op == "not_in":
        return actual not in set(expected or [])
    if op == "exists":
        return actual not in (None, "")
    if op == "not_exists":
        return actual in (None, "")
    if op == "contains":
        return str(expected) in str(actual or "")
    if op == "startswith":
        return str(actual or "").startswith(str(expected))
    if op in {"gt", "gte", "lt", "lte"}:
        return compare_numeric(actual, expected, op)
    raise ValueError(f"unsupported rule op: {op!r}")


def compare_numeric(actual: Any, expected: Any, op: str) -> bool:
    left = _as_float(actual)
    right = _as_float(expected)
    if left is None or right is None:
        return False
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    raise ValueError(f"unsupported numeric op: {op!r}")


def new_score_state() -> dict[str, Any]:
    return {
        "actions_taken": 0,
        "action_outcomes": Counter(),
        "scoring_population_actions": 0,
        "scoring_exclusions": Counter(),
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "by_cohort": defaultdict(new_cohort_state),
        "by_month": defaultdict(new_period_state),
        "first_actions": [],
    }


def new_cohort_state() -> dict[str, Any]:
    return {
        "actions_taken": 0,
        "population_actions": 0,
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "outcomes": Counter(),
    }


def new_period_state() -> dict[str, Any]:
    return {
        "actions_taken": 0,
        "resolved_r_n": 0,
        "sum_r": 0.0,
    }


def add_scored_action(
    state: dict[str, Any],
    *,
    row: Mapping[str, Any],
    observation: Mapping[str, Any],
    scoring_spec: Mapping[str, Any],
    replay_index: int,
) -> None:
    state["actions_taken"] += 1
    outcome = str(row.get("truth_outcome") or "UNKNOWN")
    state["action_outcomes"][outcome] += 1
    cohort_key = str(observation.get("cohort_key") or _row_cohort_key(row))
    cohort = state["by_cohort"][cohort_key]
    cohort["actions_taken"] += 1
    cohort["outcomes"][outcome] += 1
    period = str(row.get("month") or "") or str(row.get("candle_close_utc") or "")[:7]
    state["by_month"][period]["actions_taken"] += 1

    if len(state["first_actions"]) < 10:
        state["first_actions"].append(
            {
                "replay_index": replay_index,
                "candle_close_utc": row.get("candle_close_utc"),
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "cohort_key": cohort_key,
                "truth_outcome": outcome,
            }
        )

    included, reasons = scoring_inclusion(row, scoring_spec)
    if not included:
        for reason in reasons:
            state["scoring_exclusions"][reason] += 1
        return

    state["scoring_population_actions"] += 1
    cohort["population_actions"] += 1
    resolved_outcomes = set(scoring_spec.get("resolved_outcomes") or RESOLVED_OUTCOMES)
    if outcome not in resolved_outcomes:
        return
    realized = _as_float(row.get("truth_realized_r"))
    if realized is None:
        return
    state["resolved_r_n"] += 1
    state["sum_r"] += realized
    if realized > 0:
        state["wins"] += 1
    cohort["resolved_r_n"] += 1
    cohort["sum_r"] += realized
    if realized > 0:
        cohort["wins"] += 1
    state["by_month"][period]["resolved_r_n"] += 1
    state["by_month"][period]["sum_r"] += realized


def scoring_inclusion(
    row: Mapping[str, Any],
    scoring_spec: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    population = {
        "setup_only": scoring_spec.get("setup_only", True),
        "truth_confidences": scoring_spec.get("truth_confidences") or [],
        "exclude_truth_outcomes": scoring_spec.get("exclude_truth_outcomes") or [],
        "require_resolution_safe": scoring_spec.get("require_resolution_safe", False),
        "primary_resolved_outcomes": scoring_spec.get("resolved_outcomes") or list(RESOLVED_OUTCOMES),
    }
    return _population_inclusion(row, population)


def finalize_score(state: Mapping[str, Any]) -> dict[str, Any]:
    actions = int(state.get("actions_taken") or 0)
    resolved = int(state.get("resolved_r_n") or 0)
    sum_r = float(state.get("sum_r") or 0.0)
    return {
        "actions_taken": actions,
        "scoring_population_actions": int(state.get("scoring_population_actions") or 0),
        "resolved_r_n": resolved,
        "sum_r": round(sum_r, 6),
        "mean_r": round(sum_r / resolved, 6) if resolved else None,
        "win_rate": round(float(state.get("wins") or 0) / resolved, 6) if resolved else None,
        "action_outcomes": dict(sorted((state.get("action_outcomes") or {}).items())),
        "scoring_exclusions": dict(sorted((state.get("scoring_exclusions") or {}).items())),
        "cohort_scores": cohort_rows(state.get("by_cohort") or {}),
        "period_scores": period_rows(state.get("by_month") or {}),
        "first_actions": list(state.get("first_actions") or []),
    }


def cohort_rows(states: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cohort_key, state in sorted(states.items()):
        resolved = int(state.get("resolved_r_n") or 0)
        sum_r = float(state.get("sum_r") or 0.0)
        rows.append(
            {
                "cohort_key": cohort_key,
                "actions_taken": int(state.get("actions_taken") or 0),
                "population_actions": int(state.get("population_actions") or 0),
                "resolved_r_n": resolved,
                "sum_r": round(sum_r, 6),
                "mean_r": round(sum_r / resolved, 6) if resolved else None,
                "win_rate": round(float(state.get("wins") or 0) / resolved, 6) if resolved else None,
                "outcomes": dict(sorted((state.get("outcomes") or {}).items())),
            }
        )
    return rows


def period_rows(states: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period, state in sorted(states.items()):
        resolved = int(state.get("resolved_r_n") or 0)
        sum_r = float(state.get("sum_r") or 0.0)
        rows.append(
            {
                "period": period,
                "actions_taken": int(state.get("actions_taken") or 0),
                "resolved_r_n": resolved,
                "sum_r": round(sum_r, 6),
                "mean_r": round(sum_r / resolved, 6) if resolved else None,
            }
        )
    return rows


def forbidden_observation_fields(
    observation: Mapping[str, Any],
    lab_spec: Mapping[str, Any],
) -> list[str]:
    forbidden_fields = set(
        str(field)
        for field in ((lab_spec.get("observation_projection") or {}).get("forbidden_strategy_fields") or [])
    )
    prefixes = forbidden_prefixes(lab_spec)
    violations: list[str] = []
    for field in observation:
        if field in forbidden_fields or any(str(field).startswith(prefix) for prefix in prefixes):
            violations.append(str(field))
    return violations


def forbidden_prefixes(lab_spec: Mapping[str, Any]) -> list[str]:
    projection = lab_spec.get("observation_projection") or {}
    return [str(prefix) for prefix in projection.get("forbidden_strategy_prefixes") or []]


def input_order_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    lab_spec: Mapping[str, Any],
) -> dict[str, Any]:
    regressions = 0
    previous: tuple[datetime, str] | None = None
    first_clock = None
    last_clock = None
    field = clock_field(lab_spec)
    for row in rows:
        parsed = _parse_datetime(row.get(field))
        if parsed is None:
            continue
        key = str(row.get("opportunity_key") or "")
        current = (parsed, key)
        if previous is not None and current < previous:
            regressions += 1
        previous = current
        first_clock = first_clock or parsed.isoformat()
        last_clock = parsed.isoformat()
    return {
        "clock_field": field,
        "sort_before_replay": bool((lab_spec.get("replay_clock") or {}).get("sort_before_replay", True)),
        "input_order_clock_regressions": regressions,
        "input_first_clock": first_clock,
        "input_last_clock": last_clock,
    }


def sort_rows_for_replay(
    rows: Sequence[Mapping[str, Any]],
    lab_spec: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    if not (lab_spec.get("replay_clock") or {}).get("sort_before_replay", True):
        return list(rows)
    field = clock_field(lab_spec)
    return sorted(
        rows,
        key=lambda row: (
            _parse_datetime(row.get(field)) or datetime.max.replace(tzinfo=timezone.utc),
            str(row.get("opportunity_key") or ""),
        ),
    )


def clock_field(lab_spec: Mapping[str, Any]) -> str:
    return str(((lab_spec.get("replay_clock") or {}).get("field")) or "candle_close_utc")


def external_snapshot_after_candle(row: Mapping[str, Any]) -> bool:
    snapshot = _parse_datetime(row.get("external_snapshot_as_of_utc"))
    candle = _parse_datetime(row.get("candle_close_utc"))
    return snapshot is not None and candle is not None and snapshot > candle


def integrity_summary(**counts: int) -> dict[str, Any]:
    hard_failures = {
        key: value
        for key, value in counts.items()
        if value
        and key
        in {
            "duplicate_keys",
            "invalid_clock_rows",
            "forbidden_exposure_violations",
            "ai_attempted_rows",
            "ai_call_count_sum",
            "external_asof_violations",
        }
    }
    return {
        "clean_for_controlled_replay": not hard_failures,
        "status": "PASS" if not hard_failures else "BLOCKED",
        "blocking_counts": hard_failures,
    }


def strategy_summary(strategy_spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "strategy_id": strategy_spec.get("strategy_id"),
        "strategy_type": strategy_spec.get("strategy_type"),
        "run_mode": strategy_spec.get("run_mode"),
        "evidence_class": strategy_spec.get("evidence_class"),
        "cohort_keys": strategy_spec.get("cohort_keys"),
        "match_policy": strategy_spec.get("match_policy"),
        "rule_count": len(strategy_spec.get("rules") or []),
        "promotion_verdict_allowed": strategy_spec.get("promotion_verdict_allowed"),
    }


def render_report(summary: Mapping[str, Any]) -> str:
    score = summary.get("score") or {}
    lines = [
        "# Phase 3 Historical Replay Research Lab Report",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Input:** `{summary.get('input_jsonl')}`",
        f"**Lab spec:** `{summary.get('lab_spec_path')}`",
        f"**Strategy spec:** `{summary.get('strategy_spec_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- Replay is prequential: observation first, strategy decision second, scorer-only outcome third.",
        "- This run is historical same-dataset evidence unless paired with a predeclared untouched split or prospective rows.",
        "- DSR, PBO, and effective_N are not computed here.",
        "",
        "## Reproducibility",
        "",
        markdown_table(
            [
                {
                    "input_sha256": summary.get("input_sha256"),
                    "lab_spec_sha256": summary.get("lab_spec_sha256"),
                    "strategy_spec_sha256": summary.get("strategy_spec_sha256"),
                    "code_commit": summary.get("code_commit"),
                    "run_mode": summary.get("run_mode"),
                    "evidence_class": summary.get("evidence_class"),
                }
            ]
        ),
        "",
        "## Guardrails",
        "",
        markdown_table(
            [
                {
                    "rows_loaded": summary.get("rows_loaded"),
                    "rows_replayed": summary.get("rows_replayed"),
                    "duplicate_opportunity_keys": summary.get("duplicate_opportunity_keys"),
                    "invalid_clock_rows": summary.get("invalid_clock_rows"),
                    "forbidden_exposure_violations": summary.get("forbidden_exposure_violations"),
                    "external_asof_violations": summary.get("external_asof_violations"),
                    "ai_attempted_rows": summary.get("ai_attempted_rows"),
                    "ai_call_count_sum": summary.get("ai_call_count_sum"),
                    "integrity_status": (summary.get("integrity") or {}).get("status"),
                }
            ]
        ),
        "",
        "## Decision Counts",
        "",
        markdown_table([summary.get("decision_counts") or {}]),
        "",
        "## Score",
        "",
        markdown_table(
            [
                {
                    "actions_taken": score.get("actions_taken"),
                    "scoring_population_actions": score.get("scoring_population_actions"),
                    "resolved_r_n": score.get("resolved_r_n"),
                    "sum_r": score.get("sum_r"),
                    "mean_r": score.get("mean_r"),
                    "win_rate": score.get("win_rate"),
                }
            ]
        ),
        "",
        "## Action Outcomes",
        "",
        markdown_table([score.get("action_outcomes") or {}]),
        "",
        "## Scoring Exclusions",
        "",
        markdown_table([score.get("scoring_exclusions") or {}]),
        "",
        "## Cohort Scores",
        "",
        markdown_table(score.get("cohort_scores") or []),
        "",
        "## Period Scores",
        "",
        markdown_table(score.get("period_scores") or []),
        "",
        "## Interpretation",
        "",
        "- This validates the replay boundary: the strategy can select cohorts without receiving outcome/refinement fields.",
        "- Positive historical replay results remain diagnostic because these cohorts were discovered from the same broad dataset.",
        "- The same harness can now be used for broader controlled strategy experiments while preserving trial-budget language.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"truth_layer_prequential_replay_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(str(key))
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit_or_unknown() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    commit = result.stdout.strip() or "unknown"
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return commit
    return f"{commit}+dirty" if status.stdout.strip() else commit


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Truth-layer JSONL. Defaults to latest truth-layer artifact.")
    parser.add_argument("--lab-spec-path", default=DEFAULT_LAB_SPEC_PATH)
    parser.add_argument("--strategy-spec-path", default=DEFAULT_STRATEGY_SPEC_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input) if args.input else find_latest_input()
    summary = run_prequential_replay(
        input_path=input_path,
        lab_spec_path=args.lab_spec_path,
        strategy_spec_path=args.strategy_spec_path,
        max_rows=args.max_rows,
    )
    if args.write:
        summary_path, report_path = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        summary = dict(summary)
        summary["output_summary"] = str(summary_path)
        summary["report_path"] = str(report_path)
    if args.quiet:
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "rows_replayed": summary.get("rows_replayed"),
                    "actions_taken": (summary.get("score") or {}).get("actions_taken"),
                    "resolved_r_n": (summary.get("score") or {}).get("resolved_r_n"),
                    "mean_r": (summary.get("score") or {}).get("mean_r"),
                    "integrity_status": (summary.get("integrity") or {}).get("status"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


ALIAS_BUILDERS: dict[str, Callable[[Mapping[str, Any]], Any]] = {
    "cohort_key": _row_cohort_key,
    "regime_key": lambda row: row.get("truth_regime"),
    "bias_stack": lambda row: row.get("truth_bias_stack"),
}


if __name__ == "__main__":
    raise SystemExit(main())
