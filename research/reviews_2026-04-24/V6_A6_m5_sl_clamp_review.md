# V6 A6 — M5 SL Clamp to OB Boundary — Independent Code Review

**Reviewer:** Opus 4.7, max effort
**Branch/commit:** `worktree-agent-aa6fc1ba` @ `c3002fa`
**Files reviewed (worktree abs paths):**
- `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba\src\components\m5_refinement.py`
- `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba\src\components\orchestrator.py`
- `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba\src\components\verification.py` (read-only, for cross-check)
- `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba\src\components\permissions.py` (read-only, for cross-check)
- `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba\tests\test_m5_refinement.py`
- `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aa6fc1ba\config\agent_config.yaml`

---

## Verdict

**APPROVE WITH MINOR NOTES.** The PR is correct, well-scoped, tested, and ships with verifiable evidence. The M15_ATR-vs-H1_ATR design choice is defensible and better than the brief's suggestion. Two minor edge cases are called out below; neither is a blocker.

---

## Clamp correctness

Reviewed `clamp_m5_sl_to_ob_boundary` at `m5_refinement.py:243-386`.

### LONG path (lines 302-347)
- `target = ob.low - buffer` (line 305).
- **Early return (no clamp):** `if m5_sl < target` → `m5_sl` already below buffer-extended boundary, returns clamped=False (lines 306-315). Semantic: M5 wanting a SL further from entry than the floor — pass through. Correct.
- **Feasibility rail 1:** `if target <= pre_m5_sl` → returns feasible=False (lines 320-328). This rejects clamp targets that would not tighten vs the pre-M5 SL. Correct — avoids a degenerate no-op. Note: `<=` is correct (strict tightening required), matches the docstring.
- **Feasibility rail 2:** `if target >= entry` → returns feasible=False (lines 329-339). This blocks the pathological case where `ob.low - buffer` is above entry (would produce an inverted SL). Correct.
- **Clamp path:** returns `clamped_sl = target, clamped=True, feasible=True` (lines 340-347). Correct.

### SHORT path (lines 349-386)
Mirror of LONG with sign-flipped comparisons. Verified identical structure.

### Sanity spot-checks (traced by hand)
| case | inputs | expected | actual |
|------|--------|----------|--------|
| LONG loose m5 | `m5_sl=3995, ob.low=4000, buf=2` | no clamp, sl=3995 | no clamp, sl=3995 ✓ |
| LONG inside OB | `m5_sl=4005, ob.low=4000, buf=2, pre=3990` | clamp to 3998 | clamp to 3998 ✓ |
| LONG infeasible | `m5_sl=4005, ob.low=4000, buf=2, pre=3998` | feasible=False | feasible=False ✓ |
| LONG target above entry | `m5_sl=4009, ob.low=4010, buf=2, entry=4005` | feasible=False | feasible=False ✓ |
| SHORT inside OB | `m5_sl=4007, ob.high=4010, buf=2` | clamp to 4012 | clamp to 4012 ✓ |
| buffer=0 inside OB | `m5_sl=4005, ob.low=4000, buf=0` | clamp to 4000 | clamp to 4000 (**see edge case below**) |

### Edge case 1 (minor, non-blocking): `buffer == 0` produces SL exactly at `ob.low`

When `_compute_ob_buffer` returns 0 (M15_ATR ≤ 0, or config multiplier is 0, or full_config missing),
the LONG clamp produces `clamped_sl == ob.low` exactly. But the L2 re-check at
`verification.py:522` uses strict `<`:

```python
if sl < zone_low:  # strict
    return PASS
return FAIL
```

A clamped SL equal to `ob.low` → L2 re-check FAILS → `REJECTED_L2_POST_M5` — the exact
bug this PR is trying to prevent. In live production this is unlikely because:
1. Config `gate1.ob_retest_sl_min_buffer_atr = 0.5` (`agent_config.yaml:56`).
2. M15_ATR ≈ 0 requires near-flat M15 over 14 candles, rare.
3. `_compute_ob_buffer` returns 0 when `_full_config` is missing — but orchestrator always
   attaches it (`orchestrator.py:816`).

