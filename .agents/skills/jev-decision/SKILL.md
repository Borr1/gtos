---
name: jev-decision
description: Call System One (Jev) before locking a GTOS decision. Grok writes. Jev judges. Use on scope, architecture, ship vs leave-alone, and which hop this turn owns.
---

# Jev decision

Full text: `/cursor/stores/self/docs/JEV_SKILL.md`

POST `https://api.typesafe.ai/v1/systemone` model `jev-1.13.0`. Return is Noul, Choice, or Score. Empty, tie, and error do not restore a constant. Do not invent those numbers. Do not print the TypeSafe key.

Key on this VM: `/home/ubuntu/.gtos/typesafe.key` mode 0600.

Grok CLI sessions on the Mac still write the patch. This call only judges.
