#!/usr/bin/env python3
"""B1 — the LIMIT-arm price-bearing export.

WHY THIS EXISTS
---------------
`/private/tmp/laneG-walk/lg_{month}.pkl.gz` — the only price-bearing artifact the swarm has — is
100 % MARKET. The cause is a single explicit filter in its generator:

    /private/tmp/laneG/laneg_walk.py:236
        if str(raw["origin_family"]) not in MARKET_FAMILIES:
            continue

with MARKET_FAMILIES declared at `laneg_walk.py:64-72` (the seven MARKET origin families).
It is NOT a schema gap and NOT an unrun branch: the engine resolves LIMIT natively
(`src/research_infra/walkforward/quote_side.py:1058-1062`, `:1270-1340`, `:512-514`), and
`candidate_funnel_analysis.py:81` maps the other three families to LIMIT deterministically.
Lane G filtered them out because its MIRROR arm's spread trick (`laneg_walk.py:180-185`) is
MARKET-only — a resting LIMIT and its mirror fill at their own levels, not one spread apart.

So the LIMIT rows were never walked, and 49.4 % of the resolved population has no tick-derived
slippage. This script walks them, through the same engine entrypoint, in the same code tree.

COMPARABILITY
-------------
Imports resolve against the SAME worktree Lane G used
(/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809) so the engine bytes are
identical to the ones that produced lg_*.pkl.gz. `--arm market` re-walks the MARKET rows and is
the export-fidelity control: its `orig` output must match lg_{jun,jul}.pkl.gz row for row.

Only the `orig` arm is resolved (Lane G also walked `mirror` and `inv`, which nothing downstream of
the slippage measurement reads). `spread_at_fill_price` is therefore not reconstructed; the true
tick spread is measured directly from the tape in b1_slip.py, which is better than the modelled one.

Read-only. No live path, no broker call, no config byte, no src/ edit, no git write.
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import importlib.util
import json
import pickle
import sys
import time
from pathlib import Path

# --- the code tree Lane G walked in; keep identical for byte-comparable engine behaviour ---
WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"

# sealed generation roots: /private/tmp copies were reaped; these are the held originals
ROOTS = {
    "jun": Path("/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-junjul-r4-roots-20260812"),
    "jul": Path("/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-junjul-r4-roots-20260812"),
    "apr": Path("/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-aprmay-r3-roots-20260811"),
    "may": Path("/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-aprmay-r3-roots-20260811"),
}
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b1")
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(WT))
sys.path.insert(0, str(OA))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r3 = load_module("w21_score_aprmay_r3b_frozen", OA / "w21_score_aprmay_r3b.py")
r = r3.r
m = r.m  # candidate_funnel_analysis

from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    resolve_post_submission_m1_lifecycle,
)

# the three LIMIT families, verbatim from candidate_funnel_analysis.py:49-51
LIMIT_FAMILIES = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
# the seven MARKET families, verbatim from laneg_walk.py:64-72
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
    "apr": ("april_2026", _TR["april_manifest_root_sha256"], _TR["april_days"]),
    "may": ("may_2026", _TR["may_manifest_root_sha256"], _TR["may_days"]),
    "jun": ("june_2026", _VAL["june_2026"]["manifest_root_sha256"], _VAL["june_2026"]["days"]),
    "jul": ("july_2026", _VAL["july_2026"]["manifest_root_sha256"], _VAL["july_2026"]["days"]),
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


def resolve_orig(raw, sources, *, direction, stop, target, risk):
    """Identical call shape to laneg_walk.py:106-130 (_resolve), orig arm only."""
    symbol = str(raw["symbol"])
    _source, times, bars, spreads = sources[symbol]
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

    res = resolve_orig(raw, sources, direction=d, stop=stop, target=target, risk=risk)
    status = res.lifecycle_label_status
    gross = float(res.terminal_gross_r) if status.startswith("RESOLVED_FILLED_") else None
    orig = {
        "status": status,
        "state": res.terminal_state,
        "gross": gross,
        "net": None if gross is None else gross - deductible,
        "fill_price": res.modelled_fill_price,
        "fill_time": res.modelled_fill_time_utc,
        "terminal_time": res.terminal_time_utc,
    }
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
        "spread_r_row": float(raw.get("spread_r") or 0.0),
        "slippage_r": float(raw.get("expected_slippage_r") or 0.0),
        "commission_r": float(raw.get("commission_r") or 0.0),
        "swap_r": float(raw.get("swap_cost_r") or 0.0),
        "cost_r": float(raw.get("cost_r") or 0.0),
        "horizon_min": (expiry - submission).total_seconds() / 60.0,
        "orig": orig,
    }


def run_month(month: str, families: tuple[str, ...]):
    window_id, expected_root, days = WINDOWS[month]
    root = ROOTS[month]
    root_sha, sources = r3.load_m1_sources(MANIFEST_DIR / f"{window_id}.json", expected_root)
    log(stage="m1_loaded", month=month, symbols=len(sources), root_sha=root_sha[:12])
    records = []
    for day in days:
        raws = raw_rows_for(root, day)
        n = 0
        for raw in raws:
            if str(raw["origin_family"]) not in families:
                continue
            records.append(candidate_record(raw, sources))
            n += 1
        log(stage="day", month=month, day=day, kept=n, total=len(raws))
    del sources
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["limit", "market"], required=True)
    ap.add_argument("--months", default="jun,jul")
    args = ap.parse_args()
    families = LIMIT_FAMILIES if args.arm == "limit" else MARKET_FAMILIES
    log(stage="start", arm=args.arm, families=list(families), months=args.months)
    for month in args.months.split(","):
        records = run_month(month, families)
        path = OUT / f"b1_{args.arm}_{month}.pkl.gz"
        with gzip.open(path, "wb") as fh:
            pickle.dump(records, fh, protocol=5)
        log(stage="month_written", month=month, n=len(records), path=str(path))
    log(stage="ALL_DONE", arm=args.arm)


if __name__ == "__main__":
    main()
