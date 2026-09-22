const fs = require('fs');
const path = require('path');

// --- CONFIGURATION: QUALITY GATES ---
const QUALITY_GATES = {
  SMOKE_TARGET: 100,
  FUNCTIONAL_TARGET: 95,
  MAX_DURATION_SEC: 600
};

const ARTIFACTS_DIR = path.join(__dirname, '../../artifacts');
const DASHBOARD_PATH = path.join(__dirname, '../qa-metrics.md');
const RESULTS_DIR = path.join(__dirname, '../test-results');
const HISTORY_FILE = path.join(RESULTS_DIR, 'history.json');
const SLACK_FILE = path.join(RESULTS_DIR, 'slack-payload.json');

function main() {
  console.log('🔄 Generating QA Dashboard (v9.0 - Chart Removed)...');
  
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }
  
  const testResults = collectTestResults();
  const metrics = calculateMetrics(testResults);

  if (metrics.totalTests === 0) {
    // No real artifacts were found (see collectTestResults). Render an explicit
    // "no data" dashboard instead of a full report - recording this as a real
    // history entry would read as "a run happened and everything failed"
    // rather than "no run happened", permanently skewing the trend series and
    // flaky-test detection with a data point that never represented a run.
    console.warn('⚠️ No real test results to report - skipping history update, writing a no-data dashboard.');
    fs.writeFileSync(DASHBOARD_PATH, generateNoDataMarkdown());
    console.log('✅ Dashboard generated successfully (no data).');
    return;
  }

  updateHistory(metrics);
  const history = loadHistory();
  
  const trends = calculateTrends(metrics, history);
  const dashboard = generateDashboardMarkdown(metrics, testResults, history, trends);
  
  fs.writeFileSync(DASHBOARD_PATH, dashboard);
  
  // Save detailed latest results
  fs.writeFileSync(
    path.join(RESULTS_DIR, 'latest-results.json'),
    JSON.stringify({ timestamp: new Date().toISOString(), metrics, testResults }, null, 2)
  );
  
  // --- SLACK PAYLOAD ---
  if (metrics.failed > 0 || trends.flakyTests.length > 0) {
    const slackPayload = {
      text: `🚨 **QA Alert**`,
      blocks: [
        {
          type: "section",
          text: {
            type: "mrkdwn",
            text: `*${metrics.failed} Tests Failed* on \`${metrics.branch}\`\n<https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${metrics.runId}|View Dashboard>`
          }
        }
      ]
    };
    fs.writeFileSync(SLACK_FILE, JSON.stringify(slackPayload));
  }

  console.log('✅ Dashboard generated successfully!');
}

function collectTestResults() {
  const results = { smoke: [], functional: [] };

  const files = {
    smoke: path.join(ARTIFACTS_DIR, 'smoke-test-results/smoke-results.json')
  };

  const functionalFiles = [
    path.join(ARTIFACTS_DIR, 'error-handling-test-results/error-handling-results.json'),
    path.join(ARTIFACTS_DIR, 'download-search-test-results/download-search-results.json'),
    path.join(ARTIFACTS_DIR, 'documentation-test-results/documentation-results.json')
  ];

  // Process Standard Files
  for (const [key, filepath] of Object.entries(files)) {
    if (fs.existsSync(filepath)) {
      console.log(`Found ${key} results: ${filepath}`);
      results[key] = parsePlaywrightJson(filepath);
    } else {
      console.log(`⚠️ Missing ${key} results at: ${filepath}`);
    }
  }

  // Process & Combine Functional Files
  functionalFiles.forEach(filepath => {
    if (fs.existsSync(filepath)) {
      console.log(`Found functional results: ${filepath}`);
      const tests = parsePlaywrightJson(filepath);
      results.functional = results.functional.concat(tests);
    } else {
      console.log(`⚠️ Missing functional file: ${filepath}`);
    }
  });
  
  if (Object.values(results).every(arr => arr.length === 0)) {
    console.warn("⚠️ No artifacts found. Dashboard will show a 'no data' state.");
    return results;
  }

  return results;
}

