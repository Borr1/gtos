#!/usr/bin/env python3
"""d7 stage 3 — the empirical adjudicator.

Stage 2's required-AUC curve is model-based (a Gaussian-copula noisy oracle). This stage
answers the same question WITHOUT a model: build the best ex-ante rules the system's own
observables allow, fit them on Oct-Jan, and measure realised net on Feb-May at every
selection rate. Plus the loser-cut mechanism probe and the per-window robustness of
whatever survives.
"""
import gzip, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/tmp/d7"
A = np.load(os.path.join(OUT, "d7_arrays.npz"))
NM = json.load(open(os.path.join(OUT, "d7_names.json")))
SYMS = {int(k): v for k, v in NM["syms"].items()}
FAMS = {int(k): v for k, v in NM["fams"].items()}
WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]

M = A["clean"]
g, c, d_bps = A["g"][M], A["c"][M], A["d_bps"][M]
sym, fam, win = A["sym"][M], A["fam"][M], A["win"][M]
net = g - c
n = len(g)
TR = np.isin(win, [0, 1, 2, 3]); TE = ~TR
R = {"schema": "gtos.wave19.d7.stage3.v1", "n_clean": int(n),
     "train": "2025-10..2026-01", "test": "2026-02..2026-05",
     "n_train": int(TR.sum()), "n_test": int(TE.sum())}

RATES = [1.0, 0.50, 0.25, 0.10, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001, 0.000484]
rng = np.random.default_rng(7)


def curve(score_te, tag, higher_is_better=True):
    s = score_te if higher_is_better else -score_te
    order = np.argsort(-s, kind="stable")
    gte, cte = g[TE], c[TE]
    NT = len(order)
    rows = []
    for f in RATES:
        k = max(1, int(round(f * NT)))
        idx = order[:k]
        gg, cc = gte[idx], cte[idx]
        nn = gg - cc
        wl = gg > 0
        aa = float(gg[wl].mean()) if wl.sum() else 0.0
        bb = float((-gg[~wl]).mean()) if (~wl).sum() else 0.0
        preq = (bb + float(cc.mean())) / (aa + bb) if (aa + bb) > 0 else float("nan")
        sd = float(nn.std(ddof=1)) if k > 1 else float("nan")
        se = sd / math.sqrt(k) if k > 1 else float("nan")
        rows.append({"retain": f, "n": k, "gross": float(gg.mean()), "toll": float(cc.mean()),
                     "net": float(nn.mean()), "net_se": se,
                     "net_t": float(nn.mean()) / se if se else None,
                     "win_rate": float(wl.mean()), "required_win_rate": preq,
                     "gap_pp": (float(wl.mean()) - preq) * 100.0,
                     "median_d_bps": float(np.median(d_bps[TE][idx]))})
    return {"tag": tag, "rows": rows}


# ---------------- build ex-ante scores, fitted on TRAIN only ----------------
cost_price_bps = c * d_bps
med_sym = {}
for i in np.unique(sym[TR]):
    m = sym[TR] == i
    med_sym[int(i)] = float(np.median(cost_price_bps[TR][m]))
glob = float(np.median(cost_price_bps[TR]))
pred_toll_te = np.array([med_sym.get(int(s_), glob) for s_ in sym[TE]]) / d_bps[TE]

key_tr = sym[TR].astype(np.int32) * 100 + fam[TR]
key_te = sym[TE].astype(np.int32) * 100 + fam[TE]
mu_g, mu_n = {}, {}
for kk in np.unique(key_tr):
    m = key_tr == kk
    if m.sum() >= 100:
        mu_g[int(kk)] = float(g[TR][m].mean()); mu_n[int(kk)] = float(net[TR][m].mean())
gg0, nn0 = float(g[TR].mean()), float(net[TR].mean())
pred_gross_te = np.array([mu_g.get(int(k_), gg0) for k_ in key_te])
pred_net_te = np.array([mu_n.get(int(k_), nn0) for k_ in key_te])

scores = {
    "S1_cheap_toll_exante": (-pred_toll_te, True),
    "S2_wide_risk_distance": (d_bps[TE], True),
    "S3_trainfit_symfam_gross": (pred_gross_te, True),
    "S4_trainfit_symfam_net": (pred_net_te, True),
    "S5_combined_predgross_minus_predtoll": (pred_gross_te - pred_toll_te, True),
    "S6_random_control": (rng.standard_normal(int(TE.sum())), True),
}
R["curves"] = {}
for k, (s, hib) in scores.items():
    R["curves"][k] = curve(s, k, hib)

# oracle ceilings on the SAME test rows, for scale
R["curves"]["ORACLE_true_net"] = curve(net[TE], "ORACLE_true_net")

# ---------------- best surviving cell: robustness per window ----------------
best = None
for k, cv in R["curves"].items():
    if k in ("ORACLE_true_net", "S6_random_control"):
        continue
    for row in cv["rows"]:
        if row["n"] >= 200 and (best is None or row["net"] > best[1]["net"]):
            best = (k, row)
