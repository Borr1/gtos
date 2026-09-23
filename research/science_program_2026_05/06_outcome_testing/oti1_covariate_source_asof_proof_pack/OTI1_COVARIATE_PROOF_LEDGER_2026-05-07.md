# OTI1 Per-Covariate Proof Ledger

- promotion_verdict: NO_PROMOTION_VERDICT
## source_freshness_context

- Source IDs: OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS
- Allowed role: Lifecycle source provenance only: decision_asof_utc/source_capture_utc/source_hash for existing lifecycle/no-fill rows.
- Label boundary: May support lifecycle_no_fill provenance only; not synthetic_path_r, broker_actual_r, win/loss, or return labels.
- Packet status counts: {'CLEARED_FOR_PACKET_CONTEXT_ONLY': 9}

## local_news_schedule

- Source IDs: SRC-G5-NEWS-CALENDAR-LOCAL-001
- Allowed role: Schedule and stale-calendar context only; no release result, surprise, sentiment, or live-filter change.
- Label boundary: May label local calendar context separately from lifecycle_no_fill rows; must not merge with broker actual-R or synthetic path-R.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 7, 'CLEARED_FOR_PACKET_CONTEXT_ONLY': 2}

## friction

- Source IDs: G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE, SRC-G11-LOCAL-INSTRUMENT-EXPANSION
- Allowed role: Blocked for packet-bound decision-time friction features; existing sidecars are context-only proposals.
- Label boundary: Friction eligibility must be computed before outcome labels and kept separate from lifecycle/no-fill counts.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 7, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 2}

## realized_volatility

- Source IDs: SRC-G2-FORWARD-SHADOW-LIFECYCLE
- Allowed role: Blocked until realized-vol features are source-hashed and packet-bound as of decision time.
- Label boundary: Volatility covariates may condition lifecycle_no_fill only after packet-bound proof; they do not create return labels.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 8, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 1}

## volatility_of_volatility

- Source IDs: SRC-G2-FORWARD-SHADOW-LIFECYCLE
- Allowed role: Blocked until vol-of-vol features are source-hashed and packet-bound as of decision time.
- Label boundary: Vol-of-vol covariates may condition lifecycle_no_fill only after packet-bound proof; they do not create return labels.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 8, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 1}

## footprint_absorption_orderflow_context

- Source IDs: SRC-G4-DATABENTO-GLBX-MDP3, SRC-G4-SIERRA-DEPTH-SCID, SRC-G4-LOCAL-GTOS-ORDERFLOW-ARTIFACTS
- Allowed role: Blocked for packet-bound orderflow/absorption features; local and official references are source-contract context only.
- Label boundary: Orderflow features must be pre-decision context only and must not include fill outcomes or broker account history.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 8, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 1}

## macro_attention

- Source IDs: SRC-G5-NEWS-CALENDAR-LOCAL-001, SRC-G7-FED-FOMC-001, SRC-G7-FRED-RATES-001, SRC-G7-BIS-STATS-001, SRC-G7-ICE-DXY-001, SRC-G7-LOCAL-GTOS-MACRO-001
- Allowed role: Blocked beyond local schedule/stale-calendar context; macro-attention source stack is not packet-bound.
- Label boundary: Macro-attention features must remain context labels separate from lifecycle and return labels.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 8, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 1}

## fomc_event_windows

- Source IDs: SRC-G7-FED-FOMC-001, SRC-G5-NEWS-CALENDAR-LOCAL-001
- Allowed role: Blocked for FOMC window classification; cached official page currently supports date-only/context evidence, not packet-bound event-time windows.
- Label boundary: FOMC/event-window labels must be separate covariates and cannot include post-release surprise/outcome.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 8, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 1}

## cboe_short_vol_context

- Source IDs: SRC-G8-CBOE-METHODOLOGY-002, SRC-G8-CBOE-VOL-CSV-001
- Allowed role: Blocked for decision-row short-vol context; methodology pages are context-only and CSV publication/legal/no-lookahead proof remains unresolved.
- Label boundary: Short-vol context must be pre-decision context only and separate from lifecycle/no-fill and return labels.
- Packet status counts: {'NOT_PACKET_BOUND_BLOCKED_IF_USED': 8, 'BLOCKED_WITH_NEXT_EXACT_EVIDENCE': 1}
