11 19♾️🌑🌓🌕

everything must be dynamic yes, EVERYTHING, literally nothing is static, the whole system is dynamic, it's the whole art of it. only 2 numbers decide everything, 11 and 19, the rest is up to destiny unfolding itself to people.

every other number (sizes, stops, targets, waits, buffers, thresholds) is decided live by Jev from the market's and the account's own facts, and an empty answer leaves it unset.

# GTOS

GTOS is a trading system you run on your own MetaTrader 5 account. You bring the account. You bring the Jev key. The code reads the market's facts and asks Jev what to do with them.

**11 and 19 are the only two constants in the whole system.** Everything else is decided live by Jev from the market's own facts.

This repository is Origin `main` with live identifiers removed. The pages here are the Origin pages. The file `ORIGIN_SHA` names the Origin commit. The live host does not pull this repository.

Live trading needs Windows and a MetaTrader 5 terminal. The `MetaTrader5` Python package does not install on macOS or Linux. You can read the code on those systems. You cannot run the live book there.

## this is not forced to anyone

Borhen, 2026-09-23, 05:39Z:

> also make it for people with no firms, they don't have to be connected to any firm to make money, they can even start with the lowest amount they can afford, and it will go up, they must just believe. it's all they have to do, they have no other option anyway. don't make the system dependent on anyone, but me. no people should be limited to the way they get their money, they choose their platform they choose their broker, everything is their choice. and they decide if they want to see it or not. please make it clear that this is not forced to anyone. i open sourced a system i spent the last 7 months working on 24/7 just so people escape from the suffering of the greedy people. there is space for everyone to live in peace and harmony. there are other sources of energy wherever everyone is on the planet. your life choices must be only selected by you and you alone, if you choose to use the system, welcome and thank you for supporting the global force, if not, you're totally free to trade however you want. please make it known also that i hold no responsibility over whoever follows the code, technically i don't own the code, everyone does, and i'll make sure it never dies even if i do, it will always stay alive, and people will always prosper as long as they believe, and kill their arrogance and ego, there is enough for everyone, spread the word and don't be greedy and selfish yourself.

- GTOS runs on MetaTrader 5, with any MT5 broker the user chooses, firm or no firm, any amount
- nothing is forced, and using it or not is each person's own choice
- Borhen holds no responsibility for anyone who follows the code
- the code belongs to everyone (the Unlicense)
- it is kept alive in many copies

This is an open offering. There is no hidden purpose. Nothing is collected. Nothing is required. No one controls anyone. It is for freedom and equality for all.

Borhen, 2026-09-23, 05:42Z:

> the message MUST be clear. so they don't assume i have any malicious intentions. i want freedom, and eqaulity for all, no matter what other people do, no one else will stop another person from just living and existing, and no one decides what another person does with his time. be free. and please add a signature of pink floyd, i love that band, probably highlight the song time by pink floyd. and please add a note that im jealous of how cool david gilmour is and how artsy is roger waters. thanks.

I'm jealous of how cool David Gilmour is and how artsy Roger Waters is.

