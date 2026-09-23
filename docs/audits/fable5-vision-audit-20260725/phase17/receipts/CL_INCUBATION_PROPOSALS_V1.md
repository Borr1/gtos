# CL incubation proposals

Two dossiers are valid for registration and **neither is ready to arm**. Filing them uses zero capacity. The registry currently has **1 armed / 5**, leaving 4 live slots.

## `mx_ethusd_d1_donchian_20_breakout@target_5R@FTMO`

Proposed confidence **0.025**; basis `OWNER_RISK_ACCEPTED`. CH broker-true mid: n=217, +0.456628 R/day, +0.502914 R/trade, recent-two +1.010822; REJECT robustness and significance (q=1.0).

Arming vetoes:

- target_5R is absent from FRONTIER_EXIT_OVERRIDES for mx_ethusd; current live contract is target_2R
- no trade-by-trade research-to-live parity receipt exists for mx_ethusd@target_5R
- redacted_account broker-local target-5R measurement is absent; factory approval on both firms is impossible today

Pre-registered exit rules:

- `S0_contract_fidelity`: any live target, stop, time-stop, account, symbol or effective-confidence mismatch — `{'mismatches_allowed': 0}`
- `S1_risk_budget`: cumulative broker-net R reaches the pre-declared loss budget — `{'cumulative_net_r_lte': -6.035}`
- `S2_gross_negative`: gross expectancy is non-positive after a minimally interpretable live sample — `{'min_fills': 20, 'min_distinct_day_blocks': 8, 'mean_gross_r_lte': 0.0}`
- `P1_historical_factory_then_owner`: historical-primary graduation on the exact live contract at both firms, with no live veto — owner ceremony only

## `asia_pdl_fade@stop2.5_native_no_ts@FTMO`

Proposed confidence **0.025**; basis `OWNER_RISK_ACCEPTED`. AL broker-true best cell: n=2827, +0.084626 R/day, +0.048010 R/trade, 5/5 OOS folds positive; REJECT significance (p=0.065893, q=0.576567).

Arming vetoes:

- runtime candidate confidence is 0.25, ten times the 0.025 dossier weight; no per-launch weight override exists
- the measured stop2.5/native/no-time-stop contract is not a runtime-selectable contract
- the current execution packet uses a time stop while the measured winner uses none
- no trade-by-trade research-to-live parity receipt exists for the repaired cell

Pre-registered exit rules:

- `S0_contract_fidelity`: any live target, stop, time-stop, account, symbol or effective-confidence mismatch — `{'mismatches_allowed': 0}`
- `S1_risk_budget`: cumulative broker-net R reaches the pre-declared loss budget — `{'cumulative_net_r_lte': -3.0}`
- `S2_gross_negative`: gross expectancy is non-positive after a minimally interpretable live sample — `{'min_fills': 20, 'min_distinct_day_blocks': 8, 'mean_gross_r_lte': 0.0}`
- `P1_historical_factory_then_owner`: historical-primary graduation on the exact live contract at both firms, with no live veto — owner ceremony only

## Screened out

- `thr_sub_xvol_pullback_vr14_s125_ac015`: not a distinct runtime sleeve, parent sub_xvol_pullback is already armed at 0.45, and AL REJECTS the variant; an incubation row could not independently stop it
- `mx_btcusd_target5_redacted_account`: CH REJECTS all cost bands with negative OOS and lifetime means; live testing is not a substitute for negative historical-primary evidence
- `asia_pdl_fade_redacted_account`: no account-local broker-true dossier exists; the FTMO proposal is not transferred

The exact next build is therefore contract parity, not a tag ceremony: wire and prove ETH target-5R; add a bounded, addressable Asia stop/exit/weight contract; then obtain account-local redacted_account economics before either can qualify for the owner-approved both-account direct path.
