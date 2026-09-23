# vNext Repo Context Cleanup And Deletion Goal Prompt

Date: 2026-05-29

Route id: `vnext_repo_context_cleanup_deletion_2026_05_29`

Evidence class: `REPO_CONTEXT_CLEANUP_DELETION_CURRENT_TRUTH_PACKAGING`

Objective: clean the GTOS repository so future agents can understand and extend the current vNext moonshot system quickly, accurately, and without stale old-system context pollution. Completion is measured by executed deletions, compressed current summaries, repaired active docs, current-truth packaging, guardrail verification, and a scoped commit.

## Current Operating Reality

The repository contains many generations of truth: old live-system docs, old strategy assumptions, failed research routes, large raw ledgers, prompt drafts, stale handoffs, generated HTML/images/screenshots, current vNext production replacement code, current live activation evidence, and future research seeds.

That mixed state now harms the project. It makes searches noisy, makes agents reread obsolete files, resurrects old 7-symbol/static-1.5R/OB-only assumptions, and slows every repair or research session. The goal is not minimal context. The goal is the right context: current, relevant, source-bound, and easy to navigate.

The target end state:

- current vNext/moonshot truth is easy to find in minutes;
- active docs no longer describe stale April/old-live assumptions as current;
- historical material that still has intelligence value is compressed into current summaries or retained as cold evidence with exact manifest references;
- mixed files that contain both useful intelligence and stale framing are split at section/claim level, with useful context merged into current truth and stale framing deleted or rewritten;
- deprecated, irrelevant, duplicated, generated, and context-polluting files are deleted from the active repo;
- Git-tracked, untracked, ignored, LFS-tracked, materialized LFS, current HEAD, and GitHub-pushed footprint files are inventoried and cleaned as one repo surface;
- local Git/LFS object storage, stale remote refs/tags/release/action-artifact references available from local tooling, and workspace cache/build/runtime junk receive explicit keep/delete/prune decisions;
- credential files, account identifiers, emails, API tokens, broker-account material, and personal screenshots/media receive explicit delete/redact/current-keep decisions;
- large evidence is separated from reading context;
- future agents have one current reading path, one repo map, one stale-file policy, and one cleanup verification script/checklist;
- `git status`, `rg`, and agent preflight stop drowning in old junk.

Git history is the deep archive. Current HEAD is the working surface. A file does not deserve to remain in current HEAD merely because it once existed.

## Required Preflight

Run from current disk before acting:

