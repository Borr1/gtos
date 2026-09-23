# Session H — `SleeveBookPolicy`

**Phase 2 work item.** Worktree `worktrees/phase2-sleeve-book-policy-20260726`, branch
`phase2/sleeve-book-policy`, from `main`. **Your block range is B90–B99.**

**Read `../WAVE_2_WORKING_AGREEMENT.md` first** — authority, orchestration grant, hard constraints, and
four environment traps found and fixed the night before this wave.

---

## What this is, and why it can run beside the BroadV4 lane

Phase 2 rebuilds the replay around **one decision core hosting N policy modules behind one `Policy`
interface**. That structural amendment exists because of F1: with policy-plural, *"replay measures the
thing that trades"* becomes true by construction for any OD-1 outcome, and E1 can never reopen.

`SleeveBookPolicy` ports the **live book's** semantics: the static sleeve registry, Kelly-lite bins,
cluster collapse, smooth de-risk, gross-cap shedding — the formula chain verified in `AUDIT_STATE.md`. It
is a *different module behind the same interface* from `BroadV4Policy`, so it does not wait on that lane.
The plan writes the work items with arrows; the arrows are narrative order, not a dependency here.

**This is the module that matters most for activation.** OD-1 named the `ultimate_book` W7 book as the
activation candidate, and the second audit's two-stacks finding is that the declared live book is
**unmeasured by any replay**. This is what closes that.

---

## The validation target — and it is unusually good

*"…implemented against the reconciled Phase-0 book with its replay validated against the VPS placement
ledgers / shadow `would_units` packets."*

That evidence is now **local and hash-verified**, which it was not when the plan was written:

| what | where |
|---|---|
| placement ledgers (74), trade records (34) | `/Users/borr/GTOSActive/vps-export-20260725/extracted/` |
| runtime-learning packets — 99,112 across 38 unbroken days | `28_intelligence_timeline/`, `05_shadow_logs/` |
| broker truth, both accounts, every deal | `09_mt5_api/`; `VPS_EXPORT_FINDINGS.md` V5 |
| ticks, both brokers, 2026-06-18..07-24 | `/Users/borr/GTOSActive/vps-ticks-20260726/` |

So the bar is concrete: **your policy, replayed over the shadow window, should reproduce the decisions
the live book actually made.** That is a far stronger test than reproducing a number.

### The sleeve registry — hydrated for you, and there are two copies

`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` is your source of truth for the static
registry. It arrived in this worktree as a **131-byte LFS pointer** and was hydrated on 2026-07-26 —
without that, it would have read as an empty registry and you would have ported nothing.

It differs from the sealed copy in `/Users/borr/GTOSActive/repo` (read-only) — but **only** in
`generated_utc` and its derived `row_hash_sha256`. All 82 rows are otherwise identical, verified
field-by-field. Use your worktree copy with confidence; that is also why the H1 check reports
`drifted=1` here.

---

## The live book has moved under you — twice, this week

Both changes are on `main` and both alter what "reproduce the live book" means. Read them before porting
anything, or you will faithfully reproduce a defect.

1. **B29 Part 1 — the eight deployed sleeves now gate on broker-server hours, not UTC hours.** They were
   mined on the broker-clock archive and were firing 2–3 h late; `ny_crypto_momentum` and
   `kz_london_crypto_low` matched on an exact `(hour, minute)` and hit the wrong bar every day. Each
   sleeve's own `_day()` moved with it. See `src/components/ultimate_book/sleeves/_server_clock.py`.
2. **B56/B58 — the daily-loss reset window is per account.** FTMO resets at **00:00 CE(S)T**; redacted_account
   at **00:00 server time**. Different calendars, 1–2 h apart.

**And one thing deliberately NOT changed, which is squarely your business:**
`bar_provider.decision_day_of` still returns the **UTC** date, and it is the correlated-unit grouping key
— it drives the one-unit-per-cluster-per-day envelope that `book_owner.py:1608-1610` records the dial as
*certified on*. Moving it changes risk bucketing, so it is an owner decision (tracked as B54 Part 2), and
a test pins the current boundary so it cannot shift by accident. **Do not change it in this session** —
but if your work produces the evidence that settles it, that evidence is valuable; write it up for Borhen
as a recommendation with the risk-envelope consequence quantified.

---

## Fidelity is the deliverable — and that is a measurement requirement, not caution

**Port the live semantics exactly, including the parts that look wrong.** This is not a "be careful"
instruction and it is not a limit on your engineering: it is what the module is *for*. The entire value
of `SleeveBookPolicy` is that it measures what actually trades. A policy that silently improves on the
book is no longer a measurement of the book, and it would re-open F1 rather than close it.

So: when you find a defect while porting — and you will — **reproduce it faithfully in the policy, and
record it separately as a finding** with what the correct behaviour would be and what it would be worth.
That register of defects is a genuine deliverable of this session, quite possibly the most valuable one,
and it is where your redesign judgement belongs. Two channels, both wanted; just do not mix them.

The live book currently uses **three different notions of "day"**. Reproducing it faithfully means
reproducing that, not tidying it — but your port must be explicit about which day key it uses for what.

## Method

- **Use the differential harness.** `src/research_infra/replay_differential_harness.py` (Session D,
  B46–B50) takes two arm outputs, localises differences to row and field, fails closed on anything it
  cannot classify, and has a self-comparison null control. Unbound by either contract.
- **Enumerate disagreements; do not summarise them.** A match rate hides the interesting rows. Every
  disagreement between your policy and the live ledger is either a port defect, a live defect, or an
  evidence gap — classify each one.
- `src/components/ultimate_book/**` is **not** contract-bound; `config/agent_config.yaml` and **both**
  FTMO profiles are. Run the H1 membership check before editing anything under `src/`.

## Deliverables — the floor

1. `SleeveBookPolicy` behind the `Policy` interface, with behavioural tests.
2. A validation receipt: its decisions vs the VPS placement ledgers / shadow packets over a sampled week,
   with disagreements **enumerated and classified** rather than summarised as a match rate.
3. The defect register — everything you had to reproduce faithfully but believe is wrong, with the
   correct behaviour and its value.
4. A note on the three day-key notions in the live book and which you used where.
5. `IMPLEMENTATION_STATE.md` blocks **B90–B99**.

Commit scoped work as you go, and push your branch. Do not merge to `main`.
