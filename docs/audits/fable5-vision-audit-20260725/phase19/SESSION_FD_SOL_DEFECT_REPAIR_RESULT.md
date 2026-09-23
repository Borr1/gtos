# Session FD — Sol defect repair result

**Status:** COMPLETE — all nine commissioned defect classes are closed at the strongest safely provable boundary. Four residual evidence classes remain explicitly unmeasured; none is filled with a proxy or outcome fit.

**Branch:** `phase19/sol-defects`
**Base:** `f8c05d0ac6feefc505ba3ec3f387de4e8068fef7`
**Code commits:** `08b7ea41a4b1b729b93b5b98032e373b4c274699`, `626bc94e4532e4c89c2c8af05db22c893c7485e0`, `c86820faf56a6cfd2169ef31917704a437fcea97`
**Test hardening commit:** `deca2481945f94c66e71a5f0c0e90d2fc9cdcd72`
**Reproduction commit:** `29b4a995a4c1e3920f0f3386538d79c473b6a593`

## Boundary held

The repair read January 2026 and the owner-mandated February 2026 arm only. Every February result carries `owner_mandate_20260801` and is used for defect attribution only. No March or live-forward outcome was read. No full replay, VPS access, broker-capable script, activation token, live service, policy activation, or live-behavior change occurred. Candidate joins use `candidate_id + decision_time_utc`.

The bound replay loop was not edited. The repairs live in the unbound train capture/consumer layer and declare themselves sealed-incompatible where appropriate.

## Result by defect

| ID | Defect | Result |
|---|---|---|
| FD-01 | Flat `cost_r=0.12` and `cost_missing` | Closed. Zero broker-true commission now heals the nested packet, replaces the emitter fallback with the complete component sum, and re-runs the native gate. Legacy 0.12 remains recorded but non-authoritative unless row provenance or the February arm receipt binds the re-decode. |
| FD-02 | Missing packet/repair status and full/compact key drift | Closed. Packet provenance is flattened before footprint projection, the frozen attribution helper is wrapped additively, and both full and compact paths emit the canonical blocker key and composite identity. |
| FD-03 | BTC/oil spread placeholders claimed as measured | Closed semantically. The static floors are now `historical_template_floor`, `templated_not_decision_measured`; exact-value legacy inference is disclosed. Missing decision-time bid/ask remains an exact recapture requirement. |
| FD-04 | `close_mark_source` overloaded with outcomes | Closed. Legacy value is preserved separately; outcome and source are canonicalized, with absent source left absent. |
| FD-05 | Ambiguous binary population | Closed. The consumer emits separate `exact_contract_endpoint_population` and `terminal_outcome_first_touch_population`; the old name survives only as a deprecated exact-endpoint alias. |
| FD-06 | Selector reject re-injection | Closed as deliberate local-replay softening, not a wiring accident. Explicit authority/scope fields were added. Composite joins prove zero accepted pending instances and zero trades from the re-injected sets in both months. |
| FD-07 | A-not-B authority plumbing | Closed at capture boundary. Numeric-disagreement demotion remains intentionally off; nested signed-authority failures are flattened for future rows, and missing historical payloads receive an exact capture requirement. |
| FD-08 | Unscoreable terminal rows, cost rebases, flat slippage | Closed semantically. Two January trades are diagnostic-only with no authoritative net R; exact sums, explicit rebases, and unexplained residuals are distinct; 0.02R is labelled a configured model constant. |
| FD-09 | EV/default authority defects | Closed semantically without outcome fitting. The record now distinguishes indirect probability cost sensitivity from the unwired direct EV term, marks the 1.5R/2R geometry mismatch, name hash, 0.55 confidence default, and 0.92 fill template non-authoritative, and preserves policy behavior. |

The machine-readable register at `research/operations/wave19_sol_repair_2026_08_01/defects/DEFECT_REGISTER.json` contains root-cause `file:line`, magnitude, repair, tests, verdict impact, and residuals for every row above.

