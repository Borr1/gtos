"""B7 INDEPENDENT VERIFICATION of Lane 8's two live-change measurements.

Deliberately does NOT re-run lane8_*.py. Three layers are re-implemented from the written
specification and then cross-checked against the estate machinery; a mismatch anywhere is a
finding, not a bug to paper over.

  layer 1  bar loading      my own gz/CSV parse + broker_clock conversion, cross-checked
                            against generation.CsvBarSource (the seam AA/AQ/lane8 used)
  layer 2  the crypto rule  re-implemented from crypto.py's DOCSTRING spec (Donchian-20
                            breakout on the closed bar, gated on lag-1 autocorr of the last
                            60 close-to-close changes >= 0.15, stop 2*ATR14, target 4R),
                            cross-checked signal-by-signal against crypto.crypto_signal
  layer 3  the labeller     my own barrier walk (stop / target / maxbars, pessimistic
                            same-bar tie) AND my own partial_be_runner, cross-checked
                            trade-by-trade against walkforward.exits.replay

Cost is charged through src/costs/cost_r, which is the ratified cost authority; that is not
re-implemented (re-deriving broker truth would be a different and worse claim).

Read-only. No broker, no VPS, no config, no git write.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import glob
import gzip
import json
import os
import random
import statistics as stat
import sys
import time
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
MAXBARS = 80
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp")

from src.components.ultimate_book.primitives import Bar                       # noqa: E402
from src.utils.broker_clock import broker_epoch_to_utc, resolve_rule          # noqa: E402

RULE_FTMO = resolve_rule("FTMO-Server3")

CRYPTO9 = ["BTCUSD", "ETHUSD", "DASHUSD", "XTZUSD", "AVAUSD", "ADAUSD", "DOTUSD", "LTCUSD", "XRPUSD"]


# ================================================================ layer 1: my own bar loader ===
def my_load_h4(sym: str, broker: str = "FTMO"):
    """(bars, times_utc) from the gz CSV, my own parse, sanctioned clock conversion."""
    path = f"{BARS}/{broker}_{sym}_H4.csv.gz"
    if not os.path.exists(path):
        return None
    bars, times = [], []
    with gzip.open(path, "rt", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                ep = int(row["time"])
                o, h, l, c = (float(row["open"]), float(row["high"]),
                              float(row["low"]), float(row["close"]))
            except (TypeError, ValueError):
                continue
            bars.append(Bar(o, h, l, c, float(row.get("tick_volume") or 0.0)))
            times.append(broker_epoch_to_utc(ep, RULE_FTMO).replace(tzinfo=None))
    return bars, times


def crosscheck_loader(syms):
    """My loader vs generation.CsvBarSource, the seam lane 8 / AA / AQ used."""
    from src.research_infra.replay_policy.generation import CsvBarSource
    from src.components.ultimate_book.bar_provider import TF_H4
    files = {(s, TF_H4): f"{BARS}/FTMO_{s}_H4.csv.gz" for s in syms}
    src = CsvBarSource(files, label="crosscheck")
    out = {}
    for s in syms:
        rows = src._load((s, TF_H4))
        theirs_b = [Bar(r["open"], r["high"], r["low"], r["close"]) for r in rows]
        theirs_t = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        mine_b, mine_t = my_load_h4(s)
        ok_n = len(mine_b) == len(theirs_b)
        bad_ohlc = bad_time = -1
        if ok_n:
            bad_ohlc = sum(1 for a, b in zip(mine_b, theirs_b)
                           if (a.o, a.h, a.l, a.c) != (b.o, b.h, b.l, b.c))
            bad_time = sum(1 for a, b in zip(mine_t, theirs_t)
                           if a != (b.replace(tzinfo=None) if b.tzinfo else b))
        out[s] = {"n_mine": len(mine_b), "n_theirs": len(theirs_b),
                  "ohlc_mismatches": bad_ohlc, "time_mismatches": bad_time,
                  "first_mine": mine_t[0].isoformat(), "last_mine": mine_t[-1].isoformat()}
    return out


# ================================================================= layer 2: my own crypto rule ==
def my_atr14(bars, i):
    """Mean true range over the 14 bars ending at i. Written from the definition."""
    if i < 14:
        return 0.0
    tot = 0.0
    for j in range(i - 13, i + 1):
        pc = bars[j - 1].c
        tot += max(bars[j].h - bars[j].l, abs(bars[j].h - pc), abs(bars[j].l - pc))
    return tot / 14.0


def my_ac60(bars, i, n=60):
    """Lag-1 autocorrelation of the last n close-to-close changes ending at bar i."""
    if i < n + 1:
        return None
    r = [bars[k].c - bars[k - 1].c for k in range(i - n + 1, i + 1)]
    m = sum(r) / len(r)
    num = sum((r[k] - m) * (r[k - 1] - m) for k in range(1, len(r)))
    den = sum((x - m) ** 2 for x in r)
    return (num / den) if den > 0 else 0.0


def my_crypto_signal(bars, i, atrs):
    """(direction, stop_dist) or None — from crypto.py's docstring spec, not its code."""
    if i < 60:
        return None
    a = atrs[i]
    if a <= 0:
        return None
    hi = max(bars[k].h for k in range(i - 20, i))
    lo = min(bars[k].l for k in range(i - 20, i))
    if bars[i].c > hi:
        d = 1
    elif bars[i].c < lo:
        d = -1
    else:
        return None
    ac = my_ac60(bars, i, 60)
    if ac is None or ac < 0.15:
        return None
    return d, 2.0 * a


