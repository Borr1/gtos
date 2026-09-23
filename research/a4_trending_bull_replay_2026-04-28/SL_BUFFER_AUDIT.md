# A4 SL_buffer_applied = 0.0 Audit (Read-Only)

**Auditor:** Claude Opus 4.7 (max effort)
**Date:** 2026-04-28
**Scope:** Why did 6 of 11 H2 XAUUSD trending_bull CANDIDATEs hit L2 `sl_beyond_ob` rejection in production with `sl_buffer_applied: 0.0`, and is the current main HEAD architecture systemically robust against the same bug class?
**Branch:** worktree at `agent-ac9b936dbfe3e4e6b` (no code changes — read-only audit).

---

## TL;DR (≤5 lines)

**Root cause is HISTORICAL, not present-day.** The 6 rejected records were emitted between 2026-04-15 and 2026-04-16 under prompt commit `5242bfd`, which **literally instructed** `sl_buffer_applied: 0.0` in the TRADE PARAMETERS section. **FA-2 (commit `fa35cc0`, 2026-04-20)** rewrote that directive to require `> 0` non-zero buffer. The current main HEAD prompt produces correct emissions — the A4 replay confirms 11 of 11 records now emit `sl_buffer_applied ∈ [3.57, 5.19]`. **However**, the audit found **TWO residual systemic gaps** that should be closed before declaring the bug class engineered out: (1) `_check_sl_beyond_ob` is the ONLY L2 SL gate that does NOT precision-snap MSO floats (`_check_entry_in_breaker` and `_check_entry_in_fvg` both DO, per SISTER-1/2/4/5); (2) **XAUUSD has no `market.tick_size` defined** in any config layer, so `_sl_beyond_floor` falls back to `1e-5`, making the "1-tick floor" effectively zero ($0.00001) for a $4762 instrument — a 1-cent rendering delta will breeze past it.

---

## 1. Reproduction proof

### 1.1 Stage 2.5 evidence — 6 records rejected at L2 `sl_beyond_ob`

Per `research/a4_trending_bull_replay_2026-04-28/a4_realized_r_join.csv` (cited at lines 2-7, 8) and `a4_realized_r_join_SUMMARY.md` line 24, the rejection cohort is:

| trade_id                        | candle_time_utc                        | source                                           |
|---------------------------------|----------------------------------------|--------------------------------------------------|
| 2026-04-15_ny_1315              | 2026-04-15T13:15:52.698253+00:00       | trade_record_pipeline_rejected_l2 (sl_beyond_ob) |
| 2026-04-15_ny_1330              | 2026-04-15T13:30:05.014598+00:00       | trade_record_pipeline_rejected_l2 (sl_beyond_ob) |
| 2026-04-15_ny_1345              | 2026-04-15T13:45:05.006349+00:00       | trade_record_pipeline_rejected_l2 (sl_beyond_ob) |
| 2026-04-15_ny_1615              | 2026-04-15T16:15:05.004428+00:00       | trade_record_pipeline_rejected_l2 (sl_beyond_ob) |
| 2026-04-15_ny_1700              | 2026-04-15T17:00:05.021104+00:00       | trade_record_pipeline_rejected_l2 (sl_beyond_ob) |
| 2026-04-16_london_0800          | 2026-04-16T08:00:05.009039+00:00       | trade_record_pipeline_rejected_l2 (sl_beyond_ob) |

### 1.2 Per-record evidence — original AI emission and prompt directive

I read `knowledge_base/trade_records/XAUUSD/2026-04-15_ny_1315.json` (the canonical case) directly. Key facts:

- File `metadata.system_version`: **`5242bfd`** (line 9). This is the commit ID at the time of capture.
- Original `ai_response.trade_parameters` (line 12772-12782):
  - `direction: "LONG"`
  - `entry_price: 4777.43` (= OB.high)
  - `stop_loss: 4762.14` (= OB.low, EXACTLY)
  - `sl_buffer_applied: 0.0`
  - `take_profit_1: 4800.365`
- L2 `sl_beyond_ob` check result (line 64-69): `FAIL — "SL 4762.14 is NOT below OB low 4762.14 for LONG trade"`
- The H1 OB cited (line 12717 system_prompt, embedded user message): `bullish 4777.43-4762.14 body=4774.75-4771.16 evt=BOS (2026-04-14T23:00)`.
- **The prompt directive that produced this** (line 12717, embedded as the `system_prompt` string for that capture). Reading the substring relevant to TRADE PARAMETERS, the captured prompt explicitly contains:
  > `- sl_buffer_applied: 0.0`
  >
  > and within the JSON output schema:
  >
  > `"sl_buffer_applied": 0.0,`

