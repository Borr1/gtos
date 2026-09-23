#!/usr/bin/env python3
"""Compare the bounded B7.5 hostile/non-hostile causal risk-expression pair.

This analyzer is deliberately standalone and read-only with respect to replay
authority.  It streams the bound ledgers, filters every comparator to its exact
declared day, materializes compact identity snapshots, and publishes a
completion-manifest-last evidence set.  Importing this module performs no file
reads or writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping


ROUTE = Path(__file__).resolve().parent
SUMMARY_SCHEMA = "gtos.b7_5.causal_risk_pair_comparison.summary.v2"
IDENTITY_SCHEMA = "gtos.b7_5.causal_risk_pair_comparison.identity_transition.v1"
COHORT_SCHEMA = "gtos.b7_5.causal_risk_pair_comparison.pressure_cap_cohort.v2"
MISSED_SCHEMA = "gtos.b7_5.causal_risk_pair_comparison.missed_opportunity.v1"
MANIFEST_SCHEMA = "gtos.b7_5.causal_risk_pair_comparison.output_manifest.v2"
PROFILE = "repaired_package_conversion_v3"
DEFAULT_OUTPUT_PREFIX = "B7_5_CAUSAL_STOP_HAZARD_RISK_EXPRESSION_PAIRED"
FLOAT_TOLERANCE = 1e-8

IDENTITY_KEY_FIELDS = (
    "canonical_replay_candidate_instance_key",
    "candidate_instance_parity_key",
    "source_bound_replay_candidate_instance_key",
)
PROJECTION_WINDOW_DAY_FIELDS = (
    "projection_source_window_date",
    "source_window_date",
    "replay_source_window_date",
    "candidate_source_window_date",
)
TRADING_DAY_FIELDS = (
    "trading_day",
    "replay_trading_day",
    "decision_day",
)
DECISION_TIME_FIELDS = (
    "decision_time_utc",
    "decision_time",
)
DAY_FALLBACK_FIELDS = (
    "order_time_utc",
    "created_time_utc",
    "event_time_utc",
    "asof_utc",
    "timestamp_utc",
    "entry_time_utc",
    "close_time_utc",
)


class ArtifactError(RuntimeError):
    """Raised when an input or output artifact cannot be trusted."""


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fnum(value: Any) -> float:
    parsed = number(value)
    return parsed if parsed is not None else 0.0


def rounded(value: float) -> float:
    return round(value, 8)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def iso_day(value: Any) -> str:
    candidate = str(value or "").strip()[:10]
    if (
        len(candidate) == 10
        and candidate[4] == "-"
        and candidate[7] == "-"
        and candidate[:4].isdigit()
        and candidate[5:7].isdigit()
        and candidate[8:10].isdigit()
    ):
        return candidate
    return ""


def row_day(row: Mapping[str, Any]) -> str:
    # Pair scope is the harness/source window, not the wall-clock timestamp of
    # a cross-midnight candidate identity.  Projection rows serialize that
    # authority explicitly; terminal ledgers serialize it as trading_day.
    for field_name in PROJECTION_WINDOW_DAY_FIELDS:
        day = iso_day(row.get(field_name))
        if day:
            return day
    for field_name in TRADING_DAY_FIELDS:
        day = iso_day(row.get(field_name))
        if day:
            return day
    # Older/fallback rows may lack harness-day fields.  Only then use identity
    # and decision timestamps, followed by generic event/source times.
    for field_name in IDENTITY_KEY_FIELDS:
        value = str(row.get(field_name) or "").strip()
        if "@@" in value:
            day = iso_day(value.rsplit("@@", 1)[1])
            if day:
                return day
    for field_name in DECISION_TIME_FIELDS:
        day = iso_day(row.get(field_name))
        if day:
            return day
    for field_name in DAY_FALLBACK_FIELDS:
        value = str(row.get(field_name) or "").strip()
        day = iso_day(value)
        if day:
            return day
    return ""


def identity_key(row: Mapping[str, Any]) -> str:
    for field_name in IDENTITY_KEY_FIELDS:
        value = str(row.get(field_name) or "").strip()
        if value:
            return value
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc") or row.get("decision_time") or ""
    ).strip()
    if candidate_id or decision_time:
        return f"{candidate_id}@@{decision_time}"
    return ""


def read_json_object(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.is_file():
        raise ArtifactError(f"missing_json_artifact:{path}")
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"invalid_json_artifact:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise ArtifactError(f"json_artifact_not_object:{path}")
    return payload, {
        "path": str(path),
        "present": True,
        "byte_count": len(raw),
        "sha256": sha256_bytes(raw),
    }


def scan_jsonl(
    path: Path,
    *,
    day: str,
    visit: Callable[[dict[str, Any], int], None],
) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": str(path),
            "present": False,
            "byte_count": 0,
            "sha256": None,
            "total_rows": 0,
            "selected_day_rows": 0,
            "outside_day_rows": 0,
        }
    digest = hashlib.sha256()
    total_rows = 0
    selected_rows = 0
    outside_rows = 0
    byte_count = 0
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            digest.update(raw_line)
            byte_count += len(raw_line)
            if not raw_line.strip():
                continue
            total_rows += 1
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ArtifactError(f"invalid_jsonl:{path}:{line_number}:{exc}") from exc
            if not isinstance(row, dict):
                raise ArtifactError(f"jsonl_row_not_object:{path}:{line_number}")
            if row_day(row) != day:
                outside_rows += 1
                continue
            selected_rows += 1
            visit(row, line_number)
    return {
        "path": str(path),
        "present": True,
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "total_rows": total_rows,
        "selected_day_rows": selected_rows,
        "outside_day_rows": outside_rows,
    }


def artifact_path(root: Path, prefix: str, suffix: str) -> Path:
    return root / f"{prefix}_{suffix}"


def projection_path(root: Path, prefix: str) -> Path:
    tag = prefix.removeprefix("BROAD_LIVE_AS_IF_REPLAY_")
    return root / f"CANDIDATE_INSTANCE_PARITY_PROJECTION_{tag}_LEDGER.jsonl"


def compact_projection_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "identity_key": identity_key(row),
        "candidate_id": row.get("candidate_id"),
        "decision_time_utc": row.get("decision_time_utc"),
        "symbol": row.get("symbol"),
        "side": row.get("side") or row.get("direction"),
        "candidate_present": row.get("candidate_present") is not False,
        "scorecard_present": truthy(row.get("scorecard_present")),
        "scheduler_selected": truthy(row.get("scheduler_selected")),
        "order_present": truthy(row.get("order_present")),
        "trade_present": truthy(row.get("trade_present")),
        "missed_present": truthy(row.get("missed_present")),
        "effective_selector_action": row.get("effective_selector_action"),
        "effective_selector_reason": row.get("effective_selector_reason"),
        "scheduler_rank": row.get("scheduler_rank"),
        "risk_behavior": row.get("risk_behavior"),
        "risk_expression_ladder_tier": row.get("risk_expression_ladder_tier"),
        "risk_finalizer_action": row.get("risk_finalizer_action"),
        "risk_finalizer_reason": row.get("risk_finalizer_reason"),
        "order_status": row.get("order_status"),
        "terminal_fill_status": row.get("terminal_fill_status"),
        "terminal_outcome": row.get("terminal_outcome"),
        "lifecycle_action": row.get("lifecycle_action"),
        "lifecycle_reason": row.get("lifecycle_reason"),
        "miss_reason": row.get("miss_reason"),
        "exact_deviation_stage": row.get("exact_deviation_stage"),
        "exact_deviation_reason": row.get("exact_deviation_reason"),
        "package_order_executable_blocker_class": row.get(
            "package_order_executable_blocker_class"
        ),
        "package_order_executable_blocker_reason": row.get(
            "package_order_executable_blocker_reason"
        ),
        "actual_r": row.get("actual_r"),
    }


@dataclass
class ProjectionData:
    path: Path
    scan: dict[str, Any]
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    duplicate_keys: Counter[str] = field(default_factory=Counter)
    missing_identity_rows: int = 0
    stage_counts: Counter[str] = field(default_factory=Counter)

    @property
    def available(self) -> bool:
        return bool(self.scan.get("present"))


def load_projection(path: Path, day: str) -> ProjectionData:
    rows: dict[str, dict[str, Any]] = {}
    duplicate_keys: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    missing_identity_rows = 0

    def visit(row: dict[str, Any], _line_number: int) -> None:
        nonlocal missing_identity_rows
        key = identity_key(row)
        if not key:
            missing_identity_rows += 1
            return
        if key in rows:
            duplicate_keys[key] += 1
            return
        snapshot = compact_projection_row(row)
        rows[key] = snapshot
        stage_counts["candidate"] += 1
        for stage in (
            "scorecard_present",
            "scheduler_selected",
            "order_present",
            "trade_present",
            "missed_present",
        ):
            if snapshot[stage]:
                stage_counts[stage.removesuffix("_present")] += 1

    scan = scan_jsonl(path, day=day, visit=visit)
    return ProjectionData(
        path=path,
        scan=scan,
        rows=rows,
        duplicate_keys=duplicate_keys,
        missing_identity_rows=missing_identity_rows,
        stage_counts=stage_counts,
    )


def trade_net_r(row: Mapping[str, Any]) -> float | None:
    for field_name in ("net_r", "net_proxy_r"):
        value = number(row.get(field_name))
        if value is not None:
            return value
    return None


def risk_tier(row: Mapping[str, Any]) -> str:
    value = str(row.get("risk_expression_ladder_tier") or "").strip().lower()
    if value:
        return value
    ladder = row.get("risk_expression_ladder")
    if isinstance(ladder, Mapping):
        return str(ladder.get("ladder_tier") or "unknown").strip().lower()
    return "unknown"


def trade_rollup(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    scoreable = [
        row
        for row in materialized
        if row.get("terminal_r_scoreable") is not False and trade_net_r(row) is not None
    ]
    unscoreable = [row for row in materialized if row not in scoreable]
    headline = [row for row in scoreable if row.get("headline_result_eligible") is True]
    nets = [trade_net_r(row) or 0.0 for row in scoreable]
    headline_nets = [trade_net_r(row) or 0.0 for row in headline]
    tiers = Counter(risk_tier(row) for row in materialized)
    scoreable_expected_cost = sum(fnum(row.get("expected_cost_r")) for row in scoreable)
    unscoreable_expected_cost = sum(
        fnum(row.get("expected_cost_r")) for row in unscoreable
    )
    final_r = sum(fnum(row.get("final_r")) for row in scoreable)
    net_r = sum(nets)
    source_gap_ok = {"", "source_bound_cost_authority_present"}
    return {
        "physical_trade_rows": len(materialized),
        "physical_scoreable_trade_rows": len(scoreable),
        "physical_unscoreable_trade_rows": len(unscoreable),
        "physical_win_count": sum(value > 0 for value in nets),
        "physical_loss_count": sum(value < 0 for value in nets),
        "physical_flat_count": sum(value == 0 for value in nets),
        "physical_net_r": rounded(net_r),
        "physical_gross_r": rounded(
            sum(fnum(row.get("gross_r")) for row in scoreable)
        ),
        "physical_final_r": rounded(final_r),
        "physical_cash_pnl": rounded(
            sum(fnum(row.get("pnl_cash") or row.get("cash_pnl")) for row in scoreable)
        ),
        "physical_risk_cash": rounded(sum(fnum(row.get("risk_cash")) for row in materialized)),
        "physical_risk_pct": rounded(sum(fnum(row.get("risk_pct")) for row in materialized)),
        "physical_scoreable_expected_cost_r": rounded(scoreable_expected_cost),
        "physical_unscoreable_expected_cost_r": rounded(unscoreable_expected_cost),
        "physical_expected_cost_r": rounded(
            scoreable_expected_cost + unscoreable_expected_cost
        ),
        "physical_full_risk_trade_rows": tiers.get("full", 0),
        "physical_reduced_risk_trade_rows": tiers.get("reduced", 0)
        + tiers.get("open-reduced-risk", 0),
        "physical_risk_ladder_tier_counts": dict(sorted(tiers.items())),
        "headline_trade_rows": len(headline),
        "headline_win_count": sum(value > 0 for value in headline_nets),
        "headline_loss_count": sum(value < 0 for value in headline_nets),
        "headline_flat_count": sum(value == 0 for value in headline_nets),
        "headline_net_r": rounded(sum(headline_nets)),
        "headline_gross_r": rounded(sum(fnum(row.get("gross_r")) for row in headline)),
        "headline_final_r": rounded(sum(fnum(row.get("final_r")) for row in headline)),
        "headline_cash_pnl": rounded(
            sum(fnum(row.get("pnl_cash") or row.get("cash_pnl")) for row in headline)
        ),
        "executed_refused_cost_rows": sum(
            row.get("broker_pretrade_cost_executable") is False for row in materialized
        ),
        "executed_source_gap_rows": sum(
            str(row.get("cost_source_gap_status") or "").strip().lower()
            not in source_gap_ok
            for row in materialized
        ),
        "net_equals_final_less_scoreable_cost": math.isclose(
            net_r,
            final_r - scoreable_expected_cost,
            rel_tol=0.0,
            abs_tol=FLOAT_TOLERANCE,
        ),
        "net_final_cost_delta_r": rounded(net_r - (final_r - scoreable_expected_cost)),
    }


@dataclass
class TradeData:
    path: Path
    scan: dict[str, Any]
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    duplicate_keys: Counter[str] = field(default_factory=Counter)
    missing_identity_rows: int = 0
    rollup: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return bool(self.scan.get("present"))


def load_trades(path: Path, day: str) -> TradeData:
    rows: dict[str, dict[str, Any]] = {}
    duplicate_keys: Counter[str] = Counter()
    missing_identity_rows = 0

    def visit(row: dict[str, Any], _line_number: int) -> None:
        nonlocal missing_identity_rows
        key = identity_key(row)
        if not key:
            missing_identity_rows += 1
            return
        if key in rows:
            duplicate_keys[key] += 1
            return
        rows[key] = row

    scan = scan_jsonl(path, day=day, visit=visit)
    return TradeData(
        path=path,
        scan=scan,
        rows=rows,
        duplicate_keys=duplicate_keys,
        missing_identity_rows=missing_identity_rows,
        rollup=trade_rollup(rows.values()),
    )


def missed_scope_and_r(row: Mapping[str, Any]) -> tuple[str, float | None]:
    status = str(
        row.get("missed_opportunity_r_scoreability_status") or "not_reported"
    ).strip()
    headline_scoreable = bool(
        status == "headline_r_scoreable"
        or row.get("missed_opportunity_headline_r_scoreable") is True
    )
    diagnostic_scoreable = bool(
        status == "diagnostic_opportunity_r_scoreable"
        or row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
    )
    explicit_unscoreable = bool(
        status
        not in {
            "not_reported",
            "headline_r_scoreable",
            "diagnostic_opportunity_r_scoreable",
        }
        and "unscoreable" in status
    )
    if not explicit_unscoreable and headline_scoreable:
        value = number(row.get("net_proxy_r"))
        if value is None:
            value = number(row.get("opportunity_net_proxy_r"))
        return "executable", value
    if not explicit_unscoreable and diagnostic_scoreable:
        return "diagnostic", number(row.get("opportunity_net_proxy_r"))
    if status == "not_reported":
        value = number(row.get("net_proxy_r"))
        if value is not None:
            return "executable", value
    return "unscoreable", None


def blank_missed_metrics() -> dict[str, Any]:
    return {
        "rows": 0,
        "scoreable_rows": 0,
        "unscoreable_rows": 0,
        "missing_r_rows": 0,
        "executable_scoreable_rows": 0,
        "executable_positive_rows": 0,
        "executable_negative_rows": 0,
        "executable_flat_rows": 0,
        "executable_net_r": 0.0,
        "executable_positive_net_r": 0.0,
        "executable_negative_net_r": 0.0,
        "diagnostic_scoreable_rows": 0,
        "diagnostic_positive_rows": 0,
        "diagnostic_negative_rows": 0,
        "diagnostic_flat_rows": 0,
        "diagnostic_net_r": 0.0,
        "diagnostic_positive_net_r": 0.0,
        "diagnostic_negative_net_r": 0.0,
        "suppressed_pressure_materialized_rows": 0,
        "suppressed_pressure_materialization_blocked_rows": 0,
        "suppressed_pressure_materialization_blocked_samples": [],
        "miss_reason_counts": Counter(),
    }


def suppressed_pressure_materialization_state(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    materialized = truthy(
        row.get("stop_hazard_materialization_pressure_score_materialized")
    )
    suppressed_reason = str(
        row.get("stop_hazard_materialization_pressure_suppressed_reason") or ""
    ).strip().lower()
    dominance_applies = truthy(
        row.get("stop_hazard_materialization_requires_reallocation_dominance")
    )
    blocker_reasons = {
        str(row.get("package_replay_order_executable_final_blocker_reason") or "")
        .strip()
        .lower(),
        str(row.get("order_materialization_authority_block_reason") or "")
        .strip()
        .lower(),
        str(row.get("stop_hazard_materialization_dominance_gate_reason") or "")
        .strip()
        .lower(),
    }
    blocked = bool(
        truthy(row.get("stop_hazard_materialization_blocked"))
        or "stop_hazard_materialization_requires_reallocation_dominance"
        in blocker_reasons
    )
    causal_bypass = bool(
        materialized
        and suppressed_reason == "stop_hazard_pressure_requires_base_fragility"
        and dominance_applies
        and blocked
    )
    return {
        "materialized": materialized,
        "suppressed_reason": suppressed_reason or None,
        "dominance_applies": dominance_applies,
        "blocked": blocked,
        "causal_bypass": causal_bypass,
    }


@dataclass
class MissedData:
    path: Path
    scan: dict[str, Any]
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    duplicate_keys: Counter[str] = field(default_factory=Counter)
    missing_identity_rows: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return bool(self.scan.get("present"))


def load_missed(path: Path, day: str) -> MissedData:
    rows: dict[str, dict[str, Any]] = {}
    duplicate_keys: Counter[str] = Counter()
    metrics = blank_missed_metrics()
    missing_identity_rows = 0

    def visit(row: dict[str, Any], _line_number: int) -> None:
        nonlocal missing_identity_rows
        metrics["rows"] += 1
        materialization = suppressed_pressure_materialization_state(row)
        if materialization["materialized"]:
            metrics["suppressed_pressure_materialized_rows"] += 1
        if materialization["causal_bypass"]:
            metrics["suppressed_pressure_materialization_blocked_rows"] += 1
            samples = metrics["suppressed_pressure_materialization_blocked_samples"]
            if len(samples) < 25:
                samples.append(
                    {
                        "identity_key": identity_key(row),
                        "symbol": row.get("symbol"),
                        "side": row.get("side") or row.get("direction"),
                        "miss_reason": row.get("miss_reason"),
                        **materialization,
                    }
                )
        key = identity_key(row)
        if not key:
            missing_identity_rows += 1
        elif key in rows:
            duplicate_keys[key] += 1
        else:
            scope, net_r = missed_scope_and_r(row)
            rows[key] = {
                "identity_key": key,
                "scope": scope,
                "net_r": net_r,
                "miss_reason": row.get("miss_reason"),
                "scoreability_status": row.get(
                    "missed_opportunity_r_scoreability_status"
                ),
            }
        scope, net_r = missed_scope_and_r(row)
        metrics["miss_reason_counts"][str(row.get("miss_reason") or "unknown")] += 1
        if net_r is None:
            metrics["unscoreable_rows"] += 1
            metrics["missing_r_rows"] += 1
            return
        metrics["scoreable_rows"] += 1
        metrics[f"{scope}_scoreable_rows"] += 1
        metrics[f"{scope}_net_r"] += net_r
        if net_r > 0:
            metrics[f"{scope}_positive_rows"] += 1
            metrics[f"{scope}_positive_net_r"] += net_r
        elif net_r < 0:
            metrics[f"{scope}_negative_rows"] += 1
            metrics[f"{scope}_negative_net_r"] += net_r
        else:
            metrics[f"{scope}_flat_rows"] += 1

    scan = scan_jsonl(path, day=day, visit=visit)
    finalized: dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, Counter):
            finalized[key] = dict(sorted(value.items()))
        elif isinstance(value, float):
            finalized[key] = rounded(value)
        else:
            finalized[key] = value
    return MissedData(
        path=path,
        scan=scan,
        rows=rows,
        duplicate_keys=duplicate_keys,
        missing_identity_rows=missing_identity_rows,
        metrics=finalized,
    )


def cap_state(row: Mapping[str, Any]) -> dict[str, Any]:
    nested_gate = row.get("predecision_stop_hazard_guard")
    if not isinstance(nested_gate, Mapping):
        nested_gate = {}
    status = str(
        row.get("predecision_stop_hazard_guard_status")
        or nested_gate.get("status")
        or ""
    ).strip().lower()
    effective_action = str(
        row.get("predecision_stop_hazard_guard_effective_action")
        or nested_gate.get("effective_action")
        or ""
    ).strip().lower()
    configured_action = str(
        row.get("predecision_stop_hazard_guard_configured_action")
        or row.get("predecision_stop_hazard_guard_action")
        or nested_gate.get("configured_action")
        or nested_gate.get("action")
        or ""
    ).strip().lower()
    raw_cap_value = row.get("predecision_stop_hazard_guard_risk_cap_applied")
    if raw_cap_value is None:
        raw_cap_value = nested_gate.get("risk_cap_applied")
    effective_cap_value = row.get("predecision_stop_hazard_guard_effective_cap")
    if effective_cap_value is None:
        effective_cap_value = nested_gate.get("effective_cap")
    raw_cap_applied = truthy(raw_cap_value)
    effective_cap = truthy(effective_cap_value)
    # Mirror the canonical verifier precedence.  A configured action describes
    # what the gate may do, not what it actually did.  In particular, a passed
    # gate with no effective action/cap/block resolves to no_block even when its
    # configured action is cap or block.
    if status == "capped" or raw_cap_applied or effective_cap:
        resolved_action = "cap"
    elif status == "blocked":
        resolved_action = "block"
    elif status == "penalized":
        resolved_action = "penalize"
    elif status in {"passed", "pass", "clear", "allowed", "not_applicable"}:
        resolved_action = effective_action or "no_block"
    else:
        resolved_action = effective_action or configured_action
    cap_applied = bool(
        raw_cap_applied
        or effective_cap
        or status == "capped"
        or resolved_action in {"cap", "capped"}
    )
    unit_risk_atr = number(
        row.get("predecision_stop_hazard_guard_unit_risk_atr")
        if row.get("predecision_stop_hazard_guard_unit_risk_atr") is not None
        else nested_gate.get("unit_risk_atr")
    )
    min_unit_risk_atr = number(
        row.get("predecision_stop_hazard_guard_min_unit_risk_atr")
        if row.get("predecision_stop_hazard_guard_min_unit_risk_atr") is not None
        else nested_gate.get("min_unit_risk_atr")
    )
    base_fragile = bool(
        unit_risk_atr is not None
        and min_unit_risk_atr is not None
        and unit_risk_atr < min_unit_risk_atr
    )
    cap_pct = number(
        row.get("predecision_stop_hazard_guard_risk_cap_pct")
        if row.get("predecision_stop_hazard_guard_risk_cap_pct") is not None
        else nested_gate.get("risk_cap_pct")
    )
    risk_pct = None
    for field_name in (
        "risk_pct",
        "runtime_final_risk_pct",
        "final_approved_risk_pct",
        "approved_risk_pct",
    ):
        risk_pct = number(row.get(field_name))
        if risk_pct is not None:
            break
    return {
        "cap_applied": cap_applied,
        "status": status or None,
        "configured_action": configured_action or None,
        "effective_action": effective_action or None,
        "resolved_action": resolved_action or None,
        "raw_cap_applied": raw_cap_applied,
        "effective_cap": effective_cap,
        "pressure_requires_base_fragility": truthy(
            row.get("predecision_stop_hazard_guard_pressure_requires_base_fragility")
            if row.get("predecision_stop_hazard_guard_pressure_requires_base_fragility")
            is not None
            else nested_gate.get("pressure_requires_base_fragility")
        ),
        "pressure_triggered": truthy(
            row.get("predecision_stop_hazard_guard_pressure_triggered")
            if row.get("predecision_stop_hazard_guard_pressure_triggered") is not None
            else nested_gate.get("pressure_triggered")
        ),
        "unit_risk_atr": unit_risk_atr,
        "min_unit_risk_atr": min_unit_risk_atr,
        "base_fragile": base_fragile,
        "cap_pct": cap_pct,
        "risk_pct": risk_pct,
    }


def cap_violation_reasons(state: Mapping[str, Any]) -> list[str]:
    if not state.get("cap_applied"):
        return []
    reasons: list[str] = []
    if state.get("pressure_requires_base_fragility"):
        if state.get("unit_risk_atr") is None or state.get("min_unit_risk_atr") is None:
            reasons.append("causal_stop_hazard_base_fragility_fields_missing")
        elif not state.get("base_fragile"):
            reasons.append("causal_stop_hazard_cap_without_base_fragility")
        if state.get("pressure_triggered") and not state.get("base_fragile"):
            reasons.append("causal_stop_hazard_pressure_triggered_without_base_fragility")
    else:
        reasons.append("legacy_pressure_only_cap_policy_executed")
    cap_pct = number(state.get("cap_pct"))
    risk_pct = number(state.get("risk_pct"))
    if cap_pct is None or cap_pct <= 0:
        reasons.append("stop_hazard_cap_pct_missing_or_nonpositive")
    if risk_pct is None:
        reasons.append("executed_risk_pct_missing")
    elif cap_pct is not None and cap_pct > 0 and risk_pct > cap_pct + 1e-9:
        reasons.append("executed_risk_pct_exceeds_stop_hazard_cap")
    return reasons


def execution_bound_order(row: Mapping[str, Any]) -> bool:
    order_status = str(row.get("order_status") or "").strip().lower()
    fill_status = str(row.get("fill_status") or "").strip().lower()
    return bool(
        row.get("simulated_trade_id")
        or order_status
        in {"filled", "pending_accepted", "accepted_not_filled_pending_until_expiry"}
        or fill_status.startswith("filled")
    )


def scan_cap_authority(
    order_path: Path,
    trade_data: TradeData,
    day: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    counts: Counter[str] = Counter()
    violations: list[dict[str, Any]] = []
    suppressed_pressure_blocks: list[dict[str, Any]] = []

    def inspect(row: Mapping[str, Any], ledger: str, row_number: int) -> None:
        counts[f"{ledger}_rows"] += 1
        if ledger == "order" and not execution_bound_order(row):
            return
        counts[f"{ledger}_execution_bound_rows"] += 1
        materialization = suppressed_pressure_materialization_state(row)
        if materialization["materialized"]:
            counts[f"{ledger}_suppressed_pressure_materialized_rows"] += 1
        if materialization["causal_bypass"]:
            counts[f"{ledger}_suppressed_pressure_materialization_blocked_rows"] += 1
            if len(suppressed_pressure_blocks) < 25:
                suppressed_pressure_blocks.append(
                    {
                        "ledger": ledger,
                        "row_number": row_number,
                        "identity_key": identity_key(row),
                        "symbol": row.get("symbol"),
                        "side": row.get("side") or row.get("direction"),
                        **materialization,
                    }
                )
        state = cap_state(row)
        if not state["cap_applied"]:
            return
        counts[f"{ledger}_cap_rows"] += 1
        if state["base_fragile"]:
            counts[f"{ledger}_base_fragile_cap_rows"] += 1
        else:
            counts[f"{ledger}_non_base_fragile_cap_rows"] += 1
        reasons = cap_violation_reasons(state)
        if reasons:
            counts[f"{ledger}_bad_cap_rows"] += 1
            if len(violations) < 25:
                violations.append(
                    {
                        "ledger": ledger,
                        "row_number": row_number,
                        "identity_key": identity_key(row),
                        "symbol": row.get("symbol"),
                        "side": row.get("side") or row.get("direction"),
                        **state,
                        "reasons": reasons,
                    }
                )

    order_scan = scan_jsonl(
        order_path,
        day=day,
        visit=lambda row, row_number: inspect(row, "order", row_number),
    )
    for row_number, row in enumerate(trade_data.rows.values(), start=1):
        inspect(row, "trade", row_number)
    return (
        {
            "row_counts": dict(sorted(counts.items())),
            "bad_counts": {
                key: value for key, value in sorted(counts.items()) if "bad_cap" in key
            },
            "sample_bad": violations,
            "suppressed_pressure_materialization_blocked_rows": sum(
                value
                for key, value in counts.items()
                if key.endswith("suppressed_pressure_materialization_blocked_rows")
            ),
            "suppressed_pressure_materialization_blocked_samples": (
                suppressed_pressure_blocks
            ),
        },
        order_scan,
    )


def split_profile_stats(summary: Mapping[str, Any]) -> Mapping[str, Any]:
    rows = summary.get("split_profile_stats")
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if isinstance(row, Mapping) and row.get("profile") == PROFILE:
            return row
    return rows[0] if rows and isinstance(rows[0], Mapping) else {}


def summary_trade_parity(
    summary: Mapping[str, Any], rollup: Mapping[str, Any]
) -> dict[str, Any]:
    stats = split_profile_stats(summary)
    fields = (
        "physical_scoreable_trade_rows",
        "physical_unscoreable_trade_rows",
        "physical_win_count",
        "physical_loss_count",
        "physical_flat_count",
        "physical_net_r",
        "physical_gross_r",
        "physical_final_r",
        "physical_cash_pnl",
        "physical_risk_cash",
        "physical_risk_pct",
        "physical_scoreable_expected_cost_r",
        "physical_unscoreable_expected_cost_r",
        "physical_expected_cost_r",
        "physical_full_risk_trade_rows",
        "physical_reduced_risk_trade_rows",
        "headline_trade_rows",
        "headline_win_count",
        "headline_loss_count",
        "headline_flat_count",
        "headline_net_r",
        "headline_gross_r",
        "headline_final_r",
        "headline_cash_pnl",
    )
    aliases = {"headline_cash_pnl": "cash_pnl"}
    mismatches: list[dict[str, Any]] = []
    for field_name in fields:
        declared_field = (
            field_name
            if field_name in stats
            else aliases.get(field_name)
            if aliases.get(field_name) in stats
            else None
        )
        if declared_field is None:
            mismatches.append(
                {"field": field_name, "reason": "summary_field_missing"}
            )
            continue
        declared = stats.get(declared_field)
        observed = rollup.get(field_name)
        declared_number = number(declared)
        observed_number = number(observed)
        if declared_number is None or observed_number is None:
            equal = declared == observed
        else:
            equal = math.isclose(
                declared_number,
                observed_number,
                rel_tol=0.0,
                abs_tol=FLOAT_TOLERANCE,
            )
        if not equal:
            mismatches.append(
                {
                    "field": field_name,
                    "declared_field": declared_field,
                    "declared": declared,
                    "observed": observed,
                }
            )
    declared_trade_rows = summary.get("trade_rows")
    if declared_trade_rows != rollup.get("physical_trade_rows"):
        mismatches.append(
            {
                "field": "trade_rows",
                "declared": declared_trade_rows,
                "observed": rollup.get("physical_trade_rows"),
            }
        )
    return {
        "status": "exact" if not mismatches else "mismatch",
        "bad_counts": ({"physical_trade_summary_parity_mismatch": len(mismatches)} if mismatches else {}),
        "mismatches": mismatches[:50],
    }


def validate_target_contract(
    summary: Mapping[str, Any],
    *,
    day: str,
    shared_digest: str,
    profile_hash: str,
    source_plan_digest: str,
) -> list[str]:
    issues: list[str] = []
    expected_scalars = {
        "status": "broad_live_as_if_replay_materialized_broker_live_closed",
        "date_start": day,
        "date_end": day,
        "selected_day_count": 1,
        "max_candidates_per_symbol_window": 0,
        "candidate_generation_authority": "uncapped_full_authority",
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }
    for field_name, expected in expected_scalars.items():
        if summary.get(field_name) != expected:
            issues.append(
                f"target_summary_contract_mismatch:{field_name}:"
                f"expected={expected!r}:actual={summary.get(field_name)!r}"
            )
    binding = summary.get("b7_5_contract_binding")
    if not isinstance(binding, Mapping) or binding.get("valid") is not True:
        issues.append("b7_5_contract_binding_invalid")
        binding = {}
    if binding.get("actual_shared_execution_contract_digest_sha256") != shared_digest:
        issues.append("shared_execution_contract_digest_mismatch")
    if binding.get("actual_source_plan_digests_sha256") != [source_plan_digest]:
        issues.append("source_plan_digest_mismatch")
    shared = summary.get("shared_execution_contract")
    if not isinstance(shared, Mapping):
        issues.append("shared_execution_contract_missing")
        shared = {}
    if shared.get("shared_execution_contract_digest_sha256") != shared_digest:
        issues.append("shared_execution_contract_payload_digest_mismatch")
    profile_hashes = shared.get("effective_profile_config_hashes")
    if not isinstance(profile_hashes, Mapping) or profile_hashes.get(PROFILE) != profile_hash:
        issues.append("effective_profile_config_hash_mismatch")
    symbols = shared.get("active_replay_symbol_universe")
    if not isinstance(symbols, list) or len(symbols) != 24 or len(set(symbols)) != 24:
        issues.append("active_symbol_universe_not_exact_24")
    options = shared.get("execution_options")
    if not isinstance(options, Mapping) or options.get("max_candidates_per_symbol_window") != 0:
        issues.append("shared_execution_contract_candidate_cap_not_zero")
    invariance = summary.get("source_authority_chunk_invariance_contract")
    if not isinstance(invariance, Mapping):
        issues.append("source_authority_chunk_invariance_contract_missing")
    else:
        for field_name in (
            "all_chunk_source_plans_match_canonical",
            "all_source_plans_valid",
        ):
            if invariance.get(field_name) is not True:
                issues.append(f"source_authority_invariance_failed:{field_name}")
    return issues


def artifact_record(kind: str, role: str, scan: Mapping[str, Any]) -> dict[str, Any]:
    return {"kind": kind, "role": role, **dict(scan)}


@dataclass
class SurfaceData:
    role: str
    prefix: str
    day: str
    summary: dict[str, Any]
    summary_record: dict[str, Any]
    projection: ProjectionData
    trades: TradeData
    missed: MissedData
    order_scan: dict[str, Any] | None = None
    cap_scan: dict[str, Any] | None = None
    contract_issues: list[str] = field(default_factory=list)
    parity: dict[str, Any] | None = None

    def input_records(self) -> list[dict[str, Any]]:
        records = [
            {"kind": "summary", "role": self.role, **self.summary_record},
            artifact_record("candidate_projection", self.role, self.projection.scan),
            artifact_record("trade_ledger", self.role, self.trades.scan),
            artifact_record("missed_ledger", self.role, self.missed.scan),
        ]
        if self.order_scan is not None:
            records.append(artifact_record("order_ledger", self.role, self.order_scan))
        return records


def load_surface(
    *,
    root: Path,
    role: str,
    prefix: str,
    day: str,
    target: bool,
    shared_digest: str,
    profile_hash: str,
    source_plan_digest: str,
) -> SurfaceData:
    summary, summary_record = read_json_object(
        artifact_path(root, prefix, "SUMMARY.json")
    )
    projection = load_projection(projection_path(root, prefix), day)
    trades = load_trades(artifact_path(root, prefix, "TRADE_LEDGER.jsonl"), day)
    missed = load_missed(
        artifact_path(root, prefix, "MISSED_OPPORTUNITY_LEDGER.jsonl"), day
    )
    surface = SurfaceData(
        role=role,
        prefix=prefix,
        day=day,
        summary=summary,
        summary_record=summary_record,
        projection=projection,
        trades=trades,
        missed=missed,
    )
    if target:
        surface.contract_issues = validate_target_contract(
            summary,
            day=day,
            shared_digest=shared_digest,
            profile_hash=profile_hash,
            source_plan_digest=source_plan_digest,
        )
        surface.parity = summary_trade_parity(summary, trades.rollup)
        surface.cap_scan, surface.order_scan = scan_cap_authority(
            artifact_path(root, prefix, "ORDER_LEDGER.jsonl"), trades, day
        )
    return surface


def duplicate_summary(counter: Counter[str]) -> dict[str, Any]:
    return {
        "duplicate_identity_rows": sum(counter.values()),
        "duplicate_identity_key_count": len(counter),
        "sample_duplicate_keys": sorted(counter)[:25],
    }


def projection_parity(surface: SurfaceData) -> dict[str, Any]:
    if not surface.projection.available:
        return {"status": "projection_unavailable"}
    if not surface.missed.available or not surface.trades.available:
        return {
            "status": "terminal_candidate_union_unavailable",
            "failures": ["terminal_candidate_union_ledger_missing"],
        }
    projection_keys = set(surface.projection.rows)
    projection_trade = {
        key for key, row in surface.projection.rows.items() if row["trade_present"]
    }
    projection_missed = {
        key for key, row in surface.projection.rows.items() if row["missed_present"]
    }
    trade_keys = set(surface.trades.rows)
    missed_keys = set(surface.missed.rows)
    terminal_candidate_union = trade_keys | missed_keys
    terminal_overlap = trade_keys & missed_keys
    failures: list[str] = []
    if projection_keys != terminal_candidate_union:
        failures.append("projection_terminal_candidate_union_identity_mismatch")
    if terminal_overlap:
        failures.append("terminal_candidate_trade_missed_identity_overlap")
    if projection_trade != trade_keys:
        failures.append("projection_trade_identity_mismatch")
    if projection_missed != missed_keys:
        failures.append("projection_missed_identity_mismatch")
    return {
        "status": "exact" if not failures else "mismatch",
        "failures": failures,
        "candidate_projection_rows": len(surface.projection.rows),
        "terminal_candidate_union_rows": len(terminal_candidate_union),
        "terminal_candidate_trade_missed_overlap_rows": len(terminal_overlap),
        "projection_trade_rows": len(projection_trade),
        "trade_ledger_rows": len(trade_keys),
        "projection_missed_rows": len(projection_missed),
        "missed_ledger_rows": len(missed_keys),
        "projection_only_sample": sorted(projection_keys - terminal_candidate_union)[
            :25
        ],
        "terminal_union_only_sample": sorted(
            terminal_candidate_union - projection_keys
        )[:25],
        "terminal_trade_missed_overlap_sample": sorted(terminal_overlap)[:25],
        "trade_projection_only_sample": sorted(projection_trade - trade_keys)[:25],
        "trade_ledger_only_sample": sorted(trade_keys - projection_trade)[:25],
        "missed_projection_only_sample": sorted(projection_missed - missed_keys)[:25],
        "missed_ledger_only_sample": sorted(missed_keys - projection_missed)[:25],
    }


def numeric_delta(candidate: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "physical_trade_rows",
        "physical_scoreable_trade_rows",
        "physical_unscoreable_trade_rows",
        "physical_win_count",
        "physical_loss_count",
        "physical_flat_count",
        "physical_net_r",
        "physical_gross_r",
        "physical_final_r",
        "physical_cash_pnl",
        "physical_risk_cash",
        "physical_risk_pct",
        "physical_scoreable_expected_cost_r",
        "physical_unscoreable_expected_cost_r",
        "physical_expected_cost_r",
        "physical_full_risk_trade_rows",
        "physical_reduced_risk_trade_rows",
        "headline_trade_rows",
        "headline_net_r",
        "headline_cash_pnl",
    )
    return {
        field_name: rounded(fnum(candidate.get(field_name)) - fnum(baseline.get(field_name)))
        for field_name in fields
    }


def missed_delta(candidate: Mapping[str, Any], baseline: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "rows",
        "scoreable_rows",
        "unscoreable_rows",
        "executable_scoreable_rows",
        "executable_positive_rows",
        "executable_negative_rows",
        "executable_net_r",
        "executable_positive_net_r",
        "executable_negative_net_r",
        "diagnostic_scoreable_rows",
        "diagnostic_positive_rows",
        "diagnostic_negative_rows",
        "diagnostic_net_r",
        "diagnostic_positive_net_r",
        "diagnostic_negative_net_r",
    )
    return {
        field_name: rounded(fnum(candidate.get(field_name)) - fnum(baseline.get(field_name)))
        for field_name in fields
    }


def stage_disposition(row: Mapping[str, Any] | None) -> str:
    if row is None:
        return "candidate_generation_suppressed"
    if not row.get("scorecard_present"):
        return "candidate_preserved_before_scorecard"
    if not row.get("scheduler_selected"):
        return "scorecard_preserved_scheduler_not_selected"
    if not row.get("order_present"):
        return "scheduler_selected_order_not_materialized"
    if row.get("trade_present"):
        return "filled_trade"
    if row.get("missed_present"):
        return "order_or_scheduler_transfer_missed"
    return "order_present_without_trade_or_missed_binding"


def identity_transition_row(
    pair_name: str,
    day: str,
    key: str,
    baseline: Mapping[str, Any] | None,
    candidate: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if baseline is None:
        classification = "added"
    elif candidate is None:
        classification = "removed"
    else:
        classification = "shared"
    return {
        "schema": IDENTITY_SCHEMA,
        "pair": pair_name,
        "day": day,
        "identity_key": key,
        "identity_evidence_class": "candidate_projection",
        "identity_class": classification,
        "candidate_disposition": stage_disposition(candidate),
        "baseline": baseline,
        "candidate": candidate,
    }


@dataclass
class PairComparison:
    name: str
    day: str
    baseline: SurfaceData
    candidate: SurfaceData
    projection_required: bool
    summary: dict[str, Any]
    structural_issues: list[str]
    evidence_issues: list[str]
    warnings: list[str]
    cohort_rows: list[dict[str, Any]]
    downstream_authority_gap_signals: list[str]
    economic_unresolved_signals: list[str]

    def iter_identity_rows(self) -> Iterator[dict[str, Any]]:
        if not self.baseline.projection.available or not self.candidate.projection.available:
            # Historical compact comparators can predate candidate projection.
            # Preserve their exact trade identity delta and bind any current
            # missed row without pretending this is candidate-stage evidence.
            keys = sorted(
                set(self.baseline.trades.rows) | set(self.candidate.trades.rows)
            )
            for key in keys:
                baseline_trade = self.baseline.trades.rows.get(key)
                candidate_trade = self.candidate.trades.rows.get(key)
                candidate_missed = self.candidate.missed.rows.get(key)
                if baseline_trade is None:
                    classification = "added_trade"
                elif candidate_trade is None:
                    classification = "removed_trade"
                else:
                    classification = "shared_trade"
                if candidate_trade is not None:
                    disposition = "filled_trade"
                elif candidate_missed is not None:
                    disposition = "trade_absent_missed_identity_preserved"
                else:
                    disposition = "trade_absent_candidate_stage_identity_unavailable"
                yield {
                    "schema": IDENTITY_SCHEMA,
                    "pair": self.name,
                    "day": self.day,
                    "identity_key": key,
                    "identity_evidence_class": "trade_ledger_with_optional_missed_binding",
                    "identity_class": classification,
                    "candidate_disposition": disposition,
                    "baseline_trade": trade_snapshot(baseline_trade),
                    "candidate_trade": trade_snapshot(candidate_trade),
                    "candidate_missed": candidate_missed,
                    "candidate_stage_fields_available": False,
                }
            return
        keys = sorted(set(self.baseline.projection.rows) | set(self.candidate.projection.rows))
        for key in keys:
            yield identity_transition_row(
                self.name,
                self.day,
                key,
                self.baseline.projection.rows.get(key),
                self.candidate.projection.rows.get(key),
            )


def trade_snapshot(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "identity_key": identity_key(row),
        "symbol": row.get("symbol"),
        "side": row.get("side") or row.get("direction"),
        "decision_time_utc": row.get("decision_time_utc"),
        "net_r": trade_net_r(row),
        "gross_r": row.get("gross_r"),
        "final_r": row.get("final_r"),
        "cash_pnl": row.get("pnl_cash") or row.get("cash_pnl"),
        "risk_cash": row.get("risk_cash"),
        "risk_pct": row.get("risk_pct"),
        "risk_tier": risk_tier(row),
        "terminal_r_scoreable": row.get("terminal_r_scoreable"),
        "headline_result_eligible": row.get("headline_result_eligible"),
        "cap": cap_state(row),
    }


def cohort_outcome_assessment(
    *,
    disposition: str,
    candidate_trade: Mapping[str, Any] | None,
    candidate_missed: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Classify an old pressure-cap cohort member by observed outcome quality.

    Candidate-stage displacement is not intrinsically harmful.  A scoreable
    negative opportunity is a beneficial rejection, while a positive missed
    opportunity or an unscoreable replacement needs downstream authority and
    terminal-outcome proof before it can be judged economically.
    """

    if candidate_trade is not None:
        net_r = trade_net_r(candidate_trade)
        scoreable = bool(
            candidate_trade.get("terminal_r_scoreable") is not False
            and net_r is not None
        )
        if scoreable:
            return {
                "status": "RESOLVED_SCOREABLE_FILL",
                "scope": "physical_trade",
                "net_r": net_r,
                "economic_direction": (
                    "positive"
                    if net_r > FLOAT_TOLERANCE
                    else "negative"
                    if net_r < -FLOAT_TOLERANCE
                    else "flat"
                ),
                "downstream_authority_gap": False,
                "interpretation": "candidate remained filled with a scoreable terminal-R outcome",
            }
        return {
            "status": "UNRESOLVED_UNSCOREABLE_REPLACEMENT",
            "scope": "physical_trade",
            "net_r": None,
            "economic_direction": "unresolved",
            "downstream_authority_gap": True,
            "interpretation": (
                "candidate filled but lacks a scoreable terminal-R outcome; replacement "
                "economics remain unresolved"
            ),
        }

    if candidate_missed is not None:
        scope = str(candidate_missed.get("scope") or "unscoreable")
        net_r = number(candidate_missed.get("net_r"))
        if scope == "unscoreable" or net_r is None:
            return {
                "status": "UNRESOLVED_UNSCOREABLE_DISPLACEMENT",
                "scope": scope,
                "net_r": None,
                "economic_direction": "unresolved",
                "downstream_authority_gap": True,
                "interpretation": (
                    "candidate was displaced without a scoreable counterfactual outcome"
                ),
            }
        if net_r < -FLOAT_TOLERANCE:
            return {
                "status": "BENEFICIAL_NEGATIVE_DISPLACEMENT",
                "scope": scope,
                "net_r": net_r,
                "economic_direction": "beneficial_rejection",
                "downstream_authority_gap": False,
                "interpretation": (
                    f"candidate avoided a scoreable {scope} loss; this is beneficial, "
                    "not evidence of an allocation flaw"
                ),
            }
        if net_r > FLOAT_TOLERANCE:
            return {
                "status": f"UNRESOLVED_POSITIVE_{scope.upper()}_DISPLACEMENT",
                "scope": scope,
                "net_r": net_r,
                "economic_direction": "positive_displaced",
                "downstream_authority_gap": True,
                "interpretation": (
                    f"candidate missed a positive {scope} opportunity; replacement value "
                    "and downstream authority require causal proof"
                ),
            }
        return {
            "status": "NEUTRAL_SCOREABLE_DISPLACEMENT",
            "scope": scope,
            "net_r": net_r,
            "economic_direction": "flat",
            "downstream_authority_gap": False,
            "interpretation": "candidate displacement had a flat scoreable outcome",
        }

    if disposition == "candidate_generation_suppressed":
        return {
            "status": "STRUCTURAL_CANDIDATE_SUPPRESSION",
            "scope": "candidate_identity",
            "net_r": None,
            "economic_direction": "not_assessed",
            "downstream_authority_gap": False,
            "interpretation": "candidate identity was suppressed; structural failure takes precedence",
        }
    if disposition == "candidate_stage_identity_unavailable":
        return {
            "status": "CANDIDATE_STAGE_EVIDENCE_UNAVAILABLE",
            "scope": "historical_trade_identity_only",
            "net_r": None,
            "economic_direction": "not_assessed",
            "downstream_authority_gap": False,
            "interpretation": "historical comparator lacks candidate-stage evidence",
        }
    return {
        "status": "UNRESOLVED_OUTCOME_NOT_BOUND",
        "scope": "candidate_stage",
        "net_r": None,
        "economic_direction": "unresolved",
        "downstream_authority_gap": True,
        "interpretation": "unfilled candidate has no bound scoreable outcome evidence",
    }


