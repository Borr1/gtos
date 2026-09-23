# GTOS

GTOS is a trading system you run on your own MetaTrader 5 account. You bring the account. You bring the Jev key. The code reads the market's facts and asks Jev what to do with them.

**11 and 19 are the only two constants in the whole system.** Everything else is decided live by Jev from the market's own facts.

This repository is a public projection of a private source. The file `ORIGIN_SHA` names the Origin commit it was built from. The live host does not pull this repository.

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

The account identity in a profile is `broker_profile.expected_account.login_sha256`. `src/utils/broker_profile.py` defines that digest as SHA-256 of the login string, UTF-8 (`sha256_text`). The mint tool reads the digest from the profile. It does not take the login.

Put your own digest in your own profile. Point the process at your own terminal. The shipped `config/profiles/operator_profile.yaml` is a blank contract for that, with the live digest removed.

## Your Jev key

`src/judgment/jev_client.py` takes the first non-empty key from:

- `TYPESAFE_API_KEY`
- `TYPESAFE_KEY`
- `TYPESAFE_KEY_FILE`
- `~/.config/typesafe/api_key`
- `/run/secrets/TYPESAFE_API_KEY` or `/run/secrets/TYPESAFE_KEY`

Keep the key on the machine. It does not belong in git. `GTOS_JEV_A1_CALL=0` turns the calls off.

## The activation token

The token is the account owner's switch. `RealMT5.order_send` refuses a request that would increase exposure when the token is missing, mismatched, or bound to different config bytes. Closes, partial closes, pending cancels, and stop tightenings do not need a token.

`scripts/gtos_activation_token.py` mints, reads, and revokes tokens. It does not connect to the broker. A mint can bind `config_digest_sha256`, which is the SHA-256 of the raw bytes of the base config file plus the active profile file (`config_digest_for` in `src/safety/activation_token.py`). Edit those files and the old token no longer matches. Mint again.

Run the book and read what it would do. Mint when you want new exposure on your account.

```bash
python3 scripts/gtos_activation_token.py status
python3 scripts/gtos_activation_token.py mint \
  --profile operator_profile \
  --namespace operator \
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
