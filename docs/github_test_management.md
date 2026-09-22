# GitHub-Based Test Case Management Setup

## Test Case Management with GitHub Issues

### Issue Templates

Create `.github/ISSUE_TEMPLATE/test-case.yml`:

```yaml
name: Test Case
description: Create a new test case
title: "[TEST CASE] TC_XXX_000 - "
labels: ["test-case"]
body:
  - type: input
    id: test_id
    attributes:
      label: Test Case ID
      description: Unique identifier (e.g., TC_FUNC_001)
      placeholder: TC_FUNC_001
    validations:
      required: true
  
  - type: dropdown
    id: test_type
    attributes:
      label: Test Type
      options:
        - Smoke
        - Functional
        - Integration
        - Performance
        - Accessibility
    validations:
      required: true
  
  - type: dropdown
    id: priority
    attributes:
      label: Priority
      options:
        - Critical
        - High
        - Medium
        - Low
    validations:
      required: true
  
  - type: checkboxes
    id: environments
    attributes:
      label: Test Environments
      options:
        - label: Staging
        - label: Production
        - label: Local Development
  
  - type: checkboxes
    id: browsers
    attributes:
      label: Browser Coverage
      options:
        - label: Chromium
        - label: Firefox
        - label: WebKit
        - label: Mobile Chrome
        - label: Mobile Safari
  
  - type: textarea
    id: prerequisites
    attributes:
      label: Prerequisites
      description: Conditions that must be met before executing this test
      placeholder: "- User must be logged in\n- Database must contain sample data"
  
  - type: textarea
    id: test_steps
    attributes:
      label: Test Steps
      description: Detailed steps to execute the test
      placeholder: "1. Navigate to homepage\n2. Click on 'Libraries' link\n3. Search for 'algorithm'"
    validations:
      required: true
  
  - type: textarea
    id: expected_results
    attributes:
      label: Expected Results
      description: What should happen when the test is executed correctly
      placeholder: "1. Homepage loads within 3 seconds\n2. Libraries page displays\n3. Search results show relevant libraries"
    validations:
      required: true
  
  - type: input
    id: automation_status
    attributes:
      label: Automation Status
      description: Current automation state
      placeholder: "Automated in Playwright"
  
  - type: input
    id: automation_file
    attributes:
      label: Automation File Path
      description: Path to automated test file (if applicable)
      placeholder: "tests/functional/library-discovery.spec.js"
  
  - type: textarea
    id: notes
    attributes:
      label: Additional Notes
      description: Any additional information about this test case
```

### GitHub Labels for Test Organization

```yaml
Test Type Labels:
  - smoke-test (color: #28a745)
  - functional-test (color: #007bff)
  - integration-test (color: #6f42c1)
  - performance-test (color: #fd7e14)
  - accessibility-test (color: #20c997)

Priority Labels:
  - priority-critical (color: #dc3545)
  - priority-high (color: #fd7e14)
  - priority-medium (color: #ffc107)
  - priority-low (color: #6c757d)

Status Labels:
  - test-automated (color: #28a745)
  - test-manual (color: #17a2b8)
  - test-needs-automation (color: #ffc107)
  - test-blocked (color: #dc3545)

Environment Labels:
  - env-staging (color: #6f42c1)
  - env-production (color: #fd7e14)
  - env-local (color: #6c757d)
```

### GitHub Projects Setup

Create a project with custom fields:

```yaml
Project Fields:
  - Test Type (Single select): Smoke, Functional, Integration, Performance
  - Priority (Single select): Critical, High, Medium, Low
  - Automation Status (Single select): Automated, Manual, Needs Automation, Blocked
  - Last Executed (Date)
  - Execution Status (Single select): Pass, Fail, Skip, Not Run
  - Environment (Multi-select): Staging, Production, Local
  - Browsers (Multi-select): Chromium, Firefox, WebKit, Mobile

Project Views:
  1. Test Suite Overview (grouped by Test Type)
  2. Automation Status (grouped by Automation Status)
  3. Execution Status (grouped by Execution Status)
  4. Priority Matrix (Priority vs Status)
  5. Environment Coverage (grouped by Environment)
```

## Custom QA Dashboard

### Dashboard Architecture

```yaml
Technology Stack:
  - Frontend: React/Next.js or Vue.js
  - Backend: Node.js with GitHub APIs
  - Hosting: GitHub Pages or Vercel (free)
  - Data Sources: 
    - GitHub Issues API (test cases)
    - GitHub Actions API (execution results)
    - Playwright HTML reports
    - GitHub Projects API (dashboard data)

Key Features:
  - Real-time test execution status
  - Test case browser and search
  - Execution history and trends
  - Coverage metrics visualization
  - Performance trend charts
  - Direct links to detailed reports
```

