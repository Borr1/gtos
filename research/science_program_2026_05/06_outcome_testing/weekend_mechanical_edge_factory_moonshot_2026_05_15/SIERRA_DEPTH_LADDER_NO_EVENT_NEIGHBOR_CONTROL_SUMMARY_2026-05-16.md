# Sierra Depth Ladder No-Event Neighbor Controls

Generated UTC: `2026-05-15T21:30:04Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: no-event fallback descriptor rows joined to same-source intraday neighbor controls. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.

## Counts

- `fallback_feature_input_rows`: `26`
- `neighbor_pair_input_rows`: `5173`
- `target_neighbor_pair_rows`: `425`
- `target_summary_rows`: `26`
- `target_with_neighbor_rows`: `26`
- `target_without_neighbor_rows`: `0`
- `bucket_rows`: `26`
- `question_rows`: `8`

## Target Control Buckets

- `SAME_SOURCE_NEIGHBOR_ALIGNMENT_WEAKENING_CONTEXT`: `3`
- `TARGET_EVENT15_PROXY_BOOK_IMBALANCE_MISSING`: `3`
- `TARGET_EVENT15_PROXY_SOURCE_GAP_REMAINS`: `13`
- `UNDERPOWERED_TARGET_NEIGHBOR_N_LT_20`: `7`

## Proxy/Neighbor Relation Buckets

- `NEIGHBOR_BOUNDARY60_NO_EVENT_CONTEXT`: `30`
- `TARGET_EVENT15_PROXY_MISSING`: `12`
- `TARGET_EVENT15_PROXY_NO_SAMPLES`: `233`
- `TARGET_PROXY_BALANCED_NEIGHBOR_BALANCED`: `150`

## Interpretation Boundary

- This packet only tests whether no-event fallback proxy rows are generic same-source behavior or need split/weakening descriptors.
- Neighbor controls are descriptive and use Route C movement fields already present in the route ledger; they are not broker outcomes or promotion evidence.
- Every target-neighbor pair touching a fallback target is preserved; no pair subset or top-N cutoff is used.

## Next Same-Resource Work

- Recompute ladder source/capture requirements after incorporating exact boundary60 proof and neighbor-control buckets.
- Split the remaining imbalanced ladder descriptors by command-ladder sign, fallback proxy, and neighbor context.
- Continue exact missing `.depth` source-date acquisition where owned/current/free/public routes exist.
