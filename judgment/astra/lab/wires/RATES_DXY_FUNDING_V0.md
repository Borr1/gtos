# ULTRAGOAL — RATES / DXY / FUNDING V0

**Seat:** research-only typed Nouls. **No broker place. No remint. No flatten. No APPLY size.**
**Date:** 2026-09-18
**Schema:** `gtos.judgment.rates_dxy_funding.v0`
**Assembler:** `src/judgment/rates_dxy_funding.py` `assemble_rates_dxy_funding_v0`
**Prove:** `prove_rdf_challenge_as_of` → [`RDF_CHALLENGE_ASOF_RECEIPT_V0.json`](RDF_CHALLENGE_ASOF_RECEIPT_V0.json)
**Inventory:** `src/judgment/named_sources.py` `named_source_inventory`
**Questions:** `src/judgment/rdf_questions.py` (Noul-first; LABEL only)
**Parent desk:** [`ULTRAGOAL_WORLD_STATE_V0.md`](ULTRAGOAL_WORLD_STATE_V0.md) (PR #12)
**Correctness that still binds:** `JEV_INTEGRATION_V2` §8 — `NEWS_PROTOCOL` is **not in git**.

Owner ultragoal: hedge-fund-like context (USD impulse, rates path, funding/liquidity, risk-on/off) as **curated typed state into Jev** — not a chat LLM dumping raw X into orders, and not invented HTTP clients.

---

## 0. Non-goals

| Forbidden | Why |
|---|---|
| Invent `NEWS_PROTOCOL` URLs / calendar clients | V2 §8. Host `events.jsonl` is a writer tape. |
| Raw X firehose / funding-AI prose | `never_ingest_raw_x`. Narrative stays unassembled. |
| Treat USD FX as a yield print | `rates_impulse.usd_fx_is_not_a_yield = true`. |
| Treat gold `spread_r` as funding stress | That is `liquidity_hurtful_world` on WORLD_STATE_V0. |
| Treat Sierra VIX_VXM as TED/funding | Control-only vol slice, 3 D1 bars, April 15–17. |
| Treat Sierra ZN_CONTROL as Challenge-true rates | Control-only, **3 D1 bars**, April 15–17. |
| Rescale `data/DXY_D1.csv` ×4 because 25×4≈100 | No named metadata. Inventing a scale is a lie. |
| Score April `data/historical_2026` as Challenge-true | `test_bars_multi.py` already forbids this. |
| APPLY / size_tilt / ENFORCE from this pack | `never_resize` / `never_apply_size`. Chair LABEL only. |

---

## 1. Source map (this clone, read from disk 2026-09-18)

Code regenerates the same map: `named_source_inventory()`.

### 1.1 Challenge-true (F5 login `0` / `operator`)

| Tissue | Path | Status |
|---|---|---|
| XAU M15/H4/D1 | `judgment/astra/lab/challenge_shadow_20260917/XAUUSD_*.csv` | **Present.** 1597 / 75 / 56 bars. |
| Multi FX / index landing | `…/challenge_shadow_20260917/multi/` | **Landed 2026-09-18** (Chair peer zip `_peer_multi_20260918_0c0a` + `_gbpjpy_eurgbp_20260918_518a`). EURUSD/GBPUSD/USDJPY/US30 + EURGBP/GBPJPY M15+H4. **No D1** for non-XAU. NAS100/UK100 still empty. |
| Host writer tape | `…/events_since_20260915.jsonl` | Present. Wave M: inventory **never READ**. |
| HIGH spines | `data/news/f5_high_calendar_host_20260916.json` + FF this-week + June `data/news_calendar.json` | Present. Event proximity ≠ rates impulse. |

### 1.2 Lab-only broker CSVs (never Challenge-true)

| Pack | What is on disk | Window |
|---|---|---|
| `data/historical_2026/` | EURUSD, GBPUSD, USDJPY, NAS100, US30_cash, UK100, XAGUSD (M15/H1/H4/D1) | 2025-10-01 … **2026-04-24** |
| `data/historical/` | GBPUSD, USDJPY, US30_cash (no EURUSD / NAS100 / UK100) | older |
| `data/historical_2022_2023/` | GBPUSD, USDJPY, NAS100, XAGUSD | 2022–2024 |

`tf_snap` / RDF last-bar returns refuse stale tapes (`D1` max lag 5 days). A September 2026 Challenge as-of **cannot** wear April 2026 D1 closes.

### 1.3 DXY — file present, **rejected**

`data/DXY_D1.csv`: 515 D1 rows, 2024-02-29 … 2026-04-02, **last close 25.65**.

ICE Dollar Index lives in **70–130** (named band in `named_sources.ICE_DXY_*`). This file is not ICE DXY. It is also not 2026 XAGUSD (that D1 prints ~73 on 2026-04-02). WORLD_STATE_V0's phrase `no_dxy_csv_on_this_clone` was **stale as wording** — a file exists; RDF rejects it as `dxy_csv_present_but_not_ice_dxy`. `usd.dxy.series` stays `null`. No rescale.

`scripts/session9_task4_dxy_gold.py` downloads `DX-Y.NYB` via **yfinance**. That is not a named Challenge feed and is **not** wired here.

### 1.4 Rates stubs

| Candidate | Present? | Usable as `rates_impulse`? |
|---|---|---|
| `data/US10Y_D1.csv`, `TNX_D1.csv`, `DGS10.csv`, `DGS2.csv` | **No** | — |
| `data/fred/` cache | **No** | 2026-05 lane-6 already blocked TED/funding as incomplete |
| Sierra `ZN_CONTROL_D1.csv` | Yes — **3 rows**, 2026-04-15 … 04-17, last ~111.64 (plausible ZN) | **No.** `control_only`. Too thin. Wrong clock vs Challenge Sep-17. |
| Sierra `ZN_CONTROL_{H1,M15,M5,M1}` | Same 3-day bounded conversion | Same refusal |

### 1.5 Funding / liquidity stubs

| Candidate | Present? | Usable as `funding_stress`? |
|---|---|---|
| TED / SOFR / FRA-OIS / VIXCLS CSV | **No** | — |
| Sierra `VIX_VXM_D1.csv` | Yes — **3 rows**, April 15–17, last ~21.0 | **No.** Vol control ≠ funding. |
| Gold `spread_r_of_stop` | Via gold_state when attached | **No.** Different Noul (`liquidity_hurtful_world`). |
| Crypto funding rates | **No** | — |

### 1.6 Still missing (named)

`NEWS_PROTOCOL`, `MAC_INGEST`, Walter / `desk_briefs`, official F5 leftover-ship live freshness protocol.

---

## 2. What can be computed **now** vs blocked

| Noul | Lab / fixture (research) | Challenge-true (this clone) | Blocked on |
|---|---|---|---|
| `usd_impulse` | **Yes** — last D1/H4 return on named EURUSD/GBPUSD/USDJPY, USD-mapped. Thresholds 20 bp D1 / 10 bp H4. | **Assembles.** Prove as-of `2026-09-17T11:00Z`: H4 mean **−7.2 bp** → `value=false`, `stance=flat`, `challenge_true_target=false`. EURGBP/GBPJPY are landed and **not** USD-mapped. | D1 still absent (H4 is the print). |
| `rates_impulse` | **Only if** a caller injects named `yield_books` (tests do this). Default **null**. | **Null.** No yield invent. | Named US10Y/TNX/DGS10 with clock; or owner-promote an *extended* ZN (not the 3-day control). |
| `funding_stress` | **Only if** a caller injects named `funding_rows`. Default **null**. | **Null.** No TED invent. | TED/SOFR/FRA-OIS + publication time. Do not invent FRED URLs. |
| `risk_on_off` | **Yes** — last D1/H4 on named NAS100/US30/UK100. Yes-event = **risk_off**. Thresholds 40 bp D1 / 20 bp H4. Mixed → null. | **Assembles from US30 H4.** Prove as-of: H4 **+51.8 bp** → `stance=risk_on`, `value=false`. NAS100/UK100 still empty. | Broader index book. |

USD *proxy quality* that can be computed now:

- Challenge FX basket assembled vs DXY file **rejected** → `fx_basket_only_dxy_rejected`.
- Agreement vs ICE DXY: **uncomputed** until a usable DXY lands. DXY reject **kept**.

USD *stance* (WORLD_STATE_V0 ATR trend) is a different question from *impulse* (last-bar return). Both are FX-proxy, not DXY.

---

## 3. Typed fields

Each Noul block:

```
noul, value (true|false|null), assembled, feed_class,
challenge_true, challenge_true_target, lab_target,
source, reason, source_paths
```

`challenge_true_target` is **null** unless `feed_class == challenge_true` (path contains `challenge_shadow`). Fixtures use `source_path=fixture:…` → `lab_or_fixture`. That is the honesty the Chair asked for.

`feed_class`: `challenge_true | lab_or_fixture | sierra_control | unassembled`.

Sierra control books, if someone passes them as `yield_books`, stay **unassembled** (`sierra_zn_control_only_not_a_rates_print`).

---

## 4. Jev pack

Pack id: `gtos.judgment.rdf_pack.v0`

| Name | Yes-event | Missing |
|---|---|---|
| `usd_impulse` | USD-up impulse | ~0.5 |
| `rates_impulse` | Named yield up | ~0.5 — **not** easing |
| `funding_stress` | Named funding ≥ threshold | ~0.5 — **not** calm |
| `risk_on_off` | Named risk_off | ~0.5 if mixed/unassembled |

Choices: `usd_impulse_stance`, `risk_on_off_stance`, `rdf_chair_draft`.

`compose_rdf_shadow`: `abstain` if all four values are null, else `label`. **Never `enforce`. Never `veto` from a missing feed. Never resize.**

---

## 5. Repair list (do not skip)

1. **Land remaining Challenge index** (NAS100, UK100). EURUSD/GBPUSD/USDJPY/US30 + EURGBP/GBPJPY are in `multi/` as of 2026-09-18. D1 for non-XAU still absent.
2. **Replace or delete `data/DXY_D1.csv`.** 25.65 is not ICE DXY. Do not ×4.
3. **Ingest a named yield tape** (US10Y / TNX / DGS10) with publication clock. Do not promote 3-day ZN_CONTROL silently.
4. **Ingest TED/SOFR/FRA-OIS** with no-lookahead metadata. Lane-6 (2026-05-03) already recorded this as blocked. VIX_VXM is not the repair.
5. **Do not invent `NEWS_PROTOCOL`.** Ingest the real Project file when it exists.
6. **Host writer must READ** before any calendar-honest claim (Wave M). Unrelated to rates impulse, still binding.
7. **No raw X.** Desk briefs only if the Mac Project emits them.

---

## 6. Chair land-later

1. LABEL the four Nouls as research shadows next to WORLD_STATE_V0.
2. Do **not** add RDF ids to the 48-fluid inventory in this pack.
3. Do **not** call `apply_named_tilts`. Physical lots stay flow × cost.
4. VETO / ENFORCE are WORLD / gold packs after PROVED_SHADOW — not RDF V0.
5. RDF Challenge prove is **LABEL only**. `usd_impulse` / `risk_on_off` may now be decided; that is not ENFORCE and not APPLY.

---

## 7. Tests that pin honesty

`tests/judgment/test_rates_dxy_funding.py`:

- Inventory names real paths; no invented endpoints. Multi FX/US30/EURGBP/GBPJPY landed; NAS100/UK100 still empty.
- Opt-out (`cross_books={}`): all four Noul values **null**; DXY rejected.
- Challenge as-of auto-load: `usd_impulse` + `risk_on_off` Challenge-true; `rates_impulse` / `funding_stress` **null**; DXY reject kept; compose **label**, never enforce/APPLY.
- Fixture USD impulse (EUR down + USDJPY up) → `usd_impulse.lab_target is True`, `challenge_true_target is None`.
- Fixture risk-off → `risk_on_off.lab_target is True`.
- Injected US10Y fixture can assemble `rates_impulse`; default path cannot.
- Injected TED fixture can assemble `funding_stress`; gold spread does not.
- Sane ICE-like DXY fixture is *usable*; clone file is not.
- Sierra ZN control books do not flip `rates_impulse`.
- Compose never resizes / never APPLY / never enforce.

---

## 8. What this PR is not

It is not a live wire. It is not a rates model. It is not a DXY nowcast. It is not a funding-AI narrative. It is the **typed impulse object + honest gap list** so Jev can ask hedge-fund questions without anyone inventing a missing world.
