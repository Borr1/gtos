# JEV EVERYWHERE — 2026-09-20 13:15 ICT — login 0
n=60 sumR=-38.5948
Dimensions: jev_admit, jev_admit_cf, jev_size, jev_regime, jev_session, jev_sleeve_family, jev_cost_band, jev_conf_gate_band

## jev_admit
- `ADMIT_GOOD` n=7 sumR=15.921 avg=2.2744 wr=1.0
- `ADMIT_BAD_EVENT` n=3 sumR=-3.1387 avg=-1.0462 wr=0.0
- `ADMIT_BAD_FS` n=50 sumR=-51.3771 avg=-1.0275 wr=0.0

## jev_admit_cf
- `ADMIT_GOOD` n=7 sumR=15.921 avg=2.2744 wr=1.0
- `ADMIT_BAD_EVENT` n=3 sumR=-3.1387 avg=-1.0462 wr=0.0
- `ADMIT_CRYPTO_LEARN` n=3 sumR=-3.28 avg=-1.0933 wr=0.0
- `ADMIT_XA_LEARN` n=4 sumR=-4.74 avg=-1.185 wr=0.0
- `ADMIT_INDEX_LEARN` n=16 sumR=-16.6386 avg=-1.0399 wr=0.0
- `ADMIT_BAD_FS` n=27 sumR=-26.7185 avg=-0.9896 wr=0.0

## jev_size
- `SIZE_FULL_KEEP_WIN` n=3 sumR=7.852 avg=2.6173 wr=1.0
- `SIZE_FULL_DEFAULT` n=4 sumR=3.625 avg=0.9063 wr=0.75
- `SIZE_SESSION_TRIM` n=3 sumR=1.3053 avg=0.4351 wr=0.3333
- `SIZE_FULL_KEEP_LOSS` n=2 sumR=-2.1407 avg=-1.0703 wr=0.0
- `SIZE_HALF_FS` n=48 sumR=-49.2364 avg=-1.0258 wr=0.0

## jev_regime
- `regime_unknown` n=60 sumR=-38.5948 avg=-0.6432 wr=0.1167

## jev_session
- `Tokyo` n=1 sumR=2.962 avg=2.962 wr=1.0
- `Tokyo→London_pre` n=1 sumR=-1.034 avg=-1.034 wr=0.0
- `Off_hours` n=5 sumR=-1.461 avg=-0.2922 wr=0.4
- `Asia_London_pre` n=6 sumR=-2.35 avg=-0.3917 wr=0.1667
- `Asia` n=6 sumR=-5.5815 avg=-0.9303 wr=0.0
- `London_NY_overlap` n=7 sumR=-7.0516 avg=-1.0074 wr=0.0
- `NY` n=13 sumR=-8.8482 avg=-0.6806 wr=0.0769
- `London` n=21 sumR=-15.2305 avg=-0.7253 wr=0.0952

## jev_sleeve_family
- `spring` n=1 sumR=3.02 avg=3.02 wr=1.0
- `dsp_expand` n=1 sumR=2.99 avg=2.99 wr=1.0
- `sub_mid` n=2 sumR=2.022 avg=1.011 wr=0.5
- `vss_fxcross` n=2 sumR=0.6693 avg=0.3347 wr=0.5
- `dsp_wide` n=3 sumR=-0.5857 avg=-0.1952 wr=0.3333
- `unknown` n=3 sumR=-1.9829 avg=-0.661 wr=0.0
- `index_rev_bleed` n=2 sumR=-2.0079 avg=-1.004 wr=0.0
- `dsp_shakeout` n=2 sumR=-2.084 avg=-1.042 wr=0.0
- `other` n=2 sumR=-2.1545 avg=-1.0773 wr=0.0
- `orb_crypto` n=2 sumR=-2.28 avg=-1.14 wr=0.0
- `dsp_two` n=3 sumR=-3.0749 avg=-1.025 wr=0.0
- `dsp_reject` n=3 sumR=-3.27 avg=-1.09 wr=0.0

## jev_cost_band
- `COST_WIN` n=7 sumR=15.921 avg=2.2744 wr=1.0
- `COST_REVIEW` n=2 sumR=-2.1407 avg=-1.0703 wr=0.0
- `COST_SESSION` n=4 sumR=-3.0974 avg=-0.7743 wr=0.0
- `COST_EVENT` n=3 sumR=-3.1387 avg=-1.0462 wr=0.0
- `COST_FS` n=44 sumR=-46.139 avg=-1.0486 wr=0.0

## jev_conf_gate_band
- `CONF_GATE_ALLOW` n=4 sumR=8.069 avg=2.0173 wr=1.0
- `CONF_GATE_KEEP` n=3 sumR=7.852 avg=2.6173 wr=1.0
- `CONF_GATE_REVIEW` n=2 sumR=-2.1407 avg=-1.0703 wr=0.0
- `CONF_GATE_SESSION` n=4 sumR=-3.0974 avg=-0.7743 wr=0.0
- `CONF_GATE_EVENT` n=3 sumR=-3.1387 avg=-1.0462 wr=0.0
- `CONF_GATE_STRICT` n=44 sumR=-46.139 avg=-1.0486 wr=0.0

## CF policies (full surface Jev labels)
- **jev_sleeve_allow_spring_vss_sub_expand** sumR=8.7013 Δ=47.2961
- **jev_size_x_conf_shadow** sumR=-10.2958 Δ=28.299
- **jev_cost_band** sumR=-13.1816 Δ=25.4132
- **jev_conf_gate_shadow_trim** sumR=-13.1816 Δ=25.4132
- **LEGACY_religion_index_crypto_xa_0** sumR=-13.9362 Δ=24.6586
- **jev_size_map** sumR=-14.3029 Δ=24.2919
- **jev_sleeve_family** sumR=-17.0968 Δ=21.498
- **jev_admit_cf_half_learn_families** sumR=-26.2655 Δ=12.3293
- **jev_session** sumR=-28.1944 Δ=10.4004
- **baseline** sumR=-38.5948 Δ=0.0

Best: jev_sleeve_allow_spring_vss_sub_expand @ 8.7013R
Legacy religion: -13.9362R
Train: `/workspace/gtos/close_loop/war_room_20260920/jev_everywhere_lessons_0.jsonl`
