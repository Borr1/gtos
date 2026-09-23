# GTOS_SCORE_STEALS — Codila/Jev absorb (2026-09-20 Asia/Bangkok)

**Ultragoal:** Challenge payout + Jev as intelligence *inside gates*.  
**Hard rules:** Never invent NEWS_PROTOCOL. Jev never places. Chair ENFORCE/LABEL from this file without re-reading X posts.

Sources (local extracts):
- `docs/fan-out.md`, `docs/confidence.md`, `docs/choice.md`, `docs/score.md`, `docs/noul.md`, `docs/state.md`
- `docs/langchain_harness_jev.md`, `docs/introducing_system_one_jev.md`
- `raw/jev-ultrafast/` (Browser Use × TypeSafe), `raw/skills/skills/typesafe-ai/SKILL.md`
- Prior: `../codila_jev_article_*.txt`, `CHAIR_ABSORB_20260920.md`, `../jev/JEV_FIT_CHAIR_READ_20260916.md`

---

## Ranked steals (Chair ENFORCE / LABEL ready)

### S1 — Alive Choice menus for fluid gates  `[a]`
**Steal:** Rebuild Choice `criteria` every decision cycle from workers/actions/symbols that exist *now* (Browser Use: fresh element table → operation + target heads). Stale menus = yesterday's gate list.

**GTOS map:**
- Gate menus = live registry of sleeves/workers/handlers available this tick (not a frozen enum from last deploy).
- Include only supported ops; always offer escape hatches: `HOLD`, `ABSTAIN`, `ESCALATE_CHAIR`, `BLOCKED`.
- After tool/state change → rebuild options before next Jev call.
- Cap ≤255 options; for large sleeves: code-filter → Score shortlist → Choice (TypeSafe high-cardinality pattern).

**Chair LABEL:** `ALIVE_MENU` — Choice criteria must be regenerated from current book/worker inventory; never reuse prior-cycle option maps when inventory changed.

**Evidence:** `raw/jev-ultrafast/jev_ultrafast/model.py` (`action_space` → dynamic `operations` + speculative `*_target`); README "Every observation produces a new element table"; Codila §06.

---

### S2 — Confidence thresholds for shadow → APPLY  `[b]`
**Steal:** Confidence is distribution concentration (Choice/Score), not accuracy %. Three bands + **risk-scaled** thresholds. Noul has no separate confidence — use distance from 0.5.

**GTOS starter bands (calibrate on labeled Challenge tape — do not treat as truth):**
| Band | Choice/Score confidence | Behavior |
| --- | --- | --- |
| LOW | `< 0.50` | Stay SHADOW; log; no APPLY |
| MED | `0.50–0.85` | SHADOW + REVIEW flag; Chair may LABEL |
| HIGH | `≥ 0.85` | Eligible for APPLY only if gate risk allows |

**Risk scale (same system, different bars):**
- Read-only / LABEL assist → may act at MED
- Sleeve admit / corr HOLD → need HIGH (≥0.85 starter; Codila chief.py)
- Anything near place / broker / order path → **VETO** (Jev never places); no APPLY path exists

**Chair ENFORCE:** `CONF_GATE` — shadow→APPLY requires calibrated threshold for that gate's stake; confidence alone never authorizes side effects.

**Evidence:** `docs/confidence.md`; Codila §04 (0.85 review); TypeSafe transfer example (0.5 floor / 0.9 for high-stakes).

---

### S3 — Parallel Noul/Score on book state  `[c]`
**Steal:** One `system_one` call → many independent questions over the *same* state (fan-out / speculative). Code ignores irrelevant branches. Questions cannot read each other's answers — state premises explicitly.

**GTOS book-state pack (example shape — Chair owns final criteria):**
```text
state = {
  goal, sleeve_id, symbols[], positions[], risk_flags[],
  evidence: {tape_summary, geometry, gaps[]},
  workers_alive: [...]
}
questions (parallel):
  next_gate:     Choice  — HOLD | RESEARCH | LABEL | ENFORCE_DRAFT | ESCALATE
  urgency:       Score   — levels: routine / session_sensitive / immediate_risk
  evidence_enough: Noul  — P(yes enough to decide)
  corr_hold:     Noul    — P(multi-symbol same-sleeve needs HOLD)   [speculative]
  toxic_remint:  Noul    — P(close looks toxic)                     [speculative]
  sleeve_fit:    Score   — unrelated / adjacent / direct / deep
```

**Chair LABEL:** `FANOUT_BOOK` — pack independent gate questions in one call; consume only branch-relevant answers; never chain Jev→Jev for independent dims.

**Evidence:** `docs/fan-out.md`; LangChain multi-question; Codila §07.

---

