# G12 Leakage Ledger - 2026-05-06

**Lane:** `G12`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Ledger Summary

G12 finds no accepted CD2 prereg that currently opens outcomes or authorizes a leaky join. G12 does find hard pre-outcome blockers that must remain in force before any future outcome review:

- daily or revised macro/vol rows cannot join by observation date alone;
- G11 no-leak fields are semantically inverted in 8 rows;
- offline RL state/reward metadata must not leak post-action path, fill, or reward-window outcomes;
- source-status flags for K55 must not encode post-outcome sample coverage as predictive features;
- path/lifecycle packets must keep post-decision resolution fields out of decision features.

## Leakage Findings

| ID | Scope | Evidence | Leakage risk | G12 decision |
|---|---|---|---|---|
| `G12-LEAK-001` | CD2-01 COT/FRED/BIS/Cboe/VRP source joins | CD2-01 universal rule requires `feature_asof_utc <= candidate_decision_timestamp_utc`; Cboe same-day publication time, FRED/BIS vintage timing, COT release schedule handling, and VRP realized-window boundaries remain unresolved. | Observation-date or daily-close joins can leak unavailable macro/vol state into M15/H1 decisions. | Hard block outcome review until parser/cache/publication/vintage/no-lookahead tests pass. |
| `G12-LEAK-002` | G11 no-leak semantic inversion | Master registry records 8 G11 hypotheses whose `no_leak_fields` contain `actual_r`, `future_return`, `post_entry_path`, `trade_result`, `future_orderflow`, or equivalent forbidden fields. | Future implementers could misread forbidden outcomes as allowed feature fields. | Hard block registry cleanup/outcome opening; apply CD2-08-style replacement field lists in a future controlled cleanup. |
| `G12-LEAK-003` | CD2-02 short-vol lifecycle prereg | Accepted row excludes same-day Cboe daily rows without `publication_asof_utc`, excludes calendar-date joins, and blocks synthetic path-R, broker actual-R, and close-side cost from the primary lifecycle metric. | If those exclusions are weakened, short-vol context can leak same-day daily vol closes or mix outcome labels. | Row survives as research-only only while blockers remain explicit and `outcome_review_opened=false`. |
| `G12-LEAK-004` | CD2-03 offline RL state fields | Reward contract forbids broker actual-R, path outcomes, TP/SL outcomes, future ticks/candles, and fill outcomes after action as state fields. Registry `HYP-G9-OFFLINE-RL-POLICY-009` still lists `reward_window_start` and `reward_window_end` in `no_leak_fields`. | Reward-window fields are safe only if they are frozen horizon metadata, not observed post-action boundaries or outcome-derived windows. | Before outcome opening, rename/freeze them as `reward_horizon_rule_id` and `reward_horizon_start/end_predeclared_utc`, or keep them in reward metadata outside policy state. |
| `G12-LEAK-005` | CD2-04 K55 source-status flags | CD2-04 forbids raw OFI/depth and outcome labels, but proposed flags include readiness concepts such as broker actual-R floor state and candidate floor state. | Readiness/floor flags can encode post-outcome sample maturity or dataset coverage if used as per-row model features. | Keep outcome-coverage/floor-met flags in audit metadata unless timestamped as-of, global, and excluded from predictive decision vectors. |
| `G12-LEAK-006` | CD2-05 macro/attention event windows | Proposal requires event source cache time, calendar update time, source hash, event publication timestamp, and stale-calendar gate. Current local calendar path mismatch remains unresolved. | Event labels can be created from calendars updated after the candidate decision or from post-release surprise/narrative fields. | Block master row and outcome opening until source path, hash, cache timestamp, stale threshold, and schedule-only field list are frozen. |
| `G12-LEAK-007` | CD2-06 prefill/path packets | G10 audit says decision rows pass no-post-outcome status, but current prefill rows also contain terminal/cancel context and lack ordered prefill candles/ticks/source hashes. | Terminal lifecycle fields or post-decision path labels can be consumed as decision features if row-family boundaries are not physical. | Require separate decision, ordered-path, lifecycle, and execution/friction packets or a strict feature whitelist before any model/outcome use. |
| `G12-LEAK-008` | CD2-07 opportunity-cost sidecar | Sidecar forbids R/PnL/path labels and keeps `outcome_review_opened=false`. Source map is prop/correlation/stress context only. | "Opportunity cost" wording can drift into missed-R or financial value estimates after blocked/halved/skipped candidates are known. | Keep observation-only counts; require a separate outcome-bearing prereg before any missed-R or financial value calculation. |
| `G12-LEAK-009` | G6 normalization residue | Master copy normalized 4 G6 `label_class` values, while lane artifacts retain verbose values such as `synthetic_path_r_separated_from_broker_actual_r`. | Downstream consumers may rely on lane files and bypass the master normalization. | Future cleanup should either patch G6 lane rows or require consumers to use master registry plus normalization ledger only. |

## Required No-Leak Corrections For Future Registry Cleanup

| Row | Current issue | G12 future correction |
|---|---|---|
| `HYP-G11-PROVENANCE-GATE-001` | `no_leak_fields` lists `outcome_r`, `win_loss`, `future_price`, `post_entry_path`, `trade_result`. | Replace with source provenance/as-of fields from CD2-08; move forbidden names to blockers/test-method text. |
| `HYP-G11-COVERAGE-GATE-002` | Lists `actual_r`, `trade_outcome`, `future_return`, `post_signal_continuation`. | Replace with coverage-manifest/as-of fields; no outcome labels. |
| `HYP-G11-SOURCE-TRANSFER-003` | Lists `actual_r`, TP/SL hit, and post-entry path fields. | Replace with source-transfer alignment/missingness/lead-lag as-of fields. |
| `HYP-G11-PUBLIC-LAG-004` | Lists post-release revision/future release/outcome fields. | Replace with release/vintage/cache/decision timestamp fields. |
| `HYP-G11-OPTIONS-VOL-005` | Lists future vol index and outcome fields. | Replace with vol source publication/cache/license/history/as-of fields. |
| `HYP-G11-OBSERVER-EXPANSION-006` | Lists actual-R/win-loss/post-signal path fields. | Replace with observer enabled/source freshness/friction/session eligibility fields. |
| `HYP-G11-FRICTION-GATE-007` | Lists future return/outcome/path fields. | Replace with predecision friction manifest, spread/ATR, tick value, contract spec, and version fields. |
| `HYP-G11G4-SOURCE-GATED-ORDERFLOW-008` | Lists actual-R/trade result/post path/future orderflow. | Replace with source contract, provenance, proxy-transfer, label-separation, budget/license state, and review timestamp fields. |

## NO_PROMOTION_VERDICT

This leakage ledger opens no outcome review and does not clear any source, feature, policy, or strategy for promotion.
