#!/usr/bin/env python3
"""Diff a retained pre-integration comparator run against a fresh post-integration run.

Usage: diff_day.py DAY RETAINED_ROOT FRESH_ROOT OUT_JSON
Reads only stage ledgers + run receipts. Pure analysis; writes one JSON.
"""
import collections
import glob
import gzip
import json
import sys


def load_ledger(root: str):
    paths = glob.glob(root + "/*_stage_ledger.jsonl.gz")
    assert len(paths) == 1, paths
    rows = []
    with gzip.open(paths[0], "rt") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_receipt(root: str):
    paths = glob.glob(root + "/*_run_receipt.json")
    assert len(paths) == 1, paths
    return json.load(open(paths[0]))


def key_of(row):
    return row["identity"].get("canonical_replay_candidate_instance_key")


def census(rows):
    stages = collections.Counter(r.get("stage") for r in rows)
    cands = {key_of(r): r for r in rows if r.get("stage") == "candidate"}
    missed = {key_of(r): r for r in rows if r.get("stage") == "missed"}
    orders = [r for r in rows if r.get("stage") == "order"]
    trades = {key_of(r): r for r in rows if r.get("stage") == "trade"}
    raw_reason = collections.Counter()
    raw_action = collections.Counter()
    for r in missed.values():
        o = r["observables"]
        raw_reason[o.get("raw_selector_reason")] += 1
        raw_action[o.get("raw_selector_action")] += 1
    # trades that also appear in missed would be a conservation break; count overlap
    outcomes = collections.Counter(
        t["observables"].get("close_reason") or t["observables"].get("terminal_outcome")
        for t in trades.values()
    )
    net_vals = [
        t["observables"].get("net_r")
        for t in trades.values()
        if t["observables"].get("net_r") is not None
    ]
    unique_order_keys = {key_of(r) for r in orders}
    return {
        "stage_counts": dict(sorted(stages.items())),
        "candidates": len(cands),
        "missed": len(missed),
        "unique_order_candidates": len(unique_order_keys),
        "order_rows": len(orders),
        "trades": len(trades),
        "trade_outcomes": dict(sorted(outcomes.items())),
        "scoreable_trade_net_r_sum": (
            round(sum(net_vals), 8) if net_vals else None
        ),
        "scoreable_trades": len(net_vals),
        "raw_selector_action_census": dict(sorted(raw_action.items())),
        "raw_selector_reason_census": dict(sorted(raw_reason.items())),
        "_cands": cands,
        "_missed": missed,
        "_trades": trades,
        "_order_keys": unique_order_keys,
    }


def conservation(c):
    lhs = c["candidates"]
    rhs_keys = set(c["_missed"]) | c["_order_keys"] | set(c["_trades"])
    # terminal_unfilled candidates are order-stage keys that never traded; the
    # disjoint-union check is candidates == missed ∪ orders ∪ trades with
    # missed ∩ (orders ∪ trades) == ∅
    overlap_missed_order = set(c["_missed"]) & c["_order_keys"]
    return {
        "candidates": lhs,
        "union_missed_orders_trades": len(rhs_keys),
        "exact_union": lhs == len(rhs_keys),
        "missed_order_overlap": len(overlap_missed_order),
        "trades_outside_orders": len(set(c["_trades"]) - c["_order_keys"]),
    }


def main():
    day, retained_root, fresh_root, out_json = sys.argv[1:5]
    pre = census(load_ledger(retained_root))
    post = census(load_ledger(fresh_root))
    pre_rc = load_receipt(retained_root)
    post_rc = load_receipt(fresh_root)

    pre_keys, post_keys = set(pre["_cands"]), set(post["_cands"])
    shared = pre_keys & post_keys
    # disposition transition census on shared candidates
    def dispo(c, k):
        if k in c["_trades"]:
            return "trade"
        if k in c["_missed"]:
            return "missed:" + str(
                c["_missed"][k]["observables"].get("raw_selector_reason")
            )
        if k in c["_order_keys"]:
            return "terminal_unfilled"
        return "absent"

    transitions = collections.Counter()
    for k in shared:
        a, b = dispo(pre, k), dispo(post, k)
        if a != b:
            transitions[(a, b)] += 1

    reason_delta = {}
    for reason in set(pre["raw_selector_reason_census"]) | set(
        post["raw_selector_reason_census"]
    ):
        a = pre["raw_selector_reason_census"].get(reason, 0)
        b = post["raw_selector_reason_census"].get(reason, 0)
        if a != b:
            reason_delta[str(reason)] = {"pre": a, "post": b, "delta": b - a}

    doc = {
        "schema": "gtos.wave21.post_integration_comparator_day_diff.v1",
        "day_utc": day,
        "retained_root": retained_root,
        "fresh_root": fresh_root,
        "retained_code_manifest_root": pre_rc["inputs"]["code_manifest"][
            "code_root_sha256"
        ],
        "fresh_code_manifest_root": post_rc["inputs"]["code_manifest"][
            "code_root_sha256"
        ],
        "conservation": {"pre": conservation(pre), "post": conservation(post)},
        "counts": {
            side: {
                k: v
                for k, v in c.items()
                if not k.startswith("_")
            }
            for side, c in (("pre", pre), ("post", post))
        },
        "candidate_identity": {
            "pre_only": sorted(pre_keys - post_keys)[:50],
            "post_only": sorted(post_keys - pre_keys)[:50],
            "n_pre_only": len(pre_keys - post_keys),
            "n_post_only": len(post_keys - pre_keys),
            "n_shared": len(shared),
        },
        "selector_reason_delta": dict(sorted(reason_delta.items())),
        "disposition_transitions_on_shared": [
            {"pre": a, "post": b, "n": n}
            for (a, b), n in transitions.most_common()
        ],
        "receipt_dag_audit": {
            "pre_status": (pre_rc.get("occurrence_stage_dag_audit") or {}).get(
                "status"
            ),
            "post_status": (post_rc.get("occurrence_stage_dag_audit") or {}).get(
                "status"
            ),
            "post_dag_model": (post_rc.get("occurrence_stage_dag_audit") or {}).get(
                "dag_model"
            ),
        },
        "post_independent_verification_status": None,
    }
    # fresh runs write an independent verification receipt alongside
    ver = glob.glob(fresh_root + "/*_independent_verification.json")
    if ver:
        doc["post_independent_verification_status"] = json.load(open(ver[0])).get(
            "status"
        )
    with open(out_json, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: doc[k] for k in (
        "day_utc", "conservation", "candidate_identity",
        "receipt_dag_audit", "post_independent_verification_status",
    )}, indent=1, sort_keys=True))
    print("counts pre :", json.dumps(doc["counts"]["pre"], sort_keys=True)[:400])
    print("counts post:", json.dumps(doc["counts"]["post"], sort_keys=True)[:400])


if __name__ == "__main__":
    main()
