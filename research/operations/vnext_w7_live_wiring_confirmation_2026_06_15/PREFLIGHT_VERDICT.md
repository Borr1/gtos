# GL-5 Pre-flight Verdict — W7 book, FTMO primary (read-only, NO orders placed)

Date: 2026-06-15. All checks below are read-only / in-memory; the config file is untouched and no
order path was exercised (engine.evaluate + gate dry-runs only).

## GREEN

1. **11/11 sleeves** registered, route-parity-verified (each against the REAL route oracle), contract-
   clean (test_generator_contract drives every generator with the engine's exact call). Suite: 86 pass.
2. **Full-book live wiring** on FTMO (`run_book.py --once`): both decision cadences advance
   (advanced_tf=[H4, M15]), all 11 sleeves run on live bars, the M1 vp aux fetch works (vp fired a
   shadow signal on a prior bar), place=False (halt present), 0 orders, ~2s/cycle.
3. **Order path clears all 3 fail-closed gates** with a REAL sized unit (dry-run, no send):
   GATE1 dyn-policy None, GATE3 risk resolved = override (no error), GATE2 allow/no-block/no-fatal,
   cost PASSED. Verified for metals (0.5%) and crypto (1.32% tilted).
4. **Gross risk governor-capped**: a full multi-cluster day sizes to 3.72% gross < 4.0% cap.
5. **Safety**: idempotency (one place per sleeve/symbol/bar), kill-switch + halt force observe-only,
   open_trade enforces the 3 halt flags (runtime_control.enabled=true), governor 3% soft daily stop /
   4% gross / 7% derisk. Replacement invariant satisfied (selector_v4_apply_to_execution=false).
6. **Contract sizes** per the live broker verified earlier (no 10x hazard on FTMO).

## ONE DISCLOSURE (owner decision before real orders)

The owner-chosen profile `clean3_w7_measured_nom1p25` is NOMINAL 1.25% per unit with the **Kelly-lite
conviction tilt** (kelly_lite + kelly_conservative = half-Kelly). The tilt means a high-conviction
cluster sizes slightly ABOVE 1.25%:

| cluster | sized risk/unit |
|---|---|
| crypto | **1.3186%** (tilted up) |
| energy | 1.2410% |
| substrate | 0.6981% |
| index / jpy | 0.2327% |
| metals / volprofile | (no realized unit in the sample) |

- This is the profile's DESIGNED behavior — its validated breach stats (P(both) base 99.28%, fwd
  99.19%, 1.5x-stress 63.7%, **daily-breach 0%**) are computed WITH this tilt on. The execution gate
  accepts it (selected_cell_risk_pct is set = the tilted override, so override ≤ cell_risk holds).
- Gross is governor-capped at 4% (sample 3.72%).
- A HARD 1.25% per-unit cap would DEVIATE from the validated profile (changing the edge the route
  measured), so it is not the default.

**Decision for the owner:** run the validated nom1p25 profile as configured (per-unit may tilt to
~1.32% on crypto, gross-capped) — RECOMMENDED — or impose a hard 1.25% per-unit cap (deviates from the
validated edge). Everything else is GO. See GO_LIVE_RUNBOOK.md for the flip.
