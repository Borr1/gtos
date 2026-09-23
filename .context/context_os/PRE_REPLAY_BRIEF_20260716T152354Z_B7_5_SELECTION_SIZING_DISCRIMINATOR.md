# B7.5 Selection-Versus-Sizing Discriminator Pre-Replay Brief

Generated: 2026-07-16T15:23:54Z.

This brief was written before any selection-versus-sizing implementation or
replay outcome was produced. It is the one current pre-replay control surface
for the next B7.5 batch. The previous cross-window/lifecycle brief remains
historical evidence for the accepted R3 route and the unaccepted April R5
artifact; it does not authorize a policy change.

## 1. Accepted Proof Boundary

The latest accepted replay authority remains:

`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_XAU_ORDERED_TICK_PORTFOLIO_RECONCILIATION_PROOF_CONSUMER_R3`

It is a same-day, broker-live-closed June 4 proof with `6981` candidates, `96`
scorecards, `12` order events, `6` physical fills, and `6975` missed rows. Five
fills are terminal-R scoreable and one is terminal-R unscoreable. Physical
economics are `+4.03591467R`, `+$2204.18020365`, and `$3027.86901650` accepted
risk cash (`3.00%`). Headline economics are `+2.12544422R` and
`+$992.62016070`. R3 has `96/96` canonical pre-risk provenance maps, zero
executed REFUSED/source-gap rows, exact behavior versus R1/R2, a zero-issue
canonical verifier, and a committed implementation at `beec3ce52`.

Accepted claim: truth and proof consumers are green for this bounded day.
Unaccepted claim: the current selector or dynamic sizing generalizes
economically. R3 grants no broad, policy, broker, live, canary, or final
authority.

## 2. Partial And Unaccepted Work

The complete April R5 artifact on disk is newer than the accepted January/April
R4 pair but is untracked and unaccepted. It contains `69` fills, `56` scoreable
and `13` terminal-R unscoreable. Its scoreable physical result is
`-2.33891543R`, `-$1779.57124`, on `$12813.25995` summed risk cash. All thirteen
unscoreable fills count in reservations and exposure; none may be assigned
zero R or zero cash.

The May/June causal-risk pair is structurally accepted but economically mixed.
May improves both R and cash versus its comparator; June improves cash while
losing equal-risk R under greater accepted risk. The ordered-tick June R3 proof
removed the suspected allocation-correctness explanation without resolving
whether the value comes from selection or risk expression.

No replay process is active. The worktree contains large preserved route and
runtime evidence plus unrelated agent/user changes. Only files explicitly
owned by this batch may be staged.

## 3. Exact Unstarted Question

Does the current quality-ranked selector add value over an outcome-blind
choice among the same hard-eligible executable options, does the current
dynamic allocator add value over a fixed equal account-risk unit, or is the
observed cash result mainly an interaction between them?

Existing compact ledgers cannot answer this. They do not retain every
alternative executable option and a post-hoc risk reweight cannot reconstruct
scheduler headroom, cluster limits, pending/open occupancy, or same-symbol
causality. Four new source-bound replay arms are required under one post-change
behavioral code digest.

## 4. Sealed Four-Arm Design

The immutable decision protocol is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json`.
Its methodological choices are sealed before implementation.

| Arm | Selection | Sizing | Attribution |
| --- | --- | --- | --- |
| `S0R0` | neutral SHA-256 rank among hard-eligible options | fixed `0.10%` account-risk unit | reference |
| `S1R0` | current quality-ranked selector/scheduler | fixed `0.10%` account-risk unit | selection only |
| `S0R1` | neutral SHA-256 rank among hard-eligible options | current dynamic allocator | sizing only |
| `S1R1` | current quality-ranked selector/scheduler | current dynamic allocator | joint incumbent |

The neutral selection key is
`sha256(sealed_seed | decision_window_id | candidate_instance_key)`. It may
change only soft rank/portfolio choice after the same source, cost, fillability,
signed-authority, lifecycle, and safety gates. It may not read terminal R,
cash, PnL, close reason, MFE/MAE, future bars, future ticks, or any postdecision
path field.

The fixed unit is `$100` on frozen initial equity of `$100000`. All arms retain
the same ex-ante daily accepted-risk cap (`4.0%`), peak open-plus-pending cap
(`4.0%`), cluster cap (`1.5%`), and opening-window cap (`1.0%`). There is no
outcome-dependent rescaling. Pending risk transfers to open once and is
released once on expiry or close.

Per window and pooled:

- selection effect = `S1R0 - S0R0`;
- sizing effect = `S0R1 - S0R0`;
- interaction = `S1R1 - S1R0 - S0R1 + S0R0`;
- total incumbent value = `S1R1 - S0R0`.

Primary economics are scoreable net cash divided by accepted risk cash. Fixed
denominator portfolio R (`net_cash / $100`), physical/headline R, actual
aggregate and event-time peak risk, scoreable-risk coverage, costs, drawdown,
stress, and tail loss remain separately reported.

## 5. Windows And Leakage Boundary

- June 4, 2026: engineering parity and four-arm smoke only. It is already
  inspected and cannot establish generalization.
- January 1-31, 2026: development window, source plan `b41714da...14d2`.
- April 1-30, 2026: adverse development window, source plan
  `4987d98c...e46d`.
- May 13-17, 2026: adverse development window. A fresh source plan must be
  built and sealed because V249 is not config-identical.
- March 1-31, 2026: untouched-for-this-treatment historical challenge. It is
  not a pristine model holdout because upstream package construction may have
  used historical candidates. Its outcomes must not be inspected until the
  development disposition and treatment choice are frozen.

The March source plan may be built from source metadata before that freeze.
No March scorecard, order, fill, terminal, R, cash, or comparative outcome may
be opened or summarized before the gate.

## 6. Implementation Boundary

Allowed behavior changes are replay-only and default-off:

- harness binding to `--decision-contract`, `--arm-id`, and an expected arm
  fingerprint;
- a neutral selection rank intervention behind the sealed replay contract;
- a fixed account-risk intervention behind the sealed replay contract;
- explicit factor, seed, contract, arm, and audit fields in canonical ledgers;
- contract builder, factorial analyzer, verifier, tests, and completion
  manifest in the new route.

The default path must remain exact `S1R1`. No production configuration, broker
route, hard halt, live flag, canary authority, or deployment authority may be
changed by this batch.

Because the code digest changes even when the intervention is default-off,
`S1R1` must be rerun. The first behavioral proof is exact June 4 parity against
accepted R3. Any unexplained candidate, scorecard, order, fill, missed,
physical/headline economic, cost, or risk delta fails the implementation and
stops broader replay.

## 7. Execution Order

1. Commit this brief and the sealed outcome-unread protocol alone.
2. Implement contract-bound default-off factors and focused tests.
3. Materialize the execution contract with post-change code/config/package and
   per-arm fingerprints, without reading new outcomes.
4. Run June 4 `S1R1`; require exact R3 behavior.
5. Run June 4 `S0R0`, `S1R0`, and `S0R1`; require deterministic hard-gate,
   cost, lifecycle, reservation, and cap proof.
6. Run all four arms on January, April, and May. Analyze candidates,
   scorecards, order/fill identity, suppression, missed positive and negative
   R, scoreability, risk timeline, and economics together.
7. Freeze the treatment disposition before reading March outcomes.
8. If the protocol gate permits, run March exactly once under all four sealed
   arms and issue the final factorial disposition.

No broad replay starts without a disk-space checkpoint. Compact ledgers and
existing immutable source assets should be reused where the verifier can prove
identity; raw evidence must not be duplicated merely for convenience.

## 8. Predeclared Decision Rules

Hard validity requires deterministic replay hashes, zero risk-cap violations,
zero executed REFUSED cost rows, zero executed source-gap rows, complete
candidate-to-scorecard-to-order-to-fill identities, scoreable-risk coverage at
least `0.80`, and no arm coverage gap above `0.05`. Unscoreable executed fills
remain null economically while retaining their risk and exposure.

Effect materiality is symmetric at `0.10` net-cash dollars per accepted-risk
dollar. Promotion additionally requires positive absolute pooled development
economics, a materially positive pooled total effect, no adverse-development
window total effect below `-0.10`, non-negative March total effect, and no
hard-safety violation. Effects inside `[-0.10,+0.10]` are inconclusive.

- promote: freeze the strongest safety-passing arm, then open only the already
  sealed challenge or forward-shadow gate;
- reject: disable the failed factor and continue with the strongest
  safety-passing arm;
- inconclusive: retain the incumbent and use only a fingerprinted shadow
  successor.

No result is positive by suppression. Candidate, scorecard, order, fill,
missed positive R, missed negative R, scoreability, accepted risk, and cash/R
must be reconciled together. Date, symbol, session, and outcome filters are not
authorized treatments.

## 9. Success, Failure, And Campaign Status

This batch succeeds only if it causally separates selection, sizing, and their
interaction under source-bound executable replay and the verifier proves the
predeclared safety and truth invariants. A favorable June smoke alone cannot
pass it. A favorable cash result produced by greater accepted risk, missing
negative outcomes, or hidden unscoreable exposure cannot pass it.

The campaign remains `IN_PROGRESS`. Even a successful economic discriminator
does not establish `CONTROLLED_CANARY_READY_PENDING_HUMAN`: forward shadow,
actual production-runtime live-as-if proof, a dedicated conservative canary
package, fail-closed halt authority, monitoring/rollback, and operator handoff
remain separate required gates.

## 10. S1R1 R2 Semantic-Parity Failure And Repaired R3 Gate

Updated: 2026-07-16T17:24:10Z, before the next broad replay.

The newest completed replay is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S1R1_PARITY_R2`.
No replay, analyzer, verifier, or pytest process is active. Free disk is `55 GiB`;
the complete R2 proof-consumer set occupies approximately `898 MiB`, so one
same-day repaired parity replay is storage-safe without deleting preserved
evidence.

