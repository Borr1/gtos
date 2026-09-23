# vNext VPS FTMO V3 Clean Deploy Package

Branch: `vnext-vps-ftmo-v3-clean-deploy-2026-06-02`
Base: `origin/vps-prod-live-sync-2026-06-02` at `6726b0804`
Source integration branch: `vnext-prod-integration-vps-v3-ftmo-2026-06-02` at `1b82121e7`

## Purpose

This branch is the GitHub/VPS deploy package. It starts from the latest VPS live supervisor branch and ports only deploy-relevant local work:

- FTMO account-specific profile and profile verifier.
- redacted_account profile/account truth repair.
- Broker/account namespace helpers.
- Runtime namespace support for `run_agent.py`, M1 capture, tick capture, execution checkpoints, MT5 terminal path resolution, and orchestrator account assertions.
- Broker truth/cost capture helper.
- Default-off Selector V3, Scheduler V3, and Execution Policy V3 package files.
- FTMO dual-production handoff route and focused tests.

## Explicit Runtime State

redacted_account remains the current live default.
FTMO is staged for VPS proof and owner activation.
V3 Selector/Scheduler/Execution packages are present and default-off. This branch does not silently activate V3 trading behavior.

## Heavy Evidence Boundary

The full research/integration branch still carries heavy moonshot ledgers. Those are not included in this deploy branch. Full raw/research evidence can move by outside-Git archive or Google Drive. GitHub/VPS deploy receives production code, profile/config, verifiers, compact package artifacts, and handoff evidence only.

## Verification Already Run Locally

- `py_compile` on deploy-touched runtime, profile, MT5, broker helper, and V3 default-off code: passed.
- redacted_account profile verifier: `ok=true`, `24` active symbols, `24` aliases, `0` issues.
- FTMO profile verifier: `ok=true`, `24` active symbols, `24` aliases, `0` issues.
- Focused pytest: `198 passed`.
- `git lfs push --dry-run origin vnext-vps-ftmo-v3-clean-deploy-2026-06-02`: no LFS objects listed.

## VPS Activation Sequence

1. Pull this clean deploy branch on the VPS.
2. Run the redacted_account profile verifier on the VPS.
3. Run the VPS supervisor verifier on the VPS.
4. Run the focused production pytest matrix on the VPS.
5. Verify current MT5 account/process/open-position state.
6. Reload redacted_account only after the checks pass.
7. For FTMO, run the profile verifier against the actual VPS FTMO terminal/account export, confirm account stage/add-ons, then start a separate namespaced FTMO process group.

No remote push, live broker/order/deal/position mutation, credential change, paid/vendor call, or VPS restart/reload was performed by this local packaging step.
