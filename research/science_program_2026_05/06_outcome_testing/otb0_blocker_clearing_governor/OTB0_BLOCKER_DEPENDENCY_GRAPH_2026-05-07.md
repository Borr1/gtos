# OTB0 Blocker Dependency Graph - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 outcome tests run:** `false`
**OTB0 paid/API spend:** `$0`

## Packet Counts From OTG0

| OTG0 testing lane | Packets |
| --- | --- |
| broker_actual_r_blocked | 10 |
| control_only | 33 |
| forward_shadow_prospective | 7 |
| lifecycle_no_fill_existing_data_audit | 10 |
| source_asof_cleanup_first | 21 |
| synthetic_replay_existing_data_audit | 16 |

## Dependency Nodes

| Node | Status | Depends on | Purpose |
| --- | --- | --- | --- |
| OTB0 | COMPLETE_AFTER_ARTIFACT_AUDIT | OTG0, OTL1, OTL2, OTL3, G0_G12_OWNER_REVIEW, G12_REVIEW | Convert OTL blockers into executable blocker-clearing lanes. |
| OTB1 | NEXT | OTL1, OTB3_FOR_G11_G5_G7_G8_BLOCKERS | Emit one frozen lifecycle/no-fill input packet per OTL1 experiment. |
| OTB2 | NEXT | OTL2, OTB3_FOR_SOURCE_BLOCKERS | Regenerate or restore non-result synthetic replay packet inputs from local OHLC/path logs. |
| OTB3 | NEXT_PARALLEL_UNLOCKER | OTL3, SOURCE_CONTRACT_REGISTRY, G12_REVIEW | Clear source-path, parser, cache, publication/as-of, no-leak, and source-ref blockers. |
| OTB4 | CONDITIONAL | OTB3_G4_SOURCE_ASSIGNMENTS, FREE_CREDIT_CHECK, PRE_CALL_MANIFEST | Only check cost/credit feasibility for orderflow source packets; no pull unless future approval and free credit sufficiency are proven. |
| OTB5 | CONDITIONAL | OTB3_G5_SOURCE_CLEANUP, OTB1_OR_OTB2_PACKET_SAMPLE, TOKEN_COST_LEDGER | Design-only in OTB0; future pilot stays Sonnet-only, cached, <= $20, and small-sample. |
| G12_BLOCKER_CLEARING_AUDIT | AFTER_OTB1_OTB2_OTB3_OTB4_OTB5 | OTB1, OTB2, OTB3, OTB4_IF_RUN, OTB5_IF_RUN | Audit cleared packets and source/no-leak rewrites before any outcome result lane opens. |

## Edges

| From | To | Reason |
| --- | --- | --- |
| OTG0 | OTB0 | Packet/control rules |
| OTL1 | OTB1 | 10 lifecycle packets all blocked |
| OTL2 | OTB2 | 16 synthetic packets all blocked |
| OTL3 | OTB3 | 21 source/as-of packets all blocked |
| OTB3 | OTB1 | G11/G5/G7/G8 source/no-leak blockers |
| OTB3 | OTB2 | G4/G5/G7 source/no-leak blockers |
| OTB3 | OTB4 | Orderflow source-contract blockers only if local/Sierra insufficient |
| OTB3 | OTB5 | G5 prompt-neutral source/protocol blocker |
| OTB1 | G12_BLOCKER_CLEARING_AUDIT | Lifecycle packets built, outcomes still closed |
| OTB2 | G12_BLOCKER_CLEARING_AUDIT | Synthetic packets built, outcomes still closed |
| OTB3 | G12_BLOCKER_CLEARING_AUDIT | Source/no-leak cleanup artifacts built |

## Execution Order

1. Run `OTB3` source/as-of and no-leak cleanup first or in parallel, because it unlocks both packet-builder lanes.
2. Run `OTB1` to build lifecycle/no-fill packets from local logs after exact field, duplicate, source, and label-separation contracts are frozen.
3. Run `OTB2` to build synthetic replay packets and regenerate missing non-result path inputs from local OHLC/path logs.
4. Run `OTB4` only if G4/orderflow source packets still need Databento feasibility after local/Sierra evidence is exhausted.
5. Run `OTB5` only if G5 prompt-neutral research remains justified after source cleanup and a small frozen packet sample exists.
6. Run the later G12 blocker-clearing audit before any outcome/result lane opens.
