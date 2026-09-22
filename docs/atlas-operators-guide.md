<!-- atlas-v3:operators-guide:start -->
# How Atlas works here

Atlas is a set of Claude Code plugins. It gives coding agents one route through
planned, checked work. This guide says what Atlas does in this repository, and
what it does in your issue tracker.

This guide is for the people who run the work. `CLAUDE.md` and the documents
under `docs/agents/` hold the same rules, written for the agents. Read those
when you need the exact wording.

Setup wrote files in this repository. Setup wrote nothing in your issue
tracker. The upstream Matt Pocock setup also wrote only files. Part two says
what Atlas will write on a ticket later, while it does the work.

## Part one: what Atlas does in this repository

### This workspace

| Item | Value |
|---|---|
| Workspace name | QA-documentation |
| What this repository is for | A generic, site-agnostic Playwright QA automation Framework template: test suites, a CI-driven QA metrics dashboard, and process documentation, instantiated per client Engagement. |
| Folder for proof of work | `test-results` |

Atlas may change the repositories below, and nothing else.

| Repository | Path | Base branch |
|---|---|---|
| `QA-documentation` | `.` | `main` |

A *base branch* is the line of work that new work starts from. Atlas starts
each new branch from it. Atlas opens one pull request for each repository it
changes. A *pull request* is a request to merge a branch, which a person
reviews.

### The checks that prove a change

Atlas runs these commands to prove that a change works.

| Check | Command | What it covers | When it runs | Status |
|---|---|---|---|---|
| test | `npm run test` | Full Playwright suite under tests/ | Before PR and after implementation | inferred |
| unit | `npm run test:unit` | Unit tests for the Site config layer | On every push/PR to main/develop, as part of the automatic gate | inferred |
| template-check | `npm run test:template-check` | Structural smoke check that the template's config/spec files are intact | On every push/PR to main/develop, as part of the automatic gate | inferred |
| smoke | `npm run test:smoke` | Critical-path validation (tests/smoke_tests.spec.js) | Manual dispatch only, pending real Site config (playwright.config.js's placeholder baseURLs) | inferred |
| regression | `npm run test:regression` | documentation, download/search, and error-handling suites | Manual dispatch only, pending real Site config (playwright.config.js's placeholder baseURLs) | inferred |
| links | `npm run test:links` | Link-checker suite | Local only (no CI job) | inferred |

`verified` means setup ran the command here and it worked. `inferred` means the
repository names the command, but setup did not run it. `unavailable` means the
check does not exist yet.

Atlas saves the proof of each run in the folder named above. It clears that
folder when a new piece of work starts, so the folder holds proof of the
current work only. Atlas commits the proof with the change, then links to it
from the pull request.

### The guardrails

A *guardrail* is an automatic check that stops a risky action before it runs.
It runs outside the conversation, so words in the conversation cannot turn it
off. It catches the direct forms of these actions. It is a safety net, not a
full guarantee, so a person still reviews every change.

Atlas stops these actions here:

- reading or writing a file that holds a live password, key, or token;
- pushing straight to a protected branch, which is a branch nobody may change directly;
- merging a pull request;
- force-pushing, deleting a remote branch, or throwing away unsaved work;
- changing where this repository sends its code;
- changing a cloud or infrastructure resource;
- making a guardrail weaker.

A person can approve one exception. The record must name the approver, the
exact action, the environment, the scope, and the end date.

### The documents Atlas generated

Atlas wrote one document for each policy below. The agents read them before
they act. Your team owns these files now: edit one, and Atlas keeps the edit.

| Document | What it holds |
|---|---|
| `docs/agents/issue-tracker.md` | How Atlas reads your tracker, and what it may change there |
| `docs/agents/planning.md` | What Atlas must settle before it plans a piece of work |
| `docs/agents/testing.md` | Which checks prove a change, and what counts as proof |
| `docs/agents/tooling.md` | Which extra tools this repository may use, and when |
| `docs/agents/guardrails.md` | How the guardrails work, and how to change them |

Two more documents come from another setup. Atlas can point at them, but Atlas
does not write them.

| Document | What it holds | Comes from |
|---|---|---|
| `docs/agents/domain.md` | The words this project uses, and what each one means | `/setup-matt-pocock-skills` |
| `docs/agents/triage-labels.md` | The labels that sort and rank new tickets | `/setup-matt-pocock-skills` |

### How work reaches Atlas

Use the lightest route that fits the work.

- A small, clear change: run `/implement`, then check the result.
- A normal feature: run `/grill-with-docs`, then `/to-spec`, then `/to-tickets`, then `/atlas-implement`.
- A large or unclear effort: run `/wayfinder` first, then follow the feature route.
- A ticket, an epic, or a settled spec: run `/atlas-plan` for a written plan first, then `/atlas-implement`.

An *epic* is a parent ticket with child tickets. A *spec* is a written
statement of the work, kept in this repository.

## Part two: what Atlas does in your issue tracker

Atlas writes on a ticket only while it works on that ticket. It changes nothing
else on your board.

### The order work moves through

Work moves through your own states in the order below. A *state* is the status
on your board.

| Step | State | What it means | Who moves work into it |
|---|---|---|---|
| 1 | `Backlog` | New issue captured, not yet scoped or prioritized | Atlas |
| 2 | `To Do` | Scoped and queued; used for both planning and plan-review phases (differentiated by comment) | Atlas |
| 3 | `In Progress` | Implementation active; used for both build and Atlas self-review phases (differentiated by comment) | Atlas |
| 4 | `In QA` | QA tester verifying the fix against repro steps; human-only transition | A person only |
| 5 | `Done` | QA verified the fix and closed the issue; human-only transition | A person only |

A state marked *A person only* is one Atlas never moves work into. A person
makes that move.

### Where plans go

| Question | Answer |
|---|---|
| Where Atlas keeps a plan | On the ticket, as a comment |
| A plan arrives as a draft for approval | yes |

If a plan arrives as a draft, a person approves it before Atlas builds from it.
Atlas shows you the exact words it will post before it posts them.

### What Atlas writes on a ticket

Atlas adds a record to the ticket as the work moves. It never rewrites what the
ticket asks for.

| Record | What it says |
|---|---|
| `[EXECUTION PLAN]` | The steps Atlas plans to take |
| `[PROGRESS]` | What is finished so far |
| `[SCOPE CHANGE]` | An agreed change to the work, and the reason for it |
| `[BLOCKED]` | Why the work stopped, and what it needs to start again |
| `[AI CODE REVIEW]` | The full review of the finished change |
| `[CLOSEOUT]` | The result, the proof, and every deviation |

Atlas also writes the pull-request link on the ticket.

### What Atlas never does

- Atlas never merges a pull request. A person merges it.
- Atlas never marks work as done. A person does that, after they review the pull request.
- Atlas never removes or rewrites what a ticket asks for.
<!-- atlas-v3:operators-guide:end -->
