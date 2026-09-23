# LTO-016 J46-J49 Exit Comparator Audit - 2026-05-05

**Schema:** `lto016_j46_j49_exit_comparator_audit_report_v1`
**Generated:** `2026-06-01T23:36:48.246546+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Rows computed: `555`
- Status rows available: `7046`
- Status rows appended this run: `284`
- Filled account-history joined: `4`
- Filled account-history missing: `13`
- Candidate no-fill context: `81`
- Candidate path synthetic-only: `407`
- Actual-R claim allowed rows: `4`
- Action required: `13`

## Status Breakdown

- Status counts: `{'J46_J49_FILLED_ACCOUNT_HISTORY_JOINED': 4, 'J46_J49_FILLED_ACCOUNT_HISTORY_MISSING': 13, 'J46_J49_CANDIDATE_PATH_SYNTHETIC_ONLY': 407, 'J46_J49_CANDIDATE_NO_FILL_CONTEXT': 81, 'NO_CANDIDATE_PATH_ROW': 50}`
- Row type counts: `{'filled_exit_comparator': 17, 'candidate_context': 538}`
- ML label eligibility counts: `{'ELIGIBLE_ACCOUNT_HISTORY_REALIZED_LABEL_AFTER_TARGET_REFRESH': 4, 'NOT_ELIGIBLE_ACTION_REQUIRED_OR_MISSING_ACCOUNT_HISTORY': 63, 'SYNTHETIC_PATH_LABEL_ONLY_NOT_ACCOUNT_HISTORY_ACTUAL_R': 407, 'NO_ACTUAL_R_LABEL_NO_FILL_CONTEXT': 81}`
- Action-required codes: `{'FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT': 13}`
- Documented limitations: `{'NO_CANDIDATE_PATH_JOIN_FOR_LEGACY_FILL': 17, 'NO_CANDIDATE_PATH_ROW_FOR_COMPARATOR_CONTEXT': 50}`

## Boundary

Filled J46/J49 comparator rows may claim actual-R only when joined to ACCOUNT_HISTORY_REALIZED broker audit evidence. Candidate context rows prevent fill-only rows from being mistaken for the full candidate universe and never claim actual-R.

## ML Goal Contribution

This audit converts the exit-comparator lane into ML-ready label-quality and sample-eligibility metadata: account-history-realized fills can become target labels after K55 target refresh, while no-fill/path-only rows become explicit non-label or synthetic-path context.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`

## Action Required Examples

```json
[
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "NAS100_2026-05-29_moonshot_h06_07_0615",
    "row_key": "73c244efb393376ce249a6e69827c677",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "NAS100"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "USOIL_cash_2026-06-01_ny_1315",
    "row_key": "e4407070a22a76ebeefc3d89742c7e8c",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "USOIL_cash"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "UKOIL_cash_2026-06-01_ny_1315",
    "row_key": "45a5a90f1384c37fb8a15cacbd09a000",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "UKOIL_cash"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "NAS100_2026-06-01_ny_1315",
    "row_key": "3fce354786c45ae902916e6f2f376e33",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "NAS100"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "BTCUSD_2026-06-01_off_configured_session_1200",
    "row_key": "27128513cba0323e05b9b81b6f1c4e9b",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "GBPJPY_2026-06-01_moonshot_h16_17_1645_broadorigin_a58abd079e78a49fc3ed7a2a",
    "row_key": "6997cd4b1dd926db7391c3d1bf7af293",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "GBPJPY"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "NAS100_2026-06-01_moonshot_h17_18_1715_broadorigin_95e1f4f841a261722b80a4c7",
    "row_key": "e73fd0e2620b4a10a844089cb7eb7c85",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "NAS100"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "US30_cash_2026-06-01_moonshot_h13_14_1315",
    "row_key": "e9299dccb26adce3e10c65176ebf171a",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "US30_cash"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "ETHUSD_2026-06-01_off_configured_session_1200",
    "row_key": "4d2b0978de6a264f42f5ff825899fd09",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "ETHUSD"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "NAS100_2026-06-01_moonshot_h17_18_1745_broadorigin_2f1fcbb7f16270cd2090f5ee",
    "row_key": "e1ba679635c1bbdff3b8a567e7a9e965",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "NAS100"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "ETHUSD_2026-06-01_off_configured_session_2115_broadorigin_b85aced479b5b868a59a3815",
    "row_key": "d46f03704c6d7ba106fa1ebebed892f5",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "ETHUSD"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "US30_cash_2026-06-01_moonshot_h18_19_1845_broadorigin_87468509d8e8f8ba6b9a8506",
    "row_key": "f4c8ef3fbbb47768eff3f5be73702d64",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "US30_cash"
  },
  {
    "action_required_codes": [
      "FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"
    ],
    "candidate_id": null,
    "fill_id": "USDJPY_2026-06-01_moonshot_h12_13_1300",
    "row_key": "9518b0c34bf82bafdd2036d2a5521adb",
    "row_type": "filled_exit_comparator",
    "status": "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "symbol": "USDJPY"
  }
]
```
