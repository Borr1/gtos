# TypeSafe / Jev — Project gtos index

**Owner direction (2026-09-17):** Jev is the **living decision tissue inside GTOS**,
not a conservative refuse sidecar. The foundation (printer, selector, scheduler,
market connects, logs) already works and is fast. Wrong trade = missing state or
wrong calculation. With complete structured state, Jev runs **through the gates**
via Choice / Score / Noul; code composes; static `if`s become fluid ranges.

> **Architecture of record:** [`JEV_ALIVE_ORGANISM_20260917.md`](JEV_ALIVE_ORGANISM_20260917.md).
> What Jev *is:* [`JEV_WHAT_IT_IS_RESEARCH.md`](JEV_WHAT_IT_IS_RESEARCH.md).
> XAUUSD closed state: [`JEV_GOLD_STATE_SCHEMA_DRAFT.md`](JEV_GOLD_STATE_SCHEMA_DRAFT.md).
>
> **V2 is still correctness, not ambition.** [`JEV_INTEGRATION_V2_20260917.md`](JEV_INTEGRATION_V2_20260917.md)
> still binds: no place / remint / flatten, no invent NEWS, no Challenge-45 KEEP
> grid, LIVE vs STUDY clocks, chair writes inbox. Calling V2 “the design of
> record” **underestimates** the owner. V2’s refuse-sidecar cap is **incomplete**
> vs this vision. Design *for* Jev-in-gates. Shadow-first until a **named** live
> wire is proven.
>
> V1 / 45-row sweep numbers are **calibration evidence only** — do not treat
> 0.55 / 0.80 / geo≥1.0 or the +$406 counterfactual as a LIVE KEEP policy.
> Honest autopsy: [`JEV_V1_CRITIQUE.md`](JEV_V1_CRITIQUE.md).
>
> This standalone GitHub Cloud agent is **not** the Cursor Project `gtos`
> Fable coordinator. Project distillates `MAC_INGEST`, `OWNER_LAW`, `ASTRA_ARCH`,
> `NEWS_PROTOCOL` are **not in git** (V2 §8). Do not treat `.context/` 2026-06
> maps as F5 fire-path. **No live wiring from these docs. No place.**

## Read in this order

