# Tier-1 fixtures and GBPJPY A+ (conceptual)

SHADOW conceptual path for Instrument Edge PACK 3–5. Not an admit path.
No APPLY. No new refuse walls. Empty spine ≠ no BOJ.

Module of record: `src/judgment/pack5_fields.py` (`PACK5_FIXTURE_VECTORS`, `sleeve.gbpjpy_a_plus_ready`).
PACK 3 constants / t3=t4 alias: `src/judgment/pack3_fields.py` (`GBPJPY_FIXTURE_VECTORS`).
PACK 4 readiness label: `choice.gbpjpy_aplus_ready` ∈ {ready, not_ready, unassembled}. Keep.

---

## PACK 3 locked constants

- `resid_cap = 0.15` GJ
- `london_expand` pass ≥ 1.25, fail < 1.0
- `ny_impulse` pass ≥ 1.5, chop < 1.0
- Clocks on `time_utc` only (server−3h)
- London open winter 07–08:59 UTC / summer 06–07:59 UTC
- US30 open winter 14:30 / summer 13:30 UTC
- Overlap winter 13–17 / summer 12–16 UTC

## PACK 3 vectors (t3 aliases t4)

| id | verdict | fail | residual | expand | dual | sides (GBPUSD / USDJPY / GBPJPY) |
|---|---|---|---:|---:|---|---|
| t1 | pass | — | 0.08 | 1.40 | agree | long / long / long |
| t2 | fail | dual_split | 0.04 | 1.40 | split | long / short / long |
| t4 | fail | residual | 0.22 | 1.40 | agree | long / long / long |
| t3 | **alias of t4** | residual | 0.22 | 1.40 | agree | long / long / long |

Do not feed PACK 3 `t3` into the PACK 5 encoder. PACK 4 encode of t1/t2/t4 stays ready / not_ready `dual_split` / not_ready `residual`. PACK 4 `t3` still follows the PACK 3 alias (not_ready residual).

---

## PACK 5 Chair-canon Choice

`sleeve.gbpjpy_a_plus_ready` ∈ {`a_plus`, `almost`, `blocked`, `null_state`}.

```
a_plus = session_ok ∧ agree ∧ dual_same ∧ identity_ok(|resid|≤0.15)
         ∧ boj ∉ {print, guidance_live} ∧ tone ≠ risk_off
```

| Answer | Meaning |
|---|---|
| `a_plus` | All six conjuncts true |
| `almost` | Session ok, no hard block; a conjunct is soft or `tone` unassembled |
| `blocked` | dual_split, residual > 0.15, boj print\|guidance_live, or tone=risk_off |
| `null_state` | Required conjuncts unassembled. Empty spine ≠ no BOJ |

Fail order (hard): `dual_split` → `residual` → `boj_bucket` → `tone_risk_off`.

### PACK 5 fixture vectors (closed set)

`PACK5_FIXTURE_VECTORS`. **PACK 5 t3 is pass-capable** (residual 0.10, expand 1.25, tone neutral) — not the PACK 3 alias.

| id | choice | fail | residual | expand | tone | dual | boj_bucket |
|---|---|---|---:|---:|---|---|---|
| t1 | a_plus | — | 0.08 | 1.40 | neutral | same | none |
| t3 | a_plus | — | 0.10 | 1.25 | neutral | same | none |
| t2 | blocked | dual_split | 0.04 | 1.40 | neutral | split | none |
| t4 | blocked | residual | 0.22 | 1.40 | neutral | same | none |

Live t1 without `pack5_values.tone` → `almost` (`tone` unassembled) while PACK 4 stays `ready`.
t1 with `tone=risk_off` → `blocked` / `tone_risk_off`.

---

## Attach (Chair canon, SHADOW)

See `SLEEVE_ATTACH_MAP.md`.

- `gbpjpy_dual_leg` ≡ `gate.cross_stack_gbpjpy`, `resid_cap=0.15`
- `tokyo_event` SPLIT → `gate.asia_jpy_act_ok` + `gate.event_boj_window`
- `london_fit` SPLIT → `sleeve.london_expand_eur_gbp` + `gate.session_overlap_ok`
- `corr.xau_vs_eur_proxy_usd` alias of `usd_proxy_vs_xau`. **NO WIRE.**

Does not write `admit` / FLUID-ADM-007 / UB-AUTH-010. Inventory stays 48 / 8. `ENV-US30` stays integer OFF.
