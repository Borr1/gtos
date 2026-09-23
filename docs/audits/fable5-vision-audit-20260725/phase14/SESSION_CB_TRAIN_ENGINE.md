# Session CB — the train-grade engine (wave 14, B2150–B2199)

Read first: `phase14/TRAINING_LANE_RATIFICATION.md` (§1.4 is your charter, §5 your limits),
`phase12/SESSION_AX_FAST_ENGINE_RESULT.md` IN FULL (the wall-clock map you build from — AX
measured where the time actually goes and proved reproduction under the WRONG acceptance
test), `src/research_infra/fast_engine/` (AX's code — extend or build beside, your call,
stated), CLAUDE.md H3/H5 (the memory attribution table and the no-sub-window hazard),
`THIRD_REVIEW.md` §A1. Owner authority: the 2026-07-31 training-lane ratification.

**The objective in one sentence:** a replay engine that reproduces the frozen engine's
TRADES — not its receipts — several times faster and small enough to run arms in parallel,
so the training lane can iterate on history at iteration speed.

**The acceptance-test correction this session exists to exploit.** AX was held to
provenance-identity (byte-identical evidence receipts), which forced keeping the payload
sha256 loop (52M calls on the 2-day fixture), the evidence accumulation (60.6 % of heap,
the RSS peak), and GC-off. The training lane needs **trade-outcome identity only**: same
fills, same exits, same per-trade R. Everything that exists to *prove* rather than *decide*
is now removable — but AX also measured the trap: attribution projection (26.2 % of wall)
is **called by the selection factor**, so decisions READ some attribution values. The heart
of this build is the dataflow cut: find the decision-consumed subset and compute ONLY that.

## Work orders

**CB-1 — Define and freeze the identity tuple.** Propose the exact per-trade tuple
(symbol, direction, entry time/price, exit time/price, R, sizing inputs — you justify the
fields) and the comparator. The frozen engine's own fixture output is the reference. State
what is deliberately OUTSIDE the tuple (receipts, ledgers, attribution fields) — that list
is the permission slip for every deletion that follows.

**CB-2 — The dataflow cut, then the deletions.** Trace what the selection/sizing path
actually reads from attribution; compute only that. Then remove, in measured steps (one
lever per bench run, AX's discipline): the evidence accumulation, the payload-hash identity
loop, day-end serialisation costs, GC-off (contract-irrelevant here — this lane never runs
under R2). AX's two built-but-unverified levers (`abc_concrete_types`,
`authority_hash_identity_memo`, `attribution_fields_identity_memo` — the pending H-AX-2
bench) are yours to verify and absorb.

**CB-3 — Acceptance gates, in order.**
1. **Outcome identity on the sealed 2-day S1R1 fixture** vs the frozen engine (tuple-set
   equality, zero tolerance).
2. **Speedup + memory, measured**: wall-clock ratio and peak RSS on the same fixture;
   then TWO CONCURRENT ARMS measured on this 16 GB machine. Target ≥5×; report honestly
   whatever you get, with a residual map of where the remaining time lives.
3. **Sub-window works**: `stop_after_day` usable (H5 is killed for this lane) — a one-day
   iteration must cost one day, not a month.
4. **Partition enforcement wired**: the engine refuses any day outside TRAIN/VAL roles via
   `src/research_infra/trainer_partitions.py` (import it, do NOT modify it — Session CC
   owns that module this wave). Fail closed, tested — the lane structurally cannot touch
   March or the blackouts.
5. **One longer identity check** if wall-clock permits after speedup (a January arm at 5×
   is ~3.3 h): run it and diff trades. If it does not fit, say so and hand the command to
   the orchestrator.

**CB-4 — The lane's output contract.** Training runs emit a compact per-arm trade table +
config fingerprint (spec digest, surface stamp, engine version) that CC's iteration ledger
can log — no 6.4 GB evidence trees. Stamp every output `TRAINING_EVIDENCE — never
admission-grade` in the artifact itself.

## Done means

Result doc findings-first + receipts under `phase14/receipts/`, blocks B2150–B2199, scoped
A/B green vs the ZERO baseline with the tool-emitted `gtos-ab-receipt-v1` fence, honest
"what I got wrong", handoff = the bench command + measured table the orchestrator can rerun.
R2 and the frozen engine untouched (new files beside); H1 membership check before editing
anything under `src/`; never touch the VPS; never run broker-capable scripts; never edit
`config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, or any R2-bound path.
