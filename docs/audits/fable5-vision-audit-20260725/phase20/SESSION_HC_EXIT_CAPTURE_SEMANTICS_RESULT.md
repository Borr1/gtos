# Session HC — exit collision and capture-window semantics result

## Findings

1. **The target/time-box contradiction is resolved without reopening a cell.** A hard target owns an
   exit only when its observation timestamp is strictly earlier than the first executable deadline
   observation. The time box owns a same-tick or same-M1-timestamp collision. A deadline quote beyond
   the retained +2R target remains a `time_box` exit but is capped at +2R. This is the only reading that
   preserves both the frozen priority (`time_box` before `hard_target`) and its statement that an
   *earlier* target wins. The path evaluator states and enforces the rule at
   `src/research_infra/exit_overlay.py:13-16,342-439`; the FC vectorized evaluator uses the same
   timestamp tie and cap at
   `docs/audits/fable5-vision-audit-20260725/phase19/receipts/session_fc_exit_overlay.py:622-693`.
2. **Capture windows are now verdict-moving immutable authority.** Ordered windows, declaration id,
   ordered declaration hashes, and the already-sealed blackout are all-or-none `GateSpec` fields
   (`src/research_infra/walkforward/spec.py:151-160,518-578`). A runtime argument can assert equality
   but cannot define or replace the windows (`src/research_infra/walkforward/gate.py:438-489`). The CS
   driver verifies and binds the fold plan, look addendum, and May amendment before running the gate
   (`docs/audits/fable5-vision-audit-20260725/phase19/receipts/cs_breaker_folds.py:1653-1743`).
3. **Null resampling no longer bridges discontinuous captures.** Auto-block lag products restart at
   capture boundaries while cube-root scale and the declared minimum-block cap retain the pooled sample
   size. Circular bootstrap blocks and sign-flip blocks wrap/restart inside each capture only. The
   sign-flip null marginalizes uniformly over every common circular block phase, so no post-outcome
   alignment is selected (`src/research_infra/walkforward/stats.py:182-229,317-544`; gate wiring at
   `src/research_infra/walkforward/gate.py:788-950`).
4. **Both published dispositions are preserved.** FC's 214 published `time_box` outcomes retain their
   exact economic/identity projection, SHA-256
   `d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d`. CS remains `REJECT` with the
   exact published fold means and pooled expectancy; its corrected segmented-null raw p/q are
   `0.0021158854166666665` / `0.12483723958333333`, still above the predeclared BH alpha after the
   59-member bill.
5. **The repair is offline and non-promoting.** No current rejected exit cell was reopened; FC2 remains
   unrun; no broad replay, live/runtime/config, broker, VPS, token, March-outcome, promotion, or activation
   surface was touched. `activation_authority: false`.

## Exit collision authority

The deterministic order is:

1. an observed hard stop;
2. an already-activated break-even/giveback floor;
3. the first executable deadline observation;
4. a hard target observed at a strictly earlier timestamp;
5. the terminal mark.

For ordered ticks, the same tick is the collision unit. For M1, all synthetic open/extrema/close points
share the bar timestamp, so a target touch anywhere in the first deadline-eligible bar is not treated as
strictly earlier than that bar's close. Stop/floor precedence is unchanged. The deadline action uses the
executable deadline value bounded above by the retained hard target. No result value or candidate identity
participates in collision ordering.

## Capture authority

The repaired CS capture contract is `gtos.walkforward.capture_windows.v2`:

- windows: `2026-01-01..2026-01-30`, `2026-04-01..2026-04-30`,
  `2026-05-01..2026-05-30`;
- reserved blackout: `2026-03-01..2026-03-31`;
- declaration id:
  `CS_BREAKER_FOLD_PLAN_V1+CS_BREAKER_LOOK_ADDENDUM_V1+CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1`;
- declaration hashes, in authority order:
  `31b2ab756bf9be6ae19ca7f5e40447c2de7ea905839a78a921919ca3b5bb3b85`,
  `5ab5414a4de6eb7b0ccf54f10bc2901673205120ac7754291026290303642174`,
  `94f4688dfa89a6998eaf44c25910be6b26052253a58fcd0ad3bf9c2b5d93f44b`;
- repaired spec seal: `daeb89f5700da22d4a248923b3cc0b849f356e5bb257c7ecd6c14fd800414471`;
- capture-contract hash: `5824ced4484f6cb4a902696cc3603b14f638d1086623bb62de67f63125006ae8`;
- null segments: `[11, 11, 9]` OOS days, block length 3, with no boundary bridge.

