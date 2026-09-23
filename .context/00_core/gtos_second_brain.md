# GTOS Second Brain

Status: local owner-intelligence vault linked to Context OS.

Purpose: preserve raw owner ideas without polluting agent context, then distill
them into graph-friendly, labeled retrieval intelligence for future GTOS work.

Default vault path:

```text
/Users/borr/Documents/gtos/second-brain
```

This path is the stable agent path. It is symlinked to the Obsidian
app-specific iCloud container so the same vault is visible to Obsidian Mobile:

```text
/Users/borr/Library/Mobile Documents/iCloud~md~obsidian/Documents/GTOS Second Brain
```

The older plain iCloud Drive copy under
`/Users/borr/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/GTOS Second Brain`
is backup-only and should not be used as the active Context OS root.

Raw idea inbox:

```text
/Users/borr/Documents/gtos/second-brain/inbox
```

Open `/Users/borr/Documents/gtos/second-brain` as an Obsidian vault to inspect
notes visually. Obsidian Graph View will use the generated wikilinks, tags, and
frontmatter. Context OS also generates:

```text
/Users/borr/Documents/gtos/second-brain/graph/SECOND_BRAIN_INDEX.md
/Users/borr/Documents/gtos/second-brain/graph/SECOND_BRAIN_GRAPH.mmd
/Users/borr/Documents/gtos/second-brain/graph/SECOND_BRAIN_GRAPH.json
```

## Authority Boundary

- `inbox/` is raw owner thinking. It is preserved, searchable on request, and
  never direct agent authority.
- Distilled cards are retrieval intelligence. They help agents find the right
  methodology, hypothesis, warning, or implementation idea.
- Agents must verify actionable claims against current disk/source artifacts
  before implementing.
- Raw notes should not override `.context/LIVE_STATE.md`, route artifacts,
  code, tests, verifiers, broker truth, or current source evidence.
- Stale or emotional urgency should be distilled into a reusable rule, warning,
  or hypothesis instead of copied literally into future prompts.

## Commands

Create or repair the vault scaffold:

```bash
python3 scripts/gtos_context.py brain init
```

Capture an idea directly:

```bash
python3 scripts/gtos_context.py brain capture \
  --title "Idea title" \
  --body "Raw idea text..." \
  --tag selector \
  --tag methodology
```

Capture from a file:

```bash
python3 scripts/gtos_context.py brain capture \
  --title "Long idea dump" \
  --body-file /path/to/idea.txt
```

Distill the latest inbox note:

```bash
python3 scripts/gtos_context.py brain distill --latest
```

Search distilled brain notes:

```bash
python3 scripts/gtos_context.py brain search "selector scheduler context hygiene"
```

Regenerate visual graph artifacts:

```bash
python3 scripts/gtos_context.py brain graph
```

Include distilled brain intelligence in a Context OS pack:

```bash
python3 scripts/gtos_context.py pack \
  --task "<active task>" \
  --profile ultimate \
  --include-memory \
  --include-second-brain
```

Check whether the vault is helping or just accumulating raw notes:

```bash
python3 scripts/gtos_context.py health
python3 scripts/gtos_context.py brain status
```

`brain status` and `health` expose the distillation queue: recent raw inbox
notes that still need to become structured cards before agents should use them.

For route-owned work:

```bash
python3 scripts/gtos_context.py pack \
  --task "<active task>" \
  --profile ultimate \
  --include-memory \
  --include-second-brain \
  --route final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
```

## Vault Layout

- `inbox/`: raw idea dumps.
- `distilled/`: general distilled cards.
- `doctrine/`: stable principles and durable working doctrine.
- `hypotheses/`: testable ideas that need evidence.
- `route-intelligence/`: route-specific observations and evidence pointers.
- `implementation-ideas/`: build ideas and code-level repair concepts.
- `agent-methodology/`: instructions about how agents should work, reason, and
  avoid past mistakes.
- `decisions/`: owner or implementation decisions with dates and sources.
- `templates/`: manual note templates.
- `graph/`: generated graph/index artifacts.
- `archive/`: old notes preserved out of active retrieval.

## Agent Use

Agents should use second-brain context only through:

```bash
python3 scripts/gtos_context.py pack --task "<task>" --include-second-brain
python3 scripts/gtos_context.py brain search "<query>"
python3 scripts/gtos_context.py mcp-stdio  # for Codex/Claude/Cursor MCP use
```

They should not bulk-load the whole vault. They should not treat raw inbox notes
as active instructions. The correct workflow is:

```text
raw idea -> distilled card -> context-pack hit -> source verification -> action
```

Context OS health reports whether raw inbox notes are outpacing distilled cards.
That warning is a prompt to distill useful owner thinking into structured cards,
not a license to execute raw notes literally.
