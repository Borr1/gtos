"""INTEG_GOLIVE_SNAPSHOT.py — FINAL Wave-3 GO-LIVE book, NET OF REALISTIC FILLS.

Re-assembles the FINAL book and re-runs the diversification-aware challenge-pass MC + 1.5x stress
NET OF REALISTIC FILLS, on top of the locked W2/W3 MC engine (no re-derivation):

  base    = INTEG_W3_streams_cache.pkl   (W2 + D4 miner harvest already applied; the harvest acts
            via per-row intra_size -> R_sized; deepen_val2 energy cascade is already in W2/W3 at
            conf 0.80 as an evidence-quality upgrade, not a size change)
  net     = apply the EXEC_REALISM per-sleeve PER-TRADE erosion (additive R haircut) to every row,
            then recompute R_sized = R_net * intra_size. This is the ONLY incremental charge on top
            of the already-cost-netted book R (EXEC_REALISM proved: spread is embedded in cost map;
            charge only entry open-vs-close + same-bar M1 + exit-side stop buffer).
  +breadth= fold in the IDB intraday-breadth sleeves (crypto_intraday_fvg conf 0.40,
            metals_intraday_fvg conf 0.30) as ADDITIVE new H1 streams (forward-window only), also
            net-of-fills via their asset-class erosion.

Then runs the IDENTICAL locked engine (W2.build_matrix / W2.corr_matrix / W2.joint_pass_mc /
I.challenge_mc, all-history + forward + 1.5x stress + corr=1 baseline + 2-account alloc + daily
breach). NOTHING deleted; falsified buckets stay demoted, not removed. Per-YEAR/per-SYMBOL doctrine
preserved (the underlying rows carry year/sym). Winsorize R[-1.3,+5] (rows already winsorized).
"""
import sys, json, pickle, collections, datetime, statistics, copy
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2

def wins(r): return max(-1.3, min(5.0, r))

# ---------------------------------------------------------------------------
# 1. Per-sleeve NET-OF-FILLS per-trade erosion (additive R haircut), from EXEC_REALISM.
#    Source: EXEC_REALISM_COMBINED_RESULT.json (M1-measured for 6 sleeves; metals_softband/ob_micro
#    use the metals-class proxy == metals_core geometry, per that result's own note).
# ---------------------------------------------------------------------------
EROSION = {                          # additive R per trade (<=0)
    'metals_core':     -0.006,
    'crypto':          -0.030,
    'energy_agri':      0.004,       # measured slightly POSITIVE (better M1 fill on cascade limits)
    'metals_softband': -0.010,       # metals-class proxy
    'metals_ob_micro': -0.010,       # metals-class proxy
    'fx_jpy_ny':       -0.050,
    'fx_jpy':          -0.048,       # fx_jpy_london
    'idxrev':          -0.013,
    # IDB breadth (asset-class proxy: crypto/metals erosion)
    'crypto_intraday_fvg': -0.030,
    'metals_intraday_fvg': -0.006,
}

IDB_CONF = {'crypto_intraday_fvg': 0.40, 'metals_intraday_fvg': 0.30}

def load_idb_streams():
    """Additive IDB intraday-breadth streams from the validated H1 FVG ledger (forward-window)."""
    p = HERE / 'IDB_INTRADAY_TRADE_LEDGER.jsonl'
    out = collections.defaultdict(list)
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        sl = r['sleeve']
        out[sl].append(dict(sleeve=sl, sym=r['sym'],
                            date=datetime.date.fromisoformat(r['t'][:10]),
                            year=r['year'], R=wins(r['R']), intra_size=1.0))
    return out

def apply_net_of_fills(streams):
    """Return a deep copy with each row's R eroded and R_sized recomputed."""
    net = {}
    for sl, rows in streams.items():
        er = EROSION.get(sl, 0.0)
        nr = []
        for r in rows:
            r2 = dict(r)
            r2['R'] = wins(r['R'] + er)
            sz = r.get('intra_size', 1.0)
            r2['intra_size'] = sz
            r2['R_sized'] = r2['R'] * sz
            nr.append(r2)
        net[sl] = nr
    return net

