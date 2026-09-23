# Jev V1 critique — why the threshold sweep is not an integration

**Seat:** Astra / builder tissue. Docs only.  
**Date:** 2026-09-17.  
**Account:** Challenge **0** / ns `operator` / magic **0** / pass $110k. Verification **0** quarantined.  
**Verdict:** V1 is **calibration evidence**, not a live sidecar policy. Owner rejection of “V1 as the gate” is correct.

**Standalone GitHub agent** (not Project `gtos` chat). In-repo `.context/` was
read; Project distillates `MAC_INGEST` / `OWNER_LAW` / `ASTRA_ARCH` /
`NEWS_PROTOCOL` are **absent from git** — see V2 §8.

Sources (uploaded this session; not live wiring):

- Replay summary + 45-row jsonl (`challenge_replay_rows_7a99.jsonl`)
- `JEV_TUNED_POLICY_V1_20260917` and `JEV_GATE_SWEEP_20260917`
- Early sidecar + Astra Jev / Challenge / profit / orchestration notes
- Leftover-ship F5 desk (read from `f5-leftover-ship`, **not** this `main` checkout): `composer.py`, `write_inbox_verdict.py`, `inbox_gates.py`, `decide.py`, `shim.py`, `minimal_size.py`

Companion: [`JEV_INTEGRATION_V2_20260917.md`](JEV_INTEGRATION_V2_20260917.md).  
This file only answers: **what V1 actually measured, what it kept, what to discard.**

---

## 1. What V1 claimed to be

V1 presented a **LIVE KEEP recommend** as if it sat on the book:

```
house_toxic → BLOCK
admit_now.choice != admit → BLOCK / ESCALATE
spring|vss AND conf ≥ 0.55 → KEEP
ELSE conf ≥ 0.80 AND geo ≥ 1.0 → KEEP
ELSE escalate to chair
```

Headline on Challenge 45: kept **12** tickets, **+$406.24** vs actual **−$4,295.92**, Δ **+$4,702.16**, 4/6 winners, 100% toxic-family block.

That arithmetic is **true of the spreadsheet**. It is **false as a statement about how the book runs.**

---

## 2. The causal decomposition V1 hid

Recomputed from the same 45 jsonl rows (no re-query):

| Slice | n | Wins | PnL USD | What it is |
|---|---:|---:|---:|---|
| All 45 | 45 | 6 | **−4,295.92** | Broker tape |
| House toxic (US30 **or** bleed / orb / idxrev / xa_huge / mx_us30) | **24** | **0** | **−3,897.13** | **Owner surface law, already applied 2026-09-13** |
| Remainder (the only place Jev could add a judgment) | **21** | **6** | **−398.79** | Remaining DSP + spring + vss + three_fresh + one `sub_mid_dn_revert` + one `unknown` |
| V1 KEEP on that remainder | 12 | 4 | **+406.24** | Confidence × geo grid + spring/vss special case |
| Pre-cut (`pre_cut=true`) | 36 | 2 | **−4,748.54** | The toxic week |
| Post-cut (`pre_cut=false`) | **9** | 4 | **+452.62** | The only sample on today’s surface |

**House-toxic-only** (the sweep’s own “house_toxic block only” row) already does **Δ +$3,897.13**, 6W/15L, **−$398.79** kept. V1’s **+$4,702** headline is **~$3,900 of owner hard-off already live** plus **~$800 of in-sample threshold picking on 21 tickets**.

That is the owner complaint in one table: V1 is a **PnL grid on a week the house already cut**, not an integration with writer enrollment, chair verbs, 2-stop, 15-minute isolated re-entry, news/Walter, token digest, or Nightly Decide.

---

## 3. Defects that make V1 non-integrable

### 3.1 `admit_now` + “today surface” is hindsight on 36/45 tickets

V1 correctly notes `admit_then` = as-of-open and `admit_now` = live clock + **today’s** surface. It then **uses `admit_now` as the LIVE gate on historical closes**.

