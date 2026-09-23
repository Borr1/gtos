# Observe-only preflight

The previous checklist in this file is retired. It told you to set
`ANTHROPIC_API_KEY`, call `claude-opus-4-20250514`, and start
`python3 -m src.components.orchestrator`. That is not this system. Do not
follow it.

The current first run is in the README. This is the same list, as checks.

## Machine

- [ ] Windows, with the MetaTrader 5 terminal installed and logged into your account
- [ ] Python `>=3.11` and `python -m pip install -r requirements.txt`
- [ ] You are not trying to run the live book on macOS or Linux

## Your profile, not the owner's

- [ ] `config/profiles/myaccount.yaml` is a copy of `myaccount.example.yaml`
- [ ] `login_sha256` is the output of `python scripts/gtos_account_digest.py YOUR_LOGIN`
- [ ] `server`, `terminal_path`, and `terminal_data_path` are your terminal
- [ ] The four `ultimate_book_*` gates in that profile are still false
- [ ] `--tags` is one sleeve you chose, not the owner's `crypto,energy_agri,sub_xvol_pullback`, and not an empty string
- [ ] Symbols you care about are listed under `instruments`, with the broker's `mt5_symbol`

## Key and token

- [ ] `TYPESAFE_API_KEY` is set from the TypeSafe dashboard. It is not in git.
- [ ] No activation token has been minted yet

## One tick

```bash
python run_book.py --profile myaccount --namespace myaccount --once --tags your_sleeve
```

- [ ] The bridge reason is `ultimate_book_disabled_by_config`
- [ ] The terminal shows no new position
- [ ] You did not run `scripts/run_book_supervisor.ps1` unchanged

Mint a token only after you have turned the four gates on in your own profile
and you want new exposure. Until then, a request that reaches `order_send`
must log `Order REFUSED by the activation gate` with `activation_token_absent`.
No such line means nothing reached the broker.
