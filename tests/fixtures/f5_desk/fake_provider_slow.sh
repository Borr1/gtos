#!/usr/bin/env bash
# Fake judgment provider that hangs past the caller's timeout.
cat > /dev/null
sleep 5
printf '{"schema":"gtos.f5.judge.verdict.v1","slate_id":"slow","verdicts":[],"manage":[],"notes":"too late"}\n'