def build_cohort_rows(
    pair_name: str,
    day: str,
    baseline: SurfaceData,
    candidate: SurfaceData,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, baseline_trade in sorted(baseline.trades.rows.items()):
        old_cap = cap_state(baseline_trade)
        if not old_cap["cap_applied"] or old_cap["pressure_requires_base_fragility"]:
            continue
        candidate_projection = candidate.projection.rows.get(key)
        candidate_trade = candidate.trades.rows.get(key)
        current_cap = cap_state(candidate_trade) if candidate_trade else None
        # A retained trade ledger remains exact identity evidence even when an
        # older compact run predates the candidate-projection artifact.  Check
        # that authority before classifying a missing projection as candidate
        # suppression.
        candidate_missed = candidate.missed.rows.get(key)
        if candidate_trade is not None and current_cap and current_cap["cap_applied"]:
            disposition = (
                "filled_now_base_fragile_cap_causal"
                if current_cap["pressure_requires_base_fragility"]
                and current_cap["base_fragile"]
                else "filled_nonfragile_cap_remains"
            )
        elif candidate_trade is not None:
            disposition = "filled_cap_cleared"
        elif candidate_projection is not None:
            disposition = stage_disposition(candidate_projection)
        elif candidate_missed is not None:
            disposition = "candidate_preserved_missed_trade_not_filled"
        elif not candidate.projection.available:
            disposition = "candidate_stage_identity_unavailable"
        else:
            disposition = "candidate_generation_suppressed"
        rows.append(
            {
                "schema": COHORT_SCHEMA,
                "pair": pair_name,
                "day": day,
                "identity_key": key,
                "disposition": disposition,
                "outcome_assessment": cohort_outcome_assessment(
                    disposition=disposition,
                    candidate_trade=candidate_trade,
                    candidate_missed=candidate_missed,
                ),
                "baseline_trade": trade_snapshot(baseline_trade),
                "candidate_projection": candidate_projection,
                "candidate_trade": trade_snapshot(candidate_trade),
                "candidate_missed": candidate_missed,
            }
        )
    return rows


def compare_surfaces(
    *,
    name: str,
    day: str,
    baseline: SurfaceData,
    candidate: SurfaceData,
    projection_required: bool,
    expected_cohort_count: int,
) -> PairComparison:
    structural_issues = list(candidate.contract_issues)
    evidence_issues: list[str] = []
    warnings: list[str] = []
    if not candidate.trades.available:
        evidence_issues.append("candidate_trade_ledger_missing")
    if not baseline.trades.available:
        evidence_issues.append("baseline_trade_ledger_missing")
    for role, surface in (("baseline", baseline), ("candidate", candidate)):
        for kind, data in (
            ("projection", surface.projection),
            ("trade", surface.trades),
            ("missed", surface.missed),
        ):
            duplicate_keys = data.duplicate_keys
            missing_rows = data.missing_identity_rows
            if duplicate_keys:
                evidence_issues.append(f"{role}_{kind}_duplicate_identity_keys")
            if missing_rows:
                evidence_issues.append(f"{role}_{kind}_missing_identity_rows")
    if projection_required:
        if not baseline.projection.available:
            evidence_issues.append("baseline_candidate_projection_missing")
        if not candidate.projection.available:
            evidence_issues.append("candidate_candidate_projection_missing")
        if not baseline.missed.available:
            evidence_issues.append("baseline_missed_ledger_missing")
        if not candidate.missed.available:
            evidence_issues.append("candidate_missed_ledger_missing")
    else:
        if not baseline.projection.available or not candidate.projection.available:
            warnings.append("historical_candidate_stage_identity_unavailable_trade_identity_only")
        if not baseline.missed.available:
            warnings.append("historical_baseline_missed_ledger_unavailable")
    candidate_projection_parity = projection_parity(candidate)
    baseline_projection_parity = projection_parity(baseline)
    if projection_required:
        for role, parity in (
            ("baseline", baseline_projection_parity),
            ("candidate", candidate_projection_parity),
        ):
            if parity.get("status") != "exact":
                evidence_issues.append(f"{role}_candidate_projection_parity_not_exact")
    if candidate.parity and candidate.parity.get("bad_counts"):
        structural_issues.append("candidate_physical_summary_trade_parity_mismatch")
    if candidate.cap_scan and candidate.cap_scan.get("bad_counts"):
        structural_issues.append("candidate_stop_hazard_cap_execution_authority_leak")
    if candidate.cap_scan and candidate.cap_scan.get(
        "suppressed_pressure_materialization_blocked_rows"
    ):
        structural_issues.append(
            "candidate_suppressed_pressure_rematerialized_as_final_block"
        )
    if candidate.missed.metrics.get(
        "suppressed_pressure_materialization_blocked_rows"
    ):
        structural_issues.append(
            "candidate_suppressed_pressure_rematerialized_as_final_block"
        )
    rollup = candidate.trades.rollup
    if not rollup.get("net_equals_final_less_scoreable_cost"):
        structural_issues.append("candidate_net_final_scoreable_cost_parity_failed")
    if rollup.get("executed_refused_cost_rows"):
        structural_issues.append("candidate_executed_refused_cost_rows_nonzero")
    if rollup.get("executed_source_gap_rows"):
        structural_issues.append("candidate_executed_source_gap_rows_nonzero")

    added: set[str] = set()
    removed: set[str] = set()
    shared: set[str] = set()
    if baseline.projection.available and candidate.projection.available:
        baseline_keys = set(baseline.projection.rows)
        candidate_keys = set(candidate.projection.rows)
        added = candidate_keys - baseline_keys
        removed = baseline_keys - candidate_keys
        shared = baseline_keys & candidate_keys
        if added or removed:
            structural_issues.append("candidate_identity_drift")

    baseline_trade_keys = set(baseline.trades.rows)
    candidate_trade_keys = set(candidate.trades.rows)
    added_trades = candidate_trade_keys - baseline_trade_keys
    removed_trades = baseline_trade_keys - candidate_trade_keys
    shared_trades = baseline_trade_keys & candidate_trade_keys

    cohort_rows = build_cohort_rows(name, day, baseline, candidate)
    if len(cohort_rows) != expected_cohort_count:
        structural_issues.append(
            f"baseline_pressure_cohort_count_mismatch:expected={expected_cohort_count}:"
            f"actual={len(cohort_rows)}"
        )
    downstream_authority_gap_signals: list[str] = []
    for row in cohort_rows:
        if row["disposition"] == "candidate_generation_suppressed":
            if "candidate_identity_drift" not in structural_issues:
                structural_issues.append("pressure_cohort_candidate_suppressed")
        if row["outcome_assessment"]["downstream_authority_gap"]:
            downstream_authority_gap_signals.append(
                "pressure_cohort_outcome_unresolved:"
                f"{row['identity_key']}:"
                f"{row['outcome_assessment']['status'].lower()}"
            )
        if row["disposition"] == "filled_nonfragile_cap_remains":
            structural_issues.append("pressure_only_nonfragile_cap_remains")

    trade_delta = numeric_delta(candidate.trades.rollup, baseline.trades.rollup)
    candidate_unscoreable_keys = {
        key
        for key, row in candidate.trades.rows.items()
        if row.get("terminal_r_scoreable") is False or trade_net_r(row) is None
    }
    unscoreable_replacement_keys = sorted(
        (candidate_trade_keys - baseline_trade_keys) & candidate_unscoreable_keys
    )
    if unscoreable_replacement_keys:
        downstream_authority_gap_signals.append(
            "unscoreable_replacement_trades_require_terminal_outcomes:"
            f"{name}:count={len(unscoreable_replacement_keys)}"
        )
    if (
        baseline.missed.available
        and candidate.missed.available
        and missed_delta(candidate.missed.metrics, baseline.missed.metrics)[
            "executable_positive_net_r"
        ]
        > FLOAT_TOLERANCE
        and removed_trades
    ):
        downstream_authority_gap_signals.append(
            "removed_trades_coincide_with_more_missed_executable_positive_r"
        )

    economic_unresolved_signals = list(downstream_authority_gap_signals)
    if (
        trade_delta["physical_net_r"] < -FLOAT_TOLERANCE
        and trade_delta["physical_cash_pnl"] > FLOAT_TOLERANCE
    ):
        economic_unresolved_signals.append(
            f"{name}_physical_net_r_down_cash_up:"
            f"net_r={trade_delta['physical_net_r']:+.8f}:"
            f"cash={trade_delta['physical_cash_pnl']:+.8f}"
        )

    summary = {
        "pair": name,
        "day": day,
        "baseline_prefix": baseline.prefix,
        "candidate_prefix": candidate.prefix,
        "projection_identity_status": (
            "exact"
            if baseline.projection.available and candidate.projection.available
            else "unavailable_trade_identity_only"
        ),
        "projection_required": projection_required,
        "baseline_projection_parity": baseline_projection_parity,
        "candidate_projection_parity": candidate_projection_parity,
        "candidate_summary_trade_parity": candidate.parity,
        "candidate_stop_hazard_cap_scan": candidate.cap_scan,
        "baseline_trade_metrics": baseline.trades.rollup,
        "candidate_trade_metrics": candidate.trades.rollup,
        "candidate_minus_baseline_trade_delta": trade_delta,
        "baseline_missed_metrics": baseline.missed.metrics,
        "candidate_missed_metrics": candidate.missed.metrics,
        "candidate_minus_baseline_missed_delta": (
            missed_delta(candidate.missed.metrics, baseline.missed.metrics)
            if baseline.missed.available and candidate.missed.available
            else None
        ),
        "candidate_identity_counts": {
            "baseline": len(baseline.projection.rows),
            "candidate": len(candidate.projection.rows),
            "added": len(added),
            "removed": len(removed),
            "shared": len(shared),
        },
        "trade_identity_counts": {
            "baseline": len(baseline_trade_keys),
            "candidate": len(candidate_trade_keys),
            "added": len(added_trades),
            "removed": len(removed_trades),
            "shared": len(shared_trades),
        },
        "baseline_stage_counts": dict(sorted(baseline.projection.stage_counts.items())),
        "candidate_stage_counts": dict(sorted(candidate.projection.stage_counts.items())),
        "pressure_only_nonfragile_baseline_cohort_count": len(cohort_rows),
        "pressure_cohort_disposition_counts": dict(
            sorted(Counter(row["disposition"] for row in cohort_rows).items())
        ),
        "pressure_cohort_outcome_assessment_counts": dict(
            sorted(
                Counter(
                    row["outcome_assessment"]["status"] for row in cohort_rows
                ).items()
            )
        ),
        "unscoreable_replacement_trade_count": len(unscoreable_replacement_keys),
        "unscoreable_replacement_trade_identity_sample": unscoreable_replacement_keys[
            :25
        ],
        "duplicate_detection": {
            "baseline_projection": duplicate_summary(baseline.projection.duplicate_keys),
            "candidate_projection": duplicate_summary(candidate.projection.duplicate_keys),
            "baseline_trade": duplicate_summary(baseline.trades.duplicate_keys),
            "candidate_trade": duplicate_summary(candidate.trades.duplicate_keys),
            "baseline_missed": duplicate_summary(baseline.missed.duplicate_keys),
            "candidate_missed": duplicate_summary(candidate.missed.duplicate_keys),
        },
        "structural_issues": sorted(set(structural_issues)),
        "evidence_issues": sorted(set(evidence_issues)),
        "warnings": sorted(set(warnings)),
        "downstream_authority_gap_signals": sorted(
            set(downstream_authority_gap_signals)
        ),
        "economic_unresolved_signals": sorted(set(economic_unresolved_signals)),
    }
    return PairComparison(
        name=name,
        day=day,
        baseline=baseline,
        candidate=candidate,
        projection_required=projection_required,
        summary=summary,
        structural_issues=summary["structural_issues"],
        evidence_issues=summary["evidence_issues"],
        warnings=summary["warnings"],
        cohort_rows=cohort_rows,
        downstream_authority_gap_signals=summary[
            "downstream_authority_gap_signals"
        ],
        economic_unresolved_signals=summary["economic_unresolved_signals"],
    )


@dataclass(frozen=True)
class AnalyzerConfig:
    artifact_root: Path
    hostile_prefix: str
    hostile_baseline_prefix: str
    hostile_day: str
    non_hostile_prefix: str
    non_hostile_baseline_prefix: str
    non_hostile_day: str
    expected_shared_execution_contract_sha256: str
    expected_profile_config_sha256: str
    expected_hostile_source_plan_sha256: str
    expected_non_hostile_source_plan_sha256: str
    expected_hostile_pressure_cohort_count: int = 4
    expected_non_hostile_pressure_cohort_count: int = 4
    require_hostile_projection: bool = False
    output_prefix: str = DEFAULT_OUTPUT_PREFIX

    def as_dict(self) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in self.__dict__.items()
        }


