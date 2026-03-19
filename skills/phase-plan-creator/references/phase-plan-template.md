# Phase Plan Template & Best Practices

## When to Create Phase Plans

Use the Phase Plan Creator skill when starting:
- A new project or major feature
- A distinct research/exploration phase
- A refactoring or migration effort
- A performance improvement cycle
- A validation or testing phase

## Template Structure

```markdown
# Phase [N]: [Descriptive Name]

## Objective
[One clear sentence expressing the phase purpose.]

**Pattern:** "[Action] [thing] [into/for] [goal]"

## Scope
### Included:
- [Concrete deliverable 1]
- [Concrete deliverable 2]

### Explicitly NOT included:
- [Out of scope item] (will be Phase [N+1])
- [Out of scope item] (handled by [team/other phase])

## Key Deliverables
List concrete artifacts with format and location:
- [Deliverable type]: [Specific description], format [X], location [Y]
- [Deliverable type]: [Specific description], format [X], location [Y]

## Success Criteria
Each criterion must be objectively verifiable:

- ✓ [Measurable outcome 1]: [How verified]
- ✓ [Measurable outcome 2]: [How verified]
- ✓ [Measurable outcome 3]: [How verified]

## Dependencies

### Must Complete Before This Phase:
- Phase [N-1]: [Name] → [Why required]
- [External task]: [Why required, timeline if known]

### Blocked By:
- [External dependency]: [Current status, ETA, or workaround]

### Optional (Nice to have):
- [Task]: [Why helpful but not blocking]

## Skills Required (Broad Categories)

Skills needed for this phase (will be refined in ralph loops):

- `[skill-domain-1]`: [Specific purpose in this phase]
- `[skill-domain-2]`: [Specific purpose in this phase]
- `[skill-domain-3]`: [Specific purpose in this phase]

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [Specific risk] | Low/Med/High | Low/Med/High | [Concrete mitigation strategy] |
| [Specific risk] | Low/Med/High | Low/Med/High | [Concrete mitigation strategy] |

## Assumptions

- `[Assumption 1]`: [Why we believe it; how we'll validate]
- `[Assumption 2]`: [Why we believe it; how we'll validate]

## Project Context (from CLAUDE.md)

Relevant patterns, conventions, or tech decisions from project:
- [Tech choice]: [Applied here as...]
- [Naming convention]: [Specific pattern]

## Notes / Design Decisions

- [Design choice]: [Why this approach over alternatives]
- [Open question]: [Will resolve in ralph loops]
- [Alternative considered]: [Why not chosen]
```

---

## Best Practices

### Objective: Goal + Domain + Approach

✅ **Good:**
```
"Migrate [system] from [old approach] to [new approach]"
"Research [domain] approaches for [problem]"
"Design [component] with [constraint/requirement]"
"Validate [system] against [benchmark]"
```

❌ **Vague:**
```
"Improve system"
"Research stuff"
"Build feature"
```

### Deliverables: Be Specific About Format & Location

✅ **Good:**
```
- Implementation: [Feature] in [language], <[lines], following [pattern]
- Documentation: [README] with [sections], plus [N] examples
- Validation report: [Format], comparing [A] vs [B] on [test set]
- Configuration: [Config file], parameters: [list]
```

❌ **Vague:**
```
- Code for [feature]
- Documentation
- Tests
```

### Success Criteria: Objective & Verifiable

✅ **Good:**
```
- [Test suite] passes with >[coverage%] coverage
- [Metric] achieves [target value] on [benchmark]
- [Component] executes [operation] in <[time]
- Code review approved by [role]
```

❌ **Vague:**
```
- Tests pass
- Performance is good
- Code is clean
```

### Risk Mitigation: Concrete Actions

✅ **Good:**
```
| Risk | Mitigation |
| [Specific failure] | Action: [concrete step]. If [condition], fallback: [alternative] |
```

❌ **Vague:**
```
| Risk | Mitigation |
| Things might go wrong | Hope it works |
```

---

## Example Phase Plans (Same Structure, Different Domains)

All three examples below follow **identical structure**. Only content changes.

### Example 1: Data Processing

