# GTOS Owner Deep-Dive Monitoring Synthesis - 2026-05-06

Status: owner-facing analysis  
Evidence date: 2026-05-05 monitoring day  
Promotion verdict: `NO_PROMOTION_VERDICT`  
Trading behavior impact: none

## Evidence Used

- `.context/LIVE_STATE.md`, regenerated before this review.
- `research/operations/AI_MARKET_MONITORING_OBSERVATIONS_2026-05-05.md`
- `research/operations/GTOS_KZ_MINI_SYNTHESIS_LONDON_2026-05-05.md`
- `research/operations/GTOS_KZ_MINI_SYNTHESIS_NY_2026-05-05.md`
- `research/operations/GTOS_DEEP_ACTIVE_MONITORING_FINAL_2026-05-05.md`
- `research/operations/GTOS_DEEP_ACTIVE_MONITORING_COMPLETION_AUDIT_2026-05-05.md`
- `research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.json`
- `research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json`
- `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_*_2026-05-05.*`
- Current JSONL rows in `shadow_logs/`

## Executive Answer

There were issues, but no issue that created broker exposure or justified a trading-logic change.

Final broker truth was clean: balance/equity `101223.36`, positions `0`, orders `0`, profit `0.0`. The final monitor returned `crit=0`, `anom=0`, `pids=2`, `open_pos=0`. The final integrity verifier returned `OK_WITH_DOCUMENTED_WAITING_LANES`; semantic health returned `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`.

Live production placed no broker trade. The system did emit two `LIMIT_PLACED` production rows, but in this codebase that means a persisted internal pending limit intent, not a native MT5 pending order. `src/components/execution.py:72-77` says pending limits are checked by the orchestrator and are candle-level polling, not native MT5 pending orders. Both May 5 internal limits reached the TP area without touching their entry, so a native broker limit resting at the same entry would also not have filled.

The real intelligence from the day is this: the system repeatedly identified correct bearish metals context, especially XAGUSD, while the live execution stack refused to chase because the required M15 structure confirmation did not exist. That produced many "direction was right but entry was missed" shadow paths. This is not an execution bug. It is a research door: a continuation/no-retrace entry model might be valuable, but it needs a separate validation lane because current GTOS is a retest/limit system.

## Final Health And Operational Issues

Clean:

- Broker positions/orders: `0/0`.
- Account balance/equity: `101223.36`.
- Profit: `0.0`.
- Final monitor: `_live_monitor_iter.py` iter `634`, `crit=0`, `anom=0`, `pids=2`, `open_pos=0`.
- Final data integrity: `OK_WITH_DOCUMENTED_WAITING_LANES`.
- Final semantic data health: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`.
- Paid data calls: `0`.
- AI/canary/execution changes from monitoring/LTO lanes: `0`.

Issues and notes:

- Direct read-only side probe for NAS100 and US30/US30_cash failed with `Terminal: Call failed`. Production tick capture stayed fresh, and broker truth stayed available. This is a source/probe issue, not a trade exposure issue.
- XAUUSD and NAS100 heartbeats remained alive at `17:05:05` after configured NY end `17:00`. Monitor did not flag this as critical/anomalous, and broker exposure was zero. This should be reviewed as process lifecycle/watchdog behavior.
- 14:15 transient heartbeat jitter on US30/XAGUSD cleared on immediate recheck.
- 16:00 boundary anomaly cleared on immediate recheck.
- Early integrity warnings occurred during active write cadence, then cleared after dependent writers/audits were rerun in the correct sequence.
- One invalid JSONL fragment in `structure_detector_divergences.jsonl` was quarantined and the shared rotating JSONL writer received a cross-process lock fix. This repaired telemetry integrity only, not trading behavior.
- Shadow observer hardening had a false active-day closeout blocker. The verifier was fixed to distinguish active-session rows from historical final-closeout evidence.
- The no-AI shadow observer process had been started before later observer hardening commits; restart is recommended to load latest observer code. This is not a production trading restart.

## Candidate And Opportunity Numbers

Final candidate corpus:

- Raw candidates in `strategy_follow_candidates.jsonl`: `76`.
- Final opportunity count health: `12` countable primary unique opportunities, `63` duplicate-active setup rows, `1` blocked active same-symbol overlap.
- Final candidate outcomes across the 76-row corpus:
  - `REJECTED_L2`: `51`
  - `REJECTED_GATE1_SAFETY`: `17`
  - `LIMIT_PLACED`: `6`
  - `REJECTED_GATE3_CIRCUIT_BREAKER`: `2`

May 5 decision-time candidates only:

- Total: `25`
- By symbol: `XAGUSD=21`, `XAUUSD=2`, `NAS100=1`, `USDJPY=1`
- By session: `London=14`, `NY=10`, `Tokyo=1`
- By side: `SHORT=24`, `LONG=1`
- By framework: `ob_retest=24`, `breaker_re_entry=1`
- By outcome:
  - `REJECTED_L2`: `22`
  - `LIMIT_PLACED`: `2`
  - `REJECTED_GATE1_SAFETY`: `1`
- Main blocker: `m15_choch_exists` on all 22 L2 rejects.

May 5 opportunity countability:

- `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`: `4`
- `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE`: `20`
- `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`: `1`

May 5 latest path outcomes:

- `continued_without_entry_touch_to_tp_area`: `21`
- `entry_touched_unresolved`: `3`
- `went_through_entry_and_continued_to_sl`: `1`
- Entry touched: `4 / 25`
- TP1 area reached: `21 / 25`
- SL reached: `1 / 25`

Interpretation: the market often moved in the candidate direction, but usually did so without retracing to the GTOS limit entry. That is a missed-continuation pattern, not a missed limit fill.

## May 5 Candidate Details

Countable primary rows:

- `USDJPY_2026-05-05T00:45:00+00:00`: Tokyo, SHORT, `breaker_re_entry`, `REJECTED_L2`, blocked by `m15_choch_exists`, path `continued_without_entry_touch_to_tp_area`, no fill.
- `NAS100_2026-05-05T07:15:00+00:00`: London, LONG, `ob_retest`, `LIMIT_PLACED`, internal pending intent only, entry/SL/TP1 `27646.2 / 27598.4 / 27717.8`, path `continued_without_entry_touch_to_tp_area`, no fill.
- `XAUUSD_2026-05-05T08:00:00+00:00`: London, SHORT, `ob_retest`, `REJECTED_GATE1_SAFETY`, entry/SL/TP1 `4559.26 / 4583.57 / 4522.87`, path `went_through_entry_and_continued_to_sl`, synthetic outcome negative. This reject protected the account.
- `XAGUSD_2026-05-05T16:30:00+00:00`: NY, SHORT, `ob_retest`, `REJECTED_L2`, newer H1 bearish OB, entry/SL/TP1 `73.222 / 74.112 / 71.887`, path `entry_touched_unresolved` by close.

Other notable May 5 rows:

- `XAUUSD_2026-05-05T08:15:00+00:00`: London, SHORT, `LIMIT_PLACED`, internal pending intent only, entry/SL/TP1 `4668.45 / 4679.89 / 4651.28`, duplicate-active setup, path `continued_without_entry_touch_to_tp_area`, no fill.
- XAGUSD 07:30 through 16:15 repeatedly emitted the older bearish H1 OB short around entry `75.471`, all `REJECTED_L2` on `m15_choch_exists`, all mostly duplicate active setup evidence.
- XAGUSD 16:30, 16:45, 17:00 shifted to newer bearish H1 OB `73.971-73.222`; 16:30 was countable, 16:45 was blocked by same-symbol overlap, 17:00 duplicate. These touched entry but were unresolved by close.

## Live Production Versus Shadow/Other Systems

Live production:

- Broker trades: `0`.
- Broker orders: `0`.
- Broker positions: `0`.
- Realized broker PnL from the day: `0`.
- Internal production limit intents: `2`, both unfilled.

No-AI / observer systems:

- `strategy_follow_evaluations.jsonl` had `373` May 5 decision-time evaluation rows.
- Evaluation stages:
  - `MSO_COMPUTED_PRE_AI`: `146`
  - `SHADOW_OBSERVER_MSO_NO_AI`: `106`
  - `PRESCREEN_FAILED_PRE_AI`: `58`
  - `AI_COMPLETED_NO_TRADE`: `44`
  - `H1_POI_PRE_AI_SKIP`: `15`
  - `NEWS_CALENDAR_BLOCKED_PRE_AI`: `4`
- Observer rows came mainly from EURUSD, GER40, and UK100. They made no AI calls, no canary calls, no execution calls, and no trade claims.

Shadow strategy/comparator systems:

- They did not trade. They produced path/proxy outcomes only.
- Across all 76 latest candidates:
  - Live baseline path proxy: `+3.5R` over `71` scored path rows.
  - Pending-limit lifecycle proxy: `+4.5R` over `72` scored rows.
  - V2B OB-boundary proxy: `+3.5R` over `70` scored rows.
- For May 5 only:
  - Live baseline path proxy: `-1.0R` over `22` scored path rows.
  - Pending-limit lifecycle proxy: `-1.0R` over `22` scored rows.
  - V2B OB-boundary proxy: `-1.0R` over `21` scored rows.
- For countable May 5 opportunities only:
  - Live baseline path proxy: `-1.0R` over `3` scored rows.
  - Pending-limit lifecycle proxy: `-1.0R` over `3` scored rows.
  - V2B OB-boundary proxy: `-1.0R` over `2` scored rows.

Interpretation: the broader 76-row corpus has some positive older path proxy evidence, but May 5 countable evidence was not positive for a literal GTOS retest/limit model. The zero broker-trade result was not obviously worse than the scored countable shadow path. It likely avoided the XAUUSD 08:00 synthetic -1R.

## Could The System Have Traded Positively But Did Not?

Yes, but only under a different strategy hypothesis, not under current approved GTOS retest execution.

Cases that do not look fixable as missed fills:

- NAS100 07:15 and XAUUSD 08:15 were unfilled because entry was not touched. Native broker limit orders at those same prices would also not have filled.
- USDJPY 00:45 was L2-rejected and later reached TP area without entry touch. Again, no limit fill.
- XAUUSD 08:00 was Gate1 safety-rejected and later reached SL before TP1. Bypassing the gate would have been bad.

Potentially positive missed-continuation door:

- 21 of 25 May 5 candidates reached TP1 area without touching the GTOS entry. This is the important signal.
- The clearest cluster is XAGUSD: repeated bearish H1 OB context during a real selloff, blocked by L2 because M15 CHoCH/BOS confirmation was absent.
- If a separate continuation/no-retrace entry model entered closer to decision time, many of these would likely have been directionally favorable. But current logs do not define the exact entry, stop, spread, slippage, or invalidation for that hypothetical. It cannot be promoted from this day.

Late-NY unresolved opportunity:

- XAGUSD 16:30 on newer OB `73.971-73.222` touched entry and was unresolved by close. This is not positive or negative yet. It is a useful fresh-OB follow-up class.

Bottom line: the fixable opportunity is not "make current limit orders native" or "remove L2." The real improvement door is to create and validate a separate continuation/timing layer for cases where the H1 OB selection is directionally right but price never retraces to the retest entry.

## Market Behavior Learned

Metals were the main story.

- XAUUSD bounced from late-London lows near `4539.89` into the `4560s`, then sold during NY from the `4580s` into the `4550s`, with a monitored low near `4553.72`, and closed the monitoring window around `4560`.
- XAGUSD recovered into the `73.7x` area during London, then trended lower into the `72.8-73.1` area in NY.
- The system repeatedly found bearish XAGUSD H1 OB context, which matched the broad direction of the tape.
- The deterministic L2 verifier kept rejecting because it did not find qualifying bearish M15 CHoCH/BOS displacement.
- Late NY, XAGUSD shifted from older OB `75.789-75.471` to newer OB `73.971-73.222`. That was a real structural update, not just the same stale setup.

Indices and FX:

- NAS100 tick capture stayed live, but direct read-only probing failed.
- US30 closed flat with no exposure; direct probe failure persisted but tick capture remained available.
- USDJPY, GBPJPY, and GBPUSD closed their windows without system trades.
- GBPUSD produced clean negative evidence: repeated London movement but pre-AI prescreen remained blocked.

System behavior:

- The system is conservative and anti-chase. It prefers no trade over entering without the required lower-timeframe structural confirmation.
- Duplicate active setup counting worked; otherwise XAGUSD would have looked like many independent opportunities. Correct countability reduced 25 May 5 candidates to 4 countable primary opportunities, 20 duplicates, and 1 overlap block.
- Current GTOS is good at preserving account safety and evidence quality. It is not yet aggressive in converting directional continuation reads into trades.

## Blockades And Limitations

Decision/execution blockades:

- `m15_choch_exists` blocked 22 May 5 candidates.
- Gate1 safety blocked XAUUSD 08:00; this protected against a later synthetic SL.
- Current limit architecture is candle-polled internal intent, not native broker pending orders.
- Current strategy has no approved continuation/no-retrace entry mode.

Source/data blockades:

- Databento live GLBX.MDP3 remains license-blocked. LTO-011 status is `WAITING_FOR_DATABENTO_LIVE_LICENSE`.
- XAGUSD/SI Sierra depth is present but blocked by `SOURCE_DEPTH_DEFINITION_BLOCKED_SI`; do not treat it as Databento-equivalent orderflow.
- Some Sierra heavy depth extraction is deferred by file-size guard/background queue.
- NAS100 and US30 direct read-only side probes failed, though production tick capture stayed usable.
- GBPJPY has no registered clean orderflow proxy.
- LTO-031 external feeds are source-blocked until legal/access path, cache schema, and publication-time/no-lookahead contracts exist.
- LTO-032 gamma/VRP is mostly source-blocked; FlashAlpha Basic is forward-context only.

Research/model blockades:

- K55 ML shadow has 76 feature rows, but inference is disabled because the registered model artifact is missing.
- K55 labels are `SYNTHETIC_PATH_CONTEXT_ONLY`, not broker-realized actual-R labels.
- V2 structural selector readiness is `NOT_READY`:
  - Countable broker-actual pairs: `0`
  - Required broker actual-R floor: `>=30`
  - Countable synthetic-path pairs: `8`
  - Countable with lifecycle truth: `4`
  - Exact selector metadata missing for all countable rows
  - No promotion dossier preregistered
- Component 3B/tool-grounding/Reflexion remains approval-blocked.

Accounting/outcome blockades:

- Broker actual-R claims are allowed only for account-history-realized rows.
- Most May 5 evidence is no-fill path context or synthetic path context.
- MT5 account history cannot reconstruct unfilled shadow alternatives or missing selector metadata.

## Open Doors

Highest-value open doors:

1. Continuation/no-retrace entry research
   - Trigger condition: H1 OB context is repeatedly right, price reaches TP area without returning to limit entry.
   - May 5 evidence: 21 of 25 candidates did this.
   - Requirement: define exact entry, SL, invalidation, spread/slippage handling, duplicate counting, and no-lookahead path scoring before any live consideration.

2. L2 CHoCH diagnostic audit
   - Do not loosen `m15_choch_exists` blindly.
   - Add/report richer diagnostics: what M15 structure existed, how close it was, whether displacement was absent, and whether rejected rows later continued without retrace.
   - Goal: learn whether the gate is correctly filtering or too strict in fast continuation regimes.

3. XAGUSD fresh-OB late-NY lane
   - The newer OB `73.971-73.222` generated an entry-touched unresolved setup near the close.
   - This should be tracked as a distinct opportunity class, not merged with the older `75.789-75.471` duplicate cluster.

4. Sierra `.scid` footprint/profile extraction
   - LTO-033 registered orderflow primitives.
   - Next value is bid/ask volume, delta, stacked imbalance, POC/HVN/LVN, and eventually VAH/VAL after source semantics are frozen.

5. Databento historical-credit replay
   - Use existing credits only, predeclared windows, cost-capped.
   - First priority: NAS100/NQ, then US30/YM, XAUUSD/GC, XAGUSD/SI, USDJPY/6J, GBPUSD/6B.
   - This can test whether live Databento would add value before spending new cash.

6. K55 model artifact
   - Feature substrate exists.
   - Do not reuse stale K54 artifacts blindly.
   - Build only after target/no-leak tests and label-quality separation are green.

7. Broker actual-R sample growth
   - This is the biggest validation bottleneck. Without more broker-realized labels, shadow ideas cannot be promoted cleanly.

8. Process lifecycle hardening
   - Review XAUUSD/NAS100 post-window heartbeats.
   - Restart no-AI shadow observer to load latest code.
   - Fix/diagnose NAS100/US30 direct probe failures.

9. Pending lifecycle clarity
   - Current internal pending intent design is documented and safe, but naming remains easy to misread.
   - Consider clearer labels like `INTERNAL_LIMIT_INTENT_SET` versus `BROKER_PENDING_ORDER_PLACED` in future telemetry.
   - Native MT5 pending orders are a design discussion, not a May 5 missed-fill fix.

## Ways To Improve The System

Immediate operations:

- Restart no-AI shadow observer at a safe moment.
- Investigate why XAUUSD/NAS100 heartbeats persisted after 17:00 while exposure stayed zero.
- Diagnose direct NAS100/US30 read-only probe failure.
- Keep the daily monitoring checklist automated or supervised so K55/source/verifier rows refresh in the correct order.
- Rename or augment `LIMIT_PLACED` telemetry to make internal-intent versus broker-order state unambiguous.

Near-term research/capture:

- Add richer L2 failure diagnostics for `m15_choch_exists`.
- Add a continuation/no-retrace shadow strategy with strict point-in-time fields.
- Make XAGUSD duplicate clusters report "directionally correct but no retrace" separately from true no-trade noise.
- Build Sierra `.scid` footprint/profile extraction around candidate windows.
- Run Sierra guarded depth enrichment during non-critical windows.

Source-unblocking:

- Implement LTO-031/LTO-032 source contracts for free/public feeds first.
- Keep FlashAlpha Basic as forward context only.
- Use Databento historical credits under the existing cost caps; do not start live Databento implicitly.
- Keep SI/XAGUSD depth blocked until source semantics are solved.

Validation/promotion discipline:

- Do not promote from duplicate rows or synthetic path labels.
- Use countable primary opportunities, broker actual-R, lifecycle truth, cost/slippage, concentration, no-leak proof, and preregistered dossiers.
- Treat May 5 as a strong research day, not a proof day.

## Bottom Line

The live system behaved safely and conservatively. It saw a real metals selloff, especially XAGUSD, but refused to chase without M15 confirmation. Live production did no broker trades and avoided at least one likely losing XAUUSD safety-rejected setup.

The strongest opportunity is not to loosen existing safety gates casually. It is to build a separate, shadow-only continuation/no-retrace module for the pattern where GTOS identifies the correct H1 OB direction but price delivers before the limit entry is touched.

The strongest blockers are still evidence quality and source access: broker actual-R sample size, Databento live licensing, SI depth semantics, V2/K55 metadata/model readiness, and process/source probe cleanup.