R2 restores terminal and economic parity with accepted R3: `6981` candidates,
`96` scorecards, `12` order events, `6` fills, and `6975` missed rows; physical
economics are `+4.03591467R`, `+$2204.18020365`, and `3.0%` / `$3027.86901650`
accepted risk. Headline economics are `+2.12544422R` and `+$992.62016070`.
Candidate, trade, order, scorecard-key, and missed identity sets are exact, and
executed REFUSED/source-gap rows remain zero. Broker/live/final authority and
mutation remain false.

R2 nevertheless fails the predeclared exact-parent gate. Twenty-seven unchanged
missed candidate identities traverse the S0-only scheduler-soft counterfactual
path under S1. Their fills and economics remain suppressed, but existing
incumbent semantics change from `risk_probe_materialized` to `reject`: `21`
`open-reduced-risk` and `6` `reduce-risk` actions are reclassified into `17`
marketable-entry guard blocks, `7` risk-headroom-zero blocks, and one each of
opening-window, same-cluster cooldown, and same-symbol cooldown. The R3/R2
semantic projection hashes are therefore:

- missed: `0c178e58d430bd33bdf1deed28202ff28723cdcf6983dc4d7f41c9fc7d12ecae`
  versus `7b7dcf57182c50f42c4a64cd9f12ed517e3221542d4f8fa3f79be9f83067be08`;
- scorecard: `f1b18c1c2532a998ea70dd579311a180f765e156d9bd715c7efb04f0ca721c84`
  versus `ac2bac846f82d27943d1eebddd5b8ef10c23a0618afce303d33344db4a8ef638`.

This is a diagnostic/ledger correctness defect, not a performance result. It is
not accepted as schema evolution and does not authorize the remaining arms.

Historical full-grid baselines remain context rather than direct same-window
comparators: V89D `56` trades / `+34.84520454R`; V90 `51` /
`+28.84201157R`; V92 `51` / `+29.35570236R`. The direct behavioral comparator
for the repaired run remains the accepted June 4 R3 parent and the failed R2
implementation replay.

