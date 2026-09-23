"""Ruin-aware Monte Carlo engine for the V4 risk governor.

Builds one record per (campaign, trading_day) from the timewarp replay
SIMULATED_ORDER + SIMULATED_TRADE ledgers (oracle ledger enriches risk-
rejected counterfactual events with mae/fill/exit times), then bootstraps
whole days WITH replacement and re-walks each sampled day's events in time
order, re-deciding admission through ``evaluate_risk_governor_v4``. Risk-
rejected events become admissible when the simulated budget allows (using
their counterfactual final R) — the population a different governor would
have traded is therefore part of every world.

Outputs ruin metrics against the FTMO-style limits:

- ``p_daily_breach_per_day``      P(conservative intraday low <= -daily_limit)
- ``p_any_daily_breach_horizon``  P(>=1 daily breach within the horizon)
- ``p_overall_10pct``             P(path trough <= -10% of the 100k base)
- ``e_daily_r`` / ``e_log_growth`` expectation diagnostics (pct units/day)

Documented approximations (replay/proxy evidence, never broker-real):

- Intraday conservative low = realized day PnL minus ``sum(open risk_i *
  |mae_r_i|)`` over open events — the full-trade |mae| is charged while the
  position is open (pessimistic mark).
- Counterfactual events without an oracle mae use |mae|=1.0 (full stop).
- ``remaining_opportunity_weight`` inside a replayed day is the fraction of
  requestable events still ahead (proxy for the hourly opportunity curve).
- Day walks are day-anchored: admission re-decisions use day-local state
  (``overall_dd_pct=0``); the overall floor halts a path once cumulative
  equity reaches ``-overall_dd_floor_pct`` and the 10% ruin check runs at
  path level over cumulative equity plus intraday conservative lows.
- A daily breach is recorded and the path keeps trading the next day (the
  per-day breach rate is the unconditional target quantity).

Randomness is a counter-based sha256 hash seeded ONLY by the integer
``seed`` argument — the ``random`` module and wall clock are never used, so
identical seeds give byte-identical results and calibration grids share
common random numbers by construction (day sampling depends only on
``(seed, path, day)``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.components.risk_governor_v4 import (
    ACTION_FLATTEN_HALT,
    ACTION_FLOOR_REVIEW,
    ACTION_REFUSE,
    GovernorConfigV4,
    evaluate_risk_governor_v4,
)
from src.research_infra.learned_edge_dataset_builder import (
    ASSET_CLASS_BY_SYMBOL,
    as_float,
    discover_partition_ledgers,
    read_jsonl,
)

DAY_RECORD_SCHEMA_VERSION = "ultimate_ruin_mc_day_record_v1"
RESULT_SCHEMA_VERSION = "ultimate_ruin_mc_simulation_v1"
REPORT_SCHEMA_VERSION = "ultimate_ruin_mc_report_v1"
EVIDENCE_CLASS = "post_asof_timewarp_replay_label_not_decision_input"

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}

ACCOUNT_BASE_CASH = 100_000.0
OVERALL_RUIN_PCT = 10.0
DEFAULT_COUNTERFACTUAL_MAE_ABS_R = 1.0

EVENT_KIND_FILLED = "filled"
EVENT_KIND_RISK_REJECTED = "risk_rejected_counterfactual"
EVENT_KIND_NOT_FILLED = "accepted_not_filled"

# Conservative cross-cluster |corr| priors (documented constants, NOT
# measured estimates). Same cluster is 1.0 by definition; unlisted cross
# pairs use DEFAULT_CROSS_CLUSTER_ABS_CORR. Override per call via
# ``correlation_overrides``.
DEFAULT_CROSS_CLUSTER_ABS_CORR = 0.25
DEFAULT_CLUSTER_ABS_CORRELATION: dict[tuple[str, str], float] = {
    ("fx", "jpy_fx"): 0.65,
    ("fx", "metals"): 0.35,
    ("fx", "index"): 0.3,
    ("jpy_fx", "index"): 0.35,
    ("jpy_fx", "metals"): 0.3,
    ("index", "crypto"): 0.35,
    ("index", "energy"): 0.3,
    ("metals", "energy"): 0.3,
    ("metals", "crypto"): 0.25,
}

DEFAULT_RISK_SCALE_GRID = (0.5, 1.0, 1.5, 2.0, 2.5)
DEFAULT_KAPPA_GRID = (0.0, 0.5, 1.0)
DEFAULT_RESERVE_GRID = (0.3, 0.5, 0.8)
DEFAULT_COUNT_CAPS: tuple[int | None, ...] = (None, 3, 5)

_WILSON_Z_95 = 1.959963984540054


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def hash_uniform(seed: int, *parts: Any) -> float:
    """Deterministic uniform in [0, 1) from sha256(seed, parts)."""

    material = f"{int(seed)}|" + "|".join(str(part) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / 2.0**64


def _hash_index(seed: int, path: int, day: int, n: int) -> int:
    return min(n - 1, int(hash_uniform(seed, "day_sample", path, day) * n))


def wilson_upper_bound(k: int, n: int, *, z: float = _WILSON_Z_95) -> float:
    """Wilson score interval 95% upper bound for a binomial proportion."""

    if n <= 0:
        return 1.0
    phat = k / n
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2.0 * n)
    margin = z * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))
    return min(1.0, (centre + margin) / denom)


def cluster_correlation_lookup(
    overrides: Mapping[Any, float] | None = None,
):
    """Callable |corr| lookup over DEFAULT_CLUSTER_ABS_CORRELATION."""

    table: dict[tuple[str, str], float] = dict(DEFAULT_CLUSTER_ABS_CORRELATION)
    for key, value in (overrides or {}).items():
        if isinstance(key, str):
            parts = key.split("|")
            if len(parts) != 2:
                continue
            pair = (parts[0], parts[1])
        else:
            pair = (str(key[0]), str(key[1]))
        table[pair] = float(value)

    def lookup(cluster_a: str, cluster_b: str) -> float:
        if cluster_a == cluster_b:
            return 1.0
        for pair in ((cluster_a, cluster_b), (cluster_b, cluster_a)):
            if pair in table:
                return table[pair]
        return DEFAULT_CROSS_CLUSTER_ABS_CORR

    return lookup


# ---------------------------------------------------------------------------
# Day record construction
# ---------------------------------------------------------------------------


def _first_positive(*values: Any) -> float | None:
    for value in values:
        parsed = as_float(value)
        if parsed is not None and parsed > 0.0:
            return parsed
    return None


def _counterfactual_filled(fill_status: str) -> bool:
    return bool(fill_status) and "not_filled" not in fill_status and "no_fill" not in fill_status


def _event_from_candidate(
    candidate_id: str,
    order_rows: list[Mapping[str, Any]],
    trade_row: Mapping[str, Any] | None,
    oracle_row: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    base = order_rows[0]
    statuses = [str(row.get("order_status") or "") for row in order_rows]
    requested_chain = _first_positive(
        *[row.get("requested_risk_pct") for row in order_rows],
        base.get("scheduler_approved_risk_pct"),
        base.get("selected_cell_risk_pct"),
        base.get("risk_per_trade_pct"),
    )
    event = {
        "candidate_id": candidate_id,
        "decision_time_utc": str(base.get("decision_time_utc") or ""),
        "fill_time_utc": None,
        "exit_time_utc": None,
        "symbol": str(base.get("symbol") or ""),
        "cluster": ASSET_CLASS_BY_SYMBOL.get(str(base.get("symbol") or ""), "unknown"),
        "side": str(base.get("side") or "").upper() or None,
        "requested_risk_pct": requested_chain,
        "final_r": None,
        "mae_r": None,
        "be_reached": False,
        "filled": False,
        "was_risk_rejected": False,
        "event_kind": EVENT_KIND_NOT_FILLED,
    }
    if not event["decision_time_utc"] or requested_chain is None:
        return None

    if trade_row is not None:
        final_r = as_float(trade_row.get("net_proxy_r"))
        if final_r is None:
            final_r = as_float(trade_row.get("net_r"))
        event.update(
            {
                "event_kind": EVENT_KIND_FILLED,
                "filled": final_r is not None,
                "final_r": final_r,
                "mae_r": as_float(trade_row.get("mae_r")),
                "be_reached": bool(trade_row.get("be_reached")),
                "fill_time_utc": trade_row.get("fill_time_utc") or trade_row.get("entry_time_utc"),
                "exit_time_utc": trade_row.get("exit_time_utc")
                or trade_row.get("close_mark_time_utc"),
                "requested_risk_pct": _first_positive(
                    *[row.get("requested_risk_pct") for row in order_rows],
                    trade_row.get("risk_pct"),
                    base.get("risk_per_trade_pct"),
                ),
            }
        )
        return event

    if any(status.startswith("risk_rejected") for status in statuses):
        fill_status = str(
            base.get("counterfactual_fill_status")
            or (oracle_row or {}).get("counterfactual_fill_status")
            or ""
        )
        final_r = as_float(base.get("counterfactual_final_r"))
        if final_r is None and oracle_row is not None:
            final_r = as_float(oracle_row.get("counterfactual_final_r"))
        filled = _counterfactual_filled(fill_status) and final_r is not None
        event.update(
            {
                "event_kind": EVENT_KIND_RISK_REJECTED,
                "was_risk_rejected": True,
                "filled": filled,
                "final_r": final_r if filled else None,
                "mae_r": as_float((oracle_row or {}).get("mae_r")),
                # Counterfactual heat is never freed early: BE state unknown.
                "be_reached": False,
                "fill_time_utc": (oracle_row or {}).get("fill_time_utc"),
                "exit_time_utc": (oracle_row or {}).get("close_mark_time_utc")
                or (oracle_row or {}).get("expiry_utc")
                or base.get("expiry_utc"),
            }
        )
        return event

    # Accepted but never filled (expired pending) — admission consumes no
    # realized risk in the walk; kept for opportunity-weight accounting.
    event["exit_time_utc"] = base.get("expiry_utc")
    return event


def build_day_records(
    route_dirs: Iterable[Path | str],
) -> list[dict[str, Any]]:
    """One record per (campaign, trading_day) from replay order/trade ledgers."""

    ledger_sets, discovery_notes = discover_partition_ledgers(route_dirs)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for ledger_set in ledger_sets:
        order_path = ledger_set.paths.get("order")
        if order_path is None:
            continue
        orders = read_jsonl(order_path)
        trade_by_id: dict[str, Mapping[str, Any]] = {}
        if "trade" in ledger_set.paths:
            for row in read_jsonl(ledger_set.paths["trade"]):
                trade_by_id.setdefault(str(row.get("candidate_id")), row)
        oracle_by_id: dict[str, Mapping[str, Any]] = {}
        if "oracle" in ledger_set.paths:
            for row in read_jsonl(ledger_set.paths["oracle"]):
                oracle_by_id.setdefault(str(row.get("candidate_id")), row)

        orders_by_candidate: dict[str, list[Mapping[str, Any]]] = {}
        for row in orders:
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id:
                orders_by_candidate.setdefault(candidate_id, []).append(row)

        for candidate_id, candidate_orders in orders_by_candidate.items():
            event = _event_from_candidate(
                candidate_id,
                candidate_orders,
                trade_by_id.get(candidate_id),
                oracle_by_id.get(candidate_id),
            )
            if event is None:
                continue
            trading_day = str(candidate_orders[0].get("trading_day") or "")
            if not trading_day:
                trading_day = event["decision_time_utc"][:10]
            grouped.setdefault((ledger_set.campaign_prefix, trading_day), []).append(event)

    records: list[dict[str, Any]] = []
    for (campaign, trading_day) in sorted(grouped):
        events = sorted(
            grouped[(campaign, trading_day)],
            key=lambda e: (e["decision_time_utc"], e["candidate_id"]),
        )
        n_filled = sum(1 for e in events if e["event_kind"] == EVENT_KIND_FILLED)
        n_rejected = sum(1 for e in events if e["event_kind"] == EVENT_KIND_RISK_REJECTED)
        records.append(
            {
                "schema_version": DAY_RECORD_SCHEMA_VERSION,
                "row_kind": "ruin_mc_day_record",
                "campaign": campaign,
                "trading_day": trading_day,
                "events": events,
                "n_events": len(events),
                "n_filled_replay": n_filled,
                "n_risk_rejected_counterfactual": n_rejected,
                "n_accepted_not_filled": len(events) - n_filled - n_rejected,
                "n_fillable": sum(1 for e in events if e["filled"]),
                "sum_fillable_final_r": round(
                    sum(e["final_r"] for e in events if e["filled"] and e["final_r"] is not None),
                    8,
                ),
                "discovery_notes": list(discovery_notes),
                "evidence_class": EVIDENCE_CLASS,
                **BOUNDARY,
            }
        )
    return records


# ---------------------------------------------------------------------------
# Day walk (deterministic per (record, theta); path-independent by design)
# ---------------------------------------------------------------------------


def _prepare_events(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for event in record.get("events", []):
        decision_time = _parse_utc(event.get("decision_time_utc"))
        if decision_time is None:
            continue
        requested = as_float(event.get("requested_risk_pct"))
        if requested is None or requested <= 0.0:
            continue
        fill_time = _parse_utc(event.get("fill_time_utc")) or decision_time
        exit_time = _parse_utc(event.get("exit_time_utc")) or fill_time
        if exit_time < fill_time:
            exit_time = fill_time
        mae = as_float(event.get("mae_r"))
        prepared.append(
            {
                "candidate_id": str(event.get("candidate_id") or ""),
                "decision_time": decision_time,
                "exit_time": exit_time,
                "cluster": str(event.get("cluster") or "unknown"),
                "requested_risk_pct": requested,
                "filled": bool(event.get("filled")) and as_float(event.get("final_r")) is not None,
                "final_r": as_float(event.get("final_r")),
                "mae_abs_r": abs(mae) if mae is not None else DEFAULT_COUNTERFACTUAL_MAE_ABS_R,
                "be_reached": bool(event.get("be_reached")),
            }
        )
    prepared.sort(key=lambda e: (e["decision_time"], e["candidate_id"]))
    return prepared


def _walk_day(
    events: Sequence[Mapping[str, Any]],
    cfg: GovernorConfigV4,
    *,
    risk_scale: float,
    max_concurrent: int | None,
    corr_lookup: Any,
) -> dict[str, Any]:
    realized = 0.0
    conservative_low = 0.0
    open_sims: list[dict[str, Any]] = []
    halted = False
    n_admitted = 0
    n_refused = 0
    approved_risk_sum = 0.0
    max_open = 0
    n_requestable = len(events)
    seen_requestable = 0

    def _open_mae_sum() -> float:
        return sum(sim["risk_pct"] * sim["mae_abs_r"] for sim in open_sims)

    def _close_matured(now: datetime | None) -> None:
        nonlocal realized, conservative_low
        while open_sims and (now is None or open_sims[0]["exit_time"] <= now):
            sim = open_sims.pop(0)
            realized += sim["risk_pct"] * sim["final_r"]
            conservative_low = min(conservative_low, realized - _open_mae_sum())

    for event in events:
        _close_matured(event["decision_time"])
        seen_requestable += 1
        if halted:
            n_refused += 1
            continue

        conservative_now = realized - _open_mae_sum()
        conservative_low = min(conservative_low, conservative_now)
        remaining = n_requestable - seen_requestable
        weight = remaining / n_requestable if n_requestable > 0 else 0.0

        if max_concurrent is not None and len(open_sims) >= max_concurrent:
            n_refused += 1
            continue

        decision = evaluate_risk_governor_v4(
            cfg,
            {
                "realized_day_pnl_pct": realized,
                "open_positions": [
                    {
                        "risk_pct": sim["risk_pct"],
                        "cluster": sim["cluster"],
                        "be_reached": sim["be_reached"],
                    }
                    for sim in open_sims
                ],
                "cluster_correlation": corr_lookup,
                "requested_risk_pct": event["requested_risk_pct"] * risk_scale,
                "remaining_opportunity_weight": weight,
                "intraday_conservative_dd_pct": max(0.0, -conservative_now),
                "overall_dd_pct": 0.0,
            },
        )
        if decision.action == ACTION_FLATTEN_HALT:
            # Flatten realizes each open position at its conservative mark
            # (lower-bound approximation of an immediate market close).
            for sim in open_sims:
                realized += -sim["risk_pct"] * sim["mae_abs_r"]
            open_sims.clear()
            conservative_low = min(conservative_low, realized)
            halted = True
            n_refused += 1
            continue
        if (
            decision.action in (ACTION_REFUSE, ACTION_FLOOR_REVIEW)
            or decision.approved_risk_pct <= 0.0
        ):
            n_refused += 1
            continue

        n_admitted += 1
        approved_risk_sum += decision.approved_risk_pct
        if event["filled"]:
            sim = {
                "exit_time": event["exit_time"],
                "risk_pct": decision.approved_risk_pct,
                "cluster": event["cluster"],
                "be_reached": event["be_reached"],
                "mae_abs_r": event["mae_abs_r"],
                "final_r": event["final_r"],
            }
            open_sims.append(sim)
            open_sims.sort(key=lambda s: s["exit_time"])
            max_open = max(max_open, len(open_sims))
            conservative_low = min(conservative_low, realized - _open_mae_sum())

    _close_matured(None)
    return {
        "day_pnl_pct": realized,
        "conservative_low_pct": conservative_low,
        "breached": conservative_low <= -cfg.daily_limit_pct + 1e-9,
        "halted_intraday": halted,
        "n_admitted": n_admitted,
        "n_refused": n_refused,
        "approved_risk_sum_pct": approved_risk_sum,
        "max_concurrent_open": max_open,
    }


# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------


def _percentile(sorted_values: Sequence[float], q: float) -> float | None:
    if not sorted_values:
        return None
    n = len(sorted_values)
    index = min(n - 1, max(0, math.ceil(q * n) - 1))
    return sorted_values[index]


def simulate_paths(
    day_records: Sequence[Mapping[str, Any]],
    cfg: GovernorConfigV4,
    *,
    n_paths: int,
    horizon_days: int,
    seed: int,
    risk_scale: float = 1.0,
    max_concurrent: int | None = None,
    correlation_overrides: Mapping[Any, float] | None = None,
) -> dict[str, Any]:
    """Bootstrap whole days with replacement and walk them under the governor."""

    if not day_records or n_paths <= 0 or horizon_days <= 0:
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "status": "no_day_records_or_empty_horizon",
            "n_day_records": len(day_records),
            "evidence_class": EVIDENCE_CLASS,
            **BOUNDARY,
        }

    corr_lookup = cluster_correlation_lookup(correlation_overrides)
    outcomes = [
        _walk_day(
            _prepare_events(record),
            cfg,
            risk_scale=risk_scale,
            max_concurrent=max_concurrent,
            corr_lookup=corr_lookup,
        )
        for record in day_records
    ]
    n_records = len(outcomes)

    breach_days_total = 0
    any_breach_paths = 0
    ruin_paths = 0
    halted_paths = 0
    day_pnl_sum = 0.0
    log_growth_sum = 0.0
    finals: list[float] = []
    total_path_days = n_paths * horizon_days

    for path in range(n_paths):
        equity = 0.0
        trough = 0.0
        any_breach = False
        halted_overall = False
        for day in range(horizon_days):
            index = _hash_index(seed, path, day, n_records)
            if halted_overall:
                continue  # zero PnL day under owner-review floor
            outcome = outcomes[index]
            if outcome["breached"]:
                breach_days_total += 1
                any_breach = True
            trough = min(trough, equity + outcome["conservative_low_pct"])
            equity += outcome["day_pnl_pct"]
            trough = min(trough, equity)
            day_pnl_sum += outcome["day_pnl_pct"]
            log_growth_sum += math.log1p(max(-0.99, outcome["day_pnl_pct"] / 100.0))
            if equity <= -cfg.overall_dd_floor_pct + 1e-9:
                halted_overall = True
        finals.append(round(equity, 10))
        if any_breach:
            any_breach_paths += 1
        if trough <= -OVERALL_RUIN_PCT + 1e-9:
            ruin_paths += 1
        if halted_overall:
            halted_paths += 1

    finals.sort()
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "simulated",
        "n_day_records": n_records,
        "n_paths": n_paths,
        "horizon_days": horizon_days,
        "seed": seed,
        "risk_scale": risk_scale,
        "max_concurrent": max_concurrent,
        "account_base_cash": ACCOUNT_BASE_CASH,
        "governor_config": asdict(cfg),
        "p_daily_breach_per_day": breach_days_total / total_path_days,
        "p_daily_breach_upper_ci95": wilson_upper_bound(breach_days_total, total_path_days),
        "p_any_daily_breach_horizon": any_breach_paths / n_paths,
        "p_overall_10pct": ruin_paths / n_paths,
        "e_daily_r": day_pnl_sum / total_path_days,
        "e_log_growth": log_growth_sum / total_path_days,
        "percentiles_final_equity_pct": {
            "p05": _percentile(finals, 0.05),
            "p25": _percentile(finals, 0.25),
            "p50": _percentile(finals, 0.50),
            "p75": _percentile(finals, 0.75),
            "p95": _percentile(finals, 0.95),
        },
        "counts": {
            "breach_days": breach_days_total,
            "total_path_days": total_path_days,
            "any_breach_paths": any_breach_paths,
            "overall_ruin_paths": ruin_paths,
            "overall_floor_halted_paths": halted_paths,
        },
        "day_outcomes": [
            {
                "campaign": record.get("campaign"),
                "trading_day": record.get("trading_day"),
                **{
                    key: (round(value, 8) if isinstance(value, float) else value)
                    for key, value in outcome.items()
                },
            }
            for record, outcome in zip(day_records, outcomes)
        ],
        "approximations": [
            "conservative_low_uses_full_trade_abs_mae_while_open",
            "counterfactual_missing_mae_defaults_to_full_stop_1r",
            "remaining_opportunity_weight_is_fraction_of_requestable_events_ahead",
            "day_walks_are_day_anchored_overall_floor_applied_at_path_level",
            "daily_breach_recorded_path_continues_next_day",
        ],
        "evidence_class": EVIDENCE_CLASS,
        **BOUNDARY,
    }


# ---------------------------------------------------------------------------
# Calibration (common random numbers across the theta grid)
# ---------------------------------------------------------------------------


def calibrate(
    day_records: Sequence[Mapping[str, Any]],
    *,
    base_cfg: GovernorConfigV4 | None = None,
    risk_scale_grid: Sequence[float] = DEFAULT_RISK_SCALE_GRID,
    kappa_grid: Sequence[float] = DEFAULT_KAPPA_GRID,
    reserve_grid: Sequence[float] = DEFAULT_RESERVE_GRID,
    target_p_daily: float = 0.001,
    n_paths: int = 2000,
    horizon_days: int = 30,
    seed: int = 20260610,
    count_caps: Sequence[int | None] = DEFAULT_COUNT_CAPS,
    correlation_overrides: Mapping[Any, float] | None = None,
) -> dict[str, Any]:
    """Grid-search theta = (risk_scale, kappa, reserve) under a ruin target.

    Feasibility: Wilson 95% upper bound of the per-day breach probability
    must be <= ``target_p_daily``. Among feasible thetas the winner maximizes
    ``e_log_growth`` (ties break toward lower risk_scale/kappa/reserve). All
    grid points share the same seed and day sequences (common random
    numbers), so differences are pure policy effects.
    """

    base = base_cfg or GovernorConfigV4()
    frontier: list[dict[str, Any]] = []
    for risk_scale in sorted(risk_scale_grid):
        for kappa in sorted(kappa_grid):
            for reserve in sorted(reserve_grid):
                cfg = replace(
                    base,
                    profit_recycle_fraction=kappa,
                    hard_reserve_pct=reserve,
                )
                result = simulate_paths(
                    day_records,
                    cfg,
                    n_paths=n_paths,
                    horizon_days=horizon_days,
                    seed=seed,
                    risk_scale=risk_scale,
                    correlation_overrides=correlation_overrides,
                )
                upper = result.get("p_daily_breach_upper_ci95", 1.0)
                frontier.append(
                    {
                        "risk_scale": risk_scale,
                        "kappa": kappa,
                        "reserve": reserve,
                        "p_daily_breach_per_day": result.get("p_daily_breach_per_day"),
                        "p_daily_breach_upper_ci95": upper,
                        "p_any_daily_breach_horizon": result.get("p_any_daily_breach_horizon"),
                        "p_overall_10pct": result.get("p_overall_10pct"),
                        "e_daily_r": result.get("e_daily_r"),
                        "e_log_growth": result.get("e_log_growth"),
                        "breach_days": (result.get("counts") or {}).get("breach_days"),
                        "total_path_days": (result.get("counts") or {}).get("total_path_days"),
                        "feasible": upper is not None and upper <= target_p_daily,
                    }
                )

    feasible_rows = [row for row in frontier if row["feasible"]]
    best: dict[str, Any] | None = None
    if feasible_rows:
        best = min(
            feasible_rows,
            key=lambda row: (
                -(row["e_log_growth"] if row["e_log_growth"] is not None else -math.inf),
                row["risk_scale"],
                row["kappa"],
                row["reserve"],
            ),
        )

    # Count-cap ablation on the best feasible theta (defaults if none).
    ablation_scale = best["risk_scale"] if best else 1.0
    ablation_cfg = replace(
        base,
        profit_recycle_fraction=best["kappa"] if best else base.profit_recycle_fraction,
        hard_reserve_pct=best["reserve"] if best else base.hard_reserve_pct,
    )
    ablation_rows: list[dict[str, Any]] = []
    baseline_row: dict[str, Any] | None = None
    for cap in count_caps:
        result = simulate_paths(
            day_records,
            ablation_cfg,
            n_paths=n_paths,
            horizon_days=horizon_days,
            seed=seed,
            risk_scale=ablation_scale,
            max_concurrent=cap,
            correlation_overrides=correlation_overrides,
        )
        row = {
            "max_concurrent_cap": cap,
            "p_daily_breach_per_day": result.get("p_daily_breach_per_day"),
            "p_daily_breach_upper_ci95": result.get("p_daily_breach_upper_ci95"),
            "p_overall_10pct": result.get("p_overall_10pct"),
            "e_daily_r": result.get("e_daily_r"),
            "e_log_growth": result.get("e_log_growth"),
        }
        if cap is None:
            baseline_row = row
        ablation_rows.append(row)
    for row in ablation_rows:
        if baseline_row is None:
            row["delta_e_log_growth_vs_uncapped"] = None
            row["delta_p_daily_breach_vs_uncapped"] = None
        else:
            row["delta_e_log_growth_vs_uncapped"] = (
                (row["e_log_growth"] or 0.0) - (baseline_row["e_log_growth"] or 0.0)
            )
            row["delta_p_daily_breach_vs_uncapped"] = (
                (row["p_daily_breach_per_day"] or 0.0)
                - (baseline_row["p_daily_breach_per_day"] or 0.0)
            )

    return {
        "schema_version": "ultimate_ruin_mc_calibration_v1",
        "target_p_daily": target_p_daily,
        "n_paths": n_paths,
        "horizon_days": horizon_days,
        "seed": seed,
        "common_random_numbers": True,
        "grid": {
            "risk_scale": sorted(risk_scale_grid),
            "kappa": sorted(kappa_grid),
            "reserve": sorted(reserve_grid),
        },
        "frontier": frontier,
        "n_feasible": len(feasible_rows),
        "best": best,
        "count_cap_ablation": {
            "theta": {
                "risk_scale": ablation_scale,
                "kappa": ablation_cfg.profit_recycle_fraction,
                "reserve": ablation_cfg.hard_reserve_pct,
            },
            "rows": ablation_rows,
        },
        "evidence_class": EVIDENCE_CLASS,
        **BOUNDARY,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--route-dir",
        action="append",
        required=True,
        help="Directory containing per-day replay ledgers; repeatable.",
    )
    parser.add_argument("--out", required=True, help="Output JSON report path.")
    parser.add_argument("--paths", type=int, default=2000)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--risk-scale", type=float, default=1.0)
    parser.add_argument("--calibrate", action="store_true", help="Also run the theta grid.")
    parser.add_argument("--target-p-daily", type=float, default=0.001)
    args = parser.parse_args(argv)

    records = build_day_records([Path(p) for p in args.route_dir])
    cfg = GovernorConfigV4()
    simulation = simulate_paths(
        records,
        cfg,
        n_paths=args.paths,
        horizon_days=args.horizon,
        seed=args.seed,
        risk_scale=args.risk_scale,
    )
    payload: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": utc_now_iso(),
        "route_dirs": list(args.route_dir),
        "n_day_records": len(records),
        "day_records_index": [
            {
                "campaign": record["campaign"],
                "trading_day": record["trading_day"],
                "n_events": record["n_events"],
                "n_filled_replay": record["n_filled_replay"],
                "n_risk_rejected_counterfactual": record["n_risk_rejected_counterfactual"],
            }
            for record in records
        ],
        "simulation": simulation,
        "evidence_class": EVIDENCE_CLASS,
        **BOUNDARY,
    }
    if args.calibrate:
        payload["calibration"] = calibrate(
            records,
            n_paths=args.paths,
            horizon_days=args.horizon,
            seed=args.seed,
            target_p_daily=args.target_p_daily,
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")

    headline = {
        "n_day_records": len(records),
        "p_daily_breach_per_day": simulation.get("p_daily_breach_per_day"),
        "p_daily_breach_upper_ci95": simulation.get("p_daily_breach_upper_ci95"),
        "p_any_daily_breach_horizon": simulation.get("p_any_daily_breach_horizon"),
        "p_overall_10pct": simulation.get("p_overall_10pct"),
        "e_daily_r": simulation.get("e_daily_r"),
        "e_log_growth": simulation.get("e_log_growth"),
        "percentiles_final_equity_pct": simulation.get("percentiles_final_equity_pct"),
        "out": str(out_path),
    }
    print(json.dumps(headline, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
