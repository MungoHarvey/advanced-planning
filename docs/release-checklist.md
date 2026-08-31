# Release Checklist

What to run before cutting a release, and what each command should print.

**Every command below has been run against this repository, and the expected
output is what it actually produced** — not what it ought to produce. Where a
check is weaker than it appears, that is stated rather than hidden. A checklist
whose commands nobody has run is worse than no checklist: it manufactures
confidence without providing any.

Last verified against `v0.18.0` (`6fc3c32`), 2026-08-31.

---

## Read exit codes, not output

Several checks here print a summary line and set a meaningful exit code. **Do
not read the exit code through a pipe** — `cmd | tail -1` reports `tail`'s
status, not the command's, and will show you `0` for a command that exited `2`.

```bash
out=$(python -m platforms.python.install_audit --layers source,global 2>&1); rc=$?
echo "rc=$rc"
```

---

## Repository structure

- [ ] **Top-level directories present**

  ```bash
  ls -d core docs examples platforms setup
  ```

  Expected: all five listed. (`temp/` also exists and is scratch — nothing in a
  release should depend on it.)

- [ ] **Core layout**

  ```bash
  ls core
  ```

  Expected: `agents`, `constraints.json`, `schemas`, `skills`, `state`.

- [ ] **All adapters present**

  ```bash
  ls platforms
  ```

  Expected: `claude-code`, `codex`, `cowork`, `opencode`, `python`, `shared`.
  The first five are adapters; `shared` holds the host-neutral agent skills.

- [ ] **Installers present for the three installable adapters**

  ```bash
  ls setup/*/install.sh setup/*/install.ps1 setup/*/uninstall.sh setup/*/uninstall.ps1
  ```

  Expected: a `.sh` and a `.ps1` of each, for `claude-code`, `codex` and
  `opencode`. Both hosts must take the same decision on every path — that
  equivalence is what `test_adapter_lifecycle.py` and
  `test_uninstall_fail_closed.py` exist to hold.

- [ ] **Root files present**

  ```bash
  ls README.md CONTRIBUTING.md CLAUDE.md STRUCTURE.md LICENCE CHANGELOG.md VERSION .gitignore .github/workflows/ci.yml
  ```

---

## Portability

- [ ] **No internal session paths**

  ```bash
  grep -rn "gifted-awesome-heisenberg\|/sessions/" . \
    --include="*.md" --include="*.py" --include="*.sh" --include="*.json" \
    | grep -v '^\./\.git'
  ```

  Expected: two hits, both benign — one historical loop record in
  `.advanced-plans/phases/phase-4/loops.md`, and the grep pattern on this line
  of this file. Anything else is a real leak.

- [ ] **No secrets or credentials**

  ```bash
  grep -rn "api_key\s*=\s*['\"][^'\"]" . \
    --include="*.py" --include="*.json" --include="*.sh" \
    | grep -v "your_key\|YOUR_KEY\|placeholder" | grep -v '^\./\.git'
  ```

  Expected: zero results.

---

## Tests

- [ ] **Full suite passes**

  ```bash
  python -m pytest platforms/python/tests -q
  ```

  Expected at `v0.18.0`: **872 passed, 1 skipped** in roughly seven minutes,
  across 33 test files.

  The single skip creates a symlink, which needs Windows Developer Mode, and it
  names `WinError 1314` in its skip message. **A skip that does not name its
  reason is a defect** — a test file that skipped its whole platform half and
  reported green is how thirteen tests hid for several releases. If the skip
  count rises above one, find out which test and why before releasing.

- [ ] **The suite runs with adapter interpreters required**

  ```bash
  AP_REQUIRE_ADAPTER_INTERPRETERS=1 python -m pytest platforms/python/tests/ -q
  ```

  This is what CI runs. It fails rather than skips if `sh` or `pwsh` is absent,
  so a CI host missing an interpreter cannot report a green run over a suite
  that silently skipped its shell half.

---

## Audits

All three exit non-zero when they cannot examine their subject. That is
deliberate: before `v0.18.0` each could exit `0` having opened no files.

- [ ] **AST check**

  ```bash
  python -m platforms.python.ast_check platforms/python/ --exclude tests/ --exclude examples/
  ```

  Expected: `NONE -- 17 file(s) checked, 0 violations`, exit `0`. **Check the
  file count.** Exit `2` means no `.py` files were found, or a named path does
  not exist — the check refuses to pass on an empty subject.

