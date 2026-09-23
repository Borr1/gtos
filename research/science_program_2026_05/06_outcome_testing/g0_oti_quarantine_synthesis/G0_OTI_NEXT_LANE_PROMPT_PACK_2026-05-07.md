# G0 OTI Next-Lane Prompt Pack - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Scope:** one-line starter prompts for future research-control lanes

## Ranked Starter Prompts

| Rank | Lane | One-line starter prompt | Guardrail |
| ---: | --- | --- | --- |
| 1 | `OTB2R_G10_RISKBANK_LEG_LEDGER_PACKET` | Build a frozen input-only G10 risk-bank leg-state packet for `OTG0-PKT-013` that adds leg/reentry/risk-bank/cost fields without opening outcomes, broker actual-R, blocked OTB2R packets, paid sources, or live trading surfaces. | No result scoring. |
| 2 | `OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK` | For the 9 accepted OTI1 lifecycle packets, build per-covariate source/as-of proof ledgers for friction, volatility, footprint, news, macro-attention, FOMC, and Cboe, and leave any missing legal/cache/parser proof as exact blockers. | No covariate result claim. |
| 3 | `OTB2R_G3_GEOMETRY_INPUT_PACKET_BUILDERS` | Create input-only packet builders for G3 DC overshoot, DC swing, and TDA synthetic replay preregs using local point-in-time geometry/OHLC evidence with source hashes, duplicate groups, decision_asof fields, and no result columns. | No replay outcomes. |
| 4 | `OTB2R_G6_LOCAL_OHLC_MOMENTUM_REVERSION_PACKETS` | Build input-only G6 local OHLC packets for OB-vs-generic retrace, opening-drive continuation, exhaustion changepoint, and gold round-number/OB confluence with matched denominators and no label pooling. | Do not reuse OB rows as generic controls without explicit duplicate policy. |
| 5 | `OTL3_G4_ORDERFLOW_SOURCE_ASOF_DOSSIER` | Produce a G4 orderflow/depth/profile/fill source/as-of dossier using local/Sierra/cached evidence first, and write an exact OTB4 blocker if Databento free-credit proof is required. | No Databento call without OTB4 manifest and $0 paid-spend proof. |
| 6 | `G8_CBOE_PUBLICATION_ASOF_LEGAL_DOSSIER` | Build a Cboe VIX1D/VIX9D/VVIX/GVZ/VRP source legality, publication-as-of, parser, cache-hash, and no-lookahead dossier before any G8 or OTI1 short-vol covariate result. | No same-day daily-vol use without proof. |
| 7 | `BROKER_ACTUAL_R_CLOSE_COST_JOIN_PACKET` | Build a broker actual-R packet-readiness audit that joins account history, fills, close-side cost/slippage, candidate IDs, manual exclusions, and duplicate groups while keeping synthetic and lifecycle labels separate. | No actual-R statistic until sample floor passes. |
| 8 | `G5_PROMPT_NEUTRAL_SONNET_APPROVAL_PACK` | Prepare an owner-approval pack for a bounded Sonnet-only prompt-neutral pilot with frozen prompt hashes, fixed sample, cached calls, cost estimate, and hard $20 cap before any API call. | Approval-only until owner confirms. |

## Common Required Preamble For Future Lanes

Use this preamble before any starter prompt:

```text
Complete mandatory GTOS preflight first. This is research/tooling only with NO_PROMOTION_VERDICT, validation_safe=false, and outcome_review_opened=false. Do not run new outcomes unless the prompt explicitly authorizes a quarantined result after packet readiness. Do not inspect blocked-packet outcomes. Do not edit master registries except proposed patch artifacts. Do not touch live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior.
```

## Suggested First Lane

Run rank 1 first. It has the best combination of expected edge value, local feasibility, direct continuity from OTI2, and independence from live trading behavior. It should stop at an input-only packet and a blocker ledger if leg-level risk-bank state cannot be reconstructed locally.
