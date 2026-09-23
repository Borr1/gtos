"""e5 — instrument check. The rebuilt January paths must equal CQ's sidecar bar for bar,
and the L2-F6 rule ladder must reproduce on them.
Writes E5_JAN_VALIDATION_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws, e5_lib

OUT = os.path.join(D, "E5_JAN_VALIDATION_V1.json")

ref = {}
for rp in w0_ws.iter_rpaths():
    ref[(rp["candidate_id"], rp["decision_time_utc"])] = rp

cmp = {"rows": 0, "matched": 0, "len_mismatch": 0, "max_abs_fav": 0.0, "max_abs_adv": 0.0,
       "max_abs_cls": 0.0, "rows_with_any_diff_gt_1e_4": 0, "unmatched": 0}
mine = []
with gzip.open(os.path.join(D, "e5_january_WS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        r = json.loads(ln)
        mine.append(r)
        cmp["rows"] += 1
        k = (r["candidate_id"], r["decision_time_utc"])
        g = ref.get(k)
        if g is None:
            cmp["unmatched"] += 1
            continue
        cmp["matched"] += 1
        if len(g["fav"]) != len(r["fav"]):
            cmp["len_mismatch"] += 1
            continue
        bad = False
        for a, b in zip(g["fav"], r["fav"]):
            d = abs(a - b)
            if d > cmp["max_abs_fav"]:
                cmp["max_abs_fav"] = d
            if d > 1e-4:
                bad = True
        for a, b in zip(g["adv"], r["adv"]):
            d = abs(a - b)
            if d > cmp["max_abs_adv"]:
                cmp["max_abs_adv"] = d
            if d > 1e-4:
                bad = True
        for a, b in zip(g["cls"], r["cls"]):
            d = abs(a - b)
            if d > cmp["max_abs_cls"]:
                cmp["max_abs_cls"] = d
            if d > 1e-4:
                bad = True
        if bad:
            cmp["rows_with_any_diff_gt_1e_4"] += 1
for kk in ("max_abs_fav", "max_abs_adv", "max_abs_cls"):
    cmp[kk] = round(cmp[kk], 8)

# now re-price the L2 ladder on MY rebuilt paths
byk = {(r["candidate_id"], r["decision_time_utc"]): r for r in mine}
anch = {(r["candidate_id"], r["decision_time_utc"]): {"mkt_r_prev_close": r["mkt_r_prev_close"]}
        for r in mine}
ents, st = e5_lib.build_entries(byk, iter(mine), anch)
rules = {
    "baseline_k1": e5_lib.rule_eval(ents, lambda e: 1.0, "baseline k=1"),
    "S5": e5_lib.rule_eval(ents, lambda e: max(1.0, 5 * e["sp"]), "S(5)"),
    "S10": e5_lib.rule_eval(ents, lambda e: max(1.0, 10 * e["sp"]), "S(10)"),
    "S20": e5_lib.rule_eval(ents, lambda e: max(1.0, 20 * e["sp"]), "S(20)"),
    "k3": e5_lib.rule_eval(ents, lambda e: 3.0, "flat k=3"),
}
res = {"path_comparison": cmp, "n_entries": len(ents), "build": st, "rules_on_rebuilt": rules,
       "l2_published": {"baseline_k1": {"net_frozen": -0.78888, "net_sp73": -0.30216},
                        "S10": {"net_frozen": -0.19983}, "S20_trail": {"net_frozen": -0.11481}}}
with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps(cmp))
print("n_entries", len(ents), st)
for k, v in rules.items():
    print("%-12s gross=%+.5f netFROZEN=%+.5f net73=%+.5f" % (k, v["gross_newunit"], v["net_frozen"], v["net_sp73"]))
print("wrote", OUT)
