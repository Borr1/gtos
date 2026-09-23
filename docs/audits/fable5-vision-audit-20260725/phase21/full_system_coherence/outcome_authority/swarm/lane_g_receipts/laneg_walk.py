#!/usr/bin/env python3
"""LANE G independent walk.

Three arms on the identical sealed candidate population and the identical frozen
loader/labeler that Phase 0 used:

  ORIG   — the original contract (control; must reproduce the sealed cache).
  MIRROR — SAME entry instant, SAME risk distance, SAME 2.0 RR, direction FLIPPED
           and the barriers mirrored about the entry (stop 1R against, target 2R
           with, in the new direction). This is the assumption-free benchmark for
           "do these entries carry directional information?": it needs no driftless
           model, no volatility estimate, and no horizon correction, because it is
           the same paths, same geometry, same horizon, same spreads.
  INV    — Phase 0's inverted contract (flip direction, keep the price levels), so
           this run also independently reproduces Phase 0's headline arm.

Also records, per row, the quantities the benchmark argument needs:
  * the fill-bar spread in price (exactly |fill_long - fill_short| for MARKET), and
  * the raw sealed geometry (risk_reward_ratio field, and the measured
    |T-E|/|E-S| ratio) so the RR=2.0 correction can be verified at scale.
"""
from __future__ import annotations

import bisect
import datetime as dt
import gzip
import importlib.util
import json
import os
import pickle
import sys
import time
from pathlib import Path

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
OUT = Path("/private/tmp/laneG-walk")
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(WT))
sys.path.insert(0, str(OA))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r3 = load_module("w21_score_aprmay_r3b_frozen", OA / "w21_score_aprmay_r3b.py")
s2 = r3.s2
r = r3.r
m = r.m  # candidate_funnel_analysis

from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.walkforward.quote_side import (
    BarQuote,
    resolve_post_submission_m1_lifecycle,
)

MARKET_FAMILIES = (
    "structural_distance_extreme",
    "liquidity_sweep_reclaim",
    "cross_asset_lead_lag",
    "displacement_continuation",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)

