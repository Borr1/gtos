"""m3-1 — the gate substrate, re-walked on the corrected quote convention.

    python3 .../m3/m3_substrate.py

WHAT THIS BUILDS
----------------
The exact substrate `an_population_rule.py` gates — AA's 32 sleeves plus the three
candidate cells' own exit variants — in FOUR arms:

    old              AA's own labelling, re-derived from the bars (not copied)
    qs_low/mid/high  the same rows walked with `entry_price = close + direction * spread`

Everything downstream (the gate, the folds, the BH step-up) then reads one of these four
and nothing else changes, so any verdict move is attributable to the walker alone.

THE CONTROL THAT MAKES THE `old` ARM AN ARM AND NOT A COPY
-----------------------------------------------------------
`old` is re-walked from `vps-bars-20260727` with the sleeve's own exit policy and must
reproduce the published `r_gross` to the bit on all 22,324 AA rows and all 533 AM rows.
If it does not, the delta is about some other program and this file refuses to write.
The same standard is applied to the three resimulated candidate cells against
`ad_exit_sweep.resimulate`, which is the function AN itself calls.

WHY THE THREE CANDIDATE CELLS GO THROUGH A LOCAL COPY OF `resimulate`
---------------------------------------------------------------------
`AD.resimulate` has no `entry_price` hook. Rather than patch a wave-7 receipt, the loop is
reproduced here with the single substitution, and CONTROL C0 asserts that with the
correction disabled it reproduces `AD.resimulate` field-for-field on every row of every
cell. A re-derivation is worth what its parity proves.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    replay_anchor,
    spread_for,
)

HERE = Path(__file__).resolve().parent
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P9 = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"
AA_IN = P6 / "AA_ESTATE_TRADES.json.gz"
AM_SUBMID = P9 / "AM_SUBMID_TRADES.json.gz"
OUT = HERE / "M3_SUBSTRATE_V1.json.gz"
CTL = HERE / "M3_SUBSTRATE_CONTROLS_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
SUBMID = "sub_mid_dn_revert"
ACCOUNT = "FTMO"
BANDS = ("low", "mid", "high")
ARMS = ("old",) + tuple(f"qs_{b}" for b in BANDS)

#: The three candidate exit cells AN carries, verbatim from `an_population_rule.py:118-129`.
VARIANTS = {
    (BTC, "target_4R"): AD.Variant(name="target_4R", family="target",
                                   target_mode="fixed_r", target_r=4.0),
    (BTC, "target_5R"): AD.Variant(name="target_5R", family="target",
                                   target_mode="fixed_r", target_r=5.0),
    (XVOL, "target_4R"): AD.Variant(name="target_4R", family="target",
                                    target_mode="fixed_r", target_r=4.0),
}


# =====================================================================================
# the one substitution
# =====================================================================================

def anchor_for(symbol: str, entry_utc: dt.datetime, close: float, direction: int,
               band: str | None) -> float | None:
    """`close + direction * spread`, or None when the model refuses to price the instant.

    `band=None` is the identity — it returns None so the caller passes `entry_price=None`
    and `replay` reproduces `bars[i].c` byte-for-byte (`exits.py:333`).
    """
    if band is None:
        return None
    s = spread_for(symbol, entry_utc, account=ACCOUNT, band=band)   # raises SpreadUnavailable
    return replay_anchor(close, direction, s, BarQuote.BID)


def _trail(sleeve: str):
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") != "trailing_runner":
        return None, None
    return prof.get("trigger_r"), prof.get("trail_gap_r")


# =====================================================================================
# arm 1 — the 32 base sleeves, at AA's own labelling
# =====================================================================================

def rewalk_base(rows: list[dict], sleeve: str, series, index, band: str | None):
    """AA's recipe (`aa_estate_generate.py:260-274`), one row at a time."""
    trig_r, gap_r = _trail(sleeve)
    out, skips = [], collections.Counter()
    for r in rows:
        tf = int(r["timeframe"])
        key = (r["symbol"], tf)
        if key not in index:
            skips["no_series"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            skips["bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            skips["no_room"] += 1
            continue
        sd = float(r["sl_distance_price"])
        td = r.get("target_dist")
        if trig_r is not None and gap_r is not None:
            pol = ExitPolicy(target_dist=(float(td) if td else None),
                             trail_arm=float(trig_r) * sd, trail_gap=float(gap_r) * sd,
                             maxbars=AD.MAXBARS, label="trailing_runner")
        else:
            pol = ExitPolicy(target_dist=(float(td) if td else None), maxbars=AD.MAXBARS,
                             label="plain")
        ivl = dt.timedelta(minutes=AD.TF_MINUTES[tf])
        at = times[i] + ivl
        try:
            ap = anchor_for(r["symbol"], at, bars[i].c, int(r["direction"]), band)
        except SpreadUnavailable:
            skips["no_spread"] += 1
            continue
        pr = replay(bars, i, int(r["direction"]), stop_dist=sd, policy=pol,
                    entry_price=ap)
        xi = pr.exit_index
        out.append({
            **r,
            "entry_utc": at.isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "entry_price": (float(ap) if ap is not None else float(r["entry_price"])),
            "r_gross": float(winsorize_R(pr.r_gross)),
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * AD.TF_MINUTES[tf] / 60.0, 4),
        })
    return out, dict(skips)


# =====================================================================================
# arm 2 — the candidate exit cells, `AD.resimulate` with the one substitution
# =====================================================================================

def resimulate_qs(rows, variant, series, index, costs, rule, band: str | None):
    """`ad_exit_sweep.resimulate` verbatim plus `entry_price`. C0 pins the parity."""
    out, tel = [], collections.Counter()
    for r in rows:
        tf = int(r["timeframe"])
        key = (r["symbol"], tf)
        if key not in index:
            tel["skip_no_series"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            tel["skip_bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            tel["skip_no_room"] += 1
            continue

        stop = float(r["sl_distance_price"]) * variant.stop_mult
        native_target = r.get("target_dist")
        mode = variant.target_mode
        if mode == "native":
            target = native_target
        elif mode == "scales_with_stop":
            target = (native_target * variant.stop_mult) if native_target else None
        elif mode == "fixed_price":
            target = native_target
        elif mode == "fixed_r":
            target = (variant.target_r * stop) if variant.target_r else None
        elif mode == "no_target":
            target = None
        else:
            raise ValueError(f"unknown target_mode {mode!r}")

        pol = ExitPolicy(
            target_dist=target,
            trail_arm=(variant.trail_arm_r * stop) if variant.trail_arm_r else None,
            trail_gap=(variant.trail_gap_r * stop) if variant.trail_gap_r else None,
            maxbars=AD.MAXBARS,
            time_stop_bars=variant.time_stop_bars,
            flat_before_rollover_local_hour=variant.flat_hour,
            partial_at_r=variant.partial_at_r,
            partial_frac=variant.partial_frac,
            be_stop_after_partial=variant.be_stop_after_partial,
            trail_lag_extremes=variant.trail_lag_extremes,
            label=variant.name,
        )
        flat_utc = None
        if variant.flat_rule:
            entry_utc = times[i] + dt.timedelta(minutes=AD.TF_MINUTES[tf])
            wd = (AD.swap3_weekday(costs, r["symbol"], ACCOUNT)
                  if variant.flat_rule == "triple_swap_only" else None)
            if variant.flat_rule == "triple_swap_only" and wd is None:
                tel["skip_no_swap3_weekday"] += 1
            else:
                flat_utc = AD.next_rollover_utc(entry_utc, rule, wd)

        ivl = dt.timedelta(minutes=AD.TF_MINUTES[tf])
        at = times[i] + ivl
        try:
            ap = anchor_for(r["symbol"], at, bars[i].c, int(r["direction"]), band)
        except SpreadUnavailable:
            tel["skip_no_spread"] += 1
            continue
        pr = replay(bars, i, int(r["direction"]), stop_dist=stop, policy=pol,
                    times=times, server=AD.SERVER, bar_minutes=AD.TF_MINUTES[tf],
                    flat_before_utc=flat_utc, entry_price=ap)
        xi = pr.exit_index
        tel[f"exit_{pr.exit_reason}"] += 1
        out.append({
            **r,
            "entry_utc": at.isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "entry_price": (float(ap) if ap is not None else float(r["entry_price"])),
            "sl_distance_price": stop,
            "target_dist": target,
            "r_gross": float(winsorize_R(pr.r_gross)),
            "exit_policy": variant.name,
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * AD.TF_MINUTES[tf] / 60.0, 4),
        })
    return out, dict(tel)


# =====================================================================================

def summ(v):
    n = len(v)
    if not n:
        return {"n": 0}
    return {"n": n, "mean": round(statistics.fmean(v), 6),
            "se": (round(statistics.pstdev(v) / math.sqrt(n), 6) if n > 1 else None),
            "sum": round(math.fsum(v), 4)}


def main() -> int:
    t0 = time.time()
    aa = json.load(gzip.open(AA_IN, "rt"))
    am = json.load(gzip.open(AM_SUBMID, "rt"))
    base_in = {s: list(r) for s, r in aa["trades"].items()}
    submid_reclocked = am["trades"]["server_repaired"]
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(AD.SERVER)
    series, index, _ = AD.load_bars()
    print(f"bars in {time.time()-t0:.0f}s: {len(series)} series", flush=True)

    controls: dict = {}
    arms: dict[str, dict] = {a: {"base": {}, "variants": {}} for a in ARMS}
    skips: dict[str, dict] = {}

    # ---- C1: the `old` base arm must reproduce AA's published r_gross ---------------
    parity = {"rows": 0, "mismatch": 0, "max_abs_err": 0.0, "examples": []}
    for sleeve, rows in sorted(base_in.items()):
        for band, arm in zip((None,) + BANDS, ARMS):
            got, sk = rewalk_base(rows, sleeve, series, index, band)
            arms[arm]["base"][sleeve] = got
            if sk:
                skips[f"{arm}:{sleeve}"] = sk
        for a, b in zip(rows, arms["old"]["base"][sleeve]):
            # same order, same length when nothing skipped; guard both
            if a["decision_bar_iso"] != b["decision_bar_iso"]:
                parity["mismatch"] += 1
                continue
            err = abs(float(b["r_gross"]) - float(a["r_gross"]))
            parity["rows"] += 1
            parity["max_abs_err"] = max(parity["max_abs_err"], err)
            if err > 1e-9:
                parity["mismatch"] += 1
                if len(parity["examples"]) < 8:
                    parity["examples"].append(
                        {"sleeve": sleeve, "symbol": a["symbol"],
                         "decision_bar_iso": a["decision_bar_iso"],
                         "published": a["r_gross"], "rederived": b["r_gross"]})
        print(f"  base {sleeve:40s} n={len(rows):6d} {time.time()-t0:6.0f}s", flush=True)
    controls["C1_base_reproduces_AA_r_gross"] = parity

    # ---- SUBMID reclocked (AM's 533) — the same treatment ---------------------------
    sparity = {"rows": 0, "mismatch": 0, "max_abs_err": 0.0}
    for band, arm in zip((None,) + BANDS, ARMS):
        got, sk = rewalk_base(submid_reclocked, SUBMID, series, index, band)
        arms[arm]["variants"][f"{SUBMID}|reclocked"] = got
        if sk:
            skips[f"{arm}:{SUBMID}|reclocked"] = sk
    for a, b in zip(submid_reclocked, arms["old"]["variants"][f"{SUBMID}|reclocked"]):
        if a["decision_bar_iso"] != b["decision_bar_iso"]:
            sparity["mismatch"] += 1
            continue
        err = abs(float(b["r_gross"]) - float(a["r_gross"]))
        sparity["rows"] += 1
        sparity["max_abs_err"] = max(sparity["max_abs_err"], err)
        if err > 1e-9:
            sparity["mismatch"] += 1
    controls["C1b_submid_reclocked_reproduces_AM_r_gross"] = sparity

    # ---- C0: `resimulate_qs(band=None)` == `AD.resimulate`, field for field ----------
    c0 = {"cells": {}, "any_mismatch": False}
    for (sleeve, name), variant in sorted(VARIANTS.items()):
        ref, _ = AD.resimulate(base_in[sleeve], variant, series, index, costs, ACCOUNT, rule)
        for band, arm in zip((None,) + BANDS, ARMS):
            got, sk = resimulate_qs(base_in[sleeve], variant, series, index, costs, rule, band)
            arms[arm]["variants"][f"{sleeve}|{name}"] = got
            if sk:
                skips[f"{arm}:{sleeve}|{name}"] = sk
        mine = arms["old"]["variants"][f"{sleeve}|{name}"]
        diffs = 0
        fields = ("r_gross", "exit_reason", "exit_utc", "entry_utc", "sl_distance_price",
                  "target_dist", "exit_bar_offset", "hold_hours", "mfe_r", "mae_r")
        if len(ref) != len(mine):
            diffs += abs(len(ref) - len(mine))
        for a, b in zip(ref, mine):
            for f in fields:
                if a.get(f) != b.get(f):
                    diffs += 1
                    break
        c0["cells"][f"{sleeve}@{name}"] = {"n_ref": len(ref), "n_mine": len(mine),
                                           "rows_differing": diffs}
        c0["any_mismatch"] |= bool(diffs)
        print(f"  cell {sleeve}@{name:12s} n={len(mine):5d} C0 diffs={diffs} "
              f"{time.time()-t0:6.0f}s", flush=True)
    controls["C0_resimulate_qs_band_None_equals_AD_resimulate"] = c0

    ok = (parity["mismatch"] == 0 and sparity["mismatch"] == 0 and not c0["any_mismatch"])
    controls["all_controls_pass"] = ok

    # ---- what the substrate looks like ----------------------------------------------
    per_arm = {}
    for arm in ARMS:
        pool = [float(r["r_gross"]) for rs in arms[arm]["base"].values() for r in rs]
        per_arm[arm] = {"n_base_rows": len(pool), "base_pooled_r_gross": summ(pool),
                        "variants": {k: summ([float(r["r_gross"]) for r in v])
                                     for k, v in sorted(arms[arm]["variants"].items())}}
    controls["per_arm"] = per_arm
    controls["skips"] = skips
    controls["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    CTL.write_text(json.dumps(controls, indent=1, sort_keys=True))
    print(json.dumps({k: v for k, v in controls.items()
                      if k.startswith(("C0", "C1", "all"))}, indent=1)[:2000])

    if not ok:
        print("CONTROLS FAILED — refusing to write the substrate")
        return 2

    with gzip.open(OUT, "wt") as fh:
        json.dump({"schema": "gtos.wave20.m3.substrate.v1",
                   "generated_by": str(Path(__file__).relative_to(REPO)),
                   "arms": ARMS, "bands": BANDS,
                   "anchoring": "FILL — entry_price = close + direction * spread, BarQuote.BID",
                   "sources": {"aa": str(AA_IN.relative_to(REPO)),
                               "am_submid": str(AM_SUBMID.relative_to(REPO)),
                               "bars": AD.BARS, "costs": str(AD.COSTS.relative_to(REPO))},
                   "data": arms}, fh)
    print("WROTE", OUT, f"{OUT.stat().st_size/1e6:.1f} MB  {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
