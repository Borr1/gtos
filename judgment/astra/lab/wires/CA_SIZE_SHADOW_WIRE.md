# CA size wire — `ca_cross_asset_size_tilt` / CA-SIZ-001

**Date:** 2026-09-18  
**Wire:** `ca_cross_asset_size_tilt` / `CA-SIZ-001`  
**Surface:** Challenge `0` / `$110k` / magic `0` / ns `operator`  
**Verdict:** **PROVED_SHADOW** then **owner NAMED APPLY**  
**APPLY:** **open** (size_tilt only) as of `2026-09-18T14:34:00Z`  
**apply_claimed:** **0** until a live Challenge place

Owner spoken FULL APPROVAL 2026-09-18 ~21:34 ICT (Borhen / redacted_account Chair). Later spoken word wins.

Chair ultragoal: seven CA-* labels are `PROVED_SHADOW` (OCC / LIQ / EVT / USD / CORR / RSK / IDX). Label APPLY stays false. This pack is a **named size fire**, not a silent CA-label flip.

Jev never places. Envelope walls stay integers. NEWS_PROTOCOL is not invented.

---

## 1. Named fire (size_tilt APPLY now open)

| | flow | cost | **CA size (this pack)** |
|---|---|---|---|
| id | `f5_xau_flow_alignment_size_tilt` | `F5-JEV-004` | **`ca_cross_asset_size_tilt`** |
| status | `APPLIED_NAMED` | `APPLIED_NAMED` | **`APPLIED_NAMED` (2026-09-18T14:34Z)** |
| live | moves | moves | **moves when APPLY open** |
| APPLY | owner-named | owner-named | **owner-named size_tilt** |
| clamp | `[0.70, 1.15]` | `[0.70, 1.00]` | **`[0.70, 1.00]` veto-class** |
| in `APPLIED_WIRES` | yes | yes | **yes** |
| in 48-fluid inventory | alias | alias | **no** (not a 49th fluid) |

`wire_apply_open("ca_cross_asset_size_tilt")` is true except leave-orig / envelope walls. Physical lots still need `GTOS_JEV_APPLY_LIVE=1` + Challenge login `0` / ns `operator`. Combined live = `flow × cost × ca`. Leave-orig ticket 293332188 stays 1.0. A+ mute stays SHADOW / PROVE_SEED. XAU-only until a non-XAU wire is PROVED.

CA-* label targets stay `apply: false`. `CROSS_ASSET_PROVE_V0.json` `apply_any` stays false.

---

## 2. Tilt curve (conservative defaults)

Product of seven component tilts, then clamp to `[0.70, 1.00]`.  
Missing / unassembled / mixed / `no_clear` / empty spine → **1.0** (do not guess, do not invent).  
No component is a boost. Cannot refuse. Cannot zero a fire.

| Label | Input | Component tilt | Rationale |
|---|---|---:|---|
| **CA-OCC-001** `occupancy_world` | 2+ clusters | **0.85** | crowded book haircut |
| | 0 or 1 cluster | 1.00 | empty / one cluster — no add |
| **CA-LIQ-001** `session_liquidity` | thin (asia / dead / Friday) | **0.80** | clock thin, not invented volume |
| | ordinary or overlap | 1.00 | no overlap boost |
| **CA-EVT-001** `event_join` | named HIGH in F5 window | **0.70** | veto-class; never a refuse |
| | spine present, no HIGH | 1.00 | |
| | `spine_empty` | *skip (1.00)* | empty ≠ no HIGH; not NEWS_PROTOCOL |
| **CA-USD-001** `usd_proxy` | `usd_up` + gold long | **0.85** | adverse USD vs gold long |
| | `usd_down` + gold short | **0.85** | adverse USD vs gold short |
| | else / no side | 1.00 | do not guess side; no boost |
| **CA-CORR-001** `gold_usd_comove` | `with_usd` | **0.85** | confused gold/USD regime |
| | `against_usd` / `no_clear` | 1.00 | classic inverse is not a boost |
| **CA-RSK-001** `risk_on_funding` | `risk_on` | **0.90** | mild; gold can sell as risk |
| | `risk_off` / `mixed` | 1.00 | no risk-off boost |
| **CA-IDX-001** `gold_index_comove` | `with_us30` | **0.92** | gold acting as risk asset |
| | `against_us30` / `no_clear` | 1.00 | no safe-haven boost |

House hard-off → shadow 1.0. Leave-orig ticket 293332188 → live 1.0 (same as other wires).

---

## 3. Prove harness

```bash
python3 scripts/jev_ca_size_prove.py
```

Same Challenge pack and **same peer admit as PR #13** (`admit_challenge_peer_csv`: requires `time_utc`, last print ≥ 2026-09-17, refuses April `exports/multi_instrument/*`). Writes `CA_SIZE_SHADOW_PROVE.json`.

Bars (frozen, same as other size wires): `min_decidable=20`, `min_moved=5`, `min_distinct=2`, invented HIGH forbidden, live CA tilt must be 1.0, APPLY claimed fails, `combined_live_tilt` must equal flow × cost.

---

## 4. This-VM reads

### 4.1 First Cloud VM prove (peers absent)

97 shadow rows. Challenge XAU identity present. Chair zip FX/US30 peers were **not** on this Cloud VM (`multi/` gitignored and empty). April historical was **not** worn (`admit` refused `exports/multi_instrument/EURUSD_M15.csv`).

