# Session 24 Handoff — Task A Shipped: OB Continuation Rolling-50 Monitor

**Session:** 24 (Apr 18, 2026 — CEO Borhen, GTOS)
**Status at close:** Task A implemented, cold-reviewed, committed. Monitor is production-ready for cron deployment. Fresh-session briefing recommended for retest-geometry study (parked, CEO-approved).

---

## What shipped in session 24 (verify via `git log -1`)

| Commit | What | Files |
|---|---|---|
| `11dee1d` | `feat(monitor): OB continuation rolling-50 monitor with small_sample gate` | `scripts/ob_continuation_monitor.py` (new, 970 lines), `tests/test_ob_continuation_monitor.py` (new, 1266 lines, 69 tests), `.context/06_decisions/001_task_a_ob_continuation_monitor_approach.md` (new ADR) |

Test suite after the commit: **1292 pass / 8 fail / 1 skip**. The 8 failures are pre-existing and unrelated: 5× `test_deployment_prep.py::TestReseedFromSessions`, 1× `test_orchestrator.py::TestNewDay::test_resets_state`, 2× `test_security_framework.py::TestWF1Protection`.

Cold-reviewed by independent Opus 4.7 reviewer (A2, no prior context, adversarial brief) with **GO verdict**. Both A1 (implementation) and A1b (test additions for `small_sample` flag) were Opus 4.7. Main thread: strategy, briefing, commit.

---

## What the monitor actually does

**Purpose:** Watch the **#1 primary decay metric** for the system's edge — the OB continuation rate. Per CLAUDE.md and the Test A rerun (n=219 BOS events, p=0.003), OB retests continue in the impulse direction ~70% of the time, +17pp over generic pullback. If that rate decays toward 50%, the edge is dying and we need to know *before* a losing streak triggers SPRT or an emergency stop.

**Design contract:**
- Standalone script (observation-only, NOT a trading gate)
- Reads M15 historical CSVs from `data/historical/` (2-year corpus)
- Detects H1 OBs via `src/components/market_state.py` primitives (SAME code as live system)
- Walks forward 12 M15 candles (3h) after each retest; classifies CONTINUED vs REVERSED with target = 1.5 × SL distance
- Maintains rolling-50 per instrument + PORTFOLIO scope
- Writes daily snapshot row to `shadow_logs/ob_continuation_daily.csv`
- Fires alarm via `src.notifications.notify_alert` (best-effort) when `rate < 60%` AND window is full (`total >= 50`)
- CLI: `--date`, `--window-size`, `--alarm-threshold`, `--data-dir`, `--dry-run`, `--symbols`
- Exit codes: `0` = all-green, `1` = alarm, `2` = unrecoverable

**Methodology match:** Byte-equivalent to `scripts/ob_retest_comprehensive.py` (the script that produced the Test A +17pp finding). A2 line-by-line verified `classify_retest`, mitigation skip, first-retest semantics, and per-symbol SL buffers against `config/agent_config.yaml`:

| Symbol | Buffer | Source |
|---|---|---|
| XAUUSD | 0.1% pct | reference formula |
| US30_cash | 3.75 abs | `config/agent_config.yaml:438` |
| USDJPY | 0.012 abs | `config/agent_config.yaml:401` |
| GBPJPY | 0.014 abs | `config/agent_config.yaml:476` |
| GBPUSD | 0.00015 abs | `config/agent_config.yaml:270` |

One documented methodology divergence (safe): monitor returns `UNRESOLVED` for OBs with <13 post-formation candles; reference silently breaks the inner loop. Test A (n=219) numbers identical under both rules since every OB there had a full horizon.

---

## The `small_sample` flag — what + why

**The problem.** When A1 first ran against `data/historical_2026/` (Jan–Apr 2026, 6.4k candles), the corpus was too sparse. Swap to wider `data/historical/` (2024-04 → 2026-03, 47k+ candles) still left thin-symbol windows. Observed retest rates per calendar day:

