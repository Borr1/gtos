# G7 Ambiguity Ledger

Generated: 2026-05-06T08:30:00Z
Lane: G7
Promotion verdict: NO_PROMOTION_VERDICT

## Ambiguities

| ID | Ambiguity | Why It Matters | Blocking Decision | Evidence Needed |
| --- | --- | --- | --- | --- |
| G7-AMB-001 | DXY/gold inverse relation may be causal, common-factor, or regime-dependent. | A hard DXY filter could remove good trades in low-R2 regimes. | Treat DXY as context-only; no hard filter. | Decision-time DXY/broad-dollar cache, close-time rule, regime split, and OOS path test. |
| G7-AMB-002 | Real yields are daily/slow while GTOS decisions are M15/H1. | A daily rate print can leak if same-day availability is assumed incorrectly. | Use as slow context only until publication/close timestamp is proven. | FRED/Treasury source with timestamp, daily close availability, and no-lookahead test. |
| G7-AMB-003 | COT report date differs from publication availability. | Tuesday positions are not known until after CFTC release. | COT cannot enter decision rows without release timestamp and cache confirmation. | CFTC release calendar, parser, cache hash, and report-to-available mapping. |
| G7-AMB-004 | Futures COT categories may not map cleanly to spot/CFD FX and XAUUSD. | Mis-mapping could create false FX or gold positioning features. | FX COT and contract mapping remain blocked. | Explicit contract taxonomy, symbol map, roll policy, and validation-safe mapping tests. |
| G7-AMB-005 | FOMC effect may be anticipation, release shock, press conference, or post-event digestion. | Combining all windows can hide or fabricate signal. | Split pre-event, release, and post-event windows in preregs. | Fed event timestamps, source version, and event-window definitions frozen before outcomes. |
| G7-AMB-006 | LBMA fix timing is not the same as auction imbalance/order flow. | Timestamp-only labels cannot prove benchmark-driven flow. | Allow fix-window cohort labels only; block flow claims. | Legal auction imbalance/depth source, or accept timestamp-only non-flow test. |
| G7-AMB-007 | WGC/ETF/central-bank flow data are slow and may be revised. | Slow flow context may not align with M15 execution windows. | Use monthly/weekly context only, with vintage/as-of rules. | Series metadata, revision policy, and frozen publication timestamps. |
| G7-AMB-008 | BIS/global-liquidity series are broad and low frequency. | Broad macro data may explain regimes but not individual trade outcomes. | Use as context-only source candidate. | Exact BIS tables, SDMX endpoint, release cadence, and sample floor. |
| G7-AMB-009 | Cross-asset stress overlaps existing correlation/risk gates. | Research rows could accidentally imply live risk changes. | Compare offline only; no gate or risk edit. | Frozen cross-asset state labels and separate analysis from live gate decisions. |
| G7-AMB-010 | Local FRED/WGC/CFTC/LBMA audit notes mention rows not visible in the current working-tree data cache. | Claims could rely on unavailable or gitignored data. | Treat as prior audit context, not validation input. | Visible cache path, row counts, hashes, and refresh logs. |
| G7-AMB-011 | `data/DXY_D1.csv` exists but appears stale/suspicious for official DXY scale. | Bad proxy can create false DXY conclusions. | Do not use it for validation. | Official or authorized DXY/broad-dollar source with parser and sanity checks. |
| G7-AMB-012 | G8 and G11 lanes have not produced committed outputs at this HEAD. | Cross-domain integration could invent dependencies. | Add blocked placeholder hypotheses only. | Committed G8/G11 source-safe rows and artifacts. |

## Counter-Evidence Decisions

- Direct gold COT predictor: killed for this lane because local gold research found zero predictive value at 1-week and 4-week horizons.
- Hard DXY filter: killed for this lane because local evidence demotes DXY to low-R2 soft context.
- Macro prompt injection: blocked by live-prompt no-touch rule and stale roadmap status.
- Fix-window flow interpretation: blocked without legal auction imbalance/order-flow source.
- Vol-surface conditioning: blocked until G8 runs and commits source-safe rows.

## Residual Uncertainty

The strongest remaining uncertainty is source governance rather than mechanism plausibility. Macro/cross-asset mechanisms are plausible at the right horizon, but this pass found no validation-safe source capable of promoting a trade decision. The next useful work is exact source-contract hardening, not outcome review.

Promotion verdict: NO_PROMOTION_VERDICT
