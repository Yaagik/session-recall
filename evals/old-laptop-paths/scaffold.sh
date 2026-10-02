#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "old-laptop-home/" >> .git/info/exclude
# A backup of the OLD laptop's home: the project lived at a different path under another username
$MK claude --home old-laptop-home --cwd "/Users/olduser/code/demo-app" --id 11111111-aaaa-4aaa-8aaa-00000000000a --ts 2026-09-20T10:00:00.000Z --title "Old laptop: set up CI" --prompt "Set up GitHub Actions CI." --answer "Added .github/workflows/ci.yml running tests on push."