| Scope | Resolved retests / day | Months to fill rolling-50 |
|---|---|---|
| XAUUSD | ~0.13 | **13** |
| USDJPY | ~0.045 | **37** |
| GBPJPY | ~0.034 | **49** |
| US30_cash | ~0.022 | **74** |
| GBPUSD | ~0.011 | **148** (!) |
| PORTFOLIO | ~0.11 | **~15** |

The bottleneck is the **unmitigation funnel**, not data-age bias (I initially hypothesized age-bias; trailing-90-days data refuted it — mitigation rate 93–98% across all OB ages). Most OBs are swept through by subsequent price action before a clean retest can happen. GBPUSD retains only ~1% of its formed OBs as resolvable retests. Pulling more MT5 history helps XAUUSD/USDJPY marginally but does NOT fix GBPUSD — it's a structural feature of how GBPUSD's volatility interacts with H1 OB formation.

**CEO decision (Option 1 of 3):** Ship with `small_sample` flag.
- CSV row gets new column `insufficient_sample` (`"true"` when `total < window_size`)
- Alarm suppressed when `total < window_size` regardless of rate
- Log line gets `INSUFFICIENT_SAMPLE (n=X<Y)` suffix
- `_should_alarm(total, rate, threshold, window_size=WINDOW_SIZE)` — new trailing kwarg, default preserves behavior
- `append_daily_snapshot_row(..., insufficient_sample: bool = False)` — backwards-compatible trailing kwarg

**Why this is the right call right now:**
- Avoids spurious alarms on thin symbols (a single bad sequence on GBPUSD would otherwise trigger a false positive)
- Operators see partial windows clearly in the CSV instead of silent under-reporting
- XAUUSD is first to fill (13mo) — that's where the early-warning signal will live
- PORTFOLIO is the fastest to fill meaningfully (~15mo) and catches cross-instrument decay
- No change to `src/components/`, `prompts/`, or `config/` — zero WF-1 exposure

**Boundary contract (A2-verified):**
```
total=50, rate=59.99 → alarm ✓  (full window, below threshold)
total=50, rate=60.00 → silent ✓ (strict <, at threshold)
total=49, rate=0.00  → silent ✓ (gate beats catastrophic rate)
total=0              → silent ✓
```

---

## Unresolved findings worth investigating

### XAUUSD 126-day silent gap

During the trailing-90-days analysis, XAUUSD's last **resolved retest** was 2025-11-24, but the corpus ends 2026-03-30. That's a **126-day silent gap** with no resolved retests. Hypotheses (not tested):

1. Regime shift in XAUUSD volatility consumed every OB via mitigation
2. Our mitigation logic is over-aggressive (threshold issue in `market_state.py`)
3. H1 OB formation frequency dropped (structural)
4. Data pipeline anomaly in `data/historical/XAUUSD_M15.csv` or `XAUUSD_H1.csv` for that window

If the cause is #2 or #4, it has implications for live trading. If #1 or #3, it's still relevant — XAUUSD is the highest-weighted instrument. **Parked for later investigation, not a blocker.**

### Mitigation-bias hypothesis (refuted, documented for record)

I originally hypothesized that newly-formed OBs had artificially low retest counts because they hadn't been given time to be retested. I suggested this before checking data. **The data refuted it.** T90-formed OB mitigation rate is 93–98%, essentially identical to the full-corpus rate. Age doesn't matter — the structural funnel does.

**Lesson:** don't pass statistical hypotheses to the CEO without caveat before running the data. Documented in session memory.

---

## Approach decision record

See `.context/06_decisions/001_task_a_ob_continuation_monitor_approach.md` for the full rationale. Summary:

