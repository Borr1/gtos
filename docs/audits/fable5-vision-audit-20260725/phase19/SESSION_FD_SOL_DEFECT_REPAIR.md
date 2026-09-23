# Session FD — Sol data and decision-cycle defect repair

Wave 19. Blocks B3200-B3249. Branch phase19/sol-defects. Model: gpt-5.6-sol at max reasoning effort.

## Authority and objective

Root-cause and repair the concrete plumbing and decision-cycle defects recovered by Session FA. This is an implementation lane: trace each issue to file and line, quantify bias, fix every safely provable defect in this branch, and verify behavior. When a repair needs unavailable source data, build the exact capture/re-decode path and receipt instead of stopping at a blocker.

## Read first

1. CLAUDE.md preflight items 1-2.
2. docs/audits/fable5-vision-audit-20260725/phase19/SESSION_FA_BROAD_FORENSIC.md.
3. /Users/borr/.hermes-action-node/workspaces/personal-core/GTOS_WAVE19_SESSION_FA_RECOVERY_20260801.md.
4. Phase-1 cartographer, calibration, funnel_feb, trades_jan, and trades_feb outputs at /Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/research/operations/wave19_broad_forensic_2026_08_01/.
5. January and February lane source plans/registries and their pinned engine fingerprints, read-only.

## Absolute boundaries

- Never read March 2026 or live-forward outcomes.
- February use is defect attribution only and must carry owner_mandate_20260801 provenance.
- No VPS, broker-capable scripts, activation tokens, live services, or policy activation.
- No full replay while CS owns the heavy slot. Focused tests and bounded fixture-level reproductions are allowed.
- Other worktrees are read-only. Write only here.
- Preserve existing user changes and use composite candidate identity.

## Defects to close

1. February flat cost_r 0.12 and cost_missing for UKOIL_cash, USOIL_cash, and GER40: distinguish missing capture input from emitter fallback; quantify bias; repair the emitter/capture contract and add regression tests.
2. Missing February pretrade_cost_packet_status; null repair-status fields despite charged commission; full-ledger versus compact-pool key drift. Repair schema/projection parity with backward-compatible tests.
3. BTCUSD and oil spread placeholders: locate provenance, classify measured versus templated, repair unsupported authority claims, and make placeholder status explicit in emitted data.
4. close_mark_source overloading with terminal-outcome strings: separate source and outcome semantics and update consumers/tests.
5. Reconcile exact endpoint versus close-reason binary populations; fix ambiguous naming/receipts so hit-rate and breakeven consumers cannot silently mix definitions.
6. Selector router-reject re-injection: determine deliberate replay softening versus wiring fault, census executed exposure, and implement an explicit auditable authority field or correct the path.
7. A-not-B signed/open-reduced authority gates: trace configuration and repair mismatched authority plumbing when provable.
8. Two terminally unscoreable January trades, cost component/rebase accounting, and flat 0.02 slippage authority: correct field semantics and provenance; do not invent broker measurements.
9. EV context defects from Phase 1: dead cost hooks, pre-rewrite geometry mismatch, origin-family hash input, constant confidence/fill templates. Repair what can be made semantically correct without fitting outcomes; make remaining defaults explicit and non-authoritative.

## Required method and outputs

- Reproduce each defect before patching and add a regression test that fails on the base behavior.
- Implement narrow, default-safe repairs. Do not alter sealed production policy or activate candidates.
- Emit research/operations/wave19_sol_repair_2026_08_01/defects/DEFECT_REGISTER.json with root cause, file:line, bias, magnitude, repair, test, and verdict impact.
- Write docs/audits/fable5-vision-audit-20260725/phase19/SESSION_FD_SOL_DEFECT_REPAIR_RESULT.md.
- Produce focused test receipts, scoped A/B receipt, exact changed-file inventory, and a closing commit.
- Write phase19/receipts/SESSION_FD_COMPLETE.json only after final verification, recording branch, commit, tests, outputs, and residual unknowns.

Do not end with a list of defects only. Close them or leave an executable, higher-information repair path with exact missing evidence.
