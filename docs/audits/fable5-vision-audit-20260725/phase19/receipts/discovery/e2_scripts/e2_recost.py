"""e2 — PORTABLE recost engine.

Reimplements l10x_07_bottomline.py's cost instrument exactly, but decoupled from the
January-only working set so the SAME instrument can be pointed at any month's pool.

Instrument (identical to l10x_06/07):
  risk_distance d   = |entry_price - stop_loss|                (price units)
  gross_r           = opportunity_net_proxy_r + cost_r         (fill-blind, cost-free path value)
  frozen spread_r   = pool field spread_r
  frozen total_r    = pool field expected_cost_r
  real spread_r     = TICK[sym].spread_bps_median * entry_price / 1e4 / d
  real comm_r       = COMM_px(sym, entry_price) / d
  real slip_r       = max(LIVE_slip_px(sym), 0) / d
  real total_r      = sum of the three                          (swap = 0 at the 2 h horizon)
  gate(spread, tot) = spread <= 0.10 AND tot <= 0.15            (broker_net_cost_engine:859-866, :923-927)

NOTE ON PORTABILITY: the tick-spread model is a single per-symbol bps constant measured on the
FTMO tick archive 2026-06-18..07-24. It is MONTH-INVARIANT by construction. Every month-to-month
change in real_cost_r therefore comes from row GEOMETRY (entry_price / risk_distance mix), never
from a spread that moved. That is a feature for this extension: it isolates geometry.
"""
import json, gzip, os, bisect, csv, statistics as st
from collections import defaultdict

D = '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
TICK = json.load(open(f'{D}/L10X_TICK_SPREAD_V1.json'))
LIVE = json.load(open(f'{D}/L10X_LIVE_COST_PRICEUNITS_V1.json'))

TMAP = {'XAUUSD':'XAUUSD','UK100':'UK100_cash','SPX500':'US500_cash','NAS100':'US100_cash','US30_cash':'US30_cash',
 'GBPUSD':'GBPUSD','GER40':'GER40_cash','JP225':'JP225_cash','USDCAD':'USDCAD','BTCUSD':'BTCUSD','EURJPY':'EURJPY',
 'ETHUSD':'ETHUSD','XAGUSD':'XAGUSD','USDCHF':'USDCHF','USDJPY':'USDJPY','EURGBP':'EURGBP','NZDUSD':'NZDUSD',
 'EURUSD':'EURUSD','UKOIL_cash':'UKOIL_cash','GBPJPY':'GBPJPY','AUDJPY':'AUDJPY','USOIL_cash':'USOIL_cash',
 'AUDUSD':'AUDUSD','CHFJPY':'CHFJPY'}
JPYC = 0.00808905
USDC = 5.00048e-05
COMM = {'EURUSD':USDC,'GBPUSD':USDC,'AUDUSD':USDC,'NZDUSD':USDC,'USDJPY':JPYC,'GBPJPY':JPYC,'EURJPY':JPYC,
 'AUDJPY':JPYC,'CHFJPY':JPYC,'XAUUSD':0.0576,'XAGUSD':0.001,'UK100':0.0,'SPX500':0.0,'NAS100':0.0,
 'US30_cash':0.0,'GER40':0.0,'JP225':0.0,'UKOIL_cash':0.0,'USOIL_cash':0.0,'EURGBP':USDC*0.74}
SLIPMAP = {'XAUUSD':'ftmo:XAUUSD','SPX500':'ftmo:US500.cash','US30_cash':'ftmo:US30.cash','UK100':'ftmo:UK100.cash',
 'GER40':'ftmo:GER40.cash','JP225':'ftmo:JP225.cash','BTCUSD':'ftmo:BTCUSD','ETHUSD':'ftmo:ETHUSD',
 'EURUSD':'ftmo:EURUSD','GBPUSD':'ftmo:GBPUSD','USDJPY':'ftmo:USDJPY','GBPJPY':'ftmo:GBPJPY'}
IDX = ['SPX500','NAS100','JP225','UK100','GER40','US30_cash']


