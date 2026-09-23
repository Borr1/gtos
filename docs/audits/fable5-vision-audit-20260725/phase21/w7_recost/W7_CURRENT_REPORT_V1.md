# Wave 21 — exact-current W7 truth receipt

**Headline status: `W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP`.** The W7 profitability headline is
`NOT_EVALUABLE`. Ten supported source cells are absent and the historical rows do not
contain the state needed to traverse W7's native admission, risk, router, and broker
lifecycle. Exact partial measurements from loaded cells remain below as diagnostics only;
they are not a survivor-book result, profitability claim, or promotion input.

The quote/lifecycle class is `MODELLED`, never `COMPLETE` or `MEASURED`: the walker uses
H4 BID OHLC, an era/hour scalar spread at entry, and a conservative open-through gap rule.
There are no historical ASK quotes/ticks or resting-order lifecycle observations.

## Native W7 graph boundary

| Stage | Status | What this lane did |
|---|---|---|
| production sleeve Generator | `RECOMPUTED_DIRECT_GENERATOR_ON_OBSERVED_ROWS_RUNTIME_SLOT_CONSERVATION_NOT_EVALUABLE` | Calls the imported W7 crypto, energy/agri, and substrate production generators on observed hash-bound, broker-clock-corrected H4 rows; missing-cell and schedule-unbound full-window occurrence counts remain unknown. This does not call BookEngine's wrapper, whose insufficient-bar, stale/chronology, and generator-exception paths silently continue without one typed terminal row per decision ordinal. |
| admission.admit_and_size | `NOT_EVALUABLE_HISTORICAL_STATE_MISSING` | Historical GovernorState, open risk, running conviction, occupancy, learning/stress state, and same-cycle competing intents are absent. The broad stack's 2.0% request -> 1.5% partial allocation does not transfer: native _enforce_gross_open_risk_cap is first-fit-descending and sheds/refuses a unit that does not fit remaining same-tick headroom. |
| BookOwner router/risk/trade parameters | `NOT_EVALUABLE_HISTORICAL_STATE_MISSING` | Historical sized units, account headroom, fresh quote geometry, ledger occupancy, and same-symbol/cluster lifecycle state are absent. |
| broker order/fill/exit lifecycle | `MODELLED_H4_BID_SCALAR_SPREAD` | Research walker uses H4 BID OHLC, scalar entry spread, and conservative open-through stops; no ASK/tick/resting-order/fill authority exists. |
| component per-unit-R costs | `RECOMPUTED_LOADED_CELLS_DIAGNOSTIC_ONLY` | Production cost_r recomputes commission, swap, spread, and slippage on the modelled walker rows; lot/account translation remains unavailable. |

`execution_packets.py`'s `gtos_vnext_selector_v4_*` and
`gtos_vnext_scheduler_v4_*` fields are compatibility shims emitted after native W7
admission. They are not Selector V4 or Scheduler V4 decisions and are not counted here.

The direct generator loop is also not a terminally conserved BookEngine replay. The
native wrapper silently continues on insufficient bars, stale/chronology exceptions, and
generator exceptions. Without one typed terminal per active-spec × symbol × decision
ordinal, the native occurrence denominator remains `NOT_EVALUABLE`.

Broad-stack partial headroom does not transfer. Native W7 sizes in descending conviction
and uses first-fit against remaining gross-risk headroom; a unit that does not fit is
shed/refused rather than proportionally reduced.

## Local versus latest durable host runtime surface

| Account | Local include_clean3 | Local effective declared tags | Local frontier | Latest host include_clean3 | Latest host effective declared tags | Latest host frontier | Status |
|---|---:|---|---|---:|---|---|---|
| FTMO | False | crypto,energy_agri | none | True | crypto,energy_agri,sub_mid_dn_revert,sub_xvol_pullback | crypto | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` |
| redacted_account | False | crypto,energy_agri | none | True | crypto,energy_agri,sub_mid_dn_revert,sub_xvol_pullback | none | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` |

The host columns are the upstream read-only Wave-21 live-audit observation supplied to
this scoped lane; its durable integration receipt is not local to this branch. The
mismatch is therefore disclosed, never used to claim local or live parity. In particular,
FTMO `crypto` rows use the local empty frontier and are not the observed host exit contract.

## Supported source gaps that block the headline

