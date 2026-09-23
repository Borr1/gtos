# V1 Independent Validation Report

**Validator:** Opus 4.7, max effort, independent replication (no prior-audit scripts executed).
**Date:** 2026-04-24
**Scope:** Replicate from scratch the prior audit's claim that (a) 100% of live CANDIDATEs are LONG and (b) `src/components/market_state.py:identify_structure` is structurally biased toward bullish.

## Verdict

**CONFIRMED.** Every load-bearing claim of the prior audit was independently reproduced. The `identify_structure` function at `src/components/market_state.py:216-257` is structurally bullish-biased in realistic 168-bar H1 windows: 8,086/8,086 production-faithful replay windows across 5 instruments returned `bullish`, zero returned `bearish`. Every single CANDIDATE in the live logs (141/141 by reasoning parse, 63/63 by direct `trade_parameters.direction` field in shadow log) is LONG. The bug has existed since the initial commit (`436c16b`).

## Task-by-task findings

### Task 1 — CANDIDATE direction count

**Data sources used:**
- `knowledge_base/live_evaluations/*/*.jsonl` (1,283 rows, Apr 6–23, 2026, 5 instruments)
- `shadow_logs/candidate_features_log.jsonl` (384 rows, Apr 17–23, 2026)

**Schema gotcha (flagged):** The prior audit's hypothesized field names `trade_parameters.direction` and `trade_direction` **do not exist** in `knowledge_base/live_evaluations/*.jsonl`. A raw key dump across all CANDIDATE rows (see Appendix A) shows only these keys — no `trade_parameters` subobject and no `trade_direction` field. Direction in `live_evaluations` can only be inferred from free-text `overall_reasoning`. However, the richer `shadow_logs/candidate_features_log.jsonl` DOES have `trade_parameters.direction` (confirmed via `candidate_features_logger.py:373`), so the direction claim is verifiable via that source.

**Results:**

| Source | CANDIDATE rows | LONG | SHORT | Other |
|---|---|---|---|---|
| `shadow_logs/candidate_features_log.jsonl` (Apr 17–23) | 63 | **63** | 0 | 0 |
| `live_evaluations/*/*.jsonl` (Apr 6–23, reasoning parse) | 141 | 140 | 0 | 1 UNKNOWN (regex gap — row verified LONG via `daily_bias_direction=bullish` + reasoning text "D1/H4/H1/M15 all bullish") |
| `live_evaluations/*/*.jsonl` (daily_bias_direction proxy) | 141 | 141 bullish | 0 bearish | 0 ranging |

**Per-symbol breakdown** (live_evaluations, all 141 CANDIDATEs):

| Symbol | CANDIDATEs | LONG | SHORT |
|---|---|---|---|
| GBPJPY | 35 | 35 | 0 |
| GBPUSD | 29 | 29 | 0 |
| US30_cash | 26 | 26 | 0 |
| USDJPY | 38 | 38 | 0 |
| XAUUSD | 12 | 12 | 0 |

**April-only excluding GBPUSD observer: 112 CANDIDATEs, 100% LONG** — matches prior audit's 112/112.

**CONFIRMED:** 100% LONG. Zero SHORT CANDIDATEs ever produced.

### Task 2 — D1 bias direction distribution

Counted `daily_bias_direction` across all 1,283 evaluations (CAND + NO_TRADE):

| Value | Count | % |
|---|---|---|
| bullish | 901 | 70.23% |
| ranging | 351 | 27.36% |
| **bearish** | **31** | **2.42%** |

Per-symbol bearish counts: GBPJPY=19, GBPUSD=4, US30_cash=4, USDJPY=2, XAUUSD=2.

**Nuance:** D1 bias IS sometimes bearish (31 rows). So the AI does emit bearish D1 bias. None of those 31 rows became a SHORT CANDIDATE — consistent with the prior audit's causal chain: D1 bearish is emitted, but H1 structure is stuck bullish, so the C3 gate (`direction matches H1 bias`) fails and those rows end as NO_TRADE. This shows the bias is located at H1 structure, not at the AI's D1 inference.

