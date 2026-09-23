# AUDIT 24: GIT-HYGIENE (.gitignore, commits, hooks, repo size)

## CRITICAL
- 22 .log files TRACKED in git history (root logs/) — should be gitignored
- shadow_logs/heartbeat_flatten_events.jsonl TRACKED
- knowledge_base/pipeline_state/02_market_state.json + 2 backup variants TRACKED
- .context/LIVE_STATE.md TRACKED (intentional snapshot but auto-regenerated — debatable)
- .gitattributes NOT PRESENT (line ending policy)

## Commit message hygiene
- 100% conventional format
- 50% of agent commits missing Co-Authored-By line

## Tags
ZERO (recommend semantic versioning post-launch).

## Hooks
NONE (recommend pre-commit lint).

## Repo size
- 154 MB (.git/)
- 1 pack 143.7M
- 77 loose

## Stale refs
- origin/podcast-research-implementation

## ROOT CAUSE
.gitignore ignores `knowledge_base/logs/` but NOT root `logs/`.

## PRIORITY 1 fix
Add `logs/` to .gitignore + `git rm --cached` on 22 existing tracked logs.
