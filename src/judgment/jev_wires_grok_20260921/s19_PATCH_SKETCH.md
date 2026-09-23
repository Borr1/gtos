# PATCH SKETCH — Typesafe usage ramp (every gate POSTs evaluate())

**session:** `19_typesafe_usage_ramp_every_gate`  
**status:** DRAFT ONLY — no live APPLY, no broker place, no VPS/W7/redacted_account edit  
**API:** `POST https://api.typesafe.ai/v1/systemone`  
**questions:** `symbol_fanout_questions()` (n=49) + pack-specific extras  
**budget:** `GTOS_JEV_MAX_CALLS=500000` (code default today = 200)

Owner: usage ~$0.11 / 666 req / 7d is too cheap. Ramp = **every gate path calls `jev_client.evaluate(state)`** (observe + decide). Fail-closed if Jev dark. Writer still prints. Design Choice PLACE|STAND|DELAY only.

---

## Law for this sketch

1. Static code = thin envelope. Jev sees COMPLETE_STATE.
2. Envelope stays: identity, prop walls, hard-offs, 2-stop COUNT, token, weekend, kill switch.
3. Soft exceptions only via Jev + Challenge hist — never silent code flip.
4. `place=false` in this session. Owner override: eternal never_place is WRONG; default-off until prove is OK.
5. Do **not** flip global `GTOS_JEV_SLEEVE_SELECT_APPLY=1`.
6. TypeSafe skill: independent questions over **one** state together. Default = **one fanout POST per candidate**, not 48 HTTP POSTs. Optional `GTOS_JEV_PER_GATE_POST=1` is ablation only.
7. Fail-closed: `ok!=True` or `skipped` on a JEV_WIRE **decide** path → STAND / no size-up / no admit-as-today. Observe may still log the skip.
8. Never invent NEWS_PROTOCOL. `news_join=STATE_MISSING` is a valid POST.

---

## 0. Files to change (sketch, OUT only)

Canonical: `_pr41_land/ai-trading-agent/src/judgment/` + `book_owner.py` / `bridge.py` + `policy_c_admit.py` + `sleeve_select.py`.

| # | file | change |
|---|---|---|
| 1 | `jev_client.py` | DEFAULT_MAX_CALLS 200→500000; `evaluate_for_gate`; fail-closed helper; optional questions override |
| 2 | `a1_log.py` | observe every candidate; fanout dedup; halt/observe-only cycles still POST |
| 3 | `book_owner.py` | hook observe **before** skip continues; `place=False` still observes |
| 4 | `bridge.py` | admit observe even when 0 realized units |
| 5 | `cycle.py` | POST evaluate() instead of injected-only |
| 6 | `policy_c_admit.py` | replace 4-voter static with evaluate() Choice |
| 7 | `sleeve_select.py` | POST JEV_SLEEVE_SELECT Choice (APPLY still 0) |
| 8 | `compose.py` | fail-closed dark → no size-up |
| 9 | `apply_size.py` | reuse deduped answers; dark → 1.0 and stamp dark |
| 10 | `regime_system_one.py` | optional live evaluate() under `GTOS_JEV_S14_CALL` |
| 11 | `world_questions.py` / `rdf_questions.py` | call through `evaluate` with pack questions |
| 12 | tests | budget 500000; fail-closed; observe-on-skip |

No land on VPS. Chair APPLY later after hist-prove.

---

## 1. `jev_client.py` — budget + gate wrapper

```python
# DRAFT — do not apply from this session
API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MAX_CALLS = 500_000  # was 200; env GTOS_JEV_MAX_CALLS still wins

def evaluate(
    state: dict[str, Any],
    *,
    timeout_s: float = 8.0,
    model: str = MODEL,
    questions: dict[str, Any] | None = None,
    gate_id: str | None = None,
) -> dict[str, Any]:
    """POST /v1/systemone. Never raises into a fire path. Never places."""
    ...
    payload = {
        "state": state,
        "model": model,
        "questions": questions if questions is not None else symbol_fanout_questions(),
    }
    # existing urllib POST; stamp gate_id on receipt only (not sent as inference)
```

