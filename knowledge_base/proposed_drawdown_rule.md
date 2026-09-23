# Proposed: Mechanical Drawdown Management Rule

**Status:** SPECIFICATION — Do NOT implement during WF-1
**Location:** `src/components/permissions.py` (add as new gate or extend `_gate3_circuit_breakers`)
**Date:** 2026-04-06

---

## Problem

Current system has a **binary** daily loss circuit breaker at 2% (configurable via `max_daily_loss_pct`).
There is **no graduated risk reduction** between 0% drawdown and the hard halt.
This means the system trades at full 1% risk right up until the breaker trips — no cushion.

For FTMO-style prop accounts with a 5% daily max drawdown, this is insufficient.

## What Already Exists

| Component | File | What It Does |
|---|---|---|
| Daily loss halt | `src/components/permissions.py:44-49` | Binary halt at -2% daily PnL |
| Correlation risk reducer | `src/components/portfolio_risk.py` | Caps combined risk across correlated pairs |
| Confidence multiplier | `src/components/confidence_scorer.py:88` | Adjusts size based on setup quality |
| Drawdown display | `src/prompts/primary_analyzer_prompt.py:473` | Shows drawdown to LLM (informational, not mechanical) |

**Gap:** No mechanical, code-enforced graduated risk reduction based on account drawdown depth.

---

## Proposed Rule

### Tiered Risk Reduction

```
IF account_drawdown > 3%:
    risk_per_trade = 0.5%    (reduced from 1%)
    LOG: "DRAWDOWN PROTECTION: risk reduced to 0.5%"

IF account_drawdown > 4%:
    risk_per_trade = 0.25%
    LOG: "SEVERE DRAWDOWN: risk reduced to 0.25%"

IF account_drawdown > 4.5%:
    HALT all trading
    ALERT: "CRITICAL: approaching FTMO 5% daily limit"
```

### Hysteresis (Prevents Oscillation)

```
RESTORE normal risk (1%) ONLY when:
    account_drawdown < 2%

DO NOT restore at 2.99% — that causes flip-flopping at the boundary.
```

### State Transitions

```
NORMAL (risk=1.0%)
    │
    ├── drawdown > 3% ──→ CAUTION (risk=0.5%)
    │                          │
    │                          ├── drawdown > 4% ──→ SEVERE (risk=0.25%)
    │                          │                          │
    │                          │                          ├── drawdown > 4.5% ──→ HALTED
    │                          │                          │
    │                          │                          └── drawdown < 2% ──→ NORMAL
    │                          │
    │                          └── drawdown < 2% ──→ NORMAL
    │
    └── drawdown < 2% ──→ (stays NORMAL)
```

---

## Implementation Notes

### Where to Add

Option A (preferred): New function `_drawdown_risk_adjustment()` in `permissions.py`, called from `check_permissions()` before trade execution. Returns a `risk_pct_override` rather than a denial.

Option B: Extend `_gate3_circuit_breakers()` to return the 4.5% halt, and add the graduated reduction as a separate pre-execution hook in `orchestrator.py` (where `risk_pct_override` is already plumbed — see `orchestrator.py:673`).

### Required Inputs

- `account_drawdown_pct`: Must be computed from MT5 equity vs. starting balance (not daily PnL, which resets). Use `mt5.get_account_equity()` (exists in `mt5_real.py:98`) vs. `mt5.get_account_balance()`.
- `drawdown_state`: Persisted in `session_state` dict to implement hysteresis.

### Config Keys (add to risk section)

```yaml
risk:
  drawdown_tier1_pct: 3.0        # trigger caution
  drawdown_tier1_risk: 0.5       # reduced risk %
  drawdown_tier2_pct: 4.0        # trigger severe
  drawdown_tier2_risk: 0.25      # further reduced risk %
  drawdown_halt_pct: 4.5         # full halt
  drawdown_restore_pct: 2.0      # hysteresis restore threshold
```

### Logging

Each state transition MUST log at WARNING level with:
- Previous state → New state
- Current drawdown %
- New risk_per_trade %
- Timestamp

### Testing

- Unit test: verify each tier triggers at correct threshold
- Unit test: verify hysteresis (drawdown goes 3.5% → 2.5% → stays CAUTION, not NORMAL)
- Unit test: verify 4.5% produces ExecutionDenial
- Integration test: mock equity sequence and verify risk_pct_override values

---

## Why Not Implement Now

This is a WF-1 (Walk-Forward Phase 1) system. Adding drawdown management changes position sizing behavior, which invalidates the backtest baseline. Implement after WF-1 completes and before WF-2 or live scaling.
