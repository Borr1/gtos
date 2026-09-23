# XAU false_structure sleeve structure-fail stories

- **Login:** `0` (Challenge-true `learning_scoreboard_60`)
- **ts_ict:** 2026-09-20 13:35 ICT
- **n_xau_fs:** 25
- **place:** False | **cf_variants:** PAUSED | **NEWS_PROTOCOL:** not invented

## Sleeve rollup (XAU × false_structure)

| sleeve_family | n | sum_R | avg_R | thin? | raw sleeves |
|---|---:|---:|---:|---|---|
| `three_bar` | 7 | -7.287 | -1.041 |  | dsp_three_bar×2, dsp_three_fresh×1, dsp_three_fresh_lower_lows×2, dsp_three_bar_squeeze_into_high×1, dsp_three_fre×1 |
| `walked` | 3 | -2.8498 | -0.9499 |  | dsp_walked_hi×3 |
| `bleed` | 2 | -2.11 | -1.055 | YES | dsp_bleed_accept_fresh_20low_second_push×2 |
| `dsp_isolated_` | 2 | -2.0877 | -1.0438 | YES | dsp_isolated_×2 |
| `dsp_two_bar_t` | 2 | -1.9902 | -0.9951 | YES | dsp_two_bar_t×2 |
| `unknown` | 2 | -0.9629 | -0.4814 | YES | null×2 |
| `dsp_rejection` | 1 | -1.05 | -1.05 | YES | dsp_rejection×1 |
| `dsp_accepted_` | 1 | -1.05 | -1.05 | YES | dsp_accepted_×1 |
| `dsp_rejection_wick_then_through` | 1 | -1.04 | -1.04 | YES | dsp_rejection_wick_then_through×1 |
| `dsp_descending_lows_accepted` | 1 | -1.03 | -1.03 | YES | dsp_descending_lows_accepted×1 |
| `dsp_wide_down` | 1 | -0.9857 | -0.9857 | YES | dsp_wide_down×1 |
| `dsp_high_vol_doji_after_reclaimed_flush` | 1 | -0.98 | -0.98 | YES | dsp_high_vol_doji_after_reclaimed_flush×1 |
| `sub_mid_dn_re` | 1 | -0.94 | -0.94 | YES | sub_mid_dn_re×1 |

Priority covered: **three_bar** (n=7), **walked** (n=3), **bleed** (n=2, thin). No other XAU FS family reaches n≥3.

## Chair lessons (teachable — not new CF variants)

1. three_bar on gold dies fast or dies clean: several shorts were stopped in 1–4 minutes when the “3-bar pivot” was just a pause inside a continuing push; the structure never owned the next bars.
2. walked_hi shorts on London gold lived longer (70m–4h) but still lost ~1R — highs kept walking; “accepted high” was not a reversal, it was permission for more upside into the stop.
3. bleed_accept second-push longs are thin (n=2) but both failed the same way: second push after 20-low acceptance reversed and tagged the protective low — acceptance was a trap, not fuel.
4. Every XAU FS close in this board is orig_stop — no soft exits. The miss is the structure read itself, not management after the fact.
5. KEEP vs non-KEEP on gold FS: only one KEEP-tagged XAU FS loser (sub_mid); three_bar / walked / bleed are non-KEEP and dominate gold structure blood. Teach: do not treat DSP three/walked/bleed on XAU as KEEP-protected.

## KEEP vs non-KEEP on XAU FS

- Definition: sleeve matches spring|vss_fxcross|sub_mid (same as LOSE_NARRATIVE / jev evaluator)
- XAU FS KEEP: n=1 sum_R=-0.94 — [{'ticket': 293128383, 'sleeve': 'sub_mid_dn_re', 'R': -0.94, 'session': 'Off_hours'}]
- XAU FS non-KEEP: n=24 sum_R=-23.4233
- Contrast: On XAU false_structure only: KEEP-signature n=1 (sub_mid_dn_re ticket 293128383 R=-0.94 is the sole KEEP XAU FS loser). Non-KEEP XAU FS n=24 sumR=-23.4233 — all orig_stop structure fails. Gold FS losses are almost entirely non-KEEP DSP sleeves; KEEP does not rescue three_bar/walked/bleed.

## Candle sources / gaps

**Used:**
- `/workspace/gtos/_peer_multi_20260918_unz/XAUUSD_M15.csv`
- `/workspace/gtos/_peer_multi_20260918_unz/XAUUSD_H4.csv`
- `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_M15.csv`
- `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_H4.csv`
- `learning_scoreboard_60.jsonl`
- `admission_labels_enforce/*.json`
- `LOSE_NARRATIVE_20260920.json`
- `vps_hydrate/challenge_0_deals.json`
- `live/_close_speak_*.json`

