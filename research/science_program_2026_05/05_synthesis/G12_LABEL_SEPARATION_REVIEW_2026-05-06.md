# G12 Label-Separation Review - 2026-05-06

**Lane:** `G12`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Label Families Reviewed

G12 reviewed CD2 rows against the G1/G0 label boundary:

- `broker_actual_r`: account-history realized rows with fill and cost evidence;
- `synthetic_path_r`: research-only ordered path comparator labels;
- `lifecycle_no_fill` / `fill_no_fill`: fill, no-fill, cancel, expiry, trigger, and lifecycle states;
- `context_only` / `observation_only`: source, stress, event, eligibility, provenance, and blocker context.

No accepted CD2 row currently opens outcome review. The primary risk is not current registry state; it is future implementation drift.

## Findings

| ID | Scope | Current label boundary | G12 issue | Decision |
|---|---|---|---|---|
| `G12-LABEL-001` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | Primary label class is `lifecycle_no_fill`; short-vol fields are context; spread is context only; synthetic path-R, broker actual-R, and close-side cost are blocked. | Boundary is strong, but future reports must not rank lifecycle buckets by R or treat no-fill as a loss. | Survives as accepted research-only prereg with label-mixing blocker retained. |
| `G12-LABEL-002` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | Primary proposal is `synthetic_path_r`; broker actual-R, lifecycle no-fill, fill/no-fill, observation-only, and context labels remain separate. | Reward contract phrase "realized or path-synthetic R depending on label lane" is too easy to misuse. Future ledgers must use label-specific field names. | Survives as accepted research-only prereg; require lane-specific ledger fields before scoring. |
| `G12-LABEL-003` | CD2-06 prefill/path | Spec separates decision packet, ordered path packet, lifecycle packet, and execution/friction packet. | Current audit shows terminal/cancel context in prefill rows and missing source/candle/tick fields; physical row separation is not yet proven. | Status-only; block any outcome analysis until row-family separation or strict feature whitelist exists. |
| `G12-LABEL-004` | CD2-07 opportunity-cost | Sidecar permits only `context_only` and `observation_only`; forbids actual-R, broker actual-R, synthetic path-R, future returns, TP/SL, post-entry path, and manual financial labels. | "Opportunity cost" can drift into missed-R/dollar value. | Keep as observation-only sidecar; separate prereg required for any value/R outcome. |
| `G12-LABEL-005` | CD2-04 K55 source provenance | Source-status flags may enter K55; raw OFI/depth values and outcome labels are quarantined. | Source readiness flags tied to broker actual-R or candidate floors are not market labels but may be post-outcome readiness metadata. | Keep readiness/floor flags as metadata unless an as-of feature contract explicitly excludes outcome coverage leakage. |
| `G12-LABEL-006` | CD2-05 macro/attention | Proposed canonical row uses `lifecycle_no_fill` only and schedule/event context labels only. | External attention proxies and post-release surprise/text fields are not source-contracted and would create mixed context/outcome labels. | Block master row until source contracts and schedule-only boundaries are machine-readable. |
| `G12-LABEL-007` | G6 normalization residue | G0 normalized 4 verbose G6 label classes in the master copy. | Downstream users could read lane artifacts and bypass the master-normalized `label_class`. | Treat as blocker for promotion citations; future cleanup should patch lane rows or require master-only consumption. |

## Exact Future Label-Cleanup Requirements

| Future artifact | Required label fields |
|---|---|
| CD2-03 risk-bank ledger | Use `synthetic_closed_leg_r`, `synthetic_open_leg_stop_if_hit_r`, and `synthetic_episode_reward_r` for the current prereg. Do not include `broker_actual_*` in the same primary table. |
| CD2-02 lifecycle table | Use `label_family = lifecycle_no_fill`; if spread appears, mark `spread_role = asof_context_only`. |
| CD2-06 packet tables | Use separate tables or explicit fields: `decision_feature_allowed`, `post_decision_path_label`, `lifecycle_label`, `broker_actual_r_claim_allowed`. |
| CD2-07 opportunity rows | Use `label_family_allowed in {context_only, observation_only}` and `forbidden_label_join_attempted=false`. |
| G11 no-leak cleanup | Replace forbidden outcome names in `no_leak_fields`; do not create labels from those names. |

## NO_PROMOTION_VERDICT

No label family is cleared for validation or promotion by this review. The two accepted preregs remain outcome-closed and research-only.
