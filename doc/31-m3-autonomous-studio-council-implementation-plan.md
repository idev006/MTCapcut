# M3 Autonomous Studio Council Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use the project build/test workflow task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first autonomous, evidence-grounded Studio Council that interprets a user brief, obtains independent specialist recommendations, synthesizes a candidate edit plan, validates provenance and records the complete run without Codex editorial intervention.

**Architecture:** A deterministic Python orchestrator supplies immutable text-only snapshots to provider-backed role engines. Every role returns a strict JSON contract; the orchestrator validates evidence references, preserves disagreements and stores the run append-only before a separate Lead Editor response can become a provider-neutral Timeline Plan. Raw media remains behind Eye/Ear engines and is never opened by brain roles.

**Tech Stack:** Python 3.14 stdlib, existing OpenAI-compatible provider adapter, SQLite Understanding Map, unittest, existing Timeline Plan validator.

## Global Constraints

- Codex may implement software but must not make production editorial decisions.
- Brain engines consume only brief snapshots, asset catalog metadata and validated Understanding Map observations.
- Each specialist call is independent; Clip Director receives all specialist outputs and cannot silently erase objections.
- Every recommendation includes role, recommendation, confidence, evidence, risks and alternatives.
- Every timeline media segment references a registered asset and a source range inside its probed duration.
- Facts/on-screen text must be traceable to brief/confirmed evidence; unresolved blockers fail closed.
- Studio runs are append-only and identify provider, model, prompt version and input snapshot hash.
- Renderer fixtures authored by developers cannot be promoted to autonomous studio evaluation.

---

### Task 1: Studio contracts and strict response validation

**Files:**
- Create: `mtcapcut/studio_contracts.py`
- Test: `tests/test_studio_contracts.py`

**Interfaces:**
- Consumes: JSON documents returned by role engines.
- Produces: `EvidenceRef`, `StudioRecommendation`, `StudioSynthesis`, `AutonomousTimelineCandidate` and strict parser functions.

- [x] Write tests rejecting missing role/evidence/risks/alternatives, invalid confidence and duplicate segment IDs.
- [x] Implement immutable dataclasses and parsers that reject unknown/malformed structures.
- [x] Run focused contract tests.

### Task 2: Append-only Studio Run ledger

**Files:**
- Modify: `mtcapcut/map.py`
- Test: `tests/test_studio_ledger.py`

**Interfaces:**
- Consumes: run metadata, role recommendations, synthesis and candidate plan JSON.
- Produces: `start_studio_run`, `append_studio_recommendation`, `complete_studio_run`, `get_studio_run`.

- [x] Test atomic records, immutable recommendations, failed/incomplete status and read-back.
- [x] Add SQLite tables with foreign keys and append-only insert methods.
- [x] Run ledger tests including reopen/recovery.

### Task 3: Evidence snapshot and authorization boundary

**Files:**
- Create: `mtcapcut/studio_snapshot.py`
- Test: `tests/test_studio_snapshot.py`

**Interfaces:**
- Consumes: project assets, current observations, brief/restriction assets and asset AI policies.
- Produces: canonical `StudioInputSnapshot` plus SHA-256.

- [x] Test deterministic ordering/hash, exclusion of raw paths from prompts, current-version observations only and remote-policy denial.
- [x] Implement canonical snapshot builder and evidence reference index.
- [x] Run focused tests.

### Task 4: Provider-backed specialist and director engines

**Files:**
- Create: `mtcapcut/studio_roles.py`
- Test: `tests/test_studio_roles.py`

**Interfaces:**
- Consumes: `StudioInputSnapshot` and existing `OpenAICompatibleProvider`.
- Produces: validated role recommendations and final synthesis.

- [x] Test role isolation, JSON-only validation, prompt-injection boundary and no raw-media content/path.
- [x] Implement engines for Intent/Insight, Story, Footage, Rhythm/Sound, Motion/Graphics, Fact/Ethics/Critical Review, Clip Director and Lead Editor.
- [x] Run focused mocked-provider tests with no network.

### Task 5: Autonomous orchestrator and candidate plan validator

**Files:**
- Create: `mtcapcut/studio_orchestrator.py`
- Modify: `mtcapcut/__main__.py`
- Test: `tests/test_studio_orchestrator.py`

**Interfaces:**
- Consumes: project ID, Understanding Map, config and provider.
- Produces: append-only run ledger plus versioned candidate Timeline Plan JSON marked `autonomous_studio`.

- [x] Test complete role order, preserved objections, invalid asset/source range rejection and failure without partial completion.
- [x] Implement orchestration and CLI `run-studio`/`show-studio-run` (persistent UI events remain a later slice).
- [x] Run focused integration tests using a scripted fake provider.

### Task 6: Real-project autonomous smoke gate

**Files:**
- Create: `workspace/road-report-001/editorial/autonomous-studio-smoke-report.md`
- Modify: `doc/17-development-status.md`
- Modify: `doc/19-progress-dashboard.md`

**Interfaces:**
- Consumes: existing authorized project assets and current map snapshot.
- Produces: a candidate plan and audit report; rendering remains blocked until provenance/quality gates pass.

- [x] Run full automated tests.
- [x] Confirm all prompt-referenced assets have explicit external-AI policy or use a loopback provider.
- [x] Execute `run-studio` through the application CLI, never by composing a plan in Codex.
- [x] Validate the candidate mechanically and inspect only structured engine outputs/provenance.
- [x] Enforce render boundary: autonomous candidate requires clean gates or append-only human approval.
- [x] Record PASS/FAIL/BLOCKED/NOT RUN without claiming world-class quality before blind review.

## Self-review

- Spec coverage: intent, multiple roles, independent recommendations, objections, SSOT, evidence, source validation, provider boundary and evaluation provenance are covered.
- Explicit exclusions: professional blind review, provider quality and publication rights cannot be proven by unit tests and remain separate gates.
- No developer-authored production timeline is permitted in Task 6.

