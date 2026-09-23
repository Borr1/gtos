# GTOS Context OS

Status: context sidecar plus explicit owner second-brain capture infrastructure.

Purpose: give Codex, Claude, and future agents a compact, authority-ranked view
of GTOS context without loading every raw replay ledger, stale chat, historical
handoff, or large LFS artifact into the prompt.

Ultimate standard: Context OS should make an agent immediately oriented after
compaction, interruption, app restart, or parallel-agent churn. It should answer:
what is current disk authority, what is stale or raw, what continuity breadcrumbs
exist, what second-brain intelligence is retrieval-only, and which exact files
must be opened before concrete claims.

Posture standard: Context OS must increase agent strength, speed, and clarity.
It is not a caution layer. Health warnings are triage signals with exact repair
steps, not broad brakes. A healthy pack should push the agent to act decisively
from current disk evidence: open exact sources, patch/build/verify, preserve
evidence classes, and keep moving valid work forward.

This is not a trading goal session, replay harness, broker bridge, or autonomous
repair loop. It is a local context catalog, context-pack generator, and explicit
second-brain vault interface. The HTTP and stdio tool surfaces remain read-only;
only the `brain capture`, `brain distill`, `brain graph`, and related vault
commands write files, and those writes are outside trading/runtime authority.

## Agent Linkage

Context OS is now part of repo preflight for substantial Codex, Claude, route,
research, validation, and agentic work. After regenerating and reading
`LIVE_STATE`, the current system map, and reading order, agents should refresh
the catalog and generate a task pack:

```bash
python3 scripts/gtos_context.py build
python3 scripts/gtos_context.py pack \
  --task "<active task>" \
  --profile ultimate \
  --include-memory
```

The default build is concurrency-safe for parallel subagent preflight. Builders
serialize on a local catalog lock and later builders reuse a fresh equivalent
catalog instead of running duplicate full scans.

For a one-command context health view:

```bash
python3 scripts/gtos_context.py health
```

For a one-command restart/compaction resume view:

```bash
python3 scripts/gtos_context.py resume \
  --task "<active task>" \
  --profile ultimate
```

For route-owned work, include the route name:

```bash
python3 scripts/gtos_context.py pack \
  --task "<active task>" \
  --profile ultimate \
  --include-memory \
  --route final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
```

The pack is a retrieval map, not a replacement for source reads. If a pack
points at a current file, route artifact, verifier, or raw evidence pointer, the
agent must open the exact source before making concrete claims.

Packs now include `pack_diagnostics` with per-section elapsed time and
partial-result status. If an optional section times out, the pack still returns
with explicit section errors instead of leaving the MCP client hung.

For MCP or restart-sensitive use, prefer the bounded fast path:

```bash
python3 scripts/gtos_context.py pack \
  --task "<active task>" \
  --profile ultimate \
  --include-memory \
  --fast
```

Fast packs skip embedded health, use short per-section timeouts, and reuse the
existing catalog even when authority anchors changed. They return stale catalog
status as an explicit diagnostic instead of rebuilding inside an MCP/compaction
call. Run `python3 scripts/gtos_context.py build` for strict freshness and
`python3 scripts/gtos_context.py health` separately when process diagnostics are
needed.

Compaction recovery also checks for compact active-state files before broad
memory or second-brain recall:

```text
.context/context_os/ACTIVE_SESSION_STATE.json
.context/context_os/CURRENT_ROOT_CAUSE_MAP.json
```

These files are continuity intelligence, not proof. They should hold the latest
checkpoint/root-cause map, current replay prefix, incorporated subagent findings,
open patches, and next patch batch, then be verified against current disk before
action.

Owner second-brain intelligence can be added explicitly:

```bash
python3 scripts/gtos_context.py pack \
  --task "<active task>" \
  --profile ultimate \
  --include-memory \
  --include-second-brain
```

Second-brain notes are governed by `.context/00_core/gtos_second_brain.md`.
Raw inbox notes are preserved but not direct agent authority. Distilled cards
are retrieval intelligence only; agents still verify against current disk and
source evidence before acting.

Normal CLI packs and starters self-refresh when the catalog no longer matches
current `HEAD` or current authority anchors such as `.context/LIVE_STATE.md`.
This keeps fresh sessions moving from current disk evidence without requiring a
special flag. The underlying API and explicit `--no-auto-rebuild-stale` CLI mode
still fail closed for diagnostics. `--allow-stale` is an explicit exception flag
and should be used only for diagnostics.

