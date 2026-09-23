# G11 Ambiguity Ledger

Date: 2026-05-06  
Lane: G11 Data Sources And Market Expansion  
Verdict: NO_PROMOTION_VERDICT

| Ambiguity ID | Ambiguity | Why it matters | Current resolution | Promotion effect |
|---|---|---|---|---|
| G11-AMB-001 | "Data source expansion" could mean adding sources to live decisions, research-only manifests, or market expansion infrastructure | These have different risk levels and approval requirements | Interpreted as research-only primitive-science source and market-expansion mapping | Blocks all live changes |
| G11-AMB-002 | "Market expansion" could mean symbol promotion | Instrument expansion outputs are mechanical-only and source-limited | Treat as source/feasibility hypotheses, not symbol promotion | Blocks selector changes |
| G11-AMB-003 | Databento public documentation captures are JavaScript shells | Local capture does not prove schema details | Use G4/local Databento source index and cache manifests for details; raw capture only proves access page existence | Blocks technical Databento claims from public capture alone |
| G11-AMB-004 | Sierra bid/ask volume is available, but footprint/profile definitions vary | Stacked imbalance, VAH/VAL, and profile levels can be implementation-defined | Record bid/ask volume and depth fields as source-ready; defer profile/imbalance definitions | Blocks derived Sierra features |
| G11-AMB-005 | COT data can be public and historical, but the predictive role differs by instrument | Gold KB already warns against direct COT filter use | Keep COT as context-only until a separate release-aware prereg proves otherwise | Blocks direct COT features |
| G11-AMB-006 | FRED/BIS observation dates differ from publication and revision dates | Hindsight joins can fabricate macro timing edge | Require release/as-of timestamp joins and vintage handling | Blocks validation-safe macro use |
| G11-AMB-007 | Options/gamma sources exist, but official historical aggregate GEX and VRP are not locally complete | Partial/paid source availability can bias stress-regime findings | Treat Cboe/FlashAlpha/volatility data as source-blocked or forward context only | Blocks options/gamma validation |
| G11-AMB-008 | Broker CFD symbols and exchange/futures proxies may not align intrabar | Source-transfer mismatch can invert lead/lag or liquidity signals | Require per-symbol transfer diagnostics before feature testing | Blocks proxy-derived features |
| G11-AMB-009 | Current observer symbols are not necessarily expansion candidates | Observers are data collection containers, not endorsements | Use observers only for eligibility/source/lifecycle diagnostics | Blocks observer-to-live promotion |
| G11-AMB-010 | Existing source manifests list local raw files, but not necessarily normalized numeric features | A raw cache can be mistaken for model-ready data | Source contracts distinguish raw cache from allowed feature role | Blocks numeric feature use |
| G11-AMB-011 | Public source pages may update after capture date | Current source descriptions and access rules can change | Cache path and capture date are recorded; future work must refresh | Blocks stale-source promotion |

