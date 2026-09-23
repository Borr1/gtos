---
name: feedback-queue
description: One append-only queue for redacted_account_bot messages and public Borr1/gtos issues and discussions. Use when feedback, the Telegram bot, or that queue is involved.
---

# Feedback queue

`redacted_account_bot` is the public intake. `gold_trader_os_bot` is the trading notifier. Do not call getUpdates or setWebhook on the trading bot. A second poller steals or drops updates.

The intake is its own process, `scripts/feedback_intake.py`. It is not imported by `run_book.py`. Do not restart a book writer to load it.

Host root on the VPS: `host-local\.gtos\feedback`. Queue: `queue.jsonl` there. Token file: `redacted_account-bot.token` (one line). Chat ids stay in that directory. The Mac mirror copies only `queue.jsonl` to the coordinator store `internal/feedback/queue.jsonl` and replaces the file. Do not append that store file from two hosts.

A Telegram 429 waits on Retry-After and retries the same call. The item is fsynced before the offset advances. The sender gets `Received fb-########`.