function parsePlaywrightJson(filepath) {
  try {
    const fileContent = fs.readFileSync(filepath, 'utf8');
    if (!fileContent.trim()) return [];

    const data = JSON.parse(fileContent);
    const tests = [];
    
    function traverse(node) {
      if (node.specs) {
        node.specs.forEach(spec => {
          if (spec.tests) {
            spec.tests.forEach(test => {
              if (test.results && test.results.length > 0) {
                const result = test.results[0];
                tests.push({
                  name: spec.title || test.title || 'Unknown Test',
                  status: result.status === 'passed' ? 'passed' : 'failed',
                  durationSec: (result.duration || 0) / 1000,
                  projectName: test.projectName || 'Default', 
                  error: result.errors && result.errors.length > 0 ? result.errors[0].message : null
                });
              }
            });
          }
        });
      }
      if (node.suites) node.suites.forEach(suite => traverse(suite));
    }
    
    traverse(data);
    return tests;
  } catch (e) {
    console.error(`✗ Error parsing ${filepath}:`, e.message);
    return [];
  }
}

function calculateMetrics(results) {
  const allTests = [
    ...results.smoke,
    ...results.functional
  ];

  const passed = allTests.filter(t => t.status === 'passed').length;
  const failedTests = allTests.filter(t => t.status === 'failed');
  const totalDuration = allTests.reduce((acc, t) => acc + (t.durationSec || 0), 0);

  return {
    totalTests: allTests.length,
    passed,
    failed: failedTests.length,
    failedTestNames: failedTests.map(t => t.name),
    passRate: allTests.length > 0 ? (passed / allTests.length) * 100 : 0,
    totalDuration: totalDuration,
    smokeCount: results.smoke.length,
    functionalCount: results.functional.length,
    allTestObjects: allTests, 
    timestamp: new Date().toISOString(),
    environment: process.env.TEST_ENV || 'staging',
    runId: process.env.GITHUB_RUN_ID || 'local',
    runNumber: process.env.GITHUB_RUN_NUMBER || '0',
    branch: process.env.GITHUB_REF?.replace('refs/heads/', '') || 'unknown'
  };
}

function updateHistory(metrics) {
  let history = [];
  if (fs.existsSync(HISTORY_FILE)) {
    try {
      history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
    } catch (e) {
      console.warn('⚠️ Could not parse history file, starting fresh.');
    }
  }
  
  const runNumber = process.env.GITHUB_RUN_NUMBER || '0';
  
  const newEntry = {
    date: new Date().toISOString().split('T')[0],
    time: new Date().toISOString(),
    total: metrics.totalTests,
    passed: metrics.passed,
    failed: metrics.failed,
    passRate: metrics.passRate,
    duration: metrics.totalDuration,
    failedTestNames: metrics.failedTestNames,
    runNumber: runNumber
  };
  
  history = history.filter(entry => entry.runNumber !== runNumber);
  history.push(newEntry);
  
  if (history.length > 50) history = history.slice(-50);
  fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
}

function loadHistory() {
  return fs.existsSync(HISTORY_FILE) ? JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8')) : [];
}

function calculateTrends(metrics, history) {
  if (history.length < 2) return { durationDiff: 0, flakyTests: [] };

  const prevRun = history[history.length - 2];
  const durationDiff = metrics.totalDuration - (prevRun.duration || 0);

  const recentHistory = history.slice(-10);
  const failureCounts = {};
  
  recentHistory.forEach(run => {
    if (run.failedTestNames && Array.isArray(run.failedTestNames)) {
      run.failedTestNames.forEach(name => {
        failureCounts[name] = (failureCounts[name] || 0) + 1;
      });
    }
  });

  const flakyTests = Object.entries(failureCounts)
    .filter(([name, count]) => count > 1)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  return { durationDiff, flakyTests };
}

// --- MARKDOWN GENERATION ---

function generateNoDataMarkdown() {
  return `# 📊 QA Metrics Dashboard

No QA run data yet — this dashboard is regenerated automatically by CI. Run the workflow to populate it.
`;
}

