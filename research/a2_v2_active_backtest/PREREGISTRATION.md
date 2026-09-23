# A2 v2-Active Backtest — Pre-Registration

**Registered:** 2026-04-25 (post-slice-completion, pre-analysis-run).
**Purpose:** Validate session-38 F3's v2-active GO verdict on the same 12
slices with the expanded A1 logger schema. Decide whether CEO should flip
`detector_version: v2_shadow → v2` for Monday 2026-04-27 FTMO paid
challenge deploy.

## Pre-registered decision criteria (frozen before running analyze.py)

These thresholds were chosen BEFORE running `analyze.py` against slice
data. Script hash logged as the first line of the generated `ANALYSIS.md`
— any post-hoc edit produces a different hash.

### GO (flip to v2 ACTIVE for Monday challenge)

ALL of:
1. `fleet_expectancy >= +0.15R` (below F3's observed +0.407 to allow for
   regression; a halving of F3's observed effect still clears this bar).
2. `XAUUSD SHORT share >= 15%` of raw CANDs (allow for some regression
   from F3's 22.8%; anything <15% means v2's promised SHORT emergence
   broke).
3. `fleet LONG WR >= 55%` (prevents LONG edge collapse; F3 saw XAUUSD
   LONG WR 45.5% n=11 which is borderline — we require fleet-level 55%+
   for safe deploy).
4. `fleet MaxDD <= 8R` (at 1% risk = 8% account DD; FTMO daily-loss is
   5% and max DD is 10%; we leave 2pp margin).

### STAY (keep v2_shadow/v1 production for Monday)

ANY of:
- Any GO criterion fails AND the stay-trigger set is active.
- `fleet_expectancy <= 0` (edge gone under v2; strong STAY signal).
- `fleet LONG WR < 45%` (LONG edge materially degraded).

### HALT / council

- `fleet LONG WR ∈ [45%, 55%]` (ambiguous window — CEO review required).
- Partial criterion failure without STAY trigger → defaults to HALT for
  conservative safety.

## Rationale for thresholds

- **+0.15R Exp floor:** F3 observed +0.407R on n=32 filled fleet-wide.
  Halving this (~+0.20R) and allowing another 0.05R regression buffer
  gives +0.15R. A v2 that produces < +0.15R is not meaningfully better
  than pre-decay historical expectations.
- **15% SHORT share:** F3 saw 22.8% XAUUSD SHORT share. v2 producing
  <15% means something broke between session 38 F3 and A2 (Wave 2.5
  fixes, prompt updates, etc.). Flagging as STAY-worthy.
- **55% LONG WR:** 62% XAUUSD batch baseline (Bonferroni-surviving).
  Requiring 55% at fleet allows for 7pp degradation. Below that
  suggests LONG collapse — unsafe for challenge deploy.
- **8R MaxDD:** 1% risk-per-trade × 8R = 8% account drawdown. FTMO
  allows 10% max DD total, 5% max daily. 8R fleet MaxDD gives us a
  2pp total-DD buffer — tight but acceptable for a paid challenge.

## Analysis script identity

The only script permitted to compute the GO/STAY/HALT verdict is
`research/a2_v2_active_backtest/analyze.py`. Its SHA256 is logged as
the first line of the generated `ANALYSIS.md`. Any subsequent edit
produces a different hash, making post-hoc tuning detectable.

Committed hash at registration (before first run):
```
[will be inserted by analyze.py on first run]
```

## Out-of-scope

- **No comparison against V4-A prompt nudge.** V4-A was DEFERRED in
  session 39 extended; this backtest does NOT revisit that question.
- **No touch-count discrimination re-test.** That question was answered
  by A1's extraction (realized-R reversed walk prediction); this
  backtest focuses solely on v2-active deploy readiness.
- **No instrument expansion.** Only XAUUSD + USDJPY (the session-38 F3
  slice set). Other 22 MT5-exported instruments come in Phase 2a AFTER
  Monday challenge validates v2.
