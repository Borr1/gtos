# V5 A5 Review: `guard_candidate_inconsistent_pois` validator

**Commit:** `385055b feat(safety): post-AI validator for POI/entry/SL consistency`
**Branch:** `worktree-agent-a432468d`
**Reviewer:** Independent code review (Opus 4.7, max effort)
**Date:** 2026-04-24

---

## Verdict

**APPROVE WITH CONDITIONS.** The validator is correctly implemented, adequately tested, and correctly catches the Thursday 2026-04-23 US30 NY 16:00 class of bug. One legitimate false positive was found in recent production data (USDJPY 2026-04-22 15:15), and one minor semantic concern exists around inclusive-bound semantics.

**Conditions before merge to main:**
1. CEO should confirm the USDJPY-2026-04-22-15:15 demotion is acceptable (it blocks a setup that L2 passes via its 0.2% tolerance window).
2. Consider scoping the guard to `ob.mitigated == False` to better mirror L2 behavior (currently it matches mitigated OBs too, which is OK-in-practice but creates rationale mismatch).

**Blast radius:** LOW. Past 7 days show 0 executions blocked; whole-history shows 1 of 30 LIMIT_PLACED trades would be demoted (that one never filled anyway). Guard lives inside `PrimaryAnalyzer.analyze()` so it only affects the path between AI-response parsing and L2 verification.

---

## 1. Correctness of each check

### 1.1 OB matching logic

Code: `src/components/primary_analyzer.py:721-742`

```python
matching_obs = [ob for ob in h1_tf.order_blocks if ob.low <= poi_level <= ob.high]
```

- **0 matches:** returns unchanged (defer to L2 `h1_poi_exists`). Correct.
- **1 match:** uses it.
- **2+ matches:** picks `ob` with smallest `min(abs(ob.low - entry_price), abs(ob.high - entry_price))`.

**Finding:** the 2+ match tie-breaker uses the **nearest edge distance**, not the overall geometric distance to the OB zone. This is a subtle but correct choice:

- For a LONG pullback, entry should be near the OB high (pullback into OB from above). Nearest-edge metric captures that.
- For a SHORT rally into OB from below, entry near OB low. Nearest-edge still captures it (distance to OB low is smaller).
- Pathological case: entry WAY beyond both OB edges, both in the same direction. Then the closer edge wins; the OB chosen might not be the one the AI "meant." But in that case entry is outside the OB anyway → demote regardless of which OB is chosen. Safe.

Verified against the ambiguity test (`test_ambiguous_overlapping_obs_picks_closest`) — walked through Case A (tight OB wins, entry inside) and Case B (tight OB wins, entry outside) — both correct.

### 1.2 Entry check

Code: `src/components/primary_analyzer.py:746-751`

```python
if not (matching_ob.low <= tp.entry_price <= matching_ob.high):
    reasons.append(...)
```

- **Inclusive bounds:** entry at exact `ob.low` or `ob.high` passes. Intentional per agent design.
- **No direction-specific check:** both LONG and SHORT just require entry inside the OB zone. This is weaker than a "LONG must enter near OB high / SHORT near OB low" check but mirrors L2 `_check_entry_in_ob` (`src/components/verification.py:453-495`) exactly, minus the tolerance window.
- Brief agent doc says "entry_price in [matching_ob.low, matching_ob.high] for BOTH LONG and SHORT" — confirmed in code.

**Concern (minor):** L2 uses a `_ob_tolerance(price, config)` of ~0.2% (`verification.py:91-94, :480`). The new guard uses strict bounds. **This is the root cause of the one false positive found (USDJPY 2026-04-22-15:15).** See section 4.

### 1.3 SL check

Code: `src/components/primary_analyzer.py:754-765`

```python
# LONG
if not tp.stop_loss < matching_ob.low:
    reasons.append(...)
# SHORT
if not tp.stop_loss > matching_ob.high:
    reasons.append(...)
```

**Strict `<` / `>` operators verified.** Matches L2 `_check_sl_beyond_ob` (`verification.py:520-547`) — both use strict `<`/`>` with NO equality. 

SL exactly at `ob.low` for LONG would fail both the new guard and L2 (correct — SL at zone edge gets run over). Consistent with the longstanding Apr 14 `sl_beyond_ob` pattern; agent documentation says it mirrors L2 convention, which is true.