| Approach | What | Status | Revisit trigger |
|---|---|---|---|
| **A** | Historical-rolling monitor | **CHOSEN — shipped as `11dee1d`** | N/A |
| B | Live-events + side-file resolver | Rejected for now | If A's historical window misses short-term live decay |
| C | Build in-line resolver in `src/components/orchestrator.py` | Rejected for now | The long-term correct fix; bundle into next WF-1 window |
| D | Defer Task A; ship lower-priority items first | Rejected | N/A — methodology is proven, no reason to defer |

**This is the first entry in `.context/06_decisions/`.** Per session memory (`feedback_decision_preservation.md`), all future approach-level forks get the same ADR structure.

---

## Parked followups for future sessions

### P1 — Retest geometry study (CEO-approved, fresh session recommended)

**Question:** For every resolved CONTINUED retest, *how* did it continue? Specifically — where did price wick to before the bounce? Did it stay inside the OB or stab below it? How deep in pips and in H1 ATR units? Does this behavior drift over time?

**Why it matters:** distinguishes "price genuinely going for liquidity and coming back" (shallow wick past OB edge → profitable) from "price broke the zone and kept going" (deep wick, no bounce → losing trade). Directly informs SL buffer calibration and entry timing.

**Proposed features per resolved CONTINUED retest:**
- `mae_pips` — max adverse excursion
- `mae_atr` — MAE in H1 ATR units
- `penetration_past_ob_edge` — did it stay in the OB, or stab below?
- `time_to_mae` — M15 candles from retest to low
- `recovery_speed` — candles from MAE to first 1R
- `ob_body_size` — for normalization
- Date, symbol, session, regime label

**Proposed outputs:**
- MAE distribution per symbol (p50/p75/p90/p95)
- Rolling-median MAE quarter-over-quarter — is it growing?
- Session breakdown (London/NY/Tokyo wick depths)
- Correlation: does deeper wick predict stronger continuation?

**Practical payoff:** the p95 of MAE past OB edge directly tells us whether our 0.5 ATR SL buffer (per handoff 19) is too tight, too generous, or drifting.

**Recommendation:** dedicated fresh session (Session 25) with this as Task A. Not a drop-in for this session's tail.

### P2 — MT5 full-history pull (parked)

XAUUSD and USDJPY would benefit from an extended MT5 pull (pre-2024 history) to accelerate rolling-50 warm-up. GBPUSD structurally won't benefit — mitigation funnel is too aggressive. US30 marginal. CEO confirmed available if needed.

**When to revisit:** after 6 months of monitor running, if rolling-50 still hasn't filled for priority symbols.

### P3 — XAUUSD 126-day silent gap investigation

See "Unresolved findings" above. Should be its own scoped investigation — read-only, data-layer analysis first, then decide if the cause has downstream implications.

### P4 — GBPUSD observer cost question

CEO asked during session: GBPUSD pays ~$8–12/month in Claude API costs despite being "observer" (not trading live). Three options documented:
1. Leave as-is (~$10/mo for live observation stream)
2. Convert to local-only monitoring (skip API, run Components 1–2 + SPRT, log MSO for offline research) — requires orchestrator change, WF-1 relevant
3. Shut down entirely

**Current state:** Option 1, no change.

### P5 — Approach C (in-line resolver on `_log_ob_retest_event`)

When CEO opens a WF-1 window for orchestrator improvements, bundle the in-line OB outcome resolver so the live event log at `knowledge_base/meta/ob_retest_events_*.json` becomes self-consistent (currently writes `outcome: "PENDING"` but has no code path that updates to CONTINUED/REVERSED). Approach A's historical monitor is the belt; Approach C is the suspenders.

---

## Operations notes

### Running the monitor

```bash
# Dry-run (no CSV, no alerts)
python scripts/ob_continuation_monitor.py --dry-run

# Production cron-style invocation (recommended 6h cadence)
python scripts/ob_continuation_monitor.py

# Specific date / symbol subset
python scripts/ob_continuation_monitor.py --date 2026-04-18 --symbols XAUUSD,US30_cash

# Custom threshold for A/B testing
python scripts/ob_continuation_monitor.py --alarm-threshold 55.0
```

