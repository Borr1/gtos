# ADR-006 — SL Geometry + Multi-Framework Dispatch (Council Final Spec)

**Status:** ACCEPTED (CEO approved 2026-04-26 for atomic ship; B.1 cross-instrument-context gate deferred as follow-up)
**Date:** 2026-04-26
**Council:** 4 Stage-1 research agents (forensics + architecture + prior-work + solutions) → 2 Stage-2 agents (adversarial critic + empirical resolver) → 1 Stage-3 chairman synthesis. Opus 4.7 max effort throughout.
**Bundles:** SL geometry fix + multi-framework dispatch flip + per-instrument tight-FX overrides into ONE prompt edit, ONE canary cycle, ONE PR.

---

## Context — the bug class being engineered out

GTOS L2 `sl_beyond_ob` rejections fire at high rates on tight-FX and indices (EURUSD 168/173 = 97% in BT corpus; live fleet pre-FA-2 measured 38.04% / 35-of-92, with XAUUSD 85.7%, GBPUSD 78.6%, USDJPY 34.4%, US30 30%, GBPJPY 5.3%). The bug is multi-causal:

1. Strict-binary L2 gate (`verification.py:803-856` `_check_sl_beyond_ob` uses `<` / `>`, no tolerance)
2. AI emits `sl_buffer_applied: 0.0` universally pre-FA-2 (T2.9 audit found 1053/1053). Post-FA-2 mining (Stage 2B): XAUUSD-class fully fixed (0/33), but EURUSD-class only PARTIALLY fixed (60/66 sl_beyond_ob rejects post-FA-2 still have buffer=0.0 = 91%) — the prompt's `0.25*ATR` rounds inconsistently at 5dp precision regardless of how loud the prompt instructs.
3. Tight-FX 5dp precision rounds 0.25×ATR to where SL collides with OB boundary
4. 0.25×ATR buffer too small for tight-FX scale
5. Hardcoded ATR multipliers in 6+ prompt sections (TRADE PARAMETERS, SELF-CHECK, decision dispatch, framework list, output schema, observation report)
6. AI gets no feedback on rejection (silent rejection)

Adjacent finding (multi-framework dispatch, parallel investigation): of 9,069 production evaluations, **36.77% have fvg_fill POI but NO ob_retest POI** (3,335 setups). Pre-AI gate passes 100% of these to AI. But AI emits **128/128 = 100% ob_retest** in live CANDIDATEs since 2026-04-06. Zero fvg_fill or breaker picks. The prompt's priority-ordered DECISION ORDER ("ob_retest FIRST. ONLY IF ob_retest cannot fire... try fallback") suppresses the fallback frameworks structurally. BT non-ob-retest cohort shows 1.5× WR and 3.8× E[R] vs ob_retest — strong suggestion that fallback frameworks would add value if AI used them.

---

## Decision

### A. Architecture summary

The fix is **multi-causal-aware, single-canary-cycle**. It addresses root causes 1, 3, 4, 5, and partial-6 in one prompt edit, one gate edit, one config schema, one telemetry hook. Root cause 2 (AI buffer=0.0) is acknowledged as **structurally unsolvable on EURUSD via prompt-only intervention** — the math `0.25 × 0.0010 = 0.00025 ≈ 2.5 ticks` is unstable at 5dp regardless of how loud the prompt shouts; we instead make the **gate** quantization-tolerant AND make the **prompt buffer** wider per-instrument. Root cause 6 (silent rejection) is deferred — once the gate stops rejecting at all on legitimate setups, AI-feedback becomes a marginal optimization.

This wins over R4's Solutions 3+4+5 hybrid for three reasons. First, Solution 3's pre-AI minimum-SL pre-compute has the chicken-egg problem (framework choice happens IN the AI, not before). Second, Solution 4's AI self-verification doesn't fix quantization — math is exact, rounding is the problem. Third, R4's effort estimate (14h) underestimated test scope. Chosen design fixes the gate (unambiguous, testable) and tightens config (structural), leaving the prompt with one localized edit (multi-framework dispatch) plus a config-driven buffer-policy section that replaces hardcoded constants.

