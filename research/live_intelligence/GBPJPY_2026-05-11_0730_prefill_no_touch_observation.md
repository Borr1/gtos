# GBPJPY 2026-05-11 07:30 UTC Prefill No-Touch Observation

Created at: 2026-05-11T08:28:27.890348+00:00

## Operator Observation

Price moved up on GBPJPY before the system's long limit order level was reached.

## Candidate Context

- Candidate ID: `GBPJPY_2026-05-11T07:30:00+00:00`
- Trade ID: `lim_GBPJPY_2026-05-11_073031`
- Symbol: `GBPJPY`
- Session: London
- Side: `LONG`
- Logged framework: `ob_retest`
- Decision time: `2026-05-11T07:30:00+00:00`
- Pending intent created: `2026-05-11T07:30:31.297573+00:00`
- Entry: `213.533`
- Stop loss: `213.207`
- TP1: `214.022`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Live behavior change: none

## Tick-Tape Evidence

Source: `data/ticks/GBPJPY/2026-05-11.parquet`

Window from decision time through `2026-05-11T08:27:15.473000+00:00`:

- First tick after decision: `2026-05-11T07:30:00.440000+00:00`, bid `213.600`, ask `213.613`, mid `213.6065`
- Nearest ask to entry: `213.594` at `2026-05-11T07:32:22.280000+00:00`, still `0.061` above entry
- Nearest bid to entry: `213.576` at `2026-05-11T07:32:23.245000+00:00`, still `0.043` above entry
- Nearest mid to entry: `213.586` at `2026-05-11T07:32:22.280000+00:00`, still `0.053` above entry
- Max bid after decision: `213.779` at `2026-05-11T08:22:21.548000+00:00`, `0.246` above entry
- Max mid after decision: `213.7935` at `2026-05-11T08:22:21.548000+00:00`, `0.2605` above entry
- TP1 was not touched by bid through the inspected window; max bid remained `0.243` below TP1

Window after pending intent creation through `2026-05-11T08:27:15.473000+00:00`:

- First tick after pending intent: `2026-05-11T07:30:31.303000+00:00`, bid `213.610`, ask `213.625`, mid `213.6175`
- Ask touched entry: `false`
- Bid touched entry: `false`
- Mid touched entry: `false`
- TP1 bid touched: `false`

## Existing Shadow Classification

Source rows:

- `shadow_logs/missed_opportunity_shadow.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- `shadow_logs/pending_limit_lifecycle_audit.jsonl`
- `shadow_logs/pending_limit_lifecycle_join_backfill.jsonl`

Latest classifications:

- Limit entry outcome: `NO_ENTRY_TOUCH_BY_ASOF`
- Path label: `no_touch_stayed_above_entry`
- Pending lifecycle final state: `NO_FILL_STILL_PENDING`
- Latest lifecycle checked candle: `2026-05-11T08:15:00+00:00`
- Latest lifecycle label: `no_fill_still_pending`

## Structural Detail Preserved

The candidate row is logged as `framework=ob_retest`, while the captured setup explanation/verification cites a bullish M15 FVG fill geometry:

- H1 setup POI type: `FVG`
- H1 setup POI price level: `213.533`
- Setup explanation: qualifying unfilled bullish M15 FVG `213.570-213.496`, midpoint `213.533`, created by M15 BOS at `2026-05-11T07:00:00+00:00`
- Verification `entry_in_fvg`: `PASS`

This is preserved as source evidence only. No logic, prompt, config, execution, risk, validation, or promotion state was changed.

## Interpretation Boundary

This artifact records the live path intelligence that GBPJPY stayed above the long limit entry and moved upward before fill. It is observation-only and must not be treated as validation, promotion evidence, or a trading-behavior change by itself.
