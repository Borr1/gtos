"""CYCLE-59 — corrected aggressive sizing for the LIVE W7 book: DD-defense + STATIC floor + per-account.

Reconciles the c57 aggressive-sizing (which used a TAME 2-class core, TRAILING DD, fresh account) with
LIVE REALITY: the live W7 book (calibrated mean 0.10956 / std 0.75768 / min -1.634 — MORE volatile than my
2-class core min -0.88), the STATIC 90k floor (owner rule, not trailing), and the ACTUAL account states
(FN fresh 100k / 10% runway; FTMO 97.2k / 7.4% runway from the -2.87% legacy start). Extends the live
session's own validated MC engine (MC_LIVE_EQUITY_RERUN) with the DD-defense risk schedule the live held
1.25% for lack of — to answer the owner's "too conservative": how aggressive can the LIVE book safely go.

The live held 1.25% because WITHOUT DD-defense the dial degrades (live MC: 2%->pass 0.957/fail_dd 0.043).
DD-defense (de-risk ->0 near the static floor) holds fail_dd low at higher base -> the binding constraint
becomes the -5% DAILY limit (which the VOLATILE W7 book hits at a LOWER base than my tame core: worst day
= min_unit * base, min_unit ~ -1.634 -> daily breach near base 3.0%).
"""
import sys, json, statistics, random, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent

TARGET0 = 0.08; MAXDD = 0.10; DAILY = 0.05; BLOCK = 5; PATHCAP = 2000; N = 40000
MEAN = 0.10956; STD = 0.75768; NDAYS = 1679; VS = 0.7504
PT = 0.10; JSCALE = 3.0   # calibration from MC_LIVE_EQUITY_RERUN_RESULT.json


def build_series(pt=PT, jscale=JSCALE, seed=12345, ndays=NDAYS):
    rng = random.Random(seed); raw = []
    for _ in range(ndays):
        x = rng.gauss(0, 1)
        if rng.random() < pt:
            x += rng.expovariate(1.0) * jscale
        raw.append(x)
    mu = statistics.fmean(raw); sd = statistics.pstdev(raw)
    A = STD / sd; B = MEAN - A * mu
    return [A * r + B for r in raw]


def cap_mult(eq, dd_ref, mode):
    """DD-defense multiplier as a function of current equity (eq in NORMALIZED units of start_eq)."""
    dd = (dd_ref - eq) / dd_ref          # drawdown vs the static reference (eq normalized to start)
    if mode == 'none':
        return 1.0
    if mode == 'band':                   # live governor: full to 7% DD, linear to 0 at 10%
        if dd <= 0.07: return 1.0
        if dd >= 0.10: return 0.0
        return max(0.0, 1.0 - (dd - 0.07) / 0.03)
    if mode == 'smooth':                 # research: risk*(1 - dd_frac), dd_frac in [0,1] over [0,10%]
        return max(0.0, 1.0 - min(max(dd, 0.0), 0.10) / 0.10)
    return 1.0


def mc(vals, base, start_eq, floor_abs, target_abs, defense='none', n_paths=N, seed_base=0):
    n = len(vals); floor_norm = floor_abs / start_eq; tgt_norm = target_abs / start_eq
    dd_ref = 100000.0 / start_eq         # static 100k reference in normalized units
    outs = collections.Counter(); dl = []; worst_day = 0.0; breaches = 0; days = 0
    for s in range(n_paths):
        rng = random.Random(s * 131 + seed_base + int(base * 1e6))
        eq = 1.0; res = 'timeout'; dc = 0
        for _ in range(PATHCAP):
            start = rng.randrange(n); broke = False
            for k in range(BLOCK):
                risk = base * cap_mult(eq, dd_ref, defense)
                dp = vals[(start + k) % n] * risk; dc += 1
                if s < 200:
                    worst_day = min(worst_day, dp); days += 1
                    if dp <= -DAILY: breaches += 1
                if dp <= -DAILY:
                    res = 'fail_daily'; broke = True; break
                eq *= (1 + dp)
                if eq <= floor_norm:
                    res = 'fail_maxdd'; broke = True; break
                if eq >= tgt_norm:
                    res = 'pass'; broke = True; break
            if broke: break
        outs[res] += 1
        if res == 'pass': dl.append(dc)
    return dict(p_pass=round(outs['pass']/n_paths, 4), p_fail_dd=round(outs['fail_maxdd']/n_paths, 4),
                p_fail_daily=round(outs['fail_daily']/n_paths, 4),
                med=int(statistics.median(dl)) if dl else None,
                worst_day_pct=round(worst_day*100, 3), daily_breach_pct=round(breaches/max(1,days)*100, 3))