@dataclass
class AnalysisBundle:
    config: AnalyzerConfig
    summary: dict[str, Any]
    comparisons: tuple[PairComparison, PairComparison]

    def iter_identity_rows(self) -> Iterator[dict[str, Any]]:
        for comparison in self.comparisons:
            yield from comparison.iter_identity_rows()

    def iter_cohort_rows(self) -> Iterator[dict[str, Any]]:
        for comparison in self.comparisons:
            yield from comparison.cohort_rows

    def iter_missed_rows(self) -> Iterator[dict[str, Any]]:
        for comparison in self.comparisons:
            yield {
                "schema": MISSED_SCHEMA,
                "pair": comparison.name,
                "day": comparison.day,
                "baseline_prefix": comparison.baseline.prefix,
                "candidate_prefix": comparison.candidate.prefix,
                "baseline": comparison.baseline.missed.metrics,
                "candidate": comparison.candidate.missed.metrics,
                "candidate_minus_baseline": comparison.summary[
                    "candidate_minus_baseline_missed_delta"
                ],
            }


def decision_axes(comparisons: Iterable[PairComparison]) -> dict[str, Any]:
    """Resolve evidence, structure, economics, and downstream authority separately."""

    comparisons = tuple(comparisons)
    evidence_issues = sorted(
        {issue for comparison in comparisons for issue in comparison.evidence_issues}
    )
    structural_issues = sorted(
        {issue for comparison in comparisons for issue in comparison.structural_issues}
    )
    downstream = sorted(
        {
            signal
            for comparison in comparisons
            for signal in comparison.downstream_authority_gap_signals
        }
    )
    economic_unresolved = sorted(
        {
            signal
            for comparison in comparisons
            for signal in comparison.economic_unresolved_signals
        }
    )
    if evidence_issues:
        return {
            "evidence_status": "INSUFFICIENT_EVIDENCE",
            "structural_status": "NOT_ASSESSED",
            "economic_status": "NOT_ASSESSED",
            "downstream_status": "NOT_ASSESSED",
            "decision_status": "INSUFFICIENT_EVIDENCE",
            "decision_reasons": evidence_issues,
            "structural_reasons": [],
            "economic_reasons": [],
            "downstream_reasons": [],
        }
    if structural_issues:
        return {
            "evidence_status": "ACCEPT",
            "structural_status": "FAIL",
            "economic_status": "NOT_ASSESSED",
            "downstream_status": "NOT_ASSESSED",
            "decision_status": "BATCH_FAIL",
            "decision_reasons": structural_issues,
            "structural_reasons": structural_issues,
            "economic_reasons": [],
            "downstream_reasons": [],
        }
    deltas = [
        comparison.summary["candidate_minus_baseline_trade_delta"]
        for comparison in comparisons
    ]
    all_positive = all(
        delta["physical_net_r"] > FLOAT_TOLERANCE
        and delta["physical_cash_pnl"] > FLOAT_TOLERANCE
        for delta in deltas
    )
    if economic_unresolved:
        economic_status = "MIXED_UNRESOLVED"
        economic_reasons = economic_unresolved
    elif all_positive:
        economic_status = "POSITIVE"
        economic_reasons = []
    else:
        economic_status = "MIXED"
        economic_reasons = [
            "structural_contract_green_but_net_r_and_cash_deltas_not_uniformly_positive"
        ]
    downstream_status = (
        "DEEPER_AUTHORITY_GAP_EXPOSED" if downstream else "CLEAR"
    )
    if downstream:
        overall = "DEEPER_AUTHORITY_GAP_EXPOSED"
        overall_reasons = sorted(set([*downstream, *economic_reasons]))
    elif economic_status == "POSITIVE":
        overall = "STRUCTURAL_ACCEPT_ECONOMIC_POSITIVE"
        overall_reasons = []
    else:
        overall = "STRUCTURAL_ACCEPT_ECONOMIC_MIXED"
        overall_reasons = economic_reasons
    return {
        "evidence_status": "ACCEPT",
        "structural_status": "ACCEPT",
        "economic_status": economic_status,
        "downstream_status": downstream_status,
        "decision_status": overall,
        "decision_reasons": overall_reasons,
        "structural_reasons": [],
        "economic_reasons": economic_reasons,
        "downstream_reasons": downstream,
    }


