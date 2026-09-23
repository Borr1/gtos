# Third Review — the unconstrained answer

**Fable 5, 2026-07-27.** A review of my own `SECOND_AUDIT.md` and `FULL_VISION_PLAN.md` against the
evidence eight implementation sessions produced, answering Borhen's question: *"if there were no
constraints to the implementation sessions, what would Fable suggest we do exactly."*

Branch `review/fable-third-review`; all eight sessions' work merged in. Method: firsthand reading of
the wave-2 evidence blocks (B60–B99e) and the governing documents; **twelve parallel reader agents**
over the rest of the corpus (~1.8 M tokens of reading, full reports vendored under
`third_review_receipts/`); a **four-way judge panel** — four rival unconstrained architectures
generated independently, scored by three judges with different lenses (also vendored); **one new
measurement this review ran itself** — the memory-attribution run Session G scoped and nobody had
run, reported in §A1; and an adversarial pass — three refuters attacking the review's own pillars
plus a completeness critic — whose verdicts are §A2. Claims are tagged; `file:line` cited for
production-state claims; where a reader agent's number is relayed rather than re-derived, it is
attributed and its full report is in the receipts directory.

---

## 0. The verdict in one page

**The eight sessions were the right work.** Every one was measurement or infrastructure, and by the
charter's own test that is exactly what proof work must do to earn priority: it changed decisions.
Session E + H dissolved the premise OD-1 was decided on. Session E found the largest economic defect
in the programme's history (the zero-commission validation, F38). Session G refuted my plan's
Phase-2 memory premise by building the fix and measuring nothing move. Session D's harness became
the correctness instrument two other sessions ran on. That is not scaffolding; that is the
measurement substrate doing its one job. This review closed the question G opened by running the
attribution nobody had: **the arm's memory is the evidence machinery's own per-day accumulation —
60.6 % of the Python heap at high-water, the same share it owns of CPU — and the source layer is
1.6 %** (§A1). One redesign owns all three resource problems.

**The plan — my plan — is where the charter got inverted.** Phases 2–3 as written schedule a
monolith-scale engine rebuild before any activation-bearing decision, for a policy family (the broad
V4 stack) whose measured economics are **negative in every campaign-grade window ever measured** —
four negative January arms, sizing `material_negative` by the sealed analyzer, −0.25 R/fill native
live, 1W/20L holdout, −1,683.5 R net admitted by the production floors on the June validation frame;
the only positives on record are 1–2-day bounded probes their own source disqualifies. Meanwhile the
only *positive* validation in the tree — the W7 book's **2015–2026** locked evidence (trade rows
from 2015-03-19; per-sleeve depth ranges 11 years down to 12 months) — is **invalid rather than
negative**: contaminated by a missing commission term (F38) and a wrong-sign erosion credit (F39),
and 88.5 % of its confidence weight is unmeasured by its own live window (B63/B99b; the measured
11.5 % split JPY-negative, `idxrev`-positive). Negative evidence cannot be repaired. Invalid
evidence can, cheaply: the validation's exact input rows survive in-tree, and re-costing is
arithmetic over them (§1.2).

**So the unconstrained answer is: decide the activation candidate with two cheap measurements before
building anything large.** (1) Re-cost the W7 validation at broker-true costs → a cost-surviving
sleeve subset, `SURVIVOR_BOOK_V1`, or an honest kill. (2) Port the book's candidate *generation*
behind Session H's policy protocol and answer G4 — were the five silent high-confidence sleeves
silent from natural frequency or a generation defect — then replay the survivor book out-of-window
at true costs. Those two results, in front of Borhen as **OD-3**, decide what GTOS activates. The
engine/evidence rebuild proceeds after that, sized to the surviving lane — and the evidence
architecture is rebuilt around the measured fact that **≈0.2 % of a sealed arm's bytes are ever
value-read by any decision consumer** (the rest is hashed for custody and never read as values —
§3).

**Before any of that: port the activation token to the VPS.** The entire brake on a running,
funded, connected host is one config layer (three booleans, no second mechanism, no monitoring —
§1.4), and the fix is ~half a day.

The judge panel scored four rival architectures against the charter; the payout-first "Settled-Book
Line" won 2-of-3 judges and the aggregate (104 vs 92/90/80), with the truth-first spine's best
elements grafted in rather than lost (§2). The B7.5 campaign is **parked, banked, and priced as an
expiring option** — not deleted (§6.2). First payout runs through the survivor book or it runs
through honesty about not having an edge yet (§8).

---

## 1. The four tensions, answered

### 1.1 Did the plan invert the charter's activation-first rule?

**The sessions didn't; the plan did, in its middle; and the deeper error was mine in sequencing.**

The eight sessions pass the charter's test for proof work ("earns priority when it unlocks a
decision, exposes an economic defect, or moves the system toward operation"):

- Sessions E + H **re-opened the activation-candidate decision** with measurement: 11.5 % of
  core-8's confidence weight traded (B63); **zero of 145 placements from any train-validated sleeve
  in 38 days** (B99b); 43.4 % of placements from sleeves the registry itself marks
  `breadth_falsified`; 76.4 % of net loss from the candidate book switched on same-day with no cited
  validation (B64). "W7 underperformed live" — the premise behind OD-1 — is not supported by the
  window, in either direction.
- Session E exposed the programme's largest economic defect: **the validation and the live pre-trade
  engine charge zero commission at five independent sites** (F38; `broker_net_cost_engine.py:577-583`
  computes `spread + slippage + swap`, no commission term), while realized commission+swap was
  31.6 % of the W7 loss (−12.69 R of −25.32 R), and the authorizing MC applied tick-erosion
  **credits with the wrong sign** (F39: USDJPY +0.0179 R credited where reality charges ~−0.195 R).
  The comment above the constant even said so: `KB7_tick_truth.py:62-63` — *"If a venue charges
  commission, this is optimistic by that amount"* — self-declared and never propagated.
- Session G refuted the plan's own memory premise by construction: killed every source-layer copy,
  proved output identity over 1.78 M rows, and the arm did not shrink (B84). A negative result that
  saved every future session from aiming at the wrong layer.
- Sessions A/B/C/D built the truth instruments (shadow reducer → F31; clock truth → the US-DST
  correction both audits missed; the red-suite closure; the differential harness) that E, G, H then
  stood on. The harness alone was used as the correctness instrument by two sessions within days of
  its revival.

Where the plan inverts the charter is **Phase 2–3 as written**: a sequence of monolith-scale builds
(policy-plural core at full size, evidence-as-projection, columnar layer, ≤3 GB/arm, 10–16×
throughput) all scheduled *before* the plan reaches any activation rung — while the family those
phases serve has no positive evidence anywhere. And the root error is sequencing that I own: the
plan accepted OD-1's consequences structurally (BroadV4Policy as the primary policy module) without
demanding the two measurements that would have tested OD-1's premise first. The corrective is §2/§4:
the next unit of work is the activation-candidate decision itself, which is cheap, and the rebuild
is sized to whatever survives it.

### 1.2 OD-1's premise does not survive its own evidence — reopen it (owner's call)

Jointly established by E and H:

1. The fortnight measured **a different portfolio** than the validated book — the candidate book
   plus falsified-sleeve residue at 47 % of core-8's weighted confidence; `metals_core` (conf 1.00,
   the registry's "deepest anchor") placed nothing and ran a **2-of-6 symbol universe** because four
   of its declared symbols are absent from both live profiles (B99b).
2. The 2.0 % dial was structurally unreachable (highest confidence that traded: 0.40 → 0.80 % unit
   cap); the dial choice explains 37.5 % of the loss's magnitude and none of its sign (B65).
3. About a third of the loss was cost the model priced at zero (F38), and the JPY cluster — 37.4 %
   of net loss — was negative gross as well: a genuine kill of two sleeves, not of the book. (One
   correction this review's reader found: the receipt's "survives Bonferroni" claim double-counts
   cross-account duplicates — at the honest signal-level denominator p = 0.00588, Bonferroni ×12 =
   0.0706. Direction and magnitude stand; "decisive" does not. §5, Session E.)
4. The broad stack's own record, assembled in one place for the first time [reader-verified against
   the route artifacts; paths per claim in
   `third_review_receipts/read_research-state.md`]: January S0R0 −0.0224, S1R0 −0.0715,
   S0R1 −0.1329, S1R1 −0.1746 on the contract's primary metric
   (`B7_5_…JANUARY…MATRIX_AUDIT.json`, hash-verified by the reader) — **the dumb neutral/fixed
   reference was the least bad cell**; sealed classifications selection = inconclusive,
   **sizing = material_negative** (−0.1105), incumbent total material_negative; dynamic sizing
   multiplied accepted risk ~4.2–4.5× and maxDD ~8.8× while making cash strictly worse; KIAP
   holdout 21 fills, 1W/20L, −17.96 R net proxy (`research_current_state.md:980-982`); broker-real
   Wave1A −$859.69; native live −0.25 R/fill over 454 fills (`ULTIMATE_GO_LIVE_DOSSIER.md:276-280`);
   the only positive full-window numbers carry `validation_claim_allowed = false` (post-tuning,
   `research_current_state.md:988,1009`); and the June learned-edge gate run recorded the
   production floors admitting **−1,683.5 R net** on its validation frame
   (`ULTIMATE_LEARNED_EDGE_WALKFORWARD_GATE_V1.json`).

