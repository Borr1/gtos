# Lift Analysis — Expected R/Month Impact of Bucket Trimming

Dataset spans **24.6 months** (266 trades). 
All values are simulator-derived (q65_sim / F3 backtest / T7 live sim).

## Per-instrument 60-min bucket ranking by E[R] (worst → best)

### GBPJPY

| KZ | Bucket | n | WR | WR CI | E[R] | E[R] CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|
| london | 09:00-10:00 | 1 | 0.000 | [0.00, 0.00] | -1.000 | [-1.00, -1.00] | -1.00R | INSUFFICIENT |
| london | 08:00-09:00 | 2 | 0.000 | [0.00, 0.00] | -0.600 | [-1.00, -0.20] | -1.20R | INSUFFICIENT |
| ny | 14:00-15:00 | 6 | 0.500 | [0.17, 0.83] | -0.323 | [-0.80, +0.16] | -1.94R | INSUFFICIENT |
| tokyo | 00:00-01:00 | 3 | 0.333 | [0.00, 1.00] | -0.253 | [-1.00, +0.75] | -0.76R | INSUFFICIENT |
| london | 07:00-08:00 | 7 | 0.571 | [0.14, 0.86] | -0.210 | [-0.68, +0.32] | -1.47R | INSUFFICIENT |
| ny | 15:00-16:00 | 2 | 0.500 | [0.00, 1.00] | +0.135 | [+0.03, +0.24] | +0.27R | INSUFFICIENT |
| ny | 13:00-14:00 | 1 | 1.000 | [1.00, 1.00] | +0.200 | [+0.20, +0.20] | +0.20R | INSUFFICIENT |
| tokyo | 02:00-03:00 | 1 | 1.000 | [1.00, 1.00] | +2.120 | [+2.12, +2.12] | +2.12R | INSUFFICIENT |

### GBPUSD

| KZ | Bucket | n | WR | WR CI | E[R] | E[R] CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|
| ny | 14:00-15:00 | 5 | 0.600 | [0.20, 1.00] | +0.098 | [-0.77, +0.99] | +0.49R | INSUFFICIENT |
| london | 09:00-10:00 | 2 | 0.500 | [0.00, 1.00] | +0.215 | [-0.04, +0.47] | +0.43R | INSUFFICIENT |
| london | 07:00-08:00 | 2 | 0.500 | [0.00, 1.00] | +0.365 | [-1.00, +1.73] | +0.73R | INSUFFICIENT |
| london | 08:00-09:00 | 2 | 0.500 | [0.00, 1.00] | +0.820 | [-1.00, +2.64] | +1.64R | INSUFFICIENT |
| ny | 15:00-16:00 | 1 | 1.000 | [1.00, 1.00] | +0.980 | [+0.98, +0.98] | +0.98R | INSUFFICIENT |
| ny | 13:00-14:00 | 3 | 1.000 | [1.00, 1.00] | +1.170 | [+0.17, +2.47] | +3.51R | INSUFFICIENT |

### US30_cash

| KZ | Bucket | n | WR | WR CI | E[R] | E[R] CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|
| ny | 13:00-14:00 | 4 | 0.500 | [0.00, 1.00] | +0.133 | [-0.66, +0.88] | +0.53R | INSUFFICIENT |
| london | 08:00-09:00 | 4 | 0.500 | [0.00, 1.00] | +0.333 | [-1.00, +1.69] | +1.33R | INSUFFICIENT |
| london | 09:00-10:00 | 7 | 0.714 | [0.29, 1.00] | +0.367 | [-0.25, +0.96] | +2.57R | INSUFFICIENT |
| ny | 14:00-15:00 | 17 | 0.529 | [0.29, 0.76] | +0.462 | [-0.10, +1.07] | +7.85R | INSUFFICIENT |
| ny | 15:00-16:00 | 1 | 1.000 | [1.00, 1.00] | +0.520 | [+0.52, +0.52] | +0.52R | INSUFFICIENT |

### USDJPY

