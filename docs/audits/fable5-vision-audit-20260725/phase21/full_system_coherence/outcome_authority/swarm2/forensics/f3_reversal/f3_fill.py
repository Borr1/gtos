#!/usr/bin/env python3
"""F3 (7) — THE FILL, after F1 relocated the question.

F1 measured that the reversal story covers a small minority of losers and that the
typical stop loser goes adverse almost immediately: its best moment is ~1 minute
after the fill at ~+0.42 R.  That is a fill-quality signature, so this pass
characterises the price path AROUND the fill rather than around the peak.

Four questions, in the order the evidence has to be taken:

  A. ARTIFACT CHECK FIRST.  Is "+0.42 R one minute in" a real micro-extreme or just
     the range of the single M1 bar the fill lands in?  Measured by comparing the
     fill bar's own high-low range, in R, against the excursion attributed to it.
  B. Is the fill landing at a local extreme AGAINST us?  Measured as the percentile
     of the fill price inside the preceding 30 M1 bars' range, plus the signed
     pre-fill move over several lookbacks, in R.
  C. Does it differ by ORDER TYPE?  A LIMIT fills because price came TO us, which is
     the classic adverse-selection channel; MARKET pays to cross.
  D. Is it concentrated at the instrument's known bad boundaries (broker hour 00
     rollover, M15 bar edges)?  If so it is a defect, not a market fact.

Everything is priced against F1's all-in cost of 0.2868 R/trade.
"""
import gzip, json, pickle, sys
import datetime as dt
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f3_walk import GEOM, load_symbol_series, log

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = HERE
MONTHS = ["feb", "apr", "may", "jun", "jul"]
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
R_USD = 250.0
ALL_IN_COST_R = 0.2868          # F1
LOOKBACKS = [1, 5, 15, 30, 60]


def collect(month):
    ser = load_symbol_series(month)
    trades = pickle.load(gzip.open(TMP / f"f3_trades_{month}.pkl.gz", "rb"))
    out = []
    for t in trades:
        S = ser.get(t["sym"])
        if S is None:
            continue
        d = 1 if str(t["side"]).upper() == "LONG" else -1
        tm = S["t"]
        fi = int(np.searchsorted(tm, t["fill_min"], side="left"))
        if fi >= len(tm) or tm[fi] != t["fill_min"]:
            continue
        risk, fp = t["risk"], t["fp"]
        # ---- A: the fill bar's OWN range, in R -----------------------------
        bar_rng = (S["h"][fi] - S["l"][fi]) / risk
        fav_bar0 = (S["h"][fi] - fp) * d / risk if d > 0 else (fp - S["l"][fi]) * d / risk
        fav_bar0 = ((S["h"][fi] if d > 0 else S["l"][fi]) - fp) * d / risk
        adv_bar0 = ((S["l"][fi] if d > 0 else S["h"][fi]) - fp) * d / risk
        # ---- B: where the fill sits in the recent range ---------------------
        a = max(fi - 30, 0)
        pre_h = float(S["h"][a:fi].max()) if fi > a else np.nan
        pre_l = float(S["l"][a:fi].min()) if fi > a else np.nan
        rngw = pre_h - pre_l
        pct = (fp - pre_l) / rngw if rngw > 0 else np.nan          # 1.0 = at the top
        pct_dir = pct if d > 0 else (1.0 - pct)                    # 1.0 = extreme in OUR favour
        pre = {}
        for L in LOOKBACKS:
            j = fi - L
            pre[L] = float((S["c"][fi - 1] - S["c"][j]) * d / risk) if j >= 0 and fi >= 1 else np.nan
        # ---- immediacy of the adverse move ----------------------------------
        out.append(dict(k=t["k"], month=month, day=t["day"], sym=t["sym"], fam=t["fam"],
                        ot=t["ot"], side=t["side"], risk=risk,
                        net=t["term_gross"] - t["ded"], gross=t["term_gross"],
                        mfe=t["mfe"], mae=t["mae"], term=t["term_kind"],
                        peak_bars=t["peak_bars"], fill_min=int(t["fill_min"]),
                        sub=int(t["sub"]),
                        bar_range_R=float(bar_rng), fav_bar0_R=float(fav_bar0),
                        adv_bar0_R=float(adv_bar0),
                        fill_pct_of_30bar_range=float(pct_dir),
                        **{f"pre_move_{L}m_R": pre[L] for L in LOOKBACKS}))
    log(stage="fill_month", month=month, n=len(out))
    return out


