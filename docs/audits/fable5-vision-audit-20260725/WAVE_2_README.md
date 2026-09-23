# Wave 2 — four concurrent sessions (2026-07-26)

Launched from `main` @ `a78c66ea8`, which carries **everything** from wave 1 (sessions A–D), the
integration review, the D1 demotion, the sleeve clock repair and the per-account reset rule.
A/B'd at **507 bad → 507 bad, zero regressions**.

| Session | Item | Prompt | Worktree · branch | Blocks |
|---|---|---|---|---|
| **E** | Phase 1 item 2 — **W7 forensics, Gate G1b** | [`phase1/SESSION_E_W7_FORENSICS.md`](phase1/SESSION_E_W7_FORENSICS.md) | `phase1-w7-forensics-20260726` · `phase1/w7-forensics` | **B60–B69** |
| **F** | Phase 1 item 4 — divergence matrix v2 | [`phase1/SESSION_F_DIVERGENCE_MATRIX.md`](phase1/SESSION_F_DIVERGENCE_MATRIX.md) | `phase1-divergence-matrix-20260726` · `phase1/divergence-matrix` | **B70–B79** |
| **G** | Phase 2 — columnar source layer | [`phase2/SESSION_G_COLUMNAR_SOURCE.md`](phase2/SESSION_G_COLUMNAR_SOURCE.md) | `phase2-columnar-source-20260726` · `phase2/columnar-source` | **B80–B89** |
| **H** | Phase 2 — `SleeveBookPolicy` | [`phase2/SESSION_H_SLEEVE_BOOK_POLICY.md`](phase2/SESSION_H_SLEEVE_BOOK_POLICY.md) | `phase2-sleeve-book-policy-20260726` · `phase2/sleeve-book-policy` | **B90–B99** |

Paste into each session:

```
Read docs/audits/fable5-vision-audit-20260725/phase1/SESSION_E_W7_FORENSICS.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase1/SESSION_F_DIVERGENCE_MATRIX.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase2/SESSION_G_COLUMNAR_SOURCE.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase2/SESSION_H_SLEEVE_BOOK_POLICY.md and follow it.
```

**All four prompts open by requiring [`WAVE_2_WORKING_AGREEMENT.md`](WAVE_2_WORKING_AGREEMENT.md)**,
which carries the shared authority grant (full engineering latitude, explicit standing approval to use
subagents and the Workflow tool, deliverables-as-floor, judgment outranks the prompt), the hard
constraints, and the four environment traps below.

## Four environment defects found and fixed before launch (2026-07-26)

Each would have cost a session hours, and two would have produced *wrong* results rather than slow ones.

1. **The two contract-bound sleeve ledgers were 131-byte LFS pointers in all four worktrees.**
   `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` is the static registry **Session H exists to
   port** — it would have read as an empty registry. Hydrated offline in all four.
2. **The H1 membership check reports `drifted=1`, and it is a false alarm.** The registry ledger differs
   from R2's expected hash in exactly `generated_utc` and its derived `row_hash_sha256`; all 82 rows are
   otherwise identical to the sealed copy in `/Users/borr/GTOSActive/repo`, verified field-by-field. Every
   session runs this check first; all four prompts now say a *second* drifted path is the real signal.
3. **`shadow_logs/` (132 files) and `pipeline_state/` (104) were entirely absent** from the sparse
   worktrees. Restored — 28 MB, `git status` still clean.
4. **94 LFS pointers remain** under `research/` and `data/`. A pointer read as data is indistinguishable
   from an empty result. Documented with the offline `git lfs checkout` recovery.

## Why these four, and why concurrently

**E is the one that matters most.** `FULL_VISION_PLAN.md`'s starting queue has four items; three are
done and E is the fourth. Its own note: *"OD-1 is conditional on it."* If G1b fails, the owner's
decision about which surface is the activation candidate reopens — much cheaper to learn now than
after Phase 2's build is spent.

**F depends on E only partially.** The matrix has three inputs; two (E1, F7) are available today. F
builds the generator and schema now and takes E's live-divergence rows when they land. **E and F should
agree that row schema early.**

**G and H are independent of both and of each other.** G is infrastructure (the H3 memory ceiling: one
arm peaks at 8.61 GB of 16 GiB, which is why replays are serial today). H is a policy module behind the
same interface as `BroadV4Policy`, so it does not wait on that lane.

**`BroadV4Policy` is deliberately held back** for a second wave. It is the Gate G2 lane, and it is
better started once E has said whether OD-1 still stands.

## The one conflict wave 1 produced, and how it is prevented

All four wave-1 sessions independently numbered their findings from **B27**, so there were four
different B29s and three sections had to be renumbered at merge. Hence the assigned ranges above.
Everything else merged with **zero code conflicts**.

## Shared state

- **Baseline:** the wave-2 worktrees are **sparse checkouts** and will show **~684**, not the 507 quoted
  for a full checkout — the ~177 delta is missing evidence fixtures, not broken code (B39). Every session
  captures its **own** baseline in its **own** worktree first, and A/Bs failure *sets* against that.
  Never compare a count across worktrees.
- **A/B is mandatory** before any "no regressions" claim: `scripts/pytest_failset.py` capture → diff.
  **Sets, not counts.** Two tests are known-flaky under load (B30) — diff two runs before believing a
  small regression.
- **Contract of record: R2**, 43 bound paths. Run the H1 membership check (`CLAUDE.md` §3) before
  editing anything under `src/`. `config/agent_config.yaml` and **both** FTMO profiles are bound.
- **Python:** `/opt/homebrew/bin/python3`.
- **Read-only to every session:** `/Users/borr/GTOSActive/repo`, `worktrees/replay-accel-*`.
- **Never execute broker-capable scripts.** `create_mt5("live")` succeeds on macOS — the ImportError
  only surfaces on `.connect()`, so construction is not a safety boundary.
- **Do not merge to `main`.** Commit on your branch; integration is done deliberately, once.

## What each session should read first

`CLAUDE.md` (rewritten 2026-07-26 for this wave), then `IMPLEMENTATION_STATE.md` **B1–B58**, then the
prompt. `VPS_EXPORT_FINDINGS.md` matters most to E and H.
