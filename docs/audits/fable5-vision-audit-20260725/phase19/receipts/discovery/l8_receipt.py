#!/usr/bin/env python3
"""l8_receipt — emit the full l8 receipt tables (markdown) from the saved measurement JSONs."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(os.path.join(HERE, f)))
out = []
P = out.append

T = L("L8_TABLES_V1.json")
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]

P("## A. FULL SINGLE-AXIS TABLES — pool metric `gross_r`, CLEAN population (born_past_stop dropped)\n")
P("Pool clean: n=%d mean=%+.5f win=%.4f. Pool raw: n=%d mean=%+.5f win=%.4f. Pool honest 2R/-1R: mean=%+.5f\n"
  % (T["pool"]["clean"]["n"], T["pool"]["clean"]["mean"], T["pool"]["clean"]["win"],
     T["pool"]["raw"]["n"], T["pool"]["raw"]["mean"], T["pool"]["raw"]["win"], T["pool"]["honest"]["mean"]))
for ax in ["hour", "hour_b", "dow", "day", "week", "third", "family", "symbol", "side",
           "route_session", "session", "msc", "risk_pct", "born", "rdp_b", "spread_b",
           "cost_b", "prob_b", "ev_b", "fillp_b", "fill_class", "dup_b", "first_em",
           "order_type", "sched", "lifecycle", "blocker", "adm_risk_class", "sel_action",
           "limit_mkt", "ptr_b", "risk_rank_b", "which_first", "sched_disp", "adm_count",
           "miss_reason"]:
    P("\n### axis `%s`\n" % ax)
    P("| value | n_clean | win | mean | t | payoff | be_win | edge_vs_be | meanWin | meanLoss | honest_clean | n_raw | raw_mean | pastStop% | J1 | J2 | J3 |")
    P("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for c in T["tables"][ax]:
        th = [c["thirds"][t] for t in THIRDS]
        P("| %s | %d | %.4f | %+.5f | %+.2f | %s | %s | %s | %s | %s | %s | %d | %+.5f | %.1f | %s | %s | %s |" % (
            c["value"], c["n"], c["win"] or 0, c["mean"] or 0, c["t"] or 0,
            ("%.3f" % c["payoff"]) if c["payoff"] is not None else "-",
            ("%.4f" % c["be_win"]) if c["be_win"] is not None else "-",
            ("%+.4f" % c["edge_vs_be"]) if c["edge_vs_be"] is not None else "-",
            ("%+.4f" % c["mean_win"]) if c["mean_win"] is not None else "-",
            ("%+.4f" % c["mean_loss"]) if c["mean_loss"] is not None else "-",
            ("%+.5f" % c["honest_clean_mean"]) if c["honest_clean_mean"] is not None else "-",
            c["n_raw"], c["raw_mean"], 100 * c["past_stop_share"],
            *[("%+.4f(n=%d)" % (v[2], v[0])) if v else "-" for v in th]))

D = L("L8_DECILES_V1.json")
P("\n\n## B. DECILE TABLES — every continuous decision-time field, CLEAN population, metric `gross_r`\n")
for f, rows_ in D["fields"].items():
    P("\n### `%s`\n" % f)
    P("| bin | lo | hi | n | win | mean | t | payoff | edge_vs_be | honest | pos_thirds |")
    P("|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for c in rows_:
        P("| %d | %s | %s | %d | %.4f | %+.5f | %+.2f | %.3f | %+.4f | %+.5f | %d/3 |" % (
            c["bin"], c["lo"], c["hi"], c["n"], c["win"], c["mean"], c["t"], c["payoff"],
            c["edge_vs_be"], c["honest_mean"], c["pos_thirds"]))

R = L("L8_RESWIN_V1.json")
P("\n\n## C. RESOLUTION WIN RATE — honest first-touch 2R/-1R, entry must trade first\n")
P("CLEAN pool: n=%d resWin=%.4f mean=%+.5f | target %d | stop %d | mark %d | no_fill %d\n"
  % (R["pool_clean"]["n"], R["pool_clean"]["res_win"], R["pool_clean"]["mean"],
     R["pool_clean"]["tgt"], R["pool_clean"]["stop"], R["pool_clean"]["mark"], R["pool_clean"]["nofill"]))
P("RAW pool (incl. born_past_stop): n=%d resWin=%.4f mean=%+.5f\n"
  % (R["pool_all"]["n"], R["pool_all"]["res_win"], R["pool_all"]["mean"]))
for ax, tab in R["tables"].items():
    P("\n### `%s` (breakeven resolution win rate at 2R/-1R = 0.3333)\n" % ax)
    P("| value | n | resWin | targetRate | stopRate | markRate | noFillRate | honestMean | grossMean | J1 resWin | J2 | J3 |")
    P("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for c in tab:
        th = [c["thirds"][t] for t in THIRDS]
        P("| %s | %d | %s | %.4f | %.4f | %.4f | %.4f | %+.5f | %+.5f | %s | %s | %s |" % (
            c["value"], c["n"], ("%.4f" % c["res_win"]) if c["res_win"] is not None else "-",
            c["target_rate"], c["stop_rate"], c["mark_rate"], c["nofill_rate"],
            c["mean"], c["gross_mean"],
            *[("%.4f" % v[1]) if v and v[1] is not None else "-" for v in th]))

DE = L("L8_DEPTH_V1.json")
P("\n\n## D. LIMIT DEPTH AT THE DECISION INSTANT (`mkt_r`, R units, zero look-ahead)\n")
P("| depth bucket | n | resWin | targetRate | stopRate | markRate | honestMean | grossMean | medRDP% | medSpreadR | medCostR | J1 resWin | J2 | J3 |")
P("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
for a in DE["depth"]:
    th = [a["thirds"][t] for t in THIRDS]
    P("| %s | %d | %s | %.4f | %.4f | %.4f | %+.5f | %+.5f | %s | %s | %s | %s | %s | %s |" % (
        a["depth"], a["n"], ("%.4f" % a["res_win"]) if a["res_win"] is not None else "-",
        a["target_rate"], a["stop_rate"], a["mark_rate"], a["mean"], a["gross_mean"],
        a["median_rdp"], a["median_spread_r"], a["median_cost_r"],
        *[("%.4f" % v[1]) if v and v[1] is not None else "-" for v in th]))

F = L("L8_FILLSPEED_V1.json")
P("\n\n## E. FILL SPEED x LIMIT DEPTH, and the risk-distance control\n")
P("\n### E.1 fill speed x depth (CLEAN)\n")
P("| depth | fillspeed | n | resWin | honestMean | grossMean | targetRate | stopRate | markRate | medRDP% |")
P("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|")
for k, a in F["cross"].items():
    dep, fs = k.split("|")
    P("| %s | %s | %d | %s | %+.5f | %+.5f | %.4f | %.4f | %.4f | %s |" % (
        dep, fs, a["n"], ("%.4f" % a["res_win"]) if a["res_win"] is not None else "-",
        a["mean"], a["gross_mean"], a["target_rate"], a["stop_rate"], a["mark_rate"], a["median_rdp"]))
P("\n### E.2 at-market vs resting WITHIN risk-distance quintile (CLEAN)\n")
P("| rdp quintile | kind | n | resWin | honestMean | grossMean |")
P("|---|---|--:|--:|--:|--:|")
for k, a in F["rdp_control"].items():
    q, kind = k.split("|")
    P("| %s | %s | %d | %s | %+.5f | %+.5f |" % (q, kind, a["n"],
      ("%.4f" % a["res_win"]) if a["res_win"] is not None else "-", a["mean"], a["gross_mean"]))

DL = L("L8_DELAY_V1.json")
P("\n\n## F. THE ENTRY-DELAY POLICY, priced\n")
P("Refuse any candidate whose entry level is first touched within the first k M1 bars after the decision.")
P("Refused and never-filled candidates book 0.0 R. CLEAN population n=%d.\n" % DL["n"])
P("| k (bars) | n traded | traded share | R / opportunity | R / trade | resWin | t | target | stop | mark | refused | no_fill | total R |")
P("|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
for b in DL["delay_sweep"]:
    P("| %d | %d | %.4f | %+.5f | %s | %s | %+.2f | %d | %d | %d | %d | %d | %+.1f |" % (
        b["k"], b["n_traded"], b["traded_share"], b["mean_per_opportunity"],
        ("%+.5f" % b["mean_per_trade"]) if b["mean_per_trade"] is not None else "-",
        ("%.4f" % b["res_win"]) if b["res_win"] is not None else "-",
        b["t_per_opportunity"], b["target"], b["stop"], b["mark"], b["refused"], b["no_fill"], b["total_R"]))
P("\nRAW pool (incl. born_past_stop): " + " ; ".join(
    "k=%d R/opportunity %+.5f (traded %d)" % (b["k"], b["mean_per_opportunity"], b["n_traded"])
    for b in DL["delay_sweep_all"]))
P("\n### F.1 stability across January thirds\n")
P("| third | n | k=0 R/opp | k=1 R/opp | k=5 R/opp | k=1 traded | k=1 resWin |")
P("|---|--:|--:|--:|--:|--:|--:|")
for t, d in DL["thirds"].items():
    P("| %s | %d | %+.5f | %+.5f | %+.5f | %d | %s |" % (
        t, d["k0"]["n_opportunities"], d["k0"]["mean_per_opportunity"],
        d["k1"]["mean_per_opportunity"], d["k5"]["mean_per_opportunity"],
        d["k1"]["n_traded"], ("%.4f" % d["k1"]["res_win"]) if d["k1"]["res_win"] else "-"))
sb = DL["same_bar_tie"]
P("\n### F.2 same-bar tie-rule robustness\n")
P("bar-1 fills n=%d | stop touched on the fill bar %d (%.2f%%) | target on fill bar %d | both %d" % (
    sb["n_bar1_fills"], sb["stop_touched_on_fill_bar"],
    100 * sb["stop_touched_on_fill_bar"] / sb["n_bar1_fills"],
    sb["target_touched_on_fill_bar"], sb["both_on_fill_bar"]))
P("actual mean %+.5f | optimistic bound (fill bar exempt from the stop) %+.5f -> the penalty is NOT the tie rule\n"
  % (sb["actual_mean"], sb["mean_if_fill_bar_exempt_from_stop"]))
P("\n### F.3 per family, R/opportunity\n")
P("| family | n | k=0 | k=1 | k=5 | k5-k0 |")
P("|---|--:|--:|--:|--:|--:|")
for v, d in sorted(DL["by_family"].items(), key=lambda kv: -(kv[1]["k5"]["mean_per_opportunity"] - kv[1]["k0"]["mean_per_opportunity"])):
    P("| %s | %d | %+.5f | %+.5f | %+.5f | %+.5f |" % (
        v, d["k0"]["n_opportunities"], d["k0"]["mean_per_opportunity"],
        d["k1"]["mean_per_opportunity"], d["k5"]["mean_per_opportunity"],
        d["k5"]["mean_per_opportunity"] - d["k0"]["mean_per_opportunity"]))
for ax in ("hour_b", "symbol", "depth"):
    key = "by_" + ax
    if key not in DL:
        continue
    P("\n### F.4 per %s, R/opportunity\n" % ax)
    P("| %s | n | k=0 | k=1 | k=5 | k5-k0 |" % ax)
    P("|---|--:|--:|--:|--:|--:|")
    for v, d in sorted(DL[key].items(), key=lambda kv: -(kv[1]["k5"]["mean_per_opportunity"] - kv[1]["k0"]["mean_per_opportunity"])):
        P("| %s | %d | %+.5f | %+.5f | %+.5f | %+.5f |" % (
            v, d["k0"]["n_opportunities"], d["k0"]["mean_per_opportunity"],
            d["k1"]["mean_per_opportunity"], d["k5"]["mean_per_opportunity"],
            d["k5"]["mean_per_opportunity"] - d["k0"]["mean_per_opportunity"]))

H = L("L8_HORIZONMATCH_V1.json")
P("\n\n## G. EQUAL-EXPOSURE CONTROL — is the bar-1 penalty adverse selection or horizon?\n")
P("Resolve every cohort inside a fixed H-bar window measured from its OWN fill bar; drop any")
P("candidate whose window does not fit before the 2-hour wall. Equal exposure, equal wall distance.\n")
P("| H bars | fillspeed | eligible | excluded | target | stop | unresolved | resWin | mean (unresolved=0) |")
P("|--:|---|--:|--:|--:|--:|--:|--:|--:|")
for Hb, tab in H["H"].items():
    for fs, a in tab.items():
        P("| %s | %s | %d | %d | %d | %d | %d | %.4f | %+.5f |" % (
            Hb, fs, a["n_eligible"], a["excluded_no_window"], a["target"], a["stop"],
            a["unresolved"], a["res_win"] or 0, a["mean_treating_unresolved_as_0"]))
P("\n### G.1 binary bar1 vs later, equal exposure\n")
P("| H bars | cohort | eligible | target | stop | resWin | mean |")
P("|--:|---|--:|--:|--:|--:|--:|")
for Hb, tab in H["binary"].items():
    for name, a in tab.items():
        P("| %s | %s | %d | %d | %d | %.4f | %+.5f |" % (
            Hb, name, a["n_eligible"], a["target"], a["stop"], a["res_win"] or 0,
            a["mean_treating_unresolved_as_0"]))

GV = L("L8_GATEVALUE_V1.json")
P("\n\n## H. DO THE SHIPPED COST GATES SELECT OR SUPPRESS?\n")
P("Measured on the delayed-fill clean population, honest 2R/-1R.\n")
P("| split | n | mean | resWin | t | total R | grossMean |")
P("|---|--:|--:|--:|--:|--:|--:|")
for k, a in GV["gate_limbs"].items():
    P("| %s | %d | %+.5f | %s | %+.2f | %+.1f | %+.5f |" % (
        k, a["n"], a["mean"], ("%.4f" % a["res_win"]) if a["res_win"] else "-", a["t"], a["total_R"], a["gross_mean"]))
P("\n### H.1 the same gates at the measured 7.3x / 8.5x spread overcharge\n")
P("| split | n | mean | resWin | total R |")
P("|---|--:|--:|--:|--:|")
for k, a in GV["overcharge"].items():
    P("| %s | %d | %+.5f | %s | %+.1f |" % (k, a["n"], a["mean"],
      ("%.4f" % a["res_win"]) if a["res_win"] else "-", a["total_R"]))

FI = L("L8_FINAL_V1.json")
P("\n\n## I. THE STACKED POLICY, priced per CANDIDATE-OPPORTUNITY over all 27,658 pool rows\n")
P("| step | n traded | R/trade | resWin | R/opportunity | total R | target | stop | mark |")
P("|---|--:|--:|--:|--:|--:|--:|--:|--:|")
for a in FI["stack"]:
    P("| %s | %d | %+.5f | %s | %+.5f | %+.1f | %d | %d | %d |" % (
        a["step"], a["n"], a["mean"], ("%.4f" % a["res_win"]) if a["res_win"] else "-",
        a["mean_per_opportunity_over_full_pool"], a["total_R"], a["target"], a["stop"], a["mark"]))
P("\n## J. FULL TABLES ON THE DELAYED-FILL CLEAN POPULATION (honest 2R/-1R)\n")
P("Base: n=%d mean=%+.5f resWin=%.4f win=%.4f\n" % (
    FI["base_delayed"]["n"], FI["base_delayed"]["mean"], FI["base_delayed"]["res_win"], FI["base_delayed"]["win"]))
for ax, tab in FI["tables"].items():
    P("\n### `%s`\n" % ax)
    P("| value | n | mean | resWin | t | win | target | stop | mark | grossMean | totalR | pos_thirds | J1 | J2 | J3 |")
    P("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for c in tab:
        th = [c["thirds"][t] for t in THIRDS]
        P("| %s | %d | %+.5f | %s | %+.2f | %.4f | %d | %d | %d | %+.5f | %+.1f | %d/3 | %s | %s | %s |" % (
            c["value"], c["n"], c["mean"], ("%.4f" % c["res_win"]) if c["res_win"] else "-",
            c["t"], c["win"], c["target"], c["stop"], c["mark"], c["gross_mean"], c["total_R"],
            c["pos_thirds"], *[("%+.4f(n=%d)" % (v[1], v[0])) if v else "-" for v in th]))

open(os.path.join(HERE, "l8_TABLES_APPENDIX.md"), "w").write("\n".join(out))
print("wrote l8_TABLES_APPENDIX.md lines=%d bytes=%d" % (len(out), sum(len(x) for x in out)))
