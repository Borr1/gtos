# MARCH_PREREG_V1 — the frozen March 2026 one-shot confirm (Phase E)

Session FA continuation. Written 2026-08-05, BEFORE any March byte, from January-only
evidence. **Borhen alone triggers execution (OD-FA2-1); his explicit word is the only
valid trigger — no notification, summary, or agent statement substitutes.** Until
triggered, nothing below authorizes reading a March byte.

## 0. What March is asked to decide

January (development-fitted, every repair derived on it) established a MECHANISM story:

1. The frozen cost layer overcharged spread 8.5× and that overcharge was the de facto
   admission throttle (arm (i): removing it → 57→138 trades, book −5.51→−31.46).
2. The honest belief stack stands down almost entirely (arm (ii): 6 trades, +0.58 —
   inside the 0.751 seed band; no honest sub-book).
3. The declared 0.05 ceiling composes to near-silence (arm (iii): 1 trade).
4. The wrapper machinery is outcome-inert (arm (iv): byte-exact r0).
5. The billed V27 candidate is INEXPRESSIBLE through the R-denominated cost gate
   (arm (v): 12,668/12,668 transformed candidates cost-refused at 3.7× cost_r; zero
   trades bought).

March — the estate's only virgin month — is asked whether this MECHANISM story holds
out-of-window. It is NOT asked to certify economic magnitudes: see §6 (power).

## 1. Substrate freeze (all pinned at fa2-integration `c25e2510d`)

| artifact | sha256 |
|---|---|
| `src/research_infra/train_engine/repairs.py` | `cf8cd236adc94c5fa4618063b0563b0aa72ef13c04bcccfd1d9c1b41374cf2b8` |
| `src/research_infra/train_engine/cuts.py` | `8164e9061c477fc50c8db0fdc02b15388061eade7642a65f4a8f53731aed13c7` |
| `src/research_infra/train_engine/decision_semantics.py` | `be7843919237fc08a514a5cccfd855c755325a48f7c27ee652af302d3c7243bd` |
| `src/components/current_breaker_re_entry_repair.py` | `465ae93d54ee532021f16963e0cc956f5fee26e5c79276d09a636c634cc7192b` |
| `research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json` | `7194e1c56bbf11de24f86522fc308cdd63531946eed427f4caf55b225f2e2e82` |
| `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json` | `bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd` |
| `LANE_INPUT_REGISTRY.json` (pre-March, 4 windows) | `6415ae522dc48cd85f33a5f35223ce375c07214ad4416df60502d2ec0f10b5de` |

Registry state: REPAIR_PAIRS has 11 pairs (incl. `candidate_breaker_transform` /
`candidate_breaker_inert_control`); INCOMPATIBLE_REPAIRS has 11 rows (incl.
ruler×ceiling and breaker live×control); the `controls` bundle resolves 10 ids. Any
March run whose worktree does not reproduce these SHAs at these paths is
NOT_EVALUABLE before it starts.

## 2. Prerequisite: March lane materialization (outcome-blind)

**`march_2026` does not exist in the lane registry** — no March lane pack has ever
been built. Before the decode event:

1. Materialize March true-UTC lane packs by the CJ pattern (same tooling lineage as
   `LANE_INPUTS_TRUE_UTC_V1`), from the same source-truth class as the four existing
   windows.
2. **Outcome-blindness protocol**: CR-class loaders only (each line's date extracted
   and authorized BEFORE `json.loads`); the S0-style metadata-only preflight is the
   ONLY pre-decode inspection (file counts, byte sizes, digests, calendar coverage —
   no candidate rows, no outcome fields, no economics); materialization receipts carry
   counts and digests only. No summary statistic of any March outcome is computed,
   printed, or logged at materialization.
3. The post-March registry must carry the four existing windows' digests UNCHANGED
   (January's canonical source plan digest
   `b44b433039bf7f5372fc067f62477cdb5c8b0d2caf4202755a922a7c198be954` among them) plus
   the new `march_2026` entry. The March window's own source-plan digest is recorded
   in the decode receipt.
4. Materialization failure or partial coverage → the whole confirm is NOT_EVALUABLE.
   **No partial-window decode, ever.**

## 3. The decode event — one event, six arms, declared order

All six arms run strictly serially in ONE session, `--window march_2026`, full window,
`--purpose LANE_ITERATION --keep-outputs`, 2-day March smokes are NOT run (the configs
are January-smoked; a March pre-run would be a peek). **No analysis of any arm's
output until all six receipts exist.** Order:

| # | prefix | patches | repairs |
|---|---|---|---|
| 0 | `FA2_M_R0` | 6 cuts | `commission_broker_true_gated,swap_horizon_true` |
| 1 | `FA2_M_ARM_I` | 6 cuts | `spread_input_truth,commission_broker_true_gated,swap_horizon_true,cost_ruler_harmonize` |
| 2 | `FA2_M_ARM_II` | 6 cuts + 3 schema | arm-(i) list + 5 belief ids |
| 3 | `FA2_M_ARM_III` | 6 cuts + 3 schema | `spread_input_truth,commission_broker_true,swap_horizon_true,`5 belief ids`,cost_ceiling_0p05` |
| 4 | `FA2_M_ARM_IV` | 6 cuts | `commission_broker_true_gated,swap_horizon_true,` 8 inert controls |
| 5 | `FA2_M_ARM_V` | 6 cuts + 3 schema | arm-(iii) list + `candidate_breaker_transform` |

