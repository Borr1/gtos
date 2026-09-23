"""B10 stage 4 -- hour-of-day as a GENERATION parameter, walked on true prices.

The lane's central question: shifting entries away from the expensive hours saves spread,
but an hour may be expensive BECAUSE it is informative, which would make the shift
self-defeating.  Lane 7 tested one blunt form of this (a cash-session veto) and refuted it
at tape-true cost.  This walks the constructive form Lane 7 never built: don't refuse the
trade, DELAY it.

Arms, all on the same 21,684 MARKET candidates and the same M1 bid/ask tape:

  A0        enter at market on the first strictly-post-decision minute      (the incumbent)
  D{n}      enter at market n minutes later, same stop/target LEVELS, same declared risk
  CHEAP     enter at the first minute within 240 whose (symbol, UTC hour) tape spread is
            below that symbol's own median hour -- the cost-surface-conditioned arm
  VETO      refuse the trade entirely when the decision hour is above the symbol's median

Accounting.  The risk unit is held at the trade's own declared ``risk_price`` so that a
delayed entry is measured as what it is -- the same size against the same barriers, filled
later -- rather than silently re-sized.  Gross is ``d*(exit - entry_delayed)/risk``.  Cost
is charged from the TAPE at the actual fill instant (ask-bid at that minute's open),
plus the row's own commission and swap.

Two failure modes are counted rather than dropped, because dropping them is how a delay
arm flatters itself:

  * ``preempted`` -- the stop or target was already touched before the delayed entry.  The
    trade never happens.  Its foregone P&L is recorded separately and reported, because a
    delay rule that only skips winners is not a saving.
  * ``expired``   -- the horizon ends before the delayed entry.

Breadth is reported alongside every R figure, and R/month alongside R/trade, because a
rule that improves R/trade by trading less is not automatically an improvement (Lane 4:
breadth is a step function of cost per trade).
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

M1DIR = os.environ.get("B10_M1DIR", "/Users/borr/.claude/jobs/adb9e69b/tmp/m1")
SYMMAP = {"GER40": "GER40_cash", "JP225": "JP225_cash", "UK100": "UK100_cash",
          "NAS100": "US100_cash", "SPX500": "US500_cash"}
DELAYS = (15, 30, 60, 120, 240)
CHEAP_CAP_MIN = 240


def load_m1(broker="FTMO"):
    out = {}
    for f in glob.glob(f"{M1DIR}/{broker}_*.npz"):
        z = np.load(f, allow_pickle=True)
        s = str(z["symbol"])
        o = np.argsort(z["minute_utc"])
        n = z["n"][o]
        out[s] = dict(t=z["minute_utc"][o].astype("int64"), bh=z["bh"][o], bl=z["bl"][o],
                      ah=z["ah"][o], al=z["al"][o], bo=z["bo"][o], ao=z["ao"][o],
                      n=n, sp=z["sp_sum"][o] / np.maximum(n, 1))
    return out


def cheap_hours(tape: dict, fsym: str) -> set[int]:
    """The hours whose tape median spread is at or below this symbol's own hour median."""
    blk = (tape["accounts"].get("FTMO") or {}).get(fsym)
    if not blk:
        return set(range(24))
    m = {int(h): c["median_mult"] for h, c in blk["by_hour_utc"].items()
         if c.get("median_mult")}
    if not m:
        return set(range(24))
    thr = float(np.median(list(m.values())))
    return {h for h, v in m.items() if v <= thr}


