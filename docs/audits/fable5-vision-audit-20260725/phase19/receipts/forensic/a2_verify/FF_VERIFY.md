# Lane FF verification — Sol composition (Session FA-continuation, Phase A2)

Verifier: Fable verification agent. Date: 2026-08-03.
Sol worktree verified: `/Users/borr/GTOSActive/worktrees/wave19-sol-composition-20260801`
(commits `96701822a` → `9c95c28b7`; result doc `SESSION_FF_SOL_COMPOSITION_REPAIR_RESULT.md`).

**Boundaries.** No March 2026 outcome data, no `packs/` for March, no live-forward (2026-07-29+)
outcomes were read. February reads are **attribution-only under `owner_mandate_20260801`** — this
verification re-reads the same February attribution surfaces Sol read, for verification only. No
source file edited; no lane arm, replay, or test suite run. All `.jsonl(.gz)` inputs streamed
line-by-line; heaviest step peaked at 60.4 MB RSS.

**Method.** Recomputed from RAW inputs (lane trade tables, pools, run ledgers), never from Sol's
receipts of the same numbers. Join key everywhere:
`(candidate_id, decision_time_utc, symbol, side/direction)` — bare `candidate_id` rejected
(hazard re-confirmed: 18/57 Jan executed trades share a bare cid with ≥2 missed-pool rows).
Pool byte-identity: the pool copies Sol read (different paths) hash decompressed to the same
sha256 as the commissioned wave16/wave18 paths (`28aab6c6…`, `d4cb507f…`).

## Verdicts

| claim | claimed | recomputed | verdict |
|---|---|---|---|
| FF1 Jan FVG | −12.264 R on 21 trades | **−12.26358303** on 21 physical / 20 scoreable (1 null `net_r`: US30_cash) | **VERIFIED** (exact) |
| FF1 Feb FVG | −5.783 R on 42 trades | **−5.78345422** on 42/42 scoreable | **VERIFIED** (exact) |
| FF2 Jan non-FVG | +6.757 | **+6.75737474** (36 trades / 35 scoreable) | **VERIFIED** (exact) |
| FF2 Feb non-FVG | +1.822 | **+1.82205553** (16 trades) | **VERIFIED** (exact) |
| FF3 no-veto licensing | "no FVG veto licensed (multiplicity)" | see below | **VERIFIED in substance; label imprecise** |
| FF4 repair default-off | implemented default-off | confirmed in code, six independent gates | **VERIFIED** |

**The commissioning caution on '42':** it resolves cleanly. 42 is the `current_fvg_fill` slice of
February's 58 executed trades; the family split is 3 breaker + 42 FVG + 12 session-open-range +
1 structural = 58 exactly, and total Feb net −3.96139869 matches. January: 9 + 21 + 20 + 7 = 57,
total −5.50620829 (matches the published re-clocked January headline −5.506).

**FF vs FA cross-check (required):** FA Phase-1's committed receipts
(`trades_jan/TRADES_JAN_ATTRIBUTION.json` `by_origin_family`,
`trades_feb/TRADES_FEB_ATTRIBUTION.json` `february.aggregations.origin_family`) agree with Sol's
`EXECUTED_FAMILY_TABLE.json` to the last published decimal on every family n / net / gross / cost,
and both agree with this recompute from raw. **No disagreement exists to flag.**

## FF3 — the licensing logic, read and checked

What FF actually did:

1. **Zero billed looks.** `LOOK_MANIFEST.json` declares all six looks (FF-L0..FF-L5)
   `billed: false`, classifications `PURE_RECOUNT` / `FORENSIC_DIAGNOSTIC`, and
   `selection_use_forbidden: true`. The word "multiplicity" appears **nowhere** in FF's
   commission, result, or outputs. So FF did not price the veto against any numeric bill —
   the protection is structural: unbilled forensic looks cannot license a selection rule, and a
   licensed FVG veto would need a preregistered billed look against the declared candidate family.
2. **Identifiability is the stated primary ground.** The FVG concentration jump sits exactly
   between scheduler materialization and S0 selection — **3.5641× (Jan) / 3.8643× (Feb),
   recomputed exact** — and that is precisely the stage whose hard-eligible / neutral-rank
   partition both scalar scorecard projections discarded. S0 is an outcome-blind neutral hash.
   FF's conclusion that an outcome-safe family gate is not identifiable from the surviving
   artifacts follows from those two facts and from the funnel row it publishes as
   "hard eligible: unobserved; bounded only".
3. **Tiny paired samples.** Same-window family pairs: Jan breaker 8, Jan structural 7,
   Feb breaker 2, Feb structural 0 — recomputed exact.

Is the arithmetic right? **Every deterministic number checked is exact** (see table below). There
is no veto-pricing arithmetic (no p-value, no family-size computation for an FVG gate) in FF to be
right or wrong — that absence is deliberate and consistent with the declared look classifications.
The one imprecision is in the *circulated summary* of FF, not in FF: "(multiplicity)" suggests a
priced bill that does not exist.

## Supplementary recomputes (all exact)

**Funnel stages** (stage total = missed-ledger predicate count + all selected probes; predicates
decoded from the raw fields): Jan pool 153,425+61=153,486; cost-exec 25,132+61=25,193;
selector-pass (= action ∈ {trade, open-reduced-risk, reduce-risk}) 13,442+61=13,503; scheduler
(`scheduler_option_materialized`) 8,581+61=8,642. FVG: 89,912+24=89,936; 9,134+24=9,158;
6,263+24=6,287; 930+24=954; selected 24/61; filled 21/57. Feb: 129,165+66=129,231;
13,696+66=13,762; 8,275+66=8,341; 4,988+66=5,054. FVG: 74,512+49=74,561; 6,074+49=6,123;
4,260+49=4,309; 922+49=971; selected 49/66; filled 42/58. Feb XAUUSD: 6,471+44=6,515;
5,391+44=5,435; 3,704+44=3,748; 1,303+44=1,347; selected 44/66; filled 40/58.
Enrichment products: (21/57)/(89,936/153,486)=**0.628752**; (42/58)/(74,561/129,231)=**1.255094**;
XAU pool-to-fill **13.679943** — all equal to Sol's published values.

