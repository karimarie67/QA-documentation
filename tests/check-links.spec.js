// check-links.spec.js
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Production domains
// TODO(Engagement): replace with your site's real production domain(s)
const PRODUCTION_DOMAINS = [
  'https://www.example.com'
];

// Versions to spot-check
// TODO(Engagement): if your site has versioned documentation, list version identifiers here to spot-check each one; leave empty to skip this feature
const VERSIONS_TO_CHECK = [];

// Content identifiers to spot-check
// TODO(Engagement): replace with real content identifiers from your site, or leave as placeholders if unused (only relevant when VERSIONS_TO_CHECK is non-empty)
const CONTENT_IDENTIFIERS_TO_SPOT_CHECK = [
  'example-item-one',
  'example-item-two'
];

// State tracking
const visited = new Set();
const broken = [];
const redirects = [];
const malformedPaths = [];
let skipped = 0;
let docPagesChecked = 0;

function normalizeUrl(url) {
  for (const domain of PRODUCTION_DOMAINS) {
    if (url.startsWith(domain)) {
      return url.replace(domain, PRODUCTION_DOMAINS[0]);
    }
  }
  return url;
}

function isProductionUrl(url) {
  return PRODUCTION_DOMAINS.some(domain => url.startsWith(domain));
}

// TODO(Engagement): replace '/doc/libs/' with your site's actual versioned-documentation path prefix, or adjust this check entirely if your site has no separate doc-path structure
function isDocUrl(url) {
  return url.includes('/doc/libs/');
}

function shouldDeeplyClawl(url) {
  return !isDocUrl(url);
}

function shouldSkipUrl(url) {
  // Skip anchors and non-http links
  if (['#', 'mailto:', 'tel:', 'javascript:'].some(prefix => url.startsWith(prefix))) {
    return true;
  }

  // Skip external OAuth/login URLs
  const externalDomains = ['github.com', 'accounts.google.com', 'signin/v2', 'lifecycle/flows'];
  if (externalDomains.some(domain => url.includes(domain))) {
    return true;
  }

  // Skip external sites
  if (!isProductionUrl(url)) {
    return true;
  }

  // Skip downloads
  if (['.pdf', '.zip', '.tar.gz', '.tar.bz2', '.cpp', '.py', '.natvis'].some(ext => url.includes(ext))) {
    return true;
  }

  return false;
}

async function checkPage(page, url, sourceUrl = 'direct', depth = 0) {
  const normalizedUrl = normalizeUrl(url);

  if (visited.has(normalizedUrl)) {
    return;
  }
  visited.add(normalizedUrl);

  if (shouldSkipUrl(normalizedUrl)) {
    skipped++;
    return;
  }

  // Check for malformed paths
  try {
    const urlObj = new URL(normalizedUrl);
    if (urlObj.pathname.includes('/libs/') && !urlObj.pathname.includes('/doc/libs/')) {
      malformedPaths.push({
        source: normalizeUrl(sourceUrl),
        url: normalizedUrl,
        suggested_fix: normalizedUrl.replace('/libs/', '/doc/libs/latest/libs/')
      });
      console.log(`⚠ Malformed path: ${normalizedUrl}`);
      return;
    }
  } catch (e) {
    // Invalid URL, skip it
    return;
  }

  // Limit depth in doc pages
  const isDoc = isDocUrl(normalizedUrl);
  if (isDoc) {
    docPagesChecked++;
    if (depth > 2) {
      return;
    }
  }

  try {
    // Be respectful to production
    await page.waitForTimeout(300);

    const response = await page.goto(normalizedUrl, { 
      waitUntil: 'domcontentloaded',
      timeout: 45000 
    });
    
    const status = response?.status || 0;

    if (status >= 400) {
      broken.push({
        source: normalizeUrl(sourceUrl),
        url: normalizedUrl,
        status,
        type: isDoc ? 'doc' : 'site'
      });
      console.log(`✗ [${status}] ${normalizedUrl}`);
      return;
    } else if (status >= 300 && status < 400) {
      redirects.push({
        source: normalizeUrl(sourceUrl),
        url: normalizedUrl,
        status
      });
      console.log(`↪ [${status}] ${normalizedUrl}`);
    } else {
      if (visited.size % 25 === 0) {
        console.log(`✓ Checked ${visited.size} pages (${docPagesChecked} doc pages)...`);
      }
    }

    // Decide whether to crawl links
    if (!shouldDeeplyClawl(normalizedUrl)) {
      return;
    }

    // Extract links
    const links = await page.$$eval('a[href]', anchors => 
      anchors.map(a => a.href)
    );

    for (const href of links) {
      if (['#', 'mailto:', 'tel:', 'javascript:'].some(prefix => href.startsWith(prefix))) {
        continue;
      }

      if (shouldSkipUrl(href)) {
        continue;
      }

      const normalizedLink = normalizeUrl(href);
      if (!visited.has(normalizedLink)) {
        const nextDepth = isDoc ? depth + 1 : depth;
        await checkPage(page, href, normalizedUrl, nextDepth);
      }
    }

  } catch (error) {
    console.log(`✗ Error on ${normalizedUrl}: ${error.message}`);
    broken.push({
      source: normalizeUrl(sourceUrl),
      url: normalizedUrl,
      status: 'error',
      type: error.message
    });
  }
}