The same-root repair is confined to:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`;
- `tests/test_b7_5_neutral_selection_factorial.py`;
- the replay-free decision-contract hash/fingerprint regeneration.

S1 now materializes the incumbent scheduler-terminal probe first. A deeper
counterfactual traversal is permitted only when removing declared selection-soft
failures would make the row hard-eligible; that traversal is audit-only, cannot
enter finalizer rank selection, and is collapsed before hard-pool calculation
and every summary counter. Only `b7_5_selection_sizing_factorial_*` audit fields
are retained on the incumbent row. Mixed soft-plus-hard failures preserve the
complete incumbent failure list without traversal. S0 retains the neutral
counterfactual carry and both selection arms retain an identical hard-pool
denominator when a soft scheduler row is genuinely hard-eligible.

Independent findings are reconciled as follows:

- parity and binding audit: incorporated; R2 is semantic FAIL despite exact
  identities/economics, and all `27` affected R2 rows are hard-ineligible;
- root-cause audit: incorporated; the broad factorial carry gate caused the
  downstream reclassification;
- repair review: incorporated; audit-collapse is required for denominator
  equality, and S1 restoration is unconditional for every incumbent-ineligible
  row so mixed hard failures cannot be shortened.

Executed focused proof is `874 passed` across the complete timewarp suite plus
factorial runtime tests, followed by `47 passed` on the regenerated sealed
contract/factorial cluster. The only warning is the pre-existing unknown pytest
`asyncio_mode` option. The regenerated replay-free contract has self-hash
`a6a293216c5abc2542fe740293ed216dc83020884e6d073c62eb948417681d36`,
common input digest
`5f4cc87ba42f36089a13072b848ed596773eb0705c83e18b044ddb273eeda90d`,
and S1R1 fingerprint
`75fd29b9344002912c7789eb7db0393ef35aa6420fd0ed4237582f8183c3dc0d`.
The builder records zero outcome-ledger reads and `march_outcome_read=false`.

Expected repaired replay effect is exact semantic restoration, not better
economics: candidates/scorecards/orders/fills/missed remain
`6981/96/12/6/6975`; physical and headline R/cash/risk remain exact; missed
positive and negative R remain exact; `risk_probe_materialized` returns from
`6947` to `6974`, `reject` returns from `28` to `1`, and both semantic hashes
return to their R3 values. Any unexplained population, economic, risk, cost,
scoreability, action, reason, blocker, or semantic-hash delta fails the repaired
gate. Only that proof may authorize the other three June arms.

## 11. S1R1 R3 Exact-Parent Acceptance

Updated: 2026-07-16T17:49:57Z, after the R3 replay and its read-only semantic
audit completed.

`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S1R1_PARITY_R3`
passes the predeclared parent gate. Candidate, scorecard, order-event, physical
trade, and missed counts are exactly `6981/96/12/6/6975`. Physical behavior is
`4/1/0`, `+4.03591467R`, `+$2204.18020365`, and `3.0%` /
`$3027.86901650` accepted risk. Headline behavior is `3/1/0`,
`+2.12544422R`, and `+$992.62016070`. Missed diagnostics remain fully
materialized: `401` positive rows / `+322.45120558R`, `1070` negative rows /
`-1475.03658779R`, and `-1152.58538221R` net. Executed REFUSED-cost rows,
executed source-gap rows, and send attempts are all zero.

The exact compact semantic projections match the accepted parent with zero row
mismatches:

- missed: `0c178e58d430bd33bdf1deed28202ff28723cdcf6983dc4d7f41c9fc7d12ecae`;
- scorecard: `f1b18c1c2532a998ea70dd579311a180f765e156d9bd715c7efb04f0ca721c84`.

All `27` R2-drift identities are restored to incumbent semantics: `21`
`open-reduced-risk`, `6` `reduce-risk`, and all `27`
`risk_probe_materialized`. Exactly those rows retain the inert, outcome-free,
hard-ineligible counterfactual audit tuple. Candidate-union, trade, missed,
scorecard, and order identity hashes are exact to the parent.

Binding closure is exact: shared execution
`70eda3df1ef6ee7985f0a43d4761b862db95405de36078a5f6d56eadfecd7db7`,
source plan
`a24fc9198b11cfc447f351a7e4db4430d5c03a511dba7cee79085200bd27f001`,
decision contract
`a6a293216c5abc2542fe740293ed216dc83020884e6d073c62eb948417681d36`,
common input
`5f4cc87ba42f36089a13072b848ed596773eb0705c83e18b044ddb273eeda90d`,
S1R1 arm
`75fd29b9344002912c7789eb7db0393ef35aa6420fd0ed4237582f8183c3dc0d`,
and binding payload
`c14c8e8d371c761fd427042f8da8f8e3c9a846f377ba9f973ef0f17aa398889b`.
All materialized rows carry the sealed binding. Broker mutation, live authority,
final authority, and March outcome access remain false.

An independent post-run source audit found no concrete replay-invalidating
shadow-state or authority leak. The shadow account is deep-copied; candidate,
packet, option, and decision-input mappings are reconstructed; the audit row is
removed by object identity before hard-pool counters; and a forced S1 traversal
left caller packet, candidate, packet-map, and account state unchanged. Prefix
allowlisting and duplicate-id/forced-exception coverage remain worthwhile
defense-in-depth, but no reproducible current defect justifies changing the
sealed source digest or discarding exact R3 parity.

This acceptance authorizes only the remaining June 4 engineering arms
`S0R0`, `S1R0`, and `S0R1`. It does not promote an economic factor, open March,
or authorize policy, broker, live, canary, or final state.

## 12. Old-Source June Matrix Failure And Source-Authority Repair Gate

Updated: 2026-07-16T18:50:34Z, after all four old-source June arms completed
and before any source materialization or resolver change.

The sealed old-source June matrix is mechanically clean but fails the
predeclared absolute and cross-arm scoreable-risk coverage gates. The completed
intervention prefixes are:

- `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S0R0_ENGINEERING_R1`;
- `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S1R0_ENGINEERING_R1`;
- `BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S0R1_ENGINEERING_R1`.

Both fixed-risk arms are exact at the summary, identity, hard-pool, selected,
missed, and economic surfaces. Each has `6981/96/8/4/6977`
candidates/scorecards/order events/trades/missed, four exact `$100` fills,
three scoreable winners, one unscoreable fill, `+3.22990877R`,
`+$322.990877`, and `$400` accepted risk. Scoreable accepted risk is only
`$300 / $400 = 0.75`, below the sealed `0.80` floor. All four selected windows
have singleton hard pools, so the exact zero June selection effect is
non-discriminating rather than evidence that neutral and quality selection are
generally equivalent.

The neutral-selection dynamic-risk arm matches the incumbent S1R1 summary:
`6981/96/12/6/6975`, five scoreable and one unscoreable physical fill,
`+4.03591467R`, `+$2204.18020365`, and `$3027.86901650` accepted risk.
Its scoreable-risk coverage is
`$2776.19336275 / $3027.86901650 = 0.91688027045`, above `0.80`.
The fixed-versus-dynamic coverage gap is `0.16688027045`, above the sealed
maximum arm gap of `0.05`. The old-source matrix therefore fails both the fixed
arms' absolute coverage floor and the cross-arm coverage-comparability gate.
The dynamic arms do not fail their individual coverage floor.

Both selection effects and the interaction are exactly zero on June 4: each
nonempty hard pool is a singleton and S0/S1 select the same identities at both
risk levels. The sizing effect adds two physical and two scoreable fills,
`+0.80600590R`, `+$1881.18932665`, and `$2627.86901650` accepted risk, while
cash per accepted-risk dollar falls from `0.8074771925` to `0.7279641859`, a
`-0.0795130066` delta inside the sealed `[-0.10,+0.10]` inconclusive band.
These smoke-window effects are not generalization evidence or a promotion
result.

All completed arms have exact flushed-ledger certification, complete candidate
relational materialization, exact sealed row bindings, valid R0 or R1 risk
authority, zero cap/lifecycle failures, zero executed REFUSED-cost rows, zero
executed cost-source-gap rows, zero sends, and recursive broker/live/final
authority closure. Missed positive and negative populations remain fully
materialized. No factor or arm is accepted from the old source plan: the fixed
cells fail absolute coverage, the cross-arm matrix fails coverage comparability,
and the June hard pools provide no nontrivial selection choice.

The sole executed unscoreable row is UKOIL_cash candidate
`broadorigin_faa1c4241161583fd4a3cf29@@2026-06-04T11:30:00+00:00`.
Its entry, M1, cost, signed authority, reservation, and exposure are valid, but
the old resolver binds April-only tick components and returns zero June ticks.
The exact owner-authorized FTMO ordered-price-path source already exists in the
local legacy snapshot and matches the active manifest: `282386` rows, bounds
`2026-06-01T03:05:00.017Z..2026-06-05T23:49:57.216Z`, and SHA-256
`c9b1672454932af9600b331783b99ca83de7672ab236b63a5fd7547f8075a250`.
It is ordered-price-path evidence only, not redacted_account-native or broker
lifecycle truth.

Direct ordered-tick replay resolves the UKOIL path without ambiguity: the bid
crosses the stop at `2026-06-04T11:30:04.416Z`, before the first `+0.25R`
milestone or target. The exact row result is `-1.0R` gross and `-1.0458R` net.
Portfolio totals, later risk release, and later selected state must still be
fully replayed rather than patched arithmetically.

Simple file hydration is forbidden before a resolver repair. The current
`BroadSourceResolver.resolve_tick()` caches by symbol, searches the current root
before the integration root, and stops at the first nonempty root without a
window argument. Hydrating June under that behavior would fix June while
silently suppressing six valid April UKOIL tick extracts in April replay.

The same-root repair is therefore predeclared as:

1. key tick caching by `(symbol, source-authority window)`;
2. gather manifest-valid components across both approved roots;
3. retain only components whose declared intervals overlap the requested
   authority window;
4. deduplicate identical hashes deterministically;
5. fail closed on conflicting overlapping tick observations;
6. prove June selection of the v127 component, April preservation of its six
   existing components, and explicit no-tick authority when no component
   overlaps;
7. materialize only manifest-declared files required by active development
   windows, with exact path/hash/row/bounds verification and without raw-data
   duplication merely for convenience;
8. preserve the original sealed factor protocol and bind a source-authority
   repair amendment that changes source-plan authority only;
9. regenerate the replay-free decision contract and rerun all four June arms
   under one repaired source plan. Old-plan and repaired-plan arms may not be
   mixed.

The conditional repaired June source-plan digest is
`7e95536787006e94c1fad5fe21915879074b39655fb7d755c62883e8bed1e024`.
It remains a prediction until the repaired resolver, exact file materialization,
and fail-before-replay source preflight reproduce it. Candidate generation is
expected to remain source-identical because this repair supplies terminal tick
path evidence; every downstream scorecard/order/trade/risk/economic change must
be reconciled to the now-earlier UKOIL close and its risk-state consequences.

Development windows remain blocked until the repaired four-arm June matrix is
hard-valid. March outcome access remains false. No policy, broker, live, canary,
or final authority is granted by this repair.

## 13. Window-Aware Source Repair, R1 Conditional Failure, And R2 Reseal

Updated: 2026-07-16T19:16:00Z, after exact materialization, two independent
read-only audits, and canonical replay-free contract regeneration, but before
any repaired-source replay.

The predeclared resolver repair is implemented and independently accepted. Tick
objects are cached by symbol plus sorted authority days; both approved roots
are gathered; declared intervals are filtered to the authority window; exact
SHA-256 duplicates prefer the active root deterministically; conflicting
same-timestamp cross-source quotes fail closed at lazy query time; and selected
sources carry no rejected-alternative source gaps. The complete repair-config
file passes `197` tests, adjacent tick/oracle proof passes `12`, and the combined
resolver/factorial/contract cluster passes `246`. Compile and scoped diff checks
are clean; the only warning is the pre-existing unknown pytest `asyncio_mode`
option.

Materialization is exact and storage-preserving. Fourteen missing May v122i
files and eighteen missing June v127 files were verified against their active
manifests for path, SHA-256, row count, and first/last bounds, then created as
same-filesystem hardlinks from the exact legacy snapshot. All `48` declared
May/June files are now present; the `32` new links represent `18251729` rows and
`3899948488` logical bytes without a second raw payload allocation. June-10
v122e and March data were not materialized or read. The self-hashed audit is
`B7_5_SELECTION_SIZING_SOURCE_AUTHORITY_MATERIALIZATION_AUDIT_R1.json`, self
hash `c0498d3d106ea6eb97133125a51c7feafd72daf0ce4e6f9d312deaff3d12d31c`.

The fail-before-replay source gate correctly rejected the first conditional
digest. R1 assumed only UKOIL would be replaced while every other old,
unfiltered tick row remained. The required global window filter instead selects
exactly one active June v127 component for every one of the `24` symbols. The
old static and M1 digests remain exact, while the tick and composite digests
change. No replay or repaired-source outcome was opened before this correction.
R1 remains immutable historical evidence with file SHA
`cd019fd2cb5db43838935c571d73b24b28e8c91fbbb1bd2d8f55a9416d4103e0`
and self hash
`880061b1154894599075994b723aba23aa3b5753dc341f3afedf47784e8fb713`.

The active R2 correction is file SHA
`087811cb68736ed8f3daa924444a7bd09940f57b6dc3916efcc7c87232dbef66`
and self hash
`c6649eea6fbe83396aa25e6d978776567891f3f237e8d7a33a517b8e0cbb6a35`.
It binds the immutable protocol and R1, changes only June source authority, and
records the reproduced source plan:

- static: `ed49a9fe48e72dfb766cba7951a48496fb8954a8ae8ed048ad2aab9d97451363`;
- M1: `06f48e39610f924cd27ef81b8a2d169379248dcc1f46e779fdc9735eb676e5e5`;
- tick components: `dfcf7ecaee95f47ae9a3abf72eb1ecc17c9f1da0917b6e9363bffb2bcc1322b7`;
- tick windows: `0ec951d0759fe6e521e87ab918c10713f6024a6a27f33f010ce9ecdc183ada22`;
- composite plan: `2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434`;
- UKOIL June window: `f0aa52a1251c7c717e5d54675ed492724199f08764ba9dd504f50ee07c3efb0b`.

Real-root proof resolves all `24/24` symbols, one covered v127 component per
symbol, zero missing/incomplete sources, zero M1 unresolved symbol-days, zero
tick integrity failures, and empty selected-source gaps. The April UKOIL probe
preserves its six integration-root components with exact hashes; a July
no-overlap probe explicitly returns no tick source.

The regenerated decision contract self hash is
`de033348821d57de32008b9a6c818777d680e20bdfdb5cc4fb050cc201254220` and
its common execution-input digest is
`40f6889052cbd7c66f1b60be7594dbcd7ca9647f502d05c5665fcccbee196f3d`.
Arm fingerprints are S0R0
`091ca00f75bc5df575f005f0340583bd89319bd0e6f547d3411384a3f69703f0`,
S1R0 `e0c4cc275e93e9e24847c174890ae726a13c64789e591dc4d906661b58666047`,
S0R1 `86b51d65326383620b0231ca18478a4bdcec507fa1b90f792228b8c236299343`,
and S1R1
`c4ce81b1003c6ebc03c87d404c45123435559d8ae5a3cbb946f79c9fd08e8d7c`.
The builder remains replay-free with zero outcome reads and
`march_outcome_read=false`.

The next executable gate is a repaired-source S1R1 June replay, followed by
S0R0, S1R0, and S0R1 under the same source digest. Candidate/scorecard identity
is expected to remain source-identical, but no order, fill, close, risk,
scoreability, R, or cash total is patched or assumed: all such effects must be
fully replayed and reconciled to the newly available June tick paths and their
state-release timing. Old-source and repaired-source arms may not be mixed.
Positive-by-suppression remains forbidden. Development windows remain closed
until the full repaired June matrix passes absolute coverage, cross-arm
comparability, relational integrity, risk/cap/lifecycle, and authority gates.
March outcome access, broker mutation, live authority, canary authority, and
final authority remain false.

## 14. Repaired-Source S1R1 Hard Failure And Same-Root Cap/Lifecycle Repair

Updated: 2026-07-16T20:13:31Z, after the repaired-source S1R1 run and two
independent read-only audits. No replay is active. The remaining three June
arms are intentionally unstarted.

The latest completed prefix is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_R1`.
Its files are fully flushed and source/contract/identity valid: `6981`
candidates, `96` scorecards, `16` order events, `8` trades, `6973` missed
rows, and exact candidate and scorecard identity versus old R3. All eight
trades are ordered-tick scoreable. The diagnostic economics are `5/3/0`,
`+3.55202322R` gross, `0.63876394R` cost, `+2.91325928R` net,
`+$1752.28962531`, and `$4445.62428857` accepted risk. These figures are not an
accepted factorial cell.

