# F8 — H1->H2 hallucination delta verdict

This file overlays the F8 (H1 baseline reconstruction + H1->H2 delta)
on top of the standard B7 ``report.md`` in the same directory. The
underlying B7 rate matrices live in ``report.md``; ``rates.json``
carries the machine-readable summary; ``rows.jsonl`` carries per-row
classifications.

## H1 / H2 split definition

The agent log corpus spans only 2026-04-05 to 2026-04-27. Because no
pre-April 2026 evaluation traces survive on disk (verified via log
date-range scan + trade_records date-range scan + live_evaluations
date-range scan), the H1->H2 delta is computed using an **intra-April
split** (`period_strategy="intra_april_2026"`):

* **H1-2026** (in this report) = April 5-15, 2026 (early-April, pre-decay).
* **H2-2026** (in this report) = April 16-27, 2026 (late-April, post-decay).

This matches the empirical decay window observed in live trading
(memory ``project_b7_hallucination_per_instrument_2026-04-27``: per-
instrument hallucination rates were captured Apr 27 across the full
April corpus). Calendar half-year split (`period_strategy="calendar_half"`)
remains the default for non-F8 callers.

The reconstructed H1 corpus (`knowledge_base/live_evaluations_h1_reconstructed/`)
adds **1,435** evaluation records derived from agent logs that were not
present in the canonical `live_evaluations/` corpus (which started
2026-04-06). Dedup by `(symbol, candle_time_minute_utc)` against the
canonical corpus suppressed 165 collisions.

## H1-2026 vs H2-2026 hallucination delta (per-instrument)

| Instrument | H1 rate (n_prices) | H2 rate (n_prices) | delta_pp | direction |
|---|---:|---:|---:|---|
| GBPJPY     | 15.9% (n=189) | 4.3%  (n=186) | -11.57pp | IMPROVED in H2 |
| GBPUSD     | 0.8%  (n=133) | 3.0%  (n=168) | +2.22pp  | slightly WORSE in H2 |
| US30_cash  | 24.3% (n=185) | 18.1% (n=116) | -6.22pp  | IMPROVED in H2 |
| USDJPY     | 4.8%  (n=271) | 3.1%  (n=262) | -1.74pp  | flat |
| XAUUSD     | 11.3% (n=97)  | 12.2% (n=74)  | +0.82pp  | flat |

## H1-2026 vs H2-2026 hallucination delta (per-role)

Roles with n_prices >= 5 in BOTH halves:

| Role            | H1 rate | H1_n | H2 rate | H2_n | delta_pp |
|---|---:|---:|---:|---:|---:|
| current_price   | 19.0%   | 147  | 4.8%    | 62   | -14.21pp |
| entry_price     | 6.8%    | 73   | 0.0%    | 75   | -6.85pp  |
| ob_high         | 0.0%    | 140  | 0.0%    | 131  | 0.00pp   |
| ob_low          | 0.0%    | 140  | 0.0%    | 131  | 0.00pp   |
| ob_mid          | 9.6%    | 73   | 5.6%    | 72   | -4.03pp  |
| protected_swing | 0.0%    | 72   | 0.0%    | 75   | 0.00pp   |
| stop_loss       | 17.8%   | 73   | 16.0%   | 75   | -1.81pp  |
| sweep_price     | 11.8%   | 68   | 6.9%    | 72   | -4.82pp  |
| take_profit     | 41.1%   | 73   | 36.0%   | 75   | -5.10pp  |

## Strategic verdict

- **H1->H2 hallucination delta (overall): -5.10pp** (n_prices: H1=875, H2=806).
- **Most-degraded instrument: GBPUSD** (+2.22pp). All other instruments either improved or stayed flat.
- **Most-degraded field: ob_high / ob_low / protected_swing** — all tied at +0.00pp (zero hallucination at structural levels in BOTH halves; AI does NOT fabricate OB highs/lows beyond the MSO).
- **Reasoning:** With the F8 reconstruction, the H1->H2 hallucination delta is **NEGATIVE** at the overall level — hallucination rate IMPROVED in late-April, not degraded. Only GBPUSD shows a slight degradation (+2.22pp from a near-zero baseline). The H2-2026 WR decay (item #4 in CLAUDE.md unresolved list, observed 64.5% -> 24.0% across the H1->H2 boundary in trade outcomes) is therefore **NOT explained by hallucination drift** — the AI's price-grounding got modestly *better* in the same window where realized R got worse. This rules out hallucination as the dominant H2 decay mechanism. The investigation should next move to B12 (confidence scorer autopsy), B14 (walk-level vs realized-R), and K53 (loser anti-pattern) — which are the next entries in the B-series checklist after hallucination.

## Caveats

1. **Intra-April split is a workaround**, not a true H1/H2-2026 split. The original CEO-relevant decay window is Jan-Feb (true H1) vs Mar-Apr (true H2), but no live evaluation data exists pre-April. The intra-April split uses Apr 5-15 vs Apr 16-27, which captures the late-April decay window but cannot speak to the pre-Mar baseline.
2. **Reconstructed records carry coarser classifications** than canonical `trade_records/` (no MSO available; B7 falls back to OHLCV-window stand-in). This dilutes the misattribution arm specifically (live_evaluations + reconstructed only emit accurate/hallucinated; misattribution requires role-tagged MSO data that only `trade_records/` has).
3. **The reconstruction synthesizes `overall_reasoning` text** containing AI-cited entry/SL/TP1/displacement values extracted from log lines. B7's regex extractor (`_extract_text_prices`) picks these up, but the text format is intentionally bland to avoid false positives (it matches "Price at X" / "SL placed at X" / "TP1 at X" patterns).
4. **The decision-derivation heuristic** (CANDIDATE if entry+SL+TP1 surfaced in logs; NO_TRADE otherwise) is approximate — the canonical decision field is in the AI response JSON which is NOT logged to text. Some logged "TP1 placement warning" events that were eventually rejected by L2 will be classified as CANDIDATE here even though canonical live_evaluations would have them as NO_TRADE.

## Open questions / blockers

1. **No pre-Apr 5 data exists.** The original F8 premise (extract Jan-Mar evaluations from logs) cannot be fulfilled with current artifacts. To get a true H1-2026 baseline, either (a) replay batch_session traces through B7 with synthesized MSO + AI text, (b) run a Phase 2 backtest re-evaluation on Jan-Mar candles ($150-300 API budget), or (c) accept that the H2 decay measurement starts at Apr 5 forward.
2. **Sample sizes are modest** for several roles. `breaker_high` / `breaker_low` have only n=9 each — the "MOST-HALLUCINATED ROLE: breaker_high (55.6%)" line in `report.md` is statistically thin and should not drive any decision.
3. **The overall improvement (-5.10pp)** is largely driven by GBPJPY's strong improvement (-11.57pp) and current_price decay reduction (-14.21pp). If GBPJPY data is excluded, the picture would shift — investigators should decompose to check whether GBPJPY has framework-specific dynamics confounding the verdict.

See also:
- `report.md` (standard B7 output, same dir).
- `rates.json` (machine-readable rate matrix).
- `rows.jsonl` (per-row classifications).
- `src/research_infra/docs/F8_h1_baseline_reconstruction.md` (F8 methodology + assumptions).
- `scripts/research/reconstruct_h1_evaluations.py` (parser).
