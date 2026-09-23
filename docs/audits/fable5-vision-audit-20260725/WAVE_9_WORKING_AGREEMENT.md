# Wave 9 — working agreement

**Orchestrated by Fable 5, cut 2026-07-30 from the wave-8 evidence.** The standing correction is
unchanged: **the default is that a sleeve can be made to work and your job is to find how.** A
sleeve leaves the queue only parked with its repair list, never killed. If a check would end in
"therefore reject", turn it into "therefore repair X". Verify that your repairs do what you claim.

**Borhen's three standing instructions remain binding verbatim:** (1) use your own judgment — the
commission is a brief, not a script; (2) build, improve, fix — never refute-and-stop; (3) you have
his explicit opt-in for the Workflow tool (multi-agent fan-out) on substantive tasks — wave 8's
sessions used it to catch 21 errors in their own claims before publishing, which is the standard.

Wave 8 changed the map again. Read `phase8/SESSION_AK_SLEEVE_SUPPLY_RESULT.md` §0,
`phase8/SESSION_AH_CONDITIONING_AND_ENTRY_RESULT.md` §0, and
`phase8/SESSION_AI_CHALLENGE_BOOK_RESULT.md` §0 + §2.6 before your own prompt. The one-line
version: the multiplicity family is now a declared artifact (`CANDIDATE_FAMILY_V1.json`, ratchet
enforced); at the sealed α = 0.10 nothing admits yet and **the binding constraint is
`sub_xvol_pullback`'s p on the RECORDED population**; the two moves that close it are banked
prescriptions needing no new data; the entry hour is the FX D1 cohort's lever; and one clock
defect in `BUILT` awaits a re-derivation.

---

## 1. Authority and the live account

1. **Your session prompt.** 2. This agreement. 3. `FOURTH_REVIEW.md` as amended by the wave 6–8
results. 4. `CLAUDE.md` (wave-7 plan position + wave-8 amendments). 5. Everything else.

**FTMO IS LIVE AND TRADING REAL MONEY** — three sleeves via `run_book.py --tags`
(`crypto`, `energy_agri`, `sub_xvol_pullback`), with one **[UNVERIFIED]** condition Session AI
found: if the host's `include_clean3` is false, the armed book generates TWO of those three.
Verbatim from waves 6–8:

- **Do not edit `config/agent_config.yaml`** — the live activation token binds its digest.
- **Never run a broker-capable script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
  `mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`,
  `.tools/monitor_books.py`, `flatten_all_positions.py`,
  `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` succeeds on macOS —
  construction is **not** a safety boundary.
- **Nothing you do touches the VPS.** VPS-side changes ship only as owner-executed carries.
- **H1**: check decision-contract membership before editing anything under `src/`. Read
  `CLAUDE.md` §3's 2026-07-30 LFS amendment before believing any drift count.

## 2. Verification — the committed ZERO baseline

The suite stands at **0 failed / 0 errored** (11,294 passed, 111 skipped-with-reason, 34
strict-xfailed) and the baseline is committed at `receipts/FAILSET_BASELINE_MAIN.json`. Every red
line you produce is a real signal — there is no standing noise left to hide in.

1. **Commit implementation first**, scoped commits, before any capture or long run.
2. **Name your blast radius** with `python3 scripts/pytest_failset.py scope`, run it at HEAD,
   embed the receipt. Verify any suspicious failure at your merge-base — never the full suite.
3. **A strict xfail that XPASSES is a repair announcing itself**: verify the fix is real, then
   close the KEEP-REAL row in `TEST_TRIAGE_V1.json` (disposition `KEEP-REAL-RESOLVED`, with the
   evidence). Wave 8's hydration closed 8 this way on day one.
4. **The full suite is the orchestrator's**, once per merge train, diffed against `baseline`.
5. In a fresh worktree run `python3 scripts/gtos_hydrate_test_data.py` before anything that reads
   research inputs; hydrate `research/operations/trial_budget` before appending to the ledger.

## 3. The trial ledger and the declared family

- Every variant to `research/operations/trial_budget/TRIAL_LEDGER.jsonl` (8,488 look events after
  wave 8; append-only; sparse-hydrate first).
- **The multiplicity family is now an artifact**: `phase8/receipts/CANDIDATE_FAMILY_V1.json`
  (`CANDIDATE_BOOK_V1` = 32, ratchet enforced by `walkforward/candidate_family.py`). Gate runs on
  candidate-book members declare it via the loader — never type a family size by hand. A new
  hypothesis you create joins the family (raises the bill) via a `history` entry; that is
  deliberate and the loader refuses shrinkage.
- The gate corrects at `max(n_judged, declared)` — submitting fewer sleeves cannot shrink the
  bill (`gate.py:797`).

## 4. Machine discipline

Unchanged from wave 8 (§4 there), plus three wave-8 lessons: `build_survivor_book.py`-class
scripts are checked for write-targets **before** running as diagnostics (a diagnostic that can
mutate its subject is not a diagnostic); `spec_sha256` seals are lineage-sensitive — read
`spec._ABSENT_MEANS_UNCHANGED`'s comment before adding any `GateSpec` field; and a fresh
worktree at a merge-base is not a usable A/B for tests that read sparse-excluded artifacts —
hydrate it first or A/B in-worktree.

## 5. Block allocation

Wave 8: AK `B950–B984` · AH `B1000–B1020` · AI `B1050–B1101` — all landed.
**Wave 9: AL `B1150–B1199` · AM `B1200–B1249`.**
Need more? Take the next free 50 above `B1250` and record it. Whoever raises the ceiling past a
sibling's allocation owns `IN_FLIGHT_WAVE_RANGES`.

## 6. What "done" means

Unchanged from wave 8: committed on your branch (never merge to `main`); scoped verification with
receipt; every look in the ledger; blocks appended tagged `[MEASURED]`/`[VERIFIED]`/`[UNVERIFIED]`;
repair-queue rows appended to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` (96 rows standing),
never overwriting, carrying `prescription_in_diagnostics_enum` where one fits.

## 7. Reporting

Numbers over adjectives; failed variants report as their next prescription; cite `file:line`; run
an adversarial pass over your own load-bearing claims before publishing (wave 8's sessions caught
21 real errors this way) and keep what it corrects in the numbers, not a footnote.