**Gaps:**
- M15 cache ends 2026-09-18T01:30:00+00:00 — trades after that lack M15 bars
- H4 cache ends 2026-09-18T01:00:00+00:00 — late Sep-18 London window partially uncovered
- historical_2026 XAU dumps end 2026-04 — not used for Sep Challenge tape
- Thin note: bleed: n=2 (thin)
- Thin note: No other XAU FS sleeve_family reaches n≥3 besides three_bar (7) and walked (3). bleed n=2 thin but priority-covered. dsp_isolated_/dsp_two_bar_t each n=2 — noted thin, not story-expanded.

## Stories — `three_bar` (5 tickets)

### Ticket `291758207` — dsp_three_bar SHORT R=-1.3

- **Fill / close (ICT):** 2026-09-11 08:00 ICT → 2026-09-11 08:02 ICT | **session:** Asia | **held:** 1m17s | **exit:** orig_stop
- **Geometry:** entry=4330.91 SL=4335.19 exit=4336.43
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54. Entry 4330.91 near H4 high (4300.69–4340.19); H4 body bearish. Nearby H4: 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09; 2026-09-11 04:00ICT O=4321.95 H=4333.71 L=4311.05 C=4331.89; 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54; 2026-09-11 12:00ICT O=4331.60 H=4360.80 L=4328.17 C=4346.86.
- **M15:** M15: short entry 4330.91 / SL 4335.19. Pre-fill: 2026-09-11 07:15ICT O=4318.89 H=4323.97 L=4316.79 C=4323.79; 2026-09-11 07:30ICT O=4323.63 H=4327.44 L=4319.60 C=4327.42; 2026-09-11 07:45ICT O=4327.43 H=4333.71 L=4326.70 C=4331.89. Through stop: 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4327.96 C=4333.00; 2026-09-11 08:15ICT O=4332.99 H=4337.19 L=4320.73 C=4327.97. Window H/L 4340.19/4311.05 — adverse push up into/through SL.
- **Plain story:** DSP three-bar — short on a clean 3-bar structural pivot (expect follow-through away from the pivot). Session Asia. Filled 2026-09-11 08:00 ICT, stopped 2026-09-11 08:02 ICT, lived 1m17s, R=-1.3. Price did not respect the short structure: from entry 4330.91 it pushed up into SL 4335.19 (exit 4336.43), tagging orig_stop. H4 at fill: 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54. Entry 4330.91 near H4 high (4300.69–4340.19); H4 body bearish. Nearby H4: 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09; 2026-09-11 04:00ICT O=4321.95 H=4333.71 L=4311.05 C=4331.89; 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54; 2026-09-11 12:00ICT O=4331.60 H=4360.80 L=4328.17 C=4346.86. M15: short entry 4330.91 / SL 4335.19. Pre-fill: 2026-09-11 07:15ICT O=4318.89 H=4323.97 L=4316.79 C=4323.79; 2026-09-11 07:30ICT O=4323.63 H=4327.44 L=4319.60 C=4327.42; 2026-09-11 07:45ICT O=4327.43 H=4333.71 L=4326.70 C=4331.89. Through stop: 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4327.96 C=4333.00; 2026-09-11 08:15ICT O=4332.99 H=4337.19 L=4320.73 C=4327.97. Window H/L 4340.19/4311.05 — adverse push up into/through SL.

### Ticket `292876275` — dsp_three_bar_squeeze_into_high SHORT R=-1.01

