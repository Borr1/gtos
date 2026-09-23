# GBPJPY 2026-05-11 10:45 Live Trade Watch

Created: 2026-05-11T10:57:00Z

## Broker Position

- Symbol: GBPJPY
- Ticket: 237192029
- Side: LONG
- Volume: 4.10 lots
- Entry: 213.594
- Stop loss: 213.207
- Broker TP: 215.916
- Magic: 20260401
- Comment: GoldAgent_OBRete

## Source Linkage

- Candidate: `GBPJPY_2026-05-11T07:30:00+00:00`
- Internal intent: `lim_GBPJPY_2026-05-11_073031`
- System fill event: `2026-05-11T10:45:05Z`
- Source log: `logs/gbpjpy.log`

## Management Levels

The broker TP differs from the original AI TP1 by design. The execution log
states J46-J49 is active:

- Original AI TP1: 214.022
- Software TP1 / BE trigger: 214.755 (3R from actual fill)
- Broker TP: 215.916 (6R from actual fill)
- Actual risk distance: 0.387

## Early Snapshots

- 2026-05-11T10:54:06Z: current 213.639, about +0.12R, floating +117.44 USD.
- 2026-05-11T10:55:31Z: current 213.629, about +0.09R, floating +91.34 USD.
- 2026-05-11T10:56:30Z: current 213.567, about -0.07R, floating -70.45 USD.

## Live Watch Snapshots

- 2026-05-11T10:57:30Z: current 213.523, about -0.18R, floating -185 USD.
- 2026-05-11T10:58:16Z: current 213.516, about -0.20R, floating -203 USD.
- 2026-05-11T10:59:00Z: current 213.503, about -0.24R, floating -237 USD.
- 2026-05-11T11:00:06Z: current 213.547, about -0.12R, floating -123 USD.
- 2026-05-11T11:01:05Z: current 213.537, about -0.15R, floating -149 USD.
- 2026-05-11T11:02:06Z: current 213.555, about -0.10R, floating -102 USD.
- 2026-05-11T11:03:06Z: current 213.585, about -0.02R, floating -23 USD.
- 2026-05-11T11:04:06Z: current 213.606, about +0.03R, floating +31 USD.
- 2026-05-11T11:05:05Z: current 213.630, about +0.09R, floating +94 USD.
- 2026-05-11T11:06:06Z: current 213.675, about +0.21R, floating +211 USD.
- 2026-05-11T11:07:06Z: current 213.714, about +0.31R, floating +313 USD.
- 2026-05-11T11:08:05Z: current 213.772, about +0.46R, floating +465 USD.
- 2026-05-11T11:09:31Z: current 213.806, about +0.55R, floating +553 USD.
- 2026-05-11T11:10:31Z: current 213.820, about +0.58R, floating +590 USD.
- 2026-05-11T11:11:31Z: current 213.808, about +0.55R, floating +558 USD.
- 2026-05-11T11:12:30Z: current 213.758, about +0.42R, floating +428 USD.
- 2026-05-11T11:13:30Z: current 213.782, about +0.49R, floating +491 USD.
- 2026-05-11T11:14:30Z: current 213.808, about +0.55R, floating +558 USD.
- 2026-05-11T11:15:30Z: current 213.828, about +0.60R, floating +611 USD.
- 2026-05-11T11:16:30Z: current 213.799, about +0.53R, floating +535 USD.
- 2026-05-11T11:17:31Z: current 213.789, about +0.50R, floating +509 USD.
- 2026-05-11T11:18:31Z: current 213.816, about +0.57R, floating +579 USD.
- 2026-05-11T11:19:31Z: current 213.814, about +0.57R, floating +574 USD.
- 2026-05-11T11:20:31Z: current 213.817, about +0.58R, floating +582 USD.
- 2026-05-11T11:21:31Z: current 213.834, about +0.62R, floating +626 USD.
- 2026-05-11T11:22:31Z: current 213.822, about +0.59R, floating +595 USD.
- 2026-05-11T11:23:31Z: current 213.830, about +0.61R, floating +616 USD.
- 2026-05-11T11:24:31Z: current 213.821, about +0.59R, floating +592 USD.
- 2026-05-11T11:25:31Z: current 213.820, about +0.58R, floating +590 USD.
- 2026-05-11T11:26:31Z: current 213.821, about +0.59R, floating +592 USD.
- 2026-05-11T11:27:31Z: current 213.817, about +0.58R, floating +582 USD.
- 2026-05-11T11:28:31Z: current 213.820, about +0.58R, floating +590 USD.
- 2026-05-11T11:29:31Z: current 213.816, about +0.57R, floating +579 USD.

## Exit

- Broker position absent on 2026-05-11T11:30:31Z poll.
- System log: `2-hour timeout trailing limit reached - closing position`.
- System close reason: `timeout_2h`.
- Close price used by execution: 213.835.
- Saved trade record exit: 2026-05-11T11:30:06Z, exit price 213.832, actual R +0.6150, hold 45 minutes.
- Broker close deal: order 237202728, comment `close_timeout_2h`, price 213.835, gross profit +628.97 USD.

## Operational Finding

The timeout was anchored to the London kill-zone end, not to the late outside-KZ
fill time. London GBPJPY KZ ended at 2026-05-11T09:30:00Z; the close fired at
2026-05-11T11:30:06Z. Because the internal limit filled at 2026-05-11T10:45:05Z,
the live hold after fill was about 45 minutes. This is source-behavior
intelligence for pending-limit management, not a broker/order-account failure.

## Operational Boundary

Observation only. No order modification, account action, execution behavior,
risk change, prompt/config change, or validation/promotion change was made from
this note.
