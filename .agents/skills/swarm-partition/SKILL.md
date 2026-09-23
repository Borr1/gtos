---
name: swarm-partition
description: Divide the one live system into pieces that already exist. Each Grok CLI session owns its files and finishes that piece. The link attaches them once.
---

# Swarm partition

Do not put the whole path on one agent.

1. Name the pieces that already exist. Each piece is a file set nobody else edits.
2. One Grok CLI session per piece, on the Mac, cwd `/Users/borr/GTOSActive/jev-live-swarm`. Model `grok-4.7`, effort `xhigh`.
3. The session makes that piece perfect. It does not invent a second system. It does not edit another piece's files.
4. No session taskkills the writer. Copy the finished bytes to the host. The link is one reload after the pieces are ready.
5. Quality over speed. A piece that only reads has failed. A scattered extra file has failed.

The pieces of this pass are in `/cursor/stores/self/docs/SWARM_PARTITION.md`.
