#!/usr/bin/env python3
"""Session FA funnel_feb — Tasks 1 (waterfall), 2, 3, 4, 6, 7.

Inputs: compact per-row pickles extracted from the full MISSED_OPPORTUNITY
ledgers by extract_funnel_fields.py (Feb = CP_FEBRUARY_TRUE_UTC_S0R0_V1,
Jan = CJ_RECLOCKED_S0R0_V7), plus the two lane trade tables.

ATTRIBUTION EVIDENCE ONLY: February numbers here are defect attribution under
the 2026-08-01 owner mandate — never a selection surface.

Stage model (pipeline order, first-refusal attribution):
  S1_selector          effective_selector_action in {reject, source-required}
  S2_materialization   else scheduler_materialization_status == not_scheduler_ranked
  S3_scheduler_select  else scheduler_selection_disposition == candidate_generated_not_scheduler_selected
  S4_risk_finalizer    else scheduler_selection_disposition == scheduler_preselected_then_rejected_by_finalizer
  S5_unattributed      remainder (must be ~0)
"""
import gzip, json, pickle, collections

SCR = "/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave19-broad-forensic-20260801/98effd87-573e-44dc-bce2-9006f5900645/scratchpad"
OUT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/wave19_broad_forensic_2026_08_01/funnel_feb/"
LANE = {
    "feb": "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl",
    "jan": "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl",
}
METALS = {"XAUUSD", "XAGUSD"}


def stage_of(r):
    esa = r["effective_selector_action"]
    if esa in ("reject", "source-required"):
        return "S1_selector"
    if r["scheduler_materialization_status"] == "not_scheduler_ranked":
        return "S2_materialization"
    disp = r["scheduler_selection_disposition"]
    if disp == "candidate_generated_not_scheduler_selected":
        return "S3_scheduler_select"
    if disp == "scheduler_preselected_then_rejected_by_finalizer":
        return "S4_risk_finalizer"
    return "S5_unattributed"


def reason_of(r, stage):
    if stage == "S1_selector":
        return r["effective_selector_reason"]
    if stage == "S2_materialization":
        return r["miss_reason"]
    if stage == "S3_scheduler_select":
        return r["risk_finalizer_reason"]
    if stage == "S4_risk_finalizer":
        return r["risk_finalizer_reason"]
    return r["miss_reason"]


def econ_acc():
    return {"n": 0, "sum_net": 0.0, "sum_gross": 0.0, "sum_cost": 0.0, "n_pos": 0}


def econ_add(a, r):
    net, gr, c = r["opportunity_net_proxy_r"], r["opportunity_gross_r"], r["cost_r"]
    a["n"] += 1
    a["sum_net"] += net
    a["sum_gross"] += gr if gr is not None else (net + (c or 0.0))
    a["sum_cost"] += c or 0.0
    if net > 0:
        a["n_pos"] += 1


def econ_close(a):
    n = a["n"]
    if n == 0:
        return {"n": 0}
    return {
        "n": n,
        "sum_net_proxy_r": round(a["sum_net"], 4),
        "mean_net_proxy_r": round(a["sum_net"] / n, 6),
        "mean_gross_r": round(a["sum_gross"] / n, 6),
        "mean_cost_r": round(a["sum_cost"] / n, 6),
        "n_positive": a["n_pos"],
        "positive_share": round(a["n_pos"] / n, 6),
    }


def load(month):
    return pickle.load(gzip.open(f"{SCR}/{month}_funnel_rows.pkl.gz"))


def lane_trades(path):
    out = []
    with open(path) as f:
        for i, line in enumerate(f):
            d = json.loads(line)
            if d.get("row_kind") == "trade":
                out.append(d)
    return out