| Account | Sleeve | Symbol | Source status | Candidate count | Exact requirement |
|---|---|---|---|---:|---|
| FTMO | sub_mid_dn_revert | CORN_c | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/CORN_c covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| FTMO | sub_mid_dn_revert | COTTON_c | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/COTTON_c covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| FTMO | sub_xvol_pullback | CORN_c | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/CORN_c covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| FTMO | sub_xvol_pullback | COTTON_c | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/COTTON_c covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| FTMO | sub_xvol_pullback | EU50_cash | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/EU50_cash covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| FTMO | sub_xvol_pullback | FRA40_cash | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/FRA40_cash covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| FTMO | sub_xvol_pullback | US2000_cash | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for FTMO-Server3/US2000_cash covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| redacted_account | sub_xvol_pullback | EU50_cash | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for redacted_account-Server 2/EU50_cash covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| redacted_account | sub_xvol_pullback | FRA40_cash | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for redacted_account-Server 2/FRA40_cash covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |
| redacted_account | sub_xvol_pullback | US2000_cash | `MISSING_SOURCE` | unknown, not zero | Acquire broker-clock H4 OHLCV for redacted_account-Server 2/US2000_cash covering at least 259 closed bars before 2015-02-25 through 80 H4 bars after 2026-06-12, with a .timebase.json sidecar and manifest SHA-256; or commit an explicit named peer-transfer authority. |

Every requested account/sleeve/symbol cell—including loaded observed rows with no
emission, missing source, and outside-profile cells—is in
`W7_CURRENT_SOURCE_CELLS_V1.jsonl`. The nominal window is
4126 inclusive calendar days (2015-02-25 through
2026-06-12), but it is **not** claimed as an unconditional occurrence
denominator: no exact per-symbol trading-session/holiday schedule is bound, so absent
H4 timestamps cannot be separated from legitimate closures. Full-window candidate
counts are therefore unknown; loaded counts cover observed source rows only.

## Loaded-cell diagnostics by account, sleeve, and band

All numeric columns in this table are `OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY`.

| Account | Sleeve | Band | Result status | Source cells observed emit/no-emission/missing/outside | Emitted | Quote modelled | Cost evaluable | Floor survive/refuse | Survivor rows | Net clip mean/sum | Row coverage M/T/Md/NE |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| FTMO | crypto | low | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 180 | 180 | 149 | 180/0 | 149 | 0.293148/43.679009 | 0/0/149/31 |
| FTMO | crypto | mid | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 180 | 180 | 149 | 180/0 | 149 | 0.272868/40.657344 | 0/0/149/31 |
| FTMO | crypto | high | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 180 | 180 | 149 | 180/0 | 149 | 0.264768/39.450424 | 0/0/149/31 |
| FTMO | energy_agri | low | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 68 | 68 | 0 | 68/0 | 0 | NE/NE | 0/0/0/68 |
| FTMO | energy_agri | mid | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 68 | 68 | 0 | 68/0 | 0 | NE/NE | 0/0/0/68 |
| FTMO | energy_agri | high | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 68 | 68 | 0 | 68/0 | 0 | NE/NE | 0/0/0/68 |
| FTMO | sub_mid_dn_revert | low | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 18/0/2/0 | 323 | 323 | 126 | 252/71 | 110 | 0.812738/89.401185 | 0/0/126/197 |
| FTMO | sub_mid_dn_revert | mid | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 18/0/2/0 | 323 | 323 | 126 | 245/78 | 107 | 0.789526/84.479247 | 0/0/126/197 |
| FTMO | sub_mid_dn_revert | high | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 18/0/2/0 | 323 | 323 | 126 | 237/86 | 106 | 0.806644/85.504214 | 0/0/126/197 |
| FTMO | sub_xvol_pullback | low | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 12/1/5/0 | 79 | 79 | 14 | 74/5 | 14 | 1.507914/21.110792 | 0/0/14/65 |
| FTMO | sub_xvol_pullback | mid | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 12/1/5/0 | 79 | 79 | 14 | 74/5 | 14 | 1.507549/21.105689 | 0/0/14/65 |
| FTMO | sub_xvol_pullback | high | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 12/1/5/0 | 79 | 79 | 14 | 74/5 | 14 | 1.507112/21.099566 | 0/0/14/65 |
| redacted_account | crypto | low | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 1/0/0/1 | 94 | 94 | 94 | 94/0 | 94 | -0.104310/-9.805181 | 0/0/94/0 |
| redacted_account | crypto | mid | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 1/0/0/1 | 94 | 94 | 94 | 94/0 | 94 | -0.104381/-9.811822 | 0/0/94/0 |
| redacted_account | crypto | high | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 1/0/0/1 | 94 | 94 | 94 | 94/0 | 94 | -0.104528/-9.825616 | 0/0/94/0 |
| redacted_account | energy_agri | low | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 68 | 68 | 0 | 68/0 | 0 | NE/NE | 0/0/0/68 |
| redacted_account | energy_agri | mid | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 68 | 68 | 0 | 68/0 | 0 | NE/NE | 0/0/0/68 |
| redacted_account | energy_agri | high | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 2/0/0/0 | 68 | 68 | 0 | 68/0 | 0 | NE/NE | 0/0/0/68 |
| redacted_account | sub_mid_dn_revert | low | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 14/0/0/6 | 268 | 268 | 155 | 233/35 | 145 | 0.605253/87.761687 | 0/0/155/113 |
| redacted_account | sub_mid_dn_revert | mid | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 14/0/0/6 | 268 | 268 | 155 | 161/107 | 97 | 0.812800/78.841601 | 0/0/155/113 |
| redacted_account | sub_mid_dn_revert | high | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | 14/0/0/6 | 268 | 268 | 155 | 35/233 | 8 | 0.331650/2.653203 | 0/0/155/113 |
| redacted_account | sub_xvol_pullback | low | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 8/1/3/6 | 52 | 52 | 40 | 52/0 | 40 | 1.378580/55.143211 | 0/0/40/12 |
| redacted_account | sub_xvol_pullback | mid | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 8/1/3/6 | 52 | 52 | 40 | 44/8 | 32 | 1.627828/52.090503 | 0/0/40/12 |
| redacted_account | sub_xvol_pullback | high | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | 8/1/3/6 | 52 | 52 | 40 | 0/52 | 0 | NE/NE | 0/0/40/12 |

