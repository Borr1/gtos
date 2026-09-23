# Session AC — the pre-arming carry, authored against the live lineage

**Activation critical path.** Worktree `worktrees/wave5-activation-carry-20260729`, branch
`phase5/activation-carry`, from `main`. **Blocks B550–B579.**

**Read `../WAVE_5_WORKING_AGREEMENT.md` first** — especially §3.

---

## What this unblocks

Borhen has approved arming a **live funded FTMO account** on four sleeves at 2.0 % nominal. Three
defects stand between here and that, all of them present on the running host, and **all three land in
a single restart** — which is also the restart that finally activates the token gate (the books have
been running since **2026-07-04**, before the gate existed).

You are building that carry package. You cannot reach the VPS; the orchestrator applies it.

## The three items

**1. The strand fix — `src/components/execution.py`.**

`_normalize_volume` computes `math.floor((lots - volume_min) / volume_step)` on a raw binary quotient.
`(0.03 - 0.01) / 0.01` is `1.9999999999999996`, so **0.03 lots normalizes to 0.02**, and the close
gate at `_close_request_execution_geometry` refuses any close whose normalized volume differs from the
request. Nine close producers route through it; the live book always takes that branch; **all nine
return before the activation layer**, so the token design's never-strand guarantee never gets a say.
The retry recomputes the same volume forever.

**33 of 300** two-decimal lot sizes at `(0.01, 0.01)`; **44 of 327** real close deals. Reproduced on
the VPS with the host's own interpreter. The mainline fix is Session T's, on `main` — epsilon inside
the floor plus a never-round-up guard, 22 tests, reverting fails 7.

**On the VPS this file is at `:2552` and is 10,166 lines against mainline's 10,085 — it has changes
mainline does not have.** Do not copy the file.

**2. B56 — the daily-loss reset rule. This is the one that can breach a funded account.**

FTMO's rule is **00:00 CE(S)T**. Its MT5 server runs the **US** DST calendar
(`America/New_York + 7 h`, measured over 81 weekly boundaries). redacted_account resets at **00:00 server
time**. Three clocks; a fixed offset expresses none of them.

The VPS governor anchors to **server midnight for both accounts**. Mainline's own B56 comment states
what that means:

> "**early** for FTMO — the dangerous direction, since for that 1-2 h each night the governor
> believed the daily-loss budget had reset while FTMO was still counting losses against the previous
> day."

Measured on the host: `_effective_offset_h` present but **no** `reset_rule`, **no** `europe_prague`,
**no** `CE(S)T`; `src/utils/broker_clock.py` **absent entirely**. And the rule is written down in the
VPS's own profile at `operator_profile.yaml:104` — `daily_reset_time: 00:00 CE(S)T` — where the
running code cannot read it.

**The carry looks clean and you must confirm that rather than trust it:**
- `src/utils/broker_clock.py` imports **stdlib only** — a new file, no dependencies.
- `governor_state.py` needs the rule-aware `_effective_offset_h`; VPS 250 lines vs mainline 296.
- `book_engine.py:111-113` reads `governor_daily_reset_rule` **or falls back to**
  `prop_safe_selector_daily_reset_timezone` — which the VPS FTMO profile **already sets** to
  `Europe/Prague` at `:87`. So this should be **code-only, no config edit, no H1 exposure.**
  **Verify that claim before relying on it**; if a config key is needed after all, say so loudly,
  because both FTMO profiles are decision-contract-bound.

Two dates that make this time-bound: the CE(S)T-vs-US calendar mismatch window opens **2026-10-25**
(2 h error), and `monitor_books.py`'s hardcoded `SRV_OFFSET_H = 3   # FTMO/FN server = UTC+3 (EEST)`
breaks on **2026-11-01**, when both servers drop to +2. Mainline already replaced that hardcode;
**decide whether `monitor_books.py` belongs in this carry** and justify either answer. It is on the
never-execute list — carrying its source is not running it.

**3. Session S's packet carry.** Already authored against `redacted_host` with zero-fuzz diffs, a
`MANIFEST.json`, `verify_carry.py` and a runbook — on branch `phase4/packet-unblock`, being merged to
`main` by Session U as you start. **Do not re-author it.** Your job is to *compose* it with items 1
and 2 into one package and one restart, and to check the three don't interact badly.

## Local inputs already fetched for you

`<scratchpad>/vps_lineage/` holds the **live host's own** `governor_state.py`, `book_engine.py` and
`execution.py`, pulled read-only today. Diff against those, not against `main`. If you need another
file from the host, say which and the orchestrator fetches it.

## What "done" looks like here

**Surgical diffs that apply with zero fuzz against the VPS lineage** — the shape Session I used, and
the reason its carry applied clean on five files. Plus:

- a `MANIFEST.json` with before/after SHA-256 for every touched path
- a `verify_carry.py` that checks the applied state **behaviourally**, not by grep — for item 2 that
  means asserting the reset instant for a known UTC timestamp inside a mismatch window, both
  accounts, and for item 1 that every broker-valid volume round-trips
- **a rollback that can actually pass its own gate** — S found one that told a correct operator not to
  restart
- a PowerShell 5.1 runbook, executable **as written, by someone who is not you**

## Runbook defects found on that host — do not reproduce them

1. `Get-Process python | Where-Object { $_.CommandLine -like "*ftmo*" }` **silently matches nothing**:
   Windows PowerShell 5.1 `Get-Process` does not expose `CommandLine`. The operator sleeps, sees a
   book running, and concludes the restart worked **while it is still on old code**. Use
   `Get-CimInstance Win32_Process`.
2. `python - <<'PY'` heredocs are **bash syntax in a PowerShell runbook**. They will not run.
3. The books run `.venv-gtos\Scripts\python.exe` (**3.13.13**), not PATH `python` (3.11.15). Every
   `python ...` line in the wave-3 runbooks tested the wrong interpreter.
4. **There are two repo trees on that host**, differing in 25 `src` files. All 10 live processes run
   from one. Derive the repo root from the running book, and make it a STOP if it is ambiguous.
5. Session S found this same wrong-interpreter defect in Session I's `STAGE0_VPS_RUNBOOK.md` — a
   live-safety runbook. If your reading of the tree finds more of these, fix them and say so.

## The ordering question is yours, and it is real

Three changes, one restart, a funded account. **Which order, and what is the state if the operator
stops halfway?** S's ordering table rated a catastrophic case as survivable because it traced a
`TypeError` at the emit call site and never asked whether control reaches it — it doesn't;
`book_owner.py:32 → packet_guard.py:46` fails at **module load**, and 14 of 16 partial-copy
permutations die at startup. **The supervisor only ever *starts* a missing book, never stops one** —
so a module-load failure is a 5-minute restart loop with `manage_open_positions` off on any open
position.

Enumerate the partial states. Say which are safe to stop in and which are not.

## What is NOT yours

Do not touch the VPS — you cannot reach it and must not try. Do not arm anything, mint a token, or
flip a gate. Do not run a broker-capable script (agreement §1). Do not merge to `main`.

## Method

**Commission refuters and default them to "refuted."** Distinct lenses: one on partial-application
states, one that tries to break the rollback, one on whether the B56 carry is really config-free,
one on whether your diffs actually reconstruct the shipped files byte-identically.

**Reproduce the defects before fixing them.** Both are reproducible locally from the fetched lineage
files. A carry authored against a defect you have only read about is how the packet block happened.

Use your own judgment on packaging, ordering, scope, and on whether anything above is wrong.
