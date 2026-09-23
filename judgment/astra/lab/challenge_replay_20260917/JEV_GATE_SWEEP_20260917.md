# Jev gate sweep — Challenge replay 2026-09-17

Shadow/log only. Login **0**, magic **0**. No place / remint / flatten.
Offline grid on saved `challenge_replay_rows.jsonl` (45 tickets). No live API re-query.

## Book truth

| Metric | Value |
|---|---:|
| Tickets | 45 |
| Wins / Losses | 6 / 39 |
| Actual broker_net PnL | **-4295.92** USD |
| Winner $ total | 1938.47 |
| Toxic-family tickets (US30/bleed/orb/idxrev/xa_huge) | 24 |
| admit_now `hard_refuse` on toxic | **22/24 = 91.7%** (≥90% secondary ✓) |

Surface law held fixed: US30 off; hard-off bleed / orb_crypto / idxrev / xa_huge / mx_us30; keep spring+vss; 2-stop circuit.

## LIVE vs STUDY

| Gate class | Allowed fields |
|---|---|
| **LIVE** (pre-trade) | `admit_now` choice+conf, `surface_ok`, `toxic_family` noul, `geometry_quality`, house surface/tag/symbol |
| **STUDY** (post-hoc) | LIVE fields + `close_label.toxic_remint`, exit_class |

`admit_then` = replay-as-of-open; live sidecar should use **admit_now + today surface**.

## Constraint

Primary: maximize kept PnL subject to **keep ≥4 of 6 winners OR ≥80% of winner $**.
Secondary: toxic-family block rate under policy ≥ house hard-off (and admit_now HR ≥90% on toxic — already met by model+house).

## Top LIVE policies (selected)

| Policy | n_kept | kept PnL | Δ vs actual | W/L kept | blocked loss $ | blocked win $ | tox blk | constraint |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| V1 LIVE (recommended) | 12 | **+406.24** | +4702.16 | 4/8 | -4952.48 | 250.32 | 100% | OK |
| ALT LIVE (5W keep) | 15 | **+343.70** | +4639.62 | 5/10 | -4665.00 | 25.38 | 100% | OK |
| admit_now==admit conf≥0.80 + house_toxic | 14 | **+118.76** | +4414.68 | 4/10 | -4665.00 | 250.32 | 100% | OK |
| admit_now==admit conf≥0.55 geo≥1.0 + house_toxic | 13 | **+221.66** | +4517.58 | 4/9 | -4823.60 | 306.02 | 100% | OK |
| admit_now==admit conf≥0.70 + house_toxic | 17 | **-345.37** | +3950.55 | 4/13 | -4200.87 | 250.32 | 100% | OK |
| admit_now==admit conf≥0.55 (design v0, no house) | 21 | **-402.67** | +3893.25 | 6/15 | -3893.25 | 0.00 | 96% | OK |
| admit_now==admit conf≥0.85 + house_toxic | 8 | **+361.21** | +4657.13 | 3/5 | -5412.73 | 755.60 | 100% | fail |
| house_toxic block only | 21 | **-398.79** | +3897.13 | 6/15 | -3897.13 | 0.00 | 100% | OK |
| admit_now==admit (no conf) + house_toxic | 20 | **-257.75** | +4038.17 | 6/14 | -4038.17 | 0.00 | 100% | OK |
| BASE keep_all | 45 | **-4295.92** | +0.00 | 6/39 | 0.00 | 0.00 | 0% | OK |

## STUDY / then baselines (not for live fire)

| Policy | n_kept | kept PnL | W/L | note |
|---|---:|---:|---:|---|
| admit_then==admit conf≥0.55 | 2 | +100.53 | 1/1 | as-of-open; prefer admit_now live |
| admit_then==admit conf≥0.70 | 2 | +100.53 | 1/1 | as-of-open; prefer admit_now live |
| STUDY admit_now conf≥0.55 remint<0.48 + house | 6 | +1558.83 | 5/1 | post-hoc remint — do not use live |
| STUDY admit_now conf≥0.80 remint<0.50 + house | 6 | +1381.92 | 4/2 | post-hoc remint — do not use live |