That is leakage. The 36 pre-cut tickets were **legal to print** when they printed (`surface_allowed_then: true` on the rows). Scoring them with Sep 17 law (US30 off, bleed/orb/idxrev/xa_huge hard-off) asks Jev to refuse a world the writer had not yet been forbidden to print.

US30 `surface_ok` noul on the same tickets:

| Clock | Typical `surface_ok` | Typical `admit` |
|---|---|---|
| `admit_then` (as-of-open) | 0.14–0.23 | `hard_refuse` already, **low confidence** (0.14–0.52) |
| `admit_now` (today’s law) | **0.03–0.05** | `hard_refuse` @ **0.99–1.0** |

The model is not discovering US30 toxicity from slate geometry. It is **echoing the house digest you put in state**. That is useful as a **consistency check** (“did we tell the model the law?”). It is not a gate.

`admit_then` on the same 45 keeps **2** tickets at conf≥0.55 (the sweep’s own STUDY row). That is the honest as-of-open number. V1 discarded it because it did not maximize kept PnL.

### 3.2 State is a close reconstruct, not a slate

`jev_admit_v1` required `candidate_id`, `symbol`, `side`, plus a **four-boolean surface digest**. The replay input is richer (SL/TP/prices, `remint_of`, `hold_min`, `commission`) but **still not a candidate**.

Missing versus leftover-ship `gtos.judgment.slate.v2` (`composer.py` candidate view + charter):

| Must exist at **intent** time | In V1 schema / replay state? |
|---|---|
| `slate_id` + `fingerprint` (verdict bind) | **No** |
| `status` ∈ {intent, standing, placed, filled, refused} | **No** — replay is post-fill |
| `cluster`, `alias_ids`, same-slate siblings | **No** |
| `decision_bar_iso`, `decision_day`, clock block | **No** |
| `geometry` {entry, stop, target} as **slate** fields | Prices exist on the **close**; not the composer intent |
| `high_impact_minutes` / calendar fold (T−15..T+60) | **No** |
| `spread_r_of_stop` | **No** |
| Occupancy: symbol open / pending / `already_placed_today` | **No** |
| 15-minute sibling / `just_closed_siblings` | `remint_of` on 6 rows; **not asked as a question** |
| 2-stop remaining (`F5_SAME_SLEEVE_ORIG_STOP_DAY_CAP`) | **No** (constant is **absent** from leftover-ship; live-only) |
| Token `config_digest_sha256` match / tag digest | **No** |
| `cost_screen` / expected commission R | Commission exists **ex-post** on the close |
| Governor allow / cap_mult (composer strips P&L) | **No** |
| Writer enrollment: would this row even reach send? | **No** |

Composer `EXPOST_KEYS` exist specifically so a judge never sees realized PnL. The V1 **objective** was kept **broker_net**. That is the opposite of the slate contract.

### 3.3 `geometry_quality ≥ 1.0` is almost tautological on this book

Score legend in the admit call:

- **0** — stop too tight or TP unreachable  
- **1** — **Acceptable — house default ~1R/6R with known fast-stop risk**  
- **2** — stop/TP fit current volatility  

DSP plan-R on these 45 is **~6–8**. Asking geo≥1.0 on a 1/6 sleeve **selects the house default**, which the autopsy already named as the **death geometry** (`SL_too_tight_fast_stop`). It does not measure “will this die in 4 minutes.”

V1 KEEP losers include:

| Ticket | Sleeve | Hold | Net | Why V1 kept |
|---|---|---:|---:|---|
| 291210052 | `dsp_two_bar_*` | **3.7 min** | −151.53 | conf80_geo1 |
| 291758207 | `dsp_three_bar_*` | **1.3 min** | −195.32 | conf80_geo1 |
| 292876275 | `dsp_three_bar_squeeze_*` | **1.2 min** | −151.38 | conf80_geo1 |