- [ ] **Path convention audit**

  ```bash
  python -m platforms.python.path_audit
  ```

  Expected: `PASSED WITH 7 SUPPRESSED`, exit `0`, followed by the roots it
  actually scanned with a per-root file count — currently eleven roots. That
  list is measured, not a constant: if the total is zero, the audit exits `2`.

- [ ] **Install-layer drift**

  ```bash
  python -m platforms.python.install_audit --layers source,global
  ```

  Expected **in CI**: exit `0`, after the workflow has installed into the
  runner's global layer.

  Expected **locally**: exit `1`, `RESULT: drift detected`, unless you have
  just installed. That is the audit working — your global layer is stale
  relative to source. It is not a release blocker on its own; a drift result in
  CI is.

  An invalid `--layers` value exits `2` (`ERROR: --layers must be one of: all,
  source,global, source,project`), rather than running a comparison over
  nothing.

---

## Adapter smoke checks

- [ ] **Installer help**

  ```bash
  sh setup/claude-code/install.sh --help
  ```

  Expected: exit `0`, usage listing `--project`, `--global`, `--dry-run` and
  `--symlink`.

- [ ] **Checkpoint utility**

  ```bash
  sh platforms/cowork/checkpoint.sh --help
  ```

  Expected: exit `0`, usage listing `save`, `restore` and `list`.

- [ ] **Dry run matches the real run**

  ```bash
  T=$(mktemp -d)
  sh setup/claude-code/install.sh --dry-run --project "$T"; echo "rc=$?"
  find "$T" -mindepth 1 | wc -l
  ```

  Expected: exit `0`, a `mode: DRY RUN (no files written)` banner, a `[dry-run]`
  line per action — and **`0`** from the `find`. Checking that the directory is
  still empty is the point: a dry run is only trustworthy if you confirm it
  wrote nothing, rather than trusting the banner that says so.

  A dry run that reports work the real run would refuse is equally a false
  report. Both branches take the same decision as of `v0.18.0`;
  `test_adapter_lifecycle.py` holds that.

---

## Schemas

- [ ] **JSON state schemas are well-formed**

  ```bash
  python -c "
  import json, pathlib
  files = sorted(pathlib.Path('core/state').glob('*.json'))
  assert files, 'no schema files found -- this check examined nothing'
  for f in files:
      json.loads(f.read_text(encoding='utf-8'))
      print(f'OK: {f}')
  print(f'{len(files)} schema file(s) validated')
  "
  ```

  Expected: `6 schema file(s) validated`. The assertion matters — without it, a
  glob that matches nothing prints nothing and exits `0`.

- [ ] **Markdown schemas present**

  ```bash
  ls core/schemas
  ```

  Expected: `README.md` plus `handoff`, `phase-plan`, `ralph-loop` and `todo`
  schema documents.

---

## Documentation

- [ ] **`docs/decisions.md` records the decisions**

  ```bash
  grep -c "^## Decision" docs/decisions.md
  ```

  Expected: `10` or more.

- [ ] **CHANGELOG has a section for the version being released**, and the
  link-reference footer at the bottom names every tag that exists:

  ```bash
  for t in $(git ls-remote --tags origin | grep -o 'v[0-9.]*$' | sort -uV); do
    grep -q "^\[${t#v}\]:" CHANGELOG.md && echo "  $t ok" || echo "  $t MISSING"
  done
  ```

  Expected: `ok` for all eight tags. Note the direction — every tag needs a
  footer entry, but not every entry needs a tag: the footer runs back to
  `0.6.0`, and tagging only began at `v0.11.0`, so counting the two and
  comparing them reports a failure on correct data.

  The footer was wrong in both directions before `v0.18.0` — it named the wrong
  repository owner, so all thirteen links were dead, and it stopped five
  versions short of the tags that existed.

- [ ] **`VERSION` matches the CHANGELOG section about to be tagged**

  ```bash
  cat VERSION
  head -20 CHANGELOG.md | grep -o '\[0\.[0-9.]*\]'
  ```

---

## CI

The workflow defines **four jobs**, which report as **six required checks**
because `python-tests` is a matrix over Python 3.10, 3.11 and 3.12:

| Check | What it proves |
|---|---|
| Markdown Lint | **Nothing — see below** |
| JSON Schema Validation | `core/state/*.json` parse |
| Python Tests (3.10 / 3.11 / 3.12) | the suite passes on all three |
| Path Convention Audit | path audit clean, then install-layer drift clean |