def comm_px(sym, ep):
    """Commission in PRICE units. Byte-for-byte the l10x_07 expression."""
    return COMM.get(sym, USDC*ep if sym in ('USDCHF','USDCAD')
                    else (39.2778/88599.74*ep if sym == 'BTCUSD'
                          else (1.09905 if sym == 'ETHUSD' else 0.0)))


def born_state(m):
    if m is None: return 'UNANCHORED'
    return "born_past_stop" if m <= -1.0 else ("born_marketable" if m < 0.0 else ("born_at_limit" if m == 0.0 else "born_resting"))


def cost_row(sym, ep, d):
    tk = TICK.get('ftmo:' + TMAP.get(sym, sym))
    if not tk or not tk.get('spread_bps_median'): return None
    rspr = tk['spread_bps_median'] * ep / 1e4 / d
    rcm = comm_px(sym, ep) / d
    rsl = max(LIVE.get(SLIPMAP.get(sym, ''), {}).get('slip_px', 0.0) or 0.0, 0.0) / d
    return rspr, rcm, rsl


def gate(spr, tot):
    return (spr <= 0.10 + 1e-12) and (tot <= 0.15 + 1e-12)


def m_(v): return round(st.mean(v), 6) if v else None
def med_(v): return round(st.median(v), 6) if v else None


def book(rr):
    if not rr: return None
    return {'n': len(rr),
            'gross': m_([x['gross'] for x in rr]),
            'frozen_cost': m_([x['froz_tot'] for x in rr]),
            'real_cost': m_([x['rtot'] for x in rr]),
            'net_frozen': m_([x['gross'] - x['froz_tot'] for x in rr]),
            'net_real': m_([x['gross'] - x['rtot'] for x in rr])}


def build_rows(pool_path, anchor_map=None, precomputed=False):
    """precomputed=True => the file already carries risk_distance + gross_r (the w0 working set)."""
    rows, miss, unusable = [], defaultdict(int), 0
    for l in gzip.open(pool_path, 'rt'):
        r = json.loads(l)
        sym = r['symbol']; ep = r.get('entry_price')
        if precomputed:
            d = r['risk_distance']; gross = r['gross_r']
        else:
            sl = r.get('stop_loss')
            if ep is None or sl is None: unusable += 1; continue
            d = abs(float(ep) - float(sl))
            if not (d > 0): unusable += 1; continue
            onp = r.get('opportunity_net_proxy_r'); cr = r.get('cost_r')
            if onp is None or cr is None: unusable += 1; continue
            gross = round(float(onp) + float(cr), 9)
        c = cost_row(sym, ep, d)
        if c is None: miss[sym] += 1; continue
        rspr, rcm, rsl = c
        m = anchor_map.get((r['candidate_id'], r['decision_time_utc'])) if anchor_map is not None else None
        rows.append({'sym': sym, 'bs': born_state(m) if anchor_map is not None else 'NOANCHOR',
                     'gross': gross, 'froz_spr': r['spread_r'], 'froz_tot': r['expected_cost_r'],
                     'rspr': rspr, 'rcm': rcm, 'rsl': rsl, 'rtot': rspr + rcm + rsl,
                     'fam': r.get('origin_family'), 'sess': r.get('session_bucket'),
                     'day': (r.get('decision_time_utc') or '')[:10],
                     'hour': (r.get('decision_time_utc') or '')[11:13],
                     'rd': d, 'ep': ep})
    return rows, dict(miss), unusable


def load_anchor(path):
    a = {}
    for l in gzip.open(path, 'rt'):
        o = json.loads(l)
        a[(o['candidate_id'], o['decision_time_utc'])] = o.get('mkt_r_prev_close')
    return a


