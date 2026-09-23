# VPS Codex Ultimate Activation Handoff

Date: 2026-06-18

Status: owner-approved repo config activation package; no broker action, remote push, or VPS reload executed by
this Mac route.

## Active Intended Package

The repo config now describes the strongest current evidence-backed package:

- `ultimate_book_enabled: true`
- `ultimate_book_apply_to_execution: true`
- `ultimate_book_live_activation_allowed: true`
- `selector_v4_apply_to_execution: false`
- `ultimate_book_include_candidate_book: true`
- `ultimate_book_candidate_book_profile: runtime_executable_native_exit_v2`
- `ultimate_book_include_market_expansion_book: true`
- `ultimate_book_market_expansion_policy: positive_weighted12_after_swap`
- `ultimate_book_profile: clean3_w7_ceiling_nom2p00`
- `ultimate_book_kelly_lite: true`
- `ultimate_book_kelly_conservative: true`
- `ultimate_book_kelly_running_count: true`
- `ultimate_book_stress_derisk: true`
- `ultimate_book_metals_confluence_gate: true`
- `ultimate_book_drop_w7_symbols: true`
- `ultimate_book_derisk_mode: smooth`

Bridge library defaults remain safe/off. The active repo config is intentionally owner-activated for VPS
handoff.

## Runtime Generation Parity Fix

This branch also fixes the deploy-critical named-policy generation path:

- `ultimate_book_market_expansion_policy: positive_weighted12_after_swap` now feeds engine generation,
  owner manageable-symbol/pair management, and launcher D1 scheduling even when
  `ultimate_book_market_expansion_sleeves: []`.
- `ultimate_book_sqrt_n_pooling` is now bridge-wired into `admit_and_size`; the active config keeps it
  `false`, so current behavior is unchanged until owner-armed.

VPS Codex must verify this with `tests/ultimate_book/test_market_expansion_runtime_generator.py` and
`tests/ultimate_book/test_launcher.py` before any reload.

## Current Numbers

Evidence classes are replay/MC, not broker-real future PnL.

| Package | Monthly | Sharpe | MC Pass | Max-DD Fail | Worst Day | MaxDD |
|---|---:|---:|---:|---:|---:|---:|
| A8 active reference | `2.646%` | `0.147757` | `0.99055` | `0.00945` | `-2.66%` | `8.695125R` |
| Candidate-book reference | `4.969%` | `0.277408` | `0.9999` | `0.0001` | `-2.16%` | `8.766924R` |
| Active intended package: positive12 expansion | `5.09%` | `0.28419` | `0.9999` | `0.0001` | `-2.083%` | `8.842614R` |
| Defensive fallback: robust6 expansion | `5.052%` | `0.282076` | `0.9998` | `0.0002` | `-2.075%` | `7.956872R` |

Interpretation:

- The main current lift is A8 active reference -> candidate book: monthly `2.646%` to `4.969%`.
- The strongest conditioned expansion adds a further `+0.121%` monthly and `+0.006782` Sharpe versus the candidate book.
- The robust fallback gives slightly less return but cuts maxDD by `0.810052R` versus the candidate book.

## Deployment Commands For VPS Codex

Run from the VPS repo after absorbing this branch/package:

```bash
python3 scripts/generate_live_state.py
python3 -m py_compile src/components/ultimate_book/admission.py src/components/ultimate_book/bridge.py src/components/ultimate_book/book_engine.py src/components/ultimate_book/book_owner.py src/components/ultimate_book/launcher.py src/components/ultimate_book/sleeves/candidate_registry.py
python3 research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/verify_market_expansion_conditioned_policy_runtime_alias.py
pytest tests/ultimate_book/test_market_expansion_runtime_generator.py -q
pytest tests/ultimate_book/test_launcher.py -q
pytest $(rg --files tests/ultimate_book | rg 'market_expansion') -q
python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18 --full-jsonl
```

Before live reload, VPS Codex must verify:

- the active VPS config matches the repo keys above;
- `describe_bridge()` reports bridge default config safe/off and active config owner-on;
- runtime packet logs include `include_market_expansion_book=true` and `market_expansion_policy=positive_weighted12_after_swap`;
- candidate book, A8 confluence gate, smooth derisk, symbol damage/open-position safeguards, and W7 dropped-symbol filter remain active;
- rollback commands are prepared before reload.

## Rollback

Primary performance rollback:

```yaml
ultimate_book_market_expansion_policy: "robust6_every_split_positive"
ultimate_book_market_expansion_sleeves: []
```

Full market-expansion rollback:

```yaml
ultimate_book_include_market_expansion_book: false
ultimate_book_market_expansion_policy: "explicit_allowlist"
ultimate_book_market_expansion_sleeves: []
```

Full candidate-book rollback:

```yaml
ultimate_book_include_candidate_book: false
ultimate_book_candidate_book_sleeves: []
```

## Ultimate System Plan From Here

1. Deploy current strongest package on VPS with parity, monitoring, and rollback.
2. Expand MT5 bridge exports across M1/M5/M15/H1/H4/D1 OHLCV/tick-volume for every active and candidate market.
3. Build rolling replay partitions across many symbols, sessions, volatility regimes, and market phases.
4. Train/tune only after clean labels exist: mechanical baselines first, then meta-label/model candidates with purged/embargoed splits.
5. Add runtime learning ledgers for sleeve contribution, fill quality, spread/swap drag, symbol damage, missed opportunity, and regime state.
6. Turn every weak idea into a feature, veto, sizing hint, risk cap, watch item, or successor experiment instead of deleting useful intelligence.
7. Iterate package promotion through replay/MC/stress/holdout plus VPS packet parity, then update config only when the package is stronger than the current live-intended baseline.
