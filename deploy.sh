#!/usr/bin/env bash
#
# deploy.sh - publish public/ to https://oganbayril.com
#
# Usage (Git Bash on Windows, or any bash, from anywhere):
#   ./deploy.sh              deploy what is on GitHub's main branch
#   ./deploy.sh <commit>     deploy a specific commit (it must be on GitHub)
#   ./deploy.sh --rollback   redeploy the commit that was live before the last deploy
#
# What happens:
#   1. local checks: clean working tree, local main == origin/main, no TODOs left in public/
#   2. ssh to the VPS, which updates its own checkout ($CHECKOUT) from GitHub
#      and runs rsync --delete $CHECKOUT/public/ -> /srv/oganbayril/ ON THE SERVER
#      (Git Bash has no rsync; nothing is copied from this PC)
#   3. health check: the live site must answer 200 on a few pages
#
# The Caddy side (www redirect, clean URLs, 404 page) is vps-infra's
# templates/static-www.caddy, installed as /etc/caddy/sites-enabled/oganbayril.conf.
#
# Set ALLOW_TODO=1 to deploy even though public/ still contains "TODO".
#
# Server details live in deploy.env next to this script (git-ignored, never committed):
#   cp deploy.env.example deploy.env   and fill in DEPLOY_HOST and DEPLOY_USER.

set -euo pipefail

REPO_URL="https://github.com/oganbayril/personal-website.git"
BRANCH="main"
TARGET="/srv/oganbayril"            # the guard below accepts nothing else
SITE="https://oganbayril.com"
CHECK_PATHS="/ /projects /cv /contact"

die() { echo "deploy: $*" >&2; exit 1; }

# --- arguments ------------------------------------------------------------------
REF="origin/$BRANCH"
ROLLBACK=0
case "${1:-}" in
  "") ;;
  --rollback) ROLLBACK=1 ;;
  -h|--help) sed -n '2,23p' "$0"; exit 0 ;;
  -*) die "unknown option: $1 (see --help)" ;;
  *) REF="$1" ;;
esac
# The ref is passed to a remote shell: allow only plain ref characters.
case "$REF" in
  *[!A-Za-z0-9/._-]*) die "invalid commit/ref: $REF" ;;
esac

cd "$(dirname "${BASH_SOURCE[0]}")"

# --- server config from deploy.env ----------------------------------------------------
# Parsed, not sourced: only KEY=value lines for the keys below are read.
ENV_FILE="deploy.env"
[ -f "$ENV_FILE" ] || die "$ENV_FILE not found next to deploy.sh.
  Create it from the template:  cp deploy.env.example deploy.env
  then set DEPLOY_HOST and DEPLOY_USER (deploy.env is git-ignored)."

DEPLOY_HOST="" DEPLOY_USER="" DEPLOY_CHECKOUT=""
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  case "$line" in ''|'#'*) continue ;; esac
  key="${line%%=*}" value="${line#*=}"
  value="${value%\"}" value="${value#\"}" value="${value%\'}" value="${value#\'}"
  case "$key" in
    DEPLOY_HOST) DEPLOY_HOST="$value" ;;
    DEPLOY_USER) DEPLOY_USER="$value" ;;
    DEPLOY_CHECKOUT) DEPLOY_CHECKOUT="$value" ;;
    *) die "$ENV_FILE: unknown setting '$key' (allowed: DEPLOY_HOST, DEPLOY_USER, DEPLOY_CHECKOUT)" ;;
  esac
done < "$ENV_FILE"

