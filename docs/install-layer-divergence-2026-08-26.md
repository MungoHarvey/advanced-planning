# Install-layer divergence audit — 2026-08-26

**Source**: `M:\Coding\planning\advanced-planning` (this repository)
**Installed**: `C:\Users\mharvey2\.claude\{commands,agents,schemas}` (global layer)
**Method**: line-normalised diff (CRLF→LF) of every file present in both, plus
frontmatter/heading characterisation of every file present in only one.
**Backups**: the global layer was copied in full (40 files) before anything was
inspected, and again before the reconciliation described below.

---

## Correction — read this first

An earlier draft of this document opened with:

> *"The global layer is the real system. The source repository is a stale
> snapshot of an earlier design."*

**That was wrong, and it was wrong for an embarrassing reason.** The audit
compared the global layer against a *local checkout that was 147 commits behind
`origin/main`*. The "earlier design" the source tree appeared to be stuck in was
simply `origin/main@e199cca`. Fetching moved `origin/main` to `02b4b86`
(v0.16.0), which already contained essentially all of the 1,590 lines the audit
had attributed to "design evolution happening only in the global layer": the
Codex gating path, bounded remediation, resume detection, and the hard
contracts.

The global layer was not ahead of the framework. It was ahead of *one stale
clone of it*, which is a different and far less interesting claim.

The tiering (A: mechanical migration, B: design evolution, C: regressions) and
the per-file diff characterisation below are left intact because the *method*
was sound and the per-file evidence is still accurate as a description of the
two trees compared. What does not survive is the conclusion drawn from it.

**Nothing was lost.** The error was caught before any push. The remedy was to
branch fresh from `origin/main` and carry over only what upstream genuinely
lacked.

### The lesson worth keeping

*Fetch before you diagnose divergence.* A comparison against an unfetched
checkout cannot distinguish "the other copy is ahead of the design" from "my
copy is behind the design", and those call for opposite actions. The audit was
methodologically careful and still reached the wrong answer, because the
carefulness was all downstream of an unchecked premise.

---

## What the audit did establish

Three real gaps survived the correction, because upstream did not have them
either. All three are fixed in the commit that carries this document.

### 1. `STALE` and `DIVERGED` are different questions

`/sync-install` parses `STALE` and `MISSING` lines out of the audit report into
its copy list, and copies **source → installed only**. The auditor previously
called every content difference `stale`, which asserts the source is ahead. So
an installed file holding work the source tree had never seen was reported as
`STALE` and then silently overwritten by the next sync — the one direction that
loses data, arrived at through the sync command's own documented procedure.

The verdict is now split by mtime:

| Condition | Verdict | `/sync-install` |
|---|---|---|
| identical content | `current` | — |
| differs, source strictly newer | `stale` | refreshes it |
| differs, installed newer | `diverged` | reports, never copies |
| differs, mtimes tie | `diverged` | reports, never copies |
| differs, mtime unreadable | `diverged` | reports, never copies |

A tie resolves to `diverged` deliberately: a tie is not evidence the source is
ahead. The 2-second tolerance exists because a copy preserves no mtime exactly
across filesystems, and an exact comparison would flip verdicts on rounding.

### 2. `core/agents/` was an unaudited surface

`core/agents/` and `platforms/claude-code/agents/` are two source directories
that both install into `.claude/agents/`. Only the second was in `SURFACES`. So
`core/agents/` drift was invisible, and every installed file originating from it
was written off as `extra` — hiding 161 lines of genuine drift, including the
re-gate isolation rule.

The fix has two halves, and the second is the one that is easy to miss: `extra`
must be computed against the **union** of names claimed by every source
directory mapping to a given install directory. Compute it per-surface and the
two agent surfaces denounce each other's files.

### 3. `ralph-loop.schema.md` documented one mode twice

Single-file and individual-file mode both pointed at
`.advanced-plans/phases/phase-{N}/loops.md`. Individual-file mode now reads
`phase-{N}/ralph-loop-{NNN}.md`, matching the loop naming convention the same
file defines four lines later.

---

## The reconciliation, and a live worked example

The global layer was re-synced from `origin/main` — with two files deliberately
left alone. That split is the whole argument for the `diverged` verdict, so it
is worth recording precisely.

Ten global files differed from `origin/main`:

- **Eight** had been written earlier that day by a `/sync-install` run against
  the stale checkout. Their content came from a 147-commit-old snapshot. These
  were restored from `origin/main`.
- **Two** — `commands/new-phase.md` and `commands/next-loop.md` — predate the
  session entirely and hold real local customisation: branch-scoped phase naming
  for parallel research branches under `git worktree`
  (`experiment/<slug>` → `phase-<short>-N`, plus a foundation-phase safety
  check). Upstream has no equivalent. **These were left untouched.**

The old auditor reports all ten identically as `STALE`, which would have fed all
ten to `/sync-install` and destroyed the two customised files. The new auditor
reports all ten as `DIVERGED` and copies none of them, leaving the operator to
make exactly the distinction above by hand.

After reconciliation the global layer audits as 25 current, 2 diverged, 0
missing — the two being the customisations, correctly and permanently flagged
as needing a human decision rather than a copy.
