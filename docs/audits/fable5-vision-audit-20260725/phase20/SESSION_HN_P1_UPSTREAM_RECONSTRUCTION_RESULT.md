# Session HN — P1 upstream reconstruction result

`execution_authority: false`

`activation_authority: false`

`result_bearing_science_executed: false`

`result_use_status: SOURCE_CONTROL_ONLY_NO_OUTCOME_READ`

## Findings first

**Terminal state: `P1_SOURCE_PACKET_FROZEN_READY_FOR_OFFLINE_RESULT_RUN`.**

The HM defect is constructively closed. The exact predecision M15 source was recovered from the preserved Wave 16 true-UTC rematerialization lane, its lineage and conversion authority were bound, and the commissioned historical P1 market state was reconstructed without outcome-conditioned source selection. The immutable packet covers **73,999/73,999** composite identities across January, April, and May 2026 with zero duplicate tuple keys, zero unmatched identities, zero duplicate generator matches, zero out-of-window identities, and zero postdecision reads.

The packet is content-addressed at:

`/Users/borr/GTOSActive/p1-upstream-source-packet-hold-20260802/p1-source-packet-sha256-e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f`

Its payload root is `e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f`; its external manifest is 34,899 bytes at SHA-256 `cb1d71e38335dcc62eead82916d3576f80f873511a17886818673de3b28b4413`. The compact packet has 51 deduplicated payload files for 24 symbols and occupies 28,995,584 allocated bytes. Its identity-to-slice index is 6,388,815 bytes at `4d70635467fb96c8a5d8c3b37574a97d85b0dbf9f78bb424a53ad538be7c35c5`; its 52,803 unique predecision states are 6,556,568 bytes at `e687f505b563bab2f0a385010a34a1eb56943fea8eb0739d342b043467b72854`.

U2, U4, and U11 are closed. U5 remains honestly `NOT_EVALUABLE_OWNER_INPUT_REQUIRED`; no size, risk, allocation, or owner intent was invented. This packet authorizes only an independent branch decision to start or refuse the separately commissioned offline result lane. It does not authorize or contain an economic verdict.

## Exact source and reconstruction proof

- Tested source commit: `f59fbb829a5561b7e7b78bed324d67a8c01d6e74`, sole parent `1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51`.
- Primary upstream authority: `/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1`.
- Source identity: 24 `bridge_ftmo_m15_20250601_20260610` M15 files, 612,190 total rows, exact file hashes, schemas, bounds, and original-lineage statuses recorded in the search ledger.
- Time authority: textual true UTC produced under `new_york_plus_7` and `src.utils.broker_clock.broker_epoch_to_utc` at SHA-256 `0f97bbb64bc55b0213e47a018c2e884d83b2059b61de7941a171fd3cf2fef552`; filename or apparent UTC labels were not used as authority.
- Generator authority: `src/components/broader_origin_generators.py` at `6e274d22a72c945fa495c2b85408f0495acf6158caa2edb0d34bae108b859fba`, `src/components/market_state.py` at `c59e1d5ea2e4f2758129bca6b67b1ed86379e3278e5c0d44321542425fc680ee`, plus every bound transitive dependency.
- As-of rule: each slice contains only bars fully closed by the identity decision time. Every identity has 672 M15 lookback bars, exceeding the required 51; H1 uses 168 UTC-hour bars.
- Window counts: January 27,658; April 25,056; May 21,285. April raw March antecedent bars are warmup market data only; no March outcome/path payload was read.
- Composite identity was literal throughout. There are 2,357 reused `candidate_id` values covering 17,206 rows, all kept distinct by `(candidate_id, symbol, side, decision_time_utc)`.
- The full independent verifier recomputed H1 aggregation, predecision states, and exact generator identity for all 73,999 rows: 0 H1 mismatches, 0 state mismatches, 0 generator mismatches, 0 postdecision reads.

## Same-evidence-class pursuit

