# DP1 V3 Noise-Floor Measurement — Report

- Generated: `2026-04-24T20:42:19.149132+00:00`
- Elapsed: 6.08 minutes
- Total API spend: **$0.8393** (budget cap $2.00)
- Config: `primary_model=claude-sonnet-4-6` `primary_effort=max` `detector_version=v2`
- Runs per candle: **5** — total API calls: **20**
- Prompt version replayed: V3 (current production, HEAD `2f6ef8f` at time of test). A2's original call used the same commit.

## Executive summary

**VERDICT (internal self-consistency band): `>=85%`**

V3 IS DETERMINISTIC (all 5 reruns produced the same decision+direction on 4/4 candles). V4 iteration is on-target; A/B tests should measure real prompt effects, not LLM noise.

### Two orthogonal metrics

| Metric | Value | Interpretation |
|---|---|---|
| **(A) V3 INTERNAL hard agreement** (5 reruns same decision+direction per candle) | **4/4 candles = 100.0%** | Literal answer to 'is V3 deterministic?' — PRIMARY verdict driver. |
| (A') V3 INTERNAL soft agreement (decision only) | 4/4 = 100.0% | Ignoring direction; confirms decision-class determinism. |
| **(B) V3 REPLAY match to A2 original** (reruns matching A2's PA decision+direction) | **5/20 reruns = 25.0%** | How often fresh V3 reproduces A2's recorded call. Side-finding on stochasticity-over-time. |

**Why the primary verdict uses (A) not (B):** V4_SYNTHESIS pre-reg frames DP1 as 'V3's re-run agreement rate' citing Atil et al. — an internal-rerun noise-floor measurement. Metric (B) conflates noise with 'is A2's single sample representative?', which is a different question. A model can be 100% internally deterministic yet still disagree with a previous single roll if the previous roll itself was a low-probability outcome. That is precisely the pattern we find.

### Honest side-findings — A2 originals on these 4 candles

- **Candle 1 (2026-02-02T07:00:00Z)**: A2 was `CANDIDATE_SHORT`; all 5 V3 reruns returned `NO_TRADE`. **A2 was an outlier** (0% rerun match despite 100% rerun-to-rerun agreement).
- **Candle 2 (2026-02-04T13:30:00Z)**: A2 was `CANDIDATE_LONG`; all 5 V3 reruns returned `NO_TRADE`. **A2 was an outlier** (0% rerun match despite 100% rerun-to-rerun agreement).
- **Candle 4 (2026-02-06T07:30:00Z)**: A2 was `NO_TRADE`; all 5 V3 reruns returned `CANDIDATE_LONG`. **A2 was an outlier** (0% rerun match despite 100% rerun-to-rerun agreement).

### Per-candle breakdown

| # | Candle | A2 PA decision | 5 rerun decisions | Internal hard | A2 matches |
|---|---|---|---|---|---|
| 1 | `2026-02-02T07:00:00Z` | `CANDIDATE_SHORT` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 agree on `NO_TRADE`) | 0/5 |
| 2 | `2026-02-04T13:30:00Z` | `CANDIDATE_LONG` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 agree on `NO_TRADE`) | 0/5 |
| 3 | `2026-02-04T13:45:00Z` | `NO_TRADE` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 agree on `NO_TRADE`) | 5/5 |
| 4 | `2026-02-06T07:30:00Z` | `NO_TRADE` | `CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG` | True (5/5 agree on `CANDIDATE_LONG`) | 0/5 |

### Implications for V4 validation plan

1. **Proceed with V4 A/B as planned.** V3 is internally deterministic on decision+direction at the production config (Sonnet 4.6 effort=max, temperature=0). Any V4-vs-V3 decision difference in the A/B test is attributable to the prompt, not to LLM stochasticity.
2. However — **A2's single-sample baseline is unreliable on 75% of divergent candles**. Replay of V3 disagrees with A2's recorded V3 call on 3/4 candles despite internal determinism. This means the 'F3→A2 WR gap' that motivated V4 can be partly attributed to A2 rolling unlucky (or lucky) samples, NOT to prompt regression. V4's +4.0R counterfactual on A2 divergent candles should be re-evaluated against V3-fresh baseline, not A2.
3. Sub-decision variance (daily_bias_direction, no_trade_reason) drifts between reruns even when the top-level decision is pinned. V4 changes that touch only the reasoning scaffold (not the decision gates) will be noise-dominated — prioritise V4 changes that flip decisions, not ones that reword rationale.

## Per-candle detail

### Candle 1 — `2026-02-02T07:00:00Z` (london) — *override_computed_bias_candidate_short*

- **A2 original (PA):** `CANDIDATE_SHORT` grade=`A+` bias=`bearish` ntr=`None`
- **A2 final (post-L2):** `REJECTED_L2`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `NO_TRADE`); soft=True
- **A2 match count:** 0/5