| KZ | Bucket | n | WR | WR CI | E[R] | E[R] CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|
| london | 08:00-09:00 | 4 | 0.250 | [0.00, 0.75] | -0.273 | [-1.00, +1.18] | -1.09R | INSUFFICIENT |
| tokyo | 01:00-02:00 | 3 | 0.667 | [0.00, 1.00] | +0.167 | [-1.00, +0.75] | +0.50R | INSUFFICIENT |
| ny | 15:00-16:00 | 2 | 0.500 | [0.00, 1.00] | +0.250 | [-1.00, +1.50] | +0.50R | INSUFFICIENT |
| tokyo | 00:00-01:00 | 8 | 0.500 | [0.12, 0.88] | +0.250 | [-0.69, +1.19] | +2.00R | INSUFFICIENT |
| ny | 13:00-14:00 | 14 | 0.714 | [0.43, 0.93] | +0.301 | [-0.15, +0.74] | +4.21R | INSUFFICIENT |
| london | 07:00-08:00 | 12 | 0.750 | [0.50, 1.00] | +0.536 | [-0.09, +1.18] | +6.43R | INSUFFICIENT |
| ny | 14:00-15:00 | 3 | 1.000 | [1.00, 1.00] | +0.683 | [+0.22, +1.50] | +2.05R | INSUFFICIENT |
| london | 09:00-10:00 | 2 | 1.000 | [1.00, 1.00] | +1.295 | [+1.09, +1.50] | +2.59R | INSUFFICIENT |

### XAUUSD

| KZ | Bucket | n | WR | WR CI | E[R] | E[R] CI | Total R | Rec |
|---|---|---|---|---|---|---|---|---|
| ny | 13:00-14:00 | 29 | 0.483 | [0.31, 0.66] | -0.088 | [-0.38, +0.21] | -2.55R | OBSERVE |
| ny | 15:00-16:00 | 21 | 0.524 | [0.33, 0.71] | +0.121 | [-0.36, +0.67] | +2.54R | OBSERVE |
| london | 07:00-08:00 | 26 | 0.654 | [0.46, 0.85] | +0.160 | [-0.17, +0.49] | +4.15R | OBSERVE |
| london | 08:00-09:00 | 31 | 0.677 | [0.52, 0.84] | +0.274 | [-0.09, +0.67] | +8.50R | OBSERVE |
| ny | 14:00-15:00 | 22 | 0.636 | [0.41, 0.82] | +0.421 | [-0.03, +0.91] | +9.27R | OBSERVE |
| london | 09:00-10:00 | 11 | 0.727 | [0.45, 1.00] | +0.654 | [-0.16, +1.48] | +7.20R | INSUFFICIENT |
| ny | 16:00-17:00 | 3 | 0.667 | [0.00, 1.00] | +1.353 | [-1.00, +3.56] | +4.06R | INSUFFICIENT |
| london | 10:00-11:00 | 1 | 1.000 | [1.00, 1.00] | +1.500 | [+1.50, +1.50] | +1.50R | INSUFFICIENT |

## XAUUSD: hypothetical trimming of worst buckets (n>=20 only)

*Caveat: the only XAUUSD bucket with negative E[R] and n>=20 is NY 13:00 (n=29, E[R]=-0.088R, WR 48.3%). Its WR upper-CI (65.5%) is well above breakeven (35.7%), so it does NOT pass the SKIP rule. This section is descriptive only.*

All XAUUSD n>=20 buckets: N=129, total R delivered=+21.91R over 24.6 months = **+0.89R/month**

| Dropped buckets | Cumulative freq lost | Cumulative R avoided | New E[R]/month (after drop) | Pct N lost |
|---|---|---|---|---|
| none | 0 trades (0.0%) | +0.00R | +0.892R/mo | 0.0% |
| ny 13:00 | 29 trades (22.5%) | +2.55R | +0.996R/mo | 22.5% |
| ny 13:00, ny 15:00 | 50 trades (38.8%) | +0.01R | +0.892R/mo | 38.8% |
| ny 13:00, ny 15:00, london 07:00 | 76 trades (58.9%) | -4.14R | +0.723R/mo | 58.9% |
| ny 13:00, ny 15:00, london 07:00, london 08:00 | 107 trades (82.9%) | -12.64R | +0.377R/mo | 82.9% |
| ny 13:00, ny 15:00, london 07:00, london 08:00, ny 14:00 | 129 trades (100.0%) | -21.91R | +0.000R/mo | 100.0% |

