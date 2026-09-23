# GTOS Phase 1, Session A — the shadow reducer, and the first economics check GTOS has ever had

You are an implementation session for GTOS. Phase 0 is complete and Gate G0 is met. Work on branch
`phase1/shadow-reducer` in **`/Users/borr/GTOSActive/worktrees/phase1-shadow-reducer-20260726`** — your own worktree, already
created and sparse-configured. Push with `GIT_LFS_SKIP_PUSH=1 git push -u origin phase1/shadow-reducer`.

**Do not work in `worktrees/claude-opus5-architecture-audit-20260725` and do not commit to `main`.**
Two sibling sessions are running concurrently in their own worktrees; sharing one would collide on the
git index and on the `shadow_logs/` and `pipeline_state/` trees the suite writes into. Merge to `main`
per `.context/00_core/parallel_goal_merge_playbook.md` when your gate is met.

Two other sessions may be running in parallel on the clock repair and the red suite. Your work touches
neither.

---

## 1. Read order

1. `CLAUDE.md` — root briefing, hazards H1–H7. **H1 was rewritten**: the contract of record is now
   **R2**, 43 bound paths.
2. `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — the resumable checkpoint.
   B1–B25 are measurements that **supersede** numbers both audits carry. Trust them over the audits.
3. `docs/audits/fable5-vision-audit-20260725/GATE_G0_RECEIPT.md` — what Phase 0 established and, in
   §6, the nine gaps it did not.
4. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` §1 (verdict E3) and §3.5 — the exact
   finding you are acting on.
5. `docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md` — Phase 1, items 1 and 3.
6. Preflight per `CLAUDE.md` §2.

---

## 2. The finding you are acting on, stated precisely

The second audit's verdict on E3 is the sharpest thing in either audit:

> The route analyzer **does** independently re-sum economics from ledger rows with per-row identity
> checks (`pnl_cash == risk_cash × net_r` @1e-6; stress recompute @1e-8) — better than the first audit
> credited. **But nothing anywhere recomputes a trade's R from prices**: the analyzer contains zero
> `entry_price` / `exit_price` / `stop_loss` references, so an engine-side per-trade R defect is
> certified by the whole chain.

Read that twice. ~54,000 lines of proof code attest **byte custody**, not economic correctness. The
two questions that decide whether GTOS makes money — *does the measured system predict the trading
system?* and *are the numbers right?* — are both unanswered. You are answering the second one.

**Build:** a standalone reducer, roughly 400–600 lines, **zero imports from `src/`**, that takes
entry / exit / stop prices and costs straight from the trade, order and oracle ledgers and
independently recomputes per-trade R and the five headline aggregates. Zero engine imports is the
whole point — a reducer that imports the thing it checks proves nothing.

Run it over all four sealed January arms **and** the April partial (16 sealed days of S1R1).

**Gate G1a:** agreement with the analyzer within float tolerance, **or a filed economic defect**.
Either outcome is a win. A disagreement is the more valuable result and you should be actively hoping
for one — do not tune your reducer until it agrees.

---

## 3. What you need to know before you start

**Where the sealed evidence is.** `/Users/borr/GTOSActive/repo` and
`worktrees/replay-accel-engine-20260719` are the owner's other checkouts and are **read-only** to you.
The January arm ledgers are ~15.75 GB. Read; never write there.

**The sealed January economics, so you can sanity-check your own output.** From
`B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_SOURCE_REPAIRED_R3_CAP_R2_MATRIX_AUDIT.json`:

| Arm | scoreable_net_cash | scoreable risk cash | q = net/risk |
|---|---:|---:|---:|
| S0R0 neutral/fixed | −201.31 | 8,800 | −0.023 |
| S1R0 quality/fixed | −550.60 | 7,500 | −0.073 |
| S0R1 neutral/dynamic | −5,432.33 | 39,881 | −0.136 |
| S1R1 incumbent | −6,596.06 | 36,778 | −0.179 |

Every arm lost money. If your reducer reproduces those signs and magnitudes, that is a real
corroboration. If it does not, **that is the finding** — file it, do not explain it away.

**Two traps in the ledger data itself:**

- **F17** — the replay's `normalize_row` silently coerces unparseable OHLCV to `0.0` and drops
  bad-time rows (`v4:4640-4667`). A `0.0` price in a ledger may be a coercion artifact rather than a
  real value. Your reducer must distinguish "price is zero" from "price was unparseable" and refuse
  rather than compute through it.
- **F7 (clock)** — every research timestamp is broker time labelled UTC, 2–3 h off. **This does not
  affect R recomputed from prices** — a price is a price. It *does* affect anything you attribute to a
  session or a time-of-day bucket. Session B is repairing it; do not wait for them, just don't build
  session-conditioned claims into your output.

**Contract safety.** Your reducer is a new file with no engine imports, so it is not contract-bound
and cannot drift anything. Run the `CLAUDE.md` §3 check before touching anything under `src/` anyway.

---

## 4. Second task — close the three live-path test gaps (plan Phase 1 item 3)

Small, and they protect surfaces that currently have nothing:

1. **SHORT-side `_compute_r` has zero coverage (F12).** `orchestrator.py` around `:10248-10255`.
   Every `actual_r` assertion in the repo is `direction="LONG"` — a sign flip in the SHORT branch
   flips no assertion anywhere. The LONG side is well covered (`tests/test_exit_wiring.py:405,238,475`
   carry hand-computed values through the real `_finalize_exit` chain); mirror that for SHORT with
   hand-computed numbers, not values read back from the implementation.
