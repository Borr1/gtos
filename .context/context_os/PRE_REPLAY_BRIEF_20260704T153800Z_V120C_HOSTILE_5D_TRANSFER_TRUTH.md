# V120C Hostile 5D Transfer Truth Pre-Patch Brief

Status: current disk/process evidence brief before the next patch. This is not a full-system proof and not a live/final claim.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V120C_MATERIALIZED_SELECTOR_ORIGIN_CONTRACT_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: `2026-05-13..2026-05-17`
- Profile: `repaired_package_conversion_v3`
- Rows: 288 scorecards, 8 order rows, 2 filled trades, 2765 missed-opportunity rows
- Trade result: `-2.19911518R` net, `-2.0R` gross/final, `-$219.7906166` cash PnL, `199.8896855` risk cash, `0.2%` risk, W/L/F `0/2/0`
- Filled behavior: 2 BTCUSD LONG limit-first reduced-risk trades, both stop losses, both on `2026-05-15`
- Broker/live/final: closed. No broker mutation, no final selection claim.

## Active Process State

The V120C hostile five-day replay completed. No duplicate broad replay should be launched from this checkpoint unless the next same-root batch changes executable behavior and targeted proof is insufficient.

## Baselines

- V89D same window: 56 trades, `+34.84520454R`, W/L/F `41/15/0`
- V90 same window: 51 trades, `+28.84201157R`, W/L/F `37/14/0`; V90 scorecard ledger is absent despite summary materialization claim, so use with artifact warning.
- V92 same window: 51 trades, `+29.35570236R`, W/L/F `37/14/0`
- V119C same window: 5 trades, `-5.50984356R`, W/L/F `0/5/0`
- V120C vs V119C: `+3.31072838R`, 3 losing trades removed, no added trades.
- V120C vs V92: `-31.55481754R`, 49 fewer trades, 50 V92 trades removed for `+30.45167255R`, 1 added V120C loser for `-1.10314499R`.

## Dirty Files And Active Code

Current active route-owned changes include selector B3 action/reason fixes, reduced-risk contract updates, V120 transfer normalization, comparator/verifier additions, focused tests, Fable plan files, and this V120C control update. `.context/LIVE_STATE.md` is regenerated state and must not be staged as route proof unless intentionally required.

## Subagent Findings

- Kierkegaard: incorporated. B1 raw/effective provenance and R-identity proof gaps were patched and V120C scans are clean.
- Kant: incorporated. Off-session action/reason, fallback expiry, V120 transfer, zero-risk finalizer, and reallocation coverage concerns remain partly open; V120C confirms risk-expression/lifecycle starvation is still material.
- Ramanujan: incorporated. V119C was the correct latest baseline; V89D/V90/V92 comparator requirements are included.
- Einstein: running current lane for risk-expression/risk-basis starvation.
- Plato: running current lane for V92 removed-opportunity transfer.
- Godel: running current lane for lifecycle/fill-realism/verifier semantics.

## Top-To-Bottom Mismatch Classes

- Source-bound -> candidate: V120C source-bound parity summary is not rebuilt yet; no full-reservoir transfer claim is allowed from this run.
- Candidate -> selector: 2601 missed rows are selector-not-risk-bearing and net negative, but 772R positive opportunity exists inside that rejected bucket; needs causal separation before opening.
- Selector -> scheduler: actual orders/trades are raw `reject` materialized to `open-reduced-risk`; this is fallback expression, not native full package trade authority.
- Scheduler -> risk: all orders/trades are reduced; no full-risk rows. 97 scorecards and 10 missed rows are final-blocked by `risk_pct_basis_missing`.
- Risk -> order: transfer status is now clean for V120C, but valid opportunity is mostly final-blocked or not order-executable.
- Order -> lifecycle/fill: 49 missed rows show fill-realism/passive-envelope blocker with `+45.22953103R` net; 2 order rows expired unfilled.
- Lifecycle -> fill: same-side pending verifier currently misclassifies missed counterfactual fills as real filled duplicates; replace-pending missed bucket remains positive.
- Fill -> exit: 2 real fills both stop out; V92 removed winners include target/profit-harvest exits, but their V120C landing must be traced before policy tuning.
- Ledger/verifier: missed counterfactual fill semantics bug must be fixed; V120C source-bound parity artifacts must be built.

## Fixed / Partial / Open

- Fixed: B1 selector-origin materialization and R identity scans are clean.
- Fixed: V120C order-executable transfer scan has zero bad counts.
- Partial: same-side lifecycle scan is polluted by missed-row counterfactual fills.
- Open: risk-expression collapse, risk-basis final blocks, fill-realism/passive-envelope starvation, daily-lockout/replace-pending missed positives, V120C source-bound parity summary gap.

## Highest-Leverage Same-Root Batch

Patch V120D risk-lifecycle truth and opportunity-starvation as a batch:

1. verifier semantics: missed rows with `order_status=not_sent_missed_opportunity` and counterfactual `fill_status` must not be counted as actual filled duplicate lifecycle violations;
2. risk-basis: classify whether `risk_pct_basis_missing` is a real behavior veto or a propagation omission and patch the relevant scheduler/timewarp path;
3. risk ladder: preserve full/reduced/diagnostic causes and repair full-risk signing where predecision conditions pass;
4. fill/lifecycle: repair passive-envelope/fill-realism fallback starvation only where the row remains honest live-as-if executable;
5. parity: rebuild V120C or next-run source-bound parity before source-bound transfer claims.

## Patch Types

- Verifier missed-row fill semantics: diagnostic/ledger correctness.
- Risk-basis propagation/final-block repair: correctness and performance if it releases valid executable rows.
- Risk-expression ladder repair: correctness and performance.
- Fill-realism/passive-envelope repair: correctness first; performance may worsen or improve depending on honest fillability.
- Parity rebuild: diagnostic artifact required for denominator-normalized reporting.

## Expected Effects Before Replay

- Candidate -> scorecard: unchanged by verifier patch; risk-basis repair may increase actionable scorecard transfer if it is a propagation omission.
- Scorecard -> order: should increase only if risk-basis or lifecycle blockers are genuinely repaired.
- Order -> fill: should not be inflated by diagnostic fills; fill-realism repairs must keep realism labels honest.
- Missed positive R: verifier patch reclassifies false-positive lifecycle scan only; behavior patches should reduce positive missed R in risk-basis/fill-realism/replace-pending buckets.
- Missed negative R: should remain blocked unless causal predecision conditions distinguish it.
- Trade count/net R/WLF: no behavior effect from verifier-only patch; behavior batch must be measured with targeted proof first.
- Cost-refused/source-gap execution: must remain zero.
- Risk distribution: should expose full-risk rows only when all signing conditions pass; not by blanket promotion.

## Success / Failure Criteria

- Helped: false same-side pending missed-row lifecycle violations go to zero without hiding real order/trade duplicate fills; risk-basis rows either become named executable blockers or valid orders; full-risk/reduced/diagnostic distribution is causal and explicit; positive missed fill/lifecycle buckets shrink for executable reasons.
- Failed: any actual order/trade duplicate fill escapes lifecycle authority; `unbound_without_final_blocker` appears on an order-executable row; full-risk appears without signing conditions; improvement comes only from suppressing opportunity.
- Exposes next flaw: transfer and verifier stay clean but V120D remains negative because exits/stops damage the remaining executable fills or because removed V92 winners are truthfully non-executable under fill realism.
