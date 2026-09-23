"""p3 pass 2 — dedup, quote-side cross-check, paired direction test, family table."""
from __future__ import annotations
import json
import numpy as np

WINS = ["202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605"]
CON = ["EST", "BC", "REFUSE", "MKT", "SPRSYM", "SPRMT5", "TIETGT", "MIRROR"]
cols = ["sym", "fam", "day", "hour", "side", "e", "d", "riskbps", "mkt_r0", "sp_px", "cost_r"]

acc = {c: [] for c in cols}
for c in CON:
    acc["f_" + c] = []
    acc["r_" + c] = []
acc["win"] = []
acc["gday"] = []
per = {}
for wi, w in enumerate(WINS):
    z = np.load("/tmp/p3/P3_%s.npz" % w, allow_pickle=True)
    n = len(z["sym"])
    per[w] = {"n": n, "fam": list(z["famnames"]), "sym": list(z["symnames"])}
    for c in cols:
        acc[c].append(z[c])
    for c in CON:
        acc["f_" + c].append(z["f_" + c])
        acc["r_" + c].append(z["r_" + c])
    acc["win"].append(np.full(n, wi))
    acc["gday"].append(z["day"] + wi * 1000)
A = {k: np.concatenate(v) for k, v in acc.items()}
N = len(A["sym"])
fam_g = np.load("/tmp/p3/fam_g.npy", allow_pickle=True)
sym_g = np.load("/tmp/p3/sym_g.npy", allow_pickle=True)
OUT = {}

days = A["gday"].astype(np.int64)
udays, dinv = np.unique(days, return_inverse=True)
ND = len(udays)
rng = np.random.default_rng(20260806)
order = np.argsort(dinv, kind="stable")
di_s = dinv[order]
bounds = np.searchsorted(di_s, np.arange(ND + 1))
cnts_all = np.diff(bounds)


def boot(vals, mask=None, draws=2000):
    v = vals if mask is None else np.where(mask, vals, 0.0)
    w = np.ones(len(vals)) if mask is None else mask.astype(float)
    vs = v[order]
    ws = w[order]
    sums = np.add.reduceat(vs, bounds[:-1])
    cnts = np.add.reduceat(ws, bounds[:-1])
    out = np.empty(draws)
    for b in range(draws):
        pick = rng.integers(0, ND, ND)
        cc = cnts[pick].sum()
        out[b] = sums[pick].sum() / cc if cc > 0 else np.nan
    return (float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5)),
            float(np.nanmean(out <= 0)))


# ---------------------------------------------------------------- 1. DEDUP
print("== A4 DOUBLE COUNTING ==")
key_full = np.char.add(np.char.add(sym_g.astype(str), "|"), fam_g.astype(str))
key_full = np.char.add(np.char.add(key_full, "|"), np.where(A["side"] > 0, "L", "S"))
key_setup = np.char.add(np.char.add(key_full, "|"), days.astype(str))
key_live = np.char.add(np.char.add(sym_g.astype(str), "|"), days.astype(str))
res_dd = {}
for lab, key in (("NONE", None), ("SYM_FAM_SIDE_DAY", key_setup), ("LIVE_SYM_DAY", key_live)):
    if key is None:
        m = np.ones(N, dtype=bool)
    else:
        _, first = np.unique(key, return_index=True)
        m = np.zeros(N, dtype=bool)
        m[first] = True
    row = {"n": int(m.sum()), "compression": float(N / m.sum())}
    for c in ["EST", "BC", "SPRMT5", "MIRROR"]:
        f = A["f_" + c][m] > 0
        r = A["r_" + c][m]
        row[c] = {"gross_per_opp": float(r.mean()),
                  "gross_per_fill": float(r[f].mean()) if f.any() else float("nan"),
                  "fill_rate": float(f.mean())}
    lo, hi, p = boot(A["r_BC"], m)
    row["BC_ci95"] = [lo, hi]
    row["BC_p_le0"] = p
    res_dd[lab] = row
    print("%-18s n=%7d  x%5.2f  EST %+8.5f  BC %+8.5f [%+.5f,%+.5f] p%.3f  SPRMT5 %+8.5f  MIRROR %+8.5f"
          % (lab, row["n"], row["compression"], row["EST"]["gross_per_opp"],
             row["BC"]["gross_per_opp"], lo, hi, p, row["SPRMT5"]["gross_per_opp"],
             row["MIRROR"]["gross_per_opp"]))
OUT["DEDUP"] = res_dd

# ---------------------------------------------------------- 2. spread magnitude
sd = A["sp_px"] / A["d"]
OUT["SPREAD_OVER_RISK"] = {
    "median": float(np.median(sd)), "mean": float(sd.mean()),
    "p90": float(np.percentile(sd, 90)), "p99": float(np.percentile(sd, 99)),
    "share_gt_0.10": float((sd > 0.10).mean()), "share_gt_0.25": float((sd > 0.25).mean()),
    "share_gt_0.50": float((sd > 0.50).mean()), "share_gt_1.0": float((sd > 1.0).mean()),
    "median_risk_bps": float(np.median(A["riskbps"])),
    "median_spread_bps": float(np.median(A["sp_px"] / A["e"] * 1e4)),
}
print("\n== A2 quote-side magnitude ==")
print("s/d median %.4f mean %.4f p90 %.4f p99 %.4f | >10%% %.3f >25%% %.3f >50%% %.3f >100%% %.4f"
      % (OUT["SPREAD_OVER_RISK"]["median"], OUT["SPREAD_OVER_RISK"]["mean"],
         OUT["SPREAD_OVER_RISK"]["p90"], OUT["SPREAD_OVER_RISK"]["p99"],
         OUT["SPREAD_OVER_RISK"]["share_gt_0.10"], OUT["SPREAD_OVER_RISK"]["share_gt_0.25"],
         OUT["SPREAD_OVER_RISK"]["share_gt_0.50"], OUT["SPREAD_OVER_RISK"]["share_gt_1.0"]))
