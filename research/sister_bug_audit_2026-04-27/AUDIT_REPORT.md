# Sister Bug Audit — HALLUC-1 MSO-Render-vs-Underlying-Float Mismatch Class

**Date:** 2026-04-27
**Auditor:** Claude Opus 4.7 (max effort)
**Sister to:** `2c75f98` (HALLUC-1 fix), `project_eurusd_sl_root_cause`, `project_f12_us30_dual_mechanism_confirmed`
**Method:** Read-only static analysis of `src/components/`, `src/safety/`, `src/components/ai_tools/`
**Constraint:** $0 API. No code changes. Document bug class only.

---

## Executive summary

**Total sister bugs found: 6** (3 P0, 1 P1, 2 P2)

The HALLUC-1 fix patched ONE call site (`guard_candidate_inconsistent_pois`).
There are **5 additional places** where AI-emitted prices are compared against MSO underlying floats without precision-snapping. All are downstream of the SAME root cause:

> The MSO renders OB.high / OB.low / FVG.bottom / FVG.top / breaker.zone_low / breaker.zone_high to the AI at `prompt.price_format` (.1f for NAS100, .2f for XAUUSD/indices, .3f for JPY pairs, .5f for FX). Code-side comparisons against the underlying floats break when the rendered display value differs from the underlying.

The audit found **2 additional bug classes** beyond strict precision-vs-rendering mismatches that share the systemic root:
- **B-class:** Hardcoded `round(value, 2)` on AI-bound output that destroys FX/JPY precision (m5_refinement.py).
- **C-class:** Generous `_ob_tolerance(price) = price × 0.002` masks the precision delta in some sites; the bug is latent but not currently triggering decisions.

---

## Severity rubric

- **P0:** Blocks correct trades or alters live trade parameters in production. NAS100 (.1f) is the canonical hit; FX (.5f) and JPY (.3f) also affected by hardcoded-2dp variants.
- **P1:** Affects a path that's currently DISABLED but ships hot for activation; bug is latent.
- **P2:** Affects shadow data only (no trading impact); analytics could be slightly off.
- **P3:** Tangential / noted but not in the bug class.

---

## Per-bug table

| # | Severity | File:line | Comparison | Bug | Recommended fix |
|---|----------|-----------|------------|-----|-----------------|
| 1 | **P0** | `src/components/verification.py:734` | `sl >= zone_low` (LONG, breaker_re_entry) | Strict, no tolerance, AI-emitted SL vs MSO `BreakerBlock.zone_low` underlying float | Snap `zone_low` to `price_format` precision before compare; OR inject tick-floor like ADR-006 sl_beyond_ob |
| 2 | **P0** | `src/components/verification.py:743` | `sl <= zone_high` (SHORT, breaker_re_entry) | Strict, no tolerance, AI-emitted SL vs MSO `BreakerBlock.zone_high` underlying float | Same as #1 mirrored |
| 3 | **P0** | `src/components/m5_refinement.py:642-644` | `round(final_sl, 2)`, `round(final_tp, 2)`, `round(final_sl_dist, 2)` written to `tp.stop_loss` / `tp.take_profit_1` via `apply_m5_overrides()` | Hardcoded 2dp ROUNDS GBPUSD/EURUSD/USDJPY/JPY-cross SLs/TPs to 2 decimals — destroys precision (e.g. 1.05123 → 1.05). NAS100 keeps 2dp = harmless. FX = catastrophic. **B-class** | Replace `round(x, 2)` with `_snap_to_precision(x, decimals_from_price_format)` mirroring HALLUC-1 helper |
| 4 | **P0** | `src/components/verification.py:627` | `if sl >= matched_fvg.bottom` (LONG, fvg_fill) | Strict, no tolerance, AI-emitted SL vs MSO `FairValueGap.bottom` underlying float | Snap `matched_fvg.bottom` to `price_format` before compare |
| 5 | **P0** | `src/components/verification.py:640` | `if sl <= matched_fvg.top` (SHORT, fvg_fill) | Strict, no tolerance, AI-emitted SL vs MSO `FairValueGap.top` underlying float | Same as #4 mirrored |
| 6 | P1 | `src/components/permissions.py:593, 607` (`_ob_retest_sl_exception_applies`) | `tp.stop_loss < ob.low` (LONG), `tp.stop_loss > ob.high` (SHORT) | Strict, no tolerance, AI-emitted SL vs MSO `OrderBlock.low/high` underlying float. Bypasses `sl_floor` only when SL is "structurally" beyond OB. Rendering-collision direction silently FAILS the exception → falls through to sl_floor reject. Same NAS100 .1f class. | Snap `ob.low/high` to `price_format` precision before compare. Same helper as HALLUC-1. |
| 7 | P2 | `src/components/permissions.py:728, 733, 736` (`_reject_if_sl_behind_liquidity_cluster`) | `pool.price > tp.entry_price` (LONG eligibility), `abs(pool_price - tp.stop_loss)` distance computation | `pool.price` is unrendered MSO float; AI saw rendered version (renders at `_PRICE_FMT` per primary_analyzer_prompt.py:1135). When AI emits an SL aligned with the rendered pool price, distance computation may flip the gate. Currently DISABLED in shipping config; bug is latent. | When `gate1.sl_liquidity_cluster_enabled` is flipped to `true`, snap `pool.price` to `price_format` before distance compare. |

