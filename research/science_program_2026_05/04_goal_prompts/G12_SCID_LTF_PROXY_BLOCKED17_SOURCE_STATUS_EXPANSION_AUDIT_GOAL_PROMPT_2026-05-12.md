# G12 Audit Prompt - SCID LTF/Orderflow/Proxy Blocked-17 Source-Status Expansion

Audit the source-status packet at:

`research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/`

Evidence class: `G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY`

Required audit posture: fair-adversarial. Accept source-status/control evidence only if it is disk-backed, count-correct, denominator-safe, no-leak, and verifier-backed. Do not reject the packet merely because it does not contain validation/results/performance; this lane is forbidden from opening those surfaces.

Mandatory checks:

1. Regenerate and read `.context/LIVE_STATE.md`; read `goal_session_research_discipline.md`, `research_operating_doctrine.md`, `research_current_state.md`, `local_heavy_data_inventory.md`, and the R2 controlling prompt.
2. Recompute from `G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json` that exactly 17 cards are assigned to `SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION_FOR_BLOCKED17`, with 15 blocked cards excluded and ready-8/expansion denominators untouched.
3. Verify all required R2 artifacts exist, parse, and carry `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
4. Recompute source-status values in `SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json`; reject vague statuses, unknown/TBD placeholders, or missing per-field exact blockers.
5. Verify searched roots cover current worktree, accepted source-control ledgers, shadow logs, local-heavy absolute data/tick/external roots, Sierra local data, prior worktrees, and forbidden-source exclusions.
6. Verify proxy validity/equivalence rows never claim broker-native CFD truth and preserve context/control-only use unless future proxy contracts are accepted.
7. Verify no raw market blob was copied or committed and large/raw files have hash or explicit hash-deferral policy.
8. Run the route verifier and focused tests. If they fail, report exact blockers.
9. Emit a G12 decision ledger, completion audit, no-leak audit, and next G0 blocked-card unblocking synthesis prompt/starter if accepted.

Forbidden surfaces remain closed: no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.
