#!/usr/bin/env python3
"""FG4 raw recompute from lane trade tables:
  S4: chosen mean net (Jan n=55 expected -0.100113; Feb n=58 expected -0.068300)
  S5: executed FVG composition split via identity-tuple join to the pools
      (join key: candidate_id, decision_time_utc, symbol, direction — bare
       candidate_id is NOT unique per FA Phase-1).
February is read attribution-only under owner_mandate_20260801.
"""
import gzip, json

LANES = {
    "january": "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl",
    "february": "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl",
}
POOLS = {
    "january": "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
    "february": "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
}

def norm_time(t):
    return str(t).replace("Z", "+00:00")

out = {}
for label in ("january", "february"):
    with open(LANES[label]) as f:
        lines = [json.loads(l) for l in f]
    meta, trades = lines[0], lines[1:]
    n_trades = len(trades)
    net_vals = [t["net_r"] for t in trades if t.get("net_r") is not None]
    n_null = n_trades - len(net_vals)

    # index trades by identity tuple, then stream the pool once
    want = {}
    for t in trades:
        k = (t["candidate_id"], norm_time(t["decision_time_utc"]), t["symbol"], str(t.get("direction")))
        want.setdefault(k, []).append(t)
    hits = {}
    bare_id_hits = {}
    with gzip.open(POOLS[label], "rt") as f:
        for line in f:
            d = json.loads(line)
            k = (d.get("candidate_id"), norm_time(d.get("decision_time_utc")), d.get("symbol"), str(d.get("direction")))
            if k in want:
                hits.setdefault(k, []).append(d.get("origin_family"))
            cid = d.get("candidate_id")
            if any(cid == t["candidate_id"] for ts in want.values() for t in ts):
                bare_id_hits[cid] = bare_id_hits.get(cid, 0) + 1

    fvg = {"n": 0, "sum_net": 0.0, "n_null": 0}
    nonfvg = {"n": 0, "sum_net": 0.0, "n_null": 0}
    unjoined = []
    ambiguous = []
    for k, ts in want.items():
        fams = hits.get(k)
        for t in ts:
            if fams is None:
                unjoined.append(k[0])
                continue
            if len(set(fams)) > 1:
                ambiguous.append((k[0], sorted(set(map(str, fams)))))
            fam = fams[0]
            tgt = fvg if fam == "current_fvg_fill" else nonfvg
            if t.get("net_r") is None:
                tgt["n_null"] += 1
            else:
                tgt["n"] += 1
                tgt["sum_net"] += t["net_r"]

    out[label] = {
        "lane_meta_counts": meta.get("counts"),
        "n_trades": n_trades,
        "n_net_null": n_null,
        "chosen_mean_net_r": round(sum(net_vals) / len(net_vals), 6),
        "join": {
            "matched_tuples": len(hits),
            "unjoined_trades": unjoined,
            "ambiguous_family_tuples": ambiguous,
            "bare_candidate_id_multiplicity_max": max(bare_id_hits.values()) if bare_id_hits else 0,
        },
        "fvg_executed": {"n_scored": fvg["n"], "n_null": fvg["n_null"], "sum_net_r": round(fvg["sum_net"], 6)},
        "non_fvg_executed": {"n_scored": nonfvg["n"], "n_null": nonfvg["n_null"], "sum_net_r": round(nonfvg["sum_net"], 6)},
        "lane_total_net_r": round(sum(net_vals), 6),
    }

print(json.dumps(out, indent=1))
