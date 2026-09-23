# Session HDC — independent exit/capture semantics falsifier result

**Disposition: SAFE ONLY WITH REVIEWER COMMITS. HC is not safe as-is.**

Builder head reviewed: `82c41b122364c4ef56612a5468867fe796bd6c1a`.
Reviewer implementation: `ffff7542cd39e7f1546bc9d5cbecb580f73ecac0`.
Activation authority: **false**.

## Findings, ordered by severity

1. **HIGH — HC's common circular phase rule was not implied by the frozen
   procedure and moved the admission decision.** The frozen sign-flip
   implementation partitions from the first observation. The sealed capture
   declarations supply three real temporal origins. HC instead declared those
   origins nuisance phases and coupled one phase label across all captures.
   That added an unsealed prior over three joint alignments. It is not invariant
   to relabelling one capture's phase: a result-independent synthetic known
   answer moves from `0.640625` to `0.671875` after rotating only the second
   capture. The smaller ex-ante composition is therefore: restart blocks at
   each sealed capture and anchor block zero to that capture's first OOS day.
   This changes CS from HC's `raw p = 0.0021158854166666665`,
   `BH q = 0.12483723958333333`, **REJECT**, to
   `raw p = 0.0009765625`, `BH q = 0.0576171875`, **ADMIT**. The
   economic series, fold means, thresholds, and 59-member bill do not change.

2. **MEDIUM — HC's fast FC path disagreed with its reference state on 70 of
   3,200 rows.** Gross R, net R, reason, and time happened to agree, so HC's
   selected assertions missed it. When a giveback trigger and hard target were
   first touched on the exit observation, the vector path reported a
   post-outcome protective floor that the row state machine never installed.
   The first mismatch was case 18 / `V00_IDENTITY_CURRENT`: reference floor
   `-1.0`, fast floor `+1.7`, reason `hard_target`. The repair excludes
   the exit observation from ratchet history and makes the frozen verifier
   compare every shared state field
   (`session_fc_exit_overlay.py:709-733,815-827`). An independent third
   oracle now agrees with both implementations on all 3,200 rows.

3. **MEDIUM — a sealed empty capture could disappear behind enough other
   evaluable captures.** HC assembled empty local slices but the later sample
   gate only counted pooled evaluable folds. Four declared captures with three
   valid folds could therefore satisfy the global minimum while the fourth
   contributed nothing. The gate now returns `NOT_EVALUABLE` unless every
   sealed capture contributes an evaluable OOS slice
   (`walkforward/gate.py:733-760`). The gate reuses existing fold-capture
   telemetry rather than duplicating it.

4. **LOW — two fail-open declaration/configuration shapes remained.** Repeated
   capture-declaration digests and one-day captures are now refused
   (`walkforward/spec.py:541-583`; `walkforward/folds.py:319-353`).
   Direct construction of an exit cell can no longer combine alternatives
   outside the frozen 40-cell family
   (`exit_overlay.py:111-153`). Neither defect changed an existing FC or CS
   economic row.

No evidence supports reopening any rejected FC cell. No FC2 run was made.

## 1. Frozen authority reconstructed

### FC

- Protocol file SHA-256:
  `173b6be4dcd7a1e55248cd5f00dfcad4a09ebefd80b1739acc054ee04037f422`.
- Family: 40 unique default-off cells.
- Common envelope: hard stop `-1R`, hard target `+2R`, terminal horizon
  120 minutes, full source cost once after partial-size accounting.
- Time-box rule: target wins only when observed at a strictly earlier timestamp;
  exact tick/M1 timestamp collision belongs to the time box.
- FC executed-replay canonical self hash:
  `f2b3dbd8e837a98f7232b9c91fce9c41e9a94f88e60a9902843fc421c533639c`.

### CS

- Captures, in authority order:
  `2026-01-01..01-30`, `2026-04-01..04-30`,
  `2026-05-01..05-30`.
- Reserved blackout: `2026-03-01..03-31`.
- Declaration:
  `CS_BREAKER_FOLD_PLAN_V1+CS_BREAKER_LOOK_ADDENDUM_V1+CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1`.
- Declaration hashes:
  `31b2ab756bf9be6ae19ca7f5e40447c2de7ea905839a78a921919ca3b5bb3b85`,
  `5ab5414a4de6eb7b0ccf54f10bc2901673205120ac7754291026290303642174`,
  `94f4688dfa89a6998eaf44c25910be6b26052253a58fcd0ad3bf9c2b5d93f44b`.
