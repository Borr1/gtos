"""B7 INDEPENDENT VERIFICATION part 2 — the energy_agri exit contract, and the book-level
capped frequency effect of adding ETHUSD.

The energy A/B is a PAIRED test on identical entries, so the entry generator is deliberately the
estate's own (`metals.fvg_signal` + `energy_agri.energy_gate`) — varying it would break the pairing
that is the whole point. What is re-implemented independently here is the thing under test: the two
EXIT contracts (plain stop/4R/maxbars vs partial_be_runner), cross-checked trade-by-trade against
`walkforward.exits.replay`.

The capped-book model is read out of the live sizing code, not assumed: `admission.py:1171-1177`
buckets intents by (decision_day, cluster) and `:1256` sets `per_trade = unit_risk / n`, so a
cluster-day unit's realised R is the MEAN of its members' R and total daily risk is independent of
how many symbols fire.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import random
import statistics as stat
import sys
import time
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp")
sys.path.insert(0, str(OUT))

from b7_verify import (my_load_h4, my_atr14, my_crypto_signal, my_walk, mean, tstat,  # noqa: E402
                       day_block_boot, paired_delta, MAXBARS, CRYPTO9)

from src.components.ultimate_book.primitives import vol_ratio                    # noqa: E402
from src.components.ultimate_book.admission import winsorize_R, CLUSTER_OF_SLEEVE_FULL  # noqa: E402
from src.components.ultimate_book.sleeves import energy_agri as SL_ENERGY        # noqa: E402
from src.components.ultimate_book.sleeves.metals import fvg_signal               # noqa: E402
from src.components.ultimate_book.sleeves import substrate as SL_SUB             # noqa: E402
from src.components.ultimate_book.sleeves import substrate_engine as SE          # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay              # noqa: E402


def energy_entries(bars, atrs, i):
    """The live energy_agri entry, from the sleeve's own code (paired test => hold entries fixed)."""
    s = fvg_signal(bars, atrs, i)
    if s is None:
        return None
    d, sd = s
    if not SL_ENERGY.energy_gate(vol_ratio(atrs, i), SL_ENERGY.trend_slope(bars, i, 30)):
        return None
    return d, sd


def xvol_entry(bars, atrs, i):
    if len(bars) < SE.WARMUP or i < SE.WARMUP:
        return None
    a = atrs[i]
    if a <= 0:
        return None
    st = SE.compute_state(bars, i, None)
    if st is None:
        return None
    if not SE.cell_matches(SE.cell_coords(st), SL_SUB.XVOL_CONDS):
        return None
    sd, td = SE.stop_target(a, SL_SUB.XVOL_GEOM[0], SL_SUB.XVOL_GEOM[1])
    return SL_SUB.XVOL_DIR, sd, td


