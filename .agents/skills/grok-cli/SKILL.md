---
name: grok-cli
description: Live GTOS work runs in visible Grok CLI sessions on the Mac or the VPS. Use this instead of doing the hop in the coordinator chat, and instead of CreateAgent, when Borhen asked for grok CLI.
---

# Grok CLI sessions

Borhen, 2026-09-22: use Grok sessions with the CLI on the VPS or the Mac. The Mac windows are the surface he watches. Do not do the live hop in the coordinator. CreateAgent `grok-4.7-xhigh` is rejected on this launcher; do not open 4.6.

## Mac (default)

Door: `ssh -o ControlMaster=no -o ControlPath=none gtos-mac`.

Binary: `/Users/borr/.local/bin/grok`

Recipe already on disk: `/Users/borr/GTOSActive/gold-grok/launch/*.sh`

```
printf '\033]0;TITLE\007'
cd CWD || exit 1
exec /Users/borr/.local/bin/grok \
  --cwd CWD \
  --model grok-4.7 \
  --effort xhigh \
  --always-approve \
  --permission-mode bypassPermissions \
  --no-ask-user \
  --trust-folder \
  --no-alt-screen \
  --fullscreen \
  --sandbox off \
  --no-auto-update \
  --prompt-file /path/to/prompt.txt
```

Open a visible window:

```
osascript -e 'tell application "Terminal" to do script "exec /path/to/launch.sh"'
```

Put the prompt in a file. Do not pass a long prompt on argv. This CLI's highest accepted effort is `xhigh` (`low` `high` `medium` `xhigh`). `--effort max` was rejected 2026-09-22. Live code cwd is `/Users/borr/GTOSActive/jev-live-swarm`. Gold research cwd is `/Users/borr/GTOSActive/gold-grok`.

The Mac reaches the VPS with `ssh gtos-vps`. Host Python is the vps-python skill.

Whether a window is working is the verify-grok-sessions skill. Do not rebuild that check from the log format.

## VPS

Only when the hop has to sit on the host tree and a Mac window cannot. Binary: `host-local\.grok\bin\grok.exe`. `--model grok-4.7 --always-approve --sandbox off --prompt-file ...`. Do not steal CPU from MT5 if a Mac session can SSH in.

## Prompt

Start with the mission from `/cursor/stores/user/workflows/session-prompt.md`. A session that only reads has failed. One finite session, one hop, write it, compile it, load it on Challenge, then it can exit.