print("median risk %.3f bps  median spread %.3f bps" %
      (OUT["SPREAD_OVER_RISK"]["median_risk_bps"], OUT["SPREAD_OVER_RISK"]["median_spread_bps"]))

# exit mix shift (independent cross-check of d8x's touch-rate deltas)
mix = {}
for c in ["BC", "SPRSYM", "SPRMT5"]:
    f = A["f_" + c] > 0
    r = A["r_" + c]
    mix[c] = {"stop": float((np.abs(r + 1.0) < 1e-9)[f].mean()),
              "target": float((np.abs(r - 2.0) < 1e-9)[f].mean()),
              "path_end": float((~((np.abs(r + 1.0) < 1e-9) | (np.abs(r - 2.0) < 1e-9)))[f].mean()),
              "n_fill": int(f.sum())}
OUT["EXIT_MIX"] = mix
print("exit mix on fills:  " + "  ".join(
    "%s stop %.4f tgt %.4f end %.4f" % (c, mix[c]["stop"], mix[c]["target"], mix[c]["path_end"])
    for c in mix))
print("  delta vs BC: SPRSYM stop %+.4fpp tgt %+.4fpp | SPRMT5 stop %+.4fpp tgt %+.4fpp"
      % (100 * (mix["SPRSYM"]["stop"] - mix["BC"]["stop"]),
         100 * (mix["SPRSYM"]["target"] - mix["BC"]["target"]),
         100 * (mix["SPRMT5"]["stop"] - mix["BC"]["stop"]),
         100 * (mix["SPRMT5"]["target"] - mix["BC"]["target"])))

# ------------------------------------------------- 3. paired direction (mirror)
print("\n== A6 the direction call vs its own exact mirror (same rows, same fills) ==")
OUT["MIRROR_PAIRED"] = {}
for lab, m in (("ALL", np.ones(N, dtype=bool)),
               ("AT_MARKET", np.abs(A["mkt_r0"]) < 1e-12),
               ("LIMIT", A["mkt_r0"] > 1e-12),
               ("FILLED_BC", A["f_BC"] > 0)):
    dv = A["r_BC"] - A["r_MIRROR"]
    lo, hi, p = boot(dv, m)
    row = {"n": int(m.sum()), "real": float(A["r_BC"][m].mean()),
           "mirror": float(A["r_MIRROR"][m].mean()), "delta": float(dv[m].mean()),
           "ci95": [lo, hi], "p_le_0": p}
    OUT["MIRROR_PAIRED"][lab] = row
    print("%-10s n=%7d real %+8.5f mirror %+8.5f  signal %+8.5f CI [%+8.5f,%+8.5f] p(<=0) %.4f"
          % (lab, row["n"], row["real"], row["mirror"], row["delta"], lo, hi, p))
# per window sign of the signal
sg = []
for wi, w in enumerate(WINS):
    m = A["win"] == wi
    sg.append(float((A["r_BC"] - A["r_MIRROR"])[m].mean()))
OUT["MIRROR_PAIRED"]["per_window_signal"] = dict(zip(WINS, sg))
print("per-window signal:", " ".join("%+.5f" % x for x in sg),
      " positive %d/8" % sum(1 for x in sg if x > 0))

# ------------------------------------------------------------- 4. family table
print("\n== families, BC vs SPRMT5 vs MIRROR (gross/opp) ==")
fams = sorted(set(fam_g.tolist()))
ft = {}
for fm in fams:
    m = fam_g == fm
    row = {"n": int(m.sum()), "share": float(m.mean())}
    for c in ["EST", "BC", "SPRMT5", "MIRROR"]:
        row[c] = float(A["r_" + c][m].mean())
    row["signal_vs_mirror"] = row["BC"] - row["MIRROR"]
    row["fill_BC"] = float((A["f_BC"][m] > 0).mean())
    row["cost_r_on_fills"] = float(A["cost_r"][m][A["f_BC"][m] > 0].mean())
    ft[fm] = row
    print("%-38s n=%7d  EST %+8.5f  BC %+8.5f  SPRMT5 %+8.5f  sig %+8.5f  toll %.4f"
          % (fm, row["n"], row["EST"], row["BC"], row["SPRMT5"], row["signal_vs_mirror"],
             row["cost_r_on_fills"]))
OUT["FAMILIES"] = ft

# ------------------------------------------------- 5. what would have to be true
f = A["f_BC"] > 0
r = A["r_BC"][f]
cost = A["cost_r"][f]
wr = float((r > 0).mean())
win = float(r[r > 0].mean())
los = float(-r[r <= 0].mean())
C = float(cost.mean())
OUT["BREAKEVEN"] = {
    "n_fill": int(f.sum()), "gross_per_fill": float(r.mean()), "toll_per_fill": C,
    "net_per_fill": float((r - cost).mean()), "win_rate": wr,
    "mean_winner_R": win, "mean_loser_R": los,
    "gross_breakeven_wr": los / (win + los),
    "net_breakeven_wr": (los + C) / (win + los),
    "wr_gap_pp_net": 100 * (wr - (los + C) / (win + los)),
}
print("\n== breakeven at the repaired contract ==")
print(json.dumps(OUT["BREAKEVEN"], indent=1))

json.dump(OUT, open("/tmp/p3/P3_PASS2.json", "w"), indent=1)
print("\nwrote /tmp/p3/P3_PASS2.json")
