#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MAKE_HOME="$HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
python3 "$MAKE_HOME" cline --cwd "$WS" --id 1727600000000 --prompt "Add dark mode toggle." --answer "Added a ThemeToggle component in src/ui/ThemeToggle.tsx."
python3 "$MAKE_HOME" roo --cwd "$WS" --id 1727700000000 --prompt "Write unit tests for the theme store." --answer "Added tests/themeStore.test.ts covering persistence."
python3 "$MAKE_HOME" cline --cwd "/somewhere/else/project" --id 1727800000000 --prompt "Unrelated cline task." --answer "Elsewhere."
