# Fourth review — the build mandate

**For Fable 5. Commissioned by Borhen, 2026-07-29, after FTMO went live.**

You have written three reviews for this programme. The third one changed it and was approved in full.
This one is different in kind: **you are not being asked to audit. You are being asked to plan the
build.**

Read §1 in full and verbatim before anything else. It is the owner's own words and the orchestrator's
answer, and it is the reason you are here.

---

## 1. The conversation that commissioned you — verbatim

**Orchestrator, presenting the state of the sleeve estate, with confidence levels:**

> | question | confidence |
> |---|---|
> | We can **judge** all 37 within those sessions | **high, ~85%** |
> | A **meaningful number beyond the current 4** survive | **low, ~20%** |
> | More than **one or two** additional sleeves survive | **~10%** |
> | The current **4 are genuinely profitable forward** | **~50%. Coin-flip, and I won't dress it up** |
> | The puzzle resolves to *"a small book or nothing"* | **high, ~75%** |
>
> **The reasoning behind the low numbers:** every time this programme has tested something
> rigorously, the answer came back negative. […] That is not a pattern that usually reverses when you
> test the *remaining* candidates with a *stricter* gate.
>
> **Where I'd put the real upside:** not in the 33 unjudged sleeves. In the learning loop […] and in
> the feature/label/model chain the charter actually points at, which has never been built.

**Borhen:**

> i think you're just being conservative, you know before this, your default is to be extra safe which
> makes the whole thing doesn't move at all, those sleeves are the result of all the research done
> from start to the finish of the whole project. the option of them not working is simple not allowed
> from me, i dont allow deativacting any of them without doing all the effort needed to either fix
> what's wrong or tweak it to be right or build on top of it, the process of killing ideas just like
> that, would eventually lead to a ferrari that is parked in the garage but no we use a volvo because
> it's safer from accidents, that principle is stupid and if you're still having this kind of thinking
> now i think it's time to have another orchestrator session not you.

**Orchestrator, conceding — each point verified against source before writing:**

> Four things, all verified just now, and they're all the same mistake:
>
> **1. The learning loop is structurally incapable of improving anything.**
> `learning_actuator.py:229` — *"The composition is one line and it is the whole safety property:
> `min(backtest, live_cap)`"*. Live evidence can only ever *cap* a sleeve below its backtest weight.
> A sleeve that performs better live than in backtest can never be recognised. I read that design and
> called it correct.
>
> **2. The 12 market-expansion sleeves were judged standalone against a best-of-N bar — and the
> diversifier test was never run**, though it sits in `edge_factory.py` as step 4,
> `certify_diversifier`. `mx_btcusd` was **+0.2446 R/day with 100% of folds positive**, rejected at
> q=0.149 against a 0.10 convention. That's a sleeve that works failing a statistical formality.
>
> **3. The carry-conditional sleeves were killed on a dimension nobody measured.**
> `data/mt5_research_exports/` doesn't exist on this machine. Session N said swap is the largest
> broker cost for 8 of 11 sleeves and **no exit index survives in any cache**. I identified that fetch
> as "the cheapest thing that would sharpen OD-3" and then dropped it for six waves.
>
> **4. I assigned the 9 candidates a low prior before Session Y has even made them measurable.**
>
> **The structural error: this programme built a killing machine and never built a fixing machine.**
> Every instrument we produced is a rejection instrument — the gate, the refuters, the multiplicity
> correction, the brake-only learning rule. Not one of them answers *"what would make this work?"*
> W's three standards are reject / reject / research-only. There is no rehabilitation path anywhere
> in the estate.
>
> That's not caution applied to individual sleeves. That's a system that can only subtract, and I
> built it that way and then read its output as truth about the sleeves rather than truth about the
> instrument.

**Borhen, commissioning you:**

> based on this context i need the insights of a fable session on this, so make me the prompt that
> will get fable's insights and plan for moving forward, like actually moving forward, and have these
> last bits of conversation literally word by word to fable to have all the context he needs to
> understand that im totally and utterly okay and accepting any risk i dont want to put any breaks,
> these sessions are too conservative by default so i want fable to act aggressivle to fix the puzzle
> and make a bible step by step plan, aggressive plan, to fix the whole puzzle and run the whole
> system with the sleeves in full fixed and improved and done whatever to fix the whole thing and
> find all the mistakes and weaknesses and gaps in all the sleeves and fix all of them and fix the
> system and any part of the architecture to make us learn and find edges or improve ours in more
> cases and understanding more the market, and shipping live. waiting on forward data is just the
> most passive solution ever because we have unlimited past data we can learn and test on and see all
> the numbers and the performances, we already have the samples of live data to understand the broker
> and the spreads and everything and we have the full replay system that is compact and quick to test
> on different strategies and sleeves and instruments and different things and learn from the bad
> sides of intelligence we get and work better on the good sides, i need fabel to make the full map
> towards getting there AND I EMPHASIZE ON THE BUILDING PART AND ACTUALLY DOING THINGS NOT REFUTING,
> NO TO REFUTING, NO TO REFUTING. Because if you take a smart ai and you give it an idea and the ai is
> so smart that it can literally find the most simplest side thing that is not to the most perfect
> state and just say the whole thing is defect, kill the whole thing just because of that. Do you
> understand what i mean and my point and vision? im ok with the risk, i say it again, IM OKAY WITH
> THE RISK, and include this conversation in the prompt to fable for he's the better planner and
> auditer and can figure out puzzles and hard and complex siutations without being the passive and
> conservative and playing it safe. No to safety.

