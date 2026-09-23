"""KB6_overlay_materialize_corrcheck.py — materialize the STATE_D-validated cross-layer overlays
as LEAK-FREE per-day R streams and corr-check vs the DEPLOYED clean_3 book.

The KB6 re-mine confirmed the cross-layer winners survive the STATE_D scale-out exit (lift roughly
halves but stays positive, perm-p small, 2/2 fwd years). This step materializes the surviving
overlay setups as real tradeable daily-R sleeves UNDER cs.exit_state_d (the deployed exit), exactly
mirroring SUBSTRATE_corrcheck / KB5_fold_new_sleeves convention, then measures:

  1. each overlay's STATE_D forward stats (n, EV, win, per-year),
  2. its daily-R correlation vs the clean_3 book (W3 8 base sleeves + sub_xvol_pullback +
     vp_euidx_pocgrav + sub_mid_dn_revert, all at deploy conf), via union-0fill (the book's
     diversification convention) AND intersect,
  3. CRITICALLY its corr vs the sub_xvol_pullback sleeve itself (the overlay is a SUBSET of that
     base — we need to know if it is a SIZE-UP SELECTOR or a DOUBLE-COUNT).

Leak-free: overlay rows come from KB6_CONFLUENCE_STATE_D_RAW.json (every signal already labelled
with the STATE_D Rd from cs.exit_state_d on closed-bar features). We just filter by the overlay
condition and bucket by date. The clean_3 book daily series is rebuilt from the deployed sleeve
generators (W3 cache + the 3 KB5 fold sleeves) using the SAME build_matrix conf-wtd convention.
"""
import sys, json, collections, math, pickle, statistics, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import INTEG_portfolio_build_w3 as W3
import INTEG_portfolio_build_w2 as W2
import KB5_fold_new_sleeves as FOLD

DEPLOY_CONF = json.load(open(HERE / "INTEG_W5_CLEAN3_DEPLOY.json"))["conf"]


def pearson(x, y):
    n = len(x)
    if n < 8:
        return None
    mx = sum(x) / n; my = sum(y) / n
    sx = sum((a - mx) ** 2 for a in x); sy = sum((b - my) ** 2 for b in y)
    if sx == 0 or sy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sx * sy)


def _asdate(d):
    """Book daily keys are datetime.date; raw overlay rows carry ISO date strings.
    Normalize so both grids align on the same key type."""
    if isinstance(d, datetime.date):
        return d
    return datetime.date.fromisoformat(str(d)[:10])


def candidate_daily(rows, key):
    byday = collections.defaultdict(list)
    for r in rows:
        byday[_asdate(r["date"])].append(r[key])
    return {d: sum(v) / len(v) for d, v in byday.items()}   # mean R/day (sleeve convention)


def stream_stats(rows, key):
    fwd = [r[key] for r in rows if r["year"] >= 2025]
    tr = [r[key] for r in rows if r["year"] < 2025]
    yrs = collections.Counter(r["year"] for r in rows)
    fwd_yrs = sum(1 for y in (2025, 2026) if yrs.get(y, 0) >= 5)
    per_year = {str(y): (yrs[y], round(sum(r[key] for r in rows if r["year"] == y) / yrs[y], 4)) for y in sorted(yrs)}
    return dict(n=len(rows), n_train=len(tr), n_fwd=len(fwd),
                EV_train=round(sum(tr) / len(tr), 4) if tr else None,
                EV_fwd=round(sum(fwd) / len(fwd), 4) if fwd else None,
                win_fwd=round(100 * sum(1 for x in fwd if x > 0) / len(fwd), 1) if fwd else None,
                fwd_per_year=round(len(fwd) / 1.5, 1), fwd_years_n5=fwd_yrs, per_year=per_year)