Neither family holds a valid activation claim today — but they fail differently. **The broad stack's
evidence is negative. The W7 core book's evidence is invalid** — a positive validation contaminated
by a mis-costed model and largely unmeasured by its live window. Invalid is repairable, and this
review's adversarial pass pinned the exact substrate [verifier-measured, §A2]: **the validation's
exact input rows survive in-tree** — `INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl`
reproduce CYCLE62's 1,679-day series **to the day**, all 8 sleeves, with per-trade sym/date/R —
so re-costing is arithmetic over the caches, not a re-backtest. (`D4_COMBINED_TRADE_LEDGER.jsonl`,
which this review's first draft named as the substrate, supplies per-trade state for only 7 of 8
sleeves — no `fx_jpy_ny` — with re-simulated metals rows diverging from the consumed series by a
mean |Δ| of 0.60 R; it serves as the re-sim coordinate source, not the restatement base.) The
recommendation to Borhen — argued hard, his to make — is to **reopen OD-1 as OD-3** once the two
Stage-1 measurements exist (§4), rather than letting either the fortnight or my audit's default
stand.

The commission structure is what makes this genuinely decisive rather than hopeful — stated at the
precision the adversarial pass forced: per-instrument commission is **zero on the six measured
index CFDs and near-zero on XAU/XAG** (0.0054/0.0013 R), and **0.09–0.20 R on the measured FX/JPY
legs and BTC** (`GATE_G1B_RECEIPT.md` §5.2a). Commission alone **kills USDJPY on the validation's
own rows** (fx_jpy +0.116 gross − 0.195 = negative), **dents but does not kill GBPJPY** (+0.219
gross − 0.093 survives — its live death is gross-edge, which is precisely why the cost model never
saw it coming), haircuts BTC ~13 %, and is **unmeasured** for energy/agri, DASHUSD, the four metal
crosses, and ~24 % of `idxrev`'s index universe — the re-cost carries those as [TRANSFERRED] bands
per §2.1-A's coverage-class rule. The surviving high-weight complex is metals+energy (conf
1.00/0.80/0.50/0.30); the one fully commission-free sleeve, `idxrev`, is the registry's
lowest-weight, train-falsified sleeve that happens to be the only live-profitable one — a tension
only Stage 1's re-cost and G4 can resolve. Whether what survives is a *tradeable* book is exactly
what Stage 1 measures — see the anti-correlation risk in §2.6.

### 1.3 The evidence architecture is the real Phase 2 — but smaller and later than my plan thought

Session G plus this review's evidence-cost reader settle it:

- A sealed 2-day arm writes **932.1 MB** (859.6 MB across the eleven required roles + 23.2 MB
  compact shards + 49.2 MB semantic diagnostics) for 10 orders — and **only ~1.3–1.6 MB (≈0.16–
  0.18 %) of the eleven-role bytes are ever value-read by any decision consumer** (acceptance
  verdict + economic read-out + the currently input-less learning lane; the adversarial pass added
  Session A's reducer at ~30 KB/2-day arm and the analyzer's per-row timestamp scan at ~0.2 MB to
  the reader's 1.33 MB census). Acceptance is content-blind by design (hashes, counts, 8 summary
  scalars). [MEASURED by reader against the surviving SESSG arm outputs; census corrected in §A2]
- The redundancy is real but my briefing overstated one number: `calendar_no_session_breadth_guard`
  is **77.5 MB (one constant subtree × 2,304 rows of the no-session day, 1 distinct value)** — not
  154 MB/2 values. Corrections of the same class: the 867/802 figures are MiB; scorecard fields
  average 1,248.7 (min 888, max 1,827), not a flat 1,211. The larger truths hold: 41.3 % of
  decision-role value bytes sit in fields with ≤10 distinct values; key names alone are 178 MB
  (41.6 %) of the missed role; two scorecard trace fields are 79.7 % of the scorecard role.
- **The compact typed event sink already exists in-tree and already emits decision+missed at 28.7×
  compression**; the 69 GB cold demotion (B53) already proved expand-on-demand readers. The
  evidence-as-projection design has an existence proof, not a research risk.
- The decision-sufficient envelope: **~35–40 MB per 2-day arm (~24×), ~0.6–0.7 GB per month arm**,
  with dense-day ≈ 250 s close-to-certain from the first audit's own arithmetic.
- The ≤3 GB/arm gate came from a wrong causal story (B84/B85), and §A1 below reports where the arm
  peak actually lives — measured by this review, not inferred.

So: the columnar item was misplaced (already banked at its true value: −9 % wall, free), and the
real Phase 2 for the *monolith* lane is the evidence-schema change — **scheduled at the natural
re-seal boundary, and only if the broad family earns a future** (§4 Stage 5). In the book lane the
evidence architecture is small by construction from day one (§3).

### 1.4 The brake — right mechanism, wrong host, and four real holes

The live-surface reader corrected CLAUDE.md §4 on count and confirmed it on substance [MEASURED
against the VPS export and HEAD]:

- The VPS brake is **three** false YAML booleans (`apply_to_execution`, `live_activation_allowed`,
  `live_broker_authority` — exported working-tree `agent_config.yaml:1161-1163`), not one — with no
  second mechanism, **no monitoring watching the gate block**, and no halt flag anywhere.
  `ultimate_book_live_broker_authority: true` has never existed in any committed config, so
  accidental single-line drift cannot fire it; the risk is deliberate/erroneous edit, and nothing
  would detect one.
- **The activation token exists on mainline only.** The VPS `RealMT5.order_send` calls the raw
  module with no guard (`git show redacted_host:src/mt5/mt5_real.py`). Mainline's token layer is real
  and well-tested (36 dedicated tests; HMAC-signed, account/namespace/config-bound, ≤720 h expiry;
  risk-reducing requests exempt).
- Four genuine holes found, none previously filed — each then re-verified end-to-end by this
  review's adversarial pass (§A2): (1) `RealMT5.get_positions` masks broker fetch errors as `[]`
  and filters by magic number (`mt5_real.py:321-333`), so under token-absent + a transient fetch
  error a **close is refused as exposure-increasing** — and a stop-tighten is refused as
  `exposure_increasing_sltp_unknown_position` by the same path; the designed
  `risk_reducing_position_close_unverified` fail-safe branch is unreachable through the real
  adapter because it triggers only when the provider *raises*, and this one never does
  (`activation_token.py:394-437`). The never-strand invariant has a hole in exactly the state it
  exists for. (2) `GTOS_UB_DERISK_MODE` overrides the YAML derisk mode (`book_engine.py:580-581`)
  outside the config digest a token binds (`config_digest_for` hashes exactly two files' bytes) —
  qualified precisely: at the ≥2.0 % dial `admit_and_size` fails closed on any non-smooth mode
  (`admission.py:1367-1370`), so the live-dial exposure is a *silent fail-closed trading stop* plus
  un-audited derisk-shape drift at sub-2.0 % dials, not un-certified trading. (3)
  `scripts/mt5_preflight.py` remains a raw `mt5.order_send` path — armed only via
  `--test-order`/`GTOS_MT5_PREFLIGHT_TEST_ORDER=1`, default observation-only, but with no halt
  check and no token when armed (CLAUDE.md H6's "still default-live" is the stale phrasing; the
  review's ask stands: gate or retire it). (4) the charter's culmination item 6 says "credentials
  are absent" — they are **present** today (authenticated terminals, `trade_allowed` true, in
  shadow), a divergence the plan never states for the owner to accept or remediate.

**The plan's activation sequence was inadequate to this.** Phase 7 packaged the token; the evidence
says the token (plus the four fixes) is **item 0**, not a phase-7 deliverable — deployment-safe
while the gates are false, ~0.5–1 day including the VPS ceremony, and it converts the standing
hazard class rather than documenting it.

---

## 2. The unconstrained architecture

Four genuinely different architectures were generated independently and judged against the charter
by three judges with different lenses (charter-fidelity, evidence-honesty, execution-realism).
Result: **the Settled-Book Line** (payout-first) won two of three judges and the aggregate (104,
vs SPINE/truth-first 92, GTOS-Kernel/deletion-first 90, Forward-Court 80). The synthesis below is
the winner with the losers' best elements grafted on — each graft named. What follows is design
[DESIGN] grounded in measured facts cited where they bind.

### 2.0 The shape in one paragraph

GTOS's next system is **the W7 book made honest, measurable, and portfolio-general** — not the
monolith made faster. Seven components: a broker-truth layer that owns every cost and firm-rule
number; a re-costed validation that turns the only positive evidence in the tree into a cost-true
survivor book (or an honest kill); a book replay lane (Session H's policy layer + a generation
port) that makes the declared-live surface fully measurable for the first time, with sub-window
replay and portable seals native because the lane is small; a forward-shadow lane formalising the
VPS stream the system already pays for; the safety spine (activation tokens) on both hosts; an
activation dossier that is the single owner-facing surface for every decision; and the parked
broad-stack estate — monolith, contract, sealed January, learning stack — kept as history and
optionality, with nothing on the payout path running through it. The policy-plural core survives
from my plan, but it grows *from the book lane outward* (SleeveBookPolicy is its first validated
citizen) instead of being built at monolith scale first.

### 2.1 The components and what each owns

**A. Broker-truth layer** (`src/costs/` + versioned `BROKER_TRUE_COSTS_V1.json`). One function —
`cost_r(symbol, account, holding_hours) → {commission_r, swap_r, spread_r, slippage_r}` — backed by
Session E's measured tables (commission by instrument from broker truth; slippage +0.013 R measured;
stops fill clean at −1.0036 R gross), the vendored `BROKER_SYMBOL_SPEC_COMPARISON.json`, and
tick-derived spread. **Every number carries a coverage class** ([MEASURED]/[TRANSFERRED]/[MODELLED])
that travels into any result computed from it, and ×0.5/×1/×2 sensitivity bands (Kernel graft).
Also owns firm-rule truth: the two daily-reset clocks (B56), max-DD/daily-loss rules, and a payout-
rules capture per firm done the way the reset clocks were captured — never asserted from memory.
Replaces the five zero-commission sites (F38), the wrong-sign erosion application (F39), and the
unenforced spread floors (F40).