### Output contract

`shadow_logs/ob_continuation_daily.csv` — 10-column row per scope per UTC day:

```
date_utc, scope, window_size, window_start_date, window_end_date,
continuation_count, total_count, rate_pct, alarm_fired, insufficient_sample
```

Idempotent: running twice on the same `(date_utc, scope)` pair produces one row (the later run wins).

### Expected cron wiring

Add to watchdog's cron schedule (cadence: every 6h, aligned to UTC day boundaries):
```
0 */6 * * * cd /path/to/gtos && python scripts/ob_continuation_monitor.py >> logs/ob_continuation.log 2>&1
```
**Not yet wired** — CEO decision pending. Monitor works standalone from CLI today.

---

## Test suite evidence

Monitor-specific: `python -m pytest tests/test_ob_continuation_monitor.py -v`
- **69/69 pass in 0.55s**
- 11 test classes: `TestClassifyRetest`, `TestBuildRetestHistory`, `TestRollingWindow`, `TestComputeRate`, `TestAlarmBoundary` (with 5 new `small_sample` tests), `TestCsvAppend` (with 4 new `small_sample` tests), `TestMergeForPortfolio`, `TestRunMonitor` (with 6 new `small_sample` tests), `TestTelegramSafety`, `TestHelpers`, `TestLoadM15`, `TestMainCli`

Full suite: `python -m pytest tests/ --tb=no -q`
- **1292 passed / 8 failed / 1 skipped** in 267s
- 8 failures all pre-existing and unrelated to monitor (see Section 1)

Conftest guards (`tests/conftest.py` Layer 1+2 write guards from session 21) never fired during test run — every test uses `tmp_path` + module-ref monkeypatch pattern.

---

## What I did NOT do this session (for clarity)

- **No changes to `src/components/`, `prompts/`, `config/`.** Zero WF-1 exposure.
- **No changes to `scripts/canary_test.py`, `scripts/canary_fixtures/`.** Canary cache from Session 23 (`0c26d25`) untouched.
- **No push to remote.** Local commit only per CLAUDE.md.
- **3 pre-existing stashes preserved:** `23c083f`, `86a23fb`, `d0bbefa`. Never ran `git stash drop/clear/pop`.
- **No cron wiring.** Monitor runs from CLI; wiring is a small follow-up decision for CEO.
- **No retest-geometry study.** CEO approved this as a separate fresh session (P1 above).

---

## State at session close

- **HEAD:** `11dee1d feat(monitor): OB continuation rolling-50 monitor with small_sample gate`
- **Previous:** `1d28fab` (session 23 handoff) → `0c26d25` (canary cache)
- **Clean trees:** `src/`, `prompts/`, `config/` untouched
- **3 stashes:** all intact
- **Live system:** 5 orchestrators running (verified via `logs/gbpusd.log` through 23:30 UTC 2026-04-17)
- **Canary cache:** from session 23 — still operational per handoff 23 close
- **Next action (CEO discretion):**
  - (a) spin up Session 25 with retest-geometry study as Task A
  - (b) wire the monitor into cron (6h cadence)
  - (c) or a different priority entirely

---

## Suggested opening moves for Session 25 (if Task A = retest geometry study)

```bash
# 1. Mandatory reading
# - CLAUDE.md
# - .context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md (this file)
# - .context/00_core/quick_reference_card.md

# 2. Verify current state
git log --oneline -5   # expect 11dee1d at HEAD
git stash list         # expect 3 stashes preserved
git status --porcelain src/ tests/ prompts/ config/   # expect clean

# 3. Sanity-check the monitor still works
python -m pytest tests/test_ob_continuation_monitor.py --tb=no -q   # 69 pass

# 4. Start the retest geometry study scope doc
#    — write .context/06_decisions/002_retest_geometry_study_approach.md
#    — document options before dispatching implementation
```

---

*End of session 24 handoff. Task A monitor shipped. Retest-geometry study approved for Session 25.*
