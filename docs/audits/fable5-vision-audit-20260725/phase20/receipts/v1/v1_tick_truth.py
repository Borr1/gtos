#!/usr/bin/env python3
"""ATTACK the quote-side repair with REAL BID/ASK TICKS, not with its own reasoning.

Ground truth is a tick-level round trip that transacts on the side of the book the live
engine transacts on (`execution.py:3247` entry, `:6953` exit). It is compared against
BOTH bar-walk conventions on the SAME archive bars the estate uses.

If the repair is right, the corrected arm's bias against tick truth is ~0 and the
uncorrected arm's is ~ -(spread/stop_dist). If the sign is flipped anywhere the corrected
arm will be WORSE than the uncorrected one on one direction and better on the other.
Reported per direction, on purpose — that is where a sign trap hides.
"""
from __future__ import annotations
import csv, datetime as dt, glob, gzip, json, math, os, statistics, sys, time
from pathlib import Path
import numpy as np

REPO = Path(os.environ.get("V1_REPO", "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"))
sys.path.insert(0, str(REPO)); os.chdir(REPO)

from src.utils.broker_clock import broker_epoch_to_utc, resolve_rule           # noqa: E402
from src.components.ultimate_book.primitives import Bar, atr14                 # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy                    # noqa: E402
from src.research_infra.walkforward.quote_side import BarQuote, walk           # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource           # noqa: E402

TICKS = Path("/Users/borr/GTOSActive/vps-ticks-20260726/ftmo")
BARS  = Path("/Users/borr/GTOSActive/vps-bars-20260727")
SYMS  = os.environ.get("V1_TSYMS", "EURUSD,XAUUSD,BTCUSD,GER40,USOIL_cash,USDJPY").split(",")
TARGET_R = float(os.environ.get("V1_T", "2.0"))
MAXBARS  = int(os.environ.get("V1_MB", "80"))
RULE = resolve_rule("FTMO-Server3")
M15 = 900


def load_ticks(sym):
    p = TICKS / f"FTMO_{sym}_ticks_20260618_to_20260726.csv.gz"
    if not p.is_file():
        return None
    ts, bids, asks = [], [], []
    with gzip.open(p, "rt") as fh:
        for row in csv.DictReader(fh):
            b = float(row["bid"]); a = float(row["ask"])
            if not (a > 0 and b > 0 and a >= b):
                continue
            ts.append(float(row["time_msc"]) / 1000.0); bids.append(b); asks.append(a)
    if not ts:
        return None
    t = np.asarray(ts); b = np.asarray(bids); a = np.asarray(asks)
    o = np.argsort(t, kind="stable")
    return t[o], b[o], a[o]


def load_bars(sym):
    p = BARS / f"FTMO_{sym}_M15.csv.gz"
    if not p.is_file():
        return None
    src = CsvBarSource({(sym, 16385): str(p)}, label="v1-tick-truth")
    rows = src._load((sym, 16385))
    bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
    times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
    return bars, times


