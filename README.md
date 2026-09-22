# QA Automation Framework

A generic, site-agnostic Playwright QA automation **Framework** — a template
you instantiate per Engagement, not a finished product built for one site.

## Instantiating this for a new Engagement

Pick one:

- **Clone the repo.** This always works, regardless of any GitHub setting.
- **Click "Use this template" on GitHub.** This only appears once a repo
  admin has enabled it: **Settings → General → Template repository**. That
  is a one-time, admin-only action — nothing in this codebase can enable it
  for you. Until it's enabled, clone instead.

## Worked example

[`examples/boost/README.md`](./examples/boost/README.md) is a complete, real
(though non-live/historical) instance of this Framework wired up for a past
Engagement (Boost.org). It's a useful reference for seeing the shape of a
working configuration, including the [QA Handbook](./examples/boost/QA_handbook.md),
[functional test cases](./examples/boost/Functional-Table%201.csv), and
[regression test cases](./examples/boost/Regression-Table%201.csv) from that
Engagement.

## Quick start

```bash
npm install

npm test                     # run the full test suite
npm run test:smoke           # smoke tests only
npm run test:regression      # regression suite (documentation, download/search, error handling)
npm run test:links           # link checker
npm run test:unit            # unit tests for config-helper.js/selectors.js
npm run test:template-check  # structural smoke check that the template itself is intact
```

## Configuring a new site

A new Engagement edits Site config across a few files, all marked with
`TODO(Engagement)` comments:

- [`config-helper.js`](./config-helper.js) and
  [`playwright.config.js`](./playwright.config.js) — base URLs, download-file
  patterns, and other placeholder values.
- [`selectors.js`](./selectors.js) — the fallback CSS selectors and element
  IDs each `selectors.X` function tries; not every entry is `TODO`-marked, so
  read through the fallback arrays too, not just the comments.
- The skeleton specs under `tests/` and `tests/check-links.spec.js` — each has
  `TODO(Engagement)` markers at the assertions that need real content.

## CI

- `unit-tests` and `template-check` run automatically on every push and PR to
  `main`/`develop` — no configuration needed.
- The real browser e2e jobs (`smoke-tests`, `error-handling-tests`,
  `download-search-tests`, `documentation-tests`) only run via manual
  `workflow_dispatch`, until the placeholders in `playwright.config.js`,
  `config-helper.js`, and `selectors.js` are replaced with real Site config.

<!-- atlas-v3:readme:start -->
## Atlas

This repo uses Atlas, a Claude Code plugin that acts as a shared path for AI-assisted development — generated, customizable policies, guidelines, and guardrails that keep agent-driven work safe and consistent without locking teams into one rigid workflow. Read [`docs/atlas-operators-guide.md`](./docs/atlas-operators-guide.md) for how to work in this repo, in plain language, and the **Atlas** section in [`CLAUDE.md`](./CLAUDE.md) for the policy the agents follow.

**Before working in this repo:**

1. **Activate git hooks** (one-time, per clone):

   ```bash

   git config core.hooksPath .githooks

   ```

   These block a handful of destructive git operations before they run.

2. **Claude Code hooks** are already configured in `.claude/settings.json` — they guard against risky file, shell, and MCP actions during agent sessions. See `docs/agents/guardrails.md` if you need to change them.

Everything Atlas generated here — hooks, the `CLAUDE.md` section, `docs/agents/` — is a **base recommendation**, not fixed policy. Adapt it to this project's actual needs and processes.
<!-- atlas-v3:readme:end -->
