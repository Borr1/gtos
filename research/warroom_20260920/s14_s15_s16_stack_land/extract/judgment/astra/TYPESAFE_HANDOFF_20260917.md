# Project gtos — TypeSafe / Jev handoff (owner 2026-09-17)

Ingested into the repo on 2026-09-17 so the Cursor Project coordinator (Fable)
can continue without re-onboarding. Source: owner handoff plus official TypeSafe
skill body. Job 1 below (install skill + sidecar into shared context) is **done
in this tree**. Remaining jobs stay open.

You are the **gtos** Project coordinator (Fable). Install/use the TypeSafe skill
for all Jev work.

## Skill (now in-repo)

- Local skill (use this first): [`.agents/skills/typesafe-ai/SKILL.md`](../../.agents/skills/typesafe-ai/SKILL.md)
- Local MIT license (fetched from upstream 2026-09-17): [`.agents/skills/typesafe-ai/LICENSE`](../../.agents/skills/typesafe-ai/LICENSE)
- Official: https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md
- Re-install if the local copy is missing: `npx skills add typesafe-ai/skills --skill typesafe-ai`
- Live docs index: https://docs.typesafe.ai/llms.txt
- Sidecar design: [`JEV_SIDECAR_DESIGN_20260916.md`](JEV_SIDECAR_DESIGN_20260916.md)
- Lab probes: [`lab/SUMMARY.md`](lab/SUMMARY.md)
- Index: [`README_TYPESAFE.md`](README_TYPESAFE.md)

## House law (GTOS)

- Challenge login **0**, pass **$110k**, magic **0**
- Verification login **0** is **quarantined** — do not shadow-batch it
- Jev = **intelligence/info sidecar only** — admit scores, close labels, HOLD drafts
- **Never** place / remint / flatten / move SL from Jev
- Chair redacted_account speaks ENFORCE/VETO/LABEL; writer prints
- Surface: US30 off; hard-off bleed/orb_crypto/idxrev/xa_huge/mx_us30; keep spring+vss; 2-stop circuit
- `TYPESAFE_API_KEY` lives in env / Cursor Cloud / Project secrets only. Never
  commit it. Never paste it in chat. This ingest made **no** live API calls.

## Already proven (2026-09-16 lab)

See `JEV_SIDECAR_DESIGN_20260916.md` + `lab/SUMMARY.md`:

- ~140–230ms; fan-out 12 Nouls ~169ms
- Admit can be low-confidence → escalate
- Close label orig_stop @ conf 1.0
- Corr HOLD audit_only @ 1.0, flatten 0%
- Garbage state refuses confidently

## Your jobs

1. **DONE in this tree.** TypeSafe skill + sidecar design ingested at
   `.agents/skills/typesafe-ai/` and `judgment/astra/`.
2. Design shadow-mode schemas: `jev_admit_v1`, `jev_close_label_v1`,
   `jev_corr_hold_v1`.
3. When owner provides `TYPESAFE_API_KEY` in Project/Cloud env secrets (not
   chat), run shadow batch over Challenge closes (**log only**).
4. **Superseded as policy.** Do not propose KEEP thresholds from Challenge
   45. V2: house laws + feature-complete state; confidence is secondary.
   Nightly Decide (`n≥40` / `2·SE`) + owner word still gate any splice.
   Project distillates `MAC_INGEST` / `OWNER_LAW` / `ASTRA_ARCH` /
   `NEWS_PROTOCOL` are not in this git tree.

Ask owner for a stable API key in Cursor Cloud Agents environment Secrets for
`Borr1/ai-trading-agent` (or Project secrets) — not pasted in chat.
