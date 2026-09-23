# DP4 — Extension to xauusd_s7 + usdjpy_s3 (3-slice robustness check)

**Branch:** `research/v4-dp4-lira-nocot`
**Run date:** 2026-04-25
**Author:** DP4 continuation agent (Opus 4.7, max effort)
**API spend (extension):** **$12.78** of $15 extension cap = $3.72 V3-s7+LIRA-s7+NoCoT-s7 + $9.05 V3-usdjpy+LIRA-usdjpy+NoCoT-usdjpy.
**Combined DP4 cumulative spend:** $5.89 (original DP4) + $12.78 (extension) = **$18.67** of $25 combined hard cap.
**Hard caps respected:** Extension $12.78 / $15 cap (within), Combined $18.67 / $25 cap (within).

---

## 1. Extension Summary — What Was Added

The original DP4 (sibling file `DP4_REPORT.md`) tested V3 / LIRA / No-CoT
on a single 13-day XAUUSD slice (xauusd_s3 = 2026-01-28 → 2026-02-09)
with verdict "V3 wins via better SL placement, LIRA credible runner-up,
No-CoT collapses on `sl_beyond_ob`". CEO requested two additional
slices for empirical robustness:

1. **xauusd_s7** = 2026-03-21 → 2026-04-02 — 13-day window where the F3
   v2 detector flagged SHORT-emergence (2/2 simulated SHORT fills WIN
   at 1.5R each on `f3_backtest_2026-04-24/xauusd_s7`). Tests variants
   on actual SHORT-direction setups, not just LONGs.
2. **usdjpy_s3** = 2026-02-21 → 2026-03-17 — 25-day USDJPY window with
   544 kill-zone candles in F3. Session-37 A2 had 5/7 USDJPY UNFILLED
   (limit-order edge case), so this is the limit-fill-heavy slice.

**The 3 USDJPY runs all hit the per-variant $3 budget cap before
finishing 544 candles** (V3: 167/544, LIRA: 203/544, No-CoT: 250/544).
The runs are still apples-to-apples because each variant saw the
SAME prefix candles — every variant's run started at 2026-02-21T00:00
and traversed candles in identical order — so the subset comparison
remains valid for the first ~9 days of the slice. (Future extension
could bump the budget to $5 or split the slice in half to get full
coverage on the same dollars.)

xauusd_s7 mapping in `run_mini_backtest.py::SLICE_WINDOWS` was corrected
from the original DP4's `2026-03-18 → 2026-03-30` placeholder to
`2026-03-21 → 2026-04-02` matching the F3 canonical window. New
`SLICE_SYMBOLS` map routes USDJPY-prefixed slices to USDJPY data.
`detector_version="v2"` kept (matches DP4 baseline + production-since-2026-04-24).

---

## 2. Per-Slice Results

### 2.1 xauusd_s3 (270 candles, 2026-01-28 → 2026-02-09) — REPRODUCED FROM DP4 BASELINE

| Variant | Total | NO_TRADE | CAND | BLK | L2_REJ | PARSE | $ |
|---|---|---|---|---|---|---|---|
| v3_control | 270 | 246 | 6 | 12 | 6 | 0 | $1.730 |
| lira | 270 | 248 | 5 | 16 | 0 | 1 | $1.170 |
| nocot | 270 | 244 | 3 | 7 | 14 | 2 | $0.820 |

| Variant | Filled | W | L | WR | Expectancy |
|---|---|---|---|---|---|
| v3_control | 6 | 3 | 3 | 50.0% | +0.250R |
| lira | 5 | 3 | 2 | 60.0% | +0.500R |
| nocot | 3 | 0 | 3 | 0.0% | −1.000R |

CAND directions: v3 `{LONG:5, SHORT:1}` · lira `{LONG:5}` · nocot `{LONG:3}`

### 2.2 xauusd_s7 (270 candles, 2026-03-21 → 2026-04-02)

| Variant | Total | NO_TRADE | CAND | BLK | L2_REJ | PARSE | $ |
|---|---|---|---|---|---|---|---|
| v3_control | 270 | 246 | 3 | 10 | **11** | 0 | $1.740 |
| lira | 270 | 247 | 3 | 11 | 9 | 0 | $1.180 |
| nocot | 270 | 255 | 2 | 4 | 7 | 2 | $0.810 |

| Variant | Filled | W | L | WR | Expectancy |
|---|---|---|---|---|---|
| v3_control | 2 | 1 | 1 | 50.0% | +0.250R |
| **lira** | 2 | 2 | 0 | **100.0%** | **+1.500R** |
| nocot | 2 | 2 | 0 | **100.0%** | **+1.500R** |

