# Brief, Readiness and Editorial Governance Implementation Plan

> **For agentic workers:** Implement task-by-task with tests and a review gate after every task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent the autonomous studio from declaring a candidate ready unless it understands the typed brief, has evidence-backed media coverage, preserves independent objections, and passes deterministic private/public release gates.

**Architecture:** Add four narrow engines around the existing Studio Council: a provider-backed Brief Interpreter that produces a strict typed contract, a deterministic Brief Compliance Validator, a Media Readiness service that reports evidence coverage without opening media in the orchestration layer, and typed editorial findings whose severity controls private-preview and publication eligibility. The Lead Editor receives the typed brief and machine-readable violations and remains the only component that makes or revises editorial decisions.

**Tech Stack:** Python 3.14, dataclasses, SQLite SSOT, strict JSON Schema responses, OpenRouter/local OpenAI-compatible providers, FFmpeg evidence extraction, stdlib `unittest`.

## Global Constraints

- Codex engineers and verifies the system; it must not choose shots, story, timing, music, or copy.
- Creative decisions and revisions belong to autonomous engines and must cite SSOT evidence.
- Missing evidence remains unknown and cannot silently become a claim.
- The active brief requires 16:9, 30–35 seconds, one named music asset, private rough-cut scope, and no publication approval.
- Existing runs and decisions are append-only evidence; no historical candidate is overwritten.
- External AI receives only assets explicitly authorized by the per-asset data policy.
- UI integration remains asynchronous/event-friendly; this milestone changes engine contracts, not UI widgets.

---

### Task 1: Typed Project Brief and deterministic compliance

**Files:**
- Create: `mtcapcut/project_brief.py`
- Create: `tests/test_project_brief.py`
- Modify: `mtcapcut/studio_roles.py`
- Modify: `mtcapcut/studio_orchestrator.py`
- Modify: `mtcapcut/studio_snapshot.py`

**Interfaces:**
- Produces: `ProjectBrief`, `BriefInterpreterEngine.interpret(snapshot)`, and `BriefComplianceValidator.validate(candidate, brief, asset_catalog)`.
- Consumes: active authority observations from `StudioInputSnapshot` and strict provider output.

- [x] Write tests proving malformed brief output is rejected, 45 seconds fails a 30–35 second brief, 32 seconds passes, 16:9 is enforced, forbidden music is rejected, and private-only status blocks publication.
- [x] Run `D:\dev\MTCapcut\.venv\Scripts\python.exe -m unittest tests.test_project_brief -v` and confirm the tests fail before implementation.
- [x] Implement immutable typed fields: duration range, aspect ratio, delivery scope, required/forbidden asset selectors, required messages, tone, audience, story beats and evidence IDs.
- [x] Send only authority observations to the Brief Interpreter using a strict JSON Schema and validate every cited observation ID.
- [x] Add deterministic candidate checks that return structured findings rather than prose.
- [x] Inject the typed brief into every specialist, Clip Director and Lead Editor prompt.
- [x] Feed compliance findings to `revise_timeline`; never let orchestration code invent the repair.
- [x] Run the focused test and record PASS evidence.

### Task 2: Typed editorial findings and scoped gates

**Files:**
- Create: `mtcapcut/editorial_findings.py`
- Create: `tests/test_editorial_findings.py`
- Modify: `mtcapcut/studio_contracts.py`
- Modify: `mtcapcut/studio_roles.py`
- Modify: `mtcapcut/studio_orchestrator.py`

**Interfaces:**
- Produces: `EditorialFinding`, `FindingSeverity`, `FindingCategory`, and `compute_release_gates(findings, rights_blockers, delivery_scope)`.
- Consumes: findings emitted independently by specialist engines, deterministic validators and rights checks.

- [ ] Write tests proving a warning does not block private preview, a private blocker blocks both scopes, a publication blocker permits private preview but blocks publication, and the Clip Director cannot drop a specialist finding.
- [ ] Run the focused test and confirm RED.
- [x] Replace provider-facing untyped objection strings with strict objects containing ID, category, severity, finding, evidence, owner, recommendation, and scope flags.
- [x] Preserve the union of specialist findings deterministically outside the Clip Director response.
- [x] Compute private/public eligibility only from typed findings, rights blockers and brief delivery scope.
- [x] Run the focused test and record PASS evidence.

### Task 3: Media cognition readiness

**Files:**
- Create: `mtcapcut/media_readiness.py`
- Create: `tests/test_media_readiness.py`
- Modify: `mtcapcut/__main__.py`
- Modify: `mtcapcut/map.py`

