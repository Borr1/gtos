# LTO027 V2 Structural Selector Readiness - 2026-05-05

**Schema:** `lto027_v2_structural_selector_readiness_v1`
**Status:** `V2_STRUCTURAL_SELECTOR_NOT_READY_SHADOW_ONLY`
**Readiness verdict:** `NOT_READY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

V2 structural selector remains shadow-only and NOT_READY for promotion. MT5 account history can resolve filled broker outcomes where matching deals exist, but the current evidence still fails the broker-actual sample floor, cost/slippage/accounting, concentration, exact selector metadata, and promotion-dossier gates.

## Evidence Counts

- Latest V2b audit rows: `517`
- Latest V2b pair rows: `538`
- Countable unique pairs: `80`
- Countable broker-actual pairs: `0`
- Countable synthetic-path pairs: `19`
- Countable with lifecycle truth: `3`

## Readiness Gates

| Gate | Passed | Required | Observed | Blocker |
|---|---:|---|---|---|
| `G0_SHADOW_ONLY_BOUNDARY` | `True` | All selector/readiness evidence remains NO_PROMOTION_VERDICT with zero AI/canary/order/paid-data counters. | `{"non_no_promotion_rows": 0, "safety_counters_zero": true}` | `-` |
| `G1_COUNTABLE_BROKER_ACTUAL_R_SAMPLE_FLOOR` | `False` | >= 30 countable unique V2b/J46 pairs with broker actual-R. | `{"countable_broker_actual_pairs": 0, "countable_synthetic_path_pairs": 19, "countable_unique_pairs": 80}` | `BROKER_ACTUAL_R_SAMPLE_FLOOR_NOT_MET` |
| `G2_PENDING_LIFECYCLE_TRUTH_COMPLETE` | `False` | Every countable unique pair has pending-limit lifecycle truth or an explicit terminal/non-fill state. | `{"countable_unique_pairs": 80, "countable_with_lifecycle_truth": 3}` | `PENDING_LIFECYCLE_TRUTH_INCOMPLETE` |
| `G3_COST_SLIPPAGE_EXIT_ACCOUNTING_COMPLETE` | `False` | Promotion evidence uses broker/account-history rows with cost/slippage/exit accounting, not synthetic path R. | `{"broker_actual_pairs": 0, "candidate_linked_broker_actual_rows_available": 0, "global_broker_actual_claim_allowed_unique_rows": 5}` | `COST_SLIPPAGE_EXIT_ACCOUNTING_NOT_READY` |
| `G4_CONCENTRATION_DIAGNOSTICS_PASS` | `False` | >= 3 dates, top date share <= 0.5, top symbol share <= 0.5. | `{"date_counts": {"2026-05-03": 2, "2026-05-04": 6, "2026-05-05": 4, "2026-05-06": 3, "2026-05-07": 5, "2026-05-08": 4, "2026-05-31": 6, "2026-06-01": 50}, "distinct_dates": 8, "symbol_counts": {"AUDJPY": 1, "BTCUSD": 6, "CHFJPY": 1, "ETHUSD": 1, "EURGBP": 5, "EURJPY": 2, "GBPJPY": 2, "GBPUSD": 5, "JP225": 4, "NAS100": 3, "NZDUSD": 2, "UKOIL_cash": 14, "US30_cash": 7, "USDCAD": 1, "USDJPY": 2, "USOIL_cash": 13, "XAGUSD": 5, "XAUUSD": 6}, "top_date_share": 0.625, "top_symbol_share": 0.175}` | `CONCENTRATION_GATES_NOT_MET` |
| `G5_EXACT_SELECTOR_METADATA_CAPTURED` | `False` | Countable rows contain exact V2 selector/lock metadata, not shared candidate-path OB-boundary proxies. | `{"countable_exact_metadata_missing": 46}` | `EXACT_V2_SELECTOR_METADATA_NOT_CAPTURED` |
| `G6_PROMOTION_DOSSIER_PREREGISTERED` | `False` | A separate V2 structural selector promotion dossier is preregistered before any behavior change. | `{"matching_dossier_paths": []}` | `PROMOTION_DOSSIER_NOT_PREREGISTERED` |

## Concentration

- Date counts: `{'2026-05-04': 6, '2026-05-05': 4, '2026-05-03': 2, '2026-05-06': 3, '2026-05-07': 5, '2026-05-08': 4, '2026-05-31': 6, '2026-06-01': 50}`
- Symbol counts: `{'GBPJPY': 2, 'NAS100': 3, 'XAGUSD': 5, 'USDJPY': 2, 'XAUUSD': 6, 'US30_cash': 7, 'GBPUSD': 5, 'JP225': 4, 'BTCUSD': 6, 'ETHUSD': 1, 'EURJPY': 2, 'AUDJPY': 1, 'CHFJPY': 1, 'UKOIL_cash': 14, 'USOIL_cash': 13, 'USDCAD': 1, 'EURGBP': 5, 'NZDUSD': 2}`
- Top date share: `0.625`
- Top symbol share: `0.175`

## MT5 Account-History Boundary

- Export path: `data\account_history\mt5_deals_2026-04-27_2026-05-05.jsonl`
- Export present: `True`
- Export non-empty rows: `22`
- Global broker actual-R claim-allowed unique rows: `5`
- Candidate-linked broker actual rows available: `0`
- Countable broker-actual pairs: `0`
- Can resolve: `['filled account trades with MT5 entry/exit deals', 'commission/swap/profit and close deal IDs where exported', 'time-in-trade and close-side accounting for broker-filled positions when telemetry/export rows exist']`
- Cannot resolve: `['non-filled shadow alternatives and counterfactual selector branches', 'candidate rows that never became broker positions or closed deals', 'pending-limit no-fill/cancel/expiry lifecycle unless captured by the lifecycle logger', 'exact V2 selector lock metadata that was not written at decision time', 'preregistered promotion-dossier metadata and concentration-gate policy']`
- Claim boundary: Read-only MT5 account history is the source of truth for filled broker outcomes, but it cannot reconstruct unfilled shadow choices or missing decision-time selector metadata.

## Boundary

LTO-027 is a shadow-only promotion-readiness audit. It does not validate, promote, wire, or alter any structural selector, AI prompt, risk setting, safety gate, execution, or order path.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`
