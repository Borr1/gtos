# Intra-Candle Missed Setups Analysis (M1 Real Data)

## Method

Scanned **real M1 data** for patterns that form and resolve inside a single
M15 candle — setups invisible to the current M15-based evaluation.

**Data:** M1 XAUUSD (2025-12-18 08:10:00 to 2026-04-02 21:49:00)
**Sessions:** 74 London + 74 NY = 148 over 3.4 months

**Detection criteria:**
- Pattern 1: M1 price sweeps M5 swing, displaces ≥1.5x M5 ATR within 5 min, then pulls back ≥50%
- Pattern 2: M1 price touches H1 OB zone, M1 displaces ≥1.5x M5 ATR away within 5 min
- Pattern 3: Single M1 candle range ≥2x H1 ATR
- One detection per M15 candle (cooldown prevents double-counting)


## Pattern 1: Sweep + Displacement + Pullback

**M1 price sweeps M5 swing, displaces ≥1.5x M5 ATR, then pulls back. Classic SMC entry.**

| Metric | Value |
|---|---|
| Total events | 122 (35.4/month) |
| Resolved before M15 close | 75 (61%) |
| Still valid at M15 close | 47 (39%) |
| Would have continued 1.5R+ | 51 (42%) |
| **Est. missed tradeable/month** | **~9.1** |

| Kill Zone | Events | /Month | Resolved In-Candle | Would Continue |
|---|---|---|---|---|
| London | 42 | 12.2 | 24 (57%) | 17 (40%) |
| NY | 80 | 23.2 | 51 (64%) | 34 (42%) |

## Pattern 2: OB Zone Touch + Rejection

**M1 price touches H1 OB zone, then displaces away ≥1.5x M5 ATR within 5 min.**

| Metric | Value |
|---|---|
| Total events | 518 (150.2/month) |
| Resolved before M15 close | 96 (19%) |
| Still valid at M15 close | 422 (81%) |
| Would have continued 1.5R+ | 106 (20%) |
| **Est. missed tradeable/month** | **~5.7** |

| Kill Zone | Events | /Month | Resolved In-Candle | Would Continue |
|---|---|---|---|---|
| London | 248 | 71.9 | 41 (17%) | 23 (9%) |
| NY | 270 | 78.3 | 55 (20%) | 83 (31%) |

## Pattern 3: Flash Displacement

**Single M1 candle with range ≥2x H1 ATR.**

| Metric | Value |
|---|---|
| Total events | 1 (0.3/month) |
| All resolve within M1 candle | 100% |
| Avg range (H1 ATR mult) | 2.0x |

| KZ | Events | /Month |
|---|---|---|
| London | 0 | 0.0 |
| NY | 1 | 0.3 |

## Summary

```
Analysis period:                     3.4 months (M1 data)
Kill zone sessions scanned:          148

Pattern 1 (sweep+disp+pullback):     122 (35.4/month)
  Missed tradeable:                  ~9.1/month

Pattern 2 (OB touch + rejection):    518 (150.2/month)
  Missed tradeable:                  ~5.7/month

Pattern 3 (flash displacement):      1 (0.3/month)
  Missed tradeable:                  ~0.3/month

TOTAL MISSED SETUPS:                 ~15.1/month
```

## Priority: **HIGH**

Significant missed opportunity. Intra-candle monitoring (M5 or M1 evaluation trigger) should be prioritized.

## Caveats

1. **M1 data covers only 3.4 months.** Annualized estimates assume stationarity.
2. **Cooldown = 1 detection per M15 candle.** Multiple events within the same
   M15 window are collapsed to avoid overcounting.
3. **Continuation is measured from approximate entry** using M5 data after the event.
   Real execution with M1 refinement would likely yield better entries.
4. **OB zones use the simplified H1 detector**, not the AI's assessment.
5. **"Resolved before M15 close"** means TP or SL was hit in M1 data before the
   parent M15 candle closed. These are definitively missed — the system never saw them.