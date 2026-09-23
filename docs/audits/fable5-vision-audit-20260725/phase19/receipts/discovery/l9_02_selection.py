import json, collections, random, math
import l9_lib as L

rows = L.load()
g = L.groups(rows)

# how much of each decision cycle is invisible to us (rank gaps)
gap = []
for t, v in g.items():
    ranks = sorted(r["risk_finalizer_rank"] for r in v)
    gap.append({"t": t, "n_pool": len(v), "max_rank": ranks[-1], "min_rank": ranks[0],
                "missing": ranks[-1] - len(v)})
tot_pool = sum(x["n_pool"] for x in gap); tot_span = sum(x["max_rank"] for x in gap)
OUT = {"n_groups": len(g), "pool_rows_in_groups": tot_pool,
       "sum_max_rank": tot_span, "implied_missing_rows": tot_span - tot_pool,
       "pct_of_ranked_universe_visible": 100.0 * tot_pool / tot_span,
       "groups_with_rank1_present": sum(1 for x in gap if x["min_rank"] == 1),
       "min_rank_hist": dict(collections.Counter(min(x["min_rank"], 6) for x in gap))}

MEAS = ["gross_r", "fill_honest_walk_r", "plain_walk_r"]

def run(sub_filter, label, topn_list=(1, 2, 3, 5)):
    gg = collections.defaultdict(list)
    for r in rows:
        if sub_filter(r):
            gg[r["decision_time_utc"]].append(r)
    gg = {t: v for t, v in gg.items() if len(v) >= 2}
    res = {"n_groups": len(gg), "n_rows": sum(len(v) for v in gg.values())}
    rnd = random.Random(20260801)
    for m in MEAS:
        acc = collections.defaultdict(list)
        for t, v in gg.items():
            vv = [r for r in v if r.get(m) is not None]
            if len(vv) < 2: continue
            by_rank = sorted(vv, key=lambda r: r["risk_finalizer_rank"])
            vals = [r[m] for r in vv]
            acc["group_mean_random"].append(sum(vals)/len(vals))
            acc["oracle_best"].append(max(vals))
            acc["oracle_worst"].append(min(vals))
            acc["allocator_rank1"].append(by_rank[0][m])
            acc["allocator_rankLAST"].append(by_rank[-1][m])
            for n in topn_list:
                sel = by_rank[:n]
                acc[f"allocator_top{n}"].append(sum(r[m] for r in sel)/len(sel))
                # matched random draw of same size
                pick = rnd.sample(vv, min(n, len(vv)))
                acc[f"random_top{n}"].append(sum(r[m] for r in pick)/len(pick))
                # oracle top-n
                srt = sorted(vals, reverse=True)[:n]
                acc[f"oracle_top{n}"].append(sum(srt)/len(srt))
            for fld, rev, nm in [("expected_net_r", True, "by_expected_net_r"),
                                 ("candidate_ev_r", True, "by_candidate_ev_r"),
                                 ("cost_r", False, "by_cost_r_asc"),
                                 ("candidate_probability", True, "by_probability"),
                                 ("execution_fill_probability", True, "by_exec_fillprob"),
                                 ("risk_distance", True, "by_risk_distance_desc")]:
                cand = [r for r in vv if r.get(fld) is not None]
                if not cand: continue
                best = sorted(cand, key=lambda r: r[fld], reverse=rev)[0]
                acc[nm].append(best[m])
        res[m] = {k: {"n": len(v), "mean": sum(v)/len(v) if v else None} for k, v in acc.items()}
    OUT.setdefault("selection", {})[label] = res
    return res

run(lambda r: True, "ALL")
run(lambda r: r["takeable"], "TAKEABLE")

json.dump(OUT, open("L9_SELECTION_V1.json", "w"), indent=1, default=str)
print("groups", OUT["n_groups"], "visible%", round(OUT["pct_of_ranked_universe_visible"],2),
      "implied_missing", OUT["implied_missing_rows"], "rank1_present_groups", OUT["groups_with_rank1_present"])
print("min_rank hist(cap6):", OUT["min_rank_hist"])
for lab in ["ALL","TAKEABLE"]:
    r = OUT["selection"][lab]
    print("==", lab, "groups", r["n_groups"], "rows", r["n_rows"])
    for m in MEAS:
        d = r[m]
        ks = ["allocator_rank1","allocator_top3","group_mean_random","allocator_rankLAST",
              "oracle_best","oracle_worst","by_expected_net_r","by_candidate_ev_r","by_cost_r_asc",
              "by_probability","by_exec_fillprob","by_risk_distance_desc"]
        print(" ", m, " ".join(f"{k}={d[k]['mean']:+.4f}" for k in ks if k in d))
