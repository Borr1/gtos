# G12 READY8 Fail-Closed Source Repair Audit

Date: 2026-05-15

Evidence class: `G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_ONLY`

Decision: `ACCEPT_AS_G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_NO_PROMOTION`

The audit recomputed the `35,811` fail-closed/excluded-row inventory from the accepted target-result files, verified the sealed fail-closed ledger sums to `35,811`, recomputed all `220` repaired bars from current local Sierra byte ranges, and recomputed all `5,320` repaired target rows from the repaired bar packet plus frozen source bars.

The current Sierra files have append-time metadata drift relative to the builder packet, but all audited byte ranges still match the packet source-record hashes and parsed OHLC/volume fields. That drift is recorded as nonblocking because the packet is byte-range/hash bound, not full-file-size bound.

R7 may consume the `5,320` repaired target rows only under `G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_2026-05-15.json`. The remaining `25,240` target rows stay fail-closed, and the `5,251` role exclusions stay denominator-policy exclusions.

Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
