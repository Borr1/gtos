# Jev sidecar design for GTOS (from 2026-09-16 lab)

Status: **design only**. Live API paused until owner supplies a stable key. Never on place/remint/flatten.

## What the lab proved
- `jev-latest` / `jev-preview` return Choice / Score / Noul with probabilities + confidence in ~140–230ms.
- Fan-out of many atomic questions in one call stays ~same latency class (~169ms for 12 Nouls).
- GTOS-shaped schemas work:
  - Admit: can return `admit` at **low confidence (0.33)** → code must escalate, not fire.
  - Close label: `orig_stop` at confidence **1.0** on clear SL exit.
  - Corr HOLD: strong cluster + `audit_only` at **1.0**, flatten **0%** when criteria forbid it.
  - Garbage state: refuse (`no`) + very low surety (0.13).

## Architecture (Fable tissues)
| Layer | Role |
| --- | --- |
| Writer / printer | Unchanged. Places from tags + token. |
| Jev sidecar | Offline + online **scores/labels/HOLD drafts** only |
| Chair (redacted_account) | Speaks ENFORCE/VETO/LABEL; may ignore sidecar |
| Code policy | Combines atomic answers + confidence thresholds |

## Confidence gates (v0 proposal)
- `admit.confidence < 0.55` → **abstain / escalate** even if choice==admit
- `action_scope` must never be flatten; if model ever returns flatten → treat as broken schema / refuse
- Close-label: accept exit_class when confidence ≥ 0.8; else chair LABEL from broker facts only
- Corr HOLD draft: speak HOLD only if `speak_hold` noul ≥ 0.6 **and** hold_strength ≥ 1.5 **and** action_scope in {audit_only, block_sibling_prefills}

## Schemas to productize (JSON in judgment/live)
1. `jev_admit_v1` — state from slate candidate + surface law digest
2. `jev_close_label_v1` — state from close webhook + deals
3. `jev_corr_hold_v1` — state from cluster slate
4. Batch offline: map Challenge closes → exit_class / toxic remint scores for Challenge-true scoreboard

## Explicit non-goals
- No Jev on broker send path
- No replacing chair cards with model prose
- No auto splice from Jev scores without owner Nightly Decide

## Next when key returns
1. Replay Challenge close pack through `jev_close_label_v1` (calibration check).
2. Shadow-mode admit on live slate candidates (log only).
3. Wire results under `judgment/live/jev_sidecar/` with audit ids.

## Key handling
- Use `TYPESAFE_API_KEY` env / secret-request only.
- Do not paste keys in chat.