The pure-function test `test_zero_buffer_still_clamps_when_inside_ob` (line 517) intentionally
verifies the buffer=0 behavior but does not assert it strictly-passes L2. Not a production
risk today, but worth a one-line guard if we ever allow buffer=0 to propagate to production.

### Edge case 2 (very minor, non-blocking): OB type filter vs verification.py
`_find_matching_h1_ob` at `m5_refinement.py:184-212` filters OB by type (bullish for LONG),
whereas `verification._find_matching_ob` at `verification.py:60-71` does NOT filter on type.
The agent's docstring says "Mirrors `verification._find_matching_ob` logic but filtered to...";
it actually matches `permissions._ob_retest_sl_exception_applies`, not verification's helper.
In a pathological setup where L2 matched an OB of the wrong type (e.g., bearish OB at LONG's
POI price), the clamp would fail to match it, skip clamping, and the L2 re-check would still
fail. This is a truly unlikely execution path (would require an OB_retest framework trade
whose AI-cited POI matched a wrong-type OB), but the docstring understates the divergence.

## M15 vs H1 ATR decision analysis + recommendation

### What the brief asked for
Task brief (per caller): "buffer_atr * H1_ATR".

### What the agent shipped
`_compute_ob_buffer` reads `m15_atr` at `m5_refinement.py:235` — **M15 ATR, not H1 ATR**.

### Verification of the rationale

Read `permissions._ob_retest_sl_exception_applies` at `permissions.py:348-418`:
- Line 377-378: `m15_tf = mso.timeframes.get("M15"); m15_atr = m15_tf.atr_14`
- Line 379: `min_buffer_mult = gate1_cfg.get("ob_retest_sl_min_buffer_atr", 0.3)` (default 0.3; live config overrides to 0.5)
- Line 380: `min_buffer = m15_atr * min_buffer_mult`

**Confirmed: the Gate 1 SL exception uses M15_ATR.** Agent's rationale is factually correct.

### Quantitative consequences (LONG direction, typical values)

Typical H1_ATR / M15_ATR ratio for US30 on 2026-04-23 (real trade record):
- M15_ATR = 65.88 → buffer_M15 = 32.94
- H1_ATR = 118.16 → buffer_H1 = 59.08
- Ratio ≈ 1.79×

For the same OB (say `ob.low = 49155.31`):
- Target_M15 = 49122.37
- Target_H1 = 49096.23

For a given `pre_m5_sl`:
- Both feasible if `pre_m5_sl < 49096.23`
- Only M15 feasible if `49096.23 <= pre_m5_sl < 49122.37`
- Neither feasible if `pre_m5_sl >= 49122.37`

→ **M15 choice "rescues" more CANDIDATEs than H1 choice** (strictly, because `buffer_M15 <= buffer_H1`).

### Consistency with L2 re-check

L2 `sl_beyond_ob` (at `verification.py:494-547`) uses only the OB boundary — it does NOT
apply any ATR-based buffer. It's a pure strict-`<` check. Any buffer > 0 passes it.

### Consistency with Gate 1

Gate 1's SL exception requires `buffer >= ob_retest_sl_min_buffer_atr * M15_ATR`. If clamp
uses M15_ATR, clamped SL sits EXACTLY at the Gate 1 threshold. If clamp uses H1_ATR,
clamped SL sits at 1.79× Gate 1 threshold — "safer" but wastes the M5 AI's tightening and
shrinks the set of rescuable CANDIDATEs.

### Decision

**Agent's choice is correct and well-justified.** The M15_ATR choice:
1. Maximizes the number of CANDIDATEs rescued (smaller buffer → larger feasible set).
2. Keeps the clamp target at the minimum Gate 1 enforces, avoiding over-buffering.
3. Is consistent with the live production Gate 1 SL-exception logic.

