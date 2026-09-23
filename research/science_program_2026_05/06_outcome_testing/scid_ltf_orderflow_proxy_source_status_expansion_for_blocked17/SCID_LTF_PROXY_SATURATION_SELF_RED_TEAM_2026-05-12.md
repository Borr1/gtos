# SCID LTF/Orderflow/Proxy Blocked-17 Saturation And Self-Red-Team

Date: 2026-05-12

Evidence class: `SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_ONLY`

Promotion posture: `NO_PROMOTION_VERDICT`

## Objective Restatement

This packet pursued the 17 accepted hypothesis cards assigned to `SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17`. It did not open outcomes, validation, result scoring, R/PnL, win-rate, expectancy, performance, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restarts, live behavior changes, or trading/risk/safety/prompt-decision changes.

## Denominator Check

- Accepted denominator: 40
- Ready descriptor/control cards excluded: 8
- Blocked cards: 32
- Included LTF/orderflow/proxy blocked cards: 17
- Future-capture blocked cards excluded: 15
- Expansion candidates remain quarantined outside the accepted denominator.

## Terminal Status Distribution

{
  "PARTIAL_SOURCE_STATUS_EXPANDED_WITH_NON_GENERATABLE_SOURCE_STATE_DEPENDENCY": 6,
  "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED": 4,
  "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED": 7
}

## Source Families Found

{
  "ACCEPTED_LTF_PROXY_SOURCE_STATUS_ARTIFACT": 60,
  "BROKER_NATIVE_MARKET_TICK_PARQUET_CONTEXT_NOT_ACCOUNT_EVIDENCE": 186,
  "ORDERFLOW_DATABENTO_OR_PRIMITIVE_SOURCE_CONTROL": 593,
  "OTHER_RELEVANT_SOURCE_CONTROL_ARTIFACT": 6142,
  "OTHER_RELEVANT_SOURCE_METADATA": 931,
  "PATH_OR_SOURCE_STATUS_SHADOW_SOURCE": 30,
  "PROXY_MAPPING_OR_REGISTRY_SOURCE_CONTROL": 4545,
  "SIERRA_CONVERTED_LTF_OHLCV_SOURCE": 504,
  "SIERRA_SCID_TIME_AND_SALES_FOOTPRINT_SOURCE": 33
}

## Red-Team Questions

1. Could source-status evidence be mistaken for result evidence?
   Answer: every artifact carries `validation_safe=false`, `outcome_review_opened=false`, `opens_result_scoring=false`, and `may_score_results_now=false`; no target/result fields are created.

2. Could proxy evidence be mistaken for broker-native CFD truth?
   Answer: proxy rows are explicitly `NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY`; future G12 must accept a proxy-transfer or same-market contract before interpretation.

3. Could raw blobs leak into the repo?
   Answer: raw parquet, SCID, depth, and vendor blobs are referenced by metadata/hash-deferral policy only. The route writes no raw market data files.

4. Could non-generatable historical strategy state be invented from price?
   Answer: entry, stop, target, POI, framework, and MSO fields are classified as `NON_GENERATABLE_HISTORICAL_SOURCE_STATE` where applicable and routed to future capture/source-state proof.

5. Did the search stop at the current worktree?
   Answer: no. The ledger searches accepted source-control artifacts, current data/shadow roots, absolute production data roots, Sierra local data, and prior `C:/tmp/gtos_otb` worktrees.

6. What remains truly unresolved?
   Answer: parser/source-hash/as-of packet construction for recoverable LTF sources, explicit proxy-validity contracts for orderflow/depth/proxy sources, prospective capture for baseline/control and non-generatable strategy-state fields, and exact owner/export approval where future raw parsing or vendor pulls are outside this route.

## Stop Condition

The route stops before scoring. Next allowed gates are an independent G12 audit of this source-status packet and a later G0 blocked-card unblocking synthesis.