R["best_oos_cell_n_ge_200"] = {"score": best[0], **best[1]} if best else None
if best:
    k, row = best
    s, hib = scores[k]
    order = np.argsort(-(s if hib else -s), kind="stable")
    kk = max(1, int(round(row["retain"] * len(order))))
    idx = order[:kk]
    wsel = win[TE][idx]
    per = {}
    for wi in np.unique(wsel):
        m = wsel == wi
        per[WINDOWS[int(wi)]] = {"n": int(m.sum()), "gross": float(g[TE][idx][m].mean()),
                                 "toll": float(c[TE][idx][m].mean()),
                                 "net": float((g[TE][idx][m] - c[TE][idx][m]).mean())}
    R["best_oos_cell_by_window"] = per

# ---------------- what a 3-fold rolling refit looks like (no single split luck) ------
folds = [([0, 1, 2, 3], [4]), ([0, 1, 2, 3, 4], [5]), ([0, 1, 2, 3, 4, 5], [6]),
         ([0, 1, 2, 3, 4, 5, 6], [7])]
roll = []
for tr, te in folds:
    mtr = np.isin(win, tr); mte = np.isin(win, te)
    ms = {}
    for i in np.unique(sym[mtr]):
        mm = sym[mtr] == i
        ms[int(i)] = float(np.median(cost_price_bps[mtr][mm]))
    gl = float(np.median(cost_price_bps[mtr]))
    pt = np.array([ms.get(int(s_), gl) for s_ in sym[mte]]) / d_bps[mte]
    ktr = sym[mtr].astype(np.int32) * 100 + fam[mtr]; kte = sym[mte].astype(np.int32) * 100 + fam[mte]
    mg = {}
    for kk2 in np.unique(ktr):
        mm = ktr == kk2
        if mm.sum() >= 100:
            mg[int(kk2)] = float(g[mtr][mm].mean())
    g0 = float(g[mtr].mean())
    pg = np.array([mg.get(int(x), g0) for x in kte])
    sc = pg - pt
    o = np.argsort(-sc, kind="stable")
    NTe = len(o)
    entry = {"test_window": WINDOWS[te[0]], "n_test": NTe}
    for f in (0.25, 0.10, 0.05, 0.01):
        k2 = max(1, int(round(f * NTe)))
        ii = o[:k2]
        entry[f"net@{f}"] = float((g[mte][ii] - c[mte][ii]).mean())
        entry[f"gross@{f}"] = float(g[mte][ii].mean())
        entry[f"toll@{f}"] = float(c[mte][ii].mean())
        entry[f"n@{f}"] = k2
    roll.append(entry)
R["rolling_refit_S5"] = roll

# ---------------- loser-cut mechanism probe (w0 working set; POOL population) ------
w0 = os.path.join(HERE, "w0_WORKING_SET.jsonl.gz")
if os.path.exists(w0):
    mae, wcf, btt, bts = [], [], [], []
    with gzip.open(w0, "rt") as f:
        for line in f:
            r = json.loads(line)
            mae.append(r.get("mae_r")); wcf.append(r.get("which_came_first"))
            btt.append(r.get("bars_to_target")); bts.append(r.get("bars_to_stop"))
    mae = np.array([x if x is not None else np.nan for x in mae], dtype=float)
    wcf = np.array([str(x) for x in wcf])
    tgt = np.char.find(wcf, "target") >= 0
    ok = ~np.isnan(mae)
    probe = {"population": "w0_WORKING_SET (COUNTERFACTUAL POOL, 27,658 rows) - mechanism only, "
                           "not a population fact for the roster",
             "n_rows": int(len(mae)), "n_with_mae": int(ok.sum()),
             "n_target_first": int((tgt & ok).sum()),
             "which_came_first_values": {k: int((wcf == k).sum()) for k in np.unique(wcf)[:8]}}
    for thr in (0.20, 0.30, 0.426, 0.50, 0.60, 0.75):
        killed = (mae[tgt & ok] >= thr)
        probe[f"winners_killed_by_stop_at_{thr}R"] = float(killed.mean()) if killed.size else None
    R["loser_cut_mechanism_probe"] = probe

json.dump(R, open(os.path.join(OUT, "D7_STAGE3.json"), "w"), indent=1, default=float)
print("wrote D7_STAGE3.json")
for k, cv in R["curves"].items():
    print("\n" + k)
    for row in cv["rows"]:
        print(f"   retain {row['retain']:<8} n {row['n']:>7}  gross {row['gross']:+.5f}  toll {row['toll']:.5f}"
              f"  net {row['net']:+.5f}  t {row['net_t'] if row['net_t'] is None else round(row['net_t'],2)}"
              f"  wr {row['win_rate']:.4f} req {row['required_win_rate']:.4f}")
