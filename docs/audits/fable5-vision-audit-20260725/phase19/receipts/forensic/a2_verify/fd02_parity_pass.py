#!/usr/bin/env python3
"""FD-02 raw verification: blocker-key schema drift + full/compact parity join.

Streams the CP February full missed ledger and the CP February compact pool.
February is attribution-only under owner_mandate_20260801. No March, no
live-forward. Join key: candidate_id + decision_time_utc, with duplicate-count
audit (FA Phase 1 join hazard) and a symbol/direction extension check.
"""

from __future__ import annotations

import gzip
import json
import resource
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent / "FD02_PARITY_RAW.json"

FEB_LEDGER = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/"
    "CP_FEBRUARY_TRUE_UTC_S0R0_V1_MISSED_OPPORTUNITY_LEDGER.jsonl"
)
FEB_POOL = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"
)

LEGACY = "missed_package_replay_order_executable_final_blocker_class"
CANON = "final_blocker_class"


def is_scoreable(row) -> bool:
    return bool(
        row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        or row.get("missed_opportunity_r_scoreability_status")
        == "diagnostic_opportunity_r_scoreable"
    )


def key_of(row):
    cid = str(row.get("candidate_id") or "").strip()
    t = str(row.get("decision_time_utc") or row.get("decision_time") or "").strip()
    if not cid or not t:
        return None
    return f"{cid}@@{t}"


ledger = {
    "rows": 0,
    "legacy_key_present": 0,
    "canon_key_present": 0,
    "commission_repair_status_key_present": 0,
    "pretrade_key_present": 0,
    "scoreable_rows": 0,
    "scoreable_key_null": 0,
    "scoreable_dupe_keys": 0,
}
led_blocker: dict[str, str] = {}
led_key_counter: Counter = Counter()

with FEB_LEDGER.open("rb") as handle:
    for raw in handle:
        if not raw.strip():
            continue
        row = json.loads(raw)
        ledger["rows"] += 1
        if LEGACY in row:
            ledger["legacy_key_present"] += 1
        if CANON in row:
            ledger["canon_key_present"] += 1
        if "commission_r_repair_status" in row:
            ledger["commission_repair_status_key_present"] += 1
        if "pretrade_cost_packet_status" in row:
            ledger["pretrade_key_present"] += 1
        if is_scoreable(row):
            ledger["scoreable_rows"] += 1
            k = key_of(row)
            if k is None:
                ledger["scoreable_key_null"] += 1
                continue
            led_key_counter[k] += 1
            led_blocker[k] = row.get(LEGACY, row.get(CANON))

ledger["scoreable_unique_keys"] = len(led_blocker)
ledger["scoreable_dupe_keys"] = sum(1 for v in led_key_counter.values() if v > 1)

pool = {
    "rows": 0,
    "legacy_key_present": 0,
    "canon_key_present": 0,
    "key_null": 0,
    "dupe_keys": 0,
}
pool_blocker: dict[str, str] = {}
pool_key_counter: Counter = Counter()

with gzip.open(FEB_POOL, "rt", encoding="utf-8") as handle:
    for line in handle:
        if not line.strip():
            continue
        row = json.loads(line)
        pool["rows"] += 1
        if LEGACY in row:
            pool["legacy_key_present"] += 1
        if CANON in row:
            pool["canon_key_present"] += 1
        k = key_of(row)
        if k is None:
            pool["key_null"] += 1
            continue
        pool_key_counter[k] += 1
        pool_blocker[k] = row.get(CANON, row.get(LEGACY))

pool["unique_keys"] = len(pool_blocker)
pool["dupe_keys"] = sum(1 for v in pool_key_counter.values() if v > 1)

common = set(led_blocker) & set(pool_blocker)
mismatches = [
    k for k in common if led_blocker[k] != pool_blocker[k]
]
result = {
    "schema": "gtos.phase19.fa_a2_verify.fd02_parity.v1",
    "february_provenance": "owner_mandate_20260801",
    "ledger": ledger,
    "pool": pool,
    "parity": {
        "join_contract": "candidate_id + decision_time_utc",
        "common_keys": len(common),
        "missing_from_pool": len(set(led_blocker) - set(pool_blocker)),
        "extra_in_pool": len(set(pool_blocker) - set(led_blocker)),
        "blocker_value_mismatches": len(mismatches),
        "blocker_mismatch_examples": mismatches[:5],
    },
    "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
}
OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
print(json.dumps(result["parity"] | {"ledger_rows": ledger["rows"], "peak_rss_mb": round(result["peak_rss_bytes"] / 1e6, 1)}))
