#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
MAIN="$WS-main"
# The main clone lives elsewhere; the agent runs inside a linked worktree (here, the workspace).
mkdir -p "$MAIN" && cd "$MAIN"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin https://github.com/example/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
git worktree add -q --force "$WS" -b feature-x
cd "$WS"
echo "fixture-home/" >> "$MAIN/.git/info/exclude"
$MK claude --cwd "$MAIN" --id 11111111-aaaa-4aaa-8aaa-00000000000c --ts 2026-09-28T10:00:00.000Z --title "Work in the main clone" --prompt "Set up linting." --answer "Added eslint config."
$MK claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-00000000000d --ts 2026-09-29T10:00:00.000Z --title "Work in this worktree" --prompt "Add feature X." --answer "Added src/featureX.ts."