- **Fill / close (ICT):** 2026-09-16 09:30 ICT → 2026-09-16 09:31 ICT | **session:** Asia_London_pre | **held:** 1m13s | **exit:** orig_stop
- **Geometry:** entry=4303.81 SL=4308.97 exit=4308.97
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.5 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-16 08:00ICT O=4277.28 H=4340.83 L=4276.63 C=4321.81. Entry 4303.81 mid H4 range (4276.63–4340.83); H4 body bullish. Nearby H4: 2026-09-16 00:00ICT O=4295.51 H=4310.53 L=4290.16 C=4292.52; 2026-09-16 04:00ICT O=4295.12 H=4298.82 L=4275.35 C=4277.30; 2026-09-16 08:00ICT O=4277.28 H=4340.83 L=4276.63 C=4321.81; 2026-09-16 12:00ICT O=4321.82 H=4338.97 L=4320.67 C=4330.12.
- **M15:** M15: short entry 4303.81 / SL 4308.97. Pre-fill: 2026-09-16 08:45ICT O=4288.34 H=4288.87 L=4279.84 C=4282.34; 2026-09-16 09:00ICT O=4282.32 H=4294.73 L=4281.73 C=4292.20; 2026-09-16 09:15ICT O=4292.18 H=4300.48 L=4289.82 C=4298.80. Through stop: 2026-09-16 09:30ICT O=4298.83 H=4315.87 L=4298.53 C=4310.85; 2026-09-16 09:45ICT O=4310.87 H=4323.30 L=4310.76 C=4321.58. Window H/L 4340.83/4276.63 — adverse push up into/through SL.
- **Plain story:** DSP three-bar squeeze into high — fade the squeeze short, expecting rejection off the high cluster. Session Asia_London_pre. Filled 2026-09-16 09:30 ICT, stopped 2026-09-16 09:31 ICT, lived 1m13s, R=-1.01. Price did not respect the short structure: from entry 4303.81 it pushed up into SL 4308.97 (exit 4308.97), tagging orig_stop. H4 at fill: 2026-09-16 08:00ICT O=4277.28 H=4340.83 L=4276.63 C=4321.81. Entry 4303.81 mid H4 range (4276.63–4340.83); H4 body bullish. Nearby H4: 2026-09-16 00:00ICT O=4295.51 H=4310.53 L=4290.16 C=4292.52; 2026-09-16 04:00ICT O=4295.12 H=4298.82 L=4275.35 C=4277.30; 2026-09-16 08:00ICT O=4277.28 H=4340.83 L=4276.63 C=4321.81; 2026-09-16 12:00ICT O=4321.82 H=4338.97 L=4320.67 C=4330.12. M15: short entry 4303.81 / SL 4308.97. Pre-fill: 2026-09-16 08:45ICT O=4288.34 H=4288.87 L=4279.84 C=4282.34; 2026-09-16 09:00ICT O=4282.32 H=4294.73 L=4281.73 C=4292.20; 2026-09-16 09:15ICT O=4292.18 H=4300.48 L=4289.82 C=4298.80. Through stop: 2026-09-16 09:30ICT O=4298.83 H=4315.87 L=4298.53 C=4310.85; 2026-09-16 09:45ICT O=4310.87 H=4323.30 L=4310.76 C=4321.58. Window H/L 4340.83/4276.63 — adverse push up into/through SL.

### Ticket `291234829` — dsp_three_bar SHORT R=-0.9595

- **Fill / close (ICT):** 2026-09-09 20:46 ICT → 2026-09-09 20:50 ICT | **session:** NY | **held:** 4m14s | **exit:** orig_stop
- **Geometry:** entry=4417.31 SL=4423.64 exit=4423.79
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-09 20:00ICT O=4400.01 H=4433.92 L=4375.05 C=4409.50. Entry 4417.31 near H4 high (4375.05–4433.92); H4 body bullish. Nearby H4: 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54; 2026-09-09 16:00ICT O=4400.53 H=4415.13 L=4386.12 C=4400.00; 2026-09-09 20:00ICT O=4400.01 H=4433.92 L=4375.05 C=4409.50; 2026-09-10 00:00ICT O=4409.41 H=4421.34 L=4393.37 C=4399.82.
- **M15:** M15: short entry 4417.31 / SL 4423.64. Pre-fill: 2026-09-09 20:15ICT O=4413.15 H=4430.17 L=4410.72 C=4429.44; 2026-09-09 20:30ICT O=4429.43 H=4433.92 L=4412.86 C=4417.03; 2026-09-09 20:45ICT O=4417.02 H=4423.58 L=4410.31 C=4414.95. Through stop: 2026-09-09 21:00ICT O=4414.90 H=4428.45 L=4414.26 C=4423.23. Window H/L 4433.92/4390.79 — adverse push up into/through SL.
- **Plain story:** DSP three-bar — short on a clean 3-bar structural pivot (expect follow-through away from the pivot). Session NY. Filled 2026-09-09 20:46 ICT, stopped 2026-09-09 20:50 ICT, lived 4m14s, R=-0.9595. Price did not respect the short structure: from entry 4417.31 it pushed up into SL 4423.64 (exit 4423.79), tagging orig_stop. H4 at fill: 2026-09-09 20:00ICT O=4400.01 H=4433.92 L=4375.05 C=4409.50. Entry 4417.31 near H4 high (4375.05–4433.92); H4 body bullish. Nearby H4: 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54; 2026-09-09 16:00ICT O=4400.53 H=4415.13 L=4386.12 C=4400.00; 2026-09-09 20:00ICT O=4400.01 H=4433.92 L=4375.05 C=4409.50; 2026-09-10 00:00ICT O=4409.41 H=4421.34 L=4393.37 C=4399.82. M15: short entry 4417.31 / SL 4423.64. Pre-fill: 2026-09-09 20:15ICT O=4413.15 H=4430.17 L=4410.72 C=4429.44; 2026-09-09 20:30ICT O=4429.43 H=4433.92 L=4412.86 C=4417.03; 2026-09-09 20:45ICT O=4417.02 H=4423.58 L=4410.31 C=4414.95. Through stop: 2026-09-09 21:00ICT O=4414.90 H=4428.45 L=4414.26 C=4423.23. Window H/L 4433.92/4390.79 — adverse push up into/through SL.