The source-search ledger records ten roots and twelve pursuit actions without a top-N cutoff. It covers the commissioned worktree and its committed/LFS payloads, all relevant Wave 18/19/20 preservation lanes and their direct Wave 16 reference, the Documents M15/H1/H4 exports, the preserved VPS bars, preserved VPS ticks, preserved Hermes evidence, cited package roots, and cold evidence. The Wave 16 rematerialization lane was admitted because it alone supplied the complete hash-bound producing copy with explicit true-UTC conversion authority and all 24 source files. Corroborative, partial, broker-wall, wrong-timeframe, insufficient-window, downstream-only, or forbidden-live roots were rejected with exact reasons. Fifteen dataless original Documents files were not opened and no external download was attempted; nine resident originals matched their expected source hashes.

## Inert control closures

U4 is closed by a sanitized snapshot derived only from committed `agent_config.yaml`, `operator_profile.yaml`, and `redacted_account.yaml`. FTMO carries the later research economic/mechanical inputs; redacted_account is mechanical-only. Account identity, credentials, tokens, runtime paths, live configuration state, and owner risk are excluded.

U11 is closed by a default-off route bundle binding generator, market-state reconstruction, transform, router, capture-only scheduler, HDE, HDF, timeframe/session semantics, candidate identity, fixed family, denominator, and unchanged `ADMIT_UNCHANGED_NOT_ACTIVATION` disposition. Neither HDE nor HDF was executed in HN.

## Verification

- Focused adversarial suite: 15 passed. It covers bad or missing hashes, external tampering, naïve and mixed timebases, DST/clock errors, missing and postdecision bars, insufficient warmup, aliases, duplicate/reused IDs, changed generator bytes, identity multiplicity, deterministic compression, forbidden imports/order paths, and forbidden-window paths.
- Parent A/B by failure set: 1 bad → 0 bad, 1 fixed, 0 regressed. The exact test bytes were run at `1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51` and `f59fbb829a5561b7e7b78bed324d67a8c01d6e74`; the self-contained captures are in `receipts/SESSION_HN_AB_RECEIPT.md`.
- Independent packet verification: PASS across all 51 payloads, 24 symbols, 73,999 identity matches, 52,803 states, and all generator invocations.
- No P1 result run, replay, paper shadow, canary, calibration, optimization, economic gate, broker call, network call, vendor call, runtime write, or production/config mutation occurred.

## Instruction-coverage completion audit

| Context-anchor rule | Closeout enforcement and evidence | Complete |
|---|---|---|
| Exact ancestry; evidence commits excluded | Source commit has the commissioned sole parent; HG/HK/HL/HM were read with exact immutable bytes and recorded as authority-only | yes |
| Sparse/resource envelope | 388-rule hash bound; pre-materialization estimate preserved more than the 8 GiB floor; final disk check is recorded in completion | yes |
| Fixed HG domain | Candidate, family, three windows, denominator, thresholds, and ADMIT disposition are hash-bound and unchanged | yes |
| Source/control only | Allowlisted parsing and command ledger record no outcome or result-bearing use | yes |
| Broker-inert/offline-only | Forbidden-import and call-surface checks are green; no broker, VPS, MetaTrader, runtime, network, or production contact | yes |
| True-UTC authority | Source, manifest, conversion function, DST rule, schema, and bounds are hash-bound; invalid timebases fail closed | yes |
| No postdecision leakage | Closed-bar slice rule plus full independent recomputation proves zero postdecision reads | yes |
| Exact reconstruction semantics | Generator, market state, H1 aggregation, warmup, formation, mitigation, and retest semantics are bound and fully verified | yes |
| Composite identity/multiplicity | 73,999 unique tuple keys; reused candidate IDs explicitly measured and preserved | yes |
| Compact immutable packet | Content-addressed deduplicated series plus identity index; manifest and verifier fail closed on tampering | yes |
| U4/U11; owner-reserved U5 | U4 and U11 closed; U5 literal owner-input terminal retained | yes |
| March/February/live-forward boundary | Path allowlist and adversarial refusal tests are green; only raw March warmup bars were admitted | yes |
| Commit/closeout discipline | Immutable source commit precedes packet; focused suite, full verifier, exact-parent A/B, JSON/compile/diff/fence checks, evidence-only closeout, and clean-state check are recorded | yes |

## Handoff boundary

The next lane must first rerun the independent verifier against the exact external packet path and verify the committed manifest bindings. Only the orchestrator may then start exactly one separately commissioned offline P1 result lane. HN did not launch it and makes no candidate, promotion, activation, or implementation decision from outcome data.
