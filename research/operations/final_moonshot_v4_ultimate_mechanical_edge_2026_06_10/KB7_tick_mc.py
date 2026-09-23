"""KB7 — LOCKED-engine MC on the TICK-restated deploy book (the verdict gate).

Reproduces the clean_3 deploy combined per-day series using the SAME locked machinery (W3 book
matrix + clean_3 new sleeves from INTEG_W5_new_streams_cache.pkl) and the LOCKED MC engine
(W2.mc_series + constants). Then applies the TICK per-symbol erosion to the energy_agri sleeve only
(the single material change; metals/JPY/crude erosions are tiny improvements and folded too) and
re-runs the vol-matched + 1.5x-stress challenge-pass MC for THREE energy variants:
  (0) baseline          : modeled energy (current deploy)
  (1) tick_all          : energy with real-tick per-symbol erosion, all 4 crude/gas kept
  (2) tick_drop_HN      : energy with real-tick erosion, HEATOIL+NATGAS DROPPED (recommended)

The verdict book changes on the vol-matched challenge-pass + max-DD MC, not per-trade EV alone.
"""
from __future__ import annotations
import sys, json, statistics, collections, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3

mc_series = W2.mc_series

CLEAN3_CONF = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}


def tick_erosion():
    bysym = collections.defaultdict(list)
    for f in ["KB7_TICK_TRUTH_LEDGER.jsonl", "KB7_TICK_CRYPTO_LEDGER.jsonl", "KB7_TICK_JPY_LEDGER.jsonl"]:
        p = HERE / f
        if not p.exists(): continue
        for line in p.read_text().splitlines():
            if not line.strip(): continue
            r = json.loads(line)
            if not r.get('covered', True): continue
            if 'tick_real' not in r or 'modeled' not in r: continue
            bysym[r['sym']].append(r['tick_real'] - r['modeled'])
    return {s: statistics.mean(v) for s, v in bysym.items()}


def _sized(r):
    """The sleeve's per-trade sized R as build_matrix consumes it (R_sized if present else R)."""
    return r.get('R_sized', r.get('R', 0.0))


def energy_daily(rows, conf):
    """per-day conf-weighted energy_agri contribution (mean-pool R_sized per day x conf, exactly as
    W2.build_matrix does: daily[day][sleeve] = (sum(R_sized)/n) * SLEEVE_CONF)."""
    byday = collections.defaultdict(list)
    for r in rows:
        byday[r['date']].append(_sized(r))
    return {d: (sum(v) / len(v)) * conf for d, v in byday.items()}


def restate_rows(rows, ero, drop=None):
    """Apply the per-symbol tick erosion as an additive (winsorized) haircut to BOTH R and R_sized,
    preserving the intra_size scaling embedded in R_sized (haircut scaled by R_sized/R)."""
    drop = drop or set()
    out = []
    for r in rows:
        if r['sym'] in drop: continue
        h = ero.get(r['sym'], 0.0)
        R = r.get('R', 0.0); Rs = r.get('R_sized', R)
        scale = (Rs / R) if R not in (0.0, None) else 1.0
        newR = max(-1.3, min(5.0, R + h))
        newRs = max(-1.3 * abs(scale), min(5.0 * abs(scale), Rs + h * scale))
        out.append({**r, 'R': newR, 'R_sized': newRs})
    return out