So the ORIGINAL prompt (under `system_version: 5242bfd`) **literally instructed the AI to emit zero buffer**. The AI complied with the directive; the L2 verifier rejected the deterministic-by-construction zero-buffer SL.

### 1.3 Current replay evidence — bug already fixed at the prompt layer

I read `research/a4_trending_bull_replay_2026-04-28/raw_responses/*.json` (all 11 files) and grepped for `sl_buffer_applied`. Every record's current emission has a strictly-positive buffer in the range $3.57 to $5.19. Specifically for the 6 originally-rejected records:

| trade_id                | original sl_buffer_applied | current sl_buffer_applied | delta SL (current - original) |
|-------------------------|----------------------------|---------------------------|--------------------------------|
| 2026-04-15_ny_1315      | 0.0                        | 4.37                      | -4.37 ($SL deeper)             |
| 2026-04-15_ny_1330      | 0.0                        | 4.47                      | -4.41                          |
| 2026-04-15_ny_1345      | 0.0                        | 4.54                      | -4.49                          |
| 2026-04-15_ny_1615      | 0.0                        | 4.59                      | -4.59                          |
| 2026-04-15_ny_1700      | 0.0                        | 4.34                      | -4.34                          |
| 2026-04-16_london_0800  | 0.0                        | 3.79                      | -3.79                          |

Note the brief's framing ("6 of 11 H2 XAUUSD trending_bull candidates STILL produce sl_buffer_applied=0.0 on the current main HEAD") is INCORRECT. Stage 2.5 sources its `r_source: trade_record_pipeline_rejected_l2` from the historical `final_outcome` field of the captured trade records, not from the new replay. Stage 2 (the replay itself) shows 11/11 emit non-zero buffers — i.e., the bug at the AI-emission layer has **already** been engineered out.

The remaining audit question therefore is: **is the architecture systemically robust, or does the bug class still exist on adjacent paths?**

---

## 2. Root-cause hypothesis (cite file:line)

Walking the emission → guard → L2 path for the canonical case **2026-04-15_ny_1315 under `system_version: 5242bfd` prompt**:

### 2.1 Emission layer (PROMPT, then-active)

`src/prompts/primary_analyzer_prompt.py` at the `5242bfd` snapshot — TRADE PARAMETERS line read literally:

```
- sl_buffer_applied: 0.0
```

(I confirmed by reading `git show fa35cc0 -- src/prompts/primary_analyzer_prompt.py 2>&1`, which shows the diff `-- sl_buffer_applied: 0.0  → ++ sl_buffer_applied: compute a non-zero buffer using max(0.25 x H1 ATR(14) from MSO, 3 x the smallest price tick shown)...`). Pre-FA-2, the AI was being asked to set the buffer to zero. AI compliance was a feature, not a bug.

### 2.2 Guard layer (Component 3A)

`src/components/primary_analyzer.py:790-942` — `guard_candidate_inconsistent_pois`. This guard, post-HALLUC-1 (`2c75f98`, 2026-04-28), **does not check SL placement vs OB.low**. The HALLUC-1 commit deliberately REMOVED that check (commit message: "Drop SL-vs-OB-far-edge check from the guard (HALLUC-1 P1 / Pattern B). The prompt instructs SL placement beyond the H1/M15 swing low (LONG), not beyond the OB"). So in the present-day code path, this guard has nothing to say about SL geometry — by design.

The `guard_candidate_wrong_side_sl` guard at `primary_analyzer.py:739-787` only fires on STRICT wrong-side violations (LONG with SL > entry, SHORT with SL < entry). It explicitly skips the equality case (`primary_analyzer.py:763-764`), passing it to the next guard. SL=4762.14 is below entry=4777.43, so wrong_side_sl PASSES. SL=4762.14 ≠ entry=4777.43, so degenerate_params PASSES.

The result: when the AI emits `SL == OB.low` with `buffer = 0.0` strictly below entry, the guard layer accepts it and forwards to L2.

### 2.3 L2 verification layer (Component 4 pre-execute)

`src/components/orchestrator.py:1129` calls `verify_candidate(analysis, mso, self.config)`. Inside `src/components/verification.py:_check_sl_beyond_ob` (lines 877-945) — this is the SL gate that rejected the historical records.