def analyze(config: AnalyzerConfig) -> AnalysisBundle:
    root = config.artifact_root.resolve()
    hostile_baseline = load_surface(
        root=root,
        role="hostile_baseline",
        prefix=config.hostile_baseline_prefix,
        day=config.hostile_day,
        target=False,
        shared_digest=config.expected_shared_execution_contract_sha256,
        profile_hash=config.expected_profile_config_sha256,
        source_plan_digest=config.expected_hostile_source_plan_sha256,
    )
    hostile_candidate = load_surface(
        root=root,
        role="hostile_candidate",
        prefix=config.hostile_prefix,
        day=config.hostile_day,
        target=True,
        shared_digest=config.expected_shared_execution_contract_sha256,
        profile_hash=config.expected_profile_config_sha256,
        source_plan_digest=config.expected_hostile_source_plan_sha256,
    )
    non_hostile_baseline = load_surface(
        root=root,
        role="non_hostile_baseline",
        prefix=config.non_hostile_baseline_prefix,
        day=config.non_hostile_day,
        target=False,
        shared_digest=config.expected_shared_execution_contract_sha256,
        profile_hash=config.expected_profile_config_sha256,
        source_plan_digest=config.expected_non_hostile_source_plan_sha256,
    )
    non_hostile_candidate = load_surface(
        root=root,
        role="non_hostile_candidate",
        prefix=config.non_hostile_prefix,
        day=config.non_hostile_day,
        target=True,
        shared_digest=config.expected_shared_execution_contract_sha256,
        profile_hash=config.expected_profile_config_sha256,
        source_plan_digest=config.expected_non_hostile_source_plan_sha256,
    )
    hostile = compare_surfaces(
        name="hostile",
        day=config.hostile_day,
        baseline=hostile_baseline,
        candidate=hostile_candidate,
        projection_required=config.require_hostile_projection,
        expected_cohort_count=config.expected_hostile_pressure_cohort_count,
    )
    non_hostile = compare_surfaces(
        name="non_hostile",
        day=config.non_hostile_day,
        baseline=non_hostile_baseline,
        candidate=non_hostile_candidate,
        projection_required=True,
        expected_cohort_count=config.expected_non_hostile_pressure_cohort_count,
    )
    axes = decision_axes((hostile, non_hostile))
    inputs = sorted(
        [
            record
            for surface in (
                hostile_baseline,
                hostile_candidate,
                non_hostile_baseline,
                non_hostile_candidate,
            )
            for record in surface.input_records()
        ],
        key=lambda row: (row["role"], row["kind"]),
    )
    core = {
        "schema": SUMMARY_SCHEMA,
        "status": "b7_5_causal_risk_pair_analyzed",
        **axes,
        "broker_live_final_closed": True,
        "broker_live_authority": False,
        "final_selection_claim": False,
        "config": config.as_dict(),
        "comparisons": {
            "hostile": hostile.summary,
            "non_hostile": non_hostile.summary,
        },
        "cross_day_identity_comparison_performed": False,
        "cross_day_interpretation": (
            "hostile and non-hostile identities are never compared across disjoint days; "
            "only same-day candidate-versus-baseline identities and normalized metrics are used"
        ),
        "input_artifacts": inputs,
    }
    core["analysis_fingerprint_sha256"] = sha256_bytes(canonical_json_bytes(core))
    return AnalysisBundle(config=config, summary=core, comparisons=(hostile, non_hostile))


