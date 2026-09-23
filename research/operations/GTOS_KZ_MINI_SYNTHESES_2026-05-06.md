# GTOS KZ Mini Syntheses - 2026-05-06

Promotion posture: `NO_PROMOTION_VERDICT`

## Tokyo - USDJPY / GBPJPY - 00:00-03:00 UTC

- Production truth: No broker position, no broker pending order, and no realized PnL from the Tokyo JPY session.
- USDJPY system behavior: Repeatedly blocked before AI by the known multi-timeframe conflict pattern: lower-timeframe bullishness against D1 bearish context.
- GBPJPY system behavior: Passed deterministic direction checks on several candles, but either returned AI `NO_TRADE` or skipped before AI because no qualifying H1 POI existed.
- Market-path truth: Tokyo produced early yen-cross movement and drift, but no approved candidate path. This is no-trade market intelligence, not a missed broker execution.
- Source/orderflow context: GBPJPY still has no registered clean futures/orderflow proxy. JPY tick capture/status rows were available as operational evidence only.
- ML/shadow context: K55/strategy-shadow rows remain observational and non-promotional.
- Open issue: Continue to distinguish "system did not trade" from "market moved." Tokyo is useful no-trade discipline evidence, but not a promotion sample.

## London JPY - USDJPY / GBPJPY - 07:00-09:30 UTC

- Production truth: No broker position, no broker pending order, and no realized PnL from the London JPY window.
- USDJPY system behavior: The London sequence stayed pre-AI blocked on prescreen failures through the window. This is consistent with the D1/H4 conflict discipline seen earlier.
- GBPJPY system behavior: The system saw bullish deterministic bias in London, but most rows were `H1_POI_PRE_AI_SKIP`; the 08:45 and 09:30 rows completed AI with `COMPLETED_NO_CANDIDATE`.
- Market-path truth: GBPJPY and USDJPY participated in the broader London yen/USD move, but neither produced a production candidate or executable pending intent.
- Source/orderflow context: GBPJPY orderflow proxy gap remains a documented source limitation, not a live failure.
- ML/shadow context: K55 dependency rows were refreshed after post-writer checks and remain `NO_PROMOTION_VERDICT`.
- Open issue: The owner-visible GBPJPY/JPY movement must remain in the AI observation ledger even when GTOS produces only no-trade rows.

## London Metals / Indices - XAUUSD / XAGUSD / US30 / NAS100 - 07:00-10:30 UTC

- Production truth: `_live_monitor_iter.py` at the 10:30 and 10:45 checkpoints stayed clean with `crit=0`, `anom=0`, `pids=7`, and `open_pos=0`.
- Broad market truth: London produced a synchronized risk/metals bid after the 08:45 UTC burst. By the completed 10:45 candle, US30 and NDX100 had extended higher, XAUUSD/XAGUSD remained bid, and USDJPY stayed heavy.
- US30 path truth: `US30_cash_2026-05-06T09:15:00+00:00` was a rejected L2 LONG, not a trade. Market path later reached TP1 area without touching entry: entry `49508.05`, TP1 `49657.10`, max path high `49867.05`, no fill.
- NAS100 path truth: internal `lim_NAS100_2026-05-06_071526` remains stale/no-fill risk to monitor. It is internal candle-polled intent only, with no broker ticket and no broker pending order, while price has stayed far above original entry `27646.2`.
- XAGUSD path truth: `XAGUSD_2026-05-06T08:45:00+00:00` was rejected L2 and then adverse by path: short entry `73.971`, SL `74.249`, path `touched_entry=true`, `hit_sl=true`, max high `77.588`. This confirms the rejection was protective.
- XAUUSD anomaly truth: The 09:15 XAUUSD AI output returned candidate-shaped content with null `trade_parameters`; the analyzer demoted it to no-trade. This is a protected AI-output contract anomaly, not an execution issue.
- Source/orderflow context: US30/YM Sierra source is captured and registered; NAS100/NQ Databento trigger is eligible but disabled by env/no API key; XAGUSD/SI depth is captured but blocked by source-definition policy.
- Data-health truth: After each writer pass, the K55 dependency-signature lane needed a final refresh. Once refreshed, integrity returned `OK_WITH_DOCUMENTED_WAITING_LANES`; semantic data health stayed `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`.
- Open issue: Broad no-candidate market bursts require explicit AI ledger rows. Candidate/path logs alone are not enough to preserve the full market intelligence picture.

