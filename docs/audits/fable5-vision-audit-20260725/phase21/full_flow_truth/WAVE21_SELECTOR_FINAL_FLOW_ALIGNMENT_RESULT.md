# Wave 21 Selector-to-final-decision alignment result

The flow was not simplified by deleting gates. It was made understandable by preserving the exact terminal blocker, and the one apparently duplicated cost threshold was tested directly before changing it.

The result is clear: keep the immediate-marketable LIMIT route ceiling at **0.10R** and keep the broader Selector quality ceiling at **0.20R**. Raising the route ceiling to 0.20R admitted more orders but made the frozen unseen result worse by **4.85357727R** of scoreable net proxy across two days. The preregistered stopping rule therefore ended the experiment without running the reserved third day.

This is an offline `research_timewarp` engineering comparator. It is not production parity, broker fill truth, live authority, or final post-lifecycle broker economics.

## The clean decision flow

The measured path is now interpretable as:

1. Raw generation creates a broad candidate population.
2. Selector applies the general 0.20R quality ceiling plus probability, EV, confluence, session, and source checks.
3. The package/order route applies an additional 0.10R ceiling only to an immediately marketable LIMIT, where losing the intended resting-entry geometry is a specific execution-quality risk.
4. Scheduler ranks the remaining candidates against the same decision window.
5. Risk allocates available headroom; a 2.0% request can receive 1.5% when that is the positive headroom, while zero headroom still refuses.
6. The order/lifecycle path records fill, target, stop, time-stop, or no-fill.

The package and Scheduler probes retain their generic status strings for compatibility, but `risk_decision_reason` now carries the actual blocker: the package refusal, Scheduler primary ineligibility, or terminal effective Selector reason. A candidate blocked by `package_marketable_limit_entry_guard_blocked` will no longer finish with only `scheduler_option_runtime_ineligible` as its explanation.

## Same-candidate unseen A/B

Only one field changed between arms:

`scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_max_expected_cost_r`

Candidate generation, sources, order, all other gates, Selector's 0.20R ceiling, sizing, and lifecycle behavior were identical.

| UTC day | Candidates/arm | Raw Selector trades/arm | Orders 0.10R → 0.20R | Fills 0.10R → 0.20R | Net proxy 0.10R → 0.20R | Delta |
|---|---:|---:|---:|---:|---:|---:|
| 2025-10-29 | 9,018 | 777 | 13 → 19 | 10 → 18 | −2.56561190R → −6.88617908R | −4.32056718R |
| 2025-11-04 | 7,644 | 629 | 13 → 17 | 13 → 17 | +5.92295285R → +5.38994276R | −0.53301009R |
| Combined | 16,662 | 1,406 | 26 → 36 | 23 → 35 | +3.35734095R → −1.49623632R | **−4.85357727R** |

Generation was real and uncached from prepared candidates: 2,304 generator calls per day and 4,608 per arm across the two days. Candidate counts and identity roots matched exactly between each day's arms.

The treatment changed later portfolio state, so it did not merely add candidates monotonically. Across both days it added 18 order identities and displaced eight baseline identities. That is why a same-window end-to-end A/B was necessary; inspecting isolated candidate cost alone would have missed the Scheduler/risk/account cascade.

## What this says about cost

It does not say that all cost controls should be tight. The earlier repair correctly removed the over-strict 0.15R hard-total refusal and retained complete-packet hard bounds of 0.35R spread / 0.45R total. It also retained the 0.20R general Selector quality ceiling after the 0.45R comparison added three scoreable stops totaling −3.72975741R.

This result answers a narrower question. An immediately marketable LIMIT no longer has the same resting-entry geometry that justified the candidate. On the frozen unseen days, allowing that route up to 0.20R produced more fills but a worse portfolio. The 0.10R route ceiling is therefore doing useful execution-quality filtering in this comparator; it is not just duplicating the general Selector cost gate.

## Final decisions

- Candidate generation remains unchanged; no family was killed or suppressed.
- The Selector 0.20R quality ceiling remains unchanged.
- The immediate-marketable LIMIT route ceiling remains 0.10R.
- Fillability, probability, EV, confluence, session, package authority, daily-loss, competition, and zero-headroom controls remain in place.
- Positive-headroom partial allocation remains in place.
- No live, config, profile, token, VPS, account, arming, or broker change is authorized or performed.
- No third threshold-search day is run because the frozen stop condition was met.

## Evidence boundary

The two arms use modelled lifecycle paths and a complete pretrade-cost net proxy. They do not prove queue position, broker acknowledgement/fill, lot sizing, or broker-deal realized costs. Twenty of the broader 24-symbol source surface still lacks ordered bid/ask ticks. The edited timewarp file is R2-bound, so an affected sealed campaign needs an explicit forward reseal before it can claim contract continuity.

Machine-readable counts, roots, decisions, and artifact hashes are in `WAVE21_SELECTOR_FINAL_FLOW_ALIGNMENT_RESULT.json`.

The final affected test cone passed **1,067/1,067** on both the clean parent and this repair, with zero regressed tests.
