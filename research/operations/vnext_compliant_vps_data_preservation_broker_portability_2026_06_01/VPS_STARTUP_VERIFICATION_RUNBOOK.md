# VPS Startup Verification Runbook

Generated: 2026-05-31T18:17:52.443340Z

Run this before any future live runtime start on a compliant VPS. This runbook is default-off and read-only until the owner separately approves live operations.

1. Regenerate `LIVE_STATE.md` and record current `git rev-parse HEAD`.
2. Confirm the worktree is clean or that uncommitted changes are scoped and understood.
3. Confirm identity/residency framing: Tunisian owner, Tunisia residency/permanent address, Malaysia temporary travel only unless official KYC evidence says otherwise.
4. Capture public IP country and provider. It must not be a restricted country and must not be the United States for MT5.
5. Confirm the VPS is private/dedicated with a stable dedicated IP.
6. Document redacted_account VPS/EA add-on or fee state where applicable.
7. Confirm secrets exist without printing values.
8. Verify MT5 terminal/account in read-only mode first: symbol specs, positions, orders, history orders, and history deals.
9. Verify the 24-symbol canonical surface and broker aliases in `BROKER_PORTABILITY_MAP.json`.
10. Verify config points to the vNext/moonshot replacement, current next-level package artifacts, Lane03 selector, Lane05 scheduler, Lane06 broker truth, and Lane08 execution policy evidence.
11. Confirm log, data, tick, M1, and export directories exist and are writable.
12. Start data capture before any trading runtime.
13. Run default-off dry-run checks from `DEFAULT_OFF_EXPORT_SCRIPT_MANIFEST.json`.
14. Keep live broker actions blocked until the owner explicitly approves a separate runtime start.

Hard stops: restricted-country IP, United States IP for MT5, shared VPS, missing VPS/EA fee proof where required, missing symbol specs, missing secrets, stale HEAD, failed dry-run verifier, or any request to perform broker-changing action inside this route.
