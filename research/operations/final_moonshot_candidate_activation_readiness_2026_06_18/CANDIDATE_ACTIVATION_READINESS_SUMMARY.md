# Candidate Activation Readiness Summary

Date: 2026-06-18

Decision: `KEEP_CANDIDATE_BOOK_DEFAULT_OFF__ACTIVATION_REQUIRES_PROFILE_SPEC_HISTORY_AND_MC_PROOF`.

This route checks candidate symbols against active profile config, broker spec proof, native routing, and required OHLCV/LTF coverage. It does not activate candidate sleeves and does not touch live MT5, brokers, orders, credentials, VPS processes, or orderflow/depth data.

## Result

- Verifier status: `ok=true`.
- Candidate activation status: `activation_ready=true`.
- Candidate book remains default-off: `ultimate_book_include_candidate_book: false`.
- Candidate profile remains declared as `runtime_executable_native_exit_v2`.
- Runtime candidate symbols covered: `30`.
- Readiness work items recorded: `0`.
- LTF stress gaps recorded: `0`.
- Profile/spec disposition: `24` dual-broker profile/spec-ready symbols and `6` FTMO-only profile/spec-ready symbols with redacted_account expected-skip semantics.

## Current Shape

- `asia_pdl_fade` no longer carries `NATGAS_cash` in its deployable surface; NATGAS is preserved in the separate decomposition route as research-revival inventory.
- `AUDUSD`, `EURGBP`, `EURUSD`, `GBPUSD`, `NZDUSD`, `USDCAD`, and `USDCHF` are dual-broker profile/spec-ready from bridge and redacted_account spec evidence.
- `DASHUSD`, `LTCUSD`, `XPDUSD`, `XPTUSD`, `XRPUSD`, and `XTZUSD` are FTMO-only profile/spec-ready; their redacted_account profile gaps remain recorded for audit and are handled as expected skips.
- Native-eligible gaps: none.
- Required generation-history gaps: none.

## Next Work

- Keep the candidate book default-off on the Mac while preparing the owner/VPS activation package.
- Preserve explicit FTMO-only skip semantics unless future redacted_account-native proof upgrades those symbols.
- Use the refreshed MC/replay and dossier routes as the deployment-readiness proof surface.
- Keep `NATGAS_cash` in the separate research-revival lane unless a new limit-entry/cost route proves deployable geometry.
