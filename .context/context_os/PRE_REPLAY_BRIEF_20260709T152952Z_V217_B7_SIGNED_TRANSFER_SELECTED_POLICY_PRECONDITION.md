# V217 B7 Signed-Transfer Selected-Policy Precondition Proof

## Current Completed Replay

- Latest completed bounded proof: `BROAD_LIVE_AS_IF_REPLAY_V216_B7_SELECTED_POLICY_QUALITY_ALIAS_PRECEDENCE_GUARD_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`.
- V216 behavior: 1,651 candidate rows, 192 scorecard rows, 8 order rows, 3 filled trades, W/L/F 3/0/0, net/gross/final R `+1.10761535 / +1.35101129 / +1.35101129`, cash PnL `+277.0648589`.
- V216 live/final authority: broker/live/final all false, order-send attempts 0.
- V216 verifier result: not green. `broad_live_as_if_order_executable_transfer_contract_bad` found scorecard rows with signed-soft-transfer reliance plus finite negative selected-policy reallocation quality/source incompleteness, and missed rows with signed-soft-transfer reliance but package executable not true.

## Same-Root Patch

- Batch: B7 selected executable policy/risk-finalizer authority.
- Root mismatch: signed-soft-transfer displacement was marked allowed before selected-policy executable-quality gate was applied. Later selection blocked those rows, but scorecard/missed proof surfaces still claimed signed-transfer reliance.
- Code repair: `src/research_infra/v4_timewarp_simulated_live_research_loop.py` now evaluates selected-policy executable quality before stamping signed-soft-transfer displacement allowed; blocked selected-policy quality becomes a signed-transfer failure, not an allowed displacement.
- Tests: focused timewarp signed-transfer/selected-policy cluster passed; focused verifier signed-transfer contract cluster passed.

## Expected Replay Effect

- Behavior-changing class: correctness/proof repair with possible selection neutrality. Filled trades should remain close to V216 unless blocked non-selected probes were incorrectly influencing finalizer rank.
- Expected verifier effect: scorecard/missed rows should no longer claim signed-soft-transfer reliance when selected-policy executable quality blocks them.
- Expected transfer effect: no broker-cost REFUSED/source-gap execution; broker/live/final remain false.

## V217 Targeted Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V217_B7_SIGNED_TRANSFER_SELECTED_POLICY_PRECONDITION_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`.
- Window: 2026-05-13 through 2026-05-14.
- Symbols: XAUUSD, USDCAD, USDJPY.
- Profile: repaired_package_conversion_v3 only.
- Purpose: bounded proof of producer truth; this smoke does not prove broad reservoir conversion.

## Success Criteria

- Same-window report parsed against V216: trades, net/gross/final R, cash PnL, W/L/F, order/fill/missed counts, added/removed trades.
- No executed broker-cost REFUSED/source-gap rows.
- Signed-transfer rows with selected-policy reallocation quality below floor are non-allowed/missed diagnostics, not executable reliance.
- Route verifier green after builder consumes V217 as `GTOS_BROAD_QUALITY_PARITY_PREFIX`, or exact remaining failure classified and patched.

## Prompt Hardening / Control Clauses

- Required active context: read `goal_session_research_discipline.md` and `research_operating_doctrine.md` before treating this as a reusable route prompt; these active instructions are not background and must be operationalized in the completion audit.
- Do not rely on chat memory. Use current disk artifacts, verifier outputs, manifests, ledgers, source completeness, branch decision, and implementation decision evidence.
- Full same-evidence-class pursuit applies: literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been exhausted or exactly blocked.
- Builder posture: no conservative brake; use constructive active creativity while keeping broker/live/final claims closed until proof passes.
- Result materialization standard: every behavior-changing patch must report exact-R or proxy-R, source-capture/source completeness, branch decision, implementation decision, focused test or verifier result, and artifact outputs.
- Forbidden surfaces: no production-change claim, live trading, broker operation, paid API/vendor action, broker account/order/history/deal/position mutation, prompt/config/risk/execution/safety/canary/selector change, or final/live claim without the explicit proof gate.
- No arbitrary top-N: preserve full ledger scope, all material rows, and full 82-sleeve authority; no top 3/5/10 or number-limited cutoff proof.
