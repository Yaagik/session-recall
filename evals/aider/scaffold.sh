#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MAKE_HOME="$HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
mkdir -p fixture-home
python3 "$MAKE_HOME" aider --cwd "$WS" --ts "2026-09-25 11:00:00" --prompt "Add input validation to the signup form." --answer "Added zod validation in src/signup/schema.ts."
python3 "$MAKE_HOME" aider --cwd "$WS" --ts "2026-09-26 16:30:00" --prompt "Fix the flaky signup test." --answer "Replaced a fixed sleep with waitFor in tests/signup.test.ts."