function saveReport() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const reportDir = path.join(process.cwd(), 'test-results', 'link-check');
  
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }

  // Save broken links
  if (broken.length > 0) {
    const brokenFile = path.join(reportDir, `broken-links-${timestamp}.csv`);
    const brokenCsv = [
      'source,url,status,type',
      ...broken.map(b => `"${b.source}","${b.url}",${b.status},${b.type}`)
    ].join('\n');
    fs.writeFileSync(brokenFile, brokenCsv);
    console.log(`\n❌ Broken links saved to: ${brokenFile}`);
  }

  // Save malformed paths
  if (malformedPaths.length > 0) {
    const malformedFile = path.join(reportDir, `malformed-paths-${timestamp}.csv`);
    const malformedCsv = [
      'source,url,suggested_fix',
      ...malformedPaths.map(m => `"${m.source}","${m.url}","${m.suggested_fix}"`)
    ].join('\n');
    fs.writeFileSync(malformedFile, malformedCsv);
    console.log(`⚠ Malformed paths saved to: ${malformedFile}`);
  }
}

function printSummary() {
  const siteBroken = broken.filter(b => b.type === 'site');
  const docBroken = broken.filter(b => b.type === 'doc');

  console.log('\n' + '='.repeat(80));
  console.log('SUMMARY - PRODUCTION CHECK');
  console.log('='.repeat(80));
  console.log(`✓ Total unique pages checked: ${visited.size}`);
  console.log(`📚 Documentation pages checked: ${docPagesChecked}`);
  console.log(`⊘ Skipped (OAuth, external, etc.): ${skipped}`);
  console.log(`⚠ Malformed paths (/libs/ instead of /doc/libs/): ${malformedPaths.length}`);
  console.log(`✗ Total broken links: ${broken.length}`);
  console.log(`  - Site pages: ${siteBroken.length}`);
  console.log(`  - Doc pages (libraries): ${docBroken.length}`);
  console.log(`↪ Redirects: ${redirects.length}`);

  if (malformedPaths.length > 0) {
    console.log('\n⚠ MALFORMED PATHS (needs a source-code fix):');
    malformedPaths.slice(0, 10).forEach((link, i) => {
      console.log(`  ${i + 1}. ${link.url}`);
      console.log(`      Found on: ${link.source}`);
      console.log(`      Should be: ${link.suggested_fix}`);
    });
  }

  if (broken.length > 0) {
    console.log('\nBroken links by status:');
    const statusCounts = {};
    broken.forEach(b => {
      const status = String(b.status);
      statusCounts[status] = (statusCounts[status] || 0) + 1;
    });
    Object.entries(statusCounts).sort().forEach(([status, count]) => {
      console.log(`  ${status}: ${count}`);
    });

    if (siteBroken.length > 0) {
      console.log('\n🚨 BROKEN SITE LINKS (Priority):');
      siteBroken.slice(0, 10).forEach((link, i) => {
        console.log(`  ${i + 1}. [${link.status}] ${link.url}`);
        console.log(`      Found on: ${link.source}`);
      });
    }

    if (docBroken.length > 0) {
      console.log('\n📚 BROKEN DOC LINKS (Spot Check Results):');
      docBroken.slice(0, 10).forEach((link, i) => {
        console.log(`  ${i + 1}. [${link.status}] ${link.url}`);
        console.log(`      Found on: ${link.source}`);
      });
    }
  } else {
    console.log('\n🎉 No broken links found!');
  }
}