def analyze(month, rows):
    total = len(rows)
    sc = [r for r in rows if r["missed_opportunity_non_executable_diagnostic_scoreable"]]

    # ---------- waterfall ----------
    stage_all = collections.Counter()
    stage_sc = {}
    stage_reason_all = collections.Counter()
    stage_reason_sc = {}
    for r in rows:
        st = stage_of(r)
        r["_stage"] = st
        rs = reason_of(r, st)
        r["_reason"] = rs
        stage_all[st] += 1
        stage_reason_all[(st, rs)] += 1
        if r["missed_opportunity_non_executable_diagnostic_scoreable"]:
            econ_add(stage_sc.setdefault(st, econ_acc()), r)
            econ_add(stage_reason_sc.setdefault((st, rs), econ_acc()), r)

    order = ["S1_selector", "S2_materialization", "S3_scheduler_select",
             "S4_risk_finalizer", "S5_unattributed"]
    remaining = total
    waterfall = []
    for st in order:
        killed = stage_all.get(st, 0)
        waterfall.append({
            "stage": st,
            "entering": remaining,
            "refused_here": killed,
            "kill_rate_of_entering": round(killed / remaining, 6) if remaining else None,
            "share_of_physical": round(killed / total, 6),
            "scoreable_economics": econ_close(stage_sc.get(st, econ_acc())),
        })
        remaining -= killed

    # ---------- refusal vs outcome (scoreable) ----------
    refusal_tbl = []
    for (st, rs), acc in sorted(stage_reason_sc.items(), key=lambda kv: -kv[1]["n"]):
        e = econ_close(acc)
        e.update({"stage": st, "reason": rs,
                  "physical_n": stage_reason_all[(st, rs)],
                  "gate_economically_correct_on_mean_net": acc["sum_net"] / acc["n"] < 0})
        refusal_tbl.append(e)

    # ---------- residual choice set ----------
    choice = [r for r in rows
              if r["effective_selector_action"] in ("trade", "reduce-risk", "open-reduced-risk")
              and r["scheduler_materialization_status"] == "scheduler_option_materialized"]
    ch_sc = [r for r in choice if r["missed_opportunity_non_executable_diagnostic_scoreable"]]

    def econ_of(rs_):
        a = econ_acc()
        for r in rs_:
            econ_add(a, r)
        return econ_close(a)

    comp = collections.Counter(
        (r["origin_family"], r["direction"], r["session_bucket"]) for r in choice)
    comp_tbl = [{"origin_family": k[0], "direction": k[1], "session_bucket": k[2], "n": v}
                for k, v in comp.most_common(40)]
    declined = [r for r in ch_sc
                if r["scheduler_selection_disposition"] == "candidate_generated_not_scheduler_selected"]
    presel = [r for r in ch_sc
              if r["scheduler_selection_disposition"] == "scheduler_preselected_then_rejected_by_finalizer"]
    choice_set = {
        "definition": "effective_selector_action in {trade,reduce-risk,open-reduced-risk} AND scheduler_materialization_status == scheduler_option_materialized",
        "n_physical": len(choice),
        "n_scoreable": len(ch_sc),
        "scoreable_economics": econ_of(ch_sc),
        "composition_family_x_direction_x_session_top40": comp_tbl,
        "scheduler_declined_scoreable": econ_of(declined),
        "scheduler_preselected_then_finalizer_rejected_scoreable": econ_of(presel),
        "disposition_counts_physical": dict(collections.Counter(
            r["scheduler_selection_disposition"] for r in choice)),
    }

    # ---------- cost band ----------
    hot = [r for r in sc if (r["cost_r"] or 0) > 1.0]
    pool_net = sum(r["opportunity_net_proxy_r"] for r in sc)
    hot_net = sum(r["opportunity_net_proxy_r"] for r in hot)
    hot_phys = [r for r in rows if (r["cost_r"] or 0) > 1.0]
    cost_band = {
        "threshold": "cost_r > 1.0",
        "scoreable": {
            "n": len(hot), "row_share": round(len(hot) / len(sc), 6),
            "sum_net_proxy_r": round(hot_net, 4),
            "share_of_pool_net_loss": round(hot_net / pool_net, 6),
            "economics": econ_of(hot),
            "caught_by_stage": dict(collections.Counter(r["_stage"] for r in hot)),
            "caught_by_stage_reason_top12": [
                {"stage": k[0], "reason": k[1], "n": v} for k, v in collections.Counter(
                    (r["_stage"], r["_reason"]) for r in hot).most_common(12)],
        },
        "physical": {
            "n": len(hot_phys),
            "caught_by_stage": dict(collections.Counter(r["_stage"] for r in hot_phys)),
        },
        "leakage_into_choice_set": {
            "n": sum(1 for r in choice if (r["cost_r"] or 0) > 1.0),
            "scoreable_n": sum(1 for r in ch_sc if (r["cost_r"] or 0) > 1.0),
        },
    }

    # ---------- declined winners ----------
    winners = [r for r in sc if r["opportunity_net_proxy_r"] > 0]
    win_stage = collections.Counter(r["_stage"] for r in winners)
    win_reason = collections.Counter((r["_stage"], r["_reason"]) for r in winners)

    def class_block(rs_, label):
        gate = collections.Counter((r["_stage"], r["_reason"]) for r in rs_)
        return {
            "label": label,
            "economics": econ_of(rs_),
            "refusing_gate_top10": [
                {"stage": k[0], "reason": k[1], "n": v} for k, v in gate.most_common(10)],
        }

    ny_metal_long_sb = [r for r in sc if r["symbol"] in METALS
                        and r["direction"] == "LONG" and r["session_bucket"] == "ny"]
    ny_metal_long_as = [r for r in sc if r["symbol"] in METALS
                        and r["direction"] == "LONG" and r["authority_session"] == "ny"]
    lsr_long = [r for r in sc if r["origin_family"] == "liquidity_sweep_reclaim"
                and r["direction"] == "LONG"]
    declined_winners = {
        "n_scoreable_winners": len(winners),
        "winner_share_of_scoreable": round(len(winners) / len(sc), 6),
        "sum_winner_net_r": round(sum(r["opportunity_net_proxy_r"] for r in winners), 4),
        "refusing_stage": dict(win_stage.most_common()),
        "refusing_stage_reason_top15": [
            {"stage": k[0], "reason": k[1], "n": v} for k, v in win_reason.most_common(15)],
        "ny_long_metals_session_bucket": class_block(ny_metal_long_sb, "symbol in {XAUUSD,XAGUSD} & LONG & session_bucket==ny"),
        "ny_long_metals_authority_session": class_block(ny_metal_long_as, "symbol in {XAUUSD,XAGUSD} & LONG & authority_session==ny"),
        "liquidity_sweep_reclaim_long": class_block(lsr_long, "origin_family==liquidity_sweep_reclaim & LONG"),
    }

    # family / session / reason mixes for the comparison
    mixes = {
        "framework_mix_physical": dict(collections.Counter(r["framework"] for r in rows)),
        "selector_reason_mix_physical": dict(collections.Counter(r["selector_reason"] for r in rows)),
        "stage_kill_share": {st: round(stage_all.get(st, 0) / total, 6) for st in order},
        "direction_mix_physical": dict(collections.Counter(r["direction"] for r in rows)),
        "scoreable_share": round(len(sc) / total, 6),
    }
    return {
        "total_physical": total, "n_scoreable": len(sc),
        "pool_net_sum": round(pool_net, 4),
        "waterfall": waterfall, "refusal_tbl": refusal_tbl,
        "choice_set": choice_set, "cost_band": cost_band,
        "declined_winners": declined_winners, "mixes": mixes,
        "stage_reason_all": stage_reason_all,
    }