function generateDashboardMarkdown(metrics, results, history, trends) {
  const env = (metrics.environment || 'staging').toUpperCase();
  const timestamp = new Date().toLocaleString('en-US', { timeZone: 'America/New_York', dateStyle: 'full', timeStyle: 'short' });
  const durationText = `${formatDuration(metrics.totalDuration)}`;

  return `# 📊 QA Metrics Dashboard

> **Automated Quality Gate Report**

**Last Updated:** ${timestamp} | **Env:** ${env} | **Branch:** ${metrics.branch}
**Run:** [#${metrics.runNumber}](https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${metrics.runId})

---

## 🎯 Executive Summary

| Metric | Current Value | Status |
|--------|---------------|----------------|
| **Pass Rate** | **${metrics.passRate.toFixed(1)}%** | ${getPassRateStatus(metrics.passRate)} |
| **Duration** | **${durationText}** | ${metrics.totalDuration > QUALITY_GATES.MAX_DURATION_SEC ? '⚠️ Long' : '✅ Good'} |
| **Total Tests** | ${metrics.totalTests} | ${metrics.passed} Pass / ${metrics.failed} Fail |
| **Functional** | ${results.functional.length} Tests | ${results.functional.length > 0 ? '✅ Active' : '❌ Missing'} |

---

${generateBrowserBreakdown(metrics.allTestObjects)}

---

## 🔍 Detailed Test Results

### 🔥 Smoke Tests
${generateTestTable(results.smoke)}

### 🧩 Functional Tests (Errors, Docs, Search)
${generateTestTable(results.functional)}

---

## 📈 History (Last 10 Runs)
| Date | Pass Rate | Duration | Failures |
|------|-----------|----------|----------|
${generateHistoryTable(history.slice(-10))}

---
`;
}

// --- HELPER FUNCTIONS ---

function generateBrowserBreakdown(allTests) {
  if (!allTests || allTests.length === 0) return '';
  const browsers = {};
  allTests.forEach(t => {
    const p = t.projectName || 'Default';
    if (!browsers[p]) browsers[p] = { total: 0, passed: 0 };
    browsers[p].total++;
    if (t.status === 'passed') browsers[p].passed++;
  });
  const keys = Object.keys(browsers);
  if (keys.length < 2 && keys[0] === 'Default') return '';
  let section = '### 🌐 Browser Breakdown\n\n| Project | Pass Rate | Status |\n|---|---|---|\n';
  keys.forEach(b => {
    const rate = (browsers[b].passed / browsers[b].total) * 100;
    const icon = rate >= 98 ? '🟢' : (rate >= 90 ? '🟡' : '🔴');
    section += `| **${b}** | ${rate.toFixed(1)}% | ${icon} |\n`;
  });
  return section;
}

function formatDuration(seconds) {
  if (!seconds) return '0s';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(0);
  return `${m}m ${s}s`;
}

function getPassRateStatus(passRate) {
  if (passRate >= 98) return '🟢 Excellent';
  if (passRate >= 90) return '🟡 Good';
  return '🔴 Attention';
}

function generateTestTable(tests) {
  if (!tests || tests.length === 0) return '> *No tests found in this category* \n';
  const displayTests = tests.slice(0, 10);
  const remaining = tests.length - displayTests.length;
  let table = '| Test Name | Status | Duration | Project |\n|-----------|--------|----------|---------|\n';
  displayTests.forEach(test => {
    const statusIcon = test.status === 'passed' ? '✅' : '❌';
    const dur = test.durationSec < 1 ? '<1s' : `${test.durationSec.toFixed(1)}s`;
    table += `| ${test.name} | ${statusIcon} ${test.status} | ${dur} | ${test.projectName} |\n`;
  });
  if (remaining > 0) table += `\n*... and ${remaining} more tests*\n`;
  return table;
}

function generateHistoryTable(history) {
  if (!history || history.length === 0) return '*No history yet*';
  return history.reverse().map(entry => {
    const date = new Date(entry.time).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const dur = formatDuration(entry.duration);
    const passRate = parseFloat(entry.passRate).toFixed(1);
    return `| ${date} | ${passRate}% | ${dur} | ${entry.failed} |`;
  }).join('\n');
}

main();