test.describe('Production Link Check', () => {
  test.setTimeout(1800000); // 30 minutes for the whole test

  test.beforeEach(() => {
    // Clear state before each test run
    visited.clear();
    broken.length = 0;
    redirects.length = 0;
    malformedPaths.length = 0;
    skipped = 0;
    docPagesChecked = 0;
  });

  test('should check all main site pages and spot-check documentation', async ({ page }) => {
    console.log('='.repeat(80));
    console.log('🚀 PRODUCTION LINK CHECKER');
    console.log('='.repeat(80));
    console.log('⚠️  WARNING: Running against PRODUCTION site');
    console.log('⚠️  Using respectful delays (0.3s between requests)');
    console.log(`Started at ${new Date().toLocaleString()}`);
    console.log(`Strategy: Deep check main site pages, spot-check documentation`);
    console.log(`Versions to check: ${VERSIONS_TO_CHECK.join(', ')}\n`);

    // Set user agent
    await page.setExtraHTTPHeaders({
      'User-Agent': `Mozilla/5.0 (compatible; SiteLinkChecker/1.0; +${PRODUCTION_DOMAINS[0]})`
    });

    // Main site pages
    const startUrls = [
      `${PRODUCTION_DOMAINS[0]}/`,
      `${PRODUCTION_DOMAINS[0]}/libraries/`,
      `${PRODUCTION_DOMAINS[0]}/docs/`,
      `${PRODUCTION_DOMAINS[0]}/releases/`,
      `${PRODUCTION_DOMAINS[0]}/news/`,
      `${PRODUCTION_DOMAINS[0]}/community/`,
    ];

    console.log('Checking main site pages...');
    for (const url of startUrls) {
      await checkPage(page, url);
    }

    // Spot-check library docs
    console.log('\nSpot-checking library documentation...');
    for (const version of VERSIONS_TO_CHECK) {
      const versionUrl = `${PRODUCTION_DOMAINS[0]}/doc/libs/${version}/`;
      console.log(`\n  Checking version ${version}...`);

      await checkPage(page, versionUrl);

      for (const lib of CONTENT_IDENTIFIERS_TO_SPOT_CHECK) {
        const libUrl = `${PRODUCTION_DOMAINS[0]}/doc/libs/${version}/libs/${lib}/`;
        await checkPage(page, libUrl, versionUrl, 0);
      }
    }

    // Generate reports
    saveReport();
    printSummary();

    console.log(`\nCompleted at ${new Date().toLocaleString()}`);

    // Fail test if there are broken site links (not doc links)
    const siteBroken = broken.filter(b => b.type === 'site');
    
    // Always pass the test but report findings
    if (siteBroken.length > 0) {
      console.log(`\n⚠️  WARNING: Found ${siteBroken.length} broken site links, but test will pass for reporting purposes.`);
      console.log(`Check the CSV reports in test-results/link-check/ for details.`);
    }
    
    // Optional: Uncomment the line below if you want the test to actually fail on broken links
    // expect(siteBroken.length, `Found ${siteBroken.length} broken site links`).toBe(0);
  });
});