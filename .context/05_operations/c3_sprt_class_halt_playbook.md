# C.3 — Class-Aware LONG-WR-Watch SPRT Halt Playbook

**Version:** 1.0 — initial Monday rollout
**Date:** April 26, 2026
**Operator:** Borhen (Kuala Lumpur, UTC+8)
**Mode:** Runtime automation active; manual checks remain an operator cross-check.
**Closes:** Deferred-master item C.3 (per-class halt thresholds)

---

## Why this exists

The pre-deploy checklist had a XAUUSD-only LONG-WR-watch SPRT halt rule (halt
if XAUUSD live LONG WR <40% in first 20 trades). Per the C.3 verifier, per-class
halt thresholds are statistically justified TODAY from the 367-trade batch +
129 XAUUSD live data — no 60-day wait required.

Class definitions (Wilson 95% CI lower bounds minus 5-10pp safety margin):

| Class       | Instruments              | n (batch) | Wilson LB | Halt at  | Early-warn at |
|-------------|--------------------------|-----------|-----------|----------|---------------|
| metals      | XAUUSD, XAGUSD            |    186    | 56.31%    | <55%     | <50%          |
| indices     | US30, US30_cash, NAS100  |    132    | 46.04%    | <40%     | <35%          |
| jpy_pairs   | USDJPY, GBPJPY            |     61    | 44.90%    | <45%     | <40%          |
| tight_fx    | (EXCLUDED)                |      5    |    —      | n/a      | n/a           |

Tight-FX (GBPUSD observer + EURUSD deferred) is EXCLUDED — n=5 batch
insufficient to calibrate threshold.

---

## How to use it Monday

### Quick Reference

```bash
# Severity exit codes:
#   0 = OK or INSUFFICIENT_DATA or CLASS_EXCLUDED — no action
#   1 = EARLY_WARNING                              — monitor + flag CEO
#   2 = HALT_TRIGGERED                             — STOP that instrument

# After each instrument's trade #10 and #20:
python -m src.safety.sprt_class_halt_check <SYMBOL> <LONG_n> <LONG_wins>
```

### Step-by-step

After each fill on a tracked instrument (XAUUSD, XAGUSD, US30_cash, NAS100,
USDJPY, GBPJPY):

1. **Update the LONG-fill counter for that instrument.** Track only LONG
   fills (SHORT fills are not counted in C.3 — they live under the existing
   per-instrument SPRT).

2. **At trade #10 and trade #20**, run::

       python -m src.safety.sprt_class_halt_check XAUUSD <LONG_n> <LONG_wins>

   Read the verdict line.

3. **Act on the verdict**:

   | Verdict             | Action                                                          |
   |---------------------|------------------------------------------------------------------|
   | `OK`                  | Continue. No CEO ping needed.                                  |
   | `EARLY_WARNING`       | Continue trading. Send the formatted Telegram message to CEO.   |
   | `HALT_TRIGGERED`      | STOP that instrument NOW. Convene CEO council.                  |
   | `INSUFFICIENT_DATA`   | Continue (n < 10). No alert needed.                             |
   | `CLASS_EXCLUDED`      | (only for GBPUSD/EURUSD/etc.) — no C.3 oversight; rely on existing SPRT. |

4. **Sending the Telegram alert** (manual mode for Monday):

   ```python
   import yaml
   from src.safety.sprt_class_halt_check import check
   from src.components.sprt_halt_alert_template import format_telegram_alert

   config = yaml.safe_load(open("config/agent_config.yaml"))
   result = check("XAUUSD", LONG_n=20, LONG_wins=10, config=config)
   print(format_telegram_alert(result))
   # Copy/paste the printed text into @gold_trader_os_bot
   ```

   The template formats the verdict with the appropriate severity glyph
   (alarm-bell for HALT, warning for EARLY_WARNING, info for OK), the
   observed WR/n, and the breached threshold.

### Stopping an instrument

If a class halt fires (e.g., metals halt → XAUUSD AND XAGUSD):

1. **Stop the orchestrator process(es) for that class**:
   ```bash
   # Read PID from the lock file, kill the process.
   python -c "import json; print(json.load(open('knowledge_base/meta/.orchestrator_XAUUSD.lock'))['pid'])"
   # ⇒ <PID>
   taskkill /F /PID <PID>     # Windows
   # Repeat for XAGUSD if a metals halt
   ```

2. **Do NOT close open positions manually** — broker-side SL/TP still
   protects them. Just stop the AI from generating new entries.

