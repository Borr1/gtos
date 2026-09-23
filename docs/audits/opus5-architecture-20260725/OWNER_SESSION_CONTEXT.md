# Owner Session Context — verbatim direction from Borhen

**This file exists because the most important direction for the next auditor was given in conversation,
not in any document.** It records both sides of the exchange that followed the Opus-5 audit on 2026-07-25.
Borhen's words are quoted directly; the auditor's replies are summarised except where the reasoning
matters.

Read this alongside `ORIGINAL_MISSION_PROMPT.md` in this directory (the original mission; it was a `/gtos-architecture-audit` slash command until 2026-07-26, archived here once the mission completed) and
`.context/00_core/GTOS_ULTRA_GOAL.md` (the controlling charter).

---

## 1. The vision — what GTOS is actually for

**Borhen asked:** *"what do you think my ultimate goal and visions are?"*

The auditor had not read `GTOS_ULTRA_GOAL.md` up to that point and said so. On reading it, the answer:

GTOS is **not a backtester**. Per the charter and the capability map it is a compounding learning machine:
replay at scale → feature store → label store → trained models → default-off runtime intelligence → daily
learning loop → command center → controlled activation → first payout → repeatable payouts → scaling
toward financial independence. **The trading system is the output; the iteration loop is the asset.**

Two lines from Borhen's own charter that the codebase has drifted from:

- *"Profitability is the mission. Truth is its measurement substrate."*
- *"Activation movement is prior to scaffolding. Infrastructure and checkpoints support the mission;
  they do not culminate it."*

**Borhen confirmed the framing** and added that the vision is fully conveyed by the charter plus this
conversation plus the mission prompt.

---

## 2. Compute is not a constraint

**Borhen:** *"if time of compute and fixing the system wasn't a constraint and your ai compute isn't a
constraint in building and fixing the replay and actually having an optimized system in all parts of it to
basically have the right infrastructure so that everything else after it gets easier and faster and
smoother"*

And later: *"ai compute is no issue meaning i can have sessions work and build and do whatever is needed
to get to the goal."*

**Implication for planning:** parallel sessions, exhaustive differential testing, rebuild-and-prove rather
than refactor-and-hope are all affordable. Do not economise on analysis or on verification breadth.

---

## 3. Sequencing — architecture before replays, replays before live

**Borhen:** *"i think what i want to work on is actually make the replays faster so it doesn't make sense
for me to wait for 2 days replay when we can do the work first to get the whole architecture to be
scalable and then we can do the replays"*

And: *"without the conservatism of saying we need to wait 2 days for replay when there can be work to be
done that would make it so much shorter than that, and improve everything that follows substantially
without losing the value of the system and how these replays should tell us about the system and the
intelligence from it to make it even better"*

**Decision:** the remaining April / May / March campaign (~2 days of machine time) is **deliberately
deferred**. Architecture → scale → replays → live.

**Supporting point from the auditor:** the sealed January arms are exactly the regression baseline a
rebuild needs — four factor cells, 15.75 GB of ledgers. There is already enough sealed evidence to do the
rebuild safely. Running more windows now on the old engine adds cost and no safety, and would be re-run on
the new engine anyway.

---

## 4. THE CENTRAL DIRECTIVE — stop patching, build the system

This is the most important paragraph in this file.

**Borhen:** *"the older sessions were doing too much because they were conservative and working around
with wrappers and gates and much much passive behavior rather than building a system that works, it kept
patching like crazy, and that's not what i want to happen with the claude models because you guys are
built differently."*

And: *"i think older stale files kinda create some conservatism due to hard constraints, which i really
don't believe in now, i believe you and the fable model should have your own judgments into doing the work
needed."*

And: *"please make all the changes needed and add everything that needs to be added… let it cook the way
it's made to do, get its full potential with no constraints."*

### The evidence confirms this read exactly

The audit found, independently and before this was said, that GTOS is a museum of default-off patches:

- **The entire ML / learning loop is built and switched off.** See §6 below.
- Selector V4 and Scheduler V4: `enabled: true`, `apply_to_execution: true`,
  `live_activation_allowed: false` → the permission gate at `permissions.py:930` returns `None` for every
  candidate. The gate can never fire.
- `moonshot_default_off_policy_router.py` — misnamed; it *is* the live route, and its own function
  signature defaults to `enabled: False`.
- 179 `moonshot_*` modules, 63,646 lines, **zero** reachability from any entrypoint, 178 of 179 frozen at
  2026-05.
- 21.7 % of 1.33 M Python lines is reachable from a current entrypoint.
- 60.6 % of replay CPU is proof/attribution machinery; 8.3 % decides trades.
- 40 canonical-JSON encoders across 6 signatures; 203 JSONL readers, 94 of which raise on a malformed line
  and 84 of which silently skip it.

**The pattern is not missing capability. It is capability built, gated off, and then patched around.**

---

## 5. Conservatism about going live

**Borhen:** *"i have 3 challenge accounts ready after the building of the system is good so we can take it
live at any moment once we're good with everything and we prove the system is actually good, and by this i
don't mean to limit everything and have 0.1% risk on every trade just to make it good, that's the kind of
conservatism i was talking about, if the weights make sense and all of the architecture from getting the
data to the selector to all the way until the trade happens makes sense, then the conservatism and waiting
and blocking going live won't make sense."*

