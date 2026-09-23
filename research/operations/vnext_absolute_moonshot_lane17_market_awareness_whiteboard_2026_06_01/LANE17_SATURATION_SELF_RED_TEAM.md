# Lane17 Saturation Self Red Team

- Evidence-class confusion checked: whiteboard rows exclude result payloads and label values; label-only state is represented only as field-source metadata.
- One-timeframe collapse checked: schema and verifier require D1/H4/H1/M15/M1/tick coverage states.
- Hidden null checked: every missing/non-generatable source state requires stale_or_null_reason and source gap rows.
- Symbol starvation checked: verifier requires all 24 live symbols in replay and forward snapshot ledgers.
- Source-gap specificity checked: source gaps carry field family, symbol, broker symbol, decision timestamp/window, source path when known, and capture or repair requirement.
- Correlation top-N trap checked: all 276 symbol pairs are emitted, not only top peers.
- Runtime activation checked: forward packet fields are default-off contract decisions only.
