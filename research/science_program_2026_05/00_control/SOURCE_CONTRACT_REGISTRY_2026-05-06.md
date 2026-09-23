# Science Program Source Contract Registry - 2026-05-06

**Status:** `POST_G12_NO_SOURCE_ROWS_VALIDATION_SAFE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `2026-05-06T12:08:31Z`
**HEAD read:** `64135c3a`
**HEAD reconciled for CD2:** `4db7f47a`
**CD2 merge commit:** `0e865798`

## Summary

G0 retains `86` `source_contract_v2` rows after CD2 reconciliation. All `86` remain `validation_safe=false`. CD2 added `0` source contracts.

## CD2 Source Decisions

- CD2-01 froze macro/vol source as-of rules but kept COT/FRED/BIS/Cboe/VRP blocked.
- CD2-04 allowed K55 source-status/provenance flags only; raw orderflow/depth features remain quarantined.
- CD2-07 mapped prop/risk/stress sources as observation-only and parser/source blocked.
- CD2-08 proposed source/no-leak cleanup for G12; no source row was edited.

## Source And No-Leak Blockers

- Validation-safe source rows: `0`.
- Source-reference placeholders or unregistered literature references: `18`.
- No-leak semantic blocker rows: `8`.
- `$0` new external cash spend remains in force.

## Post-G12 Closeout

G12 reviewed source validity and cleared no source. G0 post-G12 closeout preserves all `86` source rows as `validation_safe=false`; CD2-01/CD2-04/CD2-05/CD2-06/CD2-07/CD2-08 remain source-blocked, status-only, sidecar-only, or future-cleanup guidance. No source row is eligible for validation use without a separate source-specific legal/cache/parser/publication/as-of/no-lookahead dossier.

## NO_PROMOTION_VERDICT

This registry consolidates source contracts for governance. It does not make any source validation-safe.
