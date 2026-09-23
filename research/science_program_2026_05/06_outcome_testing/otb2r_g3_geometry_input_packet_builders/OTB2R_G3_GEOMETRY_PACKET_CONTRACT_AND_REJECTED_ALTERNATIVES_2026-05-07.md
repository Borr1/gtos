# OTB2R G3 Packet Contract And Rejected Alternatives (2026-05-07)

- promotion_verdict: NO_PROMOTION_VERDICT

## Accepted Contract

- Source family: shadow_logs/candidate_features_log.jsonl + local closed OHLC CSVs
- Reason: candidate_features_log contains input-side CANDIDATE rows and no outcome/path-order resolution fields; local OHLC provides point-in-time geometry windows for covered decisions.
- Label family: `synthetic_path_r` with label values absent.
- Cost model version: `INPUT_ONLY_NO_REPLAY_COST_MODEL_V0`.
- Same-bar policy: `G3_INPUT_ONLY_CLOSED_CANDLE_POLICY_V1`.

## Rejected Alternatives

- `REJECTED_AS_PRIMARY_G3_FEATURE_SOURCE`: Use only the 86 accepted OTB2R path rows from candidate_ltf_path_order projections - Those rows answer path-order source existence, not DC/TDA pre-decision feature construction. Many decisions are 2026-05-03 to 2026-05-06 after local OHLC coverage and some LTF rows are SOURCE_BLOCKED.
- `REJECTED_FOR_POLICY`: Open V2/V3 forward pair resolution or path-scaling replay ledgers - Those files are result-bearing synthetic path/replay ledgers and may expose terminal order, hit TP/SL, or path-R values.
- `REJECTED_FOR_POLICY`: Use broker account/trade record actual-R files to backfill labels or terminal order - Broker actual-R is forbidden for this OTB2R input-only builder and remains absent from primary metric fields.
- `REJECTED_AS_DATA_SOURCE`: Use prior blocked G3 packet records - Prior OTB2R G3 packets contain zero rebuilt records; their file hashes are retained only as control evidence.
- `REJECTED_FOR_SCOPE`: Fetch public DC/TDA examples or market data from the network - G3 source contract allows methodology context only; this lane uses local market evidence and performs no network/API/data purchase.
- `REJECTED_FOR_NO_LEAK`: Use same-bar terminal path assumptions to fill unavailable synthetic replay fields - This builder computes only pre-decision geometry. Same-bar policy is recorded as input-only and never claims terminal order.

## Packet Paths

- `OTG0-PKT-031`: `research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/packets/OTG0-PKT-031__EXP-G3-DC-OVERSHOOT-002__otb2r_g3_dc_overshoot_input_packet_2026-05-07.json`
- `OTG0-PKT-032`: `research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/packets/OTG0-PKT-032__EXP-G3-DC-SWING-001__otb2r_g3_dc_swing_input_packet_2026-05-07.json`
- `OTG0-PKT-036`: `research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/packets/OTG0-PKT-036__EXP-G3-TDA-007__otb2r_g3_tda_h0_embedding_input_packet_2026-05-07.json`
