# LTO-001 MSO Snapshot Join Audit - 2026-05-05

**Schema:** `lto001_mso_snapshot_join_audit_v1`
**Generated:** `2026-05-05T10:42:46.429506+00:00`
**Status:** `OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Candidate rows considered: `66`
- Join rows appended: `17`
- Joined exact MSO snapshots: `60`
- MSO join missing rows: `6`
- Context mismatches: `0`

## Join Status Counts

`{'JOINED_EXACT_MSO_SNAPSHOT': 60, 'MSO_JOIN_MISSING': 6}`

## Context Comparison Status Counts

`{'JOINED_CONTEXT_MATCHED': 60, 'MSO_JOIN_MISSING': 6}`

## Missing MSO Join Candidates

- `GBPJPY_2026-05-04T02:15:00+00:00` `GBPJPY` `2026-05-04T02:15:00+00:00` nearest_delta=`18000.0` nearest=`GBPJPY_2026-05-04T07:15:00+00:00_pre_ai`
- `GBPJPY_2026-05-04T02:30:00+00:00` `GBPJPY` `2026-05-04T02:30:00+00:00` nearest_delta=`17100.0` nearest=`GBPJPY_2026-05-04T07:15:00+00:00_pre_ai`
- `GBPJPY_2026-05-04T03:00:00+00:00` `GBPJPY` `2026-05-04T03:00:00+00:00` nearest_delta=`15300.0` nearest=`GBPJPY_2026-05-04T07:15:00+00:00_pre_ai`
- `NAS100_2026-05-03T16:15:00+00:00` `NAS100` `2026-05-03T16:15:00+00:00` nearest_delta=`54000.0` nearest=`NAS100_2026-05-04T07:15:00+00:00_pre_ai`
- `XAUUSD_2026-05-03T16:15:00+00:00` `XAUUSD` `2026-05-03T16:15:00+00:00` nearest_delta=`54000.0` nearest=`XAUUSD_2026-05-04T07:15:00+00:00_pre_ai`
- `XAUUSD_2026-05-03T16:30:00+00:00` `XAUUSD` `2026-05-03T16:30:00+00:00` nearest_delta=`53100.0` nearest=`XAUUSD_2026-05-04T07:15:00+00:00_pre_ai`

## Safety

- No AI calls: `True`
- No canary required: `True`
- No execution: `True`
- Paid fetch attempted: `False`
- Paid data calls: `0`
