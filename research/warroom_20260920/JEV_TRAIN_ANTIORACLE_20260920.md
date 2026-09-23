# JEV TRAIN ANTI-ORACLE — 2026-09-20
**Executor:** Chair HISTORICAL JEV TRAIN · login `0` · Challenge tape only  
**ts:** 2026-09-20 13:20 ICT · **Owner:** Jev everywhere · panic religion **OFF**  
**Honesty:** CF ≠ live · **No place / no order_send / no NEWS invent / no host-mesh**

## Priority this turn
Anti-oracle on **CF D** (FS non-KEEP stand_down). **CF E not re-run** — Close Loop already delivered E hold **+5.012**.

## CF D — claim metric = HOLD
Rule (frozen): F+G soft (keep full; FS half; session×0.75 nonkeep losses) + stand_down×0 when `miss=false_structure` AND NOT KEEP signature.

| split | n_train/n_hold | train CF_D | **hold CF_D** | hold baseline | hold F+G |
|---|---:|---:|---:|---:|---:|
| **ticket 70/30** | 42/18 | 6.4548 | **4.713** | -7.7157 | -0.1096 |
| ticket 40/20 | 40/20 | 3.0448 | 8.123 | -5.3157 | 2.9216 |
| full sample (oracle caveat) | 60 | — | **11.1678** | -38.5948 | -8.2371 |

- **Cite hold CF_D=+4.713 (70/30)** for validation claims — not full-sample +11.17.
- Hold 70/30: n_stand_down=12 · n_keep=2 · n_wins=3.
- Split-sensitive: 40/20 hold (+8.123) ≠ 70/30 hold (+4.713); both beat hold baseline.
- Sources: `jev_cf_D_anti_oracle_70_30.json`, `jev_cf_D_anti_oracle_40_20.json`.

## Policies B & C — same ticket 70/30 (honesty)
| policy | train sumR | hold sumR | note |
|---|---:|---:|---|
| A baseline | -30.8791 | -7.7157 | raw tape |
| B learn-soft | -6.1661 | **1.9699** | soft_xau_fs_half / soft_event_gap_half **leak miss_type** |
| C oracle labels | 4.3815 | 4.5499 | per-row desired_label — **NOT anti-oracle** |
| **C entry-fit anti-oracle** | 4.2969 | **3.3063** | majority label fit on train `(asset,sleeve_family,keep_surface)`; apply to hold; unseen keys→stand_down (n_unseen=3) |

## CF E — reference only (do not duplicate)
- Sleeve allow ∩ size×conf anti-oracle 70/30: **hold=+5.012** (train=3.6893).
- Source: `jev_cf_E_anti_oracle_keep.md` / `jev_anti_oracle_time_split.json`.

## Regime gap — partial fill, no invent
- `regime_tag` still **null** on all 60 — never invent S14 tags.
- Filled where features exist: `session_ict` (tape) + raw H4 OHLC context from box CSVs when symbol+open_utc match → **n=54** `session_h4_context_only`.
- Remaining **n=6** → `regime_unknown` (CRYPTO / missing H4 / no open_utc).
- VPS XAU hydrate: **skipped** (no machineId; VPS unreachable; no host-mesh). Box CSVs stale ~2026-09-18T03:00Z.
- Artifact: `jev_train_regime_context_partial.jsonl`.

## Artifacts
| path | what |
|---|---|
| `/workspace/gtos/close_loop/war_room_20260920/JEV_TRAIN_ANTIORACLE_20260920.md` | this file |
| `/workspace/gtos/close_loop/war_room_20260920/JEV_TRAIN_ANTIORACLE_20260920.json` | machine-readable |
| `/workspace/gtos/close_loop/war_room_20260920/jev_cf_D_anti_oracle_70_30.json` | D hold primary |
| `/workspace/gtos/close_loop/war_room_20260920/jev_train_regime_context_partial.jsonl` | regime partial |
| `/workspace/gtos/close_loop/war_room_20260920/jev_train_next_iteration.json` | updated next steps |

## Next (concrete)
1. Wire CF D stand_down as **SHADOW research label only** — no APPLY until entry-time KEEP signature (no miss_type leak) is proven on a fresh hold.
2. Replace B's miss-leaking soft halves with entry-only proxies (sleeve_family toxic / asset INDEX / session) and re-score hold.
3. Promote C entry-fit map to question-bank Choice priors; track hold false_abstain on ok_wins.
4. Regime: land Challenge H4/M15 when VPS is up; until then keep `regime_unknown` + session/H4 context only.
5. CF E hold +5.01 stands — **no further E variants** this room.
6. place=false · order_send=false · religion=false · news invent=false.
