# Wave 7 — working agreement

**Orchestrated by Fable 5 from 2026-07-30.** Wave 6's §0 correction stands in full and is not
restated as a mood: **the default is that a sleeve can be made to work and your job is to find
how.** A sleeve leaves the queue only after its enumerated repair paths are shown to fail, and
"leaves" means parked with its repair list, never killed. If a check would end in "therefore
reject", turn it into "therefore repair X". Verify that your repairs do what you claim — that is
where the rigour points, not at manufacturing grounds for rejection.

Wave 7 is the repair wave: wave 6 built the diagnostic head and walked the estate through it
(`phase6/receipts/REPAIR_QUEUE_V1.json`, 84 rows over 32 members, every row with evidence).
You are executing prescriptions, with numbers.

---

## 1. Authority and the live account

1. **Your session prompt.** 2. This agreement. 3. `FOURTH_REVIEW.md` (the controlling plan).
4. `CLAUDE.md`. 5. Everything else — historical unless a current artifact says otherwise.
If your prompt and a repo document conflict, follow the prompt and say so in your report.

**FTMO IS LIVE AND TRADING REAL MONEY** — armed 2026-07-29 on `crypto`, `energy_agri`,
`sub_xvol_pullback` via `run_book.py --tags`. Therefore, verbatim from wave 6:

- **Do not edit `config/agent_config.yaml`** — the live activation token binds its digest
  (`ffe16657feaf`); one byte stops the armed book placing.
- **Never run a broker-capable script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
  `mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`,
  `.tools/monitor_books.py`, `flatten_all_positions.py`,
  `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` *succeeds* on macOS — the
  ImportError only surfaces on `.connect()` — so construction is **not** a safety boundary.
- **Nothing you do touches the VPS.** VPS-side changes ship only as owner-executed carry
  packages in the AC lane.
- **H1**: check decision-contract membership before editing anything under `src/`
  (`CLAUDE.md` §3, R2 contract). The walkforward / validation_integrity / learning surfaces
  are unbound — W, R and V each verified their lanes — but check anything new you touch.

## 2. Verification policy — CHANGED. Read this even if you ran a wave-6 session.

**The full-suite session A/B is retired.** The measurement that retired it: across 16 full-suite
A/B runs on 2026-07-29, five reported a REGRESSION and all five were load flakes; zero real
regressions were caught by the count. The two genuine catches came from reading failure lists.
Meanwhile Session AT is re-shaping the suite itself (B900–B949), so the standing number will
move under you and a full-suite diff against a stale base is noise by construction.

What replaces it:

1. **Commit your implementation first**, in scoped commits, before any capture or long
   measurement run. (Four of five wave-5 sessions exited mid-capture; the work survived
   because they committed first.)
2. **Name your blast radius** in your result doc: the test files/directories that cover what
   you touched — tests you added, plus tests importing the modules you changed. Run **that
   scope, at your HEAD**. It must come back green except for failures already standing at your
   merge-base — verify a suspicious failure by running the *same scope* at the base (cheap,
   because it is scoped), not the whole suite.
3. **Any suspected regression is re-run in isolation at HEAD and at base before you believe
   it.** This rule caught all five false alarms and it stays. `scripts/pytest_failset.py`
   separates LOAD-FLAKE from REGRESSED; extend `KNOWN_LOAD_FLAKES` only with the evidence its
   docstring demands.
4. **The orchestrator runs one full-suite capture per merge train** and diffs by failure set
   against the previous main capture. That is where the whole-suite net lives now. Sessions do
   not run the full suite at all.
5. **Sets, not counts.** Counts are not portable between worktrees or across AT's deletions;
   only sets are.

## 3. The trial-budget ledger is mandatory, and it is running

Every variant you evaluate — every sweep cell, every re-walk, every exit policy, every family
member — is logged to the ledger (`validation_integrity/trial_budget_ledger.py`, prospective
half live since AA; the shared artifact is `research/operations/trial_budget/TRIAL_LEDGER.jsonl`,
append-only JSONL, safe for concurrent sessions). Admission statistics deflate against the
measured count. **1,643 look events are already in it.** No variant is forbidden and nothing
waits; the ledger is what lets aggression and honesty coexist.

## 4. Machine discipline

- **Memory is the binding constraint, not CPU.** Four sessions share this machine. Before an
  archive-scale generation or re-simulation, check free memory (`vm_stat`); if another
  session's heavy phase is peaking, chunk your run or wait. Never wait on a machine-wide
  condition (wave 5 lost 5.5 h to `pgrep -f pytest` polling) — scope every wait to your own
  worktree by path.
- **Reuse AA's substrate before regenerating.** `phase6/receipts/AA_ESTATE_TRADES.json.gz`
  carries every walked trade with its intent (entry_utc, entry_price, sl_distance_price,
  direction, target_dist, timeframe, exit_policy) and its path stats. Exit re-simulation from
  stored intents + the bars archive costs minutes; AA's full generation cost 10,736 s. Only
  regenerate when the repair changes *generation* (wider stops changing R geometry, new
  symbols, changed thresholds).
- **Bars and ticks are broker wall clock, not UTC**, whatever the field is named. Convert with
  `src/utils/broker_clock.py`; it fails closed on an unregistered server. The bars archive is
  outside the repo at `/Users/borr/GTOSActive/vps-bars-20260727/`, ticks at
  `/Users/borr/GTOSActive/vps-ticks-20260726/`.
- **Sparse-checkout lies.** A file can be committed on your branch and absent from your tree
  with `git status` clean. `git ls-files -v <path>` shows it; `git sparse-checkout add`
  hydrates it. LFS pointers read as corruption and as H1 drift: `git lfs checkout <path>`
  first.
- **Lineage matters.** When you compare replay to live, state which commit each side ran.

## 5. Block allocation

Wave 6: AA `B600–B649` · AB `B650–B699` · AG `B700–B749` · AT `B900–B949`.
**Wave 7: AD `B750–B799` · AF `B800–B849` · AE `B850–B899` · AK `B950–B999`.**
Need more? Take the next free 50 above `B1000` and record it in your result doc.

## 6. What "done" means

1. Implementation **committed on your branch** — do not merge to `main`.
2. The §2 scoped verification, with the scope named and the receipt embedded in your result doc.
3. Every trial logged to the ledger (§3).
4. Blocks appended to `IMPLEMENTATION_STATE.md`, tagged `[MEASURED]` / `[VERIFIED]` /
   `[UNVERIFIED]` — append only; never renumber another session's blocks.
5. **Repair-queue updates append, never overwrite.** Add your rows beside AA's with your
   session id; the queue is a shared artifact and its history is part of the evidence.

## 7. Reporting

State what you measured, what you repaired, and what you got wrong and withdrew. Cite
`file:line` for production-state claims. **Never report a rejection as a headline: if a variant
fails, the headline is the next prescription.** A repair that does not work is a result — say
what you tried, what it cost, and what would be next. Numbers over adjectives, and give Borhen
the number that would let him decide something, not the caveat that would let nobody decide
anything.
