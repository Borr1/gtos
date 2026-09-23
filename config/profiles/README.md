# Profiles

A profile is a deep-merge overlay on `config/agent_config.yaml`.
`--profile` on the command line wins over `GTOS_PROFILE`. With neither, the
base config is used alone.

## Start here

| File | What it is |
|---|---|
| `myaccount.example.yaml` | The newcomer overlay. Copy it to `myaccount.yaml`. The four live gates are false: that is the owner's arming switch, not a limit. Size is not set. Jev scores it from the account's own facts, and an empty score leaves it unset. The login digest is the placeholder `REPLACE-ME`. |
| `operator_profile.yaml` | The owner's captured account. Not a template. |
| `ftmo.yaml` | The owner's compatibility pointer for that same captured account. Not a universal broker template. |
| `denominator_capture_research.yaml` | Research logging. `trading_enabled` is false. Not a trading profile. |

There is no `redacted_account.yaml` in this tree. Commands that name `run_agent.py --profile redacted_account` are obsolete. The first run is `run_book.py --profile myaccount`, and the steps are in the README.

## Your own profile

Copy `myaccount.example.yaml`. Fill `login_sha256` from `scripts/gtos_account_digest.py`. Point `terminal_path` and `terminal_data_path` at your MetaTrader 5 terminal. Set `server` to the server the terminal shows. Add an `instruments` block for each canonical symbol you want, with `market.mt5_symbol` set to the broker's name.

Do not start by editing `config/agent_config.yaml`. Its bytes, and the bytes of the active profile, are what an activation token can bind. Change your profile, then mint again.

## The owner's paths

The owner's profiles name the owner's terminals and namespaces. Those paths are not yours. A newcomer profile does not use them.