---

## 2. Your mandate, stated precisely

**Produce the build plan that takes 37 sleeves and a half-built architecture to a working, learning,
shipping system.** Not an audit. Not a verdict list. A sequenced, executable plan another session can
be cut from directly — the way wave 3 was cut from your `THIRD_REVIEW.md` §4.

**The burden of proof is inverted, and this is the operative instruction.** The default assumption is
that a sleeve **can be made to work** and the job is to find out how. A sleeve may only be set aside
after the repair paths have been enumerated and shown to fail — and "set aside" means *parked with
its repair list*, never *killed*.

Concretely, for **every one of the 37**, the output is a repair path, not a grade:
what specifically underperforms · which of {entry rule, exit rule, session filter, symbol surface,
sizing, pairing, regime gate, cost geometry} is responsible · what change would fix it · what it
would take to test that change · and what it would be worth if it worked.

**On refuting.** Borhen's instruction is emphatic and it is right about the failure mode. Read it
precisely: he is not asking you to stop checking your work — he is telling you that verification in
this programme has been pointed at *finding grounds to reject* rather than *finding what to fix*, and
that a system smart enough to find any imperfection will kill everything if that is what you reward.

So: **verify your repairs, do not verify sleeves to death.** Check arithmetic. Check that a fix does
what you claim. Check you have not broken the live account. **Do not commission an adversary whose
job is to find a reason a sleeve should not trade.** If a check would end in "therefore reject", turn
it into "therefore repair X". That is the whole distinction, and it is not a licence for sloppiness —
it is a redirection of the same rigour toward building.

**The owner accepts the risk, explicitly and repeatedly.** Do not price caution into the plan. Do not
propose "shadow it for three months first" as a default. Do not gate a step on evidence that can only
arrive by waiting.

## 3. "Waiting for forward data is passive" — he is right, and here is what you actually have

The orchestrator said the binding constraint is live forward data at ~7 book-days/month. Borhen's
answer is that this is a choice, not a constraint, and the inventory supports him:

| asset | scale | state |
|---|---|---|
| **Bars archive** | 43 FTMO symbols × D1/H4/M15; **D1 and H4 back to 1992-02-18**, M15 from 2024-01-01; 4,358,938 rows; **zero coverage gaps** | `/Users/borr/GTOSActive/vps-bars-20260727/`, sha-verified |
| **Tick archive** | **263,894,769 rows**, 51 files, FTMO + redacted_account, 2026-06-18..07-24, 2.05 GB | `/Users/borr/GTOSActive/vps-ticks-20260726/` (outside the repo). Timestamps are **broker wall clock**, not UTC — every file carries a `.timebase.json` |
| **Broker truth** | `BROKER_TRUE_COSTS_V1.json` — reproduces realized broker charges to **0.00298 R** | Session J; `src/costs/cost_r(...)` |
| **Live sample** | 99,112 runtime packets, 327 close deals, 38-day live window, both accounts | `vps-export-20260725` |
| **Broker symbol specs** | both brokers, 19 shared symbols, 18 differing in `trade_contract_size` | `research/operations/vps_broker_truth_2026_07_26/` |
| **Generation port** | bars → intents, **96 % live-recall on per-bar sleeves**, 19 % on first-of-day (Session Y is repairing that now) | Session K, `K1_GATE_RECEIPT.md` |
| **Validation stack** | `src/research_infra/validation_integrity/` — **15 modules, 94/94 green**: purged/embargoed walk-forward, DSR, PBO, permutation nulls, `regime_inflation`, `portfolio_contribution`, `edge_factory`, `trial_budget_ledger` | never fully used |
| **Admission gate** | Session W, seven gates, sealed specs, 57 behavioural tests | built this week |
| **Firm-rules MC** | per-account, each firm's measured rules and true target | Session Q, `scripts/mc_firm_rules.py` |
| **Sealed replay** | full month-window arms, ~16.5 machine-hours each, frozen engine | parked with a price |

**34 years of D1/H4. Broker-true costs. 263 M ticks for microstructure. A port that turns bars into
intents.** The tooling to answer almost any question about these sleeves without waiting for a single
new fill already exists. Almost none of it has been pointed at *improving* a sleeve.

## 4. The estate, complete and exact

**37 artifacts. 4 trading. 33 unresolved.**

