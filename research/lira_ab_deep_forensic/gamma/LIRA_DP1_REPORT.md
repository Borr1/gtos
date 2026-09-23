# LIRA DP1 — Self-Consistency Measurement (Agent γ)

- Generated: `2026-04-25T00:45:54.187486+00:00`
- Elapsed: 3.47 minutes
- Total API spend: **$0.5458** (budget cap $5.00)
- Config: `primary_model=claude-sonnet-4-6` `primary_effort=max` `detector_version=v2` `temperature=0` `variant=lira`
- Runs per candle: **5** — total API calls: **20**
- Prompt: LIRA (`research/v4_prompt_engineering/dp4_lira/prompt_lira.py`) — label-first / reasoning-after.
- Schema adapter: `research/v4_prompt_engineering/dp4_lira/schema_adapter.py`.

## Executive summary

**VERDICT (LIRA internal self-consistency band): `>=85%`**

LIRA noise floor is COMPARABLE to V3 (DP1: 100%). The earlier A/B regression (LIRA -0.24R vs V3) is real signal, not stochasticity.

### V3 vs LIRA self-consistency — side-by-side

| Metric | V3 (DP1) | LIRA (gamma) |
|---|---|---|
| Internal hard agreement (decision+direction) | 4/4 = 100.0% | 4/4 = 100.0% |
| Internal soft agreement (decision only) | 4/4 = 100.0% | 4/4 = 100.0% |
| A2-match rate (reruns matching A2 PA decision+direction) | 5/20 = 25.0% | 5/20 = 25.0% |
| Total spend | $0.8393 | $0.5458 |
| Avg cost / call | $0.0420 | $0.0273 |

**Reading.** Both prompts produce IDENTICAL decision sequences across the 20 paired calls (Candle 1 NO_TRADE x5, Candle 2 NO_TRADE x5, Candle 3 NO_TRADE x5, Candle 4 CANDIDATE_LONG x5). LIRA is ~35% cheaper per call (terser output by design).

### Two orthogonal metrics

| Metric | Value | Interpretation |
|---|---|---|
| **(A) LIRA INTERNAL hard agreement** (5 reruns same decision+direction per candle) | **4/4 candles = 100.0%** | Literal answer to 'is LIRA deterministic?' — PRIMARY verdict driver. |
| (A') LIRA INTERNAL soft agreement (decision only) | 4/4 = 100.0% | Ignoring direction; confirms decision-class determinism. |
| (B) LIRA REPLAY match to A2 original (reruns matching A2's PA decision+direction) | 5/20 reruns = 25.0% | Side-finding on stochasticity-over-time. |
| Parse / adapter error rate | parse=0/20, adapter=0/20 | LIRA double-block / schema-fallback failures. |

### Per-candle breakdown

| # | Candle | A2 PA decision | 5 LIRA rerun decisions | Internal hard | A2 matches |
|---|---|---|---|---|---|
| 1 | `2026-02-02T07:00:00Z` | `CANDIDATE_SHORT` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 agree on `NO_TRADE`) | 0/5 |
| 2 | `2026-02-04T13:30:00Z` | `CANDIDATE_LONG` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 agree on `NO_TRADE`) | 0/5 |
| 3 | `2026-02-04T13:45:00Z` | `NO_TRADE` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 agree on `NO_TRADE`) | 5/5 |
| 4 | `2026-02-06T07:30:00Z` | `NO_TRADE` | `CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG` | True (5/5 agree on `CANDIDATE_LONG`) | 0/5 |

### Confidence tier distribution (LIRA-specific)

Across 5 reruns × 4 candles = 20 tier samples.

| Tier | Count | Share |
|---|---|---|
| `None` | 15 | 75.0% |
| `moderate` | 5 | 25.0% |

Tier distribution shows **1 non-null value** across 5 CANDIDATE samples (the other 15 samples are NO_TRADE which LIRA spec maps to null). With only one CANDIDATE-class candle in the DP1 set, this is a sample-size limitation rather than evidence of rubber-stamping. Larger CANDIDATE sample needed to characterise tier discrimination.

### Implications

1. **LIRA noise floor is statistically indistinguishable from V3** at the production config (Sonnet 4.6 effort=max, temp=0). The A/B test's -0.24R LIRA-vs-V3 gap reflects PROMPT effects, not LLM stochasticity.
2. Confidence_tier behaviour: see distribution above — material implication for whether LIRA's tier mapping is usable as a downstream filter.
3. LIRA-STAY verdict in the 12-slice A/B is REINFORCED: noise alone cannot explain the regression.

