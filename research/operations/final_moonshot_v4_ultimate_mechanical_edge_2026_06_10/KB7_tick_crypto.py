"""KB7 — tick-measured execution truth for the CRYPTO sleeve (the #1 book contributor, 35.6%).

The book's crypto erosion is the M1 estimate -0.030R. Crypto is the largest EV contributor, so it
must be confirmed against REAL bid/ask ticks. The earlier KB7 docstring claimed crypto
copy_ticks_range hangs; re-probed 2026-06-15 the bridge serves BTCUSD (28k-35k ticks/window, fast)
and DASHUSD (thinner but present) for 2024+ -> crypto IS tick-serviceable now.

Sleeve (TW.crypto_sleeve): BTCUSD + DASHUSD Donchian-20 breakout + ac60>=0.15, sd=2*ATR. Deploy
exit = target4 (single fixed 4*sd target, 1*sd stop) + H1->M15 cascade limit entry. Forward-only
LTF (cascade fills 2025-06+).

Method (no lookahead; entries unchanged):
  entry : cascade LIMIT (H1 then M15 leg) at sc -/+ 1*ATR_LTF. Limit fills at the limit price the
          instant the correct tick quote touches it within the 12h cascade window; else H4 market
          fallback at first tick after signal close (long ASK, short BID).
  exit  : single fixed target 4*sd (limit fill on closing quote) + 1*sd structural stop (real
          crossing quote). Pessimistic: stop tested before target on each tick.
  horizon: 80 H4 bars wall-clock from signal close.

modeled         : book cascade R (target4), cost-map net (crypto 0.0953R).   [reference]
tick_costmap    : tick fills - same cost map -> apples (spread ~twice -> erosion UPPER bound).
tick_real       : tick fills, real spread already in fills, commission residual 0 -> honest live.
"""
from __future__ import annotations
import sys, json, collections
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import multitf_lib as mtf
import TW_mtf_cascade_transfer as TW
import KB7_tick_lib as TK

DATA = str(ROOT) + "/data/mt5_research_exports"
mtf.LTF_PATHS.update({
    ("BTCUSD", "H1"):  [DATA + "/bridge_ftmo_htf_20250601_20260610/BTCUSD_H1.csv"],
    ("BTCUSD", "M15"): [DATA + "/bridge_ftmo_m15_20250601_20260610/BTCUSD_M15.csv"],
    ("DASHUSD", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/DASHUSD_H1.csv"],
    ("DASHUSD", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/DASHUSD_M15.csv"],
})

TICK_SYMS = {"BTCUSD", "DASHUSD"}
COMMISSION_R = {s: 0.0 for s in TICK_SYMS}
WALL_MIN_H4 = 80 * 4 * 60
TGT = 4.0


def wins(r): return max(-1.3, min(5.0, r))
def _ts_ms(dt): return int(dt.timestamp() * 1000)


def tick_single_target(ts, start_i, entry_px, d, sd, tgt_R, stop_R, end_ms):
    """Single fixed-target tick exit: long sells at BID (target & stop), short buys at ASK.
    stop first (pessimistic)."""
    n = len(ts); j = start_i + 1
    stop_px = entry_px + d * stop_R * sd
    tgt_px = entry_px + d * tgt_R * sd
    while j < n and ts.ms[j] <= end_ms:
        cq = ts.bid[j] if d > 0 else ts.ask[j]
        if (d > 0 and cq <= stop_px) or (d < 0 and cq >= stop_px):
            return dict(R=d * (cq - entry_px) / sd, reason="stop", exit_i=j)
        if (d > 0 and cq >= tgt_px) or (d < 0 and cq <= tgt_px):
            return dict(R=d * (tgt_px - entry_px) / sd, reason="target", exit_i=j)
        j += 1
    last = min(j, n - 1)
    cq = ts.bid[last] if d > 0 else ts.ask[last]
    return dict(R=d * (cq - entry_px) / sd, reason="market_close", exit_i=last)


def reconcile_crypto_tick():
    ents = TW.crypto_sleeve()
    rows = []
    for e in ents:
        sym = e['sym']
        if sym not in TICK_SYMS:
            continue
        B_h4 = e['B']; Th4 = e['T']; i = e['i']; d = e['d']; sd = e['sd']
        vr = e['vr']; cost = e['cost']; year = e['year']; date = e['date']
        sc = B_h4[i].c
        sig_close = Th4[i] + timedelta(hours=4)
        if sig_close.tzinfo is None:
            sig_close = sig_close.replace(tzinfo=timezone.utc)
        # modeled cascade R (target4)
        casc_modeled = wins(simulate(B_h4, i, d, stop_dist=sd, target_dist=TGT * sd,
                                     cost=cost, maxbars=80)); src = "h4"
        limit_px = None; filled = False
        T1, B1 = mtf.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = mtf.load_ltf(sym, "M15"); have15 = len(B15) > 50
        if have1:
            sidx = mtf.first_ltf_index_after(T1, sig_close.replace(tzinfo=None))
            if sidx is not None and 30 <= sidx < len(B1) - 2:
                ej = TW.find_fill(B1, sidx, d, sc, TW.W_H1, TW.MI)
                if ej is not None:
                    casc_modeled = wins(simulate(B1, ej, d, stop_dist=sd, target_dist=TGT * sd,
                                                 cost=cost, maxbars=TW.H1_MAXBARS))
                    a1 = atr14(B1, sidx); limit_px = (sc - TW.MI * a1 if d > 0 else sc + TW.MI * a1)
                    filled = True; src = "h1"
        if not filled and have15:
            sidx = mtf.first_ltf_index_after(T15, sig_close.replace(tzinfo=None))
            if sidx is not None and 30 <= sidx < len(B15) - 2:
                ej = TW.find_fill(B15, sidx, d, sc, TW.W_M15, TW.MI)
                if ej is not None:
                    casc_modeled = wins(simulate(B15, ej, d, stop_dist=sd, target_dist=TGT * sd,
                                                 cost=cost, maxbars=TW.M15_MAXBARS))
                    a1 = atr14(B15, sidx); limit_px = (sc - TW.MI * a1 if d > 0 else sc + TW.MI * a1)
                    filled = True; src = "m15"
        horizon_end = sig_close + timedelta(minutes=WALL_MIN_H4)
        pull_end = min(horizon_end, sig_close + timedelta(days=20))
        import time as _t; _t0 = _t.time()
        ts = TK.load_window_stream(sym, sig_close - timedelta(minutes=5), pull_end)
        print(f"  crypto {sym} {date}: nticks={0 if ts is None else len(ts)} "
              f"({_t.time()-_t0:.1f}s)", flush=True)
        if ts is None:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                             modeled=round(casc_modeled, 4), covered=False, reason="no_tick"))
            continue
        si0 = ts.first_at_or_after(_ts_ms(sig_close))
        if si0 is None or si0 >= len(ts) - 5:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                             modeled=round(casc_modeled, 4), covered=False, reason="no_tick_at_entry"))
            continue
        no_fill = False
        if filled and limit_px is not None:
            casc_end_ms = _ts_ms(sig_close + timedelta(hours=12))
            fill_i = None; j = si0
            while j < len(ts) and ts.ms[j] <= casc_end_ms:
                q = ts.ask[j] if d > 0 else ts.bid[j]
                if (d > 0 and q <= limit_px) or (d < 0 and q >= limit_px):
                    fill_i = j; break
                j += 1
            if fill_i is None:
                no_fill = True
                entry_px = ts.ask[si0] if d > 0 else ts.bid[si0]; fill_i = si0
            else:
                entry_px = limit_px
        else:
            entry_px = ts.ask[si0] if d > 0 else ts.bid[si0]; fill_i = si0
        end_ms = _ts_ms(horizon_end)
        res = tick_single_target(ts, fill_i, entry_px, d, sd, TGT, -1.0, end_ms)
        gross = res['R']
        tick_costmap = wins(gross - cost)
        tick_real = wins(gross - COMMISSION_R.get(sym, 0.0))
        half_sp = (ts.ask[si0] - ts.bid[si0]) / 2.0
        entry_spread_R = (half_sp * 2.0) / sd if sd > 0 else 0.0
        rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                         modeled=round(casc_modeled, 4), tick_costmap=round(tick_costmap, 4),
                         tick_real=round(tick_real, 4), entry_spread_R=round(entry_spread_R, 4),
                         reason=res['reason'], covered=True, cascade_no_fill=no_fill,
                         n_ticks=len(ts)))
    return rows