For subagents or parallel agents, pass the pack text or exact Context OS command
set in their starter prompt. Subagents should not broad-scan raw JSONL ledgers by
default when a route overview or compact index can give exact paths first.

## Design Contract

- Current disk authority wins over chat, memory, old handoffs, and raw historical
  context.
- `.context/LIVE_STATE.md`, current system maps, reading order, quick reference,
  cleanup/staleness policy, and research doctrine are ranked as current
  authority anchors.
- Active code/config/tests are ranked above route artifacts for implementation
  questions.
- Route summaries, manifests, verifier outputs, reports, and dossiers are
  preferred before raw ledgers.
- Large JSONL/LFS/raw evidence stays cold by default. The catalog records and
  retrieves compact documents first; raw files are hydrated only by exact path
  when a task truly needs them.
- Recent session capsules are continuity hints. They preserve compact checkpoint
  facts after compaction/restart, but must be verified against current disk
  before action.
- Health warnings expose staleness, missing continuity, or raw-second-brain
  backlog as exact triage items. They should not make sessions passive or
  conservative; unrelated valid work continues while exact context issues are
  refreshed or repaired.
- Broker/live authority is not changed by context retrieval. This sidecar does
  not place trades, edit runtime state, restart services, or mutate credentials.

## Commands

Build or rebuild the local SQLite catalog:

```bash
python3 scripts/gtos_context.py build
```

Force an intentional rebuild even when an equivalent fresh catalog exists:

```bash
python3 scripts/gtos_context.py build --force
```

Check catalog freshness:

```bash
python3 scripts/gtos_context.py freshness
```

Show the full context-intelligence health state:

```bash
python3 scripts/gtos_context.py health
```

Build the full resume bundle after a restart, compaction, or agent handoff:

```bash
python3 scripts/gtos_context.py resume \
  --task "broad replay parity repair" \
  --profile ultimate \
  --include-second-brain
```

The resume bundle refreshes/reuses the catalog, writes a local ignored resume
capsule by default, reports health/process/git/context state, includes recent
continuity capsules, and embeds the task pack. Use `--no-write-capsule` for a
read-only resume probe.

Health and resume also include a workspace-hygiene contract: code/default search
roots, cold raw evidence globs, and the rule that raw ledgers are hydrated only
from exact route/source pointers.

By default this indexes only the current context anchors, `.context/00_core`,
compact active-state files, config, Context OS code/tests, and root docs. It does
not scan historical `.context` folders or `research/operations` on normal
preflight; raw and route evidence should be hydrated by exact route/source
pointer unless a task truly needs deep evidence search. It does not index JSONL
bodies unless explicitly requested.

Use deep scope or repeated `--root` flags for a route/code-specific build when
that extra search surface is worth the rebuild cost:

```bash
python3 scripts/gtos_context.py build --scope deep
```

```bash
python3 scripts/gtos_context.py build \
  --root .context \
  --root config \
  --root src \
  --root tests \
  --root scripts \
  --root research/operations
```

Search current indexed context:

```bash
python3 scripts/gtos_context.py search "selector scheduler replay parity"
```

Hydrate exact pointers for one route without deep-indexing every route:

```bash
python3 scripts/gtos_context.py route \
  final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
```

`route` first uses catalog rows when present, then adds a bounded filesystem
manifest from `research/operations/<route>`. The filesystem manifest records
read-first summaries/manifests/verifier outputs separately from cold raw JSONL
pointers and does not read raw ledger bodies.

Generate a compact context pack for an agent task:

```bash
python3 scripts/gtos_context.py pack \
  --task "broad replay parity repair" \
  --profile ultimate \
  --include-memory
```

Generate a bounded fast pack for MCP/compaction recovery:

```bash
python3 scripts/gtos_context.py pack \
  --task "broad replay parity repair" \
  --profile ultimate \
  --include-memory \
  --fast
```

Fast packs are stale-tolerant by design; use the explicit build command before
fast-pack only when a fresh catalog is required.

Read the compact active session/root-cause state:

```bash
python3 scripts/gtos_context.py active-state
```

Write the compact current checkpoint or root-cause map after a meaningful
context shift:

