# Lane08 Saturation And Self Red Team

- Evidence-class separation risk: decision inputs and result payload are nested separately and scanned by `LANE08_NO_LEAK_VALIDATION_LEDGER.jsonl`.
- Denominator risk: all Lane06 label rows are materialized in the replay ledger and all Lane06 missing-label rows are materialized as missing replay gaps.
- Friday-only risk: Friday is one replay depth; daily, weekly, monthly, sealed partitions, broad selected, strict tick, and broker-real depths are also written.
- Raw-candidate tournament risk: raw canonical candidates without joined label source are not scored; they are explicit gap rows with repair requirements.
- Broker/proxy confusion risk: `result_r_class` separates `exact_broker_real`, `source_bound_proxy`, `cost_adjusted_proxy`, and missing states.
- Forward-shadow gap: current inputs lack a joined full-chain contract, so forward shadow is recorded as a missing-contract depth row rather than claimed as replayed.
- Production-change risk: route artifacts are default-off research outputs and do not alter config, prompts, risk, execution, safety, canary, selector, or broker state.
