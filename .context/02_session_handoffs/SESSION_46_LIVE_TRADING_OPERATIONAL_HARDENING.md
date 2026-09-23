# SESSION 46 — Live Trading + Operational Hardening + Scaling Strategy

**Session window:** 2026-04-29 ~02:50 UTC → 2026-04-29 ~21:15 UTC (~18h, multi-resume)
**Day count:** Day 2 of FN $100K Phase 1 (live since 2026-04-27)
**Account at session close:** $101,233.47 / 0 positions / +1.23% above starting $100K
**Final main HEAD:** `cb28b9a` (12 merges shipped this session)

---

## TL;DR

Live monitoring session that surfaced and fixed **5 distinct operational bug classes**, two of them costly (one cost -$103 NAS100 SL, one would have blocked tomorrow's Tokyo+London respawns for 3 forex pairs). Net P&L for the day: -$103. Net P&L for the FN challenge: +$1,277 (+1.23% over 2 days). Everything is now patched, validated by two review-agent passes, and the system is ready for tomorrow's Tokyo open at 00:00 UTC.

**Critical preserved insight:** the system has **1 validated alpha** (J46-J49 portfolio policy) post-DSR retroactive sweep. The operational scaffolding (~50K LOC) is what surfaced today's bugs. Edge decay is the existential risk; scaling has to outrun it. Free-feed data sprint + alternative-broker investigation is the highest-ROI system-improvement next step (NOT more ML architecture iteration).

---

## 1. Live trading outcomes (Day 1 + Day 2)

### Day 1 — 2026-04-28 GBPJPY (+$1,380.81 / +0.738R / +1.38%)

- **Setup**: Tokyo eval at 01:30 UTC fired CANDIDATE LONG ob_retest at 215.301 limit
- **Fill**: limit triggered at 09:30:06 UTC, filled at 215.275 (broker UTC+3 = 12:30:06 broker time)
- **Exit**: closed at 15:31:06 UTC at 215.559 (end-of-NY-KZ flatten event, BUG #26/27/28/31 cascade — fix shipped same day)
- **Realized**: +$1,380.81 = +0.738R = +1.38% on $100K starting balance

### Day 2 — 2026-04-29 NAS100 (-$103.56 / -1.0167R / -0.10%)

- **Setup**: NY eval at 15:00 UTC fired CANDIDATE LONG ob_retest at 27116.90 limit
- **Fill**: limit triggered at 15:15:05 UTC, filled at 27100.02 (broker side TP overridden to 6R = 27866.32 per J46-J49)
- **The cascade of failures**:
  - 15:15:05.461: orchestrator's check_and_manage_trade polled positions_get 13ms after order_send → empty list (MT5 propagation lag) → falsely retired active_trade. **Race-guard fix shipped today (`1b7cf60`); position_confirmed=True now requires actual sighting before broker_closed accepted.**
  - 15:28 UTC: orchestrator restart adopted the orphan position
  - 16:00 UTC: NY KZ ended; "trade underwater at KZ end, 2h timeout applies" flagged
  - **17:16 UTC: WATCHDOG dead-zone path KILLED the NAS100 orch unconditionally** — 44 min before 2h-timeout (18:00 UTC) and 59 min before J46-J49 12-bar time-stop (18:15 UTC) could fire. Trade ran free at broker for ~3 hours.
  - ~19:30-20:00 UTC: price spiked to ~27260 (TP1/3R territory at 27244.92). Without orch, J46-J49 BE-on-TP1 logic could not move SL to entry.
  - 20:15:06 UTC: SL hit at 26970.57 (slipped 2.13 pts past nominal 26972.70). Loss -$103.56.
- **Counterfactual**: With watchdog active-trade-defer fix (also shipped today, `e7d2196`), orch would have stayed alive past dead zone, J46-J49 BE-on-TP1 would have moved SL to entry on the 27260 spike, and the eventual reversal would have closed at breakeven.
- **Cost of bug**: ~$95-103 (BE close vs SL hit difference)

### FN $100K Phase 1 progress

| Day | Trade | Realized | Account | % from start |
|-----|-------|---------:|--------:|-------------:|
| 0 (2026-04-27 start) | — | — | $100,000 | 0% |
| 1 (2026-04-28) | GBPJPY | +$1,380.81 | $101,380.81 | +1.38% |
| 2 (2026-04-29) | NAS100 | -$103.56 | $101,233.47 | +1.23% |

Target: +8% (reaches $108K). Currently +1.23% in 2 days. Realistic Phase 1 completion: 3-6 weeks if variance normal.

---

## 2. Today's complete fix stack (12 merges)

```
cb28b9a Merge watchdog marker UTC-coercion fix (CRITICAL — caught by review agent)
f47c2ee Merge orch graceful-shutdown cleanup + watchdog respawn-loop fix
d7e0a3a Merge backfill idempotency guards (review-agent feedback)
e7d2196 Merge watchdog active-trade defer + 2026-04-29 NAS100 SL backfill
1b7cf60 Merge post-fill MT5-propagation race guard
14f48de Merge JSONL task path-escaping fix (type=process bypasses Git Bash)
87cb2a1 Merge JSONL pretty-print VS Code tasks
be63203 Merge VS Code JSONL viewing config
0fdfa2f Merge broker_closed deal reconciliation + 2026-04-28 GBPJPY backfill
1e7fe76 Merge canary lock tests v2-cache schema fix
9213c79 Merge canary lock-wait + per-symbol dumb_baseline race
[earlier morning fixes per session-45 close]
```

### Trading-impacting fixes (5)

1. **`9213c79` canary lock-wait heartbeat refresh** (`src/components/orchestrator.py:3045-3069`) — Closes RED #13 from morning monitoring. Chunked 25s refresh during the 420s lock-acquire wait. af8637b lenience now actually works during cold-canary lock contention.
2. **`9213c79` per-symbol dumb_baseline state files** (`src/components/dumb_baseline_shadow_logger.py`) — Eliminates multi-orch atomic-rename WinError 5 race + read-modify-write data loss. 7 per-symbol files now, no shared state file races.
3. **`0fdfa2f` broker_closed deal reconciliation** (`src/components/orchestrator.py::_finalize_exit`) — When MT5 closes externally, orch queries `mt5.history_deals_get` for actual deal data rather than using detection-time bid + `datetime.now()`. Flag `broker_deal_reconciled` distinguishes reconciled vs fallback.
4. **`1b7cf60` TradeState.position_confirmed race guard** (`src/components/execution.py`) — 5s grace window after `order_send` before accepting broker_closed. Prevents the 13ms post-fill MT5-propagation race that orphaned today's NAS100 trade. Position must be sighted at least once OR 5s elapsed before retire-on-empty fires.
5. **`e7d2196` watchdog active-trade-defer** (`scripts/watchdog.ps1::Test-AnyActiveTradeAcrossFleet`) — Dead-zone cleanup path now queries MT5 `positions_get` and DEFERS the entire cleanup if any orch has an open position. Today's NAS100 SL would have been BE without this fix.

### Operational quality fixes (4)

6. **`f47c2ee` heartbeat cleanup on graceful shutdown** (orchestrator.py `_shutdown`) — Deletes per-symbol heartbeat file. Stops cosmetic cascade noise on shut-down orchs.
7. **`f47c2ee` graceful-shutdown marker** (orchestrator.py + watchdog.ps1) — Orch writes `.orch_shutdown_{SYM}.json` with `valid_until_utc`; watchdog respects it; orch boot clears stale markers.
8. **`cb28b9a` watchdog marker UTC coercion** (`scripts/watchdog.ps1`) — **CRITICAL** — caught by review agent post-merge. `[datetime]::Parse()` returns `Kind=Local` on Singapore (UTC+8), `[datetime]::UtcNow` is `Kind=Utc`, `.NET` comparison is Kind-blind. Without `.ToUniversalTime()`, marker effectively expires 8h late → would have suppressed Tokyo (00:00-03:00 UTC) AND London (07:00-09:30 UTC) respawns for USDJPY/GBPJPY/GBPUSD tomorrow.
9. **`d7e0a3a` backfill idempotency guards** — Both backfill scripts now refuse to re-run if `broker_deal_reconciled` flag already set. Prevents accidental data loss on re-execution.

### Test coverage (1)

10. **`1e7fe76` canary lock tests v2-cache schema** — Adapted 3 stale assertions to v2 cache shape (`schema_version`, `entries[<hash>].passed`).

### Developer ergonomics (3)

11. **`be63203` `87cb2a1` `14f48de` VS Code JSONL viewing config** — Workspace settings + 4 pretty-print tasks (terminal/sibling-file modes) + `scripts/view_jsonl.py` helper. `Ctrl+Shift+B` on any `.jsonl` opens pretty-printed view. `type=process` bypasses Git Bash's path-escaping.

### Data corrections (2)

12. **`0fdfa2f` 2026-04-28 GBPJPY backfill**: `daily_pnl.json` + trade_record + j46_j49_shadow_outcomes corrected to actual +0.738R close (was -0.0365R from false-close artifact).
13. **`e7d2196` 2026-04-29 NAS100 backfill**: same 3 artifacts corrected to actual -1.0167R / -$103.56 SL hit (was -0.0168R from race-condition artifact).

### Test results

**302/302 tests pass** across `test_execution.py`, `test_orchestrator.py`, `test_exit_wiring.py`, `test_j46_j49_policy.py`, `test_notifications.py`, `test_dumb_baseline_shadow_logger.py`, `test_orchestrator_canary_lock.py`, `test_canary_symbol_stagger.py`, `test_heartbeat_monitor.py`. **`tests/test_canary_cache.py::TestOrchestratorIntegration` excluded** per memory `feedback_canary_integration_tests_burn_real_api` (broken mocks fire real API; cost $42 yesterday).

---

## 3. Bug classes discovered + resolved this session

| # | Class | Discovery | Cost | Fix |
|---|-------|-----------|-----:|-----|
| 1 | Post-fill MT5-propagation race (13ms) | NAS100 fill 15:15:05 → false-close 15:15:05.461 | -$103 (today) | `1b7cf60` race guard |
| 2 | broker_closed exit using detection-time bid | trade_record corruption on yesterday GBPJPY + today NAS100 | data only | `0fdfa2f` deal reconciliation |
| 3 | Watchdog dead-zone kill of orch with active trade | NAS100 17:16 UTC kill cost the trade-mgmt window | (root cause of #1's $103) | `e7d2196` active-trade defer |
| 4 | Heartbeat cascade noise on shut-down orchs | observed 17:35 UTC after USDJPY/GBPJPY/GBPUSD shutdown | cosmetic | `f47c2ee` heartbeat cleanup |
| 5 | Watchdog respawn-loop on shut-down orchs | every 15min waste $0.50/day cold canaries | $15/month | `f47c2ee` shutdown marker |
| 6 | Watchdog marker UTC vs Local timezone bug | review agent caught post-merge | would have blocked Tokyo + London | `cb28b9a` `.ToUniversalTime()` |

### Catalogued but DEFERRED to next session

- **M5 SL refinement direction-sign bug** — proposes SL on wrong side (e.g., for LONG trades, SL above entry instead of below). Falls back to M15 SL gracefully so no trading impact, but fires every cycle as warning noise. Read `src/components/m5_refinement.py` line ~`m5 SL outside valid range`. **Owner: NEXT SESSION.**

### Catalogued + accepted (not worth fixing this challenge)

- **AI hallucination class #11 (m15_choch_fab) on GBPUSD** — fired 14× today, all caught by L2 deterministic gate. Wasted ~$0.70/day in API. Not blocking. Per CLAUDE.md IGNORE list.
- **CAL_STALE warnings** — operator-maintained calendar files; queue path delivers fine.
- **Telegram direct-urllib SSL errors** — queue path works.
- **CUSUM_CR up alarm** — observational.

---

## 4. Critical review-agent findings (saved scaling)

This session ran TWO review-agent dispatches:

### Review agent #1 (after first 8 merges)

Verdict: **SHIP-READY** with 3 non-blocking observations:
- Backfill scripts lack idempotency guards → **FIXED in `d7e0a3a`**
- `get_history_deals` time-type changed from int → datetime → verified safe (only `_finalize_exit` uses `time` field; other callers only use `profit`)
- Race-guard 5s window hardcoded → not blocking, future config knob

### Review agent #2 (after orch shutdown fixes)

Verdict: **NEEDS-FIX** — caught the timezone bug (would have blocked tomorrow's Tokyo + London respawns):

```
[datetime]::Parse($markerData.valid_until_utc) returns Kind=Local on Singapore.
[datetime]::UtcNow returns Kind=Utc.
.NET DateTime comparison is Kind-blind (compares ticks).
On UTC+8 host: marker effectively expires 8h late.
Effect: USDJPY/GBPJPY/GBPUSD shutdown markers from 15:31 UTC today would
have suppressed respawn through 07:45 UTC tomorrow — straight through
Tokyo (00:00-03:00) and London (07:00-09:30) for 3 forex pairs.
```

Fixed in `cb28b9a` with `.ToUniversalTime()` coercion. Verified via synthetic boundary test.

**Lesson preserved**: cross-component PowerShell + Python timezone interaction is a hidden bug class. Recommend Pester/pytest+pwsh harness as future test investment.

---

## 5. Edge analysis (what's actually validated)

### Survives DSR retroactive sweep at N=200 (post-2026-04-29 audit)

Per memory `project_dsr_retroactive_sweep_2026-04-29`:

| Alpha | Effect | DSR-corrected p | Status |
|-------|-------|----------------:|--------|
| **J46-J49 portfolio policy** | +0.742R/trade @ n=321 | 1.23e-7 (5.16σ post-deflation) | ✅ Live |
| **S79 risk policy uniform_fn 2.0%** | +26.5pp P(pass FN) @ n=1000 MC | <2.22e-16 | ✅ Live |
| **Mechanical OB cross-period 2022-2023** | z=10.5 | (separate test) | ✅ Mechanism real |

### FAILS DSR (no longer cite as "validated")

- K54 v1/v2/v3/v4 ML classifiers (all FAILED at n=528 cohort)
- Per-instrument WR claims (XAUUSD 62%, USDJPY 76%, US30 58%, GBPJPY 57%)
- +0.200R expectancy claim
- FVG-in-impulse signal (direction REVERSED in K52)
- OB advantage relative claim +17pp (mechanism survives separately, headline overfit)

### Today's live data points

- 2 trades in 2 days, 1 win 1 loss
- Net +$1,277.25 (+1.28%)
- Sample size too small to update any DSR-validated number

---

## 6. Honest expectancy + scaling timeline (per operator's question)

### Realistic per-account economics on $100K funded

| Scenario | Conservative | Central | Optimistic |
|----------|---|---|---|
| Win rate | 52% | 56% | 63% |
| Expectancy/trade | +0.25R | +0.45R | +0.85R |
| Trades/month | 12 | 17 | 25 |
| Risk per trade (avg) | 1.0% | 1.3% | 1.8% |
| **Monthly gross %** | +3% | +9.9% | +38% |
| **Monthly net (post 80% split)** | $2.4K | $7.9K | $30K |

**Central estimate: ~$5K-$8K net per $100K funded per month.**

### Phase timeline (realistic)

| Phase | Target | Realistic duration |
|-------|-------:|-------------------|
| Phase 1 ($100K → +8%) | +8% | **3-6 weeks** |
| Phase 2 ($100K → +5%) | +5% | **2-4 weeks** |
| First payout (post-funded) | — | ~14 days |
| **Start to first payout** | — | **8-14 weeks (~2-3 months)** |

### Scaling math

| Aggregate funded | Net monthly (7% × 80%) | Realistic timeline |
|---|---:|---|
| $100K (1 account) | $5,600 | Month 2-3 |
| $500K (5 accounts scaled) | $28K | Month 6-9 |
| $1M (FN scaling cap) | $56K | Month 9-12 |
| $5M (multi-firm + scaling programs) | $280K | Month 12-24 |
| $10M+ (institutional) | $560K+ | Year 2-3+ |

**Hundreds of thousands per month: achievable at $3-5M aggregate, ~12-24 months.**
**Millions per month: $20M+ aggregate, year 3+, OR algorithm licensing/institutional.**

### Edge-decay clock (the actual existential risk)

Per memory `project_f11_ob_zone_decay_velocity_pinned`:
- OB zone advantage decay: +16.8pp pre-2026 → +12.1pp H1-2026 → +4.6pp H2-2026 (~75% drop in 9 months)
- Quarterly WR decay: 73.2% → 71.4% → 63.6% → 59.4% (sustained)
- **Decay rate ≈ 2-4pp WR per quarter** on the OB-mechanism alpha
- Decay-dominant ~78% (genuine), methodology contribution ~22%

**Implication**: scaling has to outrun decay. The current edge that pays $5K/month per $100K may pay $2K/month per $100K in 12 months.

---

## 7. System-improvement strategy (per operator's question on scaling)

### What's WASTING effort (skip these)

- ❌ Iterating K54 v5/v6 ML architectures — burned ~500 trials of DSR budget on n=528 cohort; Phase 2 verdict "STOP architecture iteration"
- ❌ Buying Databento — Forensic Agent D found 12-month ROI = -91% on substrate-immune candidates
- ❌ Building dashboards/visualization tooling — premature
- ❌ Iterating prompt versions for AI hallucination class #11 — caught by L2; $0.70/day cost is rounding error

### Tier 1 — HIGHEST ROI

1. **Free-feed integration sprint** (10 engineering days, $0 cost):
   - CFTC commitments-of-traders (institutional positioning)
   - FRED macro economic data
   - WGC physical demand
   - LBMA precious-metals fix prices
   - CBOE-GEX (options gamma exposure)
   - Per Forensic Agent J: top-3 calendar features already identified
   - **Each is a SUBSTRATE-IMMUNE alpha vector — doesn't require LOB data we don't have**
   - Potential payoff: 2-3 NEW alpha candidates entering validation

2. **Alternative-broker pre-2024 data investigation** (3-5 days, $50-100/mo broker access):
   - Q1.6 from CLAUDE.md Phase 3 priority
   - Unblocks pre-2024 GBPJPY + US30 cohort: n=528 → n≥5,000
   - The ONLY way K54-class architectures could meaningfully validate
   - Either validates ML research direction or definitively closes it

3. **Live monitoring + targeted bug-fixing** (continuous):
   - Today proved this — 5 bug classes surfaced + 6 fixed
   - Each live trade adds 1 to validation cohort
   - After 30 live trades: re-run DSR on AI baseline
   - After 100 live trades: validate per-instrument WR

### Tier 2 — Parallel after Tier 1

4. **Substrate-immune Renaissance candidates** — calendar/regime/behavioral alphas; 99 of 178 candidates substrate-immune per Agent D
5. **Operational hardening post-FN-Phase-1** — M5 SL bug, cross-component test harness

### Tier 3 — Defer

6. ML architecture iteration — wait until cohort hits n≥5,000
7. Paid data feeds — only if free-feed sprint insufficient

### Realistic timeline

| Month | System work | Expected outcome |
|-------|------------|------------------|
| 1-2 | Free-feed sprint + alternative broker + live bug-fixing | 1-2 new alpha candidates entering validation |
| 2-3 | First Tier 1 alpha hits n=100 live trades | DSR-validated 2-alpha portfolio |
| 3-6 | Substrate-immune candidates | 1-2 more alphas in validation |
| 6-9 | Operational hardening, cohort expansion | n≥1000 cohort |
| 9-12 | Re-evaluate ML architecture WITH expanded cohort | Real chance K-series ML works |
| 12+ | Add new substrate-immune alphas | 4-6 alphas total |

After 12 months: maybe 3-4 validated alphas instead of 1. Trade frequency could double or triple. Decay risk diversified.

### The single most underrated action

**Document every live trade rigorously** — setup, AI reasoning, L2 details, fill price, MFE/MAE, hold time, post-mortem note. Today's `j46_j49_shadow_outcomes.jsonl` and `trade_records/` already capture most of this. Just need: 5-min post-mortem appended per trade. After 6 months → bullet-proof live cohort more valuable than 6 months of paper research.

---

## 8. Operational state for next session

### Account state (final)

- Balance: **$101,233.47**
- Equity: **$101,233.47**
- Open positions: **0**
- Pending orders: **0**
- Daily P&L (2026-04-29): **-$103.56 (-0.10%)**
- FN Phase 1 progress: **+1.23%** of +8% target

### Current code state

- Main HEAD: **`cb28b9a`**
- All 12 fixes from today's session merged + tested (302/302 pass)
- Working tree: clean except expected runtime state files

### Active running processes (in dead zone, expected)

- 0 orchestrators (all gracefully shut down at end of NY)
- 0 heartbeat_monitor (killed by previous dead-zone tick before fix shipped)
- Per-symbol heartbeat files: deleted by Bug 1 fix on shutdown (expected for shut-down orchs)
- Graceful-shutdown markers: present for orchs that shut down gracefully (will be honored by next watchdog tick)

### What's expected to happen overnight (UTC)

| UTC | Local SGT | Event |
|-----|-----------|-------|
| 23:45 | 07:45 | Watchdog dead zone ENDS. Watchdog respawns orchestrators. |
| 23:46+ | 07:46+ | Markers expire (UTC-correctly per `cb28b9a`); respawns proceed for all 7 instruments. |
| 00:00 | 08:00 | **Tokyo opens** for USDJPY/GBPJPY. Cache rolls (date_utc changes); cold canary fires. |
| 00:00-00:15 | — | Cold canary window. With today's `9213c79` lock-wait + per-symbol dumb_baseline fixes, no cascade expected. |
| 00:15+ | — | Live evaluation cycle begins. |

### What CRITICALLY needs to be verified at next session start

1. **All 7 orchs respawned at 23:45 UTC** with new HEAD `cb28b9a` code
2. **No watchdog "GRACEFUL SHUTDOWN MARKER active" log line for ANY orch** — markers should have expired correctly per UTC fix
3. **Tokyo cold canary fires WITHOUT cascade** — Fix 1 (lock-wait refresh) + Fix 5 (no false-close) should hold
4. **No false broker_closed events** in the first hour of Tokyo trading

### What's parked for fresh session

1. **M5 SL refinement direction-sign bug** — top priority for next session
2. **Live monitoring of 2026-04-30 trading day** — Tokyo + London + NY observation
3. **Optional: Pester/pytest+pwsh harness** for cross-component PowerShell+Python timezone tests (review agent recommendation)

---

## 9. Memories saved this session

New memories created (cross-session retrievable):

- `project_session_46_close_live_trading_hardening_2026-04-29` — this handoff entry
- `project_2026-04-29_nas100_sl_root_cause` — the 5-bug cascade + watchdog dead-zone kill
- `feedback_review_agent_caught_critical_timezone_bug_2026-04-29` — the .NET DateTime Kind=Local vs Kind=Utc lesson
- `project_scaling_strategy_realistic_timeline_2026-04-29` — operator's scaling discussion + system-improvement priorities

(See `MEMORY.md` index for entries.)

---

## 10. Open questions for next session

1. **Does the `cb28b9a` UTC coercion actually hold across the 23:45 UTC boundary?** Synthetic test passed, but live verification is the only proof.
2. **Will tomorrow's Tokyo orchs trigger any RED?** Cache rolls, all canaries cold-fire, all today's fixes get their first live exercise simultaneously.
3. **Do USDJPY/GBPJPY produce CANDs in Tokyo?** They're the highest-frequency Tokyo instruments. Today no Tokyo trades fired.
4. **Is M5 SL refinement bug fixable safely during Phase 1, or should it wait?** Decision-quality vs operational-quality trade-off.
5. **When does free-feed integration sprint kick off?** 10-engineering-day commitment — when does the operator have bandwidth?

---

## 11. Honest verdict from this session

System weathered a real loss (-$103) without panic. Account remains +1.23% above start of FN $100K Phase 1. Today caught more bugs in 18 hours than the previous month combined — that's surfaced fragility, not introduced fragility. The discipline of validating fixes via review agents caught a CRITICAL timezone bug that would have blocked tomorrow's trading.

The system has 1 validated alpha + extensive operational scaffolding. Path to scaling is multi-account capital + new alpha validation (free-feed sprint priority). Edge decay is real and measured at ~2-4pp WR per quarter. Window to scale aggressively is finite but real.

**Don't iterate ML architecture more.** Cohort expansion + new data sources is the actual highest-ROI move.

---

*Session 46 closed 2026-04-29 ~21:15 UTC. Next session opens with: M5 SL bug investigation + live monitoring of 2026-04-30 trading day. Account safe at $101,233.47, all fixes shipped + validated, ready for Tokyo open at 00:00 UTC.*
