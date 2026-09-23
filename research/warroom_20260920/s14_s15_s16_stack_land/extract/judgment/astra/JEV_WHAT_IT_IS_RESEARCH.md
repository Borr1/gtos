# What Jev is — research note for GTOS

**Date:** 2026-09-17  
**Seat:** docs / architecture. No TypeSafe call. No broker place.  
**Owner ask (verbatim intent):** “I need you to do a full research… on what is JEV in the first place.”  
**Live docs of record:** https://docs.typesafe.ai/llms.txt (fetched this session).  
**Skill:** [`.agents/skills/typesafe-ai/SKILL.md`](../../.agents/skills/typesafe-ai/SKILL.md)

This note is the Project-facing answer to “what is Jev.” It is not a refuse policy and it is not a chat-bot brief. Pair it with [`JEV_ALIVE_ORGANISM_20260917.md`](JEV_ALIVE_ORGANISM_20260917.md) (how GTOS uses it) and [`JEV_GOLD_STATE_SCHEMA_DRAFT.md`](JEV_GOLD_STATE_SCHEMA_DRAFT.md) (the XAUUSD state object).

---

## 0. One sentence

**Jev is TypeSafe’s flagship System One model: a non-conversational decision engine that takes structured program state plus typed questions and returns constrained answers with calibrated probabilities, in ~70–500 ms, cheap enough to run through ordinary code gates.**

It does not write, chat, remint, or place. Code owns the workflow. Jev supplies programmable common sense where a static `if` is too dead and a chat seat is too slow, too expensive, and too unstructured.

---

## 1. Names, so nobody confuses the tissues

| Name | What it actually is | What it is not |
|---|---|---|
| **TypeSafe** | The company / API that hosts System One models. HTTP `POST /v1/systemone`. Python SDK `typesafe_sdk`. | A GTOS module. A chat product. |
| **System One** | A *class* of models trained to return typed decisions + probabilities, not generated text. Named after Kahneman’s fast/intuitive System 1. | An LLM with JSON mode. A reasoning (System 2) model. |
| **Jev** | The first and currently only public System One model. Aliases: `jev-latest`, `jev-preview` → versioned id `jev-1.13.0` (as of this session’s docs fetch). Named after **William Stanley Jevons** (Jevons paradox: cheaper intelligence → more use, not less). | “Jeff.” A brain. A remit. A chair. A printer. |
| **RLCD** | **Reinforcement Learning for Calibrated Decisions** — TypeSafe’s post-training method. | RLHF (chat preference). RLVR (verifiable-reward reasoning). |
| **Choice / Score / Noul** | The three *question primitives*. Every Jev call is one or more of these over one `state`. | Prompt-and-parse. A mega-“should we trade?” question. |
| **Noul** | Portmanteau of “boolean.” A yes/no *probability* in `[0, 1]`. No separate `confidence` field. | A medium-intensity score. “0.5 means kind of yes.” |
| **Chair / redacted_account** | Human/coordinator seat. Speaks ENFORCE / VETO / LABEL. | The decision engine. |
| **Writer / printer** | Code that prints from tags + token. | An LLM. |
| **Sidecar (V1/V2)** | 2026-09-16/17 conservative placement: Jev *beside* the book, refuse / label / HOLD-draft only. | The owner’s 2026-09-17 living-tissue direction. Keep V2 as *correctness* (no place, no invent NEWS, no Challenge-45 KEEP grid). Do not keep it as the *ambition*. |

Owner word 2026-09-17: Jev is **not** “a brain or a remit.” The foundation (printer, selector, scheduler, market connects, logs) already works and is fast. Jev is the **alive element inside that foundation** — calculations through code, over complete state, on thousands of candidates.

---

## 2. System One — the programming model

