# LMAX Market Data Fees Addendum

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Evidence Files

User-supplied LMAX Exchange fee PDF:

- Source path: `C:\Users\MSI\Downloads\LMAXExchange-Market-Data-Fees.pdf`
- Local copy: `research/primitive_orderflow_sources_2026-05-02/raw/lmax_market_data_fees_user_supplied_2026-05-02.pdf`
- Extracted text: `research/primitive_orderflow_sources_2026-05-02/raw/lmax_market_data_fees_user_supplied_2026-05-02.txt`
- SHA256: `26D912252EF7A4FB3C1F0CB2A07477F6BD985DDAB8903C521FA0C57C409F24DD`
- PDF pages: `1`
- Title: `LMAX Exchange market data`
- Effective date stated in PDF: `01 JUNE 2026`

Previously fetched LMAX Global fee PDF:

- Local file: `research/primitive_orderflow_sources_2026-05-02/raw/lmax_market_data_fees_pdf.pdf`
- Extracted text: `research/primitive_orderflow_sources_2026-05-02/raw/lmax_market_data_fees_pdf.txt`
- SHA256: `56C146515493FF05CF15016FBEAA1A17A4BCD2522B884103D2D8B13D4239421B`
- PDF pages: `1`
- Title: `LMAX Global market data`
- Effective date stated in PDF: `01 MAY 2026`

These appear to be different LMAX Group market-data schedules. They should not be conflated.

## LMAX Exchange Fees

The user-supplied LMAX Exchange PDF is the most relevant source for exchange/MTF-style primitive venue data.

FIX connection fees:

| Venue | Fee |
|---|---:|
| `LD4 / NY4 / TY3` | `$500` per venue |
| `SG1` | Free of charge |

FIX market data, FX only:

| Depth | Standard fee | Trading client discount | Volume discount |
|---|---:|---:|---|
| TOB | `$1,200` | Free | n/a |
| 3 levels | `$2,600` | `$1,300` | 50% if total notional `>=4b` |
| 5 levels | `$6,000` | `$3,000` | 50% if total notional `>=7b` |
| 10 levels | `$13,500` | `$6,750` | 50% if total notional `>=10b` |
| Delayed trade feed | `$1,500` | Free | n/a |

FIX market data, metals only:

| Depth | Standard fee | Trading client discount | Volume discount |
|---|---:|---:|---|
| TOB | `$500` | Free | n/a |
| 3 levels | `$1,200` | `$600` | 50% if total notional `>=4b` |
| 5 levels | `$2,400` | `$1,200` | 50% if total notional `>=7b` |
| 10 levels | `$5,500` | `$2,750` | 50% if total notional `>=10b` |
| Delayed trade feed | `$1,100` | Free | n/a |

FIX market data, combined FX and metals:

| Depth | Standard fee | Trading client discount | Volume discount |
|---|---:|---:|---|
| TOB | `$1,500` | Free | n/a |
| 3 levels | `$3,000` | `$1,500` | 50% if total notional `>=4b` |
| 5 levels | `$6,500` | `$3,250` | 50% if total notional `>=7b` |
| 10 levels | `$15,000` | `$7,500` | 50% if total notional `>=10b` |
| Delayed trade feed | `$1,500` | Free | n/a |

Eligibility and throttling notes from the PDF:

- Non-trading clients, and trading clients who do not meet monthly eligibility criteria, receive FIX market data throttled to `10` updates per second.
- Trading-client monthly eligibility is `$250 million` minimum traded volume per month, per tier, per venue.
- Access to `5` and `10` levels requires `$5 billion` minimum traded volume per month.
- Eligible trading clients can receive unthrottled FIX market data up to `1ms` updates.
- Volume discounts are applicable to trading clients meeting monthly trading-volume thresholds in any LMAX Exchange venue.

ITCH market data access:

| Venue | Fee | Volume discount |
|---|---:|---|
| `LD4` | `$80,000` | Reduced to `$25,000` if total global volumes exceed `$25bn` and a minimum aggressive/passive ratio of `30%` is reached |

## LMAX Global Fees

The previously fetched LMAX Global PDF is lower-cost, but it appears to be a different product lane from LMAX Exchange. It may still be useful, but its venue/source identity needs separate verification before treating it as the same primitive Exchange feed.

Connection fees:

| Item | Fee |
|---|---:|
| Standard connection fee per venue | `$300` |
| Enhanced FIX fee | See enhanced solutions |

Monthly pricing matrix, all charges commission deductible:

| Levels | 1 update/sec | 10 updates/sec | 50 updates/sec | 100 updates/sec | 1,000 updates/sec |
|---|---:|---:|---:|---:|---:|
| TOB | Free | `$4,000` | `$4,500` | `$5,500` | `$8,500` |
| 2-5 levels | `$2,000` | `$5,000` | `$6,000` | `$8,000` | `$12,000` |
| 5+ / 10 levels | `$3,500` | `$6,000` | `$7,500` | `$10,000` | `$15,000` |

Other stated charges:

| Item | Fee |
|---|---:|
| Weekend FX and/or crypto CFDs | `$1,000` per month |
| White label GUI setup | `$5,000` |
| White label GUI ongoing | `$2,500` minimum monthly commission applicable |

The LMAX Global PDF also states: trade `>$5M` per month on any asset class to waive the fee, paying the connection fee only.

## GTOS Interpretation

LMAX remains a real venue-native source candidate, but the fee schedule changes the practical conclusion:

- LMAX Exchange ITCH full-depth access is not a cheap research feed. At `$80,000/mo`, or `$25,000/mo` only after very large volume conditions, it is outside the current GTOS research budget.
- LMAX Exchange FIX depth is cheaper than ITCH but still expensive for full 10-level combined FX/metals depth at `$15,000/mo` standard, before connection fees.
- Low-depth or delayed LMAX Exchange data may be cheaper, but the default non-eligible feed is throttled to `10` updates/sec, which weakens any "before MT5 broker" lead-lag thesis.
- LMAX Global has a lower-cost matrix and a possible commission-waiver path, but it must be verified as a source/provenance match before using it as a primitive FX orderflow substitute.

Current decision: LMAX should remain a monitored non-CME venue candidate, not the immediate data source for GTOS. Databento plus Sierra remains the practical near-source stack for current futures proxy research.

Open items:

1. Confirm whether LMAX Global data and LMAX Exchange data expose the same venue book, different books, or different client/product lanes.
2. Confirm whether a non-trading research client can obtain LMAX Global full-book historical data/API access without execution/account commitments.
3. Confirm whether LMAX Exchange delayed trade feed includes enough orderflow/depth information for GTOS, or only trades.
4. Confirm licensing, redistribution, storage, and historical backfill rights before planning any extractor.
