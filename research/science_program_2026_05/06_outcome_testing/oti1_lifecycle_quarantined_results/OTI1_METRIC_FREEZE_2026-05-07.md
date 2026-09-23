# OTI1 Metric Freeze - 2026-05-07

**Lane:** `OTI1`  
**Scope:** quarantined lifecycle/no-fill descriptive outcome test  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`  
**Frozen before lifecycle label inspection:** `true`

## Allowed Cohort

Use only the `9` G12 OTB rebuild accepted `OTB1R` lifecycle packets from `G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07`:

| Packet | Experiment | Frozen row count | Frozen unique duplicate groups |
|---|---|---:|---:|
| `OTG0-PKT-011` | `G10-EXP-PREFILL-003` | 8 | 7 |
| `OTG0-PKT-016` | `EXP-G11-FRICTION-GATE-007` | 8 | 7 |
| `OTG0-PKT-025` | `EXP-G2-GARCH-LIFECYCLE-002` | 8 | 7 |
| `OTG0-PKT-029` | `EXP-G2-SURVIVAL-PATH-006` | 8 | 7 |
| `OTG0-PKT-045` | `EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003` | 2 | 1 |
| `OTG0-PKT-055` | `EXP-G5-NEWS-005` | 8 | 7 |
| `OTG0-PKT-059` | `EXP-G5-XG7-MACRO-ATTN-009` | 8 | 7 |
| `OTG0-PKT-071` | `EXP-G7-FOMC-ATTN-003` | 8 | 7 |
| `OTG0-PKT-079` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | 4 | 4 |

Explicitly excluded:

- `OTG0-PKT-017` (`EXP-G11-OBSERVER-EXPANSION-006`) because it exists in the OTB1R rebuild directory but is not on the G12 OTB rebuild accepted OTB1R shortlist.
- All `OTB2R`, broker-actual-R, synthetic-path-R, source-cleanup-first, forward-shadow, control-only, blocked, and non-shortlisted packets.

## Frozen Metric

Primary OTI1 metric is descriptive lifecycle state distribution only:

```text
unique duplicate_group_id count by normalized lifecycle_state and fill_or_no_fill_state
```

Secondary descriptive slices are allowed only over fields already present in the input-only packet rows and only when they do not require source-complete covariates:

- symbol
- session
- side
- packet_id
- experiment_id
- lifecycle_state
- fill_or_no_fill_state
- cancel_expiry_or_wrong_side_reason

No broker realized R, synthetic path R, win/loss R, outcome R, return label, or blocked-packet outcome may be read or reported.

## Frozen Denominator

The denominator is unique `duplicate_group_id`, not raw rows.

Counting rule:

1. Within each packet, count each `duplicate_group_id` once.
2. Across the portfolio OTI1 rollup, count each stable `packet_id::duplicate_group_id` once so separate experiments are not collapsed into one pooled validation unit.
3. If multiple rows share a duplicate group with identical normalized lifecycle labels, count that group once and record the raw duplicate rows as non-independent children.
4. If multiple rows share a duplicate group but disagree on normalized lifecycle label, mark the group `AMBIGUOUS_DUPLICATE_GROUP_LABEL_CONFLICT`, exclude it from directional label-rate claims, include it in the denominator audit, and record it in the ambiguity ledger.
5. Raw row counts may be reported only as audit context, never as effective N or a sample-floor pass.

## Frozen Exclusions

Exclude a row or group from primary descriptive lifecycle-rate claims when:

- packet is not one of the 9 allowed G12-accepted OTB1R lifecycle packets,
- `duplicate_group_id` is missing,
- required lifecycle label fields are missing after allowed alias normalization,
- the packet contains only covariate/source context and no lifecycle truth label,
- normalized duplicate-group labels conflict,
- the row requires friction, volatility, footprint, news, macro-attention, FOMC, or Cboe covariates without local as-of/source proof already present in the packet/control artifacts.

These exclusions do not block lifecycle-truth-only descriptive output for rows whose lifecycle truth is locally present. They block only covariate/source-complete claims and validation-style inference.

## Frozen Duplicate Group Policy

`duplicate_group_id` is the independent-unit key. If a packet uses an alias or nested duplicate policy field, OTI1 may map it only when the source packet or G12 duplicate report proves the mapping without looking at outcome/R labels.

Expected unique duplicate-group counts must match the G12 OTB rebuild accepted shortlist:

- `OTG0-PKT-011`: 7
- `OTG0-PKT-016`: 7
- `OTG0-PKT-025`: 7
- `OTG0-PKT-029`: 7
- `OTG0-PKT-045`: 1
- `OTG0-PKT-055`: 7
- `OTG0-PKT-059`: 7
- `OTG0-PKT-071`: 7
- `OTG0-PKT-079`: 4

A mismatch is an implementation blocker, not a license to count raw rows.

## Frozen Sample-Floor Rule

Per-packet sample floor is read from the packet/prereg if present; otherwise OTI1 applies a strict discovery floor of `20` unique duplicate groups for validation-statistic eligibility.

Portfolio-level pooled lifecycle-truth-only descriptive totals may be shown, but validation statistics still require:

- at least `20` unique independent units,
- no duplicate-label conflicts,
- a pre-registered null and alternative for a lifecycle rate,
- no covariate/source-complete dependency unless local as-of proof is present,
- no packet-family or label-family mixing.

If these conditions fail, DSR/PBO/raw p are reported as `not_computable` with the exact reason after evidence exhaustion.

## Frozen Label-Family Boundary

OTI1 may inspect only lifecycle/no-fill labels in the 9 accepted OTB1R packets after this freeze:

- `lifecycle_no_fill`
- `fill_no_fill`
- cancel/expiry/wrong-side/tick-missing/same-bar/unresolved lifecycle reason fields

Forbidden label families for OTI1:

- `broker_actual_r`
- `synthetic_path_r`
- `win_loss`
- `actual_r`
- `outcome_r`
- realized R or path-R comparators
- blocked-packet outcomes

Any forbidden field found in an accepted packet is recorded as label-family separation evidence and is not read as a value for a result claim.

## Frozen Not-Computable Criteria

Report `not_computable` instead of a statistic when any of these apply:

- effective N below the frozen sample floor,
- missing null/alternative for a lifecycle rate,
- packet-specific denominator cannot be proven by unique duplicate groups,
- duplicate-group label conflict exists for the tested metric,
- requested statistic depends on friction, volatility, footprint, news, macro-attention, FOMC, Cboe, broker actual-R, or synthetic path-R covariates without local as-of/source proof already present,
- no validation-style target was preregistered for this quarantined outcome lane,
- PBO is requested but there are no pre-registered model/variant trials or folds,
- DSR is requested but no Sharpe/return series exists because lifecycle/no-fill labels are not R returns.

## Covariate Boundary

Friction, volatility, footprint, news, macro-attention, FOMC, and Cboe covariates may not be used for source-complete claims unless local as-of/source proof is already present in the accepted packet/control evidence. Otherwise the blocker code is:

```text
BLOCKED_COVARIATE_SOURCE_NOT_RESULT_BLOCKER
```

This blocker does not suppress lifecycle-truth-only descriptive counts.