def full_report(rows, label):
    N = len(rows)
    tk = [x for x in rows if x['bs'] != 'born_past_stop']
    res = {'label': label, 'n': N, 'n_takeable_ex_past_stop': len(tk),
           'n_unanchored': sum(1 for x in rows if x['bs'] == 'UNANCHORED'),
           'anchored': rows[0]['bs'] != 'NOANCHOR' if rows else None}
    res['A_all_rows'] = book(rows)
    res['B_takeable_only'] = book(tk)
    res['C_takeable_at_frozen_gate'] = book([x for x in tk if gate(x['froz_spr'], x['froz_tot'])])
    dr = [x for x in tk if gate(x['rspr'], x['rtot'])]
    res['D_takeable_at_real_gate'] = book(dr)
    srt = sorted(dr, key=lambda x: x['rtot'])
    res['E_takeable_real_gate_cheapest_half'] = book(srt[:len(srt)//2])
    # headline: what correcting the cost model is worth, on ALL rows
    res['OVERCHARGE_R_PER_TRADE'] = round(res['A_all_rows']['frozen_cost'] - res['A_all_rows']['real_cost'], 6)
    res['OVERCHARGE_RATIO'] = round(res['A_all_rows']['frozen_cost'] / res['A_all_rows']['real_cost'], 4)
    res['GATE_PASS_FROZEN_ALLROWS'] = sum(1 for x in rows if gate(x['froz_spr'], x['froz_tot']))
    res['GATE_PASS_REAL_ALLROWS'] = sum(1 for x in rows if gate(x['rspr'], x['rtot']))
    ix = [x for x in rows if x['sym'] in IDX]
    res['INDEX_COMPLEX'] = {'symbols': IDX, 'n': len(ix), 'frac_of_pool': round(len(ix)/N, 4) if N else None,
        'n_pass_frozen': sum(1 for x in ix if gate(x['froz_spr'], x['froz_tot'])),
        'n_pass_real': sum(1 for x in ix if gate(x['rspr'], x['rtot'])),
        'gross_mean': m_([x['gross'] for x in ix]),
        'gross_mean_takeable': m_([x['gross'] for x in ix if x['bs'] != 'born_past_stop']),
        'real_cost_mean': m_([x['rtot'] for x in ix]), 'frozen_cost_mean': m_([x['froz_tot'] for x in ix]),
        'net_real_takeable': m_([x['gross']-x['rtot'] for x in ix if x['bs'] != 'born_past_stop'])}

    def grp(key, src):
        g = defaultdict(list)
        for x in src: g[x[key]].append(x)
        return {str(k): {'n': len(v), 'gross': m_([x['gross'] for x in v]),
                         'real_cost': m_([x['rtot'] for x in v]),
                         'frozen_cost': m_([x['froz_tot'] for x in v]),
                         'net_real': m_([x['gross']-x['rtot'] for x in v]),
                         'overcharge': round(m_([x['froz_tot'] for x in v]) - m_([x['rtot'] for x in v]), 6),
                         'n_pass_real_gate': sum(1 for x in v if gate(x['rspr'], x['rtot'])),
                         'n_pass_frozen_gate': sum(1 for x in v if gate(x['froz_spr'], x['froz_tot'])),
                         'median_rd_pct_of_price': med_([100.0*x['rd']/x['ep'] for x in v]) if v else None}
                for k, v in sorted(g.items(), key=lambda kv: -len(kv[1]))}

    res['per_symbol_takeable'] = grp('sym', tk)
    res['per_family_takeable'] = grp('fam', tk)
    res['per_symbol_all'] = grp('sym', rows)
    res['per_family_all'] = grp('fam', rows)
    res['per_session_all'] = grp('sess', rows)
    fam_rc = [v['real_cost'] for v in res['per_family_takeable'].values() if v['real_cost']]
    if fam_rc:
        res['FAMILY_REAL_COST_DISPERSION'] = {'min': min(fam_rc), 'max': max(fam_rc),
                                              'ratio': round(max(fam_rc)/min(fam_rc), 3), 'n_families': len(fam_rc)}
    bs = defaultdict(list)
    for x in rows: bs[x['bs']].append(x)
    res['BORN_CENSUS'] = {k: {'n': len(v), 'share': round(len(v)/N, 5), 'gross': m_([x['gross'] for x in v]),
                              'real_cost': m_([x['rtot'] for x in v]), 'frozen_cost': m_([x['froz_tot'] for x in v])}
                          for k, v in sorted(bs.items(), key=lambda kv: -len(kv[1]))}
    return res
