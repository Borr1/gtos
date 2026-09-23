# DIG — REMINT / FLATTEN writer compose hooks — 2026-09-21

**as_of_ict:** `2026-09-21T06:15:32+07:00`  
**role:** Open Source Dig for GTOS/Jev Challenge → report to redacted_account  
**Chair WORD:** Owner unlocked Jev place 2026-09-21  
**scope:** Challenge `0` / `operator` / magic `0` when `GTOS_JEV_PLACE_APPLY=1`

## Gap closed

REMINT / FLATTEN_CANDIDATE were in `PLACE_CRITERIA` with `broker_effect=True`, but admission only refused STAND/DELAY — remint/flatten fell through as fresh PLACE. Dig arms pure writer compose + admission branch so:

| action | allow_fresh | remint | flatten | refuse_admit | admission |
|--------|-------------|--------|---------|--------------|-----------|
| PLACE | True | False | False | False | allow (existing) |
| STAND | False | False | False | True | refuse `jev_place_choice_stand` |
| DELAY | False | False | False | True | refuse `jev_place_choice_delay` |
| REMINT | False | True | False | True | refuse `jev_place_choice_remint` + stamp compose |
| FLATTEN_CANDIDATE | False | False | True | True | refuse `jev_place_choice_flatten_candidate` + stamp compose |
| SKIP_APPLY_OFF | False | False | False | False | gate idle |
| SKIP_NOT_CHALLENGE | False | False | False | False | gate idle |

## Deliverables (box)

1. `research/codila_absorb/war_room/jev_place_writer_hooks/writer_compose_place.py` — `compose_writer_intent`
2. `place_choice.py` updated — attaches `writer_compose` on every return (API compatible; `refuse_place` still STAND/DELAY only)
3. `admission_place_compose_patch.py` + `_vps_pull/admission_place_snippet.py` — REMINT/FLATTEN refuse + stamp
4. `book_owner_remint_flatten_consume.md` — **DRAFT** (no safe small LIVE hook landed)
5. This receipt + JSON

## VPS staging (`/workspace/gtos/_vps_pull/`) — parent CopyFromBox

| staged | VPS land path |
|--------|----------------|
| `writer_compose_place.py` | `src/judgment/writer_compose_place.py` |
| `place_choice.py` | `src/judgment/place_choice.py` |
| `admission_place_snippet.py` | splice into `src/components/ultimate_book/admission.py` |
| `admission_place_compose_patch.py` | helper / reference |

machineId (parent): `7cfa9657-805b-4e9c-9fbb-886c500f997b`  
Repo: `host-local\redacted_host\repo\`

## Smoke (box)

- import `compose_writer_intent` + `evaluate_place_choice` — OK
- fake receipts for each action — all assert_ok
- under APPLY with dark jev_client → DELAY + writer_compose attached
- APPLY off → SKIP_APPLY_OFF fail-closed compose
- **smoke_ok: true**

## Laws held

- Never invent NEWS_PROTOCOL / news / ON_SURFACE
- ENV-* integers unchanged
- Printer still prints
- Shadow MAX_POTENTIAL proves stay parallel
- No writer restart; no `live_armed_set` mutate
- Place effects only through place_choice + writer under Chair
- book_owner consume = **DRAFT** (not LIVE)

## book_owner consume

**DRAFT** — see `book_owner_remint_flatten_consume.md`. Writer reads `intent.details["jev_writer_compose"]` / `jev_remint_signal` / `jev_flatten_candidate`. No remint/flatten broker send from this Dig.