**B. Re-costed validation** (`w7_recost/`). Per-row arithmetic over **the series CYCLE62 actually
consumed**: `INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl`, which this review's
adversarial pass reconciled to CYCLE62's 1,679-day core-8 series **to the day** (all 8 sleeves,
per-trade sym/date/R — the whole rerun chain is at HEAD: `KB7_growth_kelly_sizing.py`,
`INTEG_W7_final_book.py`, `KB7_tick_mc.py`, and `CYCLE62_core8_revalidation.py` resolvable from
this worktree's git). `D4_COMBINED_TRADE_LEDGER.jsonl` supplies per-trade state and re-sim
coordinates only — it covers 7 of 8 sleeves and its metals rows are a re-simulation diverging
0.60 R mean-|Δ| from the consumed series [verifier-measured]. Published as a **sensitivity band
across both F39 readings** (spread-only vs commission-inclusive map intent — the record cannot
settle which was meant, so both are computed), then the MC re-run with the erosion sign fixed and
commission added, at the live dial, per account — the drop-sleeves operation is precedented, not
novel: CYCLE62 itself built core-8 by zeroing clean-3 columns of the joint daily matrix and
re-running the block-bootstrap MC, which preserves cross-sleeve correlation by construction
(`CYCLE62_core8_revalidation.py:21-31`, `CYCLE59_live_book_ddefense_sizing.py:52-77`). Output:
cost-true expectancy per sleeve×symbol with coverage classes on every cost input ([MEASURED] for
live-traded instruments; [TRANSFERRED] bands for energy/agri, DASHUSD, metal crosses, the
unmeasured quarter of `idxrev`'s universe); a kill list (USDJPY killed by commission on the
validation's own rows; the JPY cluster killed on live evidence; GBPJPY's failure gross-edge, not
cost; crypto banded); **`SURVIVOR_BOOK_V1`** — a registry-subset definition, not new code; and
cost-true p_pass / worst-day / days-to-target distributions **restated in calendar days** (the
CYCLE62 series is book-active days at ~57 % weekday density — §8). Carries the in-sample caveat
verbatim (judge graft): **this repairs cost optimism, not selection bias** — CYCLE62 remains
mined-era evidence; only out-of-window replay (C) and forward shadow (D) can kill a false GO.

**C. Book replay lane** (`src/research_infra/replay_policy/` grown by a generation port). Session H
proved the decision side by delegation (zero disagreements over 617 unit-bearing live cycles;
130/132 transmitted risk percents). The missing half is candidate generation (bars → sleeve
intents), deliberately excluded by B91. Port it behind the same protocol, with the **K1 acceptance
gate** (Kernel graft): reproduce the 617 unit-bearing live cycles **end-to-end from bars** —
generation + decision + units — at zero disagreements through Session D's harness. That single run
*is* the G4 settling move the G1b receipt names (§9: replay the live window through the book and
count generation per sleeve). Then the survivor book replays over 2024–2026 bars at cost-true
prices — the frequency and out-of-window evidence the activation decision needs. Sub-window replay
and portable seals are native here **by construction**: the lane is stdlib-pure and small, so H4/H5
never exist in it. What a sealed book-arm emits is §3.

**D. Forward-shadow lane** (the VPS stream, formalised). The book has been writing runtime-learning
packets continuously since deactivation — 99,112 over 38 days already banked. Weekly read-only
export ritual; `packet_validation.py` ingest; survivor-book admissions scored through
`SleeveBookPolicy` at cost-true prices; a tracking-error row in the dossier. Grafted from
Forward-Court: **emit-time schema validation** (a packet omitting a declared field fails at emit —
kills the F36 class structurally, instead of filing it), the **export-cadence silence alarm** (the
three execution ledgers died silently on 07-02 and nothing noticed — V3), and per-sleeve generation
counts as permanent packet telemetry so G4 can never silently regress. Honest limit, stated because
a judge caught the overstatement: the five silent core sleeves emitted no `unit_placed`, no
`unit_admitted`, no `unit_shadow` across all 99,112 packets — so the banked stream contains
approximately **zero tracking-error content for the survivor composition**; this lane starts
earning only after the generation port lands, at the book's own cadence. Two further export
constraints apply and are inherited, not solved: V2 — the broker-order lifecycle capture holds
request-side rows only (594 rows, no fills), so fill-truth for the shadow lane starts at its
Stage-3 repair; V5 — broker truth exists for all three accounts in the export, which is what lets
the dossier's firm-rule MC be per-account rather than generic (`VPS_EXPORT_FINDINGS.md`).

**E. Safety spine.** The activation token on **both** hosts (the VPS carry is constrained-plan item
0), the four §1.4 holes fixed, tokens extended with symbol/exposure bounds for canary scoping,
`mt5_preflight.py` gated or retired, and a gate tripwire in the monitor. Sessions never execute
broker-capable scripts; the VPS deploy is an owner-executed runbook.

**F. Activation dossier + thin command center.** One evolving `ACTIVATION_DOSSIER.md` plus a small
CLI (`gtos status`) over the book-evidence index and shadow scoring: the cost-true validation table,
the G4 verdict, historical replay results, forward tracking error, per-account firm-rule MC, and the
**owner-decision queue as typed packets** (SPINE graft: decision / evidence / options /
recommendation / explicitly-not-taken). Every number carries its evidence class. The owner reads one
place; the system recommends; he decides.

**G. The parked estate.** The monolith, the R2 contract, sealed January, the April partial, and the
learning stack are kept as history and optionality — **nothing on the payout path runs through
them.** January is banked before parking (§6.2). The learning stack wakes when it has a consumer
(§4 Stage 5): its first production use remains the book-lane rerate producer, now pointed at
cost-true inputs — and the capture layer that eventually feeds the candidate lane is specified from
the dataset builder's input contract *at design time* (the learning reader showed the sealed arms
cannot feed it at all today: the builder requires a per-day ledger kind the runner never emits).

### 2.2 What survives from my plan, explicitly

The policy-plural core (H's protocol is its first citizen and worked exactly as designed); the
differential-harness-first ordering; OD-2's forward-only re-seal split (every wave-2 session worked
under it without one re-seal); the truth instruments (reducer, matrix, clock, harness) as permanent
acceptance machinery; forward shadow as the evidence class that ends every path; and the walk-forward
gate as the only way sleeves enter or leave a live book (it has already proven it will refuse a
degenerate model — the June run failed a model that admitted zero candidates, correctly).

### 2.3 What the unconstrained answer deletes from my plan

The ≤3 GB/arm gate and the parallel-replay program behind it (wrong derivation, B84/B85, and §A1
settles where the memory actually is); BroadV4Policy as *primary* (it becomes optional research
capacity, 2–4 sessions by delegation if the broad family ever earns a slot — the broad-stack reader
confirmed extraction-by-delegation is feasible but that G2 "row-exact" as written smuggles Phase 3
into Phase 2 and must be re-scoped to decision-level parity); the campaign-completion-before-
anything sequencing; and the assumption that the monolith's evidence machinery must be *projected*
rather than mostly **not emitted** (0.155 % consumption — §3).

### 2.4 Is this build-the-system, or is it the patching the owner banned?

