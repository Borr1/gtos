# Session FA — broad-V4 forensic RESULT (re-authored at A2 close; extended through Phases B–E)

**Session FA continuation (OD-BROAD-FORENSIC-2), 2026-08-03. This document supersedes the
first-person result FG ghost-wrote on `phase19/sol-integration` — that file was INPUT TO
VERIFY, and its verification is now done (A2 lane FG: content fidelity verified; 10/10 sampled
quantitative statements match their receipts). Everything below is re-stated from receipts I
commissioned and verified, with a tag per finding:**

- **[FA-P1]** — FA Phase-1 measurement, cross-checked digit-for-digit at commissioning
  (`FA_CONTINUATION_VERIFIED_STATE.md` §3, all [VR]).
- **[A2-verified]** — Sol/Codex claim spot-recomputed FROM RAW POOLS by this session's
  verification lanes (`phase19/receipts/forensic/a2_verify/`).
- **[A1]** — this session's blind clean-room statistical re-derivation
  (`phase19/receipts/forensic/a1_cleanroom/`).
- **[REFUTED]** — a circulating claim my measurement contradicts, corrected here.

Evidence classes: DIAGNOSTIC (attribution, billed:false) / DEVELOPMENT-FITTED (anything shaped
on Jan/Feb/Apr/May or the June gap) / PREREGISTERED-CONFIRM (March one-shot only — none exists
yet). **Nothing below is confirmatory.** February numbers are attribution-only under
`owner_mandate_20260801`.

---

## 0. The two-sentence answer to the owner's mandate

