# change-driven-dev — Implementation Task List for Copilot

This document is an actionable, ordered backlog for implementing the full project.
It assumes the repo already contains:
- `/COPILOT_TASK.md`
- `/PROMPTS/planner.md`
- `/PROMPTS/architect.md`
- `/PROMPTS/coder.md`
- `/docs/DECISIONS.md`
- `/docs/SECURITY.md`

Conventions:
- Each task is atomic, reviewable, and should result in a PR/commit.
- Do not implement beyond task scope.
- Respect approvals/CR rules conceptually even while bootstrapping.
- “UI-first” means: always keep the UI runnable; ship thin vertical slices early.

---

## EPIC 0 — Repo bootstrap (must be first)

### T0.1 — Create repo structure
**Goal:** Create folders/files for backend, UI, docs, templates.
**Acceptance:**
- Directory tree matches contract (autobuilder/app, core, engines, plugins, state, server, ui, templates).
- `pyproject.toml` exists (Python 3.11), with formatting/lint/test tooling.
- `ui/` is a Vite+React project, builds and runs.
**Notes:** No logic yet.

### T0.2 — Add README v1 (engineering tone)
**Acceptance:**
- README describes philosophy (change-driven, approvals, CR, gates, engine-agnostic).
- Contains “Quickstart (dev)” with backend+ui run commands.
- Mentions security constraints and non-goals.

### T0.3 — Add dev scripts and Makefile
**Acceptance:**
- `make dev` runs backend + UI (or docs describe two terminals).
- `make test`, `make lint`, `make fmt` exist (or equivalent).
- `pre-commit` config optional.

---

## EPIC 1 — Persistence layer (SQLite) + DAO

### T1.1 — Implement DB connection and migrations bootstrap
**Acceptance:**
- `autobuilder/state/db.py` provides sqlite connection helper.
- DB file location is configurable for dev, default to per-project path.
- Create schema on startup (simple migrations ok).

### T1.2 — Implement schema/models (tables)
**Acceptance:**
- Tables exist per contract: projects, artifacts, tasks, task_versions, change_requests, runs, control_state.
- Foreign keys + indexes for lookup (project_id, task_id).

### T1.3 — DAO layer for projects/tasks/artifacts/CR/runs
**Acceptance:**
- CRUD functions for each entity.
- Unit tests cover basic create/read/update flows.

---

## EPIC 2 — Event bus + logging

### T2.1 — Implement internal event bus
**Acceptance:**
- `autobuilder/core/events.py` supports publish/subscribe.
- Events are persisted (optional v1) or at least emitted to WS.

### T2.2 — Structured logging + run log files
**Acceptance:**
- Each run has log file path recorded as artifact.
- Logs include timestamps and event types.

---

## EPIC 3 — FastAPI backend (REST + WS)

### T3.1 — Create FastAPI app skeleton
**Acceptance:**
- `/api/health` returns OK.
- CORS configured for UI dev.

### T3.2 — Projects endpoints
**Acceptance:**
- Create/list/get project.
- Project contains: name, root, phase, default_engine.
- Emits `project_updated` events.

### T3.3 — Tasks endpoints (read-only first)
**Acceptance:**
- List tasks and get task details, including active version.
- Emits `task_updated` events.

### T3.4 — Artifacts endpoints
**Acceptance:**
- List artifacts, download/view raw file content for small artifacts.

### T3.5 — WebSocket stream
**Acceptance:**
- `WS /ws/projects/{name}` streams events.
- UI can connect and receive `project_updated`, `task_updated`, `run_log`.

---

## EPIC 4 — UI MVP (UI-first)

### T4.1 — UI skeleton + routing
**Acceptance:**
- Pages: Dashboard, Project, Tasks, Run Console placeholders.
- API client module with typed calls.

### T4.2 — Dashboard: list/create/select project
**Acceptance:**
- Can create project from UI (name + spec text or file upload).
- Shows phase and summary counters.

