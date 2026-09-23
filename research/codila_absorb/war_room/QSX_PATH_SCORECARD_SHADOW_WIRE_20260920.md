# QSX PATH SCORECARD — SHADOW Wire SPEC (Dig FIRE)

**as_of:** 2026-09-20T19:00:14+07:00 (ICT+7)  
**role:** Dig (Open Source Dig) · Chair LABEL · SHADOW Score emitter only  
**steal:** `STEAL-QSX-PATH-SCORECARD`  
**upstream (cite only):** https://github.com/jianweiweng05/qsx-strategy-score (MIT)  
**schema twin:** `QSX_PATH_SCORECARD_SHADOW_WIRE_20260920.json`  
**CL copies:** `close_loop/war_room_20260920/QSX_PATH_SCORECARD_SHADOW_WIRE_DIG_20260920.{md,json}`

## Laws
- `place=false` always
- `promote_grade_to_admit=false` — NEVER promote grade→admit / `live_armed_set`
- Dig does **not** edit `live_armed_set`
- No invent NEWS · no host-mesh
- Affinity **instrument×sleeve > global**
- Cost never kill-gate
- Patterns absorb — do **not** dump foreign QSX code wholesale

## Purpose
Wire typed `path_scorecard{score, grade, random_timing_p, beta, maxdd}` into **warroom_shadow train/sidecar fields only**. Screening evidence before claim — not an entry bot, not place permission.

## Typed field

| key | type | notes |
|---|---|---|
| `score` | float 0–100 | path-quality composite |
| `grade` | enum | `PROVISIONAL` / `GOLD` / `SILVER` / `BRONZE` / `NEEDS_WORK` / `FLAGGED` — SHADOW label; **GOLD ≠ place** |
| `random_timing_p` | float [0,1] | vs random-timing null |
| `beta` | float | buy-and-hold / benchmark beta |
| `maxdd` | float | max drawdown (unit in sidecar meta) |

## Wire sites (existing names only)
1. **`CL-JEV-CONF-SHADOW`** — fuse score/grade into conf_shadow evidence; conf ≠ permission
2. **`S15-COST-OF-ERROR-CONF`** — FLAGGED/NEEDS_WORK → REVIEW / cost feature; never kill-gate
3. **`CFE-SLEEVE-FAMILY-HOLD-HONEST`** — hold-honest claim grade vs optimistic full-sample

## Fanout field names to add (Chair absorb)
```
shadow.jev.path_scorecard.score
shadow.jev.path_scorecard.grade
shadow.jev.path_scorecard.random_timing_p
shadow.jev.path_scorecard.beta
shadow.jev.path_scorecard.maxdd
shadow.jev.path_scorecard.instrument
shadow.jev.path_scorecard.sleeve_id
shadow.jev.path_scorecard.affinity_cell
shadow.jev.path_scorecard.place          # const false
shadow.jev.path_scorecard.promote_grade_to_admit  # const false
shadow.jev.path_scorecard.apply          # const false
```

## Affinity scope
- Attach **per affinity cell / train row** (`symbol|sleeve_id`), never one global scorecard.
- Example cells: `crypto|session_sleeve`, `XAG|metal_sleeve`, `EURGBP|vss_fxcross`.

## Train row example (shape only)
```json
{
  "login": "0",
  "ticket": 291794419,
  "symbol": "XAUUSD",
  "asset_class": "metal",
  "sleeve_id": "dsp_spring_close",
  "affinity_cell": "XAUUSD|dsp_spring_close",
  "session": "London",
  "path_scorecard": {
    "score": 72.5,
    "grade": "PROVISIONAL",
    "random_timing_p": 0.18,
    "beta": 0.42,
    "maxdd": -0.12
  },
  "shadow.jev.apply": false,
  "shadow.jev.place": false,
  "promote_grade_to_admit": false,
  "note": "example shape only \u2014 Dig does not invent NEWS or claim this ticket's real QSX score"
}
```

## Emitter stub
Optional minimal stub: `shadow_emitters/path_scorecard_shadow.py` — accepts/computes typed dict, writes sidecar JSONL. Schema + recipe preferred over copying QSX.

## Blockers
- Hosted QSX thresholds may move pre-v1
- GOLD grade ≠ place permission
- Dig must not treat grade as admit
- Free screener ≠ full QuantStats tearsheet

## Dig idle note
Subtask done when SPEC + stub + CL copies land. Dig does **not** wire live cycle, does **not** patch VPS `warroom_shadow_jev_fanout_fields.json`, does **not** edit `live_armed_set`. Chair / Close Loop absorb.

## Refs
- `CHAIR_SWARM_SCORE_STEALS_TOP10_20260920` steal #1
- `shadow_hook_stubs/P0_*` + SYSTEM_ONE recipes
- `judgment/warroom_shadow/` conf_gate + cycle
- `JEV_EVERYWHERE_SURFACE_MAP`
- `warroom_shadow_jev_fanout_fields.json`
