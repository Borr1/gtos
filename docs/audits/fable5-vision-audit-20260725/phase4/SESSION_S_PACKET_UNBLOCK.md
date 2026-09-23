# Session S — unblock the packet carry against the VPS lineage

**Stage 3 completion.** Worktree `worktrees/wave4-packet-unblock-20260729`, branch
`phase4/packet-unblock`, from `main`. **Blocks B290–B319.**

**Read `../WAVE_4_WORKING_AGREEMENT.md` first** — especially §3.

---

## What is blocked, and how it was found

Session P's packet-emitter carry landed **half** on the live VPS on 2026-07-29. Two inert files went
in. Three were **held**, correctly:

`src/components/ultimate_book/book_owner.py` (mainline) imports
`src/components/ultimate_book/convergence_advisory.py` — **a module the VPS lineage has never had.**
The VPS worker's finding, verbatim:

> A3 as written would therefore raise `ImportError` on **both namespaces** at the next supervisor
> respawn — and the supervisor only ever *starts* a missing book, never stops one. That is a 5-minute
> restart loop with `manage_open_positions` off on any open position.

`packet_guard.py` imports `build_packet_rejected_marker` and `PACKET_ECONOMICS_KEY` from
`runtime_learning_packet`, which the live version has neither of. And `runtime_learning_packet.py`,
though additive and signature-compatible, adds `"ultimate_convergence_advisory": None` to **every**
packet and recomputes `packet_hash_sha256`, so **every live packet hash shifts** — with three live
consumers reading that stream. The three are one coupled group; landing any subset breaks the rest.

**The irony is exact, and it is the lesson.** `PACKET_EMITTER_CARRY.md` §A4 performs precisely this
optional-import audit for `broker_clock.py`, calls a module-load failure propagating through
`book_owner` *"the single worst outcome this carry could have had"* — and then does not run that same
audit for `convergence_advisory`, because the authoring session was on `main` and could not see the
VPS lineage. **You have the same blind spot unless you go and look.**

## Why it matters now

A live funded FTMO account is being armed on three sleeves. Until this lands, the forward shadow does
**not** record holding time or realized cost — and holding time is the exact quantity that made OD-3
hard. Measured on the existing live export: `spread_r` absent from **all 99,112** packets, holding
time derivable from only **151**, and `position_managed` — **79 % of all packets** — carrying an
`outcome` of just `{action, placement_status, sleeve, source_completeness_status}`.

Every day armed without this is a day of live data with the same hole.

## What you own

**Re-author the three coupled files against the VPS lineage.** Two shapes, and choosing between them
is your call:

- **(a) Strip the convergence-advisory coupling** and carry a VPS-lineage `book_owner.py` that keeps
  P's economics block and nothing else new.
- **(b) Carry `convergence_advisory.py` itself** — only if it is genuinely self-contained on that
  lineage, which you must prove rather than assume, since proving-by-assumption is what created this
  block.

Deliver as **surgical diffs against the VPS commit**, plus an owner-executed runbook — the shape
Session I used and the reason its carry applied clean with zero fuzz on five files. **You cannot reach
the VPS.** Request any file you need through the orchestrator and it will be fetched read-only.

## The VPS lineage facts you need — all measured, none assumable

The VPS tree is **155 commits ahead** of its own stale `origin/main` (last fetched 2026-06-19) across
**137 source and config files**, including all three live profiles and the whole
`src/components/ai_companion/` subsystem. It is a divergent live lineage, not drift. Its HEAD before
the token carry was `redacted_host`; two commits landed on top on 2026-07-29.

Concrete divergences already measured — **assume there are more**:

| # | mainline | VPS |
|---|---|---|
| 1 | `SleeveSpec.conf` | **`SleeveSpec.confidence`** |
| 2 | `convergence_advisory.py` present | **absent** |
| 3 | `mt5_preflight.py` order arm retired (B102) | **four live `mt5.order_send` calls at `:136,142,152,155`** |
| 4 | `apply_to_execution: true` | **`false`**, three gates at `agent_config.yaml:1161-1163` |
| 5 | `live_broker_authority` in no committed config | **committed**, also at `redacted_account.yaml:13` |

**#3 is a live safety divergence and it is not yours to fix from here** — recorded so you do not
assume mainline's safety posture holds there. Note also that the books run
`.venv-gtos\Scripts\python.exe` (**3.13.13**), *not* PATH `python` (3.11.15) — every `python ...` line
in the wave-3 runbooks tested the wrong interpreter.

## Two runbook defects to avoid repeating

Both were found on the live host and both are the false-green class this carry exists to prevent:

1. `Get-Process python | Where-Object { $_.CommandLine -like "*ftmo*" } | Stop-Process` **silently
   matches nothing** — Windows PowerShell 5.1 `Get-Process` does not expose `CommandLine`. The
   operator sleeps 45 s, sees the book running, and concludes the restart worked **while it is still
   on old code.** Use `Get-CimInstance Win32_Process` (verified: 2 matches).
2. Runbook steps written as `python - <<'PY'` heredocs — **bash syntax in a PowerShell runbook.** They
   will not run as written.

Your runbook must be executable **as written, on Windows PowerShell 5.1, by someone who is not you.**

## Method

Read `PACKET_EMITTER_CARRY.md` §8 before the code — eleven withdrawn entries, including the one where
P published **71,969 still-open positions as completed holds**, a 2.49× overstatement of the exact
number OD-3 turns on, and its own refuter caught it. That is the standard: commission refuters, default
them to "refuted", publish what they overturn.

**Backward compatibility is hard.** 99,112 existing packets are the only live evidence the programme
has. Version the schema; never rewrite the history. And any validator must **fail closed without being
able to stop a live book** — a validator that raises into the decision path is worse than none, and one
that silently drops malformed packets recreates the false-green class.

Use your own judgment on approach, scope, and on whether anything above is wrong for the lineage you
actually find.
