"""KB7 — tick-measured execution truth for the JPY breadth class (the most fill-sensitive sleeve).

The book's JPY proxy charges -0.05R erosion (M1 estimate). JPY is the tight-stop (1*ATR) low-win
(~36%) class where slippage bites hardest, so the proxy must be confirmed against REAL bid/ask ticks.

Coverage: USDJPY has an on-disk micro tick export (2025-10..2026-04). GBPJPY has no tick export and
is not on the bridge -> USDJPY-only direct measure; the per-fill slip mechanic transfers to GBPJPY
(same M15 R1 geometry, same JPY pip structure) the same way the M1 probe transferred it.

Method (no lookahead; entries unchanged from EXEC_REALISM_jpy_probe):
  entry  : R1 open-impulse M15 signal. Modeled enters at the M15 signal-bar CLOSE B[iw].c.
           Tick enters at the first tick AT/AFTER that close: long fills at ASK, short at BID.
  stop   : 1*ATR. long's protective SELL fills at the BID once BID<=stop_px; short's BUY at ASK
           once ASK>=stop_px. The real crossing quote already embeds gap+spread (no buffer guess).
  target : 2.5*ATR limit. long SELL fills at BID>=tgt; short BUY at ASK<=tgt (correct quote side).
  horizon: 48 M15 bars = 720 min wall-clock from entry.
  pessimism: stop (adverse) tested before target (favorable) on each tick.

Three numbers per trade:
  modeled       : book M15-bar R, net of jpy_fx cost map (0.1148R).  [reference]
  m1            : EXEC_REALISM M1 estimate (next-M1-open + 0.5*cost stop buffer).  [reference]
  tick_costmap  : tick fills, then subtract the SAME jpy_fx cost map -> apples vs modeled
                  (charges spread ~twice -> erosion UPPER BOUND).
  tick_real     : tick fills with the REAL observed spread (already in the ASK/BID fills), NO cost
                  map (jpy_fx is spread-only; commission residual ~0) -> the honest live number.
"""
from __future__ import annotations
import sys, json, collections, bisect
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import wave1_structure_setups_ict as w1
import kb2_new_breadth as nb
import KB7_tick_lib as TK

def wins(r): return max(-1.3, min(5.0, r))

JPY = ['USDJPY']           # tick-covered only; GBPJPY transfers
LW = 4; STOP_M = 1.0; TGT_M = 2.5; MAXBARS = 48
LONDON_HOUR = 8; NY_HOUR = 14
MICRO_START = datetime(2025, 10, 1, tzinfo=timezone.utc)
MICRO_END = datetime(2026, 4, 30, tzinfo=timezone.utc)


def jpy_signals(session_hour):
    out = []
    for sym in JPY:
        T, B, A = nb.load_m15(sym); cost = w1.cost_for(sym)
        byday = collections.defaultdict(list)
        for i, t in enumerate(T): byday[t.date()].append(i)
        for day, idxs in sorted(byday.items()):
            ses = [i for i in idxs if T[i].hour >= session_hour]
            if len(ses) < LW + 2: continue
            i0 = ses[0]; iw = ses[LW - 1]
            if i0 < 20: continue
            a = A[iw]
            if a <= 0: continue
            from geometry_lib import simulate
            imp = B[iw].c - B[i0].o
            d = 1 if imp > 0 else -1
            modeled = wins(simulate(B, iw, d, stop_dist=STOP_M * a, target_dist=TGT_M * a,
                                    maxbars=MAXBARS, cost=cost))
            entry_ts = T[iw] + timedelta(minutes=15)
            if entry_ts.tzinfo is None:
                entry_ts = entry_ts.replace(tzinfo=timezone.utc)
            out.append(dict(sym=sym, year=day.year, ts=entry_ts, d=d, sd=STOP_M * a,
                            tgt=TGT_M * a, entry_close=B[iw].c, modeled=modeled, cost=cost))
    return out