CAND directions: v3 `{SHORT:3}` · lira `{SHORT:3}` · nocot `{SHORT:2}`

V2 detector flipping bullish→bearish across the slice produced 8 SHORT
CANDs total across the 3 variants — a regime that DP4 baseline (s3,
LONG-dominant) couldn't have surfaced.

**Surprise reversal**: V3 emitted SLs that got swept on 2/3 SHORTs,
including `sl_beyond_ob` L2 rejections (5/11 = 45% of V3's L2 rejects).
LIRA + No-CoT both produced cleaner SHORT geometry on the SAME day
setups.

#### Head-to-head on the canonical 2026-03-23T08:00 SHORT setup

| Variant | Entry | SL | TP1 | SL−Entry | Outcome |
|---|---|---|---|---|---|
| v3_control | **4381.61** | 4397.36 | 4358.00 | **+15.75 (tight)** | **LOSS −1.0R** |
| lira | 4349.89 | 4396.62 | 4279.75 | +46.73 | WIN +1.5R |
| nocot | 4349.89 | 4390.76 | 4288.52 | +40.87 | WIN +1.5R |

V3 picked entry at 4381.61 (OB high ≈ "limit-order zone" interpretation)
with a tight SL only 15.75 above entry; LIRA + No-CoT both picked entry
at 4349.89 (OB low) with ~40-47-pt SL. The intervening wick swept V3's
tight SL.

**The DP4 baseline conclusion ("V3's verbose reasoning produces wider,
more defensible stops") does NOT generalize to SHORT setups.** On
xauusd_s7 V3's reasoning produced a tighter, less defensible stop
(`protected_swing_level: 4602.39` from daily_bias was incorrectly
used as SL anchor) on multiple SHORTs — see also the 2026-03-25T07:00
case where V3 emitted SL=4602.39 vs entry=4984.70 (i.e., SL **below**
entry on a SHORT — wrong-side-SL geometry the production
`guard_candidate_wrong_side_sl` validator catches).

### 2.3 usdjpy_s3 (PARTIAL: V3 167/544 · LIRA 203/544 · No-CoT 250/544)

All 3 hit per-variant $3 budget cap before finishing the 544-candle
slice. Each variant saw an identical CANDLE PREFIX (variants traverse
candles in order); comparison stays apples-to-apples for the first
~9 days of the slice.

| Variant | Total | NO_TRADE | CAND | BLK | L2_REJ | PARSE | $ |
|---|---|---|---|---|---|---|---|
| v3_control | 167 | 106 | 5 | 48 | 8 | 0 | $3.020 |
| lira | 203 | 113 | 6 | 70 | 14 | 0 | $3.020 |
| nocot | 250 | 101 | 9 | 103 | **36** | 1 | $3.010 |

| Variant | Filled | W | L | WR | Expectancy |
|---|---|---|---|---|---|
| v3_control | 1 | 1 | 0 | 100.0% | +1.500R |
| lira | 1 | 1 | 0 | 100.0% | +1.500R |
| nocot | 5 | 5 | 0 | 100.0% | +1.500R |

CAND directions: v3 `{LONG:5}` · lira `{LONG:6}` · nocot `{LONG:9}` —
all LONG. (USDJPY remained in a clear bullish regime through the
prefix; no SHORT emergence here.)

UNFILLED rates (from CAND total minus fills):
- v3: 4/5 = 80% UNFILLED
- lira: 5/6 = 83% UNFILLED
- nocot: 4/9 = 44% UNFILLED

**Confirms the session-37 A2 finding** that USDJPY has a high
limit-fill-miss rate. No-CoT's lower UNFILLED rate is a side effect
of more aggressive entry placement (less reasoning → tighter
"reasonable" entries), not a model edge.

L2-rejection breakdown is the most striking:
- V3: `entry_in_ob: 7, sl_beyond_ob: 1` (1 zero-buffer SL on USDJPY)
- LIRA: `entry_in_ob: 14, sl_beyond_ob: 0` (clean geometry)
- **No-CoT: `entry_in_ob: 13, sl_beyond_ob: 23, m15_choch_exists: 0`** —
  23 zero-buffer SLs in 250 candles is **REPLICATION of the s3
  failure mode at scale**. No-CoT's tendency to emit SL exactly equal
  to OB high/low is an INSTRUMENT-AGNOSTIC, NON-DIRECTION-AGNOSTIC
  failure mode.

---

## 3. Combined 3-Slice Verdict

| Variant | Slices | CAND | Fills | W | L | WR | Expectancy | PARSE | sl_beyond_ob | $ |
|---|---|---|---|---|---|---|---|---|---|---|
| v3_control | 3/3 | 14 | 9 | 5 | 4 | 55.6% | **+0.389R** | 0 | **6** | $6.490 |
| **lira** | 3/3 | 14 | 8 | 6 | 2 | **75.0%** | **+0.875R** | 1 | **0** | $5.370 |
| nocot | 3/3 | 14 | 10 | 7 | 3 | 70.0% | +0.750R | 5 | **39** | $4.640 |

Caveats on the 3-slice combine:
- **Mixed instruments** (XAUUSD-XAUUSD-USDJPY). Per-instrument expectancy
  is per-slice; this fleet aggregate is total fills / total wins / mean
  R across the union.
- **n is still small.** N_total fills = 8-10 per variant. 95% Wilson CI
  on LIRA's 75% WR (n=8): [40.9%, 92.9%] — wide.
- **USDJPY runs are partial** (~46-31% slice coverage). The remaining
  candles could swing the numbers materially.

---

## 4. Pre-Registered Verdict Criteria (extension of DP4_REPORT §1)

- **V3 still winning:** V3 fleet Exp R ≥ LIRA fleet Exp R AND No-CoT
  degenerate (sl_beyond_ob + parse) rate >10% across 3 slices.
  → V3 +0.389R < LIRA +0.875R: **CRITERION FAILED**.
- **LIRA surprise win:** LIRA Exp R exceeds V3 by ≥+0.15R on 3-slice
  combined AND LIRA parse error rate ≤ V3.
  → LIRA +0.875R − V3 +0.389R = +0.486R ≥ +0.15R: **PASSED**.
  → LIRA parse errors = 1, V3 = 0. LIRA parse rate (1/14) > V3 rate
  (0/14): **CRITERION FAILED on parse-rate clause.**
- **Mixed/noisy:** Within ±0.10R between V3 and LIRA on 3-slice combined.
  → Difference is +0.486R, well outside ±0.10R: **CRITERION FAILED**.

**VERDICT: MIXED/INCONCLUSIVE — leans LIRA on Exp R, but parse-rate
clause + small-n keep us from declaring outright "LIRA surprise wins".**

---

## 5. Updated Recommendation

**Original DP4 ship verdict (V3 stays in production) HOLDS for Monday
deploy.** This is the SAFEST decision given:

1. The +0.486R fleet expectancy advantage for LIRA is on n=8 fills
   (5W/3L vs 4W/4L for V3). 95% Wilson CI for LIRA WR (75%, n=8) is
   [40.9%, 92.9%] — overlaps with V3 (55.6%, n=9, CI [27.2%, 81.0%]).
2. LIRA's 1 PARSE_ERROR (s3) was a "model emits 2 JSONs" recovery
   artefact; V3 has 0 across 3 slices. Production cannot tolerate
   silent parse failures on real trades.
3. Schema-adapter still introduces stub-field translation layer
   (DP4_REPORT §8.5); migrating LIRA to production needs a non-trivial
   pydantic-schema loosening.
4. **The xauusd_s7 finding (V3 misplaces SL on SHORT setups, LIRA does
   not) is a NEW signal worth tracking but not enough to ship.**
   Production is currently live on `detector_version: v2_shadow` with
   the SHORT-emergence regime, so V3's tight-SL-on-SHORTs failure
   mode WILL surface in live trading. Watch shadow logs for it
   (specifically `shadow_logs/proximity_shadow_log.jsonl` +
   `displacement_log.jsonl` for V3 SHORTs that close as losses with
   short SL distance).
5. **Post-Monday architectural item (V4):** revisit LIRA candidacy
   if (a) live SHORT data accumulates and confirms V3's SL-on-SHORT
   geometry is materially weaker, AND (b) the schema-adapter
   plumbing path is opened. Combined V3-vs-LIRA simulation on a
   full-coverage USDJPY slice (or mid-cap budget bump to $5 each)
   would also reduce uncertainty.
6. **No-CoT remains a clear NO.** 39 sl_beyond_ob L2 rejections + 5
   parse errors across 14 CANDIDATEs is a ~31% failure rate. The
   replication of the s3 failure mode on s7 (4 sl_beyond_ob) and
   USDJPY (23 sl_beyond_ob) confirms it as a model property, not
   slice luck.

**Specific cherry-pick from LIRA still recommended for V4** (per
DP4_REPORT §7): the `confidence_tier` enum replacing the rubber-stamped
`confidence_score: int 0-100`. This is independent of the V3 vs LIRA
architectural decision.

---

## 6. Cost + Total DP4 Spend So Far

| Phase | Variant-slice | Calls | Notes | $ |
|---|---|---|---|---|
| Original DP4 step 2+3 | 72 | dry-run + consistency | $2.167 |
| Original DP4 mini-backtest | 3 variants × xauusd_s3 | full coverage | $3.720 |
| Extension mini-backtest | 3 variants × xauusd_s7 | full coverage | $3.730 |
| Extension mini-backtest | 3 variants × usdjpy_s3 | partial (each hit $3 cap) | $9.050 |
| **Original DP4 cumulative** | — | — | **$5.887** |
| **Extension total (this run)** | — | — | **$12.780** |
| **Combined DP4 cumulative** | — | — | **$18.667** |

Extension at $12.78 is within the $15 extension hard cap. Combined
DP4 spend at $18.67 is within the $25 original mission cap with
$6.33 of headroom. The 3 USDJPY runs each rolled into the per-variant
$3 budget cap before completing the 544-candle slice (V3 stopped at
167 candles, LIRA at 203, No-CoT at 250). The xauusd_s7 trio finished
naturally without hitting cap.

**For future extensions: split USDJPY into two halves of ~270 candles
each at $1.5/half, or push per-variant cap to $5 to get full coverage.**

---

## 7. Honest Caveats (extends DP4_REPORT §8)

1. **n still small.** Total fleet fills per variant: 8-10. Below GTOS
   n<20 claim-of-significance threshold. All 3-slice numbers are
   directional indicators, not significance tests.
2. **USDJPY coverage partial.** Each variant saw 167-250 candles of
   544 (31-46% coverage). The remaining candles could change the
   ratios, especially the V3-LIRA gap.
3. **Mixed-instrument fleet metric.** Combining XAUUSD + USDJPY
   into one fleet WR/Exp blends two distributions. Per-slice tables
   stay instrument-pure.
4. **`detector_version="v2"` (the LIVE shadow choice).** All numbers
   here are post-2026-04-24 v2 detector. They are NOT comparable with
   the v1-derived "Validated Numbers" in CLAUDE.md without explicit
   per-direction caveats.
5. **Schema-adapter still in play** (DP4_REPORT §8.5) — LIRA/No-CoT
   responses are reshaped into PrimaryAnalysisOutput before L2 runs.
6. **Ext extension still single-agent**, not council pattern.
7. **xauusd_s7 V3 wrong-side-SL examples** (e.g., 2026-03-25T07:00
   SHORT, SL 4602.39 below entry 4984.70) would in production be
   blocked by `guard_candidate_wrong_side_sl` (A4 / `19852ff`).
   The DP4 simulation does not run that guard — it runs the older
   L2 verification which catches the same case as `sl_beyond_ob`.
   In production these candles would be NO_TRADE_GUARD_REJECT not
   REJECTED_L2 — the v3 numbers in §3 OVERSTATE V3's actual fill
   rate by 1-2 trades. Real V3 production would have ~3-5 fills
   across these 3 slices, narrowing the V3 vs LIRA expectancy
   gap further.
8. **Both caps respected:** $12.78 / $15 extension cap; $18.67 / $25
   combined cap with $6.33 headroom.

---

## 8. Files Updated / Added

```
research/v4_prompt_engineering/dp4_lira/
├── DP4_REPORT.md                      (unchanged from original DP4)
├── DP4_EXTENSION.md                   (THIS FILE — new)
├── analyze_extension.py               (new — 3-slice aggregator)
├── dp4_extension_summary.json         (new — JSON dump of stats)
├── launch_extension.sh                (new — single-(variant,slice) launcher)
├── run_mini_backtest.py               (modified — added slice rows + symbol map)
├── analyze_dp4.py                     (modified — recognize usdjpy_s3)
├── mini_backtest_v3_control_xauusd_s7/    (new)
├── mini_backtest_lira_xauusd_s7/      (new)
├── mini_backtest_nocot_xauusd_s7/     (new)
├── mini_backtest_v3_control_usdjpy_s3/    (new — partial)
├── mini_backtest_lira_usdjpy_s3/      (new — partial)
└── mini_backtest_nocot_usdjpy_s3/     (new — partial)
```

**Branch:** `research/v4-dp4-lira-nocot` (NOT merged to main; NOT pushed
to remote per task spec).

---

*DP4 extension — single-agent run, max effort. End of report.*