Those are Astra §4.3 **STARVE / next-kill** names. V1’s geo floor **endorsed** them.

vss winner `291816474` has geo **0.92** and was kept only by the **spring/vss special case** — i.e. **house KEEP**, not geometry.

### 3.4 Spring/vss @ 0.55 is circular

House law already **KEEP** `dsp_spring*` and `vss_fxcross*`. Lowering the confidence floor for those names is not a model finding. It is restating owner word so the grid can claim “we kept 4/6 winners.”

It also **kept the vss loser** (`291087142`, −$180.11, 46 min, InvTP_4h true). That is correct as house KEEP (n=2, do not starve). It is incorrect as evidence that 0.55 is a **calibrated** sleeve-specific threshold.

### 3.5 Close-label “86.7%” misses every paying exit

Replay: **5 time_stop** tickets, all **winners** (spring, three_fresh, expanding staircase, walked_hi +25, wide_down +225). Jev labeled **all five** `manual_other`.

| Ticket | True exit | Jev `exit_class` | Conf | Net |
|---|---|---|---:|---:|
| 291794419 | time_stop | manual_other | 0.81 | +453.14 |
| 292667008 | time_stop | manual_other | 0.80 | +505.28 |
| 292885676 | time_stop | manual_other | 0.86 | +449.09 |
| 293207416 | time_stop | manual_other | 0.68 | +224.94 |
| 292427064 | time_stop | manual_other | 0.37 | +25.38 |

Charter LABEL set is `orig_stop | broker_tp | time_stop | …`. V1’s `jev_close_label_v1` criteria used `tp | orig_stop | time_stop | manual_other` and still **did not emit `time_stop` on the five time_stops**. Accept-at-0.8 would have **accepted the wrong class** on the three high-conf winners.

The 39/45 (or 40/45 if you map `orig_tp`→`tp`) number is **orig_stop recall**. The exit class that paid the Challenge climb is the one V1 cannot name.

### 3.6 `toxic_remint` does not separate, and is post-hoc

Close-label Noul: winners mean **0.455** (range 0.43–0.51), losers mean **0.529** (0.47–0.61). Overlap is the whole useful interval. V1 correctly forbade it on LIVE admit — and the sweep still printed STUDY remint caps as the **best** PnL rows (+$1,558). That temptation is the defect.

Six jsonl rows carry `remint_of` (−$911.65). V1 never asked “is this the second same-sleeve orig_stop today?” as **code state**. The 2-stop circuit is a **writer integer**, not a Noul.

### 3.7 Multiple testing + constraint shopping

~600 composites, then a constraint “keep ≥4 of 6 winners **or** ≥80% of winner $.” That constraint is **the Challenge payout path** (spring / vss / three_fresh / expanding). Fitting thresholds **on the same 6 winners** you refuse to starve is how you get +$406 without a hold-out.

Nightly Decide (`decide.py`) already forbids this class of sentence: **KEEP/OFF only at n≥40 and |mean R| > 2·SE**. No V1 cell meets it. Honest word on every family in this file is **WATCH**.

### 3.8 Counterfactual is not a book

Blocking a ticket in a spreadsheet does not:

- cancel sibling **intents** on the same slate (the actual HOLD hole: 291549869 / 291549870 already LIVE),
- consume 2-stop remaining,
- change occupancy yield,
- remint or not remint after 15 minutes (writer law: isolated re-entry is a **new named fire** — do not HOLD it),
- keep the token digest valid,
- or stop the next DSP tag on the 51-list from printing.

V1 KEEP still includes two_bar / three_bar / descending / high_vol / three_fresh losers. The printer would still have a busy book. The +$406 assumes **blocked tickets vanish and nothing replaces them**.

### 3.9 Two bleed tickets the model admitted

`admit_now` **admitted** house-toxic bleed:

- `291549869` XAU `dsp_bleed_*` admit@0.66, tox_noul 0.44, −$144.92  
- `291713652` XAU `dsp_bleed_*` admit@0.44, tox_noul 0.46, −$170.70  

The sweep’s own gap note is the real finding: **do not rely on the model for toxic families.** V1 then put `house_toxic_hard_off: true` in the policy **and still sold Jev confidence as the product.**

### 3.10 No seat on the organism

V1 never specified:

- who writes `verdict.json` (only `write_inbox_verdict.py`, fingerprint-bound),
- that occupancy HOLD is **demoted** (`occupancy_script_not_intelligence`),
- that `approve` is **inert** (writer places on PASS),
- that missing Jev must be **abstain**, never fail-open-to-send,
- that Nightly Decide arithmetic stays Python,
- that this GitHub `main` tree is **W7**, not `f5-live` @ `c19c3aff9`.

A policy that cannot name those seams is a lab notebook.

---

## 4. What to keep (do not throw the lab out)

These are **real** and survive into V2:

1. **TypeSafe primitives work** on GTOS-shaped questions (2026-09-16 lab + 45-row batch). Latency class ~140–230 ms; fan-out is cheap.  
2. **House toxic is code, not a Noul.** The two bleed admits prove it.  
3. **LIVE vs STUDY field split.** `toxic_remint` / as-of-close features stay off the pre-fill path.  
4. **`admit_then` vs `admit_now` as two clocks** — keep the distinction; **do not promote `admit_now` on historical tickets**.  
5. **Flatten is a broken schema.** `jev_corr_hold_v1` enum + `not` clause. Keep.  
6. **Low-confidence admit → escalate** (lab 0.33). That is the only Jev output that may ever look “authoritative,” and only as **more abstain**.  
7. **Close-label orig_stop @ high confidence** on obvious SL deals. Useful for scoreboard LABEL assist — **after** the time_stop hole is fixed.  
8. **Garbage state refuses.** Adversarial empty probe. Keep `state_sufficient` as an explicit Noul.  
9. **Never place / never remint / never flatten / never move SL.** Stamps stay on every schema.  
10. **Shadow log + audit id** as the only next runtime. No Nightly splice from a sweep.

---

## 5. What to discard

| V1 object | Why discard |
|---|---|
| +$406.24 / +$4,702.16 as a **policy result** | House cut + in-sample grid. Quote only as “what the spreadsheet did.” |
| `min_admit_confidence` 0.80 and `spring_vss` 0.55 as **LIVE KEEP** | Thresholds fitted on 6 winners. Nightly would say WATCH. |
| `min_geometry_quality` 1.0 as a KEEP floor | Legend-1 **is** the 1R/6R death contract. |
| “admit_now + today surface” as the **historical** gate | Hindsight on 36 pre-cut rows. |
| ~600-composite sweep as model selection | Multiple testing. Pre-register metrics first (V2 §5). |
| STUDY remint-cap PnL rows | Leakage. Already labeled; still published as best. |
| Close-label 86.7% as “good enough” | Misses 5/5 time_stops — the payout exit class. |
| `confidence_gate` Score as a **fourth** policy layer | Nested confidence-about-confidence. Compose in code. |
| Any implication that V1 is **wired** | It is not. This tree has no sidecar client on the send path, and must not grow one. |

---

## 6. The one number V1 should have led with

On the **post-cut 9** (the surface that actually exists):

- Actual: **+$452.62** (4W / 5L).  
- V1 KEEP: 5 tickets, **+$501.12** (2W / 3L) — still keeps three_bar @ 1.2 min and two three_fresh orig_stops; **blocks** the +$224.94 wide_down time_stop and the +$25 walked_hi.  
- Δ vs actual on the honest window: **about +$48**, n=9.

That is a coin flip, not a gate. Fine-tuning that does not start from **writer laws + slate-complete state + Nightly n≥40** will keep rediscovering this.

V2 is the contract that starts there.