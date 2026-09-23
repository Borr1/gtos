# Full Candidate Book Live Activation Packet

Decision: `ARM_FULL_CANDIDATE_BOOK_LIVE_CONFIG_AND_HAND_TO_VPS`

Active Mac config now arms the full positive-confidence candidate book:

```yaml
ultimate_book_include_candidate_book: true
ultimate_book_candidate_book_profile: "runtime_executable_native_exit_v2"
ultimate_book_candidate_book_sleeves: [asia_pdl_fade, asian_fade, kz_london_crypto_low, liq_asia_up_low_metal, metal_session_reversion, ny_crypto_momentum, orb_crypto_london, vol_compression, vss_fxcross_london_up_low]
```

Evidence numbers:

- Active core8 + A8 baseline Sharpe: `0.147757`
- Full candidate book Sharpe: `0.277408`
- Active MC pass / max-DD fail / monthly: `0.99055` / `0.00945` / `2.646%`
- Full candidate MC pass / max-DD fail / monthly: `0.9999` / `0.0001` / `4.969%`
- Worst day improved from `-2.66%` to `-2.16%`.

Runtime meaning:

- Bridge defaults remain fail-safe/off.
- Active YAML carries an explicit nine-sleeve allowlist; live package does not use `[]` all-executable mode.
- Unknown candidate profile or sleeve still fails closed.
- `NATGAS_cash` is not in `asia_pdl_fade` live surface and remains hard-dropped as a separate limit-entry/cost-revival lane.
- This route did not mutate broker/account/order/deal/position state, credentials, remotes, MT5 order/history state, or VPS processes.

VPS apply/verify boundary:

```powershell
cd C:\Users\MSI\Documents\ai-trading-agent
git pull --ff-only

$py = ".\.venv-gtos\Scripts\python.exe"

& $py research\operations\final_moonshot_candidate_activation_readiness_2026_06_18\verify_candidate_activation_readiness.py
& $py research\operations\final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18\verify_candidate_enabled_unified_replay_mc.py
& $py research\operations\final_moonshot_candidate_subset_routing_dossier_2026_06_18\verify_candidate_subset_routing_dossier.py
& $py research\operations\final_moonshot_candidate_natgas_decomposition_2026_06_18\verify_candidate_natgas_decomposition.py
& $py research\operations\final_moonshot_candidate_full_book_live_activation_2026_06_18\verify_candidate_full_book_live_activation.py

& $py -m pytest `
  tests\ultimate_book\test_candidate_activation_readiness_artifacts.py `
  tests\ultimate_book\test_candidate_enabled_replay_mc_artifacts.py `
  tests\ultimate_book\test_candidate_subset_routing_dossier_artifacts.py `
  tests\ultimate_book\test_candidate_natgas_decomposition_artifacts.py `
  tests\ultimate_book\test_candidate_full_book_live_activation_artifacts.py `
  tests\ultimate_book\test_candidate_promotion_plumbing.py -q
```

Restart only the existing book workers by namespace after verification, using the current Windows supervisor surface. Do not restart MT5 terminals, Docker/Kasm, data bridges, tick capture/watchdog fleet, legacy `run_agent.py`, or unrelated processes.

Monitor after VPS reload:

- `pipeline_state\ultimate_book\operator_profile\heartbeat.json`
- `pipeline_state\ultimate_book\redacted_account_live_bee34003\heartbeat.json`
- `pipeline_state\ultimate_book\*\placed_decisions.jsonl`
- `shadow_logs\ultimate_book_launcher.jsonl`
- `shadow_logs\run_book_console.log`
- `shadow_logs\run_book_fn_console.log`
- `shadow_logs\book_supervisor.log`

The launcher cycle JSONL now includes a `bridge` object with `runtime_effect_now`,
`candidate_use_allowed_now`, `decision_status`, `reason`, `include_candidate_book`,
`candidate_book_profile`, `candidate_book_sleeves`, `dropped_symbols`,
`would_units`, `realized_units`, and `governor`. Per-unit rows include
`cluster`, `sleeve_members`, `n_trades`, `confidence`, `unit_risk_pct`,
`risk_pct_per_trade`, `sized`, `reason`, and `overlays_applied` when present.
Live candidate-book proof requires config true, `bridge.runtime_effect_now=true`,
`bridge.candidate_use_allowed_now=true`, the intended allowed sleeve in
`bridge.realized_units` when it fires, and placement ledger rows only for allowed
sleeves.

Alert or rollback on:

- `fail_closed_unknown_candidate_book_profile`
- `fail_closed_unknown_candidate_book_sleeves`
- any candidate sleeve outside the nine-sleeve allowlist
- any `NATGAS_cash` candidate generation or placed decision
- any `HEATOIL_c` candidate generation or placed decision
- `ceiling_profile_requires_smooth_ddefense`
- broad selector apply-to-execution becoming true while ultimate book is live
- heartbeat stale after worker reload
- candidate-book config on VPS differs from this packet

Rollback:

```yaml
ultimate_book_include_candidate_book: false
ultimate_book_candidate_book_sleeves: []
```

Then restart only the same two `run_book.py` workers by namespace and rerun the full verifier set above.
