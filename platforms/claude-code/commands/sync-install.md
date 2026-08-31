---
description: Audit and refresh the installed .claude/ command/agent/schema copies from the repository source. Fixes drift after any platforms/claude-code/ or core/schemas/ edit. Use --check for audit-only (no writes).
allowed-tools: Read, Write, Edit, Glob, Bash
argument-hint: "[--check] [--layers source,project|source,global|all]"
---

# /sync-install

Keeps the installed `.claude/` copies of commands, agents, and schemas in sync
with the canonical source tree in this repository. After any edit to
`platforms/claude-code/commands/`, `platforms/claude-code/agents/`, or
`core/schemas/`, run `/sync-install` to propagate changes outward.

**Direction is source → installed only.** This command never reads from an
installed layer and writes back to source. That direction is intentionally
unsupported.

**Writing to the global layer** (`~/.claude/`) affects every project that has
installed the framework. The command prints each file it changes there so the
operator has a complete record.

## Steps

### 1. Parse arguments

Read `$ARGUMENTS`. Accepted flags:

- `--check` — audit only; print the drift report but make no writes.
- `--layers source,project|source,global|all` — which layer pairs to audit and
  sync. Default: `all` (both layers that exist on disk).

If an unrecognised flag is present, print:

```
Error: unrecognised flag '[flag]'.
Usage: /sync-install [--check] [--layers source,project|source,global|all]
```

Stop.

### 1b. Ensure the shared runtime is reachable

`install_audit` compares `.claude/` surfaces only, so it is blind to
`.advanced-plans/runtime.json` and `.advanced-plans/bin/ap.py`. Those are what
every command uses to reach `platforms/python/`, and a `source_root` left
pointing at a moved checkout is exactly the drift this command exists to
repair. The launcher's own diagnostic names `/sync-install` as a repair, so it
has to actually be one.

This runs **before** the audit, not after it. Step 2 invokes
`install_audit` *through* the launcher, so a stale or missing record
makes the audit itself the thing that fails - and a repair placed after
it could never be reached in either case it exists for.

For each project layer included in `--layers`:

```bash
python ".advanced-plans/bin/ap.py" --check
```

- Exit 0: the record resolves. Print the line it produced and continue to
  Step 2.
- Exit 3: it does not. The diagnostic names the file and the key. Rewrite
  `source_root` in `.advanced-plans/runtime.json` to the absolute path of the
  source checkout `/sync-install` is running from, and re-copy
  `platforms/python/ap_launcher.py` to `.advanced-plans/bin/ap.py`.
- The launcher is missing entirely (`can't open file`): copy it, then write
  `runtime.json` with `schema_version: 1` and that same `source_root`.

Record the path as one the *interpreter* can open, not only the shell: under
Git Bash on Windows that means `C:/Users/...`, not `/c/Users/...`. Re-running
the installer does this correctly and is the better repair when it is
available; this step exists for the case where it is not.

### 2. Run the install audit

Run:

```bash
python ".advanced-plans/bin/ap.py" install_audit --layers [resolved_layers]
```

Capture the output and exit code.

- Exit 0 → all layers are current. Print the audit output and stop:
  ```
  /sync-install: all layers current — nothing to do
  ```
- Exit 1 → drift detected. Continue to Step 3.
- Exit 2 → argument/configuration error. Print the error and stop.
- Exit 3 → the runtime became unreachable between Step 1b and here (a
  concurrent move, or a repair that did not take). Print the launcher's
  diagnostic and stop; re-running the installer is the repair. Do **not**
  read exit 3 as an audit verdict - `install_audit` never returns it.

If `--check` was passed, print the full audit output and stop regardless of
exit code — do not proceed to the copy step.

### 3. Identify files to refresh

Parse the audit output for lines beginning with `  STALE` or `  MISSING`
followed by `<surface>/<filename>`. Construct the copy list:

For each stale or missing file:

```
source_path  = <repo_root>/<source_dir>/<filename>
project_path = <repo_root>/.claude/<surface>/<filename>
global_path  = <global_home>/.claude/<surface>/<filename>
```

where:
- `source_dir` is the surface's source directory:
  - `commands` → `platforms/claude-code/commands`
  - `agents`   → `platforms/claude-code/agents`
  - `schemas`  → `core/schemas`
- `global_home` is resolved USERPROFILE-first (same as install_audit.py).

Only copy to a layer that was included in `--layers` and that exists on disk.

### 4. Copy stale/missing files (source → installed)

For each file in the copy list, copy source to the installed path:

```bash
cp <source_path> <installed_path>
```

If the destination directory does not exist, create it first.

Print each copy performed:

```
  REFRESHED  [layer] <surface>/<filename>
```

where `[layer]` is `project` or `global`.

If writing to the global layer, prefix the line with `[GLOBAL]` to make it
visually distinct:

```
  [GLOBAL] REFRESHED  global <surface>/<filename>
```

### 5. Verify the refresh

After all copies are done, run the audit again:

```bash
python ".advanced-plans/bin/ap.py" install_audit --layers [resolved_layers]
```

- Exit 0 → success. Print:
  ```
  /sync-install: refresh complete — all layers now current
  ```
- Exit 1 → some files are still stale/missing. Print:
  ```
  WARNING: drift remains after refresh. Re-run /sync-install or inspect manually.
  ```
  Print the full residual audit output.

### 6. Print summary

```
/sync-install complete
----------------------
Layers checked : [layers]
Files refreshed: [count]
Result         : [all current | drift remains]
```

## Usage

```
/sync-install
/sync-install --check
/sync-install --layers source,project
/sync-install --layers source,global
/sync-install --check --layers source,project
```

After editing any file under `platforms/claude-code/commands/`,
`platforms/claude-code/agents/`, or `core/schemas/`, run `/sync-install` to
propagate the change to the project and global installed copies.

For CI (which cannot see the developer's global dir), use:
`python ".advanced-plans/bin/ap.py" install_audit --layers source,project`

## Error Modes

| Condition | Behaviour |
|-----------|-----------|
| `--check` passed | Audit only; no writes; exit after audit output |
| Unrecognised flag | Print usage error and stop immediately |
| Project `.claude/` dir absent | Note it (not a failure); skip project layer |
| Global `~/.claude/` dir absent | Note it (not a failure); skip global layer |
| Source file unreadable | Print error for that file; skip it; continue |
| Destination dir does not exist | Create it; then copy |
| Drift remains after refresh | Print warning; show residual audit output |

## Notes

**Source → installed only.** The copy direction is always
`source (platforms/…, core/schemas/) → installed (.claude/)`. Running
`/sync-install` will never overwrite a source file with an installed copy.

**Extra files are not removed.** Files present in an installed layer but absent
in source (verdict `extra`) are left untouched. Projects may add their own
custom commands and agents alongside the framework-provided ones.

**Idempotent.** Running `/sync-install` when all layers are already current
prints "nothing to do" and makes no changes.

**Does not commit.** Changes are left in the working tree. Commit them as part
of the normal loop-closing workflow.

**Global layer affects all projects.** Writing to `~/.claude/` refreshes the
global installed copies used by every project that consumes the framework.
`/sync-install` prints every file it changes there. Review the output before
proceeding if you are unsure which machine-global commands are appropriate to
update.
