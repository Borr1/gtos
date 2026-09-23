# VPS Deployment Handoff

Branch: `vnext-prod-integration-vps-v3-ftmo-2026-06-02`
Local HEAD before integration commit: `b6a91c9a13be764eedc00332b8a33b8c677d7de5`
VPS source branch: `origin/vps-prod-live-sync-2026-06-02` at `6726b0804582eaddacb9629eb82e5e9b90b8157e`
Merge base: `6726b0804582eaddacb9629eb82e5e9b90b8157e`

## What This Branch Integrates

- VPS live production fixes from `origin/vps-prod-live-sync-2026-06-02`: canary removal, watchdog direct Python live launch, liveness heartbeat supervision, selected-cell risk repairs, Stage13 risk label split, execution/broker lifecycle repairs, and VPS supervisor evidence.
- Local V3/FTMO production-ready package: FTMO profile support, broker/account namespace helpers, profile verifier, namespace-aware capture/execution/broker truth paths, and default-off V3 package disposition.
- Integration repairs: redacted_account profile account/broker-geometry verification now uses VPS truth without storing raw login, and trade-close notifications are non-blocking so SPRT/CUSUM exit updates continue if notification context is missing.

## Deployment Boundaries

This branch does not perform broker/order/deal/position mutation, credential changes, paid API calls, remote push, or VPS live process restart. VPS deployment is a separate owner action.

## VPS-Side Checks Before Reload

1. Pull or otherwise place this committed branch on the VPS.
2. Run `py -3 scripts/verify_broker_profile.py config/profiles/redacted_account.yaml --result research/operations/vnext_vps_local_v3_ftmo_production_integration_2026_06_02/PROFILE_VERIFIER_redacted_account_RESULT.json`.
3. Run `py -3 research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/verify_vps_supervisor_artifacts.py`.
4. Run the focused pytest matrix from `VERIFICATION_MATRIX.json`.
5. For FTMO only after owner approval, run the FTMO profile verifier against the real VPS terminal/account export and confirm account stage/add-ons before starting any FTMO process group.

## Runtime Contract

redacted_account remains the current live default. FTMO is staged with profile, namespace, terminal-path, verifier, and deployment-handoff support. V3 Selector/Scheduler/Execution packages remain default-off/promotion-ready; they are not silently activated by this integration branch.