### 1.4 TP1 direction check

Code: `src/components/primary_analyzer.py:768-779`

```python
# LONG
if not tp.take_profit_1 > tp.entry_price:
    reasons.append(...)
# SHORT
if not tp.take_profit_1 < tp.entry_price:
    reasons.append(...)
```

- **Strict inequality:** TP1 at exactly entry price = fail. Fine (degenerate case, would already be caught by `guard_candidate_degenerate_params` which uses `math.isclose(..., abs_tol=1e-9)`).
- **Overlap with prompt self-check:** by design, the agent calls this "defensive double-check." Acceptable.
- **No double-demotion:** `guard_candidate_degenerate_params` runs first. If it demotes (e.g. entry==TP1 bit-exact), then `guard_candidate_inconsistent_pois` sees `result.decision != "CANDIDATE"` and returns unchanged (`primary_analyzer.py:705`). No risk of double-counting.

### 1.5 Skip conditions

Code: `primary_analyzer.py:705-719`

- `decision != "CANDIDATE"` → return. Good.
- `trade_parameters is None` → return. Good. (Defensive; `guard_candidate_null_params` already handles this, but redundant safety is fine.)
- `poi_level == 0.0` (Pydantic default) → return. Good. Correctly treats "not reported" as pass-through.
- `mso.timeframes["H1"] is None` → return. Good. Conservative.

All skip conditions are correct.

---

## 2. Counterfactual test validity (`test_poi_and_entry_different_obs_demotes`)

Test at `tests/test_primary_analyzer.py:549-575`.

### 2.1 Does the test match the actual Thursday case?

**Partially.** Verified against `knowledge_base/trade_records/US30_cash/2026-04-23_ny_1600.json`:

| Field | Test fixture | Actual production |
|---|---|---|
| POI | 48531.325 ✓ | 48531.325 ✓ |
| Entry | 48645.71 ✓ | 48645.71 ✓ |
| SL | 48450.0 (fabricated; "would pass if touches=4 OB matched") | 48599.49 (real; both SL and entry fail) |
| TP1 | 48800.0 ✓ (any > entry passes the direction check) | 48714.98 |
| Direction | LONG ✓ | LONG ✓ |
| touches=4 OB | [48472.35, 48590.30] ✓ | [48472.35, 48590.30] ✓ |
| "touches=2" OB | **[48590.30, 48645.71]** (wrong) | **[48629.71, 48645.71]** (real) |
| Real mitigated OBs | absent | touches=29 [48456.81, 48545.41] (mitigated, but CONTAINS POI) |

**The test fixture omits the mitigated OB that ALSO contains the POI.** In real production data, the 2+ match branch engages (touches=29 mitigated OB + touches=4 unmitigated OB both contain POI 48531.325). In the test fixture, only one OB contains POI (single-match branch). This means the test **does not exercise the multi-match tie-breaker for this specific case.**

**Impact:** the test still proves the guard demotes when POI and entry map to different OBs. But it under-tests the 2+ match branch the real production data actually hits. The `test_ambiguous_overlapping_obs_picks_closest` test covers the tie-breaker separately, so total test coverage is OK.

### 2.2 Does the test actually fail on pre-fix code?

Verified. I checked out the pre-fix `primary_analyzer.py` (commit `8a9bcfe`) with the post-fix `tests/test_primary_analyzer.py`:

```
ImportError: cannot import name 'guard_candidate_inconsistent_pois' from 'src.components.primary_analyzer'
```

Pre-fix, the test collection fails with ImportError. Pre-fix, the guard function doesn't exist, so the Thursday case WOULD NOT be demoted at the primary_analyzer stage (would continue to L2 which rejects with `sl_beyond_ob` — which is what actually happened in production).

**Post-fix** (verified in my simulation), the guard correctly demotes the production NY 16:00 case with the reason `ai_output_inconsistent_pois`.

---

## 3. Call-site wiring

Code: `src/components/primary_analyzer.py:308-315`

```python
result = guard_candidate_null_params(result)
result = guard_candidate_degenerate_params(result)
# Guard against AI citing different OBs for POI / entry / SL
result = guard_candidate_inconsistent_pois(result, market_state)
```

