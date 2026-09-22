#!/usr/bin/env node
/**
 * template-check.js
 *
 * Structural smoke check for the QA-documentation framework template.
 *
 * 1. Confirms the framework's two site-config modules (config-helper.js,
 *    selectors.js) import cleanly.
 * 2. Confirms the tracked playwright.config.js can discover every spec in
 *    its testDir (via `playwright test --list --reporter=json`), and that
 *    the five expected top-level specs are all present.
 *
 * This is not a syntax linter. `node --check` was considered and rejected:
 * on a `.js` file containing an `import` statement, Node's module-syntax
 * auto-detection fires before `--check`'s validation and makes it exit 0
 * regardless of body syntax errors - it would never catch a broken spec.
 * `playwright test --list` genuinely parses and enumerates every spec, so
 * it's the real proof the template, as configured, still hangs together.
 */

import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const EXPECTED_SPECS = [
  'smoke_tests.spec.js',
  'documentation_tests.spec.js',
  'download_search_tests.spec.js',
  'error_handling_tests.spec.js',
  'check-links.spec.js',
];

async function checkModuleImports() {
  const modules = [
    ['config-helper.js', path.join(repoRoot, 'config-helper.js')],
    ['selectors.js', path.join(repoRoot, 'selectors.js')],
  ];

  for (const [label, modulePath] of modules) {
    try {
      await import(pathToFileURL(modulePath).href);
    } catch (err) {
      console.error(`FAIL: could not import ${label} (${modulePath})`);
      console.error(err && err.stack ? err.stack : err);
      process.exit(1);
    }
  }

  console.log('OK: config-helper.js and selectors.js both import cleanly.');
}

function listDiscoveredSpecs() {
  // Strip any inherited JSON-output-to-file env vars so Playwright's JSON
  // reporter writes to stdout instead, where we can parse it.
  const env = { ...process.env };
  delete env.PLAYWRIGHT_JSON_OUTPUT_NAME;
  delete env.PLAYWRIGHT_JSON_OUTPUT_FILE;

  const result = spawnSync(
    'npx',
    ['playwright', 'test', '--list', '--reporter=json'],
    {
      cwd: repoRoot,
      env,
      encoding: 'utf8',
      maxBuffer: 1024 * 1024 * 50,
    }
  );

  if (result.error) {
    console.error('FAIL: could not spawn `npx playwright test --list --reporter=json`.');
    console.error(result.error);
    process.exit(1);
  }

  const stdout = result.stdout || '';
  const stderr = result.stderr || '';

  let parsed;
  try {
    parsed = JSON.parse(stdout);
  } catch (err) {
    console.error('FAIL: `playwright test --list --reporter=json` did not produce parseable JSON.');
    console.error('--- raw stdout ---');
    console.error(stdout);
    console.error('--- raw stderr ---');
    console.error(stderr);
    process.exit(1);
  }

  if (result.status !== 0) {
    console.error(`FAIL: \`playwright test --list\` exited with status ${result.status}.`);
    console.error('--- raw stdout ---');
    console.error(stdout);
    console.error('--- raw stderr ---');
    console.error(stderr);
    process.exit(1);
  }

  if (Array.isArray(parsed.errors) && parsed.errors.length > 0) {
    console.error('FAIL: `playwright test --list` reported errors while discovering specs.');
    console.error(JSON.stringify(parsed.errors, null, 2));
    process.exit(1);
  }

  const fileNames = new Set();
  for (const suite of parsed.suites || []) {
    if (suite && suite.file) {
      fileNames.add(path.basename(suite.file));
    }
  }

  return fileNames;
}

function checkExpectedSpecsPresent(discoveredFileNames) {
  if (discoveredFileNames.size === 0) {
    console.error('FAIL: playwright discovered zero spec files.');
    process.exit(1);
  }

  const missing = EXPECTED_SPECS.filter(name => !discoveredFileNames.has(name));

  if (missing.length > 0) {
    console.error('FAIL: the following expected spec files were not discovered:');
    for (const name of missing) {
      console.error(`  - ${name}`);
    }
    console.error('Discovered spec files were:');
    for (const name of [...discoveredFileNames].sort()) {
      console.error(`  - ${name}`);
    }
    process.exit(1);
  }

  console.log(
    `OK: all ${EXPECTED_SPECS.length} expected specs were discovered (${[...discoveredFileNames]
      .sort()
      .join(', ')}).`
  );
}

async function main() {
  await checkModuleImports();
  const discovered = listDiscoveredSpecs();
  checkExpectedSpecsPresent(discovered);
  console.log('template-check: PASS');
  process.exit(0);
}

main().catch(err => {
  console.error('FAIL: template-check crashed unexpectedly.');
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
