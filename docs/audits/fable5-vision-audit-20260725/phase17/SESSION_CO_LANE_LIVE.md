# Session CO — the learning lane goes live-bounded: recommendations become sized reality

Session: CO · Wave 17 · Blocks **B2800–B2849** · Branch `phase17/lane-live` ·
Worktree `/Users/borr/GTOSActive/worktrees/wave17-lane-live-20260801`

**Authority: OD-ALL-IN (`phase17/OD_ALL_IN_20260801.md`) — read whole.** The learning lane
(Session R, wave 4; re-fed cost-true by AE, wave 7) is default-off, recommendation-only, and
its recommendations have sat unapplied by design. The owner has ended the waiting room:
challenge accounts are the live test surface. Build the bounded live application so the
orchestrator can arm it.

Standing owner directives: judgment over script; build/improve/fix; Workflow opt-in approved.

## The state you inherit

R's lane is closed-loop, live-aware, default-off, **brake-only** in design intent
(`phase4/SESSION_R_LEARNING_LANE_RESULT.md`). AE re-read it against cost-true evidence: all
seven legacy-covered verdicts changed; on the CURRENT armed sets the operative outputs
include `crypto` ×1.08 (the only up-weight the lane would apply) and DOWN_WEIGHT verdicts on
sleeves that are mostly no longer armed. The armed sets moved since AE (5 FTMO / 4 FN, exits
re-contracted, spread floor on) — the verdicts may too.

## Work orders

**CO-1 — re-run the lane's read at today's evidence.** Cost-true, per account, CURRENT armed
sleeves at their CURRENT contracts (target_5R mx, spread floor on the two REPAIR sleeves).
Output: the exact multiplier vector the lane would apply today, with the OOS basis and n
behind each. Verdicts, not vibes; if a verdict's basis is thinner than AE's floor, it emits
no multiplier.

**CO-2 — the bounded application mechanism.** Design constraints, all hard: multipliers
clamped to a declared band (propose the band from the evidence — e.g. [0.5, 1.15] — and
justify it; the DOWN side may be wider than the UP side, brakes are cheaper than throttle);
applied at the sizing layer WITHOUT touching config bytes (token digests bind them — find the
carrier: supervisor args like `--lane-weights <file>` reading a signed weights file is the
CE-precedent shape; the weights file lives outside config); every applied weight stamped into
the decision packet with provenance; the lane can only move weights at decision-day
boundaries (B365-class: no intraday size jumps); a dead/stale/invalid weights file means
×1.00 everywhere — fail-closed to neutral, logged loudly. The governor's caps and the
breach-flatten remain senior to everything the lane does.

**CO-3 — prove it can't hurt beyond its band.** Offline A/B on the live-decision surface:
current sizing vs lane-applied sizing over the replayable window; worst-day, worst-week,
`p_pass` delta at firm-true rules for the applied vector on both accounts. If the measured
vector's `p_pass` delta is negative beyond noise, the honest package arms the DOWN-weights
only and says why. Live veto wiring: the lane's own kill condition (what live evidence
reverses a weight, at what n) written into the receipt before arming.

**CO-4 — the ceremony package.** CE-style: MANIFEST, hashes, supervisor-args diff, weights
file + its signer/verifier, preflight vs host bytes, proving log line ("LANE WEIGHTS ACTIVE:
crypto=1.08 …" form), week-one telemetry (applied-weight per sleeve per day vs declared),
stop conditions, rollback (= remove the arg; books revert to ×1.00 on next launch).

## Boundaries

Never-execute list verbatim (CL's). Token-bound configs read-only. R2 membership check before
any `src/` edit (H1). B905. VPS is the orchestrator's. March 2026 never read; TEST surfaces
inviolable; the live forward window from 2026-07-29 is TEST — the lane may read it as VETO
input only, never as fitting input. Conventions: `WAVE_11_WORKING_AGREEMENT.md` §5–§6 + CG's
"Conventions that bind you"; scoped A/B with embedded `gtos-ab-receipt-v1` fence vs the
committed ZERO baseline; blocks B2800+ cited; commit as you go. Result doc
`phase17/SESSION_CO_LANE_LIVE_RESULT.md`, findings-first, "What I got wrong", ceremony
handoff.