## Sleeve scorecard — evidence disposition, not an arming decision

`NE` means a supported source cell is absent or the scored exit contract differs from
the latest durable host observation. `RESEARCH_ONLY` means all supported
source files are present but scheduled-bar continuity, observed quote/fill lifecycle,
and native historical admission/router/account state remain incomplete. No sleeve earns
`KEEP` or `REPAIR` from these partial modelled rows.

Gross and net cells below are `mean/sum R` for low/mid/high. Gross and pre-floor net
cover every observed emitted row; survivor net is conditional on the current spread
floor. This paired display prevents positive-by-suppression.

| Account | Sleeve | Evaluation | Runtime parity | Source loaded/requested/missing/outside | Observed generator evaluations/emissions | Modelled gross all observed L/M/H | Modelled pre-floor net all observed L/M/H | Modelled survivor net L/M/H | Mid survivor CI95 | Mid top abs symbol/year | Missing cells | Recommendation |
|---|---|---|---|---:|---:|---|---|---|---|---|---|---|
| FTMO | crypto | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | `NOT_EVALUABLE_EXIT_CONTRACT_DIVERGENCE` | 2/2/0/0 | 21200/180 | low:0.499110/89.839763, mid:0.396858/71.434479, high:0.385480/69.386415 | low:0.293148/43.679009, mid:0.272868/40.657344, high:0.264768/39.450424 | low:0.293148/43.679009, mid:0.272868/40.657344, high:0.264768/39.450424 | [-0.058108, 0.616886] | BTCUSD 100.0% / 2025 24.5% | none | `NE` |
| FTMO | energy_agri | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 2/2/0/0 | 16172/68 | low:0.578065/39.308409, mid:0.577951/39.300655, high:0.577762/39.287825 | low:NE/NE, mid:NE/NE, high:NE/NE | low:NE/NE, mid:NE/NE, high:NE/NE | [NE, NE] | NE | none | `RESEARCH_ONLY` |
| FTMO | sub_mid_dn_revert | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 18/20/2/0 | 224138/323 | low:0.559245/180.636258, mid:0.521758/168.527825, high:0.456022/147.294978 | low:0.739264/93.147258, mid:0.739239/93.144159, high:0.669001/84.294068 | low:0.812738/89.401185, mid:0.789526/84.479247, high:0.806644/85.504214 | [0.346863, 1.237394] | GBPJPY 28.13% / 2023 31.19% | CORN_c,COTTON_c | `NE` |
| FTMO | sub_xvol_pullback | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 13/18/5/0 | 126345/79 | low:1.423924/112.489985, mid:1.423800/112.480220, high:1.423660/112.469129 | low:1.507914/21.110792, mid:1.507549/21.105689, high:1.507112/21.099566 | low:1.507914/21.110792, mid:1.507549/21.105689, high:1.507112/21.099566 | [0.085072, 2.647215] | JP225 55.75% / 2025 55.72% | CORN_c,COTTON_c,FRA40_cash,EU50_cash,US2000_cash | `NE` |
| redacted_account | crypto | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 1/2/0/1 | 10336/94 | low:0.147183/13.835246, mid:0.147113/13.828616, high:0.146966/13.814843 | low:-0.104310/-9.805181, mid:-0.104381/-9.811822, high:-0.104528/-9.825616 | low:-0.104310/-9.805181, mid:-0.104381/-9.811822, high:-0.104528/-9.825616 | [-0.596934, 0.468738] | BTCUSD 100.0% / 2021 39.49% | none | `RESEARCH_ONLY` |
| redacted_account | energy_agri | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 2/2/0/0 | 16172/68 | low:0.578288/39.323600, mid:0.565626/38.462559, high:-1.034661/-70.356938 | low:NE/NE, mid:NE/NE, high:NE/NE | low:NE/NE, mid:NE/NE, high:NE/NE | [NE, NE] | NE | none | `RESEARCH_ONLY` |
| redacted_account | sub_mid_dn_revert | `NOT_EVALUABLE_STREAM_SCHEDULE_UNBOUND` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 14/20/0/6 | 184136/268 | low:0.462406/123.924827, mid:0.298190/79.914878, high:-0.506741/-135.806653 | low:0.546292/84.675204, mid:0.359745/55.760450, high:-0.604752/-93.736501 | low:0.605253/87.761687, mid:0.812800/78.841601, high:0.331650/2.653203 | [0.374159, 1.262184] | GBPJPY 25.36% / 2023 27.4% | none | `RESEARCH_ONLY` |
| redacted_account | sub_xvol_pullback | `NOT_EVALUABLE_SUPPORTED_SOURCE_GAP` | `NOT_EVALUABLE_LOCAL_HOST_RUNTIME_DIVERGENCE` | 9/18/3/6 | 93993/52 | low:1.453442/75.578966, mid:1.447897/75.290657, high:-0.720846/-37.484008 | low:1.378580/55.143211, mid:1.371372/54.854862, high:-0.917461/-36.698450 | low:1.378580/55.143211, mid:1.627828/52.090503, high:NE/NE | [1.116994, 2.176784] | XAGUSD 49.6% / 2025 46.56% | FRA40_cash,EU50_cash,US2000_cash | `NE` |

