# Jev sidecar design for GTOS (from 2026-09-16 lab)

Status: **design only** (2026-09-16 lab). Live API paused until owner supplies
a stable key via env/secrets. Never on place / remint / flatten.

**Superseded as policy on 2026-09-17.** v0 confidence gates below are lab
starting points. The owner rejected the later V1 threshold sweep as a gate.
Current contract: `JEV_INTEGRATION_V2_20260917.md`. V1 numbers are
calibration evidence only (`JEV_V1_CRITIQUE.md`).

Authority for this note: 2026-09-16 lab probes (`lab/SUMMARY.md`) plus owner
house law in `TYPESAFE_HANDOFF_20260917.md`. This file is the durable sidecar
contract for Project gtos / Fable. It does not authorize broker mutation.

## What the lab proved

- `jev-latest` / `jev-preview` return Choice / Score / Noul with probabilities +
  confidence in ~140–230ms.
- Fan-out of many atomic questions in one call stays ~same latency class
  (~169ms for 12 Nouls).
- GTOS-shaped schemas work:
  - Admit: can return `admit` at **low confidence (0.33)** → code must escalate,
    not fire.
  - Close label: `orig_stop` at confidence **1.0** on clear SL exit.
  - Corr HOLD: strong cluster + `audit_only` at **1.0**, flatten **0%** when
    criteria forbid it.
  - Garbage state: refuse (`no`) + very low surety (0.13).

Successful named probes: 7; failed: 0. Per-probe answers live in
`lab/SUMMARY.md`.

## Architecture (Fable tissues)

| Layer | Role |
| --- | --- |
| Writer / printer | Unchanged. Places from tags + token. |
| Jev sidecar | Offline + online **scores / labels / HOLD drafts** only |
| Chair (redacted_account) | Speaks ENFORCE / VETO / LABEL; may ignore sidecar |
| Code policy | Combines atomic answers + confidence thresholds |

Jev is an **intelligence/info sidecar**. It may emit admit scores, close labels,
and HOLD drafts. It must never place, remint, flatten, or move SL.

## Confidence gates (v0 proposal)

These are lab-derived starting gates, not owner-ratified live thresholds.
Validate on Challenge data before any Nightly Decide splice.

- `admit.confidence < 0.55` → **abstain / escalate** even if choice==admit
- `action_scope` must never be flatten; if the model ever returns flatten →
  treat as broken schema / refuse
- Close-label: accept `exit_class` when confidence ≥ 0.8; else chair LABEL from
  broker facts only
- Corr HOLD draft: speak HOLD only if `speak_hold` noul ≥ 0.6 **and**
  `hold_strength` ≥ 1.5 **and** `action_scope` in
  `{audit_only, block_sibling_prefills}`

## Schemas to productize (JSON in `judgment/live`)

1. `jev_admit_v1` — state from slate candidate + surface law digest
2. `jev_close_label_v1` — state from close webhook + deals
3. `jev_corr_hold_v1` — state from cluster slate
4. Batch offline: map Challenge closes → `exit_class` / toxic remint scores for
   a Challenge-true scoreboard

## Explicit non-goals

- No Jev on the broker send path
- No replacing chair cards with model prose
- No auto splice from Jev scores without owner Nightly Decide
- No place / remint / flatten / SL-move from this sidecar
- No `TYPESAFE_API_KEY` in repo, chat, or committed config — env / secrets only

## Next when key returns

Key must arrive as `TYPESAFE_API_KEY` in Cursor Cloud Agents environment
Secrets for `Borr1/ai-trading-agent` (or Project secrets). Do not paste keys
in chat. No live API call is required to keep this design durable.

1. Replay Challenge close pack through `jev_close_label_v1` (calibration check).
2. Shadow-mode admit on live slate candidates (**log only**).
3. Wire results under `judgment/live/jev_sidecar/` with audit ids.

## Account surface (house law, not a broker action)

- Challenge login **0**, pass **$110k**, magic **0** — the
  calibration / shadow surface.
- Verification **0** is **quarantined**. Do not use it for Jev shadow
  batches.
- Surface: US30 off; hard-off bleed / orb_crypto / idxrev / xa_huge / mx_us30;
  keep spring+vss; 2-stop circuit.

## Key handling

- Use `TYPESAFE_API_KEY` env / secret-request only.
- Do not paste keys in chat.
- Do not invent a key or call TypeSafe from this ingest.