(6 cuts = `authority_hash_content_memo,abc_concrete_types,gc_during_chunk,
skip_post_hoc_ledger_recertification,ledger_scalar_projection,missed_pool_projection`;
3 schema = `decision_semantics_projection,condition_feature_propagation,
hard_eligibility_observability`; 5 belief ids = `belief_cost_single_charge,
belief_hash_term_removal,belief_confidence_constant_retire,belief_ev_walked_contract,
belief_fill_probability_deweight`. Exactly the January T2 compositions —
`CELL_DECLARATION_V1` + amendments `424500467`, `008aec561` carried verbatim.)

T3 (swap isolation) is NOT re-run in March: it is an attribution instrument, not a
confirmable mechanism; its January answer transfers as attribution.

## 4. PRIMARY endpoints — five mechanism confirms (near-deterministic, thresholds frozen)

| # | claim | March confirm threshold | Jan value |
|---|---|---|---|
| P1 | cost truth widens the funnel | trades(I) ≥ 1.5 × trades(R0) | 2.42× |
| P2 | belief honesty stands down | trades(II) ≤ 0.25 × trades(R0) | 0.105× |
| P3 | ceiling composes to near-silence | trades(III) ≤ max(3, 0.10 × trades(R0)) | 1 |
| P4 | machinery is inert | trade set (IV) == (R0) exactly, per-trade net_r ≤ 1e-9 | exact |
| P5 | the edge is inexpressible | transformed admissions in (V) == 0 AND breaker cost-refusal in (V) ≥ 99 % | 0; 100 % |

Each is pass/fail against its frozen threshold; report all five, no substitutions. A
P-endpoint failure is a REFUTATION of that January mechanism claim out-of-window and
is reported as such (it is information, not embarrassment — P5 failing, for example,
re-opens the trade-TP provenance question and the candidate door).

**Census confirms (secondary, bands frozen):** S1 frozen/truthed spread ratio in
[4, 16] (Jan 8.5×); S2 transformed/untransformed median breaker `cost_r` ratio in
[2, 8] (Jan 3.7×).

## 5. Economics — ESTIMATION ONLY, no confirmatory sign test

Paired daily net-R deltas (arm − R0-March, union days, None-aware for unscoreable
rows), monthly totals, per-arm trade joins with contest-site separation (B2 rule 3).
Report point estimates with a daily-bootstrap 90 % interval. **The 0.751 R seed band
(B2, n=3 replicates) is a floor: any |monthly Δ| ≤ 0.75 R is NOT_EVALUABLE as an
economic direction.**

## 6. Power, stated before anyone asks

At January's paired daily-delta dispersions (sd 1.73–2.24 R/day, n≈21 trading days),
a one-sided α=0.05, power-0.8 paired test has a **monthly MDE of ≈ 20–26 R** — larger
than every January delta except arm (i)'s. January's own R0 book (−5.51, monthly sd
≈ 7.6) is itself indistinguishable from zero at month scale. **A single virgin month
cannot certify economic magnitudes of this size; anyone quoting a March monthly delta
as a powered test is over-reading it.** This is why §4's mechanism confirms are the
primary endpoints. C7 censoring language applies to every economic number: all walked
outcomes are 120-minute-wall MTM-censored, symmetrically across arms — deltas measure
the censored contract, not open-horizon economics.

## 7. NOT_EVALUABLE terminals (frozen)

- materialization failure / partial coverage → whole confirm NOT_EVALUABLE (§2.4)
- substrate SHA mismatch → NOT_EVALUABLE before start (§1)
- any arm error ≠ None → that arm NOT_EVALUABLE; the event report names it; no re-run
  inside the same decode event without a new owner word
- zero-trade cells → economics NOT_EVALUABLE for that cell (mechanism confirms still
  score)
- P5's TP-provenance sub-question → NOT_EVALUABLE while transformed admissions = 0

## 8. The CR March-decode asterisk — adjudicated

**Event (CR's own disclosure, verbatim substance):** during early source inventory,
Session CR ran a whole-container `json.load` probe on the AA estate to inspect
top-level metadata; the decoder necessarily traversed the container — including any
March 2026 outcome rows present — before a date boundary was applied. CR did not
print, inspect, aggregate, compare, or use any March economic value; the committed CR
loader now authorizes each line's date before `json.loads`, with a behavioral test
proving February and March payloads never reach the decoder.

**Adjudication:** the prereg's validity threat is OUTCOME-INFORMED SELECTION — a
hypothesis, cell, threshold, or composition shaped by March values. Three facts close
it: (1) no March-derived value exists in any committed artifact (disclosure +
committed-loader behavioral test); (2) the probed container is AA's historical walk
estate — a different artifact lineage from the March lane packs this confirm decodes,
which do not yet exist; (3) every declared cell, arm composition, and threshold above
derives from January T1/T2 alone, with commit-anchored provenance predating any March
materialization. **Ruling: March is VIRGIN FOR SELECTION PURPOSES.** The word
"untouched" is retired; the correct claim is "no March value has influenced any
declared decision," and the single disclosed mechanical decode is part of the record.
Guard: §2.2's CR-class loaders are mandatory for every March-adjacent tool.

## 9. Reporting

One report (`MARCH_CONFIRM_RESULT.md` + machine JSONs beside it): the five P
verdicts, the two S bands, the estimation tables, every receipt digest, and an
explicit "what changed vs January" section. Every number labeled with its evidence
class. The report goes to Borhen; **kill / park / iterate on the family is his
decision alone.**