### Ticket `291778371` — dsp_three_fresh LONG R=-1.01

- **Fill / close (ICT):** 2026-09-11 09:45 ICT → 2026-09-11 10:21 ICT | **session:** Asia_London_pre | **held:** 36m9s | **exit:** orig_stop
- **Geometry:** entry=4319.15 SL=4312.99 exit=4312.91
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.5 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54. Entry 4319.15 mid H4 range (4300.69–4340.19); H4 body bearish. Nearby H4: 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09; 2026-09-11 04:00ICT O=4321.95 H=4333.71 L=4311.05 C=4331.89; 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54; 2026-09-11 12:00ICT O=4331.60 H=4360.80 L=4328.17 C=4346.86.
- **M15:** M15: long entry 4319.15 / SL 4312.99. Pre-fill: 2026-09-11 09:00ICT O=4329.08 H=4333.34 L=4327.78 C=4330.65; 2026-09-11 09:15ICT O=4330.64 H=4334.42 L=4323.38 C=4325.07; 2026-09-11 09:30ICT O=4325.04 H=4326.30 L=4316.68 C=4318.66. Through stop: 2026-09-11 09:45ICT O=4318.65 H=4326.57 L=4315.77 C=4322.58; 2026-09-11 10:00ICT O=4322.57 H=4326.27 L=4314.31 C=4319.41; 2026-09-11 10:15ICT O=4319.41 H=4321.33 L=4304.12 C=4309.10; 2026-09-11 10:30ICT O=4309.09 H=4312.45 L=4306.36 C=4308.10. Window H/L 4337.19/4300.69 — adverse push down into/through SL.
- **Plain story:** DSP three-fresh — long on a fresh 3-bar structure break/continuation. Session Asia_London_pre. Filled 2026-09-11 09:45 ICT, stopped 2026-09-11 10:21 ICT, lived 36m9s, R=-1.01. Price did not respect the long structure: from entry 4319.15 it pushed down into SL 4312.99 (exit 4312.91), tagging orig_stop. H4 at fill: 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54. Entry 4319.15 mid H4 range (4300.69–4340.19); H4 body bearish. Nearby H4: 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09; 2026-09-11 04:00ICT O=4321.95 H=4333.71 L=4311.05 C=4331.89; 2026-09-11 08:00ICT O=4331.90 H=4340.19 L=4300.69 C=4331.54; 2026-09-11 12:00ICT O=4331.60 H=4360.80 L=4328.17 C=4346.86. M15: long entry 4319.15 / SL 4312.99. Pre-fill: 2026-09-11 09:00ICT O=4329.08 H=4333.34 L=4327.78 C=4330.65; 2026-09-11 09:15ICT O=4330.64 H=4334.42 L=4323.38 C=4325.07; 2026-09-11 09:30ICT O=4325.04 H=4326.30 L=4316.68 C=4318.66. Through stop: 2026-09-11 09:45ICT O=4318.65 H=4326.57 L=4315.77 C=4322.58; 2026-09-11 10:00ICT O=4322.57 H=4326.27 L=4314.31 C=4319.41; 2026-09-11 10:15ICT O=4319.41 H=4321.33 L=4304.12 C=4309.10; 2026-09-11 10:30ICT O=4309.09 H=4312.45 L=4306.36 C=4308.10. Window H/L 4337.19/4300.69 — adverse push down into/through SL.

### Ticket `292524534` — dsp_three_fresh_lower_lows LONG R=-1.01