def boot_days(v, days, n=2500, seed=61):
    v = np.asarray(v, float)
    ok = np.isfinite(v)
    v = v[ok]; days = np.asarray(days)[ok]
    if len(v) < 30:
        return float("nan"), [float("nan")] * 2
    ud, inv = np.unique(days, return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ud))]
    rng = np.random.default_rng(seed)
    mu = np.array([v[np.concatenate([idx[i] for i in rng.integers(0, len(ud), len(ud))])].mean()
                   for _ in range(n)])
    return float(v.mean()), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))]


def main():
    rows = []
    for m in MONTHS:
        rows += collect(m)
    net = np.array([r["net"] for r in rows]); day = np.array([r["day"] for r in rows])
    ot = np.array([r["ot"] for r in rows]); term = np.array([r["term"] for r in rows])
    mfe = np.array([r["mfe"] for r in rows]); pb = np.array([r["peak_bars"] for r in rows])
    brg = np.array([r["bar_range_R"] for r in rows])
    fb0 = np.array([r["fav_bar0_R"] for r in rows])
    pct = np.array([r["fill_pct_of_30bar_range"] for r in rows])
    mon = np.array([r["month"] for r in rows])
    offc = {}

    def off(mi):
        dd = int(mi) // 1440
        if dd not in offc:
            offc[dd] = offset_seconds_at_utc(EPOCH + dt.timedelta(minutes=dd * 1440),
                                             NEW_YORK_PLUS_7) // 3600
        return offc[dd]

    out = {"schema": "gtos.f3.fill.v1", "n": len(rows), "R_usd": R_USD,
           "priced_against_all_in_cost_R": ALL_IN_COST_R}

    # ---- A. artifact check ---------------------------------------------------
    stop = term == "STOP"
    out["A_bar_resolution_artifact"] = dict(
        question="is the '+0.42 R one minute in' peak a real micro-extreme, or the "
                 "range of the single M1 bar the fill lands in?",
        median_fill_bar_range_R=float(np.median(brg)),
        median_fav_within_fill_bar_R=float(np.median(fb0)),
        share_of_trades_whose_PEAK_is_the_fill_bar=float((pb == 0).mean()),
        share_of_STOP_losers_whose_PEAK_is_the_fill_bar=float((pb[stop] == 0).mean()),
        median_peak_bars_all=float(np.median(pb)),
        median_peak_bars_STOP=float(np.median(pb[stop])),
        median_mfe_STOP=float(np.median(mfe[stop])),
        verdict_note="if median_fav_within_fill_bar_R is of the same order as the "
                     "reported early peak, the early peak is bar resolution, not a "
                     "micro-extreme that could have been exited at")
    # what the M1 grid can even resolve
    out["A_bar_resolution_artifact"]["fill_bar_range_R_deciles"] = [
        float(x) for x in np.quantile(brg, np.linspace(0.1, 0.9, 9))]

    # ---- B. is the fill at a local extreme against us? ----------------------
    m0, c0 = boot_days(pct, day)
    out["B_fill_position_in_recent_range"] = dict(
        definition="percentile of the fill price inside the preceding 30 M1 bars' "
                   "high-low range, oriented so 1.0 = the fill is at the extreme IN "
                   "OUR FAVOUR (we bought the top / sold the bottom); 0.5 = mid-range",
        mean=m0, ci95_dayblock=c0,
        mean_by_order_type={o: float(np.nanmean(pct[ot == o])) for o in sorted(set(ot))},
        mean_by_terminal={k: float(np.nanmean(pct[term == k])) for k in sorted(set(term))})
    q = np.nanquantile(pct, np.linspace(0, 1, 6))
    out["B_fill_position_in_recent_range"]["net_R_by_quintile"] = {}
    for a in range(5):
        hi = pct <= q[a + 1] if a == 4 else pct < q[a + 1]
        k = np.isfinite(pct) & (pct >= q[a]) & hi
        mu, ci = boot_days(net[k], day[k])
        out["B_fill_position_in_recent_range"]["net_R_by_quintile"][f"{q[a]:.3f}-{q[a+1]:.3f}"] = \
            dict(n=int(k.sum()), mean_net_R=mu, ci95_dayblock=ci,
                 mean_mfe_R=float(mfe[k].mean()))
    out["B_pre_fill_move"] = {}
    for L in LOOKBACKS:
        v = np.array([r[f"pre_move_{L}m_R"] for r in rows])
        mu, ci = boot_days(v, day)
        qq = np.nanquantile(v, np.linspace(0, 1, 6))
        cells = {}
        for a in range(5):
            hi = v <= qq[a + 1] if a == 4 else v < qq[a + 1]
            k = np.isfinite(v) & (v >= qq[a]) & hi
            nm, nc = boot_days(net[k], day[k])
            cells[f"{qq[a]:+.3f}..{qq[a+1]:+.3f}"] = dict(n=int(k.sum()), mean_net_R=nm,
                                                          ci95_dayblock=nc)
        out["B_pre_fill_move"][f"{L}m"] = dict(
            mean_pre_move_R=mu, ci95_dayblock=ci,
            note="signed in the trade's own direction: positive = price already moved "
                 "our way before we were filled",
            net_R_by_pre_move_quintile=cells)

    # ---- C. by order type ----------------------------------------------------
    out["C_by_order_type"] = {}
    for o in sorted(set(ot)):
        k = ot == o
        mu, ci = boot_days(net[k], day[k])
        out["C_by_order_type"][o] = dict(
            n=int(k.sum()), mean_net_R=mu, ci95_dayblock=ci,
            mean_mfe_R=float(mfe[k].mean()),
            share_peak_is_fill_bar=float((pb[k] == 0).mean()),
            median_peak_bars=float(np.median(pb[k])),
            mean_fill_pct_of_range=float(np.nanmean(pct[k])),
            mean_pre_move_15m_R=float(np.nanmean(
                [r["pre_move_15m_R"] for r, kk in zip(rows, k) if kk])),
            stop_share=float((term[k] == "STOP").mean()))

    # ---- D. boundaries -------------------------------------------------------
    fm = np.array([r["fill_min"] for r in rows])
    sb = np.array([r["sub"] for r in rows])
    bh = np.array([(int(x) + off(x) * 60) % 1440 for x in fm])
    out["D_boundaries"] = {}
    for nm, k in (("fill_within_30min_of_broker_rollover", (bh < 30) | (bh >= 1410)),
                  ("fill_in_broker_hour_00", bh // 60 == 0),
                  ("submission_on_M15_grid", (sb % 15) == 0),
                  ("submission_off_M15_grid", (sb % 15) != 0)):
        if k.sum() < 100:
            continue
        mu, ci = boot_days(net[k], day[k])
        out["D_boundaries"][nm] = dict(
            n=int(k.sum()), share=float(k.mean()), mean_net_R=mu, ci95_dayblock=ci,
            mean_fill_pct_of_range=float(np.nanmean(pct[k])),
            mean_net_R_elsewhere=float(net[~k].mean()))

    # ---- reconciliation with F1's population statement ----------------------
    out["E_reconciliation_with_F1"] = dict(
        n_stop_losers=int(stop.sum()),
        share_of_stop_losers_reaching={
            str(th): float((mfe[stop] >= th).mean()) for th in [0.5, 1.0, 1.5, 1.8, 1.9]},
        n_reached_1R_and_ended_negative=int(((mfe >= 1.0) & (net < 0)).sum()),
        their_share_of_pool_loss=float(net[(mfe >= 1.0) & (net < 0)].sum() / net.sum()),
        note="F1 counts path-unambiguous pre-exit-bar crossings on 146,736 fills; this "
             "lane counts running-max MFE at the sealed terminal on 151,743.  The two "
             "populations differ slightly by construction and the shares agree.")
    (OUT / "F3_FILL.json").write_text(json.dumps(out, indent=1))
    with gzip.open(TMP / "f3_fill_rows.pkl.gz", "wb") as fh:
        pickle.dump(rows, fh, protocol=5)
    print(json.dumps(out["A_bar_resolution_artifact"], indent=1))
    print(json.dumps(out["C_by_order_type"], indent=1))
    print(json.dumps(out["E_reconciliation_with_F1"], indent=1))


if __name__ == "__main__":
    main()
