# redacted_account max-drawdown kind — RESOLVED: static from initial balance

**The one captured page AI §3.1 asked for.** Checked 2026-07-30 against redacted_account's own
help center (`help.redacted_account.com/en/articles/8019915-what-is-the-maximum-overall-loss-limit`):

> "Traders are allowed a maximum loss of 10% of their initial balance"

applies to **Stellar 2-Step** (and Evaluation/Express) — a **STATIC floor** ($90,000 on a
$100k account), not a trailing high-water mark. The only trailing variant in the product
line is **Stellar Instant** (6 %, trails equity HWM, caps at initial) — not our account
model.

**Independent confirmation from our own runtime:** the carried monitor's DD headroom for
the live FN account reads `eq $96,229 | DD headroom $+6,229` — exactly $96,229 − $90,000,
i.e. the static-initial floor, from the firm-true rules Session Q measured.

## Consequence

`BOOKS_MC_V1.json`'s redacted_account figures were computed at the static rule, so **the
published ranking stands with its caveat removed**: armed-three P2 `p_pass` **0.9331
redacted_account ≥ 0.9172 FTMO** (fwd 2025+, worst carry). The "inverts if redacted_account's max-DD
is trailing" branch (AI §3.1, CLAUDE.md §4) is dead.

**OD-AI-2 (arm redacted_account on the same three sleeves) is now a pure owner yes/no** — no
unknown blocks it. If yes, the mechanics are a repeat of FTMO's ceremony: mint an FN token,
flip the three profile-level gates, set `--tags`, release `ULTIMATE_BOOK_KILL_fn.flag` —
at a decision-day boundary per the B365 firing-ledger hazard.