### T4.3 — Task Board (read-only)
**Acceptance:**
- Kanban columns render from task status.
- Task drawer shows versions and approvals state.

### T4.4 — Live updates via WebSocket
**Acceptance:**
- UI updates when backend emits events (no refresh needed).

---

## EPIC 5 — Spec handling + artifacts

### T5.1 — Spec storage and versioned artifacts
**Acceptance:**
- Spec is stored in project root (e.g., `spec.md`).
- Each edit in UI creates an artifact record with content snapshot.

### T5.2 — Artifact service
**Acceptance:**
- `autobuilder/core/artifacts.py` can write/read artifacts, compute sha256 optionally.
- Artifacts listed in UI.

---

## EPIC 6 — Planner orchestration (no coding)

### T6.1 — EngineBase interface + session model
**Acceptance:**
- `autobuilder/engines/engine_base.py` defines the adapter interface.
- Engine events are normalized.

### T6.2 — Copilot CLI engine adapter (minimal)
**Acceptance:**
- Can start a session, stream text output, stop session.
- Transcript is saved as artifact.

### T6.3 — Planner phase runner
**Acceptance:**
- `POST /phase/plan` triggers planner run.
- Produces `plan.json` artifact.
- Creates DRAFT tasks + task_versions in DB based on plan.
- Emits events for artifacts and task creation.

### T6.4 — Planner UI page
**Acceptance:**
- Shows plan.json.
- Shows planner questions list (even if empty).
- Button: Re-run planner.

---

## EPIC 7 — Architect orchestration (options + ADR)

### T7.1 — Architect phase runner
**Acceptance:**
- `POST /phase/architect` triggers architect run.
- Produces `architecture.json` artifact and ADR markdown artifacts.
- Refines tasks (still DRAFT): deps, suggested gates, priorities.

### T7.2 — Architecture options selection
**Acceptance:**
- Endpoint to set selected option.
- UI can compare 2–3 options and select one.
- Selection stored in projects.selected_arch_option_id.

---

## EPIC 8 — Task governance (versions + CR + approvals)

### T8.1 — Change Request API + model enforcement
**Acceptance:**
- Create CR (draft/submitted) for task edits, gates changes, deps changes, engine changes.
- Approve/reject/apply CR flows.

### T8.2 — Task edit -> new TaskVersion
**Acceptance:**
- Editing task creates CR and new task_version, sets active_version_id.
- History preserved.

### T8.3 — Split task
**Acceptance:**
- Split creates two new tasks with inherited gates/acceptance, links via CR metadata.

### T8.4 — Merge tasks
**Acceptance:**
- Merge creates one new task version or new task, marks old ones superseded (metadata).

### T8.5 — Approvals gate
**Acceptance:**
- Approve all / approve single task endpoints.
- Implementation endpoints must hard-block if no approved tasks exist.

### T8.6 — UI: CR + version history
**Acceptance:**
- Task drawer shows versions and CR timeline.
- Buttons: edit/rewrite, split, merge, approve/unapprove.

---

## EPIC 9 — Sandbox + allowlist + command runner

### T9.1 — Project config.yaml + allowlist evaluator
**Acceptance:**
- Default config created per project.
- Allowlist supports patterns and explicit commands.
- No network commands by default.

### T9.2 — Sandbox file IO guards
**Acceptance:**
- Safe path resolver prevents escaping project root.
- Violations emit security events and block.

### T9.3 — Command runner with timeouts
**Acceptance:**
- Executes commands in project dir only if allowlisted.
- Captures stdout/stderr as artifacts/log events.
- Enforces per-command timeout.

---

## EPIC 10 — Gates system (authoritative)

### T10.1 — GateSpec and gate runner
**Acceptance:**
- GateSpec supports shell + python callable (optional).
- Gates are executed only by orchestrator via sandbox runner.