- **Fill / close (ICT):** 2026-09-15 11:00 ICT → 2026-09-15 12:17 ICT | **session:** London | **held:** 1h17m0s | **exit:** orig_stop
- **Geometry:** entry=4304.42 SL=4298.89 exit=4298.89
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-15 08:00ICT O=4292.80 H=4317.21 L=4287.79 C=4304.63. Entry 4304.42 mid H4 range (4287.79–4317.21); H4 body bullish. Nearby H4: 2026-09-15 04:00ICT O=4299.37 H=4299.86 L=4283.19 C=4292.86; 2026-09-15 08:00ICT O=4292.80 H=4317.21 L=4287.79 C=4304.63; 2026-09-15 12:00ICT O=4304.62 H=4307.37 L=4261.21 C=4262.22; 2026-09-15 16:00ICT O=4262.19 H=4295.67 L=4261.37 C=4290.51.
- **M15:** M15: long entry 4304.42 / SL 4298.89. Pre-fill: 2026-09-15 10:15ICT O=4310.69 H=4314.11 L=4309.72 C=4310.68; 2026-09-15 10:30ICT O=4310.67 H=4313.39 L=4307.97 C=4308.50; 2026-09-15 10:45ICT O=4308.47 H=4309.88 L=4303.19 C=4303.46. Through stop: 2026-09-15 11:00ICT O=4303.30 H=4309.42 L=4302.41 C=4307.16; 2026-09-15 11:15ICT O=4307.21 H=4308.41 L=4302.58 C=4303.44; 2026-09-15 11:30ICT O=4303.46 H=4305.99 L=4300.56 C=4304.83; 2026-09-15 11:45ICT O=4304.83 H=4307.70 L=4304.00 C=4304.63; 2026-09-15 12:00ICT O=4304.62 H=4307.37 L=4300.32 C=4301.38; 2026-09-15 12:15ICT O=4301.39 H=4301.63 L=4296.27 C=4297.27. Window H/L 4317.21/4285.90 — adverse push down into/through SL.
- **Plain story:** DSP three-fresh lower-lows — long continuation after fresh LL acceptance. Session London. Filled 2026-09-15 11:00 ICT, stopped 2026-09-15 12:17 ICT, lived 1h17m0s, R=-1.01. Price did not respect the long structure: from entry 4304.42 it pushed down into SL 4298.89 (exit 4298.89), tagging orig_stop. H4 at fill: 2026-09-15 08:00ICT O=4292.80 H=4317.21 L=4287.79 C=4304.63. Entry 4304.42 mid H4 range (4287.79–4317.21); H4 body bullish. Nearby H4: 2026-09-15 04:00ICT O=4299.37 H=4299.86 L=4283.19 C=4292.86; 2026-09-15 08:00ICT O=4292.80 H=4317.21 L=4287.79 C=4304.63; 2026-09-15 12:00ICT O=4304.62 H=4307.37 L=4261.21 C=4262.22; 2026-09-15 16:00ICT O=4262.19 H=4295.67 L=4261.37 C=4290.51. M15: long entry 4304.42 / SL 4298.89. Pre-fill: 2026-09-15 10:15ICT O=4310.69 H=4314.11 L=4309.72 C=4310.68; 2026-09-15 10:30ICT O=4310.67 H=4313.39 L=4307.97 C=4308.50; 2026-09-15 10:45ICT O=4308.47 H=4309.88 L=4303.19 C=4303.46. Through stop: 2026-09-15 11:00ICT O=4303.30 H=4309.42 L=4302.41 C=4307.16; 2026-09-15 11:15ICT O=4307.21 H=4308.41 L=4302.58 C=4303.44; 2026-09-15 11:30ICT O=4303.46 H=4305.99 L=4300.56 C=4304.83; 2026-09-15 11:45ICT O=4304.83 H=4307.70 L=4304.00 C=4304.63; 2026-09-15 12:00ICT O=4304.62 H=4307.37 L=4300.32 C=4301.38; 2026-09-15 12:15ICT O=4301.39 H=4301.63 L=4296.27 C=4297.27. Window H/L 4317.21/4285.90 — adverse push down into/through SL.

## Stories — `walked` (3 tickets)

### Ticket `291096187` — dsp_walked_hi SHORT R=-1.0343

