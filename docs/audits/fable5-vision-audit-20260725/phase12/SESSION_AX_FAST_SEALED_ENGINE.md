# Session AX — the fast sealed engine, built alongside the frozen one (wave 12, B1700–B1749)

## Authority and the point

Borhen, 2026-07-30: *"didnt you find that only a small percentage of the compute actually goes
to what matters, if we're aware of that why are we still talking about the 16.5 hour mark?"* —
following his standing order that the edge puzzle be fully solved "with as many replays as
possible". He is right: the 16.5 h/window figure is 8.3 % decision compute and ~60.6 %
evidence/attribution machinery, measured (`THIRD_REVIEW.md` §A1, receipt
`third_review_receipts/memattrib_result.json`): the per-day row/attribution accumulation in
`v4_timewarp_simulated_live_research_loop.py` is 3,866 MB at heap high-water (60.6 %), the
retained day-pack JSON another 401 MB, and **>99.8 % of the evidence bytes are never
value-read**. One redesign, three resource problems — CPU, memory, bytes. This session builds it.

## The two constraints that shape the build

1. **Never edit a bound file.** R2 binds 43 paths including the frozen engine
   (`replay_acceleration_attempt5_typed_sparse_runner.py`, the timewarp loop, the sealed
   runner); one byte of drift expires the parked January comparability option. The fast engine
   is **new files alongside** — an `engine_v2` (or R3-generation) lane that imports nothing it
   would mutate and leaves every bound hash untouched. Run the H1 membership check on every
   file you touch, every time.
2. **The acceptance test is bit-honesty, not speed.** Sealed January is the regression fixture
   the programme already paid for: the new engine must **reproduce a sealed January arm's
   economics R-identically from the same sealed inputs** (same caches, same day packs, same
   contract semantics — read-only). Target arm: S0R0 first (the smallest), then S1R1 (the
   fullest). "R-identical" means the per-trade R series, arm totals, and the primary q
   reproduce to the artifact's own precision; timing fields and evidence-layer internals may
   differ. If it cannot reproduce, it does not ship — a fast wrong engine is worse than a slow
   right one.

## Work orders

**AX-1 — The evidence-layer redesign.**
Replace resident accumulation with streaming: decision-relevant state stays in memory,
attribution/evidence rows stream to disk incrementally (append-only, compressed), and the
never-read classes become **opt-in** (a `--evidence full|decision|off` dial, default
`decision`) rather than always-on. The audit's numbers say this alone removes most of the
60.6 % CPU and collapses the 6.4 GB/arm heap spike (which exists at day-end serialisation of
the accumulation). Measure as you go: per-day wall-clock and RSS against the frozen engine on
the same fixture — the sealed 2-day S1R1 fixture (603.7 s / 8.61 GB on the frozen engine) is
the unit test; a January arm is the integration test.

**AX-2 — The reproduction proof.**
The committed deliverable is a receipt: sealed January arm(s) reproduced R-identically, with
the wall-clock and peak-RSS table (frozen vs v2, same machine), and the exact reproduction
comparator (nan-aware — AN's and AQ's lesson). If full-arm reproduction is beyond one session's
wall-clock, prove the 2-day fixture bit-exact plus the longest prefix of a January arm the
clock allows, and state precisely what remains.

**AX-3 — Concurrency, measured not assumed.**
H3's ban on parallel arms was caused by the 6.4 GB evidence accumulation. If AX-1 collapses it,
measure two concurrent arms' net cost on this machine (16 GB) at the new footprint. If two arms
fit, a four-arm month drops from 16.5 h serial toward ~½ of the single-arm total — state the
measured number, not the hope. The prize worth naming: at ~4–6 h/window, sealed confirmation
runs stop being rationed and become routine instruments — which is what "as many replays as
possible" needs the sealed lane to be.

**AX-4 — What this deliberately does NOT do.**
No sealed window is RUN (no April, no May, never March). No bound file moves. No new
measurement claims about any strategy family — this is an instrument build, and its only claim
is "same answers, this much faster." The moment AW's mine produces a rule worth sealed
confirmation, the confirmation campaign gets designed on THIS engine with its own sealed
protocol + the pooled evaluator JANUARY_BANK §7.1 requires — that design is the owner's call
and a later session's work.

## Done means

Result doc + receipts under `phase12/receipts/` (the reproduction receipt is the centrepiece),
blocks B1700–B1749, scoped A/B green vs the zero baseline, honest §what-I-got-wrong, handoff
list. Never touch the VPS; never run broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or ANY R2-bound path. H3 memory discipline: one frozen-engine
fixture run at a time on this machine, and nothing heavy while three sibling sessions run —
coordinate long runs to off-hours if the machine is loaded.
