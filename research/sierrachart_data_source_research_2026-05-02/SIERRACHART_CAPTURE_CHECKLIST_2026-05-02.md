# Sierra Chart Capture Checklist For GTOS Orderflow Research

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Objective

Produce the first real Sierra Chart evidence files needed to validate whether Sierra can replace or supplement Databento for ongoing depth-level orderflow capture.

The first target is not a live signal. The first target is a parser/parity proof.

## Minimum Setup

Preferred package:

- Sierra Chart Service Package 12 if MBO DOM/queue display is part of the test.
- Package 11 may be enough for depth files and advanced studies, but Package 12 removes the MBO ambiguity.

Feed:

- Start with Delayed Exchange Data Feed.
- Do not activate real-time Denali market-depth exchange fees until delayed capture proves useful.

## Symbols To Capture

First wave:

| GTOS symbol | Sierra/futures target | Reason |
|---|---|---|
| NAS100 | `NQ` or `MNQ` | Existing Databento MBO/MBP diagnostics; best parity target. |
| XAUUSD | `GC` or `MGC` | Gold orderflow path; high GTOS relevance. |
| XAGUSD | `SI` | Silver orderflow path. |
| US30 | `YM` or `MYM` | US30 proxy; currently sparse in Databento diagnostics. |
| GBPUSD | `6B` | FX futures proxy. |
| USDJPY | `6J` | Inverse FX futures proxy. |
| equity control | `ES` or `MES` | Optional control for broad US index depth. |

GBPJPY is not first-wave because it has no clean single futures proxy.

## Sierra Settings To Verify

Use the official Sierra docs as the operating source:

- Delayed feed symbols are opened through `File >> Find Symbol`.
- Market Depth Historical Graph works with delayed data.
- Set `Global Settings >> Sierra Chart Server Settings >> General >> Max Depth Levels` to `0` to receive all available market depth levels.
- For Market by Order, set:
  - `Subscribe Market by Order Data When Market Depth Subscribed = Yes`
  - `Use Separate Connection for Market by Order Data = Yes`
- For Market Depth Historical Graph:
  - enable `Record Market Depth Data` for the symbol or symbol pattern,
  - open an Intraday chart,
  - add `Market Depth Historical Graph`.

## Files Needed From Sierra

For each first-wave symbol, collect:

- one `.depth` file from `Data/MarketDepthData`,
- one intraday `.scid` file or one exported intraday CSV,
- a screenshot or note confirming Market Depth Historical Graph is nonblank,
- if Package 12 is active, a screenshot or note confirming MBO columns are available.

Preferred first sample:

- `NQ` / `MNQ`
- active US session
- at least `30` minutes of capture
- include a period with visible depth changes

## File Naming For GTOS Intake

Place owner-provided files under a new local folder:

`research/sierrachart_data_source_research_2026-05-02/samples/`

Suggested names:

- `NQ_YYYYMMDD.depth`
- `NQ_YYYYMMDD_intraday.csv`
- `NQ_YYYYMMDD_capture_notes.md`

Do not overwrite samples. Add a suffix if repeated:

- `_run1`
- `_run2`
- `_delayed`
- `_denali`

## Acceptance For First Sierra Proof

The first proof is complete when:

- at least one real `.depth` file exists,
- parser can read the header and records,
- UTC timestamps align with Sierra display,
- a reconstructed book exists,
- top-N depth features can be produced,
- one Databento-overlapping window can be compared,
- report says `NO_PROMOTION_VERDICT`.

## What Is Needed From Owner

Only these are externally blocked:

1. Confirm whether Sierra Chart is already installed and whether there is any active package.
2. If not installed/active, decide whether to activate/evaluate Package 12.
3. Provide one real `.depth` sample after enabling depth recording, or allow a future session on the machine where Sierra is installed.
4. Confirm whether there is a supported live funded futures account for nonprofessional Denali fees. This is not needed for delayed proof.

Everything else can remain research/tooling inside this repo.
