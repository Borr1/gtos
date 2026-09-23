# G0 SCID Parallel G12 Integration Decision Ledger - 2026-05-12

## Decision

`ACCEPT_AS_G0_PARALLEL_G12_INTEGRATION_FOR_ADDITIVE_IMPLEMENTATION_SEQUENCE`

This integrates the completed parallel G12 wave into `main` and selects the next route:

`SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_FROM_ACCEPTED_PARALLEL_G12_WAVE`

This is not a performance route. It is the bridge from accepted source/control design into additive source-capture implementation so future replay and hypothesis cards stop lacking strategy-intent/source-state fields.

## What Was Actually Reviewed

The orchestration review was not chat-summary-only. The accepted artifacts were read from disk, focused tests/verifiers were rerun where practical, the sibling branches were reconciled into `main`, and the one real verifier CLI weakness found during review was repaired:

- No-API hypothesis factory verifier now honors `--mark-focused-tests-ok`.
- Clean no-API closeout is committed in `cd961ed7`.
- Main now contains the parallel branch artifacts through merge commits `44214c21`, `2f8c63d2`, `882af807`, `6a556595`, and `91f34abe`.

## Integrated Evidence Lanes

| Lane | Terminal Decision | Useful Result |
|---|---|---|
| Live forward evidence capture hardening | `ACCEPT_AS_G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_CONTROL_EVIDENCE` | FVG/OB exact geometry/backfill and maintenance hardening accepted; 287 targeted tests passed. |
| SCID implementation design | `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_CONTROL_EVIDENCE_ONLY` | Owner-gated additive patch design accepted for 3,014 candidates and 10 capture groups. |
| Synthetic runtime harness | `ACCEPT_AS_G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_CONTROL_EVIDENCE_ONLY` | Synthetic harness accepted with 109 fixture cases and 117 fixture rows. |
| Readonly monitoring alignment | `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_CONTROL_EVIDENCE_ONLY` | Source/root saturation and capture requirement mapping accepted. |
| No-API hypothesis factory | `ACCEPT_AS_G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_CONTROL_EVIDENCE_ONLY` | 40 cards accepted across 8 science domains; 33 cards are outside current GTOS/OB framing. |
| LTF/orderflow proxy expansion | `ACCEPT_AS_G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_CONTROL_EVIDENCE_ONLY` | 844 sources, 12 categories, proxy validity and as-of gates accepted. |

## Next Route Standard

The next implementation route must be aggressive within additive evidence-capture implementation scope:

- Do not stop at missing fields if a repo-local additive logger/parser/fixture/verifier can be built.
- Do not reduce the work to a paper plan if the accepted design can be implemented safely as additive evidence capture with no decision/execution impact.
- Do not box the route to old OB-only thinking; preserve the 40-card hypothesis factory and LTF/orderflow source-expansion needs as first-class downstream consumers.
- Do not open validation, performance claims, AI/API calls, paid/vendor calls, unredacted broker reads, broker-realized performance scoring, or trading-behavior changes in this implementation step.
- Read-only redacted broker/account/order/deal/history state capture is allowed if needed to close source/lifecycle evidence, provided it is provenance-tagged, non-scoring, and cannot place, modify, or cancel orders.
- Controlled restarts are allowed if needed to load additive capture/logging changes; restart only affected process groups, record pre/post health, and verify row landing.
- Emit a G12 implementation audit prompt after implementation.

## Current Boundaries

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