# ==================================================================== layer 3: my own labeller ==
def my_walk(bars, i, d, sd, td, maxbars=MAXBARS,
            partial_r=None, partial_frac=0.5, be_after_partial=True):
    """Barrier walk. Entry at bars[i].c. Order per bar: stop, target, partial. Stop wins ties."""
    entry = bars[i].c
    end = min(i + maxbars, len(bars) - 1)
    banked = 0.0
    taken = 0.0
    sgn = 1.0 if d > 0 else -1.0
    stop = entry - sgn * sd
    tgt = (entry + sgn * td) if td else None
    plvl = (entry + sgn * partial_r * sd) if partial_r else None

    def fin(j, price, reason):
        raw = sgn * (price - entry) / sd
        return {"r": banked + (1.0 - taken) * raw, "exit_index": j, "reason": reason}

    for j in range(i + 1, end + 1):
        b = bars[j]
        if (b.l <= stop) if d > 0 else (b.h >= stop):
            return fin(j, stop, "stop")
        if tgt is not None and ((b.h >= tgt) if d > 0 else (b.l <= tgt)):
            return fin(j, tgt, "target")
        if plvl is not None and ((b.h >= plvl) if d > 0 else (b.l <= plvl)):
            banked += partial_frac * partial_r
            taken = partial_frac
            plvl = None
            if be_after_partial:
                stop = entry
    return fin(end, bars[end].c, "maxbars")


# ================================================================================ statistics ===
def mean(v):
    return stat.fmean(v) if v else float("nan")


def tstat(v):
    if len(v) < 2:
        return None
    se = stat.stdev(v) / (len(v) ** 0.5)
    return (mean(v) / se) if se else None


def day_block_boot(rows, key=lambda r: r["r_gross"], reps=20000, seed=20260811):
    """Cluster bootstrap over (symbol, entry-day) blocks — the correlated unit."""
    blocks = collections.defaultdict(list)
    for r in rows:
        blocks[(r["symbol"], r["entry_utc"][:10])].append(key(r))
    bl = list(blocks.values())
    nb = len(bl)
    if nb < 2:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        pool = []
        for _ in range(nb):
            pool.extend(bl[rng.randrange(nb)])
        means.append(sum(pool) / len(pool))
    means.sort()
    return {"n": len(rows), "blocks": nb, "mean": round(mean([key(r) for r in rows]), 5),
            "ci95": [round(means[int(0.025 * reps)], 5), round(means[int(0.975 * reps)], 5)],
            "p_le_0": round(sum(1 for m in means if m <= 0) / reps, 5)}


def paired_delta(a, b):
    """b - a, paired. Returns mean delta, CI95 (t), t-stat, n."""
    d = [x - y for x, y in zip(b, a)]
    n = len(d)
    m = mean(d)
    se = stat.stdev(d) / (n ** 0.5)
    return {"n": n, "delta": round(m, 5),
            "ci95": [round(m - 1.96 * se, 5), round(m + 1.96 * se, 5)],
            "t": round(m / se, 4) if se else None}