## Historical publication boundary

`research/operations/w7_recost_2026_07_27/W7_RECOST_V1.json` at `4f7189432c184a7037fd8c16e974035be5d702b57b981f5c03df0b321f2a81c4` is retained only as a
historical record. Its non-unique cache identity and unbound later-revised cost input
prevent an authoritative row delta. For sleeves with a supported source gap, current sign
and descriptive differences are explicitly `NOT_EVALUABLE`; loaded-cell partial values
remain nested diagnostics only.

## Exact higher-information stop

Close the ten supported source cells with committed, hash-bound broker-clock H4 OHLCV
covering at least 259 closed warm-up bars before the fixed window and 80 H4 close-out bars
after it. Bind an exact per-symbol trading-session/holiday schedule (or a capture manifest
that proves scheduled-bar completeness) before treating observed-row zero emissions as
full-window no-ops. To elevate quote/lifecycle above `MODELLED`, acquire historical BID/ASK or tick
quotes plus resting-order/fill lifecycle authority. To claim native W7 economics, also
reconstruct exact as-of governor, open-risk, admission/occupancy, account, tick, symbol,
`order_calc_profit`, and execution state. No approximation is substituted for those inputs.
 Add typed terminal rows for every native BookEngine decision ordinal before claiming full
occurrence conservation, and reconcile the local include-clean3/frontier bytes to a bound
host observation before claiming runtime parity.

**No promotion, arming, risk-dial, composition, broker, order, or live-state mutation is made.**
