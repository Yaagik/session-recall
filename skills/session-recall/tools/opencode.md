# opencode

**Status:** experimental (from opencode's CLI docs; not yet verified on a real install).

## Locations
- Data lives in a SQLite database under `HOME/.local/share/opencode/` (macOS/Linux) and `HOME\.local\share\opencode\` (Windows). **Never open the database directly**; use the `opencode` command.
- If `--home` was given, skip opencode and report: "opencode: skipped because --home was given (opencode only reads the real home folder)".
- If the `opencode` command is not on PATH, report opencode as *format mismatch* with the note "opencode command not found".

## Match to project
Run `opencode session list` once in each known path (POSIX and PowerShell are the same). Keep the sessions it lists. If `opencode export <id>` (below) shows a `directory` field, use it to confirm the session's directory equals a known path or is inside one.

## List sessions
- **ID:** the session ID printed by `opencode session list`.
- **Started:** its created time.
- **Title:** its title.
- **Size:** unknown; show "-".

## Read
- `opencode export <id>` prints the session as JSON: session info plus messages, each with a role and a list of parts.
- **Keep:** parts with `"type": "text"`.
- **Tool parts:** keep only the tool name and the file path or command from its input.
- **Skip:** tool output and reasoning parts.

## Estimate
An upper bound: `opencode export <id> | wc -c` (PowerShell: `(opencode export <id> | Out-String).Length`), ÷ 4. Only the count is printed, not the content.

## Format check
Passes if `opencode export <id> | head -c 1` prints `{` for one listed session. Before approval, pipe `opencode export` only into `head -c` or `wc -c`; never let its content print.
