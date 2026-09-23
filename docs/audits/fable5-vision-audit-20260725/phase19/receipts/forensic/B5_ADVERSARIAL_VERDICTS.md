# B5 — Adversarial verify pass: verdicts (14 refuters, 7 claims × 2 lenses)

Session FA continuation, Phase B item 5. Register: `B5_CLAIM_REGISTER.md` (declared before
the pass). Machine verdicts: `b5_verdicts.json` beside this file (full attack/evidence text
per refuter). Every refuter reproduced its claim's headline numbers from raw artifacts
before attacking; every REFUTED names the exact artifact line that breaks.

**Scoreboard: 1 claim REFUTED (both lenses), 5 QUALIFIED, 1 clean (NOT_REFUTED + a
scope qualification). The pass pays for itself twice over: it found a first-class cost
defect ~7× wider than Phase 1 filed, and it deleted two evidence legs the estate has been
quoting.**

| claim | lens A | lens B | outcome |
|---|---|---|---|
| C1 exit-geometry dominance | QUALIFIED | QUALIFIED | stands, with a precedence correction + a mechanical-origin qualification |
| C2 cost gate right-on-average AND winner-killing | QUALIFIED | QUALIFIED | winner-kill half stands (re-attributed); **right-on-average half is an accounting identity, not calibration evidence** |
| C3 geometry → cost-kill causal arrow | **REFUTED** | **REFUTED** | the flagship exhibits are a spread-INPUT defect; a real geometry core remains, smaller |
| C4 no honest-belief sub-book | QUALIFIED | QUALIFIED | **survives and is strengthened**; cross-window cost-ruler harmonization required |
| C5 selection is not the defect | QUALIFIED | QUALIFIED | conclusion stands; two published evidence legs retired, one better leg found |
| C6 replay/live belief divergence | NOT_REFUTED | QUALIFIED | fact stands; **the one-key repair scope was wrong — naive wiring double-charges** |
| C7 the 120-min measurement ceiling | NOT_REFUTED | QUALIFIED | stands as SYMMETRIC censoring; population corrected 21→25; not evidence of suppressed +R |

## C3 — REFUTED, and it reorders Phase C

Both refuters independently discovered the same construction break: **17 of 24 symbols
carry a per-row CONSTANT spread price in both monthly pools** — SPX500 = 10.0 price units
on all 1,943 rows, NAS100 = 50.0 on all 1,622, JP225 50.0, UK100/GER40 5.0, US30 8.0,
ETHUSD 10.0, EURJPY/CHFJPY 0.05, … — the replay quote-synthesis fallback
`broker_profile_symbol_spec_spread` (`v4t:58806-58816`): a static config value used
whenever the sealed replay has no tick source for the symbol. Three more are floor-table
constants (BTCUSD 0.0001, UKOIL 0.0258, USOIL 0.0270 — `admission.py:73-84`). **Only 4
symbols (18 % of rows: EURUSD, USDJPY, XAUUSD, XAGUSD) carry a real measured spread** —
exactly the 4 tick sources the lane's SOURCE_UNIVERSE registers.

Against broker truth (SPREAD_MODEL_V1 anchors; 263 M-row tick corpus): SPX500's constant
is **16.7×** the measured 0.6 anchor (and 10× the worst tick ever captured); NAS100
**28.6×** the measured 1.75. Consequences, measured by both refuters independently:

- Numerator-truthing ALONE (stops untouched, pool's own caps): Jan untradeable
  73.9 % → ~61 %, Feb 82.2 % → ~60 % at mean-truth; SPX500 48–54 % of its kills un-killed,
  NAS100 ~74 %; repaired Jan pool mean spread_r **0.157 vs the claimed 0.564 (3.6×
  inflated)**.
- Geometry ALONE cannot un-kill the flagship rows: at constant spread 10.0, 3× wider stops
  leave SPX500 99.5 % killed (5×: 82 %) — clearing the cap would need a ~1.45 %-of-price
  stop no M15 structure produces. The claimed lever is impotent against the inflated
  constant.
- A genuine geometry-killed core REMAINS at truthed spreads (~41.6 % Jan / 31.8 % Feb of
  the pool still spread-killed at broker-true p50; SPX500 ~52 %, NAS100 ~26-28 % residual).
  **R-GEOMETRY stays licensed but loses exclusivity and must be re-sized on the truthed
  residual, not the 74/82 % headline.**

Breaks named: `calibration/CALIBRATION.md:113-119` ("the MEASURED means are brutal…" —
they are config constants, not measurements, on 20 of 24 symbols) and
`COST_BELIEF.json:121`.

## The Phase C consequences, in force

1. **R-COST-TRUTH is promoted to first and load-bearing**, with three parts: (a) replace
   the 17 config-constant + 3 floor spread numerators with SPREAD_MODEL_V1 hour-aware
   truth (era-labeled; the Jun–Jul 2026 anchor applied to Jan/Feb 2026 is within-era);
   (b) **harmonize the cost ruler across windows** [C4-A]: February's `cost_r` deviates
   from its component sum on 73.5 % of rows and carries flat 0.12 overrides on
   GER40/UKOIL/USOIL that mechanically evict those symbols from Feb cells — no
   cross-month cell comparison is trusted until harmonized; (c) slippage stays flat 0.02
   disclosed unless measured.
2. **R-CAPS loses a stated premise** [C2-B]: "the gate was right on average" is an
   accounting identity here — 77.3 % of the refused-set −22,923 R is the gate's own cost
   estimate fed back as outcome; refused vs kept price-normalized market outcomes are
   near-identical (−0.0238 % vs −0.0182 %). An arbitrarily wrong cost model prints the
   same table. Cap re-derivation must be grounded ONLY in externally validated cost
   inputs (tick truth / spread model), and its reachable February winner pool is the
   cost-attributed 74.1 % (5,554), not 84.3 %.
3. **R-BELIEF is re-scoped** [C6-B]: the replay funnel is NOT cost-blind at the decision
   level — `expected_net_r = ev − cost_r` on 8,448/8,448 (`v4t:67450`), router floors gate
   `expected_net_r` (`:16883-16886`), and the allocator subtracts cost with
   anti-double-charge logic. Wiring `cost_r` into the debate context ALONE would
   DOUBLE-CHARGE. The repair is a cost-accounting decision (single charge point —
   live-style inside the debate XOR replay-style at the consumers) plus the simultaneous
   downstream neutralizations, with `candidate_direction` in the same parity bundle.
4. **R-GEOMETRY's exit-side yield expectation is bounded** [C1-B]: the loser-MFE survival
   curve matches the driftless-barrier prediction at the 0.25R floor (0.656/0.697 observed
   vs 0.700 predicted) and is THINNER than driftless deeper — the "recoverable" exit mass
   on the CURRENT book is shallow noise (TP-at-0.25 recovers little; half the bucket's R
   sits at MFE ∈ [0.25, 0.5)). Exit-geometry dominance is partly barrier arithmetic on a
   near-zero-gross-edge book. The yield case for R-GEOMETRY rests on FB-grid-class
   CONTRACT changes (entry/stop/target families), not exit tweaks to the current book.
   Also [C1-A]: the ratified rule as IMPLEMENTED is "mfe ≥ 0.25 AND mfe−cost > 0"
   (precedence), which understates exit dominance by ~0.25 R (Jan) / ~0.63 R (Feb); the
   dominance ordering is stable for floors ≤ 0.30 and INVERTS at ≥ 0.35/0.40 — never
   quote it at other floors without the sweep.
5. **C5's retired evidence legs** — never cite again: the −0.076/−0.006 rank↔outcome
   Spearman (the S0 neutral draw is outcome-free BY DESIGN — that null is designed, not
   discovered) and the 67th-percentile figure (gate-conditioning; against eligible peers
   the chosen sits at the ~50th percentile, median exactly 0.50). The claim now rests on
   the degenerate pools (row-confirmed) plus this pass's NEW leg: within eligible sets,
   expected-gross vs realized-gross correlation ≈ −0.018/−0.012 — no in-band score orders
   outcomes among eligible candidates once the shared cost term is removed.
6. **C7 reframed**: the 120-min wall is SYMMETRIC censoring — the −1.28 R MTM figure is
   84 % sunk execution cost on a gross-flat cohort and survives any horizon; wall-affected
   population is 25/58 (m1-proxy time-stop rows included). T1 horizon counterfactuals are
   hypothesis measurement under a symmetric prior, not recovery of a measured loss. March
   MDE language must say "censoring", not "suppressed edge".

## Standing corrections to earlier documents

- `LOSS_CLASS_RULE_RATIFICATION.md` + `RECONCILE_A_Q.json` row A: wording must name the
  precedence ("≥0.25 floor applied BEFORE recoverability"); 9 losers (Jan 3, Feb 6) with
  net-profitable counterfactual exits are filed under `direction_wrong` by the floor.
- `CALIBRATION.md:113-119` "measured means" → config constants on 20/24 symbols (the
  "Spread sanity" bullet's own three-placeholder count was 7× too small).
- Walk annex funnel reading inherits C3: "cost gate owns 83.2 % of refusals" is true of
  the gate's DECISIONS; the INPUTS behind most refusals are constants, so the 83.2 % is
  an input-defect census, not a geometry census.
- FULL_FLOW L2/L3a verdict cells updated this commit; L5's evidence legs replaced.
