# G10 Ambiguity Ledger

Generated: 2026-05-06T08:30:00Z
Lane: G10
Promotion verdict: NO_PROMOTION_VERDICT

| Ambiguity | Why it matters | Required resolution before promotion | Current status |
|---|---|---|---|
| Internal pending versus native pending | Historical `LIMIT_PLACED` can be misread as broker exposure. | Use `pending_order_mode`, `broker_pending_order_created`, `mt5_order_ticket`, and MT5 deal evidence. | Blocker retained. |
| Path touch versus executable fill | A lower-timeframe touch can occur without a broker fill or with worse market-order slippage. | Prospective lifecycle rows joined to actual order attempts and fills. | Blocker retained. |
| Entry slippage without close-side cost | Entry fills alone cannot price exit policy quality. | Close-side slippage, commission, swap, and broker deal close rows. | Blocker retained. |
| Broker actual-R versus synthetic path-R | Candidate/no-fill and synthetic path labels can inflate evidence if mixed with realized broker outcomes. | Separate label classes in every hypothesis and prereg. | Controlled by schema rows. |
| Missing original POI bounds in historical replay | Prefill path coverage cannot reconstruct exact touch/expiry logic without the original bounds. | Prospective capture of POI type, bounds, decision close, and expiry. | Blocker retained. |
| Same-bar order ambiguity | Intrabar TP/SL/fill ordering can flip R outcomes. | Ordered tick or M1 sequencing plus ambiguity flags. | Blocker retained. |
| J46/J49 exit attribution | BE, TP2, time stop, and close costs can confound each other. | Target-trial arms or frozen comparator rows with per-arm attribution. | Preregistered only. |
| Risk-bank reentry accounting | A profitable partial leg can mask total worst-case risk if open re-entry stops are ignored. | Per-leg realized/open stop/cost risk-bank ledger with hard -1R invariant. | Design-only. |
| Prop-firm rule drift | Daily/max-loss and reset-time rules are time-sensitive and vendor-specific. | Official source contracts with cache timestamps, parser, and update policy. | Validation_safe=false. |
| Portfolio concentration | Candidate frequency, fills, and correlation gates are clustered by symbol/session/month. | Effective-N and cluster-aware DSR/PBO policy. | Inherited from G1. |
| G9 missing neighbor | AI/ML systems synthesis may affect execution/risk labeling or model-selection leakage rules. | Rerun neighbor pass after G9 commits. | Blocker retained. |

Final ambiguity verdict: NO_PROMOTION_VERDICT.
