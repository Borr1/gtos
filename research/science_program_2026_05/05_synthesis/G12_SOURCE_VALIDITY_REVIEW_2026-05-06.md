# G12 Source-Validity Review - 2026-05-06

**Lane:** `G12`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Registry State

G12 read `SOURCE_CONTRACT_REGISTRY_2026-05-06.json`, `SOURCE_BUDGET_LEDGER_2026-05-06.json`, and the master registry. The controlling source state is:

- source contract rows: `86`;
- `validation_safe=true` rows: `0`;
- source budget spend allowed: `false`;
- current new external cash cap: `$0`;
- no paid source, MT5, order, AI, canary, credential, remote, or live behavior action is authorized by G12.

## Source-Validity Findings

| ID | Scope | Current evidence | Validity blocker | G12 decision |
|---|---|---|---|---|
| `G12-SRC-001` | Global source registry | All 86 source contracts remain `validation_safe=false`. | No CD2 artifact provides a source-specific legal/cache/parser/publication/no-lookahead dossier. | Preserve `validation_safe=false` globally. |
| `G12-SRC-002` | CD2-01 macro/vol source freshness | COT/FRED/BIS/Cboe/VRP rules are defined, but Cboe publication timing, FRED cache/vintages, BIS table/release policy, COT release schedule handling, and VRP formula boundaries remain unresolved. | Source rows are not decision-time safe. | Block outcome review and master source-safety edits. |
| `G12-SRC-003` | CD2-02 accepted short-vol lifecycle prereg | References Cboe vol CSV, G10 lifecycle/path/MT5 account-history, and G11 Cboe options-vol sources; all remain validation-safe false. | Same-day Cboe daily rows and lifecycle ordering need parser/as-of proof. | Survives as prereg only; no source validity granted. |
| `G12-SRC-004` | CD2-03 accepted offline RL prereg | Reward contract is local/offline and source-light, but future scoring depends on G10/G6 path/lifecycle fields and conservative cost model. | Behavior policy, reward ledger, path labels, and cost sources are not validation-safe for promotion. | Survives as prereg only; no outcome opening. |
| `G12-SRC-005` | CD2-04 K55/orderflow provenance | Databento/Sierra/G4/G9/G11 sources are allowed as status/provenance only; numeric-ready source bundles are `0`. | Raw orderflow/depth values, proxy transfer, legality, live license, and validation-safe claims remain blocked. | Status-only contract is acceptable; predictive source features remain blocked. |
| `G12-SRC-006` | CD2-05 macro/attention | Local news calendar exists at `data/news_calendar.json`, but source contract references `data/news/forexfactory_calendar.json`; Fed/FOMC parser and stale-source tests are missing; external G5 attention proxies are not validation-safe. | Source path mismatch and stale calendar block even lifecycle-only outcome review. | Reject master machine row until source cleanup and parser tests exist. |
| `G12-SRC-007` | CD2-06 prefill/path | Current rows miss `source_hash`, `source_symbol`, ordered prefill candles, prefill tick summaries, and pending-native fields. | Provenance and ordered-path source validity are insufficient. | Status-only; no path or fill-quality validation. |
| `G12-SRC-008` | CD2-07 opportunity-cost sidecar | FTMO/redacted_account sources are partial parser context; FRED/rates cache failed; Cboe publication timing unknown; correlation/risk snapshots incomplete. | Observation-only source map cannot support source-safe opportunity-cost outcomes. | Keep sidecar blocked from master. |
| `G12-SRC-009` | CD2-08 source/no-leak cleanup | Proposal replaces placeholders with concrete source IDs and dependency fields without marking sources validation-safe. | It is a cleanup proposal, not blocker-clearing source evidence. | Accept as future cleanup guidance only; no registry edit in G12. |
| `G12-SRC-010` | Unregistered source placeholders | G0 records 18 source-reference issues: G5 `LIT-*` references and G7 cross-domain placeholders/hypothesis IDs in `source_ids`. | Non-`source_contract_v2` IDs can be double-counted as market sources. | Move to `evidence_refs`, `neighbor_lane_dependency`, or `blocked_dependency_refs` in a future cleanup. |

## Exact Future Source Corrections Proposed By G12

| Current row or family | Future correction |
|---|---|
| `HYP-G7-XG5-MACRO-ATTN-010` | Keep only `SRC-G7-FED-FOMC-001`, `SRC-G7-LOCAL-GTOS-MACRO-001`, and `SRC-G5-NEWS-CALENDAR-LOCAL-001` in `source_ids`; move `HYP-G5-XG7-MACRO-ATTN-009` to `neighbor_lane_dependency`. |
| `HYP-G7-XG8-VOL-MACRO-011` | Replace `future_G8_options_vol_rows` with explicit source IDs `SRC-G8-CBOE-VOL-CSV-001` and `SRC-G8-VRP-FORMULA-005`; keep dependencies on G8 hypotheses outside `source_ids`. |
| `HYP-G7-XG11-SOURCE-FRESH-012` | Replace `future_G11_source_governance_rows` with `SRC-G11-LOCAL-G0-REGISTRIES`, `SRC-G11-LOCAL-LTO031032-SOURCE-UNBLOCKING`, and `SRC-G11-PUBLIC-CFTC-FRED-BIS`; move G11 hypothesis dependencies out of `source_ids`. |
| G5 literature references | Move `LIT-G5-*` values to `evidence_refs`; use `SRC-G5-ACADEMIC-LIT-001` only as context-only source-contract evidence if a resolving source ID is needed. |
| G11 rows | Add only concrete G11/G4/G5/G7/G8 source-contract IDs already present in the source registry; keep all `validation_safe=false`. |
| Source validation flips | Require a separate source-specific dossier with legal/access state, source cache path/hash, parser version, publication/as-of timestamp rule, no-lookahead tests, and source-row examples before any `validation_safe=true` change. |

## NO_PROMOTION_VERDICT

G12 clears no source for validation. All source-related rows remain research-control, context-only, observation-only, or blocked.