### Dashboard Components

#### 1. Executive Summary Widget
```javascript
// Dashboard overview showing key metrics
const ExecutiveSummary = () => {
  return (
    <div className="dashboard-summary">
      <MetricCard 
        title="Test Coverage" 
        value="87%" 
        trend="+2%" 
        color="green" 
      />
      <MetricCard 
        title="Pass Rate (24h)" 
        value="94%" 
        trend="-1%" 
        color="yellow" 
      />
      <MetricCard 
        title="Automated Tests" 
        value="142/160" 
        trend="+5" 
        color="blue" 
      />
      <MetricCard 
        title="Critical Failures" 
        value="0" 
        trend="0" 
        color="green" 
      />
    </div>
  );
};
```

#### 2. Test Execution Status
```javascript
// Real-time test execution visualization
const TestExecutionStatus = () => {
  return (
    <div className="execution-status">
      <h3>Current Test Execution</h3>
      <TestRunCard 
        environment="Staging"
        status="Running"
        progress="67%"
        tests={{ passed: 45, failed: 2, running: 8 }}
      />
      <TestRunCard 
        environment="Production"
        status="Completed"
        progress="100%"
        tests={{ passed: 28, failed: 0, skipped: 2 }}
      />
    </div>
  );
};
```

#### 3. Test Case Browser
```javascript
// Searchable test case interface
const TestCaseBrowser = () => {
  return (
    <div className="test-browser">
      <SearchFilters 
        onFilter={handleFilter}
        filters={['type', 'priority', 'automation', 'environment']}
      />
      <TestCaseList 
        testCases={filteredTestCases}
        onSelect={handleTestCaseSelect}
      />
      <TestCaseDetails 
        testCase={selectedTestCase}
        onEdit={handleEdit}
        onExecute={handleExecute}
      />
    </div>
  );
};
```

### GitHub Actions Integration

Add to your existing workflow to update dashboard data:

```yaml
# .github/workflows/update-dashboard.yml
name: Update QA Dashboard

on:
  workflow_run:
    workflows: ["Playwright Tests"]
    types: [completed]
  schedule:
    - cron: '*/15 * * * *'  # Update every 15 minutes

jobs:
  update_dashboard:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout dashboard repo
        uses: actions/checkout@v4
        with:
          repository: <your-org>/<your-repo>
          token: ${{ secrets.DASHBOARD_TOKEN }}
      
      - name: Fetch test results
        run: |
          # Fetch latest test results from GitHub Actions API
          curl -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \
            "https://api.github.com/repos/<your-org>/<your-repo>/actions/runs" \
            > test-runs.json
      
      - name: Update dashboard data
        run: |
          # Process test results and update dashboard data files
          node scripts/update-test-data.js
      
      - name: Deploy dashboard
        run: |
          npm run build
          npm run deploy
```

## Implementation Script

### Automated Setup Script

```bash
#!/bin/bash
# setup-github-test-management.sh

echo "Setting up GitHub-based test case management..."

# Create issue templates
mkdir -p .github/ISSUE_TEMPLATE
cat > .github/ISSUE_TEMPLATE/test-case.yml << 'EOF'
# [Issue template content from above]
EOF

# Create labels
gh label create "smoke-test" --color "28a745" --description "Smoke test cases"
gh label create "functional-test" --color "007bff" --description "Functional test cases"
gh label create "integration-test" --color "6f42c1" --description "Integration test cases"
gh label create "performance-test" --color "fd7e14" --description "Performance test cases"
gh label create "accessibility-test" --color "20c997" --description "Accessibility test cases"

gh label create "priority-critical" --color "dc3545" --description "Critical priority"
gh label create "priority-high" --color "fd7e14" --description "High priority"
gh label create "priority-medium" --color "ffc107" --description "Medium priority"
gh label create "priority-low" --color "6c757d" --description "Low priority"

gh label create "test-automated" --color "28a745" --description "Automated test"
gh label create "test-manual" --color "17a2b8" --description "Manual test"
gh label create "test-needs-automation" --color "ffc107" --description "Needs automation"
gh label create "test-blocked" --color "dc3545" --description "Blocked test"

# Create initial project
gh project create --title "QA Test Management" --body "Test case management and execution tracking"

echo "Setup complete! You can now:"
echo "1. Create test cases using the new issue template"
echo "2. Organize test cases in the GitHub project"
echo "3. Use labels to categorize and filter tests"
echo "4. Link test cases to Playwright test files"
```

## Migration from Existing Test Cases

