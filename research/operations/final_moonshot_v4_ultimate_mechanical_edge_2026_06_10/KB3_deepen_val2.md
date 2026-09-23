# KB3 — Close remaining D6 caveats via deeper bridge data (track: deepen_val2)

Builder pass 2026-06-15. Goal: source deeper bridge history (siliconmetatrader5 @ localhost:8001,
.cash/.c symbol names) to convert the remaining FORWARD-ONLY D6 caveats to TRAIN-validated, and
unblock grains. Doctrine: build & improve, never kill; per-YEAR/per-SYMBOL never averages; no
lookahead; TRAIN<=2024 -> FORWARD 2025/2026 holdout mandatory; real cost scaled by stop tightness;
winsorize [-1.3,+5]; verify supersets before merge; delete nothing.

## Bridge probe — TRUE earliest history the broker serves NOW (read-only `copy_rates_range`)

`KB3_probe_symbols.py` queried each D6-caveat symbol at H1/M15/H4 over 2013..2026:

| logical | broker name | H1/M15/H4 earliest | last | TRAIN(<=2024) LTF now? |
|---------|-------------|--------------------|------|------------------------|
| USOIL   | USOIL.cash  | **2020-12-31**     | 2026-06-12 | **YES** (H1 32195 / M15 124939) |
| UKOIL   | UKOIL.cash  | **2020-12-28**     | 2026-06-12 | **YES** (H1 29209 / M15 102695) |
| NATGAS  | NATGAS.cash | 2024-10-14         | 2026-06-12 | thin (Q4-24 only) |
| WHEAT   | WHEAT.c     | **2023-03-27** H4  | 2026-06-12 | **YES H4** (4776 bars, 2023-24 train) |
| SOYBEAN | SOYBEAN.c   | **2023-08-04** H4  | 2026-06-12 | **YES H4** (4239 bars, 2023-24 train) |
| CORN    | CORN.c      | 2023-03-30 H4      | 2026-06-12 | YES (control; byte-identical to D2) |
| BTCUSD  | BTCUSD      | 2024-08-12         | 2026-06-14 | partial (8 train signals, 2024-09..12) |
| DASHUSD | DASHUSD     | 2024-08-17         | 2026-06-14 | partial (covered by 2024-08 LTF) |
| HEATOIL | HEATOIL.c   | 2025-01-06         | 2026-06-12 | NO (forward-only, unchanged) |
| COTTON  | COTTON.c    | 2025-03-17         | 2026-06-12 | NO (forward-only, unchanged) |

Decisive: **USOIL/UKOIL H1+M15 from 2020-12** and **WHEAT/SOYBEAN H4 from 2023** are NEW deep
history the prior pass (KB2) did not have. BTC/DASH H1+M15 from 2024-08 covers the 8 crypto train
signals. HEATOIL/COTTON/NATGAS hit the SAME broker ceiling as before — no deeper data exists.

## Exports written (existing conventions: versioned dir, manifest.json, sha256, read_only=True, 0 errors)

1. `data/mt5_research_exports/bridge_ftmo_energy_h1m15_backfill_2020_2026/` — USOIL/UKOIL/NATGAS
   H1+M15, 2020-2026 (broker-capped). 6 files, 0 errors.
2. `data/mt5_research_exports/bridge_ftmo_grains_h4_2023_2026/` — WHEAT_c/SOYBEAN_c/CORN_c H4. CORN
   is the **parity control: byte-identical to the CORN_c already in D2 (0 OHLC mismatches, same 4759
   bars)** — proves the export harness is faithful and the broker data is stable.
3. `data/mt5_research_exports/bridge_ftmo_crypto_h1m15_backfill_2024_2026/` — BTC/DASH H1+M15,
   2024-08+. 4 files, 0 errors.

