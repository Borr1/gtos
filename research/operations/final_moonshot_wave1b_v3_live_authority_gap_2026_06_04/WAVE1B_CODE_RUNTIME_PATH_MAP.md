# Wave 1B Code Runtime Path Map

Generated: 2026-06-04T14:51:09.961282+00:00

## Selector

- Current halt-time live path: `src/components/gtos_vnext_runtime.py` dynamic moonshot router and selected-cell risk helpers write `gtos_vnext_moonshot_dynamic_execution`.
- V3 package/helper path: `src/research/moonshot_selector_v3_default_off.py` and `src/research/moonshot_v3_runtime_packages.py`.
- Runtime disposition: Selector V3 package-present but config-disabled/default-off. No halt-time runtime rows prove Selector V3 live authority.
- Wave1B repair: `src/components/orchestrator.py` writes `gtos_vnext_candidate_intelligence_packet.v3_live_authority.selector_v3` as capture-only proof.

## Scheduler And Money Risk

- Current live path: `src/components/permissions.py`, `src/components/portfolio_risk.py`, `src/components/cross_instrument_correlation_gate.py`, prop-safe selector code in `src/components/gtos_vnext_runtime.py`, and pending lifecycle rows in `shadow_logs/pending_limit_lifecycle.jsonl`.
- V3 package/helper path: `src/research/moonshot_v3_runtime_packages.py::build_scheduler_v3_packet`.
- Runtime disposition: Scheduler V3 default-off; required broker-real balance/equity/open/pending/new risk/cost/cluster fields are source gaps at packet time.
- Wave1B repair: packet records scheduler V3 default-off decision and missing money-risk source status without activating.

## Execution Policy

- Current live path: dynamic policy router intent in `src/research/moonshot_default_off_policy_router.py` and current runtime selection in `src/components/gtos_vnext_runtime.py`.
- V3 package/helper path: `src/research/moonshot_v3_runtime_packages.py::build_execution_policy_v3_packet`.
- Runtime disposition: Execution Policy V3 default-off; live authority was `momentum_exhaustion` primary with `partial_be_runner` exception selection.
- Wave1B repair: packet records execution_policy_v3 default-off decision and ticket lifecycle source requirement.

## Lifecycle, Cost, Exposure, Halt

- Same-symbol lifecycle: `src/components/permissions.py::_reject_if_same_symbol_vnext_lifecycle_conflict` plus `shadow_logs/pending_limit_lifecycle.jsonl`.
- Cost/swap/slippage: broker truth exports under `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03` and incomplete pretrade packet fields.
- Exposure/correlation: `src/components/permissions.py`, `src/components/cross_instrument_correlation_gate.py`, hard-halt review cluster failure evidence.
- Halt: `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, `pipeline_state/RESEARCH_RUNTIME_HALT.flag`, and hard-halt review.

## Packet, Profile, Launcher, Replay

- Packet: `src/components/orchestrator.py::_refresh_vnext_candidate_intelligence_packet`.
- Profile/config: `config/agent_config.yaml` V3 keys all false/default-off.
- Launcher/runtime package consumption: `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02`.
- Tests/verifiers: `tests/test_moonshot_v3_runtime_packages.py`, `tests/test_vnext_broader_origin_orchestrator.py`, and this route verifier.
