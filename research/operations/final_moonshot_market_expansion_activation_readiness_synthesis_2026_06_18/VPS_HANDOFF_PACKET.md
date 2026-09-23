# VPS Handoff Packet - Market Expansion Readiness

Local Mac decision: `MARKET_EXPANSION_ACTIVATION_READINESS_SYNTHESIS_READY_DEFAULT_OFF_NOT_PROMOTED`.

Do not activate from this packet alone. First verify the exact commit set, run route verifiers, confirm active config boundaries, and keep market expansion default-off unless the owner explicitly approves promotion.

Required local verifier commands before any VPS-side interpretation:

```bash
python3 research/operations/final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18/verify_market_expansion_activation_readiness_synthesis.py
python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18 --full-jsonl
pytest tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py -q
```

Promotion remains closed until explicit session authority, exact fill authority, commission schedule or accepted family-transfer rule, exact swap/holding model, VPS packet parity, monitoring, rollback, and owner approval are complete.
