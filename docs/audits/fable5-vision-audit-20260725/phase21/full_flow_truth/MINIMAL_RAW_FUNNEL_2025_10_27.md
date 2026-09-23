# Wave 21 minimal raw candidate funnel — 2025-10-27

The repaired one-day run did **not** kill generation, the ten emitting families,
Selector, Scheduler, or order creation. It generated 6,624 candidate
occurrences, retained all 6,624 in the terminal union, simulated eight trades,
and produced one positive numeric trade. This is an engineering comparator,
not a profitability result: it uses modelled M1 paths, does not have the final
post-lifecycle cost stage, and failed the independent full-DAG verifier.

## What changed

Four narrow defects were repaired:

- Exact broker-profile symbol mappings now outrank generic route aliases. The
  old merge could turn FTMO `GER40.cash`, `UKOIL.cash`, or `USOIL.cash` back
  into another broker's generic alias, so commission lookup correctly refused
  to invent a value but incorrectly called valid authority missing.
- When a causal tick is unavailable, the cost packet now uses the existing
  era/hour-aware spread model. It no longer promotes an R-floor, a static
  profile spread, or `max_spread_cents` (an admission ceiling) into a quote.
- An incomplete four-component cost packet stays nonnumeric; the old `.12R`
  fallback is gone. A proven explicit zero commission stays zero instead of
  being overwritten.
- An unbounded Scheduler cost ceiling now serializes as `null` plus an explicit
  unbounded flag instead of leaking JSON-invalid infinity.

The earlier **6,563 generated / zero selected** result was therefore not a
valid claim that the repaired system killed every candidate. It combined an
unhydrated package-authority surface with the pre-repair cost path. With the
exact 82-row sleeve registry and 1,101-row member-axis ledger hydrated, the
same one-day route produced this funnel:

| Stage | Count |
|---|---:|
| Decision symbol/windows | 2,304 |
| Generated candidate occurrences | 6,624 |
| Missed / not traded | 6,616 |
| Simulated orders/trades | 8 |
| Numeric positive trades | 1 |
| Numeric stopped trades | 6 |
| Outcome not evaluable (ordered ticks required) | 1 |

All ten expected broad families emitted: FVG fill 3,877; OB retest 1,841;
liquidity sweep 247; displacement 203; cross-asset 125; structural distance
122; breaker re-entry 119; session open-range 47; volatility compression 31;
and regime transition 12.

## Why 6,616 candidates did not become trades

This was not one giant cost rejection. Among missed candidates, the raw
Selector actions were 5,170 reject, 1,064 reduce-risk, 246 trade, 131
open-reduced-risk, and five source-required. In other words, **246 candidates
passed Selector as trades but did not survive the later package, competition,
risk, and order gates**.

The raw Selector reasons were:

- 4,232 cost-packet refusal
- 736 confluence disagreement
- 328 dynamic-router softened to reduce-risk
- 323 off-configured session block
- 274 negative expected value after cost
- 273 dynamic-router refusal
- 246 admission passed
- 131 source-bound router-refusal open-reduced
- 51 no exact shadow sleeve match
- 17 non-admission sleeve only
- five source-required

Looking directly at cost status, 4,509 missed candidates failed the cost packet
and 2,107 passed it. The configured limits were 0.15R total expected cost and
0.10R spread. Of the 4,509 refusals, 4,358 exceeded total cost, 2,904 exceeded
spread, and 2,753 exceeded both. That leaves 1,605 total-only and 151
spread-only refusals. **There were no remaining missing-commission-authority
refusals after the alias repair.**

Why can an ordinary spread be large in R? The gate divides price friction by
the candidate's stop distance. It is not saying the quote was far from the
limit. A very tight stop makes a normal price spread a large fraction of one R.
For example:

- UK100 short at 07:45: stop distance 8.3607 points; spread 0.1022R and total
  0.1222R. It later reached its modelled target but was refused only because
  spread was just above the 0.10R spread cap.
- GBPJPY short at 14:00: stop distance 0.1128; spread 0.1948R, commission
  0.0708R, swap 0.0824R, slippage 0.02R, total 0.3679R. It exceeded both caps.
- USDJPY short at 21:30: stop distance 0.021946; spread 1.7713R and total
  2.4642R. It later reached target in the modelled path, but its own pretrade
  forecast was still about -1.89R net because the stop was extremely tight.

The median cost-refused row was 0.3230R total and 0.1334R spread; the ranges
were 0.1209–5.7035R total and 0.00165–5.3285R spread. Those numbers are worth
reviewing, but deleting cost would silently change the risk geometry rather
than repair the system.

## Did promising candidates get lost later?

Yes. The missed-opportunity model contains 144 target-reaching candidates:
126 were cost-refused and 18 cost-passed. Four of the 18 were raw Selector
`trade` decisions. Their exact downstream blockers were:

1. USDJPY long, cross-asset, 01:45 — expected net 0.9694R. It requested 2.0%
   while the cluster ceiling was 1.5%; headroom-only reduced new entries are
   explicitly disabled, so Scheduler refused it.
2. JP225 short, liquidity sweep, 02:00 — expected net 0.5984R. Its probability
   was 0.6860 versus the immediate marketable-entry floor of 0.70.
3. USDJPY long, cross-asset, 02:00 — expected net 0.9764R. It hit the same
   2.0%-versus-1.5% cluster-headroom rule.
4. XAUUSD short, displacement, 08:30 — expected net 0.7718R. No exact
   XAUUSD-short/displacement/London member-axis row existed; the broader row
   had a lifecycle-window mismatch, so package admission refused it.

These are real explanations, not proof that any gate should be loosened. The
headroom-reduced arm had previously performed worse than the fully ranked arm,
the JP225 rule missed its floor, and the XAU case lacks exact package evidence.
The next comparison should test whether these patterns repeat on a small frozen
set of unopened days before changing policy.

## The eight simulated trades

Seven had numeric modelled outcomes: one USOIL displacement trade made
+0.9625R net and six stopped, for -5.5652R total / -0.7950R mean. The eighth,
an XAUUSD long, is correctly `NOT_EVALUABLE` because ordered ticks are required.
This single day is poor selection evidence, but it is neither a family kill nor
an edge verdict.

## Decision and next work

- Do not change live trading from this result. Live W7 has a different native
  graph and these Selector/Scheduler packets are not its authority.
- Do not relax cost, probability, headroom, or sleeve thresholds from one day.
- The next bounded science is the identical funnel on two or three
  preregistered unopened days, specifically tracking raw Selector trades,
  final vetoes, and target-reaching nonselections.
- Only if the same gate repeatedly displaces stronger candidates should that
  gate or its sleeve evidence be repaired and rerun A/B.

The machine-readable receipt beside this report binds the exact local artifact
hashes, counts, examples, A/B tests, and claim boundaries.

Three repaired files are R2 `common_behavior_inputs`: the Scheduler, replay
runner, and timewarp loop. This is an explicit forward seal break. No sealed R2
campaign may reuse its old decision contract or claim parity from this branch;
integration requires a deliberate reseal and rerun of whichever sealed windows
the owner chooses. This one-day engineering comparator is not that rerun.
