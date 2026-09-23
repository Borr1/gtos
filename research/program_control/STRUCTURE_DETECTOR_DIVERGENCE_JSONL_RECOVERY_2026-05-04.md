# Structure Detector Divergence JSONL Recovery - 2026-05-04

Status: recovered with quarantine
Promotion verdict: `NO_PROMOTION_VERDICT`

`scripts/verify_shadow_log_integrity.py` found one malformed fragment in `shadow_logs/structure_detector_divergences.jsonl`:

- Line: `115`
- Raw fragment: `2}`
- Error: `Extra data: line 1 column 2 (char 1)`

The fragment was not a complete JSON object and could not be safely reconstructed. It has been removed from the live JSONL stream so all valid divergence rows remain parseable, and the raw fragment is preserved in `research/program_control/STRUCTURE_DETECTOR_DIVERGENCE_JSONL_RECOVERY_2026-05-04.json`.

This repair made no AI calls, canary calls, order calls, or paid-data calls.
