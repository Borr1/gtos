#!/usr/bin/env python3
"""A2 RECONCILE lane — follow-up micro-checks (run inline during the session; kept
here as the reproducible receipt).

1. Row M/L adjudication: binary-endpoint counts with the target FIXED at 2.0
   (vs per-row policy_target_r) on the net+cost reconstruction, tol 1e-9.
   Result (2026-08-03 run): jan 678/3,270 fixed  (own-target 682/3,270);
   feb 950/3,660 fixed (own-target 953/3,660) -> the pool receipts'
   binary_population used the FIXED 2.0 target.
2. Row D: effective_selector_action distribution within materialized rows.
   Result: jan {open-reduced-risk 3023, reject 853, reduce-risk 199, trade 20};
   feb {open-reduced-risk 1738, reject 434, reduce-risk 195, trade 11}.
3. Row C: session-field set identity on metals-LONG.
   Result: authority_session=='ny' XOR route_session=='ny' = 0 rows (identical
   sets, n=411); session_bucket=='ny' outside route-ny = 0 rows (bucket-ny is a
   strict subset, n=386 of 411); authority XOR bucket = 25 rows.
4. Row J (feb): the one accepted-not-filled-not-expired probe is
   candidate broadorigin_a8c9f3ae6b1a2058... XAUUSD SHORT 2026-02-18T15:15:00Z,
   order_status cancelled_replaced_by_scheduler_v4; that candidate_id carries
   9 pending_accepted + 8 filled rows in the ledger overall.
"""
import gzip, json
from collections import Counter

JAN_POOL = "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
FEB_POOL = "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"


def endpoint_and_membership(path):
    t20 = s20 = 0
    own = 0
    effB = Counter()
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            net, cost = r.get("opportunity_net_proxy_r"), r.get("cost_r")
            if net is None or cost is None:
                continue
            g = net + cost
            if abs(g - 2.0) <= 1e-9:
                t20 += 1
            if abs(g + 1.0) <= 1e-9:
                s20 += 1
            tgt = r.get("policy_target_r")
            if tgt is not None and abs(g - float(tgt)) <= 1e-9:
                own += 1
            if r.get("scheduler_materialization_status") == "scheduler_option_materialized":
                effB[str(r.get("effective_selector_action"))] += 1
    return {"fixed2_target_1e9": t20, "fixed_stop_1e9": s20,
            "own_target_1e9": own, "effective_action_within_materialized": dict(effB)}


def session_identity(path):
    xor_ar = bucket_not_route = xor_ab = n = 0
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r.get("symbol") in ("XAUUSD", "XAGUSD") and r.get("direction") == "LONG":
                n += 1
                a = r.get("authority_session") == "ny"
                rt = r.get("route_session") == "ny"
                b = r.get("session_bucket") == "ny"
                if a != rt:
                    xor_ar += 1
                if b and not rt:
                    bucket_not_route += 1
                if a != b:
                    xor_ab += 1
    return {"metals_long_rows": n, "authority_xor_route": xor_ar,
            "bucket_ny_outside_route_ny": bucket_not_route, "authority_xor_bucket": xor_ab}


if __name__ == "__main__":
    print("jan:", json.dumps(endpoint_and_membership(JAN_POOL)))
    print("feb:", json.dumps(endpoint_and_membership(FEB_POOL)))
    print("jan session identity:", json.dumps(session_identity(JAN_POOL)))
