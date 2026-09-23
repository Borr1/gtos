# G12 MAC Inverse Avoid-Filter Audit

Date: 2026-05-15
Evidence class: `G12_MAC_INVERSE_AVOID_FILTER_AUDIT_ONLY`
Terminal decision: `ACCEPT_AS_G12_MAC_INVERSE_AVOID_FILTER_DESIGN_AUDIT_NO_PROMOTION`

The audit accepts the MAC-001/MAC-004 inverse avoid-filter design route as G12 audit-only evidence for downstream interpretation. It does not open promotion, validation safety, live behavior, R/PnL, win-rate, expectancy, AI/API, paid/vendor, broker/order/account, prompt/config/risk/safety/execution/canary/selector, registry, raw-blob, or remote surfaces.

Key checks: source route verifier passed, focused pytest passed, prompt hardening passed, full JSONL artifact audit passed, MAC target file rows/hashes matched accepted G12 source records, and accepted-G12 pass/control delta comparisons had zero missing or mismatched accepted rows.

MAC-001 remains a future calendar/timing-veto design candidate. MAC-004 h1 avoid-filter evidence is killed; longer-horizon metals fix-window adverse-selection designs remain source-bound, concentration-constrained, and future-validation-only.

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed.