| Run | Decision | Direction | Bias (confidence) | Grade | No-trade reason | Confidence | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | bearish (low) | C | c1_failed | 85 | $0.0412 | 18.1s |
| 2 | NO_TRADE | — | ranging (low) | C | c1_failed | 85 | $0.0408 | 16.5s |
| 3 | NO_TRADE | — | bearish (low) | C | c1_failed | 82 | $0.0422 | 18.9s |
| 4 | NO_TRADE | — | bearish (low) | C | c1_failed | 85 | $0.0411 | 17.5s |
| 5 | NO_TRADE | — | bearish (low) | C | c1_failed | 82 | $0.0426 | 20.5s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — 2 unique: `{'bearish': 4, 'ranging': 1}`
- `daily_bias_confidence` — identical: `{'low': 5}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — identical: `{'c1_failed': 5}`
- `framework` — identical: `{'none': 5}`
- `confidence_score` — 2 unique: `{85: 3, 82: 2}`

### Candle 2 — `2026-02-04T13:30:00Z` (ny) — *missing_m15_opposition_detection*

- **A2 original (PA):** `CANDIDATE_LONG` grade=`A+` bias=`bullish` ntr=`None`
- **A2 final (post-L2):** `CANDIDATE`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `NO_TRADE`); soft=True
- **A2 match count:** 0/5

| Run | Decision | Direction | Bias (confidence) | Grade | No-trade reason | Confidence | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | ranging (low) | C | c1_failed | 72 | $0.0416 | 16.6s |
| 2 | NO_TRADE | — | bullish (low) | C | c1_failed | 72 | $0.0414 | 16.9s |
| 3 | NO_TRADE | — | bullish (medium) | C | c1_failed | 72 | $0.0411 | 18.6s |
| 4 | NO_TRADE | — | bearish (low) | C | c1_failed | 72 | $0.0414 | 16.1s |
| 5 | NO_TRADE | — | ranging (low) | C | c1_failed | 72 | $0.0419 | 18.3s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — 3 unique: `{'ranging': 2, 'bullish': 2, 'bearish': 1}`
- `daily_bias_confidence` — 2 unique: `{'low': 4, 'medium': 1}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — identical: `{'c1_failed': 5}`
- `framework` — identical: `{'none': 5}`
- `confidence_score` — identical: `{72: 5}`

### Candle 3 — `2026-02-04T13:45:00Z` (ny) — *detected_m15_opposition*

- **A2 original (PA):** `NO_TRADE` grade=`C` bias=`bullish` ntr=`c2_m15_opposing`
- **A2 final (post-L2):** `NO_TRADE`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `NO_TRADE`); soft=True
- **A2 match count:** 5/5

| Run | Decision | Direction | Bias (confidence) | Grade | No-trade reason | Confidence | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | bullish (medium) | C | c2_m15_opposing | 72 | $0.0412 | 17.4s |
| 2 | NO_TRADE | — | ranging (low) | C | c1_failed | 72 | $0.0412 | 17.4s |
| 3 | NO_TRADE | — | ranging (low) | C | c1_failed | 72 | $0.0412 | 17.2s |
| 4 | NO_TRADE | — | bullish (high) | C | c2_m15_opposing | 72 | $0.0410 | 17.0s |
| 5 | NO_TRADE | — | ranging (low) | C | c1_failed | 72 | $0.0402 | 15.9s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — 2 unique: `{'bullish': 2, 'ranging': 3}`
- `daily_bias_confidence` — 3 unique: `{'medium': 1, 'low': 3, 'high': 1}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — 2 unique: `{'c2_m15_opposing': 2, 'c1_failed': 3}`
- `framework` — identical: `{'none': 5}`
- `confidence_score` — identical: `{72: 5}`

### Candle 4 — `2026-02-06T07:30:00Z` (london) — *respects_h1_bearish_mso*

- **A2 original (PA):** `NO_TRADE` grade=`C` bias=`bullish` ntr=`c1_failed`
- **A2 final (post-L2):** `NO_TRADE`
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bearish` M15=`bullish`
- **Internal consistency:** hard=True (5/5 on `CANDIDATE_LONG`); soft=True
- **A2 match count:** 0/5

| Run | Decision | Direction | Bias (confidence) | Grade | No-trade reason | Confidence | Cost | Time |
|---|---|---|---|---|---|---|---|---|
| 1 | CANDIDATE | LONG | bullish (low) | A+ | — | 72 | $0.0441 | 19.6s |
| 2 | CANDIDATE | LONG | bullish (low) | A+ | — | 72 | $0.0435 | 19.1s |
| 3 | CANDIDATE | LONG | bullish (low) | A+ | — | 72 | $0.0443 | 21.8s |
| 4 | CANDIDATE | LONG | bullish (low) | A+ | — | 72 | $0.0432 | 21.6s |
| 5 | CANDIDATE | LONG | bullish (low) | A+ | — | 72 | $0.0440 | 19.3s |

**Variance fingerprint across the 5 reruns:**

- `decision` — identical: `{'CANDIDATE': 5}`
- `direction` — identical: `{'LONG': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'low': 5}`
- `setup_grade` — identical: `{'A+': 5}`
- `no_trade_reason` — identical: `{None: 5}`
- `framework` — identical: `{'ob_retest': 5}`
- `confidence_score` — identical: `{72: 5}`
