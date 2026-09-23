#!/usr/bin/env python3
"""l8_frame — build the lane-8 analysis frame: working set + decision anchor + derived axes.

Writes l8_FRAME.jsonl.gz (one row per pool candidate, only the columns l8 sweeps need).
"""
import gzip, json, os, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "w0_WORKING_SET.jsonl.gz")
ANCH = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
OUT = os.path.join(HERE, "l8_FRAME.jsonl.gz")


def born_state(mkt_r):
    if mkt_r is None:
        return "unknown"
    if mkt_r <= -1.0:
        return "born_past_stop"
    if mkt_r < -1e-9:
        return "born_marketable"
    if mkt_r <= 1e-9:
        return "born_at_limit"
    return "born_resting"


def qbucket(v, edges, labels):
    if v is None:
        return "null"
    for e, lab in zip(edges, labels):
        if v <= e:
            return lab
    return labels[-1]


def main():
    anchor = {}
    with gzip.open(ANCH, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            anchor[(r["candidate_id"], r["decision_time_utc"])] = r

    rows = []
    with gzip.open(WS, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            k = (r["candidate_id"], r["decision_time_utc"])
            a = anchor.get(k)
            mkt = a["mkt_r_prev_close"] if a else None
            t = dt.datetime.fromisoformat(r["decision_time_utc"].replace("Z", "+00:00"))
            rd = r.get("risk_distance")
            ep = r.get("entry_price")
            rdp = (rd / ep * 100.0) if (rd and ep) else None
            out = {
                "cid": r["candidate_id"],
                "dt": r["decision_time_utc"],
                "day": t.day,
                "dow": t.weekday(),
                "hour": t.hour,
                "gross_r": r.get("gross_r"),
                "plain_walk_r": r.get("plain_walk_r"),
                "honest_r": r.get("fill_honest_walk_r"),
                "cost_r": r.get("cost_r"),
                "spread_r": r.get("spread_r"),
                "mkt_r": mkt,
                "born": born_state(mkt),
                "symbol": r.get("symbol"),
                "family": r.get("origin_family"),
                "framework": r.get("framework"),
                "setup_family": r.get("setup_family"),
                "bucket_source_family": r.get("bucket_source_family"),
                "side": r.get("side"),
                "dtf": r.get("decision_timeframe"),
                "mtf": r.get("market_timeframe"),
                "session": r.get("session_bucket"),
                "route_session": r.get("route_session"),
                "kill_zone": r.get("kill_zone"),
                "msc": r.get("matched_sleeve_count"),
                "conf": r.get("candidate_confidence"),
                "prob": r.get("candidate_probability"),
                "ev_r": r.get("candidate_ev_r"),
                "risk_pct": r.get("risk_per_trade_pct"),
                "rdp": rdp,
                "sched": r.get("scheduler_materialization_status"),
                "blocker": r.get("final_blocker_class"),
                "miss_reason": r.get("miss_reason"),
                "lifecycle": r.get("candidate_lifecycle_action"),
                "order_type": r.get("effective_order_type"),
                "fill_class": r.get("fill_realism_class"),
                "fill_prob": r.get("execution_fill_probability"),
                "limit_mkt": r.get("limit_marketable_at_decision"),
                "sel_action": r.get("selector_action"),
                "sched_disp": r.get("scheduler_selection_disposition"),
                "dyn_geo": r.get("dynamic_geometry_policy"),
                "risk_rank": r.get("risk_finalizer_rank"),
                "policy_target_r": r.get("policy_target_r"),
                "which_first": r.get("which_came_first"),
                "mfe_r": r.get("mfe_r"),
                "mae_r": r.get("mae_r"),
                "dup_count": r.get("setup_dup_count"),
                "first_em": r.get("is_first_emission"),
                "same_sym_risk": r.get("same_symbol_exposure_risk_pct"),
                "same_side_risk": r.get("same_side_pending_risk_pct"),
                "opp_risk": r.get("opposite_pending_risk_pct"),
                "adm_count": r.get("effective_admission_count"),
                "src_completeness": r.get("source_completeness"),
                "swap_r": r.get("swap_cost_r"),
                "comm_r": r.get("commission_r"),
                "utc_hour_bucket": r.get("utc_hour_bucket"),
                "auth_session": r.get("authority_session"),
                "path_bars": r.get("path_bars"),
                "adm_risk_class": r.get("admission_risk_class"),
            }
            # derived buckets
            out["rdp_b"] = qbucket(rdp, [0.02, 0.05, 0.10, 0.20, 0.40], ["<=0.02", "0.02-0.05", "0.05-0.10", "0.10-0.20", "0.20-0.40", ">0.40"])
            out["spread_b"] = qbucket(r.get("spread_r"), [0.05, 0.10, 0.20, 0.40, 1.0], ["<=0.05", "0.05-0.10", "0.10-0.20", "0.20-0.40", "0.40-1.0", ">1.0"])
            out["cost_b"] = qbucket(r.get("cost_r"), [0.10, 0.15, 0.25, 0.50, 1.0], ["<=0.10", "0.10-0.15", "0.15-0.25", "0.25-0.50", "0.50-1.0", ">1.0"])
            out["prob_b"] = qbucket(r.get("candidate_probability"), [0.65, 0.70, 0.75, 0.80, 0.85], ["<=0.65", "0.65-0.70", "0.70-0.75", "0.75-0.80", "0.80-0.85", ">0.85"])
            out["ev_b"] = qbucket(r.get("candidate_ev_r"), [0.6, 0.8, 1.0, 1.2, 1.5], ["<=0.6", "0.6-0.8", "0.8-1.0", "1.0-1.2", "1.2-1.5", ">1.5"])
            out["fillp_b"] = qbucket(r.get("execution_fill_probability"), [0.2, 0.5, 0.8, 0.91, 0.92], ["<=0.2", "0.2-0.5", "0.5-0.8", "0.8-0.91", "=0.92", ">0.92"])
            out["third"] = "J1_d1_10" if t.day <= 10 else ("J2_d11_20" if t.day <= 20 else "J3_d21_31")
            out["half"] = "H1_d1_15" if t.day <= 15 else "H2_d16_31"
            out["week"] = "W%d" % (((t.day - 1) // 7) + 1)
            rows.append(out)

    with gzip.open(OUT, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    print("rows", len(rows), "->", OUT)


if __name__ == "__main__":
    main()