**Wiring verified:**
- Runs unconditionally on every analyzer output before `_write_output(result)`.
- Runs AFTER the `null_params` and `degenerate_params` guards → both conditions already handled if triggered.
- Gets the full `market_state` (the `MarketStateObject` passed to `analyze()`).

**Double-demotion risk:** NONE. Each guard checks `decision != "CANDIDATE"` first. Once demoted, subsequent guards return unchanged.

---

## 4. False-positive risk (simulated on full production data)

### 4.1 Simulation methodology

Loaded `knowledge_base/trade_records/{GBPJPY,GBPUSD,US30_cash,USDJPY,XAUUSD}/*.json`, applied the guard logic in Python to every trade record with `ai_response.decision == "CANDIDATE"`, and bucketed by the stored `decision_pipeline.final_outcome`.

### 4.2 Results

| Final outcome | Total | Demoted by new guard | Notes |
|---|---|---|---|
| REJECTED_L2 | 92 | 68 | Good — guard catches them earlier, cleaner telemetry |
| LIMIT_PLACED | 30 | **1** | **See section 4.3** |
| REJECTED_GATE1_SAFETY | 16 | 3 | Mostly inverted LONGs that auto-correction caught; caught earlier now |
| EXECUTION_FAILED | 6 | 4 | No harm — never actually placed |
| REJECTED_L2_POST_M5 | 3 | 0 | Guard did NOT demote (passes guard, rejected later by M5 re-check). Correct. |

**Past 7 days:** 63 CANDIDATE records; 26 would be demoted by new guard. **0 of those 26 actually executed** (all had `execution: None`). So in the last week there is **no displaced execution**.

### 4.3 The one true false positive

**`knowledge_base/trade_records/USDJPY/2026-04-22_ny_1515.json`**

- AI POI = 159.239 → maps to unmitigated OB `[159.111, 159.367]` (touches=2)
- AI entry = 158.914 → NOT inside that OB (but inside another unmitigated OB `[158.792, 158.914]` touches=1)
- AI direction = LONG, SL = 158.754, TP1 = 159.154

**L2 verification PASSED all 6 checks** including `entry_in_ob` — because L2 uses a 0.2% tolerance (`verification.py:471, :480`):
- `entry_in_ob`: PASS — Entry 158.91 is within OB zone 159.11-159.37 *(via tolerance; outside strict bounds)*
- `sl_beyond_ob`: PASS — SL 158.75 is below OB low 159.11
- `ob_zone`: PASS — discount zone

**Trade was LIMIT_PLACED but never filled** (`logs/usdjpy.log:2711-2713`). No economic outcome to measure.

The AI's own reasoning explicitly names the situation (`ai_response.reasoning.h1_setup.explanation`):

> Nearest unmitigated H1 bullish OB at 159.367-159.111 (touches=2) caused by BOS at 2026-04-22T16:00; **preferred is the touches=1 OB at 158.914-158.792** but the 159.367-159.111 OB is nearest to current price.

The AI is mixing two OBs: named-POI = touches=2 OB, intended-entry = touches=1 OB. The new guard demotes this as inconsistent; L2 accepts it via the tolerance window. **Which behavior is correct is a policy question.**

### 4.4 Mitigated-OB matching behavior

**The guard does NOT filter `ob.mitigated`.** L2's `_find_matching_ob` (`verification.py:60-71`) filters mitigated OBs out. So the two do not cite the same matching OB in all cases.

Example: GBPJPY 2026-04-20_london_0715 (POI=214.102):
- L2 finds NO unmitigated OB near 214.10 → `REJECTED_L2 (h1_poi_exists)`.
- New guard finds mitigated OB `[214.023, 214.129]` containing POI → demotes with reason "entry 214.144 outside matched OB."

Both demote the trade, but with **different rationales**. No material harm — the trade is rejected either way. But for monitoring/telemetry purposes, the new guard's "inconsistent_pois" reason might mask the real AI hallucination ("cited a non-existent unmitigated OB").

**Recommendation (non-blocking):** Consider adding `if not ob.mitigated` to the list comprehension at line 722. This would make the guard's rationale track L2's rationale exactly — it would stay passive when the AI cites a phantom unmitigated OB, letting L2 `h1_poi_exists` be the reported cause. A non-critical improvement.