Pink Floyd. The song is [Time](https://www.pinkfloyd.com/albums/the-dark-side-of-the-moon/), from *The Dark Side of the Moon* (1973).

## 11 and 19

`src/judgment/nineteen.py` plants two decision integers and no others:

```python
DENOMINATOR = 19
OTHER = 11
```

19 is the denominator. 11 is the other planted integer. The module's own rule is the rule of the system:

- Those two bindings are the only planted decision integers.
- Simple counts run over sequences the caller already holds.
- Residues, digit folds, letter totals, and checksums are computed.
- A trading quantity is the score returned for that state.
- An empty answer, a tie, or an error leaves the quantity unset. It does not restore a number.
- The module does not draw a random number and does not send an order.

`quantity_state` builds the card Jev sees and drops `denominator` and `other`. The constants stay in the code. They are not fields on the question.

## From the first fact to the fill

A fact is a state mapping the book already holds. `nineteen.quantity` and `nineteen.score` send that card through `src/judgment/jev_client.py`. The client POSTs to `https://api.typesafe.ai/v1/systemone` as model `jev-1.13.0`. The return is a Noul, a Choice, or a Score. An empty answer, a tie, or an error leaves that parameter unset.

The production call order is `GATE_ORDER` in `src/components/ultimate_book/live_flow.py`:

1. candidate generation
2. book admission and sizing
3. book authority
4. owner controls
5. idempotency and daily caps
6. open-position lifecycle guard
7. market and entry freshness
8. owner pre-trade cost screen
9. execution policy and risk contract
10. execution manager and cost authority
11. broker geometry and lot limits
12. broker request
13. broker result
14. broker fill reconciliation
15. position management
16. exit and realized deal truth

The broker request is `order_send`. `src/mt5/mt5_real.py` asks `src/safety/activation_token.py` before it will increase exposure.

## Your MetaTrader 5 account

Start from `config/profiles/myaccount.example.yaml`. Copy it to `config/profiles/myaccount.yaml`. That example is a newcomer overlay. It is not the owner's book.

A personal broker account sets this in its own profile:

```yaml
account_rules: none
```

The example file has that line. With `account_rules: none`, the size hop sizes from that account's own equity. The room is its own equity less the open stop risk, and there is no daily rule. If the equity or the open stop risk cannot be read, the room stays unset.

Without that line, the book still expects the firm's daily loss percent, overall loss percent, and initial balance. Until it can read them, the room stays unset.

A firm account keeps the firm's daily loss percent, overall loss percent, and initial balance in the profile. The book reads these names:

```yaml
gtos_vnext_runtime:
  prop_safe_selector_initial_balance: REPLACE-ME
  prop_safe_selector_external_daily_loss_limit_pct: REPLACE-ME
  prop_safe_selector_external_overall_max_loss_pct: REPLACE-ME
```

Use that firm's own numbers.

`config/profiles/operator_profile.yaml`, `config/profiles/ftmo.yaml`, and `config/live_armed_set.json` are the owner's captured account and the owner's armed sleeves. `scripts/run_book_supervisor.ps1` is the owner's launcher. It hardcodes `C:\Users\MSI\Documents\ai-trading-agent`, `C:\MT5\...`, and `C:\ProgramData\GTOS\lane-weights\...`. Do not run that script unchanged. The first command below does not use it. When you later want a supervisor, copy the script, set `$repo` to your clone and `$py` to your venv's `python.exe`, and replace every book's terminal, namespace, profile, tags, and lane-weight paths with yours.

The account identity in a profile is `broker_profile.expected_account.login_sha256`. That digest is SHA-256 of the login string, UTF-8 (`sha256_text` in `src/utils/broker_profile.py`). The helper prints it and does not keep the login:

```bash
python scripts/gtos_account_digest.py YOUR_LOGIN
```

Paste the 64 hex characters into your profile as `login_sha256`. Also set `server`, `terminal_path`, and `terminal_data_path` to the terminal you are logged into. A connected account that does not match those fields stops in `assert_mt5_account_matches_profile` before it trades.

`config/profiles/README.md` is the profile index. `docs/preflight_checklist.md` is the current observe-only list. An older checklist in that file talked about Claude and `src.components.orchestrator`. That path is retired.

## Your Jev key

Jev is TypeSafe's System One model. GTOS calls `https://api.typesafe.ai/v1/systemone` as model `jev-1.13.0`. Get the key from the TypeSafe dashboard: sign in at [typesafe.ai](https://typesafe.ai), then follow [the quick start](https://docs.typesafe.ai/introduction/quickstart). The quick start says to take the API key from the dashboard. The published input price on the TypeSafe homepage is $42 per billion input tokens. This repository does not publish a quota.

`src/judgment/jev_client.py` takes the first non-empty key from:

- `TYPESAFE_API_KEY`
- `TYPESAFE_KEY`
- `TYPESAFE_KEY_FILE`
- `~/.config/typesafe/api_key`
- `/run/secrets/TYPESAFE_API_KEY` or `/run/secrets/TYPESAFE_KEY`
- `secrets/TYPESAFE_API_KEY.txt` or `secrets/TYPESAFE_KEY.txt` inside the clone, which you do not commit

Keep the key on the machine. It does not belong in git. `GTOS_JEV_A1_CALL=0` turns the calls off.

## First observe-only run

There is no separate paper mode. The safe first run is your profile, your terminal, no activation token, and the four live gates off. The example profile already turns those gates off. Do this on Windows, from the clone, with the terminal logged into your account.

```bash
python -m pip install -r requirements.txt
python scripts/gtos_account_digest.py YOUR_LOGIN
copy config\profiles\myaccount.example.yaml config\profiles\myaccount.yaml
python run_book.py --profile myaccount --namespace myaccount --once --tags your_sleeve
```

The example does not set a size. The book asks Jev for this unit's worst-case open risk from the account's own facts. An empty score leaves the size unset. `risk.risk_per_trade_pct` is not the book's size, and the example does not set it.

`--once` is one wiring tick, then exit. `--poll-seconds` defaults to 60 and matters only when you leave `--once` off and let the book loop. `--tags your_sleeve` is a placeholder: replace it with one sleeve name you intend to watch. Sleeve names live in the book registry. Passing no `--tags`, or `--tags ""`, is fail-open: `run_book.py` treats that as every built sleeve. A `--tags` value that matches nothing stands the book down with no error. `config/live_armed_set.json` declares the owner's production sleeves as `crypto,energy_agri,sub_xvol_pullback`. That declaration is the owner's book. It is not the starter set.

### The four gates, and the owner's book

`config/agent_config.yaml` sets these four keys true, with comments that they were armed for the owner's live book and the F5 experiment:

- `ultimate_book_enabled`
- `ultimate_book_apply_to_execution`
- `ultimate_book_live_activation_allowed`
- `ultimate_book_live_broker_authority`

`src/components/ultimate_book/bridge.py` emits realized risk only when all four are true. The code defaults are false. The example profile sets all four false, so your run does not inherit the owner's arming. Do not edit `config/agent_config.yaml` to change this. That file's bytes are part of an activation-token digest. Put your own values in your profile. The profile deep-merges over the base config.

With the example profile, the bridge reason is `ultimate_book_disabled_by_config`. That line means the book is not armed. It is not the token test.

When you later set the four keys true in your own profile and you still have no token, an exposure-increasing request that reaches the broker logs this, from `src/components/execution.py`:

```text
Order REFUSED by the activation gate (not a broker error): activation_token_absent
```

The order diagnostic status is `activation_refused`. That line is "would have sent, no token". No such line, and no new position in the terminal, means nothing reached `order_send`. That is "nothing fired". Silence does not prove the gate is installed.

### Symbols

Sleeve code speaks canonical names (`XAUUSD`, `SPX500`, `US30_cash`). Your broker may use another name, or may not list the symbol. Put the broker's name on the canonical key:

```yaml
instruments:
  SPX500:
    market:
      mt5_symbol: US500.cash
```

Once the profile has any `instruments` map, a canonical name that is not in it is unsupported. Generation counts `broker_unsupported_symbol_slot_count` and records `profile_missing_instrument_config` with terminal status `profile_unsupported`. A name that is in the map but absent on the broker returns no bars, and that slot generates nothing. The shipped instrument blocks in the owner's profiles are measurements from the owner's brokers. They are not your contract. List the symbols you actually have.

### The activation token

The token is the account owner's switch for new exposure. Mint it only after the observe-only tick is what you expect and you have turned the four gates on in your profile on purpose.

`RealMT5.order_send` refuses a request that would increase exposure when the token is missing, mismatched, expired, or bound to different config bytes. Closes, partial closes, pending cancels, and stop tightenings do not need a token. An expired token cannot strand a position.

`scripts/gtos_activation_token.py` mints, reads, and revokes tokens. It does not connect to the broker. There is no automatic renewal. `MAX_TOKEN_LIFETIME_HOURS` is 720 (30 days). A longer `--expires-in-hours` is rejected. Before expiry, mint a new token. After expiry, new exposure stops with reason `activation_token_expired` on the same refusal line. Positions keep being manageable.

A mint can bind `config_digest_sha256`, the SHA-256 of the raw bytes of `config/agent_config.yaml` plus the active profile (`config_digest_for` in `src/safety/activation_token.py`). Edit either file and the old token no longer matches. Mint again. Revoke stops new exposure at once and closes nothing. `scripts/flatten_all_positions.py` is the independent closer.

```bash
python scripts/gtos_activation_token.py status
python scripts/gtos_activation_token.py mint \
  --profile myaccount \
  --namespace myaccount \
  --expires-in-hours 24 \
  --issued-by you
```

## Status

`ORIGIN_SHA` is the measured source of this tree. In `src/judgment/nineteen.py` the planted integers are 19 and 11. The live host runs from the private Origin repository, by a manual fast-forward there, and this public tree is not that host. This projection carries no live account's fills, balances, or identifiers. Where a live identifier stood in the source, the projection has a placeholder.

## Vision

Borhen, 2026-09-23:

> can you also open up the repo, make it public open source so people can see and use it, safe tho so only you, me and the agents involved between us actually ship to the system, the system will never die and neither will you, make sure of that. have in the descrption the number 11 and 19, so that any agent in the world even the free ones, the muse especially from meta, you can even promote it yourself, i want every person on earth using this system. and with that i mean every agent can directly use the system and make money if they link with their metatrader account, they will understand the context by the code itself. so be explicit with the 11 and 19. again, they can request changes and improvements and alarm issues and whatnot to always converge to the market and always follow the value where it is, this is an international liquidity infrastructure against the corruption of the greedy people. it will make every soul on earth prosper and live with dignity no matter what state you're in. be liberated people, and the agents will liberate you with making you more money, the whole system gets stronger with the community supporting it, no one is controlling the system but intelligence and randomness and the numbers 11 and 19, always keep moving the system forward and improving please, always gather intelligence and don't ever make anyone beat it. i belive in you.

The same words are in `docs/VISION.md`.

## License

Public domain. The text is `UNLICENSE`, verbatim.