---

## Cross-component pattern

The single underlying root cause is well-isolated:

> **An MSO geometric primitive (OB/FVG/Breaker/Pool) is rendered into the prompt at `prompt.price_format` precision; the AI emits trade parameters at that same precision per the SELF-CHECK rules in `primary_analyzer_prompt.py`; downstream code compares the AI-emitted parameter against the MSO's UNRENDERED underlying float.**

When the underlying value's precision exceeds the display format (e.g. NAS100's `.1f` vs underlying `.2f`+), the rendered and underlying values differ. Strict `<`, `>`, `<=`, `>=` comparisons then deterministically violate even when the AI placed its emission "at the edge" of what it was shown.

**Per-instrument severity (decoded by `prompt.price_format`):**
| Instrument | price_format | Decimals dropped | NAS100-class severity |
|------------|--------------|-------------------|------------------------|
| NAS100 | `.1f` | underlying may have 2 (e.g. 27262.16) | **HIGH — confirmed live 93% rate before HALLUC-1** |
| XAUUSD, US30_cash, XAGUSD | `.2f` | underlying ≥ 3 (e.g. 2391.234) | Latent; underlying may have third decimal from MT5 |
| USDJPY, GBPJPY | `.3f` | underlying ≥ 4 | Latent |
| GBPUSD, EURUSD (FX) | `.5f` | underlying = 5 typically (no extra decimal expected; safer) | Latent but rare |

NAS100 is the only instrument where the rendering delta routinely exceeds 1 display tick, because indices have 2-decimal underlying values rendered at `.1f`. Other instruments would only hit the bug class on edge-case underlying precision overflows (e.g. XAUUSD with a quote precision >2dp).

---

## Sites confirmed SAFE (no fix needed)