- [ ] **All six are green on the PR before merging**

  ```bash
  gh pr view <N> --json mergeStateStatus,statusCheckRollup \
    --jq '"mergeState: \(.mergeStateStatus)", (.statusCheckRollup[]|"\(.name): \(.conclusion)")'
  ```

  Expected: `mergeState: CLEAN` and `SUCCESS` six times. An empty conclusion
  means the check is still running, not that it passed.

> **Known gap — Markdown Lint cannot fail.** The job runs
> `markdownlint-cli2 … --config .markdownlint.json || true`, and
> `.markdownlint.json` does not exist in this repository. It has reported
> `SUCCESS` on every pull request ever opened here and could not have reported
> anything else. Do not read it as evidence of anything.
>
> Measured 2026-08-31: on default rules the repository has **8,430 violations
> across all 161 markdown files**. Excluding `.advanced-plans/` and `temp/`
> (historical records nobody edits) and disabling `MD013` line-length and
> `MD060` table-column-style leaves **834 across 94 files**; of those, `--fix`
> resolves 505 mechanically and **329 remain**, 285 of them a code fence
> missing its language tag. So making this check real is roughly one mechanical
> commit plus an afternoon of tagging fences — not a rewrite.

---

## Cutting the release

This is the procedure actually used for `v0.17.0` and `v0.18.0`. `main` is
protected by the six checks above, so nothing here pushes to it directly.

1. **Branch from a green `main`.**

   ```bash
   git checkout -b release/<version> main
   ```

2. **Write the CHANGELOG section**, above the previous one and below
   `[Unreleased]`. Say what changed and why it mattered; cite the evidence that
   proves it, not the intention behind it.

3. **Bump `VERSION`** to the same number.

4. **Commit, push, open a PR** with an evidence table — the before and after of
   each claim, and the suite figure from a real run.

5. **Wait for all six checks**, then merge with a merge commit (not a squash,
   so the individual fix commits survive).

   ```bash
   gh pr merge <N> --merge
   ```

6. **Tag the merge commit and cut the Release**, taking the notes from the
   CHANGELOG section rather than rewriting them:

   ```bash
   git checkout main && git pull --ff-only
   git tag -a v<version> -m "v<version> — <one line>"
   git push origin v<version>
   gh release create v<version> --title "v<version> — <one line>" --notes-file <notes>
   ```

7. **Confirm the tag and Release exist**:

   ```bash
   git ls-remote --tags origin | grep "v<version>"
   gh release view v<version> --json tagName,name,createdAt
   ```

---

## Known gaps

Recorded rather than quietly omitted. None blocks a release; all mislead
someone eventually.

- **Markdown Lint cannot fail.** Measured above.

- **Three of five adapter READMEs have no Troubleshooting section.**
  `platforms/claude-code` and `platforms/cowork` do; `codex`, `opencode` and
  `python` do not.

  ```bash
  grep -l -i "Troubleshooting" platforms/*/README.md
  ```

- **`platforms/claude-code/install.sh` still has the `--symlink` defect that
  `v0.18.0` fixed in the other two installers.** Installing over a project that
  already has a real `.claude/skills/<name>/` directory produces a nested
  `<name>/<name>` symlink inside it, exits `0`, and prints `✓ Symlinked
  <name>` — a success message for work it did not do. The skill is not where
  the host will look for it, and nothing says so.

  ```bash
  T=$(mktemp -d); mkdir -p "$T/.claude/skills/plan-todos"
  sh setup/claude-code/install.sh --project "$T" --symlink; echo "rc=$?"    # 1, names the path
  sh platforms/claude-code/install.sh --project "$T"; echo "rc=$?"          # 0, nests the link
  find "$T/.claude/skills/plan-todos" -maxdepth 1
  ```

  Not destructive — pre-existing files survive — but the install is silently
  broken. This is the third adapter (F11): it is *not* an unmaintained
  leftover, which is worth stating because its 280 lines beside the `setup/`
  installer's 674 invite that assumption. It is covered by
  `test_ap_launcher.py` and `test_home_resolution_agreement.py`, it writes a
  `runtime.json`, `platforms/claude-code/README.md` documents it as the install
  path, and `v0.17.0` fixed a `SCRIPT_DIR`/`REPO_ROOT` bug in it. It was simply
  not in scope when S3 was fixed, so it kept the old behaviour.
