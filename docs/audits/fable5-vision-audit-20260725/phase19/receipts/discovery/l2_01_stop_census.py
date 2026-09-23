"""l2 step 1 — the honest stop census, stopped-then-reversed (Q1), winner MAE (Q2).

Population discipline, inherited from wave 0 and NOT re-derived:
  * born state from `mkt_r_prev_close` (strictly no-look-ahead anchor; bars are OPEN-stamped).
    born_past_stop = the stop price was ALREADY breached at the decision instant -> the order
    was never takeable.  3,516 rows.  They are separated, never silently pooled.
  * fill required: a resting limit at entry_price only fills at the first bar with adv <= 0.
    Excursion before that bar is not capturable (W0-F2).
  * conservative tie rule: stop and target reachable in the same M1 bar -> STOP.
  * hard 2h / 120 M1 bar horizon.
Writes L2_STOP_CENSUS_V1.json.
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

OUT = os.path.join(D, "L2_STOP_CENSUS_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 5) if v else None


def q(v, p):
    if not v:
        return None
    s = sorted(v)
    return round(s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))], 5)


rows = w0_ws.load()
byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln)
        anch[(a["candidate_id"], a["decision_time_utc"])] = a

recs = []
for rp in w0_ws.iter_rpaths():
    k = (rp["candidate_id"], rp["decision_time_utc"])
    r = byk.get(k); a = anch.get(k)
    if r is None:
        continue
    m = a["mkt_r_prev_close"] if a else None
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(fav)
    tgt = rp.get("policy_target_r") or 2.0
    fb = next((i for i in range(n) if adv[i] <= 0.0), None)
    e = {"cid": rp["candidate_id"], "dt": rp["decision_time_utc"], "sym": r["symbol"],
         "side": r["side"], "fam": r.get("origin_family"), "sess": r.get("session_bucket"),
         "m": m, "tgt": tgt, "n": n, "fb": fb, "eng": r.get("gross_r"),
         "cost": r.get("expected_cost_r") or 0.0, "sp": r.get("spread_r") or 0.0,
         "rd": r["risk_distance"], "px": r.get("entry_price"),
         "rdpct": (r["risk_distance"] / r["entry_price"] * 100.0) if r.get("entry_price") else None,
         "hr": r.get("utc_hour_bucket"), "tf": r.get("decision_timeframe"),
         "born": ("born_past_stop" if (m is not None and m <= -1.0)
                  else "born_marketable" if (m is not None and m < 0.0)
                  else "born_at_limit" if m == 0.0 else "born_resting" if m is not None else "unknown")}
    if fb is None:
        e["exit"] = "no_fill"; e["r"] = 0.0
        recs.append(e); continue
    # honest first-touch walk from the fill bar
    xr = None; rs = None; xb = None
    mfe_pre = -9e9; mae_pre = 9e9
    for i in range(fb, n):
        mfe_pre = max(mfe_pre, fav[i]); mae_pre = min(mae_pre, adv[i])
        ht = fav[i] >= tgt - 1e-12; hs = adv[i] <= -1.0 + 1e-12
        if hs:                       # conservative tie -> stop
            xr, rs, xb = -1.0, "stop", i; break
        if ht:
            xr, rs, xb = tgt, "target", i; break
    if xr is None:
        xr, rs, xb = cls[n - 1], "mark_at_horizon", n - 1
    e["r"] = xr; e["exit"] = rs; e["xb"] = xb
    e["mfe_pre"] = round(mfe_pre, 5)     # best excursion up to & incl. the exit bar
    e["mae_pre"] = round(mae_pre, 5)
    # ---- post-stop forensics (only meaningful for stop exits) ----
    if rs == "stop":
        post = fav[xb + 1:] if xb + 1 < n else []
        postadv = adv[xb + 1:] if xb + 1 < n else []
        e["mfe_post"] = round(max(post), 5) if post else None
        e["mae_post"] = round(min(postadv), 5) if postadv else None
        bt = next((j for j, v in enumerate(post) if v >= tgt - 1e-12), None)
        e["bars_to_tgt_post"] = (bt + 1) if bt is not None else None   # bars AFTER the stop bar
        b0 = next((j for j, v in enumerate(post) if v >= 0.0), None)
        e["bars_to_be_post"] = (b0 + 1) if b0 is not None else None
        e["r_end"] = round(cls[n - 1], 5)
        e["bars_left"] = n - 1 - xb
        # what a NO-STOP contract (target else mark at horizon) books on this same row
        e["nostop_r"] = round(tgt if bt is not None else cls[n - 1], 5)
    recs.append(e)

N = len(recs)
res = {"n_rows": N,
       "population_rules": {
           "born_state_anchor": "mkt_r_prev_close (close of M1 bar stamped decision-1min)",
           "fill": "resting limit at entry_price; first bar with adv<=0",
           "tie": "stop wins same-bar ties",
           "horizon": "120 M1 bars = 2h hard cap"}}

# ---------- population ladder ----------
def stats(v):
    if not v:
        return None
    rr = [x["r"] for x in v if "r" in x]
    return {"n": len(v), "mean_r": mean(rr),
            "win_pct": round(100 * sum(1 for x in rr if x > 0) / len(rr), 3) if rr else None,
            "stop_pct": round(100 * sum(1 for x in v if x.get("exit") == "stop") / len(v), 3),
            "target_pct": round(100 * sum(1 for x in v if x.get("exit") == "target") / len(v), 3),
            "mark_pct": round(100 * sum(1 for x in v if x.get("exit") == "mark_at_horizon") / len(v), 3),
            "nofill_pct": round(100 * sum(1 for x in v if x.get("exit") == "no_fill") / len(v), 3)}

ALL = recs
TRADEABLE = [x for x in recs if x["born"] != "born_past_stop"]
FILLED = [x for x in TRADEABLE if x["fb"] is not None]
res["populations"] = {"ALL": stats(ALL), "EX_PAST_STOP": stats(TRADEABLE),
                      "EX_PAST_STOP_FILLED": stats(FILLED),
                      "BORN_PAST_STOP": stats([x for x in recs if x["born"] == "born_past_stop"])}
res["born_census_n"] = {b: sum(1 for x in recs if x["born"] == b) for b in
                        ("born_resting", "born_at_limit", "born_marketable", "born_past_stop", "unknown")}

# ---------- Q1: stopped, then reversed ----------
for label, pop in (("HONEST_tradeable_filled", FILLED), ("ALL_rows_incl_untakeable", [x for x in recs if x["fb"] is not None])):
    S = [x for x in pop if x.get("exit") == "stop"]
    ns = len(S)
    reach_t = [x for x in S if x.get("bars_to_tgt_post") is not None]
    reach_be = [x for x in S if x.get("bars_to_be_post") is not None]
    mfep = [x["mfe_post"] for x in S if x.get("mfe_post") is not None]
    blk = {"n_stopped": ns,
           "share_of_population_pct": round(100 * ns / len(pop), 3),
           "reached_target_after_stop_n": len(reach_t),
           "reached_target_after_stop_pct": round(100 * len(reach_t) / ns, 3),
           "reached_breakeven_after_stop_n": len(reach_be),
           "reached_breakeven_after_stop_pct": round(100 * len(reach_be) / ns, 3),
           "bars_to_target_after_stop": {"median": q([x["bars_to_tgt_post"] for x in reach_t], .5),
                                         "p25": q([x["bars_to_tgt_post"] for x in reach_t], .25),
                                         "p75": q([x["bars_to_tgt_post"] for x in reach_t], .75),
                                         "p90": q([x["bars_to_tgt_post"] for x in reach_t], .90),
                                         "mean": mean([x["bars_to_tgt_post"] for x in reach_t])},
           "bars_remaining_after_stop": {"median": q([x["bars_left"] for x in S], .5),
                                         "mean": mean([x["bars_left"] for x in S])},
           "mfe_after_stop": {"mean": mean(mfep), "median": q(mfep, .5), "p75": q(mfep, .75),
                              "p90": q(mfep, .90),
                              "share_ge_1R": round(100 * sum(1 for v in mfep if v >= 1.0) / len(mfep), 3),
                              "share_ge_2R": round(100 * sum(1 for v in mfep if v >= 2.0) / len(mfep), 3),
                              "share_ge_0R": round(100 * sum(1 for v in mfep if v >= 0.0) / len(mfep), 3)},
           "counterfactual_no_stop_on_these_rows": {
               "mean_r_with_stop": -1.0,
               "mean_r_no_stop": mean([x["nostop_r"] for x in S]),
               "forgone_r_per_stopped_trade": round((mean([x["nostop_r"] for x in S]) or 0) + 1.0, 5),
               "forgone_r_per_population_trade": round(((mean([x["nostop_r"] for x in S]) or 0) + 1.0) * ns / len(pop), 5),
               "r_at_horizon_mean_on_stopped": mean([x["r_end"] for x in S])}}
    res["Q1_stopped_then_reversed_" + label] = blk

# ---------- Q2: MAE of eventual winners ----------
W = [x for x in FILLED if x.get("exit") == "target"]
mae = [x["mae_pre"] for x in W]
edges = [(-0.1, 0.0), (-0.2, -0.1), (-0.3, -0.2), (-0.4, -0.3), (-0.5, -0.4),
         (-0.6, -0.5), (-0.7, -0.6), (-0.8, -0.7), (-0.9, -0.8), (-1.0, -0.9)]
hist = []
for lo, hi in edges:
    c = sum(1 for v in mae if lo <= v < hi) if hi < 0 else sum(1 for v in mae if lo <= v <= hi)
    hist.append({"band": f"[{lo},{hi})", "n": c, "pct_of_winners": round(100 * c / len(mae), 3)})
res["Q2_winner_mae"] = {
    "n_winners_target": len(W),
    "mae_hist": hist,
    "mae_stats": {"mean": mean(mae), "median": q(mae, .5), "p10": q(mae, .10), "p25": q(mae, .25),
                  "p75": q(mae, .75), "p90": q(mae, .90), "min": round(min(mae), 5)},
    "share_mae_worse_than_-0.5R": round(100 * sum(1 for v in mae if v <= -0.5) / len(mae), 3),
    "share_mae_worse_than_-0.75R": round(100 * sum(1 for v in mae if v <= -0.75) / len(mae), 3),
    "share_mae_in_-0.8_to_-1.0": round(100 * sum(1 for v in mae if -1.0 <= v <= -0.8) / len(mae), 3),
    "share_mae_in_-0.9_to_-1.0": round(100 * sum(1 for v in mae if -1.0 <= v <= -0.9) / len(mae), 3),
    "note": "winners here = honest first-touch TARGET exits on filled, ex-past-stop rows"}
# and the same for the marked-at-horizon positive rows (the other winner class)
Mk = [x for x in FILLED if x.get("exit") == "mark_at_horizon" and x["r"] > 0]
res["Q2_marked_positive_mae"] = {"n": len(Mk), "mae_mean": mean([x["mae_pre"] for x in Mk]),
                                 "mae_median": q([x["mae_pre"] for x in Mk], .5),
                                 "share_worse_than_-0.5R": round(100 * sum(1 for x in Mk if x["mae_pre"] <= -0.5) / len(Mk), 3)}

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)

# also dump the per-row record set for downstream steps (compact)
with gzip.open(os.path.join(D, "l2_RECS_V1.jsonl.gz"), "wt") as fh:
    for e in recs:
        fh.write(json.dumps(e, separators=(",", ":")) + "\n")

print("wrote", OUT)
print("pop ALL", res["populations"]["ALL"])
print("pop EXPS_FILLED", res["populations"]["EX_PAST_STOP_FILLED"])
print("Q1 honest", {k: v for k, v in res["Q1_stopped_then_reversed_HONEST_tradeable_filled"].items()
                    if k in ("n_stopped", "reached_target_after_stop_pct", "reached_breakeven_after_stop_pct",
                             "counterfactual_no_stop_on_these_rows")})
print("Q2", res["Q2_winner_mae"]["mae_stats"], res["Q2_winner_mae"]["share_mae_in_-0.8_to_-1.0"])
