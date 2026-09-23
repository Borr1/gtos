# VPS Dual-Production Implementation Contract

Generated: 2026-06-01T18:01:51.709848Z

## Authority Model

- VPS production code/runtime is final live authority.
- Local FTMO MT5 capture is FTMO broker-fact authority for account/server/symbol/spec/session/spread/cost/history metadata.
- This local repo is the portable package source; it must be compared and rebased onto VPS production before activation.

## Required VPS Evidence Before Editing

1. Export current VPS `git status --short`, `git log -1 --oneline`, active process command lines, lock files, log roots, `pipeline_state`, `shadow_logs`, `data/m1`, `data/ticks`, and supervisor scripts.
2. Run read-only MT5 account assertions for both terminals.
3. Verify redacted_account terminal path and FTMO terminal path are distinct.
4. Verify redacted_account and FTMO account/server identities are distinct and match their profiles.

## Code And Config Package To Port

- `src/utils/broker_profile.py`
- `run_agent.py`
- `src/components/orchestrator.py`
- `src/components/execution.py`
- `src/components/m1_capture.py`
- `src/components/tick_capture.py`
- `src/components/broker_truth_cost_capture_v2.py`
- `scripts/verify_broker_profile.py`
- `config/profiles/operator_profile.yaml`
- `config/profiles/ftmo.yaml`
- route templates under `research\operations\vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/templates/`

## Namespace Contract

- redacted_account process group: `redacted_account_live_<account_hash>`.
- FTMO process group: `operator_profile`.
- Every order-capable process must pass `--runtime-namespace` and `--terminal-path`.
- Every profile must define `broker_profile.expected_account` with server, company, currency, and login SHA256.
- Orchestrator lock files must include namespace: `.orchestrator_<namespace>_<symbol>.lock`.
- Execution checkpoints must include namespace: `execution_checkpoint_<namespace>.json`.
- Pending intents must include namespace: `pending_intent_<symbol>_<namespace>.pkl`.
- M1 roots: `data/m1/<namespace>/`.
- Tick roots: `data/ticks/<namespace>/`.
- Trade records: `knowledge_base/<namespace>/trade_records/`.
- Broker truth logs: `shadow_logs/<namespace>/broker_truth_cost_capture_v2.jsonl`.
- Telegram queue: `pipeline_state/<namespace>/notification_queue.jsonl`.

## Merge Order

1. Stop no live process yet; first inspect VPS current production state.
2. Apply helper/profile/verifier code in a non-live working copy.
3. Add/copy FTMO profile and keep credentials out of repo.
4. Run offline profile verifier for both broker profiles.
5. Run mock/no-order launch checks for both namespaces.
6. Run read-only M1/tick/profile preflights with `--once` and no order-capable live mode.
7. Patch supervisor/watchdog to manage two process groups and namespace-specific locks/heartbeats.
8. Only after owner approval, start live process groups.

## Required Verifiers

```powershell
py -3 scripts/verify_broker_profile.py config/profiles/operator_profile.yaml --result research\operations\vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/PROFILE_VERIFIER_RESULT.json
py -3 -m pytest tests/test_broker_profile_namespace.py tests/test_verify_broker_profile.py tests/test_m1_capture.py -q
py -3 research\operations\vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/verify_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py
```

## Rollback

Use `research\operations\vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/templates/rollback_stop_by_namespace.ps1 -Namespace operator_profile` for FTMO-only stop. redacted_account must have its own namespace and must not be killed by FTMO rollback.

## Forbidden Until Owner Approval

No hidden live activation, no broker order/deal/position mutation, no credential commits, no remote push, and no VPS live-process mutation from the local session.
