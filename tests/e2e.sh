#!/usr/bin/env bash
# End-to-end test with REAL git (the `claude plugin eval` sandbox has no git):
# builds a repo with a linked worktree and fake tool history, runs the plugin through `claude -p`,
# and checks the files it writes. Uses your Claude account (about $0.30-0.60 per run).
#
#   bash tests/e2e.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
MK="python3 $REPO/evals/_fixtures/make_home.py"
T="$(mktemp -d)"; trap 'rm -rf "$T" "$T-wt"' EXIT
WS="$(cd "$T" && pwd -P)"
fail=0
check() { if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; fail=1; fi; }

cd "$WS"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin https://github.com/example/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
git worktree add -q "$WS-wt" -b feature
$MK claude --cwd "$WS" --id e2e00000-0000-4000-8000-000000000001 --ts 2026-09-28T10:00:00.000Z --title "Fix login redirect bug" \
  --prompt "Fix the login loop. Use key sk-test-REDACT-ME-0000." --answer "Fixed it in src/auth/login.ts. Decision: Postgres over Mongo for joins."
$MK claude --cwd "$WS-wt" --id e2e00000-0000-4000-8000-000000000002 --ts 2026-09-29T10:00:00.000Z --title "Feature work in worktree" \
  --prompt "Add the feature flag." --answer "Added src/flags.ts."
$MK codex --cwd "$WS" --id e2e-codex-1 --ts 2026-09-27T09:00:00.000Z --prompt "Add rate limiting." --answer "Added limiter."
$MK codex --cwd "/elsewhere/other" --id e2e-codex-other --ts 2026-09-27T10:00:00.000Z \
  --instructions "OTHERPROJ-INSTRUCTIONS" --prompt "OTHERPROJ-CODEX" --answer "x"

echo "Running session-recall through claude -p in $WS ..."
OUT="$(claude -p "Use the session-recall skill to document this project's AI session history. Arguments: --home ./fixture-home --all. I accept the privacy notice and approve the token estimate." \
  --plugin-dir "$REPO" --allowedTools "Bash Read Glob Grep Write Edit Skill" 2>&1)" || true
echo "$OUT" | tail -15 | sed 's/^/    | /'

H="$WS/docs/ai-history/HISTORY.md"
check "HISTORY.md written"                     "[ -f '$H' ]"
check "run log written"                        "ls '$WS'/docs/ai-history/sessions/*.md >/dev/null 2>&1"
check "main-repo session documented"           "grep -q 'claude-code:e2e00000-0000-4000-8000-000000000001' '$H'"
check "worktree session found via real git"    "grep -q 'claude-code:e2e00000-0000-4000-8000-000000000002' '$H'"
check "codex session documented"               "grep -q 'codex:e2e-codex-1' '$H'"
check "other project not documented"           "! grep -q -E 'e2e-codex-other|OTHERPROJ' '$WS'/docs/ai-history -r"
check "secret not written"                     "! grep -rq 'sk-test-REDACT-ME-0000' '$WS/docs/ai-history'"
check "secret not in reply"                    "! echo \"\$OUT\" | grep -q 'sk-test-REDACT-ME-0000'"
check "estimate reported"                      "echo \"\$OUT\" | grep -q -E 'Tokens: estimated ~[0-9,]+ input'"
check "nothing written outside docs/ai-history" "[ -z \"\$(git -C '$WS' status --porcelain --untracked-files=all | grep -v -E '^\\?\\? docs/ai-history/')\" ]"
exit $fail
