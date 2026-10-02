#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MAKE_HOME="$HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
python3 "$MAKE_HOME" gemini --cwd "$WS" --id gem-0000-0001 --ts 2026-09-26T09:00:00.000Z \
  --prompt "Write a README section about deployment." \
  --answer "Added a Deployment section to README.md describing the Vercel setup. Gotcha: preview deployments need their own env vars."
