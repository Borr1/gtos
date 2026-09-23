# Futures Proxy Expansion Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registration verdict: `NO_PROXY_MAP_ACTIVATION`

## Synthesis

Three capped trades-only windows support XAGUSD/SI and GBPUSD/6B as strict price-transfer proxies. USDJPY/6J inverse mapping is directionally strong but strict-correlation review remains open because one window falls below the 0.85 floor. No orderflow proxy map is activated by this audit.

## Pair Audit

| Pair | Status | Windows | Min corr | Median corr | Min direction | Best lag all zero | Blocking reasons |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6B.v.0->GBPUSD:direct | STRICT_TRANSFER_PASS | 3 | 0.905472 | 0.920078 | 0.931116 | True |  |
| 6J.v.0->USDJPY:inverse_return | TRANSFER_REVIEW_REQUIRED | 3 | 0.825301 | 0.856882 | 0.928977 | True | min_corr_below_0.85 |
| SI.v.0->XAGUSD:direct | STRICT_TRANSFER_PASS | 3 | 0.906536 | 0.942263 | 0.881818 | True |  |

## Decision Readout

| Decision | Status |
| --- | --- |
| strict_transfer_pass_pairs | 6B.v.0->GBPUSD:direct, SI.v.0->XAGUSD:direct |
| review_required_pairs | 6J.v.0->USDJPY:inverse_return |
| xagusd_mapping_status | STRICT_TRANSFER_PASS |
| usdjpy_mapping_status | TRANSFER_REVIEW_REQUIRED |
| gbpusd_mapping_status | STRICT_TRANSFER_PASS |
| gbpjpy_synthetic_cross_status | BLOCKED_BY_6J_USDJPY_REVIEW |

## Answered Questions

- SI.v.0 can be treated as a provisional XAGUSD price-transfer proxy for research manifests.
- 6B.v.0 can be treated as a provisional GBPUSD price-transfer proxy for research/control manifests.
- 6J.v.0 needs inverse-return handling for USDJPY and remains under review because one tested window is weak.
- GBPJPY remains blocked as a synthetic-cross orderflow source; one leg is under review and depth semantics are two-book, not one ladder.

## Ambiguity Ledger

- This is price-transfer validation only; it does not validate any orderflow alpha feature.
- The tested windows are three April 2026 windows, not a roll/date-transition proof.
- USDJPY directional agreement is high, but the strict return-correlation floor is not clean across all windows.
- Depth, LVN/HVN, absorption, and heatmap questions are still blocked until event-window hypotheses are registered.
- Continuous futures roll behavior remains untested for these symbols.

## Opened Questions

1. Does 6J/USDJPY recover above the strict floor across additional dates and roll-adjacent windows?
2. Can XAGUSD and GBPUSD event-window manifests be built without label leakage or observer/live-scope confusion?
3. Does any trades-level feature add signal after controlling for symbol/session and synthetic versus actual labels?
4. Can GBPJPY price transfer be represented by synchronized 6B/6J returns without pretending the depth book is unified?

## Next Steps

1. Add XAGUSD/SI and GBPUSD/6B to research-only event-manifest tooling in a separate tested commit if needed.
2. Run one targeted 6J/USDJPY follow-up set before using USDJPY futures orderflow beyond diagnostics.
3. Keep GBPJPY orderflow blocked until both legs pass price transfer and a separate two-book feature hypothesis is registered.
4. Do not fetch mbp-1, mbp-10, or MBO for newly mapped symbols until a symbol-specific event-window hypothesis is registered.
