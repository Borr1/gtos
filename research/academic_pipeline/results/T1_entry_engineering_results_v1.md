# T1 — Entry Engineering Results v1

**Date:** 2026-04-11  
**Bonferroni threshold:** p < 0.0125  
**Practical threshold:** |ΔR| > 0.05R, |ΔWR| > 2.0pp

---

## Data Availability

- Total trades: 129
- With AI decision: 121
- With SL extracted: 121
- With M15 OHLC: 121
- With OB zone matched: 100 (XAUUSD only)

## Critical Data Finding

The batch system enters at M15 BOS confirmation, 50-100+ pts above H1 OBs.
Entry depth within OB (as designed) is not measurable for most trades.
Tests reframed to use SL_distance_ATR as zone-width proxy.

## Test Results

| Test | Status | Significant? |
|---|---|---|
| T1 Entry vs Zone | COMPLETE | See detail |
| T2 Limit Order | COMPLETE_PROXY | See detail |
| T3 Alpha Decay | COMPLETE | See detail |
| T4 Zone Width | COMPLETE | See detail |

(Full statistical output in T1_entry_engineering_analysis.py stdout log)