def dossier_text(summary: Mapping[str, Any]) -> str:
    comparisons = summary["comparisons"]
    lines = [
        "# B7.5 Causal Stop-Hazard Risk-Expression Paired Comparison",
        "",
        f"Decision: `{summary['decision_status']}`",
        f"Evidence: `{summary['evidence_status']}`",
        f"Structure: `{summary['structural_status']}`",
        f"Economics: `{summary['economic_status']}`",
        f"Downstream authority: `{summary['downstream_status']}`",
        "",
    ]
    if summary.get("decision_reasons"):
        lines.append("Decision reasons:")
        lines.append("")
        lines.extend(f"- `{reason}`" for reason in summary["decision_reasons"])
        lines.append("")
    for name in ("hostile", "non_hostile"):
        comparison = comparisons[name]
        delta = comparison["candidate_minus_baseline_trade_delta"]
        lines.extend(
            [
                f"## {name.replace('_', ' ').title()}",
                "",
                f"- Day: `{comparison['day']}`",
                f"- Candidate identity status: `{comparison['projection_identity_status']}`",
                f"- Physical net-R delta: `{delta['physical_net_r']:+.8f}R`",
                f"- Cash-PnL delta: `{delta['physical_cash_pnl']:+.8f}`",
                f"- Candidate added/removed/shared: "
                f"`{comparison['candidate_identity_counts']['added']}/"
                f"{comparison['candidate_identity_counts']['removed']}/"
                f"{comparison['candidate_identity_counts']['shared']}`",
                f"- Pressure cohort dispositions: "
                f"`{json.dumps(comparison['pressure_cohort_disposition_counts'], sort_keys=True)}`",
                f"- Pressure cohort outcome assessments: "
                f"`{json.dumps(comparison['pressure_cohort_outcome_assessment_counts'], sort_keys=True)}`",
                f"- New unscoreable replacement fills: "
                f"`{comparison['unscoreable_replacement_trade_count']}`",
                "",
            ]
        )
        if (
            delta["physical_net_r"] < -FLOAT_TOLERANCE
            and delta["physical_cash_pnl"] > FLOAT_TOLERANCE
        ):
            lines.extend(
                [
                    f"The {name.replace('_', '-')} candidate's physical net-R fell while "
                    "cash PnL rose. That sizing-versus-selection conflict is mixed evidence, "
                    "not proof that either policy is economically superior.",
                    "",
                ]
            )
        replacement_count = comparison["unscoreable_replacement_trade_count"]
        if replacement_count:
            lines.extend(
                [
                    f"The candidate introduced {replacement_count} replacement fill(s) "
                    "without scoreable terminal-R outcomes. Their economics remain unresolved; "
                    "they are not automatically losses or proof of a flaw.",
                    "",
                ]
            )
    lines.extend(
        [
            "Broker/live/final authority remains false. This artifact decides only the bounded",
            "same-root hostile/non-hostile causal repair; it is not broad generalization or",
            "broker-real economic proof.",
            "",
        ]
    )
    return "\n".join(lines)