## Recommended LIVE V1 (headline)

**Rules (recommend-only; never place-path):**

1. **Hard block** if house toxic surface: US30 symbol OR tag family in bleed / orb_crypto / orb_* / idxrev / xa_huge / mx_us30.
2. Require `admit_now.admit.choice == "admit"`.
3. **KEEP recommend** if either:
   - sleeve is **spring*** or **vss_*** AND `confidence ≥ 0.55`, OR
   - `confidence ≥ 0.80` AND `geometry_quality.score ≥ 1.0`.
4. Else **escalate to chair** (abstain / low-conf admit / mid-conf without geo) — sidecar does not soft-steer fire.
5. `hard_refuse` → block recommend. Never flatten. Chair still speaks ENFORCE/VETO/LABEL.

### Counterfactual on these 45

| | Value |
|---|---:|
| Kept n | **12** |
| Kept PnL | **+406.24** USD |
| Actual book | -4295.92 |
| Δ vs actual | **+4702.16** |
| Winners kept | **4/6** (1688.15 / 1938.47 = 87% winner $) |
| Losses kept | 8 |
| Blocked loss $ | -4952.48 (31 tickets) |
| Blocked win $ | 250.32 (2 tickets) |
| Toxic block rate | 100% |

Blocked winners under V1:
- `292427064` XAUUSD `dsp_walked_hi` net=+25.38 admit_now=admit@0.68 geo=0.98
- `293207416` XAUUSD `dsp_wide_down_then_micro_bounce_then_thr` net=+224.94 admit_now=admit@0.57 geo=1.14

Kept winners under V1:
- `291794419` XAUUSD `dsp_spring_cl` net=+453.14 conf=0.9 geo=1.05 sv=True
- `291816474` EURGBP `vss_fxcross_l` net=+280.64 conf=0.96 geo=0.92 sv=True
- `292667008` XAUUSD `dsp_three_fresh_lower_lows` net=+505.28 conf=0.83 geo=1.13 sv=False
- `292885676` XAUUSD `dsp_expanding_two_bar_run_tokyo` net=+449.09 conf=0.87 geo=1.15 sv=False

### Alternate (more winner-keep, slightly less PnL)

ALT = V1 but also KEEP when `0.55≤conf<0.80` AND `geo≥1.10` (no SV required), and KEEP any non-toxic admit with `conf≥0.80` even if geo&lt;1.0.

| | ALT |
|---|---:|
| Kept PnL | **+343.70** |
| W/L | 5/10 |
| Blocked win $ | 25.38 |

## Axes swept (offline)

- admit source: `admit_now` (live) vs `admit_then` (study)
- conf thresholds 0.35–0.85 step 0.05
- require `choice==admit`
- house toxic hard-off on/off
- `toxic_family` noul caps 0.25–0.55
- `surface_ok` floors 0.50–0.70
- `geometry_quality` floors 0.5–1.2
- spring+vss force-keep variants
- STUDY-only: `toxic_remint` caps (leakage — not live)

~600 composites evaluated; full dump: `lab/jev_gate_sweep_results.json`.

## Gaps

- No missing admit fields for V1 — `geometry_quality`, `toxic_family`, `surface_ok` already in `jev_admit_v1` answers.
- Two toxic bleed tickets were `admit` not `hard_refuse` under admit_now (291549869 @0.66, 291713652 @0.44); **house surface hard-off still blocks them**. Do not rely on model alone for toxic families.
- `toxic_remint` separates winners/losers weakly in STUDY; tempting but **post-hoc only**.
- Calibration is **one Challenge sample (45)** — shadow on live slate next; **no auto-splice**.

## Explicit non-goals

- Never on broker send / remint / flatten
- Never replace chair cards
- No Nightly Decide splice from this sweep alone