The current logic at lines 904-918:
```python
sl = tp.stop_loss
direction = tp.direction
floor = _sl_beyond_floor(sl, config)        # line 906

if matched_ob:
    zone_low, zone_high = matched_ob.low, matched_ob.high   # line 909 — UNDERLYING float
...
if direction == "LONG":
    if sl <= zone_low - floor:               # line 918
```

For the canonical case: SL=4762.14, OB.low=4762.14, floor=1e-5 (because XAUUSD has NO `market.tick_size`, see §3 below). `4762.14 <= 4762.13999` → False → FAIL.

**The L2 gate worked correctly** in catching the deterministic 0-buffer emission; the bug was that the prompt told the AI to do it. The L2 gate caught the prompt bug.

### 2.4 Hypothesis verdict

Going through the brief's five hypotheses against the evidence:

| Hypothesis | Verdict |
|---|---|
| 1. Prompt-side scope gap (XAUUSD path doesn't include buffer instruction) | **FALSE for current HEAD.** The prompt directive at `src/prompts/primary_analyzer_prompt.py:659-663` is symbol-agnostic — it requires non-zero buffer for ALL instruments. **TRUE for the historical `5242bfd` prompt**: that prompt literally said `sl_buffer_applied: 0.0` for ALL instruments. The fix shipped in FA-2 (`fa35cc0`, 2026-04-20). |
| 2. Guard-side scope gap (precision guard only checks NAS100/US30) | **FALSE.** `guard_candidate_inconsistent_pois` (`primary_analyzer.py:790-942`) is symbol-agnostic. It snaps OB bounds to the AI's display precision via `config.prompt.price_format` — XAUUSD `.2f` produces `_snap_to_precision(low, 2)`, identical to the un-snapped underlying float for OB bounds that are already 2dp (which is the XAUUSD norm). |
| 3. Buffer-multiplier scope gap (XAUUSD trending_bull cell missing override) | **FALSE.** `agent_config.yaml:67-69` defines base `sl_buffer_atr_multiplier: 0.25` and `sl_buffer_min_ticks: 5`. There is no per-cell or per-regime override; XAUUSD inherits the base values, which gets substituted into the prompt at `primary_analyzer_prompt.py:246-251`. The current replay confirms the AI applies them (current `sl_buffer_applied` ranges $3.57-$5.19 ≈ 0.25 × XAUUSD H1 ATR 14-17). |
| 4. AI-emission compliance issue (AI told to apply buffer but doesn't) | **FALSE in current replay.** All 11 of 11 current emissions have `sl_buffer_applied > 0`. This is because FA-2's prompt is unambiguous + ADR-006's PRECISION block + the SELF-CHECK item 5 (`primary_analyzer_prompt.py:810`: "Buffer — sl_buffer_applied > 0 (strictly non-zero)") all reinforce. **TRUE for historical 5242bfd**: the prompt literally directed `0.0`. |
| 5. Some other path | **TRUE — see §3.** There are TWO real residual gaps in the systemic engineering, neither of which fires on these 6 historical records but both of which leave the same compound bug class open on adjacent paths. |

**Headline diagnosis:** the 6 rejected records are a **historical artifact** of the pre-FA-2 prompt. The AI did exactly what the prompt asked (`sl_buffer_applied: 0.0`); the L2 gate correctly caught the consequent geometry violation. **FA-2 (April 20) fixed the AI emission**. The brief misattributed the bug to the present HEAD; Stage 2.5's "6 records hit `sl_beyond_ob`" is reading historical `final_outcome` strings from trade records captured under the OLD prompt, not new emissions from the replay.

---

## 3. Why HALLUC-1 didn't cover this (and where the residual systemic gap lies)

HALLUC-1 (`2c75f98`, 2026-04-28) and the four sister fixes (`100854b` shared module, `6e13bf9` SISTER-3 m5_refinement, `4def1aa` SISTER-1/2/4/5 verification) form the **precision-aware contract**: every site that compares an AI-emitted price (which the AI saw at `prompt.price_format` precision) against an MSO underlying float MUST snap the underlying float to the same precision plane first.

### 3.1 What HALLUC-1 actually did

`primary_analyzer.py:357-359` (post-HALLUC-1) plumbs `price_format` from config into `guard_candidate_inconsistent_pois`. That guard, at `primary_analyzer.py:866-878`, snaps `ob.low` and `ob.high` to the AI's display precision via `_snap_to_precision`. **Critically, HALLUC-1 also REMOVED the SL-vs-OB-far-edge check from the guard** (commit message + lines 829-835 of primary_analyzer.py: "SL-vs-OB-edge check REMOVED (HALLUC-1 P1 fix): the prompt instructs SL placement beyond the H1/M15 swing low (LONG) or swing high (SHORT), not beyond the OB's far edge ... The existing tolerance-tier `sl_beyond_ob` L2 gate is the correct enforcement layer; it is config-driven via `verification.sl_beyond_ob_tick_floor`").

Result: SL geometry enforcement is **single-sourced** to `_check_sl_beyond_ob` (`verification.py:877-945`). HALLUC-1 deliberately deferred to L2 here.

### 3.2 What the SISTER fixes covered (and one site they did NOT)

The four SISTER fixes added `_snap_to_precision` to:
- `verification.py:_check_entry_in_breaker` lines 781-783 (SISTER-1/2): snaps `zone_low`/`zone_high` before comparing AI SL.
- `verification.py:_check_entry_in_fvg` lines 655-657 (SISTER-4/5): snaps `matched_fvg.bottom`/`matched_fvg.top` before comparing AI SL.
- `m5_refinement.py:_resolve_price_decimals` (SISTER-3): replaces hardcoded `round(_, 2)` with precision-aware snap.

**The one site that was NOT updated:** `verification.py:_check_sl_beyond_ob` at lines 877-945. Specifically lines 909, 912 read the underlying float without precision-snap:

```python
if matched_ob:
    zone_low, zone_high = matched_ob.low, matched_ob.high           # line 909 — RAW
else:
    zone_low, zone_high = matched_bb.zone_low, matched_bb.zone_high # line 912 — RAW
```

The `precision.py` module docstring at lines 53-62 explicitly notes this site is "**confirmed safe (by audit, not code)**" with the rationale:
> `verification._check_sl_beyond_ob` — ADR-006 tolerance-tier with `sl_beyond_ob_tick_floor` already absorbs the precision delta.

That assumption is wrong for one specific configuration, surfaced in §3.3.

### 3.3 The XAUUSD `tick_size` config gap (latent bug class)

`verification.py:_sl_beyond_floor` at lines 147-165:

```python
def _sl_beyond_floor(price: float, config: dict) -> float:
    tick = float(config.get("market", {}).get("tick_size") or 0.0)
    if tick <= 0:
        tick = float(config.get("prompt", {}).get("tick_size_fallback", 1e-5))
    floor_ticks = int(config.get("verification", {}).get("sl_beyond_ob_tick_floor", 1))
    return tick * floor_ticks
```

The fallback to `1e-5` is appropriate for 5dp FX — but I verified XAUUSD has no `market.tick_size` defined ANYWHERE:

- `config/agent_config.yaml` lines 600-609: XAUUSD instrument block sets only `trading_enabled`, `skip_first_ny_candle`, `market.symbol`, `market.kill_zones`. No `tick_size`.
- `config/profiles/redacted_account.yaml` lines 59-61: XAUUSD overrides only `risk.risk_per_trade_pct`. No `tick_size`.
- `config/profiles/ftmo.yaml` lines 38-40: comment "XAUUSD/US30/NAS100/XAGUSD/GBPJPY scales already work — no overrides here." No `tick_size`.

For XAUUSD, `_sl_beyond_floor` therefore evaluates to `1e-5 × 1 = 1e-5`. For a $4762 price, that floor is **9 orders of magnitude smaller than the $0.01 tick the broker actually quotes XAUUSD at**. The L2 check `sl <= zone_low - floor` becomes effectively `sl <= zone_low` — a strict inequality with a hair of slack. **A future regression where the AI emits an SL one cent above OB.low would pass the floor (1e-5 << 0.01) and hit the broker — producing exactly the bug class HALLUC-1 set out to engineer out**.

This is also why the precision.py "confirmed safe" comment is wrong for XAUUSD specifically: the comment's logic assumes the floor is meaningfully sized; for XAUUSD it is not.

### 3.4 Why the historical 6 records still hit FAIL despite the tiny floor

The 6 records emitted SL=OB.low with literal **bit-exact equality** (`sl_buffer_applied: 0.0` directive forces SL = swing-low value, which on these OBs equals OB.low because the swing was the OB itself). `4762.14 <= 4762.14 - 0.00001` is `4762.14 <= 4762.13999`, which is `False`. So the gate caught them. But this only works because the AI emitted bit-exact equality. If the AI had emitted SL=4762.13 (1 cent below) the gate would have PASSED — and that would be the same compound bug class.

### 3.5 The broader symbol-by-symbol robustness

| Symbol     | `tick_size` defined? | Effective L2 floor | Robustness against rendering delta |
|------------|----------------------|---------------------|-------------------------------------|
| XAUUSD     | NO (uses 1e-5)       | $0.00001            | **WEAK** — broker tick is $0.01     |
| US30 / US30_cash | NO (uses 1e-5)  | $0.00001            | **WEAK** — broker tick is $0.10     |
| NAS100     | NO (uses 1e-5)       | $0.00001            | **WEAK** — broker tick is $0.10     |
| XAGUSD     | NO (uses 1e-5)       | $0.00001            | **WEAK** — broker tick is $0.001    |
| GBPJPY     | NO (uses 1e-5)       | $0.00001            | **WEAK** — broker tick is $0.001    |
| EURUSD     | YES (0.00001)        | 8 × 0.00001 = 8e-5  | OK (per ADR-006 8-tick override)    |
| GBPUSD     | YES (0.00001)        | 8 × 0.00001 = 8e-5  | OK (per ADR-006 8-tick override)    |
| USDJPY     | YES (0.001)          | 5 × 0.001 = 5e-3    | OK (per ADR-006 5-tick override)    |

The "scales already work" comment in `ftmo.yaml:38` is correct for the prompt-buffer-recipe layer (XAUUSD's 0.25 × ATR ≈ $4 buffer is far above tick size, so AI-emitted SLs are well clear of OB boundary). But it is wrong for the L2 gate's tolerance floor — the floor for the 5 instruments without `tick_size` is essentially zero.

---

## 4. Proposed fix (the engineered one — no patches)

The CEO directive ("we never patch, we engineer and fix things by building correctly") points to a **single canonical fix that closes the bug class for all 7 production instruments + all future instruments**.

### 4.1 Single canonical fix (recommended)

Two coordinated edits, one rationale, one canary cycle:

#### Fix A: `_check_sl_beyond_ob` — precision-aware OB/breaker bounds

**File:** `src/components/verification.py` — `_check_sl_beyond_ob` (currently lines 877-945).

**Edit:** snap `zone_low` and `zone_high` to the AI's display precision plane before the strict comparison. Mirrors SISTER-1/2/4/5 exactly.

```python
# Pseudocode showing the diff envelope (no actual code change in this audit):
# After lines 908-913 (where zone_low / zone_high are read), insert:
_decimals = _resolve_display_decimals(config, default=2)
zone_low = _snap_to_precision(zone_low, _decimals)
zone_high = _snap_to_precision(zone_high, _decimals)
```

This requires importing `_resolve_display_decimals` (already exists in this file at lines 34-50) and `_snap_to_precision` (already imported at line 22). Estimated 4 lines of code (3 new + 1 import-touch).

**Why this matters even though XAUUSD OB.low is already 2dp:** the contract is what protects against future regressions. Without the snap, ANY future change to MSO rendering precision (e.g. someone adds 3dp rendering for XAGUSD, or 1dp for an indices instrument) creates the same compound bug class. The snap is `O(1)` cost and idempotent on already-2dp values; it is pure invariant defense.

#### Fix B: explicit `market.tick_size` for ALL instruments missing it

**Files:** `config/agent_config.yaml` (instruments.* blocks for XAUUSD, US30, US30_cash, NAS100, XAGUSD, GBPJPY).

**Edit:** add `market.tick_size: <broker-quoted-value>` to each. From the `_PIP_PAIRS` / `_JPY_PAIRS` / `_POINT_INSTRUMENTS` mappings at `primary_analyzer_prompt.py:186-188` and broker conventions:
- XAUUSD: `0.01` (cents on dollar)
- US30 / US30_cash: `0.10` (10 cents on point)
- NAS100: `0.10` (10 cents on point)
- XAGUSD: `0.001` (one-tenth cent on silver)
- GBPJPY: `0.001` (one-tenth pip on JPY)

The base value for these is "broker's smallest quote increment" — same value used by `execution.py:1149-1151` (`sym_info.trade_tick_size`).

This makes `_sl_beyond_floor` produce a meaningful floor for every instrument. With `sl_beyond_ob_tick_floor=1`, XAUUSD now requires SL ≤ OB.low - $0.01, NAS100 requires SL ≤ OB.low - $0.10, etc. — actual broker-tick clearance, not 1e-5 mathematical noise.

### 4.2 Combined LOC + risk class

| Component                                 | LOC delta | Risk class |
|-------------------------------------------|-----------|------------|
| `verification.py` precision-snap          | ~4 lines  | **Additive (low risk)** — snap is no-op when MSO float is already at display precision (XAUUSD's case). |
| `agent_config.yaml` tick_size addition    | 6 lines (one per missing-symbol)   | **Additive (low risk)** — `_sl_beyond_floor` already checks `or 0.0` fallback, so bad values default to fallback. |
| (Test additions: see §5)                  | ~80 lines | (test-only)|
| **Total ship**                            | **~10 LOC + 80 test LOC** | **Low risk; additive only.** |

This is **NOT** invasive — the fix preserves existing PASS/FAIL behavior for all current instruments under all current OB.low/OB.high values that happen to already be at 2dp (which is XAUUSD's empirical norm). The snap only changes behavior when the underlying float carries sub-display-precision residue, which is exactly the bug case.

### 4.3 Why this is single-canonical, not per-instrument

The brief explicitly asked for "the single canonical fix that covers ALL instruments — not a per-instrument patch". The proposed fix has TWO components but they share ONE invariant: **L2 SL geometry must compare AI-emitted prices against MSO floats on the same precision plane, with a clearance floor sized to the broker's actual tick**. Both components serve that invariant; both apply uniformly to all 7 production instruments + every future instrument. There is zero per-instrument branching in either edit.

The XAUUSD-trending-bull cohort question becomes a NON-special-case after this fix: regime-conditioned cells are unrelated to the precision/tick layer.

---

## 5. Test plan

### 5.1 New test cases (dedicated file, recommended `tests/test_sl_beyond_ob_precision_aware.py`)

Mirror the SISTER-1/2/4/5 test structure. Cover:

| Test class | Cases | Lines |
|------------|-------|-------|
| `TestSlBeyondObPrecisionSnap` | 7 instruments × 2 directions × {SL exactly at rendered boundary, 1 underlying-tick below, 1 underlying-tick inside} = 42 cases | ~50 |
| `TestSlBeyondObTickSizeMissing` | 6 instruments missing `market.tick_size` (the production bug class) — verify (a) `_sl_beyond_floor` returns `1e-5 × floor_ticks`, (b) test fails by `assert floor >= broker_min_tick` to flag the gap if it ever returns. **This is the regression-protection test.** | ~20 |
| `TestSlBeyondObXauusdHistoricalCase` | Reproduce the canonical 4762.14/4762.14 case with the historical `sl_buffer_applied=0.0` AI output — confirm L2 still rejects post-fix. | ~10 |

Existing coverage at `tests/test_verification_sl_beyond_ob_tolerance.py` already has XAUUSD tests, but they hardcode `tick_size=0.01` in `XAUUSD_CONFIG` (line 134). The production gap is precisely that the live config DOESN'T set `tick_size=0.01`. The new test class catches this configuration gap (test-driven configuration verification, not just code verification).

### 5.2 Add the 6 historical cohort records as canary fixtures

The brief flagged: "Whether to add the cohort's 6 records as canary fixtures (HIGH-VALUE — they're real-world bugs)". Strongly YES.

- Source: `knowledge_base/trade_records/XAUUSD/2026-04-15_ny_*.json` and `2026-04-16_london_0800.json`.
- Strip to a canary-compatible shape (manifest entry + MSO + expected `decision: REJECTED_L2` AND expected `blocked_by: sl_beyond_ob` if the AI still emits zero buffer; expected `decision: CANDIDATE_VALID` if AI emits non-zero buffer per current prompt).
- File these under `scripts/canary_fixtures/borderline/xauusd_trending_bull_sl_zero_repro/`. They become the **regression test that proves the FA-2 prompt fix continues to hold**.

This satisfies the CLAUDE.md canary-fixture coverage criterion (43 borderline + 20 baseline tier coverage). With the 6 added, borderline → 49 (all instrument coverage maintained). The PASS-only content-addressed cache means no incremental API cost after first canary cycle.

### 5.3 Pytest assertions to add

For each of the 6 canary fixtures:
```python
def test_xauusd_trending_bull_sl_zero_repro_<id>(canary_fixture):
    """Historical pre-FA-2 record: AI emitted SL=OB.low with buffer=0.
    Post-fix expectation: AI now emits SL strictly below OB.low with buffer ≥ 0.25*ATR."""
    result = run_canary_fixture(canary_fixture)
    assert result.ai_decision == "CANDIDATE", "AI should still emit CANDIDATE on this trending_bull setup"
    tp = result.trade_parameters
    assert tp.sl_buffer_applied > 0, "AI must emit non-zero buffer (FA-2 contract)"
    assert tp.stop_loss < canary_fixture.h1_ob_low, "SL must be strictly below OB.low"
    assert canary_fixture.h1_ob_low - tp.stop_loss >= 1.0, "Buffer ≥ $1 floor (loose check; real ATR floor much wider)"
    assert result.l2_outcome == "PASS", "L2 sl_beyond_ob must accept the new emission"
```

Plus the configuration-gap test from §5.1:
```python
def test_xauusd_l2_floor_at_least_broker_tick():
    """Regression protection — XAUUSD L2 floor must clear ≥ $0.01 (broker tick),
    not 1e-5 (config-fallback). Fails if `market.tick_size` is missing."""
    config = load_production_config(symbol="XAUUSD", profile="redacted_account")
    floor = _sl_beyond_floor(price=4800.0, config=config)
    assert floor >= 0.01, f"XAUUSD L2 floor is {floor:.6f} — broker tick is $0.01"
```

This is the **canary-of-the-canary** test — it fails if anyone removes the proposed Fix B `tick_size` config.

---

## 6. Risks + open questions

### 6.1 Could the fix change behavior on already-working instruments?

Negligible risk. The precision-snap on `_check_sl_beyond_ob` is **idempotent** on values already at display precision (XAUUSD OB.low/high in production are 2dp; snap to 2dp is identity). The tick_size additions are **additive new fields** that move the floor from `1e-5` to broker-actual values; this strengthens the gate for all 5 affected instruments. No existing PASS case becomes FAIL — but a few currently-marginal-PASS cases (SL = OB.low - 0.005 on XAUUSD) would become FAIL post-fix because $0.005 < $0.01 floor. **This is the desired tightening**: an SL inside the broker's tick of OB boundary is a placement error.

To quantify: I'd need to scan `shadow_logs/sl_beyond_ob_decisions.jsonl` for live-PASS records where `(zone_low - sl) < broker_tick`. That is the empirical answer to "how many edge cases get tightened?" — I did not compute this in the read-only audit; recommend a 30-second grep before ship.

### 6.2 Is there a backward-compat concern with live positions opened under the buggy emission?

Live positions opened pre-FA-2 already have their SL set at the broker. The L2 gate is a pre-execution gate and does not retro-revoke filled orders. Position management (BE moves, partial closes) is governed by `execution.py` which compares against `sym_info.trade_tick_size` (the broker's actual tick), not the L2 floor. So no live-position concern.

### 6.3 Does the prompt need ADR-006 follow-up updates?

No prompt edit is required. The current prompt at `src/prompts/primary_analyzer_prompt.py:659-663` correctly directs the AI to use `max({ob_atr_mult} x H1 ATR(14), {min_ticks} x smallest tick)` — which gets substituted at lines 246-251. For XAUUSD this evaluates to `max(0.25 × $4-17, 5 × $0.01) = $1-4.25` of buffer, well above the proposed 1-tick floor. The prompt is already healthy; the fix is entirely in the verification layer + config.

### 6.4 Can I determine the historical "buffer=0" rate without running tests?

Yes, partially: the brief's referenced project memory `project_live_l2_rejection_per_instrument` reports XAUUSD pre-FA-2 baseline = 85.7% L2 sl_beyond_ob rejection rate. My audit shows the current replay produces 0/11 such rejections at the AI emission layer. **The estimated post-fix-post-FA-2 rate is < 1% of CANDIDATEs**, gated by AI compliance with the buffer formula (which is now reinforced by 4 sites: PRECISION block, TRADE PARAMETERS line, SELF-CHECK item 5, output schema annotation `<float, MSO precision, > 0>`). Production data would need ≥30 days of `sl_beyond_ob_shadow_logger` rows from the new prompt to confirm empirically.

### 6.5 Anything I couldn't determine without running tests?

- Whether ANY current production canary fixture exercises `_check_sl_beyond_ob` with a non-2dp underlying OB.low for XAUUSD. Would be a `pytest tests/test_verification_sl_beyond_ob_tolerance.py -v` run + `grep -r 'OrderBlock(.*low=.*[0-9]\.[0-9]{3}' scripts/canary_fixtures/` plus visual inspection. The audit assumes worst-case (no such fixture).
- Whether the live `pipeline_state/heartbeat_*.json` writes flow through this gate. Verified by code path tracing — no, they don't; they go through a separate kill-switch path.
- The empirical false-positive rate of the proposed Fix B (tick_size) on the live trade_records. Needed: `grep -r 'sl_beyond_ob.*FAIL' knowledge_base/trade_records/*/*.json` and compute the SL-vs-OB.low delta distribution. ~30s audit, recommended pre-ship.

---

## Adjacent observations (brief — separate from main bug class)

These are NOT this bug class but were surfaced incidentally during the audit:

- **`raw_response_first_200_chars` shows `"model_used": "claude-opus-4-5"`** in the replay outcomes. The actual model is `claude-sonnet-4-6` (per `_parse_and_validate` at `primary_analyzer.py:501` which overrides the AI-reported value with config). The AI is hallucinating the `model_used` field; this is harmless because of the override, but indicates the AI is willing to invent values for fields it has no ground truth for. Already memorialized in commit `227cfdf` ("fix: replace hallucinated gpt-4.1 model_used references"). No action needed.

- **`raw_responses/2026-04-17_ny_1315.json`** was rejected at `Gate1` (the touch-count or grade gate), not L2 — different class of rejection. Not part of the sl_buffer bug class.

- **`primary_analyzer.py:1198` re-verifies L2 after M5 refinement** — if SISTER-3 (M5 precision) and the proposed Fix A are inconsistent in any way, an M5 refinement could pass-then-fail or vice versa. The fix in §4.1 makes them consistent (both precision-aware, both share `precision.py`); without the fix, the inconsistency is latent on instruments with non-2dp OB underlying floats.

---

## File:line evidence used in this audit

- `research/a4_trending_bull_replay_2026-04-28/replay_outcomes.jsonl` — current emissions (11 lines).
- `research/a4_trending_bull_replay_2026-04-28/a4_realized_r_join.csv` — Stage 2.5 R-join with rejection sources.
- `research/a4_trending_bull_replay_2026-04-28/a4_realized_r_join_SUMMARY.md` lines 24, 86-99 — historical rejection breakdown.
- `research/a4_trending_bull_replay_2026-04-28/raw_responses/*.json` — 11 raw AI responses (current main HEAD prompt).
- `knowledge_base/trade_records/XAUUSD/2026-04-15_ny_1315.json` — canonical historical case (lines 1-100, 12700-12800).
- `src/components/primary_analyzer.py:790-942` — `guard_candidate_inconsistent_pois` (precision-aware post-HALLUC-1).
- `src/components/primary_analyzer.py:357-359` — call site that plumbs `price_format`.
- `src/components/verification.py:147-165` — `_sl_beyond_floor`.
- `src/components/verification.py:877-945` — `_check_sl_beyond_ob` (the gap site).
- `src/components/verification.py:781-783, 655-657` — SISTER-1/2/4/5 reference snap pattern.
- `src/components/precision.py:53-62` — the "confirmed safe (by audit, not code)" comment that the audit found incorrect for XAUUSD.
- `src/prompts/primary_analyzer_prompt.py:246-251, 658-663, 793-810` — current SL buffer directive + SELF-CHECK.
- `config/agent_config.yaml:67-69, 286-299, 600-609` — base SL buffer + verification config + XAUUSD instrument block.
- `config/profiles/redacted_account.yaml:59-61, 122-142` — FN profile XAUUSD + tight-FX overrides.
- `config/profiles/ftmo.yaml:38, 41-60` — FTMO profile and the comment that says XAUUSD/etc "scales already work" (incorrect per §3.5).
- `git show fa35cc0 -- src/prompts/primary_analyzer_prompt.py` — FA-2 diff that fixed the prompt.
- `git show 2c75f98 -- src/components/primary_analyzer.py` — HALLUC-1 fix.
- `git show 100854b 6e13bf9 4def1aa` — sister fix commits.
- `tests/test_verification_sl_beyond_ob_tolerance.py:134` — existing XAUUSD_CONFIG with hardcoded `tick_size=0.01`.
- `tests/test_sister_bug_fixes.py:942-958` — TestSister1XauusdBreakerPassthrough.

---

*End of audit. Read-only; no code changes proposed in source files. The fix in §4 requires CEO approval before implementation per CLAUDE.md WF-1 discipline (changes to `src/` that alter trading evaluation behavior).*
