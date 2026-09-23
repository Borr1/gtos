# GO-LIVE — Finalize the deploy module at the chosen sizing + sqrt-N + tick floors

Track: deployment-engineer finalize of `ultimate_book_live_package.py` for the Wave-7 FINAL deploy
book. Date 2026-06-15. Posture: DEFAULT-OFF / PREPARE-DON'T-FLIP. Nothing here places an order or
connects to a broker; the system stays hard-halted (GTOS_HARD_PRODUCTION_HALT.flag is the physical
control). All new behaviour ships behind the repo triple-gate, defaulting OFF.

## What was done (all in the route dir; no production src/ or config behaviour changed)

1. **Owner sizing baked in (default-off).** The W7 final-book NOMINAL dials are wired as allocation
   profiles + named constants, two-account balanced, with the Kelly-lite conviction multiplier:
   - `clean3_w7_measured_nom1p25` — **1.25% nominal FIRST CYCLE** + `kelly_lite=True` +
     `kelly_conservative=True` (half-Kelly, breach-free even under 1.5x stress).
   - `clean3_w7_growth_nom1p50` — **1.50% nominal STEP-UP** (after first account clears) + handset
     Kelly + `stress_derisk=True` (reactive ladder+coloss).
   - `clean3_w7_ceiling_nom2p00` — **2.00% nominal HARD CEILING** (max-aggression, not a default).
   - Kelly-lite handset bins `{n_active 1:0.85, 2-3:1.10, 4+:1.60}` capped at `OVERLAY_SIZEUP_MAX`
     (1.75); half-Kelly bins `{0.748, 0.991, 1.241}`. Default profile UNCHANGED (`balanced_0p75`);
     the owner opts into the W7 dial + `include_clean3=True` + `kelly_lite=True` at go-live.
   - (Pre-existing complementary profile kept: `clean3_firstcycle_eff1p18` = the static vol-matched
     form for a runtime NOT applying Kelly. The W7 nominal dials are canonical for the Kelly runtime.)

2. **sqrt-N within-sleeve same-day pooling folded.** `pool_same_day_sleeve_R(per_trade_R, sqrt_n=)`
   implements the KB7_stale_audit (b) convention: within-sleeve same-day `sum/len -> sum/sqrt(n)`,
   cross-sleeve untouched. Threaded through `size_correlated_units(..., sqrt_n_pooling=)` and
   `admit_and_size(...)` as a RECORDED convention (worst-case-stop risk is unchanged — the correlated
   cap `base*conf` is the safe invariant; sqrt-N is an EV-credit convention applied numerically in the
   return/MC path). **DEFAULT-OFF** so live sizing + recorded convention match the locked W7 MC; the
   owner opts into the refresh. The numeric fold + parity is proved by a new default-off integrator
   (`INTEG_W7_sqrtn_refresh.py`) — the W7 integrator had left sqrt-N out (it mean-pools at
   INTEG_portfolio_build_w2.build_matrix L225 and KB7 candidate_daily).

3. **HEATOIL_c + NATGAS_cash dropped from energy_agri + per-symbol tick spread floor added.**
   - `energy_agri` universe is now `(USOIL_cash, UKOIL_cash, CORN_c, COTTON_c)` (physically dropped).
   - `ENERGY_DROPPED_SYMBOLS` (canonical) + `W7_DROPPED_SYMBOLS` (alias) + `filter_w7_dropped_symbols`
     + `admit_and_size(..., drop_w7_symbols=)` fail-closed guard.
   - `TICK_SPREAD_FLOOR_R` per-symbol round-trip floor (R), MEASURED on the siliconmetatrader5 bridge
     (KB7_execution_truth.md + KB7_TICK_TRUTH_RESULT.json + ULTIMATE_TICK_SPREAD_GOLD.json):
     XAU 0.0118, XAG 0.0408, USOIL 0.0270, UKOIL 0.0258, NATGAS 0.3932, HEATOIL 0.9763, BTC 0.0001,
     DASH 0.0850, USDJPY 0.0841. Helpers `tick_spread_floor_for()` / `is_tick_tradeable()` (the
     per-SYMBOL replacement for the per-class cost map that failed both ways).
   - `describe_book()["clean3"]["w7_final"]` now surfaces the dropped symbols, tick floor table, Kelly
     bins, sqrt-N pooling block, and the three owner dials for the production wiring + go-live audit.

## Final deploy config (owner dial)

| stage | profile | nominal | Kelly | flags |
|---|---|---|---|---|
| first cycle | `clean3_w7_measured_nom1p25` | 1.25% | half-Kelly | include_clean3, kelly_lite, kelly_conservative, drop_w7_symbols |
| step-up (after 1st clear) | `clean3_w7_growth_nom1p50` | 1.50% | handset | + stress_derisk (reactive), kelly_conservative OFF |
| hard ceiling | `clean3_w7_ceiling_nom2p00` | 2.00% | handset | + stress_derisk; do not exceed |

Both accounts balanced. Default surface stays the locked 8-sleeve `balanced_0p75` book; the W7 book is
opt-in. Staged config = `GOLIVE_phaseA_config.patch` (broad selector_v4 + scheduler_v4 allocator
DISABLED from execution — the replacement) + `GOLIVE_ultimate_book_config_block.yaml` (triple-gated
ultimate_book_* block, all default-off). NEITHER is auto-applied.