Official: [System One](https://docs.typesafe.ai/concepts/system-one.md), [How to build](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md), [State](https://docs.typesafe.ai/concepts/state.md), [Primitives](https://docs.typesafe.ai/primitives.md).

### 2.1 Contract

1. You assemble a **state** (string, JSON object, or array of text). Prefer a **named JSON object**.
2. You ask one or more **questions**. Each has an `id` (for *your* code — not sent to the model), a `type` (`choice` / `score` / `noul`), `instructions` (the full question), and `criteria` (options / levels / optional yes-no gloss).
3. Every question in one request **sees the same state**, is evaluated **independently**, and **cannot see the other answers**.
4. You get typed answers + (for Choice/Score) a full probability distribution + a derived `confidence`. Noul returns only `noul`.
5. **Your code composes.** Weights, thresholds, “any serious violation,” speculative ignore-if-unused — all live in code. Changing a weight does not require a new model call if you stored the atomics.

This is the opposite of “ask Grok / a chat seat to place.” It is also the opposite of “one mega-prompt that returns a trade.”

### 2.2 Why “System One”

Kahneman: System 1 is fast and intuitive; System 2 is slow and deliberative. TypeSafe’s bet (founder Diogo Almeida, co-author of InstructGPT / the RLHF stack behind ChatGPT): large-scale automation will be ~99% machine-to-machine. Chat-trained models optimize for text humans prefer. Production code needs **narrow, inspectable, probability-bearing decisions**.

Jev **gives up string generation**. That is the feature:

- It cannot emit a malformed tool call or a value outside your schema. Type-safety is guaranteed by a **parallel sampler** over an enumerated answer space, not by “please output JSON.”
- It cannot write a rationale, a chair card, or a remint script.
- It *can* still be **wrong** about the world. Schema-match ≠ truth. Calibration is a **group** property (see §5).

Official nuance (TypeSafe blog, 2026-09-15): “can’t hallucinate” means **cannot invent an answer outside the typed space**. It does **not** mean “cannot pick the wrong option.” GTOS must never quote the marketing line as “Jev cannot be wrong.”

### 2.3 What Jev accepts

- Text only. Strings, JSON objects, arrays of text.
- **No images, audio, or video.** Charts must be reduced to named numeric / categorical fields first (ATR, session hour, distance-to-level, signed minutes-to-HIGH).
- ~32,000 token request budget shared by state + questions (~150,000 English characters). A closed gold state object plus a fan-out of 8–20 questions fits easily.
- Choice cardinality **up to 255**. Higher cardinality is a two-stage Score-then-Choice (TypeSafe’s own wikiracing pattern). For GTOS that means: do not dump 400 sleeve tags into one Choice; prefilter in code, then choose among the enrolled remainder.

### 2.4 Latency and cost (measured + published)

| Source | Number |
|---|---|
| TypeSafe published | 70–500 ms end-to-end; input **$0.042 / MTok**; **output tokens free**; 250,000 tok/s / 1,200 rpm (limits can move) |
| GTOS 2026-09-16 lab (`lab/SUMMARY.md`) | ping 141–206 ms; fan-out 12 Nouls **169 ms**; admit probe 207 ms / 781 in / 109 out |
| GTOS Challenge 45 replay | mean **162 ms** |
| Owner word 2026-09-17 | **137 requests < $0.01** (one cent, “even less”) |

**Arithmetic that matches the owner’s “almost free” claim** (do not treat as a vendor SLA):

- Lab-sized call ≈ 400–800 input tokens.
- 137 × 600 tok = 82.2 k tok ≈ 0.082 MTok × $0.042 ≈ **$0.0035**.
- 100 richer gold-state calls at 2,000 tok ≈ 0.20 MTok ≈ **$0.0084**.
- 1,000 historical candidates × 1 call × 2,000 tok ≈ **$0.084**.
- 10,000 candidates × 2,000 tok ≈ **$0.84**.

That is why the owner is right that we do **not** wait for tomorrow’s live print. Weeks / months / years of gold bars + (real) events are a **budget**, not a fantasy. Parallel questions in one call are the cheap path: TypeSafe’s parallel-questions cookbook measures **~12× cheaper and ~10× faster** than one-question-per-call, with **no change in answers**.

Rate limits (1,200 rpm) are the practical ceiling for a historical sweep, not dollars. A 10,000-candidate gold slice at one request per candidate is ~8.3 minutes at the published rpm, or much less if you batch questions and/or shard.

---

## 3. RLCD — what the training actually optimizes

Official primer: [AI primer](https://docs.typesafe.ai/introduction/machine-learning-primer.md). Launch post: [Introducing System One Models and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) (2026-09-15).

### 3.1 Three post-training families

| Method | Optimizes for | Typical product | Failure mode TypeSafe names |
|---|---|---|---|
| **RLHF** | Human preference on generated text | ChatGPT-class chat / copilots | Sycophancy, confident-sounding hallucination, mode-dropping toward a preferred *style* |
| **RLVR** | Verifiable rewards (unit tests, math) | Reasoning models | Slow, expensive, still text-first |
| **RLCD** | **Calibrated decisions** — higher probability ↔ higher chance the typed answer is correct, *across groups of predictions* | Jev / System One | Still wrong on a single row; calibration is not a guarantee; domain shift (trading ≠ TypeSafe’s public workflow evals) |

Almeida co-invented RLHF. TypeSafe’s claim is that RLHF is the wrong objective for unattended automation: people like fluent answers; software needs **epistemically honest probabilities**.

### 3.2 What “calibrated” means — and what it does not

Across many predictions from a well-calibrated model:

- answers assigned probability 0.2 should be correct about 20% of the time;
- 0.8 ≈ 80%; 1.0 ≈ 100%.

**That is a group statistic.** Official docs are explicit: it does **not** guarantee any single answer. GTOS already learned the sister lesson on Challenge 45 (`JEV_V1_CRITIQUE.md`): high `admit_now` confidence on a pre-cut US30 ticket was the model **echoing the surface digest you put in state**, not discovering toxicity from geometry.

**GTOS-calibrated ≠ vendor-calibrated.** Until we have a reliability diagram on *our* questions (gold state, F5 slate, W7 intents) the vendor’s 0.55 / 0.80 cookbook numbers are **starting knobs**, not Nightly KEEP gates. V1 treated them as KEEP. That is discarded as policy and kept as evidence that the primitives *run*.

### 3.3 Parallel sampler

Jev does not decode one token conditioned on the last. Possible outputs are enumerated; probabilities are computed in one pass. Consequences:

- Adding questions to the same request barely changes latency (lab: 12 Nouls ≈ one Noul).
- You **must** enumerate the answer space. If a time_stop exit class is not in the Choice criteria, Jev will never emit it — Challenge replay labeled **5/5 paying time_stops** as `manual_other` (`JEV_V1_CRITIQUE.md` §3.5). Schema is hard. Missing a noun is a **code defect**, not a model personality.
- “Cannot hallucinate a type” is true. “Cannot miss a class you forgot to list” is also true, and more dangerous for GTOS.

---

## 4. The three primitives — GTOS fit

Official: [Choice](https://docs.typesafe.ai/primitives/choice.md), [Score](https://docs.typesafe.ai/primitives/score.md), [Noul](https://docs.typesafe.ai/primitives/noul.md). Skill table (same distinction):

| Need | Primitive | Returns | GTOS use |
|---|---|---|---|
| One of a defined set | **Choice** | `choice`, `probabilities`, `confidence` | admit / abstain / hard_refuse; exit_class; charter VETO mechanism; action_scope |
| Degree along a described dimension | **Score** | `score` (can fall *between* levels), `legend`, `probabilities`, `confidence` | geometry-vs-tape; with-flow vs against-flow; session purity; hold_strength; lesson-for-Nightly |
| Whether a condition holds | **Noul** | `noul` ∈ [0, 1] only | state_sufficient; event_proximity; cluster_same_dir; isolated-reentry-is-not-a-remint; cost-screen-would-hurt |

### 4.1 Choice

Pick **one** option from a closed set. The distribution compares competitors. Confidence is **how peaked** that distribution is, not “am I allowed to send.”

Rules that matter for GTOS:

- Include a **no-match** option when the list might not cover the world (`none`, `unknown`, `abstain`).
- Do not ask Choice to do a writer integer (“how many orig_stops today?”). Code counts. Jev may *label* a would-be third fire; it must not be the counter.
- Do not put `flatten` in `action_scope`. `jev_corr_hold_v1` treats flatten as a **broken schema**. Keep that.

Owner-shaped Choice (alive, not refuse-only):

```
admit:        admit | abstain | hard_refuse
exit_class:   orig_stop | broker_tp | time_stop | breach_flatten | other
mechanism:    correlation | event_proximity | microstructure | weekend_carry | none
flow_stance:  with_flow | against_flow | no_clear_flow
```

`flow_stance` is the owner’s “are we with it or against it.” It is a Choice over **named** multi-TF facts in state, not a vibe.

### 4.2 Score

Ordered descriptive **levels you write**. The model returns a probability-weighted position that **can sit between levels** (lab `geometry_quality` 1.01, `lesson` 1.68). That is the owner’s **fluid range**: not true/false, a position on a spectrum.

Rules:

- Each level must stand alone as a *situation*, not a number. “1 = house default 1R/6R with known fast-stop risk” **selected the death geometry** on Challenge DSP (`JEV_V1_CRITIQUE.md` §3.3). Write levels about **this tape vs this stop**, not about the house contract.
- A Score of 0.5-on-a-0–2-legend is *between* 0 and 1, not “medium confidence.”
- Composite scoring (TypeSafe pattern): several Scores on one state, **weights in code**. Change the gold-session weight without re-calling Jev.

Owner-shaped Scores:

```
flow_alignment     0 = fighting the named HTF/session flow
                   1 = mixed / rotating
                   2 = aligned with named flow
session_fitness    0 = dead / Friday-cutoff / wrong hour for this sleeve
                   1 = ordinary session
                   2 = sleeve’s historically clean hour
geometry_vs_tape   0 = stop dies inside the next 1–2 M15 prints given named range/ATR
                   1 = ordinary house risk
                   2 = stop/target fit named volatility
level_respect      0 = firing through a named opposing PDH/PDL/FVG
                   1 = no relevant level in state
                   2 = holding / reclaiming a named supporting level
```

### 4.3 Noul

Probability that a **yes/no** is yes. Near 1 = strong yes; near 0 = strong no; near 0.5 = **yes and no similar** — not “medium intensity.” If you wanted intensity, you wanted a Score.

Noul has **no separate confidence**. The number *is* the uncertainty.

Owner-shaped Nouls (one per independently useful label — TypeSafe: do not pack five yeses into one Choice):

```
state_sufficient          enough named fields to judge?
event_in_named_window     a *named* HIGH is in the window the code already uses?
with_macro_usd_impulse    USD-impulse facts in state support this gold side?
cluster_same_dir          ≥2 same-direction correlated intents on this slate?
isolated_reentry_is_new   writer integers say this is a new named fire, not a remint?
```

Empty calendar → do **not** invent a HIGH. Ask `state_sufficient` / `calendar_spine_empty` and let code abstain. Official empty-spine rule from V2 still binds: empty ≠ “no HIGH.”

### 4.4 Fan-out and second requests

- **Same request:** all questions that can be asked against the current state, including speculative ones. Code ignores unused answers. This is the cheap path for “thousands of candidates.”
- **Second request only when** the first answer is required to *fetch* evidence, *build* new state, or *enumerate* the next options (TypeSafe: hierarchical classification, skill-suggestion re-read, structure-recovery). Typical GTOS path: one admit fan-out per candidate; a second call only if you must fetch a Walter card or rebuild a cluster from the first answer.

Do not do one-question-per-call. The 2026-09-16 lab already proved the fan-out latency class.

---

## 5. Confidence — the second axis, not the gate

Official: [Confidence](https://docs.typesafe.ai/confidence.md), [confidence-gated routing](https://docs.typesafe.ai/patterns/confidence-routing.md).

- `confidence` is a **statistic of the probability distribution** (how peaked). You also get the raw `probabilities`; you may compute a different peakedness if you want.
- Low confidence = “I don’t know” — the useful System One signal. Code must have a path for it (abstain / escalate / gather more state).
- High confidence is **not permission to place**. TypeSafe’s own bank-transfer example raises the threshold with stakes. **Broker send is infinite stakes** relative to a support-ticket route. V2’s sentence stands: high conf still does not auto-place.
- Owner vision adds the missing half V2 under-weighted: high-confidence **fluid Scores** *are* allowed to **move a gate’s outcome** once a **named live wire** is proven — not as a KEEP grid on Challenge 45, as a composed range at a specific code site (selector merge, metals A8, pre-send cost-vs-tape). Shadow-first until that wire is named.

Three-band starter (TypeSafe), **GTOS-translated**:

| Band | TypeSafe default story | GTOS alive-organism story |
|---|---|---|
| Low | Do not act | Abstain / escalate / assemble more state. The only Jev output that may look “authoritative” without a named wire. |
| Mid | Proceed with caution | Chair-visible draft; log; compose with other atomics. |
| High | Act automatically | **Still not send.** May *steer a fluid gate* on a named, shadowed-then-proven site. May never flatten / remint / write `verdict.json`. |

Lab 0.55 / 0.80 remain **calibration evidence** (`JEV_V1_CRITIQUE.md`). Do not promote them to Nightly KEEP.

---

## 6. Fit to GTOS — why the owner is right that this is “so perfect”

GTOS already has the System One *shape*, and has been paying for it in static `if`s:

| GTOS tissue | Already true | What Jev adds when state is complete |
|---|---|---|
| Printer / `run_book.py` / F5 `minimal_size` | Fast, organized, detects what we throw at it (owner) | Not a rewrite. Jev sits **in** the gates that currently hard-boolean. |
| Selector V4 / Scheduler V4 | Packet merge, best-trade, `would_action` | Atomic Scores over the same packet; code still owns `runtime_effect`. |
| `ultimate_book` generate → admit → place → manage | Integer laws (tags, 2-stop, token digest, governor) | Fluid outcomes: “is this metals FVG *with* the named flow?”, “is this spread *hurtful* vs this stop *today*?” |
| F5 chair | ENFORCE / VETO / LABEL | Drafts those verbs from charter mechanisms. Chair still writes the inbox. |
| Logs / slates / Challenge 45 | The data is already there | Historical gold lab + slate A1 shadow — not wait-for-live. |
| Doctrine | Wrong trade = missing state **or** wrong calculation (owner, many times) | Jev does not invent the missing state. It **fails `state_sufficient`** so we go assemble it. |

TypeSafe’s own use-case map (function calling, rerank, composite scoring, feature discovery) maps onto GTOS without metaphor:

- **Select instead of generate** — thousands of candidates already exist; Jev ranks / admits / stances them.
- **Composite scoring** — session + flow + geometry + cost, weights in code, retunable without a new model.
- **Autoresearch feature discovery** — TypeSafe cookbook: propose questions, turn free text into numeric features, feed a classical model. That is the fine-tune path the owner named, *after* we have clean as-of labels (doctrine + `llm_specialization_research_backlog.md`).
- **Speculative fan-out** — ask event / cluster / isolated-reentry questions every time; code uses them only when the integers say they apply.

Chat seats (Grokbot, Project coordinator, this agent) are **research and chair**, not the decision engine. Owner: “it won’t, it doesn’t really need to be conversationalist, because it doesn’t do conversation, it’s with structured data.”

---

## 7. Limits — still can be wrong; schema is hard

These are the honest bounds. They are **not** a reason to stay a refuse sidecar. They are the reasons the **state object and the question list** are the product.

1. **Wrong answers exist.** Calibration is group-level. Challenge bleed tickets were `admit` under `admit_now` (`291549869`, `291713652`). House hard-off is still code.
2. **Schema is the intelligence bottleneck.** If `time_stop` is missing or collapsed to `manual_other`, Jev will be confidently wrong on the paying class. If gold state omits London vs NY hour, Jev cannot “feel” session. If calendar is empty, event Noul must abstain — **never invent FOMC/NFP rows** (V2 §2.5, this PR, owner/doctrine).
3. **Echoes what you put in state.** Surface digest in → high-conf hard_refuse out is a **consistency check**, not a discovery. LIVE admit must not include realized PnL, later-won flags, or today’s law on yesterday’s legal print (`admit_then` vs `admit_now`).
4. **No System 2.** Do not ask Jev to invent a sleeve, write a charter, or derive a new HIGH spine. Break those into atomics + code.
5. **Text-only / no ticks-as-images.** Tape must be fields: ATR, range, sweep depth, spread_r, signed minutes.
6. **Cardinality 255.** Prefilter in code.
7. **Domain shift.** Public workflow evals (TypeSafe vs Astra/Fable averages on business graphs) are not a gold-trading calibration. Our reliability diagram is owed.
8. **Missing sidecar must not increase fire.** V2 fail-open rule stays: missing Jev = no extra PASS. Alive-organism does **not** mean “if Jev is down, guess.”
9. **Two organisms.** This `main` tree is W7 `ultimate_book`. F5 Challenge printer lives on leftover-ship / live `f5-live`. Do not silent-edit `already_placed_today` to “fix” F5 isolated re-entry (V2 §0a / §1.5).
10. **Secrets.** `TYPESAFE_API_KEY` in Cursor Cloud / Project secrets only. Never commit, never paste, never invent. This research made **no** live API call.

---

## 8. What “fine-tune eventually” means here

Owner: we will fine-tune with the data we have. Doctrine + `llm_specialization_research_backlog.md` already set the bar:

- clean audited examples;
- **non-leaky labels** (as-of-open, no EXPOST in LIVE);
- sealed eval partitions;
- baseline vs current Jev + vs deterministic gates.

Until that exists, “tune” means **questions, state completeness, and code composition** (V2 §1.4) — which is exactly TypeSafe’s recommended loop (composite scoring + feature discovery), and exactly the gold lab in the organism doc. A 45-row Challenge PnL grid is not a fine-tune. A 2-week / 2-month / 10-month gold slice with as-of labels **is** the start of one.

---

## 9. Sources opened this session (no chat memory)

| Source | Used for |
|---|---|
| https://docs.typesafe.ai/llms.txt and the System One / State / Primitives / Confidence / Models / How-to-build / Composite-scoring / AI-primer pages | Contracts, prices, aliases (`jev-1.13.0`), limits |
| https://typesafe.ai/blog/introducing-system-one-models-and-jev | RLCD vs RLHF/RLVR, Jevons name, parallel sampler, “can’t hallucinate” nuance |
| `.agents/skills/typesafe-ai/SKILL.md` | Primitive table, compose-and-verify, speculative fan-out |
| `judgment/astra/lab/SUMMARY.md` | GTOS latency / token / probe answers |
| `judgment/astra/JEV_INTEGRATION_V2_20260917.md` + `JEV_V1_CRITIQUE.md` + Challenge replay pack | What V1 measured; what must not be repeated |
| `.context/00_core/research_operating_doctrine.md` | No tune-after-see; AI API is not the historical *backtest engine*; small-n is not validation |
| Owner verbatim 2026-09-17 | Living tissue, cheap, gold studies, outcome-oriented gates, cut passive conservatism |

**Not opened as authority:** TypeSafe training-set internals (not public); any invented NEWS window; verification login 0 as a calibration surface.