Construction rejects partial authority, malformed hashes, empty/reversed/overlapping/reordered windows,
and blackout intersection. The gate rejects an unsealed runtime definition and any runtime replacement
that differs from the sealed tuple. An identical runtime tuple is only an assertion; the gate always reads
the operative windows from `GateSpec`.

## Behavioral proof and failure sets

Added adversaries cover these exact behaviors:

- `test_target_strictly_before_deadline_retains_target_ownership`;
- `test_deadline_strictly_before_target_retains_timebox_ownership`;
- `test_same_tick_target_deadline_collision_belongs_to_timebox`;
- `test_same_m1_target_deadline_collision_belongs_to_timebox_close`;
- `test_deadline_gap_through_retained_target_is_timebox_capped_at_target`;
- `test_vectorized_analyzer_matches_same_timestamp_deadline_priority_and_cap`;
- `test_capture_authority_refuses_overlap_reorder_and_blackout`;
- `test_runtime_capture_replacement_and_unsealed_definition_are_refused`;
- `test_capture_declaration_identity_or_hash_edit_breaks_seal`;
- `test_null_blocks_restart_at_capture_boundaries`;
- `test_published_214_timebox_exit_economics_are_exactly_pinned`;
- `test_ratified_gate_seals_capture_authority_and_preserves_cs_rejection`.

Measured closure:

| Proof | Result |
|---|---:|
| Narrow exit/FC/gate/CS suite | 110 passed, 0 failed, 0 errored |
| Relevant 21-module exit/walk-forward closure | 435 passed, 1 skipped, 0 failed, 0 errored |
| Exact-parent scoped failset at `ba3c18ddf` | 511 passed, 2 skipped, 0 bad |
| Repaired scoped failset at `5693c8824` | 526 passed, 2 skipped, 0 bad |
| Failure-set diff | 0 fixed, **0 regressed** |

The parent and repaired captures use the same tool-derived 23-file scope. The machine-emitted,
self-contained `gtos-ab-receipt-v1` is
`docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HC_AB_RECEIPT.md`; both captures have an
empty failed/errored set. The captures report a dirty worktree only because the mandatory mechanical
`LIVE_STATE.md` refresh and the in-progress receipt outputs were outside the scoped source commits.

## FC and CS disposition identity

### FC

- Published exit-cell disposition: 40/40 rejected; unchanged.
- FC2: not run; unchanged.
- Published historical `time_box` outcomes: 214.
- Exact pinned projection: month, candidate id, variant id, exit reason/time, gross R, net R, source mode,
  and M1 ambiguity; canonical SHA-256
  `d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d`.
- The 3,200-case FC fast/reference equivalence check remains `PASS`, now supplemented by explicit
  same-timestamp and gap-through collisions.

### CS

- Published verdict: `REJECT`; repaired verdict: `REJECT`.
- Fold means, exact both runs: `[11.2523415098444, 7.453553638393435, 3.852045311094502]`.
- Pooled OOS mean, exact both runs: `7.519313486444113` R/day.
- Published raw p / BH q: `0.0025997400259974` / `0.1533846615338466`.
- Repaired segmented raw p / BH q: `0.0021158854166666665` / `0.12483723958333333`.
- Repaired null: exact 6,144 sign/phase assignments; three common circular phases; no block crosses a
  capture boundary.
- Ceremony: `NOT_QUEUED`; arming authority false.

## Commits and residual risks

- `d95887337` — froze the prepatch semantic contracts and TODO.
- `5693c8824` — implemented collision/capture semantics and behavioral proof; this is the verified source
  head for the result and parent A/B.
- The containing closeout commit carries this result and the compact receipts; it does not change the
  verified implementation bytes.

Residual risks and proof boundaries:

- No heavy FC route or broad replay was materialized. FC disposition identity is proven by the exact
  committed 214-outcome projection plus path/vector behavioral equivalence, not by regenerating the full
  route.
- M1 cannot reveal the order of events inside one stamped bar. The declared same-timestamp deadline rule
  makes that ambiguity deterministic and conservative; it does not invent intrabar time.
- `GateSpec` seals the declaration id and hashes; the CS driver additionally authenticates the three
  self-bound declaration files before constructing the spec. A generic caller remains responsible for
  authenticating whatever declaration hashes it claims before sealing them.
- Larger segmented sign/phase state spaces fall back to the sealed deterministic Monte Carlo budget and
  seed; CS's 6,144-state null is exact.
- The historical Wave 19 protocol and rejection receipts remain byte-unchanged. Session HC is a forward
  semantic authority repair, not a rewrite of published evidence.

`activation_authority: false`
