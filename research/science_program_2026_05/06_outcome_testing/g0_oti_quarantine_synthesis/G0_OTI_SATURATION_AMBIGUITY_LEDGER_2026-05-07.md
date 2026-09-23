# G0 OTI Saturation And Ambiguity Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Purpose:** prove what was checked, what was answered, and why further local pursuit is exhausted without new packet/source work

## Saturation Log

| Search/inspection | Scope | Finding | Saturation result |
| --- | --- | --- | --- |
| Mandatory preflight | `generate_live_state.py`, `.context/LIVE_STATE.md`, latest handoff, quick reference, doctrine, current state, reading order | HEAD `4cb74c48`, research state fresh through G12 OTI audit | Preflight complete; current state controlled. |
| Artifact inventory | `06_outcome_testing/` OTI, OTB, OTL, OTG0, G12 dirs | Located G12 OTI, OTI1, OTI2, G12 OTB, OTB1R, OTB2R, OTL1/2/3, OTB0, OTG0 artifacts | No missing local controlling directory for this synthesis. |
| G12 OTI decision read | `G12_OTI_POST_TEST_DECISION_LEDGER_2026-05-07.md/json` and next-lane recommendation | OTI1 and OTI2 accepted only as quarantined discovery evidence | Final decision boundary answered. |
| OTI1 result read | Metric freeze, result, methodology, duplicate, label, ambiguity, blocker, completion audit | OTI1 lifecycle counts and blockers reconstructed | No further OTI1 result evidence needed absent new source/as-of packet. |
| OTI2 result read | Method freeze, result, source/coverage, methodology, ambiguity, blocker, completion audit, row JSONL | OTI2 path labels and primary risk-bank blockers reconstructed | No further OTI2 evidence can compute risk-bank metric without missing fields. |
| OTB1R/OTB2R read | Rebuild ledgers, schema/no-leak, duplicate, source hash, coverage, same-bar, completion | Rebuild status and exact accepted packet substrate verified | Later G12 OTB acceptance fully explained. |
| OTL1/OTL2/OTL3 comparison | Initial audits and source/as-of triage | Initial all-blocked status superseded only for 9 OTB1R plus 1 OTB2R packet | Stale-context contradiction resolved. |
| OTB0 comparison | Completion, builder requirements, owner approval, Databento policy | OTB0 remains valid as blocker plan but partly superseded by OTB1R/OTB2R status | Use OTB0 for rules/approvals, not latest packet status. |
| Master registry parse | Source registry and experiment preregistry JSON | 86 source rows, 0 `validation_safe=true`; 97 preregs, 0 `outcome_review_opened=true` | Registry safety boundary confirmed. |
| OTI2 row parse | `OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl` | 86 rows, all `OTG0-PKT-013`; forbidden hits total 0 | Blocked-packet pooling concern answered for accepted OTI2 rows. |
| Primary-row forbidden key scan | 26 OTB1R/OTB2R packet files | 0 primary-row forbidden key issues | Hidden result-key leak not found in primary packet rows. |
| Scoped true-flag scan | OTI/G12/OTB1R/OTB2R dirs | No actual true flip found; matches are prohibitive text or code issue labels | `validation_safe=false` and `outcome_review_opened=false` preserved. |

## Ambiguity Ledger

