# NAS100 2026-05-11 09:15 UTC Already Beyond TP, No Limit Touch

Created at: 2026-05-11T09:27:46.701575+00:00

## Observation

NAS100 produced a live candidate where the long limit entry and TP1 were far below the live tick tape at decision time. The downstream path label `continued_without_entry_touch_to_tp_area` is technically true, but the market was already beyond TP1 before the pending intent was created.

## Candidate Context

- Candidate ID: `NAS100_2026-05-11T09:15:00+00:00`
- Trade ID: `lim_NAS100_2026-05-11_091525`
- Symbol: `NAS100`
- Session: London
- Side: `LONG`
- Logged framework: `ob_retest`
- Decision time: `2026-05-11T09:15:00+00:00`
- Pending intent created: `2026-05-11T09:15:26.477099+00:00`
- Entry: `27646.20`
- Stop loss: `27597.90`
- TP1: `27718.60`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Live behavior change: none

## Tick-Tape Evidence

Source: `data/ticks/NAS100/2026-05-11.parquet`

Window from `2026-05-11T09:14:30+00:00` through `2026-05-11T09:16:00+00:00`:

- Tick count: `588`
- First tick in window: `2026-05-11T09:14:30.006000+00:00`, bid `29206.58`, ask `29208.50`, mid `29207.54`
- Last tick in window: `2026-05-11T09:15:59.990000+00:00`, bid `29206.33`, ask `29208.25`, mid `29207.29`
- Window min mid: `29205.54` at `2026-05-11T09:14:51.010000+00:00`
- Window max mid: `29211.92` at `2026-05-11T09:15:33.097000+00:00`

Window from decision time through latest inspected tick `2026-05-11T09:26:17.333000+00:00`:

- First tick after decision: `2026-05-11T09:15:01.259000+00:00`, bid `29206.71`, ask `29208.63`, mid `29207.67`
- First decision-window bid was already `1488.11` above TP1
- Minimum ask after decision: `29204.75`, still `1558.55` above entry
- Maximum bid after decision: `29227.71`
- Entry touched by side trigger: `false`
- TP1 touched by side trigger: `true`, because price was already beyond TP1

Window after pending intent creation:

- First tick after pending intent: `2026-05-11T09:15:26.525000+00:00`, bid `29208.33`, ask `29210.25`, mid `29209.29`
- First post-intent bid was already `1489.73` above TP1
- Entry touched by side trigger: `false`
- TP1 touched by side trigger: `true`, because price was already beyond TP1

## Existing Shadow Classification

Source rows:

- `shadow_logs/missed_opportunity_shadow.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- `shadow_logs/live_candidate_strategy_rollups.jsonl`
- `shadow_logs/v2b_forward_pair_resolutions.jsonl`
- `shadow_logs/prefill_delivery_path_resolutions.jsonl`
- `shadow_logs/fvg_ob_confluence_resolutions.jsonl`

Latest classifications:

- Limit entry outcome: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`
- Path label: `continued_without_entry_touch_to_tp_area`
- Candidate path status: `NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH`

## Diagnostic Note

This is not a tick-capture freshness issue. NAS100 tick capture was fresh and consistent around `29207-29212`. The candidate geometry came from a deep old H1 bullish OB around `27614.76-27646.16`, far below current market. This should be analyzed as an already-beyond-TP-at-decision / deep-limit shadow classification case, not as ordinary post-decision continuation.

## Interpretation Boundary

This artifact is observation-only. It does not change live trading behavior, validation, promotion, order handling, risk, execution, prompts, config, selectors, safety, or canaries.
