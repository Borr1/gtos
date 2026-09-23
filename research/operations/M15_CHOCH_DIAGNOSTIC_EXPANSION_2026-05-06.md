# M15 CHoCH Diagnostic Expansion - 2026-05-06

## Objective

Expand `m15_choch_exists` diagnostics before any continuation/no-retrace strategy work.
This phase does not loosen the L2 gate and does not change live order, risk,
prompt, permissions, execution, canary, or safety-gate behavior.

Promotion verdict: `NO_PROMOTION_VERDICT`

## Evidence Read

- Goal prompt: `.context/05_operations/NEXT_IMPROVEMENTS_AND_LTO031_032_GOAL_PROMPT_2026-05-06.md`
- Monitoring synthesis: `research/operations/GTOS_OWNER_DEEP_DIVE_MONITORING_SYNTHESIS_2026-05-06.md`
- L2 gate implementation: `src/components/verification.py`
- Forward candidate capture: `src/research_infra/forward_capture.py`
- Candidate path follow rows: `shadow_logs/candidate_path_follow.jsonl`
- Opportunity cluster rows: `shadow_logs/live_candidate_opportunity_clusters.jsonl`
- Existing candidate rows: `shadow_logs/strategy_follow_candidates.jsonl`

## Code Findings

- `m15_choch_exists` already records the immediate L2 reason in verification
  checks. For failures, the common detail is no M15 CHoCH/BOS with displacement
  for the required direction.
- `displacement_ratio` is correctly skipped when no qualifying M15 event exists.
  That means the diagnostic must preserve the dependency, not treat the skipped
  ratio as an independent failure.
- Later path truth is recorded separately in `candidate_path_follow` and must be
  joined post-decision. It is not available at decision time and cannot be used
  as a gate feature.
- Duplicate/opportunity truth is recorded separately in
  `live_candidate_opportunity_clusters` and is required so repeated XAGUSD rows
  are not counted as independent trade opportunities.

## Implementation

- Added `src/research_infra/m15_choch_diagnostics.py`.
  - Builds decision-time diagnostics from recorded verification checks.
  - Builds append-only post-decision audit rows for `m15_choch_exists` failures.
  - Joins latest candidate path and opportunity cluster rows by `candidate_id`.
  - Emits no-leak, no-AI, no-canary, no-execution, no-paid-data flags.
- Updated `src/research_infra/forward_capture.py`.
  - Future `strategy_follow_candidate_v1` rows now include
    `m15_choch_diagnostic`.
  - Verification summaries now preserve optional `mso_value` and `ai_value`
    fields when present.
- Added `scripts/backfill_m15_choch_diagnostics.py`.
  - Default output: `shadow_logs/m15_choch_diagnostic_audit.jsonl`.
  - Default reports:
    `research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.json`
    and
    `research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.md`.
- Added tests in `tests/test_m15_choch_diagnostics.py` and extended
  `tests/test_forward_capture_shadow_loggers.py`.

## Backfill Result

Command:

```text
python scripts/backfill_m15_choch_diagnostics.py --decision-date-prefix 2026-05-05
```

Result:

- Status: `OK_DIAGNOSTIC_ONLY_NO_GATE_CHANGE`
- M15 CHoCH failures considered: `22`
- Audit rows appended: `22`
- Joined to latest path: `22`
- Waiting for path: `0`
- Later path outcomes:
  - `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`: `19`
  - `ENTRY_TOUCHED_UNRESOLVED`: `3`
- Opportunity counting:
  - `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`: `2`
  - `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE`: `19`
  - `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`: `1`

Interpretation:

- The May 5 evidence strongly motivates a continuation/no-retrace shadow lane,
  but it does not justify loosening `m15_choch_exists`.
- Most fast-continuation examples are XAGUSD duplicate active setup rows, so
  future scoring must use opportunity-level counting, not raw candidate counts.
- The two countable rows are candidates for deeper preregistered analysis, not
  promotion evidence.

## Verification

- `python -m py_compile src/research_infra/m15_choch_diagnostics.py src/research_infra/forward_capture.py scripts/backfill_m15_choch_diagnostics.py` passed.
- First focused pytest run failed before test execution because the sandbox could
  not create `C:\tmp\pytest_phase2_m15_choch_diag`.
- Approved rerun passed:

```text
python -m pytest tests/test_m15_choch_diagnostics.py tests/test_forward_capture_shadow_loggers.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_phase2_m15_choch_diag
15 passed in 4.05s
```

The pytest guard printed a production-path snapshot warning for
`pipeline_state/shadow_observer_state.json`; that file was already runtime dirt
from live/no-AI observer activity and is not part of this change.

## Ambiguity Status

- Is `m15_choch_exists` too strict in fast-continuation regimes? `OPEN`.
- This phase now makes that question auditable by joining L2 failure reason,
  later path label, and opportunity counting status.
- The next phase must preregister the continuation/no-retrace lane before
  outcome mining or threshold selection.

## Remaining Blockers

- No continuation/no-retrace entry, stop, invalidation, target, or scoring rule
  is approved yet.
- No broker actual-R evidence exists for these rejected L2 rows.
- Synthetic path labels remain separate from broker PnL and promotion claims.

NO_PROMOTION_VERDICT
