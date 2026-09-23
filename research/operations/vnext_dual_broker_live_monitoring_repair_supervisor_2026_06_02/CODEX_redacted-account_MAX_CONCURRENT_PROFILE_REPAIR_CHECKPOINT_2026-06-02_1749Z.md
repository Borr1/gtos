# Codex redacted_account Max Concurrent Profile Repair Checkpoint - 2026-06-02 17:49 UTC

## Status

- Scope: disk/profile stale-risk repair for redacted_account plus focused regression tests.
- Manual broker/order/position mutation: none.
- Runtime reload: not performed for this repair because current governed vNext rows already bypass the legacy count cap in live code, and memory was below the maintenance-widening threshold.
- Runtime effect boundary: future redacted_account profile loads no longer carry a stale raw trade-count cap.

## Defect

`config/profiles/redacted_account.yaml` still pinned:

```yaml
risk:
  max_concurrent: 4
```

That conflicted with the current vNext risk authority recorded in
`config/agent_config.yaml` and FTMO profile repairs: selected-cell/prop-safe
aggregate drawdown budget is the production authority for governed vNext rows,
not a raw count cap.

Current live `permissions._reject_if_concurrent_cap_reached` already bypasses
the legacy count cap when a trade carries active vNext selected-cell risk
context. The stale profile pin therefore was not the cause of the latest
redacted_account/FTMO behavior, but it was a disk/profile staleness defect that could
mislead future profile loads, audits, and non-governed fallback interpretation.

## Repair

- `config/profiles/redacted_account.yaml`
  - changed `risk.max_concurrent` from `4` to `null`.
  - added `max_concurrent_policy: disabled_for_vnext_selected_cell_aggregate_drawdown_budget`.
  - added `risk_policy_source` documenting aggregate drawdown budget, not trade count.
- `config/profiles/README.md`
  - updated redacted_account profile authority language.
  - added explicit redacted_account note matching the live permissions behavior.
- `tests/test_profile_overrides.py`
  - added regression checks that redacted_account profile and instrument overlays preserve the disabled count-cap policy.
  - refreshed stale US30/US30_cash profile expectations to current account-specific profile truth.

## Verification

- `python -m pytest tests\test_profile_overrides.py -q`
  - `19 passed`
- `python -m pytest tests\test_concurrent_cap.py tests\test_vnext_lane05_portfolio_scheduler.py -q`
  - `34 passed`
- `python research\operations\vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02\verify_dual_supervisor_checkpoint.py`
  - `PASS`, `failure_count=0`

## Runtime Snapshot

- redacted_account run_agent processes: 24.
- redacted_account tick_capture processes: 24.
- FTMO run_agent processes: 0.
- FTMO follower processes: 1.
- Dual projector processes: 1.
- M1 capture processes: 1.
- MT5 terminals: 2.
- Free physical memory near verification: 1506.42 MB, 18.39%.

## Reload Decision

No broad redacted_account fleet reload was performed for this profile metadata repair.
Reason: current live vNext selected-cell governed trades already bypass the
legacy count cap in `src/components/permissions.py`, and a 24-process rolling
reload would increase operational risk while free memory was low. The disk
profile is now correct for the next scoped reload or process start.

## Remaining Work

- Continue watching for the next post-repair canonical intent to confirm the
  patched FTMO follower copies or rejects only for target tick/risk-budget
  reasons.
- Continue current candidate/trade lifecycle inspection and V3 disposition
  review.
