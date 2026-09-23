# Market Expansion Swap-Adjusted Activation Rescore

Decision: `MARKET_EXPANSION_SWAP_ADJUSTED_RESCORING_POSITIVE_DEFAULT_OFF_NOT_LIVE_AUTHORITY`

Runtime effect: `none_swap_adjusted_rescore_only`

## Result

- Candidate reference monthly: `4.969`.
- Before-swap seed monthly: `5.003`.
- After-swap seed monthly: `4.991`.
- After-swap seed delta vs candidate monthly: `0.022`.
- Swap drag versus prior seed monthly: `-0.012`.

Market expansion remains a default-off candidate family. The swap-adjusted
overlay is still positive at seed and ceiling weights, but the incremental lift
is small; promotion remains blocked by live-authority/session/fill/VPS parity.
