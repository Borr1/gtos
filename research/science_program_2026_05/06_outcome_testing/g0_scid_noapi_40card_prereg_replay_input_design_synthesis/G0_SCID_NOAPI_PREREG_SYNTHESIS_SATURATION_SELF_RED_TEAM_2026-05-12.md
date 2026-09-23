# G0 SCID No-API Prereg Synthesis Saturation Self-Red-Team

Evidence class: `G0_SCID_NOAPI_40CARD_PREREG_REPLAY_INPUT_DESIGN_SYNTHESIS_ONLY`

## Objective Restatement

Synthesize accepted G12 control evidence into a ranked runnable route bundle while preserving the 40-card denominator and all forbidden-surface boundaries.

## Anti-Boxing Checks Pursued

- Checked that ready 8, blocked 32, and quarantined expansion candidates are routed separately.
- Preserved 33 outside-current-GTOS/OB cards and did not collapse the next route to OB-only.
- Added G0-discovered quarantined route families so the accepted 40 remains a floor, not a ceiling.
- Rejected passive waiting because rank 1 can materialize no-API rowset and target-horizon controls now.
- Rejected the target manifest self-hash mismatch as a fake blocker because G12 classified it nonblocking.

## What Could Break This Lane

- Treating packet readiness as permission to score results: prevented by rank-1 materialization-before-scoring gate.
- Mixing expansion candidates into the accepted 40: prevented by explicit denominator-inclusion=false rows.
- Treating LTF/orderflow unavailable status as terminal: prevented by source-status expansion route.
- Inferring historical lifecycle/order truth from price: prevented by blocked-15 source-state route requirements.
- Hiding behind source-control loops: prevented by rank 1 being a concrete next packet materialization route toward result evidence.

## Deliberately Not Answered

- No outcome/result/R/PnL/win-rate/expectancy/performance scoring was opened.
- No validation, promotion, API, paid source, broker account/order/history/deal/position, raw market blob, live restart, or trading behavior surface was opened.
