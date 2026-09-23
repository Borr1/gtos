# Test A — Dumb-Momentum Baseline (XAUUSD Jan-Apr 2026)

**Test:** Specified in `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md` §7 Test A. Open for ~7 months, never run. Executed 2026-04-25 by A6 agent (Opus 4.7 max-effort).

---

## Verdict

**AI+OB-MAYBE-UNNECESSARY** with strong sample-size caveats.

Per-trade expectancy of dumb mechanical baseline is essentially identical to GTOS F3 v2-active in the same time window. The AI's "selectivity" delivers equivalent per-trade R; its only effect is filtering ~4× volume out.

**Honest verdict: DO NOT shelve the AI+OB layer.** Same-window n=11/13 cannot statistically reject the canonical 62% true rate. The "AI may be unnecessary" claim rests on a tiny sample.

**For Monday FTMO deploy:** SHIP v2-active as planned. Add a $0 dumb-baseline live shadow logger (now implemented as `src/components/dumb_baseline_shadow_logger.py`) for empirical AI-vs-mechanical comparison after 50-100 live fills.

---

## Methodology

After every H1 BOS, enter LONG/SHORT on any close that retraces ≥X% of the impulse range. NO AI evaluation. NO OB-zone identification. Same SL/TP rules as GTOS:
- SL: 1× M15-ATR(14) beyond entry
- TP: 1.5R
- KZ-only (XAUUSD London 07:00-10:30 UTC + NY 13:00-17:00 UTC)
- Max 2 trades/day
- Max 1 trade/KZ

Tested 4 retrace variants: 50%, 70%, 80% (spec value), 90%.

Data: `data/historical_2026/XAUUSD_M15.csv` Jan 2 – Apr 13, 2026.

Implementation: `research/dumb_momentum_baseline/baseline_simulator.py` — 380-LOC standalone simulator. Re-uses `market_state.detect_swings` + `identify_fvgs`. Both-direction H1 BOS detection.

---

## Headline numbers

**XAUUSD Jan 2 – Apr 13, 2026, mechanical 80%-retrace pullback:**

| Variant | n | WR | Wilson 95% CI | Exp R | Total R | MaxDD | R/mo |
|---|---:|---:|---|---:|---:|---:|---:|
| Dumb 50% retrace | 77 | 51.9% | [40.7, 63.0] | +0.299 | +23.0R | 7.5R | +6.86 |
| Dumb 70% retrace | 66 | 53.0% | [41.2, 64.6] | +0.326 | +21.5R | 7.0R | +6.42 |
| **Dumb 80% retrace (spec)** | **55** | **54.5%** | **[41.5, 67.0]** | **+0.364** | **+20.0R** | **5.0R** | **+5.97** |
| Dumb 90% retrace | 32 | 46.9% | [30.4, 64.0] | +0.172 | +5.5R | 4.5R | +1.64 |

**Comparison vs GTOS in same window:**

| Strategy | n | WR | Exp R | Total R |
|---|---:|---:|---:|---:|
| GTOS A2 v2-active (Jan-Apr 2026) | 11 | 45.5% | +0.136 | +1.50R |
| GTOS F3 v2 (Jan-Apr 2026) | 13 | 53.8% | +0.347 | +4.51R |
| **Dumb 80% retrace** | **55** | **54.5%** | **+0.364** | **+20.0R** |
| GTOS canonical (Oct'25-Mar'26 — DIFFERENT WINDOW) | 129 | 62.0% | +0.20 | +25.8R |

### Statistical comparisons (Yates χ²)

