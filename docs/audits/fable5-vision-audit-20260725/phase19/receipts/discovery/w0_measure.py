#!/usr/bin/env python3
"""w0-dictionary — measurement backing every number in w0_DATA_DICTIONARY.md.

Emits w0_MEASURE_V1.json. Run from the wave19-broad-forensic-20260801 worktree root.
Nothing in the .md is asserted that is not produced here.
"""
from __future__ import annotations
import collections, gzip, json, math, os, statistics, sys
from datetime import datetime, timezone

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
P16 = "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
P18 = "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools"
POOL = os.path.join(ROOT, P16, "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz")
FEB  = os.path.join(ROOT, P18, "CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz")
PATHS= os.path.join(ROOT, P18, "CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz")
BRK  = os.path.join(ROOT, P18, "CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz")

from src.research_infra import b7_5_diagnostic_pool as DP


def rows(p):
    with gzip.open(p, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def q(a, p):
    return a[min(len(a) - 1, int(p * len(a)))] if a else None


def profile(rs):
    n = len(rs)
    out = {}
    for k in rs[0].keys():
        vals = [r.get(k) for r in rs]
        nn = [v for v in vals if v is not None]
        e = {"null_rate": round(1 - len(nn) / n, 6),
             "dtype": "/".join(sorted({type(v).__name__ for v in nn})) or "allnull",
             "cardinality": len(set(map(repr, nn)))}
        if nn and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nn):
            s = sorted(float(v) for v in nn)
            e.update(min=s[0], max=s[-1], mean=sum(s) / len(s), p50=q(s, .5),
                     p05=q(s, .05), p95=q(s, .95), constant=(s[0] == s[-1]))
        e["top"] = [[str(a), b] for a, b in collections.Counter(
            (v if isinstance(v, str) else json.dumps(v)) for v in nn).most_common(8)]
        out[k] = e
    return out


