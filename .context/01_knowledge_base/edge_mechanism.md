# Edge Mechanism — Long Form

Companion to `CLAUDE.md` § Edge Mechanism. CLAUDE.md keeps the 2-3 sentence headline; long-form mechanism + decay metrics live here.

## What the edge is

The system's edge is **OB zone precision** — the statistical tendency of price to continue in the impulse direction after revisiting the last opposing candle zone before a structural break. Mechanically (i.e., without AI filtering), the pattern runs at ~70% across 13 instruments, +19pp above shuffled-control baseline (Test A rerun, n=219 BOS, p=0.003 corrected).

It is **NOT** "reading institutional footprints" — that's a marketing frame. The actual mechanism is more boring and more durable: it exploits **stop-cascade mean-reversion to pre-cascade equilibrium**. When price sweeps a liquidity pool, retail and resting institutional stops trigger in cascade; the resulting overshoot is a temporary disequilibrium that price often corrects back to the last balanced zone (the OB) before continuing.

## Academic support

- **Osler (2000-2005)** — empirical evidence of round-number magnetism and stop-cluster cascades in FX, including return predictability after stop-runs.
- **Cont, Kukanov, Stoikov (2014)** — order-flow-imbalance models confirm that aggressive sweeps are not informative on their own; the price-impact often reverses post-cascade.
- **Moskowitz, Ooi, Pedersen (2012)** — time-series momentum study showing predictable continuation after impulse moves at multiple timeframes; consistent with our M15 → H1 OB-retest framing.

## How the edge can decay

Three known decay vectors, in priority order:

1. **Liquidity regime shift.** If broker-side liquidity provision changes (different LPs, wider spreads, different stop-cluster geometry), the cascade-and-correct pattern weakens. Hardest to detect; secondary signals trigger first.
2. **Pattern crowding.** If too many participants trade the same OB-retest signal, entries become self-fulfilling but exits become crowded — leading to faster reversal post-fill, lower TP-hit rate, more BE-stops. Detectable via OB continuation rate + average TP/SL ratio drift.
3. **Volatility regime shift.** If realized volatility drops below historical baselines, OBs become tighter and the gap between entry and SL narrows; small noise can stop trades that a higher-vol regime would let run. ATR-multiplier SL buffers (config `risk.sl_buffer_atr_multiplier`) mitigate but don't eliminate.

## Decay metrics

**Primary:** OB continuation rate (rolling 50-OB).
- **Baseline:** 70% (across 13 instruments, mechanical entries, no AI filter).
- **Alarm:** <60% on rolling-50.
- **Small-sample gate:** rolling-50 windows with <50 OBs flagged as `small_sample` to avoid false alarms during quiet periods.
- **Implementation:** `scripts/ob_continuation_monitor.py` + watchdog cron.

**Secondary:**
- **AI discrimination ratio.** If the gap between AI-selected vs AI-rejected setups narrows in realized-R terms, AI is no longer adding signal — but since AI adds ~0pp to entry WR (zone detection IS the edge, not AI selection), this is a low-priority secondary metric.
- **BOS frequency.** Drop in structural breaks per kill zone implies regime change (lower vol or lower trend). Tracked in `shadow_logs/displacement.log`.
- **Impulse quality.** Average displacement-candle range / ATR ratio. Drop implies weaker momentum, weaker post-impulse continuation.

**De-prioritized:**
- **H1 return autocorrelation.** Quarterly only. Theoretically the cleanest decay signal, but noisy at sub-quarterly cadence. Tracked manually post-batch.

## Decay observations to date

- **H1 → H2 2026 XAUUSD WR drop** (item #9 in CLAUDE.md unresolved). 64.5% n=31 → 24.0% n=25, chi-square p=0.006. Cause unknown; v1-detector LONG-only artifact contributes but does not fully explain. v2 promotion (item #11 GO) is one mitigation. Monthly-decay shadow monitor S1 (`405a75d`) live as of session 39.
- **Quarterly WR decay** (CLAUDE.md backtest-only bullet). 73.2% → 71.4% → 63.6% → 59.4% → 24.0% Q2-2026 partial. Trend pre-dates 2026; not a sudden cliff.
- **Touch-count stratification reversal** (item #8). Walk-level evidence (Track A AUC 0.65) reversed under realized-R; touch=2 best (Exp +0.30R) in Mar-Apr 2026 vs walk-level prediction. Reinforces "walk-level evidence is not predictive of realized R" rule.

## Implications for changes

- **Adding new frameworks** (e.g., `fvg_fill`, `breaker_re_entry` activated 2026-04-25): does not affect base OB-retest edge directly, but changes the candidate-generation funnel; monitor OB continuation rate to ensure the new frameworks are not pulling the AI's attention away from real OB setups.
- **Touch-count gate flips.** Loosening (`>=2` → `>=3`) re-tested in A19; rejected (touch=2 Exp +0.30R best). Keep monitoring after ≥30 production rejection events.
- **Detector v2 promotion** (item #11). Adds SHORT-side labels v1 missed. Expected to grow CANDIDATE share without reducing per-trade edge — F3 backtest verified Exp +0.407R fleet, Exp +0.333R under A2 12-slice re-run.
- **Prompt changes** (V4 SHELVED in item #13). Empirical V3 self-consistency (DP1 + γ) is 100% at temp=0; A/B variance is real prompt signal. ≤3-slice mini-backtests cannot validate prompt-architecture changes — require ≥12 slices and 60-fixture canary.

---

*Last updated: April 26, 2026. Created during CLAUDE.md prune (A.4) to keep the bootstrap doc < 30k chars.*