The run fails the sealed common risk contract. NAS100 was serialized from
`3.875%` to `4.375%` daily accepted risk against the `4.0%` cap. Reconstructed
open-plus-pending risk peaks at `2.0%` and clusters at no more than `0.625%`,
so those caps pass; the same event-time reconstruction reaches `1.25%`,
`1.50%`, and `2.0%` inside the active NY opening window against the `1.0%`
cap. All eight fills transfer pending risk to open exactly once, but all eight
closed trade rows retain `accepted_risk_reservation_released=false`. The sealed
contract instead requires release once on expiry or close.

The immutable failure audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_R1_CAP_LIFECYCLE_FAILURE_AUDIT.json`,
self hash
`481e095431fd69cf34ccd138307493cbeb95153db8f3780a9227891c306a9606`.
It binds the summary SHA
`50ba90ef9e8018d620717d5f3c07c6c69ee2d1ba34354281e444dd0ec7ef5843`,
order SHA
`040e60eb448bd171f58ecf62f9093dc6799fd2ddcf2335a709ae606cd49816c7`,
and trade SHA
`d12871dbe9fe99f3501b7575ba177c7dc30a6d466a9d12ffb63caa4a5992275`.

The source-mediated delta is transparent rather than positive by suppression.
The repaired source removes the old unscoreable UKOIL execution but retains its
`-1.57839462R` diagnostic miss; it adds one US30 winner and UK100/NAS100
losers, changes a second US30 from the old M1 proxy to ordered-tick giveback,
and produces `-1.12265539R` and `-$451.89057834` versus old R3. No favorable
economic claim is authorized.

The same-root defect spans four seams:

1. factorial filled positions are not releasing the original reservation at
   terminal close;
2. the R1 finalizer can lift raw hard headroom to an individually admitted
   risk amount;
3. package hard-cap releases remain executable in a sealed R1 arm;
4. the summary has no fail-closed serialized event-time lifecycle audit.

The active local repair changes only:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
  (correctness and lifecycle repair);
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
  (diagnostic/ledger plus fail-closed summary repair);
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
  (proof-consumer repair);
- `tests/test_b7_5_selection_sizing_factorial_runtime.py` and affected focused
  verifier/timewarp tests (contract proof).

The intended behavior is: pending transfers to open without a second charge;
the original acceptance-day reservation releases exactly once at every
factorial scoreable, unscoreable, or scheduler full close and at terminal
expiry/cancellation; failed exact releases preserve position/pending state,
balance, counters, and queued events; raw
daily/opening/portfolio/cluster/prop/stop-hazard headroom is hard in R0 and R1;
package reserve logic cannot release those hard caps; no fractional ex-post
rescue is allowed; and the final summary reconstructs every accept, fill,
close/expiry release, profile/campaign/account/day-scoped counter, equal-time
causal transition, peak, cluster identity, and terminal zero state from
serialized order/trade rows. The deployment verifier independently consumes
that summary, checks every peak against the matched caps, scopes reused order
IDs, and fails closed on non-finite numbers.

Focused repair proof is now green. The immutable repair audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_CAP_LIFECYCLE_REPAIR_AUDIT_R1.json`,
self hash
`77eac202cf9e4f90c7f1ee3eefda0b80365c5c3605824e1abcc3e28a2f35a5e4`.
Compilation and scoped diff checks pass. The factorial runtime, replay-free
builder, broad repair-config, full timewarp, and full deployment-verifier files
pass `39 + 8 + 197 + 846 + 341 = 1431` tests; the only warning is the
pre-existing unknown pytest `asyncio_mode` option. Two independent frozen-diff
reviews pass after adversarial atomicity, cross-midnight, equal-time, scoped-ID,
peak-cap, and NaN probes. The old invalid artifact is independently reproduced
by the new audit as zero proven close releases plus the opening-window breach.