### Task 3 — H1 structure direction distribution (smoking gun)

Counted `mso_h1_structure_direction`, `mso_m15_structure_direction`, `mso_d1_structure_direction` from `shadow_logs/candidate_features_log.jsonl` (384 rows, all decisions):

| Field | bullish | bearish | transitional | insufficient_data |
|---|---|---|---|---|
| `mso_h1_structure_direction` | **384** | **0** | 0 | 0 |
| `mso_m15_structure_direction` | 384 | 0 | 0 | 0 |
| `mso_d1_structure_direction` | 79 | 0 | 305 | 0 |

Per-symbol H1: GBPJPY 81/81 bullish, GBPUSD 42/42, US30_cash 95/95, USDJPY 108/108, XAUUSD 58/58. **CONFIRMED:** 100% bullish H1 structure across all 5 instruments over 1 week of live logging. D1 is 0 bearish as well (`transitional` or `bullish` only in this week).

### Task 4 — Code read of `identify_structure`

Read `src/components/market_state.py:216-257`. Function extracted below (current `main` HEAD + initial commit `436c16b` — identical):

```python
def identify_structure(swings: list[Swing]) -> StructureAnalysis:
    highs = [s for s in swings if s.type == "high"]
    lows = [s for s in swings if s.type == "low"]

    if len(highs) < 2 or len(lows) < 2:
        return StructureAnalysis(direction="insufficient_data", ...)

    hh_count = sum(1 for i in range(1, len(highs)) if highs[i].price > highs[i - 1].price)
    ll_count = sum(1 for i in range(1, len(lows))  if lows[i].price  < lows[i - 1].price)
    hl_count = sum(1 for i in range(1, len(lows))  if lows[i].price  > lows[i - 1].price)
    lh_count = sum(1 for i in range(1, len(highs)) if highs[i].price < highs[i - 1].price)

    recent_pairs = min(3, len(highs) - 1, len(lows) - 1)   # line 237

    if hh_count >= recent_pairs and hl_count >= recent_pairs:   # line 239 — bullish branch checked FIRST
        direction = "bullish"
    elif ll_count >= recent_pairs and lh_count >= recent_pairs: # line 242 — bearish branch only if bullish failed
        direction = "bearish"
    else:
        direction = "transitional"
```

**Plain-English analysis:**

1. `recent_pairs` is misnamed. It is **not** "how many recent pairs to look at" — it is a **threshold** (`>= recent_pairs`) capped at 3. It is computed once over the entire input window (168 H1 bars in production per `config/agent_config.yaml:124`).

2. Counts `hh`, `hl`, `lh`, `ll` iterate over **all swing pairs** in the window, not recent ones. So the `recent_pairs` name is doubly misleading: neither the threshold value nor the pairs being counted are "recent" in any meaningful sense.

3. **Saturation mechanism.** In a 168-bar H1 window with ~20 highs and ~20 lows (realistic per test results), each of the four counts almost always exceeds 3. The threshold `min(3, ...)` saturates to `3` for any window with ≥ 4 swings of each type.

4. **Asymmetric precedence.** `if hh>=rp AND hl>=rp` is evaluated BEFORE `elif ll>=rp AND lh>=rp`. When both conditions are true (which is the common case in real data), **bullish always wins**. The bearish branch is unreachable in any window where the bullish branch also qualifies — regardless of whether `ll` and `lh` counts are 3× or 10× higher.

5. No comment in the function explains the rationale. No test exercises the tie-breaking behavior (I searched `tests/` — no test seeds both branches simultaneously). This is a latent logic bug, not a documented design decision.

### Task 5 — Synthetic stress test (file: `v1_fixture_test.py`, `v1_saturation_test.py`)

Constructed OHLCV dicts directly and called `identify_structure` on resulting swings. Key results:

| Fixture | Pattern | Expected | Actual | Notes |
|---|---|---|---|---|
| A | 6 swings, pure uptrend | bullish | **bullish** | ✓ |
| B | 6 swings, pure downtrend | bearish | **bearish** | ✓ (claim partially refuted on tiny data) |
| B2 | 8 swings, strong pure downtrend | bearish | **bearish** | ✓ |
| C | Flat range, equal H and L | transitional | **transitional** | ✓ |
| D | V reversal (down→up) | bullish/transitional | transitional | ambiguous counts |
| E | Inverted V (up→down) | bearish/transitional | transitional | ambiguous counts |
| I | 3 highs 3 lows, all bearish | bearish | **bearish** | ✓ |

**On sparse synthetic swings (4–6 swings total), the function CAN correctly identify bearish.** The prior audit's strongest claim — "even a pure downtrend returns bullish" — is **refuted on minimal fixtures**: when bullish counts don't saturate to 3, bearish wins.

**BUT** — and this is the critical finding — on realistic data:

| Saturation test | hh | hl | lh | ll | direction |
|---|---|---|---|---|---|
| Test 3 (perfect tie, 4 each) | 4 | 4 | 4 | 4 | **bullish** |
| Test 4 (bearish dominant 3× over) | 3 | 3 | 10 | 10 | **bullish** |
| Test 5 (no bullish, bearish only) | 0 | 0 | 6 | 6 | bearish |

On random walks sized like production H1 windows (168 bars):

| Walk type | n | bearish label | bullish label | transitional |
|---|---|---|---|---|
| Drift −0.15 per bar (bearish-trending) | 100 | **6** | **94** | 0 |
| Drift 0 (pure random) | 100 | **0** | **100** | 0 |
| Drift +0.15 per bar (bullish-trending) | 100 | 0 | 100 | 0 |

Even a STRONGLY bearish-trending market gets labeled bullish 94% of the time in 168-bar windows. This is the smoking gun for production behavior.

### Task 6 — Current pipeline_state snapshot

`knowledge_base/pipeline_state/02_market_state.json` (timestamp 2026-04-23T17:00:05Z, symbol not recorded but one of the 5 live orchestrators wrote it last):

| Timeframe | Direction | hh | hl | lh | ll | Both branches qualify? |
|---|---|---|---|---|---|---|
| D1 | bullish | 3 | 2 | 0 | 0 | No — bearish branch does not qualify |
| H4 | **bearish** | 2 | 6 | 5 | 6 | No — bullish `hh<3` |
| **H1** | **bullish** | **11** | **9** | **11** | **9** | **YES — bearish also qualifies (lh=11, ll=9 both ≥3)** |
| M15 | bullish | 43 | 38 | 43 | 50 | **YES — lh=43, ll=50 both ≥3; LL even dominates HH** |

The H1 and M15 rows are live evidence of the ordering bug: in both cases, bearish qualifies (lh ≥ 3 AND ll ≥ 3) — at M15 the bearish signal is numerically stronger (ll=50 > hh=43) — but bullish wins by being checked first.

### Task 7 — Cross-verification via production-faithful replay (file: `v1_historical_replay.py`)

Loaded raw H1 CSV data from `data/historical_2026/{SYMBOL}_H1.csv` (Jan 2 – Apr 20, 2026) for 5 instruments. For each bar beyond #168, built a 168-bar sliding window, ran `detect_swings(min_bars=2)` + `identify_structure`, counted direction labels.

| Symbol | Windows | bullish | bearish | transitional | insufficient | "Both branches qualify (bug condition)" |
|---|---|---|---|---|---|---|
| XAUUSD | 1,553 | 1,553 (100.0%) | **0** | 0 | 0 | 1,553 (100.0%) |
| US30_cash | 1,565 | 1,565 (100.0%) | **0** | 0 | 0 | 1,565 (100.0%) |
| USDJPY | 1,656 | 1,656 (100.0%) | **0** | 0 | 0 | 1,647 (99.5%) |
| GBPJPY | 1,656 | 1,656 (100.0%) | **0** | 0 | 0 | 1,651 (99.7%) |
| GBPUSD | 1,656 | 1,656 (100.0%) | **0** | 0 | 0 | 1,656 (100.0%) |
| **TOTAL** | **8,086** | **8,086 (100.0%)** | **0** | **0** | **0** | **8,072 (99.8%)** |

