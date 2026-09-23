#!/usr/bin/env python3
"""Lane FF verification: independent recompute of executed per-family splits.

Recomputes FF1/FF2 from RAW inputs only:
  - Jan lane trade table (wave16 CJ_RECLOCKED_S0R0_V7_LANE, 1 meta + 57 trades)
  - Feb lane trade table (wave18 CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE, 1 meta + 58 trades)
  - Jan pool CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz (27,658 scoreable rows)
  - Feb pool CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz (24,239 rows)
Join key: (candidate_id, decision_time_utc, symbol, side/direction) -- the
FA-Phase-1-verified unique key; bare candidate_id is NOT unique.
Streaming line-by-line throughout; nothing loaded as a DataFrame.

February is read for ATTRIBUTION ONLY under owner_mandate_20260801.
No March data, no live-forward data, no packs/ touched.
"""
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict

JAN_LANE = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl"
FEB_LANE = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl"
JAN_POOL = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
FEB_POOL = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
# Raw run TRADE_LEDGERs (fallback family authority for trades absent from the
# scoreable pool; these are run artifacts that predate Sol, not Sol receipts).
JAN_TRADE_LEDGER = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl"
FEB_TRADE_LEDGER = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/CP_FEBRUARY_TRUE_UTC_S0R0_V1_TRADE_LEDGER.jsonl"

OUT_DIR = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/a2_verify"


def sha256_gz_decompressed(path):
    h = hashlib.sha256()
    with gzip.open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_lane(path):
    meta = None
    trades = []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            if row.get("row_kind") == "trade":
                trades.append(row)
            else:
                meta = row
    return meta, trades


def build_pool_index(path):
    """Stream the pool; index (cid, t, sym, side) -> family fields."""
    idx = {}
    dup_keys = 0
    cid_counter = Counter()
    n = 0
    fam_disagree = 0
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            n += 1
            side = r.get("side") or r.get("direction")
            key = (r["candidate_id"], r["decision_time_utc"], r["symbol"], side)
            if key in idx:
                dup_keys += 1
            of, rf, fw = r.get("origin_family"), r.get("route_family"), r.get("framework")
            if of != rf:
                fam_disagree += 1
            idx[key] = (of, rf, fw)
            cid_counter[r["candidate_id"]] += 1
    return idx, dup_keys, cid_counter, n, fam_disagree


def ledger_family(path):
    """Stream the raw TRADE_LEDGER; map 4-tuple key -> origin_family (fallback)."""
    out = {}
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            n += 1
            side = r.get("side") or r.get("direction")
            key = (r.get("candidate_id"), r.get("decision_time_utc"), r.get("symbol"), side)
            out[key] = (r.get("origin_family"), r.get("route_family"), r.get("framework"))
    return out, n


def summarize(trades, pool_idx, cid_counter, ledger_fams):
    fam_rows = defaultdict(list)
    join_stats = {
        "matched_pool_4tuple": 0,
        "unmatched_pool_4tuple": 0,
        "fallback_trade_ledger": 0,
        "unresolved": 0,
        "bare_cid_ambiguous_trades": 0,
        "origin_route_framework_consistent": True,
        "inconsistencies": [],
    }
    fw_map_ok = True
    for t in trades:
        key = (t["candidate_id"], t["decision_time_utc"], t["symbol"], t["direction"])
        fam = None
        src = None
        if key in pool_idx:
            join_stats["matched_pool_4tuple"] += 1
            of, rf, fw = pool_idx[key]
            fam, src = of, "pool"
            if of != rf:
                join_stats["origin_route_framework_consistent"] = False
                join_stats["inconsistencies"].append({"key": list(key), "origin_family": of, "route_family": rf})
        else:
            join_stats["unmatched_pool_4tuple"] += 1
            if key in ledger_fams:
                of, rf, fw = ledger_fams[key]
                fam, src = of, "trade_ledger"
                join_stats["fallback_trade_ledger"] += 1
            else:
                join_stats["unresolved"] += 1
                fam, src = "UNRESOLVED", "none"
        if cid_counter.get(t["candidate_id"], 0) > 1:
            join_stats["bare_cid_ambiguous_trades"] += 1
        fam_rows[fam].append((t, src))

    families = {}
    for fam, rows in sorted(fam_rows.items()):
        n = len(rows)
        net_vals = [r[0]["net_r"] for r in rows if r[0].get("net_r") is not None]
        gross_vals = [r[0]["final_r"] for r in rows if r[0].get("final_r") is not None]
        cost_vals = [r[0]["cost_r"] for r in rows if r[0].get("cost_r") is not None]
        families[fam] = {
            "n": n,
            "scoreable_n": len(net_vals),
            "unscoreable_n": n - len(net_vals),
            "net_r_sum": sum(net_vals),
            "gross_r_sum": sum(gross_vals),
            "cost_r_sum_all_rows": sum(cost_vals),
            "wins_net_gt_0": sum(1 for v in net_vals if v > 0),
            "family_sources": Counter(r[1] for r in rows),
        }
    total_net = [t["net_r"] for t in trades if t.get("net_r") is not None]
    total = {
        "n": len(trades),
        "scoreable_n": len(total_net),
        "unscoreable_n": len(trades) - len(total_net),
        "net_r_sum": sum(total_net),
        "gross_r_sum": sum(t["final_r"] for t in trades if t.get("final_r") is not None),
        "cost_r_sum_all_rows": sum(t["cost_r"] for t in trades if t.get("cost_r") is not None),
        "wins_net_gt_0": sum(1 for v in total_net if v > 0),
    }
    return families, total, join_stats