It also wins over the critic's "Adapter A + post-30d empirical retune" alternative because Adapter A as proposed (correlation-cluster sizing) doesn't address sl_beyond_ob at all; the 38% live rejection rate keeps bleeding setups regardless of cluster behavior.

### B. Code diffs

#### B.1 `src/components/verification.py` — quantization-tolerant SL gate

**New helper** (insert after `_ob_tolerance`, near line 124):

```python
def _sl_beyond_floor(price: float, config: dict) -> float:
    """Compute the minimum geometric distance SL must clear OB boundary.

    Returns max(broker_stops_level_proxy, configured tick floor).
    Default: 1 instrument tick. Per-instrument override via
    risk.sl_beyond_ob_tick_floor in config or profile.
    """
    tick = float(config.get("market", {}).get("tick_size") or 0.0)
    if tick <= 0:
        tick = float(config.get("prompt", {}).get("tick_size_fallback", 1e-5))
    floor_ticks = int(config.get("verification", {}).get("sl_beyond_ob_tick_floor", 1))
    return tick * floor_ticks
```

**Replace `_check_sl_beyond_ob`** (lines ~803-856):

```python
def _check_sl_beyond_ob(
    analysis: PrimaryAnalysisOutput,
    matched_ob: Optional[OrderBlock],
    matched_bb: Optional[BreakerBlock],
    config: dict,                                # NEW PARAM
) -> VerificationCheck:
    """CHECK 6: SL placed beyond OB/breaker extreme by at least tick floor.

    Tolerance model (replaces strict-<):
      LONG  : sl <= ob_low  - floor   (must clear by floor)
      SHORT : sl >= ob_high + floor   (must clear by floor)
    """
    tp = analysis.trade_parameters
    if tp is None:
        return VerificationCheck("sl_beyond_ob", "SKIP", "No trade_parameters")
    if matched_ob is None and matched_bb is None:
        return VerificationCheck("sl_beyond_ob", "SKIP",
                                 "No matched OB/breaker from Check 3")

    sl = tp.stop_loss
    direction = tp.direction
    floor = _sl_beyond_floor(sl, config)

    if matched_ob:
        zone_low, zone_high = matched_ob.low, matched_ob.high
        zone_label = "OB"
    else:
        zone_low, zone_high = matched_bb.zone_low, matched_bb.zone_high
        zone_label = "breaker"

    fmt = config.get("prompt", {}).get("price_format", ".2f")

    if direction == "LONG":
        if sl <= zone_low - floor:
            return VerificationCheck(
                "sl_beyond_ob", "PASS",
                f"SL {sl:{fmt}} clears {zone_label} low {zone_low:{fmt}} "
                f"by >= floor {floor:{fmt}}",
                mso_value=zone_low, ai_value=sl,
            )
        return VerificationCheck(
            "sl_beyond_ob", "FAIL",
            f"SL {sl:{fmt}} does not clear {zone_label} low "
            f"{zone_low:{fmt}} by floor {floor:{fmt}} for LONG",
            mso_value=zone_low, ai_value=sl,
        )
    # SHORT
    if sl >= zone_high + floor:
        return VerificationCheck(
            "sl_beyond_ob", "PASS",
            f"SL {sl:{fmt}} clears {zone_label} high {zone_high:{fmt}} "
            f"by >= floor {floor:{fmt}}",
            mso_value=zone_high, ai_value=sl,
        )
    return VerificationCheck(
        "sl_beyond_ob", "FAIL",
        f"SL {sl:{fmt}} does not clear {zone_label} high "
        f"{zone_high:{fmt}} by floor {floor:{fmt}} for SHORT",
        mso_value=zone_high, ai_value=sl,
    )
```