[ -n "$DEPLOY_HOST" ] || die "$ENV_FILE: DEPLOY_HOST is empty (server hostname or IP)"
[ -n "$DEPLOY_USER" ] || die "$ENV_FILE: DEPLOY_USER is empty (SSH user on the server)"
case "$DEPLOY_HOST" in *[!A-Za-z0-9.:-]*) die "$ENV_FILE: DEPLOY_HOST has invalid characters: $DEPLOY_HOST" ;; esac
case "$DEPLOY_USER" in *[!A-Za-z0-9._-]*|-*) die "$ENV_FILE: DEPLOY_USER has invalid characters: $DEPLOY_USER" ;; esac
case "$DEPLOY_CHECKOUT" in ''|/*) ;; *) die "$ENV_FILE: DEPLOY_CHECKOUT must be an absolute path (or left empty)" ;; esac
case "$DEPLOY_CHECKOUT" in *[!A-Za-z0-9/._-]*) die "$ENV_FILE: DEPLOY_CHECKOUT has invalid characters" ;; esac

SSH_HOST="$DEPLOY_USER@$DEPLOY_HOST"
CHECKOUT="$DEPLOY_CHECKOUT"         # empty = ~/src/personal-website on the server

# --- 1. local checks --------------------------------------------------------------
git rev-parse --is-inside-work-tree > /dev/null 2>&1 || die "not a git repository: $(pwd)"

if [ -n "$(git status --porcelain)" ]; then
  git status --short >&2
  die "uncommitted changes. Commit and push first (the server deploys from GitHub)."
fi

if [ "$ROLLBACK" = 0 ] && [ "$REF" = "origin/$BRANCH" ]; then
  git fetch --quiet origin "$BRANCH" || die "git fetch failed (is origin set and reachable?)"
  local_head="$(git rev-parse HEAD)"
  remote_head="$(git rev-parse "origin/$BRANCH")"
  if [ "$local_head" != "$remote_head" ]; then
    die "local HEAD ($(git rev-parse --short HEAD), branch $(git branch --show-current)) is not origin/$BRANCH ($(git rev-parse --short "origin/$BRANCH")). Push (or pull) first."
  fi
  if [ "${ALLOW_TODO:-0}" != 1 ] && git grep -n -I "TODO" -- public/ > /dev/null; then
    echo "public/ still contains TODO placeholders:" >&2
    git grep -n -I "TODO" -- public/ | head -20 >&2
    die "fill them in, or run ALLOW_TODO=1 ./deploy.sh"
  fi
fi

# --- 2. on the server: update the checkout, rsync public/ ---------------------------
echo "deploying $REF to $DEPLOY_HOST:$TARGET"
args="$(printf '%q ' "$REPO_URL" "$BRANCH" "$CHECKOUT" "$TARGET" "$REF" "$ROLLBACK")"

# Quoted heredoc: nothing below is expanded locally; values arrive as $1..$6.
ssh -o BatchMode=yes "$SSH_HOST" "bash -s -- $args" <<'REMOTE'
set -euo pipefail
REPO_URL="$1" BRANCH="$2" CHECKOUT="${3:-$HOME/src/personal-website}" TARGET="$4" REF="$5" ROLLBACK="$6"
die() { echo "deploy (server): $*" >&2; exit 1; }

# Guard: rsync --delete may only ever write into exactly /srv/oganbayril.
guard_target() {
  if [ -z "${TARGET:-}" ] || [ "$TARGET" != "/srv/oganbayril" ]; then
    die "refusing to rsync --delete into '${TARGET:-<empty>}' (only /srv/oganbayril is allowed)"
  fi
  [ -d "$TARGET" ] || die "$TARGET does not exist"
}
guard_target

DEPLOYED_FILE="$CHECKOUT.deployed"    # commit live now
PREVIOUS_FILE="$CHECKOUT.previous"    # commit live before that (for --rollback)

mkdir -p "$(dirname "$CHECKOUT")"
if [ ! -d "$CHECKOUT/.git" ]; then
  echo "first deploy: cloning $REPO_URL into $CHECKOUT"
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$CHECKOUT"
fi
cd "$CHECKOUT"
[ "$(git remote get-url origin)" = "$REPO_URL" ] || die "$CHECKOUT is a clone of something else"
git fetch --quiet --prune origin

if [ "$ROLLBACK" = 1 ]; then
  [ -s "$PREVIOUS_FILE" ] || die "nothing to roll back to ($PREVIOUS_FILE missing)"
  REF="$(cat "$PREVIOUS_FILE")"
  echo "rolling back to $REF"
fi
COMMIT="$(git rev-parse --verify --quiet "$REF^{commit}")" || die "unknown commit: $REF (is it pushed?)"

# The checkout is deploy-only: force it to exactly that commit.
git checkout --quiet --force --detach "$COMMIT"
git clean --quiet -ffdx

# Never sync an empty or broken tree (--delete would empty the live site).
[ -s public/index.html ] || die "public/index.html missing in $COMMIT, refusing to sync"

guard_target
rsync -a --delete --chmod=D755,F644 "$CHECKOUT/public/" "$TARGET/"

LIVE_BEFORE="$(cat "$DEPLOYED_FILE" 2>/dev/null || true)"
if [ -n "$LIVE_BEFORE" ] && [ "$LIVE_BEFORE" != "$COMMIT" ]; then
  echo "$LIVE_BEFORE" > "$PREVIOUS_FILE"
fi
echo "$COMMIT" > "$DEPLOYED_FILE"
echo "synced $(git log -1 --format='%h %s' "$COMMIT")"
REMOTE

# --- 3. health check ------------------------------------------------------------
failed=0
for path in $CHECK_PATHS; do
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$SITE$path" || true)"
  echo "  $code $SITE$path"
  [ "$code" = 200 ] || failed=1
done
[ "$failed" = 0 ] || die "health check failed. Roll back with: ./deploy.sh --rollback"
echo "deployed: $SITE"