**Fail-closed helper (new):**

```python
def dark(receipt: dict[str, Any] | None) -> bool:
    if not receipt:
        return True
    if receipt.get("ok") is True and receipt.get("answers"):
        return False
    return True  # skipped / error / empty answers


def fail_closed_stand(receipt: dict[str, Any] | None, *, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "dark": True,
        "decision": "STAND",
        "refuse_new": True,
        "size_mult": 1.0,       # cannot size-up when dark
        "place": False,
        "reason": reason or (receipt or {}).get("skipped") or (receipt or {}).get("error") or "jev_dark",
        "never_place": True,
    }
```

Dedup cache (process-local):

```python
# key = sha256(json(state, sort_keys=True) + questions_id)
# GTOS_JEV_FANOUT_DEDUP=1 default-on
def evaluate_dedup(state, *, questions=None, gate_id=None) -> dict:
    ...
```

`GTOS_JEV_PER_GATE_POST=1`: bypass dedup (ablation). Default 0.

---

## 2. Observe every candidate (`a1_log.py` + `book_owner.py`)

**Today:** observe only after `_spread_cost_screen`, and only if A1 flags on. `run_cycle(place=False)` never observes.

**Draft:**

```python
# book_owner.run_cycle — DRAFT splice, do not wholesale-copy 10k-line host file
def _maybe_observe_candidate(self, intent, tick, *, cost_skip, skip_reason, occupancy, governor, place):
    if not _usage_ramp_observe_on():
        return
    # env-gate BEFORE import (existing pattern)
    from src.judgment.a1_log import observe_candidate_once
    observe_candidate_once(
        intent, tick,
        extra={
            "skip_reason": skip_reason,
            "cost_skip": cost_skip,
            "place_flag": bool(place),
            "never_place": True,
        },
        occupancy=occupancy, governor=governor,
    )

def _usage_ramp_observe_on() -> bool:
    return (
        _env_on("GTOS_JEV_USAGE_RAMP_OBSERVE")
        or _env_on("GTOS_JEV_A1_LOG")
        or _env_on("GTOS_JEV_ALIVE_SHADOW")
    )
```

Call `_maybe_observe_candidate` on **every** skip append AND on the cost-screen survivor AND on `place=False` would_units. Must **not** mutate `cost_skip` / skip reason.

`observe_candidate_once`:

1. `intent_gold_state` / `intent_symbol_state` → COMPLETE_STATE (missing fields stay visible).
2. `evaluate_dedup(state)` **one** fanout POST.
3. Stamp all 48 fluid gate ids from answers (existing `observe_fluid_inventory` loop).
4. Write JSONL. `shadow_log_only=True`. `place=false`.

Dedup kills the 3+1+1 duplicate POSTs on survivors.

---

## 3. Fail-closed compose (`compose.py` / `apply_size.py`)

```python
# DRAFT
def compose_shadow(state, answers, *, ticket=None, extra=None, jev_receipt=None):
    extra = extra or {}
    if _env_on("GTOS_JEV_FAIL_CLOSED_DARK") and dark(jev_receipt):
        extra = {**extra, "jev_dark": True, "disposition": "stand_dark"}
        # live tilts stay 1.0; named_apply False; cannot size-up; cannot refuse envelope
    ...
```

`haircut_challenge_unit`: pass full receipt (not only `answers`). If dark and fail-closed: skip haircut, stamp receipt, **do not** invent 1.15.

Physical APPLY still Challenge login/ns only. W7 untouched.

---

## 4. Policy C — actually POST evaluate()

Today `evaluate_policy_c` is a static if/else on 4 voters. Inventory calls it JEV_JUDGED; it is not a TypeSafe call.