def tick_reconcile_jpy(sig):
    sym = sig['sym']; d = sig['d']; sd = sig['sd']; tgt = sig['tgt']; cost = sig['cost']
    ts0 = sig['ts']
    if ts0 < MICRO_START or ts0 > MICRO_END:
        return None
    horizon_end = ts0 + timedelta(minutes=MAXBARS * 15)
    stream = TK.load_window_stream(sym, ts0 - timedelta(minutes=2), horizon_end + timedelta(minutes=5))
    if stream is None or len(stream) < 5:
        return None
    si = stream.first_at_or_after(int(ts0.timestamp() * 1000))
    if si is None or si >= len(stream) - 5:
        return None
    # market entry: long ASK, short BID
    entry_px = stream.ask[si] if d > 0 else stream.bid[si]
    half_sp_entry = (stream.ask[si] - stream.bid[si]) / 2.0
    stop_px = entry_px - d * sd
    tgt_px = entry_px + d * tgt
    end_ms = int(horizon_end.timestamp() * 1000)
    R = None; reason = 'open'
    n = len(stream); j = si + 1
    while j < n and stream.ms[j] <= end_ms:
        # closing quote: long sells at BID, short buys at ASK
        cq = stream.bid[j] if d > 0 else stream.ask[j]
        # pessimistic: stop (adverse) first
        if (d > 0 and cq <= stop_px) or (d < 0 and cq >= stop_px):
            R = d * (cq - entry_px) / sd; reason = 'stop'; break
        # target limit on closing quote
        if (d > 0 and cq >= tgt_px) or (d < 0 and cq <= tgt_px):
            R = d * (tgt_px - entry_px) / sd; reason = 'target'; break
        j += 1
    if R is None:
        last = min(j, n - 1)
        cq = stream.bid[last] if d > 0 else stream.ask[last]
        R = d * (cq - entry_px) / sd; reason = 'market_close'
    tick_costmap = wins(R - cost)          # apples vs modeled (spread ~twice -> upper bound)
    tick_real = wins(R)                    # honest: spread already in fills, jpy spread-only
    entry_spread_R = (half_sp_entry * 2.0) / sd if sd > 0 else 0.0
    return dict(sym=sym, year=sig['year'], modeled=round(sig['modeled'], 4),
                tick_costmap=round(tick_costmap, 4), tick_real=round(tick_real, 4),
                entry_spread_R=round(entry_spread_R, 4), reason=reason, n_ticks=len(stream))


def block(rs, key):
    rs = [r for r in rs if r is not None]
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


def run(name, hr):
    sigs = jpy_signals(hr)
    rows = [r for s in sigs if (r := tick_reconcile_jpy(s)) is not None]
    res = {"sleeve": name, "n_signals": len(sigs), "n_tick": len(rows),
           "costmap": block(rows, "tick_costmap"), "realspread": block(rows, "tick_real")}
    for y in (2025, 2026):
        res[f"y{y}_costmap"] = block([r for r in rows if r['year'] == y], "tick_costmap")
        res[f"y{y}_real"] = block([r for r in rows if r['year'] == y], "tick_real")
    return res, rows


if __name__ == "__main__":
    out = {}; all_rows = []
    for name, hr in (("fx_jpy_london", LONDON_HOUR), ("fx_jpy_ny", NY_HOUR)):
        r, rows = run(name, hr); out[name] = r
        for x in rows:
            x2 = dict(x); x2['sleeve'] = name; all_rows.append(x2)
        print(f"=== {name} (hr={hr}) ===", flush=True)
        print("costmap :", json.dumps(r["costmap"]), flush=True)
        print("real    :", json.dumps(r["realspread"]), flush=True)
        print("y2025 cm:", json.dumps(r.get("y2025_costmap")), flush=True)
        print("y2026 cm:", json.dumps(r.get("y2026_costmap")), flush=True)
    with open(HERE / "KB7_TICK_JPY_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    with open(HERE / "KB7_TICK_JPY_LEDGER.jsonl", "w") as f:
        for r in all_rows: f.write(json.dumps(r) + "\n")
    print("WROTE KB7_TICK_JPY_RESULT.json + LEDGER", flush=True)
