# G0 Post-G12 Blocker To Next-Action Map - 2026-05-06

**Lane:** `G0`  
**Status:** `G0_POST_G12_BLOCKER_MAP_COMPLETE_RESEARCH_CONTROL_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

This map converts G12 red-team findings into concrete future actions. These are blocker-clearing or cleanup actions only. They are not live-trading changes, promotion tasks, source-validation flips, or outcome reviews.

## Blocking Map

| Blocker ID | Scope | Current blocker | Next action | Owner lane |
| --- | --- | --- | --- | --- |
| `POSTG12-BLK-001` | G11 no-leak fields | Eight G11 hypotheses list forbidden outcome/future names in `no_leak_fields`. | Replace with as-of feature whitelists and move forbidden names to blockers/test-method text. | `G0/G11/G12` |
| `POSTG12-BLK-002` | Source references | Eighteen source-reference issues remain from G5 literature refs and G7 cross-domain placeholders. | Move literature refs to `evidence_refs`, hypothesis IDs to `neighbor_lane_dependency`, and future placeholders to `blocked_dependency_refs`. | `G0/G5/G7/G11` |
| `POSTG12-BLK-003` | Macro/vol source joins | COT/FRED/BIS/Cboe/VRP publication/as-of rules are not proven. | Build source-specific cache/parser/hash/publication/vintage/no-lookahead tests before outcome review. | `G7/G8/G11/G1` |
| `POSTG12-BLK-004` | Broker actual-R | Broker actual-R evidence remains too sparse for actual-R claims. | Keep broker actual-R separate until sufficient account-history realized rows with fill/cost linkage exist under a separate prereg. | `G10/G1` |
| `POSTG12-BLK-005` | CD2-03 risk bank | Offline-RL risk-bank fields can mix label lanes if named generically. | Use `synthetic_closed_leg_r`, `synthetic_open_leg_stop_if_hit_r`, and `synthetic_episode_reward_r` for the current prereg. | `G9/G10/G1` |
| `POSTG12-BLK-006` | K55 source provenance | Source readiness/floor flags may encode post-outcome sample coverage if used as model features. | Keep coverage/floor-met flags as audit metadata unless timestamp-safe, global, and excluded from predictive vectors. | `G9/G4/G11/G1` |
| `POSTG12-BLK-007` | CD2-05 attention row | Macro/attention row is not canonical and source path/calendar/Fed parser blockers remain. | Produce machine-readable canonical row plus stale-calendar cache, Fed parser, attention source contract, and event-cluster effective-N. | `G5/G7/G1` |
| `POSTG12-BLK-008` | CD2-06 path data | Current prefill/path rows lack source hashes, ordered path packets, pending-native fields, spread/tick, and most trade IDs. | Split decision, ordered path, lifecycle, and execution/friction packets or enforce a strict feature whitelist. | `G10/G6/G4` |
| `POSTG12-BLK-009` | CD2-07 opportunity cost | Sidecar uses a non-master hypothesis ID and must not drift into missed-R or dollar value. | Create canonical master hypothesis ID and keep observation-only counts until a separate outcome-bearing prereg exists. | `G11/G10/G7/G8` |
| `POSTG12-BLK-010` | G6 normalization residue | Master rows normalized four G6 label classes, while lane artifacts retain verbose values. | Patch G6 lane artifacts in a future hygiene pass or require consumers to use only master-normalized rows plus normalization ledger. | `G0/G6` |
| `POSTG12-BLK-011` | Global source boundary | All source contracts are `validation_safe=false`. | Do not flip any source without a separate source-specific legal/cache/parser/as-of/no-lookahead dossier. | `G0/G11/G12` |

## Action Ordering

1. Preserve the global no-promotion state and empty survivor backlog.
2. Run source/no-leak cleanup only as a controlled registry-hygiene pass.
3. Build source-specific no-lookahead/parser dossiers before opening any macro/vol or source-driven outcome review.
4. Build packet/label separation tests before any path, lifecycle, RL, or opportunity-cost outcome analysis.
5. Revisit survivor backlog only after separate evidence proves a row is more than research-control inventory.

## NO_PROMOTION_VERDICT

These next actions are blockers and cleanup tasks. None authorize source validation, outcome opening, promotion, or live behavior changes.
