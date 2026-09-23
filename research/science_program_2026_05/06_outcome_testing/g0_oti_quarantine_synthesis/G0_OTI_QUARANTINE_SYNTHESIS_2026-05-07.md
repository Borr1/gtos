# G0 OTI Quarantine Synthesis - 2026-05-07

**Lane:** `G0`  
**Scope:** research-control synthesis of quarantined OTI evidence only  
**HEAD checked:** `4cb74c48`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**New outcomes run:** `false`  
**Blocked-packet outcomes inspected:** `false`

## Bottom Line

OTI1 and OTI2 are usable only as quarantined discovery evidence.

OTI1 proves that the 9 G12-accepted OTB1R lifecycle packets can be counted descriptively without raw-row denominator inflation, forbidden R/result primary fields, blocked-packet pooling, or broker/synthetic label mixing. It does not prove a trading edge, a covariate-conditioned lifecycle effect, a validation statistic, or a promotion path.

OTI2 proves that the single G12-accepted OTB2R G10 risk-bank packet has 86 source-hashed, coverage-bound, duplicate-unique synthetic path rows, and that the initial path distribution can be described after method freeze. It does not prove the risk-bank metric, because the accepted packet lacks leg-level reentry state and numeric risk-bank fields.

G12 correctly accepted both lanes only as `ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE`. That acceptance is methodological, not market validation.

## Evidence Chain

| Stage | Evidence | Finding | Current interpretation |
| --- | --- | --- | --- |
| Live state | `.context/LIVE_STATE.md` generated at HEAD `4cb74c48` | Clean tree before preflight; current research state fresh through G12 OTI audit commit `990980a9` | Use current code/artifacts over old handoffs. |
| Doctrine | `.context/00_core/research_operating_doctrine.md` | Aggressive research, strict promotion; preserve `NO_PROMOTION_VERDICT` absent a separate promotion dossier | OTI outputs can guide next research, not live logic. |
| Master registry | `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md`; `SOURCE_CONTRACT_REGISTRY_2026-05-06.md`; `EXPERIMENT_PREREGISTRY_2026-05-06.json` | 77 mechanisms, 96 hypotheses, 97 preregs, 86 source contracts, 0 survivor rows, 0 `validation_safe=true`, 0 `outcome_review_opened=true` | No registry state authorizes validation or promotion. |
| OTG0 control | `OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`; `OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md` | 97 packet definitions, outcomes closed; lifecycle, synthetic path, broker actual-R, context labels must stay separate | Packet readiness is not result readiness. |
| OTL1/OTL2/OTL3 | `OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.md`; `OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_2026-05-07.md`; `OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_2026-05-07.md` | Initial packet audits blocked all lifecycle/synthetic test implementations and all source/as-of packets | These are historical blocker baselines; later OTB1R/OTB2R cleared a narrow subset. |
| OTB0 | `OTB0_COMPLETION_AUDIT_2026-05-07.md`; `OTB0_PACKET_BUILDER_REQUIREMENTS_2026-05-07.md` | Converted blockers into packet-builder requirements, owner approvals, and source/as-of assignments; no outcomes or spend | Useful dependency map, but its packet status is partly superseded by OTB1R/OTB2R. |
| First G12 blocker audit | `G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.md` | OTB1/OTB2 invalid clearing was rejected due path-label/source-hash and result-bearing source/coverage flaws | Explains why input-only rebuild was required. |
| OTB1R rebuild | `OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.md`; `OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_2026-05-07.md`; `OTB1R_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md` | 9 lifecycle packets rebuilt ready for G12 reaudit; `OTG0-PKT-017` remains blocked; forbidden primary field issues 0; duplicate groups explicit | Cleared prior lifecycle packet-substrate blockers for 9 packets only. |
| OTB2R rebuild | `OTB2R_PACKET_MANIFEST_2026-05-07.md`; `OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.md`; `OTB2R_COVERAGE_AUDIT_2026-05-07.md`; `OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.md` | 1 packet ready for G12 reaudit: `OTG0-PKT-013`, 86 records; other 15 blocked; coverage blocked rows 0; same-bar terminal order not guessed | Cleared prior G10 risk-bank input packet blockers, not the risk-bank result metric. |
| G12 OTB rebuild reaudit | `G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.md`; `G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.md` | 10 packets accepted for future outcome-test packet audit: 9 OTB1R plus 1 OTB2R; 16 still blocked | This is the only packet set OTI1/OTI2 were allowed to use. |
| OTI1 freeze/result | `OTI1_METRIC_FREEZE_2026-05-07.md`; `OTI1_RESULT_LEDGER_2026-05-07.md`; `OTI1_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md`; `OTI1_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.md` | 62 raw rows audit-only, 54 unique packet groups; lifecycle counts 32 still_pending / 22 wrong_side; 0 denominator mismatches, 0 label conflicts, 0 source hash issues | Descriptive lifecycle/no-fill truth only. |
| OTI2 freeze/result | `OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.md`; `OTI2_RISKBANK_RESULT_LEDGER_2026-05-07.md`; `OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md`; `OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.md` | 86 raw rows, 86 unique groups; 51 non-ambiguous descriptive rows mean +0.147037R gross; 85 conservative lower-bound rows mean -0.311778R gross; 34 same-minute ambiguity flags; primary risk-bank metric not computable | Descriptive synthetic path evidence only; the conservative summary warns against overclaiming. |
| G12 OTI post-test audit | `G12_OTI_POST_TEST_DECISION_LEDGER_2026-05-07.md`; `G12_OTI_POST_TEST_NEXT_LANE_RECOMMENDATION_2026-05-07.md` | OTI1 and OTI2 both accepted as quarantined discovery evidence; no rejected or blocked lane-level decisions; exact residual questions recorded | Use in G0 synthesis only as discovery, route blockers to future packet/source lanes. |