def main():
    R = {"schema": "gtos.wave19.w0.measure.v1", "generated_utc": datetime.now(timezone.utc).isoformat()}

    # ---------------- 1. pool profile ----------------
    jan = list(rows(POOL))
    R["jan"] = {"n": len(jan), "fields": len(jan[0]), "profile": profile(jan)}
    R["jan"]["constants"] = sorted(k for k, e in R["jan"]["profile"].items()
                                   if e["cardinality"] == 1 and e["null_rate"] == 0.0)
    R["jan"]["all_null"] = sorted(k for k, e in R["jan"]["profile"].items() if e["null_rate"] == 1.0)
    R["jan"]["days"] = sorted({r["decision_time_utc"][:10] for r in jan})

    # declared source mapping
    fmap = {f.name: {"ledger_source": f.source, "family": f.family, "kind": f.kind, "note": f.note}
            for f in DP.PROJECTION + DP.DERIVED + DP.OUTCOME_PROJECTION}
    R["field_source_map"] = fmap
    nond = [f.name for f in DP.FEATURE_FIELDS if not f.source.startswith("derived:")]
    R["jan"]["from_FEATURE_FIELDS"] = [k for k in jan[0] if k in nond]
    R["jan"]["from_EXTRA_COLUMNS_only"] = [k for k in jan[0] if k not in nond]

    # ---------------- 2. cost identity + contamination ----------------
    ident = {"cost_eq_components": 0, "cost_eq_expected": 0, "n": 0, "maxdev": 0.0}
    comp_sum = collections.defaultdict(float)
    for r in jan:
        ident["n"] += 1
        s = (r["spread_r"] or 0) + (r["expected_slippage_r"] or 0) + (r["swap_cost_r"] or 0) + (r["commission_r"] or 0)
        d = abs(s - (r["cost_r"] or 0))
        ident["maxdev"] = max(ident["maxdev"], d)
        if d < 1e-6: ident["cost_eq_components"] += 1
        if abs((r["cost_r"] or 0) - (r["expected_cost_r"] or 0)) < 1e-12: ident["cost_eq_expected"] += 1
        for c in ("spread_r", "expected_slippage_r", "swap_cost_r", "commission_r"):
            comp_sum[c] += (r[c] or 0)
    ident["component_mean_r"] = {k: v / len(jan) for k, v in comp_sum.items()}
    tot = sum(comp_sum.values())
    ident["component_share_of_cost"] = {k: v / tot for k, v in comp_sum.items()}
    R["cost_identity"] = ident

    # net proxy identity: opportunity_net_proxy_r = gross - expected_cost_r  (gross absent in Jan)
    # so recover implied gross and check it against the band table
    gross = [r["opportunity_net_proxy_r"] + r["expected_cost_r"] for r in jan
             if r["opportunity_net_proxy_r"] is not None and r["expected_cost_r"] is not None]
    gs = sorted(gross)
    R["implied_gross"] = {"n": len(gross), "mean": sum(gross) / len(gross), "min": gs[0], "max": gs[-1],
                          "p01": q(gs, .01), "p50": q(gs, .5), "p99": q(gs, .99),
                          "frac_le_neg1": sum(1 for g in gross if g <= -0.999) / len(gross),
                          "frac_ge_2": sum(1 for g in gross if g >= 1.999) / len(gross),
                          "formula": "v4_timewarp_simulated_live_research_loop.py:92577-92581"}

    # ---------------- 3. truthed-spread overcharge ----------------
    over = {}
    try:
        from src.costs.spread_model import spread_price, SpreadModelError
        by_sym = collections.defaultdict(lambda: {"n": 0, "frozen": 0.0, "true": 0.0, "err": 0})
        for r in jan:
            sym = r["symbol"]
            ent, sl = r.get("entry_price"), r.get("stop_loss")
            if not ent or not sl or ent == sl: continue
            dist = abs(ent - sl)
            try:
                est = spread_price(sym, "FTMO", datetime.fromisoformat(r["decision_time_utc"]), band="mid")
                tr = est.spread_price / dist
            except Exception:
                by_sym[sym]["err"] += 1; continue
            b = by_sym[sym]; b["n"] += 1; b["frozen"] += (r["spread_r"] or 0.0); b["true"] += tr
        tot_f = tot_t = tot_n = 0
        for s, b in by_sym.items():
            if b["n"]:
                over[s] = {"n": b["n"], "frozen_mean_spread_r": b["frozen"] / b["n"],
                           "truthed_mean_spread_r": b["true"] / b["n"],
                           "overcharge_x": (b["frozen"] / b["true"]) if b["true"] else None,
                           "unpriced_rows": b["err"]}
                tot_f += b["frozen"]; tot_t += b["true"]; tot_n += b["n"]
        over["__POOL__"] = {"n": tot_n, "frozen_mean_spread_r": tot_f / tot_n,
                            "truthed_mean_spread_r": tot_t / tot_n, "overcharge_x": tot_f / tot_t}
    except Exception as exc:  # pragma: no cover
        over = {"error": repr(exc)}
    R["spread_overcharge"] = over

    # ---------------- 4. blocker / stage census ----------------
    def census(key, weight=None):
        c = collections.Counter()
        agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
        for r in jan:
            v = r.get(key)
            v = v if v is None else str(v)
            c[v] += 1
            a = agg[v]; a[0] += 1
            a[1] += (r.get("opportunity_net_proxy_r") or 0.0)
            a[2] += (r.get("cost_r") or 0.0)
        return {k: {"n": v[0], "share": v[0] / len(jan), "mean_net_proxy_r": v[1] / v[0],
                    "mean_cost_r": v[2] / v[0]} for k, v in
                sorted(agg.items(), key=lambda kv: -kv[1][0])}
    R["census"] = {k: census(k) for k in (
        "final_blocker_class", "selector_action", "effective_selector_action", "selector_reason",
        "effective_selector_reason", "admission_risk_class", "scheduler_materialization_status",
        "scheduler_selection_disposition", "risk_finalizer_reason", "miss_reason",
        "candidate_lifecycle_action", "effective_order_type", "fill_realism_class",
        "pretrade_cost_packet_status", "broker_pretrade_cost_executable",
        "entry_fill_executable", "fill_realism_executable", "limit_marketable_at_decision",
        "confidence_default_applied", "missed_opportunity_r_scoreability_status",
        "same_symbol_lifecycle_action", "origin_family", "utc_hour_bucket",
        "decision_timeframe", "market_timeframe", "session_bucket", "route_session")}

    # ---------------- 5. paths sidecar ----------------
    nb, hz, fg, tick_dicts = [], [], [], 0
    keyset = set(); tick_keys = collections.Counter()
    srcsha = collections.Counter(); persym_tick = collections.Counter(); persym = collections.Counter()
    mono_ok = 0; total = 0
    for r in rows(PATHS):
        total += 1
        obs = r.get("ordered_path_observations") or []
        nb.append(len(obs))
        keyset.add((r["candidate_id"], r["decision_time_utc"]))
        d = datetime.fromisoformat(r["decision_time_utc"]); h = datetime.fromisoformat(r["horizon_end_utc"])
        hz.append(round((h - d).total_seconds() / 60.0, 3))
        if obs:
            fg.append(round((datetime.fromisoformat(obs[0]["time_utc"]) - d).total_seconds() / 60.0, 3))
            ts = [o["time_utc"] for o in obs]
            if all(ts[i] < ts[i + 1] for i in range(len(ts) - 1)): mono_ok += 1
        persym[r["symbol"]] += 1
        t = r.get("ordered_tick_source")
        if isinstance(t, dict):
            tick_dicts += 1; tick_keys.update(t.keys()); persym_tick[r["symbol"]] += 1
        srcsha[(r["symbol"], r.get("source_sha256"))] += 1
    nbs = sorted(nb)
    pool_keys = {(r["candidate_id"], r["decision_time_utc"]) for r in jan}
    R["paths"] = {"rows": total, "unique_keys": len(keyset),
                  "join_key": ["candidate_id", "decision_time_utc"],
                  "pool_rows_with_path": len(pool_keys & keyset),
                  "coverage_of_pool": len(pool_keys & keyset) / len(pool_keys),
                  "orphan_paths": len(keyset - pool_keys),
                  "bars_min": nbs[0], "bars_p05": q(nbs, .05), "bars_p25": q(nbs, .25),
                  "bars_p50": q(nbs, .5), "bars_mean": sum(nbs) / len(nbs), "bars_p95": q(nbs, .95),
                  "bars_max": nbs[-1], "bars_total": sum(nbs),
                  "rows_at_full_120": sum(1 for b in nb if b == 120),
                  "rows_under_60_bars": sum(1 for b in nb if b < 60),
                  "horizon_minutes_distinct": dict(collections.Counter(hz).most_common(5)),
                  "first_bar_offset_min_distribution": dict(collections.Counter(fg).most_common(6)),
                  "strictly_increasing_rows": mono_ok,
                  "ordered_tick_source_present": tick_dicts,
                  "ordered_tick_source_share": tick_dicts / total,
                  "ordered_tick_source_keys": dict(tick_keys),
                  "tick_backed_by_symbol": dict(persym_tick.most_common()),
                  "rows_by_symbol": dict(persym.most_common()),
                  "distinct_source_files": len(srcsha)}

    # ---------------- 6. february + breaker ----------------
    feb = list(rows(FEB))
    R["feb"] = {"n": len(feb), "fields": len(feb[0]),
                "extra_vs_jan": [k for k in feb[0] if k not in jan[0]],
                "days": sorted({r["decision_time_utc"][:10] for r in feb}),
                "profile_extra": profile([{k: r.get(k) for k in feb[0] if k not in jan[0]} for r in feb])}
    brk = list(rows(BRK))
    R["breaker"] = {"n": len(brk), "fields": len(brk[0]), "keys": list(brk[0].keys()),
                    "profile": profile(brk)}

    json.dump(R, open(os.path.join(OUT, "w0_MEASURE_V1.json"), "w"), indent=1, default=str)
    print("wrote w0_MEASURE_V1.json")
    print("jan n=%d fields=%d  feb n=%d fields=%d  paths=%d  breaker=%d"
          % (R["jan"]["n"], R["jan"]["fields"], R["feb"]["n"], R["feb"]["fields"],
             R["paths"]["rows"], R["breaker"]["n"]))
    print("constants:", R["jan"]["constants"])
    print("all-null:", R["jan"]["all_null"])
    print("cost identity:", {k: v for k, v in R["cost_identity"].items() if k != "component_mean_r"})
    print("overcharge pool:", R["spread_overcharge"].get("__POOL__"))


if __name__ == "__main__":
    main()