**Caller change** (in `verify_candidate`, near line 960):
```python
c6 = _check_sl_beyond_ob(analysis, matched_ob, matched_bb, config)  # add config param
```

#### B.2 `src/prompts/primary_analyzer_prompt.py` — multi-framework dispatch + config-driven buffers

**Edit 1 — DECISION ORDER (lines ~407-438):** replace priority-ordered with parallel-evaluation:

```
DECISION ORDER (PARALLEL EVALUATION — 2026-04-26):
  Step A. Evaluate the THREE C-gates (C1/C2/C3) — framework-agnostic.
  Step B. If any C-gate FAILS, decision = NO_TRADE. Skip to output.
  Step C. If C1 ∧ C2 ∧ C3 PASS, evaluate ALL active frameworks IN PARALLEL:
            - For ob_retest: does a qualifying unmitigated H1 OB exist
              in the C3 direction (per STRICT RULE block)? Mark
              `frameworks_evaluated.ob_retest.qualified = true|false`.
            - For fvg_fill: does an unfilled M15 FVG aligned to H1 bias
              exist (per FVG_FILL section)? Mark `qualified`.
            - For breaker_re_entry (if addendum present): does an
              unretested H1 breaker exist (per ADDENDUM)? Mark
              `qualified`.
  Step D. If ZERO frameworks qualify, decision = NO_TRADE with
          no_trade_reason = "no_qualifying_h1_poi" (R4).
  Step E. If EXACTLY ONE framework qualifies, emit that one as the
          chosen framework.
  Step F. If MULTIPLE qualify, choose by this STRICT order:
          (1) ob_retest if it qualifies AND its OB.touch_count == 1
              (the highest-conviction case the deterministic gate
              keeps), else
          (2) the framework whose POI was created by the MOST RECENT
              displacement event (latest timestamp wins), else
          (3) fvg_fill > breaker_re_entry > ob_retest as a stable
              tiebreaker.
          Set `frameworks_evaluated.<chosen>.qualified = true` and
          all others true OR false honestly per their structural
          state. The chosen `framework` field is the single emitted
          path.

The frameworks remain STANDALONE — geometric rules of the chosen
framework are not blended with another.
```

**Edit 2 — Config-substituted multipliers (replaces hardcoded constants in lines 155, 402-403, 622, 646, 650, 929-930, 944-945):**

In `build_system_prompt`, near line 230:
```python
risk_cfg = config.get("risk", {})
ob_atr_mult = risk_cfg.get("sl_buffer_atr_multiplier", 0.25)
breaker_atr_mult = risk_cfg.get("sl_buffer_breaker_atr_multiplier", 0.5)
min_ticks = int(risk_cfg.get("sl_buffer_min_ticks", 5))
text = text.replace("{ob_atr_mult}", f"{ob_atr_mult:.2f}")
text = text.replace("{breaker_atr_mult}", f"{breaker_atr_mult:.2f}")
text = text.replace("{min_ticks}", str(min_ticks))
```

In the prompt template, replace each instance:
- `max(0.25 x H1 ATR(14), 3 x smallest tick)` → `max({ob_atr_mult} x H1 ATR(14), {min_ticks} x smallest tick)` (line 622, 650)
- `max(0.5 * H1 ATR(14), 3 * smallest tick)` → `max({breaker_atr_mult} * H1 ATR(14), {min_ticks} * smallest tick)` (line 929)
- Mirror lines 944-945
- Line 155 invalid block: `max of 0.25*H1 ATR or 3 ticks` → `max of {ob_atr_mult}*H1 ATR or {min_ticks} ticks`
- Lines 402-403: `0.5×H1 ATR buffer vs 0.25× for ob_retest` → `{breaker_atr_mult}×H1 ATR vs {ob_atr_mult}× for ob_retest`

#### B.3 `config/agent_config.yaml` — new SL buffer + verification knobs

