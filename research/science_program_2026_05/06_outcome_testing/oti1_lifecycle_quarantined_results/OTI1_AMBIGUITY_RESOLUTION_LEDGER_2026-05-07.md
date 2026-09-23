# OTI1 Ambiguity Resolution Ledger - 2026-05-07

**Lane:** `OTI1`  
**Artifact type:** `ambiguity_resolution_ledger`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

| Status | Ambiguity | Resolution |
| --- | --- | --- |
| ANSWERED_FACT | Which packets are in OTI1 scope? | Use only the 9 G12 OTB rebuild accepted OTB1R lifecycle packets from the metric freeze; exclude OTG0-PKT-017 and all non-OTB1R packets. |
| ANSWERED_FACT | Can OTI1 count raw rows? | No. All result rates use unique duplicate_group_id counts; raw rows are audit-only child-row inventory. |
| ANSWERED_FACT_WITH_BLOCKER | Are source-complete covariate claims available? | No for friction, volatility, footprint, news, macro-attention, FOMC, and Cboe packets; lifecycle-truth-only counts still run. |
| ANSWERED_FACT | Does OTG0-PKT-045 have two independent groups because it has two rows? | No. Both rows share duplicate_group_id opportunity:889468014bba028e10db17e2dc9c6fea and identical lifecycle labels; count once. |
| NOT_COMPUTABLE_AFTER_EVIDENCE_EXHAUSTION | Can validation statistics be computed? | descriptive duplicate-group counts are computable, but validation effective-N is not: the same lifecycle source groups are intentionally reused across multiple experiment packets, preregistered null/alternative/sample-floor fields are absent, and covariate/source-complete claims are blocked where applicable |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-016 use covariates for source-complete claims? | friction fields have a residual G12 question; no packet-bound as-of friction source is proven |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-025 use covariates for source-complete claims? | realized-vol and vol-of-vol source is not packet-bound for source-complete volatility claims |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-045 use covariates for source-complete claims? | footprint/absorption source contract and as-of proof are not packet-bound |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-055 use covariates for source-complete claims? | news event-window matcher/parser/no-lookahead fixtures are not cleared |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-059 use covariates for source-complete claims? | macro-attention and G5/G7 interaction source labels are not packet-bound |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-071 use covariates for source-complete claims? | FOMC parser, stale-source tests, event windows, and no-lookahead checks are not cleared |
| EXACT_LOCAL_BLOCKER | Can OTG0-PKT-079 use covariates for source-complete claims? | Cboe publication/as-of, parser/cache hashes, legal review, and no-lookahead tests remain unresolved |
