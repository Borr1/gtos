# VPS Broker Profile Market Detail Audit

Generated: `2026-06-19T04:12:38.283034Z`
Branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
Runtime effect boundary: `read_only_mt5_account_terminal_symbol_tick_inspection_no_symbol_select_no_broker_mutation`

Overall ok: `true`
Issue count: `0`
Warning count: `291`
Active canonical symbols: `46`

## Profile Summary

| Profile | Init | Supported | Unsupported | Positive ticks | Missing symbol_info | Issues | Warnings |
|---|---:|---:|---:|---:|---:|---:|---:|
| operator_profile | true | 46 | 0 | 46 | 0 | 0 | 85 |
| redacted_account | true | 36 | 10 | 36 | 0 | 0 | 206 |

## Unsupported Symbols

- `operator_profile` unsupported: `none`
- `operator_profile` unexpected unsupported: `none`
- `redacted_account` unsupported: `AVAUSD, CORN_c, COTTON_c, DASHUSD, XAGAUD, XAGEUR, XAUAUD, XAUEUR, XPDUSD, XTZUSD`
- `redacted_account` unexpected unsupported: `none`

## Issues

- `none`

## Warning Classes

- `profile_live_drift_warning`: `41`
- `profile_missing_live_available_optional_field`: `250`

## Interpretation

- Hard issues mean a supported active symbol, account identity, or static symbol field does not match current direct MT5 truth.
- Warnings preserve drift or optional metadata gaps. Live spread, tick value, and swap can move; warnings are review inputs, not automatic runtime blockers.
- This audit intentionally does not call `symbol_select`; absent or invalid ticks can reflect closed-market visibility rather than a profile defect.