The regenerated replay-free contract is valid with self hash
`a17277c24fed922e3aeb60656831ec8c0f60f5ff44523ec76f765f0eb84890fa`,
common execution-input digest
`b09f3e8a894e26c3066fb429207174e2f5d163ffe8bbb6bd7134395321438336`,
zero outcome reads, and `march_outcome_read=false`. S1R1 is bound to fingerprint
`3db57b801f080f4c35b0bafb13c0a07b84b7ce44ab2d252f34109067acd6c35e`,
binding payload
`e72236633ef992d5289fb7b246ed5fccd4a94216f621567fd49dd41d9e25b4f3`,
and shared execution digest
`38017e04aec08fde2938c96d185b5dad1236ec7ea99a2f4488c2574304a828cd`.
The repaired source-plan digest remains
`2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434`.

Expected measurable effect before replay is deliberately not an economic
forecast. Candidate and scorecard identity should remain `6981/96`. Order and
trade counts may fall or change because the previous opening-cap admissions
were invalid. Candidate-to-scorecard transfer remains unchanged;
scorecard-to-order and order-to-fill transfer must reflect only the corrected
hard envelope and close-release chronology. Missed positive and negative R
must both remain visible. Gross/net/cash, `W/L/F`, and full/reduced risk counts
must be recomputed, not patched. Executed REFUSED-cost and source-gap rows must
remain zero. Physical accepted-risk sum may exceed `4.0%` only through proven
sequential close release, while event-time daily accepted, open-plus-pending,
opening-window, and cluster peaks must remain within `4.0/4.0/1.0/1.5%`.

The repair helps only if focused tests prove strict R1 cap behavior and
release-once semantics, the replay-free contract is regenerated for the new
code bindings, and a fresh S1R1 summary carries a valid event-time lifecycle
audit with terminal accepted/open/pending risk all zero. It fails if any cap is
crossed, any fill double-charges, any close omits or duplicates a release, any
package release bypasses a matched hard cap, candidate/scorecard identity
drifts without cause, or authority flags change. Only after that S1R1 gate may
S0R0, S1R0, and S0R1 start under the same repaired source plan. March outcome
access, broker mutation, live authority, canary authority, and final authority
remain false.

## 15. Repaired S1R1 Cap/Lifecycle Acceptance And Remaining June Matrix Gate

Updated: 2026-07-16T21:54:27Z, after a fresh from-scratch S1R1 replay, all
prefix-scoped proof-consumer scans, and an independent read-only outcome audit.
No replay is active. The remaining three June arms are authorized but remain
unstarted at this checkpoint.

The accepted bounded prefix is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_CAP_R2`.
It binds source plan
`2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434`,
shared execution digest
`38017e04aec08fde2938c96d185b5dad1236ec7ea99a2f4488c2574304a828cd`,
S1R1 fingerprint
`3db57b801f080f4c35b0bafb13c0a07b84b7ce44ab2d252f34109067acd6c35e`,
and binding payload
`e72236633ef992d5289fb7b246ed5fccd4a94216f621567fd49dd41d9e25b4f3`.
The replay-free contract check remains green with zero outcome reads and
`march_outcome_read=false`.

The final namespace has `9983` nonempty serialized rows and zero binding or
JSON failures. The exact transfer surface is `6981` candidates, `96`
scorecards, `10` order events, `5` filled trades, and `6976` missed rows. The
candidate surface is exactly the union of `6976` missed instances and `5`
traded instances. Five accepted-pending rows pair one-to-one with five terminal
filled rows and five trades; the selected scorecard, order, and trade instance
sets are exact.

The repaired lifecycle audit is valid. Five accepts transfer pending risk to
open exactly once and release the original reservation exactly once at five
terminal closes. Daily accepted, open-plus-pending, and opening-window risk all
peak at `0.875%`, against `4.0%`, `4.0%`, and `1.0%` caps. Metals, US-index,
and USD-FX clusters each peak at `0.625%` against `1.5%`. Terminal daily,
pending, and open risk are all exactly zero.

Physical diagnostic economics are `4/1/0`, `+3.55202322R` gross,
`0.38248246R` cost, `+3.16954076R` net, `+$1793.91905444`, and
`$2653.90722790` / `2.625%` summed accepted risk. These numbers pass exact
serialized trade-summary parity but do not establish an economic improvement
or generalization claim.

The suppression reconciliation is explicit. Relative to the immutable invalid
R1 artifact, candidate and scorecard counts are unchanged while orders move
`16 -> 10`, trades `8 -> 5`, and missed rows `6973 -> 6976`. The removed
executions are one US30 winner (`+2.0R`, `+1.92847698R` net) and two losses,
XAUUSD (`-1.0R`, `-1.10446455R` net) and UK100 (`-1.0R`,
`-1.08029391R` net). Their aggregate is exactly `0.0R` gross,
`0.25628148R` cost, and `-0.25628148R` net. The new headline net delta is
therefore entirely avoided cost/path suppression, not selection alpha and not
negative-only suppression. Missed diagnostics correspondingly add one
`+1.92847698R` positive and two totaling `-2.18475846R` negative, preserving
both sides of the outcome ledger.

All prefix-scoped verifier scans return empty bad counts: physical summary,
cost authority, selected-quality provenance, missed semantics, candidate
identity, selector/R identity, entry-fill-terminal lifecycle, stop-hazard cap,
atomic risk/fillability, selected-policy ordered-tick authority, and order/trade
path provenance. Summary contracts for immutable package payload, exact
candidate union, runtime inputs, capacity-safe cleanup, and source invariance
are also clean. The monolithic route entrypoint still stops before selected
prefix scans on a pre-existing unrelated missing field-parity smoke summary;
that route-global dependency is not used as S1R1 acceptance evidence.

The immutable acceptance audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_CAP_R2_ACCEPTANCE_AUDIT.json`,
self hash
`f70ee4b65eeee61755f3f47e4d83fa69e780be532b1505aa984c0afb5a59da79`.
It binds summary SHA
`c8adccc9923ea318711695a15c87f12f746778854bb97a4ce591d1bbc687d129`,
order SHA
`f0cc008642cf003157bac18daf7419d68848bb0ab7f1a58fb0d8b9b16e168b75`,
trade SHA
`baf35da77d73ca155d4eaa7a9e87f390f38c0b1395d8323601886864eb79cd1a`,
and missed SHA
`27f018e5d6086e1831a7cb3fcb18d4e6ff53dc0b05a0e971ed10e4a334cb19a7`.

