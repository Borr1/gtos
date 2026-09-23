"""d5-02 — THE FILL QUESTION.  Enumerate every fill actually achievable and price the rule in each.

At T the generator emits (entry e, stop sl).  The order rests from T.
At T+1m the confirm observable c0 becomes readable.  What can you DO at that instant?

  j == 0   the entry was already touched inside [T, T+1m)  -> you are IN.  You cannot refuse.
           Achievable actions: hold (baseline) or EXIT at the close of the confirm minute (= c0 R).
  j >= 1   the entry has not been touched yet               -> the order is still pending.
           Achievable actions: hold, CANCEL (book 0.0), or CANCEL+RE-ANCHOR at market.
  j == -1  never touched in the 120-minute horizon          -> books 0.0 either way; a cancel is free.

Order type, from the no-look-ahead anchor mkt_r0 = s*(close[T-1m]-e)/d:
  mkt_r0 > 0   entry is on the price-improvement side  -> LIMIT   (price must run adversely to fill)
  mkt_r0 < 0   entry is beyond the market              -> STOP/breakout (price must run favourably)
  |mkt_r0| tiny                                        -> AT MARKET
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

TH = [-0.15, -0.05, 0.0]
R = {"windows": {}, "pooled": {}}
ACC = []

for w in WINDOWS:
    D = load(w)
    n = D["g"].size
    wi = WINDOWS.index(w)
    ACC.append({k: D[k] for k in ("g", "net", "cost_r", "c0", "mkt_r0", "j", "ra_g", "ra_net",
                                  "sym", "fam", "hour", "risk_bps", "geo", "atr60_r",
                                  "c0_fav", "c0_adv", "c0_rng", "touch0", "vol0_ratio",
                                  "c1", "c4", "fav5", "adv5", "disp0", "reason", "side")}
               | {"day": D["dayi"] + 1000 * wi, "win": np.full(n, wi)})

for k in ACC[0]:
    R.setdefault("_", {})
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g"].size
j = A["j"]; c0 = A["c0"]; g = A["g"]; net = A["net"]; day = A["day"]
prefilled = j == 0
pending = j >= 1
nofill = j == -1
mk = A["mkt_r0"]
TOL = 0.02
otype = np.where(mk > TOL, 0, np.where(mk < -TOL, 1, 2))   # 0 LIMIT 1 STOP 2 MARKET
ONAMES = ["LIMIT_price_improvement", "STOP_beyond_market", "AT_MARKET"]

R["census"] = {
    "n": int(N),
    "fill_state": {"prefilled_j0": int(prefilled.sum()), "pending_j1plus": int(pending.sum()),
                   "never_filled": int(nofill.sum())},
    "order_type": {ONAMES[t]: int((otype == t).sum()) for t in range(3)},
    "order_type_x_fill": {ONAMES[t]: {
        "prefilled_j0": int((prefilled & (otype == t)).sum()),
        "pending_j1plus": int((pending & (otype == t)).sum()),
        "never_filled": int((nofill & (otype == t)).sum())} for t in range(3)},
}

# ---- 1. where does the loss cohort live?
R["loss_cohort"] = {}
for th in TH:
    ad = c0 <= th
    cells = {}
    for name, m in (("prefilled_j0", prefilled), ("pending_j1plus", pending), ("never_filled", nofill)):
        mm = ad & m
        cells[name] = {"n": int(mm.sum()), "share_of_adverse": float(mm.sum() / max(ad.sum(), 1)),
                       "gross_mean": float(g[mm].mean()) if mm.sum() else None,
                       "total_gross_R": float(g[mm].sum()),
                       "net_mean": float(net[mm].mean()) if mm.sum() else None}
    byot = {}
    for t in range(3):
        mm = ad & (otype == t)
        byot[ONAMES[t]] = {"n": int(mm.sum()), "gross_mean": float(g[mm].mean()) if mm.sum() else None,
                           "prefilled_share": float(prefilled[mm].mean()) if mm.sum() else None}
    R["loss_cohort"]["c0<=%.2f" % th] = {
        "n_adverse": int(ad.sum()), "gross_mean": float(g[ad].mean()),
        "ci": dayblock_ci(g[ad], day[ad]),
        "by_fill_state": cells, "by_order_type": byot,
        "achievable_refusal_share_of_adverse_rows": float((ad & ~prefilled).sum() / max(ad.sum(), 1)),
        "achievable_refusal_share_of_avoided_loss": float(
            g[ad & ~prefilled].sum() / g[ad].sum()) if g[ad].sum() != 0 else None,
    }

# ---- 2. the policy arms, priced per opportunity (a refused row books exactly 0.0)
def arm(gv, nv, tag):
    return {"tag": tag, "n": int(N),
            "pool_gross_per_opportunity": float(gv.mean()),
            "pool_net_per_opportunity": float(nv.mean()),
            "ci_gross": dayblock_ci(gv, day),
            "n_traded": int((gv != 0).sum()),
            "total_gross_R": float(gv.sum()), "total_net_R": float(nv.sum())}


arms = {}
arms["P0_baseline"] = arm(g, net, "roster as walked (order rests from T, 120m horizon)")
for th in TH:
    ad = c0 <= th
    # P1 — x4's rule applied to every row (INCLUDES rows already filled: NOT achievable)
    g1 = np.where(ad, 0.0, g); n1 = np.where(ad, 0.0, net)
    arms["P1_oracle_refuse@%.2f" % th] = arm(g1, n1, "refuse every c0<=th (unachievable on filled rows)")
    # P2 — cancel only what is still pending at T+1m
    m2 = ad & ~prefilled
    g2 = np.where(m2, 0.0, g); n2 = np.where(m2, 0.0, net)
    arms["P2_cancel_pending@%.2f" % th] = arm(g2, n2, "cancel only orders not yet filled at T+1m")
    # P3 — exit at the confirm-minute close for rows already filled
    m3 = ad & prefilled
    g3 = np.where(m3, c0, g)
    n3 = np.where(m3, c0 - A["cost_r"], net)
    arms["P3_exit_at_T1@%.2f" % th] = arm(g3, n3, "already-filled adverse rows exit at close of [T,T+1m)")
    # P4 — both
    g4 = np.where(m2, 0.0, np.where(m3, c0, g))
    n4 = np.where(m2, 0.0, np.where(m3, c0 - A["cost_r"], net))
    arms["P4_cancel_plus_exit@%.2f" % th] = arm(g4, n4, "P2 + P3, the full achievable policy")
    # P5 — cancel pending adverse and re-enter at market at T+1m with the same risk distance
    rg = np.where(np.isfinite(A["ra_g"]), A["ra_g"], 0.0)
    rn = np.where(np.isfinite(A["ra_net"]), A["ra_net"], 0.0)
    g5 = np.where(m2, rg, np.where(m3, c0, g))
    n5 = np.where(m2, rn, np.where(m3, c0 - A["cost_r"], net))
    arms["P5_reanchor_pending@%.2f" % th] = arm(g5, n5, "P3 + re-anchor the pending adverse rows at market")
R["arms"] = arms

# ---- 3. the exact decomposition of x4's headline into achievable and unachievable halves
for th in TH:
    ad = c0 <= th
    tot = g[ad].sum()
    R.setdefault("decomposition", {})["c0<=%.2f" % th] = {
        "total_gross_R_in_adverse_cohort": float(tot),
        "R_in_already_filled_rows_UNAVOIDABLE": float(g[ad & prefilled].sum()),
        "R_in_pending_rows_AVOIDABLE_by_cancel": float(g[ad & pending].sum()),
        "R_in_never_filled_rows_ALREADY_ZERO": float(g[ad & nofill].sum()),
        "pct_avoidable": float(g[ad & pending].sum() / tot * 100.0) if tot else None,
        "value_of_cancel_per_opportunity": float(-g[ad & pending].sum() / N),
        "value_of_oracle_refusal_per_opportunity": float(-tot / N),
    }

# ---- 4. per-window replication of the achievable arms
for wi, w in enumerate(WINDOWS):
    m = A["win"] == wi
    sub = {}
    ad = (c0 <= -0.15) & m
    sub["n"] = int(m.sum())
    sub["baseline_pool_gross"] = float(g[m].mean())
    sub["adverse_n"] = int(ad.sum())
    sub["adverse_gross"] = float(g[ad].mean()) if ad.sum() else None
    sub["adverse_prefilled_share"] = float(prefilled[ad].mean()) if ad.sum() else None
    sub["pct_avoidable"] = float(g[ad & pending].sum() / g[ad].sum() * 100.0) if g[ad].sum() else None
    m2 = ad & ~prefilled
    sub["P2_pool_gross"] = float(np.where(m2, 0.0, g)[m].mean())
    m3 = ad & prefilled
    sub["P4_pool_gross"] = float(np.where(m2, 0.0, np.where(m3, c0, g))[m].mean())
    sub["P4_pool_net"] = float(np.where(m2, 0.0, np.where(m3, c0 - A["cost_r"], net))[m].mean())
    sub["P1_oracle_pool_gross"] = float(np.where(ad, 0.0, g)[m].mean())
    R["windows"][w] = sub

json.dump(R, open("/tmp/d5/out/D5_02_FILL.json", "w"), indent=1, default=float)
print(json.dumps(R["census"], indent=1))
print(json.dumps(R["loss_cohort"]["c0<=-0.15"], indent=1, default=float))
print(json.dumps(R["decomposition"], indent=1, default=float))