2. **The two unprotected sizing surfaces.** Sizing is otherwise genuinely well tested — a positive
   surprise the audit recorded — but **profile-overlay multipliers** and **account-currency
   conversion** have nothing. The profiles disagree on NAS100 (2×) and US30_cash (0.5×) between
   `ftmo.yaml` (replay) and `redacted_account.yaml` (live), so an overlay defect changes live size silently.

   **Sharpened 2026-07-26 by the server export** (`VPS_EXPORT_FINDINGS.md` V4): the two brokers'
   **contract specs differ on 18 of 19 shared symbols** — `trade_contract_size` on every index CFD and
   ETHUSD, and JP225 differs in `digits`/`point`/`trade_tick_size` as well. So position size is a
   product of *profile multiplier × broker contract size*, and the two disagree independently. Real
   specs are in `/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api/BROKER_SYMBOL_SPEC_COMPARISON.json`
   — write the test against those rather than against an assumed shared contract size.
3. **A live-config-truth test.** Assert which gates are *actually* live, so E1c-class facts are pinned
   by CI instead of rediscovered by archaeology every audit. Note F8: `live_activation_allowed=false`
   *disables a rejection gate* on the V4 path (`permissions.py:930` returns `None`) but *suppresses
   placement* on the book path. One flag name, two contradictory meanings — pin both.

---

## Method — use the orchestration

The owner has explicitly authorised multi-agent workflows. Use them. This programme's two live-risk
defects were found by a 28-agent adversarial pass, not by careful reading, and its worst wrong answers
came from one mind checking its own work.

Where a workflow earns its place here:

- **Ledger archaeology.** Order rows are 494 KB with 1,274 keys and you need entry/exit/stop prices out
  of five arm-windows. One agent per ledger family, in parallel, each returning the exact field path and
  provenance for the quantities you need. This is the part that will otherwise eat your session.
- **Per-arm recomputation.** Five arm-windows are independent — pipeline them rather than serialising.
- **Adversarial verification of a disagreement.** If your numbers differ from the analyzer's, that is a
  finding worth three independent agents trying to kill before you file it. If they cannot, it is real.

Before you claim your gate is met, run agents briefed to **refute with `file:line`**. Every review pass
in this programme has overturned something the session was confident about.

## Anti-drift — this task has a characteristic way of going wrong

**Fixing the ledgers instead of reading them.** You will find schema ugliness. It is not yours to
repair — your job is to read what is there and recompute R independently. A reducer that needed the
ledgers changed to work has not checked anything.

**Tuning until it agrees.** If your numbers differ from the analyzer's, that is the *result*, not a bug
in your reducer. Establish which is right; do not adjust until the disagreement disappears.

**Importing from `src/`.** Zero engine imports is the entire point. A reducer that imports the thing it
checks proves nothing.

## 5. Working rules

- **A/B every change** with `scripts/pytest_failset.py capture` + `diff` against
  `docs/audits/fable5-vision-audit-20260725/receipts/baseline_full_suite.json`. Compare failure
  **sets**, never counts — a count comparison already produced one wrong "refuted" verdict in this
  programme (B10 → B11).
- **Run the whole suite for the A/B, not a scoped subset.** Phase 0 had three regressions that passed
  in isolation *and* alongside the file that looked like the cause; only the full diff caught them.
- Never run the suite without `--continue-on-collection-errors`; the tool pins this. Without it the
  run aborts at collection, executes **zero** tests, and still exits like a completed run.
- **Never execute broker-capable scripts**: `fn_smoke_trade.py`, `mt5_preflight.py`,
  `dual_broker_execution_follower.py`, `run_agent.py`, `run_book.py`, `start_all.bat`,
  `.tools/monitor_books.py`. C1: `create_mt5("live")` **succeeds** on macOS — the ImportError only
  surfaces on `.connect()`, so construction is not a safety boundary.
- **Do not fabricate a number.** This session's entire output is numbers. If a value cannot be
  computed from the ledgers, say so and name the missing input.
- Prefer behavioural tests over source-string assertions.
- Before declaring G1a passed, run an adversarial subagent briefed to **refute with `file:line`**.
- Report faithfully: failed tests with output, skipped steps named, "done" means verified.

**Traps that have already cost time here:**

- `zsh` applies `:t`/`:s` history modifiers inside `git show $V:path` and **silently returns the wrong
  thing**. Use `git cat-file -p "${V}:path"`.
- `rg -r` is `--replace`, not "recursive". Use `rg -n`.
- **Do not delete a module from `sys.modules` and re-import it.** It creates a second module object,
  and `multiprocessing` then refuses to pickle functions from it — this broke three unrelated replay
  tests in Phase 0 and only showed up in a full-suite run.
- `tests/test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration` is
  **non-deterministic** (pass/pass/fail over three identical runs). It can appear on either side of a
  diff meaning nothing.

**Scope discipline.** ~330 research-bookkeeping and ~56 artifact-existence failures are stale, in the
deletion tier, and **must not be repaired** — Session C owns that question. If you find yourself
fixing a test outside the live surface or your own reducer, stop.

---

## 6. Deliverables

- The reducer, its output over five arm-windows, and a one-page verdict: does the analyzer's economics
  survive an independent recomputation from prices?
- The three tests from §4.
- An update to `IMPLEMENTATION_STATE.md` with your measurements tagged
  [MEASURED]/[VERIFIED]/[INFERRED]/[HYP], and a **declared-gaps section** — saying "I did not establish
  X" is a required output, not a failure.
- A G1a gate receipt in the same shape as `GATE_G0_RECEIPT.md`.

**Escalate to the owner only for:** risk dial, allocation profile, broker-real activation; a genuinely
external dependency; or a falsification that changes the plan. If your reducer contradicts the sealed
analyzer, that is exactly such a falsification — report it immediately and plainly rather than
resolving it yourself.
