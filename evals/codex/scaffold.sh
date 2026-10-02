#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin https://github.com/example/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
$MK codex --cwd "$WS" --id 019a0000-0000-7000-8000-00000000c0de --ts 2026-09-27T09:00:00.000Z \
  --prompt "Add rate limiting to the login endpoint." \
  --answer "Added a 5-requests-per-minute limiter in src/auth/rateLimit.ts. TODO: make the limit configurable."