def main():
    t0 = time.time()
    res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat()}

    # ================================================== ENERGY_AGRI EXIT CONTRACT A/B ==========
    oils = ["USOIL_cash", "UKOIL_cash"]
    entries = []
    for s in oils:
        bars, times = my_load_h4(s)
        atrs = [my_atr14(bars, k) for k in range(len(bars))]
        for i in range(len(bars) - 2):
            e = energy_entries(bars, atrs, i)
            if e is None:
                continue
            d, sd = e
            entries.append({"symbol": s, "i": i, "d": d, "sd": sd, "bars": bars, "times": times})
    print(f"energy entries: {len(entries)} ({time.time()-t0:.0f}s)")

    CONTRACTS = {
        "PLAIN_published_4R":        dict(tmult=4.0, partial=None),
        "LIVE_partial_be_runner":    dict(tmult=4.0, partial=2.0, be=True),
        "VARIANT_partial_no_BE":     dict(tmult=4.0, partial=2.0, be=False),
        "VARIANT_target_2R":         dict(tmult=2.0, partial=None),
        "VARIANT_target_3R":         dict(tmult=3.0, partial=None),
        "VARIANT_target_6R":         dict(tmult=6.0, partial=None),
    }
    per_contract = {}
    mismatch = 0
    checked = 0
    for name, cfg in CONTRACTS.items():
        rs, reasons, holds = [], collections.Counter(), []
        for e in entries:
            td = cfg["tmult"] * e["sd"]
            m = my_walk(e["bars"], e["i"], e["d"], e["sd"], td, MAXBARS,
                        partial_r=cfg.get("partial"), partial_frac=0.5,
                        be_after_partial=cfg.get("be", True))
            pol = ExitPolicy(target_dist=td, maxbars=MAXBARS,
                             partial_at_r=cfg.get("partial"), partial_frac=0.5,
                             be_stop_after_partial=cfg.get("be", True), label=name)
            pr = replay(e["bars"], e["i"], e["d"], stop_dist=e["sd"], policy=pol)
            checked += 1
            if abs(m["r"] - pr.r_gross) > 1e-9 or m["exit_index"] != pr.exit_index \
               or m["reason"] != pr.exit_reason:
                mismatch += 1
            rs.append(float(winsorize_R(m["r"])))
            reasons[m["reason"]] += 1
            holds.append((e["times"][m["exit_index"]] - e["times"][e["i"]]).total_seconds() / 3600.0)
        per_contract[name] = {
            "n": len(rs), "mean_r": round(mean(rs), 5), "t": round(tstat(rs), 3),
            "total_r": round(sum(rs), 3), "reasons": dict(reasons),
            "median_hold_h": round(stat.median(holds), 1), "_rs": rs,
        }
        print(f"  {name:28s} n={len(rs)} mean={mean(rs):+.4f} t={tstat(rs):+.2f} {dict(reasons)}")
    res["energy_labeller_crosscheck"] = {"trades_compared": checked, "mismatches": mismatch}

    base = per_contract["PLAIN_published_4R"]["_rs"]
    res["energy_exit_ab"] = {k: {kk: vv for kk, vv in v.items() if kk != "_rs"}
                             for k, v in per_contract.items()}
    res["energy_paired_deltas_vs_plain4R"] = {
        k: paired_delta(base, v["_rs"]) for k, v in per_contract.items()
        if k != "PLAIN_published_4R"}
    for k, v in res["energy_paired_deltas_vs_plain4R"].items():
        print(f"  DELTA {k:28s} {v}")

    # day-block bootstrap of the paired delta (the (symbol,day) block is the correlated unit)
    live = per_contract["LIVE_partial_be_runner"]["_rs"]
    dr = [b - a for a, b in zip(base, live)]
    blocks = collections.defaultdict(list)
    for e, d_ in zip(entries, dr):
        key = (e["symbol"], (e["times"][e["i"]] + dt.timedelta(hours=4)).date().isoformat())
        blocks[key].append(d_)
    bl = list(blocks.values())
    rng = random.Random(20260811)
    ms = []
    for _ in range(20000):
        pool = []
        for _ in range(len(bl)):
            pool.extend(bl[rng.randrange(len(bl))])
        ms.append(sum(pool) / len(pool))
    ms.sort()
    res["energy_live_vs_plain_day_block"] = {
        "n": len(dr), "blocks": len(bl), "mean_delta": round(mean(dr), 5),
        "ci95": [round(ms[500], 5), round(ms[19500], 5)],
        "p_delta_ge_0": round(sum(1 for m in ms if m >= 0) / 20000, 5)}
    print("  energy day-block delta:", res["energy_live_vs_plain_day_block"])

    # energy sleeve's own robustness, plain contract
    e_rows = [{"symbol": e["symbol"],
               "entry_utc": (e["times"][e["i"]] + dt.timedelta(hours=4)).isoformat(),
               "r_gross": r} for e, r in zip(entries, base)]
    res["energy_plain_day_block"] = day_block_boot(e_rows)
    pre = [r for r in e_rows if r["entry_utc"][:4] < "2025"]
    fwd = [r for r in e_rows if r["entry_utc"][:4] >= "2025"]
    res["energy_era_split"] = {"pre2025": {"n": len(pre), "mean": round(mean([r["r_gross"] for r in pre]), 5)},
                               "y2025plus": {"n": len(fwd), "mean": round(mean([r["r_gross"] for r in fwd]), 5)}}
    print("  energy plain day-block:", res["energy_plain_day_block"], res["energy_era_split"])

    # ================================================== BOOK-LEVEL CAPPED FREQUENCY ============
    # trades per sleeve, on the LIVE surfaces, over the window where all three surfaces exist
    sleeve_rows = {"energy_agri": [{"sleeve": "energy_agri", **r} for r in e_rows]}

    xrows = []
    for s in sorted(set(SL_SUB.XVOL_ON_SURFACE)):
        got = my_load_h4(s)
        if not got or len(got[0]) <= 300:
            continue
        bars, times = got
        atrs = [my_atr14(bars, k) for k in range(len(bars))]
        for i in range(len(bars) - 2):
            e = xvol_entry(bars, atrs, i)
            if e is None:
                continue
            d, sd, td = e
            m = my_walk(bars, i, d, sd, td, MAXBARS)
            xrows.append({"sleeve": "sub_xvol_pullback", "symbol": s,
                          "entry_utc": (times[i] + dt.timedelta(hours=4)).isoformat(),
                          "r_gross": float(winsorize_R(m["r"]))})
    sleeve_rows["sub_xvol_pullback"] = xrows
    print(f"  sub_xvol_pullback n={len(xrows)} mean={mean([r['r_gross'] for r in xrows]):+.4f} "
          f"({time.time()-t0:.0f}s)")

    crypto_rows = {}
    for s in CRYPTO9:
        got = my_load_h4(s)
        if not got or len(got[0]) <= 300:
            continue
        bars, times = got
        atrs = [my_atr14(bars, k) for k in range(len(bars))]
        out = []
        for i in range(len(bars) - 2):
            sig = my_crypto_signal(bars, i, atrs)
            if sig is None:
                continue
            d, sd = sig
            m = my_walk(bars, i, d, sd, 4.0 * sd, MAXBARS)
            out.append({"sleeve": "crypto", "symbol": s,
                        "entry_utc": (times[i] + dt.timedelta(hours=4)).isoformat(),
                        "r_gross": float(winsorize_R(m["r"]))})
        crypto_rows[s] = out

    CL = {sl: CLUSTER_OF_SLEEVE_FULL.get(sl) for sl in
          ("crypto", "energy_agri", "sub_xvol_pullback")}
    res["clusters"] = CL
    print("  clusters:", CL)

    LO, HI = "2021-02-01", "2026-08-01"
    span_months = ((2026 - 2021) * 12 + (8 - 2))  # 2021-02 .. 2026-07 inclusive = 66 months

    def book(crypto_syms):
        rows = ([r for s in crypto_syms for r in crypto_rows.get(s, [])]
                + sleeve_rows["energy_agri"] + sleeve_rows["sub_xvol_pullback"])
        rows = [r for r in rows if LO <= r["entry_utc"][:10] < HI]
        units = collections.defaultdict(list)
        for r in rows:
            units[(r["entry_utc"][:10], CL[r["sleeve"]])].append(r["r_gross"])
        unit_r = {k: mean(v) for k, v in units.items()}
        days = sorted({k[0] for k in unit_r})
        tot = sum(unit_r.values())
        n_crypto_units = sum(1 for k in unit_r if k[1] == CL["crypto"])
        return {"n_trades": len(rows), "n_units": len(unit_r), "n_crypto_units": n_crypto_units,
                "book_days": len(days), "book_days_per_month": round(len(days) / span_months, 4),
                "gross_R_per_book_day": round(tot / len(days), 4),
                "gross_R_per_month": round(tot / span_months, 4)}

    res["capped_book_2021_02_to_2026_07"] = {
        "span_months": span_months,
        "LIVE_BTC_DASH": book(["BTCUSD", "DASHUSD"]),
        "PLUS_ETH_BTC_DASH_ETH": book(["BTCUSD", "DASHUSD", "ETHUSD"]),
        "SWAP_BTC_ETH": book(["BTCUSD", "ETHUSD"]),
        "FAMILY9": book(CRYPTO9),
    }
    for k, v in res["capped_book_2021_02_to_2026_07"].items():
        if isinstance(v, dict):
            print(f"  BOOK {k:24s} {v}")

    # crypto-cluster-only capped frequency, whole archive (lane 8's crypto_frequency_capped)
    def cryptofreq(syms):
        rows = [r for s in syms for r in crypto_rows.get(s, [])]
        if not rows:
            return None
        d0 = min(r["entry_utc"][:10] for r in rows)
        d1 = max(r["entry_utc"][:10] for r in rows)
        yrs = (dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)).days / 365.25
        byday = collections.defaultdict(list)
        for r in rows:
            byday[r["entry_utc"][:10]].append(r["r_gross"])
        capped = [mean(v) for v in byday.values()]
        return {"n": len(rows), "days": len(byday), "span_y": round(yrs, 2),
                "d_per_mo": round(len(byday) / (yrs * 12), 3),
                "capped_mean": round(mean(capped), 4),
                "capped_R_mo": round(sum(capped) / (yrs * 12), 4),
                "uncapped_R_mo": round(sum(r["r_gross"] for r in rows) / (yrs * 12), 4)}

    res["crypto_cluster_capped_whole_archive"] = {
        "BTC only": cryptofreq(["BTCUSD"]),
        "BTC+DASH (LIVE)": cryptofreq(["BTCUSD", "DASHUSD"]),
        "BTC+ETH": cryptofreq(["BTCUSD", "ETHUSD"]),
        "BTC+DASH+ETH": cryptofreq(["BTCUSD", "DASHUSD", "ETHUSD"]),
        "family9": cryptofreq(CRYPTO9),
    }
    for k, v in res["crypto_cluster_capped_whole_archive"].items():
        print(f"  CRYPTOFREQ {k:18s} {v}")

    # direction split, BTC+ETH, out of window — the drift control
    bt = crypto_rows.get("BTCUSD", []) + crypto_rows.get("ETHUSD", [])
    json.dump(res, open(OUT / "B7_VERIFY_ENERGY_BOOK.json", "w"), indent=1)
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
