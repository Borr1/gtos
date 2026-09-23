# Session CL supervisor-argument diff — exact no-op

Decision: **STOP AFTER PREFLIGHT; MUTATE NOTHING.** The exact file-byte, hashtable-key and worker-argument diffs are all the empty set.

| account | hashtable-key delta | `--tags` before → after | `--frontier-exits` before → after | `--spread-geometry-floor` before → after | derived `tfs` before → after |
|---|---|---|---|---|---|
| FTMO | `∅` | `crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout` → same | `mx_btcusd_d1_donchian_20_breakout` → same | `sub_mid_dn_revert,sub_xvol_pullback` → same | `[16388, 16408]` → same |
| redacted_account | `∅` | `crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert` → same | `ABSENT` → same | `sub_mid_dn_revert,sub_xvol_pullback` → same | `[16388]` → same |

The host supervisor is a fork whose full current bytes and spread-floor field name were not
committed back to this repository. `capture_host_preflight.ps1` therefore records the actual
`$books` block, its hash and every hashtable key from those bytes. Because the authorized diff
is empty, exactness does not depend on guessing the field name: the full block must compare
byte-for-byte equal in preflight and postflight. The live worker command lines remain the
behavioural authority and are checked against the selections above.

An empty `--tags` is not an empty book; it selects all built sleeves. An all-typo non-empty
selection is a mute book. `verify_pass_surface.py` refuses both by requiring the exact,
non-empty strings and their independent `BookLauncher starting: tfs=...` lines.