3. **Send the formatted Telegram alert to CEO** with the class halt
   verdict. CEO council decision required before resuming.

---

## Runtime automation status

- `sprt_halt.automation_enabled: true` is now wired through the orchestrator.
- Live LONG exits update `pipeline_state/sprt_class_halt_state.json`; a
  `HALT_TRIGGERED` symbol cancels pending limits and blocks new evaluation.
- Manual cross-check is one `python -m` call after trades #10 and #20 per
  instrument.

---

## How the existing per-instrument SPRT relates

| Layer                          | Source                                          | Triggered by             |
|--------------------------------|-------------------------------------------------|--------------------------|
| Existing per-instrument SPRT   | `src/components/sprt_monitor.py`                | All trades (LONG + SHORT) |
| **C.3 class-aware SPRT (NEW)**  | `src/safety/sprt_class_halt_check.py`           | First 20 LONG fills/class |
| Existing XAUUSD-only LONG-watch | `SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md` step 12 | First 20 XAUUSD LONG fills |

C.3 EXTENDS the XAUUSD-only watch to all classes. The original XAUUSD watch
remains unchanged in the pre-deploy checklist — the new layer is additive.

---

## Verifying the production config is correct

```bash
cd ~/Documents/ai-trading-agent
python -c "import yaml; c = yaml.safe_load(open('config/agent_config.yaml')); s = c['sprt_halt']; \
    print('enabled:', s['enabled']); \
    print('automation:', s['automation_enabled']); \
    print('classes:', list(s['per_class_thresholds'].keys()))"

# Expected output:
# enabled: True
# automation: False
# classes: ['metals', 'indices', 'jpy_pairs']
```

The 9-test production smoke covers the full schema:
```bash
python -m pytest tests/test_sprt_class_halt_check.py::test_production_config_has_sprt_halt_block \
                 tests/test_sprt_class_halt_check.py::test_production_config_metals_thresholds \
                 tests/test_sprt_class_halt_check.py::test_production_config_indices_thresholds \
                 tests/test_sprt_class_halt_check.py::test_production_config_jpy_thresholds \
                 tests/test_sprt_class_halt_check.py::test_production_config_tight_fx_excluded \
                 tests/test_sprt_class_halt_check.py::test_production_config_smoke_via_check -v
```

---

## Common cases worked

```bash
# Halt: XAUUSD 50% LONG WR after 20 trades
$ python -m src.safety.sprt_class_halt_check XAUUSD 20 10
HALT_TRIGGERED: HALT: XAUUSD (metals) LONG WR 50.0% < 55.0% threshold (n=20)...
# (exit code 2)

# Early warning: USDJPY 33% LONG WR after 15 trades
$ python -m src.safety.sprt_class_halt_check USDJPY 15 5
EARLY_WARNING: EARLY WARNING: USDJPY (jpy_pairs) LONG WR 33.3% < 40.0% (n=15)...
# (exit code 1)

# OK: NAS100 60% LONG WR after 20 trades (above 40% indices halt)
$ python -m src.safety.sprt_class_halt_check NAS100 20 12
OK: OK: NAS100 (indices) LONG WR 60.0% n=20 ...
# (exit code 0)

# Excluded: GBPUSD (tight-FX, observer-only)
$ python -m src.safety.sprt_class_halt_check GBPUSD 20 5
CLASS_EXCLUDED: GBPUSD not in any class ...
# (exit code 0)

# Insufficient data: only 5 LONG fills
$ python -m src.safety.sprt_class_halt_check XAUUSD 5 1
INSUFFICIENT_DATA: XAUUSD (metals): n=5 < early_warning_n=10 (need more samples)
# (exit code 0)
```

---

## Post-Monday — week 1 automation

The runtime automation hook now converts manual ops into system behavior:

1. `src/components/orchestrator.py` updates persistent first-N LONG outcome
   state through `src/components/sprt_class_halt_runtime.py`.
2. After each LONG fill closes, call
   `sprt_class_halt_check.check(...)` with the running counter.
3. On `EARLY_WARNING`: emit a queued Telegram alert.
4. On `HALT_TRIGGERED`: emit Telegram, cancel pending limits, and block new
   evaluation for the halted symbol while automation is enabled.
5. Keep `sprt_halt.automation_enabled: true` unless later tested evidence
   disables, narrows, or replaces the gate.

The stateless checker remains pure so the same threshold code path serves
both manual operator checks and automated enforcement.

---

*Playbook prepared 2026-04-26. Closes deferred-master item C.3.*
