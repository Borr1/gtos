# Challenge KEEP twin FS autopsy — idea validity — 2026-09-20

**Login:** 0 · **Mode:** SHADOW labels only · place=false · no NEWS invent · no hard-off KEEP research  
**ts_ict:** 2026-09-20 14:17 ICT · Fire: WAR_ROOM_FIRE_1404 Continue 1417  
**Scope:** residual open −2.14R on 2 KEEP FS tickets — twin vs same-family wins (idea validity, not cost kill)

## Twin pairs

### Twin A — EURGBP × vss_fxcross (same instrument)

| | Loss | Win |
|---|---|---|
| Ticket | **291087142** | **291816474** |
| Symbol / side | EURGBP SELL | EURGBP SHORT |
| Sleeve | `vss_fxcross_l` (family vss_fxcross_london) | `vss_fxcross_london` |
| Session | London | London |
| R / $ | **−1.2007** / −180.11 | **+1.87** / +280.64 |
| Exit | orig_stop FS | orig_tp ok_win |
| Hold | ~46.2 min | ~304.9 min |
| Geometry | entry 0.8583 · SL 0.85882 · TP 0.8573 · MFE≈0.31R MAE≈1.48R | entry 0.85924 · SL 0.85976 · TP 0.85824 |
| Conf / admit (replay) | KEEP surface; CONF_GATE_REVIEW / ALLOW_NO_BOOST | conf_now 0.96 · admit · CONF_GATE_score 1.25 |
| Gate post-stack | ALLOW_NO_BOOST · REVIEW untouched | wins preserved |

**WHY loss (idea):** KEEP vss admit — London structure failed house ~1R in <1h (false_structure orig_stop). Same instrument×sleeve family **also wins** two days later (+1.87, held to TP ~5h). KEEP ≠ free pass; path is REVIEW / no-boost, not cage the sleeve.

**Candidate separators probed (SHADOW only):**

| Probe | Separates twins? | Durable SHADOW label? | Why |
|---|---|---|---|
| Instrument×sleeve hard-off EURGBP×vss | Would kill win | **Reject** | Eats +1.87 (291816474) |
| London×vss stand_down | Both London | **Reject** | Same session; eats win |
| Hold_min < 60m stand_down | Yes on this pair | **Reject** | Post-hoc hold gate; n=1 pair; invents time-stop religion on KEEP research |
| Tight SL / geo_q alone | Loss SL ~5.2 pips; win SL also ~5.2 pips | **No** | Geometry width similar; path length differs |
| Cost / commission | Named in old swarm pack | **Forbidden** | Owner: cost never kill-gate |
| NEWS invent | No event stamp on loss | **Forbidden** | stamps_only |

**Twin A verdict:** mixed same-instrument affinity → **RESEARCH / REVIEW**, not a new durable stand_down.

### Twin B — sub_mid_dn_re (cross-instrument)

| | Loss | Win |
|---|---|---|
| Ticket | **293128383** | **293540988** |
| Symbol / side | XAUUSD LONG | GBPJPY LONG |
| Sleeve | `sub_mid_dn_re` | `sub_mid_dn_re` |
| Session | Off_hours | Tokyo (scoreboard) / Off_hours (MT5 open) |
| R / $ | **−0.94** / −141.04 | **+2.962** / +444.23 |
| Exit | orig_stop FS | orig_tp ok_win |
| Hold | ~72 min | ~623 min |
| Event | FOMC Rate Decision in window (any_high fill+close) | no event_proximity |
| Admit replay | admit_then admit → admit_now **hard_refuse** · CONF_GATE event_window | shadow_keep true |

**WHY loss (idea):** XAU×sub_mid Off_hours structure fail into scheduled high-impact window. Same **sleeve** on **GBPJPY** wins +2.96. Under instrument×sleeve affinity law, XAUUSD×sub_mid_dn_re Challenge n=1 thin loss → **RESEARCH suspicion**, not port/kill the FX win pairing.

**Candidate separators probed:**

| Probe | Separates twins? | Durable SHADOW label? | Why |
|---|---|---|---|
| Off_hours × sub_mid stand_down | Loss Off_hours; win open also Off_hours (MT5) | **Reject** | Would eat +2.962 (293540988) |
| XAU × sub_mid hard-off | Yes (instrument) | **Reject** | Thin n=1; KEEP research surface; affinity suspicion only |
| Event window stand_down | Loss has FOMC | **Already labeled** | CONF_GATE EVENT UB / event_window — not new |
| Session Tokyo-only keep | Win labeled Tokyo | Fragile | Session taxonomy mismatch (Tokyo vs Off_hours open); do not invent session cage |
| Port XAU multiyear rules onto GBPJPY | — | **Forbidden** | Affinity law |

**Twin B verdict:** separator is **instrument×sleeve affinity + existing EVENT UB**, not a new SHADOW stand_down.

## Aggregate SHADOW label decision

### Verdict: **EMPTY / PARK**

No durable new SHADOW label that (a) preserves both KEEP wins, (b) does not invent NEWS, (c) does not hard-off KEEP research sleeves, (d) is not already covered by CONF_GATE REVIEW / EVENT UB / G7 no-boost.

| Already labeled (not new) | Role |
|---|---|
| CONF_GATE_REVIEW on 291087142 | KEEP vss FS review |
| G7 / G8 ALLOW_NO_BOOST | no-boost path |
| CONF_GATE EVENT UB / event_window on 293128383 | FOMC window |
| XAU residual S15 review seed | prior |
| Instrument×sleeve affinity law | XAU sub_mid suspicion vs GBPJPY KEEP |

**Do not hard-off KEEP research.** Residual open stays **−2.1407R** on these 2 tickets until a separator proves wins_preserved across repeats (not available on Challenge n≈1 each).

## Multiyear side-note (this fire)

GBPJPY×sub_mid multiyear on hydrate_2045 → **BLOCKED/thin** (see `GBPJPY_SUB_MID_MULTIYEAR_20260920.md`). Does not unlock Monday.

## Milestone

- **New durable SHADOW label:** **EMPTY / PARK**
- **Loss open:** still **−2.1407R** (2 KEEP FS)
- **Monday-ready:** **NO**
- **APPLY:** unset · place=false · WakeParent=NO

## Artifacts

- `/workspace/gtos/research/warroom_20260920/CHALLENGE_KEEP_TWIN_FS_AUTOPSY_20260920.md`
- `/workspace/gtos/research/warroom_20260920/CHALLENGE_KEEP_TWIN_FS_AUTOPSY_20260920.json`
- Sibling BLOCKED: `GBPJPY_SUB_MID_MULTIYEAR_20260920.{md,json}`
- Prior residual: `CHALLENGE_RESIDUAL_AFTER_CONF_GATE_20260920.*`