| | n |
|---|---:|
| decidable | **97** |
| moved (shadow ≠ 1.0) | **31** |
| distinct vals | **4** — `1.0000` 66 / `0.8000` 15 / `0.8500` 6 / `0.7000` 10 |
| live CA ≠ 1.0 | **0** |
| APPLY claimed | **0** |
| invented HIGH | **0** |
| combined = flow × cost | **97 / 97** |

Components assembled: occupancy 97, session_liquidity 97, event_join 97.  
Components moved: liquidity thin 21, occupancy crowded 14, HIGH-in-window 4.  
USD / CORR / RSK / IDX stayed **unassembled**. Conservative default 1.0 — they did not invent a tilt.

### 4.2 Chair zip re-run (2026-09-18T04:11:01Z)

Unzipped `_peer_multi_20260918` into `judgment/astra/lab/challenge_shadow_20260917/multi/`. Same admit as PR #13. CSVs stay gitignored.

| Peer M15 | admit | n | first_utc | last_utc | offset_ok |
|---|---|---:|---|---|---|
| EURUSD | ok | 2000 | 2026-08-20T07:15:00Z | **2026-09-18T03:00:00Z** | None (no `time_server_labeled`) |
| GBPUSD | ok | 2000 | 2026-08-20T06:15:00Z | **2026-09-18T03:00:00Z** | None |
| USDJPY | ok | 2000 | 2026-08-20T07:00:00Z | **2026-09-18T03:00:00Z** | None |
| US30 | ok | 2000 | 2026-08-19T05:15:00Z | **2026-09-18T03:00:00Z** | None — resolved `US30_cash_M15.csv` (aliases `US30.cash` / `US30` also admit) |

XAU identity stays parent `challenge_shadow_20260917/XAUUSD_M15.csv`. Zip XAU is unused. April `exports/multi_instrument/EURUSD_M15.csv` still refused (`no_time_utc_column_april_or_broker_naive`). `hydrate_channel = chair_attached_zip`.

| | n |
|---|---:|
| decidable | **97** |
| moved (shadow ≠ 1.0) | **95** (was 31) |
| distinct vals | **7** — `1.0000` 2 / `0.9200` 35 / `0.7820` 33 / `0.7000` 14 / `0.7360` 7 / `0.8000` 5 / `0.8280` 1 |
| live CA ≠ 1.0 | **0** |
| APPLY claimed | **0** |
| invented HIGH | **0** |
| combined = flow × cost | **97 / 97** |

| Label | assembled | moved | this-tape inputs |
|---|---:|---:|---|
| CA-OCC-001 occupancy | 97 | 14 | unchanged vs 4.1 |
| CA-LIQ-001 liquidity | 97 | 21 | unchanged vs 4.1 |
| CA-EVT-001 event | 97 | 4 | unchanged vs 4.1 |
| **CA-USD-001** usd_proxy | **97** | **34** | usd_flat 35; usd_up 56 (30 adverse-long haircut); usd_down 6 (4 adverse-short haircut) |
| **CA-CORR-001** gold_usd_comove | **32** | **0** | 32 `against_usd` (tilt 1.0 by curve); 65 `no_clear` unassembled. Classic inverse is not a boost and not a haircut. |
| **CA-RSK-001** risk_on_funding | **97** | **3** | 3 `risk_on` 0.90; 92 mixed; 2 risk_off |
| **CA-IDX-001** gold_index_comove | **87** | **87** | 87 `with_us30` 0.92; 10 `no_clear` |

**USD / RSK / IDX assemble and move tilts. CORR assembles (`against_usd`) and does not move.** APPLY stays false.

**Verdict: `PROVED_SHADOW`.** Ready to NAME later; this pack does not NAME.

---

## 5. What this pack refuses

- Place, remint, flatten, move SL, write inbox
- Flip any CA-* label `apply` to true
- Multiply CA into `combined_live_tilt`
- Add the wire to `APPLIED_WIRES` or the 48-fluid inventory
- Invent NEWS_PROTOCOL / HIGH rows
- Wear April `data/historical*` or `exports/multi_instrument/*` as Challenge tape
- Treat `data/DXY_D1.csv` as a prove source
- Lower the 20 / 5 / 2 bars
- Change envelope walls (`ENV-OCC`, `ENV-US30`, 2-stop COUNT, token, H8, dead-window writer clock)

---

## 6. Code map

| Piece | Path |
|---|---|
| Curve | `src/judgment/ca_size.py` |
| Compose attach | `src/judgment/compose.py` (`shadow_ca_size_tilt` / live follows when APPLY open) |
| Lock | `src/judgment/process_lock.py` `WIRE_CA_SIZE` in `APPLIED_WIRES` — owner NAMED APPLY 2026-09-18T14:34Z |
| Physical | `src/judgment/apply_size.py` combined = flow × cost × ca; Challenge login/ns + `GTOS_JEV_APPLY_LIVE=1` |
| Harness | `src/judgment/ca_size_prove.py` / `scripts/jev_ca_size_prove.py` |
| Tests | `tests/judgment/test_ca_size.py` |
| Prove JSON | `judgment/astra/lab/wires/CA_SIZE_SHADOW_PROVE.json` |