```python
# DRAFT policy_c_admit.py
POLICY_C_QUESTIONS = {
    "policy_c_choice": {
        "type": "choice",
        "instructions": (
            "Given COMPLETE_STATE (alive_menu, regime_tag, conf_band, session_fit, "
            "phi, cost, occupancy, hard_off_hit, full_state_dark, n_incomplete, news_join) "
            "pick admit posture. Do not invent news. House hard-offs stay integers. Never place."
        ),
        "criteria": {
            "A_STAND_DOWN": "full_state_dark or named tape/cost argues stand",
            "C_SIZE_TRIM": "incomplete but not dark — size 0.75",
            "D_FULL": "state sufficient — admit full",
        },
    }
}

def evaluate_policy_c(state):
    if not state or state.get("state_missing"):
        return {..., "reason": "STATE_MISSING", "skip": True, "place": False}
    from .jev_client import evaluate, dark, fail_closed_stand
    rec = evaluate(dict(state), questions=POLICY_C_QUESTIONS, gate_id="POLICY_C")
    if dark(rec):
        if _env_on("GTOS_JEV_FAIL_CLOSED_DARK") and policy_c_apply_env():
            return {**fail_closed_stand(rec, reason="policy_c_jev_dark"), "place": False}
        return {..., "reason": "STATE_MISSING", "skip": True}  # honest if APPLY off
    choice = (rec.get("answers") or {}).get("policy_c_choice", {}).get("choice") or "D_FULL"
    refuse = policy_c_apply_env() and choice == "A_STAND_DOWN"
    return {"Choice": choice, "refuse": refuse, "place": False, "jev": rec}
```

Admission hook (Admin dirty tree, not in `_pr41_land` admission.py — Chair land later): `_refuse(..., "policy_c_stand_down")` only when `refuse=True`. This sketch does not edit live admission.

Keep 4-voter as **shadow comparator** for ablation, not as live judge.

---

## 5. Sleeve select — POST Choice, APPLY=0

```python
# DRAFT sleeve_select.py
def evaluate_sleeve_select(symbol, state, menu) -> dict:
    questions = {
        "JEV_SLEEVE_SELECT": {
            "type": "choice",
            "instructions": "Pick one alive affinity KEEP sleeve or HOLD/ABSTAIN/ESCALATE_CHAIR/BLOCKED. Never Package B alias to sub_mid_dn_revert. Never place.",
            "criteria": {c.id: c.rubric for c in menu.criteria},  # cap 255
        }
    }
    rec = evaluate(state, questions=questions, gate_id="JEV_SLEEVE_SELECT")
    payload = emit_sleeve_select_shadow_payload(...)
    payload["jev"] = {k: rec.get(k) for k in ("ok","skipped","error","model","usage")}
    payload["apply"] = False  # global APPLY stays 0
    payload["place"] = False
    return payload
```

Scoped XAU/GBPJPY conflict bits remain Chair-owned. This session only makes the **POST** exist.

---

## 6. Fluid cycle / S14 / everywhere — one POST per cycle

```python
# DRAFT cycle.py inner
if _env_on("GTOS_JEV_FLUID_CYCLE_CALL") and not answers:
    from .jev_client import evaluate
    from .jev_questions import symbol_fanout_questions
    from .everywhere import EVERYWHERE_QUESTION_PACK
    from .regime_system_one import build_question_pack
    q = {}
    q.update(symbol_fanout_questions())
    q.update(EVERYWHERE_QUESTION_PACK)
    if _env_on("GTOS_JEV_S14_CALL"):
        q.update(build_question_pack(sleeve=...))
    rec = evaluate(dict(gold_state or {}), questions=q, gate_id="FLUID-CYCLE")
    if dark(rec) and _env_on("GTOS_JEV_FAIL_CLOSED_DARK"):
        # log sidecar; APPLY stays false; no LABEL draft
        ...
    merged_answers = rec.get("answers") or {}
```

World / RDF: second POST only when those blocks are assembled (`completeness` true). Unassembled → skip pack (honest), still POST fanout.

---

