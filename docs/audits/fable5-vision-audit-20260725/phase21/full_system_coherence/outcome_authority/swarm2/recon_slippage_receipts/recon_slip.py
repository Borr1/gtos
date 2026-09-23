"""RECON: definitive per-leg slippage from ticks, measured against the SEALED labeller's own bookings.

Frame: for every row the engine resolved (orig arm, MARKET), recover the price the engine BOOKED
at each leg, then ask the tick tape what was actually achievable at that instant.
Sign convention throughout: +ve = the engine's booked price is BETTER than achievable = ENGINE OPTIMISM.
"""
import pandas as pd, numpy as np, gzip, pickle, os, json, sys

TICK = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
MAP = {'NAS100': 'US100_cash', 'SPX500': 'US500_cash', 'GER40': 'GER40_cash',
       'JP225': 'JP225_cash', 'UK100': 'UK100_cash'}
OUT = '/Users/borr/.claude/jobs/adb9e69b/tmp/recon_out'
os.makedirs(OUT, exist_ok=True)


def to_utc(sec):
    """Broker wall clock -> UTC via new_york_plus_7 (declared rule, timebase sidecar)."""
    bn = pd.to_datetime(sec, unit="s")
    return (bn - pd.Timedelta(hours=7)).dt.tz_localize(
        "America/New_York", ambiguous=False, nonexistent="shift_forward").dt.tz_convert("UTC")


# ---------- 1. population: the sealed labeller's own resolved rows ----------
rows = []
for m in ['feb', 'apr', 'may', 'jun', 'jul']:
    for r in pickle.load(gzip.open(f'/private/tmp/laneG-walk/lg_{m}.pkl.gz', 'rb')):
        o = r.get('orig') or {}
        if not o.get('fill_time') or o.get('gross') is None:
            continue
        rows.append(dict(month=m, symbol=r['symbol'], side=r['side'], family=r['family'],
                         day=r['day'], key=r['key'], order_type=r['order_type'],
                         entry=r['entry_price'], stop=r['stop_price'], target=r['target_price'],
                         risk=r['risk_price'], state=o.get('state'), status=o['status'],
                         gross=o['gross'], fill_price=o['fill_price'],
                         fill_time=o['fill_time'], term_time=o.get('terminal_time'),
                         model_spread=r.get('spread_at_fill_price'), slippage_r=r.get('slippage_r')))
c = pd.DataFrame(rows)
print("sealed resolved rows (all 5 months):", len(c), flush=True)
print("  order_type:", c.order_type.value_counts().to_dict(), flush=True)
print("  state     :", c.state.value_counts().to_dict(), flush=True)

c['ft'] = pd.to_datetime(c.fill_time, utc=True)
c['tt'] = pd.to_datetime(c.term_time, utc=True)
# engine's BOOKED exit price, recovered from the identity gross = d*(exit-fill)/risk
c['d'] = np.where(c.side == 'LONG', 1.0, -1.0)
c['booked_exit'] = c.fill_price + c.d * c.gross * c.risk

WIN0, WIN1 = pd.Timestamp('2026-06-18', tz='UTC'), pd.Timestamp('2026-07-24', tz='UTC')
cw = c[(c.ft >= WIN0) & (c.tt <= WIN1)].copy()
print(f"in tick window {WIN0.date()}..{WIN1.date()}: {len(cw)} of {len(c)} "
      f"({100*len(cw)/len(c):.1f}%)", flush=True)
print("  window state:", cw.state.value_counts().to_dict(), flush=True)

# ---------- 2. per-symbol tick pass ----------
res = []
for sym, g in cw.groupby('symbol'):
    bs = MAP.get(sym, sym)
    f = f"{TICK}/FTMO_{bs}_ticks_20260618_to_20260726.csv.gz"
    if not os.path.exists(f):
        print("  SKIP (no tick file)", sym, len(g), flush=True)
        continue
    t = pd.read_csv(f, usecols=['time_msc', 'bid', 'ask'])
    t['tu'] = to_utc(t.time_msc / 1000.0)
    t = t.sort_values('tu')
    t = t[(t.ask >= t.bid) & (t.bid > 0)]
    tv = t.tu.values.astype('datetime64[ns]')
    bid = t.bid.values.astype('float64')
    ask = t.ask.values.astype('float64')
    n_t = len(tv)

    out = []
    for r in g.itertuples():
        ftn = np.datetime64(r.ft.tz_localize(None))
        ttn = np.datetime64(r.tt.tz_localize(None))
        a = int(np.searchsorted(tv, ftn))
        z = int(np.searchsorted(tv, ttn, side='right'))
        z = min(z + 2, n_t)                       # +2 ticks past terminal for the next-tick fill
        if a >= n_t:
            continue
        d = r.d
        rec = dict(key=r.key, month=r.month, symbol=sym, family=r.family, side=r.side,
                   state=r.state, day=r.day, risk=r.risk, hour=int(r.ft.hour),
                   n_ticks=int(max(0, z - a)))

        # --- ENTRY leg: true entry-side quote at the booked fill instant
        ei = min(a, n_t - 1)
        true_entry = ask[ei] if d > 0 else bid[ei]
        rec['entry_opt_r'] = float(d * (true_entry - r.fill_price) / r.risk)
        rec['true_spread_r'] = float((ask[ei] - bid[ei]) / r.risk)
        rec['model_spread_r'] = float(r.model_spread / r.risk) if r.model_spread == r.model_spread else np.nan

        # --- EXIT leg
        if z > a and r.state in ('STOP', 'TARGET'):
            lvl = r.stop if r.state == 'STOP' else r.target
            ex = bid[a:z] if d > 0 else ask[a:z]
            # long stop / short stop: exit-side quote falls to (long) or rises to (short) the level
            cross = (ex <= lvl) if ((d > 0) == (r.state == 'STOP')) else (ex >= lvl)
            if cross.any():
                j = int(np.argmax(cross))
                rec['exit_opt_at_cross_r'] = float(d * (lvl - ex[j]) / r.risk)
                jn = min(j + 1, len(ex) - 1)
                rec['exit_opt_next_tick_r'] = float(d * (lvl - ex[jn]) / r.risk)
                rec['found_cross'] = 1
            else:
                rec['found_cross'] = 0
        elif z > a and r.state == 'TIME_STOP':
            # engine marks at last complete pre-horizon exit-side close; compare to the true
            # exit-side quote at the terminal instant
            ti = min(int(np.searchsorted(tv, ttn)), n_t - 1)
            true_exit = bid[ti] if d > 0 else ask[ti]
            rec['exit_opt_at_cross_r'] = float(d * (r.booked_exit - true_exit) / r.risk)
            rec['exit_opt_next_tick_r'] = rec['exit_opt_at_cross_r']
            rec['found_cross'] = 1
        out.append(rec)
    res.append(pd.DataFrame(out))
    print(f"  ok {sym:12s} n={len(out):6d}  ticks={n_t:>10,d}", flush=True)

D = pd.concat(res, ignore_index=True)
D.to_pickle(f'{OUT}/recon_legs.pkl')
print("\nMEASURED ROWS:", len(D), flush=True)
print(D.state.value_counts().to_dict(), flush=True)
