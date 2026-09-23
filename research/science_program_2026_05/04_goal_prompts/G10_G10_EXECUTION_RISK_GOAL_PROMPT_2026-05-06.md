# G10 Execution Entries Exits Risk Portfolio Goal Prompt - 2026-05-06

**Role:** `science_lane`
**Domain:** `execution, entries, exits, risk, portfolio`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Worktree:** `C:\tmp\gtosg\G10`
**Branch:** `science-goals/g10-execution-risk`

## Objective

Translate internal pending vs native pending, slippage, path timing, J46/J49 successors, re-entry/trailing, and prop-firm constraints into preregistered shadow lanes.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered file in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_READING_ORDER.md` and relevant Tier 2-4 artifacts.

## Worktree Boundary

Do not touch `main`. Work only inside this lane worktree. Do not stage runtime dirt. Commit only scoped lane files.

## Access Request Policy

If the goal session is blocked by sandbox, filesystem ACL, pytest temp-dir, local Git ref/write, network, `curl.exe`, web-fetch/search tooling, or public link/sitemap crawling needed for this research program, request access instead of stopping; the owner has stated access requests for this program will be granted. If web search is insufficient, use direct public fetches, links, and sitemaps to understand source content, save raw responses/source-index evidence before making claims, and cite the saved evidence. This does not authorize paid external spend, paywall/credential bypass, MT5/order/live-trading actions, credential changes, remote pushes, or changes to forbidden live trading areas.

## Deep Research Mode

Use maximum deliberate reasoning before and during search. Start by writing what mechanisms would be worth finding, what evidence would distinguish them from noise, which GTOS components they could affect, and where the strongest evidence is likely to live. Do not perform one shallow web search and summarize it. Iterate through local context, papers, books, PDFs, exchange/vendor/regulator/platform docs, datasets, source-code references, and credible public sources when relevant. Hunt for counter-evidence, decay modes, duplicate routes, hidden leakage, implementation blockers, and non-obvious market behaviors most traders would miss. Every new ambiguity must become an answered question, a sharper hypothesis, or an explicit blocked item with the next evidence needed.

## Context And Ambiguity Discipline

Maintain a lane context ledger as you work. Record each important artifact/source read, the claim or mechanism it changed, the next question it created, and the next source or repo check to pursue. If live state or research context may be stale, regenerate/read it again before relying on it. If lost, formulate the exact question, search locally and publicly for the answer, and ask the owner only when the answer requires a preference, credential, paid-source decision, or live-system approval.

## Science-First Requirement

Extract primitive mechanisms from the domain. Do not start from public trading strategies, missed-move lists, or market-expansion wishes.

## Repo Cross-Check

For each idea, verify whether it is already active, shadowed, blocked, killed, duplicated, or stale in GTOS. Cite paths and line evidence where possible.

## Hypothesis Translation

Every useful idea must become measurable, preregistered, source-aware, and label-safe. Use `science_mechanism_v1`, `science_hypothesis_v1`, `experiment_prereg_v1`, `source_contract_v2`, and `goal_status_v1`.

## Required Stop Outputs

- domain synthesis
- lane context ledger with search plan, sources read, evolving questions, and stale-context refreshes
- ambiguity ledger with pursued answers, blockers, sharper hypotheses, and owner questions if needed
- counter-evidence and decay-mode review
- mechanism rows
- hypothesis rows
- killed-route notes
- experiment prereg specs
- source/budget blockers
- neighbor-lane cross-domain hypotheses after first synthesis pass

## Neighbor Pass

After the first synthesis pass, read outputs from neighboring lanes: G1, G6, G9. Add only cross-domain hypotheses that survive source, leakage, and killed-route checks.

## Forbidden

- No live trading prompt changes.
- No risk, execution, permissions, selector, or safety-gate changes.
- No spending without source/budget ledger approval.
- No promotion claim.
- No same-dataset discovery result labeled as validation.

## Done Standard

Do not mark `G10` complete until files exist, focused checks are recorded, blockers are explicit, and every row/report carries `NO_PROMOTION_VERDICT`.