- GateSpec seal remains
  `daeb89f5700da22d4a248923b3cc0b849f356e5bb257c7ecd6c14fd800414471`.
  No threshold or capture declaration changed.
- V27 declaration file:
  `b70c512c52e12c37e2ca5c25de13f5eb90afc29ab73253ddab3038c731cf8251`;
  59 unique declared members, 57 looks taken, exactly one billed breaker
  member.
- Broker-cost artifact:
  `bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd`.

The R2 decision contract was inspected from the committed git object because
the sparse checkout excludes that path. None of the six changed implementation
paths is an R2 common-behaviour, package-authority, verification-tooling, or
deferred-verification binding. No fixture hydration was needed.

## 2. Defensible temporal state machine

At each ordered executable observation the rule is:

1. apply an already-resting hard stop;
2. apply an already-activated protective floor;
3. if this is the first deadline-eligible observation at/after the deadline,
   close as `time_box`;
4. otherwise update MFE and activate the cell's one declared trigger action;
5. apply the hard target unless the observation has the first executable
   deadline timestamp;
6. if still open, update the giveback floor for the next observation;
7. after the path, use the final observation as `horizon_terminal_mark`.

This yields the following known answers:

- target strictly before executable deadline: `hard_target`, capped at `+2R`;
- deadline strictly before later target: `time_box`;
- exact tick collision: `time_box`;
- same M1 timestamp, either synthetic extrema order: target is not treated as
  earlier than the close; the close owns the time box;
- delayed first deadline-eligible point: a target with a strictly earlier
  timestamp still owns the exit; otherwise the delayed eligible point owns it;
- favorable gap before deadline: `hard_target` at `+2R`;
- favorable gap at deadline: `time_box` at `+2R`;
- favorable gap after deadline: unreachable because the earlier deadline has
  already closed;
- adverse gap through hard stop: `hard_stop` at `-1R`;
- active floor and deadline collision: the resting floor wins;
- gap through both an active floor and hard stop: the conservative hard-stop
  floor wins;
- partial harvest: declared fraction is realized at its trigger, remaining
  size is valued at the eventual exit, and source cost is subtracted once.

M1 high/low order is never chosen from the favorable result. Both admissible
orders are replayed and the lower net outcome is retained. Deadline ownership
uses the source timestamp and explicit close eligibility, not a
post-outcome ordering.

## 3. FC identity and economics proof

The independent projection reproduced all **214** historical time-box rows:

- January: **100**;
- February: **114**;
- full identity:
  `month + candidate_id + decision_time + symbol + side + variant_id`;
- canonical HC projection SHA-256:
  `d4f129400a85486577895888367b3ee5ea8054d4e5478de0e693e9d870bec76d`.

For every overlay row, independently:

- `net_r = gross_r - record.cost_r` within the artifact's serialized
  precision;
- every time-box gross result is at or below the retained `+2R` target;
- January train/holdout and February daily sums, total/mean gross and net,
  reason counts, source-mode counts, M1 ambiguity counts, and positive-row
  counts reproduce `OVERLAY_RESULTS.json` for all 40 variants.

The reviewer oracle and both executable implementations agree on all **3,200**
frozen comparisons over gross, net, reason, exit index/time/R, partial amount,
remaining fraction, trigger state, MFE, and protective floor. HC's implementation
had 70 protective-floor mismatches; the reviewer commit has zero.

**FC disposition is unchanged:** 40 published cells remain rejected; no cell
was reopened, selected, promoted, or rerun.

## 4. Capture authority and ordering proof

The gate refuses:

- any partial three-field capture authority;
- empty/reversed/overlapping/reordered/blackout-overlapping windows;
- one-day windows that cannot contain local train and OOS evidence;
- empty or invalid declaration identity/hash sets, including duplicate hashes;
- a runtime definition when GateSpec has no sealed capture authority;
- runtime replacement with a different window set;
- any post-serialization edit to declaration id/hash/window;
- any trade or label span outside its owning capture;
- any sealed capture with no evaluable OOS slice.

Legacy specs with all capture fields absent preserve their old canonical seal.
Serialization round trips preserve the three capture authority fields and seal.

April 30 and May 1 are touching calendar days. They remain two explicitly
declared independent captures: fold construction, AR lag pairs, bootstrap
blocks, and sign blocks restart at that boundary. The HDC capture-contract hash
is `7d9b375fb2994608ef9a25acda301416aded00e82f8ca9442227241f44ac9fec`;
the change from HC's
`5824ced4484f6cb4a902696cc3603b14f638d1086623bb62de67f63125006ae8`
is the explicit touching-boundary policy/telemetry, not a threshold or capture
change.