**CONFIRMED:** Zero bearish H1 labels across 8,086 windows over 3.5 months, all 5 instruments. 99.8% of those windows have the bearish branch ALSO qualifying — direct replicable evidence of the bullish-precedence bug on production-faithful data.

The prior audit reported 7,991 windows; I got 8,086. Difference likely reflects end-date (their replay may have stopped before Apr 20, or excluded weekend-gap bars differently). Directional finding is identical.

## Points of agreement with prior audit

1. **141/141 lifetime CANDIDATEs LONG** — confirmed exactly.
2. **112/112 April LIVE-instrument CANDIDATEs LONG** — confirmed exactly (live = 4 instruments excluding GBPUSD observer; April is the whole logging window).
3. **Zero bearish H1 labels in production replay** — confirmed: my replay returned 0/8,086 (vs their 0/7,991).
4. **Root cause is structural bias in `identify_structure`** — confirmed by code read + synthetic ties + live snapshot (H4 bearish / H1 bullish at same instant is only possible because H4 window is shorter → bullish threshold fails; H1 window saturates → bullish wins).
5. **Bug present since initial commit `436c16b`** — verified via `git log -L` on the function; no subsequent commit has touched `identify_structure`.
6. **AI D1 bias is not the problem** — confirmed: D1 bias IS sometimes bearish (31/1,283 rows), but those rows don't become SHORT CANDIDATEs because H1 is bullish-locked, and the C3 gate (`direction matches H1 bias`) fails.
7. **Downstream pipeline is symmetric** — not exhaustively re-verified, but consistent with my reading of `candidate_features_logger.py:360-373` which computes `c3_direction_matches` against `daily_bias_direction` symmetrically.

## Points of disagreement (minor)

1. **"Pure downtrend returns bullish" is overstated on minimal synthetic data.** The prior audit's phrasing "synthetic pure-downtrend data also classifies as bullish" is only true in windows large enough to saturate `min(3,...)` for both branches. On 4–6 swings, my Fixtures B, B2, I correctly return `bearish`. The bug manifests at realistic window sizes (≥ ~14 bars with alternating swings, per Test 2). This is a *nuance*, not a refutation — in production the window is always 168 H1 bars, which always saturates both branches.
2. **The name "recent_pairs" is actively misleading.** The prior audit describes it correctly as a threshold, but the variable is not in fact "recent" — it counts pairs across the ENTIRE window. This is a code-readability/reviewer-trap issue worth calling out.
3. **Schema note:** The prior audit's Task-1 wording "`trade_parameters.direction` (if present); `trade_direction` (if present)" is correct only for `shadow_logs/candidate_features_log.jsonl` — NOT for the primary `knowledge_base/live_evaluations/*.jsonl` source. A reader might be misled into thinking the field exists in both. I flag this to the CEO: the two sources have different schemas.

None of these disagreements changes the verdict.

## Root-cause verification

**Did V1 reproduce the "recent_pairs = min(3,...) saturation" finding?** YES. Across 8,086 168-bar H1 windows on raw historical data, 8,072 (99.8%) have both branches qualifying simultaneously. The saturation mechanism is: with ≥ 4 swings of each type (typical within 168 H1 bars), `recent_pairs` saturates to 3. Real markets in the 2026 Jan–Apr window have HH/HL/LH/LL counts all well above 3 in almost every window. Bullish wins by ordering (line 239 before line 242).

**Did V1's synthetic fixtures produce 0 bearish outputs?** NO — on SMALL synthetic fixtures (4–6 swings), the function correctly returns `bearish`. But on realistic 168-bar random walks, 94/100 bearish-drift walks AND 100/100 zero-drift walks label `bullish` despite having no genuine bullish regime.

**Conclusion on root cause:** The bug has TWO components:
1. First-branch-wins tie-breaking (bullish before bearish on line 239/242).
2. `recent_pairs` threshold saturates at 3 in any realistic window, causing BOTH branches to qualify simultaneously in 99.8% of production windows — making component (1) fire constantly.

Either alone would be survivable. The combination makes the bearish label effectively unreachable on real market data.

## Confidence

**Overall verdict confidence: 98%.**

