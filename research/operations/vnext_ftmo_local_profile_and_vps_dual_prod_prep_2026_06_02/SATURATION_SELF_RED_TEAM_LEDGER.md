# Saturation And Self-Red-Team Ledger

Generated: 2026-06-01T18:01:51.710830Z

- Local FTMO MT5 facts captured: terminal/account, full symbol inventory, 24-symbol alias map, symbol specs, sessions, spread samples, cost fields, history/tick depth samples.
- Active 24-symbol alias unresolved count: 0.
- Same-evidence-class repairs performed: selected non-visible symbols for read-only metadata/history capture and restored their previous visibility state; generated account-specific profile; patched terminal/account namespace helpers; generated verifier/tests/templates.
- redacted_account alias leakage guard: profile verifier rejects NDX100, GER30, UKOUSD, USOUSD, and unqualified index/oil aliases in FTMO active profile.
- Collision prevention: namespace is required for locks, checkpoints, pending intents, M1/tick roots, broker truth logs, trade records, Telegram queue, and process groups.
- Remaining exact requirements:
  - exact_full_history_depth_beyond_capture_cap: optional_extended_export_requirement_not_alias_spec_blocker -> rerun builder with larger --history-bars or use VPS MT5 export for exact full-depth inventory
  - vps_production_authority_rebase: vps_only_finalization_requirement -> export/inspect VPS current production repo, active process commands, terminal paths, accounts, locks, logs, and supervisor before dual-live activation
  - owner_account_stage_and_addon_confirmation: owner_input_required_before_activation -> confirm FTMO account phase/stage, swing/add-on status, and any dashboard-specific constraints not exposed by MT5