### S4 — DONE / side-effect verify outside Jev  `[d]`
**Steal:** Model selecting DONE ≠ task succeeded. Browser Use: independent `verify(page)` checks route/date/results; design.md: "Independent checks, rather than the model's DONE choice, determine whether the demonstrated task succeeded."

**GTOS map:**
- After any APPLY / handoff / file write / Slack send / queue push: **code verifies artifact exists and matches contract**.
- Jev may Choice `DONE` / `CONTINUE` / `BLOCKED`; Chair/code owns completion truth.
- Persist last completed action before retry; confidence cannot prove save/send/order.
- Kill switch + action/spend limits remain code.

**Chair ENFORCE:** `DONE_OUTSIDE` — completion and side-effect checks are non-Jev; Jev DONE is advisory only.

**Evidence:** `raw/jev-ultrafast/examples/flights.py` `verify()`; `docs/design.md` Boundaries; Codila §08.

---

### S5 — Usage-router before expensive Chair/browser work  `[e]`
**Steal:** LangChain `ModelRouterMiddleware` — Jev Choice least-cost model that can complete the task. Codila GrokBot skill: before browser/research/retry/extra bot → call usage router; honor action; shadow logs first.

**GTOS map:**
```text
Choice criteria (alive):
  cheap_label   — local/rules or Jev-only classify
  chair_read    — Chair prose / ENFORCE card needed
  browser_scout — Browser Use / web fetch budget
  deep_reason   — expensive LLM / multi-agent
  defer         — wait / batch / kill
```
Route *before* spawning browser or Chair-heavy work. Track **$/completed Challenge decision**, not vanity demos.

**Chair LABEL:** `USAGE_ROUTER` — expensive seats (Chair, browser, deep LLM) require prior Jev/code route with shadow log; honor `defer`.

**Evidence:** `docs/langchain_harness_jev.md` ModelRouter; Codila §09–10; skill "Route and fill known arguments".

---

## Supporting steals (keep, lower priority)

| ID | Steal | Chair verb |
| --- | --- | --- |
| S6 | State discipline: goal vs evidence vs gaps as separate fields; put requirements in question text (ids ignored) | LABEL `STATE_SHAPE` |
| S7 | Score→shortlist→Choice for >255 / deep taxonomies | LABEL `SCORE_THEN_CHOICE` |
| S8 | Local queue handoff `queue/{research,write,review}/*.json` — no chat paste | LABEL `QUEUE_HANDOFF` |
| S9 | Structured criteria (`what` / `not_for` / `examples`) when options collide | LABEL `CRITERIA_OBJECTS` |
| S10 | Cost floor claim: ~$0.042/MTok input, output free — measure ourselves | LABEL `COST_METER` |

---

## VETO — do not absorb

1. **Jev never places.** No path from Jev answer → `order_send` / broker / live Challenge place. Intelligence proposes; printer prints; Chair verbs.
2. **Never invent NEWS_PROTOCOL** from Codila article, TypeSafe blog, or LangChain post.
3. **Demo headlines ≠ Challenge edge.** Flights 7s/$0.0039, Hassan 1018 papers $0.08, Vercel fx 5–18×, Doom/Wikiracing — architecture refs only.
4. **Confidence ≠ permission.** Typed outputs cannot hallucinate schema; they can still be *wrong*. Outside verify required.
5. **No Jev on generative seats.** Briefings, code, Chair prose cards stay outside; Jev routes/scores/approves candidates.
6. **Do not treat vendor thresholds as Challenge-true** until labeled tape calibrates them.
7. **Questions cannot see sibling answers** — never design a gate that assumes fan-out answers are causal chain without a tool/state refresh in between.
8. **Secrets:** repos stored without `.git`; `.env.example` only — no API keys in this tree.

---

## Chair quick card (ENFORCE one-liners)

```
ENFORCE ALIVE_MENU: rebuild Choice criteria from live inventory each cycle.
ENFORCE CONF_GATE: shadow→APPLY only above stake-scaled confidence; else REVIEW.
ENFORCE FANOUT_BOOK: parallel Choice/Score/Noul on one book state; code routes.
ENFORCE DONE_OUTSIDE: verify artifacts/side effects in code; ignore Jev DONE as truth.
ENFORCE USAGE_ROUTER: route before Chair/browser/deep-LLM spend; shadow first.
VETO PLACE_PATH: Jev off broker/send/place forever.
VETO NEWS_PROTOCOL: do not invent from these sources.
```

---

## File index

| Path | Role |
| --- | --- |
| `GTOS_SCORE_STEALS.md` | This file — Chair ENFORCE/LABEL source |
| `CHAIR_ABSORB_20260920.md` | Digest + links |
| `docs/*.md` | Clean TypeSafe/LangChain extracts |
| `raw/jev-ultrafast/` | Shallow README+code (no secrets) |
| `raw/skills/` | typesafe-ai SKILL.md |
| `../codila_jev_article_*.txt` | X article text |
