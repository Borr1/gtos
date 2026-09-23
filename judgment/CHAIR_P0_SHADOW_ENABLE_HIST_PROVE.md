# Chair: P0 warroom_shadow enable + hist-prove (SHADOW only)

**When:** 2026-09-20 ~14:25 ICT war-room continue  
**Account:** Challenge login **0** only. Verification 0 quarantined.  
**Starting ref:** PR36 P0 `conf_gate_band` + KEEP shadow hooks (`apply=false`).  
**Monday live open:** still **NO APPLY**. Jev never places.

This receipt is the Chair enable path plus the FIRE 1201 hist-prove
score. **Never flip APPLY.** Never set `GTOS_JEV_FLUID_GATES_APPLY`.
It does **not** invent `NEWS_PROTOCOL`. Cost is never a kill-gate.

---

## 1. Enable SHADOW — this is the Chair step

On Challenge / Cloud Agent for `Borr1/ai-trading-agent`:

```bash
export GTOS_JEV_FLUID_GATES_SHADOW=1
# never:
#   export GTOS_JEV_FLUID_GATES_APPLY=1
#   export GTOS_DIG_MULTI_STAGE_GUARD_APPLY=1

python3 scripts/run_p0_shadow_hooks_historical_prove.py \
  --log-dir /tmp/p0-shadow \
  --score-out /tmp/p0-shadow/scorecard.json \
  --receipt-out /tmp/p0-shadow/fire1201.json
```

`--force` is the CI dry-run analog when the env flag is unset. Still
shadow-only. Chair production enable is **`GTOS_JEV_FLUID_GATES_SHADOW=1`
alone**.

One live sidecar cycle (still no broker):

```bash
GTOS_JEV_FLUID_GATES_SHADOW=1 python3 scripts/run_jev_fluid_gates_shadow.py
```

Logs land at `judgment/live/jev_sidecar/admit/<day>/<cycle_id>.json` with
`warroom_shadow.apply: false`.

Without `GTOS_JEV_FLUID_GATES_SHADOW=1` the live cycle writes nothing.
The hist-prove script still composes LABEL rows for scoring; Chair
enable is the env flag.

---

## 2. APPLY stays off

| Flag | State |
|---|---|
| `GTOS_JEV_FLUID_GATES_SHADOW` | **1** (Chair enable) |
| `GTOS_JEV_FLUID_GATES_APPLY` | **unset** — hist-prove **refuses** if set (exit 2) |
| `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` | **unset** — same refuse |
| `order_send` / `open_trade` under `src/judgment` | **0** |
| `NEWS_PROTOCOL` | stamps only — never invent |
| Cost | disclosure, never a kill-gate |

Even HIGH / KEEP / REVIEW labels do not authorize a place. FIRE 1201
band floors stay SHADOW — hist labels still lack numeric confidence.

---

## 3. FIRE 1201 tickets (LABEL only)

| Cohort | Tickets | Tape R | Stacked band law |
|---|---|---|---|
| KEEP wins (preserve) | `291816474` EURGBP vss · `293540988` EURUSD sub_mid · `291794419` XAUUSD spring | +1.87 / +2.962 / +3.02 | disposition **KEEP**, size **KEEP_CAP**, miss ≠ STAND_DOWN |
| Residual KEEP FS (PARKED) | `291087142` EURGBP vss · `293128383` XAUUSD sub_mid Off_hours | −1.2007 / −0.94 = **−2.14 R** | disposition **REVIEW**, miss **KEEP_EXEMPT**, not a new hard-off |

FIRE 1201 UB stack headline **+12.34 R** wins preserved is the stacked
CONF_GATE figure. This prove is LABEL on the three KEEP-win tickets
under S15 band + P0 STATE keep. Residuals stay SHADOW-PARKED.

Authority row = CF D bank (STATE keep + tape `conf_gate_band`).
S15 tape echo for the two residuals is **not** the KEEP surface when
STATE keep is missing (`293128383` sub_mid is CF D keep, not house
spring/vss name). Affinity stays instrument × sleeve on the row.

Close Loop `TICKET_SUBCLASS` wins for these tickets so S15 bands
stack (REVIEW, not the CF D miss→`fs_half` shortcut).

---

## 4. Hist-prove bars (measured 2026-09-20, Challenge 0)

```
n_rows == n_stamped == 67
apply_true == 0
n_order_send == 0
invented_high == 0
name_allowlist_used == 0
wins_preserved == true          # 3/3 KEEP wins stay KEEP under stacked bands
residual_shadow_parked == true  # 2/2 CF D authority residuals REVIEW / KEEP_EXEMPT
research_candidate.status == EMPTY
research_candidate.hard_off_keep_research == false
all-row dispositions: STRICT 23 / SESSION 13 / EVENT 6 / REVIEW 3 / KEEP 9
FIRE 1201 authority: keep_win KEEP 3 · residual REVIEW 2
```

S15-tape echo of `293128383` has no STATE keep (`sub_mid` is CF D keep, not
house spring/vss name) → disposition `None`, miss `STAND_DOWN`. That echo
is **not** a new hard-off and is **not** the authority row. Affinity stays
the instrument × sleeve pair on the row.

Machine receipt: [`astra/lab/p0_warroom_shadow_prove/FIRE1201_HIST_PROVE_RECEIPT.json`](astra/lab/p0_warroom_shadow_prove/FIRE1201_HIST_PROVE_RECEIPT.json)  
Scorecard: [`astra/lab/p0_warroom_shadow_prove/P0_WARROOM_SHADOW_SCORECARD.json`](astra/lab/p0_warroom_shadow_prove/P0_WARROOM_SHADOW_SCORECARD.json)

---

## 5. Research candidate

**EMPTY.**

No thin durable SHADOW observation beyond the parked FIRE 1201 labels.
KEEP wins stay KEEP. Residuals stay REVIEW / KEEP_EXEMPT. That does
**not** hard-off KEEP research.

Still PARKED (do not promote):

- Expanding / spring harden / V3
- GBPJPY × `sub_mid` Dig geometry HOLD-span FAIL (−922 R) — affinity
  suspicion vs Challenge n=1 KEEP; not a global rule

---

## 6. What Chair does **not** do from this receipt

- Set APPLY
- Place / remint / flatten / `order_send`
- Invent `NEWS_PROTOCOL`
- Use cost as a kill-gate
- Name-allowlist a KEEP sleeve
- Arm a new hard-off on residual FS KEEP
- Merge this PR as a live-open gate
