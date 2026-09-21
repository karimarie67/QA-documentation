# 🚀 QA Automation Framework - Boost.org Testing

> Complete QA automation suite with CI/CD integration and live metrics dashboards for Boost C++ Libraries

[![Tests](https://github.com/karimarie67/QA-documentation/actions/workflows/qa-test.yml/badge.svg)](https://github.com/karimarie67/QA-documentation/actions/workflows/qa-test.yml)
[![Dashboard](https://img.shields.io/badge/📊_Dashboard-Live-brightgreen)](./dashboards/qa-metrics.md)

## 🎯 Live Demo

### 📊 [**View QA Dashboard**](./dashboards/qa-metrics.md) ← Click to see live metrics!

The dashboard updates automatically after each test run, showing:
- Real-time test execution results
- Pass/fail rates and trends
- Historical data and metrics
- SOW progress tracking

### 🤖 [**Watch Tests Run**](../../actions) ← See automation in action!

---

## ✨ Key Features

### 🧪 Automated Test Suite
- **Smoke Tests** - Run on every PR/commit (5-10 min)
  - Critical path validation
  - Pre-merge quality gate
  - Fast developer feedback
- **Regression Tests** - Run on develop branch after merge (30-60 min)
  - `boost_io_tests.spec.js` - Comprehensive Boost.io testing
  - `boost_version_tests.spec.js` - Version-specific validation
- **Playwright-based** - Modern, reliable automation

### 🔄 CI/CD Integration  
- **Shift-left approach** - Test early and often
- **Smart test execution:**
  - Smoke tests on every PR (pre-merge gate)
  - Regression tests on develop (post-merge validation)
- Scheduled runs every 6 hours
- Manual triggers with environment selection
- Parallel execution for speed

### 📊 Live Dashboards
- Auto-updating metrics
- Visual test results
- 7-day trends and history
- SOW progress tracking
- Quality indicators

### 📚 Complete Documentation
- [QA Handbook](./docs/QA_handbook.md)
- [Testing Strategy](./docs/testing_strategy_doc.md) ← **Read this!**
- [Test Coverage Maps](./docs/Test-Coverage-Map.md)
- [Functional Test Cases](./docs/2.%20Functional-Table%201.csv)
- [Regression Test Cases](./docs/Regression-Table%201.csv)

---

## 🚀 Quick Start

### Run Tests Locally

```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run specific suite
npm run test:smoke
npm run test:boost-io
npm run test:version

# Run with UI
npm run test:headed
```

### Trigger Tests in GitHub

1. Go to [Actions](../../actions) tab
2. Select "QA Test Suite - Boost.org"
3. Click "Run workflow"
4. Choose environment (staging/production)
5. Watch the tests execute!

---

## 📊 Current Status

**SOW Completion:**
- ✅ **Month 1:** Foundation & Planning (100%)
- ✅ **Month 2:** Setup & Early Execution (100%)
- ✅ **Month 3:** Automation & Optimization (100%)

**Test Automation:**
- Smoke Tests: ✅ Fully automated
- Boost.io Tests: ✅ Fully automated  
- Version Tests: ✅ Fully automated
- CI/CD Pipeline: ✅ Running
- Live Dashboard: ✅ Implemented

---

## 🗂️ Repository Structure

```
QA-documentation/
├── .github/
│   ├── workflows/
│   │   └── qa-tests.yml          # CI/CD pipeline
│   └── ISSUE_TEMPLATE/           # Bug report templates
├── dashboards/
│   ├── qa-metrics.md             # 📊 LIVE DASHBOARD
│   ├── scripts/
│   │   └── generate-dashboard.js # Dashboard generator
│   └── test-results/             # Historical data
├── docs/
│   ├── QA_handbook.md           # Complete QA processes
│   ├── 2. Functional-Table 1.csv # Functional test cases
│   └── Regression-Table 1.csv    # Regression test cases
├── smoke_tests.spec.js           # Smoke test suite
├── boost_io_tests.spec.js        # Boost.io tests
├── boost_version_tests.spec.js   # Version tests
├── playwright.config.js          # Test configuration
└── package.json                  # Dependencies & scripts
```

---

## 🎬 Demo Walkthrough

### 1. Live Dashboard (Main Feature!)
- Navigate to [dashboards/qa-metrics.md](./dashboards/qa-metrics.md)
- See real-time test results
- View pass rates and trends
- Check SOW progress

### 2. Watch Tests Execute
- Go to [Actions](../../actions)
- Click latest workflow run
- See tests running in real-time
- Watch dashboard auto-update

### 3. Manual Test Trigger
- Actions → QA Test Suite → Run workflow
- Select staging or production
- Tests execute automatically
- Results available in minutes

### 4. Review Documentation
- [QA Handbook](./docs/QA_handbook.md) - Complete processes
- [Test Cases](./docs/) - What we test
- Dashboard metrics - Live results

---

## 🔧 Tech Stack

- **Testing Framework:** Playwright (JavaScript)
- **CI/CD:** GitHub Actions
- **Dashboard:** Auto-generated Markdown
- **Reporting:** JSON + HTML reports
- **Environments:** Boost.org (staging + production)

---

## 📈 Achievements

| Metric | Target | Current |
|--------|--------|---------|
| Test Automation | 100% | 100% |
| CI/CD Integration | Yes | ✅ |
| Live Dashboard | Yes | ✅ |
| Pass Rate | >95% | Tracking |
| SOW Completion | 100% | 100% |
---

## 🔮 Next Steps

**Q4 2025:**
- ✅ Expand regression coverage as needed
- ✅ Add visual regression testing
- [ ] Implement performance benchmarks
- [ ] Video recordings of failures
- [ ] Hire new QA Analyst

---

## 📞 About

This QA framework demonstrates:
- ✅ Modern automated testing practices
- ✅ CI/CD integration with GitHub Actions
- ✅ Live metrics and dashboards
- ✅ Complete documentation
- ✅ Real-world testing of production systems

---

<p align="center">
  <strong>Built for demonstrating professional QA automation</strong><br>
  <sub>Automated testing • Real-time metrics • Continuous improvement</sub>
</p>

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
