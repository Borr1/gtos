#!/usr/bin/env python3
"""A2 RECONCILE lane — rows A, B, J from the RAW TRADE and ORDER ledgers.

Applies BOTH loss-class rules (the Jan walker's rule and the Feb walker's rule,
re-implemented here from their receipt definitions) to BOTH months' raw TRADE
ledgers, computes the movement cross-tab, the breaker count (row B), and the
row-level order->trade reconciliation (row J).
February read is attribution-only under owner_mandate_20260801.
Writes TRADES_ORDERS_RESULT.json beside itself.
"""
import json, os
from collections import Counter, defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
JAN = ("/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/"
       "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
       "attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7")
FEB = ("/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/"
       "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
       "attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1")

# ---- Jan walker's rule (attribute_trades_jan.py) --------------------------------
STOP_REASONS = {"selected_policy_replay:stop_loss", "stop_reached_before_target"}
TARGET_REASONS = {"selected_policy_replay:final_target", "target_reached_before_stop"}
MARK_REASONS = {"selected_policy_replay:path_end_mark_to_market", "time_stop_close_mark_from_m1"}


def classify_jan_rule(t):
    g, n, c = t["gross_r"], t["net_r"], t["cost_r"]
    mfe = t["mfe_r"] if isinstance(t["mfe_r"], (int, float)) else None
    mae = t["mae_r"] if isinstance(t["mae_r"], (int, float)) else None
    cr = t["close_reason"]
    if g is None or n is None:
        return "unscoreable"
    if n > 0:
        return "winner_target" if cr in TARGET_REASONS else "winner_other"
    if g >= 0 or (c is not None and abs(g) <= c):
        return "cost_dominated"
    if mfe is not None and mfe >= 0.5:
        return "exit_geometry"
    if (cr in STOP_REASONS or (mae is not None and mae <= -0.9)) and (mfe is None or mfe < 0.5):
        return "direction_wrong"
    if cr in MARK_REASONS:
        return "horizon_marked"
    return "other_loss"


# ---- Feb walker's rule (03_attribution_and_aggregations.py) ---------------------
T_KINDS = ("final_target", "target_reached_before_stop")
S_KINDS = ("stop_loss", "stop_reached_before_target")
H_KINDS = ("path_end_mark_to_market", "time_stop")


def reason_kind(cr):
    cr = (cr or "").split(":")[-1]
    if any(t in cr for t in T_KINDS):
        return "target"
    if any(s in cr for s in S_KINDS):
        return "stop"
    if any(h in cr for h in H_KINDS):
        return "horizon"
    if "giveback" in cr:
        return "giveback"
    return "other"


def classify_feb_rule(t):
    net, gross = t["net_r"], t["final_r"]
    if net is None or gross is None:
        return "unscoreable"
    mfe = t.get("mfe_r")
    cost = t.get("cost_r") or 0.0
    kind = reason_kind(t.get("close_reason"))
    if net > 0:
        return "target_hit" if kind == "target" else "other"
    if gross >= 0 and net <= 0:
        return "cost_dominated"
    if mfe is not None and mfe < 0.25:
        return "direction_wrong"
    if mfe is not None and (mfe - cost) > 0:
        return "exit_geometry"
    if kind == "stop":
        return "stop_hit"
    if kind in ("horizon", "giveback"):
        return "horizon_marked"
    return "other"


FIELDS = ["candidate_id", "decision_time_utc", "symbol", "direction", "origin_family",
          "framework", "setup_family", "close_reason", "gross_r", "final_r", "net_r",
          "cost_r", "mfe_r", "mae_r"]


def load_trades(prefix):
    trades = []
    with open(prefix + "_TRADE_LEDGER.jsonl") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            trades.append({k: r.get(k) for k in FIELDS})
    return trades


def class_table(trades, fn):
    out = defaultdict(lambda: {"n": 0, "net_r": 0.0, "gross_r": 0.0, "cost_r": 0.0})
    for t in trades:
        c = out[fn(t)]
        c["n"] += 1
        c["net_r"] += t["net_r"] or 0.0
        c["gross_r"] += (t["final_r"] if t["final_r"] is not None else (t["gross_r"] or 0.0)) or 0.0
        c["cost_r"] += t["cost_r"] or 0.0
    for c in out.values():
        for k in ("net_r", "gross_r", "cost_r"):
            c[k] = round(c[k], 6)
    return dict(out)


def movement(trades):
    mv = defaultdict(lambda: {"n": 0, "net_r": 0.0})
    for t in trades:
        key = f"{classify_jan_rule(t)} -> {classify_feb_rule(t)}"
        mv[key]["n"] += 1
        mv[key]["net_r"] += t["net_r"] or 0.0
    return {k: {"n": v["n"], "net_r": round(v["net_r"], 4)} for k, v in sorted(mv.items())}


def orders_pass(prefix):
    status = Counter()
    accepted, filled, expired = set(), set(), set()
    n = 0
    with open(prefix + "_ORDER_LEDGER.jsonl") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            n += 1
            st = r.get("order_status")
            status[str(st)] += 1
            key = (r.get("candidate_id"), r.get("decision_time_utc"))
            if st == "pending_accepted":
                accepted.add(key)
            elif st == "filled":
                filled.add(key)
            elif st == "expired_unfilled":
                expired.add(key)
    return n, status, accepted, filled, expired


