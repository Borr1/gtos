# GTOS Active Monitoring Checkpoint - 2026-05-04 12:15 UTC

Status: monitoring continues under active goal
Owner: Codex
Scope: 12:15 candle follow pass, shadow integrity warning triage, verifier fix

## Control Plane

- `scripts\_live_monitor_iter.py` at the 12:15 UTC candle: `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- No restart is justified at this checkpoint.

## Follow Pass

`python scripts\follow_live_candidate_paths.py --max-hours 12` completed with:

- `candidates_seen=17`
- `candidate_path_follow` rows written: 17
- `live_mechanical_strategy_shadow_outcomes` rows written: 272
- Resolution/rollup rows written for LTF path order, V2b, prefill, FVG/OB, missed opportunity, opportunity clusters, and candidate strategy rollups.
- Safety flags stayed clean: `no_ai_calls=true`, `no_canary_required=true`, `no_execution=true`, `paid_fetch_attempted=false`, `paid_data_calls=0`.

## Warning Triage

The first 12:15 integrity verifier run returned `CHECK_WARNINGS_PRESENT` with 9 `MODERATE` freshness warnings.

Root cause:

- The verifier used wall-clock freshness for both per-follow logs and candidate-driven source/status ledgers.
- The warned files were candidate-driven ledgers whose latest candidate rows were from about 10:35-10:38 UTC.
- No new live candidate appeared after that, so these ledgers were not supposed to append new source rows.
- The semantic data-health audit stayed clean during the warning: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`.

Affected warning lanes:

- `strategy_follow_candidates.jsonl`
- `v2b_forward_pairs.jsonl`
- `prefill_delivery_path.jsonl`
- `fvg_ob_confluence.jsonl`
- `context_control_ledger.jsonl`
- `live_structural_strategy_metadata.jsonl`
- `databento_live_trigger_decisions.jsonl`
- `sierra_confluence_source_status.jsonl`
- `account_truth_reconciliation_status.jsonl`

Fix:

- `scripts\verify_shadow_log_integrity.py` now has a `freshness_mode` on JSONL specs.
- Candidate-driven source/status ledgers use `freshness_mode="candidate_driven"` and are not wall-clock stale merely because no new candidate appeared.
- Per-follow/path logs still use wall-clock freshness and still warn if the follow writer stops refreshing them.

Validation:

- `python -m pytest tests\test_verify_shadow_log_integrity.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_verify_shadow_integrity` -> `2 passed`.
- `python -m py_compile scripts\verify_shadow_log_integrity.py` -> passed.
- Re-running `python scripts\verify_shadow_log_integrity.py` after the fix returned `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues={}`.
- Re-running `python scripts\audit_live_shadow_data_health.py` returned `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues={}`.

## Current Interpretation

- No capture gap was found at 12:15.
- No row backfill was needed beyond the normal follow writer pass.
- The fix prevents false positives while preserving actual staleness detection for rows that must update each follow cycle.
- Databento remains an explicit waiting lane, not a paid fetch from monitoring/backfill.
