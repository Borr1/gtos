"""KB6_router_validate.py — track KB6 GOAL 3: build + validate the CONFLUENCE-SCORE ROUTER.

A leak-free per-day materializer that, for every confluence-sleeve signal, computes a
CONFLUENCE SCORE = sum of per-class-LEARNED-SIGN orthogonal conditions present at bar i,
then SIZES the trade by clamp(1 + GAIN*score, LO, HI). Signs learned on TRAIN(<=2024)
ONLY, applied unchanged forward -> no lookahead. Deletes nothing (size floor LO>0).

Confluence sleeve = the deploy flagship (xvol-up-pullback long, 4-class universe) UNION
the NEW KB6-discovered confluent bases that are forward-validated AND train-supported:
  - xvol_dn_aligned_london long (liq-sweep confluent, train+fwd +)
  - xvol_up_neutral long (a second xvol-up long base; veto + hurst=revert confluent)
This is a single SELECTOR-style sleeve: same signals under FLAT vs ROUTER sizing; only
per-trade size differs. We validate (vol-matched, on the deploy book) that ROUTER lifts:
  (a) forward size-weighted EV, and most importantly
  (b) the 1.5x left-tail STRESS challenge-pass MC (the binding constraint), and
  (c) the 2-account joint stress-pass when folded into the deploy book.

Leak-free: base-state + ALL orthogonal tags at bar i from closed bars index<=i, via the
KB5 cross-layer tagger (vp prior-day profile, regime model fit on TRAIN, leadlag z at
same close, liquidity sweep in last 3 bars). Outcome via sub.outcome (real w1.cost_for).
"""
from __future__ import annotations
import sys, json, math, collections, random, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import numpy as np
import substrate as sub
import wave1_structure_setups_ict as w1
import KB5_cross_layer_miner as XL
import KB5_fold_new_sleeves as FOLD
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

TRAIN_MAX = 2024
FWD_MIN = 2025
random.seed(19)

# --- router hyperparams: FIXED a-priori (NOT tuned on the forward verdict) --- #
GAIN = 0.5
LO, HI = 0.4, 2.0
EPS = 0.15          # min |TRAIN lift| (R) for a condition's sign to count
N_SIGN_MIN = 15     # min TRAIN rows for a per-class sign to be trusted
ROUTER_DIMS = ["ll_align", "vp_loc", "vp_poc_side", "hurst", "liq_align"]

# --- the confluence sleeve's base cells (flagship + NEW KB6 train+fwd-validated) --- #
SLEEVE_BASES = {
    "xvol_up_pullback": ("g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict",
                         dict(vol="xhi", persist="rand", trend="up", mtf="conflict"), 1, (1.0, 3.0)),
    "xvol_dn_aligned_london": ("g1.0_3.0|dir=1|depth7|vol=xhi|trend=dn|mtf=aligned|rngpos=low|comp=norm|persist=rand|session=london",
                               dict(vol="xhi", trend="dn", mtf="aligned", rngpos="low", comp="norm", persist="rand", session="london"), 1, (1.0, 3.0)),
    "xvol_up_neutral": ("g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=neutral",
                        dict(vol="xhi", persist="rand", trend="up", mtf="neutral"), 1, (1.0, 3.0)),
}


def wins(r):
    return max(-1.3, min(5.0, r))


