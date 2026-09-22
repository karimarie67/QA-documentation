# Boost.org Example (Closed Engagement)

This directory is a **closed-engagement reference**: the original Boost.org
implementation of this QA Framework, kept here for illustration only.

It is **not live**. The Boost.org engagement has ended, and nothing in this
directory is actively maintained, updated, or tested against a real site.

It is **not run in CI**. No pipeline automatically executes anything here.

It is **not discoverable by the tracked `playwright.config.js`** at all. That
config's `testDir` is `./tests`, so nothing under `examples/boost/` is ever
picked up by `npm test` or any other Playwright command that uses the repo's
own config — even accidentally.

## What's here

- `boost_io_tests.spec.js` and `boost_version_tests.spec.js` — the Boost.io
  and Boost version Playwright specs, as they were written against the live
  Boost.org site.
- `QA_handbook.md`, `playwright_setup_guide.md`,
  `playwright_cicd_implementation.md`, and
  `playwright_test_optimization_guide.md` — the QA handbook and the
  setup/CI/optimization guides written for the Boost engagement.
- `Functional-Table 1.csv` and `Regression-Table 1.csv` — the Boost
  functional and regression test-case tables.
- `Automate Release Notes.md` and `Ticketing Workflow for Boost.md` — the
  release-notes automation and ticketing workflow docs for Boost.
- `boost_prod_link_checker.py`, `boost-verify.sh`, and `check_links.py` — the
  link-checker and verification scripts used against the Boost site.

Together, these files demonstrate one complete, real instantiation of the
Framework's `config-helper.js` / `selectors.js` / `test-helpers.js` /
`utils.js` layer, wired up against an actual client project.