Final verification also exposed one ancillary pre-existing defect in the same train module: `_exact_content_key` promised mapping-order independence but hashed a non-canonical `frozenset` pickle. The parent failed 6 of 64 fixed hash seeds. `cuts.py:252` now sorts typed frozen pairs by their protocol-5 frame; the repair passes all 64 seeds and changes memo-key canonicalization only, not decisions or frozen function results.

## Reproduced magnitude

### Flat 0.12R cost

The February ledger contains 17,716 affected physical rows and 3,555 scoreable rows:

- GER40: 13,196 physical / 1,635 scoreable. Recorded mean 0.12R versus component re-decode 0.333507473R. Scoreable net changes from -457.043336230R to -712.117011599R; 18 signs flip.
- UKOIL_cash: 2,532 / 1,203. Recorded mean 0.12R versus 0.067010369R. Scoreable net changes from -256.208730920R to -198.249660512R; 36 signs flip.
- USOIL_cash: 1,988 / 717. Recorded mean 0.12R versus 0.077987289R. Scoreable net changes from -159.335224410R to -140.810044130R; 13 signs flip.

Aggregated scoreable net changes by -178.589424681R, with 67 sign flips. That aggregate is not a uniform bias: the fallback undercharged GER40 and overcharged both oils. The February repair receipt proves all lookups applied, zero unpriced calls, matching per-symbol counts, and zero broker-true commission for these symbols; this authorizes the complete-component re-decode for this arm only.

The root cause is the combination of the non-positive-total fallback at `src/research_infra/v4_timewarp_simulated_live_research_loop.py:58929`, the later zero-commission stamp at `:58965`, and the old truthiness check in `src/research_infra/train_engine/repairs.py@f8c05d0ac:350`. The repair is at `src/research_infra/train_engine/repairs.py:277` and the authority decoder at `src/research_infra/train_engine/decision_semantics.py:308`.

### Projection and schema

All 129,165 February missed rows lacked `pretrade_cost_packet_status`, repair status, and canonical `final_blocker_class`; all carried the long legacy blocker key. The scoreable full/compact composite join is nevertheless exact at 24,239 keys with zero missing, extra, or blocker-value mismatches. That proves schema drift rather than population drift. `cuts.py:947`, `cuts.py:1030`, and `cuts.py:1184` repair future capture; `cd_pool.py:162` repairs the compact consumer.

### Template spread authority

Exact template values occur on 11,915 January and 9,189 February physical rows across BTCUSD and the two oils; none retained quote-source provenance. The normalization at `decision_semantics.py:234` stops these values from being treated as decision-time measurements. Their numeric bias is not recoverable without historical predecision bid/ask.

### Terminal and binary semantics

`attach_close_mark` writes the terminal label into `close_mark_source` at `v4_timewarp_simulated_live_research_loop.py:63341`: 34/57 January trades and 29/58 February trades are overloaded. The evidence normalizer separates them at `decision_semantics.py:501`.

The February exact endpoint population is 3,660 stops / 950 targets (20.6073753%), while the terminal first-touch population is 11,499 / 2,811 (19.6436059%). The 0.9637694 percentage-point difference is secondary to the denominator mismatch: 4,610 versus 14,310. January has 3,270 / 678 exact endpoints, but its old missed projection dropped every terminal label, so first touch is not evaluable. `cd_pool.py:338` and `:357` now name both populations explicitly.

### Replay softening and authority gates

Router-reject re-injection is deliberate package-level replay softening (`v4_timewarp_simulated_live_research_loop.py:75743`; repaired-profile configuration at `replay_acceleration_attempt5_typed_sparse_runner.py:10477`). It occurs on 3,526 January and 2,001 February physical rows. The scoreable subset is -32.432205280R in January and +11.915624790R in February, so even its diagnostic sign is unstable. Exact composite joins find zero accepted pending orders and zero filled trades from either set. `decision_semantics.py:573` now emits the original/effective actions and `local_replay_only_no_broker_authority` scope.

Numeric-disagreement open-reduced authority is intentionally disabled at `replay_acceleration_attempt5_typed_sparse_runner.py:10454`; it was not re-enabled. The defect was evidence loss: 4,603/4,894 January and 2,760/3,145 February authority-gate rows lack a machine-readable failure payload. `decision_semantics.py:606` now extracts nested failures before projection and emits the exact missing capture when none exists.

