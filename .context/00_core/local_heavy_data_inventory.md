# Local Heavy Data Inventory

Date: 2026-05-10
Status: active research context
Scope: local data discovery for research and outcome-testing goal sessions
Promotion posture: NO_PROMOTION_VERDICT

## Purpose

GTOS research uses heavy local data that is often not tracked by Git and may not appear inside a newly created worktree. A goal session must not treat "file missing in this worktree" as proof that the data does not exist on the laptop.

This file is a search and evidence policy, not a validation-safe source contract. Every lane still needs source hashes, as-of rules, no-leak checks, duplicate policies, and label separation before outcome use.

## Core Rule

Worktree absence is not data absence.

Before accepting any data-missing blocker, a data-heavy goal session must search approved absolute local paths, request access if blocked, hash any file it consumes, and record positive and negative evidence in its completion audit.

Local absence is not a terminal blocker. A lane may write "blocked because data is not local" only as an intermediate state while it continues the acquisition ladder below. The final artifact must say either the data was recovered, the exact owner/access/API/export action needed, or the field is non-generatable historical source truth that must be fixed prospectively by a capture contract.

## Data Acquisition Escalation Ladder

For missing market data, sessions must pursue this ladder before finalizing a blocker:

1. Search the current worktree and committed manifests.
2. Search absolute repo roots such as `C:\Users\MSI\Documents\ai-trading-agent\data`, `data\ticks`, `shadow_logs`, and `exports`.
3. Search prior worktrees and temp caches under `C:\tmp\gtos_otb` for source-hashed artifacts, not as canonical truth but as leads.
4. Search broker-local/Sierra/vendor roots listed below, with targeted paths and hashes.
5. If local files are absent, create or execute an approved read-only extraction route, such as MT5 `copy_ticks_range` or broker export, when the lane permits it.
6. If network/vendor/API access is needed, write a pre-call manifest with symbol, window, fields, cost/free-credit status, no-leak constraints, and exact owner approval requirement.
7. If the missing field is not market data but historical GTOS intent/order/lifecycle state, search all source-safe logs and artifacts; if absent, do not infer it from price. Record the exact forward logger/capture field that prevents recurrence.

The target standard is that future research should not end with "we do not have the data locally." It should end with recovered data, exact extraction/access instructions, or a source-safe proof that the historical state was never captured and therefore cannot be reconstructed honestly.

## Recoverable Data Versus Non-Generatable Source Truth

Future sessions must not collapse all missing data into one blocker family.

Recoverable or requestable market data includes ticks, bars, quotes, spreads, session calendars, source exports, Sierra caches, broker-local archives, vendor/cache artifacts, and approved read-only MT5 extraction windows. If one of these is missing in a worktree, the session must search absolute local roots, prior worktrees, and approved extraction paths before calling it blocked.

Non-generatable historical system-state truth includes pending-limit lifecycle intent, exact write-clock events, source-safe pending-order observability, MT5 ticket redaction proof, native order type, logger-emitted capture fields, and any field that only existed because GTOS would have recorded it at decision time. If those fields were not logged in a source-safe artifact, price data alone cannot recreate them. The correct closure is either source-proof from existing logs or a forward capture/logger contract that prevents the gap from recurring.

Do not synthesize historical intent/order/lifecycle fields from later price movement. Generated or inferred rows are allowed only as clearly labeled projections or schema fixtures, never as source-bound historical truth, denominators, result labels, validation rows, or promotion evidence.

## Known And Candidate Local Data Roots

Always verify existence before use. These are discovery roots, not automatically validation-safe sources.

| Root | Expected contents | Use policy |
|---|---|---|
| `C:\Users\MSI\Documents\ai-trading-agent\data` | repo-local data tree; may contain ignored heavy files | Search first for local research data and source caches. |
| `C:\Users\MSI\Documents\ai-trading-agent\data\ticks` | MT5 tick parquet captures by symbol/date | Approved for read-only source-hashed packet/source coverage audits when the lane permits tick data. |
| `C:\Users\MSI\Documents\ai-trading-agent\data\external` | validation/source/vendor/cache artifacts if present | Read only with source-hash and source-contract/as-of review. |
| `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs` | runtime shadow logs | Use for provenance and permitted non-result fields only; do not consume broker actual-R, live trade result, blocked-packet outcome, or post-decision result fields unless the lane explicitly authorizes that label family. |
| `C:\Users\MSI\Documents\ai-trading-agent\exports` | generated exports if present | Search and hash before use; verify source lineage. |
| `C:\tmp` | temporary worktrees, downloaded caches, generated research outputs | Search for lane artifacts and caches, but never treat stale worktree data as canonical without source hashes and commit context. |
| `C:\SierraChart` | possible SierraChart install/data root | Candidate only; verify existence and exact data subpaths before use. Sierra `.scid` or related files need parser/source-contract/as-of proof before outcome use. |
| `C:\Users\MSI\Documents` | owner document/data area | Candidate only; use targeted searches and avoid broad destructive operations. |

## Required Search Behavior

For every data-heavy lane:

1. Run the mandatory GTOS preflight.
2. Read `.context/00_core/local_heavy_data_inventory.md`.
3. Search the worktree and the absolute main repo data path.
4. If the needed data might be outside the repo, search targeted candidate roots or request access.
5. Hash every source file used in an audit/result/control artifact.
6. Record searched paths, search patterns, file counts, hashes used, and exact missing windows/fields.
7. State whether a blocker is local absence, permission/access denial, source/as-of invalidity, parser absence, or true impossibility from available approved sources.

## Forbidden Without Explicit Lane Approval

- No live MT5 calls.
- No broker actual-R/account-history/live trade result use inside synthetic/path/lifecycle lanes.
- No paid/API/Databento call without a pre-call manifest, cap, source purpose, and owner approval.
- No source marked `validation_safe=true` from this file alone.
- No promotion language from local heavy data discovery alone.

## Current Lesson From G6 OTX

OTB6 initially could not see tick parquet in its worktree. Later OTX used the absolute main path `C:\Users\MSI\Documents\ai-trading-agent\data\ticks` and found May 3-6 packet-date tick files. That cleared some G6 packet blockers and proved others exactly.

Therefore future data-heavy prompts must explicitly reference absolute local data paths before declaring data unavailable.
