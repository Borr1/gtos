# OTI2 Fill/Path Source Search Ledger

Needed symbol-dates: `['GBPJPY|2026-05-04', 'GBPJPY|2026-05-06', 'NAS100|2026-05-04', 'USDJPY|2026-04-17', 'USDJPY|2026-04-20', 'USDJPY|2026-04-30', 'USDJPY|2026-05-01', 'XAUUSD|2026-05-05', 'XAUUSD|2026-05-06']`.
Conclusion: All accepted-label rows have source-authorized ordered events from OTI1/OTI3. The original OTI2 row remains exactly blocked by side-aware tick coverage gaps, and the four OTI3 same-timestamp rows remain blocked by same quote-row ordering impossibility.

Searched current worktree anchors, absolute main data/tick roots, shadow-log roots, and targeted prior worktree artifacts under `C:\tmp\gtos_otb`.
