---
description: Audit and refresh the installed .claude/ command/agent/schema copies from the repository source. Fixes drift after any platforms/claude-code/ or core/schemas/ edit. Use --check for audit-only (no writes).
allowed-tools: Read, Write, Edit, Glob, Bash
argument-hint: "[--check] [--layers source,project|source,global|all]"
---

# /sync-install

Keeps the installed `.claude/` copies of commands, agents, and schemas in sync
with the canonical source tree in this repository. After any edit to
`platforms/claude-code/commands/`, `platforms/claude-code/agents/`,
`core/agents/`, or `core/schemas/`, run `/sync-install` to propagate changes
outward.

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

### 2. Run the install audit

Run:

```bash
python -m platforms.python.install_audit --layers [resolved_layers]
```

Capture the output and exit code.

- Exit 0 → all layers are current. Print the audit output and stop:
  ```
  /sync-install: all layers current — nothing to do
  ```
- Exit 1 → drift detected. Continue to Step 3.
- Exit 2 → argument/configuration error. Print the error and stop.

If `--check` was passed, print the full audit output and stop regardless of
exit code — do not proceed to the copy step.

### 3. Identify files to refresh

Parse the audit output for lines beginning with `  STALE` or `  MISSING`
followed by `<install_dir>/<filename>`. Construct the copy list:

**`DIVERGED` and `ORPHAN` lines are deliberately not parsed.** A `DIVERGED`
file's installed copy is the same age or newer than source, so it may hold work
source has never seen; copying over it would destroy that work, and this command
copies one way only. An `ORPHAN`/`EXTRA` file has no source counterpart at all.
Both are reported for the operator to reconcile by hand. Do not add them to the
copy list to "converge faster" — that is the data-loss path this split exists to
prevent.

For each stale or missing file:

```
source_path  = <repo_root>/<source_dir>/<filename>
project_path = <repo_root>/.claude/<install_dir>/<filename>
global_path  = <global_home>/.claude/<install_dir>/<filename>
```

where:
- `install_dir` is the directory the file installs *into*, and `source_dir` is
  the source directory it comes *from*. These are not one-to-one: two source
  directories install into `agents/`.

  | `source_dir` | `install_dir` |
  |---|---|
  | `platforms/claude-code/commands` | `commands` |
  | `platforms/claude-code/agents`   | `agents` |
  | `core/agents`                    | `agents` |
  | `core/schemas`                   | `schemas` |

  The audit report prints the *source* surface for each file, so a line reading
  `core/agents/worker.md` still copies to `.claude/agents/worker.md`. Resolve the
  source directory from the reported surface, not from the install directory.
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
python -m platforms.python.install_audit --layers [resolved_layers]
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
`platforms/claude-code/agents/`, `core/agents/`, or `core/schemas/`, run
`/sync-install` to propagate the change to the project and global installed
copies.

For CI (which cannot see the developer's global dir), use:
`python -m platforms.python.install_audit --layers source,project`

## Error Modes

| Condition | Behaviour |
|-----------|-----------|
| `--check` passed | Audit only; no writes; exit after audit output |
| Unrecognised flag | Print usage error and stop immediately |
| Project `.claude/` dir absent | Note it (not a failure); skip project layer |
| Global `~/.claude/` dir absent | Note it (not a failure); skip global layer |
| Source file unreadable | Print error for that file; skip it; continue |
| File reported `diverged` | Report only; never copy over it; operator reconciles |
| Destination dir does not exist | Create it; then copy |
| Drift remains after refresh | Print warning; show residual audit output |

## Notes

**Source → installed only.** The copy direction is always
`source (platforms/…, core/agents/, core/schemas/) → installed (.claude/)`.
Running `/sync-install` will never overwrite a source file with an installed
copy. This is why the `diverged` verdict exists: it is the auditor's way of
saying "the one supported direction is the wrong one here".

**Extra files are not removed.** Files present in an installed layer but absent
in source (verdict `extra`) are left untouched. Projects may add their own
custom commands and agents alongside the framework-provided ones. `extra` is
computed against the union of every source directory that installs into that
directory — so a `core/agents/` file is not called `extra` merely because
`platforms/claude-code/agents/` does not contain it.

**Diverged files are not overwritten.** Verdict `diverged` means the installed
copy differs from source and is the same age or newer. `/sync-install` reports
it and moves on. Reconcile it by hand — usually by copying the installed
version back into the source tree as a normal edit, reviewing it, and committing
it — then re-run `/sync-install` to propagate the reconciled source outward.

**Idempotent.** Running `/sync-install` when all layers are already current
prints "nothing to do" and makes no changes.

**Does not commit.** Changes are left in the working tree. Commit them as part
of the normal loop-closing workflow.

**Global layer affects all projects.** Writing to `~/.claude/` refreshes the
global installed copies used by every project that consumes the framework.
`/sync-install` prints every file it changes there. Review the output before
proceeding if you are unsure which machine-global commands are appropriate to
update.
