"""m1 — the trades the system ACTUALLY took, re-walked on the corrected walker.

f1 established that nobody had ever measured this object: 507 rows, 464 of which its
contract could score, gross +0.05505 / toll 0.07437 / net -0.01932 R per trade.  It is the
last row of the estate's funnel and the only one that describes money the broad stack would
have moved.  It has never been walked with the spread crossed.

Contract: f1's, unchanged — market fill at the decision instant, target 1.5 R and 2.0 R
both published, horizon 120 M1 bars, stop wins ties, the h1 four-term broker-true toll.
The correction is `quote_side.replay_anchor` at the same hour-aware tick spread the toll's
own spread term uses, and the corrected net drops that spread term so it is charged once.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)

import pbg_econ as E  # noqa: E402
import pbg_lib as PL  # noqa: E402

NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601", "2026-01": "202602",
        "2026-02": "202603", "2026-03": "202604", "2026-04": "202605", "2026-05": None}
HOR = 120
NB = 4000


def walk(hi, lo, cl, n, i, *, stop, tgt, long, d, anchor, target_r, horizon=HOR):
    a, b = i + 1, min(i + 1 + horizon, n)
    if a >= b:
        return None
    h, l, c = hi[a:b], lo[a:b], cl[a:b]
    ok = ~np.isnan(c)
    if not ok.any():
        return None
    h, l, c = h[ok], l[ok], c[ok]
    ht, hs = ((h >= tgt, l <= stop) if long else (l <= tgt, h >= stop))
    it = int(np.argmax(ht)) if ht.any() else None
    iss = int(np.argmax(hs)) if hs.any() else None
    if iss is not None and (it is None or iss <= it):
        return -1.0, "stop"
    if it is not None:
        return float(target_r), "target"
    last = float(c[-1])
    return ((last - anchor) / d if long else (anchor - last) / d), "path_end"


def econ(g, c, days, rng, tag):
    n = g.size
    if n == 0:
        return {"tag": tag, "n": 0}
    net = g - c
    ud, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=net, minlength=ud.size)
    k = ud.size
    cnt = np.bincount(inv, minlength=ud.size).astype(float)
    ix = rng.integers(0, k, size=(NB, k))
    bs = s[ix].sum(axis=1) / cnt[ix].sum(axis=1)
    wins, loss = g[g > 0], g[g <= 0]
    aw = float(wins.mean()) if wins.size else 0.0
    al = float(-loss.mean()) if loss.size else 0.0
    pay = aw / al if al else None
    be = 1 / (1 + pay) if pay else None
    nw, nl = net[net > 0], net[net <= 0]
    npay = (float(nw.mean()) / -float(nl.mean())) if nl.size and nl.mean() else None
    nbe = 1 / (1 + npay) if npay else None
    return {"tag": tag, "n": int(n), "gross": float(g.mean()), "cost": float(c.mean()),
            "net": float(net.mean()),
            "net_se": float(net.std(ddof=1) / math.sqrt(n)) if n > 1 else None,
            "net_dayblock_ci95": [float(np.percentile(bs, 2.5)),
                                  float(np.percentile(bs, 97.5))],
            "net_p_le0": float((bs <= 0).mean()),
            "gross_wr": float((g > 0).mean()), "gross_breakeven_wr": be,
            "gross_gap_pp": (float((g > 0).mean()) - be) * 100 if be else None,
            "net_wr": float((net > 0).mean()), "net_breakeven_wr": nbe,
            "net_gap_pp": (float((net > 0).mean()) - nbe) * 100 if nbe else None,
            "day_blocks": int(k)}


def main(out_path):
    tk = json.load(open("/tmp/f1/taken_slim.json"))
    cm = E.CostModel()
    rng = np.random.default_rng(20260807)
    rec = defaultdict(list)
    for w, rows in sorted(tk.items()):
        mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
        tape = E.Tape(list(PL.SYMBOLS), mons)
        for r in rows:
            if r.get("stop_loss") is None or r.get("entry_price") is None:
                continue
            sym = r["symbol"]
            if sym not in tape.c:
                continue
            i = tape.idx(r["decision_time_utc"])
            if not (0 < i < tape.n):
                continue
            e, sl = float(r["entry_price"]), float(r["stop_loss"])
            d = abs(e - sl)
            if not d > 0:
                continue
            lng = r["direction"] == "LONG"
            sgn = 1.0 if lng else -1.0
            s = cm.spread_bps(sym, cm.broker_hour(r["decision_time_utc"])) / 1e4 * e
            px, terms = cm.cost_px(sym, r["decision_time_utc"], e, lng, hold_min=HOR)
            hi, lo, cl, n = tape.h[sym], tape.l[sym], tape.c[sym], tape.n
            row = {"w": w, "day": r["decision_time_utc"][:10], "sym": sym, "d": d,
                   "e": e, "fam": r.get("origin_family"),
                   "px": px, "px_nospread": px - terms["spread"], "s_over_d": s / d,
                   "realised_r": r.get("final_r"), "realised_cost": r.get("cost_r")}
            ok = True
            for T in (1.5, 2.0):
                tgt = e + sgn * T * d
                o = walk(hi, lo, cl, n, i, stop=sl, tgt=tgt, long=lng, d=d, anchor=e,
                         target_r=T)
                oc = walk(hi, lo, cl, n, i, stop=sl + sgn * s, tgt=tgt + sgn * s, long=lng,
                          d=d, anchor=e + sgn * s, target_r=T)
                if o is None or oc is None:
                    ok = False
                    break
                row[f"g_old_{T}"] = o[0]
                row[f"r_old_{T}"] = o[1]
                row[f"g_cor_{T}"] = oc[0]
                row[f"r_cor_{T}"] = oc[1]
            if ok:
                rec["rows"].append(row)
    R = rec["rows"]
    days = np.array([r["day"] for r in R])
    d = np.array([r["d"] for r in R])
    px = np.array([r["px"] for r in R])
    pxn = np.array([r["px_nospread"] for r in R])
    out = {"what": "the trades the broad stack actually took, corrected walker",
           "n_rows_in_file": sum(len(v) for v in tk.values()), "n_walked": len(R),
           "median_spread_over_risk": float(np.median([r["s_over_d"] for r in R])),
           "arms": {}}
    for T in (1.5, 2.0):
        go = np.array([r[f"g_old_{T}"] for r in R])
        gc = np.array([r[f"g_cor_{T}"] for r in R])
        out["arms"][f"OLD_t{T}"] = econ(go, px / d, days, rng, f"OLD_t{T}")
        out["arms"][f"CORRECTED_t{T}"] = econ(gc, pxn / d, days, rng, f"COR_t{T}")
        out["arms"][f"CORRECTED_DOUBLECHARGED_t{T}"] = econ(gc, px / d, days, rng,
                                                            f"COR2_t{T}")
        ch = sum(1 for r in R if r[f"r_old_{T}"] != r[f"r_cor_{T}"])
        mig = defaultdict(int)
        for r in R:
            if r[f"r_old_{T}"] != r[f"r_cor_{T}"]:
                mig[f"{r[f'r_old_{T}']}->{r[f'r_cor_{T}']}"] += 1
        out["arms"][f"exit_migration_t{T}"] = {"n_changed": ch,
                                               "share": ch / len(R),
                                               "transitions": dict(mig)}
    # the arm's own realised record, for reference
    sc = [r for r in R if r["realised_r"] is not None]
    if sc:
        out["realised_arm_record"] = econ(
            np.array([r["realised_r"] for r in sc]),
            np.array([r["realised_cost"] or 0.0 for r in sc]),
            np.array([r["day"] for r in sc]), rng, "realised")
    json.dump(out, open(out_path, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