def main():
    ero = tick_erosion()
    ENERGY_CONF = W3.SLEEVE_CONF['energy_agri']

    CRYPTO_CONF = W3.SLEEVE_CONF['crypto']

    # ---- build deploy combined series the locked way (from the LOCKED W3 stream cache) ----
    streams_w3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    eidx = book_sleeves.index('energy_agri')
    cidx = book_sleeves.index('crypto')
    comb_book = {d: sum(M_w3[i]) for i, d in enumerate(days_w3)}            # full book per-day sum
    energy_col_base = {d: M_w3[i][eidx] for i, d in enumerate(days_w3)}     # baseline energy contrib
    crypto_col_base = {d: M_w3[i][cidx] for i, d in enumerate(days_w3)}     # baseline crypto contrib
    erows_cache = streams_w3['energy_agri']                                  # locked energy rows
    crows_cache = streams_w3['crypto']                                       # locked crypto rows

    # clean_3 new sleeves from the locked cache
    new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))
    def cand_daily(rows):
        byday = collections.defaultdict(list)
        for r in rows:
            byday[r['date']].append(r.get('R_sized', r['R'] * r.get('intra_size', 1.0)))
        return {d: sum(v) / len(v) for d, v in byday.items()}
    clean3_daily = {nm: cand_daily(new_streams[nm]) for nm in CLEAN3_CONF}

    all_days = sorted(set(days_w3) | set().union(*[set(clean3_daily[n]) for n in CLEAN3_CONF]))

    def comb(energy_col, crypto_col):
        out = []
        for d in all_days:
            base = (comb_book.get(d, 0.0)
                    - energy_col_base.get(d, 0.0) + energy_col.get(d, 0.0)
                    - crypto_col_base.get(d, 0.0) + crypto_col.get(d, 0.0))
            extra = sum(clean3_daily[nm].get(d, 0.0) * cf for nm, cf in CLEAN3_CONF.items())
            out.append(base + extra)
        return out

    # energy variants (apply erosion to the LOCKED cached energy rows)
    e_tick_all = energy_daily(restate_rows(erows_cache, ero), ENERGY_CONF)
    e_tick_drop = energy_daily(restate_rows(erows_cache, ero, drop={'HEATOIL_c', 'NATGAS_cash'}), ENERGY_CONF)
    # crypto variants (BTC/DASH measured erosion; ETH no tick feed -> 0 transfer)
    c_base = energy_daily(crows_cache, CRYPTO_CONF)               # same mean-pool helper, crypto conf
    c_tick_all = energy_daily(restate_rows(crows_cache, ero), CRYPTO_CONF)
    c_tick_dropD = energy_daily(restate_rows(crows_cache, ero, drop={'DASHUSD'}), CRYPTO_CONF)

    series = {
        'baseline': comb(energy_col_base, crypto_col_base),       # locked deploy combined series
        'tick_energy_all': comb(e_tick_all, crypto_col_base),
        'tick_energy_dropHN': comb(e_tick_drop, crypto_col_base),
        'tick_all_sleeves': comb(e_tick_all, c_tick_all),         # energy+crypto erosion, keep all
        'tick_drop_HN_DASH': comb(e_tick_drop, c_tick_dropD),     # recommended: drop illiquid legs
    }

    # vol_scale: match each variant's daily std to the BOOK-ONLY std (locked convention)
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])

    report = {"tick_erosion_applied": {s: round(ero[s], 4) for s in sorted(ero)},
              "energy_conf": ENERGY_CONF, "crypto_conf": CRYPTO_CONF,
              "sd_book": round(sd_book, 5), "variants": {}}
    print(f"sd_book={sd_book:.5f}")
    print(f"{'variant':>20} {'mean':>9} {'std':>8} {'vs':>6} "
          f"{'P@1%vm':>8} {'DD@1%':>7} {'P@1.5%vm':>9} {'DD@1.5%':>8} {'str@1.5%':>9} {'strDD':>7}")
    for nm, c in series.items():
        m = statistics.fmean(c); sd = statistics.pstdev(c); vs = sd_book / sd if sd > 0 else 1.0
        cstr = [(v * 1.5 if v < 0 else v) for v in c]
        r1 = mc_series(c, 0.01 * vs, seed_base=1)
        r15 = mc_series(c, 0.015 * vs, seed_base=1)
        s15 = mc_series(cstr, 0.015 * vs, seed_base=999)
        report['variants'][nm] = dict(
            daily_mean=round(m, 5), daily_std=round(sd, 5), vol_scale=round(vs, 4),
            p_pass_1pct_vm=r1['p_pass'], p_fail_dd_1pct=r1['p_fail_dd'], med_days_1pct=r1['med_days_pass'],
            p_pass_1p5_vm=r15['p_pass'], p_fail_dd_1p5=r15['p_fail_dd'], med_days_1p5=r15['med_days_pass'],
            stress_pass_1p5=s15['p_pass'], stress_dd_1p5=s15['p_fail_dd'])
        print(f"{nm:>20} {m:>9.5f} {sd:>8.5f} {vs:>6.3f} "
              f"{r1['p_pass']:>8.2%} {r1['p_fail_dd']:>7.2%} {r15['p_pass']:>9.2%} "
              f"{r15['p_fail_dd']:>8.2%} {s15['p_pass']:>9.2%} {s15['p_fail_dd']:>7.2%}")

    (HERE / "KB7_TICK_MC_RESULT.json").write_text(json.dumps(report, indent=1))
    print("\nWROTE KB7_TICK_MC_RESULT.json")


if __name__ == "__main__":
    main()
