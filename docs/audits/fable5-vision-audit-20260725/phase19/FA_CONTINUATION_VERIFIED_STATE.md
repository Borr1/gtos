# FA continuation — verified state appendix (frozen 2026-08-03)

Companion to `SESSION_FA_CONTINUATION.md`. The executing session reads this file **second**
(after the commission core) and treats it as its state map. Every claim carries a tag:

- **[VR]** VERIFIED-BY-RECEIPT — recomputed or read directly on 2026-08-03 by the
  commissioning session's agents, against committed receipts or raw artifacts.
- **[AP]** ADOPTED-PENDING-A2 — a Sol/wave-20 claim with receipts on its branch, not yet
  independently recomputed. Phase A2 spot-recomputes the marked ones.
- **[CT]** CONTESTED — the repo carries two incompatible answers. Phase A1/A2 adjudicates.

A refutation of any tagged row invalidates THAT row, loudly, in the RESULT doc — never
silently. Nothing here is inherited as fact past its tag.

---

## §1 Where everything is

| artifact | path | tag |
|---|---|---|
| Original commission (owner mandate 2026-08-01 verbatim) | this worktree `docs/audits/fable5-vision-audit-20260725/phase19/SESSION_FA_BROAD_FORENSIC.md` | [VR] |
| FA Phase-1 route (76 files, 1.7 MB) | this worktree `research/operations/wave19_broad_forensic_2026_08_01/{priors,cartographer,funnel_jan,funnel_feb,scorecard,calibration,trades_jan,trades_feb,defects}` — committed by this commit; byte-verified 76/76 vs FG manifest (receipt `phase19/receipts/forensic/FA_ROUTE_BYTEVERIFY_20260803.json`) | [VR] |
| FA workflow state + persisted scripts | `~/.claude/projects/-Users-borr-GTOSActive-worktrees-wave19-broad-forensic-20260801/98effd87-573e-44dc-bce2-9006f5900645/workflows/` — `wf_e24aa067-5c3.json` (fa-foundations, 8/8 done, 1,439,199 tok), `wf_28ee496d-b11.json` (fa-attribution, 5/5 died on weekly limit, ZERO output — its `status: completed` means "dispatch finished", not success), scripts under `workflows/scripts/` | [VR] |
| Cold copy of the route + CS raw + JUnits | `/Users/borr/GTOSColdEvidence/wave20-preservation-20260801/fa_phase1/` (88 files, 2.3 GB) | [VR] |
| FG source manifest (the SHA authority for the route) | `wave19-sol-integration-20260801` worktree, `phase19/receipts/FG_PHASE1_SOURCE_MANIFEST.json` | [VR] |
| FG synthesis + FG-authored FA result (INPUT TO VERIFY) | same worktree: `phase19/SESSION_FG_SOL_REPAIR_INTEGRATION_RESULT.md`, `phase19/SESSION_FA_BROAD_FORENSIC_RESULT.md`, `phase19/receipts/FG_REPAIR_REGISTER.json` | [VR paths; contents AP] |
| CS gate authority | `wave19-breaker-folds-20260801` worktree, `phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json` (self_sha256 60c0f50f…) + `phase19/SESSION_CS_BREAKER_FOLDS_RESULT.md` | [VR] |
| CR result + capture gaps | `wave19-ny-metals-capture-20260801` worktree, `phase19/SESSION_CR_NY_METALS_CAPTURE_RESULT.md` | [VR] |
| Wave-20 sealed suite baseline | `wave20-control-20260801` worktree, `phase20/receipts/WAVE20_EXACT_SUITE_BASELINE.json` + `WAVE20_EXACT_SUITE_BASELINE_RESULT.md` — **12,809 passed / 2 failed / 0 errored**, 12,974 collected, 388-rule sparse profile, Python 3.14.4 / pytest 9.1.0, durable JUnit in cold evidence | [VR] |
| WAVE20 preregistered DAG | `wave20-science-preregistration-20260801` worktree, `phase20/WAVE20_SCIENCE_PREREGISTRATION.md` (412 lines; authorizes no execution itself) | [VR] |
| January pools + path sidecar | `wave18-path-pools-20260801` worktree, `phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` (3,229,819 ordered post-decision observations, 120-min horizon, bid/ask-correct), `CQ_FROZEN_99_CELL_GRID_V1.json`, tools `cq_path_pool_grid.py` / `cq_repair_gate.py` | [VR] |
| January re-clocked truth (CJ) | `wave16-rematerialization-20260731` worktree, `phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/` (57-trade identity table), `CJ_RECLOCKED_POOL_S0R0_V1.json`, `pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` (27,658 rows); arm route untracked under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/` | [VR] |
| February truth (CP) | `wave18-true-utc-factory-20260801` worktree, `phase18/receipts/` (`CP_FEBRUARY_*`, 58-trade table, `CP_TRUE_UTC_B_TIME_MAP_V1.json` — 83 cells all negative) | [VR] |
| True-UTC lane input registry | `wave16-rematerialization-20260731` worktree, `.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json` — exactly four windows (jan/feb/apr/may), `clock_rule: new_york_plus_7` | [VR] |
| Iteration ledger of record | `phase14/receipts/TRAINING_LANE_ITERATION_LEDGER.jsonl` (3,362 rows: CK 1,903 / CP 1,177 / CQ 201 / CO 29 / CJ 24 / CD 14 / CH 12 / CL 2 — **zero FA rows**) | [VR] |
| Repairs registry (the pattern to author in) | this worktree `src/research_infra/train_engine/repairs.py` — `--repairs` vs `--patches`, paired inert controls, `INCOMPATIBLE_REPAIRS`, `REPAIRS_THAT_DO_NOT_APPLY` | [VR] |
| Tick corpus (spread truth source) | `/Users/borr/GTOSActive/vps-ticks-20260726/` — 263,894,769 rows, 2026-06-18..07-24, broker WALL-CLOCK time (+7h NY rule; per-file `.timebase.json`); `FTMO_BTCUSD/UKOIL_cash/USOIL_cash_ticks_*.csv.gz` all present | [VR] |
| HV uncommitted P1 work (adopt-or-kill at A0) | `wave20-p1-m1-verifier-repair-20260802` worktree: untracked `src/research_infra/p1_offline_complete_path_runner.py` (3,092 lines) + test + `phase20/receipts/science/P1_FILL_AUTHORITY_PREREGISTRATION.json`; its referenced output hold `/Users/borr/GTOSActive/p1-offline-result-hold-20260802` **does not exist** | [VR] |
| HDF A/B comparator worktrees (VOLATILE — preserve at A3) | `/private/tmp/gtos-hdf-final-14c0e2a`, `/private/tmp/gtos-hdf-hc-82c41b1`, `/private/tmp/gtos-hdf-hdc-32d045a` — vanish on reboot | [VR] |
| P1 packet holds (byte-identical payloads, 3 manifests) | `/Users/borr/GTOSActive/p1-upstream-source-packet-hold-20260802/` (HN) and `...-canonical-hold-20260802/` (HP); two orphaned partials ("repaired2"/"repaired3") that HP forbids resuming | [AP] |

## §2 Data budget (definitive, 2026-08-03)

| window | true-UTC pack | state | notes |
|---|---|---|---|
| Jan 2026 | `packs/january_2026_runtime_v3` | **BURNED** (dev) | CJ re-clock; read by CJ/CQ/CS/FA/Sol. Free for development. [VR] |
| Feb 2026 | `packs/february_2026_runtime_v2` | **BURNED** (used-once VAL, 2026-08-01) | CP first read; FA/Sol attribution under `owner_mandate_20260801`. Development-fitted from here on — label it. [VR] |
| Mar 2026 | **never built** | **VIRGIN — the only one** | TEST by design. Asterisk: CR self-disclosed a decode-level `json.load` traversal that decoded March outcome rows (no values extracted or used; `session_boundary_disclosure` in CR result). The March prereg must adjudicate this asterisk BEFORE any read. Read only on Borhen's explicit word (OD-FA2-1). [VR] |
| Apr 2026 | `packs/april_2026_runtime_v2` | **BURNED** (2026-08-01, CS fold) | 3,671 breaker rows decoded. [VR] |
| May 2026 (1–30) | `packs/may_2026` | **BURNED** (2026-08-01, CS fold) | May 31 excluded by `CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1.json`. [VR] |
| 2026-06-01..07-28 | none | was "refused" → **TRAIN by OD-FA2-3** | Consumed by full-history gate walks (`GateSpec.global_span` ends 2026-07-27) — never confirmation-grade. Packs must be materialized (CJ factory tooling). Overlaps the tick corpus 2026-06-18..07-24 → spread-truth validation synergy. [VR] |
| 2026-07-29+ | — | **NEVER** | Live-forward, both accounts armed. [VR] |

## §3 FA Phase-1 findings — all [VR] (streamed re-derivations in `priors/POOL_CROSSCHECK_V1.json`; every number reconciles to its committed receipt)

Pool ground truth: Jan 27,658 scoreable rows, net **−24,357.199 R** (−0.8807/row; gross
−0.2175, cost 0.6632); Feb 24,239 rows, net **−15,513.473 R** (−0.6400/row; gross −0.1506,
cost 0.4895). Executed: Jan 57 trades **−5.5062 R**, Feb 58 trades **−3.9614 R**.
Breakeven precision 0.6486 / 0.6064 vs positive-row share 0.2786 / 0.3093.

1. **Selection is NEUTRAL, proven.** S0R0 draws by sha256 hash among hard-eligible
   survivors; chosen-candidate hash percentile uniform (z −0.99 / −0.72). Picks landed at
   the **67th/68th outcome percentile** of their own choice sets (chosen −0.100/−0.068 vs
   set mean −0.722/−0.665). Rank↔outcome Spearman −0.076/−0.006. "Wrong selection" is
   refuted FOR THESE ARMS. Caveat D12: the hash neutralizes only the finalizer draw —
   upstream quality score shapes which options are preserved, and hard eligibility embeds
   the adaptive replay memory guard, which reads prior closed replay outcomes
   (`v4_timewarp:34895-34926`) → the executed book is path-dependent; per-repair deltas
   do NOT sum.
2. **Gates were economically correct on average — and that is not the same as harmless.**
   Every material gate refused negative-mean row sets (cost_authority Jan n=20,448 mean
   −1.121, sum −22,923.5 R = 94.1 % of pool loss; ev-after-cost mean −2.326). The only
   positive-mean refusals: `daily_lockout` +11.4 R and `same_symbol_daily_loss_lockout`
   +8.2 R (~+20 R forgone vs −24,357 R avoided). Cost>1R band: 54.2 % / 38.8 % of pool
   loss, **zero leakage** into ranked/executed either month. BUT: **61.4 % / 84.3 % of
   pool WINNERS die at the cost stage** (Jan top-decile winners: 75 % cost-blocked,
   +3,213.5 R worth). The gate obeyed its caps; whether the caps AND the geometry are
   RIGHT is the repair question (R-GEOMETRY + R-CAPS): `spread_r = spread / |entry −
   stop|`, so tight stops price 73.9 % / 82.2 % of candidates untradeable at their own
   stop geometry (SPX500 mean spread 2.353 R, NAS100 2.216 R at Jan geometry) — the
   winner-kill is attackable from both sides, geometry and cap, with the same receipts.
3. **The belief layer is structural fiction.** Brier skill −1.147 / −0.965 (worse than
   knowing the base rate); every decile over-predicts by +0.38..+0.54; mean EV bias
   +1.084 / +1.012 R/row; `corr(candidate_ev, realized gross)` 0.0737 → **0.0067**
   out-of-window; min p 0.584/0.580 and min EV **+0.398/+0.387** (the layer cannot express
   a loser); `candidate_confidence` ≡ 0.55 on all 51,897 rows
   (`ultimate_candidate_package.py:72`, returned `:2064`); 9 belief fields = 4 quantities
   (byte-equal duplicates); probability includes `0.04 × sha256(origin_family_name)`
   (`v4_timewarp:53682`); EV is priced at the generator's 1.5R reward then the contract is
   rewritten to a 2.0R-capped giveback AFTER EV attachment (`:67426-67450` vs
   `:67680-67712`); the engine cost hooks read `context["cost_r"]` that replay never sets
   → thesis EV is gross-of-cost. The cost belief is "calibrated" by tautology
   (`expected_cost_r == cost_r`, byte-exact, all rows).
4. **The cost model is part placeholder.** BTCUSD `spread_r` = 0.0001 on every row both
   windows (2,118 rows); UKOIL_cash constant 0.02580; USOIL_cash constant 0.02700; flat
   modeled slippage 0.02 R on every row and every trade. February-only `cost_missing`
   class: 5,876 physical rows on exactly UKOIL_cash/USOIL_cash/GER40 carrying a constant
   defaulted `cost_r = 0.12` while GER40's own spread field has 1,554 distinct real
   values. Schema drift: `pretrade_cost_packet_status` on every Jan row, on ZERO of
   129,165 Feb rows. Legacy-proxy under-charge vs broker-calibrated: +0.431 / +0.280
   R/row mean with max +18.60 / +11.65. NOTE BOTH DIRECTIONS: replay stamps
   `commission_r: 0.0` (`v4_timewarp:58965-58968`) — honest costs can be HIGHER too.
5. **Executed-book truth.** Feb book **gross-POSITIVE +0.204 R** — the entire −3.961 loss
   is the 4.165 R cost bill (~0.072 R/trade — the neutral slice lands on low-cost rows vs
   0.489 pool mean). Jan gross −1.221 vs cost 4.285 (78 % of loss; spread 2.111 + flat
   slippage 1.140 + commission 0.563 + swap 0.161 + fill-geometry rebase +0.425). No
   single trade sign-flipped by cost either month. **Exit geometry is the largest loss
   class both months**; stop-first-touch trades carry essentially all losses (Jan
   first-touch stop:target 26:8; Feb stop-first −17.85 R on 18, target-first 100 %
   positive both months: +12.79/+12.84). `stop_hit`/`horizon_marked` classes EMPTY both
   months — there is no "clean stop at bad luck" population. "21/21 negative days" is a
   POOL metric: the executed Jan book was positive on 8 of 19 trading days. The
   tick-truth (headline) subset is 4.0 R WORSE than the physical book (Jan −9.526 vs
   −5.506). 120-min truncation: 21/58 Feb trades end mark-to-market, netting only
   −1.28 R.
6. **Families.** Executed: `current_fvg_fill` negative both months (Jan −12.264 on 21
   trades — 2.2× the whole book's loss), `current_breaker_re_entry` + 
   `structural_distance_extreme` positive both months. Pool: **all 40/40
   family×direction cells realize negative net**; "fiction cells" (believed positive,
   realized negative) cover 67 % / 92.6 % of rows. NY-session-LONG-metals — CP's factory
   class — went **GROSS-negative in February inside FA's own funnel** (Jan +12.7/+22.0 R
   by variant → Feb −75.6/−80.8 R, 47.8 % positive, mean cost only 0.105): the signal
   failed out-of-window, not the cost. Corroborates the wave-18 REJECT independently.
7. **The oracle gap.** 92.5 % / 90.0 % of decision points contained an ex-post-positive
   candidate; oracle best +1.164 / +1.179 R/dp; EVERY rule computable from predecision
   fields is negative in both windows (argmax-EV −0.206/−0.215, argmax-p −0.321/−0.383,
   min-cost −0.229/−0.129). Zero-cost pool headroom is still **−0.079** (gross genuinely
   negative at pool level); zero-cost executed-58 is marginally positive (+0.0023
   headroom). ≈1.35 R/dp is invisible to every field in this ledger family.
8. **Join/handling hazards.** `candidate_id` alone is NOT unique (21,880 distinct over
   27,658 rows; unique key is `(candidate_id, decision_time_utc, symbol, side)`; a bare
   join mis-joins ~5,778 rows). Lane trade tables carry 1 meta line + N trades. Jan has
   2/57 trades with null `net_r` (per-trade means use n=55). Feb: 44 unique candidate_ids
   over 58 trades; ORACLE ledger 66 rows / 48 ids, 10 dup, 4 without trade rows; Jan
   ORACLE re-keys the guarded-fallback trade (+30 min asof). Scoreability: the whole
   153,425→27,658 / 129,165→24,239 reduction is `missed_opportunity_headline_execution_
   bound_eligible` hardcoded False (`v4_timewarp:27781`).
9. **What Phase 1 queued and nobody has run**: the instrumented short-window replay walk
   (the owner's literal ask); second/third neutral-seed arms (S0R1/S0R2 — decides whether
   the executed book's family mix and ~4.2 R/month cost bill are seed artifacts, and
   supplies the March MDE seed band); the adversarial verify pass; BELIEF-RECAL (does ANY
   subset survive base-rate-honest beliefs?); where `candidate_probability` is computed
   and whether [0.58, 0.97] is a clamp; the 0.92 fill-probability template origin; the
   `binary_population` (950/3,660) vs close-reason (2,811/11,499) definitional mismatch.

## §4 Contradiction register A–Q — [VR that they exist; A2 reconciles]

A. Two incompatible Jan loss-class tables (Jan rule: MFE≥+0.5R ⇒ exit_geometry → 17
   direction_wrong/−18.325, 11 exit_geometry/−9.941; Feb rule: mfe<0.25 ⇒ direction_wrong,
   mfe−cost>0 ⇒ exit_geometry → 11/−9.697, 21/−19.951). Both sum to −5.506. Never quote
   them side by side; pick ONE rule and restate both months.
B. Jan executed breaker count: n=9 (TRADES_JAN) vs n=8 (TRADES_FEB's reference), same
   +4.356 R.
C. NY-metals Jan economics quoted under two variants (`authority_session` n=411 +12.75 R
   vs `session_bucket` n=386 +21.99 R); the prose label in `funnel_jan/DECLINED_WINNERS
   .json` does not match the number it reports.
D. Three "January residual choice set" figures (Def A n=4,509 −0.199; Def B n=4,095
   −0.213; risk-bearing∧materialized 7,575/3,242 −0.205) — reconcilable, never reconciled.
E. Two "picked vs menu" baselines (−0.213 ranked-set vs −0.722 all-scoreable set) — both
   true, trivially misquotable as a 3× discrepancy.
F. Pool key counts 78 (Jan) / 101 (Feb) / "80 fields" (SCORECARD §7, unsupported) / 47
   (enum subset).
G. `POOL_CROSSCHECK_V1.json → cq_sidecar.total_observations = 0` vs 3,229,819 in prose —
   the streaming pass never summed the field.
H. Declined-winner partitions differ by basis (final-blocker vs first-refusal stage);
   totals agree exactly (7,706 / +6,447.2 R); no cross-walk exists.
I. Funnel non-monotonicity: 3,536 selector-reject rows re-enter softened
   (`open-reduced-risk`); blocker-class vs packet-status counts differ by 3,281
   non-scoreable rows (scoreable side matches exactly).
J. 61/66 selected probes vs 57/58 trades — 4/8 probes never became trades, "consistent
   with unfilled/expired", not verified row-level.
K. `final_selection_claim` False on ALL rows both windows — a provenance flag, not "no
   selection happened".
L. Feb `binary_population` (950/3,660) vs close-reason counts (2,811/11,499) — do not
   quote 0.206 next to 0.309 until pinned.
M. Endpoint tolerance: exact-1e−9 binary endpoints 678/3,270 vs 1e−6-near 3,072/15,057.
N. `policy_target_r` has 1,231 (Jan) / 988 (Feb) distinct values — never assume uniform
   2.0 (pool shows 2.0 on 26,427/27,658).
O. Original commission cites `CJ_RECLOCKED_ARM_S0R0_V7_ECONOMICS.json` which does not
   exist (real receipts: `CJ_RECLOCKED_ARM_S0R0_V7.json`, `CJ_CD_BASELINE_S0R0_
   ECONOMICS_V1.json`).
P. Join hazards (see §3.8).
Q. No Phase-1 output is internally truncated; the only degradation is Phase 2's absence.

## §5 Sol / wave-20 estate — structure [VR], contents [AP unless noted]

**Program graph** (all forked from main f8c05d0ac; 28 branches; ZERO merged; every branch
contains all of main — no rebase needed anywhere):

- Wave 19 "Sol": FB `phase19/sol-grid`, FC `sol-exit`, FD `sol-defects`, FE
  `sol-conditions`, FF `sol-composition` → FG `sol-integration` (ba3c18ddf) —
  **cherry-picked all 66 commits from CR/CS/FB–FF (rewritten SHAs; sources are NOT
  ancestors — merging FG plus any source double-applies)**. FG wrote
  `SESSION_FA_BROAD_FORENSIC_RESULT.md` in FA's first person — INPUT TO VERIFY.
- Wave 20 (stacked on sol-integration via `phase20/control`): HG science-preregistration;
  HA fidelity-authority → HDA falsifier; HB cost-completeness → HDB falsifier → HDE
  minimality; HC exit-capture-semantics → HDC falsifier → HDF falsifier2; HI
  repair-integration (4 real merges) → HIA falsifier; HK science-critical-path; HL
  p1-adapter-builder → HM p1-adapter-falsifier; p1-offline-result (NO docs, load-bearing
  +1,730 src lines); HN p1-upstream-reconstruction; p1-upstream-falsifier;
  p1-offline-complete-path → **HP p1-m1-verifier-repair 502d90616 = PROGRAM TIP**;
  p1-m1-sparse-repair (REPUDIATED by HP — discard). Sessions HO/HQ/HR/HS named in HP's
  incident ledger, no branches; HV uncommitted.
- **Landing recipe [VR]**: merge tip `502d90616`; cherry-pick doc-only leaves
  `11594419a` (HK close), `5c94d2caa` (HL close), `ec4555696` (HM close), `97d4c7da1`
  (HN docs); discard `phase20/p1-m1-sparse-repair`; never separately merge FG's seven
  cherry-pick sources. Tip-vs-main delta: 266 files, +572,576/−219 (src/ 20 files all
  under `src/research_infra/`; zero config/token/contract/component touches [VR]).

**Falsifier rhythm [AP with receipts]**: HA, HB, HC, HI, HL — every builder REFUTED by
its falsifier and re-repaired; HDF's three-way same-test A/B: HC 13 bad → HDC 7 bad →
HDF 0 bad. Suite at HIA head: 2 bad → 0 bad with all 12,974 control node IDs present.

**Sol findings to spot-recompute at A2 [AP]**:
- FB grid (10 families × 198 geometries, January): 2 survivors — inverted breaker
  5D/0.25D **+11.901 R** (4,263 rows), OB-retest 1.5D/0.25D **+1.647 R** (1,340 rows),
  max-T p=0.001; 7 further families gross-positive but cost-killed.
- FC: **0/40 exit overlays persist** (best +0.197 TRAIN → −1.920 HOLDOUT, −0.381 Feb,
  q=0.486). Those 40 cells are dead; the exit AXIS is not — exit_geometry remains the
  largest executed loss class in both months (stop-first 26:8, target-first 100 %
  positive). The repair search moves from overlay rules to geometry/contract terms
  (R-GEOMETRY), where FB's grid already found survivors.
- FD: 9 defect classes; the Feb 0.12R-fallback re-decode moved net **−178.589 R** with 67
  sign flips (i.e., honest costs made February WORSE).
- FE: 15-field condition scan — **0 TRAIN net-positive cells, 0 persistent, 0 strict
  survivors** (Feb: 9 gross-positive, 0 net).
- FF: executed FVG −12.264 R Jan (21) / −5.783 Feb (42); non-FVG +6.757 / +1.822; **no
  FVG veto licensed** (multiplicity).
- FG integration: 66/66 integrated; changed-test sweep 301/0; 42-file closure 736 passed
  / 1 skip / 0 fail; A/B 1 bad → 0 bad.

**[CT] THE CONTESTED VERDICT — the breaker flip.** CS at the ratified gate: raw
p=0.0025997, BH q=0.153385 @ family 59, **REJECT** (folds +11.252 / +7.454 / +3.852
R/trade on Jan/Apr/May — monotone decay, all positive; pooled OOS +7.519; only failing
predicate is significance; breadth multiple needed 0.21). HC re-derives p=0.00211588,
q=0.124837, still REJECT. HDC finds the common-circular-phase rule is not
rotation-invariant; corrected null gives **p=0.0009765625 (= exactly 1/1024 — the 1,024-
permutation resolution floor), q=0.0576 < α=0.10 ⇒ ADMIT**; HDF independently upholds.
Mitigation: HDC's plan was frozen 23 minutes before implementation and pre-registers the
exact test; HDF states the rule was derived without consulting CS's sign/q. Standing
problems: phase-19 docs on the SAME tip still print REJECT; NO iteration-ledger row and
NO family-version record for the method change; the ADMIT rests on the old test's
resolution floor. → Phase A1 adjudicates blind at ≥10,000 permutations and re-issues the
verdict table for every member through the affected code path.

**P1 state [AP]**: upstream packet 73,999/73,999 identity-complete (0 dup/unmatched/
out-of-window/postdecision; canonical refreeze by HP: verifier 73,999 + 52,803 states,
0 mismatches; M1 verifier 2,188,895 rows). Fill-authority split for the 11,305 breaker
rows: FULL_TICK 492 / M1_ONLY 10,810 / PATH_START_GAP 3
(`P1_FILL_AUTHORITY_PREREGISTRATION.json`, uncommitted). Execution SCHEDULED-ON-NEED:
the moment any breaker decision moves toward money, fill truth becomes REQUIRED and P1
runs — with HP's M1-acceptance rule landed, the split is a measurement to make, not a
reason not to look.

**Structural debt [VR]**: production-consequential code under `docs/` — `phase20/
receipts/wave20_complete_path_shadow.py` (47 KB, the P1 adapter), `wave20_source_
inventory.py` (21 KB), `verify_wave20_breaker_branch.py` (12 KB), plus phase-19
`cs_breaker_folds.py` / `session_fc_exit_overlay.py` which HC/HDC/HDF edit as production
logic → relocate to `src/research_infra/` with tests at A0 (HV already chose that layout);
re-resolve any forward references to the old paths (history stays valid — landing is
merge, not rebase).

**Boundary conduct [AP, receipts sampled]**: no February fitting found (Feb used only as
a third FAILING window); every phase-19 lane froze Jan identities before opening Feb,
stamped `owner_mandate_20260801`; phase-20 excludes February from selection
(`WAVE20_SCIENCE_PREREGISTRATION.md:65-66`, `:337`); `execution_authority: false` and
`activation_authority: false` on every closing receipt; zero broker orders; the only
ledger appends are CS's 6 rows, all `billed:false`.

## §6 FG repair register (`FG_REPAIR_REGISTER.json`) — dispositions going in

| # | repair | Sol state | continuation disposition |
|---|---|---|---|
| 1 | FD semantic/authority repairs + deterministic memo key | implemented, evidence-only | adopt at A0; verify at A2 |
| 2 | CR executable capture v3 + fidelity split | implemented, training-only | adopt as INFRASTRUCTURE (stays live regardless); CR-CAPTURE-1..4 repriced on the Feb evidence — re-enter if the flow walk or cost-repaired reruns revive the class (see §7 N1) |
| 3 | FF exact hard-eligibility/rank observability | implemented, default-off | adopt; verify |
| 4 | FE 15-field condition telemetry | implemented, default-off | adopt; verify |
| 5 | OB-retest 1.5D/0.25D | research-only; needs independent RECORDED folds | = O1, adopt AS-WRITTEN (V28 single-append, 59 pads at 1.0) |
| 6 | inverted breaker 5D/0.25D | verdict CONTESTED | A1 adjudicates |
| 7 | generic exit evaluator + bounded FC2 24-cell family | evaluator default-off; FC2 unrun | FC2 is **BLOCKED** (needs C0's authenticated 2025-06-02..07-11 lane registry, ABSENT) — record BLOCKED, do not improvise inputs |
| 8 | probability/EV calibration repair | not run | rename **BELIEF-RECAL** (pool re-scoring screen on Jan/Feb; distinct from prereg-K1) — Phase B |

Sol tested and rejected (re-opening any of these takes new evidence + its own declared
step, not a preference): FVG veto, breaker preference, structural preference,
late-market conversion, authority relaxation, condition gate, the 40 tested exit
overlays, multiplicity relaxation, family kill, promotion, arming.

## §7 WAVE20 preregistered DAG — supersession draft (A4 finalizes)

| node | disposition |
|---|---|
| G0 (integration at exact commit hashes) | SUPERSEDED-WITH-REASON: its exact-hash precondition (HDA 4f5c5d42 / HDE cf70fd7e / HDF 14c0e2ad) is unsatisfiable once A0 adds relocation commits; the A0 fence + LAND gate replace it |
| S0 (metadata-only pack inventory) | ABSORBED: becomes the March-pack metadata preflight in the prereg |
| WAVE20_B0 (router on breaker verdict) | CONSUMED-CONDITIONAL-ON-A1 |
| WAVE20_B1 (frozen counterfactual) | stays SKIPPED_BY_PREREGISTERED_BRANCH; **no auto-authorization** regardless of A1 outcome — new declaration required |
| O1 (OB-retest independent RECORDED folds; identity SHA 3e8e9508…; V28 single-append, 59 pads at 1.0) | **ADOPTED AS-WRITTEN** — a sunk declared bill; only its schedule position is superseded; do NOT redesign (that would be a second look) |
| C0 (2025-06-02..07-11 observability capture) | REPRICED: its authenticated lane registry is ABSENT (prereg authority map) and its main consumer was N1 — build the registry the moment a live consumer needs it (F1/FC2 or a revived N1), never improvise inputs |
| N1 (NY-metals) | REPRICED on §3.6: the class went gross-negative in February's own funnel; its follow-ups (CR-CAPTURE-1..4) re-enter the queue the moment the full-flow walk or the cost-repaired reruns revive the class; capture infrastructure stays live |
| F1/FC2 (bounded exit family) | **BLOCKED** via C0 — record as blocked, not "unrun" |
| K1 (prereg calibration node) | PARKED; the Phase-B pool screen is renamed BELIEF-RECAL to avoid the name collision |
| P1 (breaker complete-path fill authority) | RUNNER ADOPTED at A0 (HV adopt-or-kill); EXECUTION SCHEDULED-ON-NEED — required before any breaker money decision; HP's M1-acceptance rule makes the 492/10,810 split a measurement, not an assumption |

Record: this table (finalized) + one iteration-ledger row citing the prereg doc/JSON SHAs
+ the WA §4 wave-19/20 record. The prereg doc itself is superseded by a commission of
equal formality (this one), never edited in place.

Node-id note: the two B-named nodes are written `WAVE20_`-prefixed in these two docs
because the bare zero/one node ids collide with the evidence-block citation scanner
(`tests/test_implementation_state_block_citations.py` — underscore-joined tokens are
deliberately not matched). The prereg document spells them bare; when A0's landing brings
it into the scanned tree, the same collision surfaces in the suite fence — adjudicate
THERE (a path exemption with a stated reason, the same class as the archived pre-replay
briefs), never by hand-editing the prereg.

## §8 Compute shape and operating rules — [VR]

- Lane arm: ~4.2 min/trading-day, **~1.5 h per full month**, ~4 GB, `engineering_stop_
  after_day` honored on the lane path (2 days ≈ 8 min). Sealed-path replay (16.5 h arms)
  remains FORBIDDEN — lane only.
- **Strictly serial**: one lane arm / replay walk / full-suite run at a time, machine-wide
  (H3; 8 GiB floor). 2-day smoke before every new arm config.
- Baselines are NEVER re-run: the sealed 57/58-trade receipts (CJ/CP) ARE the baselines.
- Suite A/B: `scripts/pytest_failset.py` diff vs the sealed wave-20 baseline
  (12,809/2/0); the older committed ZERO baseline is 12,705 passed / 1 failed at
  bca8c4466 (CS's correction) — cite whichever tree matches, never re-capture a before.
- Jan pool screens are free: the CQ sidecar (3.23 M ordered observations) prices any
  exit/geometry counterfactual without a lane arm — but it is 120-min-bounded and blind
  to admission changes (spread_r feeds the 0.10 hard cap → cost/belief repairs change the
  executed set; only a lane arm sees that).
- **No February ordered sidecar exists** — building one is a heavy CP decode; explicit
  BUILD-vs-SKIP decision in Phase D (build only if exit/geometry repairs survive Jan T1).
- MFE oracle bounds (+48.1/+48.6 R) are upward-biased even on random walks — never usable
  as-is (FA Phase-2 prompt note; still true).

## §9 FA workflow artifacts of record

- `fa-foundations` (wf_e24aa067-5c3): 8 agents done, 1,439,199 tokens, 383 tool calls,
  ~33 min. Result JSON carries per-agent summaries/key_numbers/open_questions.
- `fa-attribution` (wf_28ee496d-b11): 5 agents ALL `state: error` — "You've hit your
  weekly limit · resets Aug 3 at 7pm (Asia/Bangkok)"; result = all five deliverables
  `missing`. The five lanes were EXECUTED INSTEAD by Codex as FB–FF (grid-full→FB,
  exit-overlay→FC, defect-rootcause→FD, conditions-separability→FE,
  eligibility-composition→FF) — verify, don't re-run, except where §3.9 lists work nobody
  has done.
- Scripts persisted under the session `workflows/scripts/` dir; re-runnable cross-session
  via `scriptPath` (runId resume cache is same-session only; the disk outputs above are
  the real resume state).