### Conversion Script

```javascript
// migrate-existing-tests.js
const fs = require('fs');
const { Octokit } = require('@octokit/rest');

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

async function migrateTestCases() {
  // Read existing test documentation or spreadsheet
  const existingTests = JSON.parse(fs.readFileSync('existing-tests.json'));
  
  for (const test of existingTests) {
    const issue = await octokit.rest.issues.create({
      owner: '<your-org>',
      repo: '<your-repo>',
      title: `${test.id} - ${test.title}`,
      body: formatTestCaseBody(test),
      labels: generateLabels(test)
    });
    
    console.log(`Created issue #${issue.data.number} for ${test.id}`);
  }
}

function formatTestCaseBody(test) {
  return `
## Test Case Details

**Test ID:** ${test.id}
**Priority:** ${test.priority}
**Type:** ${test.type}

## Prerequisites
${test.prerequisites}

## Test Steps
${test.steps}

## Expected Results
${test.expectedResults}

## Automation Status
${test.automationStatus}

## Automation File
${test.automationFile || 'Not automated'}
  `.trim();
}

function generateLabels(test) {
  const labels = ['test-case'];
  
  if (test.type) labels.push(`${test.type.toLowerCase()}-test`);
  if (test.priority) labels.push(`priority-${test.priority.toLowerCase()}`);
  if (test.automated) labels.push('test-automated');
  else labels.push('test-manual');
  
  return labels;
}

migrateTestCases().catch(console.error);
```

## Reporting and Analytics

### Test Metrics Collection

```javascript
// scripts/collect-test-metrics.js
const { Octokit } = require('@octokit/rest');

class TestMetrics {
  constructor() {
    this.octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  }
  
  async getTestCaseMetrics() {
    const issues = await this.octokit.rest.issues.listForRepo({
      owner: '<your-org>',
      repo: '<your-repo>',
      labels: 'test-case',
      state: 'all',
      per_page: 100
    });
    
    const metrics = {
      totalTestCases: issues.data.length,
      automatedTests: 0,
      manualTests: 0,
      byPriority: {},
      byType: {},
      lastUpdated: new Date().toISOString()
    };
    
    issues.data.forEach(issue => {
      // Parse labels to extract metrics
      issue.labels.forEach(label => {
        if (label.name.startsWith('priority-')) {
          const priority = label.name.replace('priority-', '');
          metrics.byPriority[priority] = (metrics.byPriority[priority] || 0) + 1;
        }
        
        if (label.name.endsWith('-test')) {
          const type = label.name.replace('-test', '');
          metrics.byType[type] = (metrics.byType[type] || 0) + 1;
        }
        
        if (label.name === 'test-automated') metrics.automatedTests++;
        if (label.name === 'test-manual') metrics.manualTests++;
      });
    });
    
    return metrics;
  }
  
  async getExecutionMetrics() {
    const runs = await this.octokit.rest.actions.listWorkflowRuns({
      owner: '<your-org>',
      repo: '<your-repo>',
      workflow_id: 'playwright-e2e.yml',
      per_page: 50
    });
    
    const executionMetrics = {
      totalRuns: runs.data.total_count,
      successRate: 0,
      averageDuration: 0,
      recentFailures: [],
      lastRun: null
    };
    
    if (runs.data.workflow_runs.length > 0) {
      const successful = runs.data.workflow_runs.filter(run => run.conclusion === 'success').length;
      executionMetrics.successRate = (successful / runs.data.workflow_runs.length) * 100;
      executionMetrics.lastRun = runs.data.workflow_runs[0];
      
      // Calculate average duration
      const durations = runs.data.workflow_runs
        .filter(run => run.conclusion !== null)
        .map(run => new Date(run.updated_at) - new Date(run.created_at));
      
      if (durations.length > 0) {
        executionMetrics.averageDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
      }
    }
    
    return executionMetrics;
  }
}

module.exports = TestMetrics;
```

### Dashboard Data Generation

```javascript
// scripts/generate-dashboard-data.js
const TestMetrics = require('./collect-test-metrics');
const fs = require('fs');

async function generateDashboardData() {
  const metrics = new TestMetrics();
  
  const data = {
    testCases: await metrics.getTestCaseMetrics(),
    execution: await metrics.getExecutionMetrics(),
    generatedAt: new Date().toISOString()
  };
  
  // Write to dashboard data file
  fs.writeFileSync('dashboard/data/metrics.json', JSON.stringify(data, null, 2));
  
  console.log('Dashboard data generated successfully');
  return data;
}

if (require.main === module) {
  generateDashboardData().catch(console.error);
}

module.exports = generateDashboardData;
```