Append to `risk:` block:
```yaml
risk:
  # ... existing keys preserved ...

  # NEW (2026-04-26): SL buffer policy — prompt-substituted, not hardcoded.
  # Buffer = max(atr_mult * H1_ATR, min_ticks * tick).
  sl_buffer_atr_multiplier: 0.25            # ob_retest baseline
  sl_buffer_breaker_atr_multiplier: 0.5     # breaker baseline
  sl_buffer_min_ticks: 5                    # widened from effective 3
```

Append to `verification:` block:
```yaml
verification:
  # ... existing keys preserved ...

  # NEW (2026-04-26): tolerance floor for sl_beyond_ob gate.
  # Gate accepts SL when SL <= OB_low - (sl_beyond_ob_tick_floor * tick) for LONG
  # (mirror for SHORT). Set floor to 0 to revert to strict-< (rollback).
  sl_beyond_ob_tick_floor: 1                # 1-tick clearance required
  sl_beyond_ob_tolerance_enabled: true      # rollback flag
```

#### B.4 `config/profiles/ftmo.yaml` — per-instrument tight-FX overrides (additive)

Add or extend per-instrument blocks:
```yaml
EURUSD:
  market:
    tick_size: 0.00001
  risk:
    sl_buffer_atr_multiplier: 0.50      # widened from 0.25
    sl_buffer_min_ticks: 8              # 8 ticks (~0.8 pip) for headroom

GBPUSD:
  market:
    tick_size: 0.00001
  risk:
    sl_buffer_atr_multiplier: 0.50
    sl_buffer_min_ticks: 8

USDJPY:
  market:
    tick_size: 0.001
  risk:
    sl_buffer_atr_multiplier: 0.30      # widened from 0.25
    sl_buffer_min_ticks: 5
```

XAUUSD / US30 / NAS100 / XAGUSD / GBPJPY — leave unchanged (already-working scales).

Mirror to `config/profiles/redacted_account.yaml` for the same instruments where overrides exist.

#### B.5 `src/components/permissions.py` — NO required change

Gate 1's `sl_too_tight` (1.5×M15-ATR) and `sl_below_minimum_floor` rails are unchanged. The `_ob_retest_sl_exception_applies()` bypass stays as-is.

#### B.6 `src/components/sl_beyond_ob_shadow_logger.py` — extend (already shipped earlier this session)

Add new fields to log row: `tick_floor_used`, `sl_to_ob_distance_ticks`, `near_miss` (boolean: distance ≤ 2 × floor). Hook from `_check_sl_beyond_ob` after PASS/FAIL determination.

### C. Test additions

**New file: `tests/components/test_verification_sl_beyond_ob_tolerance.py`** — 10 cases (parametrized over LONG/SHORT × XAUUSD/EURUSD/USDJPY/UK100/GBPUSD/NAS100):

1. `test_pass_sl_one_tick_beyond_ob` — SL = OB.low − 1 tick → PASS
2. `test_fail_sl_at_ob_boundary` — SL = OB.low → FAIL
3. `test_fail_sl_inside_ob` — SL = OB.low + 1 tick → FAIL
4. `test_pass_sl_far_beyond_ob` — SL = OB.low − 10 ticks → PASS
5. `test_short_pass_sl_one_tick_above_ob_high` — SHORT mirror
6. `test_quantization_tightfx_eurusd` — entry=1.19000, OB.low=1.19000, SL=1.18999, floor=0.00001 → PASS
7. `test_quantization_xauusd` — entry=2300.50, OB.low=2300.20, SL=2300.19, floor=0.01 → PASS
8. `test_floor_zero_disables_tolerance` — `sl_beyond_ob_tick_floor: 0` → identical to strict<
9. `test_skip_when_no_matched_ob` — SKIP path preserved
10. `test_message_format_uses_price_format_config` — `.5f` for FX, `.2f` for XAUUSD

**Existing tests to update:** `tests/components/test_verification.py` — re-stub any sl_beyond_ob cases with `config` param.

**New file: `tests/prompts/test_dispatch_parallel_evaluation.py`** — 5 cases:

