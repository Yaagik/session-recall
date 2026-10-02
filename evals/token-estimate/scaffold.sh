#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin https://github.com/example/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
$MK claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000001 --ts 2026-09-28T10:00:00.000Z --title "Fix login redirect bug" --prompt "Fix the login redirect loop." --answer "Fixed it in src/auth/login.ts."
# Other projects on the same machine: their content must never be read before approval
$MK codex --cwd "/elsewhere/other-project" --id 019a0000-0000-7000-8000-0000000000ff --ts 2026-09-27T09:00:00.000Z \
  --instructions "OTHERPROJ-INSTRUCTIONS long AGENTS.md text of another project" --prompt "OTHERPROJ-CODEX prompt" --answer "other answer"
$MK cline --cwd "/elsewhere/other-project" --id 1727900000000 --prompt "OTHERPROJ-CLINE task text" --answer "other answer"
