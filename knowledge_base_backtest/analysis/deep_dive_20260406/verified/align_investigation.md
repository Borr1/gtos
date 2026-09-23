# Align Variable Investigation

## What `align` measures
`align` is a **timeframe alignment count** (0-4) computed in `displacement_scanner.py` line 606.

### Computation
```python
align = sum([d1_dir == dr, h4_dir == dr, h1_dir == dr])
```
Plus +1 if price is near PDL (bullish) or PDH (bearish) — a "positional alignment" bonus.

### Values
- 0 = No higher timeframes agree with displacement direction
- 1 = One timeframe agrees
- 2 = Two timeframes agree
- 3 = Three timeframes agree
- 4 = Three TFs + positional alignment bonus

### Continuation rates by align value (from recomputation)
- align=0: n=2191, cont_rate=0.4491
- align=1: n=1421, cont_rate=0.4448
- align=2: n=2262, cont_rate=0.5119
- align=3: n=1436, cont_rate=0.555
- align=4: n=186, cont_rate=0.586

### Discovery/Validation split
- Discovery: align>=2 = 0.5169, align<2 = 0.442 (7.5pp)
- Validation: align>=2 = 0.5465, align<2 = 0.4526 (9.4pp)

### Validates: YES
Effect is monotonic (0.449 -> 0.586) and stable across disc/val.

### In the AI prompt: NO
The numeric `align` field is not in the AI prompts. The prompts use qualitative H4/D1 alignment but not this composite count.

### Prior session status
Listed under `untested_features` in displacement_feature_screen_20260406.json (p=0.0, correlation=0.086).
Was NOT included in the "confirmed" features because it's numeric (not binary).

### Actionability
Strong candidate for a threshold filter: require align >= 2 for trade entry.
This is the MOST actionable untested feature from the deep dive.
