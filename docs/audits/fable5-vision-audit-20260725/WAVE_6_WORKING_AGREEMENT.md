# Wave 6 — working agreement

**The programme changed on 2026-07-29.** Read §0 before your prompt; it is the reason this wave
exists and it overrides habits the previous five waves trained into you.

---

## 0. The standing correction — build, do not kill

Borhen's words, and they are an instruction rather than a mood:

> the option of them not working is simply not allowed from me, i dont allow deactivating any of
> them without doing all the effort needed to either fix what's wrong or tweak it to be right or
> build on top of it, the process of killing ideas just like that, would eventually lead to a
> ferrari that is parked in the garage but no we use a volvo because it's safer from accidents.

He is right, and it is evidenced: **this programme built a killing machine and never built a fixing
machine.** Every instrument it produced — the admission gate, the refuters, the multiplicity
correction, the brake-only learning rule — is a rejection instrument. None answered *"what would
make this work?"*

**The burden of proof is inverted for this wave.** The default is that a sleeve **can be made to
work** and your job is to find how. A sleeve may only be set aside after its repair paths are
enumerated and shown to fail — and "set aside" means **parked with its repair list**, never killed.

**On verification.** This does not mean stop checking. It means: check that *your repairs do what
you claim*; do not commission an adversary whose job is to find a reason a sleeve should not trade.
**If a check would end in "therefore reject", turn it into "therefore repair X".**

Two proofs the approach pays, both from 2026-07-29:

- `metals_core` sat at 58.7 % cost coverage against a 60 % floor — recorded as NOT_EVALUABLE for
  want of four tick files. Exporting them (239 MB, ~1 hour) took coverage to **100 %** and produced
  a real answer. It happened to be a genuine reject, and that is worth far more than the guess.
- Session Y found K1-b's 19 % first-of-day recall was **a code-lineage artefact, not a port
  defect** — K1-b compared two different programs. Under the matching lineage the seven sleeves go
  **18.6 % → 100 %**, 175 intents recovered, 0 newly missed. Nine sleeves were classed unjudgeable
  on a broken comparison.

## 1. Your authority

Full control of repo changes on this laptop. Implement, verify, commit.

**Not yours:** strategic trading decisions — risk dial, allocation profile, sleeve composition,
admission thresholds — are Borhen's. And **nothing you do touches the VPS.**

**FTMO IS LIVE AND TRADING REAL MONEY**, armed 2026-07-29 12:55 UTC on three sleeves — `crypto`,
`energy_agri`, `sub_xvol_pullback`. **Do not edit `config/agent_config.yaml`**: the live activation
token binds its digest (`ffe16657feaf`) and one byte stops the armed book placing.