```bash
python3 scripts/gtos_context.py active-state \
  --write \
  --kind root-cause \
  --title "Current root-cause map" \
  --task "context os reliability" \
  --current-checkpoint "fast pack and current-scope catalog fixed" \
  --next-patch-batch "route manifest hydration" \
  --remaining "active route manifest index"
```

Active-state files are local continuity intelligence. They are indexed in
current-scope builds and read by packs/starters, but they do not replace opening
the exact current files before making concrete claims.

Read or write the short-lived continuation cursor:

```bash
python3 scripts/gtos_context.py cursor

python3 scripts/gtos_context.py cursor \
  --write \
  --task "selector scheduler parity repair" \
  --last-observation "Read v4_timewarp_simulated_live_research_loop.py and found finalizer authority is preserved before order materialization." \
  --current-hypothesis "The next leak is later risk recomputation overriding selected finalizer authority." \
  --next-atomic-step "Open simulate_order and patch the authority handoff." \
  --file src/research/v4_timewarp_simulated_live_research_loop.py \
  --symbol finalize_scheduler_risk_admitted_selection \
  --command "rg finalize_scheduler_risk_admitted_selection src/research/v4_timewarp_simulated_live_research_loop.py" \
  --do-not-repeat "do not rescan broad ledgers before opening the exact handoff" \
  --verify-next "python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -q"
```

The continuation cursor is not a durable route summary. It is the compact
"resume exactly here" edge for compaction/restart recovery: last observation,
current hypothesis, next atomic step, files/symbols touched, commands already
run, and checks to run next. Packs, starters, HTTP, and MCP expose it as
working memory that must be verified against current source before acting.

Write active state and the continuation cursor together:

```bash
python3 scripts/gtos_context.py checkpoint \
  --title "Context OS hardening checkpoint" \
  --task "context os reliability" \
  --current-checkpoint "fast-pack, route hydration, and active-state are wired" \
  --last-observation "Pack renders current root-cause map but lacked the last working cursor." \
  --next-atomic-step "Wire cursor and live symbol hits into pack, starter, HTTP, and MCP." \
  --fixed "active-state reader" \
  --remaining "cursor render path" \
  --source src/gtos_context_os/pack.py
```

Search live Python symbols without reading raw evidence:

```bash
python3 scripts/gtos_context.py symbols "finalize scheduler risk authority" --limit 10
python3 scripts/gtos_context.py symbols "v4_timewarp finalizer authority" \
  --root src/research_infra \
  --max-file-bytes 5000000 \
  --max-elapsed-seconds 15 \
  --limit 20
```

Symbol search scans current Python source under `src`, `scripts`, and `tests`
by default. It uses ripgrep prefiltering plus a streaming definition scanner so
MCP and fast-pack calls do not AST-parse the whole repo. Large Python files are
skipped by default unless the query points at their path; widen
`--max-file-bytes`, `--max-files`, or `--max-elapsed-seconds` for intentional
deep code hunts. It is navigation intelligence only: use it to jump to exact
code, then open the source before making a claim or patch.

Generate a doctrine-aware subagent or goal starter prompt:

```bash
python3 scripts/gtos_context.py starter \
  --task "selector scheduler parity repair" \
  --lane selector-scheduler \
  --profile selector-scheduler \
  --include-memory
```

Classify a file path:

```bash
python3 scripts/gtos_context.py classify .context/LIVE_STATE.md
```

Summarize one route without opening raw ledgers:

```bash
python3 scripts/gtos_context.py route \
  final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
```

Search controlled Codex memory registry files:

```bash
python3 scripts/gtos_context.py memory "selector scheduler current disk"
```

Create or repair the local GTOS second-brain Obsidian vault:

```bash
python3 scripts/gtos_context.py brain init
```

Pour a raw idea into the inbox:

```bash
python3 scripts/gtos_context.py brain capture \
  --title "Idea title" \
  --body "Raw idea text..."
```

Distill the latest raw note into a graph-linked card:

```bash
python3 scripts/gtos_context.py brain distill --latest
```

Search distilled second-brain intelligence:

```bash
python3 scripts/gtos_context.py brain search "context hygiene selector"
```

Regenerate the Obsidian/Mermaid graph artifacts:

```bash
python3 scripts/gtos_context.py brain graph
```

Export a context pack to a markdown file for Obsidian:

```bash
python3 scripts/gtos_context.py obsidian-export \
  --task "broad replay parity repair" \
  --profile ultimate \
  --include-memory \
  --out /path/to/vault/GTOS/context-packs/broad-replay-parity.md
```

