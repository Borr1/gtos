# V3-Cascade Prompt — Status Report (2026-04-25)

**Author:** Recovery agent (Opus 4.7 max-effort)
**Trigger:** Final review flagged "SHIP-TUESDAY V3-cascade" as unsupported by code reality.
**Date:** 2026-04-25 (Sunday, 23:55 UTC pre-Monday-deploy)
**Scope:** Step 1-5 of recovery brief. Determine whether `prompts/primary_analyzer_prompt_v3_cascade.py` exists; validate; commit or drop; update CLAUDE.md.

---

## Verdict

**FILE EXISTENCE:** NO — source `.py` does not exist anywhere; only a compiled `.pyc` artifact survived.
**RECOVERABILITY:** YES — full `_SYSTEM_PROMPT_TEMPLATE` recovered via `marshal.load` from `prompts/__pycache__/primary_analyzer_prompt_v3_cascade.cpython-313.pyc` (24,962 chars / 425 lines). Stored at `research/prompt_cascade_ab_test/RECOVERED_v3_cascade_template.py.txt`.
**VALIDATION VS A14:** UNVERIFIABLE — A14's `raw_results.jsonl`, `run_summary.json`, and any A/B numerical outputs are all missing; only A14's `runner.cpython-313.pyc` survived. No "10% flip rate, no G1-G4 leaks" claim can be confirmed against extant data.
**SHIP-AGAINST-PRODUCTION-V3:** WOULD REGRESS — cascade prompt was drafted on a stale single-framework V3 baseline (~55,254 bytes, pre-2026-04-25-morning), but production V3 is now 69,535 bytes with `fvg_fill` + `breaker_re_entry` standalone frameworks activated this morning (commits `1340f56`, `64d05b8`). Cascade prompt's `## FRAMEWORK` section literally says "OB Retest framework ONLY. Ignore all other framework references." — shipping it would actively disable two newly-deployed frameworks.

**RECOMMENDATION:** **DROP-TUESDAY-PLAN.** The Tuesday-deploy was based on a Sunday-morning A3 draft that has since been superseded by Monday-morning production V3. Even if A14's A/B numerical outputs were preserved, they were measured against a different prompt architecture (single-framework) than what is now LIVE.

---

## Step 1 — File-existence verification

Searched exhaustively:

| Search | Result |
|---|---|
| `find . -name "primary_analyzer_prompt_v3_cascade.py"` (entire repo) | **0 hits** |
| `find . -iname "*cascade*"` (entire repo, all extensions) | 2 hits: the orphaned `.pyc` + the empty `research/prompt_cascade_ab_test/` directory |
| `git log --all --oneline -- "prompts/primary_analyzer_prompt_v3_cascade*"` | **0 commits** anywhere on any branch |
| `git stash list` | 5 stashes, all pre-cascade-era (latest is `83f665c`, session 31) |
| `git fsck --lost-found` | 17 dangling commits + many dangling blobs; none contain cascade content (verified by content scan) |
| `git log --all --diff-filter=D` for deleted cascade files | **0 hits** |
| `.claude/worktrees/*/prompts/primary_analyzer_prompt_v3_cascade.py` | **0 hits** across all 22 worktrees |
| `.claude/worktrees/staging-sunday/` | Has V4_DRAFT but no cascade |

The `.pyc` artifact's metadata reports the original `.py`: 55,254 bytes, modified Sat Apr 25 03:12:06 2026 UTC, located at `C:/Users/MSI/Documents/ai-trading-agent/prompts/primary_analyzer_prompt_v3_cascade.py`. The .pyc itself was compiled 2026-04-25 11:15:17 UTC (= 19:15 +0800 Sunday evening). Between those two timestamps the source file was overwritten or removed. No backup, stash, branch, or worktree retained a copy.

A3's referenced diff document `research/cascade_prompt_diff.md` also does not exist on disk. `research/vision_program_2026-04-25/01_RETAIL_VS_INSTITUTIONAL_FOOTPRINT.md` (cited in the cascade prompt's docstring) also does not exist. Both A3 deliverables are lost.

