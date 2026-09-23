# Canonical Science Lane Goal Prompt Template - 2026-05-06

Use this template for every primitive-science lane.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered file in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_READING_ORDER.md` and the relevant Tier 2-4 artifacts.

## Worktree Boundary

Do not touch `main`. Work only inside the lane worktree. Do not stage runtime dirt. Commit only scoped lane files.

## Access Request Policy

If the goal session is blocked by sandbox, filesystem ACL, pytest temp-dir, local Git ref/write, network, `curl.exe`, web-fetch/search tooling, or public link/sitemap crawling needed for this research program, request access instead of stopping; the owner has stated access requests for this program will be granted. If web search is insufficient, use direct public fetches, links, and sitemaps to understand source content, save raw responses/source-index evidence before making claims, and cite the saved evidence. This does not authorize paid external spend, paywall/credential bypass, MT5/order/live-trading actions, credential changes, remote pushes, or changes to forbidden live trading areas.

## Objective

Extract mechanisms from primitive science, not public trading strategies. Every useful idea becomes measurable, preregistered, source-aware, and shadow-only.

## Deep Research Mode

Use maximum deliberate reasoning before and during search. Start by writing what mechanisms would be worth finding, what evidence would distinguish them from noise, which GTOS components they could affect, and where the strongest evidence is likely to live. Do not perform one shallow web search and summarize it. Iterate through local context, papers, books, PDFs, exchange/vendor/regulator/platform docs, datasets, source-code references, and credible public sources when relevant. Hunt for counter-evidence, decay modes, duplicate routes, hidden leakage, implementation blockers, and non-obvious market behaviors most traders would miss. Every new ambiguity must become an answered question, a sharper hypothesis, or an explicit blocked item with the next evidence needed.

## Context And Ambiguity Discipline

Maintain a lane context ledger as you work. Record each important artifact/source read, the claim or mechanism it changed, the next question it created, and the next source or repo check to pursue. If live state or research context may be stale, regenerate/read it again before relying on it. If lost, formulate the exact question, search locally and publicly for the answer, and ask the owner only when the answer requires a preference, credential, paid-source decision, or live-system approval.

## Repo Cross-Check

Before keeping any idea, verify whether GTOS already tested, killed, blocked, or activated it. Cite file paths and line evidence or mark the check incomplete with the exact blocker.

## Hypothesis Translation

Translate surviving mechanisms into `science_mechanism_v1`, `science_hypothesis_v1`, `experiment_prereg_v1`, and `source_contract_v2` rows where applicable.

## Stop Condition

The lane is not complete until it has produced domain synthesis, context ledger, ambiguity ledger, counter-evidence review, mechanism rows, hypothesis rows, killed-route notes, experiment specs, blockers, tests/verification notes, and a `goal_status_v1` row. Preserve `NO_PROMOTION_VERDICT`.
