#!/usr/bin/env bash
# Regenerate AGENTS.md (Codex briefing) from CLAUDE.md + Codex-specific preamble.
#
# Run this whenever CLAUDE.md is updated so Codex CLI stays in sync. Idempotent.
# Outputs to AGENTS.md at repo root.
#
# Usage:
#   bash scripts/sync_agents_md.sh
#
# Why this exists: Codex auto-loads AGENTS.md as system context, Claude Code
# auto-loads CLAUDE.md. We want both tools to share the same standing orders.
# Rather than maintain two near-identical files, AGENTS.md = preamble + CLAUDE.md.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [[ ! -f CLAUDE.md ]]; then
    echo "ERROR: CLAUDE.md not found at repo root" >&2
    exit 1
fi

{
cat <<'PREAMBLE'
<!--
This file is auto-loaded by OpenAI Codex CLI at session start.
Maintenance: regenerate after any CLAUDE.md change with:
  bash scripts/sync_agents_md.sh

Codex inherits the SAME instructions Claude Code does. Diffs from CLAUDE.md
that are Codex-specific live in the "CODEX-SPECIFIC NOTES" section below;
everything else is identical to CLAUDE.md.
-->

# AGENTS.md — Codex briefing for GTOS

> You are **OpenAI Codex CLI** working in the Gold Traders Operating System repo.
> The owner ("Borhen", "CEO") runs you in parallel with Claude Code due to
> usage-limit constraints. Treat this file as your standing orders. Everything
> below `## CODEX-SPECIFIC NOTES` is the canonical project briefing —
> follow it identically (it's an exact copy of `CLAUDE.md`).

---

## CODEX-SPECIFIC NOTES (read these first; differences from Claude)

### Working alongside Claude Code
- The CEO uses both tools. Either may have shipped commits since you last ran. **Always run the mandatory pre-flight first** — never reconstruct state from memory.
- Claude Code persists user memories at `C:\Users\MSI\.claude\projects\C--Users-MSI-Documents-ai-trading-agent\memory\` (`MEMORY.md` index + topic files). When relevant, read those files for historical CEO preferences and decisions — they are project context even though they live outside the repo. You do not write to that directory.
- For multi-step research workflows, the CEO often uses Claude's `/loop` for live monitoring. You don't need to mimic that — be self-contained per task.

### Image input
- `codex -i path/to/img.png` (repeatable) attaches images to a prompt. The CEO often shares MT5 / Telegram / browser screenshots — treat those as primary evidence.

### Model + effort
- Default model: `gpt-5-codex` (best for coding workflows on ChatGPT Pro).
- For pure research / analysis where coding is secondary, override with `-m gpt-5` for the larger general-purpose model.
- Reasoning effort is set to `high` globally. For maximum-effort one-offs (multi-day research synthesis): `codex -c model_reasoning_effort=high` (already the default; raise to "xhigh" if available in your version).

### Sandbox + approval
- Default sandbox: `workspace-write` (can edit files in cwd, blocks arbitrary system writes / network calls).
- Default approvals: `on-request` (you ask before running anything risky).
- Override per-session if needed: `--sandbox read-only` for pure analysis, or `--ask-for-approval never` (NOT recommended for live trading repo).

### Pre-flight before ANY task in this repo
1. `python scripts/generate_live_state.py` then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/current_vnext_system_map.md`.
3. Read `.context/00_core/current_repo_reading_order.md`.
4. Read the most recent session handoff (highest-numbered file in `.context/02_session_handoffs/`) as historical context only.
5. Read `.context/00_core/quick_reference_card.md`.
6. If your task is research, read `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md`.
7. If your task is cleanup/deletion/context repair, read `.context/00_core/repo_cleanup_and_staleness_policy.md` and the active cleanup route ledgers.
8. **Never assume the codebase is in the state you last saw it.** Both you and Claude commit; either could have shipped.

---

## ─── BEGIN CANONICAL CLAUDE.md (copy below; identical to repo CLAUDE.md) ───

PREAMBLE

cat CLAUDE.md
} > AGENTS.md

byte_count=$(wc -c < AGENTS.md | tr -d ' ')
line_count=$(wc -l < AGENTS.md | tr -d ' ')
echo "Wrote AGENTS.md: ${line_count} lines, ${byte_count} bytes"

# Sanity check: Codex's project_doc_max_bytes default is 32KB. If AGENTS.md
# exceeds 32KB, the global ~/.codex/config.toml MUST set project_doc_max_bytes
# higher (we set it to 200000 = 200KB for headroom). Warn if global config is
# missing or unset.
if [[ "$byte_count" -gt 32768 ]]; then
    if [[ -f "$HOME/.codex/config.toml" ]] && grep -q "^project_doc_max_bytes" "$HOME/.codex/config.toml"; then
        echo "OK: ~/.codex/config.toml already raises project_doc_max_bytes (required for ${byte_count}B AGENTS.md)"
    else
        echo "WARN: AGENTS.md is ${byte_count} bytes (>32KB Codex default). Add to ~/.codex/config.toml:" >&2
        echo "  project_doc_max_bytes = 200000" >&2
    fi
fi