def jmonth(prefix, trades):
    n, status, accepted, filled, expired = orders_pass(prefix)
    tkeys = {(t["candidate_id"], t["decision_time_utc"]) for t in trades}
    res = {
        "order_rows": n,
        "order_status_counts": dict(status),
        "n_accepted_keys": len(accepted),
        "n_filled_keys": len(filled),
        "n_expired_keys": len(expired),
        "accepted_minus_filled_keys": len(accepted - filled),
        "accepted_minus_filled_equals_expired": (accepted - filled) == expired,
        "expired_subset_of_accepted": expired <= accepted,
        "filled_subset_of_accepted": filled <= accepted,
        "trade_keys_equal_filled_keys": tkeys == filled,
        "expired_key_list": sorted(f"{c[:28]} @ {d}" for c, d in expired),
    }
    return res


def month_block(prefix, label):
    trades = load_trades(prefix)
    scoreable = [t for t in trades if t["net_r"] is not None]
    sum_net = round(sum(t["net_r"] for t in scoreable), 8)
    jr = class_table(trades, classify_jan_rule)
    fr = class_table(trades, classify_feb_rule)
    # final_r vs gross_r identity
    mism = sum(1 for t in trades
               if t["final_r"] is not None and t["gross_r"] is not None
               and abs(t["final_r"] - t["gross_r"]) > 1e-9)
    # row B: breaker
    br = [t for t in trades if t["origin_family"] == "current_breaker_re_entry"]
    br_sub = [t for t in trades if "breaker" in str(t["origin_family"]).lower()
              or "breaker" in str(t["framework"]).lower()
              or "breaker" in str(t["setup_family"]).lower()]
    breaker = {
        "n_rows_origin_family_exact": len(br),
        "n_rows_substring_3fields": len(br_sub),
        "substring_equals_exact": {(t["candidate_id"], t["decision_time_utc"]) for t in br}
                                   == {(t["candidate_id"], t["decision_time_utc"]) for t in br_sub},
        "n_scoreable": sum(1 for t in br if t["net_r"] is not None),
        "net_r_sum_scoreable": round(sum(t["net_r"] for t in br if t["net_r"] is not None), 8),
        "n_unique_candidate_ids": len({t["candidate_id"] for t in br}),
        "unscoreable_breaker_rows": [f"{t['candidate_id'][:28]} {t['symbol']}"
                                     for t in br if t["net_r"] is None],
        "winners": sum(1 for t in br if (t["net_r"] or 0) > 0),
    }
    return {
        "n_trades": len(trades),
        "n_scoreable": len(scoreable),
        "sum_net_r": sum_net,
        "sum_jan_rule_net": round(sum(v["net_r"] for v in jr.values()), 8),
        "sum_feb_rule_net": round(sum(v["net_r"] for v in fr.values()), 8),
        "final_r_vs_gross_r_mismatches": mism,
        "jan_rule_classes": jr,
        "feb_rule_classes": fr,
        "movement_jan_rule_to_feb_rule": movement(trades),
        "breaker": breaker,
        "J_orders": jmonth(prefix, trades),
    }


def main():
    out = {"schema": "gtos.a2_verify.reconcile.trades_orders.v1",
           "note_february": "February read is attribution-only under owner_mandate_20260801.",
           "rule_definitions": {
               "jan_rule": "unscoreable -> winner(target/other) -> cost_dominated (g>=0 or |g|<=cost) -> "
                           "exit_geometry (MFE>=0.5) -> direction_wrong (stop-close or MAE<=-0.9, MFE<0.5) -> "
                           "horizon_marked -> other_loss",
               "feb_rule": "unscoreable -> target_hit/other(winners) -> cost_dominated (g>=0, n<=0) -> "
                           "direction_wrong (mfe<0.25) -> exit_geometry (mfe-cost>0) -> stop_hit -> "
                           "horizon_marked -> other"}}
    out["january"] = month_block(JAN, "january")
    print("JAN done: n", out["january"]["n_trades"], "sum", out["january"]["sum_net_r"])
    out["february"] = month_block(FEB, "february")
    print("FEB done: n", out["february"]["n_trades"], "sum", out["february"]["sum_net_r"])
    with open(os.path.join(OUT, "TRADES_ORDERS_RESULT.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    for m in ("january", "february"):
        b = out[m]
        print(f"\n== {m} jan-rule:")
        for k, v in sorted(b["jan_rule_classes"].items()):
            print("  %-16s n=%3d net=%+10.4f" % (k, v["n"], v["net_r"]))
        print(f"== {m} feb-rule:")
        for k, v in sorted(b["feb_rule_classes"].items()):
            print("  %-16s n=%3d net=%+10.4f" % (k, v["n"], v["net_r"]))
        print("breaker:", {k: v for k, v in b["breaker"].items() if "list" not in k})
        print("J:", {k: v for k, v in b["J_orders"].items() if k != "expired_key_list"})


if __name__ == "__main__":
    main()
