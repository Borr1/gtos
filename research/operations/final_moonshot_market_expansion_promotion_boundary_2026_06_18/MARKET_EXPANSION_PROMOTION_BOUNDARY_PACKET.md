# Market Expansion Promotion Boundary Packet

Decision: `MARKET_EXPANSION_PROMOTION_BOUNDARY_READY_NOT_PROMOTED`

Market expansion is still default-off on the Mac package. This route built a
conditional owner-action VPS package, not a live activation.

Current numeric package:

- Active A8 reference Sharpe `0.147757`, monthly `2.646%`, MC pass `0.99055`.
- Armed candidate-book reference Sharpe `0.277408`, monthly `4.969%`, MC pass `0.9999`.
- Candidate book plus market-expansion seed `0.025` cost3 Sharpe `0.279324`, monthly `5.003%`, MC pass `0.99975`.
- Dossier delta versus candidate reference: Sharpe `0.001916`, monthly `0.034%`.
- Profile-merged synthetic pretrade packet rows passed: `28/28`.

Do not apply the market-expansion config patch until these requirements are closed:

- `MX-PROMO-REQ-001`: explicit broker trading-session table or platform-source proof
- `MX-PROMO-REQ-002`: broker-exact market-expansion commission authority
- `MX-PROMO-REQ-003`: broker-exact slippage and limit/market fill authority
- `MX-PROMO-REQ-004`: exact swap-to-R holding-time model
- `MX-PROMO-REQ-005`: owner-approved VPS promotion and monitoring execution

Non-applied activation patch:

```yaml
gtos_vnext_runtime:
  ultimate_book_include_market_expansion_book: true
  ultimate_book_market_expansion_profile: "default_off_market_expansion_d1_target2_v1"
  ultimate_book_market_expansion_sleeves:
    - "mx_aus200_cash_d1_volume_surge_reversal"
    - "mx_avausd_d1_donchian_20_breakout"
    - "mx_btcusd_d1_donchian_20_breakout"
    - "mx_cadjpy_d1_volume_surge_reversal"
    - "mx_ethusd_d1_donchian_20_breakout"
    - "mx_eu50_cash_d1_volume_surge_reversal"
    - "mx_fra40_cash_d1_volume_surge_reversal"
    - "mx_ger40_cash_d1_volume_surge_reversal"
    - "mx_jp225_cash_d1_volume_surge_reversal"
    - "mx_nzdjpy_d1_donchian_20_breakout"
    - "mx_spn35_cash_d1_volume_surge_reversal"
    - "mx_us100_cash_d1_atr_mean_reversion"
    - "mx_us30_cash_d1_volume_surge_reversal"
    - "mx_us500_cash_d1_atr_mean_reversion"
```

Rollback patch:

```yaml
gtos_vnext_runtime:
  ultimate_book_include_market_expansion_book: false
  ultimate_book_market_expansion_sleeves: []
```

VPS verification sequence before any live reload:

```powershell
cd C:\Users\MSI\Documents\ai-trading-agent
git pull --ff-only

$py = ".\.venv-gtos\Scripts\python.exe"

& $py research\operations\final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18\verify_market_expansion_runtime_generator_implementation.py
& $py research\operations\final_moonshot_market_expansion_live_authority_dossier_2026_06_18\verify_market_expansion_live_authority_dossier.py
& $py research\operations\final_moonshot_market_expansion_promotion_boundary_2026_06_18\verify_market_expansion_promotion_boundary.py

& $py -m pytest `
  tests\ultimate_book\test_market_expansion_runtime_generator.py `
  tests\ultimate_book\test_market_expansion_runtime_generator_implementation_artifacts.py `
  tests\ultimate_book\test_market_expansion_live_authority_dossier_artifacts.py `
  tests\ultimate_book\test_market_expansion_promotion_boundary_artifacts.py `
  tests\test_broker_net_cost_engine.py -q
```

Only after all requirements close and owner explicitly approves activation:

1. Apply the config patch above.
2. Restart only the existing ultimate-book workers by namespace.
3. Do not restart MT5 terminals, Docker/Kasm, bridge containers, unrelated watchdogs, legacy `run_agent.py`, or broad runtime services.
4. Monitor the same candidate-book ledgers plus market-expansion fail-closed statuses.

Monitor:

- `pipeline_state\ultimate_book\operator_profile\heartbeat.json`
- `pipeline_state\ultimate_book\redacted_account_live_bee34003\heartbeat.json`
- `pipeline_state\ultimate_book\*\placed_decisions.jsonl`
- `shadow_logs\ultimate_book_launcher.jsonl`
- `shadow_logs\run_book_console.log`
- `shadow_logs\run_book_fn_console.log`
- `shadow_logs\book_supervisor.log`

Alert or rollback on:

- `fail_closed_unknown_market_expansion_profile`
- `fail_closed_market_expansion_requires_explicit_sleeves`
- `fail_closed_unknown_market_expansion_sleeves`
- any market-expansion sleeve outside the explicit 14-sleeve allowlist
- any late D1 entry after the guarded open window
- spread/total-cost gate refusal outside expected skip handling
- session/commission/swap/fill evidence missing on the VPS packet-parity pass
- heartbeat stale after worker reload
- market-expansion config on VPS differs from this packet
