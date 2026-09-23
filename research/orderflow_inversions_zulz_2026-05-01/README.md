# Zulz Trades — Orderflow Inversions Research Pack

**Compiled:** 2026-05-01
**Purpose:** Hand-off bundle for an AI to evaluate the "Orderflow Inversions Model" sold by Zulz Trades on Whop, against the GTOS edge framework.
**Source person:** Zulz Trades (handle `@zulztrades`, Miami US, Whop creator since ~2026-03-15)
**Reach:** Whop community 206 members; YouTube channel 29 shorts; TikTok 973 followers / 28.7K likes; Discord 189 members
**Selling proposition:** "The simplest and most permanent trading model — Orderflow Inversions"

---

## Folder map

| Path | Contents |
|---|---|
| `README.md` | This file. Top-level summary + canonical model spec. |
| `product_descriptions/` | One markdown file per Whop product. 10 products + Discord. Full descriptions verbatim. |
| `transcripts/` | One markdown file per video. 30 transcripts. Filename = video ID. |
| `images/` | 67 product images downloaded from Whop CDN (highest available resolution). |
| `MODEL_SPEC.md` | Canonical reconstruction of the Orderflow Inversion setup from his words. |
| `KEY_QUOTES.md` | Pulled verbatim quotes per concept (entry trigger, invalidation, etc.). |
| `CONSTRAINTS.md` | What I could not get and why. |

---

## Quick-look: what he sells

| Product | Symbol | Price | Type |
|---|---|---|---|
| Full NQ Orderflow: Sierrachart | NQ (Nasdaq fut) | $46 (was $57.50) | Full chartbook |
| Full ES Orderflow: Sierrachart | ES (S&P fut) | $46 | Full chartbook |
| Full GC Orderflow: Sierrachart | GC (Gold fut) | $46 | Full chartbook |
| NQ & ES Orderflow: Sierrachart | NQ + ES | $73 | Combo |
| Footprint NQ: Zulz Sierrachart | NQ | $25 (was $31.25) | Footprint-only |
| Footprint ES: Zulz Sierrachart | ES | $25 | Footprint-only |
| Footprint GC: Zulz Sierrachart | GC | $25 | Footprint-only |
| VP and Heatmap NQ: Sierrachart | NQ | $33 | VP+heatmap-only |
| VP and Heatmap ES: Sierrachart | ES | $33 | VP+heatmap-only |
| VP and Heatmap GC: Sierrachart | GC | $33 | VP+heatmap-only |
| Zulz Premium Discord | — | $75/mo (was $93.75; free w/ code `ZULZ`) | Live trading + setup library |

**What you actually get:** SierraChart `.cht`/`.scbookx` template files (chartbooks), not a strategy course. The model knowledge is delivered separately through:
1. The Discord (live trade calls + recap library)
2. His TikTok/YouTube content (shorts only — no long-form course videos exist on his public channels)

**Hard requirement:** SierraChart subscription + CME Group Market Depth Data Feed. He gates against Bookmap by replicating the heatmap inside SierraChart. Says "no third-party purchases needed."

---

## The model in one paragraph (his words, condensed)

Mark a **low-volume node** (LVN) inside an ICT-style fair value gap or significant level (his preferred POI is the LVN, NOT the FVG itself — "ICT traders mark a fair value gap, but order flow traders mark a low volume node"). Wait for price to deliver to that LVN at the **first VWAP standard-deviation reclaim** of the session (ETH or RTH split). On the footprint, watch for **trapped participants** at the level (large-volume bubbles getting absorbed) followed by **aggressive participants pushing the other way** (delta shift). That delta shift is the entry trigger. Targets are the next significant resting-liquidity level visible on the in-chart heatmap. This setup works the same on NQ/ES/GC/CL/YM and overnight Asia / RTH.

Full canonical reconstruction in `MODEL_SPEC.md`.

---

## Repeated phrases (his vocabulary — useful as features)

These appear across 10+ videos:
- **"Orderflow inversion"** — the setup name
- **"Low volume node"** (LVN) — his preferred POI; explicitly contrasted with FVG
- **"First VWAP deviation"** / **"first view of deviation"** — entry timing trigger (auto-transcribed as "view")
- **"Trapped buyers / trapped sellers"** — failed aggression at the level
- **"Aggressive buyers / aggressive sellers"** — opposite-side initiative once trap confirmed
- **"Delta shift"** — moment trapped → aggressive flips
- **"Absorption"** — buyers/sellers that can't move price = getting absorbed
- **"Large volume trade indicator"** — auto-sized bubbles on his footprint
- **"Stacked imbalances"** — auto-marked on his footprint
- **"Heatmap"** / **"resting liquidity"** — used for targets, not entries
- **"A+ setup"** — only-take rule
- **"Delivery"** (ICT vocabulary) — "price delivered to the LVN"
- **"Tick-by-tick"** — why SierraChart > TradingView
- **"Vol X Delta footprint"** — his specific footprint variant
- **"2000 trade candles"** — his footprint chart prints by trade count, not time

---

## Trading style observations

- **Instruments traded live:** NQ, ES, GC, CL (crude), YM, with most recap clips on ES, GC, CL.
- **Sessions:** Asia (overnight), London/NY open. Goes live on Discord daily 9:30am EST.
- **Timeframes:** Execution on the Vol X Delta footprint (2000-trade candles); context on 5m/15m time charts; HTF VP overlay.
- **Risk targets:** Recap clips reference 1R / 1.4R / 2.4R / 3.5R targets. Conservative on news days (1R caps).
- **News behavior:** Reduces size on FOMC/CPI/Trump-tweet days; mentions inverse correlation between CL and ES, DXY and ES as required confluence.
- **Win rate claim (anecdotal, one video):** "3 wins, 1 loss, 1 BE" first week trading 5 contracts (not statistically meaningful).
- **Personality flags:** Heavy "I have the best model in the space" marketing language. Anti-Bookmap, anti-TradingView, anti-aggregated-volume. Heavy psychology content suggests he's also selling the "trader-mindset" angle alongside the technical model.

---

## What this is NOT

- Not a published strategy with a backtest report.
- Not a long-form course (no 1+ hour explanation video exists on his public channels).
- Not original — concepts (LVN, footprint absorption, delta shift, VWAP-deviation reclaim) are standard SMC + auction-theory primitives. The novelty is the **packaging**: bundling LVN-as-POI + VWAP-dev-reclaim + footprint-trap-shift into a single named setup with a pre-built SierraChart template.
- Not futures-equivalent to your CFD/forex stack. He explicitly trades centralized CME futures (NQ/ES/GC/CL/YM). Translation to MT5 XAUUSD / NAS100 / US30 / FX requires care because the volume/heatmap signal is broker-local on MT5.

---

## How to use this pack with your AI

1. Have it read `MODEL_SPEC.md` first (canonical reconstruction).
2. Then `KEY_QUOTES.md` (verbatim evidence).
3. Then skim `transcripts/` directory for any topic the AI wants to dive deeper on.
4. Cross-reference against `images/01_full_*` and `images/04_footprint_*` for visual examples of the setup he advertises.
5. The 10 product descriptions in `product_descriptions/` confirm which features ship in each chartbook (useful when the AI asks "is the heatmap in the same chart as the footprint, or a separate window?" — answer: same chart for the Full bundle, different chart for the Footprint-only bundle).
