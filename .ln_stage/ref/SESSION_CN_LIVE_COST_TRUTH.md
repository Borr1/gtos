# Session CN — H-CD-2: the live path charges zero commission; wire the truth

Session: CN · Wave 17 · Blocks **B2750–B2799** · Branch `phase17/live-cost-truth` ·
Worktree `/Users/borr/GTOSActive/worktrees/wave17-live-cost-truth-20260801`

**Authority: OD-ALL-IN (`phase17/OD_ALL_IN_20260801.md`) + the standing seal-break
authorization (owner, 2026-07-31, recorded in `phase8/OWNER_DECISION_QUEUE.md`).** H-CD-2
was "priced for owner" because the adapter is an R2-bound change and the price was the parked
campaign's resume option. That option is DEAD by owner word. The price is paid. Wire it.

Standing owner directives: judgment over script; build/improve/fix; Workflow opt-in approved.

## The defect (CD's finding, wave 14)

`broker_net_cost_engine.py` sums `spread + slippage + swap` — commission is structurally
zero on the live path (F38's live twin). CD built and committed a **prepared adapter** at
`src/costs/model.py:789` that was never wired. Every live decision that screens on cost, every
shadow-log economics row, and every learning-lane read therefore under-counts JPY-class and
commission-bearing symbols today, on real money.

## Work orders

**CN-1 — re-verify the defect at HEAD.** Cite the exact live call chain (`file:line`) from
tick to cost screen to packet emission. Confirm what CD measured: which armed sleeves'
decisions actually move if commission is charged truly (wave-3's answer for the W7 book was
"0.0000 R on the index sleeve, material on the two conf-0.15 JPY sleeves" — the ARMED set is
different; measure for it, both accounts, per-symbol commission from the broker-true tables).

**CN-2 — wire the adapter.** The change must be: default-on truth on the live path,
provenance-stamped, with the old behavior reachable only as an explicitly named comparator.
Check R2 membership of every file you touch (H1) BEFORE editing; the seal consequence is
authorized but must be RECORDED — your result doc states which bound path changed and that
the frozen engine's sealed artifacts remain untouched history. If the drift check or the
execution-seal digest moves, say so in the block, with the citation form H1 mandates
(execution-seal digest, not the drift check).

**CN-3 — blast radius, measured not asserted.** The token digests bind
`config/agent_config.yaml` + profiles — confirm your change moves NO config byte (it should
be pure `src/`; if you find a config knob is required, STOP and hand that to the orchestrator
as a ceremony input instead of editing). A/B the live-decision surface offline: same inputs,
old vs new cost, diff of every decision that flips, per account. The shadow-packet schema
must keep old fields readable (learning-lane and AE-class consumers read historical packets —
do not orphan them).

**CN-4 — the carry package.** The live books run the VPS lineage. Package the changed files
CE-style (MANIFEST, hashes, preflight vs host bytes, verify script, proving log line — e.g.
the engine's own cost-provenance stamp in the first post-restart packet, stop conditions,
rollback). The orchestrator carries it in the same ceremony wave as CL/CM's packages.

## Boundaries

Never-execute list verbatim (CL's). Token-bound configs: read-only. B905. VPS untouched by
you. March 2026 never read. TEST surfaces inviolable. Conventions:
`WAVE_11_WORKING_AGREEMENT.md` §5–§6 + CG's "Conventions that bind you"; scoped A/B with the
embedded `gtos-ab-receipt-v1` fence vs the committed ZERO baseline; blocks B2750+ cited;
commit as you go. Result doc `phase17/SESSION_CN_LIVE_COST_TRUTH_RESULT.md`, findings-first,
"What I got wrong", ceremony handoff.