The independently priced OOS order is January, April, May, with segment lengths
`[11, 11, 9]`. The rounded 12-decimal, equal-by-fold weighted pooled series
hashes to
`dc5074e539897850eb9bd6426f533bb5953a3f5a25f1c8b037494008410c510a`.
Cube-root/AR block choice retains pooled `n = 31`; only lag products restart at
capture boundaries. Fixed blocks clamp to a short segment explicitly and never
cross it. Bad length sums fail.

## 5. Null rule, selected without using CS's q-value

The method decision was made from the frozen procedure and transformation
structure:

- the pre-HC sign-flip code anchors its first block to observation zero;
- the capture declarations bind three observation-zero dates;
- no frozen artifact declares a random circular origin or a shared phase
  across captures;
- a common phase couples otherwise independent capture labels and fails its
  own nuisance-phase invariance test;
- the capture-start-anchored block sign assignments form one finite
  transformation group. HC's union of three phase-specific partitions does
  not.

Therefore the rule is:

`capture_start_anchored_sign_blocks; blocks_restart_at_each_capture`.

For CS:

- block days: `3`;
- segment blocks: `[4, 4, 3]`;
- total blocks: `11`;
- exact states: `2^11 = 2,048`;
- right-tail states: `2`;
- exact permutation p: `2 / 2,048 = 0.0009765625`;
- exact p-floor: `1 / 2,048 = 0.00048828125`;
- seed is non-operative under exact enumeration;
- segmented circular-bootstrap p:
  `1 / 10,001 = 0.00009999000099990002`;
- `both_conservative` selects the larger p:
  `0.0009765625`.

