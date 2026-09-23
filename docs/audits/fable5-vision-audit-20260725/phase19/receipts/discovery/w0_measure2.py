#!/usr/bin/env python3
"""w0-dictionary addendum — repeat structure, gate identities, calibration, fill tags,
asset inventory. Emits w0_MEASURE_V2.json. Every number in w0_DATA_DICTIONARY.md that is
not in w0_MEASURE_V1.json comes from here."""
from __future__ import annotations
import collections, gzip, json, os, sys
from datetime import datetime, timezone

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
OUT = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
POOL = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz")


def rows(p):
    with gzip.open(p, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main():
    R = {"schema": "gtos.wave19.w0.measure.v2", "generated_utc": datetime.now(timezone.utc).isoformat()}
    rs = list(rows(POOL)); n = len(rs)

    # ---- repeat / independence structure -----------------------------------------
    g = collections.defaultdict(list)
    for r in rs: g[r["candidate_id"]].append(r)
    fam = collections.defaultdict(lambda: [0, 0])
    for c, v in g.items():
        fam[v[0]["origin_family"]][0] += 1; fam[v[0]["origin_family"]][1] += len(v)
    firsts = [sorted(v, key=lambda r: r["decision_time_utc"])[0] for v in g.values()]
    R["independence"] = {
        "rows": n, "unique_candidate_id": len(g),
        "unique_join_key_candidate_id_plus_decision_time": len({(r["candidate_id"], r["decision_time_utc"]) for r in rs}),
        "repeat_offer_rows": n - len(g), "repeat_offer_share": (n - len(g)) / n,
        "max_offers_for_one_candidate_id": max(len(v) for v in g.values()),
        "candidate_ids_offered_more_than_once": sum(1 for v in g.values() if len(v) > 1),
        "offer_count_histogram": dict(collections.Counter(len(v) for v in g.values()).most_common(12)),
        "per_family": {k: {"unique_candidate_id": u, "rows": rr, "reoffer_multiplier": rr / u}
                       for k, (u, rr) in sorted(fam.items(), key=lambda kv: -kv[1][1])},
        "mean_net_proxy_r_all_rows": sum(r["opportunity_net_proxy_r"] for r in rs) / n,
        "mean_net_proxy_r_first_offer_only": sum(r["opportunity_net_proxy_r"] for r in firsts) / len(firsts),
    }

    # ---- gate identities ---------------------------------------------------------
    def S(f): return {i for i, r in enumerate(rs) if f(r)}
    ca = S(lambda r: r["final_blocker_class"] == "cost_authority")
    R["gate_identity"] = {
        "n_cost_authority": len(ca),
        "identical_to_pretrade_cost_packet_status_REFUSED": ca == S(lambda r: r["pretrade_cost_packet_status"] == "REFUSED"),
        "identical_to_broker_pretrade_cost_executable_false": ca == S(lambda r: r["broker_pretrade_cost_executable"] is False),
        "identical_to_risk_finalizer_broker_cost_blocked": ca == S(lambda r: r["risk_finalizer_reason"] == "broker_cost_authority_blocked_non_executable"),
        "rows_cost_r_gt_0_15": len(S(lambda r: r["cost_r"] > 0.15)),
        "rows_cost_r_gt_0_15_and_refused": len(S(lambda r: r["cost_r"] > 0.15) & S(lambda r: r["pretrade_cost_packet_status"] == "REFUSED")),
        "rows_cost_r_le_0_15_but_refused": len(S(lambda r: r["cost_r"] <= 0.15) & S(lambda r: r["pretrade_cost_packet_status"] == "REFUSED")),
        "rows_spread_r_gt_0_10": len(S(lambda r: r["spread_r"] > 0.10)),
        "config_max_total_cost_r": 0.15, "config_max_spread_r": 0.10,
        "config_cite": "config/agent_config.yaml:715-716",
        "cost_authority_split_by_selector_reason": dict(collections.Counter(
            r["selector_reason"] for r in rs if r["final_blocker_class"] == "cost_authority").most_common()),
    }

    # ---- belief calibration ------------------------------------------------------
    def deciles(pred_key, real_fn, B=10):
        pairs = sorted((r[pred_key], real_fn(r)) for r in rs)
        out = []
        for i in range(B):
            s = pairs[i * n // B:(i + 1) * n // B]
            out.append({"decile": i + 1, "n": len(s),
                        "pred_mean": sum(a for a, _ in s) / len(s),
                        "realized_mean": sum(b for _, b in s) / len(s),
                        "realized_win_rate": sum(1 for _, b in s if b > 0) / len(s)})
        return out
    gross = lambda r: r["opportunity_net_proxy_r"] + r["expected_cost_r"]
    R["calibration"] = {
        "candidate_probability_vs_gross": deciles("candidate_probability", gross),
        "expected_net_r_vs_net_proxy": deciles("expected_net_r", lambda r: r["opportunity_net_proxy_r"]),
        "mean_candidate_probability": sum(r["candidate_probability"] for r in rs) / n,
        "realized_gross_win_rate": sum(1 for r in rs if gross(r) > 0) / n,
        "mean_candidate_ev_r": sum(r["candidate_ev_r"] for r in rs) / n,
        "mean_realized_gross_r": sum(gross(r) for r in rs) / n,
        "share_candidate_ev_r_positive": sum(1 for r in rs if r["candidate_ev_r"] > 0) / n,
        "share_candidate_probability_ge_half": sum(1 for r in rs if r["candidate_probability"] >= 0.5) / n,
        "share_expected_net_r_positive": sum(1 for r in rs if r["expected_net_r"] > 0) / n,
    }

    # ---- fill-field constants ----------------------------------------------------
    R["fill_fields"] = {
        "execution_fill_probability_eq_0_92": sum(1 for r in rs if r["execution_fill_probability"] == 0.92),
        "execution_fill_probability_null": sum(1 for r in rs if r["execution_fill_probability"] is None),
        "execution_fill_probability_distinct": len({r["execution_fill_probability"] for r in rs}),
        "execution_eq_limit_fillability_rows": sum(1 for r in rs if r["execution_fill_probability"] == r["limit_fillability_probability"]),
        "fill_probability_eq_entry_quality_rows": sum(1 for r in rs if r["fill_probability"] == r["entry_quality_fill_probability"]),
        "fill_probability_at_0_95_clamp": sum(1 for r in rs if r["fill_probability"] == 0.95),
        "limit_marketable_at_decision": dict(collections.Counter(str(r["limit_marketable_at_decision"]) for r in rs)),
        "cross_0_92_by_class": {("%s|%s|%s" % ("0.92" if r["execution_fill_probability"] == 0.92 else "not0.92",
                                               r["fill_realism_class"], r["limit_marketable_at_decision"])): 0
                                for r in rs},
    }
    cx = collections.Counter(("0.92" if r["execution_fill_probability"] == 0.92 else
                              ("null" if r["execution_fill_probability"] is None else "other"),
                              r["fill_realism_class"], str(r["limit_marketable_at_decision"])) for r in rs)
    R["fill_fields"]["cross_0_92_by_class"] = {"|".join(k): v for k, v in cx.most_common()}

    # ---- spread_r degeneracies ---------------------------------------------------
    R["spread_degeneracy"] = {
        "rows_spread_r_eq_1e-4_exactly": sum(1 for r in rs if abs(r["spread_r"] - 1e-4) < 1e-9),
        "symbols_at_1e-4": dict(collections.Counter(r["symbol"] for r in rs if abs(r["spread_r"] - 1e-4) < 1e-9)),
        "rows_spread_r_eq_0": sum(1 for r in rs if r["spread_r"] == 0.0),
        "symbols_at_zero": dict(collections.Counter(r["symbol"] for r in rs if r["spread_r"] == 0.0).most_common(8)),
    }

    # ---- geometry degeneracies ---------------------------------------------------
    R["geometry"] = {
        "policy_target_r_eq_2_exactly": sum(1 for r in rs if r["policy_target_r"] == 2.0),
        "policy_target_r_gt_3": sum(1 for r in rs if r["policy_target_r"] > 3),
        "policy_target_r_max": max(r["policy_target_r"] for r in rs),
        "policy_ne_raw_target_rows": sum(1 for r in rs if r["policy_target_r"] != r["raw_target_r"]),
        "risk_per_trade_pct": dict(collections.Counter(r["risk_per_trade_pct"] for r in rs).most_common()),
        "dynamic_geometry_policy": dict(collections.Counter(r["dynamic_geometry_policy"] for r in rs)),
    }

    # ---- asset inventory ---------------------------------------------------------
    def stat(p, count=True):
        ap = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if not os.path.exists(ap): return {"path": p, "exists": False}
        e = {"path": p, "exists": True, "bytes": os.path.getsize(ap) if os.path.isfile(ap) else None}
        if count and ap.endswith((".jsonl", ".jsonl.gz")):
            op = gzip.open if ap.endswith(".gz") else open
            k = 0; days = set(); flds = None
            with op(ap, "rt") as f:
                for line in f:
                    if not line.strip(): continue
                    k += 1
                    r = json.loads(line)
                    if flds is None: flds = len(r)
                    d = r.get("decision_time_utc") or r.get("trading_day") or r.get("day")
                    if d: days.add(str(d)[:10])
            e.update(rows=k, fields=flds, window=[min(days), max(days)] if days else None)
        return e
    inv = {}
    for key, p in {
        "POOL_JAN_TRUE_UTC": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
        "POOL_FEB_TRUE_UTC": "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz",
        "PATHS_JAN": "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",
        "BREAKER_TRADES": "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz",
        "POOL_JAN_CD_S0R0": "docs/audits/fable5-vision-audit-20260725/phase14/receipts/pools/CD_REPAIRED_POOL_S0R0_V1.jsonl.gz",
        "POOL_JAN_CD_S0R1": "docs/audits/fable5-vision-audit-20260725/phase14/receipts/pools/CD_REPAIRED_POOL_S0R1_V1.jsonl.gz",
        "POOL_JAN_CD_S1R0": "docs/audits/fable5-vision-audit-20260725/phase14/receipts/pools/CD_REPAIRED_POOL_S1R0_V1.jsonl.gz",
        "POOL_JAN_CD_S1R1": "docs/audits/fable5-vision-audit-20260725/phase14/receipts/pools/CD_REPAIRED_POOL_S1R1_V1.jsonl.gz",
        "WALK_2D_CANDIDATES": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/walk/WALK_2D_CANDIDATES.jsonl.gz",
        "LANE_TRADES_JAN_CJ": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl",
        "LANE_TRADES_FEB_CP": "docs/audits/fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl",
    }.items():
        inv[key] = stat(p)
    for key, p in {
        "T1_SCREENS": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t1/T1_SCREENS_V1.json",
        "T2_ARM_I": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t2/T2_ARM_I_ANALYSIS.json",
        "T2_ARM_II": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t2/T2_ARM_II_ANALYSIS.json",
        "T2_ARM_III": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t2/T2_ARM_III_ANALYSIS.json",
        "T2_ARM_IV": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t2/T2_ARM_IV_ANALYSIS.json",
        "T2_ARM_V": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t2/T2_ARM_V_ANALYSIS.json",
        "T3_SWAP_ISO": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t2/T3_SWAP_ISO_ANALYSIS.json",
        "MARCH_POOL_CENSUS": "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725/phase19/receipts/march/analysis/MARCH_POOL_CENSUS.json",
        "MARCH_ENDPOINT_SCORES": "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725/phase19/receipts/march/MARCH_ENDPOINT_SCORES_V1.json",
        "PACKS_JAN": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_PACKS_JANUARY_V3.json",
        "PACKS_FEB": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_PACKS_FEBRUARY_V2.json",
        "PACKS_APR": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_PACKS_APRIL_V2.json",
        "PACKS_MAY": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_PACKS_MAY_V1.json",
    }.items():
        inv[key] = stat(p, count=False)
    HOLD = "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/packs"
    inv["LANE_PACK_ROOT"] = {"path": HOLD, "exists": os.path.isdir(HOLD),
                             "pack_roots": sorted(os.listdir(HOLD)) if os.path.isdir(HOLD) else []}
    R["asset_inventory"] = inv

    json.dump(R, open(os.path.join(OUT, "w0_MEASURE_V2.json"), "w"), indent=1, default=str)
    print("wrote w0_MEASURE_V2.json")
    print(json.dumps({k: R[k] for k in ("independence", "gate_identity")}, indent=1, default=str)[:1800])


if __name__ == "__main__":
    main()