**Read this precisely.** He is not asking for recklessness. He is rejecting the failure mode where a
system is made to *look* safe by making it trade nothing — shrinking risk to 0.1 %, adding another gate,
adding another shadow layer, deferring activation indefinitely. The bar is: **does the whole chain from
data → market state → candidate → selector → scheduler → risk → order → fill → exit make sense and hold up
under evidence?** If yes, ship it at a real risk level. If no, fix the chain — do not compensate with a
smaller dial.

**Explicit approval given:** *"i do give explicit approval on any changes needed in any part of the
architecture and all of the scaffolding and wrappers and overengineering and basically to get what's
needed and to scale the whole thing, make it good, and go live."*

Note this does **not** extend to setting the risk dial or the allocation profile — those remain Borhen's
call, per `live_system_of_record.md`. It authorises architectural change, deletion, and rebuild.

---

## 6. On whether GTOS has ML — the finding this question produced

**Borhen:** *"im not even sure if what we have is ml but i guess based on the weights we have and the
selection, before this in the codex models it used to do replays gather all the intelligence and see what
trades went right and what went wrong and the missing trades won why this got approved and why this
didn't."*

The auditor checked. **The answer is that the complete learning pipeline already exists and is switched
off.** ~6,600 lines:

| Module | Lines | Non-test importers |
|---|---:|---:|
| `src/research_infra/wave4c_label_store_v2.py` | 1,540 | 1 |
| `src/research_infra/wave4b_feature_store_v2.py` | 1,497 | 1 |
| `src/research_infra/learned_edge_dataset_builder.py` | 770 | 5 |
| `src/research_infra/learned_edge_trainer.py` | 719 | 1 |
| `src/research_infra/learned_edge_walkforward_gate.py` | 570 | **0** |
| `src/components/learned_edge_layer_v4.py` | 489 | 3 |
| `src/research_infra/model_router.py` | 405 | — |
| `src/components/ultimate_book/runtime_learning_packet.py` | 347 | — |
| `src/components/model_pin.py` | 198 | — |
| `src/components/ultimate_book/learning_actuator.py` | 106 | — |

- `selector_v4_learned_edge_enabled` is **absent from every config file**, so
  `selector_v4.py:2388` defaults it to `False`.
- `ultimate_book_runtime_learning_packet_enabled: False` in `ultimate_book/bridge.py:103`.
- `learning_actuator.rerate_book` appears in `admission.py` **only inside comments**.
- `learned_edge_walkforward_gate` has zero non-test importers — fully orphaned.

**And the intelligence Borhen describes is already being captured.** One month, one arm produces:

| Ledger | Rows | What it is |
|---|---:|---|
| missed opportunity | 154,316 | *why this candidate was NOT taken* |
| decision | 69,888 | *why this got approved or didn't* |
| scorecard | 2,016 | ranked option detail |
| orders / trades | 148 / 72 | what actually happened |

So the picture is: **the intelligence is captured, the feature store exists, the label store exists, the
trainer exists, the walk-forward gate exists, the runtime hook exists — and none of it is connected.**
On top of that the capture format (494 KB rows, 1,274 keys, 63.8 % key names) makes the data expensive to
learn from even once it is connected.

This is the single clearest instance of the pattern in §4, and it means the learning loop is far closer
than "build a feature store from scratch" implies.

---

## 7. On running a second independent audit

**Borhen:** *"i want the fable model to do the audit too and audit your audit and see for itself… i want
it to audit everything and give me a plan from its side, i want the implementation in the end for you to
own it."*

And on restrictions: *"i don't mind it going around the repo and finding out what it needs to find out
with no restrictions at all… i don't like the fable model to be restricted in any way… we get all the
value from it rather than half for example just because we told it not to do something."*

And on commits: *"it doesn't have to revert it can do more changes and commit more, it's on the same
branch and worktree and it's free to change anything, there is no reason for it to revert the actual
commits."*

**Operating model:** same branch, same worktree, full freedom, additive work. Implementation ownership
returns to the Opus session afterward — context for how to write the plan, not a limit on what to do.

---

## 8. Hardware truth

The auditor initially assumed an M4 Pro. Verified: **Apple M4 (base), 10 cores (4 performance +
6 efficiency), 16 GB RAM.**

- One replay arm peaks at **14.27 GiB — 89 % of total RAM**. Concurrent arms are impossible today.
- Only 4 performance cores; the replay is single-threaded.
- Per-core speed is good, so the 507-second dense day is already on fast silicon. **This cannot be solved
  with hardware.**
- More RAM (48–64 GB) would buy ~4× via parallel arms, but not the ~30× the learning loop needs.

---

## 9. Errors the first auditor made

Recorded so the successor can calibrate trust, and because Borhen values candour over polish.

1. Did not read `GTOS_ULTRA_GOAL.md` for most of the session despite it sitting in the core context
   directory. Cost the framing of the recommendation, not the findings.
2. Claimed "zero regressions" from a subset test run. An adversarial reviewer found **two real
   regressions**, including a change that broke a test deliberately codifying the opposite behaviour.
3. Documented finding R37 — that editing any of the 42 contract-bound files fails the next replay
   closed — and then edited three contract-bound files anyway, producing exactly the predicted error.

Two adversarial verifier passes changed **four** severity ratings out of twelve claims examined. Assume
more remain.
