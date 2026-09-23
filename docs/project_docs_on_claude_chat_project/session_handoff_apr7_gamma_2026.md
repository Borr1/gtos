# Session Handoff — Gamma: Engineering Fixes
# April 7, 2026 — Targeted Pre-Live Fixes (Claude Code Session)
# For: Next Claude session(s) continuing deployment or live monitoring

---

## WHAT THIS SESSION COVERED

Three targeted engineering fixes before Monday live deployment. No new features — all evidence-backed improvements to the existing pipeline. 25 new tests written, 543 total tests passing.

### Session Flow
1. Read orchestrator pipeline, permissions, config, design doc, existing tests
2. Implemented 13:00 UTC skip filter (Task 1)
3. Implemented correlation-aware position sizing (Task 2)
4. Implemented walk-forward lock enforcement (Task 3)
5. Verified all 543 tests pass with 0 regressions

---

## TASK 1: 13:00 UTC NY Open Candle Skip Filter

**Evidence:** 0% WR on trades at exactly 13:00 UTC (n=7) + 4 converging microstructural mechanisms (flow collision, algorithmic momentum ignition, order flow reversal, PM Fix positioning). Knowledge base rates [HIGH confidence].

**What was implemented:**
- `orchestrator.py:_should_skip_first_ny_candle()` — checks if current M15 candle falls within first 15 minutes of NY session
- Called at top of `_process_candle()`, before any API calls (saves tokens)
- Logs as `SKIP_NY_OPEN_CANDLE` in candle log
- Configurable per instrument in `config/agent_config.yaml` under `instruments.{SYMBOL}.skip_first_ny_candle`

**Config:**
```yaml
instruments:
  XAUUSD:
    skip_first_ny_candle: true   # 0% WR at 13:00 UTC (n=7)
  US30_cash:
    skip_first_ny_candle: false  # No evidence for US30
```

**Files changed:**
- `src/components/orchestrator.py` — added `_should_skip_first_ny_candle()` + call in `_process_candle()`
- `config/agent_config.yaml` — added `skip_first_ny_candle` to XAUUSD and US30_cash
- `tests/test_skip_ny_open.py` (new) — 6 tests

**Tests:** Skip at 13:00, no skip at 13:15+, no skip US30, no skip London KZ, no skip when unconfigured.

---

## TASK 2: Correlation-Aware Position Sizing

**Evidence:** USDJPY and GBPJPY share JPY exposure (correlation ~0.50-0.70). Design doc: `exports/multi_instrument/correlation_sizing_design.md`.

**What was implemented:**
- `src/components/portfolio_risk.py` (new module) — `check_correlation_risk()` function
  - Takes: symbol, base_risk_pct, list of open positions, config
  - Returns: `CorrelationAdjustment` dataclass with `adjusted`, `final_risk_pct`, `reason`, `correlated_instrument`, `group_name`
  - If correlated position open: reduces risk to fit within group budget
  - If budget exhausted: returns `final_risk_pct=0.0` (skip signal)
- Integrated in orchestrator between permission gates (step 7b) and execution (step 8)
- `_get_open_positions_for_correlation()` helper queries MT5 for open positions
- Passes `risk_pct_override` to `execution.open_trade()` when adjusted
- Trade capture records the actual risk used (not base risk)

**Correlation groups (from screening):**
```yaml
correlation_groups:
  EUR_GBP:      {instruments: [EURUSD, GBPUSD],     max_combined_risk_pct: 1.5}
  AUD_NZD:      {instruments: [AUDUSD, NZDUSD],     max_combined_risk_pct: 1.5}
  US_INDICES:   {instruments: [US30_cash, US500],    max_combined_risk_pct: 1.5}
  PRECIOUS_METALS: {instruments: [XAUUSD, XAGUSD],  max_combined_risk_pct: 1.5}
  JPY_CROSSES:  {instruments: [EURJPY, GBPJPY],     max_combined_risk_pct: 1.5}
```

