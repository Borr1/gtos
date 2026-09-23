# Wave E — executable Jev tissue (2026-09-17)

Chair redacted_account / owner: stop docs-only. This wave **runs**. No place, remint, flatten, inbox write, or token mint.

## Owner process lock (Borhen, 2026-09-17)

**Shadow score first, then wire.** Not eternal shadow. Not same-pass blind live wire.

1. Challenge-true shadow scoring on real candidates / fires / opens
2. When a named gate proves out → **NAME**
3. Then **APPLY** that live wire (later commit, owner-spoken)

Code: `src/judgment/process_lock.py` (`LOCK_ID=shadow_score_then_wire`).
Prove: `scripts/jev_wire_prove.py` → `NOT_PROVED` | `PROVED_SHADOW`.
`live_size_tilt` stays **1.0**. `shadow_size_tilt` is the prove instrument.
`GTOS_JEV_W_NAMED` cannot open apply.

## What landed

| Piece | Path | Behavior |
| --- | --- | --- |
| Assembler | `src/judgment/gold_state.py` `assemble_gold_state_v0` | Closed `gtos.judgment.gold_state.v0` |
| News spines | `src/judgment/news_spine.py` + `scripts/jev_news_calendar_repair.py` | Official FF this-week fetch. Does **not** overwrite June `data/news_calendar.json` |
| A1 logger | `src/judgment/a1_log.py` | `GTOS_JEV_A1_LOG=1` writes JSONL. `GTOS_JEV_A1_CALL=1` + key POSTs Jev |
| UB-AUTH-010 | `src/components/ultimate_book/bridge.py` (unbound) | Default-off observe after admit. Decision unchanged |
| UB-PLC-017 | `src/components/ultimate_book/book_owner.py` (unbound) | Default-off observe at cost screen. `cost_skip` unchanged |
| SEL-V4-002 | `observe_sel_v4_002` only | **Not** imported by bound `selector_v4.py` (H1 / R2) |
| Gold lab | `scripts/jev_gold_lab.py --slice G-2W` | H4 × {long,short} JSONL on bar dates we have |
| Challenge shadow | `scripts/jev_challenge_shadow.py` | Sit + `--slate` + replay pack. Ticket 293332188 scored |
| Named-wire *candidate* | `src/judgment/compose.py` `f5_xau_flow_alignment_size_tilt` | Shadow Score → `[0.70, 1.15]`. Live tilt locked at 1.0 |
| Process lock / prove | `src/judgment/process_lock.py` + `scripts/jev_wire_prove.py` | Shadow first. APPLY closed this wave |

## Run

```bash
python3 scripts/jev_news_calendar_repair.py
python3 scripts/jev_gold_lab.py --slice G-2W
python3 scripts/jev_challenge_shadow.py \
  --sit judgment/astra/lab/challenge_shadow_20260917/sit_20260917.json
# after redacted_account drops latest_slate.json:
# python3 scripts/jev_challenge_shadow.py --slate judgment/astra/lab/challenge_shadow_20260917/latest_slate.json
python3 scripts/jev_wire_prove.py
python3 -m pytest tests/judgment -q
```

A1 on a process (log only, no send change):

```bash
GTOS_JEV_A1_LOG=1  # assemble+log
# GTOS_JEV_A1_CALL=1 TYPESAFE_API_KEY=…   # only when the key is in secrets
```

## Named first live wire (candidate — prove, then NAME, then APPLY)

**`W_named: f5_xau_flow_alignment_size_tilt`** on already-admitted XAU units.
This wave **scores** it. It does **not** apply it.
After `PROVED_SHADOW` on Challenge-true tape, owner **names** it.
APPLY is a later commit. Writer still prints.
Not a refuse. Not SEL-V4-002 (V4 has no live authority on F5).
Not a US30 lift. Not a leftover-ship carry.

## Do not

- Touch ticket 293332188 (leave orig, ~+3.9R at sit).
- Become the printer. Chair verbs stay ENFORCE/VETO/LABEL.
- Invent HIGH for 2026-09-09..12 if this-week FF starts later.
- Edit `selector_v4.py` (R2-bound; reseal is 16.5h/window, not safety theater).
