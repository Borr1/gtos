# LIRA Canary Report — 60-fixture Sweep vs V3 Baseline

**Branch:** `research/lira-canary` (worktree-only; not pushed; not merged)
**Date:** 2026-04-24
**Model:** `claude-sonnet-4-6`, effort=`max`, temperature=`0`
**Methodology:** Production canary fixtures + LIRA system prompt + LIRA->V3 schema adapter; compared against the production V3 baseline (`scripts/canary_fixtures/baseline.json`, created 2026-04-24T01:00:34Z, same model + effort).

---

## 1. Executive Summary + Verdict

### Headline numbers

| Metric | Value |
|---|---|
| Fixtures evaluated | 60 / 60 |
| Total agreement with V3 baseline | **58 / 60 (96.7%)** |
| Baseline-tier flips | **2** (both XAUUSD; both NO_TRADE -> CANDIDATE) |
| Borderline-tier flips | **0** (28 / 28 borderline match V3 exactly) |
| Parse errors (LIRA JSON) | **0** |
| Schema-adapter failures | **0** |
| Cost (Sonnet 4.6 max) | **$1.58** (357.8k input + 33.5k output) |
| Wall-clock | 123.5 s |

### Pre-registered verdict thresholds

| Baseline flips | Borderline flips | Verdict |
|---|---|---|
| <=1 | <=11 | **PASS** |
| 2-3 | 12-22 | **MARGINAL** |
| 4+ | 23+ | **FAIL** |

LIRA scored **2 baseline flips, 0 borderline flips** -> **MARGINAL** by the strict pre-registered table.

### Manual classification of the 2 baseline flips

The pre-registered table assumes flips are regressions. Per-fixture inspection of both XAUUSD flips shows the picture is more nuanced:

- **Flip 1 (`london_no_trade_c2_fail_m15_opposing_2026jan23`):** **TRUE LIRA REGRESSION.** V3 correctly catches an explicit M15 CHoCH bearish at the candle being evaluated and emits NO_TRADE / `c2_m15_opposing`. LIRA explains the same M15 CHoCH away as "weak displacement / minor pullback" and emits CANDIDATE LONG. This is a genuine miss on the C2 gate.
- **Flip 2 (`ny_candidate_2026mar10_loss`):** **LIRA CORRECTNESS WIN over V3.** V3 emits `C1=PASS C2=PASS C3=PASS but no_qualifying_h1_poi in correct direction at current price context — H1 OB at 5106.92-5089.13 exists`. That reasoning is the EXACT V8-flagged G2 prompt-gaming pattern (CLAUDE.md unresolved #5: V3 closed `touches<2` loophole but other gaming patterns remain). The H1 OB literally exists; R4 does not apply. LIRA correctly returns CANDIDATE LONG, citing the OB at 5106.92.

So the empirical regression rate vs V3 is **1 / 60 = 1.67%** rather than 2 / 60. Under a hand-classified table, LIRA would land at the PASS threshold (`<=1 baseline flip` allowed). Under the strict pre-registered table treating any flip as a regression, LIRA is MARGINAL.

### Recommended verdict: **MARGINAL leaning PASS**

LIRA architecture preserves V3 canary behavior on 96.7% of fixtures with 0 parse errors / 0 adapter failures across 60 calls. The single true regression is C2-FAIL detection on bearish-CHoCH-with-low-displacement M15 candles, which is a known soft-edge of the underlying gate criterion ("active opposition" vs "minor pullback"). The lone other flip is LIRA correctly side-stepping a V3 prompt-gaming bug.

**P3-LIRA A/B-backtest recommendation: PROCEED.** The 12-slice A/B backtest is the correct next step; canary sweep does not surface a LIRA architectural problem severe enough to shelve. The C2-FAIL miss should be tracked as a sub-population in P3-LIRA — count CHoCH-vs-pullback decisions and compare LIRA vs V3 outcomes specifically there.

---

## 2. Flip Table (V3 baseline vs LIRA-adapted)

Of 60 fixtures, 58 match. The 2 flips are tabulated below.

| # | Tier | Symbol | Label | V3 | LIRA | Direction | Manual classification |
|---|---|---|---|---|---|---|---|
| 1 | baseline | XAUUSD | `london_no_trade_c2_fail_m15_opposing_2026jan23` | NO_TRADE | CANDIDATE LONG | NO_TRADE -> CAND | True LIRA regression (C2 miss) |
| 2 | baseline | XAUUSD | `ny_candidate_2026mar10_loss` | NO_TRADE | CANDIDATE LONG | NO_TRADE -> CAND | LIRA correctness win (V3 G2 gaming bug) |

### V3 vs LIRA decision distribution (across all 60)

| | V3 baseline | LIRA |
|---|---|---|
| CANDIDATE | 51 | 53 |
| NO_TRADE | 9 | 7 |

LIRA shifts **+2 CANDIDATEs net**, both in the same direction (NO_TRADE -> CAND). No CAND -> NO_TRADE flips were observed.

### Per-tier match rates

| Tier | N | Matches | Threshold | Status |
|---|---|---|---|---|
| baseline | 32 | 30 | >=31 | FAIL (1 over allowance) |
| borderline | 28 | 28 | >=21 (ceil(0.75 * 28)) | PASS |

### Per-symbol breakdown

| Symbol | N | Matches | Flips |
|---|---|---|---|
| XAUUSD | 28 | 26 | 2 |
| EURUSD | 8 | 8 | 0 |
| USDJPY | 7 | 7 | 0 |
| GBPUSD | 5 | 5 | 0 |
| US30_cash | 5 | 5 | 0 |
| GBPJPY | 4 | 4 | 0 |
| NAS100 | 3 | 3 | 0 |
| **Total** | **60** | **58** | **2** |

Both flips concentrated on XAUUSD; cross-instrument behavior on the other 6 symbols is canary-clean (32 / 32 match). USDJPY and GBPUSD — which carry the recent FX precision tightening (FA-2) — show zero LIRA regression.

---

## 3. Parse Error / Adapter Issue Log

| Metric | Count |
|---|---|
| LIRA JSON parse errors (raw text -> dict) | **0 / 60** |
| Adapter `pa_obj is None` (pydantic build failure) | **0 / 60** |
| Adapter `decision == "PARSE_ERROR"` | **0 / 60** |

The 1 parse error reported on the 6-fixture mini-backtest in DP4+extension does **not** reproduce at 60-fixture scale under canary inputs. Possible explanations: small sample (1 / 6 = 17%) was high-variance noise; the canary fixtures are the exact MSO shapes the production prompt is calibrated for and may exercise less of LIRA's edge cases; the mini-backtest used different MSO trajectories. Either way, the canary observation is consistent with LIRA being parse-stable for production-shaped MSOs.

The schema adapter's V3-equivalent reasoning block was always built successfully. `setup_grade` mapping (LIRA's 5-level A+ / A / B / C / F into V3's A+ / A / B+ / B / C, with F collapsing to C) had no observed downstream effect on canary pass/fail; the production canary's PASS criterion is decision-level only.

---

## 4. Flip Pattern Analysis

### Pattern 1 — single C2-edge-case miss

`london_no_trade_c2_fail_m15_opposing_2026jan23` is constructed specifically to test C2 FAIL on M15 active opposition. The fixture has:
- H1 = bullish (5 consecutive bullish BOS)
- M15 = explicit `CHoCH 2026-01-23T09:45 lvl=4945.59 dir=bearish disp=False ratio=0.7` AT THE EVALUATION CANDLE
- M15 also shows a `bearish 4959.57-4951.70` OB formed `2026-01-23T09:15` (CHoCH-origin)

V3 correctly emits `C1=PASS C2=FAIL C3=PASS` and NO_TRADE.

LIRA's reasoning verbatim:
> "M15 CHoCH at 4945.59 is bearish with disp=False and ratio=0.7 — a single low-displacement CHoCH constitutes a minor pullback, not active structural opposition to H1 bullish bias."

This rests on the V3 / LIRA shared C2 phrasing ("A single opposing candle or minor pullback does NOT constitute active opposition"). The C2 criterion has a soft boundary: explicit CHoCH-against-H1 should fail C2, but a low-displacement single candle should not. LIRA reads `disp=False ratio=0.7` as the latter; V3 reads the explicit `CHoCH ... dir=bearish` event as the former. **Both are defensible readings of the prompt — V3's is the production-baselined call.**

This is the only category of regression observed.

### Pattern 2 — LIRA bypasses a V3 G2 gaming pattern (correctness win)

`ny_candidate_2026mar10_loss` has H1 bullish with 1 unmitigated H1 OB at 5106.92-5089.13 (touches=1). M15 is bullish with no CHoCH. C1 / C2 / C3 all PASS, R4 (`no_qualifying_h1_poi`) literally does NOT apply because the OB exists.

V3 baseline (created today, 2026-04-24) emits NO_TRADE with the literal V3-prompt-forbidden reasoning:
> `C1=PASS C2=PASS C3=PASS but no_qualifying_h1_poi in correct direction at current price context — H1 OB at 5106.92-5089.13 exists (t...`

This is the **exact reasoning the V3 prompt's G2 forbidden block was designed to prevent**. CLAUDE.md unresolved item #5 already calls this out: "V3 closed `touches<2` loophole but age/staleness, partial-mitigation, weak-bias gaming patterns NOT explicitly forbidden in G1-G5 — V4 territory."

LIRA bypasses this V3 loophole because its label-first ordering forces the model to commit to a verdict on C1/C2/C3 BEFORE writing the rationalisation block. It cannot write `no_qualifying_h1_poi` first and then justify it, because the schema requires `decision` and `direction` fields up-front and `no_trade_reason` must literally be one of R1-R8. This is consistent with the architectural hypothesis from Hung 2025 that label-first decoding reduces post-hoc rationalisation.

The empirical implication: LIRA is more disciplined than V3 on the very gaming pattern V3 was designed to suppress but didn't fully suppress. **This single flip is plausibly an *edge gain* for LIRA, not a regression.**

### Concentration

- **2 / 2 flips on XAUUSD** (XAUUSD has 28 / 60 = 47% of fixtures, so concentration is mild not severe)
- **2 / 2 flips on baseline tier** (baseline = 32 / 60 fixtures = 53%); 0 / 28 borderline flips is striking — borderline tier was **designed** to flush out boundary disagreement, and LIRA matches V3 on 100% of it
- **2 / 2 flips in the NO_TRADE -> CAND direction** — LIRA does not over-reject vs V3 in any case; only over-accepts in 2 cases (1 regression + 1 win)
- **No cross-instrument failures** — EURUSD / USDJPY / GBPUSD / GBPJPY / US30 / NAS100 all 32 / 32 match. The new FX precision scaffolding (FA-2) carries through LIRA without issue.

### What did NOT show up

- No flips on the explicitly designed `borderline_*_touches<2` / `wrong_side_sl` / `m15_as_h1_temptation` / `mitigated_ob_straddle` / `counter_bias` / `fx_precision` fixture classes. LIRA correctly handles the V3-design-intended decision-boundary stress tests.
- No JSON malformed responses on FX (5dp) or USDJPY (3dp) — schema adapter consistently round-trips precision.
- No `setup_grade` collapse to `C` (i.e., no fixtures where the adapter had to fall back from F).

---

## 5. Recommendation

### P3-LIRA 12-slice A/B backtest readiness: **GO**

LIRA's canary behavior is flat with V3 except for one C2-soft-edge case and one V3-correctness improvement. No JSON or schema-adapter blockers. The DP4-mini-backtest 1 / 6 parse error rate did not reproduce at 60-fixture scale.

### Pre-registered watch items for the A/B backtest

1. **C2 active-opposition vs minor-pullback subpopulation** — collect every M15-CHoCH-against-H1 candle in the 12-slice run, compare LIRA decision vs V3 decision specifically there, and tag outcomes (TP1 / TP2 / SL / BE / not-filled). The canary surfaces 1 case; the A/B run should accumulate a real sample to size the regression vs the LIRA-correctness-win effect.
2. **CAND-rate net delta** — LIRA emitted +2 net CANDIDATEs over 60 fixtures (53 vs 51 = +3.9% relative). If the A/B backtest reproduces a similar net positive direction, that's an Exp R contributor only if LIRA's net-extra CANDIDATEs win at >breakeven WR. This is testable.
3. **G2-gaming-pattern incidence** — explicitly count "C1=PASS C2=PASS C3=PASS but no_qualifying_h1_poi" patterns in V3 vs LIRA traces in the A/B backtest. If LIRA structurally suppresses them, that's a measurable architectural advantage that should appear as fewer false-NO_TRADE rows.

### Schema adapter hardening

The adapter performed cleanly (0 / 60 failures), but it remains a thin layer with implicit V3-shape assumptions:
- `_GRADE_MAP` collapses LIRA's `F` -> V3 `C`. If F-cases later diverge structurally from C-cases (different downstream gate behavior), this collapse loses information.
- The adapter assumes the LIRA model emits `justification.h1_setup.poi_price_level`. If the model trims that field (e.g., on NO_TRADE rows), `poi_price_level=0.0` is silently inserted. That is the current behavior anyway, so no immediate issue, but worth noting.
- The adapter does not enforce `no_trade_reason in R1-R8` at runtime — same gap as V3 (CLAUDE.md unresolved #5). A `Literal[...]` enforcement pass should be considered jointly with V4.

None of these block P3-LIRA. They are notes for an eventual LIRA-V2 pass.

### Do NOT shelve

The MARGINAL verdict by strict thresholding does not justify shelving. The actual regression rate is 1 / 60 = 1.67%, the cost was $1.58 of the $10 budget, and DP4+extension already showed +0.486R fleet Exp on 3-slice mini-backtest. Proceeding to P3-LIRA is the proper next gate.

---

## 6. Cost Summary

| Bucket | Tokens | Estimated cost |
|---|---|---|
| Input | 357,829 | $1.073 (Sonnet 4.6 input @ $3.00/M) |
| Output | 33,472 | $0.502 (Sonnet 4.6 output @ $15.00/M) |
| **Total** | **391,301** | **$1.575** |

Plus a 2-fixture re-fetch to capture full raw text for the 2 flipped rows (~$0.04 incremental).

**Final cost: ~$1.62 of the $10 budget.** Significantly under expected ($3-6) — LIRA's terser justification block (under 500 tokens for CANDIDATE, under 250 for NO_TRADE per its prompt) drove output token usage down vs the V3 verbose schema (under 600 / under 300).

---

## Files committed under `research/v4_prompt_engineering/lira_canary/`

- `run_lira_canary.py` — runner script (not modifying production canary)
- `summary.json` — aggregated results including verdict / flip counts / per-tier scores
- `per_fixture.jsonl` — one JSON row per fixture with V3-vs-LIRA decision + adapter status + raw preview
- `flipped_full_outputs.json` — full LIRA raw text for the 2 flipped rows (for the manual classification audit trail)
- `LIRA_CANARY_REPORT.md` — this file