### T10.2 — Gates configuration lifecycle
**Acceptance:**
- Gates stored per task (gates_json) and/or project default.
- Any gate changes require CR + approval.

### T10.3 — UI: Gate results panel
**Acceptance:**
- Run Console shows gate outcomes and failure details.

---

## EPIC 11 — Coder orchestration (approved tasks only)

### T11.1 — Context bundle builder
**Acceptance:**
- Creates artifact containing: task active version, arch summary, relevant files, last failures, safety rules.
- File selection uses plugin hints + heuristics.

### T11.2 — Coder run loop (auto/step)
**Acceptance:**
- Picks next APPROVED + PENDING task with deps satisfied.
- Sets IN_PROGRESS, runs engine session.
- After engine returns, orchestrator runs gates.
- Marks PASS and commits on success.
- Updates attempts/FAIL_STUCK on repeated failure.

### T11.3 — Control state: pause/continue/limits
**Acceptance:**
- Pause stops starting new work and can interrupt engine session.
- Continue resumes.
- Limits can be changed on the fly and are persisted.

### T11.4 — Mid-run rework + engine switch
**Acceptance:**
- Rework action pauses run, sets PAUSED_FOR_REVIEW, requires CR apply.
- Engine switch pauses run and restarts task using new engine.

### T11.5 — UI: Run Console live telemetry
**Acceptance:**
- Shows current task, engine, attempt number, timers, last diff, last gate status.
- Controls work in real time.

---

## EPIC 12 — Git integration

### T12.1 — Git init per project
**Acceptance:**
- Git repo initialized (if not already).
- `.gitignore` includes `.autobuilder/` state optionally, but consider keeping DB out of git.

### T12.2 — Commit after PASS
**Acceptance:**
- Commit message: `feat(task-<id>): <title>`
- If task is non-feature (fix/change), adjust prefix.

---

## EPIC 13 — Plugins (Generic first)

### T13.1 — Plugin registry + Generic plugin
**Acceptance:**
- Registry can load plugin by name.
- Generic plugin scaffolds minimal `src/ tests/ docs/` and README.

### T13.2 — File selection hints
**Acceptance:**
- Plugin can provide globs for context bundle selection.

---

## EPIC 14 — Codex engine adapter (real or stub)

### T14.1 — Codex adapter
**Acceptance:**
- Implements EngineBase interface.
- If no API/CLI configured, it clearly errors with guidance but keeps selection available.

### T14.2 — UI: engine picker
**Acceptance:**
- Per project default engine and per task override.
- Stored in DB and used by run loop.

---

## EPIC 15 — Hardening, docs, demo, and “borrowed UX patterns”

### T15.1 — Artifacts-centric UI improvements
**Acceptance:**
- Artifacts tab shows plan/arch/ADR/transcripts/diffs.
- Filters by type, sorted by recency.

### T15.2 — Audit trail
**Acceptance:**
- Every CR and apply action emits artifact (CHANGELOG) summarizing before/after.

### T15.3 — Demo project
**Acceptance:**
- `demo/spec.md` produces 5–8 tasks.
- Demo exercises: replan, arch option select, task split, engine switch, gate failure recovery.

### T15.4 — Security docs and safe mode
**Acceptance:**
- SECURITY.md covers allowlist + sandbox.
- Config supports safe/dev mode toggle.

### T15.5 — Release checklist
**Acceptance:**
- `docs/RELEASE_CHECKLIST.md` with steps to run, test, and demo.

---

## EPIC 16 — “PR-ready” milestones (recommended)

Milestone 1: UI + DB + read-only flows (Epics 0–4)  
Milestone 2: Planner/Architect artifacts + options (Epics 5–7)  
Milestone 3: Governance (CR/versions/approvals) (Epic 8)  
Milestone 4: Execution (sandbox/gates/coder) (Epics 9–12)  
Milestone 5: Engines + polish + demo (Epics 13–15)  

END