1. `test_prompt_replaces_atr_mult_tokens` — `{ob_atr_mult}` not in built prompt; `0.25` substituted
2. `test_prompt_per_instrument_eurusd` — EURUSD overrides → `0.50` substituted
3. `test_prompt_dispatch_section_says_parallel` — "PARALLEL EVALUATION" present, "Step C. ONLY if ob_retest cannot fire" absent
4. `test_min_ticks_substitution` — `5` substituted
5. `test_breaker_addendum_uses_config_mult` — `0.5` substituted in breaker addendum

**New file: `tests/integration/test_sl_geometry_e2e.py`** — per-instrument synthetic MSO + AI output:

For each tight-FX fixture pair (EURUSD LONG/SHORT, GBPUSD LONG, USDJPY LONG, UK100 SHORT):
- SL = OB.low − 1 tick → expect PASS
- Repeat with strict-< rollback → still PASS
- SL = OB.low → FAIL with new message format

Coverage target: every instrument with sl_beyond_ob mass + active live (XAUUSD, USDJPY, US30, GBPJPY).

### D. Canary regression strategy

Run `python scripts/canary_test.py` against current 60-fixture baseline + 15 borderline (75 effective).

**Expected outcomes:**
- 32 baseline: 30-32 PASS, 0-2 flips. Allowed: ≤1 flip per tier policy. Most likely flip candidate: `baseline_eurusd_fx_prec_long.json` / `_short.json` may flip from old-FAIL to new-PASS — **intended behavior**, not regression. Regenerate fixture if so.
- 28 borderline (43 nominal): ≥21 match (75% threshold).

**Specific high-risk fixtures + remediation:**
- `borderline_*_fvg_fill_*` (6 fixtures): may flip CANDIDATE↔NO_TRADE under parallel evaluation. Re-grade with new tiebreaker, regenerate expected outputs.
- `borderline_*_breaker_*` (9 fixtures): no impact expected (tiebreaker rank 3rd preserves behavior absent parallel-fire).
- `baseline_xauusd_choch_*`: no impact expected (XAUUSD scale 2dp, 0.25×ATR ≥ $1.25 ≫ $0.01 floor).

**Canary policy:**
- First-run threshold ≥ 56/60. Below → halt.
- Tight-FX flips: regenerate fixtures via `scripts/canary_fixtures/regenerate.py` if exists, or update manifest. Commit fixture updates separately.
- Non-tight-FX flips: halt and diagnose.

### E. Implementation sequence

| Step | What | Time | Checkpoint |
|------|------|------|------------|
| 1 | Branch `feat/sl-geometry-multi-fw` from main HEAD `b907f6c`. Apply config additions (B.3, B.4). | 0.5h | Config validates: `python -c "import yaml; yaml.safe_load(open('config/agent_config.yaml'))"` clean. |
| 2 | Apply verification.py diff (B.1). Add helper, update signature, hook shadow logger. | 1.5h | `pytest tests/components/test_verification.py -v` green (existing tests still pass with new param). |
| 3 | Add `tests/components/test_verification_sl_beyond_ob_tolerance.py` (10 cases). | 1.5h | New tests green. |
| 4 | Apply prompt config substitutions (B.2 edit 2). | 1h | Visually inspect built prompt for `0.25` / `0.50` / `5` / `8` substitutions. |
| 5 | Apply prompt dispatch flip (B.2 edit 1 — parallel evaluation). | 1h | Prompt-dispatch tests pass. |
| 6 | Add `tests/prompts/test_dispatch_parallel_evaluation.py` (5 cases). | 1h | All pass. |
| 7 | Add `tests/integration/test_sl_geometry_e2e.py`. | 1.5h | All pass per-instrument. |
| 8 | Run full pytest: `pytest tests/ -v --tb=short`. | 0.5h | 2068+ green, 0 new failures. |
| 9 | Run canary: `python scripts/canary_test.py`. | 0.5h | ≥56/60 PASS. Tight-FX flips → regenerate fixtures. |
| 10 | Bench-test: pick 1 EURUSD post-FA-2 sl_beyond_ob-rejected sample, manually run through new gate, confirm now PASSES with floor=8 ticks. Document in commit. | 0.5h | One worked example logged. |
| 11 | Commit + update CLAUDE.md + LIVE_STATE.md in same commit. CEO approval gate before any push. | 0.5h | Commit message references this ADR. |