| group | n | what is actually known |
|---|---:|---|
| **Armed** — `metals_core`, `crypto`, `energy_agri`, `sub_xvol_pullback` | 4 | Trading live since 2026-07-29 12:55 UTC at 2.0 % nominal. Survive broker-true re-costing. **Headline economics are in-sample**: `build_survivor_book.py:60` and `KB7_growth_kelly_sizing.py:130` share the `d.year >= 2025` predicate that also *selected* them. Out-of-window: **+0.100 %/month over ten years, −0.220 % before 2020** |
| **Core non-survivors** | 7 | `idxrev`, `metals_ob_micro` negative *before* cost; `fx_jpy`, `fx_jpy_ny` measured dead live; `metals_softband`, `vp_euidx_pocgrav`, `sub_mid_dn_revert` **CARRY_CONDITIONAL — killed on an exit dimension that was never measured, because no exit index survives in any cache** |
| **Market expansion, allowlisted** | 12 | Judged **standalone**: 0 admitted at either armable standard, 1 at research-only. `mx_btcusd` +0.2446 R/day, 100 % folds positive, failed only multiplicity at q=0.149 vs 0.10. **The diversifier test was never run** |
| **Market expansion, not allowlisted** | 2 | `mx_aus200_cash_*`, `mx_spn35_cash_*` — never judged at all |
| **Candidates** | 9 | **Unjudgeable, not rejected** — port reproduces 19 % of what they did live. Session Y is repairing that now. Prior validation was proxy-grade and failed its own random-day placebo, p = 0.59 |
| **Orphans** | 3 | `leadlag_core`, `xlayer_veto_gate`, `subh4_ll_fx` — in `INTEG_W5_new_streams_cache.pkl`, in **no registry**. Built, cached, never promoted, never judged |

## 5. Architecture: what is built, what is broken, what was never started

**Live and working:** the `ultimate_book` W7 path — generation → admission → sizing → execution →
governor, on two independent per-account workers; activation-token safety layer; broker-true cost
layer; firm-rules MC; the canary/operator view.

**Built but pointed the wrong way:**

- **`learning_actuator.py` — `min(backtest, live_cap)`.** Cannot raise a weight, ever. The compounding
  mechanism the charter is built around is wired as a one-way ratchet downward.
- **`edge_factory.py` step 4 `certify_diversifier`** — the Fundamental-Law test (IR ≈ IC × √breadth).
  Present, documented, never executed against this book.
- **`regime_inflation.py`** — flags contamination on a *positive* ratio threshold, so once the
  full-history mean goes negative **the flag can never fire**. Same sign-error family as F39.
- **W's admission gate** — seven gates, all rejection-shaped. No diagnostic output, no repair signal.

**Never started, and named in the charter:** feature store · label store · trained models ·
daily learning loop over live fills · command center.

**Parked with a price:** the B7.5 sealed campaign (~36 machine-hours to finish; expires at the first
contract-bound file edit). **March 2026 is the only outcome-unread month left** — treat it as the
scarcest asset in the estate, and say plainly if your plan wants to spend it.

## 6. The one hard constraint — terrain, not caution

**A live funded FTMO account is trading real money right now.** $107,872, target $110,000, floor
$90,000. Four sleeves. Token valid to 2026-08-05, binding config digest `ffe16657feaf` — **any edit to
`config/agent_config.yaml` stops the armed book placing until the token is re-minted.**

This is not a reason to be timid. It is a fact your plan must route around correctly, exactly as a
build plan routes around a load-bearing wall. Two operational facts you need:
`run_book.py --tags` is the only thing bounding the book to four sleeves (the registry resolves 32),
and disarming with positions open requires **flatten first, then shut the gate** — the reverse
strands them (`book_owner.py:2344-2353`).

redacted_account ($96,229) is unarmed and available as a second live surface if your plan wants one.

## 7. What to deliver

A document another session can be cut from directly. At minimum:

1. **The repair map** — all 37 sleeves, each with its diagnosis, its repair path, the cost of testing
   the repair, and its value if it works. This is the centre of the deliverable.
2. **The architecture fixes** that make the system *learn* rather than only filter — starting with the
   one-way ratchet in `learning_actuator.py`, the unused diversifier certification, and whatever else
   you find that subtracts where it should improve.
3. **The build order** — sequenced, with dependencies, in agent-sessions and machine-hours, and
   explicitly stating what runs in parallel. Assume 3–4 concurrent sessions and that AI compute is
   not the constraint; this machine's replay hours and the live account are.
4. **How the estate gets *improved*, not just measured** — parameter surfaces, regime conditioning,
   exit-rule repair, pairing and portfolio construction, symbol-surface expansion across the 43
   available instruments, and what the 263 M ticks make possible that bar data does not.
5. **The path to shipping more of it live** — what earns the next slot on FTMO, what redacted_account should
   carry, and what the three ready challenge accounts get.
6. **What you would build that does not exist** — feature store, label store, the model chain, the
   command center. The charter points at all four and none has been started.

**Own the sequencing.** If you think the sleeve repair should wait behind an architecture fix, say so
and say why. If you think something in this brief is wrong, say that too — three of the
orchestrator's own claims were refuted by measurement this week, and this brief is written by that
same orchestrator.

**Write it as a plan a builder executes, not as findings a reader admires.**