Confronted directly, because Borhen's central directive (`OWNER_SESSION_CONTEXT.md` §4: *"stop
patching, build the system"* — GTOS as "a museum of default-off capability… built, gated off, and
then patched around") is the standard this architecture must pass, and a fast read of Stage 1
("re-cost, subset the registry") could look like the banned pattern. It is the opposite move: the
pattern the owner banned is *adding a gate around a defect*; the re-cost **removes the defect from
the system's one validated capability** (a cost model that was wrong at five sites) and the
survivor book is not a wrapper but the validation finally allowed to say what is true. The same
test applied across the plan: the token replaces absence-of-halt semantics rather than adding a
second flag; the generation port completes a half-built capability (H's policy layer) rather than
gating it; the evidence redesign deletes emission rather than projecting it; and the learning stack
is woken by giving it the input contract it always lacked, not by another enable flag. Where the
architecture *does* gate — the walk-forward gate as the only door into a live book — it is the one
gate the owner's own charter demands. On the owner's other standing point (compute is not a
constraint): agent compute is treated as free throughout; the ~36 MH campaign price is **this
machine's** wall-clock, which is genuinely scarce (one 16 GB Mac, one arm at a time), and that is
the only sense in which any cost below is "expensive."

### 2.5 The vision map, reconciled

The mandate asks what the standing capability map
(`.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md`, 2026-06-07) still governs.
The vision reader's roll-up across its ~90 limitation bullets [reader-verified; full table in
`third_review_receipts/read_vision.md`]: **~20 % RETIRED** (cleanest: clock truth — both audits had
the wrong calendar and the file's worry is now a fail-closed resolver; the research-process section
is fully retired — adversarial passes and failure-set A/B are now institutional), **~25 %
CONVERTED-TO-MEASUREMENT** (execution friction inverted: stops fill clean, slippage half of
modelled, the real friction is the missing commission term the vision never suspected), **~35–40 %
STILL-OPEN** (the M15 decision loop stands; Market Awareness is fully untouched), **~15 %
NEVER-REAL** (the autonomous self-repairing companion is an explicit anti-goal — the historical
instance was hot-patching live trading code between ticks; orderflow/depth and the all-symbol tick
loop are silently dropped). Three failure modes the eight sessions proved that the vision never
names, adopted as first-class concepts here: **deployment-state verification** (the halt flags did
not exist and nothing noticed for two months), **validation-frequency economics** (a validated
sleeve that never fires is unmeasurable live — §2.6 risk 1), and **"the live portfolio is not the
validated portfolio"** (B99b). What the Settled-Book Line consciously drops from the vision: the
vision's implicit premise that the vNext selector path is the live path (falsified — V4's gates
never fire, `permissions.py:930`), and its replay-at-maximal-scale ambition, replaced by
replay-at-the-scale-the-candidate-needs. The dormant learned-edge lane the vision calls missing
("no feature store, no label store") exists at HEAD and is dead only at its input contract — the
vision under-claims what is already built.

### 2.6 Where this architecture is most likely wrong (its own risk register)

1. **Costs and liveness are anti-correlated on the high-weight complex** (the judges' sharpest cut,
   precision-fixed by the adversarial pass): the near-zero-commission **metals** sleeves — the
   registry's highest-confidence tier — are exactly the ones never observed firing live; `idxrev`
   is the exception on both axes (commission-free *and* the most-firing, most-profitable live
   sleeve — while being train-falsified at the lowest confidence tier). The survivor book may be a
   book whose validated weight rarely trades — the re-cost can return GO on expectancy while
   G4/frequency returns "glacial." That is why Stage 1 runs both before OD-3, and why
   calendar-restated days-to-target distributions (not just expectancy) are first-class dossier
   rows.
2. **The re-cost inherits the validation's generation and fill assumptions** — it repairs cost
   optimism, not selection bias. A false GO dies only at out-of-window replay and forward shadow;
   both are in the critical path, neither is skippable.
3. **The candidate/expansion books' validations are proxy-grade and placebo-failed, not absent** —
   corrected from this review's own first draft: the candidate book carries an A8-frame MC/proxy
   package (Sharpe 0.277, MC pass 0.9999) **whose own random-day placebo it fails**
   (p(random ≥ observed) = 0.59), and the market-expansion book carries the owner-approved
   `positive_weighted12_after_swap` package (Sharpe 0.284) — neither ever jointly validated with
   the core book at the live dial (CYCLE62 contains zero occurrences of "candidate"/"expansion"),
   and the expansion book's fortnight sample is n=5, negligible either way. They enter the pool
   only through the walk-forward gate like everything else.
4. If Stage 1 kills the survivor book too, the payout path lengthens honestly (§8) — the fallback
   is the learning lane over the capture layer, not a quiet return to the broad incumbent.

---

## 3. What a sealed arm should emit

Grounded in the measured bill [reader-measured against the three surviving SESSG arm outputs;
method and per-role tables in `third_review_receipts/read_evidence-cost.md` — "value-read"
operationalised as: bytes any of the three consumer classes (arm acceptance, the January economic
analyzer, the learning-lane dataset builder) actually reads as values rather than hashes]:
932.1 MB per 2-day arm, of which decision consumers ever value-read ~1.3–1.6 MB (≈0.16–0.18 % —
the reader's 1.33 MB census plus the two consumers the adversarial pass showed it missed: Session
A's reducer, ~30 KB of trade-role fields per 2-day arm, and the analyzer's window-membership scan,
one timestamp per row of five roles ≈ 0.2 MB); the compact typed sink already achieves 28.7× on
decision+missed; `SEMANTIC_CANDIDATE_LEDGER` proves a 611 B/row candidate record beside 48.6 KB/row
missed-ledger rows (80× per-record gap). Session F's matrix reads no role bytes at all (it takes
the arm receipt and config); every consumer in the corrected census is projection-compatible — it
reads fields the compact streams carry — so the >99.8 % never-value-read conclusion, and nothing
weaker, is what the redesign rests on.