**Total: 10 engineering hours.**

### F. Monitoring + rollback plan

**Telemetry:**
- `shadow_logs/sl_beyond_ob_decisions.jsonl` rows include `tick_floor`, `sl_to_ob_distance_ticks`, `framework`, `near_miss` (boolean: 0 < distance ≤ 2 × floor)
- New watchdog metric: % evaluations with `near_miss = true`. Alarm threshold: > 10% over rolling 50 → CEO Telegram alert.

**SPRT-halt rules (per instrument, post-Monday launch):**
- First 20 filled trades post-fix: WR shall not drop below `historical_baseline_WR − 15pp`. Below → halt that instrument.
- XAUUSD-specific (LONG-WR-watch): preserve existing rule from deferred-master item #11. If XAUUSD live LONG WR drops below 40% in first 20 trades, halt regardless of cause.

**Rollback paths (in priority order):**
1. **One-line config rollback:** `verification.sl_beyond_ob_tick_floor: 0`. Gate reverts to strict-`<`. Wider buffers in prompt remain (harmless — conservative).
2. **Two-line prompt rollback:** revert `model_a.enabled_frameworks` to `[ob_retest]` only. Single-framework fallback. Keep gate fix.
3. **Full rollback:** `git revert <merge-commit>`.

**Rollback decision criteria (must-trip):**
- Live `sl_beyond_ob` rejection rate INCREASES vs pre-fix baseline (38.04%) for ≥3 consecutive trading days → revert (1).
- Any instrument's filled-trade WR drops > 20pp below CLAUDE.md Validated Numbers in first 30 trades → revert (3) for that instrument.
- Canary PASS rate < 55/60 on weekly cron → halt, freeze config until diagnosed.

### G. Multi-framework dispatch fix (BUNDLED)

**Bundling rationale:** Same prompt edit, same canary cycle, same council ship. Both fixes touch lines 380-440 of `primary_analyzer_prompt.py`. Marginal token-cost increase (~150 tokens/call ≈ $0.06/day fleet) is acceptable.

**Why parallel beats priority:** BT non-ob-retest cohort shows 1.5× WR and 3.8× E[R] vs ob_retest. Priority ordering systematically suppresses fallback frameworks. Parallel evaluation lets AI mark `fvg_fill.qualified = true` honestly when structure says so; deterministic tiebreakers pick the winner. **Up to 36.77% increase in setup volume** if all fvg-only BT cohort survives the new tiebreakers.

**Honest expectation:** AI may continue picking ob_retest most of the time even under parallel evaluation due to training+prompt gravity. First-week measurement: % of CANDIDATEs with `framework: "fvg_fill"` should rise from 0% (current live) to ≥ 10% within 30 fills. Below 5% by 50 fills → prompt-engineering follow-up needed (post-Monday research, NOT a gate-blocker).

### H. Decision-gate matrix

| Instrument | Pre-fix `sl_beyond_ob` reject rate | Live status Monday | Post-fix expected reject rate |
|-----------|-----------------------------------|---------------------|------------------------------|
| XAUUSD    | 85.7% (live, n=7 small)            | Live 0.5%           | < 5%                         |
| US30_cash | 30.0% (live)                       | Live 1%             | < 10%                        |
| USDJPY    | 34.4% (live)                       | Live 1%             | < 15%                        |
| GBPJPY    | 5.3% (live)                        | Live 1%             | < 5%                         |
| GBPUSD    | 78.6% (live, observe)              | Observer            | < 15%                        |
| XAGUSD    | n/a (no pre-fix sample)            | Live 0.5%           | < 5%                         |
| NAS100    | n/a                                | Live-OBS 0.25%      | < 5%                         |
| EURUSD    | 38.8% post-FA-2 BT                 | NOT LIVE (deferred) | < 10% (BT, post-fix)         |

