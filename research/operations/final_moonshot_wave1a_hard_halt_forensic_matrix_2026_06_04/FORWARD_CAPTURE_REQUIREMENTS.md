# Wave 1A Forward Capture Requirements

Source-gap rows requiring exact capture or source repair: `27`.

Required forward fields for every live candidate/trade:

- broker position id, order ticket, entry deal ticket, close deal ticket, and source namespace;
- selected-cell row id, selected-cell expectancy, PF, win rate, denominator, and cost-stress status;
- source-window hash, M15/M1/tick path source status, corrupt-gap status, and first-touch ordering;
- execution cash-risk amount, lot sizing diagnostics, broker-native commission/swap/slippage estimate before entry;
- realized broker cash, commission, swap, gross profit, net profit, actual-R, MFE, MAE, hold time, and giveback;
- cluster/exposure snapshot before admission, including correlated open risk and same-symbol lifecycle state;
- halt/scheduler/process/autostart state whenever emergency close or flattening runs.

Historical fields not logged in the hard-halt window are non-generatable historical truth. They must be closed prospectively by the capture contract rather than inferred from price movement.