### Terminal, cost, slippage, and EV authority

The two terminally unscoreable January composite instances are:

- `broadorigin_93c40ba45797157dc9acbf04@@2026-01-06T11:30:00+00:00`
- `broadorigin_b3f78f96213eb50b5b8c7452@@2026-01-15T15:45:00+00:00`

Their recorded diagnostics are preserved; authoritative net R is null. Trade cost accounting is 39 exact / 17 explicit rebase / 1 unexplained in January and 2 / 33 / 23 in February. Residuals remain residual. Every missed row and every trade uses the configured 0.02R slippage value from `config/agent_config.yaml:740`; it is now `modeled_constant_not_measured`.

All 153,425 January and 129,165 February candidate rows satisfy `expected_net_r = candidate_ev_r - cost_r` within 5e-10 and carry the explicit 0.55 confidence default. Cost already affects probability and source weights (`v4_timewarp_simulated_live_research_loop.py:58106`), but the returned context omits the direct cost field read at `probability_debate_v4.py:760`; the caller subtracts cost once at `v4_timewarp_simulated_live_research_loop.py:67450`. The repair therefore documents the exact scope instead of wiring a second charge. The scoreable compact pools contain 19,452/27,658 January and 17,052/24,239 February rows at the 0.92 marketable-limit template.

## Implementation

- `src/research_infra/train_engine/decision_semantics.py` — pure backward-compatible evidence normalization and authority classification.
- `src/research_infra/train_engine/repairs.py` — complete zero/nonzero commission packet healing and native re-gating.
- `src/research_infra/train_engine/cuts.py` — provenance wrapper plus missed/terminal projection integration; all new runtime patches are evidence-only and sealed-incompatible. It also canonicalizes exact memo mapping keys after the final suite proved the old key was hash-seed dependent.
- `docs/audits/fable5-vision-audit-20260725/phase14/receipts/cd_pool.py` — canonical compact normalization and population naming.
- `tests/research_infra/test_wave19_sol_decision_semantics.py` — 16 behavioral regressions.
- `research/operations/wave19_sol_repair_2026_08_01/defects/analyze_decision_defects.py` — reproducible January/February streaming census with path and month guards.

## Verification

- New regression file: 16 passed.
- Existing train-engine hydrated parent run: 158 passed. The same pre-existing suite intermittently exposed the mapping-key defect; seeded A/B makes it deterministic: parent 58 passed / 6 failed across 64 hash seeds, repair 64/64 passed. The final full repair run is the completion receipt authority.
- Behavior subset for numeric disagreement/projection/compact pool: 3 passed, 97 deselected.
- Probability-debate suite: 10 passed.
- The new regression file fails on the base at collection because `decision_semantics` does not exist, proving the base lacks the repair surface.
- R2 enforced-input drift remains the same three pre-existing paths seen at preflight; none of the changed implementation paths is contract-bound.

JUnit, A/B, bound-contract, and final verification receipts are under `research/operations/wave19_sol_repair_2026_08_01/receipts/`. `phase19/receipts/SESSION_FD_COMPLETE.json` is the closing authority.

## Residual unknowns and executable next evidence

1. Placeholder spread bias: capture a historical predecision tick with bid, ask, tick time, source path, and source hash at or before each decision. Until then the floor is a template.
2. Historical signed-authority failure member: regenerate through the repaired projection so the nested immutable-payload failures are flattened before the footprint cut.
3. One January and 23 February cost residuals: retain the explicit geometry/rebase inputs that explain recorded total minus component sum; do not distribute the residual heuristically.
4. Two January terminal paths: supply an ordered tick sequence across entry-to-terminal or keep them diagnostic-only.
5. EV/confidence/fill calibration: any policy experiment must jointly align reward geometry, direct-versus-outer cost subtraction, remove/name-hash influence as decided, and calibrate confidence/fill out of sample. This session deliberately did not fit January or February outcomes.

None of these residuals blocks the delivered capture/semantic repairs. Each blocks only the stronger claim named above.