- `python scripts/generate_live_state.py` or `py -3 scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
- Read latest numbered handoff only as historical context, not current truth.
- Read `.context/00_core/goal_session_research_discipline.md`.
- Read `.context/00_core/research_operating_doctrine.md`.
- Read `.context/00_core/orchestrator_successor_operating_brief.md`.
- Read `.context/00_core/orchestrator_methodology_hardening_controls.md`.
- Read `.context/00_core/parallel_goal_merge_playbook.md`.
- Read current vNext/live activation route state and current repair artifacts under:
  - `research/operations/vnext_live_activation_active_repair_companion_2026_05_28/`
  - `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/`
- Read current root docs and context entrypoints: `README*`, `CLAUDE.md`, `AGENTS.md`, `.context/00_READING_ORDER.md`, `.context/00_core/research_current_state.md`, `.context/00_core/research_operating_doctrine.md`.

Do not rely on chat memory. After any context compaction, resume, interruption, tool crash, long wait, or uncertainty, reread this prompt, the starter message, the doctrine files above, `.context/LIVE_STATE.md`, and the route state from disk before continuing.

## Hardening Controls

These are active instructions, not background.

No conservative brake applies inside this evidence class. Be aggressive in deleting proven context pollution and stale generated junk. The burden is on `KEEP` decisions to prove current value; it is not on `DELETE` decisions to overcome vague attachment to old files.

Full same-evidence-class pursuit is mandatory. Literal impossibility means exactly this: every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action that can classify, delete, compress, or current-truth-repair a file from available local evidence has been performed and recorded. Same-evidence-class blockers require repair/recompute/reverify, not a closeout note.

No arbitrary top-N, top 3/5/10, representative-only, sample-only, directory-only, or extension-only cutoff is allowed. Build a full file inventory and preserve all material rows. Ranked summaries are allowed only after the full machine-readable ledgers exist.

Result materialization standard: every material result must state result-use-status, source-capture/source completeness status, branch decision, implementation decision, exact/proxy result impact for result-bearing rows, before/after file counts, before/after byte counts, deleted tracked/untracked counts, compressed/current-summary counts, active-context stale-reference counts, and current-agent-reading-path effect.

Boundary language is classification only. This route is repo context cleanup, documentation/current-truth packaging, stale-file deletion, archive hygiene, and guardrail verification. If a file touches production-change, live trading, broker operation, paid API/vendor, broker account/order/history/deal/position, prompt/config/risk/execution/safety/canary/selector behavior, classify it precisely and update current truth without using the category as a reason to leave stale context pollution in place.

Classification is not whole-file-only. If a file contains mixed value, classify and act at section, claim, table, and artifact-reference level. Preserve unique useful intelligence by extracting it into the current truth layer or a current summary, then delete, rewrite, or archive the stale source according to its remaining value. Do not keep an entire polluted file because one paragraph is useful. Do not delete useful intelligence merely because it sits inside a stale file.

## Deletion Policy

Classify every file into one of these decisions:

- `KEEP_CURRENT_AUTHORITY`: current truth, active entrypoint, active code/config/test, active route state, or current operational evidence.
- `KEEP_REPRODUCIBILITY_EVIDENCE`: needed to rerun or verify current vNext claims; not default reading context.
- `COMPRESS_TO_CURRENT_SUMMARY_THEN_DELETE`: old research or route artifacts with useful intelligence already captured in a new current summary/manifest.
- `EXTRACT_UNIQUE_INTELLIGENCE_THEN_DELETE_SOURCE`: mixed file where useful sections are merged into current truth and the polluted source is removed.
- `REWRITE_ACTIVE_DOC_REMOVE_STALE_SECTIONS`: active entrypoint with useful current value and stale sections; rewrite the file so only current truth remains.
- `MERGE_DUPLICATE_CONTEXT_THEN_DELETE_DUPLICATES`: overlapping useful context exists in several files; consolidate into one current authority and delete duplicates.
- `DELETE_CONTEXT_POLLUTION_TRACKED`: tracked stale/irrelevant/duplicated/generated file to remove from HEAD.
- `DELETE_CONTEXT_POLLUTION_UNTRACKED`: untracked stale/irrelevant/duplicated/generated local file to remove from disk.
- `COLD_EVIDENCE_ARCHIVE_WITH_POINTER`: raw evidence that remains necessary for reproducibility but must be removed from default context and referenced through a current manifest.
- `REPAIR_ACTIVE_DOC_THEN_KEEP`: active entrypoint doc currently stale; update it to current vNext truth and keep.

Deletion targets include every file type when proven stale or irrelevant: Markdown, text, JSON, JSONL, CSV, HTML, images, screenshots, videos, notebooks, generated reports, old prompt drafts, stale handoffs, duplicated route outputs, temporary files, cache files, dead run artifacts, stale context docs, old root docs, stale program-control reports, and generated assets that add no current research or reproducibility value.

Do not preserve a file because an agent might browse it. Preserve it only when it has current authority, active reproducibility value, or unique intelligence that has not yet been compressed into a current summary.

When useful context and stale context share the same file, the decision must name the useful sections, the stale sections, the merge destination, and the final source-file action. The cleanup must leave future agents with less drift and more usable context, not less intelligence.

## Stage 00 - Route Setup And Current Truth Anchor

Create route directory:

`research/operations/vnext_repo_context_cleanup_deletion_2026_05_29/`

Write:

- `REPO_CLEANUP_STATE.json`
- `REPO_CURRENT_TRUTH_ANCHOR.md`
- `REPO_CLEANUP_CONTROL_LEDGER.jsonl`
- `REPO_CLEANUP_OUTPUT_MANIFEST.json`

Record current HEAD, live-state generated timestamp, current vNext route anchors, current live activation route anchors, current prompt path, current starter path, disk free space, tracked/untracked summary, LFS status summary, and first incomplete cleanup invariant.

## Stage 01 - Full Repo, Git, LFS, And GitHub Footprint Inventory

Build a full file inventory ledger for the working tree and a Git/LFS/GitHub footprint ledger for current tracked and pushed surfaces.

Required output:

- `REPO_FILE_INVENTORY_LEDGER.jsonl`
- `REPO_FILE_INVENTORY_SUMMARY.json`
- `REPO_GIT_LFS_GITHUB_FOOTPRINT_LEDGER.jsonl`
- `REPO_GIT_LFS_GITHUB_FOOTPRINT_SUMMARY.json`
- `REPO_CREDENTIAL_ACCOUNT_ARTIFACT_FOOTPRINT_LEDGER.jsonl`
- `REPO_RUNTIME_RETENTION_LEDGER.jsonl`
- `REPO_DELETE_BREAKAGE_PROOF_LEDGER.jsonl`
- `REPO_MIXED_CONTEXT_EXTRACTION_LEDGER.jsonl`
- `REPO_CONTEXT_CONSOLIDATION_LEDGER.jsonl`

Each file row must include:

- relative path;
- tracked/untracked/deleted/ignored status from git or exact non-git classification;
- file type/extension;
- size bytes;
- last modified time;
- git object hash or content hash before deletion, with exact unreadable/binary/tool-failure reason when hashing cannot complete;
- LFS pointer/materialized status for LFS-tracked files, otherwise `not_lfs_tracked`;
- directory family;
- role classification: active code, active config, active test, active context, active route, historical route, generated report, raw ledger, image/media, temp/cache, runtime data, shadow/live data, stale prompt, stale handoff, unknown;
- reference count from current active docs/code using direct search, with exact skipped reason for binary/generated/runtime files that do not need content-reference scans;
- first-pass classification;
- mixed-context status: `not_mixed`, `mixed_extract_then_delete`, `mixed_rewrite_active_doc`, `mixed_merge_duplicates`, or exact no-content-scan reason;
- useful section/claim/table references when mixed;
- stale section/claim/table references when mixed;
- merge destination or rewrite target when mixed;
- evidence used for classification.

The inventory must cover every material file in the repo folder: tracked, untracked, ignored, generated, runtime, route-local, LFS pointer, LFS materialized content, media, docs, code, tests, configs, prompt artifacts, data manifests, and stale local junk. Inventory `.git` object history and LFS object storage through Git/LFS plumbing commands rather than raw recursive content reads of `.git` internals.

The Git/LFS/GitHub footprint ledger must include:

- `git ls-tree -r HEAD` tracked paths, sizes, object ids, and LFS pointer status;
- `git lfs ls-files --all` output and `.gitattributes` rules;
- local LFS materialization status for current HEAD files;
- large reachable Git objects from `git rev-list --objects --all` or equivalent, with path, size, commit reachability, and current HEAD presence;
- local branches, remote-tracking branches, tags, worktrees, submodules, stashes, and packed refs that keep stale files reachable;
- GitHub remote footprint discoverable from available local tools, including remote refs, tags, releases, Actions artifacts/caches, and large-file warnings when `gh` or git remote queries are available;
- files that previously blocked GitHub push or exceed GitHub warning/error thresholds;
- files present in current HEAD that are already pushed or will be pushed;
- stale LFS patterns, stale LFS pointers, missing LFS objects, orphaned LFS local objects, and large raw files that belong in deletion/compression/current-evidence classification.

Large binary/raw evidence can be classified from metadata, path, manifest, hash, and references; do not skip it. Every large file and every LFS file needs a keep/delete/compress/cold-evidence decision.

The credential/account-artifact footprint ledger must cover text and metadata paths where credentials, account identifiers, or personal account artifacts appear, including `.env*`, config files, prompts, logs, route artifacts, screenshots/media metadata, notebooks, HTML, JSON/JSONL/CSV, Telegram/MT5/broker records, API-key names, bearer/token patterns, emails, account numbers, and broker login identifiers. Delete or redact stale credential/account material that has no current operational or reproducibility value. Keep current necessary account evidence only with explicit reason and non-default reading status.

The runtime retention ledger must classify `shadow_logs/`, `pipeline_state/`, `knowledge_base/trade_records/`, `knowledge_base/index/`, `data/ticks/`, `data/m1/`, `data/historical*`, parquet/csv/jsonl live data, daemon heartbeats, temp lock files, and active companion-route evidence into hot/current, warm/reproducibility, cold/evidence-pointer, compress/delete, or delete-now. This ledger must distinguish live-current evidence from stale old-system logs so cleanup does not either delete active intelligence or preserve stale noise.

The delete-breakage proof ledger must prove every delete/compress decision against current code/tests/docs/manifest references. Use direct search, manifests, route verifiers, import/reference scans, and active-doc links. Files referenced only by deprecated/historical docs can still be deleted or compressed after the current truth layer records the replacement.

The mixed-context extraction ledger must record every file where useful context and stale context coexist. For each mixed file, record unique useful intelligence, stale framing removed, duplicate context merged, target current-summary path, source-file final decision, and proof that the current truth layer now carries the useful intelligence without preserving the stale frame.

The context consolidation ledger must detect repeated or overlapping context across README/CLAUDE/AGENTS/.context/research/program-control/goal-prompt/handoff files. Consolidate useful repeated context into current authority files and delete duplicate sources that add no unique current value.

## Stage 02 - Active Context And Staleness Scan

Scan every active context entrypoint and root doc for stale current-truth claims.

Required inputs include:

- `README*`
- `CLAUDE.md`
- `AGENTS.md`
- `.context/00_READING_ORDER.md`
- `.context/LIVE_STATE.md`
- `.context/00_core/*.md`
- latest handoff index files;
- active goal prompt directory;
- current live activation route docs;
- current vNext repair-hardening route summaries.

Required outputs:

- `ACTIVE_CONTEXT_STALENESS_LEDGER.jsonl`
- `ACTIVE_CONTEXT_REPAIR_PLAN.json`
- `ACTIVE_CONTEXT_MIXED_SECTION_LEDGER.jsonl`

Flag stale claims including but not limited to:

- old 7-symbol production universe stated as current;
- old `PrimaryAnalyzer -> L2` production path stated as current for vNext;
- old static `1.5R`, J46/J49, or BE default stated as active vNext production execution;
- old 2026-04 or pre-vNext live status stated as current;
- stale risk/profile/symbol/alias tables;
- stale session/KZ language that contradicts current 24-symbol moonshot routing;
- old replay acceptance failures stated as unresolved when current repair artifacts supersede them;
- old docs that tell future agents to read stale handoffs before current vNext route artifacts;
- stale live-monitoring or Telegram statements;
- stale LFS/storage warnings that no longer describe current state;
- any language that makes historical old-system material look current.

For active docs with mixed useful/stale content, repair at section level in the same run. Keep current sections, delete or rewrite stale sections, move unique old intelligence into current summaries, and record the exact before/after section actions. Do not only list stale claims.

## Stage 03 - Current Truth Layer

Create a durable current truth layer that future agents read first.

Required outputs:

- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_vnext_system_map.json`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/repo_cleanup_and_staleness_policy.md`
- `REPO_CURRENT_TRUTH_SUMMARY.md`
- `REPO_CONTEXT_CONSOLIDATION_SUMMARY.md`

The current truth layer must include:

- current vNext production replacement architecture;
- current 24-symbol broker/native alias map;
- current live activation status;
- current dynamic execution policy: momentum primary plus partial exceptions;
- current replay numbers and caveats;
- current live/replay gate-stack status;
- current candidate-intelligence status;
- current first unresolved live lifecycle evidence: first real order/fill/close/cost/deal reconciliation;
- current data collection surfaces: tick, M1, M15/D1/H4/H1, candidate records, runtime decisions, replacement monitor;
- current evidence directories and which summaries to read before raw ledgers;
- files/directories excluded from current authority;
- cleanup policy for future generated artifacts and stale prompts.
- consolidated useful intelligence extracted from mixed old files, with source pointers and stale framing removed.

Update existing active entrypoints to point to this layer. Determine whether `AGENTS.md` is generated from `CLAUDE.md`; when generated, update the source and run the repo sync script; when standalone, update it directly.

## Stage 04 - Deletion And Compression Decisions

Build final decision ledgers:

- `REPO_DELETE_LEDGER.jsonl`
- `REPO_COMPRESS_LEDGER.jsonl`
- `REPO_KEEP_LEDGER.jsonl`
- `REPO_COLD_EVIDENCE_POINTER_LEDGER.jsonl`
- `REPO_DELETION_PREIMAGE_MANIFEST.json`
- `REPO_LFS_AND_GITHUB_FOOTPRINT_DECISION_LEDGER.jsonl`
- `REPO_LOCAL_OBJECT_AND_CACHE_PRUNE_LEDGER.jsonl`
- `REPO_CREDENTIAL_ACCOUNT_ARTIFACT_REPAIR_LEDGER.jsonl`
- `REPO_RUNTIME_RETENTION_DECISION_LEDGER.jsonl`
- `REPO_MIXED_CONTEXT_EXTRACTION_DECISION_LEDGER.jsonl`
- `REPO_CONTEXT_CONSOLIDATION_DECISION_LEDGER.jsonl`

For every delete row, record:

- file path;
- tracked/untracked;
- size bytes;
- hash or exact no-hash reason;
- stale/irrelevant reason;
- replacement/current summary path if any;
- whether git history already preserves it;
- whether LFS or manifest covers needed evidence;
- deletion method;
- verification after deletion.

Compression means the useful intelligence is written into a current summary or current map first, then the stale source file is deleted when it has no remaining current/reproducibility value.

Mixed-context extraction means the useful intelligence is written into current truth first, stale sections are removed from active docs, and the original mixed source is deleted or rewritten according to the remaining value. A mixed source can remain only if the stale sections are removed or the file is clearly demoted to cold evidence through a pointer manifest.

Deletion must be executed for proven `DELETE_CONTEXT_POLLUTION_*` rows. A deletion ledger without deletion is incomplete.

For Git/LFS/GitHub footprint rows, decide and execute the current-HEAD cleanup:

- delete stale large files from HEAD;
- delete stale LFS pointer files from HEAD;
- remove stale LFS tracking patterns that no current file class uses;
- keep active LFS tracking only for current reproducibility evidence;
- replace raw large evidence with current summaries/manifests/pointers when raw rows are not default context;
- record any historical reachable large blob that remains outside HEAD as `HISTORY_REWRITE_REQUIRED_FOR_FULL_REMOTE_SIZE_CLEANUP` with exact object id, path, size, commit reachability, and rewrite command plan.

Current HEAD cleanup is mandatory inside this route. Historical Git rewrite is a separate destructive repository-history operation; this route must still produce exact rewrite-ready proof for any stale large blob that remains reachable after HEAD cleanup.

For local object/cache rows, decide and execute verified workspace cleanup:

- remove `__pycache__`, `.pytest_cache`, `.pytest-tmp*`, `.mypy_cache`, `.ruff_cache`, `.coverage`, `htmlcov`, `.ipynb_checkpoints`, temp files, abandoned `.tmp*`, `.bak`, generated local scratch, obsolete run outputs, and empty directories when not current evidence;
- run Git/LFS prune dry-runs or equivalent listings after HEAD cleanup, record reclaimable bytes and exact retained blockers, then execute verified local prune for objects proven unreachable from current refs and not required by current evidence manifests;
- record a `GIT_GC_OR_HISTORY_REWRITE_PLAN` for historical bloat that cannot be pruned without an explicit history rewrite.

For credential/account-artifact rows, execute deletion/redaction/current-keep decisions in the same route. Do not leave stale account screenshots, stale broker/account artifacts, or token-bearing files in default reading context.

## Stage 05 - Execute Cleanup

Execute the cleanup decisions.

Required actions:

- remove tracked stale files from HEAD;
- remove untracked stale local junk;
- remove or consolidate obsolete generated HTML/images/screenshots/videos;
- remove stale prompt drafts and obsolete starter files not referenced by current truth;
- extract useful sections from mixed stale files into current summaries, then delete or rewrite the source files;
- merge duplicated context into current authority files and delete duplicate sources;
- remove duplicate route outputs whose current value is captured in summaries/manifests;
- remove stale dev/build/cache artifacts and local generated scratch;
- remove empty directories after file deletion;
- update active docs and context maps;
- update `.gitignore` or repo artifact policy when new generated junk class is discovered;
- update LFS tracking, `.gitattributes`, pointer policy, and large-artifact policy to match the current cleanup decisions;
- update runtime/live-data retention policy so future sessions know which logs/data stay hot, which compress, and which delete;
- keep large current evidence outside default reading path with exact pointer and manifest.

Before any recursive delete or move, verify the resolved absolute target paths are inside the repo and match the ledger rows. Use native PowerShell path checks or an equivalent path-bounded method. This is execution discipline, not a deletion brake.

## Stage 06 - Staleness Guardrail

Add or update a local guardrail that catches future context drift.

Required output:

- `scripts/check_repo_context_staleness.py` or an equivalent existing-script extension;
- `REPO_CONTEXT_STALENESS_VERIFICATION.json`;
- focused tests or command proof.

The guardrail must scan active context/root docs for stale-current claims and fail on forbidden active-current patterns, including:

- current production universe described as 7 symbols;
- vNext production described as old PA/L2;
- static 1.5R/J46/J49 described as active vNext default;
- BE described as current active production policy when momentum/partial is current;
- stale April/old-live state presented as current;
- active reading order pointing agents first to obsolete handoffs instead of current vNext truth;
- deprecated route docs presented as current authority.

The guardrail allows historical mentions only when clearly labeled historical/deprecated/archived.

## Stage 07 - Verification Matrix

Run and record a cleanup verification matrix.

Required checks:

- parse JSON/JSONL artifacts generated by this route;
- verify every file in delete ledger is absent after cleanup;
- verify every current-HEAD Git/LFS/GitHub footprint cleanup decision is reflected in `git status`, `.gitattributes`, LFS listing, and manifests;
- verify no raw current-HEAD file exceeds GitHub hard limit and every warning-threshold file has an explicit keep/LFS/compress/delete decision;
- verify credential/account-artifact scan has zero unresolved stale account/token-bearing rows;
- verify runtime retention decisions preserve active live intelligence and delete/compress stale runtime noise;
- verify local cache/object prune decisions are executed or have exact history-rewrite/prune blockers;
- verify delete-breakage proof ledger has zero unresolved current-reference breakage rows;
- verify every kept current-authority file exists;
- verify every compressed file has replacement summary/path;
- verify every mixed-context file has section-level extraction/rewrite/delete proof;
- verify duplicated context has one current authority and deleted or demoted duplicates;
- verify active docs point to current truth layer;
- verify root/context docs no longer present stale old-system claims as current;
- verify prompt hardening validator passes for this cleanup prompt;
- verify repo staleness guardrail passes;
- verify git status/staged scope is cleanup-owned;
- verify no unresolved same-evidence-class cleanup invariant remains.

Write:

- `REPO_CLEANUP_VERIFICATION_MATRIX.json`
- `REPO_CLEANUP_COMPLETION_AUDIT.json`

The completion audit must not self-certify. It must list each instruction, evidence artifact, command result, and remaining invariant.

## Stage 08 - Commit

Create a scoped cleanup commit after verification passes.

Commit message:

`chore: delete stale repo context and package current vnext truth`

Include:

- current truth layer;
- updated active docs/context entrypoints;
- deletion/compression/keep manifests;
- mixed-context extraction and context-consolidation ledgers;
- Git/LFS/GitHub footprint cleanup manifests;
- credential/account-artifact repair and runtime retention ledgers;
- local object/cache prune ledger;
- staleness guardrail;
- verification artifacts;
- actual deletions.

Final commit scope includes cleanup-owned changes only: current-truth artifacts, active-doc repairs, guardrails, verification artifacts, and actual deletions.

## Subagent Use

Use sidecar auditors where it improves coverage. Give them different bounded roles and exact paths:

- active context stale-current auditor;
- generated/media/junk deletion auditor;
- research-route compression auditor;
- current-vNext truth consistency auditor;
- deletion red-team checking accidental keep decisions and accidental delete risks.

Close or reuse agents as needed. Tool/thread limits are not a reason to skip repository coverage. Advisory outputs must be validated against disk evidence before they become route decisions.

## Completion Standard

The route is complete only when all are true:

- full repo inventory exists;
- Git/LFS/GitHub footprint inventory exists;
- every material file is classified;
- mixed files are classified at section/claim/table level, useful intelligence is extracted, stale sections are deleted or rewritten, and polluted originals are deleted or demoted;
- duplicated useful context is consolidated into current authority files and duplicate sources are removed;
- every current-HEAD large/LFS/pushed file has an executed cleanup decision;
- credential/account-artifact scan has no unresolved stale account/token-bearing rows;
- runtime retention policy exists and current live intelligence is separated from stale runtime noise;
- local dev/cache/Git/LFS prune cleanup is executed or exactly bounded with rewrite/prune proof;
- delete-breakage proof checks show no unresolved accidental-delete risk;
- proven stale/irrelevant files are deleted from active repo or compressed then deleted;
- current truth layer exists and is linked from active entrypoints;
- stale active docs are repaired;
- large evidence is separated from default context with manifests;
- staleness guardrail exists and passes;
- cleanup verification matrix passes;
- deletion bytes/counts and current-context reduction are reported;
- route state says first incomplete invariant is `null`;
- scoped commit exists.

If the session finds additional cleanup questions, stale file families, generated junk classes, or context-pollution patterns while executing, add them to the same route and resolve them. Do not stop at the examples in this prompt.
