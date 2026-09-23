"""d2_rank — THE REAL RANKER, MEASURED WHERE SELECTION ACTUALLY HAPPENED.

l12 tested the 15-component production score inside the diagnostic pool.  The pool is
100 % counterfactual — every row in it is a candidate the system REFUSED — so that test
could never contain the system's actual pick.  This lane rebuilds each decision window as
`pool rows (refused) UNION taken rows (executed)` and asks the question directly:

    of the candidates alive in the same decision window, where did the one the system
    actually took rank, by realised net R?

plus the three controls that make the answer readable: the window oracle (best available),
a random pick from the same window, and the reconstructed production score's own pick.

Outcome contract: the honest first-touch walk — a limit that is never touched books 0 R and
0 cost ("if it does not fill we simply do not trade"), the target is the row's own
`policy_target_r`, the stop is −1R, horizon 120 M1 bars, tie inside a bar goes to the stop.
Toll is the h1 broker-true four-term basis at the row's own entry.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pbg"))
sys.path.insert(0, str(HERE.parents[5]))
os.chdir(str(HERE.parents[5]))

import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

ROOTD = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725"
FA2 = "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725"
POOL = {
    "2025-10": f"{FA2}/phase19/receipts/pools/LP_october_2025_S0R0_POOL_V1.jsonl.gz",
    "2025-11": f"{FA2}/phase19/receipts/pools/LP_november_2025_S0R0_POOL_V1.jsonl.gz",
    "2025-12": f"{FA2}/phase19/receipts/pools/LP_december_2025_S0R0_POOL_V1.jsonl.gz",
    "2026-01": f"{ROOTD}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
    "2026-02": f"{ROOTD}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
    "2026-03": f"{ROOTD}/phase19/receipts/discovery/e2_MARCH_R0_POOL_V1.jsonl.gz",
    "2026-04": f"{FA2}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz",
    "2026-05": f"{FA2}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz",
}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601", "2026-01": "202602",
        "2026-02": "202603", "2026-03": "202604", "2026-04": "202605", "2026-05": None}
HOR = 120


def walk_limit(tape, sym, i, *, entry, stop, long, target_r, horizon=HOR):
    """Honest resting-limit fill (f1's contract, unchanged)."""
    d = abs(entry - stop)
    if not (d > 0):
        return None
    a, b = i, min(i + horizon, tape.n)
    if a >= b:
        return None
    hi, lo = tape.h[sym][a:b], tape.l[sym][a:b]
    ok = ~np.isnan(hi)
    if not ok.any():
        return None
    idxs = np.nonzero(ok)[0]
    touched = (lo[idxs] <= entry) if long else (hi[idxs] >= entry)
    if not touched.any():
        return (0.0, "no_fill", None)
    j = int(idxs[int(np.argmax(touched))])
    res = E.walk(tape, sym, a + j, entry=entry, stop=stop, long=long,
                 target_r=target_r, horizon=horizon - j - 1)
    if res is None:
        return (0.0, "no_fill", None)
    return (res[0], res[1], j)


# the production score, weights + source lines from l12b_full_score.py (which read them
# out of moonshot_scheduler_v4_best_trade_allocator.py / selector_v4.py)
def prod_score(r):
    ev, p, c = r.get("candidate_ev_r"), r.get("candidate_probability"), r.get("cost_r")
    f = r.get("execution_fill_probability")
    k = r.get("source_completeness")
    cf = r.get("candidate_confidence")
    if None in (ev, p, c, cf):
        return None
    k = 1.0 if k is None else max(0.0, min(1.0, float(k)))
    f = 0.0 if f is None else float(f)
    pm, fm = max(0.0, min(1.0, p)), max(0.0, min(1.0, f))
    act = str(r.get("effective_selector_action") or "").lower()
    return (0.55 * ev + 1.20 * (p - 0.50) + 0.20 * cf + 0.15 * k + 0.10 * f
            + 6.00 * max(0.0, ev - c) * pm * fm * k - 0.20 * 0.35 - 0.80 * c
            - 1.50 * max(0.0, 0.80 - f) + (-0.20 if "reduced-risk" in act else 0.0))


def load_pool(w):
    out = []
    with gzip.open(POOL[w], "rt") as fh:
        for line in fh:
            r = json.loads(line)
            out.append(r)
    return out


def main():
    taken_all = json.load(open("/tmp/f1/taken_slim.json"))
    rng = np.random.default_rng(20260806)
    res = {}
    rows_out = []
    for w in sorted(POOL):
        mons = [w.replace("-", "")] + ([NEXT[w]] if NEXT.get(w) else [])
        tape = E.Tape(list(L.SYMBOLS), mons)
        cm = E.CostModel()
        pool = load_pool(w)
        taken = taken_all.get(w, [])
        recs = []
        for src, rr in (("pool", pool), ("taken", taken)):
            for r in rr:
                sym = r.get("symbol")
                if sym not in tape.c:
                    continue
                t = r.get("decision_time_utc")
                e = r.get("entry_price")
                sl = r.get("stop_loss")
                if not (t and e and sl):
                    continue
                lng = str(r.get("direction") or r.get("side") or "").upper().startswith("L")
                i = tape.idx(t)
                if not (0 < i < tape.n):
                    continue
                tgt = r.get("policy_target_r") or 2.0
                o = walk_limit(tape, sym, i, entry=float(e), stop=float(sl), long=lng,
                               target_r=float(tgt))
                if o is None:
                    continue
                d = abs(float(e) - float(sl))
                px, _ = cm.cost_px(sym, t, float(e), lng, hold_min=HOR)
                filled = o[1] != "no_fill"
                recs.append({
                    "src": src, "w": w, "t": t, "day": t[:10], "sym": sym,
                    "fam": r.get("origin_family") or r.get("setup_family"),
                    "g": float(o[0]), "c": (px / d) if filled else 0.0,
                    "filled": bool(filled),
                    "rank": r.get("risk_finalizer_rank"),
                    "score": prod_score(r),
                    "p": r.get("candidate_probability"), "ev": r.get("candidate_ev_r"),
                    "fp": r.get("execution_fill_probability"),
                    "conf": r.get("candidate_confidence"),
                    "cost_model_r": r.get("cost_r"),
                    "risk_pct": r.get("risk_per_trade_pct"),
                    "approved_risk_pct": r.get("approved_risk_pct"),
                    "final_r": r.get("final_r"), "net_r_arm": r.get("net_r"),
                })
        for r in recs:
            r["net"] = r["g"] - r["c"]
        rows_out.extend(recs)

        # ---- window frames
        wins = defaultdict(list)
        for r in recs:
            wins[r["t"]].append(r)
        sel_wins = {k: v for k, v in wins.items() if any(x["src"] == "taken" for x in v)}
        stats = {
            "n_pool": sum(1 for r in recs if r["src"] == "pool"),
            "n_taken": sum(1 for r in recs if r["src"] == "taken"),
            "n_windows_total": len(wins),
            "n_windows_with_a_pick": len(sel_wins),
            "mean_candidates_per_window_all": float(np.mean([len(v) for v in wins.values()])),
            "mean_candidates_per_selected_window": float(
                np.mean([len(v) for v in sel_wins.values()])) if sel_wins else None,
        }
        # percentile of the taken row's net inside its own window (1.0 = best available)
        pcts, tak, orc, rnd, wor, nalt = [], [], [], [], [], []
        for k, v in sel_wins.items():
            if len(v) < 2:
                continue
            nets = np.array([x["net"] for x in v])
            for x in v:
                if x["src"] != "taken":
                    continue
                pct = float((nets < x["net"]).mean() + 0.5 * (nets == x["net"]).mean())
                pcts.append(pct)
                tak.append(x["net"])
                orc.append(float(nets.max()))
                wor.append(float(nets.min()))
                rnd.append(float(nets.mean()))
                nalt.append(len(v))
        stats["selection_percentile"] = {
            "n": len(pcts),
            "mean_percentile": float(np.mean(pcts)) if pcts else None,
            "median_percentile": float(np.median(pcts)) if pcts else None,
            "share_above_window_mean": float(np.mean(np.array(tak) > np.array(rnd)))
            if pcts else None,
            "taken_net": float(np.mean(tak)) if pcts else None,
            "window_random_net": float(np.mean(rnd)) if pcts else None,
            "window_oracle_net": float(np.mean(orc)) if pcts else None,
            "window_worst_net": float(np.mean(wor)) if pcts else None,
            "mean_alternatives": float(np.mean(nalt)) if pcts else None,
        }
        # production score's own pick in the SAME windows
        sc_pick, sc_n = [], 0
        for k, v in sel_wins.items():
            vv = [x for x in v if x["score"] is not None]
            if len(vv) < 2:
                continue
            b = max(vv, key=lambda x: x["score"])
            sc_pick.append(b["net"])
            sc_n += 1
        stats["production_score_pick"] = {
            "n": sc_n, "net": float(np.mean(sc_pick)) if sc_pick else None}
        # rank-vs-outcome, directly: spearman of risk_finalizer_rank with net
        rk = [(r["rank"], r["net"]) for r in recs if isinstance(r["rank"], (int, float))]
        if len(rk) > 100:
            a = np.array([x[0] for x in rk], dtype=float)
            b = np.array([x[1] for x in rk], dtype=float)
            ra = _rankdata(a)
            rb = _rankdata(b)
            stats["risk_finalizer_rank_vs_net"] = {
                "n": len(rk),
                "spearman": float(np.corrcoef(ra, rb)[0, 1]),
                "by_rank": {str(int(q)): {
                    "n": int((a == q).sum()), "net": float(b[a == q].mean())}
                    for q in sorted(set(a.tolist()))[:12]},
            }
        # the score's own decile, over EVERY row that carries one
        sc = np.array([r["score"] for r in recs if r["score"] is not None], dtype=float)
        sn = np.array([r["net"] for r in recs if r["score"] is not None], dtype=float)
        if sc.size > 500:
            q = np.quantile(sc, np.linspace(0, 1, 11))
            dec = []
            for a in range(10):
                m = (sc >= q[a]) & (sc <= q[a + 1] if a == 9 else sc < q[a + 1])
                dec.append({"decile": a + 1, "n": int(m.sum()),
                            "score_lo": float(q[a]), "net": float(sn[m].mean()),
                            "win": float((sn[m] > 0).mean())})
            stats["production_score_deciles"] = dec
            stats["production_score_spearman"] = float(
                np.corrcoef(_rankdata(sc), _rankdata(sn))[0, 1])
        res[w] = stats
        print(w, json.dumps(stats["selection_percentile"]), flush=True)

    Path("/tmp/d2/out/D2_RANK_V1.json").write_text(json.dumps(res, indent=1, default=str))
    with gzip.open("/tmp/d2/out/D2_RANK_ROWS_V1.jsonl.gz", "wt") as fh:
        for r in rows_out:
            fh.write(json.dumps(r, default=str) + "\n")
    print("rows", len(rows_out))


def _rankdata(a):
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a), dtype=float)
    r[o] = np.arange(len(a), dtype=float)
    return r


if __name__ == "__main__":
    main()
