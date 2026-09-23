# G12 Duplicate-Counting Review - 2026-05-06

**Lane:** `G12`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Registry-Level Duplicate Check

G0 CD2 reconciliation reports duplicate mechanism, hypothesis, experiment, and source IDs as zero. G12 accepts that as a registry-inventory check, not as proof that future analyses will count independent observations correctly. The remaining duplicate risk is analytic: child rows, lifecycle attempts, retries, repeated pending checks, same setup overlaps, event clusters, and source-status rows can still inflate `n` or effective-N.

## Duplicate-Counting Findings

| ID | Scope | Evidence | Duplicate risk | G12 decision |
|---|---|---|---|---|
| `G12-DUP-001` | CD2-02 short-vol lifecycle prereg | Primary independent unit is earliest eligible `setup_id + intended_limit_price + symbol + session`; retries/order attempts/repeated checks are child rows. | Lifecycle checks and order attempts can inflate event counts if child rows are treated as independent. | Duplicate policy is acceptable for prereg survival; require implementation tests before outcome opening. |
| `G12-DUP-002` | CD2-03 offline RL | Episode unit is one deduped setup/opportunity lifecycle; legs, retries, re-evaluations, and pending lifecycle children are child rows. | Reentry legs can appear as independent trades and overstate sample size/reward. | Accepted row survives only if episode-level `duplicate_group_id` is mandatory before scoring. |
| `G12-DUP-003` | CD2-05 macro/attention proposal | G5 resolves duplicate G5/G7 interaction rows into one future canonical prereg and clusters by `event_id`, attention window, symbol, session, and month. | The same FOMC/macro event can generate many correlated candidate rows and matched controls. | Blocked from master until canonical ID and event-cluster effective-N policy are machine-readable. |
| `G12-DUP-004` | CD2-06 prefill/path audit | G10 audit reports 76 current prefill rows but only 12 primary unique opportunities; 63 are duplicate active setups and 1 same-symbol overlap. Continuation/no-retrace has 22 rows but only 2 primary countable rows. | Raw counts are unusable for inference; most rows are duplicates or overlaps. | Status-only. Any future analysis must report primary-countable n, duplicate exclusions, and effective-N separately from raw rows. |
| `G12-DUP-005` | CD2-07 portfolio opportunity-cost sidecar | Sidecar clusters by setup, stress episode, prop-firm server day, symbol, and correlation group. | Correlated blocked/halved/skipped candidates during one stress day can look like many opportunities. | Observation-only counts survive; no R/opportunity-value denominator can open without clustering tests. |
| `G12-DUP-006` | G4/K55 source-status flags | CD2-04 maps many source-status logs to K55 flags. | Repeated source-status heartbeats or global readiness rows can be duplicated across many candidates and treated as independent predictive evidence. | Use source-status rows as provenance/audit metadata unless joined by stable as-of keys and de-duplicated by source signature. |
| `G12-DUP-007` | G11 source placeholders and literature refs | G0 reports 18 source-reference issues, including literature references reused across rows and hypothesis IDs in `source_ids`. | Literature/context rows can be counted as multiple independent source confirmations. | Keep outside validation-safe source counts; move to `evidence_refs` or dependency fields. |

## Effective-N Requirements Before Any Future Outcome Review

| Row or family | Minimum duplicate-control requirement |
|---|---|
| `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | Deduped lifecycle n, week-clustered effective-N, stale-source rate, and short-vol bucket minimums. |
| `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | Stable `episode_id`, `duplicate_group_id`, child-leg table, and held-out episode count after dedupe. |
| CD2-05 future canonical macro/attention row | One lifecycle observation per setup/event/window/symbol/date plus event-cluster effective-N. |
| CD2-06 future path analysis | Primary countable setup n, duplicate active setup exclusions, same-symbol overlap exclusions, and path ambiguity counts. |
| CD2-07 future observation rows | Clustering by prop-firm server day, stress episode, symbol, and correlation group. |

## NO_PROMOTION_VERDICT

This review validates no lift and no sample floor. Duplicate controls are necessary blockers, not evidence of readiness.