---

## 5. Test quality

All 10 tests in `TestGuardCandidateInconsistentPois` pass (verified locally: `pytest tests/test_primary_analyzer.py::TestGuardCandidateInconsistentPois -v` → 10 passed in 1.47s).

| Test | Verdict | Notes |
|---|---|---|
| `test_consistent_long_passes` | OK | Trivial happy path |
| `test_consistent_short_passes` | OK | SHORT happy path (note: fixture uses `_bearish_ob`, direction is overwritten — mixed-type OB in MSO is fine because the guard doesn't check `ob.type`) |
| `test_poi_and_entry_different_obs_demotes` | OK-with-caveat | Fixture's "touches=2 OB" range [48590.30, 48645.71] does not match real production [48629.71, 48645.71]. Does not exercise the 2+ match branch that real data hits. |
| `test_sl_beyond_different_ob_demotes` | OK | Exercises strict `<` bound |
| `test_tp1_wrong_side_demotes` | OK | Catches TP1 direction check |
| `test_poi_outside_all_obs_returns_unchanged` | OK | Passthrough case |
| `test_ambiguous_overlapping_obs_picks_closest` | OK | Exercises tie-breaker (tight vs wide OB) |
| `test_not_candidate_returns_unchanged` | OK | NO_TRADE passthrough |
| `test_zero_poi_level_returns_unchanged` | OK | `poi=0.0` passthrough |
| `test_missing_h1_timeframe_returns_unchanged` | OK | `H1 not in timeframes` passthrough |

**No test passes for the wrong reason.** The helpers (`_mso_with_h1_obs`, `_bullish_ob`, `_candidate_with`) correctly build real `MarketStateObject` / `PrimaryAnalysisOutput` instances — no over-mocking.

**Gap in coverage (minor):** no test with `ob.mitigated=True` — the guard does not differentiate, and this behavior is not documented in the tests. Given production data contains many mitigated OBs that match POIs, adding a test for this would improve clarity.

---

## 6. Canary coverage gap

**Agent's claim verified.** `scripts/canary_test.py:273-288` calls `Anthropic().messages.create()` directly — bypasses `PrimaryAnalyzer.analyze()`. The `guard_candidate_inconsistent_pois` guard is **never exercised on the canary path**.

**Implication:** the canary results (11/12 baseline + 3/4 borderline) in the commit message do NOT validate the new guard. Validation rests entirely on the 10 unit tests.

**Is this a problem?** Not blocking. The guard is a deterministic post-AI validator with no model-dependent behavior. Unit tests are the appropriate validation mechanism. Canary is for detecting model-drift semantics, not for pipeline guard logic.

---

## 7. Regression risk

### 7.1 Unit tests

- All 10 new tests pass (`TestGuardCandidateInconsistentPois`).
- All 28 tests in `tests/test_primary_analyzer.py` pass.
- Full suite: 1799 passed, 2 skipped, 1 failed. The one failure is `test_orchestrator.py::TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded` which I verified also fails on pre-fix `8a9bcfe` — **pre-existing and unrelated** to this commit.

### 7.2 Production simulation (whole history)

Applied guard logic to all `knowledge_base/trade_records/*/*.json`:
- **0 executed trades would be blocked** (no trade has `execution != None` matching guard-demote criteria).
- **1 LIMIT_PLACED would be demoted** (USDJPY 2026-04-22-15:15, never filled).
- 68/92 REJECTED_L2 cases demoted earlier (cleaner telemetry).
- 3/16 REJECTED_GATE1_SAFETY cases demoted earlier (mostly inverted LONGs).

### 7.3 Edge cases

- **Float equality at OB edges:** entry exactly at `ob.low` or `ob.high` → inclusive bounds → passes entry check. Verified with GBPUSD 2026-04-20_london_0716 case (entry = 1.34616 = ob.high exactly).
- **OB filtering by direction:** the guard does NOT filter OBs by `type` (bullish vs bearish). For a LONG trade, it might match a bearish OB. This could produce false positives if a bearish mitigated OB tightly overlaps the POI and geometrically beats the bullish unmitigated OB. Looking at production data, I found no such case in the 63 past-week records or in LIMIT_PLACED history. Low-probability edge, not blocking.

---

## 8. Hallucinations (fact-check)

All agent claims verified:

| Claim | Verified | Source |
|---|---|---|
| Thursday case POI=48531.325 | ✓ | `knowledge_base/trade_records/US30_cash/2026-04-23_ny_1600.json` h1_setup.poi_price_level |
| Thursday case entry=48645.71 | ✓ | same file, trade_parameters.entry_price |
| Thursday touches=4 OB = [48472.35, 48590.30] unmitigated | ✓ | same file, mso.timeframes.H1.order_blocks |
| Thursday "touches=2 OB high" = 48645.71 | ✓ (for the high price; but full zone is [48629.71, 48645.71], not [48590.30, 48645.71] as test fixture claims) | same file |
| L2 `sl_beyond_ob` uses strict `<`/`>` | ✓ | `src/components/verification.py:522, :536` |
| Canary bypasses `PrimaryAnalyzer.analyze()` | ✓ | `scripts/canary_test.py:273-288` |
| `guard_candidate_degenerate_params` runs first | ✓ | `primary_analyzer.py:308-315` |
| 10 new tests all pass | ✓ | `pytest tests/test_primary_analyzer.py::TestGuardCandidateInconsistentPois -v` |
| 1799 passed overall | ✓ | Full suite run |
| Thursday NY 16:00 was rejected by L2 `sl_beyond_ob` in production | ✓ | `logs/us30.log:2604` |

No hallucinations detected.

---

## 9. Recommendations

### 9.1 Non-blocking improvements (future enhancement)

1. **Filter mitigated OBs in matching** (line 722): `if ob.low <= poi_level <= ob.high and not ob.mitigated`. Aligns the guard's rationale with L2's. Without this, the guard occasionally assigns the demotion reason "inconsistent POIs" when the real issue is "AI cited a phantom OB" (which L2 would flag as `h1_poi_exists`).

2. **Document the tolerance disparity.** The guard uses strict bounds; L2 `entry_in_ob` uses a 0.2% tolerance. Either:
   - Add a comment explaining the intentional tighter bound, OR
   - Use the same tolerance for parity. The tolerance mismatch caused the one FP on USDJPY 2026-04-22-15:15.

3. **Add a test for mitigated-OB behavior** — whatever the chosen semantics, document it in a test.

4. **Correct the Thursday test fixture's touches=2 OB range** to [48629.71, 48645.71] (or include the real mitigated touches=29 OB) to make the test exercise the 2+ match branch the production data actually hits.

### 9.2 Blocking condition (needs CEO decision before merge)

**The USDJPY 2026-04-22-15:15 case.** The AI named one POI (touches=2 OB) but entered on another (touches=1 OB), with L2 accepting via tolerance. The new guard would block this as inconsistent.

- Option A: accept the guard's stricter behavior — AI sloppiness in POI labelling gets blocked.
- Option B: loosen the guard (add tolerance OR filter mitigated) so cases where entry is in SOME unmitigated OB pass even if POI maps to a different one.

This is a policy/semantics call that should be explicitly decided.

---

## 10. Summary table

| Dimension | Grade | Notes |
|---|---|---|
| Correctness of OB matching | A | 0/1/2+ branches all correct; tie-breaker well-chosen |
| Correctness of entry check | A- | Strict bounds correct, though tighter than L2's tolerance |
| Correctness of SL check | A | Perfect mirror of L2 |
| Correctness of TP1 check | A | Defensive double-check; no double-demotion risk |
| Skip conditions | A | All 4 passthrough branches correct |
| Counterfactual test accuracy | B+ | Correct in spirit; fixture's OB ranges are slightly different from real production |
| Call-site wiring | A | Correct ordering, runs on every CANDIDATE |
| Test quality (10 tests) | A- | Coverage is good; missing explicit mitigated-OB test |
| Canary coverage | N/A | Canary doesn't exercise this path — acknowledged, appropriate |
| Regression risk | Low | 1 would-be FP (never filled); all 30 LIMIT_PLACED cases except 1 pass guard |
| Hallucinations | None | All cited numbers verified |

**Overall: APPROVE WITH CONDITIONS.** Merge is low risk. The one USDJPY false positive deserves CEO acknowledgment but the trade never filled and the AI's reasoning was genuinely mixed-OB.