## High-quality-frequency ranking (freq x mean R) — all buckets

Ranked descending by total R delivered (n * E[R]). Useful for spotting where the edge actually lives empirically.

| Symbol | KZ | Bucket | n | WR | E[R] | Total R | Rec |
|---|---|---|---|---|---|---|---|
| XAUUSD | ny | 14:00-15:00 | 22 | 0.636 | +0.421 | +9.27R | OBSERVE |
| XAUUSD | london | 08:00-09:00 | 31 | 0.677 | +0.274 | +8.50R | OBSERVE |
| US30_cash | ny | 14:00-15:00 | 17 | 0.529 | +0.462 | +7.85R | INSUFFICIENT |
| XAUUSD | london | 09:00-10:00 | 11 | 0.727 | +0.654 | +7.20R | INSUFFICIENT |
| USDJPY | london | 07:00-08:00 | 12 | 0.750 | +0.536 | +6.43R | INSUFFICIENT |
| USDJPY | ny | 13:00-14:00 | 14 | 0.714 | +0.301 | +4.21R | INSUFFICIENT |
| XAUUSD | london | 07:00-08:00 | 26 | 0.654 | +0.160 | +4.15R | OBSERVE |
| XAUUSD | ny | 16:00-17:00 | 3 | 0.667 | +1.353 | +4.06R | INSUFFICIENT |
| GBPUSD | ny | 13:00-14:00 | 3 | 1.000 | +1.170 | +3.51R | INSUFFICIENT |
| USDJPY | london | 09:00-10:00 | 2 | 1.000 | +1.295 | +2.59R | INSUFFICIENT |
| US30_cash | london | 09:00-10:00 | 7 | 0.714 | +0.367 | +2.57R | INSUFFICIENT |
| XAUUSD | ny | 15:00-16:00 | 21 | 0.524 | +0.121 | +2.54R | OBSERVE |
| GBPJPY | tokyo | 02:00-03:00 | 1 | 1.000 | +2.120 | +2.12R | INSUFFICIENT |
| USDJPY | ny | 14:00-15:00 | 3 | 1.000 | +0.683 | +2.05R | INSUFFICIENT |
| USDJPY | tokyo | 00:00-01:00 | 8 | 0.500 | +0.250 | +2.00R | INSUFFICIENT |
| GBPUSD | london | 08:00-09:00 | 2 | 0.500 | +0.820 | +1.64R | INSUFFICIENT |
| XAUUSD | london | 10:00-11:00 | 1 | 1.000 | +1.500 | +1.50R | INSUFFICIENT |
| US30_cash | london | 08:00-09:00 | 4 | 0.500 | +0.333 | +1.33R | INSUFFICIENT |
| GBPUSD | ny | 15:00-16:00 | 1 | 1.000 | +0.980 | +0.98R | INSUFFICIENT |
| GBPUSD | london | 07:00-08:00 | 2 | 0.500 | +0.365 | +0.73R | INSUFFICIENT |
| US30_cash | ny | 13:00-14:00 | 4 | 0.500 | +0.133 | +0.53R | INSUFFICIENT |
| US30_cash | ny | 15:00-16:00 | 1 | 1.000 | +0.520 | +0.52R | INSUFFICIENT |
| USDJPY | tokyo | 01:00-02:00 | 3 | 0.667 | +0.167 | +0.50R | INSUFFICIENT |
| USDJPY | ny | 15:00-16:00 | 2 | 0.500 | +0.250 | +0.50R | INSUFFICIENT |
| GBPUSD | ny | 14:00-15:00 | 5 | 0.600 | +0.098 | +0.49R | INSUFFICIENT |
