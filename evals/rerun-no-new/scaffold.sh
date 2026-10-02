#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin https://github.com/example/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
$MK claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000001 --ts 2026-09-28T10:00:00.000Z --title "UNIQUE-TITLE-A-covered" --prompt "Fix the login redirect loop." --answer "Fixed it in src/auth/login.ts."
$MK claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000002 --ts 2026-09-29T15:30:00.000Z --title "UNIQUE-TITLE-B-covered" --prompt "Add a Stripe webhook." --answer "Added src/payments/webhook.ts."
$MK history --cwd "$WS" \
  --covered 'claude-code:11111111-aaaa-4aaa-8aaa-000000000001|2026-09-28|Claude Code|Fix login redirect bug' \
  --covered 'claude-code:11111111-aaaa-4aaa-8aaa-000000000002|2026-09-29|Claude Code|Add Stripe webhook handler'
