#!/usr/bin/env python3
"""Exact-current W7 replay/recost for the durable armed set.

This is an offline research program.  It has no broker client, no activation-token path,
no sizing/risk dial, and no order-placement imports.  The only sleeves it is allowed to
name come from ``src.safety.armed_set.armed_sleeves`` after the declaration and committed
launcher reconcile cleanly.

The program deliberately does *not* route through Selector V4 or Scheduler V4.  W7's
``execution_packets`` compatibility fields are not shared selector/scheduler decisions;
the population here is produced by W7's own production sleeve generators, labelled by its
resolved per-sleeve exit contract, crossed through the active profile's broker-symbol map,
and priced by ``src.costs.cost_r``.

Primary outputs are deterministic:

* ``PRIOR_RECONCILIATION_V1.json`` binds the published W7 recost and its cache rows before
  any current correction is applied.
* ``W7_CURRENT_RECOST_V1.json`` carries the fail-closed headline, partial diagnostics,
  uncertainty, concentration, component costs, and coverage classes.
* ``W7_CURRENT_ROWS_V1.jsonl.gz`` is the result-bearing row ledger for all three spread
  bands.  It includes refusals and NOT_EVALUABLE rows; nothing disappears from a count.
* ``W7_CURRENT_SOURCE_CELLS_V1.jsonl`` is the complete requested
  account/sleeve/symbol roster.  Loaded counts cover observed rows only; without a bound per-symbol trading
  schedule, absent calendar bars and full-window occurrence counts remain unknown.
* ``W7_CURRENT_INPUT_MANIFEST_V1.json`` binds every committed and external input actually
  consumed.

The historical window is fixed to the prior publication's own full-window calendar
(``2015-02-25 .. 2026-06-12``).  Bars after the right edge may only close an already-entered
80-H4-bar path.  They never create a candidate in the comparison population.
"""

from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import pickle
import random
import statistics
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import yaml


REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import (  # noqa: E402
    CLEAN3_REGISTRY,
    SLEEVE_REGISTRY,
    effective_registry,
    resolve_market_expansion_sleeves,
    winsorize_R,
)
from src.components.ultimate_book.bar_provider import TF_H4  # noqa: E402
from src.components.ultimate_book.bridge import config_bool_value  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    M15_BARS_PER,
    resolve_exit_profile,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves import (  # noqa: E402
    crypto as crypto_generator,
    energy_agri as energy_generator,
    substrate as substrate_generator,
)
from src.components.ultimate_book.spread_geometry import resolve_floor_limit  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import Coverage, CostTruthError, cost_r, load_broker_true_costs  # noqa: E402
from src.costs.spread_model import (  # noqa: E402
    SpreadModelError,
    load_spread_model,
    spread_price,
)
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, PathResult, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import BarQuote, replay_anchor  # noqa: E402
from src.safety.armed_set import (  # noqa: E402
    armed_sleeves,
    assert_consistent,
    declared_arming,
    manifest as armed_manifest,
)
from src.utils.config import apply_profile_overrides  # noqa: E402


SCHEMA = "gtos.wave21.w7_current_recost.v1"
ROW_SCHEMA = "gtos.wave21.w7_current_recost.row.v1"
SOURCE_CELL_SCHEMA = "gtos.wave21.w7_current_recost.source_cell.v1"
SLEEVE_SCORECARD_SCHEMA = "gtos.wave21.w7_current_recost.sleeve_scorecard.v1"
PRIOR_SCHEMA = "gtos.wave21.w7_prior_reconciliation.v1"
MANIFEST_SCHEMA = "gtos.wave21.w7_current_inputs.v1"

WINDOW_START = dt.date(2015, 2, 25)
WINDOW_END = dt.date(2026, 6, 12)
H4_DELTA = dt.timedelta(hours=4)
H4_MINUTES = 240
PRODUCTION_CLOSED_BARS = 259
RESEARCH_MAXBARS = 80
BANDS = ("low", "mid", "high")
PRIMARY_BAND = "mid"
SCORECARD_RECOMMENDATIONS = ("KEEP", "REPAIR", "RESEARCH_ONLY", "NE")
COVERAGE_CLASSES = ("MEASURED", "TRANSFERRED", "MODELLED", "NOT_EVALUABLE")
BOOTSTRAP_SEED = 20260808
BOOTSTRAP_REPS = 2000
BOOTSTRAP_BLOCK_DAYS = 5
CALENDAR_DAYS = (WINDOW_END - WINDOW_START).days + 1
QUOTE_LIFECYCLE_MODEL = "H4_BID_OHLC_SCALAR_ENTRY_SPREAD_CONSERVATIVE_OPEN_GAP"

BARS_ROOT = Path("/Users/borr/GTOSActive/vps-bars-20260727")
BARS_MANIFEST = BARS_ROOT / "BARS_MANIFEST.json"
COSTS_PATH = (
    REPO
    / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
)
SPREAD_PATH = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
PRIOR_PATH = REPO / "research/operations/w7_recost_2026_07_27/W7_RECOST_V1.json"
SURVIVOR_PATH = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
ROUTE = REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
W3_CACHE = ROUTE / "INTEG_W3_streams_cache.pkl"
W5_CACHE = ROUTE / "INTEG_W5_new_streams_cache.pkl"
D4_LEDGER = ROUTE / "D4_COMBINED_TRADE_LEDGER.jsonl"

OUT_RESULT = HERE / "W7_CURRENT_RECOST_V1.json"
OUT_ROWS = HERE / "W7_CURRENT_ROWS_V1.jsonl.gz"
OUT_SOURCE_CELLS = HERE / "W7_CURRENT_SOURCE_CELLS_V1.jsonl"
OUT_PRIOR = HERE / "PRIOR_RECONCILIATION_V1.json"
OUT_MANIFEST = HERE / "W7_CURRENT_INPUT_MANIFEST_V1.json"
OUT_REPORT = HERE / "W7_CURRENT_REPORT_V1.md"


ACCOUNT_META: dict[str, dict[str, str]] = {
    "operator_profile": {
        "account": "FTMO",
        "bar_broker": "FTMO-Server3",
        "server": "FTMO-Server3",
    },
    "redacted_account_live_bee34003": {
        "account": "redacted_account",
        "bar_broker": "redacted_account-Server 2",
        "server": "redacted_account-Server 2",
    },
}

# Read-only Wave-21 integration audit observation supplied to this lane on 2026-08-09.
# It is disclosure authority only: this lane performs no host read or mutation and never
# upgrades its local replay to live parity from this observation.
LATEST_DURABLE_HOST_SURFACE: dict[str, dict[str, Any]] = {
    "operator_profile": {
        "include_clean3": True,
        "effective_registry_intersection": [
            "crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback",
        ],
        "frontier_exits": ["crypto"],
    },
    "redacted_account_live_bee34003": {
        "include_clean3": True,
        "effective_registry_intersection": [
            "crypto", "energy_agri", "sub_mid_dn_revert", "sub_xvol_pullback",
        ],
        "frontier_exits": [],
    },
}


def _name_tuple(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,) if raw else ()
    if isinstance(raw, (list, tuple, set)):
        return tuple(str(item) for item in raw if str(item))
    return ()


def _local_effective_runtime_surface(
    runtime_cfg: Mapping[str, Any], sleeves: Sequence[str], frontier_exits: Sequence[str]
) -> dict[str, Any]:
    """Resolve the committed/profile-merged runtime membership for the declared tags."""

    include_clean3 = config_bool_value(
        runtime_cfg.get("ultimate_book_include_clean3", False), False
    )
    include_clean4 = config_bool_value(
        runtime_cfg.get("ultimate_book_include_clean4", False), False
    )
    include_candidate = config_bool_value(
        runtime_cfg.get("ultimate_book_include_candidate_book", False), False
    )
    include_expansion = config_bool_value(
        runtime_cfg.get("ultimate_book_include_market_expansion_book", False), False
    )
    candidate_sleeves = _name_tuple(
        runtime_cfg.get("ultimate_book_candidate_book_sleeves")
    )
    explicit_expansion = _name_tuple(
        runtime_cfg.get("ultimate_book_market_expansion_sleeves")
    )
    expansion_sleeves, expansion_error = resolve_market_expansion_sleeves(
        policy=str(
            runtime_cfg.get(
                "ultimate_book_market_expansion_policy", "explicit_allowlist"
            ) or "explicit_allowlist"
        ),
        explicit_sleeves=explicit_expansion,
    )
    if expansion_error:
        expansion_sleeves = ()
    registry = effective_registry(
        include_clean3=include_clean3,
        include_clean4=include_clean4,
        include_candidate_book=include_candidate,
        candidate_book_sleeves=candidate_sleeves or None,
        include_market_expansion_book=include_expansion,
        market_expansion_sleeves=expansion_sleeves or None,
    )
    declared = tuple(sorted(str(sleeve) for sleeve in sleeves))
    effective = tuple(sorted(set(declared) & set(registry)))
    return {
        "include_clean3": include_clean3,
        "include_clean4": include_clean4,
        "declared_tags": list(declared),
        "effective_registry_intersection": list(effective),
        "declared_but_locally_filtered": sorted(set(declared) - set(effective)),
        "frontier_exits": list(sorted(str(sleeve) for sleeve in frontier_exits)),
    }