The system loses for identified, repairable reasons, not for a mystery: candidates are born
with structural stops so tight that the honest spread prices 74–82 % of them untradeable
(and kills 61–84 % of the pool's WINNERS at the cost gate), the belief layer that ranks the
remainder is structural fiction (probability hash-noise, a constant confidence, EV priced on a
contract that is never walked, gross-of-cost), the exit contract donates the largest loss
class in both months (canonical partition: −19.95 R of 55-trade January and −13.97 R of
58-trade February sat on trades whose own path offered a net-profitable exit), and the
executed February book was already GROSS-POSITIVE (+0.204 R) before a 4.165 R cost bill.
Meanwhile the same surface measurably contains edge — 92.5 %/90.0 % of decision points carried
an ex-post-positive candidate; the inverted breaker measures +11.90 R/trade over 4,263 January
rows [A2-verified, bit-identical] and ADMITS at the ratified rule under the corrected null
[A1] — so the program is repair-and-capture, executed in Phases C–E of this session, not a
tidier explanation of losing.

## 1. The six axes, closed

**Axis 1 — Wrong selection? NO, proven.** [FA-P1] S0R0's neutral finalizer draw is hash-order
among hard-eligible survivors; chosen-candidate hash percentile uniform (z −0.99/−0.72); the
picks landed at the 67th/68th outcome percentile of their own choice sets; rank↔outcome
Spearman −0.076/−0.006. The selector stands in front of a pool whose scoreable mean is
−0.88 R/row (Jan); no picker fixes that pool. Caveat D12 stands: the hash neutralizes only the
finalizer draw; hard eligibility embeds the adaptive replay memory guard (prior-outcome-coupled,
`v4_timewarp:34895-34926`) — the executed book is path-dependent and per-repair deltas do not sum.

**Axis 2 — Wrong sleeve/mechanism? PARTLY — one mechanism is anti-predictive and inverts to
the estate's best candidate.** `current_breaker_re_entry` as shipped is wrong-way: inverting
it (entry fixed, target 5D, stop 0.25D) yields +11.901 R/trade over 4,263 rows
[A2-verified: recomputed bit-identically from the ordered sidecar + raw ticks; zero ambiguous
same-bar rows in the cell]. Fold evidence: +11.252/+7.454/+3.852 R/trade on Jan/Apr/May
(monotone decay, all positive; pooled OOS +7.519) [CS, reproduced byte-exact at A1].
Executed FVG is the worst family both months (−12.264 R over the 20 scoreable of 21 Jan
trades) but no veto is licensed at the declared multiplicity [A2-verified]. NY-metals-LONG
failed out-of-window in February's own funnel (its cost was NOT the problem — mean 0.105)
[FA-P1]; the wave-18 REJECT stands independently corroborated.

**Axis 3 — Inaccurate sleeve (right idea, wrong geometry)? YES — the single largest lever.**
[FA-P1] `spread_r = spread/|entry−stop|`: tight structural stops inflate spread to a 0.564
pool mean (SPX500 2.353 R, NAS100 2.216 R at January geometry), so 73.9 %/82.2 % of candidates
are priced untradeable at their own stop geometry before any belief or ranking. FB's grid
answers the counterfactual: at family-fit geometry (e.g. 0.25D stops with 5D/1.5D targets),
two cells go persistent-net-positive and seven more families are gross-positive-but-cost-killed
[A2-verified]. Exit side: under the canonical loss partition (ratified this session,
`LOSS_CLASS_RULE_RATIFICATION.md`), exit_geometry is the dominant executed loss class BOTH
months — Jan 21 trades/−19.95 R vs direction's 11/−9.70; Feb 23/−13.97 vs 10/−9.59. The 40
overlay RULES all died out-of-sample (0/40, best cell +0.197 TRAIN total → −1.920 HOLDOUT
[A2-verified]) — the repair is contract GEOMETRY (R-GEOMETRY), not overlay rules.

**Axis 4 — Inaccurate conditions? NO usable condition cell exists at current costs.**
FE's 15-field scan: zero TRAIN net-positive cells, zero persistent, zero strict survivors;
February transfer 9 gross-positive/0 net [A2-verified, with one definitional correction: the
"persistent gross-positive = 4" count is 5 under the protocol's own no-floor definition —
the implementation folded an undeclared HOLDOUT n≥100 floor into the flag; low materiality].
Conditions are not the broken link; costs and geometry are upstream of every cell.

**Axis 5 — Why were the positive options declined?** [FA-P1] Named, per class: the broker
pretrade cost authority is the refusing stage for the majority (Jan: 20,448 refusals summing
−22,923 R avoided = 94.1 % of pool loss — AND 61.4 %/84.3 % of pool winners die there;
top-decile January winners: 75 % cost-blocked, +3,213.5 R worth). The only positive-mean
refusal classes are the two daily lockouts (~+20 R forgone against −24,357 R avoided). The
gate obeyed its caps; the caps (0.10/0.15) against generator geometry are the joint question —
R-GEOMETRY attacks the denominator, R-CAPS re-derives the caps at honest spreads.

**Axis 6 — Is there an ex-ante rule that separates good from bad? Not from the belief fields;
yes from mechanism+geometry.** [FA-P1] Every rule computable from predecision fields is
negative in both windows (argmax-EV −0.206/−0.215; argmax-p −0.321/−0.383; min-cost
−0.229/−0.129); corr(candidate_ev, realized) 0.0737 → 0.0067 OOS. The belief layer cannot
carry the separation: Brier skill −1.147/−0.965, p̄ 0.766 vs realized 0.172, min EV +0.398
(the layer cannot express a loser), confidence ≡ 0.55 on 100 % of rows, probability includes
0.04×sha256(family). What DOES separate ex ante is mechanism identity × geometry (the inverted
breaker cell, the OB-retest cell) — which is why the repair program routes edge through
declared candidates at the sealed gate rather than through belief-score repairs alone.

## 2. The statistical adjudication of the one standing candidate [A1]

The ratified gate's REJECT (raw p 0.0026, q 0.1534) and HDC/HDF's contested ADMIT
(p 0.0009765625 = exactly 1/1024) were BOTH artifacts of the same defective machinery, in
opposite directions. The blind clean-room (inputs: CS's fold data + the ratified gate spec +
the null question; ≥10,000 permutations required) found:

- The common-circular-phase block permutation rule is **not rotation-invariant**: one arbitrary
  block-grid anchor is shared by every permutation; across the 31 circular anchorings p spans
  10× and the verdict flips at 14 of 31 rotations. The published REJECT depended on a block sum
  of −0.069 (1 % of the day sd) that the arbitrary grid happened to create.
- The rule's null support is intrinsically capped at 2¹¹ = 2048 assignments; near the α bar,
  q moves in 0.0288 quanta — no q near 0.10 is even expressible. Seeds alone swing the
  published p across the ADMIT bar ({0.0026, 0.0023, 0.0018, 0.0016}).
- The corrected null (independent fold segments 11/11/9; within-fold AR(1) ρ = 0.372 ± 0.175;
  per-fold scale; studentised mean; H0 mean=0 imposed exactly; primary p = max over the fitted
  model span): **p = 0.00130 (spread 1.27–1.34e-3 over 3 seeds × 700k sims), BH q at the
  declared 59-family = 0.0769 ⇒ ADMIT at α = 0.10** — series reconstruction validated
  byte-exact against the gate receipt on all 12 checks.
- Fragility, disclosed: the ADMIT flips if within-fold persistence ρ ≥ ~0.6 (1.2 SE above
  measurement); size conservatively and re-read on the next unread window. Any future gate p
  ≲ 1e-4 from a 31-point series is a floor artifact.

Consequence tree (fixed ex ante): the ADMIT stands at the corrected null; the method-defect
ledger row and the re-issued family verdict table are filed at A4 (A1b); the challenge-dossier
option goes on the owner sheet. WAVE20_B1 stays skipped. **"Admits at the corrected null under
the ratified family" is the exact sentence — DEVELOPMENT-FITTED windows; the March one-shot
remains the only confirmatory read and fires only on Borhen's word.**

## 3. What the cost bill actually is [FA-P1 + A2-verified]

January executed: gross −1.221, cost 4.285 (spread 2.111 + flat slippage 1.140 + commission
0.563 + swap 0.161 + fill-geometry rebase +0.425) → net −5.506. February executed: **gross
+0.204**, cost 4.165 → net −3.961. No single trade sign-flipped by cost in either month; the
bill is a broad tax, not a few disasters. Parts of the model are placeholders: BTCUSD spread_r
0.0001 on all 2,118 rows both windows; UKOIL 0.02580/USOIL 0.02700 constants; slippage a flat
0.02 config constant on every row; February's `cost_missing` class defaulted 0.12 on 5,876
physical rows. FD's honest re-decode of that class moved February −178.589 R with 67 sign
flips at pool level [A2-verified] — honest costs made February WORSE at pool level while the
executed book's bill is what stands between +0.204 gross and −3.961 net. R-COST-TRUTH replaces
the placeholders with tick-corpus session-conditional models, both directions disclosed.

## 4. The flow verdict

`FULL_FLOW_SPEC.md` is the link-by-link companion (intent / measured / verdict / edge per
link); its completion criterion is the repair program's. As of A2 close: L2 (generation
geometry) DEFECTIVE→R-GEOMETRY; L3a (cost inputs) DEFECTIVE→R-COST-TRUTH; L3b (beliefs)
DEFECTIVE→R-BELIEF + BELIEF-RECAL; L3d (EV-before-contract ordering) folded into R-BELIEF;
L8 (exit contract) DEFECTIVE→R-GEOMETRY; L9/L10 observability defects→R-SCHEMA; L5 (ranking)
measured neutral; L6 arm factors PENDING the seed arms; the walk annex lands in Phase B.

