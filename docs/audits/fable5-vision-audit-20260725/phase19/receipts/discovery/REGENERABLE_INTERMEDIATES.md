# What is deliberately NOT committed here

997 MB of artifacts were produced by three swarms (46 agents). ~5 MB is committed: every `.md`
receipt, every `.py` script that produced a number, all result JSONs under 5 MB, and
`w0_WORKING_SET.jsonl.gz` (the shared substrate every lane read).

Left untracked, because each is regenerable from a committed script plus the pools:

| file | size | regenerate with |
|---|---:|---|
| `L8_SWEEP3_V1.json` | 76 MB | `l8_*.py` |
| `h6_ATMKT_PATHS.npz` | 76 MB | `h6_*.py` |
| `e5_{january,february,march}_WS_V1.jsonl.gz` | 79 MB | `e5_*.py` |
| `h5_SUBSTRATE_5M.jsonl.gz` | 28 MB | `h5_*.py` |
| `x5_FRAME_JAN.npz`, `x3_TAPE.npz` | 52 MB | `x3_*.py`, `x5_*.py` |
| `l11_{SUBSTRATE,ALIGNED,ALIGNED_STRICT}_V1.npz` | 73 MB | `l11_*.py` |

They remain on disk in this worktree. Nothing unique is lost by their absence from git; the
`.git` store is already 42 GB of LFS evidence and does not need another 990 MB of derivable frames.
