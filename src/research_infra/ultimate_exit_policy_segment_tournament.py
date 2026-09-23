"""Segment exit-policy tournament over replayed ordered M1 paths.

Reconstructs the post-fill M1 bar path for every filled (and counterfactually
filled risk-rejected) ORDERED_PATH_ORACLE row, replays a curated exit-policy
grid over each path with ``dynamic_execution_policy.simulate_policy`` (same-bar
conservative), and freezes a hierarchical segment -> exit-policy table:

    leaf  (asset_class x origin_family x session_bucket)
    ->    (asset_class x session_bucket)
    ->    (asset_class)
    ->    global
    ->    DEFAULT = incumbent momentum_exhaustion (trigger 1.0 / pullback 0.4
          / cap 2.0)

Promotion is deliberately hostile to overfitting: a challenger must beat the
incumbent in >= 60% of trading-day folds, never trail the incumbent by more
than 0.10 R/trade in any fold, and survive a per-trade paired sign test
(``bonferroni_survival.binomial_test``) Bonferroni-corrected across the
segment's full challenger grid at corrected p < 0.10. Everything else stays
on the incumbent (promoted=false rows are still recorded with reasons).

Boundary: research-only replay labeling. The path replay consumes post-asof
ordered price paths, which are replay labels
(``post_asof_timewarp_replay_label_not_decision_input``) — never decision
inputs. The frozen table's match keys (asset_class, origin_family,
session_bucket) are predecision segment keys only; no outcome field ever
becomes a match key. No broker calls, no paid APIs, no runtime writes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime
from pathlib import Path
from statistics import median, pstdev
from typing import Any

from src.research.dynamic_execution_policy import (
    PathObservation,
    PolicySpec,
    observation_from_ohlc,
    simulate_policy,
)
from src.research_infra.bonferroni_survival import binomial_test, bonferroni_correct
from src.research_infra.learned_edge_dataset_builder import (
    ASSET_CLASS_BY_SYMBOL,
    as_float,
    discover_partition_ledgers,
    read_jsonl,
)

SCHEMA_VERSION = "exit_policy_segment_table_v1"
EVIDENCE_CLASS = "post_asof_timewarp_replay_label_not_decision_input"

# Evidence/deployment geometry contract: a promoted row's evidence is for the
# exact tested PolicySpec, not for the live policy family it maps onto. Every
# promoted segment is stamped ``params_fidelity: exact_params_required`` and
# carries the full tested PolicySpec field map in ``params``; downstream
# routing must not steer live policy selection unless the execution side
# actually consumes those params (ExitPolicyConfigV4.from_policy_params).
PARAMS_FIDELITY_EXACT = "exact_params_required"

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}

DEFAULT_M1_ROOT = Path("data/mt5_research_exports")

INCUMBENT_POLICY_ID = "incumbent"
FAMILY_MOMENTUM = "momentum"
FAMILY_TRAILING = "trailing"
FAMILY_FIXED_TARGET = "fixed_target"
FAMILY_BE_ONLY = "be_only"

SEGMENT_LEVELS = ("leaf", "asset_class_session", "asset_class", "global")

# Promotion thresholds (selection is incumbent-default; see module docstring).
DEFAULT_MIN_LEAF_N = 40
DEFAULT_MIN_DAYS = 6
DEFAULT_BEAT_FOLD_FRACTION = 0.60
DEFAULT_MAX_FOLD_DEFICIT_R = 0.10
DEFAULT_PROMOTE_CORRECTED_P = 0.10
_DELTA_EPS = 1e-9

# Curated grid axes. The incumbent momentum_exhaustion cell
# (trigger 1.0 / pullback 0.4 / cap 2.0) is policy_id ``incumbent``.
MOMENTUM_TRIGGER_GRID = (0.75, 1.0, 1.25)
MOMENTUM_PULLBACK_GRID = (0.3, 0.4, 0.5)
MOMENTUM_CAP_GRID = (1.5, 2.0, 2.5, 3.0)
# V2 sub-1R extension: the exit-oracle bound (mean +0.72R over 34,180 paths,
# MFE median 0.659R) and the (mfe, mae) pre-screen put the payoff region
# BELOW the V1 floor — trail(0.5, 0.35) idealized +0.05R/trade vs
# trail(0.25, 0.15)+abort idealized +0.46R/trade. Bar-discretization losses
# are measured by the replay, never assumed.
TRAILING_TRIGGER_GRID = (0.2, 0.25, 0.3, 0.4, 0.5, 1.0)
TRAILING_GAP_GRID = (0.1, 0.15, 0.2, 0.25, 0.35, 0.5)
TRAILING_CAP_GRID = (2.0, 4.0, 6.0)
FIXED_TARGET_GRID = (1.5, 2.0, 2.5, 3.0)
BE_ONLY_TRIGGER_GRID = (0.5, 0.75, 1.0)
BE_ONLY_FINAL_TARGET_R = 2.0
ABORT_ADVERSE_GRID = (0.4, 0.5, 0.6)
ABORT_MFE_FLOOR_GRID = (0.2, 0.25)
DEFAULT_ABORT_CROSS_TOP_N = 3

INCUMBENT_SPEC = PolicySpec(
    name=INCUMBENT_POLICY_ID,
    final_target_r=2.0,
    trailing_trigger_r=1.0,
    trailing_gap_r=0.4,
    description=(
        "Incumbent momentum_exhaustion: trail after 1.0R trigger with 0.4R "
        "pullback gap, capped at 2.0R (current production primary)."
    ),
)

# EXTENSION HOOK: early-loss-abort crossing only activates when
# ``PolicySpec`` carries the abort primitives (added by the abort-extension
# route). When absent, the tournament runs the base grid only and records the
# gap in result notes — no abort spec is fabricated.
_ABORT_FIELD_NAMES = ("abort_adverse_r", "abort_adverse_max_mfe_r", "abort_stop_r")
POLICY_SPEC_SUPPORTS_ABORT = set(_ABORT_FIELD_NAMES).issubset(
    {spec_field.name for spec_field in fields(PolicySpec)}
)


def _num(value: float) -> str:
    return f"{value:g}".replace(".", "p").replace("-", "n")


@dataclass(frozen=True)
class GridPolicy:
    """One tournament grid entry: stable id + family + frozen PolicySpec."""

    policy_id: str
    family: str
    spec: PolicySpec


def _momentum_keep(trigger: float, pullback: float, cap: float) -> bool:
    """Curated momentum prune: pullback stays below 0.6x trigger and the cap
    sits between trigger+0.6R and trigger+2.0R (drops degenerate cells where
    the pullback nearly equals the trigger or the cap is unreachable-tight)."""

    if pullback > 0.6 * trigger + 1e-9:
        return False
    if cap < trigger + 0.6 - 1e-9:
        return False
    if cap > trigger + 2.0 + 1e-9:
        return False
    return True


def _build_default_grid() -> tuple[GridPolicy, ...]:
    entries: list[GridPolicy] = [
        GridPolicy(INCUMBENT_POLICY_ID, FAMILY_MOMENTUM, INCUMBENT_SPEC)
    ]
    for trigger in MOMENTUM_TRIGGER_GRID:
        for pullback in MOMENTUM_PULLBACK_GRID:
            for cap in MOMENTUM_CAP_GRID:
                if (trigger, pullback, cap) == (1.0, 0.4, 2.0):
                    continue  # the incumbent cell
                if not _momentum_keep(trigger, pullback, cap):
                    continue
                policy_id = f"momentum_t{_num(trigger)}_p{_num(pullback)}_c{_num(cap)}"
                entries.append(
                    GridPolicy(
                        policy_id,
                        FAMILY_MOMENTUM,
                        PolicySpec(
                            name=policy_id,
                            final_target_r=cap,
                            trailing_trigger_r=trigger,
                            trailing_gap_r=pullback,
                        ),
                    )
                )
    for trigger in TRAILING_TRIGGER_GRID:
        for gap in TRAILING_GAP_GRID:
            for cap in TRAILING_CAP_GRID:
                policy_id = f"trailing_t{_num(trigger)}_g{_num(gap)}_c{_num(cap)}"
                entries.append(
                    GridPolicy(
                        policy_id,
                        FAMILY_TRAILING,
                        PolicySpec(
                            name=policy_id,
                            final_target_r=cap,
                            trailing_trigger_r=trigger,
                            trailing_gap_r=gap,
                        ),
                    )
                )
    for target in FIXED_TARGET_GRID:
        policy_id = f"fixed_target_{_num(target)}r"
        entries.append(
            GridPolicy(
                policy_id,
                FAMILY_FIXED_TARGET,
                PolicySpec(name=policy_id, final_target_r=target),
            )
        )
    for trigger in BE_ONLY_TRIGGER_GRID:
        policy_id = f"be_only_t{_num(trigger)}"
        entries.append(
            GridPolicy(
                policy_id,
                FAMILY_BE_ONLY,
                PolicySpec(
                    name=policy_id,
                    final_target_r=BE_ONLY_FINAL_TARGET_R,
                    tp1_r=trigger,
                    partial_close_ratio=0.0,
                    move_stop_to_be_on_tp1=True,
                ),
            )
        )
    return tuple(entries)


DEFAULT_POLICY_GRID: tuple[GridPolicy, ...] = _build_default_grid()


def default_grid() -> tuple[GridPolicy, ...]:
    return DEFAULT_POLICY_GRID


def abort_crossed_grid(base_entries: Iterable[GridPolicy]) -> tuple[GridPolicy, ...]:
    """Cross base specs with the early-loss-abort stop-tighten grid.

    ``abort_stop_r = -abort_adverse_r`` locks the loss at the adverse trigger
    level (the headroom-audit "tighten before progress" rule). Returns ``()``
    when PolicySpec lacks the abort primitives (extension hook above).
    """

    if not POLICY_SPEC_SUPPORTS_ABORT:
        return ()
    crossed: list[GridPolicy] = []
    for entry in base_entries:
        for adverse in ABORT_ADVERSE_GRID:
            for mfe_floor in ABORT_MFE_FLOOR_GRID:
                policy_id = f"{entry.policy_id}__abort_a{_num(adverse)}_m{_num(mfe_floor)}"
                crossed.append(
                    GridPolicy(
                        policy_id,
                        entry.family,
                        replace(
                            entry.spec,
                            name=policy_id,
                            abort_adverse_r=adverse,
                            abort_adverse_max_mfe_r=mfe_floor,
                            abort_stop_r=-adverse,
                        ),
                    )
                )
    return tuple(crossed)


# ---------------------------------------------------------------------------
# Path dataset construction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PathRow:
    """One replayable post-fill path with predecision segment keys."""

    candidate_id: str
    symbol: str
    trading_day: str
    side: str
    row_kind: str  # "filled" | "counterfactual_filled"
    asset_class: str
    origin_family: str
    session_bucket: str
    entry: float
    stop: float
    fill_time_utc: str
    observations: tuple[PathObservation, ...]


@dataclass
class PathDataset:
    rows: list[PathRow] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)
    missing_m1_files: list[str] = field(default_factory=list)
    consumed_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _count(counters: dict[str, int], key: str) -> None:
    counters[key] = counters.get(key, 0) + 1


def _m1_time_key(value: Any) -> str | None:
    """Normalize an ISO fill time to the M1 CSV 'YYYY-MM-DD HH:MM:SS' key."""

    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _m1_file_for(m1_root: Path, symbol: str, trading_day: str) -> Path:
    month_token = trading_day[:7].replace("-", "")
    primary = m1_root / f"bridge_ftmo_m1_{month_token}" / f"{symbol}_M1.csv"
    if primary.exists():
        return primary
    # Universe-expansion symbols live in their own monthly packages
    # (bridge_ftmo_ext_m1_*); fall back so new-symbol paths reconstruct.
    ext = m1_root / f"bridge_ftmo_ext_m1_{month_token}" / f"{symbol}_M1.csv"
    return ext if ext.exists() else primary


def _load_m1_days(path: Path, days: set[str]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {day: [] for day in days}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            time_text = str(row.get("time") or "").strip()
            day = time_text[:10]
            if day in grouped:
                grouped[day].append(row)
    for day in grouped:
        grouped[day].sort(key=lambda bar: str(bar.get("time") or ""))
    return grouped


def build_path_dataset(
    route_dirs: Iterable[Path | str],
    *,
    m1_root: Path | str = DEFAULT_M1_ROOT,
    include_missed: bool = False,
    day_filter: set[str] | None = None,
) -> PathDataset:
    """Reconstruct post-fill M1 paths for filled + counterfactually filled
    oracle rows across the given route dirs. Missing M1 files are counted per
    skipped row and reported (never silently dropped).

    ``include_missed=True`` additionally reconstructs counterfactual paths for
    selector/scheduler-MISSED candidates (the majority of the learning
    universe): geometry from the candidate row (limit = entry_reference else
    entry_price), fill derived by first limit-touch scan over M1 bars after
    decision time — the same fill semantics the missed-opportunity scorer
    uses. Used by the V2+ relabeler; the tournament's policy SELECTION
    defaults to fills-only."""

    m1_root = Path(m1_root)
    dataset = PathDataset()
    counters = dataset.counters

    ledger_sets, discovery_notes = discover_partition_ledgers(route_dirs)
    dataset.notes.extend(discovery_notes)

    pending: list[dict[str, Any]] = []
    needed_days: dict[tuple[str, str], set[str]] = {}

    for ledger_set in ledger_sets:
        if day_filter is not None:
            token = str(ledger_set.trading_day_token)
            day_iso = f"{token[:4]}-{token[4:6]}-{token[6:8]}" if len(token) >= 8 else token
            if day_iso not in day_filter and token not in day_filter:
                continue
        oracle_path = ledger_set.paths.get("oracle")
        candidate_path = ledger_set.paths.get("candidate")
        if oracle_path is None or candidate_path is None:
            _count(counters, "ledger_set_missing_oracle_or_candidate")
            dataset.notes.append(
                f"day_{ledger_set.trading_day_token}_missing_oracle_or_candidate_ledger"
            )
            continue
        dataset.consumed_files.append(str(oracle_path))
        dataset.consumed_files.append(str(candidate_path))

        candidate_index: dict[str, Mapping[str, Any]] = {}
        for candidate_row in read_jsonl(candidate_path):
            candidate_id = str(candidate_row.get("candidate_id") or "")
            if candidate_id:
                candidate_index.setdefault(candidate_id, candidate_row)

        for oracle_row in read_jsonl(oracle_path):
            _count(counters, "oracle_rows_total")
            fill_status = str(oracle_row.get("fill_status") or "")
            counterfactual_status = str(
                oracle_row.get("counterfactual_fill_status") or ""
            )
            if fill_status.startswith("filled"):
                row_kind = "filled"
                _count(counters, "filled_rows")
            elif fill_status.startswith("not_sent") and counterfactual_status.startswith("filled"):
                row_kind = "counterfactual_filled"
                _count(counters, "counterfactual_filled_rows")
            else:
                _count(counters, "not_filled_rows")
                continue

            symbol = str(oracle_row.get("symbol") or "").strip()
            trading_day = str(oracle_row.get("trading_day") or "").strip()
            side = str(oracle_row.get("side") or "").strip().upper()
            candidate_id = str(oracle_row.get("candidate_id") or "")
            if not symbol or len(trading_day) != 10 or side not in {"LONG", "SHORT"}:
                _count(counters, "missing_identity_fields")
                continue

            fill_time_key = _m1_time_key(oracle_row.get("fill_time_utc"))
            if fill_time_key is None:
                _count(counters, "bad_fill_time")
                continue

            entry = as_float(oracle_row.get("entry_price"))
            if entry is None:
                entry = as_float(oracle_row.get("fill_price"))
            stop = as_float(oracle_row.get("stop_price"))
            if entry is None or stop is None:
                _count(counters, "missing_price_fields")
                continue
            if abs(entry - stop) <= 0:
                _count(counters, "invalid_entry_stop")
                continue

            candidate_row = candidate_index.get(candidate_id)
            if candidate_row is None:
                _count(counters, "candidate_join_missing")
                continue
            origin_family = str(candidate_row.get("origin_family") or "").strip().lower()
            if not origin_family:
                origin_family = (
                    str(candidate_row.get("candidate_origin_family") or "")
                    .strip()
                    .lower()
                    .removeprefix("origin_")
                )
            session_bucket = str(
                candidate_row.get("session_bucket")
                or candidate_row.get("route_session")
                or candidate_row.get("session")
                or ""
            ).strip().lower()
            if not origin_family or not session_bucket:
                _count(counters, "segment_keys_missing")
                continue
            asset_class = ASSET_CLASS_BY_SYMBOL.get(symbol)
            if asset_class is None:
                _count(counters, "unknown_asset_class")
                continue

            month_token = trading_day[:7].replace("-", "")
            needed_days.setdefault((symbol, month_token), set()).add(trading_day)
            pending.append(
                {
                    "candidate_id": candidate_id,
                    "symbol": symbol,
                    "trading_day": trading_day,
                    "side": side,
                    "row_kind": row_kind,
                    "asset_class": asset_class,
                    "origin_family": origin_family,
                    "session_bucket": session_bucket,
                    "entry": float(entry),
                    "stop": float(stop),
                    "fill_time_key": fill_time_key,
                }
            )

        if include_missed and ledger_set.paths.get("missed") is not None:
            for missed_row in read_jsonl(ledger_set.paths["missed"]):
                _count(counters, "missed_rows_total")
                close_reason = str(missed_row.get("opportunity_close_reason") or "")
                if (
                    missed_row.get("opportunity_path_scored") is not True
                    or not close_reason
                    or close_reason == "not_filled_no_trade"
                    or close_reason.startswith("source_required")
                ):
                    _count(counters, "missed_rows_not_counterfactually_filled")
                    continue
                candidate_id = str(missed_row.get("candidate_id") or "")
                candidate_row = candidate_index.get(candidate_id)
                if candidate_row is None:
                    _count(counters, "missed_candidate_join_missing")
                    continue
                symbol = str(missed_row.get("symbol") or candidate_row.get("symbol") or "").strip()
                trading_day = str(candidate_row.get("trading_day") or ledger_set.trading_day_token).strip()
                if len(trading_day) == 8:
                    trading_day = f"{trading_day[:4]}-{trading_day[4:6]}-{trading_day[6:]}"
                side = str(missed_row.get("side") or candidate_row.get("side") or "").strip().upper()
                decision_key = _m1_time_key(
                    missed_row.get("decision_time_utc") or candidate_row.get("decision_time_utc")
                )
                limit = as_float(candidate_row.get("entry_reference"))
                if limit is None:
                    limit = as_float(candidate_row.get("entry_price"))
                stop = as_float(candidate_row.get("stop_loss"))
                if (
                    not symbol
                    or len(trading_day) != 10
                    or side not in {"LONG", "SHORT"}
                    or decision_key is None
                    or limit is None
                    or stop is None
                    or abs(limit - stop) <= 0
                ):
                    _count(counters, "missed_rows_missing_fields")
                    continue
                origin_family = str(candidate_row.get("origin_family") or "").strip().lower()
                if not origin_family:
                    origin_family = (
                        str(candidate_row.get("candidate_origin_family") or "")
                        .strip().lower().removeprefix("origin_")
                    )
                session_bucket = str(
                    candidate_row.get("session_bucket")
                    or candidate_row.get("route_session")
                    or candidate_row.get("session")
                    or ""
                ).strip().lower()
                asset_class = ASSET_CLASS_BY_SYMBOL.get(symbol)
                if not origin_family or not session_bucket or asset_class is None:
                    _count(counters, "missed_rows_segment_keys_missing")
                    continue
                month_token = trading_day[:7].replace("-", "")
                needed_days.setdefault((symbol, month_token), set()).add(trading_day)
                pending.append(
                    {
                        "candidate_id": candidate_id,
                        "symbol": symbol,
                        "trading_day": trading_day,
                        "side": side,
                        "row_kind": "missed_counterfactual_filled",
                        "asset_class": asset_class,
                        "origin_family": origin_family,
                        "session_bucket": session_bucket,
                        "entry": float(limit),
                        "stop": float(stop),
                        "fill_time_key": decision_key,
                        "missed_fill_scan": True,
                    }
                )

    # Second pass: load only the (symbol, month, day) bars actually needed.
    bars_by_file: dict[tuple[str, str], dict[str, list[dict[str, str]]] | None] = {}
    for (symbol, month_token), days in sorted(needed_days.items()):
        sample_day = sorted(days)[0]
        m1_path = _m1_file_for(m1_root, symbol, sample_day)
        if not m1_path.exists():
            bars_by_file[(symbol, month_token)] = None
            dataset.missing_m1_files.append(str(m1_path))
            continue
        bars_by_file[(symbol, month_token)] = _load_m1_days(m1_path, set(days))

    for item in pending:
        month_token = item["trading_day"][:7].replace("-", "")
        file_days = bars_by_file.get((item["symbol"], month_token))
        if file_days is None:
            _count(counters, "m1_file_missing")
            continue
        day_bars = file_days.get(item["trading_day"]) or []
        post_fill = [
            bar
            for bar in day_bars
            if str(bar.get("time") or "") >= item["fill_time_key"]
        ]
        if item.get("missed_fill_scan"):
            # Derive the counterfactual fill: first bar touching the limit
            # after decision time (missed-opportunity scorer semantics).
            fill_index = None
            for index, bar in enumerate(post_fill):
                low = as_float(bar.get("low"))
                high = as_float(bar.get("high"))
                if low is None or high is None:
                    continue
                if (item["side"] == "LONG" and low <= item["entry"]) or (
                    item["side"] == "SHORT" and high >= item["entry"]
                ):
                    fill_index = index
                    break
            if fill_index is None:
                _count(counters, "missed_limit_never_touched")
                continue
            post_fill = post_fill[fill_index:]
        if not post_fill:
            _count(counters, "no_m1_bars_after_fill")
            continue
        observations = tuple(
            observation_from_ohlc(
                index=index,
                row=bar,
                entry=item["entry"],
                stop=item["stop"],
                side=item["side"],
            )
            for index, bar in enumerate(post_fill)
        )
        dataset.rows.append(
            PathRow(
                candidate_id=item["candidate_id"],
                symbol=item["symbol"],
                trading_day=item["trading_day"],
                side=item["side"],
                row_kind=item["row_kind"],
                asset_class=item["asset_class"],
                origin_family=item["origin_family"],
                session_bucket=item["session_bucket"],
                entry=item["entry"],
                stop=item["stop"],
                fill_time_utc=item["fill_time_key"],
                observations=observations,
            )
        )
        _count(counters, "path_rows_built")

    return dataset


# ---------------------------------------------------------------------------
# Tournament
# ---------------------------------------------------------------------------

def segment_id_for(
    level: str,
    asset_class: str | None,
    origin_family: str | None,
    session_bucket: str | None,
) -> str:
    return "|".join(
        (level, asset_class or "*", origin_family or "*", session_bucket or "*")
    )


def _segment_keys_for(
    asset_class: str,
    origin_family: str,
    session_bucket: str,
) -> tuple[tuple[str, str | None, str | None, str | None], ...]:
    return (
        ("leaf", asset_class, origin_family, session_bucket),
        ("asset_class_session", asset_class, None, session_bucket),
        ("asset_class", asset_class, None, None),
        ("global", None, None, None),
    )


@dataclass
class TournamentResult:
    policies: dict[str, dict[str, Any]] = field(default_factory=dict)
    trade_rows: list[dict[str, Any]] = field(default_factory=list)
    fold_rows: list[dict[str, Any]] = field(default_factory=list)
    n_path_rows: int = 0
    notes: list[str] = field(default_factory=list)


def run_tournament(
    path_rows: Iterable[PathRow],
    *,
    policy_grid: Iterable[GridPolicy] | None = None,
    abort_cross_top_n: int = DEFAULT_ABORT_CROSS_TOP_N,
    same_bar_policy: str = "conservative",
) -> TournamentResult:
    """Replay the policy grid over every path row.

    Phase 1 replays the base grid; phase 2 (when PolicySpec carries the
    early-loss-abort primitives) crosses the best ``abort_cross_top_n`` base
    specs by overall mean R with the abort grid and replays those too.
    """

    grid = list(policy_grid) if policy_grid is not None else list(DEFAULT_POLICY_GRID)
    if not any(entry.policy_id == INCUMBENT_POLICY_ID for entry in grid):
        raise ValueError("policy grid must include the incumbent policy")
    rows = list(path_rows)
    result = TournamentResult(n_path_rows=len(rows))

    def _replay(entries: Iterable[GridPolicy]) -> None:
        for entry in entries:
            result.policies[entry.policy_id] = {
                "family": entry.family,
                "params": asdict(entry.spec),
            }
            for row in rows:
                replay = simulate_policy(
                    entry.spec, row.observations, same_bar_policy=same_bar_policy
                )
                if replay.replay_status != "replayed" or replay.final_r is None:
                    result.notes.append(
                        f"non_replayed_{entry.policy_id}_{row.trading_day}_{row.candidate_id}"
                    )
                    continue
                final_r = float(replay.final_r)
                mfe_r = float(replay.mfe_r) if replay.mfe_r is not None else final_r
                result.trade_rows.append(
                    {
                        "trade_key": f"{row.trading_day}|{row.candidate_id}",
                        "candidate_id": row.candidate_id,
                        "trading_day": row.trading_day,
                        "symbol": row.symbol,
                        "row_kind": row.row_kind,
                        "asset_class": row.asset_class,
                        "origin_family": row.origin_family,
                        "session_bucket": row.session_bucket,
                        "policy_id": entry.policy_id,
                        "family": entry.family,
                        "final_r": final_r,
                        "mfe_r": mfe_r,
                        "giveback_r": max(0.0, mfe_r - final_r),
                        "exit_reason": replay.exit_reason,
                    }
                )

    _replay(grid)

    if POLICY_SPEC_SUPPORTS_ABORT and abort_cross_top_n > 0 and rows:
        sums: dict[str, list[float]] = {}
        for trade_row in result.trade_rows:
            sums.setdefault(trade_row["policy_id"], []).append(trade_row["final_r"])
        ranked = sorted(
            ((sum(values) / len(values), policy_id) for policy_id, values in sums.items()),
            key=lambda item: (-item[0], item[1]),
        )
        top_ids = [policy_id for _, policy_id in ranked[: int(abort_cross_top_n)]]
        base_by_id = {entry.policy_id: entry for entry in grid}
        crossed = abort_crossed_grid(
            base_by_id[policy_id] for policy_id in top_ids if policy_id in base_by_id
        )
        crossed = tuple(
            entry for entry in crossed if entry.policy_id not in result.policies
        )
        result.notes.append(
            "abort_cross_phase_applied_to_" + ",".join(top_ids)
        )
        _replay(crossed)
    elif not POLICY_SPEC_SUPPORTS_ABORT:
        result.notes.append(
            "abort_cross_phase_skipped_policy_spec_missing_abort_fields"
        )

    # Fold aggregates per (segment level, policy, trading_day).
    fold_acc: dict[tuple[str, str, str], dict[str, float]] = {}
    fold_meta: dict[tuple[str, str, str], dict[str, Any]] = {}
    for trade_row in result.trade_rows:
        for level, asset_class, origin_family, session_bucket in _segment_keys_for(
            trade_row["asset_class"],
            trade_row["origin_family"],
            trade_row["session_bucket"],
        ):
            segment_id = segment_id_for(level, asset_class, origin_family, session_bucket)
            key = (segment_id, trade_row["policy_id"], trade_row["trading_day"])
            acc = fold_acc.setdefault(key, {"n": 0.0, "sum_r": 0.0})
            acc["n"] += 1.0
            acc["sum_r"] += trade_row["final_r"]
            fold_meta.setdefault(
                key,
                {
                    "segment_level": level,
                    "asset_class": asset_class,
                    "origin_family": origin_family,
                    "session_bucket": session_bucket,
                    "family": trade_row["family"],
                },
            )
    for key in sorted(fold_acc):
        segment_id, policy_id, trading_day = key
        acc = fold_acc[key]
        meta = fold_meta[key]
        result.fold_rows.append(
            {
                "segment_id": segment_id,
                "segment_level": meta["segment_level"],
                "asset_class": meta["asset_class"],
                "origin_family": meta["origin_family"],
                "session_bucket": meta["session_bucket"],
                "policy_id": policy_id,
                "family": meta["family"],
                "trading_day": trading_day,
                "n_trades": int(acc["n"]),
                "fold_mean_r": acc["sum_r"] / acc["n"],
            }
        )
    return result


# ---------------------------------------------------------------------------
# Selection -> frozen segment table
# ---------------------------------------------------------------------------

def _robust_score(fold_means: list[float], givebacks: list[float]) -> float:
    spread = pstdev(givebacks) if len(givebacks) > 1 else 0.0
    return median(fold_means) + 0.5 * min(fold_means) - 0.25 * spread


def select_segment_policies(
    results: TournamentResult,
    *,
    min_leaf_n: int = DEFAULT_MIN_LEAF_N,
    min_days: int = DEFAULT_MIN_DAYS,
    beat_fold_fraction: float = DEFAULT_BEAT_FOLD_FRACTION,
    max_fold_deficit_r: float = DEFAULT_MAX_FOLD_DEFICIT_R,
    promote_corrected_p: float = DEFAULT_PROMOTE_CORRECTED_P,
    source_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze the hierarchical segment -> exit-policy table.

    DEFAULT = incumbent everywhere; a challenger is promoted for a segment
    only when it clears sample floors, fold-dominance hard filters, and the
    Bonferroni-corrected paired sign test (corrected p < promote_corrected_p).
    Non-promoted segments are recorded with explicit reasons.
    """

    if INCUMBENT_POLICY_ID not in results.policies:
        raise ValueError("tournament results missing the incumbent policy")

    # segment -> policy -> {trade_key: (final_r, giveback_r)}
    per_segment: dict[str, dict[str, dict[str, tuple[float, float]]]] = {}
    segment_match: dict[str, dict[str, Any]] = {}
    segment_level: dict[str, str] = {}
    for trade_row in results.trade_rows:
        for level, asset_class, origin_family, session_bucket in _segment_keys_for(
            trade_row["asset_class"],
            trade_row["origin_family"],
            trade_row["session_bucket"],
        ):
            segment_id = segment_id_for(level, asset_class, origin_family, session_bucket)
            segment_level[segment_id] = level
            segment_match.setdefault(
                segment_id,
                {
                    "asset_class": asset_class,
                    "origin_family": origin_family,
                    "session_bucket": session_bucket,
                },
            )
            per_segment.setdefault(segment_id, {}).setdefault(
                trade_row["policy_id"], {}
            )[trade_row["trade_key"]] = (
                trade_row["final_r"],
                trade_row["giveback_r"],
            )

    incumbent_meta = results.policies[INCUMBENT_POLICY_ID]
    level_rank = {level: rank for rank, level in enumerate(SEGMENT_LEVELS)}
    segment_rows: list[dict[str, Any]] = []

    for segment_id in sorted(
        per_segment, key=lambda sid: (level_rank.get(segment_level[sid], 99), sid)
    ):
        policies = per_segment[segment_id]
        incumbent_trades = policies.get(INCUMBENT_POLICY_ID, {})
        trade_keys = sorted(incumbent_trades)
        n_trades = len(trade_keys)
        days = sorted({key.split("|", 1)[0] for key in trade_keys})
        n_days = len(days)
        level = segment_level[segment_id]
        match = segment_match[segment_id]

        incumbent_by_day: dict[str, list[float]] = {}
        incumbent_givebacks: list[float] = []
        for key in trade_keys:
            final_r, giveback_r = incumbent_trades[key]
            incumbent_by_day.setdefault(key.split("|", 1)[0], []).append(final_r)
            incumbent_givebacks.append(giveback_r)
        incumbent_fold_means = [
            sum(values) / len(values) for _, values in sorted(incumbent_by_day.items())
        ]
        incumbent_robust = (
            _robust_score(incumbent_fold_means, incumbent_givebacks)
            if incumbent_fold_means
            else None
        )

        base_row = {
            "segment_id": segment_id,
            "match": dict(match),
            "fallback_level": level,
            "n_trades": n_trades,
            "n_days": n_days,
        }

        if n_trades < min_leaf_n or n_days < min_days:
            reasons = []
            if n_trades < min_leaf_n:
                reasons.append(f"insufficient_trades_{n_trades}_lt_{min_leaf_n}")
            if n_days < min_days:
                reasons.append(f"insufficient_days_{n_days}_lt_{min_days}")
            segment_rows.append(
                {
                    **base_row,
                    "policy_id": INCUMBENT_POLICY_ID,
                    "family": incumbent_meta["family"],
                    "params": dict(incumbent_meta["params"]),
                    "robust_score": incumbent_robust,
                    "incumbent_delta_r_per_trade": 0.0,
                    "corrected_p": None,
                    "promoted": False,
                    "reasons": reasons,
                }
            )
            continue

        challenger_ids = sorted(pid for pid in policies if pid != INCUMBENT_POLICY_ID)
        challenger_stats: list[dict[str, Any]] = []
        raw_p_values: list[float] = []
        for policy_id in challenger_ids:
            challenger_trades = policies[policy_id]
            paired_keys = [key for key in trade_keys if key in challenger_trades]
            if len(paired_keys) != n_trades:
                challenger_stats.append({"policy_id": policy_id, "evaluable": False})
                raw_p_values.append(float("nan"))
                continue
            by_day: dict[str, list[float]] = {}
            givebacks: list[float] = []
            deltas: list[float] = []
            for key in paired_keys:
                final_r, giveback_r = challenger_trades[key]
                by_day.setdefault(key.split("|", 1)[0], []).append(final_r)
                givebacks.append(giveback_r)
                deltas.append(final_r - incumbent_trades[key][0])
            fold_means_by_day = {
                day: sum(values) / len(values) for day, values in by_day.items()
            }
            fold_means = [fold_means_by_day[day] for day in days]
            incumbent_means_by_day = {
                day: sum(values) / len(values)
                for day, values in incumbent_by_day.items()
            }
            beat_folds = sum(
                1
                for day in days
                if fold_means_by_day[day] > incumbent_means_by_day[day] + _DELTA_EPS
            )
            worst_fold_deficit = max(
                incumbent_means_by_day[day] - fold_means_by_day[day] for day in days
            )
            wins = sum(1 for delta in deltas if delta > _DELTA_EPS)
            losses = sum(1 for delta in deltas if delta < -_DELTA_EPS)
            n_effective = wins + losses
            raw_p = (
                binomial_test(wins, n_effective, 0.5) if n_effective > 0 else float("nan")
            )
            mean_delta = sum(deltas) / len(deltas)
            hard_pass = (
                n_days > 0
                and beat_folds / n_days >= beat_fold_fraction - _DELTA_EPS
                and worst_fold_deficit <= max_fold_deficit_r + _DELTA_EPS
                and mean_delta > _DELTA_EPS
                and n_effective > 0
                and wins > n_effective / 2.0
            )
            challenger_stats.append(
                {
                    "policy_id": policy_id,
                    "evaluable": True,
                    "robust_score": _robust_score(fold_means, givebacks),
                    "mean_delta": mean_delta,
                    "beat_folds": beat_folds,
                    "worst_fold_deficit": worst_fold_deficit,
                    "raw_p": raw_p,
                    "hard_pass": hard_pass,
                }
            )
            raw_p_values.append(raw_p)

        corrected = bonferroni_correct(raw_p_values)
        promotable: list[dict[str, Any]] = []
        best_corrected: tuple[float, str] | None = None
        for stats, corrected_p in zip(challenger_stats, corrected):
            if not stats.get("evaluable"):
                continue
            stats["corrected_p"] = corrected_p
            if math.isfinite(corrected_p) and (
                best_corrected is None or corrected_p < best_corrected[0]
            ):
                best_corrected = (corrected_p, stats["policy_id"])
            if (
                stats["hard_pass"]
                and math.isfinite(corrected_p)
                and corrected_p < promote_corrected_p
            ):
                promotable.append(stats)

        if promotable:
            winner = sorted(
                promotable, key=lambda stats: (-stats["robust_score"], stats["policy_id"])
            )[0]
            winner_meta = results.policies[winner["policy_id"]]
            segment_rows.append(
                {
                    **base_row,
                    "policy_id": winner["policy_id"],
                    "family": winner_meta["family"],
                    # Full tested PolicySpec field map (asdict of the replayed
                    # spec). Evidence holds for these exact params only.
                    "params": dict(winner_meta["params"]),
                    "params_fidelity": PARAMS_FIDELITY_EXACT,
                    "robust_score": winner["robust_score"],
                    "incumbent_delta_r_per_trade": winner["mean_delta"],
                    "corrected_p": winner["corrected_p"],
                    "promoted": True,
                    "reasons": [
                        f"beats_incumbent_in_{winner['beat_folds']}_of_{n_days}_folds",
                        f"worst_fold_deficit_r_{winner['worst_fold_deficit']:.4f}",
                        f"corrected_p_{winner['corrected_p']:.6f}_lt_{promote_corrected_p}",
                    ],
                }
            )
        else:
            reasons = ["no_challenger_passed_hard_filters_and_corrected_p"]
            if best_corrected is not None:
                reasons.append(
                    f"best_corrected_p_{best_corrected[0]:.6f}_policy_{best_corrected[1]}"
                )
            segment_rows.append(
                {
                    **base_row,
                    "policy_id": INCUMBENT_POLICY_ID,
                    "family": incumbent_meta["family"],
                    "params": dict(incumbent_meta["params"]),
                    "robust_score": incumbent_robust,
                    "incumbent_delta_r_per_trade": 0.0,
                    "corrected_p": best_corrected[0] if best_corrected else None,
                    "promoted": False,
                    "reasons": reasons,
                }
            )

    table = {
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "default_policy": {
            "policy_id": INCUMBENT_POLICY_ID,
            "family": incumbent_meta["family"],
            "params": dict(incumbent_meta["params"]),
        },
        "selection_thresholds": {
            "min_leaf_n": min_leaf_n,
            "min_days": min_days,
            "beat_fold_fraction": beat_fold_fraction,
            "max_fold_deficit_r": max_fold_deficit_r,
            "promote_corrected_p": promote_corrected_p,
        },
        "n_policies_in_grid": len(results.policies),
        "n_path_rows": results.n_path_rows,
        # Full PolicySpec field inventory so a params consumer can verify that
        # every promoted row's ``params`` map is complete (exact-geometry
        # reconstruction via ExitPolicyConfigV4.from_policy_params).
        "policy_spec_fields": sorted(
            spec_field.name for spec_field in fields(PolicySpec)
        ),
        "params_fidelity_contract": PARAMS_FIDELITY_EXACT,
        "segments": segment_rows,
        "source_manifest": dict(source_manifest) if source_manifest else {"files": []},
        **BOUNDARY,
    }
    return table


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Segment exit-policy tournament -> frozen segment table."
    )
    parser.add_argument("--route-dir", action="append", required=True, dest="route_dirs")
    parser.add_argument("--out", required=True)
    parser.add_argument("--m1-root", default=str(DEFAULT_M1_ROOT))
    parser.add_argument("--min-leaf-n", type=int, default=DEFAULT_MIN_LEAF_N)
    parser.add_argument("--min-days", type=int, default=DEFAULT_MIN_DAYS)
    parser.add_argument(
        "--abort-cross-top-n", type=int, default=DEFAULT_ABORT_CROSS_TOP_N
    )
    args = parser.parse_args(argv)

    dataset = build_path_dataset(args.route_dirs, m1_root=Path(args.m1_root))
    results = run_tournament(dataset.rows, abort_cross_top_n=args.abort_cross_top_n)
    source_manifest = {
        "files": [
            {"path": path, "sha256": file_sha256(path)}
            for path in sorted(set(dataset.consumed_files))
        ]
    }
    table = select_segment_policies(
        results,
        min_leaf_n=args.min_leaf_n,
        min_days=args.min_days,
        source_manifest=source_manifest,
    )
    table["dataset_counters"] = dict(sorted(dataset.counters.items()))
    table["dataset_notes"] = list(dataset.notes)
    table["missing_m1_files"] = sorted(set(dataset.missing_m1_files))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(table, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    promoted_rows = [row for row in table["segments"] if row.get("promoted")]
    summary = {
        "out": str(out_path),
        "path_rows": results.n_path_rows,
        "filled_rows": dataset.counters.get("filled_rows", 0),
        "counterfactual_filled_rows": dataset.counters.get(
            "counterfactual_filled_rows", 0
        ),
        "m1_file_missing_rows": dataset.counters.get("m1_file_missing", 0),
        "policies_in_grid": len(results.policies),
        "segments_evaluated": len(table["segments"]),
        "segments_promoted": len(promoted_rows),
        "promoted": [
            {
                "segment_id": row["segment_id"],
                "policy_id": row["policy_id"],
                "family": row["family"],
                "corrected_p": row["corrected_p"],
                "incumbent_delta_r_per_trade": row["incumbent_delta_r_per_trade"],
                "n_trades": row["n_trades"],
            }
            for row in promoted_rows
        ],
        **BOUNDARY,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


__all__ = [
    "ABORT_ADVERSE_GRID",
    "ABORT_MFE_FLOOR_GRID",
    "BOUNDARY",
    "DEFAULT_POLICY_GRID",
    "EVIDENCE_CLASS",
    "GridPolicy",
    "INCUMBENT_POLICY_ID",
    "INCUMBENT_SPEC",
    "PARAMS_FIDELITY_EXACT",
    "PathDataset",
    "PathRow",
    "POLICY_SPEC_SUPPORTS_ABORT",
    "SCHEMA_VERSION",
    "SEGMENT_LEVELS",
    "TournamentResult",
    "abort_crossed_grid",
    "build_path_dataset",
    "default_grid",
    "file_sha256",
    "main",
    "run_tournament",
    "segment_id_for",
    "select_segment_policies",
]


if __name__ == "__main__":
    raise SystemExit(main())