---

## Decisions locked

**Stage 2A Ambiguity 1 — per-instrument vs per-class taxonomy.** **Hybrid with rules.** Fleet-wide defaults in `agent_config.yaml`, per-instrument overrides in profile YAMLs. Two rough classes: tight-FX (5dp, EURUSD/GBPUSD) and broad-scale (2dp/3dp/1dp). JPY (3dp) bridges with intermediate values. Override system makes per-instrument tuning a 3-line YAML edit.

**Stage 2A Ambiguity 2 — gate strictness regime-dependent.** **Never relax conditionally.** One floor for all instruments derived from broker tick. Regime-dependent gating creates hidden state and is impossible to canary-test. Only relaxation knob is `sl_beyond_ob_tick_floor` (rollback flag). No SPRT-halt-conditioned-relaxation.

**Stage 2A Ambiguity 3 — Phase 1 → Phase 2 trigger.** **No phase split.** Spec ships atomically. CEO mandate: "no ambiguity, the solution." Splitting introduces research delay we cannot afford pre-FTMO. The deferred-master 30-day live-data observation is the natural Phase 2 if any post-launch tuning is needed; not blocking on this spec.

**Stage 2A Ambiguity 4 — Adapter A Monday vs post-Monday.** **Bundle Monday.** The prompt-side Adapter A IS this spec's section G (multi-framework dispatch flip). Shipped Monday in this single PR. Cross-instrument-context block gate by |corr|≥0.4 (deferred-master B.1 strict definition) is **deferred as follow-up** per CEO 2026-04-26.

**Critic's "skip Solutions 3/4/5 — empirical retune instead":** **REJECTED.** Empirical retune cannot fix a strict-`<` gate with quantization-prone inputs. Solution 5 (telemetry) partially adopted via B.6. Solutions 3 and 4 rejected for chicken-egg and quantization reasons.

**FA-2 effectiveness verdict:** FA-2 fixed XAUUSD-class completely (0% buffer=0.0 post-FA-2 vs 100% pre). FA-2 only PARTIALLY fixed EURUSD-class (91% of EURUSD sl_beyond_ob rejects post-FA-2 still buffer=0.0). The per-instrument 0.50 ATR mult + 8-tick floor is **necessary**, not optional.

---

## Honest expectancy

- **Total engineering hours:** 10-11h
- **P(canary 60/60 first try):** ~55%. Likely 1-3 EURUSD/GBPUSD fixture flips that need regen (intended, not regression).
- **P(live rejection rate <20% within 30d):** ~80%
- **P(regression on currently-working instruments):** ~10%. Gate becomes more permissive at boundary only; Gate 1 `sl_too_tight` rail unchanged shields baseline.
- **P(parallel-eval produces fvg_fill picks within 30 fills):** ~40%. AI training inertia favors ob_retest. Below-target = prompt-research follow-up.

---

## Ship checklist (executing agent)

1. Read this ADR end-to-end.
2. Confirm `research/t7_live_simulation/post_fa2/` artifacts exist.
3. Branch off main HEAD `b907f6c`.
4. Execute steps 1-11 of section E in strict order.
5. Tag commit message: `feat(sl-geometry+multi-fw): tolerance gate + parallel dispatch + per-instrument buffers (ADR-006)`.
6. Update `CLAUDE.md` "What is working" + "What is unresolved" sections in the SAME commit.
7. Regenerate `LIVE_STATE.md` via `python scripts/generate_live_state.py`.
8. **CEO approval gate before push to remote** (per CLAUDE.md prohibited-behavior #8).

---

*ADR-006 final spec. Council closed 2026-04-26. Implementation begins immediately.*
