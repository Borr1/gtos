# OTG0 Outcome Testing Control Rules - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Outcome review opened:** `false`  
**Validation safe:** `false`

## Acceptance Rules

- Accept OTG0 as complete only if all 97 owner-review preregs parse and match the master experiment preregistry exactly.
- Accept packet freeze only if outcome_review_opened remains false in both owner-review table and JSON preregistry.
- Accept source gating only if every source_contract_v2 row remains validation_safe=false and all source/as-of gaps are blockers, not silent assumptions.
- Accept lifecycle/synthetic lanes only for packet audit; outcome tests remain blocked until the packet audit verifies required fields, duplicate keys, no-leak fields, and source/as-of availability without reading results early.
- Accept broker actual-R lanes only as blocked unless account-history sample floors, fill/cost/close-side joins, and label-family separation are proven in a later frozen packet.
- Accept control-only rows only as audit/source/telemetry governance; they cannot become R-backtests without a new prereg.

## Blocker Rules

- If a data source has no registered source_contract_v2 row, create a source-registration blocker and do not use it as validation evidence.
- If source publication/as-of time is unknown, date-only, revised without vintage, or parser/cache/hash is missing, route to OTL3 source/as-of cleanup first.
- If no_leak_fields contain forbidden outcome/future names, block outcome opening until G0/G12 cleanup replaces them with as-of feature whitelists.
- If duplicate_group_id or independent unit is missing, block sample-floor, effective-N, DSR, PBO, and any confirm/kill language.
- If a packet mixes broker actual-R with synthetic path-R or lifecycle/no-fill in one primary metric, quarantine and fail the packet.
- If a future lane sees attractive results before packet freeze, label those results contaminated and discovery-only; do not move them into the acceptance path.

## Result Quarantine

- OTG0 itself may not create result files beyond packet/control/audit artifacts.
- Future OTL result files must live under research/science_program_2026_05/06_outcome_testing/quarantine/<lane_id>/ until G12 audits implementation validity.
- Every future result file must carry RESULT_QUARANTINED_DISCOVERY_ONLY and NO_PROMOTION_VERDICT.
- No future result may edit master registries, source validation flags, risk, prompts, selectors, permissions, execution, MT5, canaries, credentials, remote state, or order behavior.
- Broker actual-R, synthetic path-R, lifecycle/no-fill, and context/observation outputs must be separate files or separate tables with non-overlapping denominators.

## Label Families

```json
{
  "broker_actual_r": "Account-history realized R only; cost/slippage/close-side evidence required; never pooled with synthetic path-R or lifecycle/no-fill.",
  "context_only": "Source, eligibility, provenance, regime, or audit context; no return outcome.",
  "fill_no_fill": "Alias family for lifecycle fill/no-fill states; keep denominators separate from R labels.",
  "lifecycle_no_fill": "Fill/no-fill/cancel/expiry/wrong-side/tick-missing states; no-fill is not a loss and must not be ranked by R.",
  "observation_only": "Operational/audit/behavioral observation; no trading-edge backtest.",
  "synthetic_path_r": "Research-only ordered-path label; can be discovery evidence, never broker-realized validation or promotion evidence."
}
```

## Standing Blockers

| Blocker | Name | Next exact question |
|---|---|---|
| `OTG0-BLK-001` | Owner classification is routing only | For each row, does the packet audit prove the required fields before any outcome result is read? |
| `OTG0-BLK-002` | No source contract is validation safe | Which source-specific legal/cache/parser/publication/as-of/no-lookahead dossier clears a source while preserving validation_safe=false until owner approval? |
| `OTG0-BLK-003` | G11 no-leak semantic inversion | Which G0/G12 cleanup artifact replaces the 8 forbidden no_leak_fields with as-of feature whitelists without opening outcomes? |
| `OTG0-BLK-004` | Unregistered source placeholders and literature refs | Which source IDs stay in source_ids, and which move to evidence_refs, neighbor_lane_dependency, or blocked_dependency_refs? |
| `OTG0-BLK-005` | Duplicate hypothesis families | Are CD2/original experiments for the same hypothesis mutually exclusive tests, parent-child packets, or duplicate routes that must share a denominator? |
| `OTG0-BLK-006` | Existing-data packet existence is unverified | Do OTL1/OTL2 packet audits find concrete packet files with required fields, source hashes, duplicate keys, and no-leak timestamps? |
| `OTG0-BLK-007` | Broker actual-R sample and close-cost scarcity | Which account-history and close-side cost join packet reaches the preregistered actual-R floor without synthetic label pooling? |
| `OTG0-BLK-008` | Path/lifecycle packet fields missing in CD2-06 family | Where are source_hash, source_symbol, ordered prefill candles/ticks, pending-native fields, spread/tick, trade IDs, and strict packet-family separation stored? |
| `OTG0-BLK-009` | Macro/vol source publication/as-of unresolved | What exact COT/FRED/BIS/Cboe/VRP parser and vintage/cache rules prove feature_asof_utc <= decision_time_utc? |
| `OTG0-BLK-010` | Result quarantine before G12 audit | Does each later result file remain quarantined with DISCOVERY_ONLY_NOT_VALIDATION until G12 audits implementation validity? |

## NO_PROMOTION_VERDICT

These rules authorize only research-control packet audits and later quarantined discovery tests after packet readiness passes. They authorize no live trading, prompt, risk, execution, selector, safety-gate, MT5, canary, paid-data, credential, remote, order-behavior, source-validation, or promotion change.
