"""Generate and label the WHOLE generatable estate, once, for every downstream consumer.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_estate_generate.py

WHY ONE PASS
------------
Session W's pilot walked the 12 live market-expansion sleeves on the D1 archive. Three
things were left undone and all three need the same substrate:

  1. the rest of the estate — the H4 core book (`metals_core`, `crypto`, `energy_agri` and
     the rest) and the M15 session sleeves, none of which W scored;
  2. the MERGED book — the sleeves composed into one portfolio through the production
     sizer, which no artifact in the programme has ever measured;
  3. the diversifier certification — does a sleeve that fails standalone still RAISE the
     book's Sharpe (`validation_integrity/portfolio_contribution.py`).

All three need the same thing: per-trade records with an entry instant, an EXIT instant, a
direction, a stop distance and a gross R. So this script produces them once and writes one
artifact; `x_gate_estate.py`, `x_book_merge.py` and `x_diversifier.py` all read it.

WHY THE CACHES CANNOT DO THIS, MEASURED RATHER THAN ASSUMED
------------------------------------------------------------
The W7 validation caches (`INTEG_W3_streams_cache.pkl`, `INTEG_W5_new_streams_cache.pkl`)
carry `{sleeve: [{sleeve, sym, date, year, R, intra_size, R_sized}]}` and nothing else —
verified by disassembly and corroborated twice in the repo's own words:
`scripts/recost_w7_validation.py:47-48` ("the caches carry no stop distance") and
`phase3/SESSION_N_W7_RECOST_RESULT.md:32` ("no exit index survives in any cache"). Five of
the eight fields `walkforward.TradeRecord` requires are absent, most fatally `exit_utc`.
No adapter can synthesise them.

**That is why OD-3 is stuck on holding time.** Re-generating from bars does not just
work around the gap — it CLOSES it, because `simulate_detail` returns the exit bar index,
so the holding time is measured off the simulated path rather than assumed, and `cost_r`
then charges swap against a hold this run actually produced.

PRODUCTION THE WHOLE WAY DOWN
-----------------------------
    sleeve set        `book_engine._active_sleeve_names` (via `GenerationPort`)
    generation        `GenerationPort` -> the live `UltimateBookLiveEngine._generate_intents`
    canonical->broker `symbol_map.build_broker_symbol_resolver(profile)`
    fill              `ultimate_book.primitives.simulate_detail` (the sanctioned labeler)
    winsorisation     `ultimate_book.admission.winsorize_R`
    timeframes        `ultimate_book.sleeves.registry.active_specs`

ONE RESEARCH OVERRIDE, STAMPED
-------------------------------
`config/agent_config.yaml:1270` sets `ultimate_book_include_clean3: false`, so the three
clean-3 sleeves — `sub_xvol_pullback`, `vp_euidx_pocgrav`, `sub_mid_dn_revert` — are NOT in
the live active book and `GenerationPort` emits zero candidates for them. One of those,
`sub_xvol_pullback`, is a `SURVIVOR_BOOK_V1` UNCONDITIONAL sleeve and is named in this
session's brief as one of the four the funded account is being armed on. To measure it at
all the flag has to be flipped in the config dict handed to the port. That is done here, in
a research driver, and recorded in the artifact as `research_overrides`. **The config file
on disk is not touched** (it is decision-contract-bound, `CLAUDE.md` H1).

FOUR LIMITATIONS, UP FRONT
---------------------------
1. **Entry is the decision bar's CLOSE.** `simulate` enters at `bars[i].c`
   (`primitives.py:37`) and is the only sanctioned labeler. For the D1 market-expansion
   family whose contract is next-open, W measured the divergence at a signed +0.00152 R,
   i.e. marginally against the sleeves. Re-measured here.
2. **`maxbars=80`.** On H4 that is 320 hours, which is exactly the structural horizon
   `SURVIVOR_BOOK_V1.json` records for the core book (`horizon_hours: 320.0`). On D1 it is
   W's pilot setting, kept so the mx numbers stay comparable to `W_MX_PILOT.json`.
3. **Port fidelity is TRANSFERRED for every sleeve here except five.** K measured
   `fx_jpy`, `fx_jpy_ny`, `idxrev`, `mx_nzdjpy_d1_donchian_20_breakout` and
   `vol_compression`; everything else carries the per-bar CLASS rate with its basis
   attached (`walkforward/fidelity.py`).
4. **Seven first-of-day candidate sleeves are NOT generated.** K measured that port at 19%
   live-recall; a number for them would measure the latch defect. They are still emitted
   into the family list with zero trades so the multiplicity correction counts them.

Offline and pure: reads gzipped CSV bars, imports no broker module, writes one JSON.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.primitives import Bar, simulate_detail  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402
from src.research_infra.walkforward.fidelity import fidelity_for  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_ESTATE_TRADES.json.gz"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80
FIDELITY_FLOOR = 0.50


def build(config_overrides: dict) -> tuple:
    base = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    cfg.update(config_overrides)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files = {}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    port = GenerationPort(cfg, src, namespace="x_estate", broker_symbol=res)
    return cfg, prof, res, files, src, port


def main() -> dict:
    overrides = {
        # See module docstring. Measured, stamped, and NOT written to the config file.
        "ultimate_book_include_clean3": True,
    }
    cfg, prof, res, files, src, port = build(overrides)
    active = set(port.active_sleeve_names())
    print(f"active book (with research overrides): {len(active)} sleeves")

    # sleeve -> decision timeframe, from the PRODUCTION generation registry. The membership
    # test is the engine's own active set; this lookup only supplies the timeframe.
    tf_of: dict[str, int] = {}
    surface_of: dict[str, tuple] = {}
    # Resolve the two opt-in sub-books with the ENGINE's own resolvers. Passing
    # `market_expansion_sleeves=None` here is not "all of them" — `market_expansion_registry`
    # returns `{}` for None (`admission.py:570-572`), asymmetrically with the candidate book,
    # which silently dropped all 12 mx sleeves on the first run of this driver.
    for spec in active_specs(
        None,
        include_candidate_book=bool(cfg.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
        include_market_expansion_book=bool(
            cfg.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
    ):
        if spec.tag in active:
            tf_of[spec.tag] = spec.timeframe
            surface_of[spec.tag] = tuple(spec.on_surface)
    missing = sorted(active - set(tf_of))
    if missing:
        # `active_specs(market_expansion_sleeves=None)` returns the whole authored family;
        # anything still missing has no generator at all.
        print(f"  no generator spec for: {missing}")

    # Fidelity split. Generating a sleeve the gate will refuse anyway wastes hours; NOT
    # listing it in the family would shrink the multiplicity correction, which is the
    # failure the correction exists to prevent. So: refused sleeves are carried with zero
    # trades.
    scoreable, refused = [], []
    for s in sorted(tf_of):
        f = fidelity_for(s)
        (scoreable if f.scoreable(FIDELITY_FLOOR) else refused).append(s)
    print(f"  fidelity>= {FIDELITY_FLOOR}: {len(scoreable)} scoreable, {len(refused)} refused")
    print(f"  refused (not generated, still in the family): {refused}")

    by_tf: dict[int, list[str]] = collections.defaultdict(list)
    for s in scoreable:
        by_tf[tf_of[s]].append(s)

    # ---- bar series, once ---------------------------------------------------------------
    series: dict[tuple[str, int], tuple[list[Bar], list[dt.datetime]]] = {}
    index: dict[tuple[str, int], dict[dt.datetime, int]] = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        series[key] = (bars, times)
        index[key] = {ts: i for i, ts in enumerate(times)}

    t_start = time.time()
    all_rows: list[dict] = []
    grids: dict[str, dict] = {}
    seen: set = set()
    n_dupes = 0

    for tf in sorted(by_tf, key=lambda t: TF_MINUTES[t]):
        sleeves = sorted(by_tf[tf])
        # Drive the UNION of this timeframe's bar closes across every symbol its sleeves can
        # trade, so a symbol whose history starts later is not truncated to another's grid.
        wanted = {res(s) for name in sleeves for s in surface_of[name]}
        stamps = set()
        for (sym, ktf) in files:
            if ktf != tf or sym not in wanted:
                continue
            for ts in series.get((sym, ktf), ((), ()))[1]:
                stamps.add(ts)
        grid = sorted(t + dt.timedelta(minutes=TF_MINUTES[tf]) for t in stamps)
        if not grid:
            print(f"  {TF_NAME[tf]}: no bars for {sleeves}")
            continue
        print(f"\n=== {TF_NAME[tf]}: {len(sleeves)} sleeves, {len(grid)} closes "
              f"{grid[0].date()} .. {grid[-1].date()} ===", flush=True)
        t0 = time.time()
        got = 0
        for i, ts in enumerate(grid):
            for c in port.generate(ts, tags=sleeves).candidates:
                # Live places each (sleeve, symbol, decision_bar) AT MOST ONCE
                # (`book_owner.py:1678`, key named at `book_engine.py:546-548`). A union grid
                # re-fires a 5-day symbol on instants contributed by a 7-day one and the
                # staleness guard permits it for two intervals. W measured 22.0% duplicates
                # on the D1 grid; un-deduped they would tell the sample gate it had that much
                # more evidence than it has.
                key = (c.sleeve, c.symbol, c.decision_bar_iso)
                if key in seen:
                    n_dupes += 1
                    continue
                seen.add(key)
                all_rows.append({"cand": c, "tf": tf})
                got += 1
            if (i + 1) % 5000 == 0:
                el = time.time() - t0
                print(f"    {i+1}/{len(grid)}  {el:.0f}s  "
                      f"eta {el/(i+1)*(len(grid)-i-1):.0f}s  kept={got}", flush=True)
        grids[TF_NAME[tf]] = {
            "n_closes": len(grid), "first": grid[0].isoformat(), "last": grid[-1].isoformat(),
            "sleeves": sleeves, "seconds": round(time.time() - t0, 1), "candidates_kept": got,
        }
        print(f"  {TF_NAME[tf]} done in {time.time()-t0:.0f}s, {got} unique candidates",
              flush=True)

    print(f"\ngeneration total {time.time()-t_start:.0f}s; {len(all_rows)} unique candidates, "
          f"{n_dupes} duplicates dropped", flush=True)

    # ---- label through the sanctioned fill authority --------------------------------------
    trades: dict[str, list[dict]] = {s: [] for s in sorted(tf_of)}
    skips: collections.Counter = collections.Counter()
    gaps: list[float] = []
    for row in all_rows:
        c, tf = row["cand"], row["tf"]
        sym = res(c.symbol)
        key = (sym, tf)
        if key not in index:
            skips[f"{c.sleeve}:no_series[{c.symbol}->{sym}]"] += 1
            continue
        iso = c.decision_bar_iso
        if not iso:
            skips[f"{c.sleeve}:no_decision_bar_iso"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(iso))
        bars, times = series[key]
        if i is None or i + 2 >= len(bars):
            skips[f"{c.sleeve}:bar_not_found_or_no_room"] += 1
            continue
        r, xi = simulate_detail(
            bars, i, c.direction, stop_dist=c.stop_dist, target_dist=c.target_dist,
            maxbars=MAXBARS, cost=0.0,
        )
        r = winsorize_R(r)
        entry = bars[i].c
        ivl = dt.timedelta(minutes=TF_MINUTES[tf])
        # The trade is entered at the decision bar's CLOSE, which is `times[i] + interval`,
        # not `times[i]` (the bar's OPEN). The difference does not move holding_hours — both
        # ends shift together — but it does move the swap-night count `cost_r` charges and
        # the calendar day the panel keys on. W's pilot used the open stamp; this is the
        # instant the fill actually happens.
        gaps.append(c.direction * (bars[i + 1].o - entry) / c.stop_dist)
        trades[c.sleeve].append({
            "sleeve": c.sleeve,
            "symbol": sym,
            "symbol_canonical": c.symbol,
            "entry_utc": (times[i] + ivl).isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "direction": int(c.direction),
            "sl_distance_price": float(c.stop_dist),
            "entry_price": float(entry),
            "r_gross": float(r),
            "timeframe": int(tf),
            "decision_bar_iso": iso,
            "decision_day": c.decision_day,
            "bar_decision_day": (c.features or {}).get("bar_decision_day"),
            "target_dist": (float(c.target_dist) if c.target_dist else None),
            "intra_size": float(c.intra_size or 1.0),
            "ll_impulse": c.ll_impulse,
            "decision_hour": c.decision_hour,
            "vp_loc": c.vp_loc,
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
            "features": {k: v for k, v in (c.features or {}).items() if k != "last_close"},
        })

    n_tr = sum(len(v) for v in trades.values())
    print(f"labelled {n_tr} trades over {sum(1 for v in trades.values() if v)} sleeves; "
          f"skipped {sum(skips.values())}")
    if skips:
        print("  skips:", dict(skips))

    abs_gaps = [abs(g) for g in gaps]
    entry_gap = {
        "n": len(gaps),
        "mean_signed_R": round(statistics.fmean(gaps), 6) if gaps else None,
        "median_signed_R": round(statistics.median(gaps), 6) if gaps else None,
        "mean_abs_R": round(statistics.fmean(abs_gaps), 6) if abs_gaps else None,
        "note": ("direction * (next_open - decision_close) / stop_dist. POSITIVE means the "
                 "next open would have been better for the trade, i.e. entering at the close "
                 "is DISADVANTAGED."),
    }
    print("  entry-convention gap (signed):", entry_gap["mean_signed_R"])

    out = {
        "schema": "gtos.walkforward.estate_trades.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_estate_generate.py",
        "bars_archive": BARS,
        "maxbars": MAXBARS,
        "research_overrides": {
            "config": overrides,
            "why": ("config/agent_config.yaml:1270 sets ultimate_book_include_clean3: false, so "
                    "sub_xvol_pullback / vp_euidx_pocgrav / sub_mid_dn_revert are NOT in the live "
                    "active book and the port emits zero candidates for them. sub_xvol_pullback is "
                    "a SURVIVOR_BOOK_V1 UNCONDITIONAL sleeve. The flag is flipped in the config "
                    "DICT handed to GenerationPort; the file on disk is untouched."),
        },
        "active_book": sorted(active),
        "family_all": sorted(tf_of),
        "generated_sleeves": scoreable,
        "fidelity_refused_sleeves": refused,
        "timeframe_by_sleeve": {s: TF_NAME.get(t, str(t)) for s, t in sorted(tf_of.items())},
        "grids": grids,
        "n_candidates_unique": len(all_rows),
        "n_duplicates_dropped": n_dupes,
        "n_trades_by_sleeve": {s: len(v) for s, v in sorted(trades.items())},
        "entry_convention_gap": entry_gap,
        "skips": dict(skips),
        "seconds_total": round(time.time() - t_start, 1),
        "trades": trades,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, default=str)
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB)")
    for s, v in sorted(trades.items(), key=lambda kv: -len(kv[1])):
        print(f"  {s:42s} {len(v):6d}")
    return out


if __name__ == "__main__":
    main()
