# Lane06 Saturation And Self-Red-Team

Generated: 2026-06-01T03:17:46.650184+00:00

- Evidence-class confusion checked: broker-real `broker_real_net_r` remains a
  separate label family from `source_bound_proxy_r`; proxy labels are not
  broker performance claims.
- Denominator leakage checked: label rows carry `label_only_excluded_from_feature_rows`;
  Lane02 feature-store forbidden classes are rechecked in the no-leak ledger.
- Lane05 no-leak integration checked: present feature-store contract requires
  labels to join only after purged/embargoed splits and forbids label/outcome
  fields as feature columns.
- Lane07 broker/cost integration checked: broker-real trade-cost rows remain
  label-store broker truth, and non-trade slippage/spread rows remain source
  coverage rather than feature leakage or live execution input.
- Full same-class coverage checked: all Lane04 timeline rows were streamed into
  `research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01/LANE06_LABEL_VECTOR_LEDGER.jsonl.gz` and all Lane03 canonical candidates without a
  joined label source were streamed into `research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01/LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz`.
- No arbitrary top-N: no row cap was used for label vectors or Lane03 gap rows.
- Missing source rule: broker-real net-R, cost-adjusted R, and tick/broker path
  gaps remain row-level missing-label/source reasons, not invented values.
- Downstream contract frozen: Feature Store, Digital Twin, ML, Selector,
  Scheduler, and Execution Policy use rules are written in
  `research/operations/vnext_moonshot_lane06_label_store_v1_2026_06_01/LANE06_DOWNSTREAM_CONTRACT.json`.

Counts:
- label vector rows: `289928`
- Lane03 candidates scanned: `3761515`
- missing label gap rows: `3471773`
- source gap rows inside vectors: `289604`
- Lane07 broker truth rows: `64`
- Lane07 cost rows: `53`