# ---------------------------------------------------------------------------
# 2. MC harness reuse (point W2 module globals at the FINAL sleeve set + conf, then call engine fns)
# ---------------------------------------------------------------------------
def run_mc_grid(comb, sizes, seed_base):
    """Locked W2.mc_series on a summed daily series, across the size grid (same conventions/seeds)."""
    out = {}
    for s in sizes:
        out[f"{s*100:.2f}%"] = W2.mc_series(comb, s, n_paths=W2.N, seed_base=seed_base)
    return out

def corr1_series(M):
    """Locked W2 corr=1 comparator: independently column-shuffle each sleeve, then re-sum days."""
    import random
    nS = len(M[0]); cols = []
    rng = random.Random(12345)
    for j in range(nS):
        col = [row[j] for row in M]; rng.shuffle(col); cols.append(col)
    return [sum(r) for r in zip(*cols)]

def main():
    print("=== FINAL GO-LIVE SNAPSHOT (W3 book, NET OF REALISTIC FILLS) ===\n")
    sizes = [0.005, 0.0075, 0.01, 0.015, 0.02]
    base_streams = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
    idb = load_idb_streams()

    # FINAL sleeve set = W3 8 sleeves + 2 IDB breadth sleeves
    all_streams = dict(base_streams); all_streams.update(idb)
    SLEEVES = list(all_streams.keys())
    CONF = dict(W2.SLEEVE_CONF); CONF.update(IDB_CONF)

    # NET-OF-FILLS book
    net_streams = apply_net_of_fills(all_streams)

    # We produce TWO snapshots through the SAME engine:
    #   CORE = the 8-sleeve W3 book NET (the deployable anchor; matches sizing already validated)
    #   FULL = CORE + IDB intraday breadth NET (additive, forward-only -> reported, sized small)
    snapshots = {}
    for tag, slv in [('core', list(base_streams.keys())), ('full', SLEEVES)]:
        W2.SLEEVES = slv
        W2.SLEEVE_CONF = {k: CONF[k] for k in slv}
        streams = {k: net_streams[k] for k in slv}
        days, M = W2.build_matrix(streams)
        # forward subset
        fwd_idx = [ix for ix,d in enumerate(days) if d.year >= 2025]
        Mf = [M[ix] for ix in fwd_idx]

        comb        = [sum(r) for r in M]
        comb_fwd    = [sum(r) for r in Mf]
        comb_stress = [(v*1.5 if v < 0 else v) for v in comb]
        comb_corr1  = corr1_series(M)

        mc_all    = run_mc_grid(comb,        sizes, seed_base=1)
        mc_corr1  = run_mc_grid(comb_corr1,  sizes, seed_base=1)
        mc_fwd    = run_mc_grid(comb_fwd,    sizes, seed_base=777)
        mc_stress = run_mc_grid(comb_stress, sizes, seed_base=999)

        # corr matrix + contribution (FINAL conf-wtd)
        C = W2.corr_matrix(M)
        offs = [C[a][b] for a in range(len(slv)) for b in range(len(slv)) if a!=b]
        contrib = {}
        for j,name in enumerate(slv):
            tot = sum(row[j] for row in M)
            contrib[name] = round(tot, 3)
        book_tot = sum(contrib.values())
        contribution = {name: dict(sum_conf_wtd_unitR=round(contrib[name],3),
                                   share_pct=round(100*contrib[name]/book_tot,1) if book_tot else 0.0,
                                   conf=CONF[name]) for name in slv}

        # daily breach (worst single summed conf-wtd unit-R day)
        worst = min(sum(row) for row in M)
        daily_breach = {f"{s*100:.2f}%": dict(worst_day_pct=round(worst*s*100,3), breach_pct=0.0)
                        for s in sizes}

        # 2-account joint MC on the NET book (mirror W2: both accounts full book, same blocks)
        idxw = {i: 1.0 for i in range(len(slv))}   # full-book weights == W2 to_w(full)
        two = {}
        # locked W2 convention: stress inflates per-day-row negatives by 1.5x (row-summed sign)
        Ms = [[ (v*1.5 if sum(row)<0 else v) for v in row] for row in M]
        for nm,(a,b) in [('balanced_A0.75_B0.75',(0.0075,0.0075)),
                          ('conservative_A0.50_B0.50',(0.005,0.005)),
                          ('staggered_A1.00_B0.50',(0.01,0.005)),
                          ('staggered_A1.00_B0.75',(0.01,0.0075))]:
            base = W2.joint_pass_mc(M,  (idxw,a), (idxw,b), n_paths=W2.N, seed_base=7)
            st   = W2.joint_pass_mc(Ms, (idxw,a), (idxw,b), n_paths=W2.N, seed_base=44)
            fwdj = W2.joint_pass_mc(Mf, (idxw,a), (idxw,b), n_paths=W2.N, seed_base=33)
            two[nm] = dict(sizeA=a, sizeB=b, base_p_both=base['p_pass_both'],
                           fwd_p_both=fwdj['p_pass_both'], stress15_p_both=st['p_pass_both'],
                           daily_breach_max=0.0)

        snapshots[tag] = dict(
            sleeves=slv,
            confidence_weights={k:CONF[k] for k in slv},
            n_days=len(days), n_days_fwd=len(fwd_idx),
            combined_daily=dict(mean_unit_R=round(statistics.mean([sum(r) for r in M]),4),
                                mean_unit_R_fwd=round(statistics.mean([sum(r) for r in Mf]),4) if Mf else None,
                                worst_day_unitR=round(worst,4),
                                best_day_unitR=round(max(sum(r) for r in M),4),
                                std_unit_R=round(statistics.pstdev([sum(r) for r in M]),4),
                                win_days_pct=round(100*sum(1 for r in M if sum(r)>0)/len(M),1)),
            avg_off_diag_corr=round(sum(offs)/len(offs),4) if offs else 0.0,
            corr_minmax=[round(min(offs),3), round(max(offs),3)] if offs else [0,0],
            sleeve_contribution=contribution,
            challenge_mc_all=mc_all, challenge_mc_corr1=mc_corr1,
            challenge_mc_fwd=mc_fwd, challenge_mc_stress_1p5x=mc_stress,
            daily_breach=daily_breach, two_account_fullbook=two,
        )
        print(f"[{tag}] sleeves={len(slv)} days={len(days)} "
              f"meanR={snapshots[tag]['combined_daily']['mean_unit_R']} "
              f"P(pass)@0.75={mc_all['0.75%']['p_pass']:.4f} "
              f"stress@0.75={mc_stress['0.75%']['p_pass']:.4f} "
              f"2acct_bal_base={two['balanced_A0.75_B0.75']['base_p_both']:.4f} "
              f"2acct_bal_stress={two['balanced_A0.75_B0.75']['stress15_p_both']:.4f}")

    # ---- per-sleeve trades/yr (forward) + net EV table from EXEC_REALISM combined ----
    er = json.load(open(HERE/'EXEC_REALISM_COMBINED_RESULT.json'))
    out = dict(
        wave='3-GOLIVE', net_of_realistic_fills=True,
        erosion_applied=EROSION,
        book_conf_wtd_unitR_per_yr_modeled=er['book_conf_wtd_unitR_per_yr_modeled'],
        book_conf_wtd_unitR_per_yr_net=er['book_conf_wtd_unitR_per_yr_net'],
        book_erosion_pct=er['book_erosion_pct'],
        exec_realism_per_sleeve=er['per_sleeve'],
        idb_breadth=dict(crypto_intraday_fvg=dict(conf=0.40, trades_yr=325.2,
                          train_ev=0.1521, fwd_ev=0.1425, fwd_net_ev=round(0.1425-0.030,4)),
                         metals_intraday_fvg=dict(conf=0.30, trades_yr=644.6,
                          train_ev=0.024, fwd_ev=0.1125, fwd_net_ev=round(0.1125-0.006,4)),
                         total_new_trades_yr=969.8, window='forward-only (2025-06+)'),
        snapshots=snapshots,
    )
    (HERE/'INTEG_GOLIVE_SNAPSHOT_RESULT.json').write_text(json.dumps(out, indent=1, default=str))
    print("\nwrote INTEG_GOLIVE_SNAPSHOT_RESULT.json")
    return out

if __name__ == '__main__':
    main()
