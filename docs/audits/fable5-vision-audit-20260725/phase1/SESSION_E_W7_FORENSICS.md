# Session E — W7 live-vs-validation divergence forensics (Gate G1b)

**Phase 1 item 2.** Worktree `worktrees/phase1-w7-forensics-20260726`, branch `phase1/w7-forensics`,
branched from `main`. **Your `IMPLEMENTATION_STATE.md` block range is B60–B69.**

**Read `../WAVE_2_WORKING_AGREEMENT.md` first** — it carries your authority, the orchestration grant,
the hard constraints, and four environment traps that were found and fixed the night before this wave.

---

## Why this one matters more than the others in the wave

`FULL_VISION_PLAN.md`'s starting queue has four items. Three are done. **This is the fourth**, and the
plan says of it: *"OD-1 is conditional on it."* Its standing-risk row is blunter:

> Stack-B evidence does not survive audit (G1b fails) → **OD-1 reopens**; broad-stack + learned lane
> becomes primary; activation timeline extends honestly.

OD-1 is the owner's decision that the **`ultimate_book` W7 book** is the activation candidate. That
decision rests on evidence nobody has audited. You are auditing it.

**Both outcomes are wins, and they are not equally likely a priori — you decide which it is.** A clean
result confirms the programme's direction. A failure is arguably worth more, because it redirects Phase
2's large build before it is spent on the wrong surface. Nothing in this prompt should be read as a
preference for either. The second audit's two-stacks finding is the shape of the risk: the sealed replay
measures a strategy family the go-live dossier ordered off, and the declared live W7 book is unmeasured
by any replay. You hold the only live-execution evidence the modern stack has ever produced.

---

## What the plan asks for

Per-trade join of the VPS ledgers → realized R per sleeve family → attribute the drawdown window across
four axes:

- **(a)** validated core-8 vs same-day-approved candidate / market-expansion sleeves
- **(b)** the 2.0 % ceiling dial vs the dossier's 1.25 % recommendation
- **(c)** execution friction — slippage, spread-blocks, swap — vs the validation's cost model
- **(d)** the FTMO-vs-redacted_account asymmetry on identical signals

**Gate G1b:** every W7 live trade attributed to sleeve + dial + cost with **no unexplained residual**, or
the gaps named exactly.

**On the window's size — check it before you attribute it.** It is usually quoted as "−5.3 % / −3.9 %",
but `SECOND_AUDIT.md:159-160` is more careful than the shorthand: FTMO ≈ −5.3 %, while **redacted_account is a
range, ≈ −3.0 to −3.9 %, because its 06-18 start is not pinned** (pre-halt fleet losses sit on the same
account) — tagged `[VERIFIED snapshots; starts part-inferred]`. Pin the FN start from the broker deal
history in `09_mt5_api/` if you can; if you cannot, carry the range through your arithmetic rather than
collapsing it to a point. Establishing the denominator is legitimate primary work here, not preamble.

---

## Where the evidence is — it is local now, and that is new

The VPS export landed and verified. **Nothing here needs the VPS.**

| what | where |
|---|---|
| pipeline_state, shadow_logs, runtime-learning packets | `/Users/borr/GTOSActive/vps-export-20260725/extracted/` (`04_`, `05_`, `28_`) |
| placement ledgers (74), slippage (70), trade records (34), pending-limit (29) | same tree |
| broker truth — every deal, both accounts | `09_mt5_api/`, and `VPS_EXPORT_FINDINGS.md` V5 |
| broker symbol spec divergence | `research/operations/vps_broker_truth_2026_07_26/` (in-repo) |
| ticks, 2026-06-18..07-24, both brokers | `/Users/borr/GTOSActive/vps-ticks-20260726/` |

In-repo `shadow_logs/` and `pipeline_state/` were restored to your worktree on 2026-07-26 and are a
useful cross-check against the export's copies — if they disagree, that is itself a finding.

**Read `docs/audits/fable5-vision-audit-20260725/VPS_EXPORT_FINDINGS.md` first.** V2, V3 and V5 change
what you can and cannot conclude, and two of them constrain axis (c) directly.

---

## Four traps, each already paid for by someone

1. **The execution ledgers died on 2026-07-02** (V3). `execution_manager_v4_decisions`,
   `broker_order_lifecycle_capture_v4` and `slippage_runtime` have written nothing since. The learning
   loop kept running — 99,112 packets across 38 unbroken days — so *volume* is not *execution evidence*.
   Axis (c) will be **partial**. Establish exactly which days carry execution truth before attributing
   anything to friction, and state the covered fraction in the verdict.

2. **`broker_order_lifecycle_capture_v4.jsonl` has 594 rows, all request-side** (V2). `order_result` is
   absent and deal-cost reconciliation is entirely null. It records intent, never a fill. It is the
   natural broker-truth source and it **cannot** serve as one in its present form.

3. **Every timestamp you touch is suspect until you check it.** Broker epochs are server wall clock, not
   UTC (F7). Use `src/utils/broker_clock.py`. Two live components disagreed about what "day" means until
   yesterday (B56/B58) — if you join a broker deal to a packet on a date key, decide *which* day boundary
   you mean and say so. FTMO's P&L day is **00:00 CE(S)T**; redacted_account's is server midnight;
   `decision_day_of` is still UTC.

4. **redacted_account's opening 100k deposit is deal type 4, not type 2** (V5). A deal-type filter written
   against FTMO's shape silently misclassifies it — and it is 100k, so it will not be subtle.

---

## Method

**Reconcile to broker truth first.** V5 gives balance = equity exactly on both accounts, 269 FTMO deals
and 362 redacted_account deals with commission and swap. If your row set does not reconcile to those totals,
your row set is wrong — not the broker's. Do that before any attribution.

**State residuals as residuals.** G1b's bar is "no unexplained residual, or the gaps named". A named gap
passes; a residual quietly absorbed into a rounding term does not.

**On sample size — this is your call to make, in whichever direction the data supports.** The window is
~10 trading days. Ten days is a thin basis for overturning a 2014–2026 validation, and if that is where
the arithmetic lands, say it plainly with the arithmetic. But small-sample caution is not a default
answer and must not become a way to avoid reporting a real signal: if the attribution shows one sleeve
family, one dial setting, or one broker carrying the loss, that is worth knowing at n=10, stated with its
uncertainty. Run the power arithmetic and let it decide. Do not pre-commit either way — including to
anything implied by this paragraph.

---

## Coordination with Session F — concrete, because "agree early" is not a mechanism

Session F (`worktrees/phase1-divergence-matrix-20260726`) consumes your live-divergence row set and is
running right now in another terminal.

**Within your first working hour**, commit `LIVE_DIVERGENCE_ROW_SCHEMA.md` — the schema alone, no data
required — and `git push origin phase1/w7-forensics`. Tell Borhen you have pushed it.

F has been told to `git fetch origin phase1/w7-forensics` and adopt your schema. **Whoever pushes a
schema first owns it; the other adapts.** If F pushed first, take theirs and adapt — this is a tiebreak
rule, not a negotiation, and it exists so neither of you rewrites at the end.

## Deliverables — the floor

1. `docs/audits/fable5-vision-audit-20260725/GATE_G1B_RECEIPT.md` — the verdict, the four-axis
   attribution, the residual, and the gaps named.
2. The live-divergence row set as a committed artifact, in the shape agreed with F.
3. Measured cost inputs for Phase 6, with their coverage fraction stated.
4. `IMPLEMENTATION_STATE.md` blocks **B60–B69**.

Commit scoped work as you go, and push your branch. Do not merge to `main`.
