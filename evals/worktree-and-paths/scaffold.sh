#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
WS_LOGICAL="${WS#/private}"   # macOS: /tmp/... is the logical form of /private/tmp/...
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
mkdir -p packages/api && echo "# demo-app" > README.md && echo "api" > packages/api/README.md
git add . && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
git worktree add -q "$WS-wt" -b feature
mkdir -p "$WS-old"
# A: recorded under the logical (possibly symlinked) path, e.g. /var/... instead of /private/var/...
$MK claude --cwd "$WS_LOGICAL" --id 11111111-aaaa-4aaa-8aaa-000000000001 --ts 2026-09-28T10:00:00.000Z --title "Fix login redirect bug" --prompt "Fix the login redirect loop." --answer "Fixed it in src/auth/login.ts."
# W: in the worktree
$MK claude --cwd "$WS-wt" --id 11111111-aaaa-4aaa-8aaa-000000000006 --ts 2026-09-30T14:00:00.000Z --title "Refactor payments in feature worktree" --prompt "Refactor the payments module." --answer "Split src/payments into charge.ts and refund.ts."
# SUB: started in a subfolder
$MK claude --cwd "$WS/packages/api" --id 11111111-aaaa-4aaa-8aaa-000000000007 --ts 2026-09-30T15:00:00.000Z --title "Tune API package" --prompt "Speed up the API package tests." --answer "Parallelized tests in packages/api."
# OTHER: a sibling project sharing the path prefix - must NOT be included
$MK claude --cwd "$WS-old" --id 11111111-aaaa-4aaa-8aaa-000000000008 --ts 2026-09-30T16:00:00.000Z --title "Unrelated old project" --prompt "Work on the old project." --answer "Did old-project things."
# DEL: a worktree that Superset/Conductor already deleted (folder gone, next to the live worktree)
$MK claude --cwd "$(dirname "$WS")/deleted-worktree-xyz" --id 11111111-aaaa-4aaa-8aaa-000000000009 --ts 2026-09-29T09:00:00.000Z --title "Work in a merged and deleted worktree" --prompt "Add audit logging." --answer "Added src/audit/log.ts."
# LONG: started in a deeply nested folder, so Claude Code cut the folder name to 200 chars + hash
LONGDIR="$WS/packages/$(printf 'very-long-directory-name-%.0s' 1 2 3 4 5 6 7 8)"
mkdir -p "$LONGDIR"
$MK claude --cwd "$LONGDIR" --id 11111111-aaaa-4aaa-8aaa-00000000000b --ts 2026-09-30T17:00:00.000Z --title "Deeply nested package work" --prompt "Fix the nested package build." --answer "Fixed the build config."