# ===================================================================================== main ====
def main():
    t0 = time.time()
    res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "bars_archive": BARS, "maxbars": MAXBARS}

    # ---- layer 1 cross-check
    res["loader_crosscheck"] = crosscheck_loader(["BTCUSD", "ETHUSD", "DASHUSD",
                                                  "USOIL_cash", "UKOIL_cash"])
    print("loader cross-check:", json.dumps(res["loader_crosscheck"]["BTCUSD"]))

    series = {}
    for s in CRYPTO9 + ["USOIL_cash", "UKOIL_cash"]:
        got = my_load_h4(s)
        if got and len(got[0]) > 300:
            series[s] = got
    print(f"loaded {len(series)} series ({time.time()-t0:.0f}s)")

    atrs_all = {s: [my_atr14(b, k) for k in range(len(b))] for s, (b, _) in series.items()}

    # ---- layer 2 cross-check: my rule vs crypto.crypto_signal, every bar of every symbol
    from src.components.ultimate_book.sleeves import crypto as SL_CRYPTO
    rule_cmp = {}
    for s in CRYPTO9:
        if s not in series:
            continue
        bars, _ = series[s]
        mine = theirs = both = disagree = 0
        for i in range(len(bars) - 2):
            a = my_crypto_signal(bars, i, atrs_all[s])
            b = SL_CRYPTO.crypto_signal(bars, i)
            if a:
                mine += 1
            if b:
                theirs += 1
            if bool(a) != bool(b):
                disagree += 1
            elif a and b:
                both += 1
                if a[0] != b[0] or abs(a[1] - b[1]) > 1e-12:
                    disagree += 1
        rule_cmp[s] = {"mine": mine, "estate": theirs, "agreeing": both, "disagreements": disagree}
    res["rule_crosscheck"] = rule_cmp
    print("rule cross-check:", {k: v["disagreements"] for k, v in rule_cmp.items()})

    # ---- walk every crypto symbol with MY rule and MY labeller
    from src.research_infra.walkforward.exits import ExitPolicy, replay
    from src.components.ultimate_book.admission import winsorize_R

    rows_by_sym = {}
    lab_mismatch = 0
    lab_checked = 0
    for s in CRYPTO9:
        if s not in series:
            continue
        bars, times = series[s]
        out = []
        for i in range(len(bars) - 2):
            sig = my_crypto_signal(bars, i, atrs_all[s])
            if sig is None:
                continue
            d, sd = sig
            td = 4.0 * sd
            m = my_walk(bars, i, d, sd, td)
            pr = replay(bars, i, d, stop_dist=sd,
                        policy=ExitPolicy(target_dist=td, maxbars=MAXBARS))
            lab_checked += 1
            if abs(m["r"] - pr.r_gross) > 1e-9 or m["exit_index"] != pr.exit_index \
               or m["reason"] != pr.exit_reason:
                lab_mismatch += 1
            out.append({
                "symbol": s, "direction": int(d),
                "entry_utc": (times[i] + dt.timedelta(hours=4)).isoformat(),
                "entry_price": float(bars[i].c), "sl_distance_price": float(sd),
                "r_gross": float(winsorize_R(m["r"])), "r_raw": float(m["r"]),
                "exit_reason": m["reason"],
                "hold_hours": float((times[m["exit_index"]] - times[i]).total_seconds() / 3600.0),
            })
        rows_by_sym[s] = out
        print(f"  {s:8s} n={len(out):4d} mean={mean([r['r_gross'] for r in out]):+.4f}")
    res["labeller_crosscheck"] = {"trades_compared": lab_checked, "mismatches": lab_mismatch}

    # ---- per-symbol table
    def desc(rows):
        if not rows:
            return {"n": 0}
        g = [r["r_gross"] for r in rows]
        yrs = collections.defaultdict(list)
        for r in rows:
            yrs[r["entry_utc"][:4]].append(r["r_gross"])
        pre = [r["r_gross"] for r in rows if r["entry_utc"][:4] < "2025"]
        fwd = [r["r_gross"] for r in rows if r["entry_utc"][:4] >= "2025"]
        lo = [r["r_gross"] for r in rows if r["direction"] > 0]
        sh = [r["r_gross"] for r in rows if r["direction"] < 0]
        return {
            "n": len(g), "mean_r": round(mean(g), 5), "t": round(tstat(g), 3) if len(g) > 1 else None,
            "days": len({(r["symbol"], r["entry_utc"][:10]) for r in rows}),
            "target_rate": round(sum(1 for r in rows if r["exit_reason"] == "target") / len(g), 4),
            "reasons": dict(collections.Counter(r["exit_reason"] for r in rows)),
            "first": min(r["entry_utc"] for r in rows)[:10],
            "last": max(r["entry_utc"] for r in rows)[:10],
            "pre2025": {"n": len(pre), "mean_r": round(mean(pre), 5)} if pre else None,
            "y2025plus": {"n": len(fwd), "mean_r": round(mean(fwd), 5)} if fwd else None,
            "long": {"n": len(lo), "mean_r": round(mean(lo), 5)} if lo else None,
            "short": {"n": len(sh), "mean_r": round(mean(sh), 5)} if sh else None,
            "by_year": {y: [len(v), round(mean(v), 4)] for y, v in sorted(yrs.items())},
            "years_positive": f"{sum(1 for v in yrs.values() if mean(v) > 0)}/{len(yrs)}",
            "median_hold_h": round(stat.median([r["hold_hours"] for r in rows]), 2),
        }

    res["per_symbol"] = {s: desc(r) for s, r in rows_by_sym.items()}

    ARMS = {
        "A0_LIVE_BTC_DASH": ["BTCUSD", "DASHUSD"],
        "A1_BTC_DASH_ETH": ["BTCUSD", "DASHUSD", "ETHUSD"],
        "A_BTC_ETH": ["BTCUSD", "ETHUSD"],
        "BTC_only": ["BTCUSD"],
        "ETH_only": ["ETHUSD"],
        "A2_family9": CRYPTO9,
        "ADDED4_ADA_DOT_LTC_XRP": ["ADAUSD", "DOTUSD", "LTCUSD", "XRPUSD"],
    }
    arms = {}
    for name, syms in ARMS.items():
        rows = [r for s in syms for r in rows_by_sym.get(s, [])]
        pre = [r for r in rows if r["entry_utc"][:4] < "2025"]
        fwd = [r for r in rows if r["entry_utc"][:4] >= "2025"]
        arms[name] = {"symbols": syms, "all": desc(rows),
                      "day_block_all": day_block_boot(rows),
                      "day_block_pre2025": day_block_boot(pre) if len(pre) > 5 else None,
                      "day_block_2025plus": day_block_boot(fwd) if len(fwd) > 5 else None}
        print(f"  ARM {name:26s} n={arms[name]['all']['n']:4d} "
              f"gross={arms[name]['all']['mean_r']:+.4f} "
              f"dbCI={arms[name]['day_block_all']['ci95'] if arms[name]['day_block_all'] else None}")
    res["arms_gross"] = arms

    # ---- cost, through the ratified authority
    from src.costs import load_broker_true_costs, cost_r
    BT = load_broker_true_costs()

    def _f(x):
        return None if x is None else (float(x.value) if hasattr(x, "value") else float(x))

    def charge(rows):
        priced, unpriced = [], collections.Counter()
        for r in rows:
            try:
                b = cost_r(r["symbol"], "FTMO", max(0.25, r["hold_hours"]),
                           sl_distance_price=r["sl_distance_price"], entry_price=r["entry_price"],
                           side="LONG" if r["direction"] > 0 else "SHORT",
                           entry_utc=dt.datetime.fromisoformat(r["entry_utc"]), costs=BT)
            except Exception as e:
                unpriced[f'{r["symbol"]}:{type(e).__name__}'] += 1
                continue
            c = _f(b.total_r)
            priced.append({**r, "cost_r": c, "r_net": r["r_gross"] - c, "swap_r": _f(b.swap_r)})
        return priced, unpriced

    costed = {}
    for name in ("A0_LIVE_BTC_DASH", "A1_BTC_DASH_ETH", "A_BTC_ETH", "BTC_only", "ETH_only"):
        rows = [r for s in ARMS[name] for r in rows_by_sym.get(s, [])]
        priced, unpriced = charge(rows)
        pre = [r for r in priced if r["entry_utc"][:4] < "2025"]
        fwd = [r for r in priced if r["entry_utc"][:4] >= "2025"]
        cell = {
            "n_walked": len(rows), "n_priced": len(priced),
            "coverage": round(len(priced) / len(rows), 4) if rows else None,
            "unpriced": dict(unpriced),
            "gross": round(mean([r["r_gross"] for r in priced]), 5) if priced else None,
            "cost": round(mean([r["cost_r"] for r in priced]), 5) if priced else None,
            "swap_share": (round(mean([r["swap_r"] for r in priced])
                                 / mean([r["cost_r"] for r in priced]), 4)
                           if priced and mean([r["cost_r"] for r in priced]) else None),
            "net": round(mean([r["r_net"] for r in priced]), 5) if priced else None,
            "day_block_net_all": day_block_boot(priced, key=lambda r: r["r_net"]) if priced else None,
            "day_block_net_pre2025": (day_block_boot(pre, key=lambda r: r["r_net"])
                                      if len(pre) > 5 else None),
            "day_block_net_2025plus": (day_block_boot(fwd, key=lambda r: r["r_net"])
                                       if len(fwd) > 5 else None),
        }
        costed[name] = cell
        print(f"  COST {name:22s} cov={cell['coverage']} net={cell['net']} "
              f"dbCI={cell['day_block_net_all']['ci95'] if cell['day_block_net_all'] else None}")
    res["arms_cost_charged"] = costed

    json.dump(res, open(OUT / "B7_VERIFY_CRYPTO.json", "w"), indent=1)
    print(f"crypto part done in {time.time()-t0:.0f}s")
    json.dump({s: rows_by_sym.get(s, []) for s in CRYPTO9},
              gzip.open(OUT / "B7_CRYPTO_ROWS.json.gz", "wt"))
    return res, rows_by_sym, series, atrs_all


if __name__ == "__main__":
    main()