Create a proposed canonical writeback without mutating memory:

```bash
python3 scripts/gtos_context.py propose-writeback \
  --title "Selector parity finding" \
  --body "Verify this finding against current disk before promotion." \
  --source src/components/selector_v4.py
```

Create a local session capsule for continuity without raw chat replay:

```bash
python3 scripts/gtos_context.py session-capsule \
  --title "Context OS hardening checkpoint" \
  --task "context hardening" \
  --summary "Added stale self-refresh checks and doctrine-aware starters." \
  --source src/gtos_context_os/catalog.py \
  --command "python3 -m pytest tests/test_gtos_context_os.py -q" \
  --decision "normal pack/starter commands self-refresh stale catalogs"
```

Read recent continuity capsules:

```bash
python3 scripts/gtos_context.py session-capsules --limit 5
python3 scripts/gtos_context.py session-capsules --status
```

Ingest a subagent/session finding into bounded continuity intelligence:

```bash
python3 scripts/gtos_context.py ingest-finding \
  --title "Selector finding" \
  --body-file /path/to/finding.md \
  --task "selector scheduler replay parity" \
  --source src/components/selector_v4.py \
  --decision "Verify the finding against current disk before action" \
  --to-second-brain \
  --reviewed
```

Run the read-only local HTTP sidecar:

```bash
python3 scripts/gtos_context.py serve --host 127.0.0.1 --port 8765
```

Available read-only endpoints:

- `GET /ping`
- `GET /health`
- `GET /stats`
- `GET /search?q=selector+scheduler&limit=10`
- `GET /route?route=<route_name>`
- `GET /memory?q=current+disk&limit=5`
- `GET /second-brain/status`
- `GET /second-brain/search?q=context+hygiene&limit=5`
- `GET /session-capsules?limit=5`
- `GET /session-capsules?status=1`
- `GET /active-state`
- `GET /cursor`
- `GET /symbols?q=finalize+scheduler+risk&limit=10`
- `GET /resume?task=broad+replay+parity&profile=ultimate`
- `GET /pack?task=broad+replay+parity&profile=ultimate&include_memory=1`
- `GET /pack?task=broad+replay+parity&profile=ultimate&include_second_brain=1`
- `GET /fast-pack?task=broad+replay+parity&profile=ultimate&include_memory=1`
- `GET /pack?task=broad+replay+parity&format=markdown`

There are intentionally no HTTP endpoints for broker actions, git mutation,
memory mutation, replay execution, source deletion, or deployment.

Run the dependency-free read-only MCP stdio server for local tool-style
integrations:

```bash
python3 scripts/gtos_context.py mcp-stdio
```

It supports the MCP JSON-RPC lifecycle (`initialize`, `tools/list`,
`tools/call`) and exposes read-only tools for bounded `pack`, `fast_pack`,
`search`, `route`, `memory`, `second_brain_status`, `second_brain_search`, bounded
`second_brain_read`, bounded repo `read_file`, `health`, `active_session_state`,
`continuation_cursor`, live `code_symbol_search`, `resume`, and session capsules.
The older simple JSON-lines method shape is retained for internal tests and
scripts.

Codex/Claude MCP config shape:

```json
{
  "mcpServers": {
    "gtos-context": {
      "command": "python3",
      "args": [
        "/Users/borr/Documents/gtos/repo/ai-trading-agent-ultimate-convergence-20260619/scripts/gtos_context.py",
        "--repo",
        "/Users/borr/Documents/gtos/repo/ai-trading-agent-ultimate-convergence-20260619",
        "mcp-stdio"
      ]
    }
  }
}
```

The server is intentionally read-only. It does not expose broker actions, git
mutation, replay execution, source deletion, memory mutation, or deployment.

The default catalog path is:

```text
.context/context_os/catalog.sqlite
```

The SQLite catalog is generated and ignored by git. Rebuild it instead of
committing it.

Default indexing stores up to 64 KB of searchable text per indexed file plus
path, size, mtime, hash, authority tier, evidence class, route, and freshness
metadata. Larger files are represented as metadata-only entries or skipped when
they are cold raw evidence.

Context pack profiles:

- `standard`: current authority anchors plus task search.
- `implementation`: standard query expanded toward `src`, `tests`, `config`,
  `scripts`, and verifier surfaces.