def output_paths(config: AnalyzerConfig) -> dict[str, Path]:
    root = config.artifact_root.resolve()
    prefix = config.output_prefix
    return {
        "identity_transition_ledger": root / f"{prefix}_IDENTITY_TRANSITION_LEDGER.jsonl",
        "pressure_cap_cohort_ledger": root / f"{prefix}_PRESSURE_CAP_COHORT_LEDGER.jsonl",
        "missed_opportunity_ledger": root / f"{prefix}_MISSED_OPPORTUNITY_COMPARISON_LEDGER.jsonl",
        "dossier": root / f"{prefix}_DOSSIER.md",
        "summary": root / f"{prefix}_COMPARISON_SUMMARY.json",
        "manifest": root / f"{prefix}_OUTPUT_MANIFEST.json",
    }


def staged_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".building.tmp")


def write_jsonl_stage(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("wb") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")
                + b"\n"
            )
            count += 1
        handle.flush()
        os.fsync(handle.fileno())
    return count


def write_bytes_stage(path: Path, payload: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def staged_record(
    *, kind: str, final_path: Path, temporary_path: Path, row_count: int | None = None
) -> dict[str, Any]:
    record = {
        "kind": kind,
        "path": str(final_path),
        "byte_count": temporary_path.stat().st_size,
        "sha256": sha256_file(temporary_path),
    }
    if row_count is not None:
        record["row_count"] = row_count
    return record


def publish(bundle: AnalysisBundle) -> dict[str, Any]:
    paths = output_paths(bundle.config)
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    stages = {name: staged_path(path) for name, path in paths.items()}
    for path in stages.values():
        path.unlink(missing_ok=True)
    try:
        identity_count = write_jsonl_stage(
            stages["identity_transition_ledger"], bundle.iter_identity_rows()
        )
        cohort_count = write_jsonl_stage(
            stages["pressure_cap_cohort_ledger"], bundle.iter_cohort_rows()
        )
        missed_count = write_jsonl_stage(
            stages["missed_opportunity_ledger"], bundle.iter_missed_rows()
        )
        dossier = dossier_text(bundle.summary).encode("utf-8")
        write_bytes_stage(stages["dossier"], dossier)

        output_records = [
            staged_record(
                kind="identity_transition_ledger",
                final_path=paths["identity_transition_ledger"],
                temporary_path=stages["identity_transition_ledger"],
                row_count=identity_count,
            ),
            staged_record(
                kind="pressure_cap_cohort_ledger",
                final_path=paths["pressure_cap_cohort_ledger"],
                temporary_path=stages["pressure_cap_cohort_ledger"],
                row_count=cohort_count,
            ),
            staged_record(
                kind="missed_opportunity_ledger",
                final_path=paths["missed_opportunity_ledger"],
                temporary_path=stages["missed_opportunity_ledger"],
                row_count=missed_count,
            ),
            staged_record(
                kind="dossier",
                final_path=paths["dossier"],
                temporary_path=stages["dossier"],
            ),
        ]
        summary_payload = dict(bundle.summary)
        summary_payload["output_artifact_contract"] = {
            "manifest_published_last": True,
            "artifacts": output_records,
        }
        write_bytes_stage(stages["summary"], canonical_json_bytes(summary_payload))
        summary_record = staged_record(
            kind="summary",
            final_path=paths["summary"],
            temporary_path=stages["summary"],
        )
        manifest_payload = {
            "schema": MANIFEST_SCHEMA,
            "status": "b7_5_causal_risk_pair_outputs_complete",
            "completion_marker": True,
            "analysis_fingerprint_sha256": bundle.summary[
                "analysis_fingerprint_sha256"
            ],
            "decision_status": bundle.summary["decision_status"],
            "evidence_status": bundle.summary["evidence_status"],
            "structural_status": bundle.summary["structural_status"],
            "economic_status": bundle.summary["economic_status"],
            "downstream_status": bundle.summary["downstream_status"],
            "config": bundle.config.as_dict(),
            "input_artifacts": bundle.summary["input_artifacts"],
            "output_artifacts": [*output_records, summary_record],
            "row_parity": {
                "identity_transition_ledger": identity_count,
                "pressure_cap_cohort_ledger": cohort_count,
                "missed_opportunity_ledger": missed_count,
            },
        }
        write_bytes_stage(stages["manifest"], canonical_json_bytes(manifest_payload))

        for name in (
            "identity_transition_ledger",
            "pressure_cap_cohort_ledger",
            "missed_opportunity_ledger",
            "dossier",
            "summary",
            "manifest",
        ):
            os.replace(stages[name], paths[name])
    finally:
        for path in stages.values():
            path.unlink(missing_ok=True)
    verification = verify_manifest(paths["manifest"])
    if not verification["valid"]:
        raise ArtifactError(f"published_manifest_verification_failed:{verification}")
    return {
        "manifest_path": str(paths["manifest"]),
        "summary_path": str(paths["summary"]),
        "decision_status": bundle.summary["decision_status"],
        "evidence_status": bundle.summary["evidence_status"],
        "structural_status": bundle.summary["structural_status"],
        "economic_status": bundle.summary["economic_status"],
        "downstream_status": bundle.summary["downstream_status"],
        "verification": verification,
    }


def count_jsonl_rows(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def verify_manifest(path: Path) -> dict[str, Any]:
    manifest, _record = read_json_object(path)
    issues: list[str] = []
    if manifest.get("schema") != MANIFEST_SCHEMA:
        issues.append("manifest_schema_invalid")
    if manifest.get("completion_marker") is not True:
        issues.append("manifest_completion_marker_missing")
    for artifact in manifest.get("output_artifacts") or []:
        artifact_path_value = Path(str(artifact.get("path") or ""))
        kind = str(artifact.get("kind") or "unknown")
        if not artifact_path_value.is_file():
            issues.append(f"output_missing:{kind}")
            continue
        if artifact_path_value.stat().st_size != artifact.get("byte_count"):
            issues.append(f"output_byte_count_mismatch:{kind}")
        if sha256_file(artifact_path_value) != artifact.get("sha256"):
            issues.append(f"output_sha256_mismatch:{kind}")
        if "row_count" in artifact and count_jsonl_rows(artifact_path_value) != artifact.get(
            "row_count"
        ):
            issues.append(f"output_row_count_mismatch:{kind}")
    return {"valid": not issues, "issues": issues}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=ROUTE)
    parser.add_argument("--hostile-prefix", required=True)
    parser.add_argument("--hostile-baseline-prefix", required=True)
    parser.add_argument("--hostile-day", required=True)
    parser.add_argument("--non-hostile-prefix", required=True)
    parser.add_argument("--non-hostile-baseline-prefix", required=True)
    parser.add_argument("--non-hostile-day", required=True)
    parser.add_argument("--expected-shared-execution-contract-sha256", required=True)
    parser.add_argument("--expected-profile-config-sha256", required=True)
    parser.add_argument("--expected-hostile-source-plan-sha256", required=True)
    parser.add_argument("--expected-non-hostile-source-plan-sha256", required=True)
    parser.add_argument("--expected-hostile-pressure-cohort-count", type=int, default=4)
    parser.add_argument(
        "--expected-non-hostile-pressure-cohort-count", type=int, default=4
    )
    parser.add_argument("--require-hostile-projection", action="store_true")
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = AnalyzerConfig(
        artifact_root=args.artifact_root,
        hostile_prefix=args.hostile_prefix,
        hostile_baseline_prefix=args.hostile_baseline_prefix,
        hostile_day=args.hostile_day,
        non_hostile_prefix=args.non_hostile_prefix,
        non_hostile_baseline_prefix=args.non_hostile_baseline_prefix,
        non_hostile_day=args.non_hostile_day,
        expected_shared_execution_contract_sha256=(
            args.expected_shared_execution_contract_sha256
        ),
        expected_profile_config_sha256=args.expected_profile_config_sha256,
        expected_hostile_source_plan_sha256=args.expected_hostile_source_plan_sha256,
        expected_non_hostile_source_plan_sha256=(
            args.expected_non_hostile_source_plan_sha256
        ),
        expected_hostile_pressure_cohort_count=(
            args.expected_hostile_pressure_cohort_count
        ),
        expected_non_hostile_pressure_cohort_count=(
            args.expected_non_hostile_pressure_cohort_count
        ),
        require_hostile_projection=args.require_hostile_projection,
        output_prefix=args.output_prefix,
    )
    result = publish(analyze(config))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["decision_status"] == "INSUFFICIENT_EVIDENCE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