def walk_signals():
    """One leak-free pass: emit every sleeve-base signal with date, year, R, and its
    orthogonal condition tags (for the router score). Drop crypto+jpy_fx (deploy
    universe convention for these xvol long bases)."""
    syms = [s for s in w1.SYMBOLS if s not in FOLD.DROP_XVOL and AC.get(s)]
    leader_sigs = XL.build_leader_signals()
    rows = []
    for s in syms:
        built = sub.build_states(s)
        if built is None:
            continue
        T, B, A, states = built
        closes = np.array([b.c for b in B], dtype=float)
        atrs_np = np.array(A, dtype=float)
        cost = w1.cost_for(s); n = len(B)
        model, arch = XL.build_regime_model(s, B, closes, atrs_np, T)
        profs, days = XL.build_vp(s)
        lm = XL.build_liquidity(s, T, B)
        cls = AC.get(s)
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st = states[i]
            if st is None:
                continue
            co = sub.cell_coords(st)
            a = A[i]
            if a <= 0:
                continue
            t = T[i]; price = B[i].c
            matched = [bn for bn, (_, conds, _, _) in SLEEVE_BASES.items()
                       if all(co.get(d) == v for d, v in conds.items())]
            if not matched:
                continue
            cd = {}
            cd.update(XL.vp_conditions(profs, days, t, price, a))
            cd.update(XL.regime_conditions(model, arch, B, closes, atrs_np, i))
            cd.update(XL.leadlag_conditions(s, t, leader_sigs))
            cd["liq_sweep"] = XL.liquidity_sweep_recent(lm, i, a, K=3)
            for bn in matched:
                _, _, dmode, (stop_atr, target_R) = SLEEVE_BASES[bn]
                R, hit = sub.outcome(B, i, dmode, stop_atr, target_R, a, cost)
                bc = dict(cd)
                if cd.get("ll_impulse") in ("up", "dn"):
                    bc["ll_align"] = "aligned" if ((cd["ll_impulse"] == "up") == (dmode > 0)) else "opposed"
                else:
                    bc["ll_align"] = "none"
                if cd.get("liq_sweep") in ("sweep_long", "sweep_short"):
                    bc["liq_align"] = "aligned" if ((cd["liq_sweep"] == "sweep_long") == (dmode > 0)) else "opposed"
                else:
                    bc["liq_align"] = "none"
                rows.append(dict(base=bn, sym=s, cls=cls, date=t.date(), year=t.year,
                                 R=wins(R), conds=bc))
    return rows


def learn_signs(rows):
    """Per (base, dim, val) class, learn sign from TRAIN ONLY. base-specific because
    KB5/KB6 proved confluence is base-specific. Returns {(base,dim,val): +-1}."""
    by_base = collections.defaultdict(list)
    for r in rows:
        by_base[r["base"]].append(r)
    signs = {}
    detail = {}
    for base, rs in by_base.items():
        tr = [r for r in rs if r["year"] <= TRAIN_MAX]
        if not tr:
            continue
        bmean = sum(r["R"] for r in tr) / len(tr)
        bucket = collections.defaultdict(list)
        for r in tr:
            for d in ROUTER_DIMS:
                v = r["conds"].get(d)
                if v in (None, "na"):
                    continue
                bucket[(d, v)].append(r["R"])
        for (d, v), Rs in bucket.items():
            if len(Rs) < N_SIGN_MIN:
                continue
            lift = sum(Rs) / len(Rs) - bmean
            sg = +1 if lift > EPS else (-1 if lift < -EPS else 0)
            if sg != 0:
                signs[(base, d, v)] = sg
                detail[f"{base}|{d}={v}"] = dict(sign=sg, train_lift=round(lift, 3), n_tr=len(Rs))
    return signs, detail


def score_row(r, signs):
    sc = 0
    for d in ROUTER_DIMS:
        v = r["conds"].get(d)
        if v in (None, "na"):
            continue
        sc += signs.get((r["base"], d, v), 0)
    return sc


def per_day(rows, sized_signs=None):
    """Aggregate to per-day mean R. If sized_signs given, size-weight each trade by
    router_size(score); else flat (size=1). Per-day R = sum(size*R)/sum(size) so a
    day's contribution stays in R-units (risk-equivalent), the deploy convention."""
    byday_num = collections.defaultdict(float)
    byday_den = collections.defaultdict(float)
    for r in rows:
        if sized_signs is not None:
            sz = max(LO, min(HI, 1.0 + GAIN * score_row(r, sized_signs)))
        else:
            sz = 1.0
        byday_num[r["date"]] += sz * r["R"]
        byday_den[r["date"]] += sz
    return {d: byday_num[d] / byday_den[d] for d in byday_num}


def ev_stats(rows, signs=None):
    def agg(rs):
        if not rs:
            return dict(n=0, meanR=None)
        if signs is not None:
            num = sum(max(LO, min(HI, 1.0 + GAIN * score_row(r, signs))) * r["R"] for r in rs)
            den = sum(max(LO, min(HI, 1.0 + GAIN * score_row(r, signs))) for r in rs)
            return dict(n=len(rs), meanR=round(num / den, 4))
        return dict(n=len(rs), meanR=round(sum(r["R"] for r in rs) / len(rs), 4))
    tr = [r for r in rows if r["year"] <= TRAIN_MAX]
    fw = [r for r in rows if r["year"] >= FWD_MIN]
    py = collections.defaultdict(list)
    for r in fw:
        py[r["year"]].append(r)
    pys = {}
    for y, rs in sorted(py.items()):
        if signs is not None:
            num = sum(max(LO, min(HI, 1.0 + GAIN * score_row(r, signs))) * r["R"] for r in rs)
            den = sum(max(LO, min(HI, 1.0 + GAIN * score_row(r, signs))) for r in rs)
            pys[str(y)] = dict(n=len(rs), meanR=round(num / den, 4))
        else:
            pys[str(y)] = dict(n=len(rs), meanR=round(sum(r["R"] for r in rs) / len(rs), 4))
    return dict(train=agg(tr), fwd=agg(fw), fwd_per_year=pys)