**Never run a broker-capable script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
`mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
`flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` *succeeds*
on macOS — the ImportError only surfaces on `.connect()` — so construction is **not** a safety
boundary.

## 2. Authority order

1. **Your session prompt.** 2. This agreement. 3. `FOURTH_REVIEW.md` (the controlling plan).
4. `CLAUDE.md`. 5. Everything else — historical unless a current artifact says otherwise.

If your prompt and a repo document conflict, follow the prompt and **say so in your report.**

## 3. The trial-budget ledger is mandatory, and it is not a brake

A repair campaign is a large multiple-testing exercise by construction. **Every variant you
evaluate — every sweep point, every re-walk, every parameter neighborhood — is logged to
`validation_integrity/trial_budget_ledger.py`** (built, tested, never run). Final admission
statistics deflate against the *measured* trial count instead of the assumed floor of 128 that
`gate.py:47-48` itself flags as *"a number nobody measured"*.

**No repair is slowed, no variant forbidden, nothing waits.** This is the difference between "we
tried 400 things and the ledger says the survivor still clears deflation" and "we tried 400 things
and reported the best one" — the second is how this programme admitted a candidate book that failed
its own placebo at p = 0.59.

## 4. What the orchestrator got wrong, so you catch it faster

Assume the same failure modes are in *your* prompt. All evidenced:

| # | what happened |
|---|---|
| 1 | **Claims stated as facts that measurement refuted.** Fable's fourth review corrected the orchestrator's own census on **five** counts: `idxrev` is gross **+0.006 on n=6,473**, not negative; `metals_ob_micro` is **n=7**, never measured; `fx_jpy` is net-positive at its measured live carry; the carry data had **already landed**; and `xlayer_veto_gate` already ships live as the `leader_impulse_veto` overlay. |
| 2 | **Absence concluded from a malformed probe — four times in one day.** `rg -r` misuse "proved" a walk-forward module didn't exist (it did, 15 modules, 94/94 green). A raw `mt5.symbol_info` call bypassing `symbol_map.py` reported two live sleeves untradeable (both full surface). A regex demanding a quote PowerShell never emitted reported `tags=(none)` on a correctly armed book. A grep requiring line-start reported merged blocks missing. **When your probe says something surprising, suspect the probe first.** |
| 3 | **Two sessions fixing the same module.** X and Z both fixed `regime_inflation.py`'s sign defect; the hand-merge parsed and was internally inconsistent (5 `NameError`s) until the tests caught it. **Say so in your first commit message if you touch a shared instrument.** |
| 4 | **Four of five wave-5 sessions exited while their A/B was still running.** The work survived because they committed first. **Commit your implementation before you start the capture.** |

## 5. Environment traps

- **Sparse-checkout lies.** A file can be committed on your branch, absent from your tree, and
  `git status` still clean. `git ls-files -v <path>` shows it; `git sparse-checkout add` hydrates it.
- **LFS pointers read as corruption and as H1 drift.** `git lfs checkout <path>` first. A large
  share of the ~660 standing failures is **data absence, not broken code**.
- **Memory is the binding constraint, not CPU.** Check free memory before a full-suite run.
- **Never wait on a machine-wide condition.** Session T left a shell polling
  `until [ $(pgrep -f pytest | wc -l) -eq 0 ]` for **5.5 hours** — unsatisfiable with other sessions
  running. Scope every wait to your own worktree by path.
- **Bars and ticks are broker wall clock, not UTC**, whatever the field is named. Convert with
  `src/utils/broker_clock.py`; it fails closed on an unregistered server.
- **Lineage matters.** Y's whole finding was that two "identical" programs differed by one module.
  When you compare replay to live, state which commit each side ran.

## 6. Block allocation

Waves 3–5: `B100–B576` (see `WAVE_5_WORKING_AGREEMENT.md` §4 and `IMPLEMENTATION_STATE.md`).
**Wave 6: AA `B600–B649` · AB `B650–B699` · AG `B700–B749` · AT `B900–B949`.** 50 each — repair
campaigns generate more findings than audits. Need more? Take the next free 50 above `B900` and
record it.

**AT recorded its own allocation here, per that sentence, and checked the ceiling before writing.**
Writing past a gap turns every unwritten allocation below the new ceiling into a dangling citation
— the mechanism `tests/test_implementation_state_block_citations.py` documents at length, and the
reason `IN_FLIGHT_WAVE_RANGES` exists. Measured before appending: ceiling 720, and the only
citations that would fall under a ceiling of 949 are `B900` itself (defined by AT's first block)
and `B969` (safely above). AA's `B600–B649` was already covered by its in-flight entry, and AG's
`B700–B749` is written. **No `IN_FLIGHT_WAVE_RANGES` edit was needed; the guard passes 8/8.**

## 7. What "done" means

1. **Committed on your branch** — implementation first, *then* the A/B. Do not merge to `main`.
2. **A/B by failure set, full-suite, captures embedded**:
   `python3 scripts/pytest_failset.py receipt <before> <after> -o <receipt.md>`. Counts are not
   portable between worktrees; only sets are.
3. **Any claimed regression is re-run in isolation at both HEAD and base before you believe it.**
   Three wave-5 "regressions" were pre-existing flakes.
4. **H1: check decision-contract membership before editing under `src/`** (`CLAUDE.md` §3).
5. **Blocks appended to `IMPLEMENTATION_STATE.md`**, tagged `[MEASURED]` / `[VERIFIED]` /
   `[UNVERIFIED]`.
6. **Every trial logged to the ledger** (§3).

## 8. Reporting

State what you measured, what you repaired, and **what you got wrong and withdrew**. Cite
`file:line` for production-state claims. Never report a rejection as a headline: if a sleeve fails,
the headline is the prescription.

**A repair that does not work is a result** — say what you tried, what it cost, and what would be
next. That is different from "this sleeve is dead", and the difference is the whole wave.