## London GBPUSD - 07:00-12:00 UTC

- Production truth: No broker position, no broker order, and no realized PnL. GBPUSD remained observer/no-execution.
- System behavior: GBPUSD produced London evaluation/no-candidate evidence but no production candidate, no internal pending intent, and no broker exposure.
- Market-path truth: GBPUSD participated in the broad London USD-pressure move but stayed outside production execution scope.
- Source/orderflow context: 6B source-transfer context remains research/status-only and not a live filter.
- ML/shadow context: K55 and mechanical rows remain observational only.
- Open issue: GBPUSD movement is useful cross-market context, but there is no broker-actual evidence or promotion-grade setup here.

## NY JPY / GBPUSD - 13:00-15:30 UTC

- Production truth: USDJPY, GBPJPY, and GBPUSD closed NY with no broker position, no broker pending order, and no realized PnL.
- System behavior: No executable candidate survived the production gates in these symbols.
- Market-path truth: JPY and GBPUSD moved with the broader USD/yen tape, but this was no-trade context rather than a missed production fill.
- Source/orderflow context: GBPJPY still has a documented orderflow-proxy gap; GBPUSD/6B remains source-transfer research only.
- ML/shadow context: no promotion verdict; shadow rows remain context only.

## NY Metals / Indices - XAUUSD / XAGUSD / US30 / NAS100 - 13:00-17:00 UTC

- Production truth: Final MT5 account truth at 17:10 UTC showed balance/equity/free margin `101223.36`, trade allowed, positions `0`, broker orders `0`.
- Monitor truth: `_live_monitor_iter.py` iter `769`, candle `2026-05-06T17:00:00+00:00`, returned `crit=0`, `anom=0`, `pids=1`, `open_pos=0`.
- Process truth: XAUUSD and XAGUSD shut down cleanly after NY close. One NAS100 orchestrator remained alive only because internal pending intent `lim_NAS100_2026-05-06_071526` is still being candle-polled.
- NAS100 pending truth: The NAS100 intent is internal only: no broker pending order, no MT5 ticket, no broker position. Path evidence says price reached TP area without touching entry, leaving one `NO_FILL_STILL_PENDING` lifecycle state under current 48h/new-day cancellation logic.
- Stale-data incident: After the owner-reported internet interruption, XAUUSD/XAGUSD/NAS100 PIDs and heartbeats stayed alive while MT5 reads inside those processes returned stale/bad data (`equity=0`, `D1 candles=0`). Commit `9dec9be5` fixed the source paths and the fleet was restarted safely after verifying zero broker exposure.
- Data-health truth: Final post-writer chain returned integrity `OK_WITH_DOCUMENTED_WAITING_LANES`, data health `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`, latest candidates `86`, countable opportunities `21`, duplicates `64`, same-symbol overlap `1`.
- Shadow performance truth: Countable proxy-R is not positive: live baseline `-8.5R`, pending-limit lifecycle `-6.5R`, V2/V2B OB-boundary `-7.5R`. This is `NO_PROMOTION_VERDICT`.
- Source/orderflow context: Sierra process was running/responding; latest `.depth` writes for GC/NQ/SI were around 16:29-16:31 UTC and `.scid` writes around 16:34 UTC, so source rows remain status/context only at close. Databento live remains disabled/no paid fetch.
- Open issue: Internal pending intents do not cancel solely because price reached TP area without entry. That is a design decision candidate, not a silent live patch.

## End-Of-Day Closeout - 17:10 UTC

- Final writer sequence: path follow ran after the last active row; Sierra pending enrichment ran after path follow; dependent append-only audits were refreshed; integrity and semantic health verifiers were rerun cleanly.
- Watchdog: `WATCHDOG E2E: WARN` only because the canary cache is stale under owner-approved canary skip through `2026-12-31`; watchdog/API refusal/profile checks passed.
- Tick capture: all seven daemon progress heartbeats were fresh at close, with latest progress ages under 3 minutes.
- Storage: read-only disk check required escalation and returned C: free space `58.35 GB` of `237.6 GB`.
- Final posture: monitoring complete for the day with `NO_PROMOTION_VERDICT`; no trading-logic, prompt, risk, execution, safety-gate, selector, or order-behavior promotion.