# --------------------------------------------------------------------------- #
# Build the DEPLOYED clean_3 book daily conf-wtd matrix.
#   base 8 sleeves: from W3 cache via W3 build_matrix machinery.
#   +3 fold sleeves: regenerate via KB5_fold_new_sleeves gens, apply deploy conf.
# --------------------------------------------------------------------------- #
def build_clean3_book():
    streams_w3 = pickle.load(open(HERE / "INTEG_W3_streams_cache.pkl", "rb"))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    base_sleeves = W3.SLEEVES
    daily = {sl: {} for sl in base_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(base_sleeves):
            daily[sl][day] = M_w3[di][si]
    # +3 fold sleeves (clean_3)
    fold_streams = {}
    for nm in ("sub_xvol_pullback", "vp_euidx_pocgrav", "sub_mid_dn_revert"):
        rows = FOLD.NEW_GENS[nm]()
        cd = candidate_daily(rows, "R")
        conf = DEPLOY_CONF[nm]
        daily[nm] = {d: v * conf for d, v in cd.items()}
        fold_streams[nm] = rows
    sleeves = list(base_sleeves) + ["sub_xvol_pullback", "vp_euidx_pocgrav", "sub_mid_dn_revert"]
    all_days = set()
    for sl in sleeves:
        all_days |= set(daily[sl])
    comb = {d: sum(daily[sl].get(d, 0.0) for sl in sleeves) for d in all_days}
    return sleeves, daily, comb, all_days, fold_streams


def corr_report(cand_daily, sleeves, daily, comb, book_days):
    cand_days = set(cand_daily)
    out = {"per_sleeve_union0": {}, "per_sleeve_intersect": {},
           "n_cand_days": len(cand_days), "n_overlap_book": len(cand_days & book_days)}
    for sl in sleeves:
        u = sorted(cand_days | set(daily[sl]))
        out["per_sleeve_union0"][sl] = pearson([cand_daily.get(d, 0.0) for d in u],
                                               [daily[sl].get(d, 0.0) for d in u])
        inter = sorted(cand_days & set(daily[sl]))
        if len(inter) >= 8:
            out["per_sleeve_intersect"][sl] = pearson([cand_daily[d] for d in inter],
                                                      [daily[sl][d] for d in inter])
    u = sorted(cand_days | book_days)
    out["vs_combined_union0"] = pearson([cand_daily.get(d, 0.0) for d in u], [comb.get(d, 0.0) for d in u])
    inter = sorted(cand_days & book_days)
    out["vs_combined_intersect"] = pearson([cand_daily[d] for d in inter], [comb[d] for d in inter]) if len(inter) >= 8 else None
    out["max_abs_sleeve_union0"] = max((abs(v) for v in out["per_sleeve_union0"].values() if v is not None), default=None)
    return out


# The STATE_D-surviving overlays to materialize. Each = (name, base_cell, cond_dim, cond_val, note).
OVERLAYS = [
    ("veto_xvol_pullback", "xvol_up_pullback_L3R", "ll_align", "none",
     "leader-impulse VETO on flagship xvol uptrend-pullback long (no aligned/opposed leader impulse)"),
    ("veto_xvol_conflict", "xvol_up_conflict_L3R", "ll_align", "none",
     "leader-impulse VETO on broad xvol uptrend-conflict long"),
    ("veto_xvol_conflict_mid", "xvol_up_conflict_mid_L3R", "ll_align", "none",
     "leader-impulse VETO on xvol uptrend-conflict midrange long"),
    ("vpacc_mid_dn_revert", "mid_dn_revert_ny_L3R", "vp_loc", "above_va",
     "VP-acceptance (price above prior value-area) on NY mid-vol dn-revert long"),
]


def main():
    print("=== KB6: materialize STATE_D-validated cross-layer overlays + corr-check vs clean_3 book ===\n")
    raw = json.load(open(HERE / "KB6_CONFLUENCE_STATE_D_RAW.json"))

    print("Building deployed clean_3 book daily matrix (8 base + 3 fold sleeves)...")
    sleeves, daily, comb, book_days, fold_streams = build_clean3_book()
    print(f"  clean_3 book: {len(sleeves)} sleeves, {len(book_days)} trading days\n")

    report = {"book": "clean_3", "book_sleeves": sleeves, "n_book_days": len(book_days),
              "corr_convention": "union-0fill (deploy diversification convention) + intersect",
              "overlays": {}}

    for name, base_cell, dim, val, note in OVERLAYS:
        rows = [r for r in raw[base_cell] if r["conds"].get(dim) == val]
        # STATE_D label and (comparison) fixed-3R label as daily streams
        st_d = stream_stats(rows, "Rd")
        st_3 = stream_stats(rows, "R3")
        cd_d = candidate_daily(rows, "Rd")
        cc = corr_report(cd_d, sleeves, daily, comb, book_days)
        # the double-count check: corr specifically vs the sub_xvol_pullback fold sleeve
        corr_vs_xvol = cc["per_sleeve_union0"].get("sub_xvol_pullback")
        corr_vs_xvol_int = cc["per_sleeve_intersect"].get("sub_xvol_pullback")
        report["overlays"][name] = {
            "note": note, "base_cell": base_cell, "condition": f"{dim}={val}",
            "state_d_stats": st_d, "fixed3R_stats": st_3, "corr": cc,
            "corr_vs_sub_xvol_pullback_union0": corr_vs_xvol,
            "corr_vs_sub_xvol_pullback_intersect": corr_vs_xvol_int,
        }
        print(f"--- {name}  [{base_cell} x {dim}={val}] ---")
        print(f"  {note}")
        print(f"  STATE_D : n={st_d['n']} (tr {st_d['n_train']}/fwd {st_d['n_fwd']}) "
              f"EVtr={st_d['EV_train']} EVfw={st_d['EV_fwd']} win_fwd={st_d['win_fwd']}% "
              f"~{st_d['fwd_per_year']}/yr ({st_d['fwd_years_n5']}/2 fwd-yrs n>=5)")
        py = " ".join(f"{y}:{v[1]:+.3f}(n{v[0]})" for y, v in st_d['per_year'].items())
        print(f"     per-year STATE_D: {py}")
        print(f"  fixed3R : EVtr={st_3['EV_train']} EVfw={st_3['EV_fwd']} win_fwd={st_3['win_fwd']}%  (comparator)")
        print(f"  corr vs COMBINED clean_3 book: union0={cc['vs_combined_union0']:+.4f} "
              f"intersect={cc['vs_combined_intersect'] if cc['vs_combined_intersect'] is None else round(cc['vs_combined_intersect'],4)}")
        print(f"  corr vs sub_xvol_pullback sleeve (double-count check): "
              f"union0={corr_vs_xvol if corr_vs_xvol is None else round(corr_vs_xvol,4)} "
              f"intersect={corr_vs_xvol_int if corr_vs_xvol_int is None else round(corr_vs_xvol_int,4)}")
        print(f"  max |corr| vs any single sleeve (union0): {cc['max_abs_sleeve_union0']:.4f}")
        top = sorted(((abs(v), s, v) for s, v in cc["per_sleeve_union0"].items() if v is not None), reverse=True)[:4]
        print("  top sleeve corrs (union0): " + ", ".join(f"{s}={v:+.3f}" for _, s, v in top))
        print()

    (HERE / "KB6_OVERLAY_CORRCHECK_RESULT.json").write_text(json.dumps(report, indent=1, default=str))
    print("wrote KB6_OVERLAY_CORRCHECK_RESULT.json")
    return report


if __name__ == "__main__":
    main()
