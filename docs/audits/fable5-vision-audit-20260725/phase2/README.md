# Phase 2 handoff — the rebuild, starting with the harness

`FULL_VISION_PLAN.md` Phase 2: one policy-plural decision core. This is where the throughput comes
from — **72.4 % of replay CPU is proof/attribution machinery and 0.2 % decides trades**, a dense day is
507.6 s against a 150–250 s target, and one arm peaks at 8.61 GB on a 16 GiB machine.

| Session | Task | Worktree / branch |
|---|---|---|
| **D** — `SESSION_D_HARNESS_REVIVAL.md` | Revive the differential harness. Three modules, ~6,800 lines, already written and tested and dead. | `worktrees/phase2-harness-20260726` · `phase2/harness-revival` |

**Why this runs now rather than after Phase 1.** Gate G2's regression baseline is the four sealed
January arms, which already exist — so D depends on none of the Phase-1 sessions (`../phase1/`) and can
run concurrently with all three. The plan sequences **harness before core** deliberately: without a
comparator, every parity claim about the rebuild is an assertion.

**What comes after D**, per the plan, in order: `BroadV4Policy` vertical slice against the sealed
January pack → widen to the month → `SleeveBookPolicy` validated against the VPS placement ledgers →
sub-window replay and portable seals → the single-materialisation columnar source layer that takes
memory to ≤3 GB/arm and makes four-arm parallelism possible.

Shared state — baseline, contract of record, Python version, worktree rules — is in
[`../phase1/README.md`](../phase1/README.md); it applies to every session regardless of phase.
