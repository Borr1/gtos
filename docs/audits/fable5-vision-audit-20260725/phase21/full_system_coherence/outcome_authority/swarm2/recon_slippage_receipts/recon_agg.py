"""Aggregate the per-leg tick measurement into the adjudicated slippage table."""
import pandas as pd, numpy as np, json, gzip, pickle
OUT = '/Users/borr/.claude/jobs/adb9e69b/tmp/recon_out'
rng = np.random.default_rng(20260812)
D = pd.read_pickle(f'{OUT}/recon_legs.pkl')


def boot_ci(v, days, B=4000):
    """Cluster bootstrap on trading day."""
    v = np.asarray(v, float); days = np.asarray(days)
    if len(v) < 5: return [float('nan')] * 2
    ud = pd.unique(days); idx = {d: np.where(days == d)[0] for d in ud}
    means = np.empty(B)
    for b in range(B):
        pick = rng.choice(len(ud), len(ud), replace=True)
        sel = np.concatenate([idx[ud[p]] for p in pick])
        means[b] = v[sel].mean()
    return [float(np.quantile(means, .025)), float(np.quantile(means, .975))]


def desc(v, days=None, ci=False):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    if len(v) == 0: return None
    d = dict(n=int(len(v)), mean=float(v.mean()), median=float(np.median(v)),
             p95=float(np.quantile(v, .95)), p99=float(np.quantile(v, .99)),
             frac_adverse=float((v > 1e-9).mean()))
    if ci and days is not None: d['CI95'] = boot_ci(v, days[:len(v)])
    return d


R = {'schema': 'recon_slippage_adjudication_v1',
     'window': '2026-06-18..2026-07-24 (tick archive extent)',
     'population': 'sealed labeller MARKET resolved rows, orig arm, all 5 sealed months',
     'sign_convention': '+ve = engine booked price is BETTER than achievable = ENGINE OPTIMISM (a cost)',
     'n_rows_measured': int(len(D)),
     'state_counts': {k: int(v) for k, v in D.state.value_counts().items()}}

# ---------- ENTRY leg ----------
e = D.dropna(subset=['entry_opt_r'])
R['entry_leg'] = desc(e.entry_opt_r.values, e.day.values, ci=True)

# ---------- EXIT legs ----------
for st in ['STOP', 'TARGET', 'TIME_STOP']:
    s = D[(D.state == st) & (D.get('found_cross') == 1)]
    R[f'exit_{st}'] = {
        'at_crossing_tick': desc(s.exit_opt_at_cross_r.values, s.day.values, ci=True),
        'at_next_tick': desc(s.exit_opt_next_tick_r.values, s.day.values, ci=True),
        'n_state_rows': int((D.state == st).sum()),
        'n_resolved_from_ticks': int(len(s)),
    }
R['crossing_resolution'] = {
    st: dict(n=int((D.state == st).sum()),
             found=int(((D.state == st) & (D.get('found_cross') == 1)).sum()))
    for st in ['STOP', 'TARGET', 'TIME_STOP']}

# ---------- composition to a per-resolved-trade charge ----------
n_all = len(D)
shares = {st: float((D.state == st).mean()) for st in ['STOP', 'TARGET', 'TIME_STOP']}
stop = D[(D.state == 'STOP') & (D.found_cross == 1)]
comp = {}
for lab, col in [('at_crossing_tick', 'exit_opt_at_cross_r'), ('at_next_tick', 'exit_opt_next_tick_r')]:
    stop_mean = float(stop[col].mean())
    # target: a TP resting limit fills AT its level -> zero slippage, credit correctly declined
    # time stop: engine marks an executable exit-side close; measured drift below
    ts = D[(D.state == 'TIME_STOP') & (D.found_cross == 1)]
    ts_mean = float(ts[col].mean()) if len(ts) else 0.0
    entry_mean = float(e.entry_opt_r.mean())
    comp[lab] = dict(
        stop_leg_conditional=stop_mean,
        stop_share=shares['STOP'],
        stop_leg_per_resolved_trade=stop_mean * shares['STOP'],
        target_leg_per_resolved_trade=0.0,
        time_stop_leg_conditional=ts_mean,
        time_stop_leg_per_resolved_trade=ts_mean * shares['TIME_STOP'],
        entry_leg_per_resolved_trade=entry_mean,
        TOTAL_round_trip_per_resolved_trade=(stop_mean * shares['STOP']
                                             + ts_mean * shares['TIME_STOP'] + entry_mean),
        EXIT_ONLY_per_resolved_trade=stop_mean * shares['STOP'] + ts_mean * shares['TIME_STOP'])
R['state_shares_in_window'] = shares
R['composition'] = comp
R['charged_by_estate'] = 0.02

# ---------- by symbol / by hour, stop leg ----------
R['stop_leg_by_symbol'] = {k: dict(n=int(len(g)), mean=float(g.exit_opt_at_cross_r.mean()),
                                   median=float(g.exit_opt_at_cross_r.median()),
                                   p95=float(g.exit_opt_at_cross_r.quantile(.95)),
                                   p99=float(g.exit_opt_at_cross_r.quantile(.99)),
                                   frac_adverse=float((g.exit_opt_at_cross_r > 1e-9).mean()))
                           for k, g in stop.groupby('symbol')}
R['stop_leg_by_hour'] = {int(k): dict(n=int(len(g)), mean=float(g.exit_opt_at_cross_r.mean()),
                                      p95=float(g.exit_opt_at_cross_r.quantile(.95)))
                         for k, g in stop.groupby('hour')}
# per-resolved-trade round trip by symbol (what a book actually pays)
rt = []
for sym, g in D.groupby('symbol'):
    gs = g[(g.state == 'STOP') & (g.found_cross == 1)]
    gt = g[(g.state == 'TIME_STOP') & (g.found_cross == 1)]
    if len(gs) < 20: continue
    v = (gs.exit_opt_at_cross_r.mean() * (g.state == 'STOP').mean()
         + (gt.exit_opt_at_cross_r.mean() if len(gt) else 0) * (g.state == 'TIME_STOP').mean()
         + g.entry_opt_r.mean())
    rt.append((sym, int(len(g)), float(v)))
R['round_trip_by_symbol'] = {s: dict(n=n, total_r=v) for s, n, v in sorted(rt, key=lambda x: -x[2])}

json.dump(R, open(f'{OUT}/RECON_SLIPPAGE_TRUTH_V1.json', 'w'), indent=1)
print(json.dumps({k: R[k] for k in ('n_rows_measured', 'state_counts', 'state_shares_in_window',
                                    'entry_leg', 'crossing_resolution', 'composition')}, indent=1))
print('\n=== EXIT LEGS ===')
for st in ['STOP', 'TARGET', 'TIME_STOP']:
    print(st, json.dumps(R[f'exit_{st}'], indent=1))