def _runtime_parity_doc(namespace: str, local_surface: Mapping[str, Any]) -> dict[str, Any]:
    host_surface = dict(LATEST_DURABLE_HOST_SURFACE[namespace])
    registry_matches = (
        local_surface["effective_registry_intersection"]
        == host_surface["effective_registry_intersection"]
    )
    frontier_matches = local_surface["frontier_exits"] == host_surface["frontier_exits"]
    return {
        "overall_status": (
            "LOCAL_COMMITTED_SURFACE_MATCHES_LATEST_HOST_OBSERVATION"
            if registry_matches and frontier_matches
            else "NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE"
        ),
        "live_parity_claimed": False,
        "local_committed_surface": dict(local_surface),
        "latest_durable_host_observation": {
            **host_surface,
            "evidence_class": "UPSTREAM_READ_ONLY_WAVE21_LIVE_AUDIT_OBSERVATION",
            "observation_date": "2026-08-09",
            "artifact_binding_status": (
                "UPSTREAM_INTEGRATION_RECEIPT_NOT_LOCAL_TO_THIS_SCOPED_LANE"
            ),
        },
        "effective_registry_matches": registry_matches,
        "frontier_exit_selection_matches": frontier_matches,
        "claim_boundary": (
            "Local merged config/launcher bytes and the latest durable host observation "
            "diverge. The direct generator recost is not an exact local-runtime or live-runtime "
            "graph replay; the upstream integration owner must preserve the host observation "
            "receipt when composing this scoped lane."
        ),
    }


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_sha(doc: Any) -> str:
    raw = json.dumps(doc, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def quantile(values: Sequence[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(float(x) for x in values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * float(p)
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - k) + xs[hi] * (k - lo)


def summary(values: Sequence[float]) -> dict[str, Any]:
    vals = [float(v) for v in values]
    if not vals:
        return {"n": 0, "mean": None, "sum": None, "median": None, "sd": None}
    return {
        "n": len(vals),
        "mean": round(statistics.fmean(vals), 6),
        "sum": round(math.fsum(vals), 6),
        "median": round(statistics.median(vals), 6),
        "sd": round(statistics.stdev(vals), 6) if len(vals) > 1 else None,
        "p05": round(quantile(vals, 0.05), 6),
        "p95": round(quantile(vals, 0.95), 6),
    }


def moving_block_cluster_ci(
    rows: Sequence[dict], field: str, *, reps: int = BOOTSTRAP_REPS
) -> dict[str, Any]:
    """Deterministic moving-block bootstrap, clustered by entry day.

    The statistic is trade mean, but whole days are resampled in five-day blocks.  This
    retains same-day clusters and short serial dependence.  It is an uncertainty interval,
    not an admission test and not an owner-selected threshold.
    """

    buckets: dict[str, list[float]] = collections.defaultdict(list)
    for row in rows:
        val = row.get(field)
        if val is not None:
            buckets[str(row["entry_utc"])[:10]].append(float(val))
    days = sorted(buckets)
    n_trades = sum(len(buckets[d]) for d in days)
    if not days or not n_trades:
        return {
            "method": "moving_block_bootstrap_by_entry_day",
            "n_days": 0,
            "n_trades": 0,
            "point_mean": None,
            "ci95": [None, None],
        }
    rng = random.Random(BOOTSTRAP_SEED + sum(ord(c) for c in field))
    block = min(BOOTSTRAP_BLOCK_DAYS, len(days))
    draws: list[float] = []
    for _ in range(reps):
        sampled: list[float] = []
        while len(sampled) < n_trades:
            start = rng.randrange(len(days))
            for off in range(block):
                sampled.extend(buckets[days[(start + off) % len(days)]])
                if len(sampled) >= n_trades:
                    break
        draws.append(statistics.fmean(sampled[:n_trades]))
    return {
        "method": "circular_moving_block_bootstrap_by_entry_day",
        "seed": BOOTSTRAP_SEED + sum(ord(c) for c in field),
        "reps": reps,
        "block_traded_days": block,
        "n_days": len(days),
        "n_trades": n_trades,
        "point_mean": round(statistics.fmean(
            float(r[field]) for r in rows if r.get(field) is not None
        ), 6),
        "ci95": [round(quantile(draws, 0.025), 6), round(quantile(draws, 0.975), 6)],
    }


def concentration(rows: Sequence[dict], field: str) -> dict[str, Any]:
    by_symbol: dict[str, float] = collections.defaultdict(float)
    by_year: dict[str, float] = collections.defaultdict(float)
    for row in rows:
        val = row.get(field)
        if val is None:
            continue
        by_symbol[str(row["symbol_canonical"])] += float(val)
        by_year[str(row["entry_utc"])[:4]] += float(val)

    def _one(values: Mapping[str, float]) -> dict[str, Any]:
        abs_total = math.fsum(abs(v) for v in values.values())
        positive_total = math.fsum(max(v, 0.0) for v in values.values())
        abs_rank = sorted(values.items(), key=lambda kv: (-abs(kv[1]), kv[0]))
        pos_rank = sorted(values.items(), key=lambda kv: (-max(kv[1], 0.0), kv[0]))
        shares = [abs(v) / abs_total for _, v in abs_rank] if abs_total else []
        return {
            "contributions": {k: round(v, 6) for k, v in sorted(values.items())},
            "absolute_contribution_total": round(abs_total, 6),
            "top_absolute": [
                {"name": k, "sum_r": round(v, 6),
                 "share_abs_pct": round(100.0 * abs(v) / abs_total, 2) if abs_total else None}
                for k, v in abs_rank[:3]
            ],
            "top_positive": [
                {"name": k, "positive_sum_r": round(max(v, 0.0), 6),
                 "share_positive_pct": (
                     round(100.0 * max(v, 0.0) / positive_total, 2)
                     if positive_total else None
                 )}
                for k, v in pos_rank[:3]
            ],
            "hhi_absolute": round(math.fsum(x * x for x in shares), 6) if shares else None,
        }

    return {"by_symbol": _one(by_symbol), "by_entry_year": _one(by_year)}


def _coverage_weakest(*classes: str) -> str:
    order = {"MEASURED": 0, "TRANSFERRED": 1, "MODELLED": 2, "NOT_EVALUABLE": 3}
    return max(classes, key=lambda c: order[c])


def _measure_doc(measure: Any) -> dict[str, Any]:
    return {
        "value": float(measure.value),
        "coverage": measure.coverage.value,
        "band_low": float(measure.band_low),
        "band_high": float(measure.band_high),
        "provenance": str(measure.provenance),
    }


@dataclass(frozen=True)
class Series:
    symbol: str
    source_account: str
    source_broker: str
    source_class: str
    path: Path
    sha256: str
    sidecar: Path
    sidecar_sha256: str
    bars: tuple[Bar, ...]
    times: tuple[dt.datetime, ...]


def _bar_manifest_index() -> tuple[dict[tuple[str, str, str], dict], dict]:
    doc = json.loads(BARS_MANIFEST.read_text())
    out: dict[tuple[str, str, str], dict] = {}
    for row in doc["files"]:
        out[(str(row["broker"]), str(row["symbol"]), str(row["timeframe"]))] = row
    return out, doc


def _source_for(
    account: str,
    broker: str,
    symbol: str,
    index: Mapping[tuple[str, str, str], dict],
) -> tuple[dict | None, str | None, str | None]:
    own = index.get((broker, symbol, "H4"))
    if own is not None:
        return own, "MEASURED", account
    if account == "redacted_account":
        transfer = index.get(("FTMO-Server3", symbol, "H4"))
        if transfer is not None:
            return transfer, "TRANSFERRED", "FTMO"
    return None, None, None


def _load_one_series(
    symbol: str,
    source_row: Mapping[str, Any],
    source_class: str,
    source_account: str,
) -> Series:
    path = BARS_ROOT / str(source_row["file"])
    actual = sha256_path(path)
    if actual != str(source_row["sha256"]):
        raise RuntimeError(f"bar byte drift: {path} {actual} != {source_row['sha256']}")
    sidecar = Path(str(path) + ".timebase.json")
    if not sidecar.is_file():
        raise RuntimeError(f"bar source has no timebase sidecar: {sidecar}")
    src = CsvBarSource({(symbol, TF_H4): path}, label=f"wave21:{source_row['broker']}")
    raw = src._load((symbol, TF_H4))
    bars = tuple(Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                 for r in raw)
    times = tuple(dt.datetime.fromisoformat(str(r["time"])) for r in raw)
    if not bars or len(bars) != len(times):
        raise RuntimeError(f"empty/misaligned series for {symbol}: {path}")
    if list(times) != sorted(times) or len(times) != len(set(times)):
        raise RuntimeError(f"non-unique/non-ascending true-UTC times for {path}")
    return Series(
        symbol=symbol,
        source_account=source_account,
        source_broker=str(source_row["broker"]),
        source_class=source_class,
        path=path,
        sha256=actual,
        sidecar=sidecar,
        sidecar_sha256=sha256_path(sidecar),
        bars=bars,
        times=times,
    )


GENERATOR: dict[str, Callable[..., Any]] = {
    "crypto": crypto_generator.generate,
    "energy_agri": energy_generator.generate,
    "sub_xvol_pullback": substrate_generator.generate_sub_xvol_pullback,
    "sub_mid_dn_revert": substrate_generator.generate_sub_mid_dn_revert,
}

SURFACE: dict[str, tuple[str, ...]] = {
    "crypto": tuple(crypto_generator.ON_SURFACE),
    "energy_agri": tuple(energy_generator.ON_SURFACE),
    "sub_xvol_pullback": tuple(substrate_generator.XVOL_ON_SURFACE),
    "sub_mid_dn_revert": tuple(substrate_generator.MIDDN_ON_SURFACE),
}


def _generator_authority_checks(armed: Iterable[str]) -> None:
    armed_set = set(armed)
    unknown = armed_set - set(GENERATOR)
    if unknown:
        raise RuntimeError(
            f"durable armed set names sleeves this exact W7 driver cannot replay: {sorted(unknown)}"
        )
    # The surface is imported from the generator modules.  These comparisons ensure a
    # future registry drift is loud rather than silently narrowing the replay.
    if set(SURFACE["crypto"]) != set(SLEEVE_REGISTRY["crypto"].symbols):
        raise RuntimeError("crypto generator surface != production admission registry")
    if not set(SURFACE["energy_agri"]).issubset(SLEEVE_REGISTRY["energy_agri"].symbols):
        raise RuntimeError("energy generator surface is outside production admission registry")
    for sleeve in ("sub_xvol_pullback", "sub_mid_dn_revert"):
        if not set(SURFACE[sleeve]).issubset(CLEAN3_REGISTRY[sleeve].symbols):
            raise RuntimeError(f"{sleeve} generator surface is outside CLEAN3 registry")


def _exit_policy(sleeve: str, frontier_exits: Sequence[str], stop: float) -> tuple[ExitPolicy, dict]:
    prof = resolve_exit_profile(sleeve, frontier_exits=frontier_exits)
    raw_m15 = int(prof["time_stop_bars"])
    own_bars = int(round(raw_m15 / M15_BARS_PER["H4"]))
    if own_bars != RESEARCH_MAXBARS:
        raise RuntimeError(
            f"{sleeve}: current time stop is {raw_m15} M15 prints = {own_bars} H4 bars, "
            f"outside this lane's 80-H4 comparison contract"
        )
    mode = str(prof.get("policy"))
    final_r = prof.get("final_target_r")
    if prof.get("final_from_intent"):
        target = None  # replaced by the caller from the intent
    else:
        target = float(final_r) * stop if final_r is not None else None
    partial_at = None
    partial_frac = 0.5
    if mode == "partial_be_runner":
        partial_at = float(prof["trigger_r"])
        partial_frac = float(prof.get("partial_close_ratio", 0.5))
    elif mode != "time_stop":
        raise RuntimeError(f"{sleeve}: unsupported armed exit policy {mode!r}")
    pol = ExitPolicy(
        target_dist=target,
        maxbars=RESEARCH_MAXBARS,
        time_stop_bars=own_bars,
        partial_at_r=partial_at,
        partial_frac=partial_frac,
        be_stop_after_partial=bool(partial_at),
        label=f"current:{mode}",
    )
    return pol, {
        "resolved_profile": copy.deepcopy(prof),
        "time_stop_h4_bars": own_bars,
        "policy": mode,
    }


def _gap_conservative(
    bars: Sequence[Bar], entry: float, direction: int, stop: float,
    policy: ExitPolicy, result: PathResult,
) -> tuple[float, dict[str, Any]]:
    """Conservative H4 gap fill on the already quote-side-corrected path.

    Stops fill at the adverse open when the bar opens through the standing level; targets
    remain at their limit.  A post-partial stop is at breakeven, not at ``entry - 1R``.
    This is the M4 convention with that partial-stop detail made explicit.
    """

    j = int(result.exit_index)
    bar = bars[j]
    bank = float(result.detail.get("partial_banked_r", 0.0) or 0.0)
    taken = float(result.detail.get("partial_frac_taken", 0.0) or 0.0)

    def at_price(px: float) -> float:
        raw = ((px - entry) if direction > 0 else (entry - px)) / stop
        return bank + (1.0 - taken) * raw

    level_r = float(result.r_gross)
    if result.exit_reason == "stop":
        level = entry if taken else entry - direction * stop
        through = (direction > 0 and bar.o < level) or (direction < 0 and bar.o > level)
        if through:
            raw = at_price(float(bar.o))
            return raw, {
                "gap_leg": "breakeven_stop" if taken else "stop",
                "gap_fill_price": float(bar.o),
                "gap_level": float(level),
                "gap_delta_r_raw": raw - level_r,
            }
    return level_r, {
        "gap_leg": None,
        "gap_fill_price": None,
        "gap_level": None,
        "gap_delta_r_raw": 0.0,
    }


def _generate_for_series(sleeve: str, series: Series) -> tuple[list[dict], dict]:
    fn = GENERATOR[sleeve]
    rows: list[dict] = []
    tel: collections.Counter[str] = collections.Counter()
    seen: set[tuple[str, str, int]] = set()
    for i in range(PRODUCTION_CLOSED_BARS - 1, len(series.bars) - RESEARCH_MAXBARS):
        entry_utc = series.times[i] + H4_DELTA
        if entry_utc.date() < WINDOW_START or entry_utc.date() > WINDOW_END:
            continue
        tel["bar_evaluations"] += 1
        history = series.bars[i - PRODUCTION_CLOSED_BARS + 1 : i + 1]
        intent = fn(
            series.symbol,
            history,
            series.times[i].date().isoformat(),
            bar_time=series.times[i],
        )
        if intent is None:
            continue
        if str(intent.sleeve) != sleeve or int(intent.direction) not in (-1, 1):
            raise RuntimeError(f"malformed production intent: {intent!r}")
        ident = (series.symbol, series.times[i].isoformat(), int(intent.direction))
        if ident in seen:
            tel["duplicate_intent"] += 1
            continue
        seen.add(ident)
        rows.append({
            "sleeve": sleeve,
            "symbol_canonical": series.symbol,
            "decision_bar_iso": series.times[i].isoformat(),
            "entry_utc": entry_utc.isoformat(),
            "source_index": i,
            "direction": int(intent.direction),
            "sl_distance_price": float(intent.stop_dist),
            "intent_target_dist": (
                float(intent.target_dist) if intent.target_dist is not None else None
            ),
        })
    tel["candidates"] = len(rows)
    return rows, dict(tel)


def _not_evaluable_row(seed: Mapping[str, Any], *, namespace: str, account: str,
                        band: str, reason: str, source: Series | None = None) -> dict:
    row = {
        "schema": ROW_SCHEMA,
        "namespace": namespace,
        "account": account,
        "band": band,
        "sleeve": seed.get("sleeve"),
        "symbol_canonical": seed.get("symbol_canonical"),
        "symbol": seed.get("symbol"),
        "decision_bar_iso": seed.get("decision_bar_iso"),
        "entry_utc": seed.get("entry_utc"),
        "direction": seed.get("direction"),
        "sl_distance_price": seed.get("sl_distance_price"),
        "intent_target_dist": seed.get("intent_target_dist"),
        "status": "NOT_EVALUABLE",
        "reason": reason,
        "coverage": "NOT_EVALUABLE",
        "quote_authority_status": "NOT_EVALUABLE",
        "quote_lifecycle_coverage": "NOT_EVALUABLE",
        "quote_lifecycle_model": QUOTE_LIFECYCLE_MODEL,
        "cost_authority_status": "NOT_EVALUABLE",
        "floor_status": "NOT_EVALUABLE",
        "lot_account_translation_status": "NOT_EVALUABLE",
        "source_class": source.source_class if source else "NOT_EVALUABLE",
    }
    if source is not None:
        row.update({
            "source_account": source.source_account,
            "source_broker": source.source_broker,
            "source_path": str(source.path),
            "source_sha256": source.sha256,
            "source_sidecar": str(source.sidecar),
            "source_sidecar_sha256": source.sidecar_sha256,
        })
    return row


def _score_seed(
    seed: Mapping[str, Any], *, namespace: str, account: str, server: str,
    band: str, series: Series, resolver: Callable[[str], str], runtime_cfg: Mapping[str, Any],
    floor_selection: Mapping[str, float | None], frontier_exits: Sequence[str], costs: Any,
    spread_model: Any,
) -> dict:
    sleeve = str(seed["sleeve"])
    symbol = resolver(str(seed["symbol_canonical"]))
    i = int(seed["source_index"])
    stop = float(seed["sl_distance_price"])
    entry_utc = dt.datetime.fromisoformat(str(seed["entry_utc"]))
    side = "LONG" if int(seed["direction"]) > 0 else "SHORT"

    try:
        est = spread_price(
            symbol, account, entry_utc, band=band, model=spread_model,
        )
    except (SpreadModelError, CostTruthError, KeyError, TypeError, ValueError) as exc:
        return _not_evaluable_row(
            {**seed, "symbol": symbol}, namespace=namespace, account=account, band=band,
            source=series, reason=f"spread_unavailable:{type(exc).__name__}:{str(exc)[:180]}",
        )

    floor_limit = resolve_floor_limit(runtime_cfg, sleeve, floor_selection)
    spread_r = float(est.spread_price) / stop
    floor_refused = bool(
        floor_limit is not None and spread_r > float(floor_limit)
    )
    floor_status = (
        "REFUSED" if floor_refused else
        "SURVIVED" if floor_limit is not None else
        "NOT_APPLICABLE"
    )

    policy, exit_contract = _exit_policy(sleeve, frontier_exits, stop)
    if exit_contract["resolved_profile"].get("final_from_intent"):
        policy = ExitPolicy(**{
            **asdict(policy),
            "target_dist": seed.get("intent_target_dist"),
        })
    direction = int(seed["direction"])
    level = replay(
        series.bars, i, direction, stop_dist=stop, policy=policy,
        times=series.times, server=server, bar_minutes=H4_MINUTES,
    )
    anchor = replay_anchor(
        float(series.bars[i].c), direction, float(est.spread_price), BarQuote.BID
    )
    quote = replay(
        series.bars, i, direction, stop_dist=stop, policy=policy,
        times=series.times, server=server, bar_minutes=H4_MINUTES,
        entry_price=anchor,
    )
    gap_raw, gap = _gap_conservative(
        series.bars, anchor, direction, stop, policy, quote
    )
    level_raw = float(level.r_gross)
    quote_raw = float(quote.r_gross)
    level_clip = float(winsorize_R(level_raw))
    quote_clip = float(winsorize_R(quote_raw))
    gap_clip = float(winsorize_R(gap_raw))
    level_exit_utc = series.times[int(level.exit_index)] + H4_DELTA
    exit_utc = series.times[int(quote.exit_index)] + H4_DELTA
    level_hold = (level_exit_utc - entry_utc).total_seconds() / 3600.0
    hold = (exit_utc - entry_utc).total_seconds() / 3600.0

    quote_fields = {
        "schema": ROW_SCHEMA,
        "namespace": namespace,
        "account": account,
        "band": band,
        "sleeve": sleeve,
        "symbol_canonical": seed["symbol_canonical"],
        "symbol": symbol,
        "decision_bar_iso": seed["decision_bar_iso"],
        "source_index": i,
        "entry_utc": entry_utc.isoformat(),
        "exit_utc": exit_utc.isoformat(),
        "direction": direction,
        "source_account": series.source_account,
        "source_broker": series.source_broker,
        "source_class": series.source_class,
        "source_path": str(series.path),
        "source_sha256": series.sha256,
        "source_sidecar": str(series.sidecar),
        "source_sidecar_sha256": series.sidecar_sha256,
        # This walker has exact H4 BID OHLC and a modelled scalar spread only at
        # entry.  It has neither historical ASK bars/ticks nor resting-order quote
        # lifecycle.  Calling this COMPLETE would promote a model into a measurement.
        "quote_authority_status": "MODELLED",
        "quote_lifecycle_coverage": "MODELLED",
        "quote_lifecycle_model": QUOTE_LIFECYCLE_MODEL,
        "cost_authority_status": "NOT_EVALUABLE",
        "floor_status": floor_status,
        "lot_account_translation_status": "NOT_EVALUABLE",
        "sl_distance_price": stop,
        "intent_target_dist": seed.get("intent_target_dist"),
        "entry_bid_close": float(series.bars[i].c),
        "entry_transacted": float(anchor),
        "spread_price": float(est.spread_price),
        "spread_r": spread_r,
        "spread_coverage": est.coverage.value,
        "spread_era": est.era,
        "spread_era_class": est.era_class,
        "spread_decidable": bool(est.decidable),
        "floor_limit_r": float(floor_limit) if floor_limit is not None else None,
        "exit_contract": exit_contract,
        "exit_reason_level": level.exit_reason,
        "exit_reason_quote": quote.exit_reason,
        "exit_reason_changed_by_quote": level.exit_reason != quote.exit_reason,
        "exit_bar_offset_level": int(level.exit_index) - i,
        "exit_bar_offset_quote": int(quote.exit_index) - i,
        "holding_hours_wall": hold,
        "holding_hours_level_wall": level_hold,
        "r_level_raw": level_raw,
        "r_level_validation_clip": level_clip,
        "r_quote_raw": quote_raw,
        "r_quote_validation_clip": quote_clip,
        "r_quote_gap_raw": float(gap_raw),
        "r_quote_gap_validation_clip": gap_clip,
        "r_delta_quote_gross_clip": quote_clip - level_clip,
        "r_delta_gap_on_quote_clip": gap_clip - quote_clip,
        "gap": gap,
    }

    try:
        c_level = cost_r(
            symbol, account, level_hold,
            sl_distance_price=stop, entry_price=float(series.bars[i].c), side=side,
            entry_utc=entry_utc, spread_band=band, spread_model=spread_model, costs=costs,
        )
        c = cost_r(
            symbol, account, hold,
            sl_distance_price=stop, entry_price=anchor, side=side,
            entry_utc=entry_utc, spread_band=band, spread_model=spread_model, costs=costs,
        )
    except (CostTruthError, SpreadModelError, KeyError, TypeError, ValueError) as exc:
        return {
            **quote_fields,
            "status": "REFUSED_BY_CURRENT_FLOOR" if floor_refused else "NOT_EVALUABLE",
            "reason": (
                f"spread_geometry_floor:{spread_r:.6f}>{float(floor_limit):.6f};"
                if floor_refused else ""
            ) + f"cost_unavailable:{type(exc).__name__}:{str(exc)[:180]}",
            "coverage": "NOT_EVALUABLE",
            "cost_authority_status": "NOT_EVALUABLE",
        }

    components = {
        "commission_r": _measure_doc(c.commission_r),
        "swap_r": _measure_doc(c.swap_r),
        "spread_r": _measure_doc(c.spread_r),
        "slippage_r": _measure_doc(c.slippage_r),
    }
    nonspread_cost = (
        float(c.commission_r.value) + float(c.swap_r.value) + float(c.slippage_r.value)
    )
    current_coverage = _coverage_weakest(
        series.source_class,
        "MODELLED",  # weakest-class cap imposed by H4 BID + scalar-spread lifecycle
        est.coverage.value,
        c.commission_r.coverage.value,
        c.swap_r.coverage.value,
        c.slippage_r.coverage.value,
    )
    counterfactual = {
        "counterfactual_pre_floor_r_net_level_all_cost_clip": (
            level_clip - float(c_level.total_r.value)
        ),
        "counterfactual_pre_floor_r_net_quote_all_cost_double_spread_clip": (
            gap_clip - float(c.total_r.value)
        ),
        "counterfactual_pre_floor_r_net_current_clip": gap_clip - nonspread_cost,
        "counterfactual_pre_floor_r_net_current_raw": float(gap_raw) - nonspread_cost,
        "counterfactual_pre_floor_r_delta_current_vs_level_net_clip": (
            (gap_clip - nonspread_cost) - (level_clip - float(c_level.total_r.value))
        ),
    }
    current_fields = {}
    if not floor_refused:
        current_fields = {
            "r_net_level_all_cost_clip": counterfactual[
                "counterfactual_pre_floor_r_net_level_all_cost_clip"
            ],
            "r_net_quote_all_cost_double_spread_clip": counterfactual[
                "counterfactual_pre_floor_r_net_quote_all_cost_double_spread_clip"
            ],
            "r_net_current_clip": counterfactual[
                "counterfactual_pre_floor_r_net_current_clip"
            ],
            "r_net_current_raw": counterfactual[
                "counterfactual_pre_floor_r_net_current_raw"
            ],
            "r_delta_current_vs_level_net_clip": counterfactual[
                "counterfactual_pre_floor_r_delta_current_vs_level_net_clip"
            ],
        }
    return {
        **quote_fields,
        "status": "REFUSED_BY_CURRENT_FLOOR" if floor_refused else "EVALUABLE",
        "reason": (
            f"spread_geometry_floor:{spread_r:.6f}>{float(floor_limit):.6f}"
            if floor_refused else None
        ),
        "coverage": current_coverage,
        "cost_authority_status": "COMPLETE",
        "current_contract_economic_status": (
            "EXCLUDED_BY_SPREAD_GEOMETRY_FLOOR"
            if floor_refused else "INCLUDED_AFTER_SPREAD_GEOMETRY_FLOOR"
        ),
        "cost_components": components,
        "cost_total_all_four_r": float(c.total_r.value),
        "cost_nonspread_r": nonspread_cost,
        "swap_nights": (c.detail.get("swap") or {}).get("nights_charged"),
        **counterfactual,
        **current_fields,
    }


def _prior_cache_rows() -> dict[str, list[dict]]:
    with W3_CACHE.open("rb") as fh:
        w3 = pickle.load(fh)  # trusted, hash-bound committed input
    with W5_CACHE.open("rb") as fh:
        w5 = pickle.load(fh)  # trusted, hash-bound committed input
    return {**w3, **w5}


def prior_reconciliation(armed_by_ns: Mapping[str, Sequence[str]]) -> dict:
    prior = json.loads(PRIOR_PATH.read_text())
    caches = _prior_cache_rows()
    armed_union = sorted(set().union(*(set(v) for v in armed_by_ns.values())))
    per: dict[str, dict] = {}
    for sleeve in armed_union:
        rows = list(caches.get(sleeve) or [])
        if not rows:
            raise RuntimeError(f"prior cache has no rows for armed sleeve {sleeve}")
        identities: collections.Counter[tuple] = collections.Counter(
            (sleeve, str(r["sym"]), str(r["date"])) for r in rows
        )
        duplicate_rows = sum(n for n in identities.values() if n > 1)
        pub_ftmo = prior["accounts"]["FTMO"]["sleeves"][sleeve]
        pub_fn = prior["accounts"]["redacted_account"]["sleeves"][sleeve]
        per[sleeve] = {
            "cache_rows": len(rows),
            "cache_first": min(str(r["date"]) for r in rows),
            "cache_last": max(str(r["date"]) for r in rows),
            "cache_mean_consumed_r": round(statistics.fmean(float(r["R"]) for r in rows), 6),
            "cache_unique_sleeve_symbol_date": len(identities),
            "cache_rows_on_nonunique_sleeve_symbol_date": duplicate_rows,
            "max_multiplicity_sleeve_symbol_date": max(identities.values()),
            "exact_rejoinable_from_cache_key": duplicate_rows == 0,
            "published": {
                "FTMO": {
                    "n": pub_ftmo["n"], "gross_r": pub_ftmo["gross_r"],
                    "modelled_horizon_net_r": pub_ftmo["net_r"]["n_horizon_mean"],
                    "survivor_tier": pub_ftmo["survivor_tier"],
                    "coverage": pub_ftmo["coverage"],
                },
                "redacted_account": {
                    "n": pub_fn["n"], "gross_r": pub_fn["gross_r"],
                    "modelled_horizon_net_r": pub_fn["net_r"]["n_horizon_mean"],
                    "survivor_tier": pub_fn["survivor_tier"],
                    "coverage": pub_fn["coverage"],
                },
            },
            "n_matches_published": (
                len(rows) == int(pub_ftmo["n"]) == int(pub_fn["n"])
            ),
        }
    return {
        "schema": PRIOR_SCHEMA,
        "authority_status": "HISTORICAL_NON_AUTHORITATIVE_RECORD_NOT_A_COMPARATOR",
        "authoritative_current_comparator": False,
        "published_artifact": str(PRIOR_PATH.relative_to(REPO)),
        "published_sha256": sha256_path(PRIOR_PATH),
        "survivor_artifact": str(SURVIVOR_PATH.relative_to(REPO)),
        "survivor_sha256": sha256_path(SURVIVOR_PATH),
        "inputs": {
            str(p.relative_to(REPO)): sha256_path(p)
            for p in (W3_CACHE, W5_CACHE, D4_LEDGER)
        },
        "armed_sleeves_resolved_from_api": armed_union,
        "pipeline_parity_published": prior["pipeline_parity"],
        "pipeline_parity_all_true": all(prior["pipeline_parity"]["matches"].values()),
        "prior_runner_reproduction": {
            "result": "GEOMETRY_AND_NONCOST_BLOCKS_REPRODUCED_COST_BLOCK_DRIFTED",
            "result_bearing_command": (
                "python3 scripts/recost_w7_validation.py --out "
                "docs/audits/fable5-vision-audit-20260725/phase21/w7_recost/.prior_repro_tmp"
            ),
            "detail": (
                "With committed data hydrated, the current legacy runner reproduces stop tiers, "
                "price basis, ATR fractions, calendar and pipeline parity. redacted_account is exact. "
                "FTMO cost blocks differ because the artifact names but does not SHA-bind "
                "BROKER_TRUE_COSTS_V1.json, which was revised in later commits. The published "
                "artifact is therefore a historical record only, not an authoritative current "
                "comparator; its current rerun is not silently substituted for it."
            ),
        },
        "identity_limit": (
            "The old caches carry sleeve/symbol/date but no decision timestamp, direction for "
            "every row, or exit index. That key is non-unique. Old rows are reconciled as a "
            "published historical record and are not claimed to be an authoritative comparator "
            "or exact current-row joins."
        ),
        "sleeves": per,
    }


def _coverage_counts(rows: Sequence[dict]) -> dict[str, int]:
    counts = collections.Counter(str(r.get("coverage")) for r in rows)
    return {key: int(counts.get(key, 0)) for key in COVERAGE_CLASSES}


def _component_summary(rows: Sequence[dict]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("commission_r", "swap_r", "spread_r", "slippage_r"):
        vals = [
            float(r["cost_components"][key]["value"])
            for r in rows if r.get("cost_components")
        ]
        cov = collections.Counter(
            r["cost_components"][key]["coverage"]
            if r.get("cost_components") else "NOT_EVALUABLE"
            for r in rows
        )
        out[key] = {
            "value": summary(vals),
            "coverage": {cls: int(cov.get(cls, 0)) for cls in COVERAGE_CLASSES},
        }
    return out


def _source_records(rows: Sequence[dict]) -> list[dict[str, Any]]:
    records: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        path = row.get("source_path")
        digest = row.get("source_sha256")
        if not path or not digest:
            continue
        key = (
            row.get("source_account"), row.get("source_broker"),
            row.get("source_class"), path, digest,
            row.get("source_sidecar_sha256"),
        )
        records[key] = {
            "source_account": row.get("source_account"),
            "source_broker": row.get("source_broker"),
            "source_class": row.get("source_class"),
            "path": path,
            "sha256": digest,
            "sidecar": row.get("source_sidecar"),
            "sidecar_sha256": row.get("source_sidecar_sha256"),
        }
    return [records[key] for key in sorted(records, key=lambda x: tuple(str(v) for v in x))]


def _source_cell_summary(cells: Sequence[dict]) -> dict[str, Any]:
    statuses = collections.Counter(str(row["source_status"]) for row in cells)
    missing_supported = [
        row for row in cells
        if row["profile_support_status"] == "SUPPORTED"
        and row["source_status"] == "MISSING_SOURCE"
    ]
    loaded = [
        row for row in cells
        if str(row["source_status"]).startswith("LOADED_OBSERVED_ROWS_")
    ]
    return {
        "nominal_calendar_window": {
            "candidate_entry_start": WINDOW_START.isoformat(),
            "candidate_entry_end": WINDOW_END.isoformat(),
            "calendar_days_inclusive": CALENDAR_DAYS,
            "coverage_authority_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
            "claim_boundary": (
                "The window length is arithmetic only. No per-symbol trading-session/holiday "
                "schedule is bound, so absent H4 timestamps cannot be classified as market "
                "closures versus missing source and cannot be counted as no-op opportunities."
            ),
        },
        "requested_cells": len(cells),
        "supported_cells": sum(
            row["profile_support_status"] == "SUPPORTED" for row in cells
        ),
        "loaded_cells": len(loaded),
        "loaded_observed_rows_with_emissions_cells": int(
            statuses.get("LOADED_OBSERVED_ROWS_WITH_EMISSIONS", 0)
        ),
        "loaded_observed_rows_no_emission_cells": int(
            statuses.get("LOADED_OBSERVED_ROWS_NO_EMISSION", 0)
        ),
        "missing_supported_cells": len(missing_supported),
        "outside_active_profile_cells": int(statuses.get("OUTSIDE_ACTIVE_PROFILE", 0)),
        "observed_loaded_candidate_emissions": sum(
            int(row["observed_candidate_emissions"]) for row in loaded
        ),
        "full_window_candidate_emissions": None,
        "full_window_occurrence_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
        "unknown_full_window_candidate_count_is_not_zero": True,
        "status_counts": dict(sorted(statuses.items())),
        "missing_supported_source_cells": [
            {
                "source_cell_id": row["source_cell_id"],
                "symbol_canonical": row["symbol_canonical"],
                "exact_requirement": row["exact_requirement"],
            }
            for row in missing_supported
        ],
        "source_cells": list(cells),
    }


def _sleeve_summary(rows: Sequence[dict], source_cells: Sequence[dict]) -> dict[str, Any]:
    # A numeric walker outcome is available for loaded cells, but its quote/lifecycle
    # evidence is modelled. ``unconditional_roster`` below means only "before the
    # spread-floor filter"; it never asserts calendar or scheduled-bar completeness.
    quote_rows = [r for r in rows if r.get("quote_authority_status") == "MODELLED"]
    authority_rows = [r for r in rows if r.get("cost_authority_status") == "COMPLETE"]
    eval_rows = [r for r in rows if r["status"] == "EVALUABLE"]
    refused = [r for r in rows if r.get("floor_status") == "REFUSED"]
    floor_survivors = [
        r for r in quote_rows if r.get("floor_status") in {"SURVIVED", "NOT_APPLICABLE"}
    ]
    ne = [r for r in rows if r["status"] == "NOT_EVALUABLE"]
    cell_summary = _source_cell_summary(source_cells)
    source_blocked = bool(cell_summary["missing_supported_cells"])
    evaluation_status = (
        "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
        if source_blocked else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
    )
    reasons = collections.Counter(str(r.get("reason")) for r in rows if r.get("reason"))
    fields = (
        "r_level_validation_clip",
        "r_quote_validation_clip",
        "r_quote_gap_validation_clip",
        "r_net_level_all_cost_clip",
        "r_net_current_clip",
        "r_net_current_raw",
        "r_delta_quote_gross_clip",
        "r_delta_gap_on_quote_clip",
        "r_delta_current_vs_level_net_clip",
    )
    gross_fields = (
        "r_level_validation_clip", "r_quote_validation_clip",
        "r_quote_gap_validation_clip", "r_quote_gap_raw",
        "r_delta_quote_gross_clip", "r_delta_gap_on_quote_clip",
    )
    counterfactual_fields = (
        "counterfactual_pre_floor_r_net_level_all_cost_clip",
        "counterfactual_pre_floor_r_net_quote_all_cost_double_spread_clip",
        "counterfactual_pre_floor_r_net_current_clip",
        "counterfactual_pre_floor_r_net_current_raw",
    )
    unconditional = {
        "definition": (
            "Observed generator emissions on loaded source rows before the current "
            "spread-geometry floor. Full-window emissions remain unknown because no exact "
            "per-symbol H4 trading schedule is bound; missing-source emissions are also unknown. "
            "Every numeric quote/lifecycle value is a MODELLED H4-BID/scalar-spread "
            "diagnostic; counterfactual net on floor-refused rows is diagnostic only."
        ),
        "emitted": len(rows),
        "headline_eligible": False,
        "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
        "quote_authority_complete": 0,
        "quote_authority_modelled": len(quote_rows),
        "quote_authority_not_evaluable": len(rows) - len(quote_rows),
        "quote_lifecycle_model": QUOTE_LIFECYCLE_MODEL,
        "cost_authority_complete": len(authority_rows),
        "cost_authority_not_evaluable": len(rows) - len(authority_rows),
        "source_hash_class_records": _source_records(rows),
        "source_class_counts": dict(sorted(collections.Counter(
            r.get("source_class", "NOT_EVALUABLE") for r in rows
        ).items())),
        "coverage_counts": _coverage_counts(rows),
        "terminal_outcomes_quote_lifecycle_modelled": dict(sorted(collections.Counter(
            r["exit_reason_quote"] for r in quote_rows
        ).items())),
        "gross": {
            field: summary([r[field] for r in quote_rows if r.get(field) is not None])
            for field in gross_fields
        },
        "component_costs_all_emitted_with_not_evaluable_explicit": _component_summary(rows),
        "counterfactual_pre_floor_net": {
            field: summary([r[field] for r in authority_rows if r.get(field) is not None])
            for field in counterfactual_fields
        },
        "day_block_uncertainty_counterfactual_pre_floor": {
            field: moving_block_cluster_ci(authority_rows, field)
            for field in (
                "counterfactual_pre_floor_r_net_current_clip",
                "counterfactual_pre_floor_r_net_current_raw",
            )
        },
        "concentration_counterfactual_pre_floor": {
            field: concentration(authority_rows, field)
            for field in (
                "counterfactual_pre_floor_r_net_current_clip",
                "counterfactual_pre_floor_r_net_current_raw",
            )
        },
    }
    conditional = {
        "definition": (
            "Only loaded-cell rows that survive the durable current spread-geometry floor "
            "and have evaluable cost components. Quote/lifecycle remains MODELLED, and "
            "supported missing-source cells make this diagnostic ineligible as a headline."
        ),
        "headline_eligible": False,
        "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
        "evaluable": len(eval_rows),
        "retained_fraction_of_emitted": (
            round(len(eval_rows) / len(rows), 6) if rows else 0.0
        ),
        "terminal_outcomes": dict(sorted(collections.Counter(
            r["exit_reason_quote"] for r in eval_rows
        ).items())),
        "gross": {
            field: summary([r[field] for r in eval_rows]) for field in gross_fields
        },
        "component_costs": _component_summary(eval_rows),
        "net": {
            field: summary([r[field] for r in eval_rows])
            for field in ("r_net_current_clip", "r_net_current_raw")
        },
        "day_block_uncertainty": {
            "r_net_current_clip": moving_block_cluster_ci(eval_rows, "r_net_current_clip"),
            "r_net_current_raw": moving_block_cluster_ci(eval_rows, "r_net_current_raw"),
        },
        "concentration": {
            "r_net_current_clip": concentration(eval_rows, "r_net_current_clip"),
            "r_net_current_raw": concentration(eval_rows, "r_net_current_raw"),
        },
    }
    return {
        "evaluation_status": evaluation_status,
        "headline_eligible": False,
        "result_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
        "source_cell_denominators": cell_summary,
        "n_emitted": len(rows),
        "quote_authority_complete": 0,
        "quote_authority_modelled": len(quote_rows),
        "quote_authority_not_evaluable": len(rows) - len(quote_rows),
        "cost_authority_complete": len(authority_rows),
        "cost_authority_not_evaluable": len(rows) - len(authority_rows),
        "spread_floor_survivors": len(floor_survivors),
        "spread_floor_refused": len(refused),
        "conditional_survivor_evaluable": len(eval_rows),
        "n_candidates": len(rows),
        "n_evaluable": len(eval_rows),
        "n_refused_by_current_floor": len(refused),
        "n_not_evaluable": len(ne),
        "retained_fraction": round(len(eval_rows) / len(rows), 6) if rows else 0.0,
        "status_counts": dict(sorted(collections.Counter(r["status"] for r in rows).items())),
        "coverage_counts": _coverage_counts(rows),
        "source_class_counts": dict(sorted(collections.Counter(
            r.get("source_class", "NOT_EVALUABLE") for r in rows
        ).items())),
        "reason_counts": dict(sorted(reasons.items())),
        "metrics": {field: summary([r[field] for r in eval_rows]) for field in fields},
        "uncertainty": {
            "r_net_current_clip": moving_block_cluster_ci(eval_rows, "r_net_current_clip"),
            "r_net_current_raw": moving_block_cluster_ci(eval_rows, "r_net_current_raw"),
        },
        "concentration": {
            "r_net_current_clip": concentration(eval_rows, "r_net_current_clip"),
            "r_net_current_raw": concentration(eval_rows, "r_net_current_raw"),
        },
        "component_costs": _component_summary(eval_rows),
        "exit_reason_counts": dict(sorted(collections.Counter(
            r["exit_reason_quote"] for r in eval_rows
        ).items())),
        "quote_exit_reason_changed": sum(
            1 for r in eval_rows if r["exit_reason_changed_by_quote"]
        ),
        "gap_through_stops": sum(1 for r in eval_rows if r["gap"]["gap_leg"]),
        "validation_clip_moved_rows": sum(
            1 for r in eval_rows
            if abs(r["r_quote_gap_raw"] - r["r_quote_gap_validation_clip"]) > 1e-12
        ),
        "unconditional_roster": unconditional,
        "conditional_survivor_economics": conditional,
    }


def _band_robustness(band_summaries: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    sleeves = sorted(next(iter(band_summaries.values())))
    out: dict[str, Any] = {}
    for sleeve in sleeves:
        rows = {band: band_summaries[band][sleeve] for band in BANDS}
        means = {
            band: rows[band]["metrics"]["r_net_current_clip"]["mean"] for band in BANDS
        }
        intervals = {
            band: rows[band]["uncertainty"]["r_net_current_clip"]["ci95"] for band in BANDS
        }
        evaluable = {
            band: (
                not rows[band]["evaluation_status"].startswith("NOT_EVALUABLE_")
                and
                rows[band]["n_candidates"] > 0
                and rows[band]["n_evaluable"] >= 30
                and rows[band]["retained_fraction"] >= 0.60
            )
            for band in BANDS
        }
        point_positive = {
            band: bool(means[band] is not None and means[band] > 0) for band in BANDS
        }
        ci_positive = {
            band: bool(
                intervals[band][0] is not None and float(intervals[band][0]) > 0
            )
            for band in BANDS
        }
        source_dispositions = {
            rows[band]["evaluation_status"]
            for band in BANDS
            if rows[band]["evaluation_status"].startswith("NOT_EVALUABLE_")
        }
        if "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP" in source_dispositions:
            disposition = "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
        elif source_dispositions:
            disposition = "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
        elif not all(evaluable.values()):
            disposition = "NOT_EVALUABLE_ACROSS_FULL_SPREAD_BAND"
        elif len(set(point_positive.values())) > 1:
            disposition = "MODELLED_MODEL_SENSITIVE_SIGN"
        elif all(point_positive.values()) and all(ci_positive.values()):
            disposition = "MODELLED_POSITIVE_ALL_BANDS_CI_EXCLUDES_ZERO"
        elif all(point_positive.values()):
            disposition = "MODELLED_POSITIVE_POINT_ALL_BANDS_UNCERTAIN"
        elif not any(point_positive.values()):
            disposition = "MODELLED_NONPOSITIVE_POINT_ALL_BANDS"
        else:  # pragma: no cover - exhaustive guard
            disposition = "UNCLASSIFIED"
        numeric = [float(v) for v in means.values() if v is not None]
        out[sleeve] = {
            "disposition": disposition,
            "evaluable_by_band": evaluable,
            "point_mean_by_band": means,
            "ci95_by_band": intervals,
            "point_positive_by_band": point_positive,
            "ci_excludes_zero_positive_by_band": ci_positive,
            "min_point_mean": round(min(numeric), 6) if numeric else None,
            "max_point_mean": round(max(numeric), 6) if numeric else None,
        }
    return out


def _sleeve_scorecard(
    *,
    namespace: str,
    account: str,
    sleeve: str,
    band_summaries: Mapping[str, Mapping[str, Any]],
    source_cells: Sequence[dict],
    runtime_parity: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one compact decision card without upgrading partial evidence.

    The card intentionally carries both the pre-floor roster and conditional survivor
    diagnostics.  Keeping both prevents a positive survivor mean from suppressing current
    floor refusals.  Neither numeric view is a full-window or native-graph W7 result.
    """

    cells = [row for row in source_cells if row["sleeve"] == sleeve]
    cell_summary = _source_cell_summary(cells)
    missing = [
        row for row in cells
        if row["profile_support_status"] == "SUPPORTED"
        and row["source_status"] == "MISSING_SOURCE"
    ]
    loaded = [
        row for row in cells
        if str(row["source_status"]).startswith("LOADED_OBSERVED_ROWS_")
    ]
    evaluation_status = (
        "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
        if missing else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
    )
    local_frontier = set(runtime_parity["local_committed_surface"]["frontier_exits"])
    host_frontier = set(
        runtime_parity["latest_durable_host_observation"]["frontier_exits"]
    )
    exit_contract_matches_host = (sleeve in local_frontier) == (sleeve in host_frontier)
    recommendation = "NE" if (missing or not exit_contract_matches_host) else "RESEARCH_ONLY"
    if missing:
        recommendation_basis = (
            "One or more profile-supported generator cells have no committed source. "
            "Their occurrence counts are unknown, so no sleeve result or repair verdict "
            "can be inferred from the loaded subset."
        )
    elif not exit_contract_matches_host:
        recommendation_basis = (
            "The local declaration and pre-integration recost use a different frontier-exit "
            "selection from the latest durable host observation. This sleeve's local rows do "
            "not represent the observed live exit contract, so its live-parity result is not "
            "evaluable."
        )
    else:
        recommendation_basis = (
            "All profile-supported source files are present, but scheduled-bar continuity "
            "is unbound, quote/fill lifecycle is MODELLED, and the historical native "
            "admission/router/account state is absent. The observed mechanism is useful only "
            "for research until those authorities close."
        )

    diagnostics_by_band: dict[str, Any] = {}
    for band in BANDS:
        doc = band_summaries[band][sleeve]
        pre_floor = doc["unconditional_roster"]
        survivors = doc["conditional_survivor_economics"]
        diagnostics_by_band[band] = {
            "evaluation_status": doc["evaluation_status"],
            "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
            "quote_lifecycle_coverage": "MODELLED",
            "observed_emitted": doc["n_emitted"],
            "current_floor_survivors": doc["spread_floor_survivors"],
            "current_floor_refusals": doc["spread_floor_refused"],
            "cost_evaluable_survivors": doc["conditional_survivor_evaluable"],
            "modelled_gross_all_observed_rows": pre_floor["gross"][
                "r_quote_gap_validation_clip"
            ],
            "modelled_counterfactual_net_all_observed_rows_pre_floor": pre_floor[
                "counterfactual_pre_floor_net"
            ]["counterfactual_pre_floor_r_net_current_clip"],
            "modelled_net_current_floor_survivors": survivors["net"][
                "r_net_current_clip"
            ],
            "uncertainty": {
                "counterfactual_pre_floor": pre_floor[
                    "day_block_uncertainty_counterfactual_pre_floor"
                ]["counterfactual_pre_floor_r_net_current_clip"],
                "current_floor_survivors": survivors["day_block_uncertainty"][
                    "r_net_current_clip"
                ],
            },
            "concentration": {
                "counterfactual_pre_floor": pre_floor[
                    "concentration_counterfactual_pre_floor"
                ]["counterfactual_pre_floor_r_net_current_clip"],
                "current_floor_survivors": survivors["concentration"][
                    "r_net_current_clip"
                ],
            },
        }

    return {
        "schema": SLEEVE_SCORECARD_SCHEMA,
        "namespace": namespace,
        "account": account,
        "sleeve": sleeve,
        "evaluation_status": evaluation_status,
        "headline_eligible": False,
        "native_graph_status": "NOT_EVALUABLE_NATIVE_GRAPH_INCOMPLETE",
        "runtime_parity": {
            "status": (
                "NOT_EVALUABLE_EXIT_CONTRACT_DIVERGENCE"
                if not exit_contract_matches_host
                else runtime_parity["overall_status"]
            ),
            "local_effective_registry_member": sleeve in set(
                runtime_parity["local_committed_surface"][
                    "effective_registry_intersection"
                ]
            ),
            "latest_host_effective_registry_member": sleeve in set(
                runtime_parity["latest_durable_host_observation"][
                    "effective_registry_intersection"
                ]
            ),
            "local_frontier_exit_applied": sleeve in local_frontier,
            "latest_host_frontier_exit_applied": sleeve in host_frontier,
            "exit_contract_matches_latest_host_observation": exit_contract_matches_host,
            "live_parity_claimed": False,
        },
        "coherent_source_coverage": {
            "status": evaluation_status,
            "requested_cells": cell_summary["requested_cells"],
            "supported_cells": cell_summary["supported_cells"],
            "loaded_cells": cell_summary["loaded_cells"],
            "loaded_observed_rows_with_emissions_cells": cell_summary[
                "loaded_observed_rows_with_emissions_cells"
            ],
            "loaded_observed_rows_no_emission_cells": cell_summary[
                "loaded_observed_rows_no_emission_cells"
            ],
            "missing_supported_cells": cell_summary["missing_supported_cells"],
            "outside_active_profile_cells": cell_summary[
                "outside_active_profile_cells"
            ],
            "loaded_source_class_counts": dict(sorted(collections.Counter(
                str(row["source_class"]) for row in loaded
            ).items())),
            "calendar_schedule_authority_status": (
                "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
            ),
            "calendar_denominator_claimed_unconditional": False,
            "full_window_occurrence_status": (
                "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
            ),
        },
        "emissions_activity": {
            "scope": "DIRECT_GENERATOR_OBSERVED_SOURCE_ROWS_PARTIAL_ONLY",
            "native_book_engine_decision_slot_conservation": (
                "NOT_EVALUABLE_NO_TYPED_DECISION_ORDINAL_TERMINALS"
            ),
            "observed_generator_bar_evaluations": sum(
                int(row["observed_bar_evaluations"]) for row in loaded
            ),
            "observed_candidate_emissions": sum(
                int(row["observed_candidate_emissions"]) for row in loaded
            ),
            "full_window_candidate_emissions": None,
            "full_window_candidate_count_unknown_not_zero": True,
            "observed_scored_rows_by_band": {
                band: int(band_summaries[band][sleeve]["n_emitted"])
                for band in BANDS
            },
        },
        "modelled_gross_net_diagnostics_by_band": diagnostics_by_band,
        "missing_supported_source_cells": [
            {
                "source_cell_id": row["source_cell_id"],
                "symbol_canonical": row["symbol_canonical"],
                "exact_requirement": row["exact_requirement"],
            }
            for row in missing
        ],
        "recommendation": recommendation,
        "recommendation_basis": recommendation_basis,
        "allowed_recommendation_vocabulary": list(SCORECARD_RECOMMENDATIONS),
        "arming_or_composition_change_authorized": False,
    }


def _historical_published_separation(
    prior: Mapping[str, Any], summaries: Mapping[str, Any], robustness: Mapping[str, Any],
    namespace: str, account: str,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for sleeve, current in summaries.items():
        old = prior["sleeves"][sleeve]["published"][account]
        net = current["metrics"]["r_net_current_clip"]["mean"]
        gross = current["metrics"]["r_quote_gap_validation_clip"]["mean"]
        n_eval = int(current["n_evaluable"])
        old_net = float(old["modelled_horizon_net_r"])
        old_gross = float(old["gross_r"])
        source_blocked = current["evaluation_status"].startswith("NOT_EVALUABLE_")
        out[sleeve] = {
            "authoritative_comparison": False,
            "comparison_status": (
                current["evaluation_status"]
                if source_blocked
                else "MODELLED_DESCRIPTIVE_SEPARATION_FROM_HISTORICAL_RECORD_ONLY"
            ),
            "headline_eligible": False,
            "prior_n": int(old["n"]),
            "current_candidates": int(current["n_candidates"]),
            "current_evaluable": n_eval,
            "descriptive_population_count_difference": (
                None if source_blocked else n_eval - int(old["n"])
            ),
            "prior_published_gross_r": old_gross,
            "current_quote_gap_gross_r": None if source_blocked else gross,
            "descriptive_gross_difference": (
                round(gross - old_gross, 6)
                if gross is not None and not source_blocked else None
            ),
            "prior_modelled_horizon_net_r": old_net,
            "current_exact_exit_cost_net_r": None if source_blocked else net,
            "descriptive_net_difference": (
                round(net - old_net, 6)
                if net is not None and not source_blocked else None
            ),
            "observed_source_rows_partial_diagnostic": {
                "candidate_count": n_eval,
                "quote_gap_gross_r_mean": gross,
                "current_cost_net_r_mean": net,
                "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
            },
            "prior_survivor_tier": old["survivor_tier"],
            "current_sign": (
                "NOT_EVALUABLE" if source_blocked else
                "POSITIVE" if net is not None and net > 0 else
                "NONPOSITIVE" if net is not None else "NOT_EVALUABLE"
            ),
            "coverage_disposition": robustness[sleeve]["disposition"],
            "band_robustness": robustness[sleeve],
            "claim_scope": (
                "Simultaneous population, generator-lineage, exit, quote/gap, holding-time and "
                "cost separation from a historical record whose later-revised cost input was not "
                "hash-bound. This is not an authoritative delta, attribution to one defect, or a "
                "broad-V4 result."
            ),
        }
    return out


def _write_json(path: Path, doc: Any) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True, default=str) + "\n")


def _write_jsonl(path: Path, rows: Sequence[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str))
            fh.write("\n")


def _write_gzip_jsonl(path: Path, rows: Sequence[dict]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as z:
            with io.TextIOWrapper(z, encoding="utf-8", newline="\n") as text:
                for row in rows:
                    text.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str))
                    text.write("\n")


def _render_report_legacy(result: Mapping[str, Any], prior: Mapping[str, Any]) -> str:
    """Superseded pre-truth renderer retained only to make the receipt diff reviewable.

    It is never called. In particular, its old ``unconditional``/``COMPLETE`` labels are
    not authoritative; :func:`_render_report` below is the sole output renderer.
    """
    def num(value: Any) -> str:
        return "NE" if value is None else f"{float(value):.6f}"

    def mean_sum(doc: Mapping[str, Any]) -> str:
        return f"{num(doc.get('mean'))}/{num(doc.get('sum'))}"

    def cov(doc: Mapping[str, int]) -> str:
        return "/".join(str(int(doc.get(key, 0))) for key in COVERAGE_CLASSES)

    source_keys: dict[tuple, str] = {}
    source_docs: dict[tuple, dict] = {}
    for account in result["accounts"].values():
        for band in BANDS:
            for sleeve in account["bands"][band].values():
                for row in sleeve["unconditional_roster"]["source_hash_class_records"]:
                    key = (
                        row["source_account"], row["source_broker"], row["source_class"],
                        row["path"], row["sha256"], row["sidecar_sha256"],
                    )
                    source_docs[key] = row
    for idx, key in enumerate(sorted(source_docs, key=lambda x: tuple(str(v) for v in x)), 1):
        source_keys[key] = f"S{idx}"

    lines = [
        "# Wave 21 — exact-current W7 recost/replay (pre-integration receipt)",
        "",
        f"**Headline status: `{result['headline_status']}`.** This is a result-bearing offline ",
        "per-unit-R replay, but it is not the final W7 headline until the shared Wave-21 ",
        "cost/quote-truth repairs are integrated and this unchanged runner is rerun with ",
        "`--integration-state POST_INTEGRATION_WAVE21_COST_QUOTE_TRUTH`.",
        "",
        "The rows come only from `src.safety.armed_set.armed_sleeves()` after durable-declaration ",
        "reconciliation. They use W7's production sleeve generators and native exit contracts. ",
        "They do not count the compatibility Selector/Scheduler packets as decisions, infer broad ",
        "V4 results, select a book, recommend promotion, or mutate broker/live state.",
        "",
        "Coverage cells are `MEASURED/TRANSFERRED/MODELLED/NOT_EVALUABLE`. Gross/net cells are ",
        "`mean/sum R`. Roster means are unconditional on the spread floor; survivor means are ",
        "conditional on the current floor. Pre-floor net on refused rows is counterfactual only.",
        "",
    ]

    for namespace, account in sorted(result["accounts"].items()):
        lines.extend([
            f"## Current `{account['account']}` rows — `{namespace}`",
            "",
            "| Sleeve | Band | Emit | Quote auth | Cost auth | Floor S/R | Eval | "
            "Roster terminal outcomes | Gross roster | Components roster C/Sw/Sp/Sl | "
            "Pre-floor net | Gross survivor | Net survivor | Day-block CI | "
            "Top concentration symbol/year | Row coverage | Sources |",
            "|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---|---|---|---|",
        ])
        for sleeve_name in sorted(account["bands"][PRIMARY_BAND]):
            for band in BANDS:
                doc = account["bands"][band][sleeve_name]
                un = doc["unconditional_roster"]
                con = doc["conditional_survivor_economics"]
                component_cells = []
                component_doc = un["component_costs_all_emitted_with_not_evaluable_explicit"]
                for name in ("commission_r", "swap_r", "spread_r", "slippage_r"):
                    comp = component_doc[name]
                    component_cells.append(
                        f"{num(comp['value']['mean'])}[{cov(comp['coverage'])}]"
                    )
                source_ids = []
                for row in un["source_hash_class_records"]:
                    key = (
                        row["source_account"], row["source_broker"], row["source_class"],
                        row["path"], row["sha256"], row["sidecar_sha256"],
                    )
                    source_ids.append(source_keys[key])
                net_conc = con["concentration"]["r_net_current_clip"]
                top_sym = net_conc["by_symbol"]["top_absolute"]
                top_year = net_conc["by_entry_year"]["top_absolute"]
                concentration_cell = (
                    f"{top_sym[0]['name']} {top_sym[0]['share_abs_pct']}% / "
                    f"{top_year[0]['name']} {top_year[0]['share_abs_pct']}%"
                    if top_sym and top_year else "NE"
                )
                lines.append(
                    "| " + " | ".join([
                        sleeve_name,
                        band,
                        str(doc["n_emitted"]),
                        f"{doc['quote_authority_complete']}/{doc['quote_authority_not_evaluable']}",
                        f"{doc['cost_authority_complete']}/{doc['cost_authority_not_evaluable']}",
                        f"{doc['spread_floor_survivors']}/{doc['spread_floor_refused']}",
                        str(doc["conditional_survivor_evaluable"]),
                        ", ".join(
                            f"{key}:{value}" for key, value in
                            un["terminal_outcomes_quote_authority_complete"].items()
                        ) or "NE",
                        mean_sum(un["gross"]["r_quote_gap_validation_clip"]),
                        "/".join(component_cells),
                        mean_sum(un["counterfactual_pre_floor_net"][
                            "counterfactual_pre_floor_r_net_current_clip"
                        ]),
                        mean_sum(con["gross"]["r_quote_gap_validation_clip"]),
                        mean_sum(con["net"]["r_net_current_clip"]),
                        str(con["day_block_uncertainty"]["r_net_current_clip"]["ci95"]),
                        concentration_cell,
                        cov(un["coverage_counts"]),
                        ",".join(source_ids) or "NE",
                    ]) + " |"
                )
        lines.append("")

    lines.extend([
        "## Exact source/hash authority",
        "",
        "| ID | Source account | Broker | Class | Path | SHA-256 | Sidecar SHA-256 |",
        "|---|---|---|---|---|---|---|",
    ])
    for key in sorted(source_docs, key=lambda x: tuple(str(v) for v in x)):
        row = source_docs[key]
        lines.append(
            f"| {source_keys[key]} | {row['source_account']} | {row['source_broker']} | "
            f"{row['source_class']} | `{row['path']}` | `{row['sha256']}` | "
            f"`{row['sidecar_sha256']}` |"
        )

    lines.extend([
        "",
        "## Historical publication reconciliation — not an authoritative comparator",
        "",
        f"`{prior['published_artifact']}` at `{prior['published_sha256']}` is retained as a ",
        "historical record. Its later-revised FTMO cost input was not hash-bound, and its old cache ",
        "identity is non-unique. The descriptive differences below therefore do not carry an ",
        "authoritative delta claim.",
        "",
        "| Account | Sleeve | Prior/current n | Prior/current gross | Prior/current net | "
        "Descriptive gross/net difference | Band disposition |",
        "|---|---|---:|---:|---:|---:|---|",
    ])
    for account in result["accounts"].values():
        for sleeve, row in sorted(
            account["historical_published_separation_non_authoritative"].items()
        ):
            lines.append(
                f"| {account['account']} | {sleeve} | {row['prior_n']}/{row['current_evaluable']} | "
                f"{num(row['prior_published_gross_r'])}/{num(row['current_quote_gap_gross_r'])} | "
                f"{num(row['prior_modelled_horizon_net_r'])}/{num(row['current_exact_exit_cost_net_r'])} | "
                f"{num(row['descriptive_gross_difference'])}/{num(row['descriptive_net_difference'])} | "
                f"{row['coverage_disposition']} |"
            )

    lines.extend([
        "",
        "## Explicit higher-information stops",
        "",
        "redacted_account high-band xvol is **52 emitted, 52 cost-authority complete, 0 floor survivors, "
        "52 floor refusals**. redacted_account high-band sub-mid is **268 emitted, 268 cost-authority ",
        "complete, 35 floor survivors, 233 floor refusals**. These are true current spread-floor ",
        "exclusions, not missing/transferred cost rows; survivor economics are conditional and the ",
        "unconditional pre-floor values remain separately labelled counterfactual.",
        "",
        "Lot/account cash translation is `NOT_EVALUABLE`: exact history would require the live ",
        "BookOwner governor/unit state, same-tick account equity/headroom, fresh broker tick and ",
        "symbol_info, plus broker `order_calc_profit` before the current ExecutionEngine volume ",
        "normalizer. None exists for the 2015–2026 rows, so no emulator or imputation is used.",
        "",
        "Missing bar sources and outside-profile symbols are listed with exact requirements in ",
        "`W7_CURRENT_INPUT_MANIFEST_V1.json` and `W7_CURRENT_RECOST_V1.json`. Their unknown candidate ",
        "counts are not treated as zero.",
        "",
        "**No promotion, arming, risk-dial, or composition decision is made here.**",
        "",
    ])
    return "\n".join(line.rstrip() for line in lines)


def _render_report(result: Mapping[str, Any], prior: Mapping[str, Any]) -> str:
    """Render the fail-closed W7 headline and keep partial numbers subordinate."""

    def num(value: Any) -> str:
        return "NE" if value is None else f"{float(value):.6f}"

    def mean_sum(doc: Mapping[str, Any]) -> str:
        return f"{num(doc.get('mean'))}/{num(doc.get('sum'))}"

    def band_stats(card: Mapping[str, Any], field: str) -> str:
        return ", ".join(
            f"{band}:{mean_sum(card['modelled_gross_net_diagnostics_by_band'][band][field])}"
            for band in BANDS
        )

    lines = [
        "# Wave 21 — exact-current W7 truth receipt",
        "",
        f"**Headline status: `{result['headline_status']}`.** The W7 profitability headline is ",
        "`NOT_EVALUABLE`. Ten supported source cells are absent and the historical rows do not ",
        "contain the state needed to traverse W7's native admission, risk, router, and broker ",
        "lifecycle. Exact partial measurements from loaded cells remain below as diagnostics only; ",
        "they are not a survivor-book result, profitability claim, or promotion input.",
        "",
        "The quote/lifecycle class is `MODELLED`, never `COMPLETE` or `MEASURED`: the walker uses ",
        "H4 BID OHLC, an era/hour scalar spread at entry, and a conservative open-through gap rule. ",
        "There are no historical ASK quotes/ticks or resting-order lifecycle observations.",
        "",
        "## Native W7 graph boundary",
        "",
        "| Stage | Status | What this lane did |",
        "|---|---|---|",
    ]
    for stage in result["native_flow_truth"]["stages"]:
        lines.append(
            f"| {stage['stage']} | `{stage['status']}` | {stage['evidence']} |"
        )
    lines.extend([
        "",
        "`execution_packets.py`'s `gtos_vnext_selector_v4_*` and ",
        "`gtos_vnext_scheduler_v4_*` fields are compatibility shims emitted after native W7 ",
        "admission. They are not Selector V4 or Scheduler V4 decisions and are not counted here.",
        "",
        "The direct generator loop is also not a terminally conserved BookEngine replay. The ",
        "native wrapper silently continues on insufficient bars, stale/chronology exceptions, and ",
        "generator exceptions. Without one typed terminal per active-spec × symbol × decision ",
        "ordinal, the native occurrence denominator remains `NOT_EVALUABLE`.",
        "",
        "Broad-stack partial headroom does not transfer. Native W7 sizes in descending conviction ",
        "and uses first-fit against remaining gross-risk headroom; a unit that does not fit is ",
        "shed/refused rather than proportionally reduced.",
        "",
        "## Local versus latest durable host runtime surface",
        "",
        "| Account | Local include_clean3 | Local effective declared tags | Local frontier | "
        "Latest host include_clean3 | Latest host effective declared tags | Latest host frontier | Status |",
        "|---|---:|---|---|---:|---|---|---|",
    ])
    for namespace, parity in result["native_flow_truth"]["runtime_parity"].items():
        local = parity["local_committed_surface"]
        host = parity["latest_durable_host_observation"]
        lines.append(
            "| " + " | ".join([
                result["accounts"][namespace]["account"],
                str(local["include_clean3"]),
                ",".join(local["effective_registry_intersection"]) or "none",
                ",".join(local["frontier_exits"]) or "none",
                str(host["include_clean3"]),
                ",".join(host["effective_registry_intersection"]) or "none",
                ",".join(host["frontier_exits"]) or "none",
                f"`{parity['overall_status']}`",
            ]) + " |"
        )
    lines.extend([
        "",
        "The host columns are the upstream read-only Wave-21 live-audit observation supplied to ",
        "this scoped lane; its durable integration receipt is not local to this branch. The ",
        "mismatch is therefore disclosed, never used to claim local or live parity. In particular, ",
        "FTMO `crypto` rows use the local empty frontier and are not the observed host exit contract.",
        "",
        "## Supported source gaps that block the headline",
        "",
        "| Account | Sleeve | Symbol | Source status | Candidate count | Exact requirement |",
        "|---|---|---|---|---:|---|",
    ])
    for row in sorted(
        (r for r in result["source_gaps"] if r["source_status"] == "MISSING_SOURCE"),
        key=lambda r: (r["namespace"], r["sleeve"], r["symbol_canonical"]),
    ):
        lines.append(
            f"| {row['account']} | {row['sleeve']} | {row['symbol_canonical']} | "
            f"`{row['source_status']}` | unknown, not zero | {row['exact_requirement']} |"
        )
    lines.extend([
        "",
        "Every requested account/sleeve/symbol cell—including loaded observed rows with no ",
        "emission, missing source, and outside-profile cells—is in ",
        "`W7_CURRENT_SOURCE_CELLS_V1.jsonl`. The nominal window is ",
        f"{CALENDAR_DAYS} inclusive calendar days ({WINDOW_START.isoformat()} through ",
        f"{WINDOW_END.isoformat()}), but it is **not** claimed as an unconditional occurrence ",
        "denominator: no exact per-symbol trading-session/holiday schedule is bound, so absent ",
        "H4 timestamps cannot be separated from legitimate closures. Full-window candidate ",
        "counts are therefore unknown; loaded counts cover observed source rows only.",
        "",
        "## Loaded-cell diagnostics by account, sleeve, and band",
        "",
        "All numeric columns in this table are `OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY`.",
        "",
        "| Account | Sleeve | Band | Result status | Source cells observed emit/no-emission/missing/outside | "
        "Emitted | Quote modelled | Cost evaluable | Floor survive/refuse | Survivor rows | "
        "Net clip mean/sum | Row coverage M/T/Md/NE |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for account in result["accounts"].values():
        for sleeve_name in sorted(account["bands"][PRIMARY_BAND]):
            for band in BANDS:
                doc = account["bands"][band][sleeve_name]
                cells = doc["source_cell_denominators"]
                net = doc["conditional_survivor_economics"]["net"]["r_net_current_clip"]
                cov = doc["coverage_counts"]
                lines.append(
                    "| " + " | ".join([
                        account["account"],
                        sleeve_name,
                        band,
                        f"`{doc['evaluation_status']}`",
                        "/".join(str(cells[key]) for key in (
                            "loaded_observed_rows_with_emissions_cells",
                            "loaded_observed_rows_no_emission_cells",
                            "missing_supported_cells", "outside_active_profile_cells",
                        )),
                        str(doc["n_emitted"]),
                        str(doc["quote_authority_modelled"]),
                        str(doc["cost_authority_complete"]),
                        f"{doc['spread_floor_survivors']}/{doc['spread_floor_refused']}",
                        str(doc["conditional_survivor_evaluable"]),
                        f"{num(net['mean'])}/{num(net['sum'])}",
                        "/".join(str(cov[key]) for key in COVERAGE_CLASSES),
                    ]) + " |"
                )

    lines.extend([
        "",
        "## Sleeve scorecard — evidence disposition, not an arming decision",
        "",
        "`NE` means a supported source cell is absent or the scored exit contract differs from ",
        "the latest durable host observation. `RESEARCH_ONLY` means all supported ",
        "source files are present but scheduled-bar continuity, observed quote/fill lifecycle, ",
        "and native historical admission/router/account state remain incomplete. No sleeve earns ",
        "`KEEP` or `REPAIR` from these partial modelled rows.",
        "",
        "Gross and net cells below are `mean/sum R` for low/mid/high. Gross and pre-floor net ",
        "cover every observed emitted row; survivor net is conditional on the current spread ",
        "floor. This paired display prevents positive-by-suppression.",
        "",
        "| Account | Sleeve | Evaluation | Runtime parity | Source loaded/requested/missing/outside | "
        "Observed generator evaluations/emissions | Modelled gross all observed L/M/H | "
        "Modelled pre-floor net all observed L/M/H | Modelled survivor net L/M/H | "
        "Mid survivor CI95 | Mid top abs symbol/year | Missing cells | Recommendation |",
        "|---|---|---|---|---:|---:|---|---|---|---|---|---|---|",
    ])
    for card in result["sleeve_scorecard"]["rows"]:
        coverage = card["coherent_source_coverage"]
        activity = card["emissions_activity"]
        mid = card["modelled_gross_net_diagnostics_by_band"][PRIMARY_BAND]
        ci = mid["uncertainty"]["current_floor_survivors"]["ci95"]
        conc = mid["concentration"]["current_floor_survivors"]
        top_symbol = conc["by_symbol"]["top_absolute"]
        top_year = conc["by_entry_year"]["top_absolute"]
        concentration_cell = (
            f"{top_symbol[0]['name']} {top_symbol[0]['share_abs_pct']}% / "
            f"{top_year[0]['name']} {top_year[0]['share_abs_pct']}%"
            if top_symbol and top_year else "NE"
        )
        missing_symbols = ",".join(
            row["symbol_canonical"]
            for row in card["missing_supported_source_cells"]
        ) or "none"
        lines.append(
            "| " + " | ".join([
                card["account"],
                card["sleeve"],
                f"`{card['evaluation_status']}`",
                f"`{card['runtime_parity']['status']}`",
                "/".join(str(coverage[key]) for key in (
                    "loaded_cells", "requested_cells", "missing_supported_cells",
                    "outside_active_profile_cells",
                )),
                f"{activity['observed_generator_bar_evaluations']}/"
                f"{activity['observed_candidate_emissions']}",
                band_stats(card, "modelled_gross_all_observed_rows"),
                band_stats(
                    card,
                    "modelled_counterfactual_net_all_observed_rows_pre_floor",
                ),
                band_stats(card, "modelled_net_current_floor_survivors"),
                f"[{num(ci[0])}, {num(ci[1])}]",
                concentration_cell,
                missing_symbols,
                f"`{card['recommendation']}`",
            ]) + " |"
        )

    lines.extend([
        "",
        "## Historical publication boundary",
        "",
        f"`{prior['published_artifact']}` at `{prior['published_sha256']}` is retained only as a ",
        "historical record. Its non-unique cache identity and unbound later-revised cost input ",
        "prevent an authoritative row delta. For sleeves with a supported source gap, current sign ",
        "and descriptive differences are explicitly `NOT_EVALUABLE`; loaded-cell partial values ",
        "remain nested diagnostics only.",
        "",
        "## Exact higher-information stop",
        "",
        "Close the ten supported source cells with committed, hash-bound broker-clock H4 OHLCV ",
        "covering at least 259 closed warm-up bars before the fixed window and 80 H4 close-out bars ",
        "after it. Bind an exact per-symbol trading-session/holiday schedule (or a capture manifest ",
        "that proves scheduled-bar completeness) before treating observed-row zero emissions as ",
        "full-window no-ops. To elevate quote/lifecycle above `MODELLED`, acquire historical BID/ASK or tick ",
        "quotes plus resting-order/fill lifecycle authority. To claim native W7 economics, also ",
        "reconstruct exact as-of governor, open-risk, admission/occupancy, account, tick, symbol, ",
        "`order_calc_profit`, and execution state. No approximation is substituted for those inputs.",
        " Add typed terminal rows for every native BookEngine decision ordinal before claiming full ",
        "occurrence conservation, and reconcile the local include-clean3/frontier bytes to a bound ",
        "host observation before claiming runtime parity.",
        "",
        "**No promotion, arming, risk-dial, composition, broker, order, or live-state mutation is made.**",
        "",
    ])
    return "\n".join(line.rstrip() for line in lines)


def run(*, integration_state: str = "PRE_INTEGRATION_957_COST_QUOTE_TRUTH") -> dict:
    assert_consistent()
    declaration = declared_arming()
    raw_declaration = armed_manifest()
    if set(declaration) != set(ACCOUNT_META):
        raise RuntimeError(
            f"account metadata is stale: declaration={sorted(declaration)} driver={sorted(ACCOUNT_META)}"
        )
    armed_by_ns = {
        ns: tuple(sorted(armed_sleeves(ns)))
        for ns in sorted(declaration)
    }
    for sleeves in armed_by_ns.values():
        _generator_authority_checks(sleeves)

    prior = prior_reconciliation(armed_by_ns)
    _write_json(OUT_PRIOR, prior)

    bar_index, bar_manifest = _bar_manifest_index()
    costs = load_broker_true_costs(COSTS_PATH)
    spread_model = load_spread_model(SPREAD_PATH)
    base_cfg = yaml.safe_load((REPO / "config/agent_config.yaml").read_text()) or {}
    input_series: dict[tuple[str, str], Series] = {}
    source_cells: list[dict] = []
    source_gaps: list[dict] = []
    generation_tel: dict[str, dict] = {}
    rows_all: list[dict] = []
    account_summaries: dict[str, Any] = {}
    scorecard_rows: list[dict] = []
    runtime_parity_by_namespace: dict[str, Any] = {}

    for namespace in sorted(declaration):
        arming = declaration[namespace]
        meta = ACCOUNT_META[namespace]
        account = meta["account"]
        merged_cfg = apply_profile_overrides(copy.deepcopy(base_cfg), arming.profile)
        runtime_cfg = dict(merged_cfg.get("gtos_vnext_runtime") or {})
        resolver = build_broker_symbol_resolver(merged_cfg)
        floor_selection = {s: None for s in arming.spread_geometry_floor}
        sleeves = tuple(sorted(armed_sleeves(namespace)))
        local_runtime_surface = _local_effective_runtime_surface(
            runtime_cfg, sleeves, arming.frontier_exits
        )
        runtime_parity = _runtime_parity_doc(namespace, local_runtime_surface)
        runtime_parity_by_namespace[namespace] = runtime_parity
        namespace_rows: list[dict] = []

        seeds_by_sleeve: dict[str, list[tuple[dict, Series]]] = {
            s: [] for s in sleeves
        }
        for sleeve in sleeves:
            for symbol in SURFACE[sleeve]:
                cell_id = f"{namespace}::{sleeve}::{symbol}"
                cell_base = {
                    "schema": SOURCE_CELL_SCHEMA,
                    "source_cell_id": cell_id,
                    "namespace": namespace,
                    "account": account,
                    "profile": arming.profile,
                    "sleeve": sleeve,
                    "symbol_canonical": symbol,
                    "candidate_entry_start": WINDOW_START.isoformat(),
                    "candidate_entry_end": WINDOW_END.isoformat(),
                    "nominal_window_calendar_days_inclusive": CALENDAR_DAYS,
                    "calendar_schedule_authority_status": (
                        "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
                    ),
                    "calendar_denominator_claimed_unconditional": False,
                }
                if not resolver.supports(symbol):
                    cell = {
                        **cell_base,
                        "profile_support_status": "OUTSIDE_ACTIVE_PROFILE",
                        "source_status": "OUTSIDE_ACTIVE_PROFILE",
                        "evaluation_status": "NOT_EVALUABLE_OUTSIDE_ACTIVE_PROFILE",
                        "observed_candidate_emissions": None,
                        "observed_bar_evaluations": None,
                        "full_window_candidate_emissions": None,
                        "candidate_occurrence_completeness": "NOT_APPLICABLE_OUTSIDE_PROFILE",
                        "reason": "active profile has no instrument contract",
                        "exact_requirement": (
                            "No source acquisition can make this symbol executable on the current "
                            "profile. A profile/composition change is owner-controlled and outside "
                            "this recost lane."
                        ),
                    }
                    source_cells.append(cell)
                    source_gaps.append(cell)
                    generation_tel[cell_id] = {
                        "source_status": cell["source_status"],
                        "bar_evaluations": None,
                        "candidates": None,
                    }
                    continue
                source_row, source_class, source_account = _source_for(
                    account, meta["bar_broker"], symbol, bar_index
                )
                if source_row is None:
                    cell = {
                        **cell_base,
                        "profile_support_status": "SUPPORTED",
                        "source_status": "MISSING_SOURCE",
                        "evaluation_status": "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP",
                        "observed_candidate_emissions": None,
                        "observed_bar_evaluations": None,
                        "full_window_candidate_emissions": None,
                        "candidate_occurrence_completeness": (
                            "NOT_EVALUABLE_MISSING_SOURCE_UNKNOWN_NOT_ZERO"
                        ),
                        "reason": "no native H4 source and no declared FTMO transfer source",
                        "exact_requirement": (
                            f"Acquire broker-clock H4 OHLCV for {meta['bar_broker']}/{symbol} "
                            f"covering at least 259 closed bars before {WINDOW_START.isoformat()} "
                            f"through 80 H4 bars after {WINDOW_END.isoformat()}, with a "
                            ".timebase.json sidecar and manifest SHA-256; or commit an explicit "
                            "named peer-transfer authority."
                        ),
                    }
                    source_cells.append(cell)
                    source_gaps.append(cell)
                    generation_tel[cell_id] = {
                        "source_status": cell["source_status"],
                        "bar_evaluations": None,
                        "candidates": None,
                    }
                    continue
                skey = (namespace, symbol)
                if skey not in input_series:
                    input_series[skey] = _load_one_series(
                        symbol, source_row, str(source_class), str(source_account)
                    )
                series = input_series[skey]
                seeds, tel = _generate_for_series(sleeve, series)
                cell = {
                    **cell_base,
                    "profile_support_status": "SUPPORTED",
                    "source_status": (
                        "LOADED_OBSERVED_ROWS_WITH_EMISSIONS"
                        if seeds else "LOADED_OBSERVED_ROWS_NO_EMISSION"
                    ),
                    "evaluation_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
                    "observed_candidate_emissions": len(seeds),
                    "observed_bar_evaluations": int(tel.get("bar_evaluations", 0)),
                    "full_window_candidate_emissions": None,
                    "candidate_occurrence_completeness": (
                        "OBSERVED_SOURCE_ROWS_PARTIAL_ONLY_SCHEDULE_UNBOUND"
                    ),
                    "source_class": series.source_class,
                    "source_account": series.source_account,
                    "source_broker": series.source_broker,
                    "source_path": str(series.path),
                    "source_sha256": series.sha256,
                    "source_sidecar": str(series.sidecar),
                    "source_sidecar_sha256": series.sidecar_sha256,
                    "source_rows": len(series.times),
                    "first_true_utc": series.times[0].isoformat(),
                    "last_true_utc": series.times[-1].isoformat(),
                    "reason": None,
                    "exact_requirement": None,
                }
                source_cells.append(cell)
                generation_tel[cell_id] = {
                    **tel,
                    "source_status": cell["source_status"],
                    "source_class": series.source_class,
                    "source_broker": series.source_broker,
                    "first_true_utc": series.times[0].isoformat(),
                    "last_true_utc": series.times[-1].isoformat(),
                    "rows": len(series.times),
                }
                seeds_by_sleeve[sleeve].extend((seed, series) for seed in seeds)

        for sleeve in sleeves:
            seeds_by_sleeve[sleeve].sort(
                key=lambda pair: (
                    pair[0]["entry_utc"], pair[0]["symbol_canonical"], pair[0]["direction"]
                )
            )
            for seed, series in seeds_by_sleeve[sleeve]:
                for band in BANDS:
                    row = _score_seed(
                        seed,
                        namespace=namespace,
                        account=account,
                        server=meta["server"],
                        band=band,
                        series=series,
                        resolver=resolver,
                        runtime_cfg=runtime_cfg,
                        floor_selection=floor_selection,
                        frontier_exits=arming.frontier_exits,
                        costs=costs,
                        spread_model=spread_model,
                    )
                    namespace_rows.append(row)
                    rows_all.append(row)

        band_summaries: dict[str, Any] = {}
        for band in BANDS:
            br = [r for r in namespace_rows if r["band"] == band]
            band_summaries[band] = {
                sleeve: _sleeve_summary(
                    [r for r in br if r["sleeve"] == sleeve],
                    [
                        cell for cell in source_cells
                        if cell["namespace"] == namespace and cell["sleeve"] == sleeve
                    ],
                )
                for sleeve in sleeves
            }
            for sleeve in sleeves:
                cell_rows = [
                    row for row in source_cells
                    if row["namespace"] == namespace and row["sleeve"] == sleeve
                ]
                band_summaries[band][sleeve]["source_surface"] = {
                    "requested_current_generator_symbols": list(SURFACE[sleeve]),
                    "loaded_symbols": sorted(
                        row["symbol_canonical"] for row in cell_rows
                        if str(row["source_status"]).startswith("LOADED_")
                    ),
                    "unavailable_or_outside_profile": [
                        row for row in cell_rows
                        if not str(row["source_status"]).startswith("LOADED_")
                    ],
                    "unknown_candidate_count_on_missing_sources": any(
                        row["source_status"] == "MISSING_SOURCE" for row in cell_rows
                    ),
                    "full_window_occurrence_status": (
                        "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
                    ),
                }
        robustness = _band_robustness(band_summaries)
        namespace_cells = [
            row for row in source_cells if row["namespace"] == namespace
        ]
        namespace_missing = [
            row for row in namespace_cells if row["source_status"] == "MISSING_SOURCE"
        ]
        band_status = {
            band: {
                "evaluation_status": (
                    "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
                    if namespace_missing else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
                ),
                "headline_eligible": False,
                "missing_supported_source_cells": len(namespace_missing),
                "stream_schedule_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
                "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
            }
            for band in BANDS
        }
        namespace_scorecard = {
            sleeve: _sleeve_scorecard(
                namespace=namespace,
                account=account,
                sleeve=sleeve,
                band_summaries=band_summaries,
                source_cells=namespace_cells,
                runtime_parity=runtime_parity,
            )
            for sleeve in sleeves
        }
        scorecard_rows.extend(namespace_scorecard[sleeve] for sleeve in sleeves)
        account_summaries[namespace] = {
            "account": account,
            "profile": arming.profile,
            "evaluation_status": (
                "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
                if namespace_missing else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
            ),
            "headline_eligible": False,
            "missing_supported_source_cells": len(namespace_missing),
            "stream_schedule_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
            "source_cell_denominators": _source_cell_summary(namespace_cells),
            "armed_sleeves_from_api": list(sleeves),
            "frontier_exits_from_declaration": list(arming.frontier_exits),
            "spread_geometry_floor_from_declaration": list(arming.spread_geometry_floor),
            "bands": band_summaries,
            "band_status": band_status,
            "band_robustness": robustness,
            "sleeve_scorecard": namespace_scorecard,
            "runtime_parity": runtime_parity,
            "current_mid_band": {
                "status": (
                    "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP"
                    if namespace_missing else "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
                ),
                "location": f"accounts.{namespace}.bands.{PRIMARY_BAND}",
                "cost_input_sha256": sha256_path(COSTS_PATH),
                "spread_input_sha256": sha256_path(SPREAD_PATH),
                "authoritative_relative_to_historical_artifact": True,
                "final_post_integration_headline": False,
                "integration_state": integration_state,
            },
            "historical_published_separation_non_authoritative": _historical_published_separation(
                prior, band_summaries[PRIMARY_BAND], robustness, namespace, account
            ),
        }

    rows_all.sort(key=lambda r: (
        str(r["namespace"]), str(r["band"]), str(r.get("entry_utc")),
        str(r.get("sleeve")), str(r.get("symbol_canonical")), str(r.get("direction")),
    ))
    source_cells.sort(key=lambda row: (
        str(row["namespace"]), str(row["sleeve"]), str(row["symbol_canonical"]),
    ))
    _write_gzip_jsonl(OUT_ROWS, rows_all)
    _write_jsonl(OUT_SOURCE_CELLS, source_cells)

    input_manifest = {
        "schema": MANIFEST_SCHEMA,
        "integration_state": integration_state,
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "comparison_window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()],
        "committed_inputs": {
            str(path.relative_to(REPO)): sha256_path(path)
            for path in (
                REPO / "config/live_armed_set.json",
                REPO / "scripts/run_book_supervisor.ps1",
                REPO / "config/agent_config.yaml",
                REPO / "config/profiles/operator_profile.yaml",
                REPO / "config/profiles/redacted_account.yaml",
                COSTS_PATH,
                SPREAD_PATH,
                PRIOR_PATH,
                SURVIVOR_PATH,
                W3_CACHE,
                W5_CACHE,
                D4_LEDGER,
                REPO / "src/safety/armed_set.py",
                REPO / "src/components/ultimate_book/admission.py",
                REPO / "src/components/ultimate_book/bar_provider.py",
                REPO / "src/components/ultimate_book/book_engine.py",
                REPO / "src/components/ultimate_book/execution_packets.py",
                REPO / "src/components/ultimate_book/order_router.py",
                REPO / "src/components/ultimate_book/spread_geometry.py",
                REPO / "src/components/ultimate_book/symbol_map.py",
                REPO / "src/components/ultimate_book/sleeves/crypto.py",
                REPO / "src/components/ultimate_book/sleeves/energy_agri.py",
                REPO / "src/components/ultimate_book/sleeves/substrate.py",
                REPO / "src/components/execution.py",
                REPO / "src/components/ultimate_book/book_owner.py",
                REPO / "src/research_infra/replay_policy/generation.py",
                REPO / "src/research_infra/walkforward/exits.py",
                REPO / "src/research_infra/walkforward/quote_side.py",
                REPO / "src/costs/model.py",
                REPO / "src/costs/spread_model.py",
                REPO / "src/utils/broker_clock.py",
                HERE / "w7_current_recost.py",
                HERE / "verify_w7_current_recost.py",
            )
        },
        "external_manifest": {
            "path": str(BARS_MANIFEST),
            "sha256": sha256_path(BARS_MANIFEST),
            "canonical_sha256": canonical_json_sha(bar_manifest),
            "total_files": bar_manifest["total_files"],
            "total_rows": bar_manifest["total_rows"],
            "timestamps_basis": bar_manifest["TIMESTAMPS_ARE_BROKER_CLOCK"],
        },
        "external_series_consumed": [
            {
                "namespace": ns,
                "symbol_canonical": symbol,
                "path": str(series.path),
                "sha256": series.sha256,
                "sidecar": str(series.sidecar),
                "sidecar_sha256": series.sidecar_sha256,
                "source_account": series.source_account,
                "source_broker": series.source_broker,
                "source_class": series.source_class,
                "rows": len(series.times),
                "first_true_utc": series.times[0].isoformat(),
                "last_true_utc": series.times[-1].isoformat(),
            }
            for (ns, symbol), series in sorted(input_series.items())
        ],
        "source_cell_ledger": {
            "path": str(OUT_SOURCE_CELLS.relative_to(REPO)),
            "sha256": sha256_path(OUT_SOURCE_CELLS),
            "rows": len(source_cells),
            "status_counts": dict(sorted(collections.Counter(
                row["source_status"] for row in source_cells
            ).items())),
        },
        "source_gaps": source_gaps,
    }
    _write_json(OUT_MANIFEST, input_manifest)

    result = {
        "schema": SCHEMA,
        "status": "NOT_EVALUABLE_HIGHER_INFORMATION_STOP",
        "integration_state": integration_state,
        "headline_status": "W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP",
        "headline_eligible": False,
        "partial_diagnostic_status": (
            "RESULT_BEARING_OBSERVED_SOURCE_ROWS_ONLY_NOT_A_W7_RESULT"
        ),
        "scope": {
            "system": "W7 ultimate_book only",
            "selector_v4_decisions_measured": False,
            "scheduler_v4_decisions_measured": False,
            "broad_v4_result_inferred": False,
            "live_runtime_parity_claimed": False,
            "owner_risk_dial_or_composition_selected": False,
            "broker_or_live_state_mutated": False,
            "population": (
                "current production W7 generator emissions on observed rows from loaded cells; "
                "ten supported cells have no source and every loaded stream lacks a bound exact "
                "trading schedule, so the full-window population remains unknown"
            ),
            "entry": (
                "MODELLED fill anchor from H4 BID close plus era/hour scalar spread. No "
                "historical ASK quote/tick or resting-order lifecycle is observed; spread is "
                "embedded in geometry and is not subtracted twice from diagnostic current net"
            ),
            "gap": (
                "conservative H4 open-through fill for standing stop/breakeven-stop; "
                "targets remain at limit; intrabar ordering otherwise retains sanctioned replay"
            ),
            "cost": (
                "commission + swap on true wall holding time + slippage subtracted from "
                "quote/gap gross; spread is reported as a component and used in geometry"
            ),
            "validation_clip": (
                "both raw live-path R and the historical [-1.3,+5] validation clip are published"
            ),
            "lot_account_translation": (
                "NOT_EVALUABLE: the true path is BookOwner sizing/router -> "
                "ExecutionEngine.open_trade -> broker order_calc_profit -> volume normalization. "
                "Historical same-tick account equity/headroom, governor occupancy, fresh broker "
                "tick, symbol_info and order_calc_profit are absent. No tick-value or contract-size "
                "emulator is substituted. Per-unit-R economics remain evaluable because cost_r "
                "converts per-lot cash terms to the same risk denominator, but only as loaded-cell "
                "partial diagnostics and never as a native-graph W7 headline."
            ),
        },
        "native_flow_truth": {
            "graph": (
                "production sleeve Generator -> admission.admit_and_size -> BookOwner/"
                "UltimateBookOrderRouter risk and trade-parameter construction -> "
                "ExecutionEngine broker/order/fill/exit lifecycle"
            ),
            "overall_status": "NOT_EVALUABLE_NATIVE_GRAPH_INCOMPLETE",
            "stages": [
                {
                    "stage": "production sleeve Generator",
                    "status": (
                        "RECOMPUTED_DIRECT_GENERATOR_ON_OBSERVED_ROWS_"
                        "RUNTIME_SLOT_CONSERVATION_NOT_EVALUABLE"
                    ),
                    "evidence": (
                        "Calls the imported W7 crypto, energy/agri, and substrate production "
                        "generators on observed hash-bound, broker-clock-corrected H4 rows; "
                        "missing-cell and schedule-unbound full-window occurrence counts remain "
                        "unknown. This does not call BookEngine's wrapper, whose insufficient-bar, "
                        "stale/chronology, and generator-exception paths silently continue without "
                        "one typed terminal row per decision ordinal."
                    ),
                },
                {
                    "stage": "admission.admit_and_size",
                    "status": "NOT_EVALUABLE_HISTORICAL_STATE_MISSING",
                    "evidence": (
                        "Historical GovernorState, open risk, running conviction, occupancy, "
                        "learning/stress state, and same-cycle competing intents are absent. "
                        "The broad stack's 2.0% request -> 1.5% partial allocation does not "
                        "transfer: native _enforce_gross_open_risk_cap is first-fit-descending and "
                        "sheds/refuses a unit that does not fit remaining same-tick headroom."
                    ),
                },
                {
                    "stage": "BookOwner router/risk/trade parameters",
                    "status": "NOT_EVALUABLE_HISTORICAL_STATE_MISSING",
                    "evidence": (
                        "Historical sized units, account headroom, fresh quote geometry, ledger "
                        "occupancy, and same-symbol/cluster lifecycle state are absent."
                    ),
                },
                {
                    "stage": "broker order/fill/exit lifecycle",
                    "status": "MODELLED_H4_BID_SCALAR_SPREAD",
                    "evidence": (
                        "Research walker uses H4 BID OHLC, scalar entry spread, and conservative "
                        "open-through stops; no ASK/tick/resting-order/fill authority exists."
                    ),
                },
                {
                    "stage": "component per-unit-R costs",
                    "status": "RECOMPUTED_LOADED_CELLS_DIAGNOSTIC_ONLY",
                    "evidence": (
                        "Production cost_r recomputes commission, swap, spread, and slippage on "
                        "the modelled walker rows; lot/account translation remains unavailable."
                    ),
                },
            ],
            "execution_packet_selector_scheduler_fields": {
                "status": "COMPATIBILITY_SHIMS_NOT_SHARED_DECISIONS",
                "selector_v4_decision_measured": False,
                "scheduler_v4_decision_measured": False,
                "evidence": (
                    "execution_packets.build_book_trade_params constructs trade/schedule-shaped "
                    "telemetry after native W7 admission; this lane does not call those fields "
                    "Selector V4 or Scheduler V4 decisions."
                ),
            },
            "runtime_parity": runtime_parity_by_namespace,
            "production_wrapper_slot_conservation": {
                "status": "NOT_EVALUABLE_NO_TYPED_DECISION_ORDINAL_TERMINALS",
                "direct_generator_observed_row_reexecution_complete": True,
                "full_scheduled_or_native_wrapper_opportunity_denominator_complete": False,
                "known_silent_paths": [
                    "book_engine insufficient bars -> continue",
                    "book_engine stale/chronology exception -> continue",
                    "book_engine generator exception -> intent None -> continue",
                ],
                "exact_requirement": (
                    "Emit one typed terminal row for every active spec x on-surface symbol x "
                    "decision ordinal, then prove input-slot equals terminal conservation. Until "
                    "then all activity counts remain observed direct-generator diagnostics."
                ),
            },
        },
        "shared_repair_dependency": {
            "state": integration_state,
            "locally_duplicated_repairs": [],
            "shared_surfaces_called": [
                "src.costs.model.cost_r",
                "src.costs.spread_model.spread_price",
                "src.utils.broker_clock via replay/cost rollover",
                "src.research_infra.walkforward.quote_side.replay_anchor",
            ],
            "pending_at_pre_integration_head": [
                "price-domain slippage",
                "historical FX conversion",
                "pre-2007 broker clock",
                "observed spread accounting",
            ] if not integration_state.startswith("POST_") else [],
            "component_delta_ready": (
                "Every sleeve/account/band publishes same-row gross, commission, swap, spread, "
                "slippage and net summaries; compare pre/post manifests and component means "
                "without changing this runner."
            ),
        },
        "authority": {
            "armed_manifest_declared": raw_declaration.get("declared"),
            "armed_by_namespace_from_api": {k: list(v) for k, v in armed_by_ns.items()},
            "armed_set_reconciled": True,
        },
        "comparison_window": {
            "candidate_entry_start": WINDOW_START.isoformat(),
            "candidate_entry_end": WINDOW_END.isoformat(),
            "right_edge_bars_only_close_existing_paths": True,
        },
        "coverage_vocabulary": {
            "MEASURED": "observed on this account/instrument/source",
            "TRANSFERRED": "borrowed from a named peer source or account",
            "MODELLED": "stated current model or historical extrapolation",
            "NOT_EVALUABLE": "missing source/cost/quote authority; no numeric outcome substituted",
            "class_travels": "row net inherits the weakest of source, quote and charged components",
            "quote_lifecycle_cap": (
                "Every numeric walker row is at most MODELLED because H4 BID plus scalar "
                "entry spread is not quote/fill lifecycle measurement."
            ),
        },
        "prior_reconciliation": {
            "path": str(OUT_PRIOR.relative_to(REPO)),
            "sha256": sha256_path(OUT_PRIOR),
            "all_cache_counts_match_published": all(
                row["n_matches_published"] for row in prior["sleeves"].values()
            ),
            "any_old_identity_key_nonunique": any(
                not row["exact_rejoinable_from_cache_key"]
                for row in prior["sleeves"].values()
            ),
        },
        "inputs": {
            "manifest": str(OUT_MANIFEST.relative_to(REPO)),
            "manifest_sha256": sha256_path(OUT_MANIFEST),
            "cost_artifact": str(COSTS_PATH.relative_to(REPO)),
            "spread_artifact": str(SPREAD_PATH.relative_to(REPO)),
            "bar_archive": str(BARS_ROOT),
        },
        "generation": generation_tel,
        "source_gaps": source_gaps,
        "source_gap_counts": {
            namespace: sum(
                row["namespace"] == namespace and row["source_status"] == "MISSING_SOURCE"
                for row in source_cells
            )
            for namespace in sorted(declaration)
        },
        "source_cell_ledger": {
            "path": str(OUT_SOURCE_CELLS.relative_to(REPO)),
            "sha256": sha256_path(OUT_SOURCE_CELLS),
            "rows": len(source_cells),
            "calendar_days_inclusive": CALENDAR_DAYS,
            "status_counts": dict(sorted(collections.Counter(
                row["source_status"] for row in source_cells
            ).items())),
            "calendar_schedule_authority_status": (
                "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND"
            ),
            "calendar_denominator_claimed_unconditional": False,
            "all_missing_candidate_counts_unknown_not_zero": all(
                row["full_window_candidate_emissions"] is None
                and row["candidate_occurrence_completeness"]
                == "NOT_EVALUABLE_MISSING_SOURCE_UNKNOWN_NOT_ZERO"
                for row in source_cells if row["source_status"] == "MISSING_SOURCE"
            ),
            "all_loaded_full_window_counts_unknown": all(
                row["full_window_candidate_emissions"] is None
                and row["candidate_occurrence_completeness"]
                == "OBSERVED_SOURCE_ROWS_PARTIAL_ONLY_SCHEDULE_UNBOUND"
                for row in source_cells
                if str(row["source_status"]).startswith("LOADED_OBSERVED_ROWS_")
            ),
        },
        "accounts": account_summaries,
        "sleeve_scorecard": {
            "schema": SLEEVE_SCORECARD_SCHEMA,
            "status": "NOT_EVALUABLE_NATIVE_GRAPH_AND_SOURCE_COVERAGE",
            "headline_eligible": False,
            "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
            "allowed_recommendations": list(SCORECARD_RECOMMENDATIONS),
            "recommendation_counts": {
                recommendation: sum(
                    row["recommendation"] == recommendation
                    for row in scorecard_rows
                )
                for recommendation in SCORECARD_RECOMMENDATIONS
            },
            "rows": scorecard_rows,
            "decision_boundary": (
                "NE marks sleeves with supported missing source. RESEARCH_ONLY marks "
                "source-file-complete sleeves whose stream schedule, quote/fill lifecycle, "
                "and native admission/router/account state remain incomplete. FTMO crypto is "
                "also NE because the local empty frontier selection differs from the latest "
                "durable host observation's crypto frontier. No KEEP or REPAIR recommendation "
                "is earned by partial modelled rows, and no arming or composition decision is made."
            ),
            "arming_or_composition_change_authorized": False,
        },
        "aggregate_evaluation": {
            "evaluation_status": "NOT_EVALUABLE_SUPPORTED_SOURCE_GAP",
            "headline_eligible": False,
            "missing_supported_source_cells": sum(
                row["source_status"] == "MISSING_SOURCE" for row in source_cells
            ),
            "stream_schedule_status": "NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND",
            "numeric_scope": "OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY",
        },
        "row_ledger": {
            "path": str(OUT_ROWS.relative_to(REPO)),
            "sha256": sha256_path(OUT_ROWS),
            "rows": len(rows_all),
            "status_counts": dict(sorted(collections.Counter(r["status"] for r in rows_all).items())),
            "coverage_counts": _coverage_counts(rows_all),
        },
        "claim_boundary": (
            "These rows recompute observed-source-row W7 generator emissions and a MODELLED H4 BID/"
            "scalar-spread research walker with component per-unit-R costs. They do not traverse "
            "admit_and_size, BookOwner/router/risk, broker order/fill lifecycle, Selector V4, "
            "Scheduler V4, a shared decision surface, portfolio sizing, lot rounding, prop-account "
            "pass probability, or live activation. Local effective-registry and FTMO frontier-exit "
            "bytes diverge from the latest durable host observation; live parity is not claimed. "
            "BookEngine wrapper slots are not terminally conserved. Missing-cell and stream-schedule "
            "populations are unknown. Raw "
            "unweighted values are partial diagnostics, not a W7 profitability or composition result."
        ),
    }
    _write_json(OUT_RESULT, result)
    OUT_REPORT.write_text(_render_report(result, prior))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument(
        "--integration-state",
        choices=(
            "PRE_INTEGRATION_957_COST_QUOTE_TRUTH",
            "POST_INTEGRATION_WAVE21_COST_QUOTE_TRUTH",
        ),
        default="PRE_INTEGRATION_957_COST_QUOTE_TRUTH",
    )
    args = parser.parse_args(argv)
    doc = run(integration_state=args.integration_state)
    if args.print_summary:
        compact = {
            ns: {
                sleeve: {
                    "evaluation_status": row["evaluation_status"],
                    "n": row["n_evaluable"],
                    "coverage": row["coverage_counts"],
                    "observed_source_rows_net_clip_diagnostic": row["metrics"]
                    ["r_net_current_clip"]["mean"],
                    "observed_source_rows_net_raw_diagnostic": row["metrics"]
                    ["r_net_current_raw"]["mean"],
                }
                for sleeve, row in acc["bands"][PRIMARY_BAND].items()
            }
            for ns, acc in doc["accounts"].items()
        }
        print(json.dumps(compact, indent=2, sort_keys=True))
    print(f"wrote {OUT_RESULT.relative_to(REPO)}")
    print(f"wrote {OUT_ROWS.relative_to(REPO)}")
    print(f"wrote {OUT_SOURCE_CELLS.relative_to(REPO)}")
    print(f"wrote {OUT_PRIOR.relative_to(REPO)}")
    print(f"wrote {OUT_MANIFEST.relative_to(REPO)}")
    print(f"wrote {OUT_REPORT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
