# G8 Options, Gamma, VRP Context Ledger - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

## Search Plan

1. Re-read the G8 goal prompt, G0 wave-1 reconciliation, master registry, source-contract registry, budget ledger, and schema contracts.
2. Re-read local LTO-032 options/gamma source-readiness and manifest docs before accepting or modifying any blocker.
3. Cross-check repo overlap in external-feed code, OPEX calendar features, and volatility features.
4. Fetch public sources only where allowed, cache raw responses, and index status before writing claims.
5. Convert mechanisms into schema-bound rows with explicit killed-route checks.
6. Read neighbor outputs after first synthesis pass. G2 existed and was read; G7/G10 did not exist.

## Local Context Read

| File | What It Changed |
|---|---|
| `research/program_control/LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md` | Kept official/historical GEX, VIX1D/VIX9D, and VRP validation blocked absent legal timestamped sources. |
| `research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md` | Confirmed FlashAlpha Basic forward proxy and local FRED/CBOE status before G8 source refresh. |
| `research/program_control/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.md` | Confirmed validation_safe=false for official/historical GEX, VIX1D/VIX9D, VRP, and FlashAlpha forward proxy. |
| `research/program_control/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | Reused source-state language and avoided treating proxy sources as validated. |
| `.context/04_agents/PHASE_3_FREE_FEED_SPRINT_PLAN.md` | Confirmed option/gamma regime was high-prior but source-specific; no official free aggregate dealer GEX. |
| `research/ml_program/scripts/features/time_session.py` | Found existing OPEX calendar feature overlap; G8 should not duplicate the feature. |
| `research/ml_program/scripts/features/volatility.py` | Found existing realized-vol/ATR/GARCH/fat-tail overlap; VRP must add implied variance source and strict no-lookahead realized variance. |
| `scripts/fetch_external_feeds.py` and `src/components/external_feeds.py` | Confirmed FlashAlpha and FRED infrastructure exists, but no Cboe volatility-index source registry row is active. |
| `research/science_program_2026_05/01_domain_syntheses/G2_STOCHASTIC_TAILS_SYNTHESIS_2026-05-06.md` | Neighbor lane reinforces that vol/gamma rows are source-blocked context until validation-safe contracts exist. |

## Source Refreshes

| Refresh | Result | Follow-up |
|---|---|---|
| Cboe VIX/VIX1D/VIX9D/GVZ/VVIX/VIX3M CSVs | Public CSVs fetched and cached, through 2026-05-05 | Add registry/parser/publication-time/no-lookahead tests before any model use |
| Cboe methodology/product pages | VIX1D methodology, selected-vol methodology, VIX/SPX/VIX options specs cached | Use only as context until source joins exist |
| FlashAlpha API page | Free-tier/vendor GEX endpoint docs cached | Keep local Basic proxy forward-context only |
| Academic gamma/VRP literature | Barbon/Buraschi gamma fragility, NBER demand-based option pricing, Fed VRP context cached | Use as mechanism context only |
| SSRN/OCC/Cboe alternate specs | Several routes blocked 403/404 | Record blockers; do not bypass |

## Evolving Questions

- Are Cboe public volatility-index CSVs legally usable for internal research caches under current repo policy after license review?
- What is the conservative publication timestamp for daily Cboe CSV rows? Until known, next-calendar-day availability is safer than same-day KZ joins.
- Can FlashAlpha Basic provide replayable historical endpoint responses within free-tier limits, or is it strictly forward collection for GTOS?
- Should G8 source work prioritize VIX1D/VIX9D/GVZ/VVIX cache/parser before paid aggregate GEX?
- Is OPEX pressure testable with the existing third-Friday calendar feature alone, or should it remain blocked until gamma/open-interest state is available?

## Stale Refreshes

- The older "VIX1D/VIX9D source blocked" state is now partly stale: public CSVs were found. The correct refreshed state is "public Cboe CSV discovered but validation_safe=false."
- The official/historical GEX blocker is still current.
- The VRP blocker is still current because a formula and no-lookahead realized-variance estimator are not frozen.

