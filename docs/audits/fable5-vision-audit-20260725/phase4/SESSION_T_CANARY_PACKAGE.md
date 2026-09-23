# Session T — make the canary observable and survivable

**Stage 4.** Worktree `worktrees/wave4-canary-package-20260729`, branch `phase4/canary-package`,
from `main`. **Blocks B320–B349.**

**Read `../WAVE_4_WORKING_AGREEMENT.md` first** — especially §3.

---

## The situation you are building for

**A live funded FTMO account is being armed on three sleeves at the 2.0 % dial, right now.** Borhen
has explicitly accepted the risk, explicitly declined automatic stop conditions, and said he will
follow it himself.

Take that at face value — **you are not being asked to build brakes.** You are being asked to make
"follow it himself" into something a person can actually do, and to prove the safety layer holds when
things go wrong. Every automatic-halt instinct you have should become **an alert to him** instead.
He decides when to stop; the system's job is to make sure he *knows*, in time, with the right number.

## What exists, and what does not

**Exists:** `TOKEN_CHAOS_DRILLS.md` — 8 drill specs, marked **"Written, not run. Stage 4 runs them."**
The activation-token layer itself landed on the VPS on 2026-07-29 and was behaviourally probed there:
9 request classes, `authorize_broker_mutation` raised on **0 of 9**, exposure-increasing refused
without a token, risk-reducing allowed **including when the broker position read fails**.

**Does not exist:** pre-registered stop conditions of any kind, and any monitoring the owner can read.

**And this is the one that should worry you:** the audit's standing finding is that **nothing monitors
the gate.** `ultimate_book_live_activation_allowed` is a YAML boolean on a running funded host, and
until 2026-07-28 the only process that could page a human — `.tools/monitor_books.py`, which carries
`gate_tripwire()` — **could not deliver an alert at all.** It was granted at integration (B186) on
mainline. The VPS is running an older build that does deliver. **Verify rather than assume**, and
assume nothing about which build is where.

## What you own

**1. Run the eight chaos drills.** Gate-flip-without-token, expiry mid-position + fetch error, dir
unreadable, clock skew, revoke-restore, wrong Windows user, and the two others in the spec. Run them
**locally against the mainline token layer** — you cannot reach the VPS. Report which pass, which fail,
and which cannot be run locally at all and why.

The one that matters most: **an expired or revoked token must never strand an open position.** The
design says risk-reducing requests pass without a token — closes, partial closes, pending cancels,
stop tightenings — and the VPS probe confirmed a close survives even a *failed* position read. Attack
that. If there is any path where a position cannot be closed, that is the single most important finding
you could produce, and it outranks everything else in this prompt.

**2. Build the owner-facing view.** He is the monitor. Today he has a terminal and 160 MB of JSONL.
What he needs, at minimum, is: **is it armed; did it trade; what did it cost versus what we predicted;
how much drawdown headroom is left; and is the book still exactly three sleeves.**

That last one is not paranoia. The config could not express a three-sleeve book at all until a
confidence floor was added on 2026-07-29 — before that, "core-8 only" would have traded `idxrev` and
the two JPY sleeves, which are precisely the sleeves measured as dead (`fx_jpy` −0.453 R gross,
signal-level p 0.0059). **A silent reversion to eight sleeves is a realistic failure mode**, and it
would look like normal trading.

Design for how he actually works: he is not going to run a dashboard server. Prefer something that
renders to a file or prints a page.

**3. Pre-register evidence-based stop conditions — as alerts, not halts.** The plan asks for
*"pre-registered evidence targets and evidence-based stop conditions, not only loss limits."* The
sharpest one available: **measured cost deviation from `BROKER_TRUE_COSTS_V1.json` over n fills.**
The entire activation case rests on that cost table being right — `cost_r` predicted 175 live fills to
a mean absolute error of **0.000535 R**, against a shipped model whose error *is* 0.0591 R because it
charges zero. If live fills start deviating materially, the re-cost is wrong and the book's economics
are wrong with it. That should reach him **fast**, and it is measurable from the first handful of fills.

Second: **sleeve-level tripwires of the JPY kind.** The JPY cluster was 37.4 % of the live net loss and
was negative *gross* — a genuine kill of two sleeves that took a fortnight and a forensic session to
see. A tripwire that surfaces it in days is worth more than one that is statistically pure.

## Numbers you will want — treat every one as a claim to verify

- FTMO: balance **$107,872**, high-water $107,881, **flat**, static DD floor **$90,000** →
  headroom **$17,872**. Phase 1, target 10 % = $110,000, so **~1.97 % to clear.**
- redacted_account: **$96,229**, −3.5 % from high-water, headroom **$6,229**, governor already at
  `size_cap_multiplier 0.622928 — derisking_into_maxdd_wall`. **Not being armed.**
- Armed book: `metals_core` (conf 1.00), `crypto` (0.85), `energy_agri` (0.80), at 2.0 % nominal —
  `vol_scale` makes effective risk **~0.85–0.96 %**, not 2 %.
- Firm rules differ and are not interchangeable: FTMO daily loss is 5 % of **Initial Capital** reset
  **00:00 CE(S)T**; redacted_account is 5 % of **Initial Balance + today's realized profit** reset **00:00
  server time**. Never hardcode +3 for the server clock — it is `America/New_York + 7 h` on the **US**
  DST calendar, measured, and `src/utils/broker_clock.py` fails closed on an unregistered server.
- Expect **~7 book-days a month**. Long silences are the normal state, not a fault — the three armed
  sleeves fired **zero times** across the entire 38-day live window and that is consistent with their
  natural frequency (empirical P(0) 0.369 / 0.284 / 0.638). **A monitor that alarms on silence will
  cry wolf continuously.** A monitor that never mentions silence will hide a genuinely dead book.
  Resolving that tension is real work, and Session P's `ultimate_book_packet_silence_alarm.py`
  (calibrated against the live export) is prior art worth reading.

## Method

Commission refuters and default them to "refuted". Attack your own alerting hardest: **an alert that
does not fire is indistinguishable from all-clear**, which is exactly how `monitor_books` sat mute.
If you build a check, prove it goes red — a test that only ever sees green has tested nothing.

Use your own judgment on scope, on what the owner actually needs, and on whether anything above is
wrong.