## What OTI1 Proves

- The 9 accepted lifecycle packet artifacts can be summarized using unique `duplicate_group_id` denominators, not raw child rows.
- `OTG0-PKT-017` did not enter the accepted OTI1 cohort.
- The accepted lifecycle rows are `lifecycle_no_fill` primary rows, with broker actual-R and synthetic path-R excluded from primary labels.
- The observed lifecycle/no-fill descriptive counts for the accepted packet units are: `32` still pending and `22` wrong side; fill/no-fill counts mirror those as `32` no_fill_still_pending and `22` no_fill_cancelled_wrong_side.
- Covariate source-complete claims remain blocked for friction, volatility, footprint, news, macro-attention, FOMC, and Cboe/short-vol packets.

## What OTI1 Does Not Prove

- It does not prove a lifecycle edge or rejection/entry rule.
- It does not validate a source-conditioned covariate effect.
- It does not satisfy validation effective-N, DSR, or PBO requirements.
- It does not create broker actual-R evidence.
- It does not show that no-fill is a loss; lifecycle labels must not be ranked as R.
- It does not make the 54 packet-level units independent validation trials, because only 11 source duplicate-group units, and 7 source opportunity IDs after prefix unwrap, underlie repeated cross-packet reuse.

## What OTI2 Proves

- The single accepted G10 risk-bank OTB2R packet has 86 source-hashed, coverage-bound, duplicate-unique synthetic path rows.
- All OTI2 result rows are scoped to `OTG0-PKT-013`; blocked OTB2R packets are not opened.
- Label family is synthetic path-R only, with broker actual-R and live trade results outside the lane.
- Same-minute terminal order is not guessed; 34 rows are flagged for same-minute ambiguity and retained as bounded/unresolved evidence.
- The current accepted packet describes initial path outcomes, but not a full risk-bank reentry policy.

## What OTI2 Does Not Prove

- It does not compute the primary risk-bank metric.
- It does not prove reentry, child-leg, structural-lock, or risk-bank state behavior.
- It does not pass the frozen validation floor of 150 unique resolved path rows.
- It does not provide an unseen validation split, CPCV folds, PBO matrix, or DSR-valid return series.
- It does not overcome same-bar terminal-order ambiguity.
- It does not validate the positive non-ambiguous gross mean. The conservative lower-bound mean is negative, and the primary metric is blocked.

## Contradictions And Stale Context Resolved

