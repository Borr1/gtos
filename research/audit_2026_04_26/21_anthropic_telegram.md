# AUDIT 21: ANTHROPIC-TELEGRAM (SDK integration)

## Anthropic SDK: anthropic>=0.87.0 pinned

## 5 call sites
1. Primary Analyzer (Sonnet 4.6 effort=max with cache_control ephemeral)
2. Debate Engine (claude-sonnet-4-6, no cache)
3. Adaptive Review (claude-sonnet-4-20250514 STALE MODEL NAME)
4. Devil's Advocate (claude-sonnet-4-6 shadow)
5. M5 Refinement (claude-sonnet-4-6)

## Caching
- Ephemeral cache active in Primary Analyzer (~70-80% hit rate, $12-15/mo savings)
- Debate/Adaptive don't cache (low priority candidates)

## Telegram
- stdlib urllib HTTP (notifications.py:72-97)
- 6 production templates + C.3 SPRT halt template
- Bot in Claw Empire codebase (separate)

## Failure handling
- Anthropic robust (1-2 retries, NO_TRADE on exhaustion)
- Telegram fire-and-forget (alerts lost on process crash — MEDIUM concern)

## Cost tracking
- Token usage in `_last_usage` but no per-call $ logging

## Issues
- Debate model timestamp drift
- No graduated spend alerts
- Telegram delivery non-persistent
