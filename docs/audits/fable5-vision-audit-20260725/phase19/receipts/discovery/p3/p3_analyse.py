"""p3 — pooled adversarial analysis of the eight window walks."""
from __future__ import annotations
import json
import numpy as np

WINS = ["202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605"]
CON = ["EST", "BC", "REFUSE", "MKT", "SPRSYM", "SPRMT5", "TIETGT", "MIRROR"]

D = {}
per = {}
off = 0
cols = ["sym", "fam", "day", "hour", "side", "e", "d", "riskbps", "mkt_r0", "sp_px", "cost_r"]
acc = {c: [] for c in cols}
for c in CON:
    acc["f_" + c] = []
    acc["r_" + c] = []
acc["win"] = []
acc["gday"] = []
famnames = None
symnames = None
for wi, w in enumerate(WINS):
    z = np.load("/tmp/p3/P3_%s.npz" % w, allow_pickle=True)
    n = len(z["sym"])
    for c in cols:
        acc[c].append(z[c])
    for c in CON:
        acc["f_" + c].append(z["f_" + c])
        acc["r_" + c].append(z["r_" + c])
    acc["win"].append(np.full(n, wi))
    acc["gday"].append(z["day"] + wi * 1000)
    if famnames is None:
        famnames = list(z["famnames"])
        symnames = list(z["symnames"])
    else:
        assert list(z["famnames"])[: len(famnames)] == famnames[: len(z["famnames"])] or True
    per[w] = {"n": int(n), "famnames": list(z["famnames"]), "symnames": list(z["symnames"])}
A = {k: np.concatenate(v) for k, v in acc.items()}
N = len(A["sym"])
print("pooled rows", N)

# family names differ per window in id order -> rebuild a global family label
fam_g = np.empty(N, dtype=object)
o = 0
for w in WINS:
    n = per[w]["n"]
    fn = per[w]["famnames"]
    fam_g[o:o + n] = np.array(fn, dtype=object)[A["fam"][o:o + n].astype(int)]
    o += n
sym_g = np.empty(N, dtype=object)
o = 0
for w in WINS:
    n = per[w]["n"]
    sn = per[w]["symnames"]
    sym_g[o:o + n] = np.array(sn, dtype=object)[A["sym"][o:o + n].astype(int)]
    o += n

mk = A["mkt_r0"]
SEG = {
    "limit_mkt_r0_gt0": mk > 1e-12,
    "at_market_mkt_r0_eq0": np.abs(mk) < 1e-12,
    "stopentry_mkt_r0_lt0": mk < -1e-12,
    "  ...of which born past stop (<=-1)": mk <= -1.0,
    "  ...of which 0>mkt_r0>-1": (mk < -1e-12) & (mk > -1.0),
}

OUT = {}


def stat(mask, c):
    f = A["f_" + c][mask] > 0
    r = A["r_" + c][mask]
    cost = A["cost_r"][mask] * f
    n = int(mask.sum())
    nf = int(f.sum())
    g_opp = float(r.mean()) if n else float("nan")
    g_fill = float(r[f].mean()) if nf else float("nan")
    net = r - cost
    return {
        "n": n, "n_fill": nf, "fill_rate": (nf / n) if n else float("nan"),
        "gross_per_opp": g_opp, "gross_per_fill": g_fill,
        "net_per_opp": float(net.mean()) if n else float("nan"),
        "net_per_fill": float(net[f].mean()) if nf else float("nan"),
        "total_gross_R": float(r.sum()),
        "win_rate_on_fills": float((r[f] > 0).mean()) if nf else float("nan"),
    }


ALL = np.ones(N, dtype=bool)
OUT["POOLED_CONTRACTS"] = {c: stat(ALL, c) for c in CON}
print("\n== POOLED, %d emissions ==" % N)
print("%-8s %8s %8s %10s %10s %10s %10s" % ("contract", "fill", "n_fill", "gross/opp", "gross/fill", "net/opp", "net/fill"))
for c in CON:
    s = OUT["POOLED_CONTRACTS"][c]
    print("%-8s %8.4f %8d %+10.5f %+10.5f %+10.5f %+10.5f"
          % (c, s["fill_rate"], s["n_fill"], s["gross_per_opp"], s["gross_per_fill"],
             s["net_per_opp"], s["net_per_fill"]))

# ---- per window
OUT["PER_WINDOW"] = {}
print("\n== gross/opp per window ==")
print("%-8s %8s " % ("window", "n") + " ".join("%10s" % c for c in CON))
for wi, w in enumerate(WINS):
    m = A["win"] == wi
    OUT["PER_WINDOW"][w] = {c: stat(m, c) for c in CON}
    print("%-8s %8d " % (w, m.sum())
          + " ".join("%+10.5f" % OUT["PER_WINDOW"][w][c]["gross_per_opp"] for c in CON))