- **Fill / close (ICT):** 2026-09-09 14:30 ICT → 2026-09-09 18:50 ICT | **session:** London | **held:** 4h19m52s | **exit:** orig_stop
- **Geometry:** entry=4408.59 SL=4415.27 exit=4415.58
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54. Entry 4408.59 near H4 high (4380.34–4412.55); H4 body bullish. Nearby H4: 2026-09-09 08:00ICT O=4364.62 H=4384.22 L=4354.05 C=4381.46; 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54; 2026-09-09 16:00ICT O=4400.53 H=4415.13 L=4386.12 C=4400.00; 2026-09-09 20:00ICT O=4400.01 H=4433.92 L=4375.05 C=4409.50.
- **M15:** M15: short entry 4408.59 / SL 4415.27. Pre-fill: 2026-09-09 14:00ICT O=4400.44 H=4407.58 L=4399.19 C=4406.41; 2026-09-09 14:15ICT O=4406.21 H=4408.61 L=4402.82 C=4407.59; 2026-09-09 14:30ICT O=4407.55 H=4410.34 L=4406.38 C=4410.18. Through stop: 2026-09-09 14:30ICT O=4407.55 H=4410.34 L=4406.38 C=4410.18; 2026-09-09 14:45ICT O=4410.20 H=4412.55 L=4408.28 C=4409.13; 2026-09-09 15:00ICT O=4409.07 H=4411.84 L=4403.65 C=4403.73; 2026-09-09 15:15ICT O=4403.75 H=4404.69 L=4399.41 C=4399.52; 2026-09-09 15:30ICT O=4399.61 H=4403.41 L=4398.88 C=4399.83; 2026-09-09 15:45ICT O=4399.85 H=4403.21 L=4398.90 C=4400.54. Window H/L 4415.13/4386.12 — adverse push up into/through SL.
- **Plain story:** DSP walked-high — short after highs walked/accepted; expect failure of further upside and roll. Session London. Filled 2026-09-09 14:30 ICT, stopped 2026-09-09 18:50 ICT, lived 4h19m52s, R=-1.0343. Price did not respect the short structure: from entry 4408.59 it pushed up into SL 4415.27 (exit 4415.58), tagging orig_stop. H4 at fill: 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54. Entry 4408.59 near H4 high (4380.34–4412.55); H4 body bullish. Nearby H4: 2026-09-09 08:00ICT O=4364.62 H=4384.22 L=4354.05 C=4381.46; 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54; 2026-09-09 16:00ICT O=4400.53 H=4415.13 L=4386.12 C=4400.00; 2026-09-09 20:00ICT O=4400.01 H=4433.92 L=4375.05 C=4409.50. M15: short entry 4408.59 / SL 4415.27. Pre-fill: 2026-09-09 14:00ICT O=4400.44 H=4407.58 L=4399.19 C=4406.41; 2026-09-09 14:15ICT O=4406.21 H=4408.61 L=4402.82 C=4407.59; 2026-09-09 14:30ICT O=4407.55 H=4410.34 L=4406.38 C=4410.18. Through stop: 2026-09-09 14:30ICT O=4407.55 H=4410.34 L=4406.38 C=4410.18; 2026-09-09 14:45ICT O=4410.20 H=4412.55 L=4408.28 C=4409.13; 2026-09-09 15:00ICT O=4409.07 H=4411.84 L=4403.65 C=4403.73; 2026-09-09 15:15ICT O=4403.75 H=4404.69 L=4399.41 C=4399.52; 2026-09-09 15:30ICT O=4399.61 H=4403.41 L=4398.88 C=4399.83; 2026-09-09 15:45ICT O=4399.85 H=4403.21 L=4398.90 C=4400.54. Window H/L 4415.13/4386.12 — adverse push up into/through SL.

### Ticket `291072108` — dsp_walked_hi SHORT R=-0.9472

- **Fill / close (ICT):** 2026-09-09 13:03 ICT → 2026-09-09 14:17 ICT | **session:** London | **held:** 70m13s | **exit:** orig_stop
- **Geometry:** entry=4401.15 SL=4406.89 exit=4407.07
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54. Entry 4401.15 mid H4 range (4380.34–4412.55); H4 body bullish. Nearby H4: 2026-09-09 04:00ICT O=4357.29 H=4365.43 L=4341.22 C=4364.59; 2026-09-09 08:00ICT O=4364.62 H=4384.22 L=4354.05 C=4381.46; 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54; 2026-09-09 16:00ICT O=4400.53 H=4415.13 L=4386.12 C=4400.00.
- **M15:** M15: short entry 4401.15 / SL 4406.89. Pre-fill: 2026-09-09 12:30ICT O=4385.02 H=4395.35 L=4384.14 C=4395.35; 2026-09-09 12:45ICT O=4395.29 H=4400.70 L=4392.42 C=4398.69; 2026-09-09 13:00ICT O=4398.67 H=4405.13 L=4398.26 C=4401.28. Through stop: 2026-09-09 13:15ICT O=4401.27 H=4403.06 L=4395.12 C=4398.05; 2026-09-09 13:30ICT O=4398.04 H=4405.86 L=4396.99 C=4400.27; 2026-09-09 13:45ICT O=4400.37 H=4401.45 L=4398.73 C=4400.49; 2026-09-09 14:00ICT O=4400.44 H=4407.58 L=4399.19 C=4406.41; 2026-09-09 14:15ICT O=4406.21 H=4408.61 L=4402.82 C=4407.59; 2026-09-09 14:30ICT O=4407.55 H=4410.34 L=4406.38 C=4410.18. Window H/L 4412.55/4377.34 — adverse push up into/through SL.
- **Plain story:** DSP walked-high — short after highs walked/accepted; expect failure of further upside and roll. Session London. Filled 2026-09-09 13:03 ICT, stopped 2026-09-09 14:17 ICT, lived 70m13s, R=-0.9472. Price did not respect the short structure: from entry 4401.15 it pushed up into SL 4406.89 (exit 4407.07), tagging orig_stop. H4 at fill: 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54. Entry 4401.15 mid H4 range (4380.34–4412.55); H4 body bullish. Nearby H4: 2026-09-09 04:00ICT O=4357.29 H=4365.43 L=4341.22 C=4364.59; 2026-09-09 08:00ICT O=4364.62 H=4384.22 L=4354.05 C=4381.46; 2026-09-09 12:00ICT O=4381.41 H=4412.55 L=4380.34 C=4400.54; 2026-09-09 16:00ICT O=4400.53 H=4415.13 L=4386.12 C=4400.00. M15: short entry 4401.15 / SL 4406.89. Pre-fill: 2026-09-09 12:30ICT O=4385.02 H=4395.35 L=4384.14 C=4395.35; 2026-09-09 12:45ICT O=4395.29 H=4400.70 L=4392.42 C=4398.69; 2026-09-09 13:00ICT O=4398.67 H=4405.13 L=4398.26 C=4401.28. Through stop: 2026-09-09 13:15ICT O=4401.27 H=4403.06 L=4395.12 C=4398.05; 2026-09-09 13:30ICT O=4398.04 H=4405.86 L=4396.99 C=4400.27; 2026-09-09 13:45ICT O=4400.37 H=4401.45 L=4398.73 C=4400.49; 2026-09-09 14:00ICT O=4400.44 H=4407.58 L=4399.19 C=4406.41; 2026-09-09 14:15ICT O=4406.21 H=4408.61 L=4402.82 C=4407.59; 2026-09-09 14:30ICT O=4407.55 H=4410.34 L=4406.38 C=4410.18. Window H/L 4412.55/4377.34 — adverse push up into/through SL.

