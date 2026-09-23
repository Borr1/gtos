# Orderflow Event Window Manifest

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This manifest converts supported GTOS structure/candidate rows into Databento futures harvest windows. It is a data acquisition plan, not an alpha or promotion claim.

## Counts

- Rows loaded: 518
- Events selected: 183
- Merged fetch groups: 20
- Truncated event windows: 6
- Symbol counts: {'NAS100': 73, 'US30_cash': 83, 'XAUUSD': 27}
- Event class counts: {'candidate': 23, 'm15_choch_context': 43, 'structural_context': 117}

## Fetch Groups

| Group | Symbols | Start UTC | End UTC | Events | Classes |
|---|---|---|---:|---:|---|
| ofwin_0001 | GC.v.0 | 2026-04-17T06:15:00+00:00 | 2026-04-17T11:30:00+00:00 | 12 | [('m15_choch_context', 5), ('structural_context', 7)] |
| ofwin_0002 | GC.v.0 | 2026-04-17T12:15:00+00:00 | 2026-04-17T14:30:00+00:00 | 2 | [('candidate', 2)] |
| ofwin_0003 | GC.v.0 | 2026-04-19T15:15:00+00:00 | 2026-04-19T18:00:00+00:00 | 4 | [('m15_choch_context', 4)] |
| ofwin_0004 | GC.v.0 | 2026-05-01T07:00:00+00:00 | 2026-05-01T09:15:00+00:00 | 2 | [('candidate', 1), ('structural_context', 1)] |
| ofwin_0005 | GC.v.0 | 2026-05-01T13:15:00+00:00 | 2026-05-01T16:00:00+00:00 | 7 | [('candidate', 7)] |
| ofwin_0006 | NQ.v.0 | 2026-04-28T06:15:00+00:00 | 2026-04-28T11:30:00+00:00 | 14 | [('candidate', 8), ('m15_choch_context', 3), ('structural_context', 3)] |
| ofwin_0007 | NQ.v.0 | 2026-04-28T12:15:00+00:00 | 2026-04-28T18:00:00+00:00 | 16 | [('candidate', 1), ('m15_choch_context', 4), ('structural_context', 11)] |
| ofwin_0008 | NQ.v.0 | 2026-04-29T06:15:00+00:00 | 2026-04-29T11:30:00+00:00 | 14 | [('m15_choch_context', 6), ('structural_context', 8)] |
| ofwin_0009 | NQ.v.0 | 2026-04-29T12:15:00+00:00 | 2026-04-29T18:00:00+00:00 | 13 | [('candidate', 2), ('m15_choch_context', 4), ('structural_context', 7)] |
| ofwin_0010 | NQ.v.0 | 2026-04-30T12:45:00+00:00 | 2026-04-30T18:00:00+00:00 | 14 | [('m15_choch_context', 7), ('structural_context', 7)] |
| ofwin_0011 | NQ.v.0 | 2026-05-01T07:00:00+00:00 | 2026-05-01T09:15:00+00:00 | 2 | [('candidate', 1), ('structural_context', 1)] |
| ofwin_0012 | YM.v.0,ES.v.0 | 2026-04-17T07:15:00+00:00 | 2026-04-17T11:30:00+00:00 | 9 | [('m15_choch_context', 4), ('structural_context', 5)] |
| ofwin_0013 | YM.v.0,ES.v.0 | 2026-04-17T12:45:00+00:00 | 2026-04-17T17:00:00+00:00 | 10 | [('candidate', 1), ('structural_context', 9)] |
| ofwin_0014 | YM.v.0,ES.v.0 | 2026-04-28T08:00:00+00:00 | 2026-04-28T11:30:00+00:00 | 7 | [('m15_choch_context', 1), ('structural_context', 6)] |
| ofwin_0015 | YM.v.0,ES.v.0 | 2026-04-28T12:45:00+00:00 | 2026-04-28T17:00:00+00:00 | 10 | [('m15_choch_context', 3), ('structural_context', 7)] |
| ofwin_0016 | YM.v.0,ES.v.0 | 2026-04-29T07:15:00+00:00 | 2026-04-29T11:30:00+00:00 | 10 | [('m15_choch_context', 2), ('structural_context', 8)] |
| ofwin_0017 | YM.v.0,ES.v.0 | 2026-04-29T13:15:00+00:00 | 2026-04-29T17:00:00+00:00 | 8 | [('structural_context', 8)] |
| ofwin_0018 | YM.v.0,ES.v.0 | 2026-04-30T12:45:00+00:00 | 2026-04-30T17:00:00+00:00 | 10 | [('structural_context', 10)] |
| ofwin_0019 | YM.v.0,ES.v.0 | 2026-05-01T07:15:00+00:00 | 2026-05-01T11:30:00+00:00 | 10 | [('structural_context', 10)] |
| ofwin_0020 | YM.v.0,ES.v.0 | 2026-05-01T12:45:00+00:00 | 2026-05-01T16:00:00+00:00 | 9 | [('structural_context', 9)] |

## Ambiguity Ledger

- canonical_m15_close_utc is inferred by flooring live wall-clock evaluation timestamps to the prior M15 boundary.
- The manifest only covers GTOS symbols with validated CME proxy mappings so far: XAUUSD, NAS100, and US30_cash/US30.
- Fetch commands use trades schema first; depth schemas require a separate cost and value gate.
- Event inclusion is limited to fields already present in candidate_features_log.jsonl.
- Rows at or after available_end_utc are excluded when an availability cap is supplied; windows crossing the cap are truncated.

## Open Questions

1. Do trades-level features around these windows separate candidates from structural no-trade context?
2. Which event classes justify mbp-1/mbp-10 depth after trades features are measured?
3. Do inferred M15 candle timestamps match future shadow-only canonical candle-close logging?

## Next Steps

1. Fetch trades schema for the merged candidate/context groups under explicit cost caps.
2. Extract CVD, delta acceleration, POC/HVN/LVN, volume imbalance, and absorption proxies per event.
3. Join features back to synthetic/actual outcomes before any strategy hypothesis is registered.
