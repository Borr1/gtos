# G11 Killed Or Blocked Routes

Date: 2026-05-06  
Lane: G11 Data Sources And Market Expansion  
Verdict: NO_PROMOTION_VERDICT

| Route ID | Route | Kill/block reason | Evidence basis | Future reopen condition |
|---|---|---|---|---|
| G11-KILL-001 | Direct live COT filter for XAUUSD | Prior KB says COT has not earned direct gold filter role; weekly Tuesday-to-Friday lag is too slow for M15/H1 use | Gold KB plus CFTC COT capture | Separate release-aware, preregistered study with no outcome peeking |
| G11-KILL-002 | Use FRED/BIS macro observations by observation date | Observation-date join can leak unreleased/revised values | FRED vintages/release calendar and BIS release-calendar evidence | As-of/vintage join implementation and frozen macro hypothesis |
| G11-KILL-003 | Add options/gamma/GEX feature now | Official/historical aggregate GEX, VIX1D/VIX9D, VVIX, and VRP unavailable or blocked in local source registry | LTO032 options/gamma manifest and Cboe source capture | Licensed historical source, timestamp rules, and validation-safe contract |
| G11-KILL-004 | Pull paid Databento data during G11 | Controlling prompt forbids paid data without approval; replay manifests have 0 fetch-ready requests | LTO031/LTO032 Databento manifest | CEO approval plus estimate-before-fetch and frozen request manifest |
| G11-KILL-005 | Treat Sierra footprint/profile features as ready | Bid/ask base fields exist, but stacked imbalance/profile definitions are not frozen | Sierra plan and Sierra public docs | Freeze footprint/profile definitions and unit tests before feature extraction |
| G11-KILL-006 | Promote instrument candidates from mechanical screen | No true temporal OOS resolved; costs/slippage/proxy limits unresolved | Instrument expansion and expanded OOS artifacts | Source coverage, transfer, friction, and prereg sample floors met |
| G11-KILL-007 | Use Nasdaq auction imbalance as free feature | Imbalance data is subscription-only; equity auction transfer to NAS100 CFD/NQ requires proof | Nasdaq source capture and G4 blockers | Licensed source and source-transfer experiment |
| G11-KILL-008 | Use LBMA benchmark history as free gold feature | LBMA page notes licensing requirements for real-time/historical benchmark data use | LBMA capture | Licensed historical source and as-of contract |
| G11-KILL-009 | Treat observer symbols as expansion approvals | Observer registry is for no-AI collection, not trade selection | Observer source registry | Later governed lane with unopened labels and promotion criteria |
| G11-KILL-010 | Use Databento public HTML capture for schema claims | Captured pages are JS shells with no schema content | G11 raw Databento captures | Official API docs captured in parseable form or local repo evidence |

