# Session K — The generation port, the K1 gate, and G4

**Stage 1 item 1.3a. The keystone of the plan.** Worktree `worktrees/wave3-generation-port-20260727`,
branch `phase3/generation-port`, from `main` @ `1e95fe7fa`. **Your block range is B120–B129.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## The missing half

Session H ported the live book's **decision** side behind the `Policy` protocol and validated it hard:
zero disagreements over **617 unit-bearing live cycles**, 130 of 132 transmitted risk percents
reproduced. Read `src/research_infra/replay_policy/sleeve_book.py`, its validation receipt, and
`IMPLEMENTATION_STATE.md` B90–B99e before you write anything — you are extending that work, not
restarting it.

What H deliberately excluded (its B91) is **candidate generation**: bars → sleeve intents. That
exclusion is why the live book is still, today, **unmeasurable end-to-end**. The decision layer can be
replayed; the thing that decides *what there is to decide about* cannot.

**You close that.** After this session the declared-live surface is fully measurable for the first time
in the programme's history, and F1 — the two-stacks finding, that the sealed replay measures a strategy
family the go-live dossier ordered off — closes at full strength.

## G4, and why it may be the most important number in the wave

Here is the finding that reopened the owner's activation decision, from Sessions E and H jointly:

- **Zero of 145 placements over 38 unbroken days came from any train-validated sleeve** (B99b).
- **43.4 %** of placements came from sleeves the registry itself marks `breadth_falsified`.
- Weighted mean confidence of what actually traded: **0.2312**, against a registry mean of **0.4875**.
- `metals_core` — confidence **1.00**, the registry's self-described *"deepest anchor"* — **placed
  nothing**, and ran a **2-of-6 symbol universe** because four of its declared symbols are absent from
  both live profiles.
- Only **11.5 %** of core-8's 3.90 confidence weight ever placed a single trade (B63).

**G4 is the question: were the five silent high-confidence sleeves silent because of natural signal
frequency, or because of a generation defect?**

Those are opposite worlds. If it is frequency, the book is honest and slow, and the activation
conversation is about cadence and account choice. If it is a defect, the book has never been tried, its
2015–2026 validation was never actually deployed, and the fortnight that triggered OD-1 measured
something that is not the book at all.

**Nobody knows which.** Your port is the instrument that answers it — replay the live window through
the book from bars and count generation per sleeve. The G1b receipt §9 names exactly this as *"what
would actually settle OD-1."*

## K1 — the acceptance gate, and it is strict on purpose

**Reproduce the 617 unit-bearing live cycles end-to-end from bars — generation + decision + units — at
zero disagreements, through Session D's differential harness.**

Not "high fidelity." Not a match rate. **Zero, or an enumerated and classified list of every
disagreement** with each one attributed to a port defect, a live defect, or an evidence gap. A match
rate hides exactly the rows that matter.

Use `src/research_infra/replay_differential_harness.py` — it localises differences to row and field,
fails closed on anything it cannot classify, and has a self-comparison null control. It is unbound by
either contract. Two sessions have now used it as their correctness instrument, so start there rather
than building a second one — **but it was built for arm-vs-arm comparison, and you are comparing a
port against a live ledger.** If it does not fit that shape, extending it or replacing it is your call
and a legitimate deliverable; what would be wasteful is rebuilding what it already does well.

**And heed B99e, now a standing rule:** *a validated port measured by an unvalidated comparator is not
a validated result.* Budget a comparator-refutation pass. Session H learned this the hard way and it is
the reason its receipt is trusted.

## Fidelity is the deliverable, and it is a measurement requirement

**Port the generation semantics exactly, including the parts that look wrong.** The entire value of this
lane is that it measures what actually trades. A port that silently improves on the book stops being a
measurement of the book and re-opens F1 instead of closing it.

When you find a defect while porting — and you will — **reproduce it faithfully, and record it
separately** with what correct behaviour would be and what it would be worth. Two channels, both wanted,
never mixed. Session H's `SLEEVE_BOOK_DEFECT_REGISTER.md` (D0–D12) is the format and the precedent.

**Two live changes landed under you this month.** Read them or you will faithfully reproduce a bug that
was already fixed:

1. **B29 Part 1** — the eight deployed sleeves gate on **broker-server hours, not UTC**. They were
   firing 2–3 h late; `ny_crypto_momentum` and `kz_london_crypto_low` matched an exact `(hour, minute)`
   and hit the wrong bar every day. See `src/components/ultimate_book/sleeves/_server_clock.py`.
2. **B56/B58** — the daily-loss reset window is **per account** (FTMO 00:00 CE(S)T, redacted_account 00:00
   server time).

And one deliberately **not** changed and squarely your business: `bar_provider.decision_day_of` still
returns the **UTC** date and is the correlated-unit grouping key. Moving it changes risk bucketing, so
it is an owner decision (B54 Part 2). **Do not change it** — but if your work produces the evidence that
settles it, that evidence is valuable; write it up with the risk-envelope consequence quantified.
The live book uses **three different notions of "day"**. Reproduce that; be explicit about which key you
use where.

## Inputs

- **Bars/ticks:** `/Users/borr/GTOSActive/vps-ticks-20260726/` — 1.9 GB, both brokers, 2026-06-18..07-24,
  191.9 M rows, sha256-verified. **`time` and `time_msc` are broker wall clock, not UTC.** Every file
  carries a `.timebase.json` saying so. Convert with `broker_clock.broker_epoch_to_utc`.
- **The live truth to reproduce:** placement ledgers (74) and trade records (34) at
  `/Users/borr/GTOSActive/vps-export-20260725/extracted/`; 99,112 runtime-learning packets across 38
  unbroken days in `28_intelligence_timeline/` and `05_shadow_logs/`; broker truth for every deal in
  `09_mt5_api/`.
- **The registry:** hydrated for you (205,754 B, 82 rows). Note H's D12 — an earlier prompt of mine
  named this ledger as the *static registry* and was **wrong**; the real registry is Python literals at
  `admission.py:154`. This ledger is `...ultimate_candidate_package.sleeve_registry.v1` and contains
  **zero live sleeve names**. Verify before relying on either.
- **Sleeve census:** the live book is **29 sleeves** — core-8 + 9 candidate + 12 market-expansion, via
  `admission.effective_registry()`.

## The out-of-window replay is Stage 1.3b and it needs Session J

Replaying the survivor book over 2024–2026 at cost-true prices needs the broker-truth layer (Session J,
running concurrently) and the re-cost's survivor definition (Stage 1.2, next wave). **Do not wait for
either.** Build the port, pass K1, answer G4 — those are self-contained and they are the wave's
highest-value output. If J's layer lands in time, take it; if not, keep the cost interface abstract so
1.3b is a wiring job rather than a rewrite.

## Deliverables — the floor

1. The generation port behind the `Policy` protocol, with behavioural tests.
2. **K1 receipt**: 617 cycles end-to-end from bars, disagreements enumerated and classified, harness
   output, comparator-refutation pass.
3. **G4 answered**: per-sleeve generation counts over the live window, with the verdict — frequency or
   defect — argued from the counts, and `metals_core`'s 2-of-6 universe quantified as a counterfactual.
4. A defect register in H's format for everything you reproduced faithfully but believe is wrong.
5. A note on which day-key you used where.
6. `IMPLEMENTATION_STATE.md` blocks **B120–B129**, and a full-suite A/B by failure set, committed.

Commit scoped work as you go, push your branch, do not merge to `main`.