## 5. Corrections this continuation made to circulating claims

1. [REFUTED] "FC registered a sign-convention defect against family artifact V17" — no such
   registration exists; V17 is the best TRAIN overlay CELL id, whose book sign-flips OOS
   (+0.197 TRAIN total → −1.920 HOLDOUT). The commission text itself carried the garble and I
   propagated it into a lane brief before the lane caught it.
2. [REFUTED] FE "persistent gross-positive = 4" — 5 under the protocol's own definition; the
   4 required an undeclared HOLDOUT n≥100 floor.
3. [CORRECTED] "+0.197 R/trade" — the number is the 30-trade TRAIN book TOTAL (+0.00657/trade).
4. [CORRECTED] FF's "Feb −5.783 on 42" — 42 is the FVG subset of the 58 executed; Jan's
   "−12.264 on 21" sums the 20 scoreable of 21 physical FVG trades.
5. [CORRECTED] The register's row-A tables: superseded by the canonical counterfactual-exit
   partition (`LOSS_CLASS_RULE_RATIFICATION.md`); never quote the two old rules side by side.
6. Register rows B–P: RESOLVED from raw data (15 of 16; Q is meta) — see
   `a2_verify/RECONCILE_A_Q.md`, including: the sidecar-crosscheck total_observations=0 was a
   crosscheck bug (recount 3,229,819); the bare candidate_id join mis-joins 5,778 Jan rows
   (unique key is the 4-tuple, reconfirmed independently by the FB walker).

## 6. New defects found while verifying (queued into Phase C)

- FD's deterministic-memo-key instability class SURVIVES at HEAD in the `cuts.py`
  set/frozenset branch [A2 lane FD] — repair queued.
- The compact pools carry null repair-status columns while the repairs demonstrably ran
  (projection reads the row; stamps live on the packet) [FA-P1] — R-SCHEMA.
- The February emitter drift (`pretrade_cost_packet_status` on zero Feb physical rows) and the
  3,536 softened-reject non-monotonicity — R-SCHEMA, fix or document as intended semantics.

## 7. What I got wrong (running; finalized at Phase E)

- I propagated the "V17 sign flip" garble from the commission into a lane brief before the
  lane refuted it (§5.1).
- My first environment-parity pass for the A0 suite fence assumed the sealed baseline's
  worktree state was reproducible from its sparse-rules file; it is not (incremental
  application drift), and my index-level sync then assumed skip-worktree ⇒ absent-from-disk,
  which is also false there. Both assumptions cost one wasted 45-minute suite run under memory
  pressure (88 spurious bad IDs) before the disk-level mirror fixed parity. The lesson is the
  H1 lesson generalized: an environment is a property of the working TREE, not of any
  configuration that claims to generate it.
- A `git checkout` on LFS paths in a `filter-process --skip` repo silently de-hydrates them —
  I re-learned B185's lesson the measured way before using `git lfs checkout` as prescribed.

## 8. What extends this document

Phase B: the instrumented 2-day walk annex + S0R1/S0R2 seed band + BELIEF-RECAL + the
adversarial pass over the combined causal claims. Phase C: the repair registry with ex-ante
specs. Phase D: T1/T2/T3 tables (cost-truth-only headline; arm (v) with the edge in). Phase E:
the March preregistration (frozen, Borhen-triggered), the owner decision sheet, and the final
"What I got wrong".
