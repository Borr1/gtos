# OTI3 G3 Geometry Alternative Packetization Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Candidate LTF Path Inventory

| Field | Value |
| --- | --- |
| Path | shadow_logs/candidate_ltf_path_order.jsonl |
| Rows | 1985 |
| Exact setup matches | 0 |
| Decision | REJECTED_AS_DIRECT_G3_OUTCOME_SOURCE |

## Alternatives

| Decision | Alternative | Reason |
| --- | --- | --- |
| USED_FOR_QUARANTINED_DESCRIPTIVE_GEOMETRY_ONLY | Use accepted G3 packets plus local price-compatible M1 OHLC labels | Labels are computed from local source-hashed M1 OHLC and are post-decision labels only, with no broker actual-R, live trade result, or blocked-packet outcome source. |
| REJECTED_FOR_G3_DIRECT_JOIN | Use candidate_ltf_path_order directly | The local candidate_ltf_path_order log has zero exact setup_id matches for the accepted G3 packets and carries result-bearing keys. |
| REJECTED_BLOCKED_PACKET_OUTCOMES | Use OTB2/OTB2R blocked G3 synthetic packets | OTB2 and OTB2R G3 rows were zero-record/blocked before the later G3 geometry input builder; blocked packet outputs are outside OTI3 scope. |
| REJECTED_FOR_LABEL_FAMILY_POLICY | Use broker account history, trade index lifecycle, or trade records | Broker actual-R, final_outcome, execution, and lifecycle labels are forbidden in this synthetic_path_r lane. |
| REJECTED_FOR_TERMINAL_ORDER_UNCERTAINTY | Use M15/H1 OHLC-only terminal order | M15/H1 bars cannot resolve intrabar entry/SL/TP order. OTI3 uses M1 only and still refuses same-M1 terminal-order guesses. |
| REJECTED_DENOMINATOR_TRAP | Pool all three G3 packets as independent rows | G3 packets are feature-family projections; parent_duplicate_group_id reuse makes pooled raw rows non-independent. |
