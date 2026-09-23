# LTO-026 Trade Index Lifecycle Completeness - 2026-05-05

**Schema:** `lto026_trade_index_lifecycle_completeness_v1`
**Generated:** `2026-06-01T23:41:45.935534+00:00`
**Status:** `OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Trade-record rows considered: `499`
- Audit rows available: `926`
- Audit rows appended this run: `19`
- Complete: `171`
- Complete with documented blockers: `328`
- Action required: `0`

## Index Boundary

- Current inventory index: `knowledge_base\index\trade_record_inventory_index_2026-05-05.json`
- Inventory index count equals trade-record count: `True`
- Trade-record count: `499`
- Legacy `_trade_index.json` count: `129`
- Count delta current minus legacy: `370`
- Legacy `_trade_index.json` was not overwritten; it remains a frozen historical cohort only.

## Lifecycle Completeness

- Lifecycle completeness counts: `{'LIMIT_PLACED_COMPLETE_WITH_PENDING_LIFECYCLE_AUDIT': 31, 'NON_EXECUTED_DECISION_COMPLETE_NO_LIFECYCLE_REQUIRED': 171, 'UNKNOWN_STATE_DOCUMENTED': 297}`
- Limit-placed rows: `31`
- Limit-placed rows without lifecycle truth: `0`
- Raw trade-id collision rows: `3`
- Exit-present/execution-null rows: `0`

## Migration Plan

- Replacement: `knowledge_base\index\trade_record_inventory_index_2026-05-05.json`
- Consumer policy: new current-inventory consumers should read the versioned inventory index or aggregate knowledge_base/trade_records directly; older research consumers may keep using _trade_index.json only as a frozen historical cohort with source flags

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`

## Documented Blocker Examples

```json
[
  {
    "candidate_id": "AUDJPY_2026-06-01T03:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_moonshot_h03_04_0345.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T00:15:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0015.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T00:30:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0030.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T01:00:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0100.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T01:15:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0115.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T01:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0145.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T02:00:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0200.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "AUDJPY_2026-06-01T02:15:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "AUDJPY/2026-06-01_tokyo_0215.json",
    "symbol": "AUDJPY"
  },
  {
    "candidate_id": "BTCUSD_2026-05-31T23:15:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-05-31_off_configured_session_2315.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-05-31T23:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-05-31_off_configured_session_2345.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T01:15:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0115.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T01:30:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0130.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T02:15:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0215.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T02:30:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0230.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T02:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0245.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T06:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0645.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T07:00:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0700.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T07:30:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0730.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T07:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0745.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T08:30:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0830.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T08:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_0845.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T10:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_1045.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T12:00:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_1200.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T12:45:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_1245.json",
    "symbol": "BTCUSD"
  },
  {
    "candidate_id": "BTCUSD_2026-06-01T16:00:00Z",
    "documented_limitation_codes": [
      "TRADE_RECORD_STATE_UNKNOWN"
    ],
    "lifecycle_completeness": "UNKNOWN_STATE_DOCUMENTED",
    "source_path": "BTCUSD/2026-06-01_off_configured_session_1600.json",
    "symbol": "BTCUSD"
  }
]
```