PREREG = json.loads((OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json").read_text())
_TR = PREREG["training"]
_VAL = {w["window_id"]: w for w in PREREG["validation"]["windows"]}
WINDOWS = {
    "feb": ("february_2026", Path("/private/tmp/w21-market-top-feb-r2"),
            _TR["february_manifest_root_sha256"], _TR["february_days"]),
    "apr": ("april_2026", Path("/private/tmp/w21-market-top-aprmay-r3"),
            _TR["april_manifest_root_sha256"], _TR["april_days"]),
    "may": ("may_2026", Path("/private/tmp/w21-market-top-aprmay-r3"),
            _TR["may_manifest_root_sha256"], _TR["may_days"]),
    "jun": ("june_2026", Path("/private/tmp/w21-market-top-junjul-r4"),
            _VAL["june_2026"]["manifest_root_sha256"], _VAL["june_2026"]["days"]),
    "jul": ("july_2026", Path("/private/tmp/w21-market-top-junjul-r4"),
            _VAL["july_2026"]["manifest_root_sha256"], _VAL["july_2026"]["days"]),
}

T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def raw_rows_for(root: Path, day: str):
    summary = json.loads((root / day / "run_summary.json").read_text(encoding="utf-8"))
    sink = ReplayCompactEventSink.open_sealed(
        root=root / day / "compact_events",
        expected_authority_root_sha256=summary["authority_root_sha256"],
    )
    return list(sink.ledger("missed"))


def _resolve(raw, sources, *, direction, stop, target, risk):
    symbol = str(raw["symbol"])
    source, times, bars, spreads = sources[symbol]
    submission = m._utc(str(raw["decision_time_utc"]))
    expiry = m._utc(str(raw["limit_first_expiry_utc"]))
    start = max(0, bisect.bisect_right(times, submission) - 1)
    end = min(len(times), bisect.bisect_left(times, expiry) + 1)
    return resolve_post_submission_m1_lifecycle(
        bars[start:end],
        m1_open_times_utc=times[start:end],
        direction=direction,
        proposed_order_type=m._order_type(raw),
        submission_or_ack_time_utc=submission,
        expiry_utc=expiry,
        required_horizon_utc=expiry,
        approved_entry_price=float(raw["entry_price"]),
        approved_stop_price=stop,
        approved_target_price=target,
        approved_risk_distance=risk,
        m1_price_basis=BarQuote.BID,
        spread_by_bar=spreads[start:end],
        source_interval_verified=True,
        symbol_spec_hash_sha256=m.SPEC_SHA256,
        spread_source_hash_sha256=m.SPREAD_SHA256,
    )


def candidate_record(raw, sources):
    symbol = str(raw["symbol"])
    source, times, bars, spreads = sources[symbol]
    entry = float(raw["entry_price"])
    stop = float(raw["stop_loss"])
    target = float(raw["take_profit_1"])
    risk = abs(entry - stop)
    reward = abs(target - entry)
    d = 1 if str(raw["side"]).upper() == "LONG" else -1
    deductible = sum(
        float(raw.get(field) or 0.0)
        for field in ("expected_slippage_r", "swap_cost_r", "commission_r")
    )
    submission = m._utc(str(raw["decision_time_utc"]))
    expiry = m._utc(str(raw["limit_first_expiry_utc"]))

    arms = {}
    arms["orig"] = (_resolve(raw, sources, direction=d, stop=stop, target=target, risk=risk), risk, d)
    # MIRROR: flip direction, mirror the barriers about the entry -> same 1R stop, same 2R target
    arms["mirror"] = (
        _resolve(raw, sources, direction=-d, stop=entry + d * risk,
                 target=entry - d * reward, risk=risk),
        risk, -d,
    )
    # INV: Phase 0's inverted contract -- flip direction, keep the price levels
    arms["inv"] = (_resolve(raw, sources, direction=-d, stop=target, target=stop, risk=reward),
                   reward, -d)

    def pack(res, risk_unit):
        status = res.lifecycle_label_status
        gross = float(res.terminal_gross_r) if status.startswith("RESOLVED_FILLED_") else None
        ded = deductible * (risk / risk_unit) if risk_unit > 0 else None
        return {
            "status": status,
            "state": res.terminal_state,
            "gross": gross,
            "net": None if gross is None else gross - ded,
            "fill_price": res.modelled_fill_price,
            "fill_time": res.modelled_fill_time_utc,
            "terminal_time": res.terminal_time_utc,
        }

    out = {name: pack(res, unit) for name, (res, unit, _dd) in arms.items()}

    # fill-bar spread in price: the MARKET fill is the successor bar open on the
    # executable ENTRY side, so a LONG fill and a SHORT fill at the same instant
    # differ by exactly one spread.
    fo, fm = out["orig"]["fill_price"], out["mirror"]["fill_price"]
    spread_at_fill = (
        abs(float(fo) - float(fm))
        if (fo is not None and fm is not None and out["orig"]["fill_time"] == out["mirror"]["fill_time"])
        else None
    )

    horizon_min = (expiry - submission).total_seconds() / 60.0

    def bars_held(a):
        ft, tt = out[a]["fill_time"], out[a]["terminal_time"]
        if ft is None or tt is None:
            return None
        return (m._utc(str(tt)) - m._utc(str(ft))).total_seconds() / 60.0

    return {
        "key": str(raw["canonical_replay_candidate_instance_key"]),
        "day": str(raw["trading_day"]),
        "symbol": symbol,
        "family": str(raw["origin_family"]),
        "side": str(raw["side"]).upper(),
        "window": str(raw["decision_window_id"]),
        "decision_utc": str(raw["decision_time_utc"]),
        "order_type": m._order_type(raw),
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "risk_price": risk,
        "reward_price": reward,
        "rr_measured": (reward / risk) if risk > 0 else None,
        "rr_field": raw.get("risk_reward_ratio"),
        "policy_target_r": raw.get("policy_target_r"),
        "raw_target_r": raw.get("raw_target_r"),
        "geometry_policy": raw.get("dynamic_geometry_policy"),
        "spread_r_row": float(raw.get("spread_r") or 0.0),
        "spread_at_fill_price": spread_at_fill,
        "slippage_r": float(raw.get("expected_slippage_r") or 0.0),
        "commission_r": float(raw.get("commission_r") or 0.0),
        "swap_r": float(raw.get("swap_cost_r") or 0.0),
        "cost_r": float(raw.get("cost_r") or 0.0),
        "horizon_min": horizon_min,
        "orig": out["orig"], "mirror": out["mirror"], "inv": out["inv"],
        "minutes_held_orig": bars_held("orig"),
        "minutes_held_mirror": bars_held("mirror"),
    }


def run_month(month: str):
    window_id, root, expected_root, days = WINDOWS[month]
    root_sha, sources = r3.load_m1_sources(MANIFEST_DIR / f"{window_id}.json", expected_root)
    log(stage="m1_loaded", month=month, symbols=len(sources))
    records = []
    for day in days:
        raws = raw_rows_for(root, day)
        n = 0
        for raw in raws:
            if str(raw["origin_family"]) not in MARKET_FAMILIES:
                continue
            records.append(candidate_record(raw, sources))
            n += 1
        log(stage="day", month=month, day=day, kept=n, total=len(raws))
    del sources
    return records


def main():
    months = sys.argv[1].split(",") if len(sys.argv) > 1 else list(WINDOWS)
    for month in months:
        records = run_month(month)
        path = OUT / f"lg_{month}.pkl.gz"
        with gzip.open(path, "wb") as fh:
            pickle.dump(records, fh, protocol=5)
        log(stage="month_written", month=month, n=len(records), path=str(path))
    log(stage="ALL_DONE")


if __name__ == "__main__":
    main()
