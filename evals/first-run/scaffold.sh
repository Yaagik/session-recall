#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MK="python3 $HERE/../_fixtures/make_home.py"
WS="$(pwd -P)"
git init -q -b main && git config user.email t@example.com && git config user.name t
git remote add origin https://github.com/example/demo-app.git
echo "# demo-app" > README.md && git add README.md && git commit -qm init
echo "fixture-home/" >> .git/info/exclude
$MK claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000001 --ts 2026-09-28T10:00:00.000Z \
  --title "Fix login redirect bug" \
  --prompt "The login page redirects in a loop when the session cookie is missing. Fix it." \
  --answer "Fixed the redirect loop in src/auth/login.ts: when the session cookie is missing we now render the login form instead of redirecting. Decision: keep sessions in Postgres rather than Mongo because we need joins and JSON queries. TODO: add a regression test for the missing-cookie case."
$MK claude --cwd "$WS" --id 11111111-aaaa-4aaa-8aaa-000000000002 --ts 2026-09-29T15:30:00.000Z --subagent \
  --title "Add Stripe webhook handler" \
  --prompt "Add a Stripe webhook endpoint for checkout.session.completed." \
  --answer "Added POST /api/stripe/webhook in src/payments/webhook.ts with signature verification. Gotcha: the raw request body must be used for the signature check, not the parsed JSON. TODO: handle refunds."
