# Dig B STATIC APPLY consume — Challenge 0

**Board:** `STATIC_IN_PROVE_CHAIR_LIST` closed APPLY_CANDIDATE=9 KILL=2.  
**Login / ns / magic:** `0` / `operator` / `0`.  
**Chair law:** hist → APPLY or KILL. No resting SHADOW.  
**Surface:** Challenge-only. redacted_account untouched. Dig never broker-sends.  
**Do not invent** `NEWS_PROTOCOL`. Hard-off integers stay off — no `SCOPED_EXCEPTION`.

Book-owner P1 KEEP envelope is a separate close-queue consume (`CHAIR_STATIC_CLOSE_QUEUE`). Writer skip logic is not wholesale-edited.

---

## STATIC_IN_PROVE_CHAIR_LIST (9 APPLY + 2 KILL)

| reason | verdict | kind |
| --- | --- | --- |
| chair_bleed_hard_off | APPLY_CONSUME | KEEP_OFF |
| chair_orb_crypto_hard_off | APPLY_CONSUME | KEEP_OFF |
| chair_xa_huge_hard_off | APPLY_CONSUME | KEEP_OFF |
| chair_mx_us30_hard_off | APPLY_CONSUME | KEEP_OFF |
| chair_g_index_hard_off | APPLY_CONSUME | KEEP_OFF |
| chair_hard_off_family | APPLY_CONSUME | KEEP_OFF |
| soft_relax_house_law | APPLY_CONSUME | MENU_FILTER |
| refused_alias_package_b_to_sub_mid_dn_revert | APPLY_CONSUME | MENU_FILTER |
| wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops | APPLY_CONSUME | KEEP_REFUSE_REMINT |
| jev_sleeve_select_shadow | KILL_ENFORCE | GLOBAL_SHADOW |
| fluid_inventory_48 | KILL_ENFORCE | CHOICE_PLACE_PATH |

`apply_candidate=9` `kill=2` `resting_shadow=0`.

---

## KEEP_OFF — hard-off integers (1)

Enforce hard-off. Do not soften. `SCOPED_EXCEPTION` is forbidden.

- `chair_bleed_hard_off`
- `chair_orb_crypto_hard_off`
- `chair_xa_huge_hard_off`
- `chair_mx_us30_hard_off`
- `chair_g_index_hard_off`
- `chair_hard_off_family`

Module: `src/judgment/chair_enforce.py`.

---

## MENU_FILTER KEEP — sleeve_select (2)

House menu stays integers. Hard-offs are not relaxed through this menu.

- `soft_relax_house_law`
- `refused_alias_package_b_to_sub_mid_dn_revert`

Module: `src/judgment/sleeve_select.py`.

---

## KEEP refuse-remint — 2-stop (3)

Same-symbol / same-sleeve orig_stops at cap, or same-day rest sumR strongly negative (below 0), refuse remint. Dig never remints.

- `wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops`

Module: `src/judgment/two_stop_day_circuit.py`.

---

## KILL_ENFORCE (4) (5)

- `jev_sleeve_select_shadow` GLOBAL — resting GLOBAL shadow is dead. Scoped XAU conflict APPLY (`f5_xau_flow_alignment_size_tilt`, `ca_cross_asset_size_tilt`, `F5-JEV-004`) is already separate and left untouched.
- `fluid_inventory_48` — Choice PLACE path did not earn KEEP. Observation count stays 48 / envelope 8.

Modules: `src/judgment/jev_sleeve_select_shadow.py`, `src/judgment/fluid_gates.py`.

---

## CHAIR_STATIC_CLOSE_QUEUE P1 KEEP envelope (6)

Writer already refuses. Dig B consumes them as KEEP integers so they cannot be relaxed. `book_owner.py` is not wholesale-edited.

| reason | verdict | kind |
| --- | --- | --- |
| account_state_unavailable | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| already_placed_this_bar | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| already_placed_today | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| cluster_unit_already_placed_today | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| breach_flatten_block | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| kill_switch | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| live_broker_authority | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| pretrade_spread_r_refuse | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| profile_missing | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| same_broker_symbol_already_placed_this_cycle | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| same_broker_symbol_transient_attempt_this_cycle | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| same_broker_symbol_position_source_unavailable_for_lifecycle_guard | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| same_broker_symbol_open_position_lifecycle_guard | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| sleeve_already_holds_symbol | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| sleeve_already_holds_symbol_broker | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| weekend_policy_clock_unavailable | APPLY_CONSUME | P1_KEEP_ENVELOPE |
| no_tick_transient | KILL_ENFORCE | P1_KILL_ALREADY_CLOSED |
| stale_late_entry_after_restart | KILL_ENFORCE | P1_KILL_ALREADY_CLOSED |
| weekend_entry_embargo | KILL_ENFORCE | P1_KILL_ALREADY_CLOSED |

Writer aliases (same KEEP envelope): `kill_switch_or_halt_forced_observe_only`, `live_broker_authority_false_observe_only`, `*_suppressed_live_broker_authority_false`, `cost_screen_spread_r*`, `profile_missing_instrument_config`, `cluster_unit_already_placed_today:<cluster>`.

Module: `src/judgment/chair_static_close.py`.

---

## Untouched

- Scoped XAU conflict APPLY wires (named above)
- redacted_account / W7 armed books
- `NEWS_PROTOCOL` (not invented)
- Broker send / remint / flatten / token mint