- `research`: standard query expanded toward route summaries, manifests,
  source evidence, and verifier artifacts.
- `ultimate`: implementation plus research plus context-hygiene terms for
  long GTOS repair sessions.
- `replay-repair`: replay behavior, source-bound to executable parity, splits,
  stress, verifier, and repair surfaces.
- `selector-scheduler`: candidate admission, source completeness, probability,
  expected net R, ranking, and reallocation surfaces.
- `cost-order`: broker-calibrated cost, spread/slippage/commission/swap, order
  policy, fillability, fallback, and refusal surfaces.
- `lifecycle-exit`: pending lifecycle, delay/skip/reduce/cancel-replace/expire,
  same-symbol handling, exit, harvest, stop, and target geometry.
- `verifier-audit`: verifier, artifact, manifest, prompt-hardening, diff-check,
  row-count, and authority-leak surfaces.
- `context-cleanup`: stale context, cleanup, archive, cold pointer, and current
  authority surfaces.

## Authority Tiers

- `platinum_current_disk_authority`: regenerated/current context anchors such as
  `LIVE_STATE`, current system map, reading order, quick card, cleanup policy,
  and doctrine.
- `gold_active_code_config_test`: implementation files under `src`, `scripts`,
  `config`, and `tests`.
- `gold_route_summary_manifest`: route summaries, manifests, verification
  results, reports, and dossiers.
- `silver_route_artifact`: other compact route artifacts that need current
  manifest verification.
- `bronze_chat_or_memory`: chat, transcript, and memory-derived material.
- `cold_raw_evidence`: JSONL/LFS/raw data pointers, not default prompt context.

Codex memory hits are deliberately `bronze_chat_or_memory`. They are useful for
finding prior thread intelligence, but every actionable fact must be verified
against current disk artifacts before being treated as current authority.

## Running Beside Active Goal Sessions

The Context OS is safe to run beside a goal session when used in its default
mode:

- it reads files and writes only the local catalog database;
- it excludes raw JSONL text by default;
- it does not inspect broker state, place orders, or change runtime files;
- it does not stage, commit, push, restart, or deploy.

For heavy runs, prefer building the catalog when no broad replay is actively
writing route artifacts. If a broad replay is active, use existing catalog packs
or restrict roots with repeated `--root` flags. The default `build` command uses
current scope; add `--scope deep` only when historical `.context` material or
full `research/operations` metadata search is needed.

Example bounded build:

```bash
python3 scripts/gtos_context.py build \
  --root .context \
  --root src \
  --root tests \
  --root research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
```

## Raw Evidence Policy

Do not dump raw ledgers into Obsidian or agent prompts. For large JSONL or LFS
files, preserve:

- repo-relative path;
- size and mtime;
- hash when cheap enough for the task;
- schema or row-count summary from route artifacts;
- route manifest/verifier pointer;
- exact reason a raw hydration is needed.

Only use `--include-jsonl` when the task explicitly needs JSONL text indexed and
the cost is acceptable. Otherwise retrieve exact raw files directly from the
heavy evidence worktree.

## Writeback Policy

The Context OS can create writeback proposal files, but it does not silently edit
`~/.codex/memories`, canonical route docs, or Obsidian notes. A proposal must
carry:

- title;
- body;
- source paths;
- status `proposal_only_not_canonical_memory`;
- promotion rule requiring owner or route-owner acceptance.

This prevents memory from becoming another stale authority surface.

## Doctrine Enforcement

Every context pack now includes a doctrine checklist with:

- lane posture;
- current-disk authority rules;
- evidence-class boundaries;
- no arbitrary top-N reminders;
- same-evidence-class repair guidance;
- anti-staleness checks;
- completion questions.

This checklist is meant to be copied into subagent starters and used by the main
agent before making claims or ending a route checkpoint.

## Future Extensions

The current implementation is intentionally simple: standard-library SQLite plus
deterministic markdown/JSON packs. The next natural extensions are:

- an MCP wrapper exposing `pack`, `search`, `stats`, and `classify`;
- richer promotion flow from session capsules/writeback proposals into canonical
  docs after owner or route-owner acceptance;
- a curated Obsidian mirror for human-readable current authority notes;
- writeback proposals that require source paths and evidence classes before
  promoting a finding into canonical context;
- optional vector/BM25 indexing after the authority model proves useful.