# ---- MC harness (reuse the LOCKED engine) ---- #
TARGET = I.TARGET; MAXDD = I.MAXDD; DAILY = I.DAILY; BLOCK = I.BLOCK; PATHCAP = I.PATHCAP; N = I.N
mc_series = W2.mc_series
joint_pass_mc = W2.joint_pass_mc


def main():
    print("=== KB6 CONFLUENCE-SCORE ROUTER — build + validate ===\n")
    cache = HERE / "KB6_router_signals.pkl"
    if cache.exists():
        rows = pickle.load(open(cache, "rb"))
        print(f"(loaded {len(rows)} sleeve signals from cache)")
    else:
        print("walking leak-free sleeve signals...", flush=True)
        rows = walk_signals()
        pickle.dump(rows, open(cache, "wb"))
        print(f"walked {len(rows)} sleeve signals")

    report = {"track": "KB6_confluence_router", "hyperparams": dict(GAIN=GAIN, LO=LO, HI=HI, EPS=EPS, N_SIGN_MIN=N_SIGN_MIN, dims=ROUTER_DIMS)}

    # per-base sample
    by_base = collections.defaultdict(list)
    for r in rows:
        by_base[r["base"]].append(r)
    report["base_sample"] = {}
    print("\nconfluence-sleeve bases (sample):")
    for b, rs in by_base.items():
        tr = sum(1 for r in rs if r["year"] <= TRAIN_MAX); fw = sum(1 for r in rs if r["year"] >= FWD_MIN)
        report["base_sample"][b] = dict(n=len(rs), n_tr=tr, n_fwd=fw)
        print(f"  {b:24} n={len(rs)} tr={tr} fwd={fw}")

    # learn signs on TRAIN only
    signs, detail = learn_signs(rows)
    report["learned_signs"] = detail
    print(f"\nlearned {len(signs)} per-base condition signs (TRAIN only):")
    for k, v in sorted(detail.items()):
        print(f"  {k:48} sign={v['sign']:+d} train_lift={v['train_lift']:+.3f} (n{v['n_tr']})")

    # EV: flat vs router
    flat = ev_stats(rows, signs=None)
    rout = ev_stats(rows, signs=signs)
    report["ev_flat"] = flat; report["ev_router"] = rout
    print(f"\n=== EV: FLAT vs ROUTER (size-weighted R per unit risk) ===")
    print(f"  FLAT   TRAIN {flat['train']['meanR']} (n{flat['train']['n']})  FWD {flat['fwd']['meanR']} (n{flat['fwd']['n']})  per-yr {flat['fwd_per_year']}")
    print(f"  ROUTER TRAIN {rout['train']['meanR']} (n{rout['train']['n']})  FWD {rout['fwd']['meanR']} (n{rout['fwd']['n']})  per-yr {rout['fwd_per_year']}")
    print(f"  fwd EV lift (router-flat): {round((rout['fwd']['meanR'] or 0)-(flat['fwd']['meanR'] or 0),4):+}")

    # per-day streams
    flat_daily = per_day(rows, sized_signs=None)
    rout_daily = per_day(rows, sized_signs=signs)
    # standalone-sleeve MC (vol-matched between flat & router so the comparison is risk-equivalent)
    print(f"\n=== STANDALONE CONFLUENCE-SLEEVE STRESS MC (vol-matched flat vs router) ===")
    all_days = sorted(set(flat_daily) | set(rout_daily))
    fv = [flat_daily.get(d, 0.0) for d in all_days]
    rv = [rout_daily.get(d, 0.0) for d in all_days]
    fwd_days = [d for d in all_days if d.year >= 2025]
    fv_fwd = [flat_daily.get(d, 0.0) for d in fwd_days]
    rv_fwd = [rout_daily.get(d, 0.0) for d in fwd_days]
    sd_f = statistics.pstdev(fv); sd_r = statistics.pstdev(rv)
    vm = sd_f / sd_r if sd_r > 0 else 1.0     # vol-match router to flat
    def stress(v): return [(x * 1.5 if x < 0 else x) for x in v]
    report["standalone_mc"] = {}
    print(f"  (flat std={sd_f:.4f} router std={sd_r:.4f}; router vol-scaled x{vm:.3f} to match flat)")
    print(f"  {'risk':>7} {'FLAT pass':>10} {'ROUT pass':>10} | {'FLAT str1.5':>11} {'ROUT str1.5':>11}")
    for risk in (0.005, 0.0075, 0.01, 0.015):
        pf = mc_series(fv, risk, seed_base=1)['p_pass']
        pr = mc_series(rv, risk * vm, seed_base=1)['p_pass']
        sf = mc_series(stress(fv), risk, seed_base=999)['p_pass']
        sr = mc_series(stress(rv), risk * vm, seed_base=999)['p_pass']
        report["standalone_mc"][f"{risk*100:.2f}%"] = dict(flat_pass=pf, router_pass=pr,
                                                           flat_stress15=sf, router_stress15=sr)
        print(f"  {risk*100:6.2f}% {pf:>10.2%} {pr:>10.2%} | {sf:>11.2%} {sr:>11.2%}")

    # ---- DEPLOY-BOOK FOLD: flat-sleeve vs router-sleeve, vol-matched, joint stress ---- #
    print(f"\n=== DEPLOY-BOOK FOLD (book + confluence sleeve @ conf 0.45; flat vs router) ===")
    streams_w3 = pickle.load(open(HERE / "INTEG_W3_streams_cache.pkl", "rb"))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    book_days = set(days_w3)
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])
    CONF = 0.45    # flagship-equivalent sizing for the confluence sleeve

    def fold(daily, label):
        adays = sorted(book_days | set(daily))
        comb = [comb_book.get(d, 0.0) + CONF * daily.get(d, 0.0) for d in adays]
        sd = statistics.pstdev(comb); vs = sd_book / sd if sd > 0 else 1.0
        cstr = [(v * 1.5 if v < 0 else v) for v in comb]
        out = dict(sharpe=round(statistics.fmean(comb) / sd, 4), vol_scale=round(vs, 4),
                   daily_mean=round(statistics.fmean(comb), 5), daily_std=round(sd, 5))
        for risk in (0.01, 0.015):
            out[f"p_pass_{risk*100:.1f}pct_vm"] = mc_series(comb, risk * vs, seed_base=1)['p_pass']
            out[f"stress15_{risk*100:.1f}pct_vm"] = mc_series(cstr, risk * vs, seed_base=999)['p_pass']
        return out

    book_only_days = sorted(book_days)
    bo_comb = [comb_book[d] for d in book_only_days]
    sd_bo = statistics.pstdev(bo_comb); vs_bo = sd_book / sd_bo if sd_bo > 0 else 1.0
    bo_str = [(v * 1.5 if v < 0 else v) for v in bo_comb]
    book_only = dict(sharpe=round(statistics.fmean(bo_comb) / sd_bo, 4), vol_scale=round(vs_bo, 4))
    for risk in (0.01, 0.015):
        book_only[f"p_pass_{risk*100:.1f}pct_vm"] = mc_series(bo_comb, risk * vs_bo, seed_base=1)['p_pass']
        book_only[f"stress15_{risk*100:.1f}pct_vm"] = mc_series(bo_str, risk * vs_bo, seed_base=999)['p_pass']

    fold_flat = fold(flat_daily, "flat")
    fold_rout = fold(rout_daily, "router")
    report["deploy_fold"] = dict(book_only=book_only, sleeve_flat=fold_flat, sleeve_router=fold_rout)
    print(f"  {'variant':>16} {'sharpe':>7} {'P@1%vm':>8} {'P@1.5%vm':>9} {'str@1%vm':>9} {'str@1.5%vm':>10}")
    for lbl, o in (("book_only", book_only), ("+sleeve FLAT", fold_flat), ("+sleeve ROUTER", fold_rout)):
        print(f"  {lbl:>16} {o['sharpe']:>7.4f} {o['p_pass_1.0pct_vm']:>8.2%} {o['p_pass_1.5pct_vm']:>9.2%} "
              f"{o['stress15_1.0pct_vm']:>9.2%} {o['stress15_1.5pct_vm']:>10.2%}")

    (HERE / "KB6_ROUTER_RESULT.json").write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB6_ROUTER_RESULT.json")
    return report


if __name__ == "__main__":
    main()
