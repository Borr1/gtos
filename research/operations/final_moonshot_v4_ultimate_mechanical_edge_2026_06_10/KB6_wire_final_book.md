# KB6 — Wire clean_3 + confluence overlays into the live package & FINAL go-live dossier

Builder track, 2026-06-15. Consolidate the data-chosen Wave-5 deploy book (`clean_3`) and the
validated confluence overlays into the deployable surface (`ultimate_book_live_package.py`), apply the
vol-matched risk rescale, extend the tests, and refresh the FINAL go-live dossier. Result-first.

## 0. What shipped (consolidated book)

DEPLOY BOOK = **`clean_3`**: locked W3 8-sleeve core + 3 additive sleeves
`sub_xvol_pullback (0.45)` + `vp_euidx_pocgrav (0.30)` + `sub_mid_dn_revert (0.20)`, deployed at the
**vol-matched effective 0.71%/0.71% per risk-unit** (0.75% nominal × vol_scale 0.9481), with two
confluence size-up SELECTORS wired on their base sleeves:
- `leader_impulse_veto` (1.5x on `sub_xvol_pullback` when `ll_impulse=none`) — base +0.71R → +1.53R
  fwd, perm-p 0.0003, both fwd years; mirror (leader opposed) fwd-negative −0.35R.
- `session_active_stack` (1.15x on `sub_xvol_pullback`, `sub_mid_dn_revert` when H4 hour ∈ {8,12,16}).

All three additives + both overlays are **DEFAULT-OFF** in the deployable module — the owner flips
`include_clean3=True, overlays=True` at go-live. The default surface stays the locked 8-sleeve book.

## 1. Changes made

### `ultimate_book_live_package.py` (extended, import-safe, zero heavy deps)
- `CLEAN3_REGISTRY` — 3 additive `SleeveSpec`s (conf 0.45/0.30/0.20), NEW corr clusters
  `substrate`/`volprofile` (independent of the core, per the W5 corr matrix).
- `CLEAN3_VOL_SCALE = 0.9481` — the risk-equivalent rescale; diversification banks as a higher
  pass-rate FLOOR, not bigger bets.
- `CONFLUENCE_OVERLAYS` (`leader_impulse_veto`, `session_active_stack`) + `overlay_sizeup_for()` —
  bounded, compounding, capped at `OVERLAY_SIZEUP_MAX = 1.75` (governor-safe). Overlays apply ONLY to
  declared base sleeves and ONLY when their leak-free condition holds; default-off.
- `TradeIntent` gained leak-free advisory fields `ll_impulse` + `decision_hour` (pure facts at the
  decision bar; absent → no size-up).
- `effective_registry(include_clean3)` / `cluster_of()` — toggle the active book; LOCKED-BOOK cluster
  map kept core-only (5 cluster ids), clean_3 clusters resolved separately so the default surface is
  unpolluted.
- `size_correlated_units(..., include_clean3, overlays)` + `admit_and_size(..., include_clean3,
  overlays)` — clean_3 sleeves are FAIL-CLOSED (unknown) unless enabled; overlay size-up raises unit
  confidence on matching base sleeves.
- Allocation profiles `clean3_balanced_eff0p71` (RECOMMENDED) + `clean3_conservative_eff0p47` (first
  cycle) at vol-matched effective risk; `CLEAN3_DEFAULT_PROFILE`.
- `describe_book()` → schema `v2` with a `clean3` block (sleeves, vol_scale, overlays, profiles, full
  cluster map). `assert_clean3_parity()` — parity vs the locked deploy artifact.

### Integrator side (already wired — verified, not disturbed)
`INTEG_portfolio_build_w5.py` is the canonical Wave-5 integrator and ALREADY carries all clean_3
generators (`gen_sub_xvol_pullback`, `gen_vp_euidx_pocgrav`, `gen_sub_mid_dn_revert`) at conf
0.45/0.30/0.20 plus the overlay generators (`gen_xlayer_veto_gate`, `gen_subh4_ll_fx`).
`INTEG_w5_clean3_deploy.py` finalizes the deploy MC → `INTEG_W5_CLEAN3_DEPLOY.json`.
NOTE: the W1 baseline `INTEG_portfolio_build.py` has intentionally-frozen older confidence weights
(crypto 0.70, etc.) as the locked baseline of the W2/W3 parity chain; editing it would corrupt that
chain, so the clean_3 wiring lives in the W5 integrator + the live package, not the frozen baseline.

