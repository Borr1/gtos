# Structure-Log Loader (Shared)

**Module:** `src/research_infra/structure_log_loader.py`
**Purpose:** A single discover + parse + cache pipeline for the structure-detector shadow log + every companion file.
**Consumers:** A3 (`stratification.py`), A5 (`regime_matrix.py`).

## Why this exists

A3's loader was extended in commit `e4bf7b9` to consume rotated `.jsonl.gz` archives plus the offline backfill emitted by `scripts/research/backfill_v2_regime.py`. A5's `load_regime_index` was NOT updated, which collapsed A5's 2026-04-26 re-run to UNTAGGED=100% after the live log rotated to its current ~12-line state.

The systemic fix per memory note `feedback_engineer_systemic_not_patches`: extract the loader into a shared module so any future rotation/backfill change applies to A3 and A5 (and any future research consumer) atomically.

## Public surface

| Function | Returns | When to use |
|---|---|---|
| `discover_structure_log_paths(seed_path)` | `list[Path]` | Pure path discovery — list every companion the loader will read. Useful for diagnostics. |
| `load_structure_log_rows(seed_path)` | `Iterator[dict]` | Stream all parsed rows. Caller filters / projects whatever fields it wants. A5's `load_regime_index` consumes this. |
| `build_h4_regime_index(seed_path)` | `dict[(symbol, "H4", ts_iso_z), regime_label]` | Convenience helper that filters to H4 rows + applies the production label-priority rule. A3's `_load_structure_log` wraps this. |
| `reset_cache()` | `None` | Clear the module-level caches. Tests that mutate the same on-disk path between assertions need this. |

## Discovery rules

For a seed path (typically `shadow_logs/structure_detector_divergences.jsonl`), the loader walks:

1. **The seed itself** if it exists.
2. **Same-directory siblings** whose name starts with one of `STRUCTURE_LOG_PREFIXES` (`structure_detector_divergences`, `structure_detector_backfill`) AND ends in `.jsonl` or `.jsonl.gz`. This covers:
   - The live log when seeded with one of its rotation archives.
   - The offline backfill (`structure_detector_backfill_*.jsonl`).
   - Same-directory archive drops from older deployments.
3. **The canonical archive directory** at `research/archive/structure_detector_divergences/` (located by walking up from the seed's parent until a `pyproject.toml` is found; bounded to 8 levels to avoid unbounded traversal).

De-duplicated by resolved path. Sorted lexicographically — newer archive names contain ISO dates so the order is deterministic and the newest archive shadows older entries when collisions happen during merge.

## Fingerprint cache

Every call computes a tuple of `(resolved_path_str, mtime_ns, st_size)` for each contributing file. The full tuple is the cache key:

```python
fingerprint = (
    ("/.../structure_detector_divergences.jsonl", 1745718900_000_000_000, 8580),
    ("/.../structure_detector_backfill_2026.jsonl", 1745719560_000_000_000, 1323973),
)
```

Any file mutation (rotation, backfill re-run, truncation, archive drop) flips at least one of `mtime_ns` or `st_size` and the cache key changes — the next call reparses. Two separate cache dicts are maintained:

| Cache | Used by | Stores |
|---|---|---|
| `_ROWS_CACHE` | `load_structure_log_rows` | List of all parsed dicts (no filter). |
| `_H4_INDEX_CACHE` | `build_h4_regime_index` | The H4-only `{(symbol, "H4", ts_iso_z): regime_label}` map. |

Tests that need a fresh cache call `reset_cache()` (the new `tests/research_infra/test_structure_log_loader.py` does this autouse).

## Fail-open semantics

| Failure mode | Behaviour |
|---|---|
| Seed path doesn't exist | Discovery walks the rest of the rules; returns whatever is found. |
| No companions discovered at all | Returns `[]` / empty iterator / empty dict. |
| Corrupt `.jsonl.gz` (truncated, wrong magic) | `gzip.open` raises on first read; caught and logged at WARNING. The other companions still load. |
| Malformed JSON line | Skipped silently (debug-logged). The rest of the file still loads. |
| `OSError` on stat / iterdir | Logged at WARNING; the function returns whatever has accumulated. |

The contract: **the loader never raises out**. Research callers tag UNTAGGED rather than dying mid-CLI.

## Latest-write-wins on key collisions

The H4 index iterates companions in discovery order (seed first, then siblings in lexicographic order). Each row's `(symbol, "H4", ts_iso_z)` is written into the dict; later writes clobber earlier ones. This matches A3's prior contract — a freshly rotated archive can correct an earlier `production_label` value without needing manual cleanup.

## Memory budget

* Live log: ~10-20k rows post-rotation = ~5 MB JSON.
* Backfill: 3,571 rows = ~1.3 MB.
* Archive directory: variable; current single `*.jsonl.gz` files run 1-3 MB compressed.

Total resident: well under 10 MB for the H4 index plus the row list. Both caches are process-local and cleared at process exit.

## Tests

`tests/research_infra/test_structure_log_loader.py` covers:

* `discover_structure_log_paths`: returns `[]` for `None`, returns `[]` when seed dir missing, finds the live `.jsonl`, finds `.gz` archives, finds backfill siblings, skips unrelated `.jsonl` siblings, dedups when seed is also a sibling, pins the recognised prefixes.
* `load_structure_log_rows`: empty for missing companions, yields rows from live `.jsonl`, yields from `.gz` only, yields from backfill only, merges all three, skips malformed rows silently, fails open on corrupt `.gz`.
* Cache fingerprint: repeat call uses cache, mtime change invalidates, new archive invalidates, `reset_cache()` clears both dicts.
* `build_h4_regime_index`: H4-only filter, label priority (`production_label > v2_direction > v1_direction`), empty-symbol skip, archive + backfill merge, latest-write-wins on collision.
* Project-root archive walk: discovers `research/archive/structure_detector_divergences/` under a synthetic project tree (with a fake `pyproject.toml`).

## Out of scope

* The loader does NOT canonicalise the regime label to A5's `bullish/bearish/transitional` taxonomy or A3's `trending_bull/trending_bear/range/...` taxonomy in `load_structure_log_rows`. That's the consumer's choice. `build_h4_regime_index` applies A3's normalisation; A5's `_select_regime` applies A5's.
* The loader does NOT compute H4 boundaries, run binary search, or maintain the per-symbol time-sorted index — those are A5 concerns layered on top in `regime_matrix.py`.
* The loader does NOT touch production code. Both `stratification.py` and `regime_matrix.py` are research-only modules.
