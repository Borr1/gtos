# G8 Options, Gamma, VRP Completion Audit - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

## Prompt Checklist

| Requirement | Status | Evidence |
|---|---|---|
| Mandatory preflight completed | Done | Regenerated `.context/LIVE_STATE.md`; read latest handoff, quick reference, research doctrine/current state, reading order, G8 prompt, and G0 registries. |
| Source ledger/search plan | Done | `G8_OPTIONS_VOL_CONTEXT_LEDGER_2026-05-06.md` |
| Raw responses/source-index evidence | Done | Raw cache directory plus `G8_OPTIONS_VOL_SOURCE_INDEX_2026-05-06.md/json` |
| Domain synthesis | Done | `G8_OPTIONS_VOL_DOMAIN_SYNTHESIS_2026-05-06.md/json` |
| Ambiguity ledger | Done | `G8_OPTIONS_VOL_AMBIGUITY_LEDGER_2026-05-06.md` |
| Counter-evidence and decay-mode review | Done | Domain synthesis and mechanism rows include decay modes and killed-route checks. |
| Mechanism rows | Done | `G8_OPTIONS_VOL_MECHANISM_ROWS_2026-05-06.json` |
| Hypothesis rows | Done | `G8_OPTIONS_VOL_HYPOTHESIS_ROWS_2026-05-06.json` |
| Source contracts | Done | `G8_OPTIONS_VOL_SOURCE_CONTRACT_ROWS_2026-05-06.json` |
| Experiment prereg specs | Done | `G8_OPTIONS_VOL_EXPERIMENT_PREREGS_2026-05-06.json`; all `outcome_review_opened=false`. |
| Killed-route notes | Done | Domain synthesis, ambiguity ledger, source contracts, mechanism rows. |
| Neighbor-lane pass | Done with blocker | G2 read; G7 and G10 not present at run time. |
| Source/budget blockers explicit | Done | Domain synthesis, source index, goal status, source contracts. |
| Live trading code untouched | Verified | Forbidden-path diff returned clean for `src`, `prompts`, `config`, canaries, and MT5 preflight paths. |

## Scope Audit

Files are limited to G8 research artifacts under `research/science_program_2026_05` plus the G8 raw source cache. The mandatory generated `.context/LIVE_STATE.md` change is intentionally not a G8 deliverable and must not be staged.

No changes were made to:

- `src/`
- `prompts/`
- `config/`
- `scripts/canary_fixtures/`
- `scripts/canary_test.py`
- `scripts/mt5_preflight.py`
- live execution, permissions, selectors, safety gates, MT5, order behavior, or paid data paths

## Key Findings

- Official historical aggregate GEX remains blocked.
- FlashAlpha Basic remains forward-context/proxy only.
- Public Cboe daily volatility-index CSVs for VIX, VIX1D, VIX9D, VIX3M, GVZ, and VVIX were found and cached through 2026-05-05.
- That public CSV discovery does not create a validation-safe feature. It creates a source-engineering follow-up: registry row, parser, publication-time policy, license review, and no-lookahead join tests.
- OPEX calendar features already exist in the research feature code. G8 therefore frames OPEX as a controlled observation/interaction hypothesis, not a request to add another feature.
- VRP remains formula-blocked until implied-source timing and realized-variance no-lookahead rules are frozen.

## Verification Run

- PASS: `python -m json.tool` on 7 G8 JSON artifacts.
- PASS: required-field smoke check for G8 source contracts, mechanism rows, hypothesis rows, and prereg rows.
- PASS: `NO_PROMOTION_VERDICT` presence check on 12 non-raw G8 reports/rows.
- PASS: forbidden-path diff check for `src`, `prompts`, `config`, `scripts/canary_fixtures`, `scripts/canary_test.py`, and `scripts/mt5_preflight.py`.
- PASS: `python -m pytest tests/test_science_goal_program.py -q -p no:cacheprovider --basetemp C:\tmp\gtosg\G8\.pytest_tmp_g8_science_program_e2` returned 9 passed in 0.34s. The first sandboxed attempts failed before test execution due Windows temp-directory permission errors; the approved escalated rerun passed.

## Cleanup Note

Pytest temp directories created during the failed sandboxed run and escalated rerun are ignored by git and do not appear in `git status`. Windows denied deletion even after an escalated cleanup attempt, so they are left outside the commit.