def block(rs, key):
    rs = [r for r in rs if r.get('covered')]
    if not rs: return None
    mod = [r['modeled'] for r in rs]; tk = [r[key] for r in rs]
    ero = [r[key] - r['modeled'] for r in rs]
    esr = [r.get('entry_spread_R', 0.0) for r in rs]
    return dict(n=len(rs), modeled_ev=round(sum(mod) / len(mod), 4),
                tick_ev=round(sum(tk) / len(tk), 4),
                erosion_ev=round(sum(ero) / len(ero), 4),
                tick_win=round(100 * sum(1 for x in tk if x > 0) / len(rs), 1),
                worst_erosion=round(min(ero), 4),
                mean_entry_spread_R=round(sum(esr) / len(esr), 4))


def summarize(rows, name):
    cov = [r for r in rows if r.get('covered')]
    out = {"sleeve": name, "n_total": len(rows), "n_covered": len(cov),
           "n_uncovered": len(rows) - len(cov),
           "costmap": block(cov, "tick_costmap"), "realspread": block(cov, "tick_real")}
    for y in (2024, 2025, 2026):
        b = block([r for r in cov if r['year'] == y], "tick_costmap")
        if b: out[f"y{y}_costmap"] = b
        br = block([r for r in cov if r['year'] == y], "tick_real")
        if br: out[f"y{y}_real"] = br
    bysym = collections.defaultdict(list)
    for r in cov: bysym[r['sym']].append(r)
    out["per_symbol_costmap"] = {s: block(rs, "tick_costmap") for s, rs in sorted(bysym.items())}
    out["per_symbol_real"] = {s: block(rs, "tick_real") for s, rs in sorted(bysym.items())}
    return out


if __name__ == "__main__":
    print("=== crypto (tick) ===", flush=True)
    rc = reconcile_crypto_tick()
    res = {"crypto": summarize(rc, "crypto")}
    print("costmap:", json.dumps(res["crypto"].get("costmap")), flush=True)
    print("real   :", json.dumps(res["crypto"].get("realspread")), flush=True)
    with open(HERE / "KB7_TICK_CRYPTO_RESULT.json", "w") as f:
        json.dump(res, f, indent=1)
    with open(HERE / "KB7_TICK_CRYPTO_LEDGER.jsonl", "w") as f:
        for r in rc:
            r2 = dict(r); r2["sleeve"] = "crypto"; f.write(json.dumps(r2) + "\n")
    print("WROTE KB7_TICK_CRYPTO_RESULT.json + LEDGER", flush=True)