**Book lane (new, from day one).** A sealed book-arm emits one `BOOK_ARM_RECEIPT.json` +
five small ledgers, target < 20 MB/month: config fingerprint (registry subset + `BROKER_TRUE_COSTS`
version + bar-source sha256 manifest with **repo-relative paths** — killing H4 in this lane);
per-sleeve generation counts (G4 telemetry, permanent); a decisions ledger (one row per decision);
a fills ledger with **gross, cost, and net R side by side** (the B69 rule — a cost can never again
be read as slippage); daily equity + governor curve; the `ADAPTER_DIVERGENCES`/`PLACEMENT_GATES`
coverage statement; and the divergence-matrix verdict. **Every field names the decision that
consumes it or it is not emitted** (SPINE's proof-budget rule, enforced by schema). Acceptance =
Session D's harness + Session F's matrix + Session A's reducer re-run — the three truth instruments
the waves already built, now doing their permanent job.

**Monolith lane (only if the broad family returns; at the natural re-seal boundary).** Make the
compact typed event stream the ledger of record for decision/missed/scorecard-trace; the eleven-role
acceptance hashes bind the compact streams; expand-on-demand readers (already proven by the cold-
evidence pattern). Split the missed role into a ~1.5 KB/row label+identity record (learning +
economics) and compact forensic events — 428 MB → ~15–20 MB per 2-day arm, and it retires most of
the 26.2 %-of-wall attribution-construction on the missed path. Demote the two scorecard trace
megafields to the compact sink (174 MB → ~5 MB). Emit once-per-scope subtrees (arm-constant,
day-constant, window-constant) with references — ~170 MB of the 2-day arm. Turn off
`materialize_semantic_diagnostics` on sealed arms (49.2 MB/arm consumed only by a verifier the
enforcement loop never executes — verify the flag sits outside the namespace contract first).
Envelope: **~35–40 MB per 2-day arm, ~0.6–0.7 GB per month arm, dense day ≈ 250 s** — a ~24×
evidence reduction that is simultaneously most of the CPU fix (60.6 % proof self-time) and, per
§A1's attribution, the memory fix as well. All of this is one contract regeneration scheduled at
the same boundary as any campaign restart — never as its own re-seal event.

---

## 4. The constrained plan

The unconstrained answer minus nothing impossible — every item below is executable now; the
constraint applied is honesty about calendar physics and owner boundaries. Costs are stated as
agent-sessions (AS), machine-hours (MH), or calendar. Items marked **[OWNER]** are decisions, not
work.

**Stage 0 — the brake and the banked decisions (this week; ~2 sessions total, no replay time)**

| # | Item | Cost | Unblocks |
|---|---|---|---|
| 0.1 | **VPS token carry**: `src/safety/` as a package (not one file — `authorize_raw_broker_request` lazily imports `runtime_halt`), `mt5_real.py` guard, `run_book.py` context call (a 17-line delta against the VPS copy [verifier-measured]), P4 `create_mt5` validation; verify zero-token status + one healthy shadow cycle. Deployment-safe while gates are false — mechanically verified: the carry imports nothing from the `book_owner`/packet coupling trap, zero-token shadow is a no-op at every call site, and the risk-reducing exemption lives in the token layer. Note: `run_book.py:201` constructs `RealMT5` directly, so P4 protects the *other* entrypoints; the healthy-shadow-cycle check exists to catch exactly a mode-string surprise. | 0.5–1 AS + owner VPS ceremony | Converts the standing hazard; every later activation step |
| 0.2 | The four §1.4 holes: masked-`[]` close-refusal; `.env` derisk-mode outside the token's config digest; gate tripwire in `monitor_books.py`/digest; gate-or-retire `mt5_preflight.py`. | ~1 AS | The never-strand invariant actually holds |
| 0.3 | **[OWNER] Decision batch #1**, delivered as typed packets: (a) end the JPY-cross trial (measured dead: −0.453 R gross, signal-level p 0.0059) — *reframed*: `one_unit_per_cluster_per_day` is globally `false` at HEAD (`agent_config.yaml:1373`), so the real decision is whether to re-impose the certified one-unit envelope at all; (b) candidate book on/off at the 2.0 % base (76.4 % of the net loss; its cited validation is proxy-grade and failed its own random-day placebo, p = 0.59; never jointly validated with the core book at the live dial); (c) Q8 — three tests pass only when a live gate is OPEN; (d) B54 Part 2 day-key re-key, after H's MC pack. | minutes each | Config truth matches evidence |
| 0.4 | **`JANUARY_BANK.md`** — bank the factorial's portable claims before parking: sizing `material_negative` (standing design rule: *no dynamic runtime sizing on any activation path without factorial-grade evidence*), selection inconclusive, F31 restatement, April partial = salvage-only. Keep **March outcome-unread** (it is the only untouched month for any future broad-family treatment). | 0.5 AS | The park doesn't orphan the lessons |

**Stage 1 — the candidate-decision evidence (~2 weeks of sessions; ~0 replay MH)**

| # | Item | Cost | Unblocks |
|---|---|---|---|
| 1.1 | Broker-truth layer + `BROKER_TRUE_COSTS_V1.json` (coverage classes, sensitivity bands, firm payout-rules capture). | 1 AS | Everything priced |
| 1.2 | **Re-cost the W7 validation** (per-row over the `INTEG_W3`/`INTEG_W5` streams caches — the series CYCLE62 consumed, reconciled to the day by this review's verifier; both F39 readings; MC re-run with fixed sign + commission; calendar-day restatement) → `SURVIVOR_BOOK_V1` or kill. | 1–2 AS | OD-3's first input |
| 1.3 | **Generation port + K1 gate** (bars → intents behind the policy protocol; reproduce the 617 live cycles end-to-end, zero disagreements) → **G4 answered**; survivor book replayed 2024–2026 at true costs (frequency + out-of-window). | 2–4 AS | OD-3's second input; F1 closed at full strength; the Phase-4 walk-forward baseline |
| 1.4 | Session H's cheap evidence packs: dial-counterfactual grid over the 38-day packets (seconds per run); D1 shed A/B over the 1,754 recorded governor states; D2 runtime-day-key MC. | 1.5 AS | Owner decision batch #2 with measurements attached |
| 1.5 | Hygiene batch (no owner decisions): H's D3/D4/D5/D6/D7/D8/D10-guard/D11; C's four B42 defects; B41 L1/L2 vacuous-test fixes; wave4b/c permanently-red tests skipped-with-reason; F30/Q7 suite-notification suppression; B58 ghost references. Full A/B by failure set per change. | 1–2 AS | A clean tree under the new work |

**Stage 2 — [OWNER] OD-3: the activation-candidate decision.** The dossier v1 presents: cost-true
validation table (both F39 readings), G4 verdict, survivor-book out-of-window replay, days-to-target
distributions, firm-rule MC per account, evidence classes on every number, and the explicit
statement of what remains unproven (in-sample selection bias; the book under risk pressure — the
gross-cap shed has zero live evidence). Borhen chooses the candidate composition and dial. Minutes,
after Stage 1.

**Stage 3 — forward shadow that can bear weight (calendar physics begins here)**

VPS packet-emitter hardening in one carry (spread_r, direction on `unit_admitted`, A8 features, raw
governor equity/open-risk — kills the self-fulfilling headroom recovery, makes the shed validatable;
one packet per intent), emit-time schema validation, silence alarm, lifecycle-capture result side
repaired (the named Phase-6 cost source currently records intent only). ~1 AS + owner deploy. Then
survivor-book shadow scoring accrues at the book's cadence — with the honest note that it starts
earning only now (§2.1-D).

**Stage 4 — canary package** (charter rung `CONTROLLED_CANARY_READY_PENDING_HUMAN`). My plan's
Phase 7 stands, plus: token chaos drills (gate-flip-without-token, expiry-mid-position + fetch
error, dir unreadable, clock skew, revoke-restore, wrong Windows user); **pre-registered evidence
targets and evidence-based stop conditions** (measured-cost deviation from the table over n fills →
halt; sleeve-level tripwires of the JPY kind), not only loss limits; and the credentials-present
divergence from charter item 6 stated for the owner to accept or remediate. Scope and dial are
Borhen's, made with the dossier in front of him.

**Stage 5 — the estate, right-sized (parallel lane; never blocks Stages 0–4)**

- **Campaign disposition [OWNER]:** parked as an expiring option, priced: finishing under the frozen
  engine costs ~36 MH serial (April 16.5 + May ~2.7 + March 16.5 — the plan's 49.3 h figure was
  wrong; May is ~3 trading days) and the option expires at the first bound-file edit (then +16.5 MH
  to re-run January for comparability). **If any window ever runs: the pooled promote/reject/
  inconclusive evaluator must be written and sealed first — it does not exist anywhere** [reader-
  verified by search], and reading April outcomes without it would improvise the terminal decision
  post-hoc. Promotion is arithmetically near-foreclosed by January (pooled must exceed +0.1 from a
  −0.152 start; both realistic outcomes route to forward shadow, which Stage 3 reaches regardless).
  The evaluator-absence claim survived a hostile re-search by this review's adversarial pass: the
  promotion-threshold keys appear in the four sealed JSONs and nowhere in Python; the only pooling
  token in route code is a forward-looking boolean whose disposition block hard-codes
  `factor_or_policy_promotion_authorized: False` (`analyze_…_january.py:3728-3732`). And sharper:
  **the protocol seals the thresholds but not the pooling weights** (by-window vs by risk-cash), so
  even the pooling semantics would otherwise be chosen after seeing the data. Under either weighting
  April would need a total effect of roughly +0.36 to +0.45 from a family whose every measured cell
  is negative. Also priced correctly now: April carries **no partial credit** — the runner refuses
  any non-fresh output namespace (`b7_5_post_acceleration_runner.py:292-315`) and hardcodes away
  sub-window on the sealed path (`:832`), so the 15-day S1R1 partial cannot resume (April is 15
  sealed days, not CLAUDE.md §4's "16 of 30" — B36).
- Monolith evidence-schema change per §3, at the same boundary as any campaign restart.
- BroadV4Policy by delegation (2–4 AS) *if and when* a repaired broad family seeks a slot through
  the walk-forward gate; G2 re-scoped to decision-level parity.
- Learning lane: book-lane rerate producer (~1 AS) once Stage 1 gives it cost-true inputs — noting
  `recommend()` currently ignores `live_meanR`/`live_n` (~20-line extension) and the June run's
  correct refusal is the gate working; trainer hygiene (per-fold specs, purge/embargo, ~1 AS)
  before any training run; the B7.5 partition registry re-authored (the existing one marks March
  2026 as TRAIN — it must never be passed to the builder as-is).

**Execution logistics (the questions Borhen will ask first):**

- **The two running VPS books change nothing today.** They stay in shadow exactly as they are —
  supervisor Running, packets accumulating, placement gates false. The only near-term changes that
  touch them are Stage 0.1 (the token carry, a no-op while gates are false) and whichever Stage-0.3
  config decisions Borhen takes, each deployed as its own owner-executed step with the same
  discipline as the token carry. Nothing in Stages 1–2 runs on the VPS at all.
- **Who executes:** the Opus implementation sessions, per the programme's standing convention —
  this review is the input to the next wave's session prompts, which should be commissioned from
  §4's stages the way `WAVE_2_README.md` was cut from the plan (Stage 0.1-0.2 one session;
  Stage 1.1+1.2 one to two; Stage 1.3 its own; Stage 1.4+1.5 one to two).
- **The sleeve census:** the live book is 29 sleeves (core-8 + 9 candidate + 12 market-expansion,
  `admission.effective_registry()`). On today's evidence: the 2 JPY sleeves are dead on live
  measurement; the 5 metals/index/energy-side core sleeves are the likely cost-survivors pending
  the re-cost; `idxrev` is registry-falsified but was the only live-profitable sleeve (the status
  field did not predict live sign — B63); the 21 candidate/expansion sleeves have no validation and
  enter `SURVIVOR_BOOK_V1` only through the walk-forward gate. The census is settled by Stage 1.2,
  not by this table.
- **Total cost to the decision:** roughly **10–14 agent-sessions over ~2–3 weeks** to OD-3, at
  ~zero replay machine-hours. After OD-3 on a GO: Stage 3–4 are ~2–3 sessions of engineering plus
  calendar physics (§8). Stage 4's package assembly is ~2 AS. AI compute is not the constraint
  (owner's word); this machine's replay hours and the VPS deploy ceremonies are the only scarce
  resources in the plan.

---

## 5. Verdict per session

**Phase-0 Sessions 1–2 (fork reconciliation, token, OD-2) — KEEP.** Reconciled the live fork,
vendored `run_book.py`, built the activation token, landed OD-2, and the second session's
adversarial pass caught the first's A/B holes (B24) — the discipline that then propagated through
every later session. The token's VPS carry (Stage 0.1) is its unfinished half.

**Session A — shadow reducer (G1a) — KEEP, and make it permanent.** The first genuine economics
check in GTOS history; found F31 (zero gap-through; −8.095 R lower bound across the sealed arms;
ordering and classifications unchanged — B34); correctly did not block April. Extend: the reducer
runs on every future arm as part of acceptance; open the tick source for the F31 rows (declared
gap, ~0.5 AS) to bound observation granularity vs genuine gap-through; the gap-through cost term
goes into any future core exit model before an absolute number reaches a canary argument.

**Session B — clock truth — KEEP.** Both audits named the wrong calendar; B measured the right one
five ways and shipped a fail-closed resolver. Residue: the redacted_account DST-window gap (one read-only
probe on the VPS closes it, batched with the Stage-3 carry) and the B29-Part-2/B54 owner decision
(Stage 0.3d).

**Session C — red suite + deletion — KEEP.** Closed Q4 (77.4 % environment-bound; zero genuine
defects on the live decision path), and its producer-side sweep collapsed the first audit's
219,469-line LOW tier to **8 lines** — establishing route-level retirement on owner decisions as
the only valid deletion unit. Its four B42 defects land in Stage 1.5.

**Session D — differential harness — KEEP.** A thin driver over the sealed comparator instead of
the plan's three-module revival (two rejected with mechanism — one contract-forbidden, one
input-less: the finding, not a shortfall). Became the programme's correctness instrument within
days (G's B86, H's B92). Open item: the B48 scorecard-encoder decision (P1's Infinity sentinels
make two byte-identical scorecard rows incomparable) must be decided before any parity claim over
scheduler evidence.

**Session E — W7 forensics (G1b) — KEEP, act on it, and amend the receipt.** The strongest session
of the wave (§1.2). Two amendments this review's reader found, to be recorded in the receipt the
same way E recorded its own §14 withdrawals: (1) the JPY "survives Bonferroni" claim fails at the
honest signal-level denominator (29 distinct signals, p 0.00588, ×12 = 0.0706) — direction and
magnitude stand, "decisive" does not; (2) §10 decision 2 is framed on a moot mechanism —
`one_unit_per_cluster_per_day` is globally `false` at HEAD, so the real owner decision is
re-imposing the certified envelope, not the JPY exemption. Also: the packet-telemetry lane rests on
one generator whose adversarial pass covered only the broker-truth lane — treat single-generator
packet claims as one-witness until the generation port cross-checks them.

**Session F — divergence matrix — KEEP as-is.** H7 is now machinery: verdict computed from rows,
laundering fails at acceptance, declarations decay with their sources, the residual row catches the
undeclared. The 42 %-unpaired-signals row is the single best argument in the repo that a replay R
is not a live R. The B79 wiring decision (acceptance-time, not production-time) was the right cost
call; the stronger form stays on the shelf priced at a re-seal.

**Session G — columnar source — KEEP the layer, ADOPT the negative result.** The most valuable
thing G produced is the refutation (§1.3). Keep the free −9 % wall; measure the eviction fix's
arm-level effect in some future quiet window (10 min); **stop all further source-layer RSS work**.
The attribution run G scoped is executed by this review — §A1 — and closes the question G opened.

**Session H — SleeveBookPolicy — EXTEND; it is the seed of the activation answer.** Delegation-not-
copying was right; the validation is honest about its subset; B99b outranks everything in the wave;
B99e's lesson (*"a validated port measured by an unvalidated comparator is not a validated
result"*) becomes a standing rule: every future validation receipt budgets a comparator-refutation
pass. The generation port (Stage 1.3) is its continuation and the programme's keystone.

**The integration review — KEEP.** Zero regressions on the first reproducible baseline; D1
executed (69.2 GiB → 2.5 GB, zero irreversible loss); B56's per-account reset rule fixed in the
dangerous direction's favour.

---

## 6. What to delete or stop doing

Applying the charter's test — proof work earns priority only when it unlocks a decision or moves
toward operation — to what exists:

### 6.1 Stop (work that fails the test now)

1. **The ≤3 GB/arm program and all further source-layer memory work.** Wrong derivation (B84/B85);
   §A1 attributes the peak; the book lane never has the problem.
2. **Monolith sub-window replay (H5) as an engineering goal.** Priced at a re-seal for a lane not
   on the payout path; the book lane gets it by construction.
3. **Per-file Python deletion analytics.** Closed by B43: the unit is the route, on an owner
   decision. (Deleting Python reclaims ~nothing anyway — the disk was in untracked stores, and D1
   already recovered it.)
4. **Semantic diagnostics on sealed arms** — 49.2 MB/arm consumed only by a verifier the
   enforcement loop never executes; verify the flag sits outside the namespace contract, then stop
   emitting (§3).
5. **Hand-maintained divergence prose.** The matrix owns it now; prose divergence claims that
   bypass it are how H7 decayed the first time.
6. **The two rejected harness modules** stay retired (contract-forbidden output; input format that
   exists for no sealed arm).

### 6.2 Park with a price (optionality preserved deliberately)

1. **The B7.5 campaign** (April remainder, May, sealed March): parked per Stage 5, banked per
   Stage 0.4, priced as an expiring option (~36 MH; expires at first bound-file edit; pooled
   evaluator must be written-and-sealed before any outcome is read). *"A discriminator ranks layers
   of a losing system; it cannot locate edge"* [campaign reader] — its remaining decision value
   (config pruning for shadow, the learning-lane dataset, the March holdout) is real but does not
   outrank the candidate decision, and the learning-lane consumer is broken as-is anyway (the arms
   emit no ledger the dataset builder can read).
2. **The monolith + R2 contract + sealed January**: the parity anchor and design-knowledge archive.
   Nothing deleted; nothing on the critical path.
3. **The learned challenger arm** waits for the new contract generation it structurally requires
   (`selector_v4_learned_edge_enabled` is bound config).

### 6.3 Delete / demote / correct (small, now)

Wave4b/4c one-shots demoted with their 8 permanently-red tests skipped-with-reason (inputs deleted
from history; they can never pass again); `mt5_preflight.py` gated or archived (last ungated
mutating script); the orphaned sleeve-registry LFS payload committed behind a pointer before any
`git lfs prune` can erase the last **git-custodied** copy of a contract-bound input (D-1; a
hash-verified out-of-tree hold copy exists per B53, but nothing committed records that custody, so
D-1's closure condition remains unmet); and the documentation corrections — CLAUDE.md H3 (strike
the echo sentence; 8.61 GB is a 2-day fixture; no month-arm RSS measurement exists), CLAUDE.md §4
(three booleans, no monitoring, gate-4-true never existed; April is **15** sealed days, not "16 of
30" — B36; H6's "mt5_preflight is default-live" → default observation-only, ungated when armed),
CLAUDE.md/IS B58 ghost references, `SECOND_AUDIT.md` §5.3/E8 amendment banner (mirroring the F7
banner), `FULL_VISION_PLAN.md` ≤3 GB re-derivation note and Phase-4 item 1's stack conflation
(§7.8), `research_current_state.md` staleness banner (its live-state claims are affirmatively
misleading today), and `THIRD_REVIEW_UNCONSTRAINED_PROMPT.md`'s evidence-weight numbers (77.5 MB /
MiB / 1,248.7 — §1.3).

---

## 7. On disagreement with myself — corrections to the second audit and the plan

1. **`SECOND_AUDIT.md:619-622` ("15.3 GB is a GiB/GB echo") is wrong and is struck.** Refuted by
   arithmetic and by measurement (B81/B83); §A1 reproduces both fields again. Amendment banner owed
   to §5.3/E8; CLAUDE.md H3 carries my error and is corrected per §6.3.
2. **The plan's ≤3 GB/arm target was derived from a wrong causal story** (R20 as cause). Session G
   measured it non-causal; §A1 supplies the attribution the target never had. The target is
   withdrawn, not re-derived — the lane that needed it is no longer on the critical path.
3. **Both audits named the wrong DST calendar** (B27). Already amended in the plan text; recorded
   here because the failure mode — trusting a plausible convention over a one-script measurement —
   is the programme's signature error, and it was mine too.
4. **F13's mechanism was wrong** (B8): the engine's provenance-refusing atom is correct and the
   fixtures were stale; my implied remedy would have wired cross-stitching into a contract-bound
   file. The fix landed in fixtures; the engine was untouched.
5. **F1's owner-decision update aged badly within 48 hours.** I recorded OD-1 with three
   confounders; E and H showed the confounding was total (B99b). The audit's warning stands; the
   decision it recorded deserves reopening as OD-3 (§1.2).
6. **The plan under-weighted the cost model.** Phase 6 scheduled "cost calibration" as forward-
   shadow refinement; F38/F39 show the cost model decides whether the validated edge *exists*.
   Re-costing is now Stage 1's first input.
7. **The plan's Phase-2 memory/throughput program pointed at the wrong layer** — G proved it; §A1
   closes it. And E10's honest band (10–16×) was itself re-derived against a destination (monolith
   window throughput) that the winning architecture no longer needs.
8. **The plan's Phase-4 item 1 conflated the two stacks** [learning reader]: "B7.5 per-sleeve
   splits" do not exist for W7 sleeves — B7.5's sleeve vocabulary is the broad stack's `fpsc_*`
   package families. The book-lane producer's real inputs are the June deep-history Stack-B chain
   (which my own audit ordered adversarially audited before reliance) plus the live packet evidence.
   The plan's wording would have pointed a session at the wrong registry — exactly the D12 trap
   Session H caught in its own brief.
9. **The plan's G2 gate as written smuggles Phase 3 into Phase 2** [broad-stack reader]: row-exact
   reproduction requires carrying the evidence machinery the extraction exists to shed. Re-scoped
   to decision-level parity (selected ids, actions, sizes, block reasons) with byte parity deferred
   to the projection gate.
10. **What the plan got right, stated plainly:** the policy-plural core; the harness-first
    ordering; the shadow-reducer-first truth sequencing; OD-2's forward-only split; refusing the
    507-red suite as a blocker; and the walk-forward gate as the only door into a live book. Those
    survive into §2 unchanged.

---

## 8. The shortest honest path to first payout

**The honest premise: no policy family today has demonstrated positive expectancy net of measured
costs on evidence that survives its own audit.** The broad stack's record is negative in every
campaign-grade window ever measured. The book's record is invalid-pending-repair. Any path that
skips that sentence lies.

The shortest path that does not lie:

1. **Stage 0–1 (~2–3 weeks of sessions, ~zero machine-hours):** token to the VPS; re-cost the
   validation; port generation; answer G4; replay the survivor book out-of-window at true costs.
   Outcome A: a cost-true, frequency-known, out-of-window-positive survivor book. Outcome B: an
   honest kill. Both are progress; only A continues this list.
2. **OD-3 (owner, minutes):** candidate composition + dial, from the dossier.
3. **Stage 3 (calendar begins):** forward shadow of the survivor book on the hardened packet
   stream. Evidence-defined, per my plan's G6 — but the clock genuinely starts here (§2.1-D: the
   banked 3.5 weeks contain nothing for the survivor composition). Expect **weeks, not days**, at
   the book's own trade cadence — the never-observed-live sleeves are the high-weight metals
   complex (the anti-correlation risk, §2.6).