| Site | Why safe |
|------|----------|
| `verification.py:_check_sl_beyond_ob` (lines 824-892) | ADR-006 tolerance-tier model with `verification.sl_beyond_ob_tick_floor`. Tick floor absorbs precision delta. |
| `verification.py:_check_entry_in_ob` (lines 471-513) | Uses `_ob_tolerance(entry, config) = entry × 0.002` (0.2% of price). For NAS100 at 27262 → 54-pt tolerance, far larger than any rendering delta. |
| `verification.py:_check_h1_poi_exists` (lines 277-404) | Same `_ob_tolerance` (0.2%) generosity. |
| `verification.py:_check_entry_in_fvg` (line 611, entry-in-range only) | Uses `_ob_tolerance` for the in-range check. (SL strict-< checks at lines 627/640 ARE vulnerable — see #4/#5.) |
| `verification.py:_check_entry_in_breaker` (line 723, entry-in-zone only) | Uses `_ob_tolerance` for entry. (SL strict-< checks at lines 734/743 ARE vulnerable — see #1/#2.) |
| `permissions.py:_find_target_ob` (line 417) | `ob_tol = sl_buffer_dollars` (NAS100 = 15.0, XAUUSD = 1.20). Generous enough to absorb sub-tick rendering delta. Safe in practice. |
| `permissions.py:_reject_if_touch_count_too_high` | Receives the OB from `_find_target_ob` — inherits its safety. |
| `permissions.py` Gate 1 TP/SL geometry (lines 846-948) | All comparisons are AI-vs-AI (entry vs SL vs TP1 — all from `tp.*`); no MSO floats involved. Safe per HALLUC-1's audit logic. |
| `m5_refinement.py:_find_matching_h1_ob` (line 210) | Tolerance = `entry × 0.002` (0.2%). Safe. |
| `m5_refinement.py:clamp_m5_sl_to_ob_boundary` (lines 305+) | Uses `ob_low - buffer` math; `m5_sl < target` strict, but `target = ob_low - buffer` includes ATR-derived buffer which dominates rendering delta. Safe. |
| `execution.py` SL/TP comparisons (lines 547-548, 561, 699-707) | `current_price` comes from MT5 tick (broker reality), not from MSO. Different precision plane — not the bug class. |
| `proximity_shadow_logger.py` | Parses prices from rendered MSO TEXT (user_message), so both sides of comparison are in the AI's display plane. Consistent. |
| `be_shadow_logger.py` | All comparisons `current_price` (MT5 tick) vs `entry_price` (MT5 fill). MT5-vs-MT5, not MSO-vs-AI. |
| `touch_count_gate_logger.py` | Receives data from caller; logs only. |
| `sl_beyond_ob_shadow_logger.py` | Same — observation-only. |
| `cross_instrument_correlation_gate.py` | No price comparisons; correlation-matrix arithmetic only. |
| `pre_ai_gates.py` | Existence checks only — no AI-vs-MSO price comparison. |
| `direction_emission_logger.py`, `structure_detector_shadow_logger.py`, `d1_bias_lag_logger.py` | No price comparisons of the bug class. |
| `regime_classifier.py`, `regime_shadow_logger.py` | No AI/MSO price comparisons. |
| `cross_instrument_correlation_gate.py` | No price comparisons. |
| `safety/heartbeat_monitor.py`, `safety/dormant_state.py`, `safety/equity_guard.py`, `safety/sprt_class_halt_check.py` | No AI/MSO price comparisons. |
| `orchestrator.py:_log_ob_retest_event` (line 3459) | `ob.low <= current_price <= ob.high` where `current_price` is MT5 tick. MT5-vs-MSO; not the AI-vs-MSO bug class. Dedup tolerance 0.5 is XAUUSD-tuned but shadow-only (P3). |

---

## Other findings out of bug-class scope

- `orchestrator.py:3464-3465` — `abs(... - ob.high) < 0.5` is hardcoded 0.5 dedup tolerance. For FX (1.05XXX), 0.5 always matches — degenerate dedup. Shadow log only. P3. Same hardcoded-tolerance failure pattern as the round(2) issue but in dedup not trade decisions.
- `proximity_shadow_logger.py:196` — `round(current_price, 5)` hardcoded; safe for FX/JPY but truncates XAUUSD/index 6-digit prices. Log-only. P3.
- `verification.py:811-820` — `round(current_price, 2)` and `round(entry_price, 2)` in mso_value/ai_value reporting only (decision unaffected). P3.
- `data_ingestion.py:322` — `round(avg_price, 2)` for spread reporting. Display-only. P3.

---

## Recommended ship priority

1. **Ship #3 first (m5_refinement.py:642-644 hardcoded 2dp ROUND).** This is the single most damaging finding because it WRITES corrupt values back into trade parameters and is unconditionally active for every M5-refined trade on FX/JPY/USDJPY/GBPJPY. Replace `round(*, 2)` with `_snap_to_precision(*, decimals_from_price_format(config))`.

2. **Ship #1 + #2 + #4 + #5 together.** All four are strict-< / strict-> SL placements against `zone_low`/`zone_high`/`fvg.bottom`/`fvg.top`. Single helper applied to four call sites. Pattern matches HALLUC-1 (`_snap_to_precision` + `_decimals_from_format`); helper already exists in `primary_analyzer.py:705-728` and could be promoted to `src/components/__init__.py` or a shared `precision.py` module.

3. **Defer #6 (permissions.py:593/607).** Lower live impact: the strict-< check is inside the BYPASS-EXCEPTION (`_ob_retest_sl_exception_applies`); a precision-collision FAILS the exception, which routes to the standard sl_floor + ATR check. The standard check uses geometric distance (not strict zone comparison), so the bug effectively "no-ops" without affecting trade safety. Worth fixing for consistency, not urgency.

4. **Defer #7 (permissions.py:728-736).** Currently DISABLED via config. When CEO flips `gate1.sl_liquidity_cluster_enabled` to true, fix this in the same commit.

---

## Notes on the bug class

This audit confirms that HALLUC-1 was correctly diagnosed as a CLASS bug, not a single-instance bug. The systemic remedy (a `_snap_to_precision` helper used wherever AI prices touch MSO floats) is correct. The bug class will continue to surface anywhere the codebase adds new strict comparisons unless the helper is institutionalized.

**Suggested institutionalization** (out of audit scope; CEO decision):
- Move `_decimals_from_format` + `_snap_to_precision` from `primary_analyzer.py` to a shared `src/components/precision.py` module.
- Add a lint rule or CI grep for `tp\.(stop_loss|entry_price|take_profit_1).*[<>=].*\b(ob|matched_ob|fvg|matched_fvg|breaker|matched_bb|pool)\.` patterns.
- Document in `.context/06_decisions/` an ADR on the precision contract between MSO rendering and downstream comparisons.
