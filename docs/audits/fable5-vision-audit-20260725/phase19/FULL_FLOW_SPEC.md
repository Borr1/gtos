# FULL FLOW — the broad-V4 system start to finish, one link at a time, flawless or repaired

**Session FA (continuation), OD-BROAD-FORENSIC-2. Working draft — this document is the repair
program's completion criterion: it is DONE when every link's verdict column reads FLAWLESS or
carries a LANDED repair id with its measured delta.** Column key:

- **SUPPOSED** — design intent, from code and charter (file:line cites; engine paths per
  `research/operations/wave19_broad_forensic_2026_08_01/cartographer/DECISION_CYCLE_MAP.md`,
  which recomputed and reconciled every number it cites).
- **DOES** — what is measured (receipts named per cell; evidence class labeled).
- **VERDICT** — FLAWLESS, or DEFECTIVE/MISCALIBRATED + repair id.
- **EDGE** — where edge enters / leaks at this link, in R (window named).

Abbreviations: `v4t` = `src/research_infra/v4_timewarp_simulated_live_research_loop.py`;
`bog` = `src/components/broader_origin_generators.py`; `bnce` =
`src/components/broker_net_cost_engine.py`; pools = CJ re-clocked January (27,658 scoreable) /
CP virgin February (24,239). Status tags: [P1] = FA Phase-1 measured; [A2] = continuation-verified;
[WALK] = awaits the instrumented 2-day walk; [T1]/[T2] = awaits pool screen / lane arm.

---

## The one-paragraph flow

Closed true-UTC bars enter per symbol per closed-M15 window; ten origin families plus three
current frameworks propose candidates with family geometry (stop from structure, target 1.5R at
birth); each candidate is priced by the broker pretrade cost authority (spread_r = spread/|entry−stop|
+ flat 0.02 slippage + swap + commission), given beliefs (probability/EV/confidence/fill
probabilities), routed to a policy that rewrites its target to a 2.0R-capped giveback contract,
admitted or refused by Selector V4, materialized into the scheduler's option set, scored and
allocated (best-trade, one new position per window), re-ranked and risk-gated by the finalizer
(arm factors S/R bind here: S0 = neutral-hash order among hard-eligible, R0 = fixed 0.10%/$100
unit), materialized as a limit order that lives at most 120 minutes, filled/expired by
bid/ask-correct path truth, exited by the policy replay overlay (stop −1 / target +2 / 0.4R
giveback after +1R MFE / mark-to-market at horizon), and every non-selected candidate is walked
counterfactually through the identical path machinery into the missed-opportunity pool with a
named refusal stage. Evidence: every stage stamps its decision and reason onto ledgers; the pool
is the scoreable subset (counterfactually filled + terminally markable within 2 h).

## Link table

### L0 — Launch, config resolution, arm binding
- SUPPOSED: `train_engine/runner.py:252` resolves window + purpose (March blackout fails closed,
  guard.py); merges cuts (may not move outcomes) + repairs (exist to move exactly one number);
  attempt5 builds the sealed runtime config; arm factors bind S/R at `v4t:36172`.
- DOES: CJ/CP arms ran cuts ledger_scalar_projection+missed_pool_projection (+4 memo/gc cuts) and
  repairs commission_broker_true_gated+swap_horizon_true [P1, arm receipts]. Cuts proven
  outcome-inert on their A/B; repairs re-priced cost (commission mean 0.0652 R/row Jan).
- VERDICT: **FLAWLESS** [WALK, receipts/forensic/walk/WALK_2D_ANNEX.md]: purpose/window/
  blackout/contract sha/plan digest all stamped and receipt-verified; cuts+repairs
  enumerated with per-cut stats; commission repair live on 8,452/8,452 rows. One
  operating rule captured: evidence arms must pass `--keep-outputs` (the runner
  auto-removes routes otherwise).
- EDGE: none enters here; a mis-bound flag leaks everything downstream (see L6 S0 caveat).

### L1 — Source snapshot, session guards, market state
- SUPPOSED: closed bars only, per-symbol session windows (`bog:75-134`), whole-day breadth guard
  (min 8 symbols), market-state compute; lane arms replay prepared day packs bit-compatible with
  live generation (`v4t:90513-90524`).
