# Gemini CLI

**Status:** experimental (from Gemini CLI docs and third-party sources; not yet verified on a real install).

## Locations
- macOS / Linux: `HOME/.gemini/tmp/<project-id>/chats/*.json`
- Windows: `HOME\.gemini\tmp\<project-id>\chats\*.json`

## Match to project
A `<project-id>` folder belongs to the project if any one of these is true:
1. **The name is a SHA-256 hash of a known path.** The folder name equals the SHA-256 hex digest of a known path (try both as-given and resolved forms). On Windows, hash the native form with backslashes and a drive letter (`C:\Users\me\app`), as Gemini CLI does, not the `C:/Users/...` form that git prints. To compute it:
   - macOS / Linux: `printf '%s' "<path>" | shasum -a 256`
   - Windows PowerShell: `$b=[Text.Encoding]::UTF8.GetBytes('<path>'); -join ([Security.Cryptography.SHA256]::Create().ComputeHash($b) | ForEach-Object { $_.ToString('x2') })`
2. **It names its project root.** The folder contains a `.project_root` file whose content is a known path, or a path inside one.
3. **It is in the registry.** `HOME/.gemini/projects.json` exists and maps a known path to this folder name. Newer versions use short project names.

## List sessions
- **ID:** the `sessionId` field of the chat file.
- **Started:** `startTime`.
- **Title:** the first `"type": "user"` message, cut to 70 characters:
  - macOS / Linux: `grep -m1 -A4 '"type": *"user"' "<file>" | grep -o -m1 '"content": *"[^"]*"' | cut -c1-90`
  - Windows PowerShell: `(Select-String -LiteralPath '<file>' -Pattern '"type": *"user"' -Context 0,4 -List | ForEach-Object { $_.Context.PostContext } | Select-String -Pattern '"content": *"([^"]*)"' | Select-Object -First 1).Matches[0].Groups[1].Value`
- **Size:** the file size.

## Read
- The chat file is a single JSON object with a `messages` array.
- **Keep:**
  - `"type": "user"` messages: the user's prompts. `content` is a string or a list of parts with `text`.
  - `"type": "gemini"` messages: the replies.
  - `"type": "error"` messages: keep for "Notable".
- **Tool calls:** where a message has tool calls, keep only the tool names and file paths or commands.
- **Skip:** thoughts and tool results.

## Estimate
An upper bound: file size ÷ 4. Get it with `wc -c <files>` (macOS/Linux) or `(Get-Item <file>).Length` (PowerShell). The file can't be filtered without parsing it, so read it in chunks and skip tool results as you go.

## Format check
Passes if `grep -c '"messages"' "<file>"` prints at least 1 and `grep -o -m1 '"sessionId": *"[^"]*"' "<file>"` prints a value. Don't load the file to check it.

## Retention
Gemini CLI deletes sessions after 30 days by default (see the session retention settings in Gemini CLI's session-management docs).