**Interfaces:**
- Produces: `MediaReadinessService.assess()` and a JSON report with `ready`, `needs_cognition`, `policy_blocked`, `failed`, and `excluded` assets.
- Consumes: registered asset versions, current observations, policy decisions, FFmpeg evidence artifacts and `MediaCognitionEngine`.

- [ ] Write tests for observed assets, missing observations, external-policy denial, extraction failure, idempotent cache reuse and unsupported asset kinds.
- [ ] Run the focused test and confirm RED.
- [ ] Implement a read-only readiness assessment that never treats unobserved media as usable.
- [ ] Implement an explicit cognition command whose extraction strategy is deterministic and bounded by config; store only validated observations and artifact provenance.
- [ ] Reuse observations when asset hash, producer version and cognition configuration are unchanged.
- [ ] Emit progress events suitable for a non-blocking UI worker.
- [ ] Run the focused test and record PASS evidence.

### Task 4: Evidence-backed on-screen copy

**Files:**
- Create: `mtcapcut/onscreen_copy.py`
- Create: `tests/test_onscreen_copy.py`
- Modify: `mtcapcut/studio_roles.py`
- Modify: `mtcapcut/studio_orchestrator.py`

**Interfaces:**
- Produces: `CopyProposal` with `verbatim` or `faithful_condensation`, source evidence IDs and fact-review status.
- Consumes: authority observations and provider-generated copy proposals.

- [ ] Write tests proving verbatim copy passes, unsupported copy fails, faithful condensation requires an independent fact review, and rejected copy never enters the timeline.
- [ ] Run the focused test and confirm RED.
- [ ] Add a strict provider-backed Copy Engine; do not generate copy in deterministic orchestration code.
- [ ] Keep exact-substring verification for `verbatim`; require a second provider role and evidence citations for `faithful_condensation`.
- [ ] Store copy proposals and reviews in the candidate evidence bundle.
- [ ] Run the focused test and record PASS evidence.

### Task 5: SSOT persistence, migration and run lifecycle

**Files:**
- Modify: `mtcapcut/map.py`
- Create: `tests/test_studio_governance_ledger.py`
- Modify: `mtcapcut/studio_orchestrator.py`

**Interfaces:**
- Produces: append-only brief interpretations, compliance reports, readiness reports and typed findings associated with `run_id` and input hash.

- [ ] Write migration and round-trip tests against a fresh database and an existing schema.
- [ ] Run the focused test and confirm RED.
- [ ] Add additive SQLite tables/columns without rewriting historical rows.
- [x] Introduce `candidate_rejected` for exhausted revision attempts and reserve `candidate_ready` for a compliant candidate.
- [ ] Persist every revision finding and provider attempt before returning or failing.
- [ ] Run the focused test and record PASS evidence.

### Task 6: End-to-end autonomous revision and documentation

**Files:**
- Modify: `tests/test_studio_orchestrator.py`
- Modify: `doc/17-development-status.md`
- Modify: `doc/19-progress-dashboard.md`
- Modify: `doc/30-studio-autonomy-boundary.md`
- Modify: `doc/31-m3-autonomous-studio-council-implementation-plan.md`
- Create: `workspace/road-report-001/editorial/autonomous-studio-compliance-report.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: a compliant or explicitly rejected autonomous run with evidence and no hidden human/Codex editorial choices.

- [x] Add an integration test where the first provider candidate is 45 seconds and the engine-generated revision is 32 seconds.
- [x] Add an integration test where all revisions remain noncompliant and the run ends `candidate_rejected` with no output file.
- [x] Run the studio suite and then the full `unittest` suite.
- [x] Run Media Readiness against `road-report-001` using SSOT output only; do not manually inspect media.
- [ ] Run the autonomous council only after readiness and policy gates pass.
- [ ] Do not render until candidate compliance is PASS and private-preview approval requirements are satisfied.
- [ ] Update Kanban/status documents with observed evidence, risks and exact commands/results.

## Quality Gates

- Architecture boundary: PASS only if no orchestration code makes creative choices.
- Brief compliance: PASS only if duration, aspect, music, forbidden assets, required messages and delivery scope are machine checked.
- Evidence integrity: PASS only if every used source range has current observations.
- Independent review: PASS only if specialist findings cannot be suppressed by synthesis.
- Private preview: PASS only if no private blocker remains and candidate-specific approval policy is satisfied.
- Publication: PASS only if brief permits publication, rights are cleared and no publication blocker remains.
- Regression: PASS only if the full test suite passes.

## Rollback

All schema changes are additive. Disable the new orchestration path at the CLI/config boundary and retain old run records; never delete the newly written brief, finding, readiness or compliance evidence.
