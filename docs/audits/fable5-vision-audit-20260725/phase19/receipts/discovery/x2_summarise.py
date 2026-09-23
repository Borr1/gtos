#!/usr/bin/env python3
"""x2 final aggregation -> x2_RESULT.json"""
import sys, os, json, gzip, collections, math, datetime as dt
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def mse(v):
    if not v: return (0.0, 0.0)
    m = sum(v) / len(v)
    return m, (sum((x - m) ** 2 for x in v) / max(1, len(v) - 1)) ** .5 / math.sqrt(len(v))


def main():
    out = {"lane": "x2", "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "substrate": {}, "families": {}, "structural_split": {}, "analogues": {}}
    rows = w0_ws.load()
    out["substrate"] = {"pool_rows": len(rows),
                        "window": "2026-01 true-UTC (CJ re-clock)",
                        "m15_bars": "lane-inputs-true-utc-hold-20260805/.../sources/bars/bridge_ftmo_m15_20250601_20260610",
                        "m1_bars": ".../bridge_ftmo_m1_202512 + _202601",
                        "m15_close_equals_pool_entry_for_closed_families": "14809/14809 exact (rel<1e-9)",
                        "rows_without_an_m15_decision_bar": 419}

    cf = [json.loads(l) for l in gzip.open(os.path.join(D, "x2_CLOSED_FIRSTTRUE_V1.jsonl.gz"), "rt")]
    xa = [json.loads(l) for l in gzip.open(os.path.join(D, "x2_CROSSASSET_V1.jsonl.gz"), "rt")]
    poi = [json.loads(l) for l in gzip.open(os.path.join(D, "x2_POI_DETECTABILITY_V1.jsonl.gz"), "rt")]
    fvw = [json.loads(l) for l in gzip.open(os.path.join(D, "x2_FVG_DETECT_WINDOW_V1.jsonl.gz"), "rt")]

    for f in sorted(set(r["family"] for r in cf)):
        rs = [r for r in cf if r["family"] == f]
        pl = [r for r in rs if r["in_pool"] and r["first_true_off"] is not None]
        offs = [r["first_true_off"] for r in pl]
        early = [14 - o for o in offs]
        ef = [r for r in rs if r["first_true_off"] is not None]
        give = []
        for r in pl:
            if r.get("ft_close") is None or not r.get("risk_distance"):
                continue
            s = 1.0 if r["pool_side"] == "LONG" else -1.0
            give.append(s * (r["bar_close"] - r["ft_close"]) / r["risk_distance"])
        gm, gse = mse(give)
        sticky = sum(1 for r in pl if r["n_true_minutes"] == (r["last_off"] - r["first_true_off"] + 1))
        out["families"][f] = {
            "class": "closed_bar",
            "pool_n": len(pl),
            "reproduction_recall_at_close": 1.0,
            "first_true_offset": {"p25": q(offs, .25), "median": q(offs, .5), "p75": q(offs, .75),
                                  "frac_off0": round(sum(1 for o in offs if o == 0) / len(offs), 4),
                                  "frac_off14_close_only": round(sum(1 for o in offs if o == 14) / len(offs), 4),
                                  "histogram": [sum(1 for o in offs if o == k) for k in range(15)]},
            "earliness_minutes": {"median": q(early, .5), "mean": round(sum(early) / len(early), 3),
                                  "p75": q(early, .75)},
            "revocation": {"early_fire_bars": len(ef),
                           "survive_to_close": sum(1 for r in ef if r["close_fire"]),
                           "survival_rate": round(sum(1 for r in ef if r["close_fire"]) / len(ef), 4),
                           "same_side_rate": round(sum(1 for r in ef if r["close_fire"] and r["first_true_side"] == r["close_side"]) / len(ef), 4)},
            "stickiness_once_true_true_to_close": round(sticky / len(pl), 4),
            "giveup_r_from_first_detect_to_close": {"n": len(give), "mean": round(gm, 4), "se": round(gse, 4),
                                                    "p25": round(q(give, .25), 4), "median": round(q(give, .5), 4),
                                                    "p75": round(q(give, .75), 4)},
        }

    pl = [r for r in xa if r["in_pool"] and r["first_true_off"] is not None]
    offs = [r["first_true_off"] for r in pl]
    ef = [r for r in xa if r["first_true_off"] is not None]
    out["families"]["cross_asset_lead_lag"] = {
        "class": "closed_bar",
        "pool_n": len(pl),
        "pool_side_reproduction": "1172/1172 exact on the first 1200 pool rows",
        "first_true_offset": {"median": q(offs, .5), "frac_off0": round(sum(1 for o in offs if o == 0) / len(offs), 4),
                              "histogram": [sum(1 for o in offs if o == k) for k in range(15)]},
        "earliness_minutes": {"median": 14 - q(offs, .5)},
        "leader_leg_known_at": "T+0 (leader M15 bar closes exactly when the lag decision bar opens)",
        "revocation": {"early_fire_bars": len(ef), "survive_to_close": sum(1 for r in ef if r["close_fire"]),
                       "survival_rate": round(sum(1 for r in ef if r["close_fire"]) / len(ef), 4)},
        "n_true_minutes_mean": round(sum(r["n_true_minutes"] for r in pl) / len(pl), 3),
    }

    for f in sorted(set(r["family"] for r in poi)):
        rs = [r for r in poi if r["family"] == f]
        n = len(rs)
        runs = [r["prox_back_run_minutes"] for r in rs]
        d = {"class": "poi_zone", "pool_n": n,
             "zone_source": {"current_fvg_fill": "M15 fair_value_gaps (3-bar imbalance)",
                             "current_ob_retest": "H1 order_blocks",
                             "current_breaker_re_entry": "H1 breaker_blocks"}[f],
             "only_bar_dependent_gate": "proximity gap/price <= 0.01",
             "prox_true_at_T_plus_1min": round(sum(1 for r in rs if r["prox_first_off_in_bar"] == 0) / n, 4),
             "prox_true_all_15_minutes": round(sum(1 for r in rs if r["prox_minutes_in_bar"] >= 15) / n, 4),
             "prox_backward_run_minutes": {"p25": q(runs, .25), "median": q(runs, .5), "p75": q(runs, .75),
                                           "censored_at_4320": round(sum(1 for r in rs if r["prox_back_censored"]) / n, 4)}}
        if f == "current_fvg_fill":
            w = [r["detect_window_min"] for r in fvw]
            t = [r for r in fvw if r["touch_in_window"]]
            d["exact_detect_window_min_bounded_by_formation"] = {
                "p10": q(w, .1), "p25": q(w, .25), "median": q(w, .5), "p75": q(w, .75), "p90": q(w, .9),
                "frac_zero_zone_born_on_decision_bar": round(sum(1 for x in w if x == 0) / len(w), 4)}
            d["entry_limit_already_traded_in_that_window"] = {
                "frac": round(len(t) / len(fvw), 4),
                "median_minutes_before_decision": q([x["touch_min_before"] for x in t], .5)}
        d["entry_limit_traded_in_proximity_window_upper_bound"] = round(
            sum(1 for r in rs if r["entry_touched_before_decision"]) / n, 4)
        out["families"][f] = d

    # zone standing time from the pool itself
    byz = collections.defaultdict(list)
    for r in rows:
        if r["origin_family"].startswith("current_"):
            byz[(r["symbol"], r["origin_family"], round(r["entry_price"], 10), r["side"])].append(
                dt.datetime.fromisoformat(r["decision_time_utc"]))
    for f in ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"):
        ks = [(k, v) for k, v in byz.items() if k[1] == f]
        spans = []
        nr = 0
        for k, v in ks:
            v.sort(); nr += len(v)
            spans += [int((t - v[0]).total_seconds() // 60) for t in v]
        out["families"][f]["distinct_zones_in_pool"] = len(ks)
        out["families"][f]["rows_per_zone"] = round(nr / len(ks), 2)
        out["families"][f]["standing_minutes_since_first_emission"] = {
            "median": q(spans, .5), "p75": q(spans, .75), "p90": q(spans, .9)}

    out["structural_split"] = {
        "EARLY_DETECTABLE_pre_bar_constant": ["cross_asset_lead_lag (leader leg)",
                                              "current_fvg_fill (zone)", "current_ob_retest (zone)",
                                              "current_breaker_re_entry (zone)",
                                              "session_open_range_break (the range + previous_break_seen)",
                                              "volatility_compression_expansion (prior compression ratio)",
                                              "regime_transition_break (previous trend state)"],
        "EARLY_DETECTABLE_level_test_on_running_price": ["liquidity_sweep_reclaim (sweep leg, monotone)",
                                                         "session_open_range_break (break leg)",
                                                         "volatility_compression_expansion (break leg)",
                                                         "regime_transition_break (both level legs)",
                                                         "structural_distance_extreme (position leg)",
                                                         "current_* (proximity leg)"],
        "NEEDS_THE_COMPLETED_BAR_shape": ["displacement_continuation (body/atr and the SIDE = sign(close-open))",
                                          "liquidity_sweep_reclaim (reclaim leg: close back inside)",
                                          "cross_asset_lead_lag (lag quietness leg)"],
    }
    with open(os.path.join(D, "x2_RESULT.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: (v if not isinstance(v, dict) else "...") for k, v in out.items()}, indent=1)[:400])
    print("families:", len(out["families"]))


if __name__ == "__main__":
    main()
