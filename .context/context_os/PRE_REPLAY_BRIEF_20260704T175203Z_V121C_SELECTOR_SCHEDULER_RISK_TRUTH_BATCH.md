# V121C Selector/Scheduler/Risk Truth Batch Pre-Replay Brief

Broker/live/final remain closed. Local replay/package authority remains full. This is a bounded one-day repair checkpoint, not a full-reservoir conversion claim.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121B_EXACT_BOUND_RISK_INTENT_SOURCE_GAP_CLOSURE_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-15..2026-05-15`
- Scorecards/orders/trades/missed: `96 / 26 events (13 unique) / 4 / 8161`
- W/L/F: `0/4/0`
- Net R: `-3.80274600`
- Gross/final R: `-3.36900465`
- Cash PnL: `-379.74586967`
- Expired unfilled: `9`
- Executed REFUSED/source-gap rows: `0`
- Delta vs V120F: no behavioral delta.

V121B proved that ladder/provenance fields were present, but not that exact-bound risk intent changed allocator behavior.

## Active Process State

No broad replay is running. Stale `git diff --numstat` helpers were cleared. Do not start another replay until the verifier/current-prefix proof tooling patch is done and focused tests pass.

## Comparator Context

V89D/V90/V92 are hostile five-day comparators only. Do not compare the V121C one-day smoke to the full million-R reservoir.

| Run | Window | Trades | Net R | Gross/Final R | Cash | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |

## Subagent Findings

- Dalton: incorporated. Signed exact-bound risk intent existed in missed rows but was not allocator-visible. V121C now carries bounded `risk_per_trade_pct` into allocator selected-cell/requested risk only when signed, cost-passed, source-complete, and exact-bound.
- Wegener: partially incorporated. V121B equals V120F; reallocation probes still admit/select zero. V121C addresses risk transfer first; fill-floor/reallocation/lifecycle remain the next C-chain leaks if replay still does not transfer.
- Curie: queued before replay. The verifier can prove an older prefix while the current root map points to V121B. This must be patched before trusting any V121C proof.

## Patched Same-Root Batch

Correctness repairs:

- Preserve raw `selector_action` / `selector_reason`; materialized package authority is emitted as `effective_selector_action` / `materialized_selector_action`.
- Rebind selected scheduler score-component proof to the exact preserved selected option.
- Export `execution_fill_shortfall_score_penalty_weight` through `scheduler_config`.
- Align repaired reduced-risk execution-drag floor to `0.80` and shortfall penalty weight to `2.50`.
- Allow signed `bounded_package_risk_per_trade_pct` to become allocator selected-cell risk intent when selector selected-cell risk is explicit zero.

Diagnostics:

- Add selected scheduler score-component proof fields.
- Add bounded risk transfer provenance before allocator construction.

Focused verification before the next patch: `py_compile` passed; focused pytest `5 passed, 1 warning`.

## Known Mismatch Classes

- source-bound -> candidate: bounded smoke omits candidate ledger, so candidate-generation proof remains scoped.
- candidate -> selector: raw/effective selector truth repaired.
- selector -> scheduler: score-component and exact selected-option proof repaired.
- scheduler -> risk: bounded exact risk now transfers before allocator veto.
- risk -> order: REFUSED/source-gap rows must remain non-executable.
- order -> lifecycle/fill: passive queue, guarded fallback, expiry, and lifecycle/reallocation remain open after replay if new rows still do not fill.
- fill -> exit: exit/stop geometry remains open, but should follow transfer truth.
- ledger -> verifier: current-prefix proof selection is not trustworthy until patched.

## Next Patch Before Replay

Patch verifier/proof tooling:

- `verify_denominator_to_deployment_execution.py`: fail if selected proof prefix differs from `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json` latest prefix unless an explicit override is passed; fail if current-prefix required artifacts are missing.
- `audit_provenance_and_flags_v114.py`: parse list-valued `pretrade_cost_refusal_reasons` into multi-reason family counts and preserve spread-floor/cost-quality source status.
- Verifier count pins: make snapshot count assertions opt-in with a pin argument rather than unconditional replay trust gates.

## Replay Criteria After Verifier Patch

Run targeted one-day V121C first, then broaden only after the same-root batch proves itself.

Helped if:

- nonpositive selected/requested-risk blockers drop or move to exact downstream blockers;
- selected scheduler score component fields are present;
- added/removed orders and trades are causally attributed;
- cost REFUSED/source-gap execution remains zero.

Failed if:

- nothing changes and nonpositive risk remains the dominant exact-bound blocker;
- any REFUSED/source-gap row becomes executable;
- positive movement comes only from suppressing opportunity;
- verifier proves a stale prefix.