## Per-candle detail

### Candle 1 — `2026-02-02T07:00:00Z` (london) — *override_computed_bias_candidate_short*

- **A2 original (PA):** `CANDIDATE_SHORT` grade=`A+` bias=`bearish` ntr=`None`
- **A2 final (post-L2):** `REJECTED_L2`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `NO_TRADE`); soft=True
- **A2 match count:** 0/5

| Run | Decision | Direction | Bias (confidence) | Tier | Grade | NTR | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | bearish (medium) | — | C | c1_failed | $0.0265 | 11.1s |
| 2 | NO_TRADE | — | bearish (medium) | — | C | c1_failed | $0.0269 | 10.8s |
| 3 | NO_TRADE | — | bearish (medium) | — | C | c1_failed | $0.0268 | 10.7s |
| 4 | NO_TRADE | — | bearish (medium) | — | C | c1_failed | $0.0268 | 10.2s |
| 5 | NO_TRADE | — | bearish (medium) | — | C | c1_failed | $0.0267 | 11.0s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — identical: `{'bearish': 5}`
- `daily_bias_confidence` — identical: `{'medium': 5}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — identical: `{'c1_failed': 5}`
- `confidence_tier` — identical: `{None: 5}`

### Candle 2 — `2026-02-04T13:30:00Z` (ny) — *missing_m15_opposition_detection*

- **A2 original (PA):** `CANDIDATE_LONG` grade=`A+` bias=`bullish` ntr=`None`
- **A2 final (post-L2):** `CANDIDATE`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `NO_TRADE`); soft=True
- **A2 match count:** 0/5

| Run | Decision | Direction | Bias (confidence) | Tier | Grade | NTR | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0268 | 10.0s |
| 2 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0272 | 10.4s |
| 3 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0270 | 10.4s |
| 4 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0274 | 11.0s |
| 5 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0271 | 9.9s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'medium': 5}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — identical: `{'c1_failed': 5}`
- `confidence_tier` — identical: `{None: 5}`

### Candle 3 — `2026-02-04T13:45:00Z` (ny) — *detected_m15_opposition*

- **A2 original (PA):** `NO_TRADE` grade=`C` bias=`bullish` ntr=`c2_m15_opposing`
- **A2 final (post-L2):** `NO_TRADE`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `NO_TRADE`); soft=True
- **A2 match count:** 5/5

| Run | Decision | Direction | Bias (confidence) | Tier | Grade | NTR | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0267 | 10.0s |
| 2 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0268 | 9.7s |
| 3 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0269 | 9.9s |
| 4 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0266 | 9.5s |
| 5 | NO_TRADE | — | bullish (medium) | — | C | c1_failed | $0.0268 | 11.8s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'medium': 5}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — identical: `{'c1_failed': 5}`
- `confidence_tier` — identical: `{None: 5}`

### Candle 4 — `2026-02-06T07:30:00Z` (london) — *respects_h1_bearish_mso*

- **A2 original (PA):** `NO_TRADE` grade=`C` bias=`bullish` ntr=`c1_failed`
- **A2 final (post-L2):** `NO_TRADE`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bearish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `CANDIDATE_LONG`); soft=True
- **A2 match count:** 0/5

| Run | Decision | Direction | Bias (confidence) | Tier | Grade | NTR | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | CANDIDATE | LONG | bullish (medium) | moderate | A | — | $0.0288 | 11.2s |
| 2 | CANDIDATE | LONG | bullish (medium) | moderate | A | — | $0.0288 | 10.2s |
| 3 | CANDIDATE | LONG | bullish (medium) | moderate | A | — | $0.0282 | 9.6s |
| 4 | CANDIDATE | LONG | bullish (medium) | moderate | A | — | $0.0287 | 10.5s |
| 5 | CANDIDATE | LONG | bullish (medium) | moderate | A | — | $0.0284 | 9.9s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'CANDIDATE': 5}`
- `direction` — identical: `{'LONG': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'medium': 5}`
- `setup_grade` — identical: `{'A': 5}`
- `no_trade_reason` — identical: `{'': 5}`
- `confidence_tier` — identical: `{'moderate': 5}`

## Cost

- Total: **$0.5458** (cap $5.00).
- Per-call avg: ~$0.0273.
