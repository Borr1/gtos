# Wave3 Execution Lifecycle Prompt Requirements

Status: requirements only; Wave3 prompt pack remains blocked.

- Require broker-ticket-bound entry/order/deal/position lifecycle capture.
- Require every SLTP modify, partial close, BE, trailing, timeout, manual/emergency close, and terminal broker result.
- Require M1/tick first-passage fields for time to green, +0.25R, +0.5R, +1R, partial, BE, MFE, reversal, target, stop, and stale timeout.
- Require broker-net cost/swap/slippage fields and no favorable inference from missing lifecycle truth.
