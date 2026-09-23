---
name: worker-model
description: Always the latest model at max effort for agents and Grok CLI sessions. Do not choose Grok 4.6.
---

# Worker model

Borhen, 2026-09-22: always the latest model, max effort, for agents and for Grok CLI sessions.

- Agents: pass `model: grok-4.7-xhigh` on every `CreateAgent`.
- CLI: `grok --model grok-4.7 --effort xhigh`. This CLI accepts `low` `medium` `high` `xhigh`. `--effort max` was rejected 2026-09-22. Use `xhigh`.
- Do not pass `cursor-grok-4.6-xhigh`.
- If `grok-4.7-xhigh` is rejected, say so in chat that turn. Do not open the next session on 4.6.
- Leaving `model` blank was also refused (2026-09-22, twice): `Requested resource was not found`. Do not treat a blank model as a way onto 4.7.
- Do not retry a rejected slug unchanged.
- Live hops run in Grok CLI on the Mac. Skill: grok-cli.