### Ticket `293650737` — dsp_walked_hi SELL R=-0.8683

- **Fill / close (ICT):** 2026-09-18 15:07 ICT → 2026-09-18 15:43 ICT | **session:** London | **held:** 35m38s | **exit:** orig_stop
- **Geometry:** entry=4368.3 SL=4375.24 exit=4375.9
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 unavailable: fill after H4 cache end 2026-09-18T01:00:00+00:00.
- **M15:** M15 unavailable: fill 2026-09-18T08:07:56+00:00 after cache end 2026-09-18T01:30:00+00:00.
- **Plain story:** DSP walked-high — short after highs walked/accepted; expect failure of further upside and roll. Session London. Filled 2026-09-18 15:07 ICT, stopped 2026-09-18 15:43 ICT, lived 35m38s, R=-0.8683. Price did not respect the short structure: from entry 4368.3 it pushed up into SL 4375.24 (exit 4375.9), tagging orig_stop. H4 unavailable: fill after H4 cache end 2026-09-18T01:00:00+00:00. M15 unavailable: fill 2026-09-18T08:07:56+00:00 after cache end 2026-09-18T01:30:00+00:00. Data gaps: m15_after_cache_end, h4_after_cache_end.
- **Data gaps:** m15_after_cache_end, h4_after_cache_end

## Stories — `bleed` (2 tickets)

### Ticket `291713652` — dsp_bleed_accept_fresh_20low_second_push LONG R=-1.14

- **Fill / close (ICT):** 2026-09-11 01:47 ICT → 2026-09-11 02:01 ICT | **session:** Off_hours | **held:** 14m14s | **exit:** orig_stop
- **Geometry:** entry=4331.72 SL=4321.91 exit=4320.4
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.5 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09. Entry 4331.72 mid H4 range (4313.62–4367.60); H4 body bearish. Nearby H4: 2026-09-10 16:00ICT O=4394.74 H=4400.03 L=4323.83 C=4339.93; 2026-09-10 20:00ICT O=4340.00 H=4376.36 L=4339.59 C=4363.95; 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09; 2026-09-11 04:00ICT O=4321.95 H=4333.71 L=4311.05 C=4331.89.
- **M15:** M15: long entry 4331.72 / SL 4321.91. Pre-fill: 2026-09-11 01:15ICT O=4340.71 H=4346.18 L=4337.36 C=4338.89; 2026-09-11 01:30ICT O=4338.91 H=4338.91 L=4331.68 C=4333.64; 2026-09-11 01:45ICT O=4333.58 H=4338.50 L=4329.64 C=4332.74. Through stop: 2026-09-11 02:00ICT O=4332.58 H=4332.58 L=4313.62 C=4322.16; 2026-09-11 02:15ICT O=4322.23 H=4330.79 L=4319.21 C=4327.15. Window H/L 4366.14/4313.62 — adverse push down into/through SL.
- **Plain story:** DSP bleed-accept fresh 20-low second push — long on second push after bleed acceptance of a fresh 20-low (expect continuation). Session Off_hours. Filled 2026-09-11 01:47 ICT, stopped 2026-09-11 02:01 ICT, lived 14m14s, R=-1.14. Price did not respect the long structure: from entry 4331.72 it pushed down into SL 4321.91 (exit 4320.4), tagging orig_stop. H4 at fill: 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09. Entry 4331.72 mid H4 range (4313.62–4367.60); H4 body bearish. Nearby H4: 2026-09-10 16:00ICT O=4394.74 H=4400.03 L=4323.83 C=4339.93; 2026-09-10 20:00ICT O=4340.00 H=4376.36 L=4339.59 C=4363.95; 2026-09-11 00:00ICT O=4364.03 H=4367.60 L=4313.62 C=4315.09; 2026-09-11 04:00ICT O=4321.95 H=4333.71 L=4311.05 C=4331.89. M15: long entry 4331.72 / SL 4321.91. Pre-fill: 2026-09-11 01:15ICT O=4340.71 H=4346.18 L=4337.36 C=4338.89; 2026-09-11 01:30ICT O=4338.91 H=4338.91 L=4331.68 C=4333.64; 2026-09-11 01:45ICT O=4333.58 H=4338.50 L=4329.64 C=4332.74. Through stop: 2026-09-11 02:00ICT O=4332.58 H=4332.58 L=4313.62 C=4322.16; 2026-09-11 02:15ICT O=4322.23 H=4330.79 L=4319.21 C=4327.15. Window H/L 4366.14/4313.62 — adverse push down into/through SL.

