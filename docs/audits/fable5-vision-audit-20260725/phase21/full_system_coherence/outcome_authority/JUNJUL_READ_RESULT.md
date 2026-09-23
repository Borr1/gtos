# June/July 2026 BAR-3 confirm read — REJECT (sealed 2026-08-12)

One-shot frozen read under `JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3` (payload
`d92c80ea…`), owner-ratified BAR-3, executed on owner pre-authorization. Result
payload `13c92591…`. 42 days (June 22, July 20), zero outcome reads before the
freeze; June generated under V1_2 after three measured source-depth repairs,
July under V1; scorer bootstrap repaired by V1_3 before any scored outcome.

## Verdict: REJECT — three of four gates fail, and it is not a near-miss

| gate | value | verdict |
|---|---|---|
| discipline beats naive mixed (worst-case) | **+28.96 R** | PASS |
| pooled worst-case > −2 R | **−16.72 R** | FAIL |
| rule∘LSR positive in window | **−7.00 R** | FAIL |
| rule∘LSR positive every scored month | jun **−3.16**, jul **−3.84** | FAIL |

BAR-1 REJECT, BAR-2 REJECT (reported, not used; bootstrap p05 −35.76).

## The decomposition that matters

- **General rule**: June −0.12 R worst-case (flat); **July −16.61** (49/68
  selected, 16 positive vs 24 negative active days pooled, max daily DD 24.4 R).
- **Scoped rule∘liquidity_sweep_reclaim — the primary deployable object —
  failed in BOTH months**: 23 trades, outcomes 11 STOP / 8 TIME_STOP / 2 TARGET
  / 2 censored; June −8.41 wc, July −4.03 wc, pooled −12.44 wc. The four-month
  positive streak (jan +4.40, feb +13.64, apr +0.70, may +0.31) broke
  out-of-sample. February was the outlier, not the norm.
- **Family sign-instability recurs**: `structural_distance_extreme` was June's
  hero (+10.06) and July's disaster (−12.69). Same shape as April's autopsy.
  No family is robust (ex-top still −16.35).
- **What survives every read ever run**: the discipline-vs-naive margin —
  +18.9 (Feb), +6.6 (AprMay), **+28.96 (JunJul)**. The selection layer has
  real relative skill; the candidate population underneath it is what is
  negative out-of-window.

## Consequences

1. **No incubation ceremony.** The LSR-scoped live arming is off the table —
   its confirm failed on its own terms. The prereg discipline did its job
   before money did it instead (23 live trades at −10.4 R actual avoided).
2. **The shadow lane keeps running** (read-only, dual-lane, daily prequential
   refit as of `1c9266850`) — it is now the forward-truth instrument for any
   V2 iteration, at zero risk.
3. **Program state**: the funnel's five-month sealed record is Feb PASS /
   AprMay REJECT / JunJul REJECT. The stable positive is relative skill, not
   absolute edge. Any V2 must target the candidate population's
   non-stationarity (the post-mortem §5 feature set: regime interactions,
   completion-rate proxies, calibration), and validates on the four never-read
   2025 windows + the live forward stream.
