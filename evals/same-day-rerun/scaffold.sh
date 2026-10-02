#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MAKE_HOME="$HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
python3 "$MAKE_HOME" claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000001 --ts 2026-09-28T10:00:00.000Z --title "Fix login redirect bug" --prompt "Fix the login redirect loop." --answer "Fixed it in src/auth/login.ts."
python3 "$MAKE_HOME" claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000002 --ts 2026-09-29T15:30:00.000Z --title "Add Stripe webhook handler" --prompt "Add a Stripe webhook." --answer "Added src/payments/webhook.ts. TODO: handle refunds."
python3 "$MAKE_HOME" history --cwd "$WS" \
  --covered 'claude-code:99999999-ghost-0000-0000-000000000000|2026-08-01|Claude Code|Session from my old laptop' \
  --covered 'claude-code:11111111-aaaa-4aaa-8aaa-000000000001|2026-09-28|Claude Code|Fix login redirect bug'
python3 "$MAKE_HOME" runlog --cwd "$WS" --runlog-date "$(date +%F)"