def main():
    series = build_series()
    print(f"W7 series: mean {statistics.fmean(series):.4f} std {statistics.pstdev(series):.4f} "
          f"min {min(series):.3f} max {max(series):.2f}")
    # Owner-confirmed Phase-1 targets: FTMO +10% (110k), FN +8% (108k); both daily -5% / static 90k floor.
    ACCTS = {'FN_fresh_100k_tgt108': dict(start=100000.0, floor=90000.0, target=108000.0),
             'FTMO_97p2k_static_tgt110': dict(start=97200.0, floor=90000.0, target=110000.0)}
    bases = [0.0125, 0.015, 0.02, 0.025, 0.03, 0.035]
    out = {'schema': 'gtos.cycle59.live_book_ddefense_sizing.v1',
           'series': {'mean': round(statistics.fmean(series),5), 'std': round(statistics.pstdev(series),5),
                      'min': round(min(series),3), 'max': round(max(series),2),
                      'note': 'live W7-book reconstruction (MC_LIVE_EQUITY_RERUN calibration), eff=base*VS(0.7504)'},
           'accounts': {}}
    for acct, a in ACCTS.items():
        print(f"\n=== {acct} (start {a['start']:.0f}, floor {a['floor']:.0f}, runway {(a['start']-a['floor'])/a['start']*100:.1f}%) ===")
        rows = {}
        for base in bases:
            eff = base * VS
            none = mc(series, eff, a['start'], a['floor'], a['target'], 'none', seed_base=7)
            band = mc(series, eff, a['start'], a['floor'], a['target'], 'band', seed_base=7)
            smooth = mc(series, eff, a['start'], a['floor'], a['target'], 'smooth', seed_base=7)
            rows[f'{base*100:.2f}%'] = {'no_defense': none, 'band_defense': band, 'smooth_defense': smooth}
            print(f"  base {base*100:.2f}% (eff {eff*100:.2f}%): "
                  f"NONE pass {none['p_pass']}/dd {none['p_fail_dd']}/dly {none['p_fail_daily']}/{none['med']}d | "
                  f"BAND pass {band['p_pass']}/dd {band['p_fail_dd']}/dly {band['p_fail_daily']}/{band['med']}d worst{band['worst_day_pct']}% | "
                  f"SMOOTH pass {smooth['p_pass']}/dd {smooth['p_fail_dd']}/{smooth['med']}d")
        out['accounts'][acct] = rows
        # safe-aggressive base = highest base with band-defense fail_daily==0 AND p_pass>=0.98 AND fail_dd<=0.02
        safe = [b for b in bases if rows[f'{b*100:.2f}%']['band_defense']['p_fail_daily'] == 0.0
                and rows[f'{b*100:.2f}%']['band_defense']['p_pass'] >= 0.98
                and rows[f'{b*100:.2f}%']['band_defense']['p_fail_dd'] <= 0.02]
        out['accounts'][acct + '_safe_aggressive_base'] = (f'{max(safe)*100:.2f}%' if safe else 'none>1.25%')
        print(f"  >>> safe-aggressive base (band-defense, fail_daily=0, pass>=0.98, fail_dd<=0.02): "
              f"{max(safe)*100:.2f}%" if safe else "  >>> none clears above 1.25%")
    (HERE / 'KNOWLEDGE_BASE' / 'validation' / 'CYCLE59_LIVE_BOOK_DDEFENSE.json').write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == '__main__':
    main()
