# OTB2R G6 Local-OHLC Packet Manifest - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

This lane built input-only G6 local-OHLC packets. No outcome review, replay
result, broker actual-R, paid/API/Databento, MT5/order, registry edit, or live
trading surface was opened.

## Summary

- Packets: `5`
- Records: `310`
- Unique duplicate groups: `74`
- Decisions: `{'INPUT_PACKET_BUILT_WITH_EXACT_LIMITATION_LEDGER': 2, 'INPUT_PACKET_BUILT_PARTIAL_FORWARD_SOURCE_BLOCKED': 1, 'INPUT_PACKET_BUILT_SOURCE_HASHED_NO_OUTCOMES': 2}`

| Packet | Experiment | Family | Decision | Records | Unique duplicate groups |
| --- | --- | --- | --- | --- | --- |
| OTG0-PKT-060 | G6-EXP-001-OB-VS-GENERIC-RETRACE | ob_vs_generic_retrace | INPUT_PACKET_BUILT_WITH_EXACT_LIMITATION_LEDGER | 80 | 20 |
| OTG0-PKT-061 | G6-EXP-002-CONTINUATION-NO-RETRACE | impulse_pullback_no_retrace | INPUT_PACKET_BUILT_PARTIAL_FORWARD_SOURCE_BLOCKED | 51 | 8 |
| OTG0-PKT-062 | G6-EXP-003-OPENING-DRIVE-CONTINUATION | opening_drive_continuation | INPUT_PACKET_BUILT_SOURCE_HASHED_NO_OUTCOMES | 86 | 19 |
| OTG0-PKT-063 | G6-EXP-004-EXHAUSTION-CHANGEPOINT | exhaustion_changepoint | INPUT_PACKET_BUILT_SOURCE_HASHED_NO_OUTCOMES | 86 | 21 |
| OTG0-PKT-066 | G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE | gold_round_ob_confluence | INPUT_PACKET_BUILT_WITH_EXACT_LIMITATION_LEDGER | 7 | 6 |