Residual 2% uncertainty:
- The production replay used historical CSV data, not a MSO-byte-exact reconstruction of what each live orchestrator computed per tick. The structure module is deterministic given OHLCV input, so this should match — but I did not prove byte-equivalence to the live `02_market_state.json` snapshots by cross-checking timestamps.
- The `mso_h1_structure_direction` shadow log covers only Apr 17–23. For the Apr 6–16 window, I have only inferred direction (100% bullish from D1 bias + reasoning text), not the raw `identify_structure` output. That said, the production replay covers the entire Jan–Apr window and returns 0 bearish, so the gap is closed by the replay.

**No claim is made below 80% confidence.** Every factual assertion in this report has a file:line citation or direct-output evidence in the Appendix.

## Appendix

### A. Schema of `knowledge_base/live_evaluations/*.jsonl` CANDIDATE rows

All CANDIDATE rows across 5 symbols have exactly these keys (no `trade_parameters`, no `trade_direction`):

```
align_score, candle_index_in_kz, candle_time, confidence_score,
daily_bias_confidence, daily_bias_direction, decision, framework,
h1_causing_event, h1_fib_pct, h1_poi_identified, h1_poi_type, h1_zone,
h4_aligned, kill_zone, m15_choch, m15_displacement_quality,
m15_displacement_ratio, no_trade_reason, overall_reasoning,
reasoning_price_count, reasoning_word_count, session_memory_count,
setup_grade, spread, sweep_detected, sweep_quality, sweep_type,
symbol, timestamp, wait_reason
```

### B. Source files written by V1 (read-only investigation; no code changed)

- `research/directional_concentration_audit_2026-04-24/v1_fixture_test.py` — synthetic stress test.
- `research/directional_concentration_audit_2026-04-24/v1_saturation_test.py` — saturation hypothesis tests (precedence + random walks).
- `research/directional_concentration_audit_2026-04-24/v1_historical_replay.py` — 168-bar sliding window replay over raw CSV data.

No `src/`, `config/`, `prompts/`, or production state files were modified.

### C. Key file:line citations

- `src/components/market_state.py:216-257` — `identify_structure` function.
- `src/components/market_state.py:237` — `recent_pairs = min(3, len(highs)-1, len(lows)-1)` — threshold cap.
- `src/components/market_state.py:239-247` — bullish-first if/elif/else chain.
- `src/components/market_state.py:776` — `_build_timeframe_state` calls `identify_structure(swings)` for each TF.
- `src/components/market_state.py:867-876` — D1/H4/H1/M15 all processed identically; no symmetry break per TF.
- `src/components/candidate_features_logger.py:360-373` — `c3_direction_matches` symmetric (not a source of bias).
- `src/components/candidate_features_logger.py:509-511` — `mso_h1_structure_direction` etc. are logged verbatim from MSO.
- `config/agent_config.yaml:124` — H1 lookback = 168 bars.
- `config/agent_config.yaml:129` — H1 `swing_detection_min_bars` = 2.

Git commit `436c16b "initial files"` introduced `identify_structure` in its current form; no subsequent commit has touched it.

### D. Raw replay numbers

See `v1_historical_replay.py` output, reproduced in-line in Task 7.

### E. Implications for validated numbers

If the verdict is correct, every number in CLAUDE.md's "Validated numbers" section derived from live or batch MSO-filtered data is based on a LONG-only sample:

- **Impacted:** 62% XAUUSD WR, 65% batch WR, 10.3% CAND rate, 70% OB continuation, MC 99.4% FTMO pass, 58.5% US30 WR, 75.8% USDJPY WR, 57.1% GBPJPY WR.
- **Likely NOT impacted:** findings that come from bar-level mechanical backtests independent of `identify_structure` (e.g., FVG-in-impulse cross-instrument finding — needs separate verification, outside V1 scope).
- **Effect:** The empirical edge may hold ONLY in bullish regimes on these instruments. A bearish regime has never been tested live and the system cannot detect bearish H1 structure to trade against it. This is a critical backtest-validity concern — not a verdict V1 is qualified to render. Flagging to CEO.