**Feb XAUUSD executed economics:** XAUUSD n=40 gross **+0.950208** net **−1.594567**; other
symbols n=18 gross **−0.746289** net **−2.366832** — exact.

**Family tension** (pool comparator = full family slice of the compact pool on
`opportunity_net_proxy_r`, valid because the pool is 100 % non-selected; executed = TRADE_LEDGER
`net_r`; paired = executed minus same-`decision_time_utc` same-family peer mean):

| cell | Sol | recomputed |
|---|---|---|
| Jan breaker pool 4,263 | −1.4680 | −1.46800061 |
| Jan breaker executed 9/8 | +0.5445 | +0.54446884 |
| Jan breaker paired n=8 | +1.9200 (7/8 positive) | +1.91996888 (7/8) |
| Jan structural pool 1,993 | −1.4128 | −1.41276888 |
| Jan structural paired n=7 | +0.6636 | +0.66360620 |
| Feb breaker pool 2,375 | −1.0628 | −1.06276011 |
| Feb breaker paired n=2 | +0.9471 | +0.94707459 |
| Feb structural pool 1,806 | −1.2393 | −1.23931515 |
| Feb structural executed 1/1 | +1.1697 | +1.16971807 |

Wilson 95 % intervals recomputed exactly (e.g. Jan breaker `[0.30574239, 0.86315571]`).
Bootstrap CI endpoints (20,000 day-cluster draws, seed 20260801) are the one component taken as
reported — resampling-procedure-bound.

**Probe conversion:** unconverted Jan 4 (3 FVG + 1 breaker), Feb 8 (7 FVG + 1 breaker) — exact;
conversion splits 21/24 vs 36/37 (Jan) and 42/49 vs 16/17 (Feb) — exact; fill-probability
separation (field `predecision_limit_fillability_probability`, aliases agree): Jan filled 0.8629
vs unfilled 0.5838, Feb 0.8037 vs 0.6303 — exact. The replacing XAUUSD long FVG trade exists in
the raw Feb lane table at **+0.69513675** (Sol: +0.695137); the −0.064425 fallback counterfactual
was not independently re-walked.

## FF4 — code confirmation (Sol worktree, commit `d52e48b2d`, 2 files)

- `src/research_infra/train_engine/cuts.py:1293-1294` — patch registered `default_on=False`,
  `sealed_compatible=False`.
- `cuts.py:843` — `_HARD_ELIGIBILITY_OBSERVABILITY_ACTIVE = 0` (inert at import).
- `cuts.py:1337-1346` — `TRAIN_SAFE_SET_PATCHES` and `TRAIN_DEFAULT_PATCHES` (= safe set) exclude it.
- `cuts.py:1397-1410` — `resolve_patches` reaches it only via the explicit
  `safe+hard-eligibility-observability` alias or an explicit comma-name.
- `src/research_infra/fast_engine/accel.py:155` — when no patches are named, only
  `default_on=True` patches are selected, so the flag is honored at apply time.
- `cuts.py:1092-1096` + `:1264-1267` — the lift is double-gated (scorecard suffix AND active
  counter) and applies only to `*_SCORECARD_LEDGER.jsonl` (train lane), so the default-on scalar
  projection path stays inert without the explicit patch.
- R2 binds **neither** changed path (checked against the 43 bound paths + `verification_tooling`
  in this worktree's R2 contract JSON) — Sol's "both changed implementation paths are unbound" holds.

## New findings

1. **The compact scoreable pools contain ONLY missed rows** (all 27,658 Jan rows carry
   `miss_reason`; zero executed/selected rows). Executed-trade joins against them return nothing on
   any key; family attribution for executed trades must come from the TRADE_LEDGER — Sol and FA
   both did this correctly. Future lanes should treat the pool as a comparator population, never a
   superset.
2. **The circulated FF3 label "(multiplicity)" mischaracterizes FF's grounds** — no bill was
   priced; the refusal rests on unbilled/selection-forbidden looks + identifiability + sample size.
   Substance unchanged.
3. **Join hazard corroborated on executed money:** 18/57 Jan trades' bare candidate_ids collide
   with missed-pool rows; the 4-tuple is unique everywhere it was tested (0 duplicate keys in any
   pool or ledger).
4. **Lane trade tables are faithful projections** of the TRADE_LEDGERs: 1:1 by 4-tuple, zero
   economic-field mismatches, both months; Jan's two null-`net_r` rows split 1 FVG + 1 breaker,
   matching Sol's per-family `unscoreable_n`.
5. **Sol's output integrity holds:** all six composition outputs hash to the sha256 values in
   `SESSION_FF_COMPLETE.json`; Sol's pool copies are byte-identical to the commissioned paths.

## Artifacts

- `FF_VERIFY.json` (machine-readable verdicts) — this directory
- `ff_recompute.py` / `ff_recompute_raw.json` — executed-family recompute
- `ff_funnel_stream.py` / `ff_funnel_stream_result.json` — missed-ledger stage counts
- `ff_family_tension_recompute.py` / `ff_family_tension_recompute_result.json` — comparators, paired tests, Wilson CIs
