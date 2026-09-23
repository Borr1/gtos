# GL-4 — Index/Oil Live Spread Floors (FTMO)

Date: 2026-06-15 ~02:35 UTC (Monday, indices/oil quoting live)
Earlier GL-4 covered core 24/5 (FX/metals/crypto/energy/agri). The 5 index symbols were skipped as
out-of-session; this records them with live quotes. Read-only, FTMO broker names, NO orders.
Geometry: idxrev stop = 1.5·ATR(H4); oil ~1·ATR(H4). Wall = 0.20R.

```
canon       native       spread_px   bps      ATR_H4    spr/ATR  spr/stop  verdict
SPX500      US500.cash       0.550   0.73     54.879    0.0100   0.0067    OK (<0.20R)
UK100       UK100.cash       3.350   3.18     67.803    0.0494   0.0329    OK (<0.20R)
JP225       JP225.cash      10.000   1.44   1026.844    0.0097   0.0065    OK (<0.20R)
GER40       GER40.cash       3.330   1.33    203.329    0.0164   0.0109    OK (<0.20R)
US30_cash   US30.cash        2.380   0.46    310.012    0.0077   0.0051    OK (<0.20R)
USOIL_cash  USOIL.cash       0.068   8.47      2.373    0.0287   0.0287    OK (<0.20R)
UKOIL_cash  UKOIL.cash       0.060   7.13      2.127    0.0282   0.0282    OK (<0.20R)
```

Worst spread/stop across index+oil: **0.0329R** (UK100), all others < 0.03R. **VERDICT: ALL UNDER WALL.**

Note: oil shows higher raw bps (7-8) but in stop-R terms (the dimension the cost gate cares about) it
is negligible because oil ATR dwarfs the spread. The broker_net_cost_engine remains the binding cost
safety at order time; this is the pre-screen and it is comfortably clear for all index/oil book symbols.

Tool: `.tools/measure_index_spread_floors.py`. Combined with the earlier core measurement, GL-4 is
covered for all 13 built-sleeve book symbols on FTMO.
