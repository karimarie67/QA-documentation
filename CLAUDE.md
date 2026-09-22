## Agent skills

### Issue tracker

Issues are tracked as GitHub Issues in this repo (karimarie67/QA-documentation), via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role label vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), applied as-is. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at the repo root). See `docs/agents/domain.md`.

<!-- atlas-v3:guidance:start -->
## Workspace framing

Atlas workspace: **QA-documentation**. Confirmed repositories:

- `QA-documentation` at `.`; base `main`; source host `github`.

When isolation or parallel delivery benefits from worktrees, they live beneath
`.claude/worktrees/<work-package>/<repository-id>/`. The frontier
orchestrator chooses direct checkout, worker worktrees, and an optional
integration worktree from the dependency, concurrency, file-ownership, and
shared-state risks. Never place worktrees beneath `.atlas/`. Each affected
repository keeps its own base SHA, branch, verification result, and pull request.

## Repository framing

**QA-documentation** — a generic, site-agnostic Playwright QA automation Framework template: test suites, a CI-driven QA metrics dashboard, and process documentation, instantiated per client Engagement.

### Structure

- `tests/` — Playwright spec files (smoke, regression, error handling, documentation, download/search, link-checker tests) plus `tests/unit/` unit tests
- `docs/` — Atlas agent docs and remaining process documentation
- `dashboards/` — QA metrics dashboard generator and published dashboard, auto-committed by CI after each run
- `scripts/` — Support scripts, including the `template-check` structural smoke check
- `test-results/` — Evidence root: Playwright HTML/JSON reports and captured output
- `examples/` — trimmed, non-live Examples of the Framework from closed Engagements, kept for reference; not discoverable by the tracked `playwright.config.js`

### Repository-specific rules

- dashboards/ is auto-committed directly to main by the qa-test.yml CI workflow (github-actions[bot]) after every test run. Expect frequent upstream commits touching only that path; rebase/pull before pushing.
- staging and production are Playwright project names (deploy targets in playwright.config.js), not git branches. Do not treat them as protected branches.

## Atlas repository workflow

Use the lightest route that fits:

- Small, clear change: `/implement <description-or-spec>` then verify.
- Normal feature: `/grill-with-docs` → optional prototype → `/to-spec` → optional `/to-tickets` → `/atlas-red-team` when required → optional `/atlas-plan <ticket-epic-or-spec>` → `/atlas-implement`.
- Huge or unclear effort: `/wayfinder`, then rejoin at the spec route.
- Existing ticket, epic, or stable spec: optional `/atlas-plan <work-package>` → `/atlas-implement <work-package>`.

Run `/atlas-plan` and `/atlas-implement` using the most capable approved
frontier-grade model available. These commands reserve frontier capacity for
planning, orchestration, review, and final verification; implementation
delegates tightly specified or mechanical work to the least expensive capable
worker model.

Managed work uses `/atlas-implement <ticket-or-epic-or-spec>`. A frontier
orchestrator chooses the execution structure and delegates bounded deliverables
when useful. It uses the least expensive capable worker model per delegation;
tight, mechanical packets favor cheaper models, while final review and
verification judgment stay with the frontier orchestrator. Implementation
workers read and follow the supported Matt Pocock implementation skill source
while deferring its final review step. Size alone is never a reason to stop.

## Repository policy and contract model

`CLAUDE.md` is the agent entry point and cross-cutting policy router. Team-owned
documents under `docs/agents/` are authoritative for their named scope. Within
a document that classifies entries, the classification determines authority;
recommendations and repository facts do not silently become mandatory policy.
Tickets and specs remain stable work-package contracts. Planning resolves the
applicable repository policy and facts into technical plans and execution
packets. Generic skills provide reusable mechanics and do not override
repository policy.

Setup initializes `docs/agents/*`; the team owns those files afterward. A setup
rerun refreshes only the managed sections Atlas itself last wrote, preserves any
section the team has edited, and reports every preserved edit in `plan` and
`verify` output.

- Before any tracker read, write, comment, claim, or transition, read and follow
  `docs/agents/issue-tracker.md`.
- Before creating, classifying, prioritizing, or decomposing tickets, read and
  follow `docs/agents/triage-labels.md`.
- Before clarifying, researching, prototyping, specifying, decomposing,
  technically planning, or red-team reviewing proposed work, read and follow
  `docs/agents/planning.md`. This includes `/grill-with-docs`, Wayfinder,
  planning prototypes, `/to-spec`, `/to-tickets`, and `/atlas-plan`.
- During planning, read `docs/agents/domain.md` when the work introduces or
  changes domain concepts and resolve conflicting terminology in the plan.
- Before writing acceptance criteria, Definition of Done, fixtures, or
  verification steps, read `docs/agents/testing.md`.
- During planning, read `docs/agents/tooling.md` when work depends on a detected
  capability and resolve the applicable tool into the execution plan.
- Before changing Claude permissions, Atlas hooks, git hooks, or guardrail
  policy, read `docs/agents/guardrails.md` and obtain human approval.

Execution workers receive resolved decisions, exact verification commands, and
the evidence location in their task packet. Do not make execution workers
reread planning, tracker, triage, domain, testing, or tooling guidance.

## Atlas planning contract

- Invoking `/atlas-implement` approves the fixed work-package contract and any
  existing technical plan. When the contract is content-complete but no plan
  exists, the frontier orchestrator derives the execution plan without inventing
  missing product or architectural decisions.
- `/atlas-plan` is optional. Read `docs/agents/issue-tracker.md` for the
  project's configured readiness, availability, claim, transition, and
  writeback policy; do not infer those rules here.

## Atlas guardrails

- Protected branches by repository: `QA-documentation:main`, `QA-documentation:develop`, `QA-documentation:master`. Changes land through each repository's configured PR.
- Never merge a PR. Follow `docs/agents/issue-tracker.md` for human-only tracker actions.
- Never read or write live secret files. Use `.example` or `.template` files and ask a human to populate live values out of band.
- Never force-push, bypass hooks, destroy uncommitted work, repoint remotes, or weaken guardrails.
- Cloud tools detected/configured: none detected. Mutating cloud and infrastructure actions are denied by default.
- Guardrail exceptions must be durable, attributable, narrow, environment-specific, and time-bounded.
- Claude permission precedence is `deny` over `ask` over `allow`, regardless of
  specificity. Permission modes that suppress prompts can bypass an `ask`; they
  do not override a `deny` or an enforcement hook.
- Installed guardrail files are self-protected. A Claude file-tool edit to one
  prompts for human approval; ask Claude Code to run the `setup-atlas` skill's
  adopt step (not a full setup or refresh) to record it so verification treats
  it as a sanctioned customization rather than tampering.
- Activation, failure behavior, transcript retention, and troubleshooting are in
  `docs/agents/guardrails.md`.
<!-- atlas-v3:guidance:end -->
