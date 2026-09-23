# Directional Concentration Audit — April 2026 — TL;DR

**Date:** 2026-04-24
**Scope:** All 5 live/observer instruments — April 2026
**Auditor:** investigation agent (Opus 4.7, max effort)
**Method:** claim verification -> MSO audit -> deterministic classifier replay -> prompt + pipeline symmetry check

---

## HEADLINE

**The forensic report's "98% bullish" claim is correct in direction but understated: the actual April 2026 rate across the 4 live instruments is 100.0% LONG CANDIDATEs (112/112), and across the entire lifetime evaluation corpus the rate is 100.0% LONG (141/141).** The root cause is a **deterministic bullish bias bug** in `src/components/market_state.py::identify_structure`, not genuine regime.

---

## VERDICT (ranked by magnitude x likelihood)

1. **(b) STRUCTURAL BULLISH BIAS IN MARKET-STATE ANALYZER - CONFIRMED, high severity.** `identify_structure` at `src/components/market_state.py:216-257` uses `recent_pairs = min(3, ...)` as the threshold for "confirmed" direction and checks the bullish branch FIRST. With production H1 lookback=168, 100.0% of ~1,500 H1 closes across all 5 instruments Jan-Apr 2026 classify as bullish. Synthetic pure-downtrend data also classifies as bullish. **This is a logic bug, not a regime observation.**
2. **(a) MILD GENUINE APRIL UPTREND** - 4 of 5 instruments had net positive April returns (+0.9% to +6.8%), 58-69% bull days. This amplifies but does not explain the 100.0% concentration.
3. **(d) AI PROMPT BIAS - NOT IMPLICATED.** Prompt at `src/prompts/primary_analyzer_prompt.py` has balanced LONG (7) vs SHORT (6) / bullish (2) vs bearish (3) mentions. No asymmetric examples. The AI correctly emits `daily_bias=bearish` when fed bearish inputs (15/15 rows on GBPJPY 2026-04-10 - but C3 then fails because H1 is bullish-stuck).
4. **(c) DOWNSTREAM PIPELINE - SYMMETRIC except one minor tie-breaker.** Pre-screen, pre-AI gate, L2 verification, and permissions are all symmetric. **One cosmetic bullish tie-breaker** in `orchestrator.py:1119` (`dominant = "bullish" if bullish >= bearish else "bearish"`) lives in the alignment-context display string; does not gate decisions. Deterministic bias (`_compute_deterministic_bias`, lines 1073-1084) is symmetric and correctly falls back to `"no_bias"`.

---

## CAUSAL CHAIN (how structural bullish bias creates 100% LONG CANDIDATEs)

1. `identify_structure(swings)` uses `hh>=3 AND hl>=3` -> bullish (branch fires first).
2. With 168 H1 bars the window typically contains 20+ swings. Both bullish and bearish branches qualify simultaneously in most real markets, but **the bullish branch is checked first**.
3. Therefore MSO `timeframes["H1"].structure.direction` is essentially always bullish in production.
4. `_compute_deterministic_bias` hands D1 (sometimes bearish when lookback=30 is short enough) to the AI when D1 is directional.
5. Pre-screen blocks candles where D1 disagrees with H4 (`L2_h4_conflict_bullish_vs_d1_bearish` - 48 such rejections observed in xauusd.log Apr 13-15).
6. When the AI does see `bias=bearish`, the C3 gate fails because H1 structure (which must match direction via C3) is stuck bullish - 15/15 bearish-bias rows on GBPJPY 2026-04-10 resulted in NO_TRADE with reasoning "H1/M15 structure is bullish".
7. Net effect: the only setups that reach CANDIDATE are bullish ones.

---

## EVIDENCE (load-bearing)

| Claim | Evidence | Location |
|---|---|---|
| 112/112 April CANDIDATEs bullish | extract_candidates.py output | `research/directional_concentration_audit_2026-04-24/scripts/extract_candidates_output.txt` |
| 141/141 all-time CANDIDATEs LONG | grep on live_evaluations | verified inline |
| H1 structure 100% bullish across 1,554 XAUUSD closes etc. | production-lookback replay | `scripts/structure_full_replay_v2_output.txt` |
| Pure 200-bar downtrend -> bullish label | synthetic stickiness test S_down | `scripts/structure_stickiness.py` |
| Pure random walk -> bullish label | S_flat | same file |
| AI correctly emits bearish on D1-bearish days | GBPJPY 2026-04-10 15/15 bearish-bias rows | live_evaluations/GBPJPY/2026-04-10.jsonl |
| Pre-screen blocked 48 XAUUSD candles when D1 flipped bearish | `L2_h4_conflict_bullish_vs_d1_bearish` count | logs/xauusd.log |
| Prompt is balanced LONG/SHORT | regex count | `src/prompts/primary_analyzer_prompt.py` |

---

## RECOMMENDATION

1. **This IS a bug and should be fixed.** It is blocking ~half of addressable setups even in a mildly bullish regime - and would be catastrophic in any future bearish regime (full blind-spot, potential 0 trades until market reverses).
2. **Do not fix in this task.** The fix touches a core data-path (market_state.py -> D1/H4/H1 structure -> every downstream gate). It requires: (a) CEO approval per CLAUDE.md WF-1, (b) backtest against full 2026 data, (c) re-verification of all existing empirical numbers (`65% WR`, `62% XAUUSD WR`, etc.) which were derived over this same biased classifier - they may not survive. T7 live-sim rerun likely required.
3. **Report as a Priority-1 follow-up** to the chairman of the forensic audit. Recommend creating ADR entry.
4. **Interim mitigation options** (no code change, CEO decision):
    - Ship the fix and accept the partial-invalidation of prior empirical numbers.
    - Leave as-is and accept ~half of signal space is invisible - but only viable if forward performance remains positive and the bull-only bias is acknowledged.
    - Ship a SHORT-side validator on a shadow branch to confirm the bug manifests as predicted in live data before touching production.

Full details in `report.md`.
