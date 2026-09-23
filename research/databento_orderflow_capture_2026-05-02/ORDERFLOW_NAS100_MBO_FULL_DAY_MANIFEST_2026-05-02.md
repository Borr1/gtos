# NAS100 MBO Full-Day Manifest

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

This manifest scopes MBO pulls to NAS100/NQ event dates that contain GTOS candidates. Each request starts at UTC midnight for Databento synthetic book reconstruction, while feature extraction remains limited to as-of pre60/event15 event windows.

## Coverage

- Events: 59
- Fetch groups: 3
- Candidate dates: ['2026-04-28', '2026-04-29', '2026-05-01']
- Event class counts: {'candidate': 12, 'm15_choch_context': 17, 'structural_context': 30}

## Fetch Groups

| Group | Start UTC | End UTC | Events | Classes |
|---|---|---|---:|---|
| mbo_nas100_nqv0_20260428 | 2026-04-28T00:00:00+00:00 | 2026-04-28T17:00:00+00:00 | 30 | [('candidate', 9), ('m15_choch_context', 7), ('structural_context', 14)] |
| mbo_nas100_nqv0_20260429 | 2026-04-29T00:00:00+00:00 | 2026-04-29T17:00:00+00:00 | 27 | [('candidate', 2), ('m15_choch_context', 10), ('structural_context', 15)] |
| mbo_nas100_nqv0_20260501 | 2026-05-01T00:00:00+00:00 | 2026-05-01T08:15:00+00:00 | 2 | [('candidate', 1), ('structural_context', 1)] |

## Ambiguity Ledger

- Raw request coverage includes pre-event dead time from midnight because MBO reconstruction requires the starting book snapshot.
- Analysis features must not use data after each event's canonical close.
- Context rows are restricted to dates that also contain NAS100 candidates.

## Next Steps

1. Estimate the MBO groups before fetching.
2. Execute only if the cost cap passes.
3. Run the registered no-leak MBO extractor on pre60/event15 windows only.
