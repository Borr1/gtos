# Edge ENFORCE B — SleeveSpec draft + VPS land path

**as_of:** 2026-09-20T19:11:16+07:00  
**tag:** `sub_mid_dn_re_proxy_eurusd_short_m15_atr`  
**status:** Edge `.py` **NOT_LANDED** · Dig draft ready · `place=false` · **no `live_armed_set` edit until Chair APPLY**

## Affinity
`EURUSD` × `sub_mid_dn_re_proxy_eurusd_short_m15_atr` · SHORT · M15 · Module_ATR lens ONLY  
Distinct from clean3 `sub_mid_dn_revert` (H4 LONG multi-symbol substrate).

## Evidence (already on disk)
| pack | role |
|------|------|
| `SECONDARY_CANDIDATE_EURUSD_SUB_MID_DN_RE_PROXY_ATR_20260920` | secondary_candidate SCORE |
| ATR year tables | SHORT 13/13 · hold_year_sumR ~1114 · n=5818 |
| `EURUSD_SUB_MID_DN_RE_SHORT_MODULE_ATR_BLOTTER_20260920` | Module_ATR blotter |
| anti-oracle / deepen / handoff packs | honesty locks |

Locks: `ready_for_key_fx=false` · `promote=false` · `place=false`

## SleeveSpec draft — admission (confidence weight)

```python
    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr", 0.15, "fx_major",
        ('EURUSD',),
        "forward_only",
        "EURUSD M15 SHORT mid-stretch≥1ATR London/NY mean-revert (dn_re proxy); ATR-lens secondary_candidate 13/13 hold_year_sumR~1114 n=5818; NOT clean3 sub_mid_dn_revert H4 LONG; place=false until Chair APPLY"),
```

confidence starts **0.15** · status **forward_only** · asset_class **fx_major** · symbols `("EURUSD",)`

## SleeveSpec draft — registry (generation)

```python
    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": SleeveSpec(
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr",
        sub_mid_dn_re_proxy_eurusd_short_m15_atr.generate,
        TF_M15,
        "fx_major",
        sub_mid_dn_re_proxy_eurusd_short_m15_atr.ON_SURFACE,
    ),
```

`ON_SURFACE` must equal admission symbols. TF_M15. Import module when Edge lands.

## VPS land path (when Edge lands `.py`)

1. Land module → `src\components\ultimate_book\sleeves\sub_mid_dn_re_proxy_eurusd_short_m15_atr.py`
2. Verify TAG / ON_SURFACE=(EURUSD,) / generate / SHORT fail-closed
3. Registry import + SleeveSpec draft (DEFAULT-OFF / not live ACTIVE until Chair)
4. Optional admission draft block (commented or RESEARCH_REGISTRY) — not live_armed
5. Dig mirrors under `war_room/recovered/` + `research/warroom_20260920/`
6. Smoke import; confirm no place path
7. **STOP** — Dig does **not** edit `live_armed_set` until Chair says APPLY

## Dig idle
Until Edge lands the `.py` or Chair renames APPLY. Optional OSS ON_SURFACE hunt deferred unless Chair asks.

## Laws
place=false · no NEWS invent · affinity instrument×sleeve · ATR ≠ Dig PRIMARY · no host-mesh