The commit message's rationale is sound. Brief's H1_ATR suggestion would have been safer on
sweep margin but strictly worse on CANDIDATE-rescue rate. If CEO wants extra sweep margin
above Gate 1 minimum, the correct lever is raising `gate1.ob_retest_sl_min_buffer_atr`
(config), not using a different ATR window in the clamp.

**Recommendation: accept the M15_ATR choice.** Flag to CEO: this is a deliberate deviation
from the brief; the rationale is recorded in the commit message.

## Counterfactual authenticity

Real Thursday US30 NY 13:46 trade record: `knowledge_base/trade_records/US30_cash/2026-04-23_ny_1346.json`

Figures verified against the live record:
- AI_ORIGINAL_SL = **49046.27** ✓ (line 68: `"detail": "SL 49046.27 is below OB low 49155.31"`; line 14258: `"stop_loss": 49046.27`)
- OB_LOW = **49155.31** ✓ (line 41, 1390, etc.)
- OB_HIGH = **49365.31** (not 49205.20 as used in test — test uses an approximation of OB_HIGH)
- M5_PROPOSED_SL = **49219.75** ✓ (confirmed in `logs/us30.log:2557` — the M5 refinement log line: `"M5 REFINED: quality=MEDIUM structure=higher_low ... SL=49219.75 TP=49583.65"`)
- L2 outcome = **REJECTED_L2_POST_M5** ✓ (trade record line 82: `"final_outcome": "REJECTED_L2_POST_M5"`; `logs/us30.log:2561`: `"L2 verification FAILED: sl_beyond_ob ... SL 49219.75 is NOT below OB low 49155.31 for LONG trade"`)
- OB_TYPE = **bullish** ✓ (line 1388)
- OB `mitigated` = **false** ✓ (line 1396)
- M15_ATR = **65.88** (live); test uses 32.0 as approximation

**Agent did NOT fabricate counterfactual data.** The test's `ENTRY`, `OB_HIGH`, and `M15_ATR`
are approximations (real values are 49365.31, 49365.31, 65.88 respectively), but the three
load-bearing figures (OB_LOW, AI_SL, M5_SL) are exact matches to the production trade record.

Sanity recheck with REAL values: `buffer = 0.5 * 65.88 = 32.94`, `target = 49155.31 - 32.94
= 49122.37`, `pre_m5_sl = 49046.27 < 49122.37` → feasible=True; `target < entry=49365.31` →
feasible=True; clamp fires → SL = 49122.37. Below OB low (strict `<`), above pre-M5 SL
(tighter) → L2 re-check would PASS. Trade preserved. **Fix does what it claims** on the real
incident.

## "Skip refinement" semantic validation

Reviewed the infeasible branch at `m5_refinement.py:575-593`.

- When `clamp["feasible"] is False`, the function returns `NO_CHANGE` (which is
  `{"applied": False, "m5_result": {...}, "overrides": None}`) with `decision: "CLAMP_INFEASIBLE"`.
- Orchestrator consumes this at `orchestrator.py:824`: `if m5_out["applied"]` — since
  applied=False, the else branch runs (line 844-846), which logs "M5: CLAMP_INFEASIBLE —
  using M15 SL/TP." and SKIPS `apply_m5_overrides`.
- Execution proceeds with unchanged analysis.trade_parameters (the original AI-set SL).
- **NOT a NO_TRADE demotion.** No `return` out of `_run_candle_iteration`. The CANDIDATE
  continues through the pipeline with its original M15 SL.

Verified behavior matches agent's claim.

### What counts as "infeasible"?

Three explicit infeasible conditions:
1. `target <= pre_m5_sl` (LONG) or `target >= pre_m5_sl` (SHORT) → "no tightening room".
2. `target >= entry` (LONG) or `target <= entry` (SHORT) → OB boundary pathological.
3. (Implicit via `matched_ob is None` → clamp is no-op feasible=True; NOT infeasible.)

### Geometrically-wrong SL (LONG with m5_sl > entry)

This is caught by the pre-existing `SL_OUT_OF_RANGE` guardrail at `m5_refinement.py:540-543`
BEFORE reaching the clamp. Returns NO_CHANGE with decision=`SL_OUT_OF_RANGE` and emits a
WARNING log. Agent's claim verified. The warning message uses `$%.2f` format (see flagged
issue #1).

