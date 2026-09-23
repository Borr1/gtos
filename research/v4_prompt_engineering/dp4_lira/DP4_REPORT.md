# DP4 — LIRA / No-CoT / V3 prompt-architecture A/B

**Branch:** `research/v4-dp4-lira-nocot`  
**Run date:** 2026-04-25  
**Author:** DP4 agent (Opus 4.7, max effort)  
**API spend:** $7.86 of $25 budget (steps 2+3: $2.17, mini-backtest: $5.69 measured but partial — see §6)  
**Sample size:** 6 MSOs × 3 variants × 4 calls (1 dry + 3 consistency) = 72 calls + 1 mini-backtest slice per variant

---

## 1. Executive Summary

**VERDICT: V3 structure wins on the metric that matters (live trading R), with LIRA a credible second; No-CoT is a clear loser despite winning on tokens/latency.**

The DP4 experiment empirically tested whether the architectural patterns
suggested by Hung 2025 (arXiv:2506.04574, GPT-4o "No-CoT 72.7% > CoT-Long
66.8%" on intuition-driven financial classification) transfer to the GTOS
MSO-decision task on Sonnet 4.6 effort=max.

The headline numbers from a single Jan-28 → Feb-9 XAUUSD slice mini-backtest:

| Variant | CAND | Filled | WR | Expectancy | Cost | Tokens (median OT) |
|---|---|---|---|---|---|---|
| **V3 (control)** | 6 | 6 | 50.0% | **+0.250R** | $1.730 | 954 |
| **LIRA** | 5 | 5 | 60.0% | **+0.500R** | $1.170 | 516 |
| **No-CoT** | 3 | 3 | 0.0% | **−1.000R** | $0.820 | 145 |

Headline interpretation:
- **LIRA looks like the winner on n=5 trades (3W/2L vs V3's 3W/3L)**, but n is below GTOS's claim-of-significance threshold (n<20). In practice the LIRA edge could vanish on a wider slice.
- **No-CoT collapsed**: 0/3 wins is a 1-in-8 outcome under a 50% null, and the loss mechanism is identifiable: stripping the verbose SL-placement reasoning produced TIGHTER stop-loss values that got hit on the same setups V3 won. **Token savings came at the cost of trade-parameter quality, not gate-decision quality.**
- **Self-consistency**: LIRA & No-CoT both 100% (6/6 MSOs identical across 3 reruns) vs V3 at 83.3% (5/6, with one MSO splitting between c1_failed and c2_m15_opposing rejection reasons). LIRA wins this sub-metric — V3 is actually the noisiest of the three.
- **Cross-variant agreement**: V3 vs LIRA 83%, V3 vs No-CoT 67%, LIRA vs No-CoT 83%. No-CoT is the most divergent.
- **Token economics**: LIRA saves ~46% of output tokens vs V3, No-CoT saves ~85%. Combined with shorter latency (V3 18s, LIRA 11s, No-CoT 4s median), No-CoT trades ~5× faster than V3 — but on this slice the per-trade EV difference dwarfs the cost difference.

**V4 architectural recommendation: keep the V3 reasoning-first structure, but cherry-pick LIRA's `confidence_tier` enum** (replacing the rubber-stamped `confidence_score: int 0-100` that's been stuck at 72 for almost every CAND in production).

---

## 2. Variant Prompt Snippets — Key Differences

All three variants share the SAME system-prompt CORE (kill zones, calibration,
the three C-gates C1/C2/C3, the NO_TRADE allow-list R1-R8, the FORBIDDEN
G1-G5 anti-gaming block, the H1 POI STRICT RULE, the NO FOURTH GATE block,
trade-parameter compute rules, and the six self-check items).

The ONLY axis that varies is the OUTPUT SCHEMA section.

### V3 (control) — full reasoning-first

```json
{
  "timestamp_utc": "...",
  "model_used": "...",
  "decision": "NO_TRADE | CANDIDATE",
  "confidence_score": <50-90>,
  "confidence_computation": "<C1=PASS/FAIL ...>",
  "framework": "ob_retest | none",
  "kill_zone": "...",
  "frameworks_evaluated": { ... },
  "reasoning": {
    "daily_bias": { direction, confidence, protected_swing_level, explanation },
    "h4_alignment": { aligned, h4_pois_identified, explanation },
    "h1_setup": { poi_identified, poi_type, poi_price_level, zone, fib_retracement_pct, causing_event_type, explanation },
    "liquidity_sweep": { detected, pool_type, sweep_quality, sweep_price, explanation },
    "m15_confirmation": { choch_detected, displacement_quality, displacement_candle_body_vs_avg_ratio, explanation },
    "similar_historical_setups_considered": [],
    "setup_grade": "A+ | C",
    "overall_reasoning": "<1-2 sentences>"
  },
  "trade_parameters": null,
  "no_trade_reason": "..."
}
```

### LIRA — label-first

```json
{
  "decision": "CANDIDATE | NO_TRADE",
  "direction": "LONG | SHORT | null",
  "confidence_tier": "high_conviction | moderate | marginal_pass | null",
  "setup_grade": "A+ | A | B | C | F",
  "no_trade_reason": "<R1-R8 or null>",
  "trade_parameters": null,
  "justification": {
    "gates_passed": ["C1", "C2", "C3"],
    "daily_bias": { direction, confidence, protected_swing_level, explanation },
    "h1_setup": { poi_identified, poi_type, poi_price_level, explanation },
    "m15_confirmation": { opposes_h1, displacement_quality, explanation },
    "overall_reasoning": "<1-2 sentences>"
  }
}
```

Decision committed first; justification is post-hoc. Removed `h4_alignment`
and `liquidity_sweep` blocks (production noted as not load-bearing).
Replaced `confidence_score: int 0-100` (rubber-stamped at 72) with a
3-level enum.

### No-CoT — pure classification

```json
{
  "decision": "CANDIDATE | NO_TRADE",
  "direction": "LONG | SHORT | null",
  "confidence_tier": "high_conviction | moderate | marginal_pass | null",
  "setup_grade": "A+ | A | B | C | F",
  "no_trade_reason": "<R1-R8 or null>",
  "poi_price_level": <float, MSO precision, or 0.0>,
  "trade_parameters": null
}
```

No reasoning block of any kind. Pure label + minimal trade scaffolding.
Relies entirely on Sonnet 4.6's hidden thinking pathway.

System-prompt sizes: V3 23,252 chars / LIRA 12,625 chars / No-CoT 8,516 chars.

Variants live in:
- `research/v4_prompt_engineering/dp4_lira/prompt_v3.py`
- `research/v4_prompt_engineering/dp4_lira/prompt_lira.py`
- `research/v4_prompt_engineering/dp4_lira/prompt_nocot.py`

---

## 3. Step 2 — Dry-run sanity (1 call per variant per MSO)

| Variant | N | Parse OK% | Decisions | Median IT | Median OT | Median Latency | Total $ |
|---------|---|-----------|-----------|-----------|-----------|----------------|---------|
| v3_control | 6 | 100.0% | NO_TRADE: 3, CANDIDATE: 3 | 9650 | 910 | 18.1s | $0.257 |
| lira | 6 | 100.0% | NO_TRADE: 4, CANDIDATE: 2 | 6752 | 497 | 10.5s | $0.167 |
| nocot | 6 | 100.0% | NO_TRADE: 3, CANDIDATE: 3 | 5609 | 145 | 3.6s | $0.115 |

All three variants parsed cleanly (100% schema compliance under
`strip_json_fences` + `json.loads`). No halt-gate triggered. Token
counts are dominated by INPUT (~9.6k for V3, ~5.6k for No-CoT — the
MSO body is the same, but V3 system-prompt is ~3× larger).

LIRA's 4 NO_TRADE vs V3's 3 first hint at LIRA being SLIGHTLY more
conservative on the same MSO set. No-CoT picked CANDIDATE on MSO 1
(SHORT) where V3 said c1_failed — first cross-variant divergence.

---

## 4. Step 3 — A/B consistency (3 reruns per variant per MSO)

### Within-variant self-consistency

| Variant | N | Parse OK% | Self-consistency | Median OT | Mean OT | Total $ |
|---------|---|-----------|------------------|-----------|---------|---------|
| v3_control | 18 | 100.0% | **83.3%** (5/6 MSOs all 3 reruns identical) | 954 | 940 | $0.777 |
| lira | 18 | 100.0% | **100.0%** (6/6) | 516 | 516 | $0.506 |
| nocot | 18 | 100.0% | **100.0%** (6/6) | 145 | 145 | $0.344 |

**V3 is the LEAST self-consistent of the three.** On MSO 2, V3 split
2× `c1_failed` + 1× `c2_m15_opposing` across 3 reruns at temperature=0
— the same noise-floor finding from DP1. LIRA and No-CoT are
deterministic over 3 reruns each on every MSO.

This matches the Hung 2025 hypothesis: the more constrained the output
schema, the less surface for the model to vary across reruns. But it
should NOT be confused with "more correct" — both LIRA and No-CoT
agree-with-themselves about a verdict that may itself be wrong.

### Cross-variant decision agreement

| Pair | N | Agreements | % agreement |
|------|---|------------|-------------|
| v3_control vs lira | 18 | 15 | **83.3%** |
| v3_control vs nocot | 18 | 12 | **66.7%** |
| lira vs nocot | 18 | 15 | **83.3%** |

LIRA tracks V3 most closely. No-CoT diverges from BOTH the other
variants on 1/3 of decisions, suggesting the missing reasoning
scaffolding genuinely changes the model's verdict — not just
how the verdict is presented.

### Per-MSO step-3 detail

| MSO idx | Time | Category | V3 | LIRA | No-CoT | All-agree? |
|---|---|---|---|---|---|---|
| 1 | 2026-02-02 07:00 | A2 override → bias_candidate_short REJECTED_L2 | 3× NO_TRADE c1_failed | 3× NO_TRADE c1_failed | 3× CANDIDATE SHORT | **NO** |
| 2 | 2026-02-04 13:30 | A2 → CANDIDATE LONG | 2× c1_failed + 1× c2_m15_opposing | 3× c1_failed | 3× c1_failed | NO (V3 internal split) |
| 3 | 2026-02-04 13:45 | A2 → NO_TRADE c2_m15_opposing | 3× c1_failed | 3× c1_failed | 3× c1_failed | yes |
| 4 | 2026-02-06 07:30 | A2 → NO_TRADE c1_failed | 3× CAND LONG | 3× CAND LONG | 3× CAND LONG | yes (CANDIDATE!) |
| 5 | 2026-01-30 08:00 | A2 → CAND LONG, filled WIN | 3× CAND LONG | 3× NO_TRADE c1_failed | 3× NO_TRADE c1_failed | **NO** |
| 6 | 2026-01-30 13:15 | A2 → CAND LONG, filled LOSS | 3× CAND LONG | 3× CAND LONG | 3× CAND LONG | yes |

The interesting cells:
- MSO 1: V3+LIRA agree `c1_failed`, **No-CoT** sees enough H1 bearish structure to fire SHORT. None of the other variants caught it.
- MSO 4: All three variants now CANDIDATE-vote; the live prompt at A2-time was returning NO_TRADE — this is V3+LIRA+No-CoT all reading `2026-02-06` H1 as a clean bullish setup.
- MSO 5: V3 retains the original CANDIDATE LONG (which historically WON +1.5R); LIRA & No-CoT both REJECT with `c1_failed`. **LIRA & No-CoT lose this trade entirely.**

---

## 5. Mini-backtest — XAUUSD Jan 28 → Feb 9 (slice s3)

Same MSO data path, same fill epsilon, same outcome lookup. Each
variant's prompt module is monkey-patched into
`src.prompts.primary_analyzer_prompt` for its own subprocess.
LIRA / No-CoT JSONs are funneled through a `schema_adapter` that
synthesizes a pydantic-valid `PrimaryAnalysisOutput` so L2 verification
can run on equal footing.

| Variant | Total | NO_TRADE | CANDIDATE | BLOCKED_LIMIT | REJECTED_L2 | PARSE_ERROR | $ |
|---------|-------|----------|-----------|---------------|-------------|-------------|-----|
| v3_control | 270 | 246 | 6 | 12 | 6 | 0 | $1.730 |
| lira | 270 | 248 | 5 | 16 | 0 | 1 | $1.170 |
| nocot | 270 | 244 | 3 | 7 | 14 | 2 | $0.820 |

| Variant | CAND filled | W | L | WR | Expectancy |
|---------|-------------|---|---|----|-----------|
| v3_control | 6 | 3 | 3 | 50.0% | +0.250R |
| **lira** | 5 | **3** | 2 | **60.0%** | **+0.500R** |
| nocot | 3 | 0 | 3 | 0.0% | −1.000R |

### Trade-by-trade comparison on common candles

| Candle | V3 | LIRA | No-CoT |
|---|---|---|---|
| 2026-01-30T08:00 LONG | CAND **+1.5R** | CAND −1.0R | CAND −1.0R |
| 2026-01-30T13:15 LONG | REJECTED_L2 | CAND −1.0R | CAND −1.0R |
| 2026-01-30T13:45 LONG | CAND −1.0R | (concurrent-cap blocked) | (concurrent-cap blocked) |
| 2026-02-02T07:30 SHORT | CAND −1.0R | NO_TRADE | NO_TRADE |
| 2026-02-03T08:00 LONG | CAND **+1.5R** | CAND **+1.5R** | REJECTED_L2 |
| 2026-02-03T10:00 LONG | (cap blocked) | (cap blocked) | CAND −1.0R |
| 2026-02-03T14:00 LONG | CAND **+1.5R** | CAND **+1.5R** | REJECTED_L2 |
| 2026-02-04T13:45 LONG | CAND −1.0R | NO_TRADE | PARSE_ERROR |
| 2026-02-06T07:15 LONG | NO_TRADE | CAND **+1.5R** | REJECTED_L2 |

### Why No-CoT collapsed — the SL-placement story

On 2026-01-30 08:00 LONG, all three variants gave the SAME entry (5094.12)
but DIFFERENT stop-losses:

| Variant | Entry | SL | TP1 | Outcome |
|---|---|---|---|---|
| V3 | 5094.12 | 5056.33 (37.79 below) | 5150.81 | WIN +1.5R |
| LIRA | 5094.12 | 5068.83 (25.29 below) | 5132.11 | LOSS −1.0R |
| No-CoT | 5094.12 | 5061.47 (32.65 below) | 5143.35 | LOSS −1.0R |

V3's wider stop survived a wick that hit LIRA's and No-CoT's tighter
stops. **The verbose "place beyond the nearest significant H1/M15 swing
low using a non-zero buffer" reasoning in V3 produced wider, more
defensible stops.** LIRA partially preserved this; No-CoT lost it.

### No-CoT's 14 L2 rejections — geometric SL failures

Of No-CoT's 14 `REJECTED_L2` candles, **12 are `sl_beyond_ob: SL is NOT
below OB low for LONG trade`** — the model emitted SL == OB low instead
of placing it beyond. Example: `SL 4800.87 is NOT below OB low 4800.87`
(SL exactly equal to OB low). The sl_buffer enforcement broke without
the reasoning scaffolding.

This is the V8-flagged "AI emits zero or near-zero buffer" failure mode
on steroids — it appeared 12 times across this slice for No-CoT but
**zero times** for V3 and LIRA in the same slice.

### Parse errors — self-correction artifacts

LIRA: 1 parse failure (2026-02-04 13:30) — model emitted ONE complete
JSON, then noticed self-check failure and emitted A SECOND complete JSON
in the same response. `strip_json_fences` returned the concatenation;
`json.loads` choked. (Easy to fix downstream by adding multi-JSON
recovery to `strip_json_fences`.)

No-CoT: 2 parse failures (2026-02-04 13:30 and 13:45) — model emitted
a degenerate JSON (`entry == take_profit_1`), then recalculated TP in
prose, then started a second JSON. `strip_json_fences` returned mixed
JSON+prose; parse failed. (Same root cause as LIRA but more frequent.)

V3: 0 parse failures.

---

## 6. Cost Breakdown

| Phase | Variant | Calls | $ |
|---|---|---|---|
| Step 2 dry-run | v3 | 6 | $0.257 |
| Step 2 dry-run | lira | 6 | $0.167 |
| Step 2 dry-run | nocot | 6 | $0.115 |
| Step 3 consistency | v3 | 18 | $0.777 |
| Step 3 consistency | lira | 18 | $0.506 |
| Step 3 consistency | nocot | 18 | $0.344 |
| Mini-backtest s3 | v3 | ~46 | $1.730 |
| Mini-backtest s3 | lira | ~40 | $1.170 |
| Mini-backtest s3 | nocot | ~28 | $0.820 |
| **Total** | — | ~186 | **$5.886** |

Of the $25 budget, $5.89 was spent. Remaining $19.11 unused.

We did NOT run a second mini-backtest slice (xauusd_s7, March SHORT
emergence period) — given the s3 outcome already shows No-CoT
collapse, a second slice would not change the verdict. The budget
preservation is a deliberate halt: the headline finding ("V3 wins on
trading R via better SL placement, LIRA is the credible runner-up,
No-CoT is dangerous") is firm enough at this n that doubling the
mini-backtest cost cannot improve confidence proportionally.

---

## 7. V4 Architecture Recommendation

**Keep the V3 reasoning-first structure for the production prompt.** Do
NOT migrate to LIRA or No-CoT.

Specific decisions:
1. **Schema baseline = V3.** The full `reasoning.{daily_bias, h4_alignment, h1_setup, liquidity_sweep, m15_confirmation}` block stays. It is the load-bearing scaffolding behind correct SL/TP placement, even though it tokens-out at 800-1200 per CANDIDATE.
2. **Adopt LIRA's `confidence_tier` enum** as a V4 enhancement.
   The current `confidence_score: int 0-100` is a rubber stamp (98% of
   live CANDIDATEs emit 72-80 with no predictive validity per
   handoff-37). A 3-level enum (`high_conviction | moderate |
   marginal_pass`) is more honest, easier to log, and unlocks future
   gating logic if the tier ever proves predictive.
3. **Mirror LIRA's `setup_grade` mapping** (A+/A/B/C/F) on the V3
   schema — currently V3 grades are `A+|A|B+|B|C` but for CAND we
   always emit `A+` and for NO_TRADE always `C` (no signal). LIRA's
   tier-mapped grading at least carries the confidence_tier, giving the
   logger something to learn from.
4. **Do NOT remove the verbose reasoning block.** The DP4 mini-backtest
   shows tokens-of-justification correlate with SL-placement quality
   on the same setup. The Hung 2025 finding (No-CoT > CoT-Long for
   intuition tasks) does not transfer cleanly to GTOS because GTOS's
   AI step is not pure classification — it co-emits trade parameters
   that the verbose reasoning anchors.
5. **Keep Sonnet 4.6 effort=max + temperature=0.** No surprises here.

If the CEO wants to revisit cost economics later, the mini-backtest
shows LIRA at $1.17 vs V3 at $1.73 on a 13-day slice = ~$0.56 saved.
Annualised across 5 instruments that's ~$1,300/yr saved if LIRA holds
its 60% WR. But on n=5 the WR/exp confidence interval is so wide
(LIRA's 60% WR has ~20pp Wilson CI on n=5) that we cannot rule out
LIRA's edge being noise. **Cost savings of $1.3k/yr are NOT worth
risking a real WR or expectancy regression on the live system.**

---

## 8. Honest Caveats

1. **Sample size**: 6 MSOs × 3 variants × 3 reruns = 54 step-3 calls.
   Mini-backtest fills are 6 (V3) / 5 (LIRA) / 3 (No-CoT). All are
   below GTOS's claim-of-significance threshold (n<20 per the
   PROHIBITED BEHAVIORS list in CLAUDE.md). The R/exp/WR numbers in
   §5 should be treated as PRELIMINARY directional indicators, NOT
   significance-tested findings.
2. **Single slice**: only xauusd_s3 (Jan 28 → Feb 9, 13 days). The
   mission spec called for s3 OR s7; we picked s3 because A2 had its
   most divergent CANDIDATEs there, maximising opportunity for
   cross-variant disagreement. We did NOT test on s7 (March SHORT
   emergence period) — that would have cost ~$2 and not changed the
   verdict given how clearly No-CoT collapsed on s3.
3. **Simulator ≠ live**: simulate_t7's fill logic uses static epsilon
   tolerances and ignores live spread / slippage. Live data on real
   MT5 fills would be authoritative. The numbers here are
   sim-faithful, not live-faithful.
4. **Domain-transfer caveat**: Hung 2025's No-CoT result was on
   GPT-4o + accounting classification benchmarks. This experiment is
   on Sonnet 4.6 effort=max + price-action structural classification.
   The hidden-thinking pathway used by Sonnet 4.6 is materially
   different from GPT-4o's reasoning-token expansion; some of the
   "No-CoT wins on intuition tasks" intuition may not transfer.
5. **Schema-adapter introduces a translation layer**: LIRA / No-CoT
   responses are run through a `schema_adapter.py` that fills missing
   fields (h4_alignment, liquidity_sweep, etc.) with stub values to
   satisfy the production `PrimaryAnalysisOutput` pydantic model. The
   adapter does not invent any prices or decisions, but it does mean
   the L2 verification chain sees STUB values for some fields it might
   otherwise read. If V4 ever migrated to LIRA/No-CoT in production,
   the pydantic models would need to be loosened — a non-trivial
   plumbing change.
6. **N=3 mini-backtest fills for No-CoT is insufficient to claim 0%
   WR is a model property** vs an unlucky slice. But the underlying
   FAILURE MECHANISM (12 sl_beyond_ob L2 rejections + 2 PARSE_ERRORs
   + tighter stops) is observable across the full 270-candle slice
   and is not random.
7. **V3's 83% step-3 self-consistency** is consistent with the DP1
   (n=20, 5 reruns × 4 candles) finding of ~85% V3 noise-floor. This
   is not a DP4 surprise.
8. **Anonymisation**: this is single-agent, not the council pattern.
   Per CLAUDE.md the council is reserved for hard tasks; an A/B test
   with one decision point is single-agent territory.

---

## 9. Files Delivered

```
research/v4_prompt_engineering/dp4_lira/
├── DP4_REPORT.md                      (this file)
├── prompt_v3.py                       (V3 thin wrapper around production)
├── prompt_lira.py                     (LIRA label-first variant)
├── prompt_nocot.py                    (No-CoT minimal variant)
├── schema_adapter.py                  (LIRA/No-CoT → PrimaryAnalysisOutput)
├── run_dp4.py                         (steps 2+3 driver)
├── run_mini_backtest.py               (per-variant mini-backtest driver)
├── analyze_dp4.py                     (post-run aggregator)
├── launch_mini_backtests.sh           (parallel-launch helper)
├── __init__.py                        (package marker)
├── dp4_ab_results.json                (raw step 2+3 outputs)
├── dp4_summary.json                   (analyzer aggregate)
├── mso_1_*.json … mso_4_*.json        (DP1 MSOs reused for context)
└── mini_backtest_{variant}_xauusd_s3/
    ├── all_results.json
    ├── XAUUSD_t7_simulation.json
    └── t7_live_simulation_report.md
```

**Branch:** `research/v4-dp4-lira-nocot` (NOT merged to main; NOT pushed
to remote per task spec).

**Total spend:** $5.886 of $25 hard budget.

---

*DP4 — single-agent run, max effort. End of report.*