4. **Stage 4 (owner authorizes):** bounded canary on one funded account under token scoping,
   pre-registered evidence targets, cost-deviation and sleeve-level stop conditions.
5. **The payout itself is firm-rules calendar physics, and the unit conversion matters** [the
   adversarial pass caught this review's first draft eliding it]: CYCLE62's "median days-to-target
   64 (FN) / 110 (FTMO)" are **book-active days**, and the series trades on ~57 % of weekdays — so
   those medians are ≈ **5 and ≈ 9 calendar months**, at the *old, cost-optimistic* numbers,
   against June-era account states rather than firm challenge rules (two phases, minimum trading
   days, payout cycles). The cost-true MC restates all of this in calendar days against the
   Stage-1.1 firm-rules capture; the two already-funded accounts' payout cycles are the shorter
   lane, the challenge accounts the longer one.

**The vehicles, named** (absent from my plan and from every prior framing): the operation holds
**five accounts** — the two connected on the VPS (FTMO #1 ≈ 108 k, recovered by two owner-manual
trades after deactivation; redacted_account ≈ 96.1 k) plus FTMO #2 (100 k untouched) and, per the owner,
**three challenge accounts ready** once the system is proven ("i have 3 challenge accounts ready
after the building of the system is good" — `OWNER_SESSION_CONTEXT.md:110`). The canary in
Stage 4 runs on one of the connected funded accounts under token scoping (which one is Borhen's
call in OD-3's packet); the challenge accounts are the scaling lane after the canary holds, each
adding its firm's challenge-phase duration plus payout cycle to its own calendar. Broker truth for
all three exported accounts already exists to parameterise each account's MC individually
(`VPS_EXPORT_FINDINGS.md` V5).

**Stated as a calendar: roughly one month of engineering-and-decision (10–14 agent-sessions); then
forward-shadow and canary observation in weeks; then the money timeline forks by vehicle — on the
two already-funded accounts, the firm's payout cycle governs and months-scale is plausible; on
challenge accounts, CYCLE62's own medians converted to calendar time say challenge progression
alone is ~5–9 months at the old numbers, and the cost-true restatement will move that in whichever
direction the surviving book's cadence dictates — if Stage 1 returns GO.** If it returns KILL, the
honest path runs through the learning lane over a capture layer that finally feeds it (F5), and is
longer; saying so is the review's job, and pretending the broad incumbent is a shortcut would
repeat the exact mistake this programme has now measured twice.

---

## 9. Integration recommendation

**Merge `review/wave2-integration-20260727` into `main` now, as-is — with one honest residual
stated and one cheap step to close it.** [VERIFIED] `main` is an ancestor (fast-forward);
+80,561/−36 across 41 files; the three conflicted wave-2 merges had **docs-only** conflicts, zero
code conflicts. The A/B evidence, stated precisely after this review's own adversarial pass caught
its first draft conflating two merges: the 507→507 zero-regression receipt (B51/B57) certifies the
**wave-1** merge already in `main`, not this one; **no full-suite A/B exists for the integrated
wave-2 tree itself.** The three wave-2 sessions that touched `src/` each A/B'd zero regressions in
their own trees (B79b, B88, B99a); Session E changed no `src/` file at all (9 files: docs, two
scripts, one test) and has no suite A/B. So: **run one full-suite A/B on the integrated tree at
merge time** (hours, zero replay machine-time) — or merge accepting that stated residual. This
review recommends retiring **nothing** from the four branches. The two receipt amendments for
Session E (§5) are post-merge edits, not holds. This review's branch merges separately after
Borhen reads it — its tree changes are this document, the receipts directory, and §A1's artifacts.

---

## 10. The owner-decision queue, in one place

Everything above that is Borhen's, batched (typed packets per §2.1-F; none taken by this review):

| # | Decision | Evidence attached |
|---|---|---|
| OD-3 | Activation candidate + composition + dial (reopens OD-1 — a contingency the plan itself pre-authorized: *"OD-1 reopens"* is the plan's own standing-risk response, `FULL_VISION_PLAN.md:411`) | Stage-1 dossier: re-cost band, G4, out-of-window replay, days-to-target |
| OD-2 | **Stands unchanged** — the forward-only verification split proved itself: every wave-2 session worked under it, zero re-seals | B75/B80/B88 |
| 0.3a | End the JPY-cross trial; and the real cluster-cap question: re-impose the certified one-unit envelope? (`one_unit_per_cluster_per_day: false` at HEAD) | G1b §5.2/§10 + this review's Bonferroni correction |
| 0.3b | Candidate book on/off at the 2.0 % base | 76.4 % of net loss (B64); validation proxy-grade, placebo-failed p=0.59, never joint with core at the live dial |
| 0.3c | Q8: three tests green only when a live gate is OPEN | B41 L3 |
| 0.3d | B54 Part 2: runtime-derived day key (certified-envelope change) | H's D2 MC pack (Stage 1.4) |
| 5.x | Campaign disposition: finish under frozen engine (~36 MH, evaluator first) / park / retire | Campaign reader's pricing; January bank |
| 1.4 | D0 universe reconciliation (4 metals crosses + DASHUSD absent from both live profiles) — contract-bound profile edits | B99b; next bound-file wave |
| 0.1 | VPS token carry execution (sessions prepare; owner runs on the VPS) | §1.4 |
| — | Charter item 6 divergence: credentials present in shadow today — accept or remediate | Live-surface reader |
| C12 | Legacy history graft (carried from G0 §7; still open, still non-blocking) | F28 |

---

## A1. The measurement this review took: attributing the unattributed ~5.5 GB

**The question Session G left open — where does the arm's peak memory actually live — is answered:
in the decision loop's per-day accumulation of evidence structures.** The monolith's own
row/attribution machinery holds **60.6 % of the Python heap at high-water** — numerically the same
share the first audit measured for proof machinery in CPU, now measured in memory.

**Setup [MEASURED].** The sealed 2-day fixture arm (S1R1, 2026-01-01..02, R2 contract, sealed
source layer, no columnar bridge) run to completion under `tracemalloc(1)` with a 1 Hz RSS+traced
timeline and threshold-triggered snapshot statistics at the Python-heap high-water mark. Harness:
`third_review_receipts/mem_attrib_harness.py` (derived from the audit's `profile_day_harness.py`,
contract → R2; no bound file touched, no re-seal owed); result:
`third_review_receipts/memattrib_result.json`. The fixture reproduced exactly — 8,812 candidates,
10 orders, 5 trades, 96 scorecard, 8,807 missed — identical to Session G's three runs, `error:
None`. Wall 3,957.8 s (6.2× the uninstrumented 634 s — tracemalloc's cost on an allocation-heavy
engine).

**The shape [MEASURED — timeline, 3,481 samples].** Traced Python-heap bytes grow **monotonically
through each replay day** — 0 → 5.5 GB across day 1, releasing to ~1.5 GB at the day boundary,
then 1.5 → **6.38 GB** across day 2 — and collapse at day end. RSS meanwhile stays ~1–2 GB
throughout the loop (macOS compresses the cold accumulation out of residency — the same
maxrss-vs-footprint mechanics B81/B83 established) and **spikes to its 5.98 GB peak at the exact
instant of the day-2 traced collapse** (t≈3,404 s): the day-end finalisation/serialisation touches
the accumulated structures, forcing them resident. `ru_maxrss` for this run was 6.33 GB — residency
under a 6.2×-slower, compression-friendly schedule; the *demand* number is the traced 6.38 GB of
live Python objects at high-water, which is schedule-independent. The known caches were empty at
end (`_file_cache`/`_day_file_cache` = 0 — the engine's chunk-boundary release working, per B84).

**The owners [MEASURED — snapshot at traced 6.38 GB, top-14 files = 95.2 % of the heap]:**

| owner | MB at high-water | share | what it is |
|---|---:|---:|---|
| `v4_timewarp_simulated_live_research_loop.py` | **3,866** | **60.6 %** | the monolith's per-day row/attribution accumulation |
| `moonshot_scheduler_v4_best_trade_allocator.py` | 614 | 9.6 % | allocator surface accumulation (`:2227-2235` collects every decision surface) |
| stdlib `json/decoder` | 401 | 6.3 % | retained parsed day-pack JSON (9.3 M dicts) |
| `attempt5` runner | 366 | 5.7 % | incl. the tick `_day_cache` dict-normalisation (`:7803`, 186 MB — B84's named copy layer, now sized) |
| stdlib `copy`/`dataclasses`/`json.encoder` | 489 | 7.7 % | deep-copies, dataclass churn, serialisation buffers |
| `live_decision_packet_v4` + `probability_debate_v4` | 158 | 2.5 % | packet objects |
| **source layer** (`integrated_source` + `prepared_day_pack`) | **99** | **1.6 %** | — the columnar target, measured tiny at high-water |

Inside the monolith's 3.87 GB, the top sites are named machinery, not mystery: the recursive
`cleaned()` deep-rebuild of nested row structures (`v4:14756-14798`, **~840 MB / 5.3 M objects**
retained as sanitised copies); the package-authority attribution-field builders
(`ultimate_package_effective_signal_fields` at `v4:69127`, 469 MB at ~5 KB/object;
`v4:67997` 272 MB; the parity-field seeds at `v4:69626` 121 MB) — **the same
attribution-field family the first audit measured at 26.2 % of wall-clock**; and row construction
with alias splicing (`v4:18676`, 132 MB).

**What this settles.**

1. Session G's negative result now has its positive complement: the source layer is **1.6 %** of
   the high-water heap. No source-layer work of any kind can move the arm peak. The ≤3 GB/arm gate
   was pointed at the wrong five gigabytes.
2. **The evidence machinery is simultaneously the bytes (§3), the CPU (60.6 % self-time), and the
   memory (60.6 % of heap)** — one redesign, three resource problems. §3's emission redesign gains
   its memory corollary: rows written/spilled when produced instead of accumulated per-day would
   remove most of the monotonic ramp by construction. Stated as direction, not as a new gate — this
   review declines to mint a successor to the ≤3 GB number it just retired; if the monolith lane
   returns (§4 Stage 5), the target is re-derived from this attribution at design time.
3. The B7.5 windows, if ever resumed on the frozen engine, run at today's footprint — this changes
   nothing for the parked campaign's pricing.
4. Caveats, stated: `tracemalloc(1)` attributes by allocation site, not retaining owner —
   file-level attribution is robust, per-site ownership is indicative; traced bytes exclude
   interpreter/allocator overhead, so the true demand is somewhat above 6.38 GB; and this remains
   the programme's one profiled fixture (2-day S1R1) — the first-audit reader's caveat that every
   profile number descends from this fixture family applies to this measurement too.
5. **Contention robustness** (the machine carried browser/session load during the run, so this is
   stated rather than assumed): the decisive numbers — traced heap, the per-day ramp shape, and
   the allocation-site attribution — count live Python objects and are **immune to system memory
   pressure by construction**; the fixture's row counts reproduced exactly, so the computation was
   identical. The run's own counters confirm it was undisturbed: **99.1 % CPU-bound**
   (utime+stime 3,923 s of 3,958 s wall) and **75 major page faults** total — against 1,756 in the
   audit's known-contended run (B81). Only the RSS side-readings are residency outcomes under
   whatever compression pressure prevailed, and §A1 already treats them as such — the 6.2× wall
   ratio is therefore tracemalloc-dominated, with contention a minor term.

Arm outputs (877 MB, `MEMATTRIB_*` under the columnar worktree's route directory) were this
review's own dirt, deleted by explicit path after the receipt JSON was vendored — per B88's rule,
no `git clean` anywhere near that route.

## A2. Adversarial verification of this review

Four independent agents were run against the review's own text before it reached the owner — three
refuters instructed to attack its pillars and default toward "refuted" when uncertain, and one
completeness critic reading it against the mandate. **They changed this document**; every change is
folded into the sections above, and the material verdicts are recorded here so the corrections are
visible rather than silent (the discipline Sessions E and H established). Full transcripts:
`third_review_receipts/` holds the reader/panel evidence they audited against.

**Refuted or weakened, and corrected above:**

1. **§9's integration A/B was a conflation** (refuter 2): the 507→507 zero-regression receipt
   (B51/B57) certifies the *wave-1* merge already in `main`; **no full-suite A/B exists for the
   integrated wave-2 tree**, and "each session independently A/B'd" was true of three of four
   (Session E touched no `src/` file and has no suite A/B). §9 now states the residual and asks for
   one full-suite A/B at merge time. This was the review's most consequential error — the exact
   "confident first answer" failure the programme keeps measuring.
2. **The re-cost substrate was wrong** (refuter 1, who ran the reconciliation): `D4_COMBINED_TRADE_
   LEDGER.jsonl` covers 7 of 8 core sleeves (no `fx_jpy_ny`), its metals rows are a re-simulation
   diverging 0.60 R mean-|Δ| from the series CYCLE62 consumed, and CYCLE62's n=1679 is a *daily*
   series built from `INTEG_W3/W5_streams_cache.pkl` — which the verifier reproduced **to the day**
   from HEAD. §1.2/§2.1-B/§4-1.2 now name the caches as the substrate and demote D4 to re-sim
   coordinates. The drop-sleeves MC was simultaneously *validated* as precedented (CYCLE62 itself
   zeroed clean-3 columns and re-ran the block-bootstrap MC, preserving cross-sleeve correlation).
3. **The kill/spare cost map was too coarse** (refuter 1): commission kills USDJPY on the
   validation's own rows but only dents GBPJPY (whose live death is gross-edge); energy/agri,
   DASHUSD, the four metal crosses and ~24 % of `idxrev`'s universe are commission-**unmeasured**
   and now carried as [TRANSFERRED] bands; `idxrev` — the one commission-free sleeve — is the
   registry's lowest-weight, train-falsified sleeve and raw-negative inside the validation cache
   (−237 R over 6,473 rows) while being the only live-profitable one. §1.2/§2.6 restated.
4. **Two absolutized sentences were false at the letter** (refuter 1): "negative in every cell
   anyone has ever measured" (two 1–2-day bounded probes are positive and disqualified by their own
   source) → "every campaign-grade window"; "the candidate/expansion books have no validation at
   all" → proxy-grade, placebo-failed (p = 0.59), never joint with the core at the live dial — the
   honest packet for owner decision 0.3b.
5. **The payout calendar elided its own unit** (refuter 1): CYCLE62's 64/110 days-to-target are
   *book-active* days at ~57 % weekday density → ≈5/≈9 **calendar months** at the old numbers,
   against account states rather than firm challenge rules. §8 restated; the "two-to-four months"
   total is now forked by vehicle and conditioned.
6. **The 0.155 % consumption census missed two consumers** (refuter 3): Session A's reducer
   (~30 KB/2-day arm — 47× the census's trade-role count) and the January analyzer's per-row
   timestamp scan (~0.2 MB) → ≈0.16–0.18 %; and §0's paraphrase had dropped the "value-read"
   qualifier without which the claim is flatly false (acceptance *hashes* 100 % of the bytes).
   Corrected in §0/§1.3/§3.
7. **§1.4 hole 2's threat framing was too strong** (refuter 3): at the ≥2.0 % dial the smooth-mode
   interlock fails closed (`admission.py:1367-1370`), so the env-override hole is a silent
   fail-closed trading stop plus sub-2.0 %-dial drift, not un-certified live trading. Hole 3
   gained its "default observation-only, ungated when armed" qualifier (and exposed CLAUDE.md H6
   as the stale text). Hole 1 was *understated*: the same masked-`[]` defeats the SLTP fail-safe.

**Confirmed as written (the pillars that held):** the pooled promote/reject evaluator's
non-existence and the near-foreclosure arithmetic — strengthened: the protocol seals thresholds but
not pooling weights (refuter 2, hostile re-search); the ~36 MH campaign price, May = 3 trading
days, April = 15 sealed days with no resume path (runner refuses non-fresh namespaces); the VPS
token carry's deployment-safety, mechanically proven to the 17-line `run_book.py` delta and the
absence of any `book_owner` import coupling; the Session E receipt amendments (Bonferroni
re-derived exactly: 29 signals, 12 concordant pairs, p 0.00588, ×12 = 0.0706; cluster cap globally
off at `agent_config.yaml:1373`); the §7.8 stack-conflation correction (82/82 registry rows are
`fpsc_*`); the masked-`[]` close-refusal hole (end-to-end trace); and **25+ load-bearing numbers
re-verified against primary artifacts** with exactly one discrepancy found (a commission range
endpoint, fixed).

**The completeness critic** forced: the §2.4 build-don't-patch confrontation, the §2.5 vision-map
reconciliation, the execution-logistics block (the running books' disposition, executor, sleeve
census, cost totals), the named accounts and vehicles in §8, artifact paths on the broad-record
numbers, the receipts directory itself, and honesty in this document's header about what was still
in flight when earlier drafts were committed. It also independently re-verified three pillar facts
(the D4 ledger's fields, the masked-`[]` hole, the cluster-cap-off config) — all held.

The pattern across all four agents matches the programme's history exactly: the architecture and
the recommendations survived; the confident specifics — a substrate name, an absolutized "every,"
a conflated receipt, a dropped qualifier — did not. That is why this section exists.