- DOES: refusal census on DECISION ledger rows [P1]; day-pack path exercised on both arms; the
  re-clock (CJ) proved sealed labels were UTC+2h and moved the family +3.435 R — the CLOCK was a
  defect and is now measured true-UTC end to end (`clock_rule: new_york_plus_7`).
- VERDICT: **FLAWLESS** [WALK]: both branches verified — 2026-01-01 holiday stand-down is
  clean end to end (0 candidates, 0 windows, session refusal stamped; day-1 source hashes
  null); 2026-01-02 assembles 96 windows with the full census. Re-clock confirmed on-path
  (`clock_rule: new_york_plus_7` in the arm's lane authority).
- EDGE: mislabeled sessions previously mis-bucketed 50.04% of `sub_mid_dn_revert` bars (B-family
  precedent); on THIS path the re-clock is landed — leak closed, walk confirmed.

### L2 — Candidate generation (the geometry is BORN here)
- SUPPOSED: family rule proposes entry/stop from structure; target = entry ± 1.5R×|entry−stop|
  (`bog:2254-2257`, config min_rr 1.5); candidate_id = sha(family|symbol|side|bar|geometry).
- DOES [P1, **corrected by B5/C3 — REFUTED as originally read**]: 10 families reach the
  pools. The "spread_r explosion" headline (mean 0.564 Jan; SPX500 2.353 R, NAS100 2.216 R;
  73.9%/82.2% untradeable) is DOMINATED BY A SPREAD-INPUT DEFECT, not geometry: 17/24
  symbols carry a per-row CONSTANT config spread (`broker_profile_symbol_spec_spread`
  fallback, `v4t:58806-58816`; SPX500 constant = 16.7× tick truth, NAS100 = 28.6×), 3 more
  are floor constants; only 4 symbols have real tick spreads. Truthed numerators alone:
  pool mean spread_r 0.564 → ~0.157; untradeable → ~61%/60%. A REAL geometry core remains
  at truthed spreads: ~41.6%/31.8% of the pool still spread-killed (SPX500 ~52%, NAS100
  ~26-28% residual) — structure-tight stops genuinely bind there.
- VERDICT: **DEFECTIVE-INPUTS FIRST (→ R-COST-TRUTH part a), DEFECTIVE-GEOMETRY SECOND on
  the truthed residual (→ R-GEOMETRY, re-sized after truthing; FB's grid stays the
  prior)**. [B5_ADVERSARIAL_VERDICTS.md §C3.]
- EDGE: the pool's separable opportunity (oracle +1.164 R/dp over 92.5% of dps [P1]) enters
  here; the KILL of it is jointly owned by the constant inputs (larger share) and true
  geometry (residual share) — the split is measurable only after R-COST-TRUTH lands.

### L3a — Broker pretrade cost authority
- SUPPOSED: price the trade honestly (spread from last real tick ≤60min, else measured floor,
  else config; + slippage + swap + commission), refuse when spread_r>0.10 or total>0.15
  (`bnce:585-930`, caps `config/agent_config.yaml:715-716`).
- DOES [P1]: placeholder inputs — BTCUSD spread 0.0001 (2,118 rows both windows), UKOIL 0.02580 /
  USOIL 0.02700 constants, slippage flat 0.02 on every row, Feb `cost_missing` class = constant
  0.12 default on 5,876 rows (UKOIL/USOIL/GER40); legacy-proxy under-charge vs broker-calibrated
  +0.431/+0.280 R/row mean (max +18.6). Commission was 0.0 by status-string satisfaction (F38) —
  repaired on these arms by `commission_broker_true_gated`. Swap was 8h-charged vs 120-min ceiling
  — repaired by `swap_horizon_true`.
- VERDICT: DEFECTIVE-INPUTS (placeholder spread/slippage models — **B5/C3: the placeholder
  class is 20 of 24 symbols, ~7× wider than filed**) → **R-COST-TRUTH** (SPREAD_MODEL_V1
  hour-aware truthing of the 17 config constants + 3 floors; cross-window cost-ruler
  harmonization [B5/C4-A: Feb cost_r deviates from component sum on 73.5% of rows, flat
  0.12 trio evicts symbols]; slippage flat 0.02 disclosed; era label "Jun–Jul 2026 anchors
  on Jan/Feb 2026", within-era).
- EDGE: the winner-kill half of C2 stands re-attributed (cost-attributed kills: Feb 74.1%,
  Jan 78.1% at consistent rules; still the majority under every pairing). **The
  right-on-average half is RETIRED as calibration evidence [B5/C2-B]: 77.3% of the refused
  set's −22,923 R is the gate's own cost estimate fed back as outcome — refused vs kept
  price-normalized market outcomes are near-identical (−0.0238% vs −0.0182%), so the same
  table prints under an arbitrarily wrong cost model.** Caps re-derive from external truth
  only (L3e/R-CAPS).

### L3b — Beliefs: probability / EV / confidence / fill probabilities
- SUPPOSED: candidate beliefs feed selector thresholds and scheduler score.
- MECHANISM PINNED [B4, receipts/forensic/PHASE1_OPEN_QUESTIONS.md]: the "[0.58, 0.97]
  clamp" is REFUTED — no such clamp exists; the envelope is EMERGENT from shrinkage-to-0.50
  calibration over a jury where 4 of 5 sources support the candidate's side by construction
  (`probability_debate_v4.py:754-758`). The hash term is live (family name alone moves p by
  0.00446, EV by 0.0114 R, measured through the real path). The EV floor is structural
  because the debate's cost term is ZERO in replay: the replay context omits top-level
  `cost_r` (`v4t:58197-58213`) — **the LIVE runtime builder already passes it**
  (`probability_debate_v4.py:934`, `:1094-1096`), so replay and live run DIFFERENT belief
  systems and the R-BELIEF cost wire is a ONE-KEY parity fix, not an invention. The 0.92 is
  `execution_fill_probability` from `poi_execution_lifecycle.py:176-178` (0.92·0.70+
  0.92·0.30, one constant for every symbol/session); the ledger's `fill_probability` is a
  different heuristic with 19.2 % of rows pinned at its own 0.95 ceiling; 3 of the 4
  executed walk trades ride exactly 0.92. Also: `expectancy_r` ≡ `candidate_ev_r`
  byte-equal 8,448/8,448 (R-SCHEMA dedup).
- DOES [P1]: structural fiction — probability includes 0.04×sha256(family) (`v4t:53682`);
  Brier skill −1.147/−0.965 (worse than base rate); stamped p̄ 0.766 vs realized 0.172; EV priced
  at 1.5R reward then contract rewritten to 2.0R-giveback AFTER attachment (`v4t:67426-67450` vs
  `:67680-67712`); both engine cost hooks read `context["cost_r"]` that replay never sets →
  thesis EV gross-of-cost; layer cannot express a loser (min EV +0.398/+0.387);
  `candidate_confidence` ≡ 0.55 default on 100% of rows yet feeds scheduler score ×0.20;
  `execution_fill_probability` 0.92 flat for 70.3% of rows; cost belief "calibrated" by tautology
  (expected_cost_r == cost_r byte-exact).
- VERDICT: DEFECTIVE-MISCALIBRATION (fiction) → **R-BELIEF** (honesty bundle: remove hash term +
  0.55 constant + EV floor; price EV at the walked contract). **[B5/C6-B re-scope: the replay
  funnel already charges cost once downstream (`expected_net_r = ev − cost_r` at v4t:67450;
  router floors :16883-16886; allocator anti-double-charge) — wiring `cost_r` into the debate
  context ALONE double-charges. R-BELIEF = a single-charge-point decision (live-style inside
  the debate XOR replay-style at consumers) + simultaneous downstream neutralizations +
  `candidate_direction` in the same parity bundle.]** **BELIEF-RECAL
  is ANSWERED [B3, receipts/forensic/BELIEF_RECAL.md]: NO subpopulation clears its own breakeven
  under honest beliefs.** Declared 160-cell screen (10 families × 4 cost bands × 4 sessions;
  108 cells n≥30): 4/108 nominally positive, BH α=0.10 marks ZERO (best p 0.0084 vs 0.000926
  rank-1 bar); the 4 transfer to February at **−19.13 R** (sign agreement 1/4, and the one
  agreeing cell is placeholder-dependent). Honest beliefs make this family STAND DOWN — the
  expected T2 direction for R-BELIEF is fewer trades, not more R.
- EDGE: corr(candidate_ev, realized gross) 0.0737 in-window → 0.0067 out-of-window [P1]: the
  belief layer carries ~zero transferable signal — the edge that exists is invisible to it.
  Cross-month cell-mean Spearman +0.823 is the COST GRADIENT transferring (within-band ρ 0.224,
  p 0.37): what transfers is how negative, not what's positive [B3]. Re-weighting this pool
  cannot build a positive sub-book; edge must enter at mechanism × geometry (L2/L8).

### L3c — Lifecycle + policy router
- SUPPOSED: same-symbol lifecycle dedup/replace; dynamic policy per candidate.
- DOES [P1]: `momentum_exhaustion` selected on 100% of rows — the router is a constant on these
  arms. [WALK confirms: 8,448/8,448 on BOTH `dynamic_geometry_policy` and
  `selected_policy_for_expected_net_r`.]
- VERDICT: **DEFECTIVE-DEAD-CONFIG** — one exit contract for ten origin families; the
  "router" routes nothing. Repair side: family-fit contracts belong to **R-GEOMETRY**;
  whether the router mechanism itself is revived or retired is a design decision recorded
  there.
- EDGE: a dead router means one exit contract for every family — see L8, where the walk
  measured the shared giveback contract cutting BOTH ways (+0.65 / −0.315 R vs wall marks
  on the same day).

### L3d — Geometry rewrite (1.5R → 2.0R-capped giveback)
- SUPPOSED: policy contract overwrites candidate target (`v4t:67680-67712`).
- DOES [P1]: raw_target_r = 2.0 on 26,427/27,658 rows; EV stamped at 1.5R is stale for the
  walked contract (L3b).
- VERDICT: DEFECTIVE-ORDERING (belief attached before contract known) → folded into **R-BELIEF**.
- EDGE: none directly; corrupts belief truthfulness.

### L3e — Selector V4 admission
- SUPPOSED: thresholds (min_trade_ev 0.10 net, cost ceiling 0.20, confluence 0.15); ladder to
  trade/reduce/queue/reject (`selector_v4.py:3543-4941`).
- DOES [P1]: Jan census — reject 23,018 / open-reduced 3,743 / reduce 745 / trade 21. Top reason
  `broker_net_pretrade_cost_packet_refused` 13,907. 3,536 selector-reject rows re-enter softened
  (`open-reduced-risk`) — non-monotone [reconcile lane, A2].
- VERDICT: PENDING [A2 reconcile + T1: are the thresholds earning their keep at honest costs?]
  → **R-SCHEMA** (softened-reject semantics: fix or document) + **R-CAPS** overlap.
- EDGE: gates refused negative-mean sets on average [P1] — but "correct on average" is not
  harmless: the winner-kill concentration lives at L3a/L3e caps jointly.

### L4 — Scheduler materialization filter
- SUPPOSED: skip non-risk-bearing candidates before ranking; stamp skip reason.
- DOES [P1]: Jan 23,563 skipped / 4,095 materialized. Reasons enumerated (cost block first).
  [WALK 2-day census: cost_authority 7,029/8,448 = 83.2 % of all refusals; the day's
  single largest opportunity (+2.169 R AUDUSD SHORT, EV +0.765) died at the cost gate.]
- VERDICT: **FLAWLESS-AS-PROPAGATOR** [WALK] — the stage faithfully stamps and propagates
  upstream refusals; its own skip logic added nothing anomalous on the walked days.
- EDGE: skip-before-rank means a cost-refused winner never reaches ranking — the leak is
  upstream (L3a); this link faithfully propagates it.

### L5 — Scheduler allocation (best-trade)
- SUPPOSED: score = ev×0.55 + (p−0.5)×1.2 + confidence×0.2 + … + transfer×6.0 − cost×0.8;
  one new position per window; caps (portfolio 4%, cluster 1.5%).
- DOES [P1]: transfer term dominates; learned ranking exists, default OFF; score consumes the
  L3b fictions (dead 0.55 constant × 0.20; 0.92 flat fill prob × 0.10 + inside transfer).
- VERDICT: MISCALIBRATED-INPUTS (garbage in) — repaired via R-BELIEF; ranking itself
  settled by B5/C5: **two published evidence legs are RETIRED** (the −0.076/−0.006
  Spearman is the S0 neutral draw's DESIGNED null; the 67th percentile is
  gate-conditioning — vs eligible peers the chosen sits at the ~50th, median exactly
  0.50). The claim "selection is not the defect" now rests on the degenerate hard pools
  (walk, row-confirmed) + the NEW eligible-set leg: within eligible sets expected-gross ↔
  realized-gross ≈ −0.018/−0.012 — no in-band score orders outcomes among eligibles once
  the shared cost term is removed.
- EDGE: edge neither enters nor leaks here materially — conclusion unchanged, evidence
  upgraded [B5_ADVERSARIAL_VERDICTS.md §5].

### L6 — Risk finalizer + arm factors
- SUPPOSED: transfer-score re-rank, risk headroom, hard caps; S0 neutral-hash order among
  hard-eligible; R0 fixed unit.
- DOES [P1]: Jan probe census (cost authority re-block 20,448; package authority 4,097; …);
  S0 caveat measured — neutrality replaces only the finalizer's ordering; scheduler quality
  still shaped preservation upstream; hard eligibility embeds the adaptive memory guard
  (prior-outcome-coupled, `v4t:34895-34926`) → path dependence; per-repair deltas do NOT sum.
  **[WALK measured the pool itself: 92/96 windows have a hard-eligible pool of ZERO; 3
  singletons + 1 pair; the one contested window was a same-symbol-same-side XAUUSD pair, so
  selection had zero economic degrees of freedom on the whole day. Memory-guard coupling is
  declared in-band on every option row (`hard_eligibility_uses_prior_closed_trade_outcome_
  fields: true`, neutral rank outcome-free) — the separation is honest.]**
- VERDICT: **SELECTION-DEGENERATE (measured; not a defect of the selector)** — the funnel
  upstream (L2 geometry × L3a cost) decides the book; by the finalizer there is nothing
  left to choose between. Seed arms [B2, running] bound how much the neutral seed can move
  composition; the S-axis itself is economically inert at current geometry/costs.
- EDGE: none direct; the leak is upstream. Repairing L2/L3a is what would repopulate this
  stage — re-measure the pool sizes on the repaired arms (T2).

### L7 — Order materialization + fill simulation (the 120-minute wall)
- SUPPOSED: resting limit (marketable → immediate fill), queue realism for passive fills,
  guarded market fallback; expiry = min(asof+120min, day+1d) (`v4t:85864-85866`).
- DOES [P1]: fill price always the limit price; first-touch terminal; 120-min ceiling clamps
  every horizon (21/58 Feb trades end mark-to-market, netting −1.28 R); fill truth prefers
  ordered ticks, falls back M1 (P1 fill-authority split for breaker rows: 492 FULL_TICK /
  10,810 M1_ONLY / 3 gap — frozen prereg, execution scheduled-on-need).
- VERDICT: **MEASUREMENT-CEILING, SYMMETRIC** [B5/C7]: wall-affected population is 25/58
  Feb (m1-proxy time-stop rows included), and the −1.28 R MTM figure is 84 % sunk execution
  cost on a gross-flat cohort (gross marks −0.20 R; 8/21 positive) — it survives any
  horizon and is NOT evidence of suppressed +R. T1 horizon counterfactuals = hypothesis
  measurement under a symmetric prior; hold the already-charged costs fixed. MFE-oracle
  upward bias still binds — never use raw MFE bounds.
- EDGE: the 120-min bound censors BOTH tails — longer-horizon edge is invisible, and so are
  longer-horizon losses. March MDE language must say "censoring", never "suppressed edge".

### L8 — Exit (policy replay overlay)
- SUPPOSED: momentum_exhaustion: stop −1, target +2.0, giveback 0.4R after +1R MFE,
  mark-to-market at horizon end.
- DOES [P1]: exit geometry is the largest executed loss class BOTH months; stop-first-touch
  carries essentially all losses (Jan 26:8 stop:target first-touch; Feb stop-first −17.85 R);
  target-first trades 100% positive both months; `stop_hit`/`horizon_marked` clean-classes
  EMPTY. FC's 0/40 overlay cells died OOS [A2 verified] — the AXIS is alive (the loss class
  is real), the overlay FAMILY is dead. **[B5/C1: the implemented partition is "mfe≥0.25 AND
  mfe−cost>0" (precedence understates exit dominance by ~0.25/0.63 R); ordering stable at
  floors ≤0.30, inverts ≥0.35/0.40; AND the loser-MFE survival curve matches the
  driftless-barrier prediction at the floor (0.656/0.697 vs 0.700) and is THINNER deeper —
  much of the "recoverable" mass is barrier arithmetic on a near-zero-gross-edge book, and
  TP-at-the-floor recovers little.]**
- VERDICT: DEFECTIVE-GEOMETRY (exit side) → **R-GEOMETRY** — with the B5 bound: the yield
  case rests on FB-grid-class CONTRACT changes (entry/stop/target families), NOT exit
  tweaks to the current book (walk measured the giveback ±: +0.65/−0.315 on one day).
- EDGE: [P1] Jan executed gross −1.221 vs cost 4.285; Feb gross +0.204 vs cost 4.165 — at
  executed level the book's loss IS the cost bill; at pool level exit-vs-direction split
  pending the A2 loss-class reconciliation (register row A).

### L9 — Missed-opportunity expansion + scoreability
- SUPPOSED: every non-selected candidate walked counterfactually through identical machinery;
  named refusal stage; scoreable = filled + markable within 2h.
- DOES [P1]: 153,425→27,658 / 129,165→24,239 reduction entirely from
  `headline_execution_bound_eligible` hardcoded False (`v4t:27781`); final_blocker taxonomy
  complete; join hazard (candidate_id not unique — 4-tuple key) [P1, register P].
- VERDICT: PENDING [R-SCHEMA covers the join key + Feb emitter drift
  (`pretrade_cost_packet_status` on zero Feb rows)].
- EDGE: this link is the MEASUREMENT substrate — its defects (schema drift, join traps) leak
  false conclusions, not R.

### L10 — Day close, ledgers, pools
- SUPPOSED: ledger roles; lane trade-table identity tuple (14 fields); compact pools = declared
  projections.
- DOES [P1]: repair-status columns null in pools while repairs demonstrably ran (projection
  reads row, stamps live on packet) — measurement blind spot; Feb pool 101 keys vs Jan 78
  (superset, CK repair columns).
- VERDICT: DEFECTIVE-OBSERVABILITY → **R-SCHEMA** (projection completeness for repair stamps).
- EDGE: none; measurement integrity only.

---

## The flow-level verdict (to be finalized at Phase E)

[PENDING — after T1/T2: the composed answer to "where does the edge enter and where does it
leak", quantified per link, with the repaired flow's measured deltas beside the baseline.]

## Walk annex

**DONE — `receipts/forensic/walk/WALK_2D_ANNEX.md`** (+ machine `WALK_2D_ANNEX.json`,
`WALK_2D_CANDIDATES.jsonl.gz`; route `FA2_WALK_S0R0_2D` kept in the integration worktree).
Headlines: day-1 holiday stand-down clean; day-2 funnel 8,448 → 5 hard-eligible → 4 trades
(cost gate owns 83.2 % of refusals); **selection degenerate** (92/96 windows empty pool;
the one contest a same-symbol pair — zero economic degrees of freedom); the four trades
walked end to end with market context in-band (giveback contract measured ±: +0.65 / −0.315
vs wall marks); the exit-vocabulary duality explained (two layers, two truths, one naming
defect → R-SCHEMA); the day's biggest winner (+2.169 R) killed by the cost gate; WALK-F1
instrumentation miswire filed (condition features reach TRADE/ORDER, never MISSED — Phase C
telemetry fix).
