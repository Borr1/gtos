# Jev tuned LIVE sidecar policy V1 — 2026-09-17

Status: **shadow / recommend-only**. Never place-path. Chair (redacted_account) still speaks ENFORCE/VETO/LABEL.
Calibrated offline on Challenge replay 45 (login 0). Sample-of-one — shadow live slate before any splice.

## Contract

| Item | Value |
|---|---|
| Schema | `jev_admit_v1` |
| Model | jev (TypeSafe System One) — admit call at slate time |
| Mode | `shadow_log_only` |
| Admit clock | **`admit_now` + today surface** (not admit_then) |
| Action scope | never flatten; never place |

## LIVE KEEP recommend (all must hold)

```
IF house_toxic(symbol, tag):
    → BLOCK recommend   # US30 | bleed | orb_crypto | orb_* | idxrev | xa_huge | mx_us30

IF admit_now.choice != "admit":
    → BLOCK if hard_refuse
    → ESCALATE if abstain / other

IF sleeve_is_spring_or_vss(tag) AND confidence >= 0.55:
    → KEEP recommend

ELSE IF confidence >= 0.80 AND geometry_quality.score >= 1.0:
    → KEEP recommend

ELSE IF choice == "admit" AND confidence >= 0.55:
    → ESCALATE to chair   # mid-conf without geo/SV path

ELSE:
    → ESCALATE / BLOCK recommend
```

### Numeric gates (V1)

| Gate | Threshold | Role |
|---|---:|---|
| `min_admit_confidence` (general KEEP) | **0.80** | with geo≥1.0 |
| `spring_vss_min_confidence` | **0.55** | house KEEP sleeves |
| `min_geometry_quality` | **1.0** | Score 0–2 from admit call |
| `escalate_below_general` | 0.80 | admit but below KEEP band → chair |
| `house_toxic_hard_off` | true | code surface, not model-only |
| `max_toxic_family_noul` (advisory) | 0.35 | log/escalate if admit + high toxic noul; house already blocks families |
| `never_place` | true | |
| `never_flatten` | true | |

### Escalate rules

1. `admit` with `0.55 ≤ conf < 0.80` and not (spring/vss) and geo &lt; 1.0 → **escalate** (do not auto KEEP).
2. `admit` with conf ≥ 0.80 but geo &lt; 1.0 and not spring/vss → **escalate** (V1 prefers geo co-sign).
3. `confidence_gate` score legend-0 (escalate) → treat as escalate even if choice==admit.
4. Garbage / schema break / flatten scope → refuse; chair LABEL from broker facts only.

### Chair still speaks

Sidecar may only: score, label, HOLD draft, admit recommend.
Printer / writer unchanged. No auto splice without owner Nightly Decide.

## Counterfactual on Challenge 45

Actual book: **-4295.92** USD (6W / 39L).

| | V1 LIVE gate |
|---|---:|
| Kept tickets | 12 |
| Kept PnL | **+406.24** |
| Δ vs actual | **+4702.16** |
| Winners kept | **4/6** (87% of winner $) |
| Losses kept | 8 |
| Blocked loss $ | -4952.48 |
| Blocked win $ | 250.32 |
| Toxic families blocked | 100% |

Headline: on these 45, live gate would have kept **+406.24** vs actual **-4295.92**, kept **4W / 8L**.

### Alternate ALT (optional shadow A/B)

KEEP also when `(conf≥0.80)` without geo floor, OR `(0.55≤conf AND geo≥1.10)`.
Counterfactual: kept PnL **+343.70**, **5W/10L**, blocked win $25.38.

## Surface law (inputs, not Jev)

- US30 off
- Hard-off: bleed / orb_crypto / idxrev / xa_huge / mx_us30
- Keep: spring + vss
- 2-stop circuit
- Challenge pass context: 0 / $110k

## Close-label / corr HOLD (unchanged from design)

- Close-label: accept `exit_class` when confidence ≥ 0.8; else chair LABEL from broker facts.
- Corr HOLD draft: speak HOLD only if speak_hold noul ≥ 0.6 AND hold_strength ≥ 1.5 AND action_scope ∈ {audit_only, block_sibling_prefills}.
- STUDY may use `toxic_remint`; **LIVE admit must not**.

## Next

1. Shadow V1 on live slate candidates (log KEEP/ESCALATE/BLOCK + audit ids under `judgment/live/jev_sidecar/`).
2. Compare ALT in parallel logs.
3. Owner Nightly Decide before any intelligence-tissue soft-steer.
4. Do **not** re-query Challenge 45 unless a schema field is missing (none missing for V1).

## References

- Sweep tables: `research/jev/lab/JEV_GATE_SWEEP_20260917.md`
- Replay: `research/jev/lab/CHALLENGE_JEV_REPLAY_20260917.md`
- Design: `research/jev/JEV_SIDECAR_DESIGN_20260916.md`
- Schema: `research/jev/sidecar/schemas/jev_admit_v1.json`