When the sign state space exceeds the sealed permutation budget, the same
anchored transformation draws from the frozen seed and uses the add-one
Monte-Carlo estimate. Equal-budget exact/sampled transition, deterministic
seed replay, block counts, and p-floors are pinned by tests. The add-one
fallback follows Phipson and Smyth's random-permutation guidance
([2010 paper](https://pubmed.ncbi.nlm.nih.gov/21044043/)); exact enumeration
is preferred when the finite transformation group fits
([exact randomization discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC6405018/)).
The circular bootstrap remains within each capture, consistent with the
within-series circular-block construction
([Politis and Romano technical report](https://statistics.stanford.edu/technical-reports/circular-block-resampling-procedure-stationary-data)).

Equivalent whole-capture label order and complete-block relabellings leave the
exact tail unchanged. An arbitrary within-capture rotation is deliberately not
called equivalent: it changes which outcome belongs to the sealed first OOS
day. That temporal origin is authority, not a nuisance chosen after outcomes.

## 6. CS economics, multiplicity, and every p/q delta

Independent reconstruction, without calling `run_gate`, produced:

- raw records: `11,305`;
- RECORDED population: `6,536` kept, `4,769` dropped,
  `0` unpriceable;
- broker-cost coverage: `1.0`;
- fold means:
  `[11.2523415098444, 7.453553638393435, 3.852045311094502]`;
- equal-by-fold pooled OOS mean:
  `7.519313486444113 R/day`;
- family: 59 declared, 57 looks taken, 58 members padded at `p=1`.

The deltas are:

| Procedure | Tail calculation | raw p | BH q (m=59) | Verdict |
|---|---:|---:|---:|---|
| Published continuous adjacency | add-one MC, `26/10001` | 0.0025997400259974 | 0.1533846615338466 | REJECT |
| HC segmented common phase | exact, `13/6144` | 0.0021158854166666665 | 0.12483723958333333 | REJECT |
| HDC segmented capture anchor | exact, `2/2048` | 0.0009765625 | 0.0576171875 | **ADMIT** |

The first delta removes manufactured adjacency but adds three coupled circular
phases. The second removes that unsupported phase prior and enumerates only the
frozen anchored sign group. Since this is rank one and the other 58 members are
`p=1`, each q-value is `min(1, 59 * raw_p)`. No economic value, capture,
block length, alpha, family member, or cost changes between the last two rows.

The repaired driver reports
`RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED` and ceremony
`ACTIVATION_DOSSIER_REQUIRED_BEFORE_QUEUE`, `arming_authority: false`.
HDC did not create a dossier, queue the candidate, set a risk dial, arm it, or
grant activation authority.

## 7. Complexity review

HC added **833 / removed 53** Python lines across 11 files relative to
`ba3c18ddf`. HDC does not hide its own proof cost: the reviewer commit adds
**1,084 / removes 120** Python lines relative to HC, overwhelmingly independent
known-answer/adversarial tests.

The decision-bearing null primitive itself was simplified:

- `block_permutation_p`: **144 lines → 102 lines**;
- common-phase allocation loop removed;
- per-phase result telemetry removed;
- joint sign/phase state-space telemetry removed;
- `stats.py` is **7 net lines smaller** than HC even after adding explicit
  exact/MC floor metadata and invalid-budget guards.

No walk-forward redesign was made. Capture completeness reuses existing
fold-capture metadata. Exit cells are restricted to the six frozen one-action
shapes instead of supporting undeclared hybrids.

## 8. Verification

### Focused properties and known answers

```text
tests/research_infra/test_exit_overlay.py
tests/research_infra/test_session_fc_exit_overlay.py
tests/research_infra/test_walkforward_gate.py
tests/research_infra/test_session_cs_breaker_folds.py

146 passed, 0 failed, 0 errored
```

Key proof nodes:

- `test_independent_state_machine_reproduces_all_3200_fast_and_reference_rows`
- `test_all_214_timebox_identities_and_economics_reproduce_independently`
- `test_temporal_state_machine_edge_table_matches_row_path_and_oracle`
- `test_cs_economics_segments_and_59_member_bill_reproduce_without_run_gate`
- `test_ratified_gate_seals_capture_authority_and_applies_anchored_exact_null`
- `test_common_phase_coupling_fails_its_own_capture_rotation_premise`
- `test_segmented_null_alignment_exact_sampling_and_bad_lengths_are_explicit`
- `test_every_sealed_capture_must_contribute_an_evaluable_oos_slice`

### Independently selected closure

Thirty-one exit, walk-forward, family, fidelity, trainer, validation-integrity,
FC, CS, and true-UTC gate modules:

```text
576 passed, 2 skipped, 0 failed, 0 errored
```

The skips are pre-existing conditional tests. Warnings were the repository's
unknown `asyncio_mode` pytest option and one pre-existing test returning a
dict.

### Exact builder-head A/B

The tool-emitted, embedded `gtos-ab-receipt-v1` is at
`phase20/receipts/SESSION_HDC_AB_RECEIPT.md`.

```text
before 82c41b122: 526 passed, 2 skipped, 0 bad
after  ffff7542c: 562 passed, 2 skipped, 0 bad
failure-set delta: 0 fixed, 0 regressed
bad node identities before: []
bad node identities after:  []
```

The before capture was taken before implementation edits. Its dirty bit was
only mandatory preflight/reviewer documentation state; the builder source and
test scope were exactly `82c41b122`. The after capture was clean.

All changed Python files compile. `git diff --check` passes.

## 9. Reviewed and created commits

Reviewed:

- `ba3c18ddf268294813545501f84b635ccc0f25bb` — HC base;
- `d95887337a7298a66607bb4729c6c7188a3c5454` — freeze HC contracts;
- `5693c8824e5f410326e51035636c61f8792b2ed2` — HC implementation;
- `82c41b122364c4ef56612a5468867fe796bd6c1a` — HC closeout/builder head.

Created:

- `48a461ce290c13bc05124b693d1901bcc648bcb3` — freeze HDC TODO;
- `ffff7542cd39e7f1546bc9d5cbecb580f73ecac0` — reviewer repairs and proof;
- closing documentation commit — this result, A/B receipt, and completion
  receipt (identified by its scoped closeout subject in git history).

## 10. Residual risks and hard boundaries

- Sign-flip exactness still assumes block-level sign symmetry. Realized R is
  bounded and skewed. The separately segmented centred circular bootstrap is
  retained and the gate takes `max(p_bootstrap, p_permutation)`; here the
  sign-flip p is the conservative/binding one.
- There are only 31 OOS daily observations. ADMIT means the frozen ratified
  research gate now passes; it does not establish live-path fidelity, activation
  readiness, size, or payout.
- M1 replay can only bound unknown extrema order. It cannot recover tick order.
- CS's original declaration sealed block days/seed/captures but did not spell
  out a segmented alignment policy. HDC's anchor is the smallest composition of
  the frozen continuous algorithm and sealed capture origins. Future capture
  declarations should name the alignment explicitly before outcomes.

No broad replay was run. No March or live outcome was read. No runtime, config,
broker, VPS, token, production, live-trading, promotion, queue, dossier, or
activation surface was mutated. No merge or push was performed.

**Final review status: SAFE ONLY WITH REVIEWER COMMITS.**
**activation_authority: false**
