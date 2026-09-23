# CL ZN VIX Context Control Readiness - 2026-05-04

**Status:** `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Registered Questions

| ID | Family | Question |
| --- | --- | --- |
| VIX_VXM_VOL_REGIME_CONTEXT_V1 | VIX/VXM | Does volatility-regime context explain candidate quality without becoming a direct trade validator? |
| ZN_RATES_STRESS_CONTEXT_V1 | ZN | Does rates stress context identify index/metals regimes at decision time? |
| CL_LIQUIDITY_MACRO_CONTEXT_V1 | CL | Does oil/liquidity macro stress context explain risk-on/off candidate behavior? |

## Join Rule

latest observation at or before candidate decision time; no forward-fill after the event timestamp