# ---- segments
OUT["SEGMENTS"] = {}
print("\n== segments (share, EST gross/opp, BC gross/opp, total gross R) ==")
for name, m in SEG.items():
    OUT["SEGMENTS"][name] = {"share": float(m.mean()), **{c: stat(m, c) for c in CON}}
    print("%-38s %7.4f  EST %+9.5f (tot %+12.1f)  BC %+9.5f (tot %+10.1f)  SPRMT5 %+9.5f"
          % (name, m.mean(), OUT["SEGMENTS"][name]["EST"]["gross_per_opp"],
             OUT["SEGMENTS"][name]["EST"]["total_gross_R"],
             OUT["SEGMENTS"][name]["BC"]["gross_per_opp"],
             OUT["SEGMENTS"][name]["BC"]["total_gross_R"],
             OUT["SEGMENTS"][name]["SPRMT5"]["gross_per_opp"]))

tot_est = float(A["r_EST"].sum())
tot_est_seg = float(A["r_EST"][SEG["stopentry_mkt_r0_lt0"]].sum())
OUT["NEGATIVITY_CONCENTRATION"] = {
    "roster_total_gross_R_EST": tot_est,
    "stopentry_total_gross_R_EST": tot_est_seg,
    "share_of_total": tot_est_seg / tot_est,
    "rest_total_gross_R_EST": tot_est - tot_est_seg,
    "stopentry_share_of_rows": float(SEG["stopentry_mkt_r0_lt0"].mean()),
}
print("\nEST total gross %.1f R; stop-entry segment %.1f R (%.4f of it) on %.4f of rows"
      % (tot_est, tot_est_seg, tot_est_seg / tot_est, SEG["stopentry_mkt_r0_lt0"].mean()))

# ---- long/short split for the quote-side attacks
print("\n== long / short, gross/opp ==")
OUT["BY_SIDE"] = {}
for lab, m in (("LONG", A["side"] > 0), ("SHORT", A["side"] < 0)):
    OUT["BY_SIDE"][lab] = {c: stat(m, c) for c in CON}
    print("%-6s n=%7d " % (lab, m.sum())
          + " ".join("%s %+8.5f" % (c, OUT["BY_SIDE"][lab][c]["gross_per_opp"]) for c in
                     ["EST", "BC", "SPRSYM", "SPRMT5", "MIRROR"]))

# ---- day-block bootstrap
rng = np.random.default_rng(20260806)
days = A["gday"].astype(np.int64)
udays, dinv = np.unique(days, return_inverse=True)
ND = len(udays)
print("\nday blocks:", ND)


def boot(vals, draws=2000):
    """day-block bootstrap of the MEAN of `vals` over all rows."""
    order = np.argsort(dinv, kind="stable")
    v = vals[order]
    di = dinv[order]
    bounds = np.searchsorted(di, np.arange(ND + 1))
    sums = np.add.reduceat(v, bounds[:-1])
    cnts = np.diff(bounds)
    out = np.empty(draws)
    for b in range(draws):
        pick = rng.integers(0, ND, ND)
        out[b] = sums[pick].sum() / cnts[pick].sum()
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), float((out <= 0).mean())


OUT["BOOTSTRAP_gross_per_opp"] = {}
print("\n== day-block bootstrap, gross/opp (2000 draws, %d day blocks) ==" % ND)
for c in CON:
    lo, hi, p = boot(A["r_" + c])
    OUT["BOOTSTRAP_gross_per_opp"][c] = {
        "mean": float(A["r_" + c].mean()), "ci95": [lo, hi], "p_le_0": p}
    print("%-8s %+9.5f  CI95 [%+9.5f, %+9.5f]  p(<=0) %.4f"
          % (c, A["r_" + c].mean(), lo, hi, p))

# paired deltas
OUT["BOOTSTRAP_DELTAS"] = {}
print("\n== paired deltas vs BC, gross/opp ==")
for c in ["EST", "REFUSE", "MKT", "SPRSYM", "SPRMT5", "TIETGT", "MIRROR"]:
    dv = A["r_" + c] - A["r_BC"]
    lo, hi, p = boot(dv)
    OUT["BOOTSTRAP_DELTAS"][c + "_minus_BC"] = {
        "mean": float(dv.mean()), "ci95": [lo, hi], "p_le_0": p}
    print("%-8s %+9.5f  CI95 [%+9.5f, %+9.5f]  p(<=0) %.4f" % (c, dv.mean(), lo, hi, p))

json.dump(OUT, open("/tmp/p3/P3_MAIN.json", "w"), indent=1)
np.save("/tmp/p3/fam_g.npy", fam_g)
np.save("/tmp/p3/sym_g.npy", sym_g)
print("\nwrote /tmp/p3/P3_MAIN.json")