## 7. Place-fluid / occupancy / two-stop / hard-off exception

**Observe now, decide APPLY later.** Question drafts (add to fanout or pack):

| gate family | primitive | labels | APPLY |
|---|---|---|---|
| place_fluid FLUID-PLC-* | Choice | PLACE / STAND / DELAY | off until hist |
| occupancy remint | Choice | HOLD / REMINT / FLATTEN_ADD | off |
| two-stop exception | Choice | REMINT_OK / STAND / SWITCH_SLEEVE / FLATTEN_SIBLING | COUNT integer stays |
| hard-off exception | Choice | KEEP_OFF / SCOPED_EXCEPTION | walls stay default |
| conf_gate | Choice | YES / NO / UNSURE | SHADOW |
| pretrade cost | Score | COST_OK / TRIM / STAND | static 0.10 remains envelope until hist |
| governor derisk | Score | block / trim / full | hard DD / circuit stay envelope |

`veto.py` still raises `JevPlacePathVeto` if a fluid APPLY tries `place`/`order_send`. Owner override means **design** may return PLACE; writer execute only after Challenge hist-prove + Chair APPLY. This sketch never calls `router.place`.

---

## 8. Env recipe (Challenge f5-live only — Chair sets)

```text
GTOS_JEV_MAX_CALLS=500000
GTOS_JEV_A1_LOG=1
GTOS_JEV_ALIVE_SHADOW=1
GTOS_JEV_USAGE_RAMP_OBSERVE=1
GTOS_JEV_FANOUT_DEDUP=1
GTOS_JEV_PER_GATE_POST=0
GTOS_JEV_FAIL_CLOSED_DARK=1
GTOS_JEV_FLUID_GATES_SHADOW=1
GTOS_JEV_FLUID_CYCLE_CALL=1
GTOS_JEV_SLEEVE_SELECT_SHADOW=1
GTOS_JEV_SLEEVE_SELECT_CALL=1
# GTOS_JEV_SLEEVE_SELECT_APPLY stays 0
GTOS_JEV_POLICY_C_APPLY=1
GTOS_JEV_APPLY_LIVE=1          # size tilts Challenge-only; already named
GTOS_JEV_S14_CALL=1
GTOS_JEV_WORLD_CALL=1
GTOS_JEV_RDF_CALL=1
GTOS_JEV_CONF_GATE_CALL=1
# do not set on W7 / redacted_account
```

---

## 9. Tests (sketch)

- `test_default_max_calls_500000`
- `test_budget_env_override`
- `test_fail_closed_stand_on_skip`
- `test_observe_called_on_skip_reason` (book_owner unit with fake intent)
- `test_fanout_dedup_one_post`
- `test_policy_c_posts_evaluate` (mock urlopen)
- `test_sleeve_select_apply_remains_0`
- `test_never_place_in_receipt`
- `test_news_missing_still_posts`

---

## 10. Explicit non-goals

- No `order_send`, no `router.place`, no remint/flatten from Jev this pass.
- No global sleeve-select APPLY.
- No invent NEWS_PROTOCOL / DXY / yields.
- No merge Module_ATR R with Dig_3R.
- No live VPS file write from this session.
- Chair ENFORCE/VETO/LABEL only from Chair.

---

## 11. Expected usage after Chair land (order of magnitude, not a promise)

| mode | req / 7d (rough) vs 666 |
|---|---|
| now (survivor-only, budget 200) | 666 |
| observe every candidate, 1 fanout POST, budget 500k | tens of thousands (writer cadence × n_intents) |
| + cycle/policy_c/sleeve_select/s14 packs | +1 POST per cycle + 1 per conflict/admit |
| `PER_GATE_POST=1` ablation | ×48 — **do not** enable on live |

Cost stays small in dollars (Jev 0-output-token class) even when req count ramps. Cheapness today is **coverage**, not unit price.

Gate to APPLY (fire-rate changing): Challenge hist-prove receipt — see `HIST_PROVE_PLAN.md`.