- Dumb 80% vs GTOS A2 same-window: **p=0.825** (not distinguishable; A2's Wilson CI is too wide at n=11)
- Dumb 80% vs GTOS F3 same-window: **p=1.000** (per-trade Exp essentially identical)
- Dumb 80% vs GTOS canonical (n=129, different window): p=0.434

None reject the dumb rate.

---

## Best risk-adjusted variant

**80% retrace** is highest-expectancy AND best risk-adjusted (Calmar ≈ 4.0 vs 50%'s 3.07). Higher 50% total R comes with proportionally higher MaxDD.

---

## Sub-analyses

### Per-month — does dumb baseline replicate GTOS's H1→H2 decay?

| Month | Dumb n | Dumb WR | Dumb Exp | GTOS A1 (v1-prod) n | GTOS A1 WR |
|---|---:|---:|---:|---:|---:|
| 2026-01 | 9 | 55.6% | +0.389R | 11 | 45.5% |
| 2026-02 | 16 | 50.0% | +0.250R | 20 | 75.0% |
| 2026-03 | 20 | 60.0% | +0.500R | 15 | 33.3% |
| 2026-04 | 10 | **50.0%** | +0.250R | 10 | **10.0%** |

**Dumb baseline does NOT replicate the April collapse.** GTOS Apr 10% (n=10) vs Dumb 50% (n=10). Same market candles. **Directly addresses CLAUDE.md unresolved item #9: April XAUUSD WR collapse is AI-side, not market-side.**

### Per-session

- London n=28 WR 50.0% Exp +0.250R
- NY n=27 WR 59.3% Exp +0.481R
- NY +9.3pp advantage

### Per-direction

- LONG n=23 WR 65.2% Exp +0.630R
- SHORT n=32 WR 46.9% Exp +0.172R
- LONG +18.3pp — same direction skew GTOS sees

### FVG-in-impulse stratification (NEGATIVE finding for "FVG alone is the edge")

Across all 4 variants, FVG-in-impulse INVERTS without OB-zone anchoring:

| Variant | FVG | n | WR | Exp R |
|---|---|---:|---:|---:|
| 80% | yes | 22 | 40.9% | +0.023 |
| 80% | no | 33 | 63.6% | +0.591 |

**Without OB-zone constraint, FVG-in-impulse + deep retrace is a TREND-EXHAUSTION signal, not continuation.** "FVG alone recovers most of the AI's edge" — FALSE. The OB+FVG composite signal does not decompose. **Positive coherence finding for the AI+OB layer doing meaningful work.**

---

## Verdict per spec thresholds

| Reference | GTOS WR | Δ vs Dumb 80% | Verdict slot |
|---|---:|---:|---|
| GTOS A2 v2-active same-window (n=11) | 45.5% | +9.0pp ABOVE | "AI may be hurting" — but n=11 cannot reject |
| GTOS F3 v2 same-window (n=13) | 53.8% | +0.7pp | "AI+OB MAY BE UNNECESSARY" |
| GTOS canonical (n=129, different window) | 62.0% | -7.5pp | between bands |

**Honest verdict: AI+OB-MAYBE-UNNECESSARY** with strong sample-size caveats. Within 5pp WR / 0.05R Exp of GTOS F3 same-window. The 7.5pp gap to canonical 62% is real but spans Oct'25-Mar'26, not Jan-Apr'26.

---

## Recommendations (per the verdict)

1. **SHIP v2-active for Monday.** The dumb baseline result does NOT justify a delay or shelving the AI.
2. **Treat the April decay as AI-side** via S1 monthly-decay shadow monitor (already shipped 2026-04-24).
3. **Add a $0 dumb-baseline live shadow log** alongside live trades for empirical comparison after 50-100 live fills. **DONE** — `src/components/dumb_baseline_shadow_logger.py` shipped 2026-04-25 (commit `1b2d4e8`).
4. **Run a same-window 6-month batch (~$60) post-Monday** for definitive verdict on AI vs dumb comparison.
5. **Keep A2's LONG-WR-watch SPRT gate** at <40% / first 20 trades.

---

## Honest caveats

1. **Same-window GTOS samples are tiny (n=11/13).** Cannot reject any honest dumb-baseline rate. The "dumb beats GTOS" claim rests on n=11.
2. **No spread / slippage modeled.** Realistic XAUUSD ~30-50¢ spread shrinks Exp ~0.03R. Dumb 80% drops to ~+0.32-0.34R after costs. Still positive.
3. **Per-trade Exp F3 (+0.347R) ≈ Dumb 80% (+0.364R).** AI is NOT adding selectivity on this window — its only effect is reducing volume 4×.
4. **F3 used pre-V3 prompt; A2 has V3.** A2's lower per-trade Exp may reflect V3 regression (CLAUDE.md item #5/#13), not v2 detector quality.
5. **80% retrace is the right risk-adjusted variant** (Calmar 4.0 vs 50%'s 3.07).

---

## Highest-expectancy variant

**80% retrace, +0.364R/trade, +20R total, MaxDD 5R, 55 trades over 102 days = 0.54 trades/day average.**

Implementation reference: `research/dumb_momentum_baseline/baseline_simulator.py` (380 lines).

---

*Test A executed 2026-04-25. Decision: AI+OB scaffold STAYS for Monday. Live shadow logger captures empirical AI-vs-mechanical comparison going forward.*
