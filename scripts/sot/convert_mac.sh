#!/bin/sh
# New clone. Default dest is /Users/borr/GTOSActive/gtos.
# Does not touch jev-live-swarm or gold-grok.
# Does nothing unless --apply is passed.
# Tests set SOT_DEST and SOT_URL. Unset, those are the cutover values.
if [ "$1" != "--apply" ]; then
  echo "refusing: pass --apply only when the coordinator has said go"
  echo "plan: git clone --branch main into /Users/borr/GTOSActive/gtos"
  exit 2
fi
dest="${SOT_DEST:-/Users/borr/GTOSActive/gtos}"
url="${SOT_URL:-}"
if [ -z "$url" ]; then
  echo "refusing: set SOT_URL to the Origin clone URL"
  exit 2
fi
if [ -e "$dest" ]; then
  echo "refusing: $dest already exists"
  exit 2
fi
case "$dest" in
  */jev-live-swarm|*/jev-live-swarm/*|*/gold-grok|*/gold-grok/*)
    echo "refusing: dest is a live Grok tree"
    exit 2
    ;;
esac
if ! out=$(git -c core.autocrlf=false clone --branch main "$url" "$dest" 2>&1); then
  printf '%s\n' "$out" | sed -E 's#://[^/@[:space:]]+@#://#g'
  echo "clone failed"
  exit 1
fi
echo "clone ready at $dest"
