# Wave 3 — five concurrent sessions (2026-07-27)

Launched from `main` @ `1e95fe7fa`, which carries **everything**: wave 1 (A–D), wave 2 (E–H), the
third review and its 22 receipts, the integration A/B receipt, and the corrected `CLAUDE.md`.
Wave-2 integration A/B'd at **695 bad → 695 bad by failure set, 0 regressed, +145 net new passing
tests**.

**This wave executes `THIRD_REVIEW.md` §4 — Stage 0 and most of Stage 1 — approved in full by Borhen
on 2026-07-27.** It ends at **OD-3, the activation-candidate decision.**

| Session | Stage item | Prompt | Worktree · branch | Blocks |
|---|---|---|---|---|
| **I** | 0.1 + 0.2 — **the safety spine** | [`phase3/SESSION_I_SAFETY_SPINE.md`](phase3/SESSION_I_SAFETY_SPINE.md) | `wave3-safety-spine-20260727` · `phase3/safety-spine` | **B100–B109** |
| **J** | 1.1 — **broker-truth layer** | [`phase3/SESSION_J_BROKER_TRUTH.md`](phase3/SESSION_J_BROKER_TRUTH.md) | `wave3-broker-truth-20260727` · `phase3/broker-truth` | **B110–B119** |
| **K** | 1.3a — **generation port, K1, G4** | [`phase3/SESSION_K_GENERATION_PORT.md`](phase3/SESSION_K_GENERATION_PORT.md) | `wave3-generation-port-20260727` · `phase3/generation-port` | **B120–B129** |
| **L** | 1.4 + 0.4 — **evidence packs + January bank** | [`phase3/SESSION_L_EVIDENCE_PACKS.md`](phase3/SESSION_L_EVIDENCE_PACKS.md) | `wave3-evidence-packs-20260727` · `phase3/evidence-packs` | **B130–B139** |
| **M** | 1.5 + §6.3 — **hygiene + corrections** | [`phase3/SESSION_M_HYGIENE.md`](phase3/SESSION_M_HYGIENE.md) | `wave3-hygiene-20260727` · `phase3/hygiene-batch` | **B140–B149** |

Paste into each session:

```
Read docs/audits/fable5-vision-audit-20260725/phase3/SESSION_I_SAFETY_SPINE.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase3/SESSION_J_BROKER_TRUTH.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase3/SESSION_K_GENERATION_PORT.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase3/SESSION_L_EVIDENCE_PACKS.md and follow it.
Read docs/audits/fable5-vision-audit-20260725/phase3/SESSION_M_HYGIENE.md and follow it.
```

All five prompts open by requiring [`WAVE_3_WORKING_AGREEMENT.md`](WAVE_3_WORKING_AGREEMENT.md).

---

## Why these five, and why concurrently

**All five are independent.** That is the point of this wave's composition. The plan's real serial
chain is `1.1 → 1.2 → 1.3b` (broker truth → re-cost → survivor replay out-of-window), and none of
those second and third links are in this wave. Everything here can start now.

**I is item 0 of the entire plan.** The VPS is a running, funded, connected host with `trade_allowed`
true on both terminals, and its whole brake is three false YAML booleans with **nothing watching
them**. The activation token exists on mainline and not there. Half a day of work converts a standing
hazard class.

**J unblocks the economics.** Nothing in Stage 1.2 can happen until one function owns every cost
number. F38 — zero commission at five sites — is why the only positive validation in the tree is
invalid rather than trustworthy.

**K is the keystone.** It is the session most likely to change what GTOS does next, because G4 has two
opposite answers and nobody knows which is true. If the five silent high-confidence sleeves were silent
from a *generation defect*, the book has never actually been tried.

**L is the cheapest decision-value in the plan** — three owner decisions converted from opinion to
measurement in seconds of compute each, over evidence already banked.

**M makes the tree the other four land on trustworthy**, and closes D-1, the only backlog item that
gets worse with time.

**Deliberately not in this wave:** Stage 1.2 (the re-cost) waits for J's layer; Stage 1.3b (survivor
replay out-of-window) waits for both. Those are wave 4.

## Two disciplines that are new, and apply to every session

From the review's overfitting analysis, in `WAVE_3_WORKING_AGREEMENT.md` §3:

1. **Placebo is automatic, not optional.** Of every book-level improvement in the record, exactly one
   passed its own random-drop placebo. The large exciting one failed at **p = 0.59 and was activated
   anyway.** Any claim of improvement now carries its null control in the same receipt.
2. **Out-of-sample windows are a budgeted resource.** March stays outcome-unread. A window read for
   hypothesis generation can never later confirm that hypothesis. Reading one is recorded in blocks.

## Environment — preflighted 2026-07-27 before launch

The four wave-2 traps recur in every fresh worktree. All five were fixed before these sessions start:

1. **The two contract-bound sleeve ledgers arrived as 131-byte LFS pointers** — hydrated offline in all
   five (registry 205,754 B; join ledger 5,995,223 B). A pointer read as data is indistinguishable from
   an empty result.
2. **The H1 check reports `drifted=1` and it is a known false alarm** — the registry ledger differs from
   R2 only in `generated_utc` and its derived `row_hash_sha256`; all 82 rows otherwise identical. **A
   second drifted path is the real signal.** 43 bound paths checked.
3. **`shadow_logs/` (132) and `pipeline_state/` (104) were absent** from the sparse profile — restored;
   `git status` clean in all five.
4. **~4,150 LFS pointers remain.** Recover offline with `git lfs checkout <path>`; the object store is
   local.

## Shared state

- **Baseline:** capture your **own** in your **own** worktree first and A/B failure *sets* against it.
  These are sparse checkouts; counts are not portable across worktrees. **Commit your capture summary**
  — the wave-2 A/B was run and not committed, so to the next reader it did not exist.
- **Contract of record: R2**, 43 bound paths. Run the H1 membership check before editing under `src/`.
  `config/agent_config.yaml` and **both** FTMO profiles are bound.
- **Python:** `/opt/homebrew/bin/python3`.
- **Read-only:** `/Users/borr/GTOSActive/repo`, `worktrees/replay-accel-*`.
- **Never execute broker-capable scripts.** `create_mt5("live")` succeeds on macOS — construction is not
  a safety boundary. The VPS is live and funded; anything touching it is an owner-executed runbook.
- **Do not merge to `main`.** Integration is done once, deliberately, with an A/B.

## What each session reads first

`CLAUDE.md` (rewritten 2026-07-27) → `THIRD_REVIEW.md` §0, §1, §4 and the §5 verdict on the session
yours continues → `WAVE_3_WORKING_AGREEMENT.md` → the prompt. `VPS_EXPORT_FINDINGS.md` matters most to
I, J and K.