**Example:** USDJPY open at 1% → GBPJPY signals → reduced to 0.5% (group max 1.5%).

**Files changed:**
- `src/components/portfolio_risk.py` (new) — core logic
- `src/components/orchestrator.py` — import, `_get_open_positions_for_correlation()`, correlation check before execution
- `config/agent_config.yaml` — `correlation_groups` section
- `tests/test_portfolio_risk.py` (new) — 10 tests

**Tests:** No conflict (empty, uncorrelated, same-symbol), one-sided both directions, precious metals, budget exhaustion skip, config override, default fallback.

**Execution engine updated:** `ExecutionEngine.open_trade()` now accepts `risk_pct_override: float | None = None`. When set, it overrides the config `risk_per_trade_pct` for lot size calculation via `_calculate_lots()`. The full chain is verified end-to-end: `portfolio_risk.check_correlation_risk()` → orchestrator step 7b → `execution.open_trade(risk_pct_override=)` → `risk_amount = balance * (risk_pct / 100)` → `_calculate_lots(sl_distance, risk_amount)`.

---

## TASK 3: Walk-Forward Lock Enforcement

**Problem:** 3-month walk-forward windows defined but nothing prevents prompt changes mid-window except discipline.

**What was implemented:**
- `src/components/walk_forward.py` (new module):
  - `compute_prompt_hash()` — SHA256 of `src/prompts/primary_analyzer_prompt.py`
  - `check_walk_forward_lock()` — loads lock file, compares hash, checks expiry
  - `create_lock()` — creates lock file with window name, hash, timestamps
- Lock file: `knowledge_base/meta/walk_forward_lock.json`
  ```json
  {
    "window": "WF-1",
    "prompt_hash": "sha256...",
    "locked_at": "2026-04-07T00:00:00+00:00",
    "lock_expires": "2026-07-07T00:00:00+00:00",
    "prompt_version": "v1.0_multi_instrument"
  }
  ```
- **WARNING only, not a hard block** — allows emergency fixes
- Warning format: `⚠️ WALK-FORWARD VIOLATION: Prompt has changed during WF-1 window. Lock expires 2026-07-07.`
- Called during orchestrator `_bootstrap()` after component init
- CLI command to create/update lock:
  ```bash
  python run_agent.py --lock-walk-forward --window WF-1 --months 3
  ```

**Files changed:**
- `src/components/walk_forward.py` (new) — hash, check, create functions
- `src/components/orchestrator.py` — import + call in `_bootstrap()`
- `run_agent.py` — `--lock-walk-forward`, `--window`, `--months` CLI args
- `tests/test_walk_forward.py` (new) — 9 tests

**Tests:** Deterministic hash, content change detection, no lock passes, matching hash passes, mismatch warns, expired lock passes, missing prompt passes, lock creation with duration, nested directory creation.

---

## IMMEDIATE TODO FOR NEXT SESSION

1. **Lock the walk-forward window before Monday:**
   ```bash
   python run_agent.py --lock-walk-forward --window WF-1 --months 3
   ```

2. **Commit these changes** — all 627 tests pass, ready to commit.

---

## FILES CHANGED (SUMMARY)

| File | Change | Lines |
|------|--------|-------|
| `src/components/orchestrator.py` | Modified — skip filter, correlation integration, walk-forward check | +91 |
| `config/agent_config.yaml` | Modified — skip config, correlation groups | +22 |
| `run_agent.py` | Modified — walk-forward CLI args | +23 |
| `src/components/portfolio_risk.py` | **New** — correlation-aware sizing | ~130 |
| `src/components/walk_forward.py` | **New** — walk-forward lock enforcement | ~120 |
| `tests/test_skip_ny_open.py` | **New** — 6 tests | ~80 |
| `tests/test_portfolio_risk.py` | **New** — 10 tests | ~100 |
| `tests/test_walk_forward.py` | **New** — 9 tests | ~100 |

**Tests:** 25 new, 543 total passing, 0 regressions.