## Refreshed numbers (LOCKED W2 MC engine, N=20000, FTMO 8%/5%/10%, BLOCK=5)

PARITY: the new integrator's mean-pool path reproduces the locked `INTEG_W7_FINAL_RESULT.json`
`final` headline **bit-for-bit across the full dial x {base, 1.5x-stress, 2.0x-stress}** on
(p_pass, maxDD, med_days); VS_final 0.7504 both. sqrt-N then folds as the only change.

| dial | mean P(pass) | sqrt-N P(pass) | mean maxDD | sqrt-N maxDD | mean str1.5 | sqrt-N str1.5 | daily-breach |
|---|---|---|---|---|---|---|---|
| **1.25%** | 99.36% | **99.84%** | 0.65% | **0.17%** | 79.1% | **85.4% (+6.25pp)** | 0.00% |
| **1.50%** | 98.59% | **99.50%** | 1.41% | **0.51%** | 73.5% | **80.9% (+7.46pp)** | 0.00% |
| 2.00% | 95.74% | 98.03% | 4.27% | 1.97% | 67.8% | 72.6% (+4.83pp) | 0.00% |

sqrt-N runs colder (VS_final 0.7504 -> 0.522 at equal book vol), so it is a strictly-better tail at the
same nominal: at 1.25%/1.50% it RAISES unstressed P(pass), HALVES+ the maxDD-breach prob, and lifts
the binding 1.5x-stress pass-rate +6-7pp, with daily-breach still 0% and worst stressed day inside
-5%. (The lift exceeds KB7_stale_audit's +1.9-2.2pp because that was the clean_3 base; here it stacks
on the Kelly-folded W7 final book.) Numbers in `INTEG_W7_SQRTN_REFRESH_RESULT.json`.

The locked W7 headline the module asserts parity against (mean-pooling, the conservative default):
**1.25% -> P(pass) 99.36% / maxDD-breach 0.65% / 79 median days / 0% daily-breach**;
**1.50% -> 98.59% / 1.41% / 66 days / 0% daily-breach**.

## Tests

`test_ultimate_book_live_package.py`: **95 pass** (was 78 at the start of this track; +14 W7-finalize
+ a W7 parity test added here, on top of the +2/+1 from a prior in-session pass). New coverage:
energy drop, dropped-symbol alias + filter, tick spread floor monotonicity + tradeability gate,
sqrt-N pooling (mean vs sqrt-N, edge cases, more-credit, flag recorded + risk-neutral), the three W7
nominal dials (sizes + monotone + governor-gated + headline parity to the locked artifact), the
drop_w7_symbols admit flag, describe_book W7 block, and `assert_w7_final_parity()` vs the locked MC.
Import-safety subprocess test still green (deployable surface pulls ZERO heavy deps). Run:
`PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 -m pytest $ROUTE/test_ultimate_book_live_package.py -q`
(no pytest under /opt/homebrew python3.14; /usr/bin/python3 3.9.6 has pytest+numpy+pandas).

## Guardrails honored

- No order / broker / network code; module is a pure decision/sizing/governor library (verified by
  the import-safety test).
- Every new behaviour ships behind a default-OFF flag; the locked default book is unchanged.
- Production `src/` untouched; `config/agent_config.yaml` NOT modified (the broad-selector disable is
  staged as `GOLIVE_phaseA_config.patch`, verified by `git apply --check`, NOT applied — config is
  pristine in the working tree). The patch was generated mechanically (apply-edit-diff-revert), not
  hand-typed, so it applies cleanly.
- Locked `INTEG_W7_FINAL_RESULT.json` is byte-untouched; the refresh writes a new file.
- No fabricated numbers: every tick floor / erosion / MC figure is sourced from the named KB JSON /
  the re-run locked-engine MC.

## Ready vs blocked

- READY (this Mac, default-off): module finalized + tested; owner dials + Kelly + sqrt-N + tick
  floors baked; refreshed MC quantified; Phase A config staged as a reviewed patch + YAML block.
- BLOCKED on owner/infra (NOT edge): apply the Phase A patch on explicit go; append + flip the
  ultimate_book_* triple-gate; Phase C broker/runtime authority (hard-halt forensic, V3-vs-live gap,
  dual-broker audit, production-return dossier, FTMO creds on the VPS); remove the halt flag.

## Files

- `ultimate_book_live_package.py` — energy drop, TICK_SPREAD_FLOOR_R + helpers, pool_same_day_sleeve_R,
  sqrt_n_pooling/drop_w7_symbols threading, W7 dials (pre-existing) + describe_book W7 extensions,
  `assert_w7_final_parity()`.
- `test_ultimate_book_live_package.py` — 95 tests.
- `INTEG_W7_sqrtn_refresh.py` -> `INTEG_W7_SQRTN_REFRESH_RESULT.json` — default-off sqrt-N fold +
  exact parity to the locked W7 mean-pool headline.
- `GOLIVE_phaseA_config.patch` — staged broad-selector/scheduler disable (verified, not applied).
- `GOLIVE_ultimate_book_config_block.yaml` — staged triple-gated ultimate_book_* block (default-off).
