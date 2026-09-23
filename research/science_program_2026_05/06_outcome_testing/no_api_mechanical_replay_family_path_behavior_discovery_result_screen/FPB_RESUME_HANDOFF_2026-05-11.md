# FPB Resume Handoff

Date: 2026-05-11
Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
Status: interrupted/incomplete; preserve all progress.

## Mandatory Resume Rule

Before launching or restarting any builder, prove whether an existing
`build_family_path_behavior_result_screen_2026_05_10.py` process is still
running. Do not launch a duplicate while PID `13608`, PID `4576`, or any other
builder process is responsive or has CPU/progress/artifact activity.

If a process is running, monitor CPU, responsiveness, progress-file growth, and
artifact timestamps. If progress appears stalled, wait long enough to
distinguish a large source chunk or final artifact write from a true hang, then
record exact evidence before taking any action.

## What Happened

PID `13608` was the interrupted original builder. It was monitored instead of
starting a duplicate. It completed the full source scan and then exited before
writing the required result ledgers.

Preserved proof file:

- `FPB_SOURCE_PROGRESS_2026-05-10.jsonl`

The final progress row showed:

- `source_number=365`
- `source_row_id=SRC-02270`
- `symbol=XAUUSD`
- `timeframe=M5`
- `candidate_attempts_so_far=13540033`
- `duplicate_candidate_keys_so_far=687275`
- `path_label_rows_so_far=12852758`
- `unique_candidate_denominator_so_far=12852758`

This proves the scan reached the accepted full denominator, but it does not by
itself replace the missing family-by-label aggregate ledgers because those
counters were in memory when the process exited.

The prior root cause was a write failure around the post-scan artifact/G12
prompt phase. A small probe wrote the G12 prompt path, so the current file at:

- `research/science_program_2026_05/04_goal_prompts/G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md`

may contain only probe content and must be overwritten by the real generated
G12 prompt before completion.

The builder was patched to:

- preserve any existing `FPB_SOURCE_PROGRESS_2026-05-10*.jsonl` instead of
  deleting it;
- write a timestamped progress file on resumed scans when the original progress
  file exists;
- write `FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json` and `.md`
  immediately after full aggregation, before later artifacts;
- reuse an existing valid aggregate matrix on a later run instead of rescanning.

A repaired builder was launched once as PID `4576` with logs:

- `FPB_BUILDER_STDOUT_20260511_121252.log`
- `FPB_BUILDER_STDERR_20260511_121252.log`

At the last check, `Get-Process` returned no rows for PID `13608` or PID `4576`.
The command-line process scan using `Get-CimInstance Win32_Process` was denied
by permissions in that check, so a resumed run must still perform a fresh
process/command-line check before any restart.

## Current Artifact State To Expect

As of this handoff, the route directory contained the builder, verifier, tests,
the preserved full-scan progress file, and empty stdout/stderr logs. Required
result ledgers were not yet present.

If `FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json` exists on resume,
inspect it first. If it matches the accepted expected counts, rerun the builder
only after proving no active builder; it should reuse the matrix and finish
artifact emission. If the matrix does not exist, a fresh no-duplicate builder
run is required to recompute aggregate counters while preserving the existing
progress file.

## Required Next Actions

1. Run the mandatory project preflight from `AGENTS.md` and the controlling
   goal prompt.
2. Read this handoff before deciding whether to restart anything.
3. Prove active builder state with PID and command-line evidence where possible.
4. If no builder is active, inspect:
   - `FPB_BUILDER_STDOUT_20260511_121252.log`
   - `FPB_BUILDER_STDERR_20260511_121252.log`
   - all `FPB_SOURCE_PROGRESS_2026-05-10*.jsonl`
   - all `FPB_*2026-05-10*` artifacts
5. Preserve the completed progress file and any later matrix/artifact files.
6. Continue the original controlling prompt to full completion without
   compact-only downgrade.

## Verification Already Run After Patches

- `python -m py_compile build_family_path_behavior_result_screen_2026_05_10.py verify_family_path_behavior_result_screen_2026_05_10.py test_family_path_behavior_result_screen_2026_05_10.py` passed.
- `python test_family_path_behavior_result_screen_2026_05_10.py` passed with
  `{"ok": true, "tests_run": 3}`.
- A `pytest` invocation reached `100%` but appeared to hang during Windows
  teardown, so the direct focused test runner is the reliable recorded test
  signal unless this is rechecked.

