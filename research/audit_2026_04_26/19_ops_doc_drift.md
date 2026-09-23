# AUDIT 19: OPS-DOC-DRIFT (operational docs vs current code)

Total 8 drift findings across 6 docs: 3 HIGH, 2 MEDIUM, 3 LOW.

## CLAUDE.md (recently pruned) ACCURATE.

## Pre-deploy checklist
Mostly correct (item-numbering mismatch, ftmo.yaml/redacted_account.yaml naming clarity).

## Operator Playbook v3 STALE — 3 weeks old (HIGH)
- Missing XAGUSD + NAS100 in all 41 scenarios

## ARCHITECTURE.md predates entire live system (HIGH)
- Describes single-framework single-instrument design

## QUICK_REFERENCE_CARD
- NY-candle skip window confusing wording
- Missing XAGUSD 0.5% + NAS100 0.25% risk overrides

## MASTER_ROADMAP.md OBSOLETE (April 2 era)

## 00_READING_ORDER stale
- TIER 1 ref to handoff 15
- Current is 40

## Phantom features: NONE

## Hidden features: 3 shipped but not in operational docs
- S1 monthly decay
- A.2 logger
- C.3 class-aware
