# G0 OTI Blocker And Action Map - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Scope:** blockers and next actions only; no new outcomes

## Active Blockers

| Blocker ID | Area | Blocking fact | Evidence | Exact missing file/source/field/approval | Next action |
| --- | --- | --- | --- | --- | --- |
| `G0-OTI-BLK-001` | OTI2 risk-bank primary metric | Accepted packet lacks leg-level reentry/risk-bank ledger fields | `OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.md`; `OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.md` | Future frozen input packet with `leg_id`, `reentry_state`, `structural_lock_event`, `risk_bank_before_action_r`, `risk_bank_after_action_r`, `realized_closed_leg_r`, `open_leg_stop_if_hit_r`, numeric `estimated_remaining_cost_r` | Build a G10 risk-bank leg-ledger input-only packet. |
| `G0-OTI-BLK-002` | OTI2 terminal order | 34/86 rows have same-minute ambiguity and terminal order cannot be claimed | `OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.md`; `OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.md` | Tick-order evidence or a predeclared conservative-bound scoring policy | Add tick-order evidence if local logs exist; otherwise freeze a conservative scoring policy before any new outcome read. |
| `G0-OTI-BLK-003` | OTI2 validation statistics | 86 accepted groups below frozen 150 validation floor; no unseen split or variant matrix | `OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.md`; `OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.md` | Additional prospectively separated resolved path rows or owner-approved pre-frozen floor change; CPCV/train-test design | Do not compute DSR/PBO. Build packet quality first, then collect forward rows. |
| `G0-OTI-BLK-004` | OTI1 covariate claims | Lifecycle truth is present, but source-complete covariates are not packet-bound | `OTI1_BLOCKER_LEDGER_2026-05-07.md`; `G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.md` | Packet-bound as-of proof for friction, realized-vol/vol-of-vol, footprint/absorption, news, macro-attention, FOMC, Cboe short-vol | Build source/as-of proof packs per covariate, not a pooled result. |
| `G0-OTI-BLK-005` | OTI1 denominator independence | 54 packet groups collapse to 11 source duplicate-group IDs and 7 source opportunities | `OTI1_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md` | Independent source cohort or duplicate policy proving cross-experiment independence | Treat OTI1 portfolio rollup as repeated-packet discovery, not validation. |
| `G0-OTI-BLK-006` | Observer lifecycle packet | `OTG0-PKT-017` has 0 rebuilt lifecycle rows | `OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.md`; `G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.md` | Dedicated observer lifecycle logger or decision to keep observer expansion outside lifecycle/no-fill packet testing | Build observer lifecycle packet only if owner wants that lane; otherwise keep blocked. |
| `G0-OTI-BLK-007` | Other OTB2R synthetic packets | 15 synthetic packets have 0 rebuilt input-only path records | `OTB2R_PACKET_MANIFEST_2026-05-07.md`; `G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.md` | Source-specific input-only packet builders with source_hash, duplicate_group_id, decision_asof_utc, ordered_path_source_id, cost_model_version, same_bar policy | Prioritize local OHLC/geometry/G6 packet builders before source-hard G4/G8/G7 packets. |
| `G0-OTI-BLK-008` | Source/as-of legality and timing | G7/G8/G4/G5 sources are mostly blocked or context-only | `OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_2026-05-07.md`; `SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | Official/vendor source selection, cache/raw hash, parser version, publication_asof rule, license/access state, no-lookahead fixtures | Run source-specific source/as-of cleanup dossiers; use webfetch only for official source evidence when local cache is insufficient. |
| `G0-OTI-BLK-009` | Broker actual-R validation | No OTI lane provides account-history realized-R validation | OTG0 controls; master registry; OTI label audits | Candidate-to-account-history join, fill/cost/close-side fields, sample floor, manual-trade exclusion, label-family separation | Build a separate broker actual-R packet lane; do not mix with OTI1/OTI2. |
| `G0-OTI-BLK-010` | Master registry mutation | All master rows remain outcome closed and source validation unsafe | Master registry, source registry, preregistry parses | Owner approval plus separate patch/dossier if any registry row is to be edited | Do not edit master registries in this lane; emit proposed patch artifacts only if requested later. |

## Recommended Action Order

| Rank | Action | Why first or later | Expected output | Forbidden in action |
| ---: | --- | --- | --- | --- |
| 1 | Build `OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET` | Closes OTI2's central blocker and uses the already accepted G10 packet scope | Input-only leg/risk-bank packet plus no-leak/source/duplicate/same-bar audit | No outcome scoring, no blocked OTB2R packets, no live logic |
| 2 | Build `OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK` for local-ready covariates | Turns OTI1's source-complete blockers into answerable packet-bound questions | Per-covariate source/as-of proof or exact blocker ledger | No covariate-conditioned result claim |
| 3 | Build `OTB2R_G3_GEOMETRY_INPUT_PACKETS` | Local geometry is likely feasible without paid/source legal blockers and is less OB-dependent | DC/TDA input-only packets with duplicate/source/as-of contracts | No synthetic outcome opening |
| 4 | Build `OTB2R_G6_LOCAL_OHLC_PACKETS` | Momentum/reversion and opening-drive lanes defend against OB decay if packetized cleanly | G6 packet builders for local OHLC families | No generic-vs-OB denominator pooling |
| 5 | Run `OTL3_G4_ORDERFLOW_SOURCE_ASOF_DOSSIER` | High potential but source-hard; must clear source legality/as-of first | Source contracts and packet-readiness map for local/Sierra/cached orderflow | No Databento call unless OTB4 policy gates pass |
| 6 | Run `G8_CBOE_PUBLICATION_ASOF_LEGAL_DOSSIER` | Needed for short-vol lifecycle and G8 packets, but legal/timing evidence is the blocker | Cboe parser/publication/legal/no-lookahead dossier | No same-day daily data use without proof |
| 7 | Build `BROKER_ACTUAL_R_CLOSE_COST_JOIN_PACKET` | Highest validation value, lower immediate sample readiness | Broker actual-R packet contract and sample/readiness audit | No pooling with synthetic/lifecycle labels |
| 8 | Prepare `G5_PROMPT_NEUTRAL_OWNER_APPROVAL_PACK` | Requires explicit API budget/caching protocol | Frozen prompt hashes, sample, cost estimate, owner decision points | No API calls before approval |

## Dependency Notes

- OTI2 leg-ledger packet construction should run before any new G10 risk-bank outcome result. The existing OTI2 result already shows the primary metric is not computable.
- OTI1 covariate work should be split by source family. Local friction/news schedule can be attempted before FOMC/Cboe/legal dossiers.
- G3/G6 packet builders are attractive because they may reduce dependence on OB-retest and use local data, but they still need packet field completeness before outcome opening.
- G4 orderflow and G8 volatility are potentially high edge-value lanes, but their source/as-of and legal readiness are the limiting factor.
- Broker actual-R work should stay separate. It is not an OTI1/OTI2 extension.

## Owner/Access Requirements

| Requirement | Current state |
| --- | --- |
| Direct master registry edits | Not approved in this lane |
| Webfetch/curl source verification | Allowed only for official source-contract evidence when local cache is insufficient; raw response and source index must be saved |
| Databento calls | Conditional future OTB4 only; existing free credits, pre-call manifest, and $0 paid-spend proof required |
| G5 Sonnet prompt-neutral pilot | Conditional future pilot only; $20 cap, no Opus, cached calls, frozen prompt hashes |
| Live trading prompts/risk/execution/selectors/MT5/canaries | Not approved and out of scope |