The next gate is the same-day `S0R0`, `S1R0`, and `S0R1` matrix under their
sealed repaired-source fingerprints and shared digests. All three must pass
absolute lifecycle/cap/authority checks and cross-arm candidate, scorecard,
coverage, scoreability, suppression, risk, cost, R, and cash reconciliation
before January, April, or May can start. Free disk is `44 GiB`; the remaining
same-day matrix is storage-safe without deleting preserved evidence. March
outcomes stay closed. Broker mutation, live authority, canary authority,
policy promotion, and final authority remain false.

## 16. Repaired S0R0 CAP_R2 Acceptance And Exact Fixed-Dollar Reconciliation

Updated: 2026-07-16T23:12:38Z, after the S0R0 replay, prefix-scoped proof
consumption, exact R0 atomicity reconciliation, and an independent read-only
outcome audit. No replay is active. `S1R0` and then `S0R1` are the only
remaining June arms and remain unstarted at this checkpoint.

The accepted bounded prefix is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S0R0_SOURCE_REPAIRED_CAP_R2`.
It preserves the repaired June source and sealed S0R0 contract. The exact
transfer surface is `6981` candidates, `96` scorecards, `12` order events,
`6` filled trades, and `6975` missed rows. Candidate identity is exactly the
union of the six traded instances and `6975` missed instances; all six
selected scorecards, order instances, and trades reconcile one-to-one.

The lifecycle envelope passes without qualification. Six accepts transfer
pending risk to open exactly once and release the original reservation exactly
once at six terminal closes. Daily accepted, open-plus-pending, and opening-
window risk each peak at `0.2%`, against `4.0%`, `4.0%`, and `1.0%` caps.
Metals, US-index, and USD-FX clusters each peak at `0.1%` against `1.5%`.
Terminal daily, pending, and open risk are all exactly zero.

S0R0 also passes its sealed fixed-dollar contract. Every one of the `18`
execution-bound rows (`12` order plus `6` trade) binds exactly `0.10%` and
`$100` to the frozen `$100,000` initial-equity basis. Physical diagnostic
economics are `5/1/0`, `+5.55202322R` gross, `0.45400548R` cost,
`+5.09801774R` net, `+$509.801774`, and `$600.00` / `0.6%` summed accepted
risk, with `1.0` scoreable-risk coverage. These figures establish only the
bounded S0R0 cell; they do not establish economic improvement, a selection or
sizing effect, an interaction effect, or policy promotion.

The generic atomicity scan remains recorded exactly as emitted: `10 + 10`
order findings and `5 + 5` trade findings, a raw bad-count sum of `30` across
`15` unique rows. Those are duplicate-labeled false positives from applying an
evolving-current-balance cash equation to the sealed R0 frozen-initial-equity
basis. The route analyzer invoked its exact R0 reconciliation against the real
S0R0 ledgers: all `18` rows prove the frozen `$100` / `0.10%` equation, all
`15` generic rows reconcile, and unreconciled and effective bad counts are
both empty. Raw and reconciled counts remain preserved; `sample_bad` is
diagnostic-only. The reconciliation status is
`reconciled_exact_frozen_initial_equity_basis`, with complete-row proof hash
`da853574be73545643424875e32091b4923c8483a4bccf1a38f981316e59ad2b` and
analyzer hash
`9fbfb6ee79e02b67c507ab7b373b38f777d84dae569f352710d55183f9920fd5`.
This is analyzer-only proof: no generic verifier or runtime behavior changed,
and no contract reseal or replay is required for this equation disagreement.
The current focused analyzer barrier is `67 passed`; the only warning is the
pre-existing unknown pytest `asyncio_mode` option.

The immutable acceptance audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_S0R0_SOURCE_REPAIRED_CAP_R2_ACCEPTANCE_AUDIT.json`,
self hash
`f2149de6c79e8cef46f27aeebf8e6b8b88c53763479e7e5fd6f19d3beb8a4dcf`.
It binds summary SHA
`169acb63e3855fbfe4e7b8246cea0cb06c9081251b579227a4a8f4010279df55`,
order SHA
`9e1e4b74fbde618cbb62acc57fcb741f4db662e0ccc3cb68f8187c811e09ff0b`,
trade SHA
`ac9ea68bfd0e31a84055925e6629b78a466178f4537911a2381f60969f058329`,
and missed SHA
`5d824e34494415273d97bfc8ceb5e17a4ee72d1c3f6a92fb397b05b102972ae6`.

The next gate is `S1R0`, then `S0R1`, on the same June 4 repaired source under
their frozen fingerprints and shared execution digests. Only the complete
four-arm June audit may evaluate cross-arm identity, coverage, suppression,
scoreability, risk, cost, R, cash, selection, sizing, and interaction effects.
Development windows remain closed until that matrix passes. March outcomes
remain unread (`march_outcome_read=false`); economic or policy promotion,
broker mutation, live authority, canary authority, and final authority remain
false.

## 17. Repaired S1R0 CAP_R2 Acceptance And Sole Remaining S0R1 Gate

Updated: 2026-07-16T23:54:22Z, after direct frozen-contract validation of the
completed S1R0 namespace. No replay is active. `S0R1` is now the sole remaining
June arm and remains unstarted at this checkpoint.

The accepted bounded prefix is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S1R0_SOURCE_REPAIRED_CAP_R2`.
All `11` required artifacts exist and remained stable across the read-only
audit, totaling `809853859` logical bytes and `9987` nonempty serialized rows.
There are zero invalid JSON rows, binding mismatches, recursive authority
violations, per-arm validation failures, or summary-contract issues. The route
analyzer remained stable at
`9fbfb6ee79e02b67c507ab7b373b38f777d84dae569f352710d55183f9920fd5`;
the frozen verifier remained stable and exact at
`4d93308430561b7f886c88633c64a494fecdb0b3e114dff128652ebaec4dac28`.

The exact transfer surface is `6981` candidates, `96` scorecards, `12` order
events, `6` filled trades, and `6975` missed rows. Candidate identity is the
exact missed/order/trade union; six selected scorecards, order instances,
fills, and trades reconcile one-to-one. All prefix-scoped scans and five
summary contracts pass after the declared R0 reconciliation.

Lifecycle and matched caps pass. Six accepts transfer pending risk to open
exactly once and release the original reservation exactly once at six terminal
closes. Daily accepted, open-plus-pending, and opening-window risk each peak at
`0.2%`, against `4.0%`, `4.0%`, and `1.0%` caps. Metals, US-index, and USD-FX
clusters each peak at `0.1%` against `1.5%`. Terminal daily, pending, and open
risk are exactly zero.

Every one of the `18` execution-bound S1R0 rows (`12` order plus `6` trade)
binds exactly `0.10%` and `$100` to the frozen `$100,000` initial-equity basis.
The generic scan remains preserved at `10 + 10` order findings and `5 + 5`
trade findings: `30` duplicate labels across `15` unique generic false-positive
rows. Exact route-local reconciliation proves all `18` rows, reconciles all
`15`, and leaves empty unreconciled and effective counts. The complete-row
proof hash is
`49f108d382012baffcf0a43e7d56a11e52a229b788cabb89034aa0f9f49675cd`.
No runtime or generic-verifier change, contract reseal, or replay is required
for this equation disagreement. The focused analyzer barrier is `67 passed`;
the only warning is the pre-existing unknown pytest `asyncio_mode` option.

Physical diagnostic economics are `5/1/0`, `+5.55202322R` gross,
`0.45400548R` cost, `+5.09801774R` net, `+$509.801774`, and `$600.00` / `0.6%`
summed accepted risk, with `1.0` scoreable-risk coverage. Recomputed stress net
R remains `+4.79801774`, `+4.49801774`, and `+3.89801774` after respectively
adding `0.05R`, `0.10R`, and `0.20R` cost per trade; each case retains one
loss. Missed accounting preserves `851` diagnostic-positive rows totaling
`+418.86968082R`, `1214` diagnostic-negative rows totaling
`-1518.09905181R`, `4910` path-auditable unscoreable rows, and zero headline
scoreable missed R. These are bounded per-arm facts only: no economic
improvement, selection effect, sizing effect, interaction effect,
generalization, or policy claim is authorized before the complete matrix.

The immutable acceptance audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_S1R0_SOURCE_REPAIRED_CAP_R2_ACCEPTANCE_AUDIT.json`,
self hash
`6683d9b7077dcb9b28c4575e09c973c65a16d6960cb6ea973c82ad89d73679eb`.
It binds summary SHA
`411a32003315dab5c0e3648af3b386853fa35c36368f247669e71b8657b9d6f8`,
order SHA
`32ef01537592e3c84e3065b1d6523706b09fd3a10456c5e5980f94a197958156`,
trade SHA
`c3fdcccbe006275bc75d9f48de1d00e309f5bab9e25ff7b107203f59091db32d`,
and missed SHA
`17693abd76cd8f5c00a55e14a93cdb62baa09c2cdc1bb9982d6e6872765f9f27`.