**Superset verification (the "verify supersets before merge" requirement):** the deep energy/crypto
LTF is a STRICT SUPERSET of the forward-only LTF the prior cascade used — every prior-fwd row exists
in the deep export with **0 OHLC mismatches** (USOIL H1/M15, BTC H1/M15). The deep data only ADDS
earlier bars; the forward window is identical, so repointing the cascade reproduces the prior forward
numbers exactly (it does) and the new train numbers are pure additions.

**Grains merge:** WHEAT_c/SOYBEAN_c H4 copied into `bridge_ftmo_deep_h4_2022_2026/` (the dir
`w1.load` reads) — additive (both were ABSENT from D2). Provenance + src/dst sha in
`bridge_ftmo_deep_h4_2022_2026/KB3_GRAINS_BACKFILL_MERGE_PROVENANCE.json`. `w1.load('WHEAT_c')` now
serves 4776 bars / years [2023,2024,2025,2026]; cost falls back to global median 0.0953 = CORN's
agri cost (parity). The default `energy_agri_sleeve.ENERGY/AGRI` lists are UNCHANGED, so the locked
CORN/COTTON sleeve is a verified no-regression (ENERGY FWD +0.658R, AGRI FWD +0.418R reproduced).

---

## RE-VALIDATION VERDICTS (TRAIN<=2024 -> FORWARD, per-year, per-symbol, leak-audited)

### 1) ENERGY H1->M15 cascade better-fill -> **CONVERTS to TRAIN-VALIDATED** (the win of this track)

`KB3_revalidate_energy_cascade.py` repoints USOIL/UKOIL/NATGAS LTF to the deep export and re-runs
the EXACT cascade engine (`TW_mtf_cascade_transfer.run_cascade`, locked A/B-gated entries, STATE_D
exit). **0 leak flags across 104 audited LTF entries.** Fill mix now H1=54 / M15=22 / H4=29 (and on
TRAIN: H1=20 / M15=8 / H4=7 — the better-fill mechanic now FIRES on train-year signals, which it
could not before because there was no pre-2025 LTF).

| metric | BASE (H4 STATE_D) | **CASCADE** |
|--------|-------------------|-------------|
| **TRAIN<=2024 (n35)** | +0.457R, 74% | **+0.642R, 77%** |
| FWD2025 (n30) | +0.306 | **+0.588** |
| FWD2026 (n40) | +0.952 | **+1.281** |
| **FWD2526 (n70)** | +0.675 | **+0.984** |

- **Paired cascade-base: TRAIN +0.186R (t=1.68) ; FWD +0.309R (t=3.2).** The TRAIN lift is the
  conversion — previously 0 (cascade==base on train, no LTF). Now positive on energy's OWN pre-2025
  history, same sign as forward.
- **Better-filled rows only (where LTF actually improved the fill): TRAIN base +0.272 -> casc
  +0.504R (+0.232R lift)** — matches the metals pre-2025 OOS lift magnitude (+0.416R) the cascade
  was originally justified by, now reproduced ON energy directly (not just cross-class corroboration).
- **Per-symbol, both forward-validatable symbols are BOTH-SIDE positive lifts:**
  USOIL TRAIN +0.530->+0.711 (n18) / FWD +0.509->+0.828 (n18); UKOIL TRAIN +0.396->+0.628 (n14) /
  FWD +0.240->+0.660 (n22). (NATGAS train n3 flat; HEATOIL fwd-only +1.205->+1.589.)
- **VERDICT: the energy cascade lift is now a DIRECT train proof, not forward-only. D6 caveat
  CLOSED for energy.** Forward EV is also slightly higher than KB2's +0.877 (now +0.984) because
  UKOIL now has deep LTF instead of falling back to H4 on its 22 forward signals.
  Artifacts: `KB3_ENERGY_CASCADE_REVAL_RESULT.json`, `KB3_ENERGY_CASCADE_LEDGER.jsonl`.

### 2) CRYPTO H1->M15 cascade better-fill -> **PARTIALLY converts (train sign confirmed, thin)**