---

## Step 2 — Validation against A3 / A14 expectations

Recovered the cascade prompt's `_SYSTEM_PROMPT_TEMPLATE` (25 KB) by `marshal.load`-ing the .pyc and inspecting `code.co_consts[22]`. Recovered docstring confirms A3's stated diff philosophy (PRESERVED bit-exact: C1/C2/C3 gates, R1-R8, G1-G5, NO FOURTH GATE, STRICT RULE—H1 POI SOURCE, SELF-CHECK 1-6, TRADE PARAMETERS, PRECISION, output schema. ADDED: `## MECHANISM CONTEXT` preamble with Osler 2003/2005 + Cont-Kukanov-Stoikov 2014. LIGHTLY REFRAMED: `## FRAMEWORK` paragraph + `displacement_quality` rubric).

Spot-checked recovered template against the docstring's promises:

| Checkpoint | Status |
|---|---|
| `## MECHANISM CONTEXT` block (lines 5-15) | PRESENT — 110 words, cites the three papers |
| R1-R8 enumerated NO_TRADE allow-list | PRESENT, bit-exact vs production V3 |
| G1-G5 forbidden block | PRESENT, bit-exact |
| C1/C2/C3 three-gate decision rule | PRESENT, bit-exact |
| STRICT RULE — H1 POI SOURCE | PRESENT, bit-exact |
| STRICT RULE — NO FOURTH GATE | PRESENT, bit-exact |
| TRADE PARAMETERS / PRECISION / SELF-CHECK | PRESENT, bit-exact (numeric thresholds preserved) |
| Output JSON schema | PRESENT, bit-exact |
| `## FRAMEWORK` cascade-mechanism reframe | PRESENT — single sentence "post-cascade mean-reversion to pre-cascade equilibrium" |
| `displacement_quality` rubric inline gloss | PRESENT — labeled as "cascade SIGNATURE — the body/ATR ratio the cascade carved" |

So the recovered cascade prompt does match A3's diff philosophy as documented. **What is unverifiable** is A14's A/B comparison output. The runner script (`runner.cpython-313.pyc`, also recovered via marshal) was designed to call 60 evaluations (30 MSOs × 2 arms = control V3 + v3_cascade) using A2's exact MSO sample manifest. But the run outputs (`raw_results.jsonl`, `run_summary.json`, `run_progress.log`) are all missing on disk, never committed, and not in any worktree. The brief's claim of "10% flip rate, no G1-G4 leaks, recommended SHIP-TUESDAY" cannot be substantiated — it may be true, may be embellished, may be agent fabrication. Per agent reliability rule #2 ("no fabricated numbers"), I cannot treat A14's verdict as evidence.

### Critical: cascade prompt is structurally STALE vs production V3

Beyond the missing A14 outputs, there is a hard architectural problem:

| File | Size | `## FRAMEWORK` section | Active frameworks |
|---|---|---|---|
| `prompts/primary_analyzer_prompt_v3_cascade.py` (recovered from .pyc, drafted ~Sunday 03:12 UTC) | 55,254 bytes | "OB Retest framework ONLY. Ignore all other framework references." | 1 (`ob_retest`) |
| `research/v4_prompt_engineering/v3_prompt_snapshot.py` (V4-engineering's V3 snapshot) | 49,302 bytes | Same single-framework `## FRAMEWORK` section | 1 (`ob_retest`) |
| `src/prompts/primary_analyzer_prompt.py` (production V3, HEAD) | 69,535 bytes | `## FRAMEWORKS (UP TO THREE STANDALONE PATHS)` with FW1/FW2/FW3 + Step A-E decision order + dedicated `## FVG_FILL FRAMEWORK` block + `{breaker_re_entry_section}` placeholder | 3 (`ob_retest`, `fvg_fill`, `breaker_re_entry`) |

Production `agent_config.yaml` confirms: `enabled_frameworks: ["ob_retest", "fvg_fill", "breaker_re_entry"]`. Two of these were activated **after the cascade prompt was drafted**, by commits `1340f56` (fvg_fill, 2026-04-25 18:19 +0800 / 10:19 UTC) and `64d05b8` (breaker_re_entry, 2026-04-25 18:30 +0800 / 10:30 UTC). The cascade .pyc was compiled at 11:15 UTC — slightly after the multi-framework merges, but its `.py` source file is dated 03:12 UTC, before the merges, meaning the `.pyc` was a recompile of a stale `.py` that never got rebased.

If the recovered cascade prompt were committed and shipped Tuesday, it would:
1. Replace the multi-framework V3 with single-framework V3, silently disabling fvg_fill and breaker_re_entry (which were CEO-approved + canary-cleared this morning).
2. Cause framework decision-routing in `primary_analyzer.py` to misalign with prompt instructions — the runtime code paths for fvg_fill / breaker_re_entry are still active, but the AI would never emit those framework values because the prompt forbids them.
3. Almost certainly fail the 60-fixture canary on any borderline fixtures whose intended framework is `fvg_fill` or `breaker_re_entry` (analogous to V4 DRAFT's 6 baseline flips per CLAUDE.md item #13).

A14's A/B test (assuming it ran) was MSO-based, not framework-based — it tested whether cascade-vs-V3 produced different decisions on 30 MSOs from A2's manifest. It did NOT test against the multi-framework V3 currently in production, and could not have, because that V3 didn't exist when the test ran.

### Surgical diff that would still be needed

Even if we accept A3's "surgical" framing, to ship cascade Tuesday would require:
1. Re-create the `.py` file from the recovered template (mechanical, ~10 min).
2. Rebase the cascade prompt onto current production V3 (manual, 1-2 hours): port the MECHANISM CONTEXT preamble + the cascade-reframe sentence in `## FRAMEWORKS` (FW1 description) + the displacement_quality gloss, while preserving all FW2/FW3 logic.
3. Re-run 60-fixture canary against the rebased prompt.
4. Re-run A14's A/B (60 calls × $X) against the rebased prompt to confirm flip rate stays bounded.
5. Re-validate Council pre-reg gates.

Total cost: ≥ 4 hours engineering + ≥ $20-50 API budget. With Monday FTMO challenge starting tomorrow, this is unworkable.

---

## Step 3 — Decision

**Options considered:**

(a) Re-implement from A3's brief (= rebase cascade prompt onto multi-framework V3 + re-run A14): **REJECTED** — 4+ hours work + ≥$20 API + canary risk on the eve of Monday challenge violates the CEO's existing risk posture (V4 + LIRA both shelved on Sunday for similar "not enough validation time" reasons; cascade is the same shape of decision).

(b) Re-dispatch a small agent to re-draft from scratch: **REJECTED** — same time/cost concerns + the original A3 brief was based on a vision_program document that itself does not exist on disk. We would be writing fiction to support fiction.

(c) Drop Tuesday cascade-prompt deploy entirely; keep V3 production: **CHOSEN.** V3 production is the empirically-best Monday prompt per CLAUDE.md item #13 (DP1 100% self-consistency, V4 SHELVED, LIRA SHELVED). Adding a cascade-mechanism preamble is a research-mechanism polish, not an edge-recovery move. Edge concerns dominate (XAUUSD H2-2026 decay, item #9), and v2 detector promotion is already the chosen response to that concern.

**Recommendation:** DROP-TUESDAY-PLAN. The cascade prompt is preserved as a research artifact for future reattempt (post-Monday, post-v2-stability-check, after rebase against multi-framework V3).

### What I am committing
- `research/cascade_prompt_status_2026-04-25.md` (this report).
- `research/prompt_cascade_ab_test/RECOVERED_v3_cascade_template.py.txt` (recovered SYSTEM_PROMPT_TEMPLATE for future reference; saved as `.txt` not `.py` to make accidental import impossible).
- CLAUDE.md item #13 update — appended cascade-prompt status note.

### What I am NOT committing
- `prompts/primary_analyzer_prompt_v3_cascade.py` reconstructed source — would be a stale single-framework artifact in a directory that overrides production `src/prompts/`.
- The orphaned `.pyc` files. (They are gitignored by `.gitignore`'s standard `__pycache__/` pattern; leaving them in place does no harm. Removing them would risk masking the historical evidence trail.)

---

## Step 4 — Commit decision

No code commit is being created for the cascade prompt itself. Only:
- This report file.
- The recovered template (as `.txt`, in `research/`).
- A documentation update in CLAUDE.md.

---

## Step 5 — CLAUDE.md item #13 status note

Will append the following bracketed status to CLAUDE.md item #13:

> **Cascade prompt addendum (2026-04-25 23:55 UTC):** A3's draft `prompts/primary_analyzer_prompt_v3_cascade.py` exists ONLY as an orphaned `.pyc` artifact (no `.py` source on disk, no commit on any branch). A14's A/B outputs (`raw_results.jsonl`, `run_summary.json`) are also missing. Brief's "SHIP-TUESDAY V3-cascade" plan is **DROPPED**. Recovered template at `research/prompt_cascade_ab_test/RECOVERED_v3_cascade_template.py.txt`; status report at `research/cascade_prompt_status_2026-04-25.md`. The recovered cascade prompt is structurally stale vs current production V3 (drafted on single-framework V3 baseline, but production now has fvg_fill + breaker_re_entry frameworks activated 2026-04-25 by `1340f56` + `64d05b8`). LOST-IRRECOVERABLE for Tuesday; rebase + re-run A14 is post-Monday research candidate if CEO wants to revive.

---

## Risk assessment

| Risk if dropped | Magnitude |
|---|---|
| Lose any expected-value uplift the cascade-mechanism preamble would have given | LOW. A14's claimed +0.0R (test was for "no regression," not edge-uplift). MECHANISM CONTEXT is mechanism-pedagogy not gate. |
| Burn A3's engineering effort | LOW. The recovered template is preserved; future rebase trivial. |
| Optics of "we said we'd ship and didn't" | LOW. CEO greenlit shelving V4 and LIRA on Sunday for similar reasons; cascade is consistent with that posture. |

| Risk if shipped as-is (recovered template, no rebase) | Magnitude |
|---|---|
| Silently disable fvg_fill + breaker_re_entry frameworks | HIGH. CEO-approved + canary-cleared this morning; reverting would erase real work. |
| Canary regression on multi-framework fixtures | HIGH. V4 DRAFT had 6 baseline flips for analogous reasons; cascade likely worse. |
| Misalignment between prompt allow-list (`ob_retest` only) and runtime framework router | MEDIUM. Could cause silent filter-cascade increases. |
| Confidence in A14's A/B outputs (which are missing) | UNVERIFIABLE. Per reliability rule #2, treat as non-evidence. |

Risk-asymmetry strongly supports DROP-TUESDAY-PLAN.

---

## Final words

The Final Review's flag was correct: this was a paper-trail gap with no shippable artifact. The recovery exercise has surfaced two systemic concerns worth noting for future sessions:

1. **Sub-agents shipping `.pyc` without `.py`.** A3 wrote the cascade prompt, ran A14's A/B against it (likely in-process by importing the module and triggering Python's pyc compilation), and then either crashed or returned without committing the source. The `.pyc` was the only durable evidence. Future research dispatches should explicitly require committing the source `.py` before any test execution.

2. **Methodology fragility for prompt experiments.** A14's A/B output files all live in `research/prompt_cascade_ab_test/` with no commit hook. If the agent is killed, all numerical evidence is lost. The neutral-test (A2) sister directory has the same problem — `prompt_neutral_test/` also has only `.pyc` artifacts and no committed reports. Recommend a tooling fix: every research-runner script should write to `git add`-able paths and commit on completion, or be wrapped by a shell that does so.

These are post-Monday concerns. Tonight's action is a clean DROP. Production V3 ships as-is for the Monday FTMO challenge.

— Recovery agent, signing off.