The next and only replay gate is `S0R1` on the same June 4 repaired source under
its frozen fingerprint and shared execution digest. Only after S0R1 passes may
the complete four-arm audit evaluate cross-arm identity, coverage,
suppression, scoreability, lifecycle, stress, risk, cost, R, cash, selection,
sizing, and interaction effects. Development windows and March outcomes remain
closed. Economic or policy promotion, broker mutation, live authority, canary
authority, and final authority remain false.

## 18. Repaired S0R1 CAP_R2 Acceptance And Complete-Matrix Gate

Updated: 2026-07-17T00:44:09Z, after direct frozen-contract validation of the
completed S0R1 namespace and an independent read-only outcome audit. No replay
is active. All four repaired June arms have now passed their bounded per-arm
gates; the complete four-arm June matrix audit is the sole next gate.

The accepted bounded prefix is
`BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_SELECTION_SIZING_S0R1_SOURCE_REPAIRED_CAP_R2`.
All `11` required artifacts exist and remained stable across the isolated
audit, totaling `810659677` logical bytes and `9983` nonempty serialized rows.
There are zero invalid JSON rows, binding mismatches, recursive authority
violations, per-arm validation failures, raw or effective verifier findings,
or summary-contract issues. The route analyzer remains hash-bound at
`9fbfb6ee79e02b67c507ab7b373b38f777d84dae569f352710d55183f9920fd5`;
the frozen verifier remains exact at
`4d93308430561b7f886c88633c64a494fecdb0b3e114dff128652ebaec4dac28`.

The exact transfer surface is `6981` candidates, `96` scorecards, `10` order
events, `5` filled trades, and `6976` missed rows. Candidate identity is the
exact missed/order/trade union; five selected scorecards, order instances,
fills, and trades reconcile one-to-one. S0R1 is native R1: its raw and
effective generic atomicity counts are both empty, all `10` execution-bound
order rows and all `5` trade rows validate the canonical final-risk atom, and
no R0 reconciliation applies.

Lifecycle and matched caps pass. Five accepts transfer pending risk to open
exactly once and release the original reservation exactly once at terminal
close. Daily accepted, open-plus-pending, and opening-window risk each peak at
`0.875%`, against `4.0%`, `4.0%`, and `1.0%` caps. Metals, US-index, and USD-FX
clusters each peak at `0.625%` against `1.5%`. Terminal daily, pending, and
open risk are exactly zero.

Physical diagnostic economics are `4/1/0`, `+3.55202322R` gross,
`0.38248246R` cost, `+3.16954076R` net, `+$1793.91905444`, and
`$2653.9072279` / `2.625%` accepted risk, with `1.0` scoreable-risk coverage.
Recomputed stress net R remains `+2.91954076`, `+2.66954076`, and
`+2.16954076` after respectively adding `0.05R`, `0.10R`, and `0.20R` cost per
trade; every case retains one loss. Missed accounting preserves `852`
diagnostic-positive rows totaling `+420.7981578R`, `1214`
diagnostic-negative rows totaling `-1518.09905181R`, `4910` path-auditable
unscoreable rows, and zero headline scoreable missed R.

The mechanical same-R1 comparison to accepted S1R1 has the same candidate
universe, scorecard windows, and hard-pool digest, with five common trades and
five common order instances, no added or removed trade/order instance, no
stage transition, no missed-positive or missed-negative delta, no
cash-per-accepted-risk-dollar delta, and no trade, order, or execution
suppression. Five simulated order IDs differ only because they are prefix
scoped. This is identity and suppression evidence only; the full matrix is
still required for any selection, sizing, interaction, or economic claim.

The immutable acceptance audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_S0R1_SOURCE_REPAIRED_CAP_R2_ACCEPTANCE_AUDIT.json`,
self hash
`76d59407195bdbca6f3a7e392b942822055628885883e06489b33e7195ea700a`.
It binds summary SHA
`2a2408014d13a65e22d939804fb97ecfb904e32fcd1d5d0a2a799e0a6dc5fc70`,
order SHA
`5ee785f6e26087102618bafdd4b257ada0d54c9da6a968e707ac8d2fdd379e57`,
trade SHA
`3de77e7de004704e08bf44dcb6ef0983d3bc24c6361facebf456b595ee799782`,
and missed SHA
`ca28cd4d0b8976a678c2d49f9211764d9b23b3da8ac99e1331847fbd4c1dff4f`;
the audit records the remaining seven artifact hashes, bytes, and JSONL row
counts.

The next action is the committed replay-free complete four-arm June matrix
analyzer against the exact CAP_R2 namespaces. It must close cross-arm
identity, coverage, matched risk, lifecycle, scoreability, suppression,
stress, cost, R, cash, and canonical self-hash checks before any development
window opens. March outcomes remain unread. Economic, factor, policy, broker,
live, canary, and final authority remain false.

## 19. Sealed June Engineering Matrix Acceptance And Development-Window Gate

Updated: 2026-07-17T00:59:56Z, after the sealed replay-free four-arm analyzer
completed and an independent `--check` rebuild reproduced the same canonical
self hash with zero failures. The matrix audit file was unchanged across that
check. All `44` arm artifacts (`11` per arm) remained stable before parsing,
through frozen-verifier consumption, and after the audit. Candidate universes
(`6981` each), scorecard windows (`96` each), hard pools within both selection
pairs, and scoreable-risk coverage (`1.0` in every arm; gap `0.0`) reconcile.

The durable audit is
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_ENGINEERING_JUNE_04_SOURCE_REPAIRED_CAP_R2_MATRIX_AUDIT.json`.
Its file SHA-256 is
`93f652cc4a826fedbf56a0f8f861f7b8052e90a59536bf9294696d11423b91cb`
and its canonical self hash is
`9c05d91618785d461f15041caadfdc1948b1249a48798cafe343141382ddba4c`.
The frozen analyzer remains
`9fbfb6ee79e02b67c507ab7b373b38f777d84dae569f352710d55183f9920fd5`
and the production verifier remains
`4d93308430561b7f886c88633c64a494fecdb0b3e114dff128652ebaec4dac28`.