`KB3_revalidate_crypto_cascade.py` repoints BTC/DASH LTF to the 2024-08+ deep export (covers all 8
TRAIN signals, 2024-09..12), native target4 exit. **0 leaks, 68 audited.** TRAIN fill mix now
H1=6 / M15=1 / H4=1 (7 of 8 train signals got an LTF fill — impossible before).

| metric | BASE | **CASCADE** |
|--------|------|-------------|
| **TRAIN (n8)** | +1.138R, 50% | **+1.339R, 62%** |
| **FWD2526 (n60)** | +0.751 | **+1.068** (reproduces KB2 exactly) |

- Paired: TRAIN +0.201R (t=1.07, thin n8 -> not significant but SAME SIGN as fwd) ; FWD +0.317R
  (t=2.2). Better-filled TRAIN rows: +1.048 -> +1.277.
- **VERDICT: the crypto cascade train lift now exists and points the right way, but n=8 keeps it
  not-statistically-significant.** Caveat downgraded from "forward-only, no train at all" to "train
  sign-confirmed, thin". Broker ceiling (BTC/DASH 2024-08) blocks a deeper train. Artifacts:
  `KB3_CRYPTO_CASCADE_REVAL_RESULT.json`.

### 3) GRAINS (WHEAT_c, SOYBEAN_c) -> **UNBLOCKED + validated; LEARNING: do NOT carrier-weight them**

`KB3_revalidate_grains.py` adds WHEAT_c/SOYBEAN_c to AGRI and applies the LOCKED agri gates verbatim
(persistence ac60>=0.10 ; seasonal not-Dec-Feb). Real TRAIN(2023-24) + FORWARD(2025-26) split.

- **agri_persistence with grains added: TRAIN +0.003R (n28) ; FWD2025 +0.676 ; FWD2026 -0.908 ;
  FWD2526 -0.229R.** Adding grains DRAGS the pocket negative vs CORN/COTTON-only (+0.98R prior).
- **Per-symbol persistence:** WHEAT TRAIN **-0.420** / FWD **-0.901** (negative both sides);
  SOYBEAN TRAIN +0.738 (n3 tiny) / FWD **n=0** (no forward persistence trades -> cannot validate);
  CORN TRAIN +0.138 / FWD +0.530 (still the carrier); COTTON FWD +1.280 (fwd-only).
- **Grains-only persistence pocket: TRAIN -0.153R / FWD -0.901R** — falsified.
- **Grains seasonal breadth: TRAIN -0.047 / FWD -0.539R** — also negative forward.
- **VERDICT: grains caveat is CLOSED (data sourced + validated), with the honest finding that
  WHEAT/SOYBEAN do NOT carry the CORN/COTTON agri-persistence edge.** They are a different regime
  (the 2026 grain decline punishes the persistence gate). Kept (delete nothing) but must NOT be
  added at carrier weight; conf 0 for now, re-test as more bars accrue. CORN stays the agri carrier.
  This is a real improvement: it prevents diluting the agri sleeve with a negative-EV addition that
  a naive "add more grains for breadth" move would have made. Artifact: `KB3_GRAINS_REVAL_RESULT.json`.

### 4) HEATOIL / COTTON / NATGAS deep H4 -> **STILL BLOCKED at the broker ceiling**
Probe confirms HEATOIL.c 2025-01, COTTON.c 2025-03, NATGAS.cash 2024-10 are the broker's earliest —
NO deeper history exists. These remain forward-only / thin, exactly as KB2 found. Keep the 0.5 sym
haircut. This is now a HARD source ceiling, not a "not yet exported" gap.

---

## SUMMARY — D6 caveat status after this track

