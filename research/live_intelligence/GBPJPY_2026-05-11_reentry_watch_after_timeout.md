# GBPJPY 2026-05-11 Re-entry Watch After Timeout Close

Created: 2026-05-11T11:36:00Z

## Context

The GBPJPY London 07:30 candidate filled late at 2026-05-11T10:45:05Z and was
closed by the live system's session-end `timeout_2h` rule at
2026-05-11T11:30:06Z for about +0.615R.

The operator requested that the same setup be watched for a possible return to
the original zone.

## Saved Setup Levels

- Symbol: GBPJPY
- Direction: LONG
- Candidate: `GBPJPY_2026-05-11T07:30:00+00:00`
- Internal intent: `lim_GBPJPY_2026-05-11_073031`
- Qualifying framework in reasoning: `fvg_fill`
- FVG zone from AI reasoning: 213.496-213.570
- Original midpoint/entry: 213.533
- Original stop loss: 213.207
- Original AI TP1: 214.022
- Prior actual fill: 213.594
- Prior J46-J49 broker TP from actual fill: 215.916

## Watch Rules

Observation only. Monitor live GBPJPY ticks for:

- Zone touch: ask <= 213.570.
- Midpoint retest: ask <= 213.533.
- Invalidation pressure: bid approaching 213.207.

No order placement, order modification, risk change, config change, prompt
change, or broker/account action was made from this note.

## Live Watch Tape

- 2026-05-11T11:35:16Z: bid 213.804, ask 213.821, 0.251 above zone top.
- 2026-05-11T11:39:01Z: bid 213.808, ask 213.820, 0.250 above zone top.
- 2026-05-11T11:46:34Z: bid 213.848, ask 213.862, 0.292 above zone top.
- 2026-05-11T11:53:30Z: bid 213.777, ask 213.789, 0.219 above zone top.
- 2026-05-11T11:54:00Z: bid 213.755, ask 213.769, 0.199 above zone top.
- 2026-05-11T11:56:46Z: bid 213.707, ask 213.736, 0.166 above zone top.
- 2026-05-11T11:57:00Z: bid 213.736, ask 213.760, 0.190 above zone top.
- 2026-05-11T11:59:30Z: bid 213.782, ask 213.793, 0.223 above zone top.
- 2026-05-11T12:00:06Z: bid 213.794, ask 213.813, 0.243 above zone top.

As of 2026-05-11T12:00:06Z the old zone has not been retested since this
post-close watch note began.

## Screenshot / Sweep Evidence

- 2026-05-11T12:10:56Z screenshot, GBPJPY M15 MT5 chart: visual evidence shows
  price swept down into/below the original FVG pocket near 213.496-213.570,
  reclaimed the 213.53 area, then displaced upward into the 213.82-213.86
  region.
- The chart overlay showed `ACTIVE: none`, `candidates 0`, `rejected 2`,
  `no-trade 11`, and `LAST_LIMIT_PLACED [07:30] lim_GBPJPY_2026-05-11_073031`.
- MT5 OHLC cross-check at 2026-05-11T12:11:46Z: recent GBPJPY M15 bars showed a
  low of 213.464 and high of 213.861. The 13:45 broker-time M15 bar had
  O=213.552 H=213.670 L=213.464 C=213.527 V=2974 and was flagged as
  `TOUCHED_ZONE`, `SWEPT_ZONE_LOW_RECLAIM`, and `FULL_ZONE_WICK`.
- Current tick at 2026-05-11T12:11:46Z: bid 213.766, ask 213.778, which is
  0.208 above the zone top. No active re-entry touch at that moment.

## Continued Post-Screenshot Watch

- 2026-05-11T12:13:33Z: bid 213.772, ask 213.786, 0.216 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:13:43Z: bid 213.772, ask 213.784, 0.214 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:13:53Z: bid 213.767, ask 213.787, 0.217 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:14:03Z: bid 213.766, ask 213.781, 0.211 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:14:13Z: bid 213.761, ask 213.775, 0.205 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:14:23Z: bid 213.742, ask 213.760, 0.190 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:14:33Z: bid 213.733, ask 213.745, 0.175 above zone top,
  GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:15:28Z: bid 213.732, ask 213.744, 0.174 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:15:43Z: bid 213.737, ask 213.749, 0.179 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:15:58Z: bid 213.727, ask 213.741, 0.171 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:16:13Z: bid 213.713, ask 213.730, 0.160 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:16:28Z: bid 213.717, ask 213.729, 0.159 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:16:43Z: bid 213.718, ask 213.730, 0.160 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:16:58Z: bid 213.703, ask 213.716, 0.146 above zone top,
  all positions 0, all orders 0, GBPJPY positions 0, GBPJPY orders 0.
- 2026-05-11T12:51:01Z: broker positions 0, broker orders 0. GBPJPY bid
  213.782, ask 213.800, 0.230 above zone top and 0.267 above midpoint. Recent
  M15 window: price balanced above the old pocket after the prior sweep/reclaim,
  with recent candles ranging roughly 213.733-213.861 and no fresh retest of the
  213.496-213.570 pocket.

## Infrastructure Intervention During Watch

- 2026-05-11T12:18Z tick-state check found stale capture freshness on
  `US30_cash` and `XAGUSD`, while GBPJPY remained fresh.
- Restarted only the stale tick-capture daemons: `US30_cash` old PIDs
  12636/15660 and `XAGUSD` old PIDs 16228/12896. Trading orchestrators and
  broker/order/account state were not touched.
- 2026-05-11T12:19:51Z post-restart tick-state verification:
  `US30_cash` age 45.8s OK, `XAGUSD` age 63.3s OK, `GBPJPY` age 25.4s OK.
