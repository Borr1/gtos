# ADR-004 — Market-State Structural Bullish Bias in `identify_structure`

> **Filename note.** The user's task-brief requested this filename verbatim. The existing
> file `004_sl_gate_reconciliation_2026-04-18.md` already uses the integer prefix `004`,
> so this document is functionally **ADR-005** in the repo's existing numbering convention
> (`001_`, `002_`, `003_`, `004_`). The filename is preserved per brief; internally this
> record is referred to as "ADR-004 (bullish-bias)" or "ADR-005" interchangeably.
> Suggestion: rename to `005_market_state_structural_bullish_bias_2026-04-24.md` before
> commit if a clean sequence is preferred. Left to CEO discretion.

---

## 1. Status

**PROPOSED — awaiting CEO decision on fix approach.**

- Date: 2026-04-24
- Author: Claude Code (senior-architect role, Opus 4.7 max effort, ADR-only pass)
- Supersedes: none
- Related records:
  - `research/directional_concentration_audit_2026-04-24/V1_INDEPENDENT_VALIDATION.md` (V1, 2026-04-24)
  - `research/directional_concentration_audit_2026-04-24/report.md` (A7 original audit, 2026-04-24)
  - `research/b_deep_audit_2026-04-19/phase2/zeta_review.md` (Phase-2 review, 2026-04-19, Leak #1 discussion lines 19-46, 282)
  - `research/b_deep_audit_2026-04-19/phase1/zeta_market_state_prechecks.md` (Phase-1 leak claim, lines 128-175)
  - `.context/06_decisions/004_sl_gate_reconciliation_2026-04-18.md` (format reference)

---

## 2. Context

### 2.1 What the bug is

`src/components/market_state.py::identify_structure` (lines 216-257) classifies H1 / H4 /
D1 / M15 structure as `bullish` / `bearish` / `transitional` / `insufficient_data`.
In every realistic production window (168-bar H1, 80-bar H4, etc. per
`config/agent_config.yaml:120-125`) the function's two qualifying branches both evaluate
True simultaneously; the bullish branch is checked first in the `if / elif` chain and
wins by precedence, regardless of whether the bearish signal is numerically stronger.

Relevant code, `src/components/market_state.py:232-247`:

```python
hh_count = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i-1].price)
ll_count = sum(1 for i in range(1, len(lows))  if lows[i].price  < lows[i-1].price)
hl_count = sum(1 for i in range(1, len(lows))  if lows[i].price  > lows[i-1].price)
lh_count = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i-1].price)

recent_pairs = min(3, len(highs) - 1, len(lows) - 1)          # line 237 — saturates at 3

if hh_count >= recent_pairs and hl_count >= recent_pairs:     # line 239 — checked first
    direction = "bullish"
    protected_swing = lows[-1]
elif ll_count >= recent_pairs and lh_count >= recent_pairs:   # line 242 — unreachable when bullish also qualifies
    direction = "bearish"
    protected_swing = highs[-1]
else:
    direction = "transitional"
    protected_swing = None
```

Two compounding defects:

1. **Saturating threshold** at line 237. With a 168-bar H1 window producing ~20 highs and
   ~20 lows, all four counts (hh, hl, lh, ll) routinely exceed 3; `recent_pairs` saturates
   to `3`; both branches qualify. V1 replay over 8,086 H1 production windows across 5
   instruments: 8,072 (99.8%) had both branches qualifying simultaneously (V1
   `V1_INDEPENDENT_VALIDATION.md:166`).
2. **Asymmetric precedence** at lines 239 vs 242. When both branches qualify, bullish
   wins deterministically. The `lh`/`ll` counts can be 3× higher than `hh`/`hl` and the
   function still returns `bullish`. V1 saturation test 4: `hh=3 hl=3 lh=10 ll=10 →
   bullish` (V1 line 129).

### 2.2 Where in code

- `src/components/market_state.py:216-257` — `identify_structure` body.
- `src/components/market_state.py:237` — `recent_pairs = min(3, ...)` cap.
- `src/components/market_state.py:239-247` — bullish-first if/elif/else.
- `src/components/market_state.py:776` — `_build_timeframe_state` calls `identify_structure` for every timeframe (D1, H4, H1, M15), all equally affected.
- `src/components/market_state.py:289-350` — `detect_structure_breaks` gates BOS emission on `structure.direction`; a bullish label yields bullish BOS only (lines 323-336), a bearish label yields bearish BOS only (lines 337-350). **Because the structure direction is stuck bullish, only bullish BOS events are emitted in 99.8% of H1 windows — which in turn means `identify_order_blocks` emits only bullish OBs.** The bias therefore propagates into the OB supply, not just the label.
- `src/components/market_state.py:867-876` — D1/H4/H1/M15 processed identically; no per-TF override.
- `src/components/candidate_features_logger.py:509-511` — `mso_*_structure_direction` logged verbatim from MSO output.
- `src/components/knowledge_base.py:372-374` — session-memory context reads `structure.direction` from D1/H4.

### 2.3 Since when

**Since the initial commit `436c16b` ("initial files", 2026-03-29).** `git log -L` on
`identify_structure` returns that commit only; no subsequent commit has touched the
function. The defect has existed for the entire life of the system
(V1 `V1_INDEPENDENT_VALIDATION.md:9`, A7 `report.md:97`). Note Phase-2 review `zeta_review.md:41-46`
explicitly raised the same mechanism on 2026-04-19 and asked whether it was "a bug or a
conservative design choice"; at that time the mechanism was flagged but not prioritised
because the R-impact estimate it was attached to (the D1-bias-lag / EURUSD +110R claim)
collapsed under correlated-sample correction. V1 replay (2026-04-24) on
production-faithful H1 windows proves the production impact is broader and more severe
than the D1-bias-lag framing suggested.

### 2.4 Impact

Three layers of evidence:

**Layer 1 — live trading (directly observed):**
- 141/141 lifetime CANDIDATE decisions LONG (V1 Task 1, `V1_INDEPENDENT_VALIDATION.md:22-38`).
- 112/112 April CANDIDATEs on the 4 LIVE instruments LONG (100%, not the "98%" the triggering forensic had claimed).
- 44/44 post-redacted_account-kickoff (2026-04-20 onwards) CANDIDATEs LONG.
- 0 SHORT CANDIDATEs ever produced, across five instruments, over the entire logging window.

**Layer 2 — shadow / internal state (directly observed):**
- `mso_h1_structure_direction = bullish` for 384/384 rows in `shadow_logs/candidate_features_log.jsonl` over Apr 17-23 (all five instruments).
- `mso_m15_structure_direction = bullish` for 384/384 rows over the same window.
- `mso_d1_structure_direction = bullish` or `transitional` only; 0 bearish.
  (V1 Task 3, `V1_INDEPENDENT_VALIDATION.md:60-67`.)

**Layer 3 — production-faithful replay (reproducible):**
- 8,086/8,086 168-bar H1 windows across 5 instruments × Jan 2 – Apr 20, 2026, returned `bullish`. Zero `bearish`. Zero `transitional`. Zero `insufficient_data`. (V1 Task 7, `V1_INDEPENDENT_VALIDATION.md:159-167`.)
- 99.8% of those windows had the bearish branch also qualifying (i.e., the bug condition fires in nearly every production decision).

**Live pipeline snapshot** (`knowledge_base/pipeline_state/02_market_state.json`, timestamp
`2026-04-23T17:00:05`):

| TF   | Label       | hh | hl | lh | ll | Both branches qualify? |
|------|-------------|----|----|----|----|------------------------|
| D1   | bullish     | 3  | 2  | 0  | 0  | No (bearish branch fails)           |
| H4   | bearish     | 2  | 6  | 5  | 6  | No (bullish branch fails on hh<3) — and the correct bearish label is emitted |
| H1   | **bullish** | 11 | 9  | 11 | 9  | **YES** — bearish also qualifies    |
| M15  | **bullish** | 43 | 38 | 43 | **50** | **YES** — `ll=50 > hh=43`; bearish is numerically stronger, bullish wins by precedence |

At this instant, H4 correctly returned `bearish` because the bullish branch failed
(hh=2 < recent_pairs=3). H1 and M15 demonstrate the bug live: bearish qualifies, at M15
bearish is stronger by count, yet `bullish` is the label.

**Validated-number exposure.** Every number in CLAUDE.md's "Validated numbers" section
that was computed over the live or batch-filtered MSO sample has been computed on a
sample drawn from the bullish-only partition of the true production distribution.
Their external validity under the fixed detector is unknown. (See §8 for itemised
mapping.)

### 2.5 Causal chain (why 100% LONG follows)

Reproduced from A7 `report.md:159-167` and verified by V1:

1. `identify_structure(H1)` returns `bullish` in ~100% of production windows.
2. `identify_structure(H4)` returns `bullish` in 94-95% of production windows (H4's 80-bar window has fewer swings; bullish branch fails more often than on H1; bearish occasionally reachable).
3. `identify_structure(D1)` returns `transitional` most often, `bullish` sometimes, `bearish` very rarely (D1's 30-bar window often lacks 3 swings of each type — the one case where the saturating-threshold mechanism mostly does not fire).
4. AI emits `daily_bias.direction = bullish` for 901/1,283 evals (70.2%) and `bearish` for 31/1,283 (2.42%). AI *can* emit bearish when the inputs support it.
5. When AI emits `bearish` D1 bias, downstream C3 gate `direction matches H1 bias` fails because H1 structure is locked bullish → `NO_TRADE`. None of the 31 bearish-bias rows ever became a SHORT CANDIDATE.
6. When AI emits `bullish` D1 bias AND MSO H1/H4 structure is bullish, LONG CANDIDATEs pass.
7. Net effect: 100% LONG, zero SHORT, for the entire life of the system.

---

## 3. Constraints

1. **System is LIVE** on redacted_account $100K demo since 2026-04-20 per CLAUDE.md §Status. Any fix must be validated against historical data AND run in shadow mode against live tick-by-tick evaluation before production cutover. Direct production deployment of an unvalidated fix is out of bounds under the repository's WF-1 discipline (`CLAUDE.md §WF-1 DISCIPLINE`).
2. **Anthropic API budget cap** is $50-60/month. The cap is structural (auto-reload disabled per CLAUDE.md memory `project_anthropic_billing_auto_reload_disabled.md`). Each full 3.5-month T7 slice (Jan 2 – Apr 13, XAUUSD only) costs ~$27 at `ai.primary_model=claude-sonnet-4-6` with `effort=max` (CLAUDE.md §Running the System). A full 5-instrument × 2-slice re-validation is ~$270 and exceeds the monthly cap — decisions about scope must be made explicitly by the CEO.
3. **Single decision-maker.** CEO Borhen is the only human in the loop. No delegation to vote among reviewers is possible; Claude Code's council pattern may be invoked but ultimate sign-off is single-author.
4. **Validated-number load-bearing.** Numbers in CLAUDE.md's "Validated numbers" section (62% XAUUSD WR, 65% batch WR, 10.3% CAND rate, 70% OB continuation, 99.4% MC P(pass FTMO), per-instrument WRs) are referenced throughout the documentation and by Monte Carlo simulations. Any fix whose behaviour would plausibly invalidate those numbers requires re-validation BEFORE the system can be trusted in production.
5. **Backtest infrastructure exists.** `scripts/simulate_t7_live_period.py` runs the production pipeline end-to-end on CSV slices per `data/historical_2026/`. It consumes the same `identify_structure` under test, so T7 replay is a valid counterfactual. Per-slice cost is ~$27 for XAUUSD (3.5 months); FX precision bug and `_FILL_EPSILON` mis-scale (CLAUDE.md unresolved #7/#8) are known residual concerns for EURUSD/FX slices.
6. **Shadow deployment plumbing exists.** `src/components/candidate_features_logger.py` already logs MSO structure fields verbatim per live candle; a parallel `v2` classifier can be added as a log-only column without touching the decision path. `src/components/proximity_shadow_logger.py` is the conventional pattern for shadow gates (file header documents intent). This reduces the shadow-deploy engineering burden to adding one column and one computation.
7. **CLAUDE.md guardrails apply.** Changes to `src/` that alter trading logic require CEO approval. The proposed fix is a trading-logic change (not a pure bug-crash fix — the function currently "works", it is just systematically wrong), per the Phase-2 review's own framing: "the function works — it classifies structure with a known conservative threshold. Changing ... is a design change, not a crash fix" (`zeta_review.md:282`). Therefore this ADR does not pre-authorise any fix; it lays out the option space for CEO decision.

---

## 4. Fix options

Seven candidate fixes below. Each is rated on four axes (invariant, behavioural change,
risk profile, validation burden) with a code sketch showing the before-after diff of
`src/components/market_state.py:232-247`.

A common notation used below:

- `bull_ok := (hh_count >= threshold_bull) and (hl_count >= threshold_bull)`
- `bear_ok := (ll_count >= threshold_bear) and (lh_count >= threshold_bear)`
- `recent_pairs` in the original is both the threshold AND the variable name; in what
  follows "threshold" is the parameter.

### Option A — Raise the saturating threshold

**Code sketch:**

```python
# BEFORE
recent_pairs = min(3, len(highs) - 1, len(lows) - 1)
if hh_count >= recent_pairs and hl_count >= recent_pairs:
    direction = "bullish"
elif ll_count >= recent_pairs and lh_count >= recent_pairs:
    direction = "bearish"
else:
    direction = "transitional"

# AFTER (option A1 — fixed raised constant)
recent_pairs = min(6, len(highs) - 1, len(lows) - 1)
# ... rest unchanged

# OR (option A2 — percentile of swing count)
swing_pairs = min(len(highs) - 1, len(lows) - 1)
recent_pairs = max(3, swing_pairs // 2)      # at least half the pairs
# ... rest unchanged
```

**Invariant guarantee:** neither branch qualifies unless roughly half the swings in its
direction agree. Bullish/bearish label only emitted on clearly-directional windows;
in most real markets this means `transitional` is the common case.

**Expected behavioural change:** a substantial fraction of current `bullish` labels
flip to `transitional` rather than to `bearish`. Based on the live H1 snapshot
(hh=11, hl=9, lh=11, ll=9), at threshold=6 the bullish branch still qualifies (11>=6, 9>=6)
and the bearish branch also qualifies (11>=6, 9>=6) — so the precedence bug is not
fixed by Option A alone; it must be combined with one of Options B-F. At threshold=10,
the H1 snapshot would flip to `transitional` (hl=9 < 10). V1 replay under A1
(threshold=6) is a straightforward re-run — but **V1 did not run this experiment** so
expected-flip fractions are unknown. Estimated from the Phase-1 analysis
`zeta_market_state_prechecks.md:175`: raising the threshold narrows the bullish branch
but would not, on its own, unlock bearish when both branches still qualify.

**Risk profile:** conservative. Partially fixes the bug by reducing the joint-qualification
rate, but does not address the precedence-on-tie issue. **The Phase-2 review already
flagged this:** the function "is just conservative about regime flips" (`zeta_review.md:46`);
raising the threshold makes it *more* conservative, potentially suppressing legitimate
bullish labels as well. **Must be paired with C/D/E/F to address the precedence-on-tie problem.**

**Validation burden:** low — single parameter sweep. Recommend A1 at threshold ∈ {4, 5, 6, 8}
as a parameter sweep alongside whichever of C/D/E/F is the primary fix.

**Testability:** trivial. Existing swing-count fixtures test this directly.

**New bugs possible:**
- If the threshold is set too high, `transitional` rate explodes; NO_TRADEs triple.
- Real rapid trend flips (March 2026 NAS100 +15% rally, per Phase-2 replay `zeta_review.md:31-39`) would not be reclassified until the window refills — same problem the Phase-1 review raised for Leak #1, just in a different axis.

**Minimum prompt change:** none.

---

### Option B — Reverse precedence (bearish checked first)

**Code sketch:**

```python
# AFTER
if ll_count >= recent_pairs and lh_count >= recent_pairs:
    direction = "bearish"
elif hh_count >= recent_pairs and hl_count >= recent_pairs:
    direction = "bullish"
else:
    direction = "transitional"
```

**Invariant guarantee:** when both branches qualify, bearish wins.

**Expected behavioural change:** symmetric inversion. Instead of 100% bullish, the system
would produce ~100% bearish on the same data (V1 saturation test 4: 99.8% of windows
have BOTH branches qualifying — simply flipping the order flips the outcome 99.8% of
the time).

**Risk profile:** catastrophic in symmetry. This is the worst of both worlds; the system
would trade only SHORT in all regimes.

**Validation burden:** not needed; the outcome is predictable from V1 Task 7.

**Testability:** trivial unit test.

**New bugs possible:** the same 100%-one-direction failure mode, just the opposite sign.

**Minimum prompt change:** none.

**Conclusion:** included for completeness per the brief. **NOT RECOMMENDED** — the
problem is not "bullish wins when it should be bearish" but "the tie-breaking is
direction-independent rather than evidence-based". Swapping the order does not fix the
class of bug, it just re-signs it. Listed explicitly so the CEO can dismiss it.

---

### Option C — Strength-based tie-break

**Code sketch:**

```python
# AFTER
bull_ok = hh_count >= recent_pairs and hl_count >= recent_pairs
bear_ok = ll_count >= recent_pairs and lh_count >= recent_pairs

if bull_ok and bear_ok:
    bull_strength = hh_count + hl_count
    bear_strength = ll_count + lh_count
    if bull_strength > bear_strength:
        direction = "bullish"
    elif bear_strength > bull_strength:
        direction = "bearish"
    else:
        direction = "transitional"      # true tie → no call
elif bull_ok:
    direction = "bullish"
elif bear_ok:
    direction = "bearish"
else:
    direction = "transitional"
```

**Invariant guarantee:** when both branches qualify, the side with higher aggregate
evidence wins; exact ties go to `transitional` (not to either side by default).

**Expected behavioural change (from live H1 snapshot):**
- Current (buggy): `bullish` at hh=11, hl=9, lh=11, ll=9 (bull=20, bear=20 → tie).
  Under Option C: `transitional`.
- Current M15: `bullish` at hh=43, hl=38, lh=43, ll=50 (bull=81, bear=93 → bear wins).
  Under Option C: `bearish`. This matches the intuition that at M15 the bearish signal
  is numerically stronger.

Using V1's snapshot data, Option C would flip at least some windows to `bearish` that
are currently mis-labeled. **Exact fraction is not known** without a full replay; must
be computed (see §6).

**Risk profile:** low-medium. Preserves the existing branch semantics (both conditions
must be met for a directional call) and only changes the tie-break. Bearish comes online
only when genuinely warranted.

**Validation burden:** medium. Requires the full 8,086-window replay under Option C's
detector to characterise the new label distribution, plus at least two T7 slices (XAUUSD
Jan-Feb, Mar-Apr) to re-measure CAND rate and WR.

**Testability:** straightforward — synthetic fixtures with known hh/hl/lh/ll counts
(V1 already wrote `v1_fixture_test.py`; extend for ties and near-ties).

**New bugs possible:**
- Exact-tie transitional might be common at M15 (many equal counts) — could over-produce `transitional`. Monitor NO_TRADE-due-to-transitional rate.
- `bull_strength = hh + hl` treats HH and HL as equally informative; that may be wrong (HHs are arguably stronger than HLs because they represent *new* highs). Could refine to weighted sum but that's an orthogonal design decision.
- A very slight tilt (hh+hl = 10, lh+ll = 11) gets called `bearish` even though the underlying evidence is near-tie. Dead-zone threshold (tie margin ≥ X) would harden this; see Option F.

**Minimum prompt change:** none — prompt already handles all three directions.

---

### Option D — Net-score classifier

**Code sketch:**

```python
# AFTER
bull_points = hh_count + hl_count
bear_points = ll_count + lh_count
net_score   = bull_points - bear_points

# Dead-zone threshold scaled by sample size; candidate = 2
min_swings = min(len(highs) - 1, len(lows) - 1)
dead_zone_threshold = max(2, min_swings // 4)   # ~25% of pairs

if net_score >= dead_zone_threshold:
    direction = "bullish"
elif net_score <= -dead_zone_threshold:
    direction = "bearish"
else:
    direction = "transitional"
```

**Invariant guarantee:** symmetric by construction. `bullish` iff evidence surplus
exceeds threshold; `bearish` iff deficit exceeds threshold; otherwise `transitional`.
No "both branches qualify" state can exist.

**Expected behavioural change (live snapshot):**
- D1: net = (3+2) − (0+0) = 5; min_swings=4, threshold=2 → `bullish` ✓ (matches current label for the right reason)
- H4: net = (2+6) − (5+6) = −3; min_swings=?, threshold≥2 → `bearish` ✓
- H1: net = (11+9) − (11+9) = 0; → `transitional` (currently mislabeled bullish)
- M15: net = (43+38) − (43+50) = −12; threshold large, but −12 still far past it → `bearish` (currently mislabeled bullish)

**Risk profile:** low-medium. Cleanest first-principles rewrite. Removes the two-branch
ambiguity entirely. The Phase-1 review flagged Leak #1 with essentially this fix in
mind (`zeta_market_state_prechecks.md:175` — "should be windowed count, not all-pairs").

**Validation burden:** medium. Same as Option C — full replay + at least two T7 slices.

**Testability:** very easy. A single numeric score is trivially unit-testable with
synthetic swings.

**New bugs possible:**
- `dead_zone_threshold` is new tunable. Needs its own pre-deployment sweep (V1 saturation
  data suggests candidate values of 2, 3, 4, 6).
- At very low swing counts (len(highs)==2, len(lows)==2 → `min_swings=1`), threshold collapses to 2 which may never be reached. Behaviour: likely `transitional`; verify.
- `hh_count + hl_count` weights HL equally to HH. Option C inherits this; Option D amplifies it via the difference. Could be refined to weighted net-score but see §4 warning for Option C.

**Minimum prompt change:** none.

---

### Option E — Swing-slope-based classifier

**Code sketch:**

```python
# AFTER
# Linear regression of highs vs their indices; same for lows
def _slope(points: list[Swing]) -> float:
    if len(points) < 2:
        return 0.0
    n = len(points)
    xs = [s.index for s in points]
    ys = [s.price for s in points]
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n)) or 1.0
    return num / den

high_slope = _slope(highs)
low_slope  = _slope(lows)

# Normalize by current price to make threshold instrument-independent
price = (highs[-1].price + lows[-1].price) / 2.0
norm_high_slope = high_slope / price
norm_low_slope  = low_slope  / price

threshold = 1e-5                  # empirical — tune per-instrument
if norm_high_slope > threshold and norm_low_slope > threshold:
    direction = "bullish"
elif norm_high_slope < -threshold and norm_low_slope < -threshold:
    direction = "bearish"
else:
    direction = "transitional"
```

**Invariant guarantee:** `bullish` iff both swing highs AND swing lows trend upward;
`bearish` iff both trend downward. No both-branches-qualify state by construction
(slopes have a sign).

**Expected behavioural change:** unknown without empirical replay. Conceptually, E
should be strictly more sensitive than D to recent acceleration — a pullback late in
the window may depress the slope on one series even if the overall level is rising.
Calibration is instrument-specific (`threshold` must be tuned per-instrument per-TF).

**Risk profile:** medium. This is a different primitive from counting; it opens a new
research axis. Threshold tuning for five instruments × four TFs = 20 parameters is
substantial; a bad calibration could cause over- or under-fit to the Jan-Apr 2026
sample.

**Validation burden:** high. Needs per-instrument threshold calibration before replay,
then full T7 re-validation.

**Testability:** moderate. Synthetic slope fixtures easy; real data noise hard to
reason about without empirical runs.

**New bugs possible:**
- Slope is sensitive to outliers (a single sweep wick → false slope sign). `_slope`
  should probably use median-of-slopes (Theil-Sen) or Huber regression; this compounds
  engineering complexity.
- Normalising by price doesn't help non-percentage instruments like US30 or JPY-quote
  pairs in the same way — empirical calibration per-symbol needed.
- Transient whipsaw between `bullish`/`bearish`/`transitional` possible near zero-slope;
  could be smoothed by requiring N consecutive windows, but that re-introduces a
  memory-like mechanism the current detector deliberately avoids.

**Minimum prompt change:** none — produces same labels.

---

### Option F — Hybrid count + slope

**Code sketch:**

```python
# AFTER
bull_ok = hh_count >= recent_pairs and hl_count >= recent_pairs
bear_ok = ll_count >= recent_pairs and lh_count >= recent_pairs

if bull_ok and bear_ok:
    high_slope = _slope(highs)
    low_slope  = _slope(lows)
    if high_slope > 0 and low_slope > 0:
        direction = "bullish"
    elif high_slope < 0 and low_slope < 0:
        direction = "bearish"
    else:
        direction = "transitional"
elif bull_ok:
    direction = "bullish"
elif bear_ok:
    direction = "bearish"
else:
    direction = "transitional"
```

**Invariant guarantee:** existing branch semantics preserved for unambiguous cases;
slope breaks ties on the ambiguous ones.

**Expected behavioural change:** in unambiguous windows (bull_ok XOR bear_ok), behaviour
unchanged from current. In ambiguous windows (99.8% of production per V1),
slope decides. Because the existing `if` chain short-circuits on bull_ok XOR bear_ok,
this fix is strictly additive — no current correctly-labeled window flips.

**Risk profile:** low. Most conservative minimal-behaviour-change-for-the-common-case fix.

**Validation burden:** medium. Same as C/D because 99.8% of windows exercise the
tie-break path.

**Testability:** good. Synthetic tests for each arm.

**New bugs possible:**
- `_slope` outlier sensitivity (same as Option E).
- Mixed-signal windows where e.g. highs slope up but lows slope flat → default
  `transitional`. This is a legitimate outcome for a genuinely transitional window,
  but more frequent than the current detector produces.
- Adds a second primitive (slope) into a function currently built on counts — costs
  test surface area and code readability.

**Minimum prompt change:** none.

---

### Option G — Direction-agnostic with explicit `neutral` / downstream gate

**Code sketch:**

```python
# AFTER — identical to Option D (net-score) but the orchestrator consumes
# `direction ∈ {bullish, bearish, transitional, neutral}` where `neutral`
# is a new explicit state distinct from `transitional`.
# (In Option D, transitional already plays this role; G formalises it.)

# Downstream: pre-AI gate and permissions gate require
#   direction in {bullish, bearish}
# and treat {transitional, neutral} as NO_TRADE with a dedicated reason.
```

**Invariant guarantee:** system only trades when structure is decisively directional.
No "coerced" label is ever produced.

**Expected behavioural change:** fewer CANDIDATEs (some of today's bullish labels flip
to transitional/neutral, suppressing those trades). CAND rate drops by approximately the
same fraction of windows that were genuinely ambiguous. The edge-preservation question is
whether those trades were +EV or −EV as a subset; unknown without replay.

**Risk profile:** medium. The gate semantics change means downstream consumers
(orchestrator prescreen, primary analyzer prompt, permissions) need a synchronised edit.
This is a larger blast radius than C/D/F.

**Validation burden:** high. Requires all the replay work of C/D plus re-testing the
downstream surface area (the pre-AI gate at `src/components/pre_ai_gates.py` already
handles multi-direction symmetrically per A7 `report.md:123-124`, but needs an explicit
`neutral` branch).

**Testability:** medium — more integration tests needed.

**New bugs possible:**
- Every downstream consumer that currently assumes `direction ∈ {bullish, bearish, transitional, insufficient_data}` must be audited. Grep `structure.direction` — already 20+ call sites per earlier grep (candidate_features_logger, knowledge_base, d1_bias_lag_logger, chart_renderer). Any consumer that assumes a closed-world match of `{bullish, bearish}` with `transitional` as the default else-branch needs adjustment.

**Minimum prompt change:** prompt likely already supports neutral/ranging via the
`daily_bias.direction = ranging` arm; need to audit `src/prompts/primary_analyzer_prompt.py:165` (A7 report cites "H1 bullish → LONG. H1 bearish → SHORT. Mismatch → FAIL.") to confirm how the prompt handles absent direction.

---

### Option H — [added] Symmetric `if / if / else`: emit BOTH labels on tie, let downstream sort it out

**Rationale.** The CEO brief enumerates A-G and invites additions for completeness.
Option H is added for symmetry analysis; it is **not recommended**.

**Code sketch:**

```python
# AFTER
bull_ok = hh_count >= recent_pairs and hl_count >= recent_pairs
bear_ok = ll_count >= recent_pairs and lh_count >= recent_pairs

if bull_ok and not bear_ok:
    direction = "bullish"
elif bear_ok and not bull_ok:
    direction = "bearish"
elif bull_ok and bear_ok:
    direction = "conflicted"        # new state
else:
    direction = "transitional"
```

**Invariant guarantee:** no tie-break happens in the detector; ambiguity is surfaced as a
distinct state.

**Why not recommended:** creates a state (`conflicted`) that 99.8% of H1 production
windows enter, and no downstream consumer knows what to do with it. Either
`conflicted → NO_TRADE` (then practically equivalent to Option G with more plumbing) or
`conflicted → fall back to AI decision` (re-creates the AI-trusting semantics the
deterministic gates were built to avoid). Included for taxonomic completeness.

---

### Summary table

| Option | Invariant | CAND flips | Risk level | Val. burden | Testability | Downstream changes |
|---|---|---|---|---|---|---|
| A | Higher threshold, same branches | Probably ↓ bullish, ↑ transitional; net zero unlock of bearish | low-med | low | easy | none |
| B | Bearish-first | Flips 100% LONG → 100% SHORT | catastrophic | N/A | easy | none |
| C | Strength tie-break | Some bullish → bearish + some → transitional | low-med | med | easy | none |
| D | Net score | Some bullish → bearish + some → transitional (cleaner) | low-med | med | easy | none |
| E | Slope | Unknown, per-instrument calibration | medium | high | medium | none |
| F | Count + slope tie-break | Strictly additive | low | med | good | none |
| G | Explicit neutral gate | ↓ CAND rate, unknown edge | medium | high | medium | audit all consumers |
| H | Emit `conflicted` | No tie-break in detector | not practical | - | - | everything |

---

## 5. Proposed decision framework

The option space collapses into three genuine design positions. The CEO should pick one:

**Position P1 — minimum-change-to-ship:** Option C (strength tie-break).
- Rationale: touches ONE line (the tie-break); preserves everything else about
  `identify_structure`; prompt unchanged; downstream consumers unchanged;
  unit-testable with existing fixture infrastructure.
- Use this if the priority is "unblock SHORT CANDIDATEs fast without compounding risk".

**Position P2 — correctness-from-first-principles:** Option D (net-score classifier).
- Rationale: structurally symmetric by construction; removes the two-branch pattern
  entirely; more interpretable under cognitive load; easier to explain in a postmortem
  or to an auditor. Behaves identically to Option C on the live snapshot but has a
  cleaner spec.
- Use this if the priority is a rewrite that eliminates the bug class, not just
  the specific failure.

**Position P3 — novel-but-explainable:** Option E (swing-slope) or F (hybrid).
- Rationale: opens a new research axis (slope-based structure identification) that
  could be more robust to discrete swing counts in choppy regimes. Adds engineering
  complexity (`_slope`, outlier handling, per-instrument threshold calibration) and
  validation cost.
- Use this only if the CEO has a separate research interest in trend-measurement
  primitives. Not motivated by the current bug alone.

**Recommended default (not forced):** Position P2 → **Option D (net-score classifier)
with `dead_zone_threshold = max(2, min_swings // 4)`.** Reasoning:

- Bug class is "two-branch ambiguity + precedence tie-break"; Option D removes the
  branch structure entirely, which eliminates the bug class — not just the instance.
- Option D is the simplest code that admits a symmetric, provably-unambiguous fix.
- CAND-flip volume on live H1/M15 snapshots is intuitive (H1 tie → transitional,
  M15 bearish-stronger → bearish).
- Per-instrument calibration is NOT required (percentage-of-swings threshold).
- Unit test surface is small: synthetic swing counts in, label out.
- Combined with Option A's raised threshold on the underlying counts is a future
  parameter-tuning exercise, not a pre-deployment block.
- Prompt and downstream code are unaffected.

**Against the default:** Option C is a strictly smaller diff (change ~5 lines; keep
the two-branch `if/elif/else` shell). If the CEO prefers minimum-diff-for-minimum-risk,
Option C is equally defensible. The live-snapshot behaviour is identical for C and D on
H1/M15 in the example data.

**Strongly not recommended:** Option B (symmetric-but-inverted bug), Option H
(practically unimplementable), Option A alone (doesn't fix the precedence issue).

---

## 6. Backtest plan

Assumes the CEO picks **Option D** (net-score classifier). Substitute the chosen
detector wherever "v2" appears below. Structure of plan is option-agnostic.

### 6.1 Sanity-check fixtures (no API cost)

1. Extend `research/directional_concentration_audit_2026-04-24/v1_fixture_test.py` with
   20+ synthetic windows covering:
   - 6 clear bullish uptrend (HH/HL cascades).
   - 6 clear bearish downtrend (LL/LH cascades).
   - 4 balanced range (equal HH+HL vs LL+LH).
   - 4 reversal-in-progress (window early-half bullish, late-half bearish).
2. Run v1 detector + v2 detector + ground-truth label on all 20+ fixtures.
3. **Decision criterion:** v2 matches ground-truth ≥ 19/20 AND does not regress any of
   v1's previously-correct fixtures (`v1_fixture_test.py:195` already tests boundary at
   `recent_pairs=3`).

**Cost:** $0. **Time:** < 1 hour.

### 6.2 Historical replay (no API cost)

1. Run v2 `identify_structure` on every 168-bar H1 window Jan 2 – Apr 20, 2026, across 5 instruments (8,086 total windows per V1 Task 7, `V1_INDEPENDENT_VALIDATION.md:160-166`). Extend `research/directional_concentration_audit_2026-04-24/v1_historical_replay.py` to run v2.
2. Report per-instrument:
   - v2 label distribution: % bullish / bearish / transitional.
   - v1 vs v2 per-window flip matrix (bullish→bullish / bullish→bearish / bullish→transitional / etc.).
   - % of bearish v2 labels by calendar week (check for regime sensitivity).
3. Run the same on H4 (120-bar windows), D1 (30-bar), M15 (672-bar) for completeness.
4. **Decision criterion:** v2 per-instrument bearish rate is non-zero, plausibly reflects
   actual directional market moves per A7 Table §3 (e.g., GBPUSD 60% bearish D1 days in
   April should produce some non-zero H1 bearish labels).

**Cost:** $0 — pure CSV replay. **Time:** ~1 hour of compute, <1 hour interpretation.

### 6.3 T7 simulation replay — production-faithful with API call

1. Run `scripts/simulate_t7_live_period.py` with a **v2-patched** `market_state.py` on
   representative slices:
   - **Minimum tier (~$54):** XAUUSD Jan 2 – Feb 13 + Mar 1 – Apr 13. Covers two slices
     with known pre-fix baselines in `research/t7_live_simulation/` (e.g.,
     `XAUUSD_t7_simulation_jan_mar11.json`).
   - **Mid tier (~$162):** XAUUSD + USDJPY + EURUSD × (Jan 2 – Feb 13, Mar 1 – Apr 13).
     Covers a FX pair (regime-sensitivity check) and one research instrument
     (EURUSD — can cross-reference to the Phase-2 audit's EURUSD L2 replay).
   - **Full tier (~$270):** all 5 live instruments × 2 slices. Exceeds current monthly
     budget.
2. For each slice: record every AI evaluation's decision (CANDIDATE / NO_TRADE) and,
   for CANDIDATEs, the direction + entry/SL/TP + simulated outcome (per the T7 harness).
3. Produce comparison table vs the equivalent v1 simulation artifacts in
   `research/t7_live_simulation/`.

**Budget gating.** The minimum tier (~$54) fits the monthly cap (noting current spend at
~$12/mo canary-cache baseline). Mid tier (~$162) requires the CEO to either (a) allocate
~3 months of API budget up-front or (b) accept a narrower validation scope.

**Decision criterion (binary):** go/no-go gate for shadow deployment, defined in §6.5.

### 6.4 Metric comparison

For each slice (v1 baseline vs v2 fixed):

| Metric | Pre-fix | Post-fix | Delta | Significance test |
|--------|---------|----------|-------|-------------------|
| CAND rate (% of evaluated setups) | from v1 artifacts | from v2 run | absolute pp | binomial CI |
| Fraction of CANDIDATEs SHORT | 0% (v1) | TBD (v2) | - | descriptive |
| WR on LONG CANDIDATEs | 62% baseline | TBD | pp | Fisher exact |
| WR on SHORT CANDIDATEs | N/A | TBD | N/A | one-sample vs 40% null (1.5R TP break-even) |
| Expectancy (R/trade) | +0.200R (batch) | TBD | R | t-test, p<0.05 |
| MaxDD over slice | from v1 | TBD | % | Monte Carlo 10k resamples |

### 6.5 Re-derivation of XAUUSD "62% WR n=129" claim

The "62% WR n=129" headline in CLAUDE.md §Validated Numbers was computed on the
Oct 2025 – Mar 2026 batch (`knowledge_base_backtest/`, see
`knowledge_base_backtest/analysis/data_exploitation_20260405.md`). That batch's CANDIDATE
set already included SHORT entries blocked by the `direction_mismatch` safety gate
(`permissions.py:609-614`); per `data_exploitation_20260405.md:210-230`, 29 SHORT
CANDIDATEs were historically generated and then blocked. **Important nuance:**
- The batch WAS computed on AI outputs that could go SHORT — meaning the AI generated
  SHORT decisions on the batch but a downstream permissions gate dropped them.
- However, those SHORT CANDIDATEs were still fed the SAME biased MSO as the current live
  system; so the AI's SHORT recommendations were generated *despite* a bullish-locked H1
  structure, most likely relying on the AI's "override" reasoning when it saw bearish M15
  structure.
- **Implication:** the 62% WR on the 129 LONG-winning trades may be reliable IF (a) the
  LONG subset's edge is independent of what the SHORT subset would do under fixed H1
  structure. That is a non-trivial assumption.

Re-validation step:
1. Pull the 129-trade XAUUSD sample from the batch.
2. Re-run the same backtest harness with v2 `identify_structure`.
3. Check whether:
   a. The same 129 trades still become CANDIDATEs (most will — bullish H1 with genuine
      bullish evidence will still label bullish under any of the options).
   b. Additional SHORT trades get unlocked; measure their WR and expectancy.
   c. The 62% WR on the LONG subset is preserved (expected, since the fix primarily
      adds bearish CAPACITY, not removes bullish ones).

**Cost:** ~$27 for the XAUUSD Oct-Mar batch re-run if API-gated; free if deterministic
mechanical replay (most batch trades used AI evaluation, so likely $27).

### 6.6 Decision criteria for shadow deployment

Shadow deploy v2 alongside v1 (NOT replace v1) iff ALL the following hold after §6.1-6.5:

1. **C1 (sanity):** v2 passes ≥ 19/20 ground-truth fixtures; v2 does not regress any
   correct v1 label on the existing `v1_fixture_test.py`.
2. **C2 (distribution):** v2 produces at least 5% bearish H1 labels across the 8,086-window
   replay (i.e., genuinely breaks the 0%/100% pathology).
3. **C3 (XAUUSD edge preservation):** v2 XAUUSD WR on unchanged CANDIDATEs ≥ 55% (>55% is
   3σ below the 62% baseline binomial σ ~4.3pp for n=129 — permissive lower bound).
4. **C4 (no catastrophic regression):** v2 on any slice does not produce negative expectancy
   with p < 0.05.
5. **C5 (prompt unaffected):** v2's direction field is consumed by the prompt identically
   (no prompt change needed).

If C1-C5 hold → ship v2 to shadow mode.
If C1 fails → option is incorrect; revert to design.
If C2 fails → option is under-fixed; consider Option A combined with primary option.
If C3 fails → option is over-aggressive; investigate whether SHORT unlock is spuriously
flipping genuine bullish trades.
If C4 fails → option is over-aggressive; consider Option D with larger dead-zone.

---

## 7. Shadow deployment plan

The repo already has a pattern for shadow gates: `src/components/proximity_shadow_logger.py`
(file header documents promotion criteria; see lines 19-23). Follow the same pattern.

### 7.1 Deploy phase

1. Add `identify_structure_v2` to `src/components/market_state.py` (next to `identify_structure`; do NOT replace the existing function yet).
2. In `_build_timeframe_state` (`market_state.py:768-824`), invoke both v1 and v2 on the
   same swing list; attach the v2 result to the `TimeframeState` as a new optional
   `structure_v2` field (`src/models/market_state_models.py` update required). v1 continues
   to drive `detect_structure_breaks`, order blocks, and the downstream pipeline.
3. In `src/components/candidate_features_logger.py:509-511`, add three new logged fields
   per CANDIDATE: `mso_h1_structure_direction_v2`, `mso_m15_structure_direction_v2`,
   `mso_d1_structure_direction_v2`.
4. Add a new shadow logger `src/components/structure_divergence_shadow_logger.py`
   (mirrors `proximity_shadow_logger.py`'s pattern) that writes a JSONL row for every
   M15 candle close (not only CANDIDATEs):
   ```
   {timestamp, symbol, tf, v1_direction, v2_direction, v1_counts:{hh,hl,lh,ll}, v2_score, diverged:bool}
   ```
5. CEO approval gate: the v2 *shadow* deployment itself is still a `src/` change to a
   live system. Per CLAUDE.md WF-1 discipline, this requires CEO approval (log-only does
   not exempt from approval). The approval scope is "add shadow column + log v2 direction,
   no production behavior change" — narrower than the approval needed for the production cutover.

### 7.2 Observation phase (1-2 weeks)

1. Accumulate per-symbol-per-day divergence count. Expected divergence rate based on V1
   data: close to 99.8% on H1. The *interesting* metric is not "are they different" but
   "for each divergence, which is the correct answer?"
2. Produce divergence report via a small analysis script:
   ```
   python scripts/structure_v2_divergence_report.py --days 14
   ```
   Output: per-instrument-per-day divergence count, v2-label distribution, per-hour
   breakdown; cross-reference against `logs/*.log` for any anomalies.
3. For each divergence, sample (N=20 per instrument, stratified by TF) and verify by
   visual inspection (chart) or by analyst agent review: which label is correct? Record
   v2_correct/v1_correct/both_defensible/ambiguous counts.

### 7.3 Promotion criteria

Promote v2 to production (replacing v1) iff ALL hold:

**P1 (correctness):** v2 label is "correct" in ≥ 80% of sampled divergences; v1 is
correct in ≤ 20%.

**P2 (no catastrophic error):** v2 never produces a label on a plainly-trending window
that contradicts the trend (e.g., v2 says `bullish` during a 3σ downswing with no retrace).

**P3 (production behavior validation):** the shadow-replay backtest (§6.3) showed
expectancy preservation (C3) or improvement.

**P4 (redacted_account trial context):** if redacted_account trial (see CLAUDE.md §36) is still
open, CEO defers the cutover until the trial's close-out — or explicitly waives this
constraint.

**P5 (dev CEO window):** production cutover commit happens outside kill zones
(weekend or after NY close) per CLAUDE.md §MT5 preflight and the rolling-restart
procedure (Session 36 precedent, commit `bd1af27`).

If P1 fails: v2 is wrong; iterate on design, return to §6.
If P2 fails: v2 over-fitted a pathology; investigate and patch (likely Option F hybrid).
If P3 fails: v2 shifted the edge out of a profitable subset; careful — the 62%/65% WR
may not be edge-neutral under a different label distribution. Require Council review.
If P4 fails (redacted_account trial mid-window): hold.
If P5 fails (in-kill-zone attempt): re-schedule.

### 7.4 Rollback

v2 is reverted to shadow-only iff, post-promotion, any of the following occurs within
30 days:

- Monthly expectancy dips below +0.10R/trade on any live instrument.
- MaxDD exceeds 6% (vs the 8% H29 threshold).
- 5 consecutive SHORT losses on any single instrument (mirrors the emergency stop in
  CLAUDE.md §Emergency Stops).

### 7.5 Observability fields required

Per the ADR-004 SL-gate precedent (`004_sl_gate_reconciliation_2026-04-18.md:99-108`),
define the exact observability schema up-front so the promotion data is collectable:

```
{
  "timestamp_utc": "...",
  "symbol": "...",
  "tf": "H1|H4|D1|M15",
  "v1_direction": "bullish|bearish|transitional|insufficient_data",
  "v2_direction": "bullish|bearish|transitional|insufficient_data",
  "v1_counts": {"hh": int, "hl": int, "lh": int, "ll": int, "recent_pairs": int},
  "v2_score": float,
  "diverged": bool,
  "swing_count": int
}
```

---

## 8. Implications for CLAUDE.md validated numbers

Map each "validated number" to post-fix risk. Numbers below are quoted from CLAUDE.md §Validated Numbers.

| Number | Pre-fix value | Computed on | Post-fix risk | Re-verification needed? |
|---|---|---|---|---|
| XAUUSD WR vs breakeven | 62.0% (n=129) | Batch Oct 2025 – Mar 2026 | **Unknown.** Batch AI DID generate SHORT decisions (see §6.5) but MSO input was LONG-biased. The 129 LONG-winning trades' edge may or may not survive under fixed MSO — most likely YES for the LONG subset, unknown for newly-unlocked SHORT subset. | **YES** — re-run batch with v2. See §6.5. |
| Batch full-pop WR | 65% (n=367) | Batch Oct 2025 – Mar 2026 | Same as above. | **YES** — re-run batch. |
| 2026-only WR | 59.5% | Live + batch Jan-Apr 2026 | Same. | **YES.** |
| CANDIDATE rate (baseline) | 10.3% | Live + batch | **Post-fix likely HIGHER** — bearish setups that were previously absorbed into the NO_TRADE pool become CANDIDATEs. Magnitude unknown (depends on fraction of windows that flip to bearish under v2). | **YES** — measure from §6.3. |
| OB continuation | 70% rolling-50 | Bullish OBs, historical | Bullish-OB continuation rate likely unaffected (same supply of bullish OBs). Bearish-OB continuation is unknown because bearish OBs have never existed in the live OB population. The `scripts/ob_continuation_monitor.py` methodology (ADR-001 Approach A) computes continuation on historical CSV data via `src/components/market_state.py` primitives — so **if v2 changes structure labels in that replay, it changes the OB population feeding the monitor.** See §9 open question. | **YES** — re-run `ob_continuation_monitor.py` under v2 and compare rolling-50 rates per instrument, per OB direction. |
| MC P(pass FTMO) | 99.4% | LONG-only sample | **Unknown.** MC is parameterised on expectancy + variance; both may shift under v2. Must be re-derived after §6.4. | **YES** — re-MC with v2-derived expectancy + MaxDD. |
| US30 WR | 58.5% (n=41) | Batch | Same as XAUUSD (LONG-only). | **YES** — if batch re-run in §6.5 extends to non-XAUUSD. |
| USDJPY WR | 75.8% (n=33) | Batch | Same. | **YES.** |
| GBPJPY WR | 57.1% (n=42) | Batch; does NOT survive Bonferroni per CLAUDE.md | Same. | **YES.** |
| FVG-in-impulse signal | +7-20pp across 6 instruments | Cross-instrument mechanical backtest | **Probably unaffected.** FVG detection at `market_state.py::identify_fvgs` does not depend on `structure.direction` (verified via grep — FVG detection iterates over candles only, structure is not an input). | **NO** — can remain valid. (Quick grep confirmation prior to promotion.) |
| Expectancy | +0.200R/trade | Batch; does NOT survive Bonferroni | LONG-only sample → must be re-derived. | **YES.** |
| Session memory suppresses CR 55% | p=0.007 | Live (session-memory experiment, 2026-03) | The 55% figure is a CR-delta ratio under fixed MSO; v2 changes the MSO label distribution but not the memory-vs-no-memory relative comparison. **Probably unaffected directionally.** | **NO** — treated as robust until replication fails. |
| Opus vs Sonnet MSO gate (CR 38% vs 19%) | — | Live experiment | Same ratio logic as session memory; relative comparison, not absolute. | **NO.** |

**Summary:** ~10 of CLAUDE.md's headline numbers require re-derivation after v2 ships.
The estimated API + compute cost of re-derivation is the "mid tier" cost of §6.3 (~$162)
plus batch re-runs if needed. Numbers in the "confirmed but does not survive Bonferroni"
group are already flagged as weak evidence; their further weakening under v2 is a
relatively small practical cost.

**Critical hygiene note.** Until §6.5 re-derivation completes, CLAUDE.md's "Validated
Numbers" section should be marked as "**pre-v2 detector**" (or "under re-derivation" if
v2 shipped) to avoid stale confidence in downstream documents. This is a commit-time
doc hygiene task per CLAUDE.md §Verification Protocol item 7.

---

## 9. Open questions

### Q1. Does the batch dataset `knowledge_base_backtest/` include SHORT trades?

**Partial answer.** `knowledge_base_backtest/analysis/data_exploitation_20260405.md:210-219`
reports 29 direction-mismatch SHORT CANDIDATEs (23 XAUUSD, 6 GBPUSD) that were historically
generated but blocked at the `permissions.py:609-614` `direction_mismatch` gate. This means
the AI DID emit SHORT decisions against the (biased) MSO, and they have known entry/SL/TP
logs. These are potential counterfactuals for §6.5.

**Unanswered:** whether the batch's 367-trade population (n=367 per CLAUDE.md) includes
those 29 SHORTs or excludes them. A re-reading of the batch construction pipeline is
needed before re-validation.

**Action:** before re-running §6.5, run `python scripts/analyze_batch_composition.py`
(or equivalent ad-hoc grep) to confirm the SHORT vs LONG composition of n=367.

### Q2. Does T7 simulation go through `identify_structure`?

**Answer: YES, by construction.** `scripts/simulate_t7_live_period.py` calls
`compute_market_state` (same entry point as production), which calls
`_build_timeframe_state → identify_structure` for every TF per
`src/components/market_state.py:776`. Therefore:
- All T7 results to date (`research/t7_live_simulation/*.json`) inherit the bullish bias.
- All numbers derived from T7 (CANDIDATE rate, WR, expectancy) are LONG-only.
- The T7 harness is the correct replay environment for v2 validation.

### Q3. Are there other MSO-derived labels affected by the same saturating-threshold pattern?

Grep `min(3,` across `src/`:

```
C:\Users\MSI\Documents\ai-trading-agent\src\components\market_state.py:237
```

Single hit — `identify_structure` is the only function using this pattern in `src/`. No
other `min(3, ...)`-based thresholds exist. **Conclusion:** the bug is localised to
`identify_structure`; no sweep of related classifiers is needed. (Phase-2 review flagged
this independently at `zeta_review.md:41-46`.)

### Q4. Does the orchestrator `_compute_deterministic_bias` propagate the bias?

`src/components/orchestrator.py:1046-1093` (per A7 `report.md:234`) — deterministic bias
is computed from D1 + H4 structure directions. Because D1's 30-bar window rarely triggers
the saturation pathology (too few swings to hit `recent_pairs=3`), D1 direction is
`transitional` in 78% of XAUUSD D1 windows per A7 `report.md:86`. H4 is 94% bullish at
XAUUSD. Net deterministic bias: skewed bullish but not 100%. **The downstream bias is
attenuated from the 100% structural pathology by one degree.** Post-fix, deterministic
bias likely gets a more balanced distribution as H4 bearish becomes reachable.

### Q5. Pre-existing `direction_mismatch` safety gate

`permissions.py:609-614` enforces `direction == daily_bias` symmetrically. The gate is
well-formed — it rejects LONGs against bearish bias AND SHORTs against bullish bias. It
does NOT amplify the bullish-bias bug downstream; it is a symmetric safety gate that
faithfully applies whatever (biased or unbiased) `daily_bias` it receives. Not a source
of additional bias.

### Q6. What's the expected fraction of windows that flip to `bearish` under v2?

V1 did not run v2-counterfactual replays (the V1 scope was validation of the bug, not
fix design). Per the Phase-1 replay `zeta_market_state_prechecks.md` on NAS100:
- D1 rolling-60 windows correctly flip bullish↔bearish over time.
- H1 rolling-168 windows do not (saturation).

Naive estimate: under Option D with the proposed dead-zone, historical H1 bearish rate
should match the H4 bearish rate (H4 has less saturation and is a proxy for "windows
with legitimate bearish structure that escape the saturation"). From A7 `report.md:86`:
- XAUUSD H4 bearish rate: 5.7%.
- GBPUSD D1 bearish rate: 59.6%.

Plausible fleet-wide v2 H1 bearish rate: 5-30%, heavily instrument-dependent. **This is
an estimate, not a derivation.** Actual rate must come from §6.2.

### Q7. How does v2 interact with the CLAUDE.md "protected_swing" logic?

`identify_structure` also returns `protected_swing` (lines 241, 244), which feeds into
`detect_structure_breaks` CHoCH detection at `market_state.py:354`. Under v2, many currently-bullish-labeled windows flip to `transitional`, where `protected_swing = None`. This
means CHoCH events cannot fire on those windows — a potentially significant change in OB
and BOS supply that ripples through `identify_order_blocks` and beyond.

**Must verify** in §6.2 that v2 does not reduce the OB supply to the point where the
system has no retest candidates. The `pre_ai_gates.py` H1 POI availability gate
(`shadow_logs/candidate_features_log.jsonl` already logs the `h1_poi_exists` field)
provides a direct measurement.

### Q8. Do validated numbers that come from mechanical-only studies stay valid?

OB continuation 70% baseline (CLAUDE.md §Edge Mechanism) came from Test A rerun
(n=219 BOS events, `scripts/ob_retest_comprehensive.py`). That script uses the same
`identify_structure` as production. So the baseline was computed on a biased-label sample
and must be re-verified. **"Test A rerun" and "FVG-in-impulse" are the two non-AI mechanical studies most likely affected.** Re-run against v2 is free (no API cost).

---

## 10. Decision (CEO to fill)

> [Template — leave blank until CEO fills in.]
>
> **Date decided:** __________
>
> **Option chosen:** [ ] A [ ] B [ ] C [ ] D [ ] E [ ] F [ ] G [ ] H [ ] Other: ____________
>
> **Dead-zone / threshold value (if applicable):** __________
>
> **Shadow-deployment duration:** __________ weeks
>
> **Minimum backtest tier per §6.3:** [ ] Minimum (~$54) [ ] Mid (~$162) [ ] Full (~$270) [ ] Other: ____________
>
> **Validated-number re-derivation scope:** [ ] All 10 [ ] XAUUSD only [ ] Other: ____________
>
> **Production cutover condition:** [ ] All §7.3 promotion criteria [ ] Modified: ____________
>
> **Rationale / notes:**
> ___________________________________________________________________________
> ___________________________________________________________________________
>
> **Signed:** CEO Borhen, __________.

---

## 11. Links

- `research/directional_concentration_audit_2026-04-24/V1_INDEPENDENT_VALIDATION.md` — V1 report.
- `research/directional_concentration_audit_2026-04-24/report.md` — A7 audit.
- `research/directional_concentration_audit_2026-04-24/V1_SUMMARY.md` — V1 one-page.
- `research/b_deep_audit_2026-04-19/phase1/zeta_market_state_prechecks.md` — Phase-1 leak claim.
- `research/b_deep_audit_2026-04-19/phase2/zeta_review.md` — Phase-2 review (same mechanism, different framing).
- `src/components/market_state.py:216-257` — `identify_structure` (target of fix).
- `src/components/market_state.py:776` — `_build_timeframe_state` call site.
- `src/components/candidate_features_logger.py:509-511` — shadow-log entry points.
- `scripts/simulate_t7_live_period.py` — T7 replay harness.
- `.context/06_decisions/004_sl_gate_reconciliation_2026-04-18.md` — closest ADR format precedent.
- `knowledge_base/pipeline_state/02_market_state.json` — live snapshot (bug demonstration, 2026-04-23T17:00:05).
- CLAUDE.md §Validated Numbers — definitions of numbers at risk (§8 of this ADR).

---

*This ADR is part of the GTOS architecture decision log at `.context/06_decisions/`.
Pre-approval-gate ADRs follow the same structure as `004_sl_gate_reconciliation_2026-04-18.md`:
status updates are appended as signed closure notes when the CEO acts.*
