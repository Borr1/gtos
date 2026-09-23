#!/usr/bin/env python3
"""A2 RECONCILE lane — streaming recomputation over the RAW pools + sidecar + lane tables.

Recomputes register rows C, D(scoreable), E, F, H, I(scoreable), K(pool-absence), L, M, N, P
from the raw compact pools. Never loads a ledger into a DataFrame; line-by-line gzip streaming.
February reads are attribution-only under owner_mandate_20260801.
Writes POOLS_PASS_RESULT.json beside itself.
"""
import gzip, json, os
from collections import Counter, defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
JAN_POOL = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
FEB_POOL = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
SIDECAR  = "/Users/borr/GTOSActive/worktrees/wave18-path-pools-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
JAN_LANE = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl"
FEB_LANE = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl"

RISK_ACTIONS = {"trade", "open-reduced-risk", "reduce-risk"}
MAT = "scheduler_option_materialized"


def fnum(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def stat():
    return {"n": 0, "sum": 0.0, "pos": 0}


def add(s, v):
    s["n"] += 1
    if v is not None:
        s["sum"] += v
        if v > 0:
            s["pos"] += 1


def close(s):
    s["sum"] = round(s["sum"], 4)
    s["mean"] = round(s["sum"] / s["n"], 6) if s["n"] else None
    s["pos_share"] = round(s["pos"] / s["n"], 6) if s["n"] else None
    return s


def pool_pass(path, month):
    n = 0
    union_keys = set()
    first_keys = None
    key_variants = set()
    net_sum = 0.0
    pos = stat()          # H: positive rows
    neg = stat()
    # C: metals LONG session variants (jan primarily; harmless for feb)
    c_var = {k: stat() for k in ("authority_session_ny", "session_bucket_ny", "route_session_ny",
                                 "route_or_bucket_ny", "authority_contains_ny")}
    c_sess_values = {f: Counter() for f in ("authority_session", "session_bucket", "route_session")}
    # D definitions
    dA, dB, dC = stat(), stat(), stat()
    dAB, dAnotB, dBnotA = stat(), stat(), stat()
    dC_vs = Counter()      # membership pattern A/B/C
    d_flags_counter = Counter()
    # E: groups by decision_time
    groups = defaultdict(list)   # decision_time -> [(candidate_id, outcome)]
    # I scoreable
    i_reject_mat = stat()
    i_reject_mat_eff = Counter()
    i_reject_mat_reason = Counter()
    blocker_counter = Counter()
    packet_counter = Counter()
    cost_blocker_sc = 0
    packet_refused_sc = 0
    # H cross-walk over positive rows
    h_cross = Counter()   # (final_blocker_class, selector_reason)
    h_blocker = Counter()
    h_sel_reason = Counter()
    # M endpoints
    m = {t: {"target_1e9": 0, "stop_1e9": 0, "target_1e6": 0, "stop_1e6": 0} for t in ("gross_recon", "gross_native")}
    m_sbs = [0, 0]        # crosscheck heuristic on source_bound_signal_r
    m_raw_t_1e9 = 0
    # N
    ptr_counter = Counter()
    rtr_counter = Counter()
    # P
    id_counter = Counter()
    tuple_counter = Counter()
    # L (feb)
    l_close = Counter()
    l_raw_close = Counter()
    l_diag_close = Counter()
    l_terminal_outcome = Counter()
    l_diag_outcome = Counter()
    l_binary_close_cross = Counter()   # close reason of binary-1e9 rows
    l_target_close_tol = Counter()     # |g-t| bands for target_reached rows
    # K field presence
    k_field_rows = 0

    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            n += 1
            ks = r.keys()
            if first_keys is None:
                first_keys = sorted(ks)
            elif len(ks) != len(first_keys) or sorted(ks) != first_keys:
                key_variants.add(tuple(sorted(ks)))
            union_keys.update(ks)
            if "final_selection_claim" in r:
                k_field_rows += 1

            net = fnum(r.get("opportunity_net_proxy_r"))
            cost = fnum(r.get("cost_r"))
            net_sum += net if net is not None else 0.0
            if net is not None and net > 0:
                add(pos, net)
            elif net is not None:
                add(neg, net)

            sym = r.get("symbol")
            direction = r.get("direction")
            if sym in ("XAUUSD", "XAGUSD") and direction == "LONG":
                as_, sb, rs = r.get("authority_session"), r.get("session_bucket"), r.get("route_session")
                c_sess_values["authority_session"][str(as_)] += 1
                c_sess_values["session_bucket"][str(sb)] += 1
                c_sess_values["route_session"][str(rs)] += 1
                if as_ == "ny":
                    add(c_var["authority_session_ny"], net)
                if sb == "ny":
                    add(c_var["session_bucket_ny"], net)
                if rs == "ny":
                    add(c_var["route_session_ny"], net)
                if rs == "ny" or sb == "ny":
                    add(c_var["route_or_bucket_ny"], net)
                if "ny" in str(as_):
                    add(c_var["authority_contains_ny"], net)

            sa = r.get("selector_action")
            esa = r.get("effective_selector_action")
            mat_ = r.get("scheduler_materialization_status")
            ce = r.get("broker_pretrade_cost_executable")
            inA = bool(ce) and sa in RISK_ACTIONS
            inB = mat_ == MAT
            inC = (esa in RISK_ACTIONS) and inB
            if inA:
                add(dA, net)
            if inB:
                add(dB, net)
            if inC:
                add(dC, net)
            if inA and inB:
                add(dAB, net)
            if inA and not inB:
                add(dAnotB, net)
            if inB and not inA:
                add(dBnotA, net)
            dC_vs[(inA, inB, inC)] += 1

            groups[r.get("decision_time_utc")].append((r.get("candidate_id"), net))

            blocker = r.get("final_blocker_class")
            packet = r.get("pretrade_cost_packet_status")
            blocker_counter[str(blocker)] += 1
            packet_counter[str(packet)] += 1
            if blocker == "cost_authority":
                cost_blocker_sc += 1
            if packet == "REFUSED":
                packet_refused_sc += 1
            if sa == "reject" and inB:
                add(i_reject_mat, net)
                i_reject_mat_eff[str(esa)] += 1
                i_reject_mat_reason[str(r.get("selector_reason"))] += 1

            if net is not None and net > 0:
                h_cross[(str(blocker), str(r.get("selector_reason")))] += 1
                h_blocker[str(blocker)] += 1
                h_sel_reason[str(r.get("selector_reason"))] += 1

            ptr = r.get("policy_target_r")
            rtr = r.get("raw_target_r")
            ptr_counter[repr(ptr)] += 1
            rtr_counter[repr(rtr)] += 1

            tgt = fnum(ptr)
            g_recon = (net + cost) if (net is not None and cost is not None) else None
            g_native = fnum(r.get("opportunity_gross_r"))
            for name, g in (("gross_recon", g_recon), ("gross_native", g_native)):
                if g is None or tgt is None:
                    continue
                if abs(g - tgt) <= 1e-9:
                    m[name]["target_1e9"] += 1
                if abs(g + 1.0) <= 1e-9:
                    m[name]["stop_1e9"] += 1
                if abs(g - tgt) <= 1e-6:
                    m[name]["target_1e6"] += 1
                if abs(g + 1.0) <= 1e-6:
                    m[name]["stop_1e6"] += 1
            if g_recon is not None and fnum(rtr) is not None and abs(g_recon - fnum(rtr)) <= 1e-9:
                m_raw_t_1e9 += 1
            sbs = fnum(r.get("source_bound_signal_r"))
            if sbs is not None:
                if fnum(rtr) is not None and abs(sbs - fnum(rtr)) < 1e-9:
                    m_sbs[0] += 1
                elif abs(sbs + 1.0) < 1e-9:
                    m_sbs[1] += 1

            cid = r.get("candidate_id")
            id_counter[cid] += 1
            tuple_counter[(cid, r.get("decision_time_utc"), sym, r.get("side"))] += 1

            if month == "feb":
                l_close[str(r.get("opportunity_close_reason"))] += 1
                l_raw_close[str(r.get("raw_opportunity_close_reason"))] += 1
                l_diag_close[str(r.get("terminal_r_diagnostic_close_reason"))] += 1
                l_terminal_outcome[str(r.get("terminal_outcome"))] += 1
                l_diag_outcome[str(r.get("terminal_r_diagnostic_outcome"))] += 1
                if g_native is not None and tgt is not None:
                    if abs(g_native - tgt) <= 1e-9 or abs(g_native + 1.0) <= 1e-9:
                        l_binary_close_cross[str(r.get("opportunity_close_reason"))] += 1
                cr = str(r.get("opportunity_close_reason"))
                if "target" in cr and g_native is not None and tgt is not None:
                    d = abs(g_native - tgt)
                    band = "<=1e-9" if d <= 1e-9 else ("<=1e-6" if d <= 1e-6 else ("<=1e-3" if d <= 1e-3 else ">1e-3"))
                    l_target_close_tol[band] += 1

    multi_id_rows = sum(c for c in id_counter.values() if c > 1)
    dup_tuples = sum(c for c in tuple_counter.values() if c > 1)
    res = {
        "rows": n,
        "net_sum": round(net_sum, 4),
        "net_mean": round(net_sum / n, 6),
        "F_first_row_key_count": len(first_keys),
        "F_union_key_count": len(union_keys),
        "F_key_variants_beyond_first": len(key_variants),
        "F_union_keys": sorted(union_keys),
        "H_positive": close(pos),
        "H_negative": close(neg),
        "C_variants": {k: close(v) for k, v in c_var.items()},
        "C_session_value_counts_metalsLONG": {f: dict(c.most_common(8)) for f, c in c_sess_values.items()},
        "D_defA_costexec_and_selector_risk": close(dA),
        "D_defB_materialized": close(dB),
        "D_defC_effective_risk_and_materialized": close(dC),
        "D_A_and_B": close(dAB),
        "D_A_not_B": close(dAnotB),
        "D_B_not_A": close(dBnotA),
        "D_membership_pattern_counts": {str(k): v for k, v in sorted(dC_vs.items())},
        "I_reject_and_materialized": close(i_reject_mat),
        "I_reject_mat_effective_action": dict(i_reject_mat_eff),
        "I_reject_mat_selector_reason": dict(i_reject_mat_reason),
        "I_blocker_counts": dict(blocker_counter.most_common()),
        "I_packet_counts": dict(packet_counter.most_common()),
        "I_scoreable_cost_blocker": cost_blocker_sc,
        "I_scoreable_packet_refused": packet_refused_sc,
        "H_crosswalk_blocker_x_selreason_positives": {f"{b} || {s}": c for (b, s), c in h_cross.most_common()},
        "H_positive_by_blocker": dict(h_blocker.most_common()),
        "M_endpoint_counts": m,
        "M_sbs_heuristic_target_stop": m_sbs,
        "M_gross_recon_vs_raw_target_1e9": m_raw_t_1e9,
        "N_policy_target_r_distinct": len(ptr_counter),
        "N_policy_target_r_top": dict(ptr_counter.most_common(5)),
        "N_raw_target_r_distinct": len(rtr_counter),
        "P_distinct_candidate_ids": len(id_counter),
        "P_rows_in_multi_id_groups": multi_id_rows,
        "P_duplicate_full_tuples": dup_tuples,
        "K_rows_with_final_selection_claim_field": k_field_rows,
    }
    if month == "feb":
        res["L_opportunity_close_reason"] = dict(l_close.most_common())
        res["L_raw_opportunity_close_reason"] = dict(l_raw_close.most_common(12))
        res["L_terminal_r_diagnostic_close_reason"] = dict(l_diag_close.most_common(12))
        res["L_terminal_outcome"] = dict(l_terminal_outcome.most_common(12))
        res["L_terminal_r_diagnostic_outcome"] = dict(l_diag_outcome.most_common(12))
        res["L_binary_1e9_rows_close_reason"] = dict(l_binary_close_cross.most_common(12))
        res["L_target_close_gross_tolerance_bands"] = dict(l_target_close_tol.most_common())
    return res, groups


def lane_join(lane_path, groups):
    trades = []
    with open(lane_path) as f:
        f.readline()
        for line in f:
            t = json.loads(line)
            if t.get("row_kind") == "trade":
                trades.append(t)
    chosen = []
    for t in trades:
        net = fnum(t.get("net_r"))
        rows = groups.get(t.get("decision_time_utc"), [])
        outs = [o for (cid, o) in rows if o is not None and cid != t.get("candidate_id")]
        if net is None or not outs:
            continue
        chosen.append(sum(outs) / len(outs))
    return {
        "n_trades_lane": len(trades),
        "n_matched": len(chosen),
        "mean_set_mean_outcome": round(sum(chosen) / len(chosen), 8) if chosen else None,
    }


def sidecar_pass():
    n = 0
    obs = 0
    maxlen = 0
    minlen = None
    with gzip.open(SIDECAR, "rt") as f:
        for line in f:
            r = json.loads(line)
            n += 1
            o = r.get("ordered_path_observations")
            if isinstance(o, list):
                L = len(o)
                obs += L
                maxlen = max(maxlen, L)
                minlen = L if minlen is None else min(minlen, L)
    return {"rows": n, "total_observations": obs, "max_obs_per_row": maxlen, "min_obs_per_row": minlen}


def main():
    out = {"schema": "gtos.a2_verify.reconcile.pools_pass.v1",
           "note_february": "February read is attribution-only under owner_mandate_20260801."}
    out["G_sidecar"] = sidecar_pass()
    print("sidecar:", out["G_sidecar"])
    jan, jan_groups = pool_pass(JAN_POOL, "jan")
    out["january"] = jan
    out["E_jan_chosen_sets"] = lane_join(JAN_LANE, jan_groups)
    print("jan rows:", jan["rows"], "E:", out["E_jan_chosen_sets"])
    del jan_groups
    feb, feb_groups = pool_pass(FEB_POOL, "feb")
    out["february"] = feb
    out["E_feb_chosen_sets"] = lane_join(FEB_LANE, feb_groups)
    print("feb rows:", feb["rows"], "E:", out["E_feb_chosen_sets"])
    del feb_groups
    jan_keys = set(jan["F_union_keys"])
    feb_keys = set(feb["F_union_keys"])
    out["F_jan_minus_feb"] = sorted(jan_keys - feb_keys)
    out["F_feb_minus_jan_count"] = len(feb_keys - jan_keys)
    out["F_feb_contains_all_jan"] = jan_keys <= feb_keys
    with open(os.path.join(OUT, "POOLS_PASS_RESULT.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print("written")


if __name__ == "__main__":
    main()
