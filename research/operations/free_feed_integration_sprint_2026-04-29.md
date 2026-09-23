# Free-Feed Integration Sprint (10 eng days)

**Filed:** 2026-04-29 (Phase 2 dispatch sequence — CEO-approved as decision #5)
**Source:** `research/ml_program/forensics/2026-04-29/agent_d_substrate_audit.md` + `agent_d_substrate_immune_directions.md`
**Status:** AWAITING MAIN-THREAD ENGINEERING (no production state changes; pure data ingestion infrastructure)
**CEO approval:** 2026-04-29 (Phase 2 dispatch sequence sync)
**Owner:** Main-thread engineer

## TL;DR

Replace the Databento subscription path (12-month ROI -91%, $2,148/yr cost vs $200/yr expected lift) with a **10-engineering-day free-feed integration sprint**. $0/yr ongoing cost. ~$400/yr expected R-lift via 19 substrate-immune feature unblocks. Plus investigate **futures broker route** (NinjaTrader/IBKR/AMP via Rithmic/CQG, $50-100/mo for L2) as a 30-50% cheaper alternative to Databento for futures-equivalent instruments (NAS100/US30 via NQ/YM contracts).

## Why this beats Databento

Per Agent D's full ROI audit:

| Path | Annual cost | Expected lift | 12-mo ROI | Spot-FX coverage? |
|---|---:|---:|---:|---|
| Databento CME Standard | $2,148 | $200 | **-91%** | NO (Hotspot/EBS aggregated) |
| Free-feed sprint | **$0** | $400 | **INF** | Partial (CFTC + LBMA + macro) |
| Futures broker (Rithmic/CQG) | $600-1,200 | $300-500 | -30% to -50% | NO (futures only) |
| FN Level-2 add-on | unknown | unknown | n/a | YES if available; verified-NULL 2026-04-29 |

**Free-feed sprint is the only positive-ROI path. Futures broker route is conditionally interesting if NAS100/US30 dealer-gamma features prove valuable.**

## Five free feeds to integrate (per Agent D ranking)

### 1. CFTC COT (Commitments of Traders)
- **Unblocks:** A-9 Gold COT positioning (large-spec / commercial / managed-money).
- **Source:** `https://www.cftc.gov/dea/futures/dea_cot_txt.htm` (free text feed) OR `cftc.gov/MarketReports/CommitmentsofTraders/index.htm`.
- **Cadence:** Weekly Tuesday release.
- **Data:** Per-instrument long/short/spread positions for large/small specs + commercials.
- **Eng days:** 1-2.
- **Output schema:** `data/external/cftc_cot/{INSTRUMENT}_{YYYY-MM-DD}.csv`

### 2. FRED (Federal Reserve Economic Data)
- **Unblocks:** A-13 Brunnermeier-Nagel-Pedersen funding-liquidity (TED spread, FRA-OIS), A-7 Treasury-basis (DXY change indirect), intermediary-capital proxies.
- **Source:** `fred.stlouisfed.org/docs/api/fred/` (free API; key registration required).
- **Series:** TEDRATE, T10Y2Y (2Y-10Y curve), DGS10, DGS2, VIXCLS, GVZCLS (gold vol index), DTWEXBGS (broad dollar).
- **Cadence:** Daily / weekly per series.
- **Eng days:** 1.
- **Output schema:** `data/external/fred/{SERIES_ID}.csv`

### 3. WGC (World Gold Council) central-bank flow
- **Unblocks:** A-10 Gold central-bank-flow (Arslanalp 2023 sanctions-driven CB demand).
- **Source:** `gold.org/goldhub` (free dataset downloads + monthly reports).
- **Data:** Per-country central bank gold purchases / sales (monthly).
- **Cadence:** Monthly.
- **Eng days:** 1 (manual scrape; no public API).
- **Output schema:** `data/external/wgc_cb_flows/{YYYY-MM}.csv`

### 4. LBMA (London Bullion Market Association) fix
- **Unblocks:** A-11 LBMA fix anomaly feature (Caminschi-Heaney 2014; XAU NY kill-zone edge).
- **Source:** `lbma.org.uk/prices-and-data/precious-metal-prices` (free historical XAU + XAG fix prices).
- **Data:** AM fix (10:30 London), PM fix (15:00 London) for XAU/XAG/PT/PD.
- **Cadence:** Twice-daily.
- **Eng days:** 0.5 (calendar feature; closed-form computation on existing OHLCV).
- **Output schema:** `data/external/lbma_fix/{INSTRUMENT}_{YYYY}.csv` + features computed on the fly.

### 5. CBOE GEX proxy (FlashAlpha or GEX-Metrix)
- **Unblocks:** A-1 Gamma-sign feature for indices, A-2 VIX1D-VIX9D spread.
- **Source:** `flashalpha.io` (free tier ~$0/mo for daily snapshots) OR `gex-metrix.com` (free historical).
- **Data:** Dealer gamma exposure (GEX) per index; VIX1D + VIX9D series.
- **Cadence:** Daily.
- **Eng days:** 1-2 (registration + scraping; no public API).
- **Output schema:** `data/external/cboe_gex/{INSTRUMENT}_{YYYY-MM-DD}.json`

## Total engineering investment

- **5-6 eng days** for the 5 feeds above.
- **2-3 eng days** for unified `src/components/external_feeds.py` adapter (consistent API across feeds).
- **1-2 eng days** for catalog feature additions (compute features from feeds; merge into K54 catalog as new feature family).
- **Total: ~10 eng days.**

## Items unblocked

Per Agent D's substrate matrix (`agent_d_substrate_matrix.csv`), the 5 feeds unblock approximately **19 substrate-immune items**:

- A-1 Gamma-sign feature for indices.
- A-2 VIX1D-VIX9D spread.
- A-3 VRP delta.
- A-7 Treasury-basis + Fed-funds + intermediary-capital features.
- A-8 Erb-Harvey real-gold-price percentile.
- A-9 Gold COT positioning.
- A-10 Gold central-bank flow.
- A-11 LBMA fix anomaly.
- A-12 Krohn-Mueller-Whelan FX-fix W-shape (calendar features from LBMA).
- A-13 Brunnermeier-Nagel-Pedersen funding-liquidity.
- A-14 Aquilina BIS JPY-carry-unwind regime classifier.
- + 8 derivative interaction features (e.g., gamma × regime, COT × side).

These flow into K54 v4+ catalog enrichment OR position-management variants.

## CEO-approval status
- 2026-04-29: CEO approved free-feed sprint as part of Phase 2 dispatch sequence (decision #5).
- Databento DEFER (-91% ROI) confirmed.
- Futures broker route INVESTIGATE (separate ticket below).

## Recommended order of operations

1. **Day 1: API key registration** for FRED + FlashAlpha. Set up output directory structure.
2. **Days 2-3: FRED + LBMA integrations** (cheapest, fastest wins).
3. **Days 4-5: CFTC COT + WGC** (manual scrapes; less polished but high data value).
4. **Days 6-7: CBOE GEX + dealer-gamma feature catalog additions.**
5. **Days 8-10: Unified adapter `src/components/external_feeds.py` + catalog feature integration + smoke tests.**

## Companion ticket: Futures broker route investigation

**Separate task (not part of 10-eng-day sprint):** evaluate NinjaTrader/IBKR/AMP via Rithmic/CQG for futures L2 depth.

- **Cost:** $50-100/mo (30-50% cheaper than Databento).
- **Coverage:** NQ (NAS100-equivalent), YM (US30-equivalent), GC (XAU-equivalent), 6E/6J/6B (FX futures).
- **Caveat:** Futures contracts are different instruments from spot; participants + intraday seasonalities differ. Per Agent D analysis, may not transmit fully — but L2 depth IS present where MT5 retail has none.
- **Investigation cost:** 0.5 day (research + provider quotes + prototype data feed).
- **Decision gate:** if dealer-gamma features (CBOE GEX) prove valuable in K54 v4+, escalate to futures broker route to enable per-tick gamma reconstruction.

## CEO-approval status (companion)
- 2026-04-29: CEO approved investigation as part of decision #5. No commitment yet to subscribe.

## Pre-dispatch screening
Before any future literature-port dispatch, run `research/ml_program/forensics/2026-04-29/agent_d_pre_dispatch_screen.py`:
```bash
python research/ml_program/forensics/2026-04-29/agent_d_pre_dispatch_screen.py --item-id <ID>
```
Returns PASS / PARTIAL / FAIL on MT5 retail substrate. Avoids K-4-class re-discoveries.

---

*Ticket end. Main thread: claim when ready; estimated 10 eng days. Output integrated into K54 v4+ catalog + position-management Phase 2 dispatches.*
