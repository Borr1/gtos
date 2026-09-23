# LIVE-CONFIRM BREADTH ROADMAP — turning the cost-gated orthogonal premia into deployable breadth (capstone, cycles 60/63/64)

The in-walls breadth frontier is closed-with-evidence (64 cycles). The DURABLE reframing from this session:
**the MT5 breadth wall is a COST wall, not a signal wall.** Several genuinely real, mutually-orthogonal
premia exist — but each one's per-unit edge is smaller than my conservative retail execution cost, and
diversification cannot rescue negative net-of-cost expectancy. The ONE lever that unlocks them is cheaper
execution, which the now-live accounts provide (c60: real index cost is 3–10× below my retail estimate).

This file makes the "self-improving loop" concrete: a pre-registered queue of the orthogonal candidates,
each with its measured gross edge, the exact cost threshold it needs, and the live-data it takes to certify.
As the live system accumulates real fills + cost, re-run each through the SAME hardened gauntlet (no new
freedom — pre-registered here to avoid post-hoc selection).

## THE QUEUE (all gross-real + orthogonal to the deployed core; gated by cost/significance, NOT signal)

| Candidate | Mechanism | Gross edge (OOS) | Orthogonality | What gates it | Cost threshold to deploy | Certify when |
|---|---|---|---|---|---|---|
| **overnight night-effect** (c64) | hold close→next-open, 39 US names | +2.05 bps/day, SEALED +3.92, PSR 1.0, perm 0.0005, **gross CERTIFIED diversifier** (CI [+0.003,+0.024]) | corr +0.109 to Donchian sleeve | cost (~2 bps gross < ~6–8 bps CFD overnight cost) | real close+open spread + swap **< ~4 bps/hold** | live overnight cost map per name |
| **time-of-day drift** (c60) | h07 pre-Euro index drift {US30,GER40,UK100} | net +0.11R @ real cost, PSR 0.87, corr −0.02 | orthogonal to core | significance (PSR < 0.95) at real cost | already net-positive; needs more **sample** to clear PSR | ~2× more live index intraday sample |
| **intraday reversion** (c63) | VWAP stretch ≥2.5σ revert, FX+IDX | +0.075R @ 0.27×, +0.59R @ 0.15×; genuine only @0.15× | corr +0.014 | cost + significance (fails div CI even @0.15×) | real RT **< ~0.15× retail** AND more sample | live FX+IDX intraday cost + sample |
| **session momentum** (c63) | 12:00 session-extension, FX+IDX | +0.04R @ 0.27×, PSR 0.68 | corr −0.037 | significance (never clears PSR) | needs cost **< 0.15×** + much more sample | likely the weakest — low priority |

## CERTIFICATION PROTOCOL (pre-registered — same machine, no new freedom)
1. From live fills, build the **real per-instrument round-trip cost** (spread at the relevant session +
   slippage + overnight swap for the night-effect). This replaces the swept cost_mult with a measured number.
2. Re-run each candidate's daily series at the measured cost through `validation_integrity.gauntlet`
   (DSR/PSR + block-permutation + per-year + trial-budget) → genuine iff PSR>0.95 AND perm<0.05 AND SEALED>0.
3. If genuine, run `portfolio_contribution.certify_diversifier` vs the live deployed book (not the backtest
   proxy) → deploy only if CERTIFIED (incremental CI excludes 0) at a satellite weight.
4. Trial-budget honesty: these 4 are the registered family; count them in the DSR trial budget. Do NOT
   mine new intraday variants post-hoc and slip them in (that is the cell-selection leak the machine guards).
5. Size any certified live breadth as a small satellite first (like us_equity@0.35×); it competes for the
   same 4% gross cap, so it must raise BOOK Sharpe net, not just add positions.

## WHY THIS IS THE NORTH-STAR PATH
The north star ("Sharpe × breadth → return as a safe dial") is breadth-gated, and breadth is cost-gated.
The deployable core (metals + equity momentum) deploys because its per-trade edge is LARGE R that amortizes
cost. The queue above is the inventory of small orthogonal premia that ONLY cheaper live execution can turn
positive. So the live system is not just the proof of the core — it is the **execution-cost instrument**
that converts this queued breadth into deployable sleeves. Every certified live breadth raises √breadth,
which lets return be dialed up at the SAME ruin risk (the smooth-defense governor already shipped supports it).

## OUT-OF-WALLS (unchanged)
Beyond live-confirm, the only other breadth lever is finer/paid data (tick order-flow, options/VRP,
cross-venue) — deferred to post-payout per owner doctrine.
