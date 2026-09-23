# Session P — what the carry would have recorded, replayed over the live closes

The 151 `position_closed` packets from `vps-export-20260725` fed back through
`build_economics_block`. This is not a projection; it is the block the emitter would have written,
computed from the fields those packets already carry.

Reproduce: see `phase3/PACKET_EMITTER_CARRY.md` §6.

## Result

| | |
|---|---:|
| `position_closed` rows | 151 |
| economics block built | **148** (3 carry no entry instant at all) |
| holding provenance **measured** (broker fill → broker exit deal) | **89** |
| holding provenance **modelled** (poll-loop observation on one or both ends) | **59** |
| median hold | 2.2466 h |
| exit observation lag **published** | 90 rows, median **26.8 s**, max **1,446.5 s** |

**The 89/59 split is the point.** Today all 148 look identical to a reader — a timestamp is a
timestamp. After the carry, 89 of them are broker facts and 59 are poll observations, and the packet
says which. A consumer computing a cost-true P&L can weight them differently, or drop the 59, or
publish both. It cannot do any of that now.

## `rollover_nights` — a field that exists nowhere today

| nights charged | closes |
|---:|---:|
| 0 | 109 |
| 1 | 31 |
| 2 | 2 |
| **3** | **6** |

**53 swap-charged nights across the 37-day live window; 39 of 148 closes carry at least one.**

The six 3-night closes are the triple-swap weekday collection, and they are exactly the case Session
N's carry layer got wrong and withdrew (`SESSION_N_W7_RECOST_RESULT.md` §9.1: scaling horizons by
5/7 understated every H4 ceiling 1.40×, and the claim that the JPY sleeves "cannot pay three nights
of carry no matter what is assumed" was false). Counted on the broker wall clock, six live closes
did pay three.

Session N §8.1 names carry as the dominant remaining uncertainty for OD-3 — `P(pass)` **0.951** at
one night of average carry against **0.450** at every trade running to its horizon. **This is the
field that measures which of those two worlds the live book is in.** It is not available for any
past trade; it starts at the first packet after deployment.

## Realized cost completeness

| | closes |
|---|---:|
| all five broker components present | **50** |
| at least one component missing (named individually) | **40** |

No total is emitted for the 40. A partial sum is a wrong number wearing the costume of a right one,
and charging zero for an unknown cost is the F38 defect itself. The missing components are derived
by **set-difference** from the full expected field set, so absence reads as absence rather than zero.

---

## Scope note, added after the adversarial pass (B218)

**Everything above is `position_closed` only, and those figures are unchanged by the B218 fix** —
terminal events were never affected by it. Re-verified after the fix: 148 blocks, 89 measured /
59 modelled, 53 swap-charged nights, 50 complete / 40 incomplete realized-cost sets.

But the corpus-wide picture is the one a reader should hold, because 99.6 % of economics blocks are
**not** closes:

| | n | mean |
|---|---:|---:|
| **completed** holds (`holding_seconds` set) | **293** | 8.269 h |
| — of which `position_closed` | 148 | 8.369 h |
| — of which `position_managed` (genuine mid-management closes) | 144 | 8.199 h |
| — of which `position_adopted` | 1 | 3.520 h |
| **right-censored** observations (`elapsed_seconds_at_emit`, position still open) | **71,988** | 20.88 h |

The censored rows are real evidence — a position open for 20 h is a lower bound on its hold, which
is exactly what a survival analysis consumes. They are published under a **separate key** with
`elapsed_is_right_censored: true` and `position_open_at_emit: true`, so nothing can average them in
with the 293 completed holds by accident. Before B218 was fixed they were published *as* completed
holds, and a naive mean over the block read 20.85 h against a true 8.37 h.
