#!/usr/bin/env bash
# Fake judgment provider (tests only). Consumes the whole prompt from stdin,
# echoes prose around a valid gtos.f5.judge.verdict.v1 object, echoing back the
# slate_id it finds in the prompt (so daemon end-to-end tests validate).
input="$(cat)"
sid="$(printf '%s' "$input" | sed -n 's/.*"slate_id": *"\([a-f0-9][a-f0-9]*\)".*/\1/p' | head -1)"
if [ -z "$sid" ]; then sid="unknown"; fi
echo "Model prose the extractor must skip {not json}."
printf '{"schema":"gtos.f5.judge.verdict.v1","slate_id":"%s","verdicts":[],"manage":[],"notes":"fake ok"}\n' "$sid"
echo "Trailing prose."