| Apparent contradiction | Resolution |
| --- | --- |
| OTL1 says all 10 lifecycle packets were blocked, but OTI1 ran 9 packets. | OTL1 was the initial packet-readiness audit. OTB1R later rebuilt sanitized input-only lifecycle packets, and G12 OTB rebuild reaudit accepted 9 of them. The remaining observer packet stayed blocked. |
| OTL2 says all 16 synthetic replay packets were blocked, but OTI2 ran `OTG0-PKT-013`. | OTB2R later rebuilt only the G10 risk-bank packet from sanitized projections. G12 accepted only that one OTB2R packet; the other 15 still have 0 records and exact blocked questions. |
| OTB0 packet-builder requirements list `OTG0-PKT-013` as blocked. | OTB0 is a blocker-governor baseline. OTB2R and G12 OTB rebuild reaudit are later and supersede this one packet status. OTB0 remains valid for required field families and approvals. |
| First G12 blocker clearing rejected OTB1/OTB2, but later G12 accepted OTB1R/OTB2R. | The later accepted packets were rebuilt input-only artifacts that explicitly fixed the prior path-label/source-hash/coverage flaws. |
| OTI2 result ledger lacks an explicit `validation_safe=false` field. | No `validation_safe=true` appears, the method freeze and G12 wrapper carry `validation_safe=false`, and master source/prereg registries remain 0 true. This synthesis carries the flag explicitly. Future result builders should include the flag in every top-level result ledger for easier machine audit. |

## Next-Lane Ranking

Scores are 1 to 5. Higher is better. The order below is the recommended run order, not a promotion ranking.

| Rank | Next lane | Expected edge value | Feasibility | OB-retest independence | Sample readiness | Source/as-of readiness | Decay-defense value | Rationale |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET` | 5 | 4 | 4 | 3 | 5 | 5 | Directly closes OTI2's primary blocker using local packet/log evidence. Risk-bank/path management can improve exits and risk without changing entry selectors. |
| 2 | `OTB1R_OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK` | 4 | 3 | 3 | 3 | 3 | 4 | Converts OTI1 from lifecycle-truth-only counts into source-complete packet slices where possible. Start with local friction/news schedule; leave Cboe/FOMC/legal items blocked if evidence is not local. |
| 3 | `OTB2R_G3_GEOMETRY_INPUT_PACKET_BUILDERS` | 4 | 3 | 5 | 2 | 4 | 4 | DC overshoot/swing/TDA lanes are more substrate-independent than OB retest and likely use local OHLC/geometry. They first need input-only packets, not outcomes. |
| 4 | `OTB2R_G6_LOCAL_OHLC_MOMENTUM_REVERSION_PACKETS` | 4 | 3 | 3 | 2 | 4 | 5 | Opening-drive, exhaustion, round-number, and OB-vs-generic packets may defend against regime decay, but must separate generic retrace from OB-specific denominators. |
| 5 | `OTL3_G4_ORDERFLOW_SOURCE_ASOF_PACKET_DOSSIER` | 5 | 2 | 5 | 2 | 2 | 5 | High edge potential and OB independence, but source/legal/as-of routes are the hard part. Use local/Sierra/cached evidence first; no Databento call unless OTB4 policy gates pass. |
| 6 | `G8_CBOE_VOL_PUBLICATION_ASOF_LEGAL_DOSSIER` | 3 | 2 | 5 | 2 | 1 | 4 | Needed for OTI1 short-vol covariate claims and G8 packets. The blocker is publication/legal/no-lookahead proof, not a market result. |
| 7 | `BROKER_ACTUAL_R_CLOSE_COST_JOIN_PACKET` | 5 | 2 | 4 | 1 | 3 | 5 | Actual-R validation is ultimately highest value, but sample/readiness are still sparse. Build packet joins before any statistic. |
| 8 | `G5_PROMPT_NEUTRAL_SONNET_PILOT_APPROVAL_PACK` | 3 | 2 | 4 | 2 | 2 | 3 | Potentially useful, but requires owner-approved API budget/cache protocol and must remain separate from OTI evidence. |

## Final Verdict

The correct G0 use of OTI1 and OTI2 is a discovery-only evidence section plus a blocker-driven next-lane queue. There is no basis to promote, flip `validation_safe`, open registry outcome review, pool label families, inspect blocked-packet outcomes, or change live trading behavior.
