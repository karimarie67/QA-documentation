# Boost.org QA Automation Framework - Onboarding Guide

---

## 📋 Table of Contents
1. [What You're Taking Over](#what-youre-taking-over)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Understanding the Test Structure](#understanding-the-test-structure)
4. [Running Your First Tests](#running-your-first-tests)
5. [How the Helper Files Work](#how-the-helper-files-work)
6. [Integrating CI/CD into website-v2](#integrating-cicd-into-website-v2)
7. [Daily QA Workflow](#daily-qa-workflow)
8. [Debugging & Troubleshooting](#debugging--troubleshooting)
9. [Quick Reference](#quick-reference)

---

## What You're Taking Over

You're inheriting a fully functional QA automation setup with:
- **Complete test suites** for boost.org (staging + production)
- **CI/CD pipeline** running in GitHub Actions (currently in separate QA repo)
- **Live dashboard** showing test results and metrics
- **Helper architecture** that makes writing new tests easy

---

## Prerequisites & Setup

### What You Need Installed

```bash
# Check if you have these (you probably already do)
node --version    # Should be v18 or higher
npm --version     # Should be v9 or higher
git --version     # Any recent version

# Install VS Code extension (recommended)
# Search for "Playwright Test for VSCode" in extensions
```

### Step 1: Clone the QA Repo (For Reference)

```bash
# Clone the existing QA repo to see how everything works
git clone https://github.com/karimarie67/QA-documentation.git
cd QA-documentation

# Install dependencies
npm install

# Install Playwright browsers (one-time setup)
npx playwright install
```

**Note**: This repo is your reference. You'll eventually move this setup into `boostorg/website-v2`.

### Step 2: Verify Everything Works

```bash
# Run a quick smoke test to make sure everything's set up correctly
npm run test:smoke

# If that works, you're good to go!
```

**Expected output**: You should see tests running in the terminal, and they should mostly pass (some flakiness is normal on first run).

---

## Understanding the Test Structure

Before you start moving things around, let's understand what you're working with.

### Project Layout

```
QA-documentation/
├── .github/workflows/
│   └── qa-tests.yml              # CI/CD pipeline (you'll move this)
│
├── tests/
│   ├── smoke_tests.spec.js           # Quick health checks (5-10 min)
│   ├── boost_io_tests.spec.js        # Main functional tests (30-60 min)
│   └── boost_version_tests.spec.js   # Version-specific tests
│   ├── documentation_tests.spec.js   # Verify docs
│   ├── error_handling_tests.spec.js  # Check for 404s, etc.
│   └── download_search_tests.spec.js # Verify search and download functionality
|
├── Helper Files (the magic sauce):
│   ├── config-helper.js          # Environment switching (staging/prod)
│   ├── test-helpers.js           # Reusable test functions
│   ├── selectors.js              # Page element locators
│   └── utils.js                  # General utilities
│
├── playwright.config.js          # Main Playwright config
├── package.json                  # Dependencies & npm scripts
└── README.md                     # Current documentation
```

### Test Categories

Our testing suite is divided into two primary tiers to balance speed and coverage across the development lifecycle. All tests are triggered automatically on any change to the **QA Documentation repository** and can also be run manually as needed.

---

#### 1. Smoke Tests
* **File:** `smoke_tests.spec.js`
* **Execution:** Run on every PR before merge.
* **Duration:** Fast (5-10 minutes).
* **Objective:** Verifies critical paths to ensure basic site stability.
* **Key Scenarios:** Homepage loads, main navigation works, and basic search functions.

---

#### 2. Functional & UI Tests
* **Execution:** Run after merge to the `develop` branch.
* **Duration:** 30–60 minutes.
* **Objective:** Deep-dive validation of end-to-end user journeys, documentation integrity, and version-specific logic.

| Test Suite | File | Key Scenarios |
| :--- | :--- | :--- |
| **Main Functional** | `boost_io_tests.spec.js` | Full search flows and library filtering. |
| **Documentation** | `documentation_tests.spec.js` | TOC visibility, library link accessibility, code block formatting, and breadcrumb navigation. |
| **Search & Download** | `download_search_tests.spec.js` | Download link status codes, filename formats, search relevancy, and pagination. |
| **Error Handling** | `error_handling_tests.spec.js` | 404 error messaging, malformed URL redirects, and form validation. |
| **Version Specifics** | `boost_version_tests.spec.js` | Release downloads and version comparisons. |
| **Doc Versioning** | `documentation_tests.spec.js` | Specifically tests the documentation version switcher (TC_DOC_005). |

---

### Requirement Traceability Matrix (RTM)

| Test ID | Category | Validation Goal | Source File |
| :--- | :--- | :--- | :--- |
| **TC_SMOKE_001** | Smoke | Homepage loads with logo, nav, and main content | `smoke_tests.spec.js` |
| **TC_SMOKE_002** | Smoke | Navigation menu links work correctly and change URLs | `smoke_tests.spec.js` |
| **TC_SMOKE_003** | Smoke | Libraries page displays and links to documentation | `smoke_tests.spec.js` |
| **TC_SMOKE_004** | Smoke | Download section initiates file downloads correctly | `smoke_tests.spec.js` |
| **TC_SMOKE_005** | Smoke | Search bar works with basic working query | `smoke_tests.spec.js` |
| **TC_SMOKE_006** | Smoke | Homepage is responsive on mobile viewports | `smoke_tests.spec.js` |
| **TC_FUNC_001** | Functional | Homepage loads key elements and CTA button navigation | `boost_io_tests.spec.js` |
| **TC_FUNC_002** | Functional | Search bar is visible and functional on mobile | `boost_io_tests.spec.js` |
| **TC_FUNC_003** | Functional | Navigation menu links work across the site | `boost_io_tests.spec.js` |
| **TC_FUNC_004** | Functional | Responsive design adapts to mobile/desktop viewports | `boost_io_tests.spec.js` |
| **TC_FUNC_005** | Functional | Logo redirects to homepage from subpages | `boost_io_tests.spec.js` |
| **TC_FUNC_006** | Functional | Footer links are accessible and visible | `boost_io_tests.spec.js` |
| **TC_FUNC_007** | Functional | Main content loads on library-specific pages | `boost_io_tests.spec.js` |
| **TC_FUNC_008** | Functional | External links are valid and visible | `boost_io_tests.spec.js` |
| **TC_FUNC_009** | Functional | GitHub links point to correct repositories | `boost_io_tests.spec.js` |
| **TC_FUNC_010** | Functional | Documentation page loads and displays content | `boost_io_tests.spec.js` |
| **TC_FUNC_011** | Functional | Release notes are accessible | `boost_io_tests.spec.js` |
| **TC_FUNC_012** | Functional | Download link for previous release (1.85.0) works | `boost_io_tests.spec.js` |
| **TC_FUNC_013** | Functional | Handles broken or unavailable download links | `boost_io_tests.spec.js` |
| **TC_FUNC_014** | Functional | Community page links are functional | `boost_io_tests.spec.js` |
| **TC_DOC_001** | Documentation | Documentation page loads with table of contents | `documentation_tests.spec.js` |
| **TC_DOC_002** | Documentation | Library documentation links are accessible | `documentation_tests.spec.js` |
| **TC_DOC_003** | Documentation | Code examples are properly formatted | `documentation_tests.spec.js` |
| **TC_DOC_004** | Documentation | Documentation breadcrumbs navigation works | `documentation_tests.spec.js` |
| **TC_DOC_005** | Documentation | Documentation version switcher works | `documentation_tests.spec.js` |
| **TC_DOC_006** | Documentation | Search within documentation pages works | `documentation_tests.spec.js` |
| **TC_DOC_007** | Documentation | Documentation anchor links work correctly | `documentation_tests.spec.js` |
| **TC_DOC_008** | Documentation | Documentation external links open correctly | `documentation_tests.spec.js` |
| **TC_DOC_009** | Documentation | Documentation page titles are descriptive | `documentation_tests.spec.js` |
| **TC_DOC_010** | Documentation | Documentation PDF/print versions are accessible | `documentation_tests.spec.js` |
| **TC_DOWNLOAD_001** | Download | Download links return valid HTTP status codes | `download_search_tests.spec.js` |
| **TC_DOWNLOAD_002** | Download | Download file names are correct format | `download_search_tests.spec.js` |
| **TC_DOWNLOAD_003** | Download | Version selector displays available versions | `download_search_tests.spec.js` |
| **TC_DOWNLOAD_004** | Download | Download page displays file sizes | `download_search_tests.spec.js` |
| **TC_SEARCH_001** | Search | Returns relevant results for common queries | `download_search_tests.spec.js` |
| **TC_SEARCH_002** | Search | Handles special characters gracefully | `download_search_tests.spec.js` |
| **TC_SEARCH_003** | Search | Empty search shows appropriate message | `download_search_tests.spec.js` |
| **TC_SEARCH_004** | Search | Search result pagination works correctly | `download_search_tests.spec.js` |
| **TC_SEARCH_005** | Search | Search autocomplete/suggestions appear | `download_search_tests.spec.js` |
| **TC_ERROR_001** | Error Handling | 404 page displays appropriate error message | `error_handling_tests.spec.js` |
| **TC_ERROR_002** | Error Handling | Broken documentation link returns appropriate error | `error_handling_tests.spec.js` |
| **TC_ERROR_003** | Error Handling | Invalid search query handles gracefully | `error_handling_tests.spec.js` |
| **TC_ERROR_004** | Error Handling | Malformed URL redirects or shows error appropriately | `error_handling_tests.spec.js` |
| **TC_ERROR_005** | Error Handling | Broken external links are identified | `error_handling_tests.spec.js` |
| **TC_ERROR_006** | Error Handling | Form validation errors display correctly | `error_handling_tests.spec.js` |
| **TC_VERSION_001** | Version Tests | Libraries page loads version information | `boost_version_tests.spec.js` |
| **TC_VERSION_002** | Version Tests | Releases page displays release information | `boost_version_tests.spec.js` |

### Test Implementation Details
* **Tracing:** Each test is mapped to a unique Test Case ID (e.g., `TC_DOC_001` or `TC_DOWNLOAD_001`) via Playwright annotations.
* **Logging:** Test progress and findings (such as found selectors or navigation paths) are appended to `test-logs.txt`.
* **Resilience:** Tests utilize custom helper patterns like `loadAndValidatePage` and `findVisibleElement` to handle dynamic content.

## Running Your First Tests

### Local Development Commands

```bash
# Run ALL tests (takes a while)
npm test

# Run just smoke tests (recommended for testing)
npm run test:smoke

# Run specific test file
npm test tests/boost_io_tests.spec.js

# Run with browser visible (great for debugging)
npm run test:headed

# Run in Playwright UI mode (interactive debugging)
npm run test:ui

# Run specific test by name
npm test -- --grep "TC_FUNC_001"
```

### Environment Switching

```bash
# Test against staging (default)
npm run test:staging

# Test against production
npm run test:production

# Or set environment inline
ENVIRONMENT=production npm test
```

### Understanding Test Output

```bash
# When you run tests, you'll see:
Running 15 tests using 3 workers
  ✓ TC_SMOKE_001: Homepage loads successfully (2s)
  ✓ TC_SMOKE_002: Main navigation is accessible (1s)
  ✗ TC_FUNC_015: Search filters apply correctly (30s)
    
# After tests complete:
npm run test:report  # Opens HTML report in browser
```

---

## How the Helper Files Work

Understanding these will make your life MUCH easier when writing new tests.

### config-helper.js - Environment Management

**What it does**: Handles switching between staging and production

```javascript
// In your tests, you use it like this:
import { getConfig } from '../config-helper.js';

test('Example test', async ({ page }) => {
  const config = getConfig();
  await page.goto(config.baseUrl);  // Automatically uses correct environment
  // config.baseUrl is either boost.org or stage.boost.org
});
```

**Why it matters**: Write tests once, run them anywhere. No hardcoded URLs.

### test-helpers.js - Reusable Test Functions

**What it does**: Common test actions wrapped in functions

```javascript
// Instead of writing this in every test:
await page.waitForLoadState('networkidle');
await page.waitForSelector('.search-results');
await expect(page.locator('.search-results')).toBeVisible();

// You call this:
await testHelpers.waitForSearchResults(page);
```

**Common helpers you'll use**:
- `waitForPageLoad(page)` - Wait for page to fully load
- `waitForSearchResults(page)` - Wait for search results to appear
- `clickAndWaitForNavigation(page, selector)` - Click link and wait for page change
- `verifyElementVisible(page, selector)` - Check if element exists and is visible

### selectors.js - Page Element Locators

**What it does**: Centralized list of all element selectors

```javascript
// Instead of scattered selectors throughout your tests:
await page.click('.header-nav-item:has-text("Libraries")');

// You use named selectors:
import { SELECTORS } from '../selectors.js';
await page.click(SELECTORS.navigation.librariesLink);
```

**Why it matters**: When the UI changes, you update ONE file instead of 50 tests.

### utils.js - General Utilities

**What it does**: Logging, timing, data helpers

```javascript
// Helpful for debugging
import { logTestStep, measurePerformance } from '../utils.js';

logTestStep('Searching for "algorithm"');
const timing = await measurePerformance(page, async () => {
  await page.fill('input[type="search"]', 'algorithm');
});
console.log(`Search took ${timing}ms`);
```

---

## Integrating CI/CD into website-v2

This is your main task. Here's the step-by-step process:

### Phase 1: Understand Current Setup

**Current state**: 
- QA tests live in `karimarie67/QA-documentation`
- CI/CD runs there, testing boost.org from outside
- website-v2 has no QA automation

**Goal state**:
- QA tests live in `boostorg/website-v2` 
- CI/CD runs there as part of the main workflow
- Tests run on every PR and merge

### Phase 2: Create QA Directory in website-v2

```bash
# In the website-v2 repo
cd boostorg/website-v2

# Create QA directory structure
mkdir -p qa-tests/tests
mkdir -p qa-tests/.github/workflows

# You'll copy files here
```

### Phase 3: Copy Files Over

**Files to copy from QA-documentation to website-v2**:

```
QA-documentation/                    →    website-v2/qa-tests/
├── tests/                           →    ├── tests/
│   ├── smoke_tests.spec.js          →    │   ├── smoke_tests.spec.js
│   ├── boost_io_tests.spec.js       →    │   ├── boost_io_tests.spec.js
│   └── boost_version_tests.spec.js  →    │   └── boost_version_tests.spec.js
├── config-helper.js                 →    ├── config-helper.js
├── test-helpers.js                  →    ├── test-helpers.js
├── selectors.js                     →    ├── selectors.js
├── utils.js                         →    ├── utils.js
├── playwright.config.js             →    ├── playwright.config.js
└── package.json                     →    ├── package.json (merge scripts)
```

### Phase 4: Modify GitHub Actions Workflow

**Current workflow** (in QA-documentation):
```yaml
# .github/workflows/qa-tests.yml
name: QA Test Suite - Boost.org

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
```

**What you need to change for website-v2**:

```yaml
# website-v2/.github/workflows/qa-tests.yml
name: QA Tests

on:
  pull_request:
    branches: [ develop, main ]
    # Run smoke tests on every PR
    
  push:
    branches: [ develop ]
    # Run full regression after merge to develop
    
  schedule:
    - cron: '0 */6 * * *'

jobs:
  smoke-tests:
    # Runs on every PR (pre-merge gate)
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./qa-tests  # Important!
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: qa-tests/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run Smoke Tests
        run: npm run test:smoke
        env:
          CI: true
          ENVIRONMENT: staging
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: smoke-test-results
          path: qa-tests/playwright-report/
  
  regression-tests:
    # Runs after merge to develop
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./qa-tests
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: qa-tests/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run Regression Tests
        run: npm test
        env:
          CI: true
          ENVIRONMENT: staging
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: regression-test-results
          path: qa-tests/playwright-report/
```

### Phase 5: Update package.json for website-v2

**In `website-v2/qa-tests/package.json`**, make sure you have:

```json
{
  "name": "boost-qa-tests",
  "version": "1.0.0",
  "scripts": {
    "test": "playwright test",
    "test:smoke": "playwright test tests/smoke_tests.spec.js",
    "test:boost-io": "playwright test tests/boost_io_tests.spec.js",
    "test:version": "playwright test tests/boost_version_tests.spec.js",
    "test:headed": "playwright test --headed",
    "test:ui": "playwright test --ui",
    "test:debug": "playwright test --debug",
    "test:report": "playwright show-report",
    "test:staging": "ENVIRONMENT=staging playwright test",
    "test:production": "ENVIRONMENT=production playwright test"
  },
  "devDependencies": {
    "@playwright/test": "^1.48.0"
  }
}
```

### Phase 6: Update Paths in Config Files

**In `playwright.config.js`**, update paths:

```javascript
export default defineConfig({
  testDir: './tests',  // This stays the same
  
  // Update output directories if needed
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  
  // Rest of config stays the same...
});
```

### Phase 7: Test Locally Before Pushing

```bash
# In website-v2/qa-tests/
npm install
npx playwright install

# Run smoke tests to verify everything works
npm run test:smoke

# If that works, you're ready to commit!
```

### Phase 8: Create PR for Integration

```bash
# In website-v2/
git checkout -b add-qa-automation
git add qa-tests/
git commit -m "Add QA automation framework

- Integrate Playwright test suite from QA-documentation repo
- Add smoke tests (run on PRs)
- Add regression tests (run on develop)
- Configure GitHub Actions workflow
- Add helper files for test maintainability"

git push origin add-qa-automation
```

**In your PR description, include**:
- Link to QA-documentation repo
- Explanation of smoke vs regression tests
- How to run tests locally
- What the CI/CD workflow does

---

## Daily QA Workflow

Once everything's integrated, here's your typical day:

### Morning: Check Test Results

1. Go to [Actions tab](https://github.com/boostorg/website-v2/actions)
2. Check overnight scheduled runs
3. Review any failures
4. File bugs if needed

### When PR is Created:

1. Smoke tests run automatically
2. Review results in PR checks
3. If tests fail:
   - Check if it's a real bug
   - Or if selectors need updating
   - Update tests if UI changed legitimately

### After PR Merges to Develop:

1. Regression tests run automatically
2. Review full test results
3. Monitor for new failures
4. Update dashboard (it auto-updates, but verify)

### Writing New Tests:

```javascript
// In tests/boost_io_tests.spec.js
import { test, expect } from '@playwright/test';
import { getConfig } from '../config-helper.js';
import { SELECTORS } from '../selectors.js';
import * as helpers from '../test-helpers.js';

test('TC_FUNC_XXX: Your test description', async ({ page }) => {
  const config = getConfig();
  
  // Navigate to page
  await page.goto(`${config.baseUrl}/your-page`);
  await helpers.waitForPageLoad(page);
  
  // Perform actions
  await page.click(SELECTORS.yourElement);
  
  // Assert results
  await expect(page.locator(SELECTORS.yourResult)).toBeVisible();
});
```

---

## Debugging & Troubleshooting

### Common Issues

#### Tests Not Running in GitHub Actions

**Problem**: Workflow doesn't trigger
**Solution**: 
- Check workflow file is in `.github/workflows/`
- Verify YAML syntax (tabs vs spaces matter!)
- Check branch names match your triggers

#### Tests Fail Locally But Pass in CI

**Problem**: Environment differences
**Solution**:
```bash
# Run in CI mode locally
CI=true npm test

# Check if it's a timing issue
npm test -- --timeout=60000
```

#### Element Not Found Errors

**Problem**: Selectors out of date
**Solution**:
```bash
# Use Playwright's inspector to find new selectors
npx playwright codegen https://stage.boost.org

# Update selectors.js with new values
```

#### Tests Are Flaky

**Problem**: Tests pass sometimes, fail other times
**Solution**:
```javascript
// Add more explicit waits
await page.waitForLoadState('networkidle');
await page.waitForSelector(SELECTORS.yourElement);

// Or use retry logic
await expect(page.locator(SELECTORS.yourElement))
  .toBeVisible({ timeout: 10000 });
```

### Debugging Commands

```bash
# Run single test with visible browser
npm test -- --grep "TC_FUNC_001" --headed

# Run with Playwright inspector (step through test)
npm run test:debug

# Run with trace (records everything)
npm test -- --trace on

# View trace after test
npx playwright show-trace trace.zip
```

### Using Playwright's Tools

```bash
# Generate new test interactively (records your actions)
npx playwright codegen https://stage.boost.org

# View last test run in UI
npx playwright show-report

# Check which browsers are installed
npx playwright list
```

---

## Quick Reference

### Essential Commands

```bash
# Running tests
npm test                          # All tests
npm run test:smoke                # Just smoke tests
npm run test:headed               # See browser
npm test -- --grep "keyword"      # Specific tests

# Debugging
npm run test:ui                   # Interactive mode
npm run test:debug                # Step through
npm run test:report               # View results

# Environments
npm run test:staging              # Stage environment
npm run test:production           # Production (careful!)

# CI/CD
# Manual trigger: Actions → qa-tests.yml → Run workflow
```

### File Quick Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `tests/*.spec.js` | Test files | Adding/modifying tests |
| `selectors.js` | Element locators | UI changes |
| `test-helpers.js` | Reusable functions | New common patterns |
| `config-helper.js` | Environment config | New environments |
| `playwright.config.js` | Test runner config | Test behavior changes |
| `.github/workflows/qa-tests.yml` | CI/CD pipeline | Changing when tests run |

### Getting Help

**When tests fail**:
1. Check the HTML report: `npm run test:report`
2. Look at screenshots in `test-results/`
3. Run with `--headed` to see what's happening

**When writing new tests**:
1. Copy existing test as template
2. Use `codegen` to find selectors
3. Test locally before pushing

**When stuck**:
- Check existing tests for examples
- Read Playwright docs: https://playwright.dev
- Ask in #boost-website Slack channel

---

## Important Notes

- **Smoke tests must be fast** - They're a pre-merge gate, keep under 10 minutes
- **Don't test against production frequently** - Use staging for development
- **Update selectors.js when UI changes** - Don't put selectors in test files
- **Keep tests independent** - Each test should work on its own
- **CI/CD is your friend** - If it's not automated, it won't get done consistently

---

**Questions?** Check the existing tests in the QA-documentation repo for examples, visit https://playwright.dev/docs/intro or check with some of the Boost folks
