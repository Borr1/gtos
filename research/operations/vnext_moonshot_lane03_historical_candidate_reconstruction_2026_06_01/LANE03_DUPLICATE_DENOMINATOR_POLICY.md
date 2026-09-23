# Lane03 Duplicate And Denominator Policy

The event ledger preserves every parsed material source row. Deduplication never deletes event evidence.

Canonical duplicate groups are keyed by normalized symbol, side, framework, mechanism family, candidate time, session, and the strongest source row identifier available. If no source row identifier exists, the source id and line number become the identifier.

The canonical candidate ledger and duplicate group ledger aggregate those keys for denominator-aware downstream use. Singleton groups remain explicit so denominator changes are auditable.

Exact R is used only when an explicit actual/broker/realized/deal/executed R field exists. Simulated, replay, path, selected, gross, or generic R fields are labeled proxy R. Missing R rows keep row-level missing-field proof and capture/export requirements in the gap ledger.

Runtime boundary: `offline_research_only_no_live_trading_effect`.