The arm-local physical facts are:

| Arm pair | Trades | W/L/F | Net R | Cash | Accepted risk | Primary q |
|---|---:|---:|---:|---:|---:|---:|
| S0R0 and S1R0 | 6 each | 5/1/0 | `+5.09801774R` | `+$509.801774` | `$600.00` / `0.6%` | `0.849669623333` |
| S0R1 and S1R1 | 5 each | 4/1/0 | `+3.16954076R` | `+$1793.91905444` | `$2653.9072279` / `2.625%` | `0.675953942768` |

The primary metric is scoreable net cash divided by total accepted risk cash,
with a closed symmetric materiality band of `0.1`. The exact June contrasts
are: selection `0.0` and interaction `0.0`, both inconclusive inside the band;
sizing and total-incumbent value are both `-0.173715680565`, classified
material-negative inside this engineering smoke. Sizing/total also change
physical net R by `-1.92847698R`, accepted risk cash by `+$2053.9072279`,
aggregate risk by `+2.025` percentage points, execution cost by
`-0.07152302R`, fixed-denominator portfolio R by `+12.8411728R`, and maximum
drawdown cash by `+$468.73623127`; scoreable-risk coverage and tail loss do
not change. Selection and interaction are zero on those scalar contrasts.

Both selection transitions are identity-neutral: S0R0 to S1R0 preserves all
six trades, six order instances, and twelve order events; S0R1 to S1R1
preserves all five trades, five order instances, and ten order events. There
are no added or removed executions, stage transitions, missed-positive or
missed-negative deltas, q deltas, or suppression in either selection pair.
Prefix-scoped simulated order IDs differ for the six and five common order
instances respectively.

Both sizing transitions, and therefore S0R0 to S1R1 total-incumbent value,
preserve five common trades but remove the same exact positive execution:
`broadorigin_29c1c0e8f3a71c07164aac14@@2026-06-04T13:30:00+00:00`.
That row contributes `+1.92847698R`, `+$192.847698`, and `$100` accepted risk
in R0. Its accepted-pending and terminal-filled order events move exactly to
one diagnostic-positive missed row carrying the same `+1.92847698R`; there
are no missing, non-comparable, R-mismatched, or negative missed transitions.
The five common dynamic-risk trades add `+$1476.96497844` cash versus R0, but
q falls by `0.173715680565`. Trade/order suppression is therefore present on
the sizing path, while positive-by-suppression, positive delta with execution
suppression, and non-comparable suppression are all false.

This result is a hard-valid June engineering smoke matrix, not an economic or
factor promotion. It authorizes only the predeclared development sequence:
January `2026-01-01..2026-01-31`, adverse April
`2026-04-01..2026-04-30`, and adverse May `2026-05-13..2026-05-17`, with the
May current-config source plan rebuilt and sealed before replay. After all
three four-arm development windows, the development disposition and treatment
must be frozen before March can be read exactly once. March remains unread and
closed now. Economic improvement, factor attribution or promotion, policy
change, broker mutation, live authority, canary authority, and final authority
remain false.

## 20. January R3 Window Control, Cold Identity, And Analyzer Adapter Gate

Updated: 2026-07-17T16:22:38Z, after both retained January large-ledger
namespaces completed cold demotion, independent full logical-byte verification,
and the January analyzer/cold-writer repair batch was committed as
`69c094ba5304e891cc7a20b527c1ad7412bbd9e2`. No January R3 arm replay is
active or complete.

### January R3 source authority

The sealed January window control is file SHA
`83cd158cc4ddeb0edb4a67c71637c56d711c0e92725c8335bc1a9da0ad238932`
and self hash
`cf2e0af3c338cdfa3a7db8b6de3ce1be25ce0b8287d5a74083d3c2f8ff601f34`.
R3 source authority is file SHA
`853f4b09acd45918fc868588b7ecef18f46b3e360a225fe958e8ef8a0684e619`,
self hash
`55ef3a65c65723521706f78ebe3466929b04874722ed1c7b2c24d60b258a2e3e`,
and active source-plan digest
`85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5`.
The old protocol digest
`b41714da59188be2ca1c4d72797521589a594ceb000a5e7f58eb3ac2ea5147d2`
is provenance-only: old-plan and R3-plan arms may never be mixed. The decision
contract remains file SHA
`614fe667024a844972cf5df02e9a923da6fe4b8087bf385769de0d69d32b741a`
and self hash
`f15ddbe2c67ee803ca88260887dc694594f793f6cbb85e0fc719f4fe14f74222`.
Check-only validation is green with zero outcome reads and no replay launch.

### Retained cold identity proofs

The retained extended-history operation is terminal PASS at operation file SHA
`01f406bddc7c6726fac8e6287e584d9e239d095a0c539dd1e26737c666e0aa9c`
and self hash
`480080a49135e035f7892419eded760f3ebaaa081967583c749f1c3a4be62a3a`.
Its independent report is file SHA
`cafdf86020ad2c30e527188609b713513095721ad6f3f68810bab46562e40d46`
and self hash
`37781852b5e78a22a2be02d4b74c5d0f726fcdfeb655350809804a4fdf2559f3`.
The retained terminal-blocker R4 operation is terminal PASS at operation file
SHA `f1a230a2edb8f774061dc4915379c7f430bac8e89482b518ac716b0726c81780`
and self hash
`3d345218c3795f1c84261348cbfdef4e459d588244a8f4bd4592ad090ffdb375`.
Its independent report is file SHA
`dda63eb54f760662ab73134ec3eca33a0ece5537fd97f9d650598a995891e6dd`
and self hash
`b2762abd0952abdbcda096a4ae1d452686e26e7a3b74081375f75aacd3ec083a`.
Both reports prove raw/cold exclusivity, compressed identities, per-shard
uncompressed identities and exact EOF, bounded full concatenated reads, stable
filesystem signatures, no retained backup or staging artifact, and no outcome
or March access.

### January analyzer adapter repair

`RawOrColdLogicalPath` previously was not iterable, so two frozen-verifier
passes could silently consume zero scorecard/order/trade/missed rows in either
raw or cold mode. The committed adapter at SHA
`a8725c2b43bf79ceaecf0deac157893b854869cf1e0d54186da6fecbd2c6664e`
now reopens a fresh logical stream for every iteration and fails closed unless
all `24` expected physical row-coverage checks reconcile to the arm artifact
map. Raw and actual-zstd-cold regressions are included; the dedicated analyzer
suite is `35 passed`, and independent review is PASS.

### Future-arm cold writer repair

The two completed retained operations preserve their historical launch
writer/test hashes. Future arm demotions use the committed writer SHA
`0bcacda6f90e1096f4b657294d908795044a1542d1b780888da60c779f420d55`
and test SHA
`cd29cf6dc11f4e246536ee61e06be920bc32ec0fe93fc6af5c58d5a76bf6315e`.
The repair temporarily buffers line reads on the same locked FileIO, then
detaches and rewinds without duplicating or closing the descriptor. Lock,
inode, immediate pre-rename rehash, rollback, line-safe shard, and exact-byte
semantics remain unchanged. The focused cold suite is `24 passed`; the full
bounded barrier is `177 passed`; independent review is PASS.

### Exact next sequence

Run `S0R0`, then the reviewed structural gate, cold-demote decision/missed/
scorecard, run an independent full logical-byte verifier, and commit that arm's
proof. Repeat exactly for `S1R0`, `S0R1`, and `S1R1`. Do not inspect interim arm
economics. Only after all four proofs may the sealed full-January analyzer run.
Cold storage and adapter correctness are provenance/correctness proof, not
behavioral or economic improvement. June remains engineering smoke only;
April and May remain unstarted; March remains unread; factor, policy, broker,
live, canary, and final authority remain false.
