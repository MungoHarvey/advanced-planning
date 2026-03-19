# Release Checklist

Pre-publication checklist for the Advanced Planning System v8 open-source release. Each item is verifiable with the command or action shown.

---

## Repository Structure

- [ ] **Core directories present**
  ```bash
  ls core/schemas core/skills core/agents core/state
  # Expected: non-empty directories for each
  ```

- [ ] **All three adapters present**
  ```bash
  ls platforms/claude-code platforms/cowork platforms/python
  ```

- [ ] **Docs suite present**
  ```bash
  ls docs/
  # Expected: architecture.md, concepts.md, getting-started.md,
  #           model-tier-strategy.md, adapting-to-new-platforms.md,
  #           decisions.md, release-checklist.md
  ```

- [ ] **Root files present**
  ```bash
  ls README.md CONTRIBUTING.md LICENCE .gitignore .github/workflows/ci.yml
  ```

---

## Portability

- [ ] **No internal session paths**
  ```bash
  grep -r "gifted-awesome-heisenberg\|/sessions/" . \
    --include="*.md" --include="*.py" --include="*.sh" --include="*.json" \
    | grep -v plans/phase-4-ralph-loops.md
  # Expected: zero results
  ```

- [ ] **No secrets or credentials**
  ```bash
  grep -r "api_key\s*=\s*['\"][^'\"]" . \
    --include="*.py" --include="*.json" --include="*.sh" \
    | grep -v "your_key\|YOUR_KEY\|placeholder"
  # Expected: zero results
  ```

- [ ] **No deprecated stubs**
  ```bash
  find . -type d -name "phase-plan-creator-mh" -o -name "phase-plan-creator-claude"
  # Expected: zero results
  ```

---

## Code Quality

- [ ] **All Python tests pass**
  ```bash
  python -m pytest platforms/python/tests/ -v
  # Expected: 40 passed, 0 failed
  ```

- [ ] **JSON schema files are valid**
  ```bash
  python -c "
  import json, pathlib
  for f in pathlib.Path('core/state').glob('*.json'):
      json.loads(f.read_text())
      print(f'OK: {f}')
  "
  # Expected: OK for each file, no exceptions
  ```

- [ ] **checkpoint.sh works**
  ```bash
  sh platforms/cowork/checkpoint.sh --help
  # Expected: usage output with save/restore/list subcommands
  ```

- [ ] **install.sh works**
  ```bash
  sh platforms/claude-code/install.sh --help
  # Expected: usage output with --project/--global/--reference flags
  ```

---

## Documentation

- [ ] **getting-started.md: all commands are shown verbatim**
  Read `docs/getting-started.md`. Every command a developer needs to run should be in a fenced code block.

- [ ] **concepts.md: every term used in other docs is defined**
  Read `docs/concepts.md`. Cross-check against terms in `docs/architecture.md` and the adapter READMEs.

- [ ] **decisions.md: at least 8 decisions**
  ```bash
  grep -c "^## Decision" docs/decisions.md
  # Expected: 8 or more
  ```

- [ ] **All adapter READMEs have troubleshooting sections**
  ```bash
  grep -l "Troubleshooting" platforms/*/README.md platforms/cowork/README.md
  # Expected: each adapter README listed
  ```

---

## Colleague Review

- [ ] **A colleague has cloned a fresh copy of the repository and followed `docs/getting-started.md` without additional guidance**
  - [ ] Install step succeeded (`install.sh --project`)
  - [ ] `/new-phase` produced a phase plan
  - [ ] `/next-loop` ran a loop to completion
  - [ ] No steps required assistance beyond reading the docs

- [ ] **Colleague has reviewed `docs/concepts.md` and confirmed terms are clear to a newcomer**

---

## Final Verification

- [ ] **CI is green on the main branch**
  Check `.github/workflows/ci.yml` — all three jobs (markdown-lint, schema-validation, python-tests) should pass.

- [ ] **Repository has no uncommitted changes**
  ```bash
  git status
  # Expected: nothing to commit, working tree clean
  ```

- [ ] **LICENCE contains the correct year and author**
  ```bash
  grep "Copyright" LICENCE
  # Expected: Copyright [year] [author name]
  ```

---

## Post-Release

After making the repository public:

- Update the `install.sh` GitHub URL from `your-org/advanced-planning` to the real URL
- Update the README badge placeholders with real CI badge URLs
- Tag the release: `git tag v8.0.0 && git push --tags`
- Announce to colleagues for initial feedback before broader promotion