def main(lg_pkl: str, tape_json: str, out_json: str) -> None:
    T = load_m1("FTMO")
    tape = json.load(open(tape_json))
    df = pd.read_pickle(lg_pkl)
    df = df[(df.horizon_min.fillna(0) > 0) & (df.order_type == "MARKET")].reset_index(drop=True)
    ch = {s: cheap_hours(tape, s) for s in T}

    rows = []
    for tsym, g in df.groupby("tsym"):
        A = T.get(tsym)
        if A is None:
            continue
        t, bh, bl, ah, al, bo, ao, sp = (A[k] for k in
                                         ("t", "bh", "bl", "ah", "al", "bo", "ao", "sp"))
        cheap = ch.get(tsym, set(range(24)))
        hour_of = ((t % 1440) // 60).astype("int64")
        for r in g.itertuples():
            d = 1 if r.side == "LONG" else -1
            s0 = int(np.searchsorted(t, r.min_utc, "right"))
            s1 = int(np.searchsorted(t, r.min_utc + int(r.horizon_min), "right"))
            if s1 - s0 < 2:
                continue
            S, TG, risk = r.stop_price, r.target_price, r.risk_price

            def walk(j0: int, fp: float):
                """From index j0 (inclusive, absolute), first barrier and gross R."""
                if j0 >= s1:
                    return ("EXPIRED", np.nan)
                if d > 0:
                    hS, hT = bl[j0:s1] <= S, bh[j0:s1] >= TG
                else:
                    hS, hT = ah[j0:s1] >= S, al[j0:s1] <= TG
                iS = int(np.argmax(hS)) if hS.any() else 10 ** 9
                iT = int(np.argmax(hT)) if hT.any() else 10 ** 9
                if iS <= iT and iS < 10 ** 9:
                    return ("STOP", d * (S - fp) / risk)
                if iT < 10 ** 9:
                    return ("TARGET", d * (TG - fp) / risk)
                xp = float(bo[s1 - 1] if d > 0 else ao[s1 - 1])
                return ("TIME", d * (xp - fp) / risk)

            def touched_before(j: int) -> bool:
                if j <= s0:
                    return False
                if d > 0:
                    return bool((bl[s0:j] <= S).any() or (bh[s0:j] >= TG).any())
                return bool((ah[s0:j] >= S).any() or (al[s0:j] <= TG).any())

            row = {"key": r.key, "symbol": r.symbol, "tsym": tsym, "family": r.family,
                   "side": r.side, "day": r.day, "hour": int(hour_of[s0]),
                   "risk": risk, "comm_r": r.commission_r, "swap_r": r.swap_r,
                   "cheap_hour": bool(int(hour_of[s0]) in cheap)}
            fp0 = float(ao[s0] if d > 0 else bo[s0])
            st0, g0 = walk(s0, fp0)
            row["A0_state"], row["A0_gross"] = st0, g0
            row["A0_spread_r"] = float(sp[s0]) / risk
            for n in DELAYS:
                j = int(np.searchsorted(t, r.min_utc + n, "right"))
                if j >= s1:
                    row[f"D{n}_state"] = "EXPIRED"
                    continue
                if touched_before(j):
                    row[f"D{n}_state"] = "PREEMPTED"
                    row[f"D{n}_foregone"] = g0
                    continue
                fp = float(ao[j] if d > 0 else bo[j])
                st, gr = walk(j, fp)
                row[f"D{n}_state"], row[f"D{n}_gross"] = st, gr
                row[f"D{n}_spread_r"] = float(sp[j]) / risk
                row[f"D{n}_hour"] = int(hour_of[j])
            # CHEAP: first minute in the next 240 whose hour is a cheap hour
            jj = None
            for k in range(0, CHEAP_CAP_MIN + 1, 5):
                j = int(np.searchsorted(t, r.min_utc + k, "right"))
                if j >= s1:
                    break
                if int(hour_of[j]) in cheap:
                    jj = j
                    break
            if jj is None:
                row["CHEAP_state"] = "NO_CHEAP_SLOT"
            elif touched_before(jj):
                row["CHEAP_state"] = "PREEMPTED"
                row["CHEAP_foregone"] = g0
            else:
                fp = float(ao[jj] if d > 0 else bo[jj])
                st, gr = walk(jj, fp)
                row["CHEAP_state"], row["CHEAP_gross"] = st, gr
                row["CHEAP_spread_r"] = float(sp[jj]) / risk
                row["CHEAP_wait_min"] = int(t[jj] - r.min_utc)
                row["CHEAP_hour"] = int(hour_of[jj])
            rows.append(row)
    W = pd.DataFrame(rows)
    W.to_pickle(os.path.splitext(out_json)[0] + "_rows.pkl")

    n_months = 5.0
    span_days = float(pd.to_datetime(W.day).nunique())

    def arm(prefix: str, mask=None) -> dict:
        m = W if mask is None else W[mask]
        st = m.get(f"{prefix}_state")
        if st is None:
            st = pd.Series("ABSENT", index=m.index)
        ok = st.isin(["STOP", "TARGET", "TIME"])
        e = m[ok]
        if f"{prefix}_gross" not in m.columns or len(e) == 0:
            return {"n_entered": 0, "breadth_pct": 0.0,
                    "n_preempted": int((st == "PREEMPTED").sum()),
                    "n_expired": int(st.isin(["EXPIRED", "NO_CHEAP_SLOT"]).sum()),
                    "note": "no candidate survives to this delay -- the median horizon is "
                            "120 M1 bars, so a delay at or beyond it expires every trade"}
        gross = e[f"{prefix}_gross"]
        spread = e[f"{prefix}_spread_r"]
        net = gross - spread - e.comm_r - e.swap_r - 0.02
        pre = (m.loc[st == "PREEMPTED", f"{prefix}_foregone"]
               if ((st == "PREEMPTED").any() and f"{prefix}_foregone" in m.columns)
               else pd.Series(dtype=float))
        pre = pre.dropna()
        return {
            "n_entered": int(len(e)), "breadth_pct": float(100 * len(e) / len(W)),
            "n_preempted": int((st == "PREEMPTED").sum()),
            "n_expired": int((st.isin(["EXPIRED", "NO_CHEAP_SLOT"])).sum()),
            "gross_r_per_trade": float(gross.mean()) if len(e) else None,
            "gross_ci95": [float(gross.mean() - 1.96 * gross.sem()),
                           float(gross.mean() + 1.96 * gross.sem())] if len(e) > 2 else None,
            "spread_r_per_trade": float(spread.mean()) if len(e) else None,
            "net_r_per_trade": float(net.mean()) if len(e) else None,
            "net_ci95": [float(net.mean() - 1.96 * net.sem()),
                         float(net.mean() + 1.96 * net.sem())] if len(e) > 2 else None,
            "total_net_R": float(net.sum()) if len(e) else None,
            "net_R_per_day": float(net.sum() / span_days) if len(e) else None,
            "preempted_foregone_mean_R": float(pre.mean()) if len(pre) else None,
            "preempted_foregone_total_R": float(pre.sum()) if len(pre) else None,
        }

    arms = {"A0_immediate": arm("A0")}
    for n in DELAYS:
        arms[f"D{n}_delay_{n}min"] = arm(f"D{n}")
    arms["CHEAP_wait_for_cheap_hour"] = arm("CHEAP")
    # VETO: refuse the expensive-hour half outright
    v = arm("A0", W.cheap_hour)
    v["note"] = ("VETO arm: A0 restricted to the symbol's own cheap hours. Breadth is "
                 "relative to the FULL candidate set, so it is directly comparable.")
    arms["VETO_cheap_hours_only"] = v
    ve = arm("A0", ~W.cheap_hour)
    ve["note"] = "the half the veto refuses -- is it worse, or only more expensive?"
    arms["VETO_the_refused_half"] = ve

    # the informativeness question, stated as pre-cost gross by hour
    W["A0_pre"] = W.A0_gross
    byh = (W[W.A0_state.isin(["STOP", "TARGET", "TIME"])]
           .groupby("hour")
           .agg(n=("A0_gross", "size"), gross=("A0_gross", "mean"),
                spread=("A0_spread_r", "mean"),
                net=("A0_gross", lambda s: float(s.mean())))
           .reset_index())
    W2 = W[W.A0_state.isin(["STOP", "TARGET", "TIME"])].copy()
    W2["net"] = W2.A0_gross - W2.A0_spread_r - W2.comm_r - W2.swap_r - 0.02
    byh2 = (W2.groupby("hour")
            .agg(n=("net", "size"), gross=("A0_gross", "mean"),
                 gross_sem=("A0_gross", "sem"), spread=("A0_spread_r", "mean"),
                 net=("net", "mean")).reset_index())

    doc = {
        "schema": "b10_entry_timing_v1",
        "population": {"n_candidates": int(len(W)),
                       "window": "FTMO tick overlap 2026-06-18..07-24",
                       "trading_days": span_days,
                       "risk_unit": "held at the trade's own declared risk_price; a delayed "
                                    "entry is the same size against the same barriers"},
        "arms": arms,
        "by_hour_A0": json.loads(byh2.to_json(orient="records")),
        "informativeness_test": {
            "question": "is an expensive hour expensive BECAUSE it is informative?",
            "instrument": "pre-cost gross R by UTC hour on the immediate arm; if the "
                          "expensive hours carry higher gross, avoiding them costs signal",
            "corr_hour_spread_vs_hour_gross": float(
                np.corrcoef(byh2.spread, byh2.gross)[0, 1]),
            "cheap_half_gross": float(W2[W2.cheap_hour].A0_gross.mean()),
            "expensive_half_gross": float(W2[~W2.cheap_hour].A0_gross.mean()),
            "cheap_half_gross_ci95": [
                float(W2[W2.cheap_hour].A0_gross.mean() - 1.96 * W2[W2.cheap_hour].A0_gross.sem()),
                float(W2[W2.cheap_hour].A0_gross.mean() + 1.96 * W2[W2.cheap_hour].A0_gross.sem())],
            "expensive_half_gross_ci95": [
                float(W2[~W2.cheap_hour].A0_gross.mean() - 1.96 * W2[~W2.cheap_hour].A0_gross.sem()),
                float(W2[~W2.cheap_hour].A0_gross.mean() + 1.96 * W2[~W2.cheap_hour].A0_gross.sem())],
        },
    }
    json.dump(doc, open(out_json, "w"), indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in
                          ("n_entered", "breadth_pct", "n_preempted", "gross_r_per_trade",
                           "spread_r_per_trade", "net_r_per_trade", "total_net_R",
                           "preempted_foregone_total_R")}
                      for k, v in arms.items()}, indent=1))
    print("\ninformativeness:", json.dumps(doc["informativeness_test"], indent=1))
    print("\nby hour:")
    print(byh2.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