| Ambiguity | Status | Evidence answer or blocker | Exact next need |
| --- | --- | --- | --- |
| Which packets can OTI1 use? | `ANSWERED` | `OTI1_METRIC_FREEZE_2026-05-07.md` and G12 accepted shortlist restrict OTI1 to 9 accepted OTB1R lifecycle packets | None for current synthesis. |
| Did OTI1 include blocked `OTG0-PKT-017`? | `ANSWERED` | OTI1 freeze excludes `OTG0-PKT-017`; builder contains a guard against that packet entering accepted set | None. |
| Which packet can OTI2 use? | `ANSWERED` | OTI2 method freeze restricts scope to `OTG0-PKT-013`; local parse of row ledger found only that packet ID | None. |
| Did OTI2 inspect blocked-packet outcomes? | `ANSWERED` | G12 OTI, OTI2 result ledger, and local row parse show blocked-packet outcomes inspected false and no blocked packet IDs in OTI2 row ledger | None. |
| Are OTL1/OTL2 blockers contradicted by OTI1/OTI2? | `ANSWERED_STALE_SEQUENCE` | OTL1/OTL2 were earlier packet-readiness audits. OTB1R/OTB2R and G12 OTB rebuild reaudit are later and narrower | Preserve chronology in future summaries. |
| Did OTB0's blocked status for G10 remain current? | `ANSWERED_STALE_SEQUENCE` | OTB0 predates OTB2R. It remains a requirements map, while OTB2R/G12 OTB accepted `OTG0-PKT-013` | Do not cite OTB0 as current G10 status. |
| Are OTI1 packet counts independent validation units? | `ANSWERED_WITH_LIMITATION` | OTI1 duplicate report: 54 packet/cross-packet groups, 11 source duplicate-group units, 7 source opportunity IDs | Need prospective independent units for validation. |
| Can OTI1 compute DSR/PBO/raw p? | `ANSWERED_NOT_COMPUTABLE` | OTI1 result/methodology: no return series, no null/alternative, no variant/fold matrix | Future prereg with target rate and independent sample if desired. |
| Can OTI1 make covariate-conditioned claims? | `BLOCKED` | OTI1 blocker ledger lists friction, volatility, footprint, news, macro-attention, FOMC, Cboe blockers | Packet-bound source/as-of proof per covariate. |
| Can OTI2 compute primary risk-bank metric? | `BLOCKED` | Missing leg-level reentry and risk-bank fields in OTI2 methodology/blocker ledger | Future frozen G10 leg-ledger input packet. |
| Can OTI2 use the non-ambiguous +0.147037R mean as edge evidence? | `ANSWERED_NO` | OTI2 says descriptive only; conservative lower-bound mean is -0.311778R and primary metric is not computable | No promotion language; build risk-bank packet first. |
| Can same-minute ambiguous rows be resolved locally now? | `BLOCKED` | OTB2R/OTI2 same-bar policy prohibits terminal-order guessing; 34 rows flagged | Tick-order evidence or frozen conservative scoring policy. |
| Are source hashes and coverage clean for OTI2 accepted packet? | `ANSWERED` | OTI2 source report: packet hash match true, row source hash failures 0, coverage failures 0 | None for accepted packet; other 15 packets still blocked. |
| Are forbidden result fields hidden in primary packet rows? | `ANSWERED` | Local primary-row scan over 26 OTB1R/OTB2R packet files found 0 forbidden primary-row key issues | Future builders should keep the same scan. |
| Does OTI2 result ledger explicitly carry `validation_safe=false`? | `PARTIAL_FORMAT_GAP_NOT_FLAG_FLIP` | OTI2 method freeze and G12 wrapper carry false; result ledger has no explicit `validation_safe` key; no true flip exists | Future builders should put `validation_safe=false` in every top-level result payload. |
| Are source/legal/as-of questions answerable without web? | `MOSTLY_BLOCKED` | OTL3 gives local classifications and exact source questions; Cboe/FRED/BIS/WGC/FlashAlpha need source-specific evidence | Use local cache first; official webfetch/curl only when necessary and save raw/source index. |
| Should master registries be patched now? | `ANSWERED_NO` | Objective forbids master registry edits except proposed patch artifacts; master flags remain false/closed | Future G0/G12 patch proposal only if explicitly requested. |
| Is broker actual-R validation available from OTI1/OTI2? | `ANSWERED_NO` | OTG0 and G12 label boundaries separate broker actual-R; OTI1/OTI2 do not inspect account-history R | Separate broker actual-R packet lane required. |

## Exhaustion Statement

All local artifacts needed to reconstruct the chain from preregistration to packet build to quarantine result to G12 OTI decision were read or mechanically checked. The remaining uncertainties are not answerable by more local summarization:

- OTI2 needs fields absent from accepted packet rows.
- OTI1 covariates need source/as-of proof not present in accepted lifecycle packets.
- Fifteen OTB2R synthetic packets have zero rebuilt records.
- Broker actual-R validation requires a separate account-history/cost packet.
- Source legality/publication/as-of questions require source-specific dossiers and, where local cache is insufficient, approved official fetches.

Further local pursuit without building new packets or source dossiers would only restate the same blockers.
