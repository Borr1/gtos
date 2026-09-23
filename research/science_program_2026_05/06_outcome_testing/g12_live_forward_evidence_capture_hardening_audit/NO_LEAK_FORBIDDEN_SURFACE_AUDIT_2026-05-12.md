# No-Leak, Raw-Data, and Forbidden-Surface Audit - 2026-05-12

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Finding

PASS. The target commit does not include raw `shadow_logs/`, `data/account_history/`, tick parquet/data blobs, credentials, prompt/config/risk/safety/execution/canary/selector edits, validation/result scoring, or remote-push behavior.

## Diff Evidence

`git show --name-only 3faa2b70` includes no paths under:

- `config/`
- `prompts/`
- `shadow_logs/`
- `data/account_history/`
- `data/ticks/`
- credential/env paths

It also includes no production edits to:

- `src/components/permissions.py`
- `src/components/execution.py`
- production canary files
- production selector files

The only path with `selector` in its name is `src/research_infra/v2_structural_selector_readiness.py`, which is a research readiness lane and is covered by `tests/test_v2_structural_selector_readiness.py`.

## Account-History Reader Boundary

The commit changes account-history readers to consume deduplicated read-only exported deal files, but it does not add new account-history data files:

- `scripts/backfill_account_pnl_truth_reconciliation.py:32` points to the account-history directory.
- `scripts/backfill_account_pnl_truth_reconciliation.py:46` to `:72` deduplicates MT5 deal exports by ticket/order/position/entry/time.
- `scripts/backfill_broker_actual_r_audit.py:32` points to the account-history directory.
- `scripts/backfill_broker_actual_r_audit.py:40` to `:66` deduplicates MT5 deal exports by the same key.
- `scripts/verify_shadow_log_integrity.py:2554` defines `read_mt5_deal_exports`.
- `scripts/verify_shadow_log_integrity.py:2559` to `:2572` deduplicates read-only deal exports.
- `scripts/verify_shadow_log_integrity.py:4791` uses the deduped export reader for broker actual-R audit.
- `scripts/verify_shadow_log_integrity.py:6250` uses it for account/PnL truth audit.
- `tests/test_verify_shadow_log_integrity.py:1883` verifies newer MT5 deal export filenames are consumed.

## Workspace Dirt Ledger

The worktree contains live/runtime dirt outside this audit lane, including `.context/LIVE_STATE.md`, many `shadow_logs/`, pipeline state, and untracked read-only account-history/runtime files. The G12 prompt explicitly says to ledger unrelated live/runtime dirt as unscoped. None of that dirt is staged or required for this audit decision.

The targeted pytest run emitted a production-path snapshot warning naming active live-process writes under `knowledge_base/`, `shadow_logs/`, and `pipeline_state/`. The tests still passed, and the warning is treated as runtime concurrency evidence, not a target-commit blocker.

## Boundary

This audit did not run MT5 account/order/history/deal/position reads, did not call AI/API/paid vendors, did not restart live processes, did not push to remote, and did not edit prompts/config/risk/safety/execution/canary/selector surfaces.