```markdown
# Phase 2: ETL Pipeline Development

## Objective
Migrate [legacy integration] from [batch approach] to [scalable pipeline] with [monitoring].

## Scope
### Included:
- Pipeline: [N data sources], [specific transformations]
- Validation: [Error detection], [data quality checks]
- Monitoring: Dashboard + alerts for [failure modes]

### Explicitly NOT included:
- Real-time analytics (Phase 3)
- Archive migration

## Key Deliverables
- Implementation: [Language/framework], modular design
- Validation framework: [Specific tests for edge cases]
- Monitoring config: [Alert conditions]
- Documentation: Setup guide + troubleshooting

## Success Criteria
- ✓ Pipeline processes [N records] end-to-end without manual steps
- ✓ Data validation catches [error type] accurately
- ✓ Runtime: [full dataset] completes in <[time]
- ✓ Data integrity: Record count ±[tolerance]
- ✓ Code review approved

## Dependencies
- Phase 1: [Source systems] accessible
- External: [Production access] (pending approval)

## Skills Required
- `pipeline-engineering`: Process design
- `data-validation`: Quality checks
- `monitoring-setup`: Alerting
- `documentation`: Technical writing

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
| [Source failure mode] | Med | High | Implement [workaround]; test with [simulated failure] |
| [Framework compatibility] | Low | High | Pin stable version; test upgrades in staging |
```

### Example 2: Machine Learning

```markdown
# Phase 2: Model Validation & Optimization

## Objective
Research [optimization approaches] for [use case] and validate against [benchmark].

## Scope
### Included:
- Hyperparameter tuning: [N configurations]
- Ablation study: Impact of [specific components]
- Comparison: vs. [baseline/competitors]

### Explicitly NOT included:
- Production deployment (Phase 3)
- Dataset expansion

## Key Deliverables
- Experiment report: [Format], [N configurations tested]
- Best model: [Checkpoint], performance metrics
- Ablation analysis: Feature importance
- Recommendation: [Configuration choice] + justification

## Success Criteria
- ✓ [Metric] achieves [target] on validation set
- ✓ Outperforms baseline by [threshold]
- ✓ Ablation identifies [important features]
- ✓ All experiments reproducible: seed, split, parameters documented
- ✓ ML lead review approved

## Dependencies
- Phase 1: [Training data] prepared

## Skills Required
- `model-optimization`: Tuning, experiments
- `comparative-analysis`: Benchmarking
- `result-documentation`: Writing findings

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
| [Metric] below target | Med | High | [Alternative architecture] ready to test |
```

### Example 3: Infrastructure

```markdown
# Phase 2: System Refactoring

## Objective
Refactor [system] from [current architecture] to [new architecture] with [zero downtime].

## Scope
### Included:
- Core module rewrite: [module names], following [pattern]
- API migration: [old schema] → [new schema]
- Data migration: [format transformation]

### Explicitly NOT included:
- Frontend updates (Phase 3)
- Performance optimization (Phase 4)

## Key Deliverables
- Refactored code: [module], tests, following [pattern]
- Migration script: [old format] → [new format]
- API documentation: Endpoint reference + deprecation guide
- Rollback procedure: [Failure scenarios]

## Success Criteria
- ✓ Test suite passes (including legacy compatibility)
- ✓ Performance: [Metric] <[target]
- ✓ Zero downtime deployment: [validation method]
- ✓ Data integrity: Count ±[tolerance], [validation] passes
- ✓ Code + security review approved

## Dependencies
- Phase 1: [Dependency system] upgraded

## Skills Required
- `system-architecture`: Design patterns
- `data-migration`: ETL, validation
- `api-design`: Schema evolution
- `deployment`: Blue-green strategies

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
| Legacy dependency breaks | Med | High | Test against old versions; implement shim if needed |
| Data migration edge cases | Low | Med | Dry-run on sample; prepare rollback |
```

---

## Key Design Patterns

Use `[brackets]` to show **where your specific content goes**. This makes templates generalisable:

- `[thing]` = System, component, dataset, model name
- `[metric]` = Whatever you're measuring (accuracy, latency, throughput, etc.)
- `[format]` = PDF, markdown, code, dataset, Docker image, etc.
- `[constraint]` = Budget, time, resources, requirement
- `[team/role]` = Who needs to approve or is responsible

---

## Connecting to Ralph Loop Planning

Once your phase plan is complete and reviewed:

1. Pass it to `@ralph-loop-planner`
2. Planner will:
   - Refine broad skills → specific skills per iteration
   - Discover additional skills if needed
   - Break deliverables into N verifiable iterations
   - Generate execution-ready prompts

Example refinement:
```
Phase-level skill: `[skill-domain]`
↓
Ralph-loop-level skills:
  - `[specific-skill-1]`: [purpose]
  - `[specific-skill-2]`: [purpose]
  - `[discovered-skill]`: [why needed]
```