### `test_ultimate_book_live_package.py` (31 → 52 tests)
+21 tests: clean_3 registry/locked-conf, default-off + fail-closed-when-off + sized-when-on,
substrate-collapse-to-one-unit, vol-scale + vol-matched profiles, overlay veto/session/compound/cap,
base-sleeve scoping, overlay-off-by-default, admit_and_size clean_3 path, clean_3 parity vs deploy
artifact, describe_book v2 serializability, and import-safety (zero heavy deps on the deployable path,
checked in a clean subprocess).

### `ULTIMATE_GO_LIVE_DOSSIER.md` (refreshed)
Replaced the superseded 2026-06-14 single-gold-sleeve dossier with the `clean_3` book net of fills:
trades/yr (~1717 fwd), P(pass) grid, 1.5x stress, 2-account allocation (balanced 0.71% recommended),
confluence overlays, deployable-surface description, and the GO-LIVE CHECKLIST (disable broad selector
+ scheduler, wire default-off → owner flip, size vol-matched, clear runtime/broker-authority blocker).

## 2. Consolidated book — key numbers (net of real cost, leak-free labeler)

| metric | value |
|---|---|
| sleeves | 11 (8 core + 3 additive) |
| avg off-diag daily-R corr | +0.0027 (min -0.119, max +0.116) |
| Sharpe | 0.1522 (book-only 0.1396) |
| trades/yr fwd | ~1717 (book ~1512 + additives ~205) |
| daily mean (all / fwd) | +0.0913 / +0.2796 unit-R |
| vol_scale | 0.9481 → effective 0.711% at 0.75% nominal |
| P(pass) @1% vol-matched | 99.91% (book 99.79%) |
| STRESS 1.5x @1% vol-matched | 80.86% (book 82.66%) — the ~1.8pt price of the additive breadth |
| P(both pass) balanced 0.71% | base 99.99% / FWD 100% / STRESS1.5x 70.30% |
| daily-breach (all sizes) | 0.00% (worst day -2.02% @1%) |

## 3. Verification status

- **Tests: 52 passed** (`/usr/bin/python3 -m pytest`, py3.9 has pytest+numpy; the homebrew 3.14 lacks
  pytest, the project .venv lacks numpy — documented).
- **Import-safety: PASS** — the deployable module pulls ZERO heavy deps on import (no numpy/pandas/
  substrate/integrators); the parity functions import the integrator/artifact LAZILY only.
- **Replay-vs-module parity: PASS** — `INTEG_w5_clean3_deploy.py` re-run reproduces
  `INTEG_W5_CLEAN3_DEPLOY.json` byte-identically; `assert_clean3_parity()` confirms the module's conf
  weights + vol_scale + 11-sleeve book == the artifact; `assert_confidence_parity()` confirms the 8
  core weights == the W2 integrator.

## 4. Honest caveats (carried into the dossier)

Short forward window (2025 + partial 2026); VP layer is forward-only (M1-since-2024); substrate/VP
additives answer a fixed 1:3R question while the deployed exit is STATE_D scale-out (re-mine next);
1.5x stress 80.86% @1% is the honest ceiling — challenge-robust, not stress-bulletproof; the deploy
surface has zero broker authority by design (runtime/broker-authority blocker is the real gate).

## 5. Files
- `ultimate_book_live_package.py` (extended), `test_ultimate_book_live_package.py` (52 tests)
- `ULTIMATE_GO_LIVE_DOSSIER.md` (refreshed), `INTEG_W5_CLEAN3_DEPLOY.json` (locked, reproduced)
- integrators verified intact: `INTEG_portfolio_build_w5.py`, `INTEG_w5_clean3_deploy.py`
