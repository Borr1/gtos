# Live Monitoring Handoffs

Operational handoffs for live GTOS monitoring sessions.

Use these when the next session's job is to watch active kill zones, verify live process health, inspect MT5 positions/orders, and diagnose live-session anomalies. These are separate from `.context/02_session_handoffs/`, which is mostly research and engineering continuity.

Recommended startup order for live monitoring:

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the newest file in this folder.
3. Read `.context/00_core/quick_reference_card.md`.
4. Check `git status --short`; assume unrelated dirt may belong to another active session.
5. Verify MT5 positions/orders, internal pending intents, orchestrator/tick daemon duplicate counts, and fresh logs before judging market behavior.

Do not edit or delete runtime logs, shadow logs, cache files, or another session's research files unless explicitly instructed.
