#!/usr/bin/env python3
"""l6 — build the GATE FRAME: one compact row per candidate carrying every gate/refusal
field plus the honest outcome under the no-look-ahead fill contract.

Outcome contract (identical to w0-capture W0CAP2_NOLOOKAHEAD_FULL_V1):
  born state   from mkt_r_prev_close (close of the M1 bar that closes AT the decision) —
               born_past_stop <= -1.0 R, born_marketable < 0, born_at_limit == 0, else resting
  filled       first bar where adv[i] <= 0.0 (entry price touched)
  hr           honest first-touch walk from the fill bar: target=policy_target_r, stop=-1R,
               else mark at horizon clipped to [-1, tgt]
  eng          the pool's own walked gross_r (contaminated by untakeable rows — kept for A/B)

Writes l6_GATEFRAME_V1.jsonl.gz
"""
import gzip, json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa: E402

OUT = os.path.join(D, "l6_GATEFRAME_V1.jsonl.gz")

GATE_FIELDS = [
    "final_blocker_class", "miss_reason",
    "selector_action", "selector_reason",
    "effective_selector_action", "effective_selector_reason",
    "risk_finalizer_reason", "risk_finalizer_rank",
    "scheduler_selection_disposition", "scheduler_materialization_status",
    "candidate_lifecycle_action", "same_symbol_lifecycle_action",
    "pretrade_cost_packet_status", "broker_pretrade_cost_executable",
    "admission_risk_class", "fill_realism_class", "fill_realism_executable",
    "entry_fill_executable", "effective_order_type", "source_completeness",
    "limit_marketable_at_decision", "effective_admission_count", "matched_sleeve_count",
    "route_session", "session_bucket", "authority_session", "kill_zone",
    "dynamic_geometry_policy", "selected_policy_for_expected_net_r",
    "swap_horizon_repair_status", "commission_r_repair_status",
    "confidence_default_applied", "source_bound_signal_r",
]
NUM_FIELDS = [
    "gross_r", "cost_r", "spread_r", "commission_r", "swap_cost_r", "expected_slippage_r",
    "expected_cost_r", "expected_net_r", "opportunity_net_proxy_r", "candidate_ev_r",
    "candidate_probability", "candidate_confidence", "expectancy_r",
    "execution_fill_probability", "fill_probability", "risk_per_trade_pct",
    "policy_target_r", "raw_target_r", "risk_distance", "entry_price",
    "same_symbol_exposure_risk_pct", "same_side_pending_risk_pct", "opposite_pending_risk_pct",
    "mfe_r", "mae_r", "setup_dup_count", "setup_dup_rank",
    "broker_pretrade_diag_expected_cost_r", "fallback_execution_surcharge_r",
    "guarded_market_fallback_extra_cost_r", "commission_r_broker_true_measured",
]
META = ["candidate_id", "decision_time_utc", "symbol", "side", "origin_family", "setup_family",
        "decision_timeframe", "utc_hour_bucket", "is_first_emission", "outcome_band",
        "which_came_first", "fill_honest_walk_r", "plain_walk_r", "path_bars"]


def born(m):
    return ("born_past_stop" if m <= -1.0 else
            "born_marketable" if m < 0.0 else
            "born_at_limit" if m == 0.0 else "born_resting")


def main():
    rows = w0_ws.load()
    byk = {w0_ws.key(r): r for r in rows}
    anch = {}
    with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
        for ln in f:
            a = json.loads(ln)
            anch[(a["candidate_id"], a["decision_time_utc"])] = a

    n_out = 0
    n_noanchor = 0
    with gzip.open(OUT, "wt") as out:
        for rp in w0_ws.iter_rpaths():
            k = (rp["candidate_id"], rp["decision_time_utc"])
            r = byk.get(k)
            if r is None:
                continue
            a = anch.get(k)
            fav, adv = rp["fav"], rp["adv"]
            tgt = rp.get("policy_target_r") or 2.0
            fb = next((i for i in range(len(adv)) if adv[i] <= 0.0), None)
            rec = {f: r.get(f) for f in META}
            for f in GATE_FIELDS:
                rec[f] = r.get(f)
            for f in NUM_FIELDS:
                rec[f] = r.get(f)
            if a is None:
                n_noanchor += 1
                rec["born"] = None
                rec["m"] = None
            else:
                rec["m"] = a["mkt_r_prev_close"]
                rec["born"] = born(a["mkt_r_prev_close"])
            rec["filled"] = fb is not None
            rec["fill_bar"] = fb
            if fb is not None:
                xr = None
                rs = None
                mfe = -9e9
                for i in range(fb, len(fav)):
                    mfe = max(mfe, fav[i])
                    ht = fav[i] >= tgt
                    hs = adv[i] <= -1.0
                    if ht and hs:
                        xr, rs = -1.0, "same_bar"
                        break
                    if ht:
                        xr, rs = tgt, "target"
                        break
                    if hs:
                        xr, rs = -1.0, "stop"
                        break
                if xr is None:
                    xr, rs = max(-1.0, min(rp["cls"][-1], tgt)), "mark_at_horizon"
                rec["hr"] = round(xr, 6)
                rec["hreason"] = rs
                rec["hmfe"] = round(mfe, 4)
            else:
                rec["hr"] = None
                rec["hreason"] = "no_fill"
                rec["hmfe"] = None
            # takeable = not born past stop AND filled
            rec["takeable"] = (rec["born"] is not None and rec["born"] != "born_past_stop"
                               and rec["filled"])
            out.write(json.dumps(rec) + "\n")
            n_out += 1
    print(json.dumps({"rows": n_out, "no_anchor": n_noanchor, "out": OUT}))


if __name__ == "__main__":
    main()
