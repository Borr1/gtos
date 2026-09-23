---
name: learn-a-skill
description: When a session hits a real limitation, or rebuilds a check it has already done, write or update a short skill in the same turn so the next ask does not rediscover it. Use after a failed prompt, a host quirk, a wrong tree, a repeated hesitation, or any procedure reconstructed from ssh and logs.
---

# Learn a skill

A limitation that stays in chat gets repeated. A check rebuilt from logs gets repeated too. Write it down the same turn, including when the check succeeded.

1. One limitation, one short skill under `/cursor/stores/user/skills/<name>/SKILL.md`.
2. Link it from the top of `/cursor/stores/user/preferences.md`.
3. Put the same failure in one line of `/cursor/stores/user/workflows/session-prompt.md` so the next prompt starts from it.
4. Also copy the skill into `/workspace/.agents/skills/<name>/SKILL.md` when it is about how GTOS work is done.
5. Keep it short enough that the next session obeys it instead of re-reading the whole history.

Do not add a second copy of a rule he already struck.
