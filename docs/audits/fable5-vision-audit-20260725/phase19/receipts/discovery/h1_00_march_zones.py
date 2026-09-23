"""h1 helper: pull (cid, dt) -> kill_zone/session_bucket/utc_hour_bucket for MARCH.

The March pool is the 74 MB FA2_M_R0 missed-opportunity ledger. Jan/Feb pools are small
and read inline; this one is streamed once, in the background, and cached as a tiny gz.
"""
import gzip, json, os, sys, time

D = os.path.dirname(os.path.abspath(__file__))
SRC = ("/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/research/operations/"
       "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
       "attempt_5_typed_sparse/FA2_M_R0/FA2_M_R0_MISSED_OPPORTUNITY_LEDGER.jsonl.gz")
OUT = os.path.join(D, "h1_MAR_ZONES_V1.jsonl.gz")

KEEP = ("candidate_id", "decision_time_utc", "kill_zone", "session_bucket",
        "authority_session", "route_session", "utc_hour_bucket", "origin_family",
        "decision_timeframe")

t0 = time.time()
n = w = 0
with gzip.open(OUT, "wt") as out:
    for line in gzip.open(SRC, "rt"):
        if not line.strip():
            continue
        n += 1
        r = json.loads(line)
        if r.get("missed_opportunity_r_scoreability_status") != "diagnostic_opportunity_r_scoreable":
            continue
        out.write(json.dumps({k: r.get(k) for k in KEEP}) + "\n")
        w += 1
print(json.dumps({"read": n, "written": w, "seconds": round(time.time() - t0, 1),
                  "out": OUT}))
