# NQM26 Sierra Delayed Capture Notes

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Operator Setup

- Sierra package: Service Package 12, per owner confirmation.
- Sierra feed: `SC Data` delayed.
- Symbol pattern configured: `NQ?##-CME`.
- Active chart symbol: `NQM26-CME[M]`.
- Chart timeframe: `1 Min`.
- Market Depth Historical Graph: added to chart per owner screenshot.
- `Record Market Depth Data`: enabled for `NQ?##-CME`.
- Sierra data folder observed: `C:\SierraChart\Data\`.
- Sierra market-depth folder observed: `C:\SierraChart\Data\MarketDepthData\`.

## Files Observed

Copied into repo:

- `research/sierrachart_data_source_research_2026-05-02/samples/NQM26-CME.2026-05-02_delayed.depth`
- `research/sierrachart_data_source_research_2026-05-02/samples/NQM26-CME.2026-05-01_delayed.depth`

Observed but not copied:

- `C:\SierraChart\Data\NQM26-CME.scid`
- File size observed: `675077736` bytes.
- Reason not copied: large intraday file; not needed for the first `.depth` header/parser proof.

## Interpretation

This is enough for a first Sierra `.depth` parser proof.

It is not enough for market/orderflow conclusions because the capture occurred on Saturday, 2026-05-02, when CME futures were not in a normal active session. The next required sample is a longer active-session capture.
