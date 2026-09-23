# Lane02 Saturation And Self-Red-Team

- Evidence-class confusion risk: source metadata and broker history fields can look like candidate-time fields; contract marks them source_metadata or broker_realized unless explicit candidate clocks are present.
- Leakage risk: feature-store validation rejects post-order, post-fill, post-close, broker-realized, replay-only, label-only, and future-outcome classes.
- Duplicate-key risk: canonical key policy requires source_row_id plus route_id and broker ticket/order/deal ids where applicable.
- Filename-date risk: filename dates are inventoried as source metadata and cannot substitute for decision/candle time.
- Local-heavy-data risk: MT5 preservation inventory is consumed as source completeness evidence; raw binary caches require an exporter/parser route before row-level use.
- Dependency risk: absent absolute master and Lane01 source-authority outputs are dependency-state rows, not stop conditions.
- Runtime risk: this route writes research-only artifacts and tests; it does not change config, prompts, risk, execution, safety, canary, selector, or broker state.
