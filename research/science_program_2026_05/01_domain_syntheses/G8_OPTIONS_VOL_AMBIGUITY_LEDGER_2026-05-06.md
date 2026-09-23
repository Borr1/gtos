# G8 Options, Gamma, VRP Ambiguity Ledger - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

| Ambiguity | Why It Matters | Current Handling | Promotion Verdict |
|---|---|---|---|
| Official aggregate GEX vs vendor proxy GEX | GEX estimates vary by chain coverage, open-interest timing, spot, Greeks model, and contract filters. | FlashAlpha stays forward-context/proxy only; official historical GEX remains blocked. | `NO_PROMOTION_VERDICT` |
| Public Cboe CSV availability timing | Daily rows may be available after the GTOS kill zone, making same-day joins leaky. | Any prereg must use conservative as-of availability until publication timestamps are verified. | `NO_PROMOTION_VERDICT` |
| VIX1D/VIX9D relevance to CFD instruments | Indices reference SPX option volatility, while GTOS trades broker NAS100/US30 CFDs. | Use as index-vol context only with proxy-transfer checks. | `NO_PROMOTION_VERDICT` |
| GVZ as XAUUSD/XAGUSD proxy | GVZ references gold ETF options, not spot XAUUSD or silver spot. | Treat GVZ as ETF implied-vol proxy; require mapping/basis checks and separate metals cohorts. | `NO_PROMOTION_VERDICT` |
| VRP formula degrees of freedom | Realized variance windows, annualization, tenor mapping, and close-to-close vs intraday estimators can change results. | Freeze formula before outcome review; no post-decision bars. | `NO_PROMOTION_VERDICT` |
| OPEX calendar vs actual pressure | Third-Friday proximity is not the same as gamma pinning or open-interest pressure. | Calendar-only is a weak context row; pinning requires gamma/open-interest source. | `NO_PROMOTION_VERDICT` |
| Gamma sign mechanism direction | Positive gamma can dampen movement; negative gamma can amplify, but effects depend on liquidity and proximity. | Hypotheses include liquidity/vol controls and avoid one-direction claims. | `NO_PROMOTION_VERDICT` |
| Literature-to-GTOS transfer | Academic results are often equity-index, quarterly, or broad-market; GTOS is intraday multi-instrument. | Literature used only for mechanism priors, never validation. | `NO_PROMOTION_VERDICT` |
| Label mixing risk | Source rows could be wrongly scored against broker actual-R, synthetic path-R, lifecycle no-fill, and context labels together. | Every hypothesis/prereg declares label class and label separation policy. | `NO_PROMOTION_VERDICT` |
| Same-dataset discovery | G8 discovered sources and wrote hypotheses in the same session. | Outcome review remains closed for every prereg; no promotion claim. | `NO_PROMOTION_VERDICT` |

