#!/bin/sh
# Point a checkout at main in place, the same way as the VPS.
# Default root is /workspace. Tests set SOT_ROOT and SOT_HOLD.
# Does nothing unless --apply is passed.
# Converting /workspace also requires SOT_CONFIRM_WORKSPACE=1.
# Other worktrees that share this .git require --detach-worktrees.
if [ "$1" != "--apply" ]; then
  echo "refusing: pass --apply only when the coordinator has said go"
  echo "plan: move .git aside, git init, fetch main, reset --mixed"
  echo "also pass --detach-worktrees if other worktrees share this .git"
  exit 2
fi
root="${SOT_ROOT:-/workspace}"
hold="${SOT_HOLD:-/home/ubuntu/gtos-sot-preserve}"
if [ "$root" = "/workspace" ] && [ "$SOT_CONFIRM_WORKSPACE" != "1" ]; then
  echo "refusing: set SOT_CONFIRM_WORKSPACE=1 to convert /workspace"
  exit 2
fi
if [ ! -d "$root/.git" ]; then
  echo "refusing: $root has no .git directory"
  exit 2
fi
others=$(git -C "$root" worktree list | wc -l | tr -d ' ')
if [ "$others" -gt 1 ] && [ "$2" != "--detach-worktrees" ]; then
  echo "refusing: other worktrees share $root/.git"
  git -C "$root" worktree list
  echo "pass --apply --detach-worktrees to move that .git aside anyway"
  exit 2
fi
url=$(git -C "$root" remote get-url origin)
mkdir -p "$hold"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
aside="$hold/git-aside-workspace-$stamp"
if [ -e "$aside" ]; then
  echo "refusing: $aside already exists"
  exit 2
fi
mv "$root/.git" "$aside"
run_git() {
  out=$("$@" 2>&1)
  rc=$?
  printf '%s\n' "$out" | sed -E 's#://[^/@[:space:]]+@#://#g'
  return "$rc"
}
if ! run_git git -C "$root" init -b main \
  && ! { run_git git -C "$root" init && run_git git -C "$root" symbolic-ref HEAD refs/heads/main; }
then
  rm -rf "$root/.git"
  mv "$aside" "$root/.git"
  echo "refusing: git init failed; old .git restored"
  exit 1
fi
restore() {
  if [ -e "$root/.git" ] && [ -e "$aside" ]; then
    rm -rf "$hold/git-failed-$stamp"
    mv "$root/.git" "$hold/git-failed-$stamp"
  fi
  if [ -e "$aside" ] && [ ! -e "$root/.git" ]; then
    mv "$aside" "$root/.git"
  fi
}
run_git git -C "$root" config core.autocrlf false || { restore; exit 1; }
run_git git -C "$root" remote add origin "$url" || { restore; exit 1; }
run_git git -C "$root" fetch origin main || { restore; exit 1; }
run_git git -C "$root" reset --mixed origin/main || { restore; exit 1; }
run_git git -C "$root" branch -M main || { restore; exit 1; }
run_git git -C "$root" branch --set-upstream-to=origin/main || { restore; exit 1; }
ignore="$root/.gitignore"
touch "$ignore"
for line in \
  "pipeline_state/" \
  "shadow_logs/" \
  ".venv/" \
  ".venv-*/" \
  "venv/" \
  "__pycache__/" \
  "*.pyc" \
  ".env" \
  ".env.*" \
  "*.env" \
  "secrets/" \
  "ceremony-secrets/" \
  "*.pem" \
  "id_rsa" \
  "judgment/**/*.jsonl" \
  "judgment/**/*.csv" \
  "*.jsonl" \
  "*.parquet" \
  "*.pkl"
do
  if ! grep -qxF "$line" "$ignore"; then
    printf '%s\n' "$line" >> "$ignore"
  fi
done
echo "index matches origin/main; old git dir is $aside"
echo "working tree was not checked out, cleaned, stashed, or hard-reset"
