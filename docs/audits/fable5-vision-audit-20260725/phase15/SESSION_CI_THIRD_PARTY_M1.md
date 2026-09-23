# Session CI — the third-party M1 ingest: vp decidable now, not in September (wave 15, B2500–B2549)

**Codex session #3, full network access.** The conventions in `SESSION_CG_LANE_FOOTPRINT.md`
§"Conventions that bind you" apply verbatim. Read first:
`phase15/receipts/FTMO_SYMBOL_RENAME_EVENT_20260731.md` §"The vp M1 backfill" (the measured
negative this session routes around: NO broker serves M1 older than ~3 months under any
name), `phase14/SESSION_CA_REVIVAL_GATES_RESULT.md` §0.3 + §0.5 (vp's first evidence — 33
trades, +0.486 R/trade gross, NOT_EVALUABLE on 1 fold vs a floor of 3 — and the CsvBarSource
fail-open repair whose honesty you inherit), `src/utils/research_timebase.py` (the sanctioned
sidecar writer), `WAVE_11_WORKING_AGREEMENT.md` §1/§6. Owner authority: OD-HISTORICAL-FIRST
§2 ("missing data is a fetch, never a verdict") and Borhen's explicit "data is data" —
third-party bars are legitimate WITH declared provenance.

**The objective in one sentence:** extend GER40/UK100 M1 coverage back past 2025-12 from a
third-party source with honestly-declared provenance, validate it against the broker's own
overlap window, and give `vp_euidx_pocgrav` its first decidable gate.

## Work orders

**CI-1 — Source and fetch.** Dukascopy-class free historical M1 for the DAX (GER40) and
FTSE-100 (UK100) index CFDs, covering AT MINIMUM 2025-12-01 → 2026-04-27 (the join to broker
data) and as far back as the source honestly serves (2024+ buys folds). Document the exact
instrument identity (cash index vs CFD vs future — say what the source actually quotes),
the download provenance (URLs, instrument codes, fetch date), and land raw + converted files
under `data/mt5_research_exports/thirdparty_m1_ger40_uk100_20260731/` in the estate's CSV
shape. If the primary source is blocked, try one alternative, then report the exact blocker
— a failed fetch with receipts beats a silent substitute.

**CI-2 — Provenance-declared sidecars.** Write `.timebase.json` sidecars with the sanctioned
writer, basis stated as what the source ACTUALLY uses (likely UTC — do not launder it into
`broker_server_local`), evidence text: `THIRD-PARTY, provenance-declared: <source>, fetched
2026-07-31; NOT broker bars; see CI-3 for the measured divergence vs FTMO-Server3 on the
overlap window.` The loader must accept them through the front door — no loader edits to
make data fit.

**CI-3 — The validation that makes third-party honest.** The broker's own M1 exists from
~2026-04-27 → today (fetchable view already measured). On the overlap window, measure
per-bar OHLC divergence (bps distribution, gap alignment, session boundaries, DST behaviour)
between the third-party series and FTMO's `.cash` series. Publish the divergence table —
that number is the caveat every downstream verdict carries. If divergence is structurally
large (different session calendars, different underlying), SAY SO and stop short of gating
rather than gating on unlike data.

**CI-4 — The vp gate, decidable.** Re-run the `vp_euidx_pocgrav` gate (CA's
`ca_revival_gate.py` pattern — reuse its declared cut rules P1–P5 and verdict vocabulary,
outcome-blind) at the ratified rule with the extended M1 aux: RECORDED population, band
alongside, chronological folds (now ≥3 evaluable), maxbars share, broker-true costs from OUR
spread/era models (state that costs are FTMO-priced on third-party bars — declared, not
hidden). vp's `CANDIDATE_BOOK_V1` look is already TAKEN (CA converted it); extending data on
the same declared member is not a new look — state this against the ratchet rather than
assuming it silently. Deliverable: REVIVAL_CANDIDATE / CONDITIONAL / STAYS_DEAD /
NOT_EVALUABLE-still, with the third-party caveat carried on every number; a
REVIVAL_CANDIDATE gets a CC-shape incubation dossier (`OWNER_RISK_ACCEPTED` unless it
actually graduates).

## Done means

Result doc `phase15/SESSION_CI_THIRD_PARTY_M1_RESULT.md` findings-first + receipts, blocks
B2500–B2549, scoped A/B vs the ZERO baseline (12,476) with the tool-emitted fence, honest
what-I-got-wrong, handoff list. Never touch the VPS; never run broker-capable scripts; never
edit `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, or any R2-bound path;
March 2026 outcome-unread. Arm nothing; file candidates. Keep heavy runs ≤2 concurrent while
CD's arms finish.
