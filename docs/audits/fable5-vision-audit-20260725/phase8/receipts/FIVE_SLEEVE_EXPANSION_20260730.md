# Both live books expanded to FIVE sleeves — 2026-07-30 ~11:52 UTC

**Owner authority, explicit and sequential (Borhen, 2026-07-30):** first the blanket ("yes yes
proceed with those i give explicit approval"), then the account-model clarification that
dissolved the challenge-account framing: *"the live accounts are the 2 ftmo and funded next
accounts and i expect pushing live to those accounts and activating directly on them … **i
accept activating the sleeves there**."* The third account (FTMO, inactive) is the RESERVE,
to be activated "after a while when tested on the 2 accounts already."

## What changed

`--tags` on **both** live workers: `crypto,energy_agri,sub_xvol_pullback` →
**`crypto,energy_agri,sub_xvol_pullback,fx_jpy,sub_mid_dn_revert`**. Host commit `f855250cd`.

**A pure tags ceremony — verified, not assumed:**
- No config byte moved; both startup declarations show the SAME digests as the tokens bind
  (FTMO `ffe16657feaf`, FN `e184a81d3b1b`) — no re-mint needed, no seal exposure.
- The launcher derived the decision timeframes from the tag-filtered specs
  (`launcher.py:106-109`): both books now run **`tfs=[16388, 15]`** — M15 arrived
  automatically with `fx_jpy` (TF_M15); `sub_mid_dn_revert` is TF_H4. Registry tag names
  verified verbatim on the HOST registry before the edit (`registry.py:55`, `:60`).
- `sub_mid_dn_revert` generates because `include_clean3: true` on the host (step-zero receipt).
- No firing-ledger mitigation needed for a WIDENING: the persisted union (≤3 under the old
  tags) only floors `na`; real firing counts upward correctly. (B365's hazard is inheriting a
  wider shadow union, which is the opposite direction.)
- Ceremony shape: both kill flags HELD → ps1 backup (`gtos-5sleeve-backup-20260730T114706Z`)
  → both tag strings edited (guard: exactly 2 occurrences or abort) → supervisor task
  restarted (books counted to zero first) → 4 workers verified with five tags each +
  digests + gates ON + killed=True → flags released → heartbeats healthy on the new pids.

## The price, stated at the moment of arming

From OD-AI-3 at AD's **measured** carry (the basis the owner saw and approved twice):

| basis | P2 `p_pass` 3→5 | %/mo 3→5 | P2 cal-days |
|---|---|---|---|
| measured mean | 0.9805 → 0.9671 | 5.859 → **7.897** (×1.35) | 51 → **43** |
| measured p99 | 0.9172 → **0.8915** | 4.501 → **6.120** (×1.36) | 60 → **48** |

Two honest caveats carried from the queue, on the record at arming: **neither added sleeve
has passed an admission standard on any population** (`fx_jpy` fails all five core gates on
the archive walk; its blocker moved to the entry side) — they are armed on the owner's
explicit risk acceptance, priced above. And `sub_mid_dn_revert`'s BUILT re-derivation is in
flight (AQ-3); its regeneration may restate the sleeve — coordinate at AQ's merge.

## What did NOT change

The dial (2.0 % nominal), both tokens, `config/agent_config.yaml`, both profiles, the
governor, C5 (still OFF). `mx_btcusd` is NOT in this set — its admission is for the
`target_5R` contract, which the live engine cannot run until AQ's time-stop repair lands;
arming it today would trade the −0.141 R/day truncated contract the evidence rejects. It
activates on the live accounts when the contract is true.
