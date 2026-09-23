# Orderflow Proxy Mapping Priority Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registration verdict: `NO_PROXY_MAPPING_ACTIVATED`

## Summary

The current research orderflow manifest supports ['GBPUSD', 'NAS100', 'US30', 'US30_cash', 'XAGUSD', 'XAUUSD']. The remaining proxy-mapping blockers are {'GBPJPY': 23, 'USDJPY': 34}; USDJPY/6J is under transfer review and GBPJPY remains a two-book synthetic-cross problem.

## Current Coverage

- Rows loaded: 518
- Supported symbols: ['GBPUSD', 'NAS100', 'US30_cash', 'XAGUSD', 'XAUUSD']
- Unsupported symbols: ['GBPJPY', 'USDJPY']
- Supported candidate counts: {'GBPUSD': 21, 'NAS100': 12, 'US30_cash': 1, 'XAGUSD': 14, 'XAUUSD': 10}
- Unsupported candidate counts: {'GBPJPY': 23, 'USDJPY': 34}
- Unsupported orderflow-relevant rows: 271

## Priority Queue

| Rank | Symbol | Proposed futures proxy | Candidates | Relevant rows | Relation | Complexity | Status |
|---:|---|---|---:|---:|---|---|---|
| 1 | XAGUSD | SI.v.0 | 14 | 19 | direct precious-metal futures proxy | low | SUPPORTED_RESEARCH_PROXY_MAP |
| 2 | USDJPY | 6J.v.0 | 34 | 124 | inverse FX futures proxy | medium | NOT_IN_FUTURES_PROXY_MAP |
| 3 | GBPUSD | 6B.v.0 | 21 | 44 | direct FX futures proxy | low | SUPPORTED_RESEARCH_PROXY_MAP |
| 4 | GBPJPY | 6B.v.0, 6J.v.0 | 23 | 147 | synthetic cross from two FX futures legs | high | NOT_IN_FUTURES_PROXY_MAP |

## Rank Rationale

- XAGUSD: Closest unresolved extension of the already-supported GC/XAUUSD metals lane; single futures contract, direct directional relation, and no synthetic cross book.
- USDJPY: Largest unsupported candidate count and live-enabled, but the 6J quote direction is inverse to USDJPY, so it must pass an explicit sign/scale audit before event harvesting.
- GBPUSD: Clean direct futures relationship and useful as a control/leg for GBPJPY, but GBPUSD is observer-only in the current GTOS deployment, so it follows the live-enabled unresolved symbols.
- GBPJPY: Live-enabled, but there is no single CME GBPJPY ladder. Price transfer may be synthetic; orderflow/depth interpretation is split across two books and is therefore highest ambiguity.

## Blocking Validations

### XAGUSD
- SI.v.0 to XAGUSD M1 return correlation across multiple windows
- date-aware MT5 timestamp correction without per-window hindsight
- silver futures roll behavior around selected windows
- CFD/futures basis stability during London and NY kill zones

### USDJPY
- inverse-return sign agreement between 6J.v.0 and USDJPY
- price-scale convention for any absolute-level diagnostics
- roll/calendar continuity around JPY futures
- whether inverse depth/flow features preserve the same economic interpretation

### GBPUSD
- 6B.v.0 to GBPUSD M1 return correlation across multiple windows
- date-aware MT5 timestamp correction without per-window hindsight
- sterling futures roll behavior around selected windows
- observer-only status handling in any later event manifest

### GBPJPY
- 6B and 6J direct/inverse leg validation first
- synthetic cross return correlation against GBPJPY
- synchronized futures-leg timestamp policy
- definition of what a two-book LVN/HVN or absorption signal would mean

## Validation Protocol

- Scope: mapping validation before event-window harvesting
- Minimum first pull: one or more capped trades-only windows per proposed proxy; no depth pull before price-transfer passes

Mandatory checks:

- date-aware MT5 timestamp correction must be chosen by rule, not hindsight per window
- M1 return correlation and sign agreement must be checked on multiple windows
- roll-date behavior must be pinned for continuous futures symbols
- basis/lag diagnostics must be reported before any orderflow feature use
- observer-only symbols must stay controls unless separately promoted by CEO-approved system scope

Explicitly blocked:

- adding unsupported symbols to FUTURES_PROXY_MAP from this audit alone
- pulling mbp-1/mbp-10 depth before trades-level transfer passes
- using synthetic GBPJPY two-book depth as if it were one executable ladder
- registering an alpha hypothesis from proxy availability alone

## Synthesis

- Loaded 518 candidate-feature rows. Unsupported CANDIDATE rows total 57 across {'GBPJPY': 23, 'USDJPY': 34}.
- Supported CANDIDATE rows total 58 across {'GBPUSD': 21, 'NAS100': 12, 'US30_cash': 1, 'XAGUSD': 14, 'XAUUSD': 10}.
- Recommended validation order is based on current candidate inventory, live relevance, proxy directness, and transform risk.
- 1. XAGUSD -> SI.v.0: 14 current candidates; direct precious-metal futures proxy; complexity=low; status=SUPPORTED_RESEARCH_PROXY_MAP.
- 2. USDJPY -> 6J.v.0: 34 current candidates; inverse FX futures proxy; complexity=medium; status=NOT_IN_FUTURES_PROXY_MAP.
- 3. GBPUSD -> 6B.v.0: 21 current candidates; direct FX futures proxy; complexity=low; status=SUPPORTED_RESEARCH_PROXY_MAP.
- 4. GBPJPY -> 6B.v.0,6J.v.0: 23 current candidates; synthetic cross from two FX futures legs; complexity=high; status=NOT_IN_FUTURES_PROXY_MAP.

## Ambiguity Ledger

- This audit reflects the current research proxy map; it is not a live trading configuration change.
- XAGUSD/SI and GBPUSD/6B have strict price-transfer support, but no orderflow alpha is validated.
- USDJPY/6J requires inverse-return handling and remains under strict transfer review.
- GBPJPY has no single CME order book; synthetic price transfer and synthetic depth/flow interpretation are different problems.
- Current candidate counts come from the mutable local shadow log and are not an immutable historical population.
- Depth pulls remain blocked until symbol-specific event-window hypotheses are registered.

## Opened Questions

1. Does 6J.v.0 recover above the strict USDJPY transfer floor across additional windows?
2. Should GBPUSD/6B remain a control-only research symbol unless observer scope changes?
3. Can GBPJPY be represented by 6B/6J synthetic returns for price transfer without corrupting orderflow interpretation?
4. Which newly supported direct proxy, XAGUSD or GBPUSD, has enough labels to justify trades-feature extraction?
5. Can the seasonal -120/-180 minute MT5 timestamp policy be converted into a date-aware rule before more futures pulls?

## Next Steps

1. Build a refreshed event-window manifest with XAGUSD/SI and GBPUSD/6B included, but do not fetch depth.
2. Run one targeted 6J/USDJPY follow-up set before adding USDJPY to the research proxy map.
3. Keep GBPJPY orderflow blocked until both legs pass price transfer and a two-book hypothesis is registered.
4. Only after labels exist, extract trades-level features for newly supported symbols.
