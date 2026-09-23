#!/usr/bin/env python3
"""Session CM: re-read the armed sleeves' measured-best exit cells on the current lane.

This is an OFFLINE research driver.  It calls the production sleeve generators directly,
labels their intents with the production exit translator, applies broker-true costs and the
ratified RECORDED/B_balanced gate, and writes summaries only.  It constructs no MT5 client and
has no placement, sizing, token, supervisor, or broker-authority path.

The outcome-unread boundary is structural rather than a post-hoc filter: each CSV line's UTC
timestamp is classified before any OHLC cell is converted to a number.  Non-iterable rows are
therefore never available to generation or labelling.  A second span guard refuses candidates
whose 259-closed-bar production lookback or 80-bar maximum label path crosses a non-iterable day.

Development runs should use ``--no-ledger``.  The final run omits it and appends one unbilled
TRAIN/VAL look per sleeve/account to an ``IterationLedger``; this driver never opens TrialLedger
and never graduates a candidate.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import hashlib
import json
import statistics
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import yaml

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase17/receipts"
AU = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
BD = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AU))
sys.path.insert(0, str(BD))

import au_live_contract as LC  # noqa: E402
import bd_partial_exit as BD_EXIT  # noqa: E402

AD = LC.AD

from src.components.ultimate_book.admission import (  # noqa: E402
    CLEAN3_REGISTRY,
    SLEEVE_REGISTRY,
    winsorize_R,
)
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4  # noqa: E402
from src.components.ultimate_book.execution_packets import resolve_exit_profile  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves import (  # noqa: E402
    crypto as crypto_generator,
    energy_agri as energy_generator,
    market_expansion_d1,
    substrate as substrate_generator,
)
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.costs.spread_model import load_spread_model  # noqa: E402
from src.research_infra.training_lane import IterationLedger  # noqa: E402
from src.research_infra.trainer_partitions import DEFAULT_SURFACE_MAP  # noqa: E402
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as POP  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.utils.config import apply_profile_overrides  # noqa: E402


SCHEMA = "gtos.cm.armed_fidelity.v1"
ENGINE = "cm-production-generator-reread-v1"
MAXBARS = 80
PRODUCTION_CLOSED_BARS = 259  # engine requests 260; bar_provider drops the forming bar
POPULATION = "RECORDED"
OPTION = "B_balanced"
BANDS = ("low", "mid", "high")
MX = "mx_btcusd_d1_donchian_20_breakout"
SLEEVES = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert", MX)
ACCOUNTS = {
    "FTMO": {"profile": "operator_profile", "server": "FTMO-Server3"},
    "redacted_account": {"profile": "redacted_account", "server": "redacted_account-Server 2"},
}
FAMILY = REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CANDIDATE_FAMILY_V25.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SPREAD = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
DEFAULT_LANE = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
DEFAULT_OUT = HERE / "CM_REVERIFY_V1.json"
DEFAULT_ITERATIONS = HERE / "CM_ITERATION_LEDGER_V1.jsonl"

SLEEVE_SURFACE: dict[str, tuple[str, ...]] = {
    "crypto": tuple(SLEEVE_REGISTRY["crypto"].symbols),
    "energy_agri": tuple(SLEEVE_REGISTRY["energy_agri"].symbols),
    "sub_xvol_pullback": tuple(CLEAN3_REGISTRY["sub_xvol_pullback"].symbols),
    "sub_mid_dn_revert": tuple(CLEAN3_REGISTRY["sub_mid_dn_revert"].symbols),
    MX: ("BTCUSD",),
}
TIMEFRAME = {s: TF_H4 for s in SLEEVES}
TIMEFRAME[MX] = TF_D1
TF_NAME = {TF_H4: "H4", TF_D1: "D1"}
TF_DELTA = {TF_H4: dt.timedelta(hours=4), TF_D1: dt.timedelta(days=1)}


@dataclass(frozen=True)
class LaneSeries:
    symbol: str
    timeframe: int
    times: tuple[dt.datetime, ...]
    bars: tuple[Bar, ...]
    source_relpath: str
    sha256: str
    catalog_rows: int
    skipped: Mapping[str, int]

    @property
    def index(self) -> dict[dt.datetime, int]:
        return {stamp: i for i, stamp in enumerate(self.times)}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@lru_cache(maxsize=None)
def iterable_day(day: dt.date) -> bool:
    return bool(DEFAULT_SURFACE_MAP.surface_for_day(day).iterable)


def span_is_iterable(start: dt.datetime, end: dt.datetime) -> bool:
    """True only when every calendar day in the causal span belongs to TRAIN or VAL."""
    day = start.date()
    while day <= end.date():
        if not iterable_day(day):
            return False
        day += dt.timedelta(days=1)
    return True


def load_lane_series(lane: Path, entry: Mapping[str, Any]) -> LaneSeries:
    """Load one true-UTC bar file, classifying time before parsing any economic field.

    The SHA pass is a byte-identity check only.  During the semantic pass, a refused row may carry
    deliberately invalid OHLC text and still load successfully because those cells are never read.
    That property is pinned by ``test_cm_armed_fidelity.py``.
    """
    path = lane / str(entry["lane_relpath"])
    expected_sha = str(entry["sha256"])
    actual_sha = sha256_path(path)
    if actual_sha != expected_sha:
        raise RuntimeError(f"lane byte drift for {path}: {actual_sha} != {expected_sha}")
    if entry.get("time_column_basis") != "true_utc":
        raise RuntimeError(f"{path}: time basis is not true_utc")

    times: list[dt.datetime] = []
    bars: list[Bar] = []
    skipped: collections.Counter[str] = collections.Counter()
    with path.open("rt", encoding="utf-8", newline="") as fh:
        header = fh.readline().rstrip("\r\n").split(",")
        positions = {name: i for i, name in enumerate(header)}
        required = ("time", "open", "high", "low", "close", "volume")
        missing = [name for name in required if name not in positions]
        if missing:
            raise RuntimeError(f"{path}: missing columns {missing}")
        for line_no, line in enumerate(fh, 2):
            cells = line.rstrip("\r\n").split(",")
            stamp = dt.datetime.fromisoformat(cells[positions["time"]])
            if stamp.tzinfo is None or stamp.utcoffset() != dt.timedelta(0):
                raise RuntimeError(f"{path}:{line_no}: timestamp is not explicit UTC")
            disposition = DEFAULT_SURFACE_MAP.surface_for_day(stamp.date())
            if not disposition.iterable:
                skipped[str(disposition.refusal)] += 1
                continue  # load-bearing: no OHLC cell is touched before this branch
            times.append(stamp)
            bars.append(
                Bar(
                    float(cells[positions["open"]]),
                    float(cells[positions["high"]]),
                    float(cells[positions["low"]]),
                    float(cells[positions["close"]]),
                    float(cells[positions["volume"]]),
                )
            )
    if list(times) != sorted(times) or len(set(times)) != len(times):
        raise RuntimeError(f"{path}: timestamps are not unique ascending")
    return LaneSeries(
        symbol=str(entry["symbol"]),
        timeframe={"H4": TF_H4, "D1": TF_D1}[str(entry["timeframe"])],
        times=tuple(times),
        bars=tuple(bars),
        source_relpath=str(entry["lane_relpath"]),
        sha256=actual_sha,
        catalog_rows=int(entry["row_count"]),
        skipped=dict(skipped),
    )


def catalog_entries(lane: Path) -> tuple[dict[tuple[str, int], Mapping[str, Any]], dict]:
    catalog_path = lane / "SOURCE_CATALOG.json"
    doc = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not str(doc.get("status", "")).endswith("_VALID") or doc.get("campaign_sealed") is not False:
        raise RuntimeError("CJ lane catalog is not the declared valid, unsealed research input")
    if doc.get("march_outcomes_read") is not False:
        raise RuntimeError("CJ catalog says March outcomes were read; refusing the substrate")
    out: dict[tuple[str, int], Mapping[str, Any]] = {}
    for entry in doc.get("bar_sources", []):
        if entry.get("source_family") != "deep_universe_h4d1_2014_2026":
            continue
        tf = {"H4": TF_H4, "D1": TF_D1}.get(str(entry.get("timeframe")))
        if tf is not None:
            out[(str(entry["symbol"]), tf)] = entry
    return out, {
        "path": str(catalog_path),
        "sha256": sha256_path(catalog_path),
        "catalog_root_sha256": doc.get("catalog_root_sha256"),
        "status": doc.get("status"),
        "campaign_sealed": doc.get("campaign_sealed"),
        "economic_outcomes_read_before_cm": doc.get("economic_outcomes_read"),
        "march_outcomes_read_before_cm": doc.get("march_outcomes_read"),
    }


def load_required_series(lane: Path) -> tuple[dict[tuple[str, int], LaneSeries], dict]:
    entries, catalog = catalog_entries(lane)
    keys = {
        (symbol, TIMEFRAME[sleeve])
        for sleeve in SLEEVES
        for symbol in SLEEVE_SURFACE[sleeve]
        if (symbol, TIMEFRAME[sleeve]) in entries
    }
    series: dict[tuple[str, int], LaneSeries] = {}
    for n, key in enumerate(sorted(keys), 1):
        print(f"  load {n:02d}/{len(keys):02d} {key[0]} {TF_NAME[key[1]]}", flush=True)
        series[key] = load_lane_series(lane, entries[key])
    return series, catalog


def generator_for(sleeve: str) -> Callable[..., Any]:
    return {
        "crypto": crypto_generator.generate,
        "energy_agri": energy_generator.generate,
        "sub_xvol_pullback": substrate_generator.generate_sub_xvol_pullback,
        "sub_mid_dn_revert": substrate_generator.generate_sub_mid_dn_revert,
        MX: market_expansion_d1.generator_for(MX),
    }[sleeve]


def generate_seeds(
    sleeve: str,
    series: Mapping[tuple[str, int], LaneSeries],
) -> tuple[list[dict], dict]:
    """Drive the production generator once per source bar, retaining safe causal paths only."""
    tf = TIMEFRAME[sleeve]
    fn = generator_for(sleeve)
    out: list[dict] = []
    telemetry: collections.Counter[str] = collections.Counter()
    by_symbol: collections.Counter[str] = collections.Counter()
    seen: set[tuple] = set()
    for symbol in SLEEVE_SURFACE[sleeve]:
        source = series.get((symbol, tf))
        if source is None:
            telemetry["surface_symbol_absent"] += 1
            continue
        for i in range(PRODUCTION_CLOSED_BARS - 1, len(source.bars) - MAXBARS):
            telemetry["bar_evaluations"] += 1
            start = source.times[i - PRODUCTION_CLOSED_BARS + 1]
            end = source.times[i + MAXBARS]
            if not span_is_iterable(start, end):
                telemetry["causal_span_refused"] += 1
                continue
            history = source.bars[i - PRODUCTION_CLOSED_BARS + 1 : i + 1]
            kwargs = {"bar_time": source.times[i]}
            if sleeve == MX:
                kwargs["runtime_now"] = source.times[i] + TF_DELTA[tf]
            intent = fn(symbol, history, source.times[i].date().isoformat(), **kwargs)
            if intent is None:
                continue
            if str(intent.sleeve) != sleeve or int(intent.direction) not in (-1, 1):
                raise RuntimeError(f"production generator returned malformed intent: {intent!r}")
            key = (symbol, source.times[i].isoformat(), int(intent.direction))
            if key in seen:
                telemetry["duplicate_intent"] += 1
                continue
            seen.add(key)
            out.append(
                {
                    "sleeve": sleeve,
                    "symbol_canonical": symbol,
                    "decision_bar_iso": source.times[i].isoformat(),
                    "decision_day": str(intent.decision_day),
                    "direction": int(intent.direction),
                    "sl_distance_price": float(intent.stop_dist),
                    "target_dist": (
                        float(intent.target_dist) if intent.target_dist is not None else None
                    ),
                    "entry_price": float(source.bars[i].c),
                    "timeframe": tf,
                    "source_index": i,
                }
            )
            by_symbol[symbol] += 1
    out.sort(key=lambda r: (r["decision_bar_iso"], r["symbol_canonical"], r["direction"]))
    telemetry["candidates"] = len(out)
    return out, {**dict(telemetry), "by_symbol": dict(sorted(by_symbol.items()))}


def variants_for(sleeve: str) -> tuple[Any, Any]:
    grid = TF_NAME[TIMEFRAME[sleeve]]
    # `energy_agri` joined this list on 2026-08-11: its scale-out stopped being the committed
    # default and moved to the frontier override, so "current_live" as CM measured it -- the
    # 2R scale-out -- is now reached through the override. Pinning it here keeps this dated
    # receipt comparing the same two arms it always compared (scale-out vs plain) rather than
    # silently comparing plain against plain. See `bd_partial_exit.scale_out_profile`.
    frontier = (sleeve,) if sleeve in (MX, "energy_agri") else ()
    current = LC.variant_for_profile(
        sleeve,
        resolve_exit_profile(sleeve, frontier_exits=frontier),
        grid=grid,
        name="current_live",
    )
    if sleeve == "crypto":
        candidate = dataclasses.replace(
            current,
            name="stop_1.5x_tgtscale",
            family="stop_width",
            stop_mult=1.5,
            target_mode="scales_with_stop",
            note="AD measured-best crypto fidelity cell; target price scales with the stop",
        )
    elif sleeve == "energy_agri":
        candidate = LC.variant_for_profile(
            sleeve,
            BD_EXIT.plain_profile(sleeve),
            grid=grid,
            name="plain_exit_no_partial",
        )
    elif sleeve == "sub_xvol_pullback":
        candidate = LC.variant_for_profile(
            sleeve,
            resolve_exit_profile(sleeve, frontier_exits=(sleeve,)),
            grid=grid,
            name="target_4R",
        )
    elif sleeve == "sub_mid_dn_revert":
        candidate = dataclasses.replace(
            current,
            name="time_stop_40",
            family="time_stop",
            time_stop_bars=40,
            note="AD/AM measured-best repaired-clock horizon; target and stop unchanged",
        )
    elif sleeve == MX:
        candidate = dataclasses.replace(current, name="target_5R_reverify")
    else:  # pragma: no cover - closed tuple above
        raise KeyError(sleeve)
    return current, candidate


def label_variant(
    seeds: Sequence[dict],
    variant: Any,
    series: Mapping[tuple[str, int], LaneSeries],
    *,
    resolver: Callable[[str], str],
    server: str,
) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    exits: collections.Counter[str] = collections.Counter()
    for seed in seeds:
        tf = int(seed["timeframe"])
        source = series[(str(seed["symbol_canonical"]), tf)]
        i = int(seed["source_index"])
        stop = float(seed["sl_distance_price"]) * float(variant.stop_mult)
        native_target = seed.get("target_dist")
        if variant.target_mode == "native":
            target = native_target
        elif variant.target_mode == "scales_with_stop":
            target = native_target * float(variant.stop_mult) if native_target is not None else None
        elif variant.target_mode == "fixed_price":
            target = native_target
        elif variant.target_mode == "fixed_r":
            target = float(variant.target_r) * stop if variant.target_r is not None else None
        elif variant.target_mode == "no_target":
            target = None
        else:
            raise RuntimeError(f"unknown target mode {variant.target_mode!r}")
        policy = ExitPolicy(
            target_dist=target,
            trail_arm=(float(variant.trail_arm_r) * stop if variant.trail_arm_r else None),
            trail_gap=(float(variant.trail_gap_r) * stop if variant.trail_gap_r else None),
            maxbars=MAXBARS,
            time_stop_bars=variant.time_stop_bars,
            partial_at_r=variant.partial_at_r,
            partial_frac=variant.partial_frac,
            be_stop_after_partial=variant.be_stop_after_partial,
            trail_lag_extremes=variant.trail_lag_extremes,
            label=variant.name,
        )
        result = replay(
            source.bars,
            i,
            int(seed["direction"]),
            stop_dist=stop,
            policy=policy,
            times=source.times,
            server=server,
            bar_minutes=int(TF_DELTA[tf].total_seconds() // 60),
        )
        exit_i = int(result.exit_index)
        interval = TF_DELTA[tf]
        exits[result.exit_reason] += 1
        rows.append(
            {
                **seed,
                "symbol": resolver(str(seed["symbol_canonical"])),
                "entry_utc": (source.times[i] + interval).isoformat(),
                "exit_utc": (source.times[exit_i] + interval).isoformat(),
                "sl_distance_price": stop,
                "target_dist": target,
                "r_gross": float(winsorize_R(result.r_gross)),
                "exit_policy": variant.name,
                "exit_reason": result.exit_reason,
                "mfe_r": round(float(result.mfe_r), 6),
                "mae_r": round(float(result.mae_r), 6),
                "bars_to_mfe": int(result.bars_to_mfe),
                "exit_bar_offset": exit_i - i,
                "hold_hours": round((exit_i - i) * interval.total_seconds() / 3600.0, 4),
            }
        )
    return rows, {"n": len(rows), "exit_reasons": dict(sorted(exits.items()))}


def to_records(rows: Iterable[Mapping[str, Any]]) -> list[TradeRecord]:
    return [
        TradeRecord(
            sleeve=str(r["sleeve"]),
            symbol=str(r["symbol"]),
            entry_utc=dt.datetime.fromisoformat(str(r["entry_utc"])),
            exit_utc=dt.datetime.fromisoformat(str(r["exit_utc"])),
            direction=int(r["direction"]),
            sl_distance_price=float(r["sl_distance_price"]),
            entry_price=float(r["entry_price"]),
            r_gross=float(r["r_gross"]),
            features={
                "decision_day": r["decision_day"],
                "decision_bar_iso": r["decision_bar_iso"],
                "symbol_canonical": r["symbol_canonical"],
                "timeframe": r["timeframe"],
                "hold_hours": r["hold_hours"],
                "mfe_r": r["mfe_r"],
                "mae_r": r["mae_r"],
                "bars_to_mfe": r["bars_to_mfe"],
                "exit_reason": r["exit_reason"],
                "exit_policy": r["exit_policy"],
            },
        )
        for r in rows
    ]


def verdict_summary(sv: Any, spec: Any, mix: Mapping[str, int]) -> dict:
    stability = sv.gates.get("stability", {}) if sv is not None else {}
    sample = sv.gates.get("sample", {}) if sv is not None else {}
    fold_means = list(stability.get("fold_means") or [])
    diag = (sv.diagnostics or {}) if sv is not None else {}
    cost = diag.get("cost_decomposition") or {}
    return {
        "verdict": sv.verdict.value if sv is not None else "ABSENT",
        "n_trades": sv.n_trades if sv is not None else 0,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r if sv is not None else None,
        "fold_means": fold_means,
        "latest_evaluable_fold_mean_r": fold_means[-1] if fold_means else None,
        "n_folds_evaluable": sample.get("n_folds_evaluable"),
        "oos_positive_fold_frac": stability.get("oos_positive_fold_frac"),
        "p_raw": sv.p_raw if sv is not None else None,
        "q_value": sv.q_value if sv is not None else None,
        "failing_core_gates": (
            [
                name
                for name in ("expectancy", "lifetime", "stability", "robustness", "significance")
                if not sv.gates.get(name, {}).get("pass")
            ]
            if sv is not None
            else []
        ),
        "coverage": dict(sv.coverage or {}) if sv is not None else {},
        "mean_gross_r": cost.get("mean_gross_r"),
        "mean_cost_r": cost.get("mean_cost_r"),
        "population_mix": dict(mix),
        "spec_sha256": spec.seal(),
        "declared_family_size": spec.declared_family_size,
    }


def run_one_gate(
    sleeve: str,
    rows: Sequence[dict],
    *,
    account: str,
    server: str,
    band: str,
    allowlist: Mapping[str, Sequence[str]],
    family: Any,
    costs: Any,
    spread: Any,
    label: str,
) -> dict:
    option = OPTIONS[OPTION]
    spec = option.with_(
        spec_id=f"{option.spec_id}_cm_{sleeve}_{label}_{account.lower()}_{band}",
        account=account,
        sleeve_symbol_allowlist=dict(allowlist),
        spread_band=band,
    )
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=family)
    records, spec, mix = POP.apply(
        POPULATION,
        {sleeve: to_records(rows)},
        spec,
        account=account,
        model=spread,
        band=band,
    )
    result = run_gate(records, spec, costs=costs, server=server, diagnose=True)
    wipeout = (result.family or {}).get("wipeout") or {}
    row = verdict_summary(result.verdicts.get(sleeve), spec, mix)
    row["family_wipeout"] = dict(wipeout)
    return row


def paired_summary(current: Mapping[str, dict], candidate: Mapping[str, dict]) -> dict:
    bands: dict[str, dict] = {}
    for band in BANDS:
        cur, cand = current[band], candidate[band]
        cm, nm = cur.get("pooled_oos_mean_r"), cand.get("pooled_oos_mean_r")
        cf, nf = list(cur.get("fold_means") or []), list(cand.get("fold_means") or [])
        fold_deltas = [b - a for a, b in zip(cf, nf)] if len(cf) == len(nf) else []
        bands[band] = {
            "current_pooled_oos_mean_r": cm,
            "candidate_pooled_oos_mean_r": nm,
            "candidate_minus_current_r_per_day": (
                None if cm is None or nm is None else round(float(nm) - float(cm), 9)
            ),
            "fold_deltas": [round(x, 9) for x in fold_deltas],
            "latest_fold_delta": round(fold_deltas[-1], 9) if fold_deltas else None,
            "positive_fold_delta_frac": (
                sum(x > 0 for x in fold_deltas) / len(fold_deltas) if fold_deltas else None
            ),
        }
    return bands


def arm_rule(sleeve: str, current: Mapping[str, dict], candidate: Mapping[str, dict]) -> dict:
    """Apply the committed CM look declaration literally, without inspecting other cells."""
    paired = paired_summary(current, candidate)
    mid = candidate["mid"]
    reasons: list[str] = []
    if int(mid.get("n_trades") or 0) < 30:
        reasons.append("candidate_has_fewer_than_30_RECORDED_trades")
    if int(mid.get("n_folds_evaluable") or 0) < 3:
        reasons.append("candidate_has_fewer_than_3_evaluable_folds")
    for band in BANDS:
        p = paired[band]
        if p["candidate_minus_current_r_per_day"] is None or p["candidate_minus_current_r_per_day"] <= 0:
            reasons.append(f"{band}_pooled_delta_not_positive")
        if p["latest_fold_delta"] is None or p["latest_fold_delta"] <= 0:
            reasons.append(f"{band}_latest_fold_delta_not_positive")
        frac = p["positive_fold_delta_frac"]
        if frac is None or frac < 0.60:
            reasons.append(f"{band}_positive_fold_delta_frac_below_0p60")
    if sleeve == "energy_agri" and int(mid.get("n_trades") or 0) <= 67:
        reasons.append("energy_extension_does_not_exceed_AD_n67")
    if sleeve == MX:
        reasons.append("already_armed_identity_control_not_a_new_ceremony_delta")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "paired": paired,
        "rule": {
            "sample": "candidate RECORDED n>=30 and >=3 evaluable folds",
            "direction": "candidate-current >0 pooled and latest fold in low/mid/high",
            "stability": ">=60% of paired fold deltas positive in low/mid/high",
            "energy_extension": "RECORDED candidate n>67",
            "carrier": "existing per-sleeve --frontier-exits override",
        },
    }


def identity_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    keys = sorted(
        (str(r["symbol_canonical"]), str(r["decision_bar_iso"]), int(r["direction"]))
        for r in rows
    )
    return hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest()


def config_context() -> dict[str, dict]:
    base = yaml.safe_load((REPO / "config/agent_config.yaml").read_text(encoding="utf-8")) or {}
    out: dict[str, dict] = {}
    for account, meta in ACCOUNTS.items():
        merged = apply_profile_overrides(base, str(meta["profile"]))
        resolver = build_broker_symbol_resolver(merged)
        out[account] = {"config": merged, "resolver": resolver, **meta}
    return out


def _surface_account_summary(
    sleeve: str,
    available: set[str],
    resolver: Callable[[str], str],
) -> dict:
    expected = [s for s in SLEEVE_SURFACE[sleeve] if resolver.supports(s)]
    measured = [s for s in expected if s in available]
    return {
        "broker_supported_canonical": expected,
        "measured_canonical": measured,
        "missing_from_lane": [s for s in expected if s not in available],
        "measured_surface_fraction": len(measured) / len(expected) if expected else 0.0,
        "broker_symbols_measured": [resolver(s) for s in measured],
    }


def _ledger_verdict(rule: Mapping[str, Any]) -> str:
    if rule.get("eligible"):
        return "improved"
    deltas = [
        b.get("candidate_minus_current_r_per_day")
        for b in (rule.get("paired") or {}).values()
        if b.get("candidate_minus_current_r_per_day") is not None
    ]
    if deltas and all(abs(float(x)) <= 1e-12 for x in deltas):
        return "no_change"
    if deltas and statistics.fmean(float(x) for x in deltas) < 0:
        return "regressed"
    return "evaluated"


def run(args: argparse.Namespace) -> dict:
    started = time.time()
    lane = Path(args.lane_root).resolve()
    print("loading true-UTC lane (timestamps are classified before OHLC)", flush=True)
    series, catalog = load_required_series(lane)
    available = {symbol for symbol, _tf in series}
    configs = config_context()
    family = CF.load_candidate_family(FAMILY)
    costs = load_broker_true_costs(COSTS)
    spread = load_spread_model(SPREAD)

    seeds_by_sleeve: dict[str, list[dict]] = {}
    generation: dict[str, dict] = {}
    for sleeve in SLEEVES:
        t0 = time.time()
        print(f"generate {sleeve} through production generator", flush=True)
        seeds, telemetry = generate_seeds(sleeve, series)
        seeds_by_sleeve[sleeve] = seeds
        generation[sleeve] = {**telemetry, "seconds": round(time.time() - t0, 2)}
        print(f"  {sleeve}: {len(seeds)} safe intents", flush=True)

    accounts: dict[str, dict] = {}
    iteration_rows: list[dict] = []
    for account, context in configs.items():
        resolver = context["resolver"]
        server = str(context["server"])
        accounts[account] = {}
        for sleeve in SLEEVES:
            coverage = _surface_account_summary(sleeve, available, resolver)
            measured = set(coverage["measured_canonical"])
            seeds = [r for r in seeds_by_sleeve[sleeve] if r["symbol_canonical"] in measured]
            current_variant, candidate_variant = variants_for(sleeve)
            current_rows, current_tel = label_variant(
                seeds, current_variant, series, resolver=resolver, server=server
            )
            candidate_rows, candidate_tel = label_variant(
                seeds, candidate_variant, series, resolver=resolver, server=server
            )
            cur_keys = identity_digest(current_rows)
            cand_keys = identity_digest(candidate_rows)
            if cur_keys != cand_keys or len(current_rows) != len(candidate_rows):
                raise RuntimeError(f"{account}/{sleeve}: exit cell changed trade identity")
            allowlist = {
                sleeve: tuple(resolver(s) for s in coverage["broker_supported_canonical"])
            }
            gated = {"current": {}, "candidate": {}}
            for band in BANDS:
                print(f"gate {account:10s} {sleeve:42s} {band}", flush=True)
                gated["current"][band] = run_one_gate(
                    sleeve,
                    current_rows,
                    account=account,
                    server=server,
                    band=band,
                    allowlist=allowlist,
                    family=family,
                    costs=costs,
                    spread=spread,
                    label="current",
                )
                gated["candidate"][band] = run_one_gate(
                    sleeve,
                    candidate_rows,
                    account=account,
                    server=server,
                    band=band,
                    allowlist=allowlist,
                    family=family,
                    costs=costs,
                    spread=spread,
                    label="candidate",
                )
            rule = arm_rule(sleeve, gated["current"], gated["candidate"])
            accounts[account][sleeve] = {
                "evidence_class": "fidelity",
                "surface": coverage,
                "trade_identity": {
                    "current_n": len(current_rows),
                    "candidate_n": len(candidate_rows),
                    "same_identity": True,
                    "key_digest_sha256": cur_keys,
                },
                "current_variant": current_variant.as_dict(),
                "candidate_variant": candidate_variant.as_dict(),
                "current_label_telemetry": current_tel,
                "candidate_label_telemetry": candidate_tel,
                "gate": gated,
                "arm_rule": rule,
            }
            days = sorted({str(r["decision_bar_iso"])[:10] for r in seeds})
            iteration_rows.append(
                {
                    "account": account,
                    "sleeve": sleeve,
                    "days": days,
                    "verdict": _ledger_verdict(rule),
                    "metric": rule["paired"]["mid"]["candidate_minus_current_r_per_day"],
                    "spec": {
                        "current": current_variant.as_dict(),
                        "candidate": candidate_variant.as_dict(),
                        "population": POPULATION,
                        "option": OPTION,
                        "bands": list(BANDS),
                        "family": "CANDIDATE_BOOK_V1@V25",
                        "declaration": "phase17/receipts/CM_LOOK_DECLARATION_V1.json",
                    },
                }
            )

    selected = {
        account: [s for s, row in sleeves.items() if row["arm_rule"]["eligible"]]
        for account, sleeves in accounts.items()
    }
    source_rows = {
        f"{symbol}:{TF_NAME[tf]}": {
            "source_relpath": item.source_relpath,
            "sha256": item.sha256,
            "catalog_rows": item.catalog_rows,
            "semantic_rows_loaded": len(item.bars),
            "skipped_before_OHLC_parse": dict(item.skipped),
        }
        for (symbol, tf), item in sorted(series.items())
    }
    doc = {
        "schema": SCHEMA,
        "session": "CM",
        "blocks": "B2700-B2749",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "elapsed_seconds": round(time.time() - started, 2),
        "boundary": {
            "offline_only": True,
            "production_generator_called_directly": True,
            "mt5_client_constructed": False,
            "broker_or_vps_contact": False,
            "config_bytes_written": False,
            "trial_ledger_opened": False,
            "graduation_run": False,
            "march_outcomes_read": False,
            "test_surface_consumed": False,
            "semantic_loader_rule": "timestamp classified before OHLC conversion",
            "causal_span_rule": "259 closed-bar lookback plus 80-bar max path all TRAIN/VAL",
        },
        "protocol": {
            "declaration": "phase17/receipts/CM_LOOK_DECLARATION_V1.json",
            "population": POPULATION,
            "option": OPTION,
            "bands": list(BANDS),
            "family": "CANDIDATE_BOOK_V1 via CANDIDATE_FAMILY_V25",
            "look_type": "unbilled carry; no new grid; no DSR ratchet",
            "used_once_disclosure": (
                "VAL 2025-01-01..2026-05-31 is already consumed and is used once here; "
                "figures are selection evidence, not TEST confirmation."
            ),
        },
        "catalog": catalog,
        "source_rows": source_rows,
        "generation": generation,
        "accounts": accounts,
        "selected_for_ceremony": selected,
        "energy_extension": {
            account: {
                "safe_generated_n": accounts[account]["energy_agri"]["trade_identity"]["candidate_n"],
                "exceeds_AD_n67": (
                    accounts[account]["energy_agri"]["trade_identity"]["candidate_n"] > 67
                ),
                "eligible": accounts[account]["energy_agri"]["arm_rule"]["eligible"],
                "missing_lane_symbols": accounts[account]["energy_agri"]["surface"]["missing_from_lane"],
            }
            for account in accounts
        },
    }
    Path(args.output).write_text(json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8")

    if not args.no_ledger:
        ledger = IterationLedger(
            Path(args.ledger), session="CM", run_id=f"CM-{doc['generated_utc'][:19]}"
        )
        for row in iteration_rows:
            if not row["days"]:
                continue
            ledger.record(
                mechanism="armed_exit_fidelity_reread",
                sleeve=f"{row['account']}::{row['sleeve']}",
                spec=row["spec"],
                engine_version=ENGINE,
                days=row["days"],
                verdict=row["verdict"],
                metric=row["metric"],
                metric_name="candidate_minus_current_mid_R_per_day",
                note=(
                    "Unbilled existing-cell carry under CM_LOOK_DECLARATION_V1; VAL is used-once; "
                    "no TEST, no graduation, no trial-family ratchet."
                ),
                receipt=str(Path(args.output).resolve().relative_to(REPO)),
                extra={"account": row["account"], "bands": list(BANDS)},
            )
        doc["iteration_ledger"] = {
            "path": str(Path(args.ledger).resolve().relative_to(REPO)),
            "rows_written": ledger.n_written,
            "billed": False,
        }
        Path(args.output).write_text(json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {Path(args.output)}")
    print("selected: " + json.dumps(selected, sort_keys=True))
    return doc


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-root", default=str(DEFAULT_LANE))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--ledger", default=str(DEFAULT_ITERATIONS))
    parser.add_argument("--no-ledger", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    run(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