| D6 caveat (forward-only / blocked)        | deep data sourced            | status now |
|-------------------------------------------|------------------------------|-----------|
| Energy cascade lift forward-only          | USOIL/UKOIL H1+M15 2020-12+  | **CLOSED — train-validated** (TRAIN +0.186R t1.68; better-filled +0.232R) |
| Crypto cascade lift forward-only          | BTC/DASH H1+M15 2024-08+     | **PARTIAL — train sign confirmed, thin n8** (TRAIN +0.201R t1.07) |
| Grains blocked (no WHEAT/SOYBEAN)         | WHEAT/SOYBEAN H4 2023+       | **CLOSED — validated, LEARNING: not carrier-grade** (grains-only TRAIN -0.153 / FWD -0.901) |
| HEATOIL/COTTON forward-only               | none (broker ceiling)        | **STILL OPEN — hard source ceiling** (HEATOIL 2025-01, COTTON 2025-03) |
| NATGAS thin                               | none deeper (2024-10 ceiling)| **STILL OPEN — hard source ceiling** |

Net: of the open D6 caveats, **energy cascade fully closes** (the highest-value one — the energy
sleeve is a confirmed carrier), **crypto cascade partially closes** (sign confirmed on train, thin),
**grains close as a validated-negative learning** (prevents a bad breadth add). HEATOIL/COTTON/NATGAS
are now proven HARD source ceilings, not export gaps — the remaining amber on those is broker-data-
bound and cannot be closed from available inputs.

## Recommended scorecard update (D6)
D6 stays amber but for a SMALLER, sharper reason: the energy-cascade portion of the amber is now
GREEN (train-validated). Remaining amber = (a) crypto-cascade train is thin (n8), (b) HEATOIL/COTTON/
NATGAS are forward-only by HARD broker ceiling, (c) fx_jpy/idxrev remain falsified single-regime
(KB2, unchanged, correctly demoted to conf 0.15). No change to deployed sizing is required by this
track; it HARDENS the evidence under the energy sleeve (already conf 0.80) and ADDS a guardrail
against over-weighting grains.

## Data now in repo (exact)
- `bridge_ftmo_energy_h1m15_backfill_2020_2026/` (6 files: USOIL/UKOIL/NATGAS H1+M15; manifest+sha)
- `bridge_ftmo_grains_h4_2023_2026/` (3 files: WHEAT/SOYBEAN/CORN H4; manifest+sha; CORN=parity control)
- `bridge_ftmo_crypto_h1m15_backfill_2024_2026/` (4 files: BTC/DASH H1+M15; manifest+sha)
- `bridge_ftmo_deep_h4_2022_2026/` now also serves WHEAT_c/SOYBEAN_c H4 (provenance JSON inside)

## Scripts (track-prefixed)
- `KB3_probe_symbols.py` — broker earliest-history probe (read-only)
- `KB3_revalidate_energy_cascade.py` (+ `KB3_ENERGY_CASCADE_REVAL_RESULT.json`, `..._LEDGER.jsonl`)
- `KB3_revalidate_crypto_cascade.py` (+ `KB3_CRYPTO_CASCADE_REVAL_RESULT.json`)
- `KB3_revalidate_grains.py` (+ `KB3_GRAINS_REVAL_RESULT.json`)

## Next steps (for the loop)
1. Wire the train-validated energy cascade into `INTEG_portfolio_build_w2.py` at the SAME conf 0.80
   (EV unchanged ~+0.98R fwd; the change is evidence quality, not size) — energy now carries a
   direct train proof, removing the cross-class-only justification footnote.
2. Leave grains at conf 0; add a standing note that WHEAT/SOYBEAN are validated-negative on the
   persistence gate (do not re-add as breadth without a NEW gate that is train+forward positive).
3. HEATOIL/COTTON/NATGAS: mark as HARD source ceiling in the scorecard; the only unblock is the
   broker adding pre-2025 history (re-probe periodically).
4. Crypto cascade: re-run this validation as BTC/DASH H4 history deepens past 2024-08 to thicken the
   n=8 train sample toward significance.