def main():
    result = {"schema": "gtos.wave19.a2_verify.lane_ff.recompute.v1"}

    # --- integrity: pools I read vs pools Sol read (different paths) ---
    result["pool_sha256_decompressed"] = {
        "jan_pool_path": JAN_POOL,
        "jan_pool_sha256": sha256_gz_decompressed(JAN_POOL),
        "jan_pool_sha256_sol_manifest": "28aab6c609624b88662146475dd9632be1943bc161ce4672bebf2d5e506654eb",
        "feb_pool_path": FEB_POOL,
        "feb_pool_sha256": sha256_gz_decompressed(FEB_POOL),
        "feb_pool_sha256_sol_manifest": "d4cb507f812f9f990c62591c0a3ae4c38f5cd5147a65f66a027ac4d23efe6929",
    }

    for win, lane_path, pool_path, ledger_path in (
        ("january", JAN_LANE, JAN_POOL, JAN_TRADE_LEDGER),
        ("february", FEB_LANE, FEB_POOL, FEB_TRADE_LEDGER),
    ):
        meta, trades = load_lane(lane_path)
        pool_idx, dup_keys, cid_counter, pool_n, fam_disagree = build_pool_index(pool_path)
        # fallback ledger only loaded lazily if needed
        need_fallback = any(
            (t["candidate_id"], t["decision_time_utc"], t["symbol"], t["direction"]) not in pool_idx
            for t in trades
        )
        ledger_fams, ledger_n = ({}, 0)
        if need_fallback:
            ledger_fams, ledger_n = ledger_family(ledger_path)
        families, total, join_stats = summarize(trades, pool_idx, cid_counter, ledger_fams)
        for fam in families.values():
            fam["family_sources"] = dict(fam["family_sources"])
        # bare-cid ambiguity magnitude inside the pool itself
        multi_cid = sum(1 for c, k in cid_counter.items() if k > 1)
        result[win] = {
            "lane_meta_counts": meta.get("counts") if meta else None,
            "lane_trade_rows": len(trades),
            "pool_rows": pool_n,
            "pool_4tuple_duplicate_keys": dup_keys,
            "pool_origin_route_family_disagreements": fam_disagree,
            "pool_candidate_ids_with_multiple_rows": multi_cid,
            "trade_ledger_fallback_rows_loaded": ledger_n,
            "join_stats": join_stats,
            "families": families,
            "total": total,
        }
        # FVG vs non-FVG split
        fvg = families.get("current_fvg_fill", {"net_r_sum": 0.0, "n": 0})
        result[win]["fvg_net_r_sum"] = fvg["net_r_sum"]
        result[win]["fvg_n"] = fvg["n"]
        result[win]["non_fvg_net_r_sum"] = total["net_r_sum"] - fvg["net_r_sum"]
        result[win]["non_fvg_n"] = total["n"] - fvg["n"]

    with open(f"{OUT_DIR}/ff_recompute_raw.json", "w") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print(json.dumps({
        k: {kk: vv for kk, vv in v.items() if kk in (
            "lane_trade_rows", "pool_rows", "fvg_n", "fvg_net_r_sum",
            "non_fvg_n", "non_fvg_net_r_sum", "join_stats")}
        if isinstance(v, dict) and k in ("january", "february") else v
        for k, v in result.items()
    }, indent=1, sort_keys=True))
    print("\nFAMILIES:")
    for win in ("january", "february"):
        print(f"-- {win}")
        for fam, s in result[win]["families"].items():
            print(f"  {fam}: n={s['n']} scoreable={s['scoreable_n']} net_sum={s['net_r_sum']:.8f} "
                  f"gross_sum={s['gross_r_sum']:.8f} cost_sum={s['cost_r_sum_all_rows']:.8f} wins={s['wins_net_gt_0']} src={s['family_sources']}")
        t = result[win]["total"]
        print(f"  TOTAL: n={t['n']} scoreable={t['scoreable_n']} net_sum={t['net_r_sum']:.8f} "
              f"gross_sum={t['gross_r_sum']:.8f} cost_sum={t['cost_r_sum_all_rows']:.8f} wins={t['wins_net_gt_0']}")


if __name__ == "__main__":
    sys.exit(main())
