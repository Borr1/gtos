# US30 Cash 2026-05-11 08:15 UTC Continued Without Limit Touch

Created at: 2026-05-11T08:30:49.049226+00:00

## Observation

US30_cash produced a live candidate where price was already well above both the long limit entry and the original TP1 area at decision time. The limit entry was not touched.

## Candidate Context

- Candidate ID: `US30_cash_2026-05-11T08:15:00+00:00`
- Trade ID: `lim_US30_cash_2026-05-11_081524`
- Symbol: `US30_cash`
- Session: London
- Side: `LONG`
- Logged framework: `ob_retest`
- Decision time: `2026-05-11T08:15:00+00:00`
- Pending intent created: `2026-05-11T08:15:26.123383+00:00`
- Entry: `49340.72`
- Stop loss: `49216.94`
- TP1: `49526.27`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Live behavior change: none

## Tick-Tape Evidence

Source: `data/ticks/US30_cash/2026-05-11.parquet`

Window from decision time through `2026-05-11T08:26:07.693000+00:00`:

- First tick after decision: `2026-05-11T08:15:00.942000+00:00`, bid `49589.21`, ask `49592.11`, mid `49590.66`
- First decision-window bid was already `62.94` above TP1
- Minimum ask after decision: `49585.11` at `2026-05-11T08:21:00.980000+00:00`, still `244.39` above entry
- Maximum bid after decision: `49605.21` at `2026-05-11T08:23:35.912000+00:00`
- Maximum favorable bid move from entry: `264.49`
- TP1 bid touch status: `true`
- Max bid exceeded TP1 by `78.94`

Window after pending intent creation:

- First tick after pending intent: `2026-05-11T08:15:27.911000+00:00`, bid `49592.21`, ask `49595.11`, mid `49593.66`
- First post-intent bid was already `65.94` above TP1
- Entry touched by side trigger: `false`
- TP1 touched by side trigger: `true`
- Minimum ask after pending intent: `49585.11`, still `244.39` above entry

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

## Interpretation Boundary

This artifact records a live path observation that US30_cash was already beyond the original TP1 area without first touching the long limit entry. It is observation-only and must not be treated as validation, promotion evidence, or a trading-behavior change by itself. The `continued_without_entry_touch_to_tp_area` classifier is technically true but should be interpreted with this already-beyond-TP-at-decision caveat.
