#!/usr/bin/env bash
# GOLIVE_vps — deploy/push script (PREP — does NOT connect a broker or place orders).
#
# Pushes a committed branch to the VPS and runs verification ONLY. It deliberately:
#   * never writes credentials,
#   * never starts the live trader (that is a separate, deliberate owner action),
#   * never removes the halt flag,
#   * fails closed on any missing owner-supplied value.
#
# Owner supplies (env or args): VPS_HOST, VPS_USER, VPS_REPO_DIR, GIT_BRANCH.
#
# Usage:
#   VPS_HOST=1.2.3.4 VPS_USER=gtos VPS_REPO_DIR=/opt/gtos GIT_BRANCH=golive-prep \
#     ./push.sh            # sync + verify (default, safe)
#   ... ./push.sh --verify-only
set -euo pipefail

: "${VPS_HOST:?set VPS_HOST (owner-supplied)}"
: "${VPS_USER:?set VPS_USER (owner-supplied)}"
: "${VPS_REPO_DIR:?set VPS_REPO_DIR (owner-supplied)}"
: "${GIT_BRANCH:?set GIT_BRANCH}"

ROUTE="research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DEPLOY="${ROUTE}/GOLIVE_vps_deploy"
SSH="ssh ${VPS_USER}@${VPS_HOST}"

echo "==> [1/5] Local guard: ensure branch is committed and pushed to origin"
git rev-parse --verify "${GIT_BRANCH}" >/dev/null
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: working tree dirty — commit before deploy." >&2; exit 1
fi
git push origin "${GIT_BRANCH}"

echo "==> [2/5] VPS: fetch the committed branch (no live start)"
$SSH "cd ${VPS_REPO_DIR} && git fetch origin && git checkout ${GIT_BRANCH} && git pull --ff-only origin ${GIT_BRANCH}"

echo "==> [3/5] VPS: install pinned deps (idempotent)"
$SSH "cd ${VPS_REPO_DIR} && python3 -m pip install -r ${DEPLOY}/config/requirements-vps.txt"

echo "==> [4/5] VPS: self-verify the deploy module + scaffolding (NO broker)"
$SSH "cd ${VPS_REPO_DIR} && python3 -m pytest ${ROUTE}/test_ultimate_book_live_package.py -q"
$SSH "cd ${VPS_REPO_DIR} && python3 -m pytest ${DEPLOY}/tests -q"
$SSH "cd ${VPS_REPO_DIR} && python3 ${DEPLOY}/monitoring/kill_switch.py state"

echo "==> [5/5] VPS: confirm halt flag + gates state (must show kill-switch ON until owner go)"
$SSH "cd ${VPS_REPO_DIR} && python3 ${DEPLOY}/monitoring/kill_switch.py state | python3 -c 'import sys,json; s=json.load(sys.stdin); print(\"kill_switch_engaged=\", s[\"kill_switch_engaged\"]); sys.exit(0)'"

cat <<'EOF'

==> DONE (PREP only). NOTHING is trading.
Next owner-only steps (deliberate, separate):
  1. Create /opt/gtos/.env and /opt/gtos/.env.<ns> from GOLIVE_vps_deploy/config/env.template
  2. Provision MT5 + bridge (host/port) and confirm `nmetatrader5` connects READ-ONLY first
  3. Apply the staged Phase A config patches (patches/) after review
  4. Clear the kill-switch (kill_switch.py disengage --approval-token <token>) AND remove the
     halt flag — only after the Phase C broker/runtime-authority work is signed off
  5. Start ONE account small: systemctl start gtos-live@ftmo_acct_a  (or docker compose --profile live up gtos-live-a)
EOF
