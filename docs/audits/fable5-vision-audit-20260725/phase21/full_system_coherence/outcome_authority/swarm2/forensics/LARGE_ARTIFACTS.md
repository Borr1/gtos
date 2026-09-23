# swarm2/forensics — large artifacts held out of git

CLAUDE.md §8 sets the inline non-LFS blob threshold at 5 MB and records that 4.8 GB of the
tracked tree already sits in 280 such blobs. These four files are above the threshold, are
fully regenerable from committed builders plus the sealed corpus, and are therefore excluded
by `.gitignore` and recorded here instead. This file is the pointer; the bytes are local.

Verify any of them with `shasum -a 256 <path>`.

| path (relative to this directory) | bytes | sha256 | regenerate with |
|---|---:|---|---|
| `f1_excursion/F1_TRADE_EXCURSION_CENSUS_V1.parquet` | 58,609,264 | `e173e7b7a6860f47ca0a86d300bf489567b875494f4ce4bb389385283c4c7b59` | `f1_excursion/f1_walk.py` then `f1_excursion/f1_artifact.py` |
| `f4_accuracy/f4_new_features.pkl.gz` | 25,697,345 | `2736d876fcf3157e16ca17d9842c8c79976a45aac915ee08fc04743287ea04be` | `f4_accuracy/f4_newfeatures.py` |
| `f4_accuracy/f4_excursion_join.pkl.gz` | 9,034,715 | `caf0dc4c7635c8cdea947bb9c6ab4ea3ca53448b7398f64b89b5b30851c7fdd1` | `f4_accuracy/f4_census.py` |
| `g2_replay/receipts/G2_M1_ROWS.json` | 7,130,330 | `60e5c126a959d02f1a2d13b1d970c46f6999f0a8ff66edb86724fe951547bd56` | `g2_replay/aggregate_restate.py` |

## What survives without them

The committed aggregates carry every published figure. `f1_excursion/F1_CENSUS.json` (244 KB)
and `F1_SUPP.json` (20 KB) hold the census, near-miss ladder, hit-rate ladder, cost
decomposition and cell statistics that `F1_EXCURSION_CENSUS_V1.md` reports; the parquet is
needed only to re-cut the population along an axis nobody has asked for yet. The same holds
for the F4 and G2 pickles against their own `receipts/*.json`.

## The one thing the parquet is worth keeping locally for

`F1_TRADE_EXCURSION_CENSUS_V1.parquet` is the only per-trade excursion corpus this programme
has ever built (146,736 rows × 158 columns). The estate re-derived per-trade MFE roughly 1,631
times inside AD's exit sweep and persisted none of it, and `AA_ESTATE_TRADES.json.gz` has held
22,324 unmined MFE/MAE rows since wave 6. Rebuilding costs a full walk of five sealed months.
Do not delete it to reclaim disk; if this worktree is retired, move it to the evidence hold at
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/` first.