### Edge case: `target == pre_m5_sl`

The LONG check is `if target <= pre_m5_sl` (line 320, inclusive `<=`) — so equal values
trigger infeasible. Strict tightening required. Matches docstring. **Correct** — a clamp
that produces an SL identical to pre-M5 SL is effectively a no-op, so skipping the
override saves the `apply_m5_overrides` side effects while still preserving the valid
pre-M5 SL.

## Flagged issues verified

### Flag 1: `$%.2f` truncates 5dp FX prices (m5_refinement.py:541, 546)
**VERIFIED.** Lines 541 and 546 use `"M5 SL $%.2f outside valid range [%.2f, %.2f]."` — this
truncates FX prices like 1.10234 to 1.10. For a LONG trade with entry=1.10234 and m5_sl=
1.10200 (0.00034 outside valid range), the log would print `$1.10 outside valid range
[1.10, 1.10]` — unhelpful. Pre-existing, unrelated to this PR's clamp. Legitimate flag.

### Flag 2: M5 LOOSER SL rejected as SL_OUT_OF_RANGE (m5_refinement.py:540, 545)
**VERIFIED.** At line 540 for LONG: `if m5_sl >= entry or m5_sl < sl` — the `m5_sl < sl`
condition rejects M5 proposals that are LOOSER than the M15 SL (below it for LONG). Pre-
existing behavior, predates this PR. Agent correctly notes this is NOT changed by the PR.
Test `test_m5_looser_sl_passes_through` (line 552) documents the current behavior.

### Flag 3: `test_pending_intent_stale_before_first_kz_discarded` time-of-day flake
**VERIFIED.** Reproduced on parent commit `8aq1bcfe` (pre-this-PR):
```
tests\test_orchestrator.py:656: AssertionError
FAILED tests/test_orchestrator.py::TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded
```
Not introduced by this PR. Pre-existing.

## Regression risk

### Test suite results (reviewer-verified)
| scope | result |
|-------|--------|
| `tests/test_m5_refinement.py` alone | **40/40 pass** ✓ |
| `tests/test_m5_refinement.py + test_verification.py + test_permissions.py` | 118/118 pass |
| `tests/ -k "m5 or refinement or verification or permissions or orchestrator"` | 224 passed, 1 failed (the pre-existing flake) |
| Full suite (`pytest tests/`) | **1852 passed, 1 failed, 2 skipped** ✓ — exact match to commit claim |

The agent claimed "147/147" broader-related tests — reviewer's broader run (m5 + verification
+ permissions + orchestrator) hit 224 tests. The exact 147 figure cannot be reproduced
without knowing the agent's selector, but it's within order of magnitude and the broader
outcome (no net regressions) is confirmed.

### Specific regression guards exercised
- `test_clamp_no_mso_is_noop` (line 728) — confirms `mso=None` preserves pre-PR behavior.
- `test_high_quality_refinement` (line 117) — unchanged baseline M5 happy path.
- `test_sl_floor_enforcement` (line 192) — floor logic downstream of clamp still works.
- `test_short_direction` (line 267) — unchanged SHORT baseline.
- `test_atr_floor_overrides_m5` (line 208) — ATR floor cooperation.

### Integration points reviewed
1. `orchestrator.py:823` passes `mso=mso` positionally-correct; single-line change is safe.
2. `m5_config["_full_config"]` attached at `orchestrator.py:816` — clamp correctly reads it
   at `m5_refinement.py:559`.
3. Post-clamp SL feeds `raw_m5_dist` at `m5_refinement.py:606` — downstream floor logic
   applies correctly to the clamped value.

### Backward compatibility
- `mso=None` default (line 399) preserves legacy behavior. `test_clamp_no_mso_is_noop`
  confirms.
- New overrides keys (`m5_ob_clamp_applied`, `m5_ob_pre_clamp_sl`, `m5_ob_boundary`,
  `m5_ob_clamp_buffer`) are additive; not consumed by execution. Safe.

