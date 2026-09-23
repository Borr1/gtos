# Market Expansion Conditioned Policy Runtime Alias And Owner Activation Config

Decision: `MARKET_EXPANSION_CONDITIONED_POLICY_ALIASES_AND_OWNER_APPROVED_CONFIG_ACTIVATION_PACKAGED`

Runtime effect from this Mac route: `none_no_broker_or_vps_reload_executed`

Config effect in repo: `ultimate_book_include_market_expansion_book=true` with policy
`positive_weighted12_after_swap`, for VPS Codex absorption/deployment handoff.

## What Changed

- Added audited conditioned policy aliases for market expansion:
  - `all14_swap_adjusted`
  - `positive_weighted12_after_swap`
  - `robust6_every_split_positive`
- Added `ultimate_book_market_expansion_policy` to the runtime bridge/config vocabulary.
- Kept bridge defaults as `explicit_allowlist` and `ultimate_book_include_market_expansion_book: false`.
- Activated the repo config to the owner-approved strongest conditioned policy:
  `positive_weighted12_after_swap`.
- Unknown policy names fail closed.
- Named policy plus a mismatched manual sleeve list fails closed.

## Current Meaning

The flat all-sleeve market-expansion overlay was not the strongest behavior. This package lets the runtime
and VPS handoff reference the smarter conditioned policies directly. The repo config now selects the best
monthly/Sharpe policy, while the bridge still has safe defaults and fail-closed policy validation.

This is not a broker action and not a VPS reload. It is an owner-approved repo config activation package
for the VPS deployment session.
