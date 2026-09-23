# Prompt Engineering Patterns — GTOS Research Pipeline
## Learned from April 11, 2026 session (12 prompts written, all executed successfully)

## Prompt Structure Template

Every literature search or implementation prompt follows this structure:
1. Context block (what GTOS does now, what the question is, why it matters)
2. Specific questions with search terms (for lit search) or step-by-step instructions (for implementation)
3. Quality filter / verification criteria
4. Output format (matching existing file structures)
5. Save path (versioned, never overwrite)
6. Constraints section (no src/ modification unless deploying, seed=42, per-instrument mandatory)

## Patterns That Work

1. Implementation prompts need concrete file paths and grep commands, not vague "find the relevant file."
2. Always specify what happens with null results — a null finding is valuable, not a failure.
3. Monte Carlo prompts need seed=42, path count, and explicit grid resolution.
4. Per-instrument analysis is mandatory — gold parameters (ξ=0.35, GARCH 0.99) never apply universally.
5. Literature search prompts need an indicator exclusion filter — RSI/MACD/Bollinger papers flood results uselessly.
6. Quality filter needs 5 dimensions: testability, data availability, relevance, journal tier, OOS validation.
7. Output format must match existing files (phase1_priority_a_papers.md structure) for cross-session consistency.
8. Cross-reference against the 69 existing Priority A papers before searching — avoid rediscovery.
9. Every prompt ends with explicit constraints section.
10. Pressure test sequence is mandatory: (1) critic mode, (2) list issues, (3) fix them, (4) state what was fixed. Never skip.

## Known Agent Failure Modes

1. Agent recommends building features already in the codebase — always require codebase cross-reference step.
2. Agent claims "COMPLETED" without file on main branch — require file existence verification.
3. Agent applies gold-only parameters to all instruments — always specify per-instrument requirement.
4. Agent hallucinates paper titles/authors — verify citation counts and journal existence.
5. Post-execution verification is for confirming results, NOT for catching design flaws — those must be caught in the pressure test before submission.

## Model Selection Guide

| Task | Model | Effort | Rationale |
|------|-------|--------|-----------|
| Literature search | Opus | High | Needs reasoning depth for paper quality assessment |
| Grep-fix-rerun diagnostics | Sonnet | High | Mechanically straightforward, well-defined |
| Complex math (BOCPD, Kelly MC) | Sonnet | Max | Multiple interacting components, easy to get subtly wrong |
| File organization | Sonnet | Low | Just copying and renaming |
| Live deployment | Opus | Max | Zero tolerance for errors |
| Prompt writing/reviewing | Opus | High | Needs full project understanding |

## Effective Prompt Length

- Implementation prompts: 400-800 words. Every step explicit.
- Literature search prompts: 300-500 words. Questions + search terms + filter + output format.
- Don't over-constrain creative tasks (brainstorming). Do over-constrain mechanical tasks (deployment).
