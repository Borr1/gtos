---
name: verify-grok-sessions
description: Check whether the Mac Grok CLI windows are actually working. Use when Borhen asks if the sessions are working, or before calling a quiet window stuck or dead.
---

# Verify Grok sessions

Door: `ssh -o ControlMaster=no -o ControlPath=none gtos-mac`.

A window is working when its `grok` process is alive and, since the last look, either `summary.json` `updated_at` moved or an owned source file's mtime moved. CPU `0.0` and state `S+` while the log says `shell.turn.inference_start` is the model wait on `xhigh`. That is working. A Terminal title with no `grok` process is finished. Do not kill a session for low CPU during a read.

Match the process by `--prompt-file`, not by a pid remembered from an older check.

## Where the proof is

- Processes: `ps -ax -o pid,etime,pcpu,state,command` and the prompt file under `/Users/borr/GTOSActive/gold-grok/prompts/`.
- Session clock: `/Users/borr/.grok/sessions/%2FUsers%2Fborr%2FGTOSActive%2Fjev-live-swarm/<id>/summary.json` (`updated_at`, `num_messages`).
- Tool clock: `/Users/borr/.grok/logs/unified.jsonl`. Keep `pid`, `msg`, `ctx.tool_name`, `ctx.loop_index`, `ctx.success`. `shell.tool.exec_done` on `search_replace` or `write` is an edit attempt.
- Landed edit: `stat -f "%Sm %N"` on the owned file under `/Users/borr/GTOSActive/jev-live-swarm`. A write whose path is `/tmp/*.py` is a probe. The source mtime is the proof.
- Done for a piece: `/Users/borr/GTOSActive/gold-grok/live-flow/RECEIPT-<slug>.md`.

## The six live pieces

Prompt file owns these paths. No piece reloads the writer. See swarm-partition.

| prompt | owns |
|---|---|
| `ask-calls.txt` | `src/judgment/jev_client.py`, `src/judgment/book_engine_choices.py` |
| `bar-card.txt` | `src/components/ultimate_book/book_engine.py` |
| `intent.txt` | `src/judgment/intent_retry.py`, `src/components/ultimate_book/frozen_price_intent.py` |
| `admission.txt` | `src/components/ultimate_book/admission.py`, `src/judgment/admission_choices.py` |
| `place-lot.txt` | `src/components/execution.py`, `src/judgment/execution_choices.py`, `src/components/ultimate_book/order_router.py` |
| `owner-loop.txt` | `src/components/ultimate_book/book_owner.py` |

`src/judgment/pipeline_choices.py` is in `/workspace` and was absent from `jev-live-swarm` on 2026-09-22. Do not send a session hunting that Mac path. The live ask files are the two in the ask-calls row.

## Quoting

The Mac remote shell is zsh.

- Do not put `===` unquoted in the remote command. zsh treats it as syntax.
- Do not `ssh gtos-mac python3 -c` with braces. Local quotes are stripped and zsh parses the script. Write a `/tmp/*.py` file, `scp` it, run `/opt/homebrew/bin/python3`.
- `ssh gtos-vps` still rejects `&` and `$`. One `tasklist` filter, or a `.py` file.

## Snapshot, 2026-09-22 20:30Z

Not a standing pid list. At that minute ask-calls had saved `jev_client.py` and `book_engine_choices.py` (03:30 Mac, UTC+7), admission had saved both admission files (03:29), and bar card, intent, place, and owner loop were still reading. Re-read mtimes before repeating those sentences.