def main():
    feb_rows, jan_rows = load("feb"), load("jan")
    feb = analyze("feb", feb_rows)
    jan = analyze("jan", jan_rows)

    lane_feb = lane_trades(LANE["feb"])
    lane_jan = lane_trades(LANE["jan"])
    lane_sum = {m: {"n_trades": len(t),
                    "n_net_r_null": sum(1 for x in t if x.get("net_r") is None),
                    "sum_net_r_nonnull": round(sum(x["net_r"] for x in t if x.get("net_r") is not None), 5),
                    "n_cost_gt_1": sum(1 for x in t if (x.get("cost_r") or 0) > 1.0),
                    "max_cost_r": round(max((x.get("cost_r") or 0) for x in t), 5)}
                for m, t in (("feb", lane_feb), ("jan", lane_jan))}

    hdr = {
        "evidence_class": "FEBRUARY ATTRIBUTION EVIDENCE ONLY - owner mandate 2026-08-01; never a selection surface",
        "stage_model": "S1 selector refusal (effective_selector_action in {reject,source-required}) -> S2 materialization skip (not_scheduler_ranked) -> S3 scheduler decline -> S4 finalizer rejection of preselected",
    }

    W = lambda name, obj: json.dump(obj, open(OUT + name, "w"), indent=1)

    W("STAGE_WATERFALL.json", {
        "schema": "gtos.session_fa.funnel_feb.stage_waterfall.v1", **hdr,
        "february": feb["waterfall"], "january_reference": jan["waterfall"],
        "executed_lane_apex": lane_sum,
    })
    W("REFUSAL_VS_OUTCOME.json", {
        "schema": "gtos.session_fa.funnel_feb.refusal_vs_outcome.v1", **hdr,
        "n_scoreable": feb["n_scoreable"], "pool_net_sum_r": feb["pool_net_sum"],
        "per_refusal_class": feb["refusal_tbl"],
    })
    W("RESIDUAL_CHOICE_SET.json", {
        "schema": "gtos.session_fa.funnel_feb.residual_choice_set.v1", **hdr,
        "february": feb["choice_set"], "january_reference": jan["choice_set"],
        "executed_lane_apex": lane_sum,
    })
    W("COST_BAND_CROSS.json", {
        "schema": "gtos.session_fa.funnel_feb.cost_band_cross.v1", **hdr,
        "february": feb["cost_band"], "january_reference": jan["cost_band"],
    })
    W("DECLINED_WINNERS.json", {
        "schema": "gtos.session_fa.funnel_feb.declined_winners.v1", **hdr,
        "february": feb["declined_winners"],
        "january_reference": jan["declined_winners"],
    })

    # ---------- January comparison / drift ----------
    def share(d, tot):
        return {k: round(v / tot, 6) for k, v in d.items()}

    drift_rows = []
    keys = set(feb["mixes"]["selector_reason_mix_physical"]) | set(jan["mixes"]["selector_reason_mix_physical"])
    for k in sorted(keys):
        fj = feb["mixes"]["selector_reason_mix_physical"].get(k, 0) / feb["total_physical"]
        jj = jan["mixes"]["selector_reason_mix_physical"].get(k, 0) / jan["total_physical"]
        drift_rows.append({"selector_reason": k, "jan_share": round(jj, 6),
                           "feb_share": round(fj, 6), "delta_pp": round((fj - jj) * 100, 3)})
    fw_rows = []
    keys = set(feb["mixes"]["framework_mix_physical"]) | set(jan["mixes"]["framework_mix_physical"])
    for k in sorted(keys):
        fj = feb["mixes"]["framework_mix_physical"].get(k, 0) / feb["total_physical"]
        jj = jan["mixes"]["framework_mix_physical"].get(k, 0) / jan["total_physical"]
        fw_rows.append({"framework": k, "jan_share": round(jj, 6),
                        "feb_share": round(fj, 6), "delta_pp": round((fj - jj) * 100, 3)})
    # reasons appearing/disappearing across months (physical stage-reason table)
    fr = {f"{s}::{r}" for (s, r) in feb["stage_reason_all"]}
    jr = {f"{s}::{r}" for (s, r) in jan["stage_reason_all"]}
    W("JANUARY_COMPARISON.json", {
        "schema": "gtos.session_fa.funnel_feb.january_comparison.v1", **hdr,
        "totals": {"jan_physical": jan["total_physical"], "feb_physical": feb["total_physical"],
                   "jan_scoreable": jan["n_scoreable"], "feb_scoreable": feb["n_scoreable"],
                   "jan_scoreable_share": jan["mixes"]["scoreable_share"],
                   "feb_scoreable_share": feb["mixes"]["scoreable_share"]},
        "stage_kill_share": {"jan": jan["mixes"]["stage_kill_share"],
                             "feb": feb["mixes"]["stage_kill_share"]},
        "selector_reason_share_drift": drift_rows,
        "framework_share_drift": fw_rows,
        "stage_reasons_only_in_feb": sorted(fr - jr),
        "stage_reasons_only_in_jan": sorted(jr - fr),
        "waterfall_jan": jan["waterfall"], "waterfall_feb": feb["waterfall"],
        "declined_winners_jan_vs_feb": {
            "jan": {k: jan["declined_winners"][k] for k in
                    ("n_scoreable_winners", "winner_share_of_scoreable", "refusing_stage")},
            "feb": {k: feb["declined_winners"][k] for k in
                    ("n_scoreable_winners", "winner_share_of_scoreable", "refusing_stage")}},
    })
    print("DONE tables")
    # console digest
    for m, a in (("JAN", jan), ("FEB", feb)):
        print(f"\n== {m} waterfall")
        for w in a["waterfall"]:
            print(f"  {w['stage']:22s} refused {w['refused_here']:7d} ({w['share_of_physical']*100:6.2f}%)  sc_econ {w['scoreable_economics']}")
        print("  choice set:", a["choice_set"]["n_physical"], "phys /", a["choice_set"]["n_scoreable"], "scoreable",
              a["choice_set"]["scoreable_economics"])
        print("  winners:", a["declined_winners"]["n_scoreable_winners"], a["declined_winners"]["refusing_stage"])
        print("  ny_long_metals(session_bucket):", a["declined_winners"]["ny_long_metals_session_bucket"]["economics"])
        print("  lsr_long:", a["declined_winners"]["liquidity_sweep_reclaim_long"]["economics"])
        print("  cost>1 scoreable:", a["cost_band"]["scoreable"]["n"], "share_of_loss",
              a["cost_band"]["scoreable"]["share_of_pool_net_loss"], "leak:", a["cost_band"]["leakage_into_choice_set"])


if __name__ == "__main__":
    main()
