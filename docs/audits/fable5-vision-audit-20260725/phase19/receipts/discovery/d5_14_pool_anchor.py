"""d5-14 — tie the roster mechanism back to x4's own object.

If x4's separator on the counterfactual pool is the same fill artifact, then its refused cohort
should be dominated by rows whose entry the market had ALREADY left at the decision instant.
The pool carries the engine's own field for this — `limit_marketable_at_decision` — which no
prior lane used.  Measured here against the M1 tape as well, so the two are cross-checked.
"""
import gzip, json, os, sys
import numpy as np
REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG); sys.path.insert(0, REPO); os.chdir(REPO)
import pbg_lib as L, pbg_econ as E

POOL = REPO + "/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
tape = E.Tape(list(L.SYMBOLS), ["202601", "202602"])
rows = []
with gzip.open(POOL, "rt") as fh:
    for ln in fh:
        rows.append(json.loads(ln))
mk, c0, gp, mark, sym_ok = [], [], [], [], 0
for r in rows:
    s = r["symbol"]
    if s not in tape.c:
        continue
    i = tape.idx(r["decision_time_utc"])
    if not (0 < i < tape.n - 2):
        continue
    e = float(r["entry_price"]); sl = float(r["stop_loss"]); d = abs(e - sl)
    if not (d > 0):
        continue
    lng = (r.get("direction") or r.get("side", "")).upper().startswith("L")
    sgn = 1.0 if lng else -1.0
    m0 = tape.c[s][i - 1]; cc = tape.c[s][i]
    if m0 != m0 or cc != cc:
        continue
    mk.append(sgn * (m0 - e) / d); c0.append(sgn * (cc - e) / d)
    gp.append(float(r.get("fill_honest_walk_r") or 0.0))
    mark.append(r.get("limit_marketable_at_decision"))
    sym_ok += 1
mk = np.array(mk); c0 = np.array(c0); gp = np.array(gp)
mv = np.array([1 if m is True else (0 if m is False else -1) for m in mark])
N = mk.size
ad = c0 <= -0.15
R = {
    "n_pool_rows": len(rows), "n_joined_to_tape": int(N),
    "engine_field_limit_marketable_at_decision": {
        "true": int((mv == 1).sum()), "false": int((mv == 0).sum()), "null": int((mv == -1).sum())},
    "agreement_engine_field_vs_tape_anchor": {
        "engine_true_and_mkt_r0<0": int(((mv == 1) & (mk < 0)).sum()),
        "engine_true_and_mkt_r0>=0": int(((mv == 1) & (mk >= 0)).sum()),
        "engine_false_and_mkt_r0<0": int(((mv == 0) & (mk < 0)).sum()),
        "engine_false_and_mkt_r0>=0": int(((mv == 0) & (mk >= 0)).sum())},
    "pool_composition": {
        "share_mkt_r0>0_reachable_limit": float((mk > 0).mean()),
        "share_mkt_r0==0_at_market": float((mk == 0).mean()),
        "share_mkt_r0<0_unreachable": float((mk < 0).mean()),
        "share_born_past_stop": float((mk <= -1).mean())},
    "x4_refused_cohort_c0<=-0.15": {
        "n": int(ad.sum()), "share_of_pool": float(ad.mean()),
        "mean_fill_honest_walk_r": float(gp[ad].mean()),
        "share_mkt_r0>0": float((mk[ad] > 0).mean()),
        "share_mkt_r0==0": float((mk[ad] == 0).mean()),
        "share_mkt_r0<0": float((mk[ad] < 0).mean()),
        "share_born_past_stop": float((mk[ad] <= -1).mean())},
    "kept_cohort": {
        "n": int((~ad).sum()), "mean_fill_honest_walk_r": float(gp[~ad].mean()),
        "share_mkt_r0<0": float((mk[~ad] < 0).mean())},
    "pool_gross_attribution": {
        "total_fill_honest_R": float(gp.sum()),
        "share_from_mkt_r0<0_rows": float(gp[mk < 0].sum() / gp.sum()) if gp.sum() else None,
        "mean_on_mkt_r0<0": float(gp[mk < 0].mean()) if (mk < 0).any() else None,
        "mean_on_mkt_r0>=0": float(gp[mk >= 0].mean())},
}
json.dump(R, open("/tmp/d5/out/D5_14_POOL_ANCHOR.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1))
