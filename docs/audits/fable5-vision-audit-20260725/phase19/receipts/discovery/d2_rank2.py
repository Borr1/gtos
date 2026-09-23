"""d2_rank2 — decompose the real ranker's value, and test whether it is a cost filter.

Reads D2_RANK_ROWS_V1.jsonl.gz (pool UNION taken, honest fill, broker-true toll).

Three questions:
  1. The +0.222 R/trade the real pick earns over a random pick from the SAME decision
     window: how much of it is gross and how much is a cheaper toll?
  2. Does it survive a geometry-matched control (same window, same symbol, toll within
     +/-25 %)?  f1 measured ~40 % of the raw taken-vs-roster gap is geometry.
  3. Does the reconstructed production score order GROSS, or only NET?  A score that
     orders net but not gross is a fee schedule, not a ranker (the swarm's dead
     headline #2, generalised).
"""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = "/tmp/d2/out/D2_RANK_ROWS_V1.jsonl.gz"


def rankdata(a):
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a), float)
    r[o] = np.arange(len(a), dtype=float)
    return r


def main():
    rows = []
    with gzip.open(SRC, "rt") as fh:
        for line in fh:
            rows.append(json.loads(line))
    for r in rows:
        r["net"] = r["g"] - r["c"]
    out = {"n_rows": len(rows)}

    wins = defaultdict(list)
    for r in rows:
        wins[(r["w"], r["t"])].append(r)
    sel = {k: v for k, v in wins.items() if any(x["src"] == "taken" for x in v)}

    # ---------------- 1. gross / cost decomposition, paired inside the window
    dg, dc, dn, tg, tc, rg, rc = [], [], [], [], [], [], []
    for k, v in sel.items():
        if len(v) < 2:
            continue
        G = np.array([x["g"] for x in v])
        C = np.array([x["c"] for x in v])
        for x in v:
            if x["src"] != "taken":
                continue
            tg.append(x["g"])
            tc.append(x["c"])
            rg.append(float(G.mean()))
            rc.append(float(C.mean()))
            dg.append(x["g"] - float(G.mean()))
            dc.append(x["c"] - float(C.mean()))
            dn.append((x["g"] - x["c"]) - float((G - C).mean()))
    out["WINDOW_PAIRED"] = {
        "n": len(dn),
        "taken_gross": float(np.mean(tg)), "window_gross": float(np.mean(rg)),
        "taken_cost": float(np.mean(tc)), "window_cost": float(np.mean(rc)),
        "delta_gross": float(np.mean(dg)), "delta_cost": float(np.mean(dc)),
        "delta_net": float(np.mean(dn)),
        "share_of_delta_net_from_cost": float(-np.mean(dc) / np.mean(dn))
        if np.mean(dn) else None,
        "t_delta_net": float(np.mean(dn) / (np.std(dn, ddof=1) / np.sqrt(len(dn)))),
        "t_delta_gross": float(np.mean(dg) / (np.std(dg, ddof=1) / np.sqrt(len(dg)))),
    }

    # ---------------- 2. geometry-matched control: same window, same symbol, toll +/-25 %
    md, mdg, mn = [], [], 0
    for k, v in sel.items():
        for x in v:
            if x["src"] != "taken":
                continue
            ctl = [y for y in v if y is not x and y["sym"] == x["sym"]
                   and x["c"] > 0 and 0.75 * x["c"] <= y["c"] <= 1.25 * x["c"]]
            if len(ctl) < 1:
                continue
            md.append((x["g"] - x["c"]) - float(np.mean([y["g"] - y["c"] for y in ctl])))
            mdg.append(x["g"] - float(np.mean([y["g"] for y in ctl])))
            mn += 1
    out["MATCHED_SAME_SYMBOL_SAME_TOLL"] = {
        "n": mn,
        "delta_net": float(np.mean(md)) if md else None,
        "delta_gross": float(np.mean(mdg)) if md else None,
        "t_delta_net": float(np.mean(md) / (np.std(md, ddof=1) / np.sqrt(len(md))))
        if len(md) > 2 else None,
    }
    # looser: same window, any symbol, toll +/-25 %
    md2 = []
    for k, v in sel.items():
        for x in v:
            if x["src"] != "taken":
                continue
            ctl = [y for y in v if y is not x and x["c"] > 0
                   and 0.75 * x["c"] <= y["c"] <= 1.25 * x["c"]]
            if ctl:
                md2.append((x["g"] - x["c"]) - float(np.mean([y["g"] - y["c"] for y in ctl])))
    out["MATCHED_SAME_TOLL_ANY_SYMBOL"] = {
        "n": len(md2), "delta_net": float(np.mean(md2)) if md2 else None,
        "t": float(np.mean(md2) / (np.std(md2, ddof=1) / np.sqrt(len(md2))))
        if len(md2) > 2 else None}

    # ---------------- 3. does the score order GROSS or only NET
    sc = np.array([r["score"] for r in rows if r["score"] is not None], float)
    gg = np.array([r["g"] for r in rows if r["score"] is not None], float)
    cc = np.array([r["c"] for r in rows if r["score"] is not None], float)
    nn = gg - cc
    rs = rankdata(sc)
    out["SCORE_ORDERING"] = {
        "n": int(sc.size),
        "spearman_score_vs_net": float(np.corrcoef(rs, rankdata(nn))[0, 1]),
        "spearman_score_vs_gross": float(np.corrcoef(rs, rankdata(gg))[0, 1]),
        "spearman_score_vs_cost": float(np.corrcoef(rs, rankdata(cc))[0, 1]),
    }
    q = np.quantile(sc, np.linspace(0, 1, 11))
    dec = []
    for a in range(10):
        m = (sc >= q[a]) & ((sc <= q[a + 1]) if a == 9 else (sc < q[a + 1]))
        dec.append({"decile": a + 1, "n": int(m.sum()), "gross": float(gg[m].mean()),
                    "cost": float(cc[m].mean()), "net": float(nn[m].mean()),
                    "win": float((gg[m] > 0).mean())})
    out["SCORE_DECILES"] = dec
    # and the same for each component the score is built from
    comp = {}
    for f in ("p", "ev", "fp", "conf", "cost_model_r"):
        v = np.array([r[f] if r[f] is not None else np.nan for r in rows], float)
        g2 = np.array([r["g"] for r in rows], float)
        c2 = np.array([r["c"] for r in rows], float)
        m = np.isfinite(v)
        if m.sum() < 500:
            continue
        comp[f] = {
            "n": int(m.sum()),
            "spearman_vs_net": float(np.corrcoef(rankdata(v[m]),
                                                 rankdata((g2 - c2)[m]))[0, 1]),
            "spearman_vs_gross": float(np.corrcoef(rankdata(v[m]), rankdata(g2[m]))[0, 1]),
        }
    out["COMPONENT_ORDERING"] = comp

    # ---------------- 4. what the ranker is worth as a BOOK at the real capacity
    #   real pick vs (a) random-in-window (b) score's pick (c) window oracle,
    #   all restricted to the same windows.
    real, rndm, orc, scp, wor = [], [], [], [], []
    for k, v in sel.items():
        if len(v) < 2:
            continue
        nets = np.array([x["g"] - x["c"] for x in v])
        vv = [x for x in v if x["score"] is not None]
        for x in v:
            if x["src"] != "taken":
                continue
            real.append(x["g"] - x["c"])
            rndm.append(float(nets.mean()))
            orc.append(float(nets.max()))
            wor.append(float(nets.min()))
            if vv:
                b = max(vv, key=lambda y: y["score"])
                scp.append(b["g"] - b["c"])
    out["BOOK_AT_REAL_CAPACITY"] = {
        "n": len(real), "real_pick": float(np.mean(real)),
        "random_in_window": float(np.mean(rndm)),
        "production_score_pick": float(np.mean(scp)) if scp else None,
        "window_oracle": float(np.mean(orc)), "window_worst": float(np.mean(wor)),
        "capture_real": (np.mean(real) - np.mean(rndm)) / (np.mean(orc) - np.mean(rndm)),
        "capture_score": ((np.mean(scp) - np.mean(rndm)) / (np.mean(orc) - np.mean(rndm)))
        if scp else None,
    }
    Path("/tmp/d2/out/D2_RANK2_V1.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "SCORE_DECILES"},
                     indent=1, default=str))
    print("\nSCORE DECILES")
    for d in out["SCORE_DECILES"]:
        print("d%-3d n=%-6d gross %+.5f cost %.5f net %+.5f win %.4f"
              % (d["decile"], d["n"], d["gross"], d["cost"], d["net"], d["win"]))


if __name__ == "__main__":
    main()
