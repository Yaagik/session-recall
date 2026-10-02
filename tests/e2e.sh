#!/usr/bin/env bash
# End-to-end test with REAL git (the `claude plugin eval` sandbox has no git):
# builds a repo with a linked worktree and fake tool history, runs the plugin through `claude -p`,
# and checks the files it writes. Uses your Claude account (about $0.30-0.60 per run).
#
#   bash tests/e2e.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
MAKE_HOME="$REPO/evals/_fixtures/make_home.py"
T="$(mktemp -d)"; trap 'rm -rf "$T" "$T-wt"' EXIT
WS="$(cd "$T" && pwd -P)"
fail=0
pass_check() { echo "  ok   $1"; }
fail_check() { echo "  FAIL $1"; fail=1; }

cd "$WS"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin ../origin/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
git worktree add -q "$WS-wt" -b feature
python3 "$MAKE_HOME" claude --cwd "$WS" --id e2e00000-0000-4000-8000-000000000001 --ts 2026-09-28T10:00:00.000Z --title "Fix login redirect bug" \
  --prompt "Fix the login loop. Use key sk-test-REDACT-ME-0000." --answer "Fixed it in src/auth/login.ts. Decision: Postgres over Mongo for joins."
python3 "$MAKE_HOME" claude --cwd "$WS-wt" --id e2e00000-0000-4000-8000-000000000002 --ts 2026-09-29T10:00:00.000Z --title "Feature work in worktree" \
  --prompt "Add the feature flag." --answer "Added src/flags.ts."
python3 "$MAKE_HOME" codex --cwd "$WS" --id e2e-codex-1 --ts 2026-09-27T09:00:00.000Z --prompt "Add rate limiting." --answer "Added limiter."
python3 "$MAKE_HOME" codex --cwd "/elsewhere/other" --id e2e-codex-other --ts 2026-09-27T10:00:00.000Z \
  --instructions "OTHERPROJ-INSTRUCTIONS" --prompt "OTHERPROJ-CODEX" --answer "x"

echo "Running session-recall through claude -p in $WS ..."
OUT="$(claude -p "Use the session-recall skill to document this project's AI session history. Arguments: --home ./fixture-home --all. I accept the privacy notice and approve the token estimate." \
  --plugin-dir "$REPO" --allowedTools "Bash Read Glob Grep Write Edit Skill" 2>&1)" || true
echo "$OUT" | tail -15 | sed 's/^/    | /'

H="$WS/docs/ai-history/HISTORY.md"
D="$WS/docs/ai-history"
STRAY="$(git -C "$WS" status --porcelain --untracked-files=all | grep -v -E '^\?\? docs/ai-history/' || true)"

if [ -f "$H" ]; then pass_check "HISTORY.md written"; else fail_check "HISTORY.md written"; fi
if ls "$D"/sessions/*.md >/dev/null 2>&1; then pass_check "run log written"; else fail_check "run log written"; fi
if grep -q 'claude-code:e2e00000-0000-4000-8000-000000000001' "$H" 2>/dev/null; then pass_check "main-repo session documented"; else fail_check "main-repo session documented"; fi
if grep -q 'claude-code:e2e00000-0000-4000-8000-000000000002' "$H" 2>/dev/null; then pass_check "worktree session found via real git"; else fail_check "worktree session found via real git"; fi
if grep -q 'codex:e2e-codex-1' "$H" 2>/dev/null; then pass_check "codex session documented"; else fail_check "codex session documented"; fi
if grep -rqE 'e2e-codex-other|OTHERPROJ' "$D" 2>/dev/null; then fail_check "other project not documented"; else pass_check "other project not documented"; fi
if grep -rq 'sk-test-REDACT-ME-0000' "$D" 2>/dev/null; then fail_check "secret not written"; else pass_check "secret not written"; fi
if grep -q 'sk-test-REDACT-ME-0000' <<<"$OUT"; then fail_check "secret not in reply"; else pass_check "secret not in reply"; fi
if grep -qE 'Tokens: estimated ~[0-9,]+ input' <<<"$OUT"; then pass_check "estimate reported"; else fail_check "estimate reported"; fi
if [ -z "$STRAY" ]; then pass_check "nothing written outside docs/ai-history"; else fail_check "nothing written outside docs/ai-history"; fi
exit $fail
