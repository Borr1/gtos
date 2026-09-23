---
name: edit-gtos
description: Edit the GTOS repo whenever the change belongs in the system. Use for any GTOS code, config, test, research, or judgment change. Do not route around the repo or tell a session not to edit it.
---

# Edit GTOS

Borhen did not forbid editing GTOS. He ordered the opposite on 2026-09-22: do not avoid the repo, and do not invent a ban.

- Edit `/workspace` (the GTOS tree) when the change belongs in the system.
- Live is the destination, and it is priority 1. A repo edit is unfinished until the running Challenge writer has loaded it. Copy, compile on the host, reload that writer.
- Never worry about live risk. Discover the break on the live path and fix it there. Each gate has to be perfect, each one, from the first fact through the fill.
- A hotfix that exists only on the VPS host tree is unfinished until the same behavior is in the repo.
- Do not tell a worker "do not edit /workspace".
- Do not make a git worktree for this. Edit the checkout he is looking at.
- Do not commit unless he asked for a commit.
- Do not flatten, and do not stop `GTOS_W7_BookSupervisor`, because those were his orders, not a reason to skip the edit.
