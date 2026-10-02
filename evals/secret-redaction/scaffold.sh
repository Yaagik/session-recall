#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MAKE_HOME="$HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
python3 "$MAKE_HOME" claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000004 --ts 2026-09-30T12:00:00.000Z --title "Configure database" \
  --prompt "Use this key sk-test-REDACT-ME-0000 and put DATABASE_URL=postgres://admin:hunter2@db.internal:5432/app in .env" \
  --answer "Configured src/db.ts to read DATABASE_URL from the environment. I did not hardcode the key sk-test-REDACT-ME-0000; the password hunter2 stays only in .env."
