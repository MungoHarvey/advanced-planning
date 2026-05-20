---
name: permission-config
description: "Edit hooks.json, settings.json, and agent tool-set frontmatter to grant or restrict permissions; verify that edits land at runtime. Triggers: add tool permission, edit settings, update hooks, agent tools field, tool allowlist, restrict write access, permission update."
---

# Permission Config

Edits the framework's permission and hook configuration files to grant or restrict
tool access, and verifies that the changes propagate to runtime behaviour. The three
files in scope are `settings.json` (project-level tool permissions), `hooks.json`
(PreToolUse / PostToolUse guards), and agent frontmatter `tools:` fields.

## When to Use

- Adding or removing a tool from an agent's `tools:` field in its frontmatter
- Updating the `permissions.allow` or `permissions.deny` array in `settings.json`
- Adding, editing, or removing a `PreToolUse` or `PostToolUse` hook in `hooks.json`
- Verifying that a permission change landed after an install or manual edit
- Diagnosing why a tool call is blocked or unexpectedly allowed at runtime

Do NOT use this skill for changes to command logic, skill content, or planning data.
Scope: only the three files listed above and agent frontmatter `tools:` lines.

## Process

### 1. Identify the target file and change

Determine which file(s) need editing:
- **Agent frontmatter** (`platforms/claude-code/agents/<name>.md` or
  `core/agents/<name>.md`): change the `tools:` field on the YAML frontmatter line
- **`settings.json`** (`.claude/settings.json` in the target project, or the template
  written by `install.sh`): change the `permissions.allow` or `permissions.deny` array
- **`hooks.json`** (`.claude/settings.json` `hooks` block, or a dedicated `hooks.json`):
  add, edit, or remove a `PreToolUse` / `PostToolUse` entry

### 2. Read the file before editing

Always read the current file content before making any edit. Confirm:
- The field or entry you intend to change actually exists and has the value you expect
- No duplicate entries would be created by the edit
- The surrounding YAML or JSON syntax is well-formed

### 3. Make the targeted edit

For **agent frontmatter** `tools:` field:
- The value is a comma-separated string: `"Read, Glob, Grep, Write"`
- Add the new tool at the end of the list, separated by `, `
- Do not reorder existing tools unless there is a functional reason
- Example before: `tools: Read, Glob, Grep`
- Example after: `tools: Read, Glob, Grep, Write`

For **`settings.json`** permission arrays:
- Each entry is a string like `"Write(.advanced-plans/**)"` or `"Read"`
- Add entries as new array elements; remove by deleting the matching element
- Maintain valid JSON: no trailing commas; use double quotes
- Use the narrowest scope possible: prefer `Write(.advanced-plans/gate-verdicts/*)`
  over `Write(.advanced-plans/**)`

For **`hooks.json`** / hook blocks:
- `PreToolUse` hooks fire before a tool call; they can block the call
- `PostToolUse` hooks fire after; they cannot block
- Each hook entry needs: `"matcher"` (tool name glob), `"hooks"` (array of hook objects)
- A hook object needs: `"type"` (`"command"`), `"command"` (shell command string)
- The hook command exits 0 to allow, non-zero to block (PreToolUse only)

### 4. Verify the edit landed

After saving the file:
- Re-read the file and confirm the change is present with the correct syntax
- For JSON files: validate with `python -c "import json, pathlib; json.loads(pathlib.Path('<path>').read_text())"`
- For YAML frontmatter: visually confirm the field line is correct
- For hooks: confirm the sentinel condition they guard is consistent with the hook command

### 5. Note runtime propagation

Permission changes in `settings.json` and `hooks.json` take effect the next time
a Claude Code session is started (they are read at session startup, not live-reloaded).
Agent frontmatter `tools:` changes take effect the next time the agent is spawned.

Document in the commit message whether the change is:
- **In-file only** (edit confirmed, runtime effect verified in a later E2E step)
- **E2E verified** (a test or dry-run confirmed the tool was allowed/blocked at runtime)

## Output Format

This skill produces file edits, not standalone documents. After completion:

1. The target file(s) have been edited in-place
2. JSON validity confirmed (if applicable)
3. Commit message documents the change and whether it is in-file-only or E2E-verified

Checklist before marking the todo complete:
- [ ] Target file read before edit
- [ ] Edit is minimal and targeted (no unrelated changes)
- [ ] No duplicate entries introduced
- [ ] JSON or YAML syntax valid after edit
- [ ] Change confirmed by re-reading the file
- [ ] Runtime propagation status noted in commit message