### Ticket `291549869` — dsp_bleed_accept_fresh_20low_second_push LONG R=-0.97

- **Fill / close (ICT):** 2026-09-10 19:00 ICT → 2026-09-10 19:24 ICT | **session:** NY | **held:** 23m45s | **exit:** orig_stop
- **Geometry:** entry=4374.38 SL=4366.48 exit=4366.39
- **Admission:** ADMIT / ALLOW_WITH_CUT size_mult=0.375 keep_surface=False rules=['G4_XAU_DSP_FS_HALF', 'G6_SESSION_0_75', 'G8_ORIG_STOP_NO_SILENT_REENTRY']
- **KEEP signature:** False
- **H4:** H4 at fill: 2026-09-10 16:00ICT O=4394.74 H=4400.03 L=4323.83 C=4339.93. Entry 4374.38 mid H4 range (4323.83–4400.03); H4 body bearish. Nearby H4: 2026-09-10 08:00ICT O=4400.92 H=4420.71 L=4400.03 C=4408.34; 2026-09-10 12:00ICT O=4408.35 H=4434.36 L=4392.32 C=4394.76; 2026-09-10 16:00ICT O=4394.74 H=4400.03 L=4323.83 C=4339.93; 2026-09-10 20:00ICT O=4340.00 H=4376.36 L=4339.59 C=4363.95.
- **M15:** M15: long entry 4374.38 / SL 4366.48. Pre-fill: 2026-09-10 18:15ICT O=4383.46 H=4388.57 L=4379.77 C=4385.76; 2026-09-10 18:30ICT O=4385.56 H=4390.61 L=4384.01 C=4384.40; 2026-09-10 18:45ICT O=4384.62 H=4385.14 L=4374.38 C=4374.45. Through stop: 2026-09-10 19:00ICT O=4374.41 H=4377.70 L=4369.75 C=4374.89; 2026-09-10 19:15ICT O=4375.15 H=4376.91 L=4361.75 C=4363.90; 2026-09-10 19:30ICT O=4363.65 H=4372.62 L=4323.83 C=4340.64. Window H/L 4394.55/4323.83 — adverse push down into/through SL.
- **Plain story:** DSP bleed-accept fresh 20-low second push — long on second push after bleed acceptance of a fresh 20-low (expect continuation). Session NY. Filled 2026-09-10 19:00 ICT, stopped 2026-09-10 19:24 ICT, lived 23m45s, R=-0.97. Price did not respect the long structure: from entry 4374.38 it pushed down into SL 4366.48 (exit 4366.39), tagging orig_stop. H4 at fill: 2026-09-10 16:00ICT O=4394.74 H=4400.03 L=4323.83 C=4339.93. Entry 4374.38 mid H4 range (4323.83–4400.03); H4 body bearish. Nearby H4: 2026-09-10 08:00ICT O=4400.92 H=4420.71 L=4400.03 C=4408.34; 2026-09-10 12:00ICT O=4408.35 H=4434.36 L=4392.32 C=4394.76; 2026-09-10 16:00ICT O=4394.74 H=4400.03 L=4323.83 C=4339.93; 2026-09-10 20:00ICT O=4340.00 H=4376.36 L=4339.59 C=4363.95. M15: long entry 4374.38 / SL 4366.48. Pre-fill: 2026-09-10 18:15ICT O=4383.46 H=4388.57 L=4379.77 C=4385.76; 2026-09-10 18:30ICT O=4385.56 H=4390.61 L=4384.01 C=4384.40; 2026-09-10 18:45ICT O=4384.62 H=4385.14 L=4374.38 C=4374.45. Through stop: 2026-09-10 19:00ICT O=4374.41 H=4377.70 L=4369.75 C=4374.89; 2026-09-10 19:15ICT O=4375.15 H=4376.91 L=4361.75 C=4363.90; 2026-09-10 19:30ICT O=4363.65 H=4372.62 L=4323.83 C=4340.64. Window H/L 4394.55/4323.83 — adverse push down into/through SL.