## Hallucinations

| claim | status |
|-------|--------|
| Thursday OB_LOW = 49155.31 | ✓ verified (`2026-04-23_ny_1346.json:41`) |
| Thursday AI_SL = 49046.27 | ✓ verified (`2026-04-23_ny_1346.json:68,14258`) |
| Thursday M5_SL = 49219.75 | ✓ verified (`logs/us30.log:2557`) |
| REJECTED_L2_POST_M5 outcome | ✓ verified (`2026-04-23_ny_1346.json:82`) |
| Bullish OB, unmitigated | ✓ verified (`2026-04-23_ny_1346.json:1388,1396`) |
| permissions uses M15_ATR for buffer | ✓ verified (`permissions.py:377-380`) |
| gate1.ob_retest_sl_min_buffer_atr = 0.5 | ✓ verified (`agent_config.yaml:56`) |
| 40/40 m5 tests pass | ✓ reproduced |
| 1852 passed, 1 failed (flake) | ✓ reproduced exactly |
| Pre-existing flake on parent commit | ✓ reproduced on `8a9bcfe` |
| `_find_matching_ob` no type filter | ✓ verified (`verification.py:60-71`) |
| `clamp_m5_sl_to_ob_boundary` is pure function | ✓ verified (no logger/FS/network) |
| Orchestrator line 823 one-line signature change | ✓ verified |

**No hallucinations detected.** Test approximations (ENTRY=49230, OB_HIGH=49205.20,
M15_ATR=32) are explicitly approximate and do not fabricate outcomes. Real values produce
an even more favorable clamp (feasible region is wider).

## Recommendations

### Merge-blocking: none

### Merge-ready with follow-ups

1. **(Optional, tiny) Guard buffer=0 → SL == ob.low edge case.** In `clamp_m5_sl_to_ob_boundary`
   LONG path, if `buffer == 0` and clamp fires, the clamped SL equals `ob.low` exactly, which
   fails the strict-`<` L2 re-check. One-line fix: treat `buffer <= 0` as "clamp infeasible"
   (fall back to pre-M5 SL), so we never produce an SL exactly at the boundary. Not urgent —
   live config always has `buffer > 0`.

2. **(Optional, docstring hygiene)** Update `_find_matching_h1_ob` docstring at
   `m5_refinement.py:188` to clarify it mirrors `permissions._ob_retest_sl_exception_applies`
   (which type-filters), NOT `verification._find_matching_ob` (which does not type-filter).
   The current wording conflates the two.

3. **(Already flagged by agent, keep on backlog)** Fix the `$%.2f` log format truncation at
   `m5_refinement.py:541, 546` — use `%.5f` or a price-format injection. Pre-existing, not
   this PR's problem to solve.

4. **(Already flagged by agent, keep on backlog)** Decision on whether LOOSER M5 SLs should
   pass through (vs current `SL_OUT_OF_RANGE` rejection at `m5_refinement.py:540, 545`). This
   is a CEO-level design decision — the current behavior is deliberate (refinement = tighten
   only) but the brief hints at future relaxation.

5. **(Already flagged by agent)** Pre-existing `test_pending_intent_stale_before_first_kz_discarded`
   flake. Reproduced on parent. Not this PR's problem. Should be fixed in a dedicated PR.

### Design decision to surface to CEO

The M15_ATR-vs-H1_ATR choice deviates from the brief. Agent's rationale is sound
(consistency with `_ob_retest_sl_exception_applies`, max CANDIDATE rescue rate). CEO should
explicitly sign off on this deviation before merge. If CEO wants larger sweep margin, the
right lever is `gate1.ob_retest_sl_min_buffer_atr` config — NOT switching to H1_ATR in the
clamp.

### Overall

PR is well-scoped, thoroughly tested, accurately diagnoses a real live bug (Thursday US30
NY 13:46), and ships a clean fix. M15/H1 ATR choice is defensible and superior to the brief
on the CANDIDATE-rescue dimension. Approve pending CEO sign-off on the deviation from brief.