1. TypeSafe skill — [`.agents/skills/typesafe-ai/SKILL.md`](../../.agents/skills/typesafe-ai/SKILL.md)
   (MIT: [`.agents/skills/typesafe-ai/LICENSE`](../../.agents/skills/typesafe-ai/LICENSE);
   live docs: https://docs.typesafe.ai/llms.txt)
2. **What Jev is** —
   [`JEV_WHAT_IT_IS_RESEARCH.md`](JEV_WHAT_IT_IS_RESEARCH.md)
   (System One, RLCD, Choice / Score / Noul, GTOS fit, limits)
3. **Alive organism (owner direction)** —
   [`JEV_ALIVE_ORGANISM_20260917.md`](JEV_ALIVE_ORGANISM_20260917.md)
   (every major W7 / F5 / selector / scheduler gate → outcome + primitive + wire class;
   gold lab G-2W / G-2M / G-10M)
4. **Gold state draft** —
   [`JEV_GOLD_STATE_SCHEMA_DRAFT.md`](JEV_GOLD_STATE_SCHEMA_DRAFT.md)
   (`gtos.judgment.gold_state.v0` — sessions, levels, news spine, sleeve, cost, geometry)
5. V2 correctness contract (do not drop) —
   [`JEV_INTEGRATION_V2_20260917.md`](JEV_INTEGRATION_V2_20260917.md)
6. V1 critique (why the sweep is not a gate) —
   [`JEV_V1_CRITIQUE.md`](JEV_V1_CRITIQUE.md)
7. Owner handoff — [`TYPESAFE_HANDOFF_20260917.md`](TYPESAFE_HANDOFF_20260917.md)
8. Sidecar design + v0 lab gates (historical starting point) —
   [`JEV_SIDECAR_DESIGN_20260916.md`](JEV_SIDECAR_DESIGN_20260916.md)
9. Shadow-mode schemas —
   [`schemas/jev_admit_v2.json`](schemas/jev_admit_v2.json) **(F5 slate envelope)**,
   [`schemas/jev_admit_v1.json`](schemas/jev_admit_v1.json) (frozen lab),
   [`schemas/jev_close_label_v1.json`](schemas/jev_close_label_v1.json),
   [`schemas/jev_corr_hold_v1.json`](schemas/jev_corr_hold_v1.json)
10. 2026-09-16 lab probes — [`lab/SUMMARY.md`](lab/SUMMARY.md)

## Two layers, do not collapse them

| Layer | Job | Do not |
| --- | --- | --- |
| **Alive organism** | Map every gate to an **outcome question**. Assemble complete state. Jev answers Choice / Score / Noul. Code composes fluid ranges. Gold-first historical lab instead of wait-for-tomorrow. | Shrink this back into “sidecar only.” Treat chat seats as the decision engine. |
| **V2 correctness** | House integers stay code (token, 2-stop count, US30 / hard-off, H8 flatten-first). No invent NEWS. Challenge 45 is a mechanism pack, not a KEEP oracle. Shadow-first until a **named** live wire. | Delete house physics because the owner said “don’t put rules on it.” “No rules” means **judgment** is not a dead boolean — not that the writer may ignore a digest. |

Chat seats (Grokbot, Project coordinator) are **not** the decision engine. Jev is non-conversational structured decisions.

## Shadow schemas (landed)

Each schema stamps `mode: shadow_log_only` and `never_place: true`. They
validate a future log row; they do not call TypeSafe and they do not authorize
broker mutation. `jev_admit_v2` remains the F5 **slate envelope**. The gold-state
draft is the **XAUUSD body** that envelope (or a W7 intent envelope) should carry
under `state.gold` / `state.market` — not a replacement that silently drops
house-law fields.

| Schema | State | Code composition |
| --- | --- | --- |
| `jev_admit_v2` | slate-complete candidate + writer enrollment + house_law | **Primary:** house laws + feature-complete state. Confidence is **secondary** abstain/escalate (lab 0.55 floor). Never KEEP from a PnL grid. |
| `jev_admit_v1` | slim candidate + surface digest | **Frozen.** v0/V1 conf 0.55 and geo floors are **calibration evidence**, not policy. |
| `jev_close_label_v1` | close webhook + deals | accept `exit_class` only when the class is a charter noun; V1 0.8 floor is lab-starting. V2 / Alive require a real `time_stop` label (V1 missed 5/5 paying time_stops). |
| `jev_corr_hold_v1` | cluster slate | speak HOLD only if `speak_hold` ≥ 0.6 and `hold_strength` ≥ 1.5 and `action_scope` is `audit_only` or `block_sibling_prefills` |
| `gtos.judgment.gold_state.v0` | closed XAUUSD object (draft) | Assembler not yet wired. Empty news spine ≠ no HIGH. Pin `geometry_atr_basis`. |

`jev_corr_hold_v1` **forbids flatten**. `action_scope` enum is
`audit_only` | `block_sibling_prefills` only. A flatten choice or flatten
probability key is a broken schema: refuse and log. Do not flatten.

## Secrets

- Set `TYPESAFE_API_KEY` in Cursor Cloud Agents environment Secrets
  (`Borr1/ai-trading-agent`) or Project secrets when a shadow batch is
  actually run.
- Never commit the key. Never paste it in chat. Never invent one.
- Schema ingest and these architecture docs do **not** require a live TypeSafe
  call and must not make one.

## House law (short)

- Shadow / calibrate on Challenge **0** (pass $110k, magic 0).
- Verification **0** is quarantined.
- Chair redacted_account speaks ENFORCE/VETO/LABEL; writer prints from tags + token.
- Surface: US30 off; hard-off bleed/orb_crypto/idxrev/xa_huge/mx_us30; keep
  spring+vss; 2-stop circuit.
- Two fire-paths (W7 `ultimate_book` on this `main`, F5 Challenge on leftover-ship
  / `f5-live`). Do not splice `already_placed_today` onto isolated 15m re-entry.

## Next jobs (Fable / redacted_account)

Still no broker actions. Still no TypeSafe call until the owner places
`TYPESAFE_API_KEY` in secrets. Still no live wiring until a **named** site.

Implementing only `jev_admit_v2` refuse on close-reconstructs is **V2 again**.
The owner asked for gates as outcomes.

1. **Assembler** `assemble_gold_state_v0` (default-off, research). Write G-2W
   JSONL first. News fail-closed: if the committed calendar does not cover the
   as-of, `spine_empty=true` and event questions abstain. **Never invent HIGH.**
2. **A1 hooks (log only)** when the key is present — Alive §11 order:
   `UB-AUTH-010` (sized units vs named tape), `UB-PLC-017` (cost vs geometry),
   selector V4 merge (`SEL-V4-002`), close-label with `time_stop` in criteria.
3. **Gold lab:** G-2W fan-out → reliability sketch → G-2M → G-10M. Pre-register
   metrics before any Jev call. Calendar windows are the **bar dates we have**
   (`XAUUSD_M15.csv` ends 2026-04-17). See Alive §9.
4. Ingest Project gtos shared files named in V2 §8 **when they exist on disk**.
   Do not invent their contents.
5. Chair A2 only if `f5-chair-sit` can consume a draft **pre-fill**.
6. **Named live wire** — owner names the site (example: metals `ac60` band may
   read `persistence` Score). Until that sentence exists, no send-path AND.
7. Do not splice live tags without Nightly Decide (`n≥40` / `2·SE`) **and**
   owner word. V1 winner-keep constraints are out of contract.
8. Wire audit-id receipts under `judgment/live/jev_sidecar/` when a shadow
   batch actually runs.
9. **Challenge fluid-gate A1 (this tree):** shadow-first `ALIVE_MENU` +
   `CONF_GATE` + `DONE_OUTSIDE` in `src/judgment/`. Chair enable:
   [`../CHAIR_ENABLE_SHADOW_CHALLENGE.md`](../CHAIR_ENABLE_SHADOW_CHALLENGE.md).
   Steal source (Chair ENFORCE/LABEL, no re-read of X posts):
   [`../GTOS_SCORE_STEALS.md`](../GTOS_SCORE_STEALS.md). Schema:
   [`schemas/jev_fluid_gate_v1.json`](schemas/jev_fluid_gate_v1.json).
   Flags default off (`GTOS_JEV_FLUID_GATES_SHADOW`,
   `GTOS_JEV_FLUID_GATES_APPLY`). Jev still never places.