def main() -> int:
    out = {}
    for sym in SYMS:
        t0 = time.time()
        tk = load_ticks(sym)
        bb = load_bars(sym)
        if tk is None or bb is None:
            out[sym] = {"skip": "no ticks" if tk is None else "no bars"}; continue
        tt, tb, ta = tk
        bars, times = bb
        # tick epochs are BROKER wall clock -> true UTC (the sidecar's whole point)
        t_utc = np.array([broker_epoch_to_utc(x, RULE).timestamp() for x in tt])
        lo_utc, hi_utc = t_utc[0], t_utc[-1]
        bt = np.array([x.timestamp() for x in times])
        # bars fully inside the tick window, leaving room for the horizon
        ok = np.nonzero((bt >= lo_utc) & (bt + (MAXBARS + 2) * M15 <= hi_utc))[0]
        if len(ok) == 0:
            out[sym] = {"skip": "no overlap"}; continue

        # --- archive identity control: bar close == last bid tick of the bar
        ident_n = ident_ok = 0
        idc = []
        # --- the experiment
        rows = {1: [], -1: []}
        reason_agree = {1: [0, 0], -1: [0, 0]}
        exit_spread = {1: [], -1: []}
        entry_spread = {1: [], -1: []}
        for bi in ok:
            i = int(bi)
            if i < 20:
                continue
            sd = atr14(bars, i)
            if not (sd > 0):
                continue
            close_t = bt[i] + M15            # bar labelled by its OPEN; closes one period later
            j = int(np.searchsorted(t_utc, close_t, side="right")) - 1
            if j < 0 or t_utc[j] < bt[i]:
                continue
            spread = float(ta[j] - tb[j])
            if not (spread > 0):
                continue
            ident_n += 1
            if abs(float(tb[j]) - bars[i].c) <= 1e-12 * max(1.0, abs(bars[i].c)):
                ident_ok += 1
            else:
                idc.append((float(tb[j]) - bars[i].c) / spread)
            end_t = bt[i] + (MAXBARS + 1) * M15
            k = int(np.searchsorted(t_utc, end_t, side="right"))
            if k <= j + 1:
                continue
            sb = tb[j + 1:k]; sa = ta[j + 1:k]
            for d in (1, -1):
                entry = float(ta[j]) if d > 0 else float(tb[j])
                stop = entry - d * sd
                tgt = entry + d * TARGET_R * sd
                if d > 0:
                    hs = sb <= stop; ht = sb >= tgt
                else:
                    hs = sa >= stop; ht = sa <= tgt
                iss = int(np.argmax(hs)) if hs.any() else None
                it = int(np.argmax(ht)) if ht.any() else None
                kex = None
                if iss is not None and (it is None or iss <= it):
                    kex = iss
                elif it is not None:
                    kex = it
                if kex is not None:
                    exit_spread[d].append(float(sa[kex] - sb[kex]))
                    entry_spread[d].append(spread)
                if iss is not None and (it is None or iss <= it):
                    # `truth_level` fills at the level (the bar walk's own convention, so
                    # the comparison isolates the quote side); `truth_touch` fills at the
                    # quote that actually breached, which also carries gap/slippage.
                    r_true, why_true = -1.0, "stop"
                    q = float(sb[iss]) if d > 0 else float(sa[iss])
                    r_touch = d * (q - entry) / sd
                elif it is not None:
                    r_true, why_true = TARGET_R, "target"
                    q = float(sb[it]) if d > 0 else float(sa[it])
                    r_touch = d * (q - entry) / sd
                else:
                    q = float(sb[-1]) if d > 0 else float(sa[-1])
                    r_true, why_true = d * (q - entry) / sd, "maxbars"
                    r_touch = r_true
                pol = ExitPolicy(target_dist=TARGET_R * sd, maxbars=MAXBARS)
                w = walk(bars, i, d, stop_dist=sd, spread=spread,
                         bar_quote=BarQuote.BID, policy=pol)
                rows[d].append((r_true, w.corrected.r_gross, w.uncorrected.r_gross,
                                spread / sd, r_touch))
                reason_agree[d][0] += int(w.corrected.exit_reason == why_true)
                reason_agree[d][1] += int(w.uncorrected.exit_reason == why_true)

        def summ(v):
            n = len(v)
            if not n:
                return {"n": 0}
            tr = [x[0] for x in v]; co = [x[1] for x in v]; un = [x[2] for x in v]
            dc = [x[1] - x[0] for x in v]; du = [x[2] - x[0] for x in v]
            sr = [x[3] for x in v]; th = [x[4] for x in v]
            dct = [x[1] - x[4] for x in v]; dut = [x[2] - x[4] for x in v]
            return {
                "n": n,
                "r_tick_truth_touchfill": round(statistics.fmean(th), 6),
                "bias_corrected_vs_touchfill": round(statistics.fmean(dct), 6),
                "bias_uncorrected_vs_touchfill": round(statistics.fmean(dut), 6),
                "r_tick_truth": round(statistics.fmean(tr), 6),
                "r_corrected": round(statistics.fmean(co), 6),
                "r_uncorrected": round(statistics.fmean(un), 6),
                "bias_corrected": round(statistics.fmean(dc), 6),
                "bias_uncorrected": round(statistics.fmean(du), 6),
                "se_bias_corrected": round(statistics.pstdev(dc) / math.sqrt(n), 6),
                "se_bias_uncorrected": round(statistics.pstdev(du) / math.sqrt(n), 6),
                "mae_corrected": round(statistics.fmean([abs(x) for x in dc]), 6),
                "mae_uncorrected": round(statistics.fmean([abs(x) for x in du]), 6),
                "spread_over_stop_median": round(statistics.median(sr), 6),
            }

        both = rows[1] + rows[-1]
        out[sym] = {
            "archive_bid_identity": {"n": ident_n, "exact_close_eq_last_bid": ident_ok,
                                     "rate": round(ident_ok / ident_n, 6) if ident_n else None,
                                     "worst_mismatch_in_spreads":
                                         round(max((abs(x) for x in idc), default=0.0), 6)},
            "LONG": summ(rows[1]), "SHORT": summ(rows[-1]), "BOTH": summ(both),
            "spread_at_exit_vs_entry": {
                k: ({"n": len(exit_spread[v]),
                     "mean_entry_spread": round(statistics.fmean(entry_spread[v]), 8),
                     "mean_exit_spread": round(statistics.fmean(exit_spread[v]), 8),
                     "ratio": round(statistics.fmean(exit_spread[v]) /
                                    statistics.fmean(entry_spread[v]), 4)}
                    if exit_spread[v] else {"n": 0})
                for k, v in (("LONG", 1), ("SHORT", -1))},
            "exit_reason_agreement": {
                "LONG": {"corrected": reason_agree[1][0], "uncorrected": reason_agree[1][1],
                         "n": len(rows[1])},
                "SHORT": {"corrected": reason_agree[-1][0], "uncorrected": reason_agree[-1][1],
                          "n": len(rows[-1])}},
            "elapsed_s": round(time.time() - t0, 1),
        }
        print(f"{sym:12s} n={out[sym]['BOTH']['n']:6d} "
              f"bias_corr={out[sym]['BOTH']['bias_corrected']:+.5f} "
              f"bias_uncorr={out[sym]['BOTH']['bias_uncorrected']:+.5f} "
              f"({out[sym]['elapsed_s']}s)", flush=True)

    dest = os.environ.get("V1_OUT", "/tmp/v1_tick_truth.json")
    json.dump({"contract": {"target_r": TARGET_R, "maxbars": MAXBARS,
                            "tape": "vps-bars-20260727 FTMO M15 (true UTC)",
                            "ticks": "vps-ticks-20260726 FTMO, broker epoch -> true UTC",
                            "entry": "last tick of the decision bar; LONG pays ask, SHORT hits bid",
                            "exit": "LONG on bid, SHORT on ask; stop wins ties"},
               "per_symbol": out}, open(dest, "w"), indent=1)
    print("WROTE", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
