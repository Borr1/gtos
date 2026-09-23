# Wave 21 minimal repair — decision result

The system still generates candidates. The three frozen days produced 23,309 raw candidate occurrences, 29 orders, and 25 filled comparator trades. The repairs did not kill the families or shrink candidate generation.

This is an offline `research_timewarp` engineering comparator, not production parity, broker fill truth, live authority, or a final strategy-profit result.

## Decisions

- Keep the valid XAUUSD SHORT displacement-continuation owner family root in offline research. It no longer needs a shadow-only or fabricated exact-member join.
- Keep positive-headroom sizing: a valid 2.0% request with only 1.5% available receives 1.5%; it is not rejected merely for lacking the full request. Zero headroom still refuses the trade.
- Keep the complete physical pretrade packet and its 0.35R spread / 0.45R total hard bounds.
- Keep the Selector quality ceiling at 0.20R. Do not raise it to 0.45R.
- Keep the generic same-symbol daily-loss lockout.
- Make no live/config/arming/activation change from this evidence.

## What cost actually did

The original 0.15R total hard cap was too strict. On 2025-10-28 it would have blocked a UK100 `current_fvg_fill` trade with 0.17092848R cost that reached +2R gross and +1.82907152R net proxy. The repaired complete-packet bound therefore remains 0.45R.

But moving the downstream Selector quality ceiling from 0.20R to 0.45R failed its same-source test. Candidate identity and count were unchanged across 2025-10-28, 2025-11-03, and 2025-11-07. The looser ceiling added five trades:

- XAGUSD `current_ob_retest`: −1.21961005R net.
- EURJPY `current_ob_retest`: −1.22023596R net.
- SPX500 `current_fvg_fill`: −1.28991140R net.
- UK100 `current_fvg_fill`: ordered-tick sequence required, not scoreable.
- USDCAD `liquidity_sweep_reclaim`: ordered-tick sequence required, not scoreable.

The three scoreable additions were all stops, totaling −3.72975741R. There was no scoreable added winner. This is why 0.20R is retained: it was not arbitrary caution in this sample; the relaxed candidates were worse.

Cost is measured as a fraction of stop distance, not as a fraction of the nominal price or target move. For example, the added EURJPY trade had a 13.23-pip stop. Spread consumed about 1.85 pips-equivalent, commission about 0.80, and modeled slippage about 0.26: 0.2202R total. It then hit the stop. By contrast, the repaired gold candidates cost only 0.036–0.048R, so cost was not their problem.

Commission authority matters because zero, missing, wrong-broker, or wrong-symbol commission can make expected net R falsely optimistic. The current packet requires the four finite components—spread, slippage, swap, commission—and refuses incomplete authority rather than filling commission with zero. This became visible only when the old stored-row validation was decomposed into broker/profile/date-specific components; the older validation did not provide that complete attribution.

## What the 6,563 count means

On the final 2025-11-03 run, 8,284 candidate occurrences were conserved with no truncation. `not_filled_no_trade = 6,563` is a counterfactual lifecycle result: the modeled entry was never touched inside the available path. It is not “6,563 cost rejections.”

The first Selector disposition of all 8,284 candidates was:

- 743 incomplete/over-hard-bound cost packets;
- 2,199 above the retained 0.20R Selector cost-quality ceiling;
- 282 negative expected value after cost;
- 1,629 numeric-confluence disagreement;
- 533 off-session;
- 662 dynamic-router refusal;
- 675 clean admission passes;
- the remaining 1,561 were reduced-risk, open-reduced, package-role, or source-required dispositions.

Those 675 Selector passes still compete in the Scheduler and risk/account state. Eleven unique orders were sent; nine filled and two expired. The nine filled outcomes were four stops, two targets, two time stops, and one terminal requiring ordered ticks for exact R. Candidate generation is deliberately broader than final trading; generated does not mean selected, and selected does not mean filled.

## Gold trace

Before the final Scheduler repair, three of four exact approved XAU family-root occurrences were vetoed by a stale package alias check. After the repair all four were ranked, with zero stale root vetoes.

They still did not become new trades because XAU had already taken a real SHORT liquidity-sweep trade at 07:15 UTC: −1.0R gross, 0.04743378R cost, −1.04743378R net at 0.625% risk. The generic same-symbol daily-loss lockout then blocked later XAU entries for that day.

The four repaired family-root counterfactuals had costs of only 0.0365R, 0.0476R, 0.0363R, and 0.0378R. Three modeled time-stop paths were small positives (+0.0319R, +0.2357R, +0.0783R net proxy); one needs ordered ticks. Thus:

- the gold admission mismatch was real and is fixed;
- cost was not blocking these gold candidates;
- a separate, genuine post-loss risk rule was blocking them;
- there is no evidence here to remove that daily-loss rule.

## Verification and remaining boundary

The final raw replay called the generator 2,304 times, consumed no prepared candidate pack, conserved all 8,284 candidate occurrences, and passed the candidate-to-terminal relational audit. The full affected current matrix is 660 passed. The exact Scheduler parent/current comparison is 347 passed versus 349 passed, both with zero failures; the two additions are the XAU-root and explicit 2.0%→1.5% behavioral proofs.

The independent verifier did not pass: it stopped on `independent_occurrence_stage_dag_mismatch` because it still expects the old flattened stage graph. Therefore no result-bearing economics or production-parity claim is made. The Scheduler file also breaks the historical R2 byte seal; any affected sealed campaign must be deliberately resealed before it can claim R2 continuity.

The next useful work is not another threshold search. It is to integrate these scoped repairs into the current research branch, update the independent verifier to the actual occurrence DAG, and then run a larger never-opened multi-day/full-flow validation. Nothing should be added to live trading until that result exists.

Machine-readable findings and artifact hashes are in `WAVE21_MINIMAL_REPAIR_MULTIDAY_RESULT.json`.
