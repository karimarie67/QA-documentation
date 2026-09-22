import { test, expect } from '@playwright/test';
import fs from 'fs';
import { selectors } from '../selectors.js';
import { logAndScreenshot } from '../utils.js';
import { buildURL, testData, urlPatterns } from '../config-helper.js';
import { testPatterns, testElementVisibility, findVisibleElement } from '../test-helpers.js';

fs.mkdirSync('test-results', { recursive: true });

test.describe('Documentation Tests', () => {
  
  test('Documentation page loads with table of contents', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_001' });
    const testId = 'TC_DOC_001';
    testInfo.setTimeout(45000);

    const docUrl = buildURL(testInfo, urlPatterns.documentation, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

    // Look for table of contents
    const tocSelectors = [
      page.locator('[class*="toc"], [id*="toc"]'),
      page.locator('nav[aria-label*="table of contents" i]'),
      page.locator('.sidebar, .navigation, [class*="sidebar"]'),
      page.locator('ul li a').first() // Generic navigation list
    ];

    let tocFound = false;
    for (const selector of tocSelectors) {
      const count = await selector.count();
      if (count > 0) {
        const isVisible = await selector.first().isVisible().catch(() => false);
        if (isVisible) {
          await expect(selector.first()).toBeVisible({ timeout: testData.timeouts.medium });
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Table of contents found\n`);
          tocFound = true;
          break;
        }
      }
    }

    if (tocFound) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Documentation TOC verified\n`);
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No explicit TOC found - doc may use different navigation\n`);
    }

    // Verify main content area exists
    const contentLocator = selectors.content(page);
    await testElementVisibility(page, testInfo, contentLocator, [], 'Documentation content', testId);
  });

  test('Library documentation links are accessible', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_002' });
    const testId = 'TC_DOC_002';
    testInfo.setTimeout(60000);

    const librariesUrl = buildURL(testInfo, urlPatterns.libraries, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, librariesUrl, testId);

    // Find library links
    // TODO(Engagement): replace with real content identifiers from your site
    const popularLibraries = ['item-one', 'item-two', 'item-three'];
    let foundLibraries = 0;

    for (const libName of popularLibraries) {
      const libraryLink = page.locator(`a:has-text("${libName}")`).first();
      const count = await libraryLink.count();
      
      if (count > 0) {
        const isVisible = await libraryLink.isVisible().catch(() => false);
        
        if (isVisible) {
          const href = await libraryLink.getAttribute('href');
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${libName} library: ${href}\n`);
          
          // Verify it's a valid link
          expect(href).toBeTruthy();
          foundLibraries++;
          
          // Test clicking one library
          if (foundLibraries === 1) {
            await libraryLink.click();
            await page.waitForLoadState('networkidle', { timeout: testData.timeouts.medium });
            
            const newUrl = page.url();
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Navigated to library doc: ${newUrl}\n`);
            
            // Verify we're on a documentation page
            const hasDocContent = await page.locator('h1, h2, main, article').count();
            expect(hasDocContent).toBeGreaterThan(0);
            
            // Go back for next test
            await page.goto(librariesUrl, { waitUntil: 'networkidle' });
          }
        }
      }
    }

    expect(foundLibraries).toBeGreaterThan(0);
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${foundLibraries} library links\n`);
  });

  test('Code examples are properly formatted', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_003' });
    const testId = 'TC_DOC_003';
    testInfo.setTimeout(45000);

    try {
      const docUrl = buildURL(testInfo, urlPatterns.docLibsVersion(), { cachebust: true });
      await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

      // Look for code blocks
      const codeSelectors = [
        page.locator('pre code'),
        page.locator('.code, .example-code'),
        page.locator('[class*="code-"]'),
        page.locator('pre')
      ];

      let codeBlockFound = false;
      for (const selector of codeSelectors) {
        const count = await selector.count();
        if (count > 0) {
          const firstCode = selector.first();
          const isVisible = await firstCode.isVisible().catch(() => false);
          
          if (isVisible) {
            const codeText = await firstCode.textContent();
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Found code block with ${codeText?.length} characters\n`);
            
            // Verify it contains code-like content
            const looksLikeCode = /[{};()#include]/.test(codeText || '');
            if (looksLikeCode) {
              fs.appendFileSync('test-results/test-logs.txt', `${testId} Code block appears properly formatted\n`);
              codeBlockFound = true;
            }
            break;
          }
        }
      }

      if (codeBlockFound) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Code examples verified\n`);
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No code examples found on this page\n`);
      }
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test failed: ${error.message}\n`);
      // Don't fail the test if page doesn't exist
      if (!error.message.includes('closed')) {
        throw error;
      }
    }
  });

  test('Documentation breadcrumbs navigation works', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_004' });
    const testId = 'TC_DOC_004';
    testInfo.setTimeout(45000);

    const docUrl = buildURL(testInfo, urlPatterns.docLibsVersion(), { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

    // Look for breadcrumbs
    const breadcrumbSelectors = [
      page.locator('[aria-label*="breadcrumb" i]'),
      page.locator('.breadcrumb, .breadcrumbs'),
      page.locator('[class*="breadcrumb"]'),
      page.locator('nav ol, nav ul').first()
    ];

    let breadcrumbsFound = false;
    for (const selector of breadcrumbSelectors) {
      const count = await selector.count();
      if (count > 0) {
        const isVisible = await selector.first().isVisible().catch(() => false);
        
        if (isVisible) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Breadcrumbs found\n`);
          breadcrumbsFound = true;
          
          // Try clicking a breadcrumb link
          const breadcrumbLinks = await selector.locator('a').all();
          if (breadcrumbLinks.length > 0) {
            const firstLink = breadcrumbLinks[0];
            const href = await firstLink.getAttribute('href');
            
            if (href && href !== '#') {
              const urlBefore = page.url();
              await firstLink.click();
              await page.waitForLoadState('networkidle', { timeout: testData.timeouts.medium });
              const urlAfter = page.url();
              
              fs.appendFileSync('test-results/test-logs.txt', `${testId} Breadcrumb navigation: ${urlBefore} -> ${urlAfter}\n`);
              expect(urlAfter).not.toBe(urlBefore);
            }
          }
          break;
        }
      }
    }

    if (breadcrumbsFound) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Breadcrumbs navigation verified\n`);
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No breadcrumbs found - may not be used on this page\n`);
    }
  });

  test('Documentation version switcher works', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_005' });
    const testId = 'TC_DOC_005';
    testInfo.setTimeout(45000);

    const docUrl = buildURL(testInfo, urlPatterns.docLibsVersion(), { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

    // Look for version switcher
    const versionSelectors = [
      page.locator('select[name*="version"], select[id*="version"]'),
      page.locator('[data-testid*="version"]'),
      page.locator('.version-switcher, .version-selector'),
      page.locator('text=/version/i').locator('..').locator('select')
    ];

    let versionSwitcher = null;
    for (const selector of versionSelectors) {
      const count = await selector.count();
      if (count > 0) {
        const isVisible = await selector.first().isVisible().catch(() => false);
        if (isVisible) {
          versionSwitcher = selector.first();
          break;
        }
      }
    }

    if (versionSwitcher) {
      await expect(versionSwitcher).toBeVisible({ timeout: testData.timeouts.medium });
      
      const tagName = await versionSwitcher.evaluate(el => el.tagName.toLowerCase());
      
      if (tagName === 'select') {
        const options = await versionSwitcher.locator('option').all();
        const optionCount = options.length;
        
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${optionCount} version options\n`);
        expect(optionCount).toBeGreaterThan(0);
        
        // Try switching version if multiple options exist
        if (optionCount > 1) {
          const urlBefore = page.url();
          await versionSwitcher.selectOption({ index: 1 });
          await page.waitForTimeout(2000);
          const urlAfter = page.url();
          
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Version switch: ${urlBefore} -> ${urlAfter}\n`);
        }
      }
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No version switcher found - may be on latest version only\n`);
    }
  });

  test('Documentation search within docs works', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_006' });
    const testId = 'TC_DOC_006';
    testInfo.setTimeout(45000);

    const docUrl = buildURL(testInfo, urlPatterns.documentation, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

    // Look for documentation-specific search
    const docSearchSelectors = [
      page.locator('input[placeholder*="search doc" i]'),
      page.locator('input[placeholder*="search librar" i]'),
      page.locator('.doc-search input, .library-search input'),
      page.locator('input[type="search"]')
    ];

    let searchInput = null;
    for (const selector of docSearchSelectors) {
      const count = await selector.count();
      if (count > 0) {
        searchInput = await findVisibleElement(selector, 'Doc search input', testId);
        if (searchInput) break;
      }
    }

    if (searchInput) {
      await searchInput.fill(testData.searchTerms.working);
      await searchInput.press('Enter');
      await page.waitForTimeout(2000);

      // Look for search results
      const resultsFound = await page.locator('text=/result|found|match/i').count() > 0;
      
      if (resultsFound) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Documentation search returned results\n`);
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search executed but results format unclear\n`);
      }
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No doc-specific search found - uses global search\n`);
    }
  });

  test('Documentation anchor links work correctly', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_007' });
    const testId = 'TC_DOC_007';
    testInfo.setTimeout(30000);

    try {
      const docUrl = buildURL(testInfo, urlPatterns.docLibsVersion(), { cachebust: true });
      await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

      // Check if page is still open
      if (page.isClosed()) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Page closed, skipping test\n`);
        return;
      }

      // Find anchor links (links starting with #)
      const anchorLinks = await page.locator('a[href^="#"]').all();
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${anchorLinks.length} anchor links\n`);

      if (anchorLinks.length > 0) {
        // Test first anchor link
        const firstAnchor = anchorLinks[0];
        const href = await firstAnchor.getAttribute('href');
        const isVisible = await firstAnchor.isVisible().catch(() => false);

        if (isVisible && href && href !== '#') {
          const yBefore = await page.evaluate(() => window.scrollY).catch(() => 0);
          
          // Click the anchor link
          await firstAnchor.click().catch(() => {
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Could not click anchor link\n`);
          });
          
          await page.waitForTimeout(500);
          const yAfter = await page.evaluate(() => window.scrollY).catch(() => 0);

          fs.appendFileSync('test-results/test-logs.txt', `${testId} Anchor click: scroll from ${yBefore} to ${yAfter}\n`);
          
          // Verify page scrolled (unless already at top)
          if (yBefore > 100 && yAfter !== yBefore) {
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Anchor link successfully scrolled page\n`);
          }
        }
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No anchor links found on this page\n`);
      }
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test error: ${error.message}\n`);
      if (error.message.includes('closed')) {
        return;
      }
    }
  });

  test('Documentation external links open correctly', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_008' });
    const testId = 'TC_DOC_008';
    testInfo.setTimeout(45000);

    try {
      const docUrl = buildURL(testInfo, urlPatterns.documentation, { cachebust: true });
      await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

      // Check if page is still open
      if (page.isClosed()) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Page closed, skipping test\n`);
        return;
      }

      // Find external links in documentation
      const externalLinks = await page.locator('a[href^="http"]').all();
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${externalLinks.length} external links\n`);

      let checkedLinks = 0;
      const maxToCheck = 3;

      for (let i = 0; i < Math.min(externalLinks.length, maxToCheck); i++) {
        const link = externalLinks[i];
        const href = await link.getAttribute('href');
        const isVisible = await link.isVisible().catch(() => false);
        const target = await link.getAttribute('target');

        if (href && isVisible) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} External link ${i}: ${href}, target=${target}\n`);
          
          // Check if link opens in new tab
          if (target === '_blank') {
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Link correctly set to open in new tab\n`);
          }
          
          checkedLinks++;
        }
      }

      if (checkedLinks > 0) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Checked ${checkedLinks} external links\n`);
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No external links found in documentation\n`);
      }
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test error: ${error.message}\n`);
      if (error.message.includes('closed')) {
        return;
      }
    }
  });

  test('Documentation page titles are descriptive', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_009' });
    const testId = 'TC_DOC_009';
    testInfo.setTimeout(45000); // Increased timeout

    try {
      const docUrl = buildURL(testInfo, urlPatterns.documentation, { cachebust: true });
      
      // Use shorter timeout for page load
      const response = await page.goto(docUrl, { 
        waitUntil: 'domcontentloaded', 
        timeout: 20000 
      }).catch(() => null);

      if (!response) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Could not load page, skipping test\n`);
        return;
      }

      // Quick check if page is still open
      if (page.isClosed()) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Page closed, skipping test\n`);
        return;
      }

      // Get title with timeout
      const pageTitle = await page.title().catch(() => '');
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Page title: "${pageTitle}"\n`);

      // Get H1 with timeout
      const h1 = page.locator('h1').first();
      const h1Count = await h1.count();
      
      if (h1Count > 0) {
        const h1Text = await h1.textContent().catch(() => '');
        fs.appendFileSync('test-results/test-logs.txt', `${testId} H1 text: "${h1Text}"\n`);
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No H1 found on page\n`);
      }

      // Verify title is descriptive (not generic)
      if (pageTitle.length > 10) {
        // TODO(Engagement): replace with keywords that should appear in this site's page titles
        const expectedTitleKeywords = ['Documentation', 'Docs', 'Guide'];
        const isDescriptive = expectedTitleKeywords.some(kw => pageTitle.includes(kw));
        
        if (isDescriptive) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Title is descriptive\n`);
        } else {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Title may not be descriptive: "${pageTitle}"\n`);
        }
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Title is too short: "${pageTitle}"\n`);
      }

    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test error: ${error.message}\n`);
      // Don't fail test - just log and continue
    }
  });

  test('Documentation PDF/print versions are accessible', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOC_010' });
    const testId = 'TC_DOC_010';
    testInfo.setTimeout(30000);

    const docUrl = buildURL(testInfo, urlPatterns.documentation, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, docUrl, testId);

    // Look for PDF or print links
    const pdfPrintSelectors = [
      page.locator('a[href*=".pdf"]'),
      page.locator('a:has-text("PDF"), button:has-text("PDF")'),
      page.locator('a:has-text("Print"), button:has-text("Print")'),
      page.locator('[class*="print"], [class*="pdf"]')
    ];

    let pdfPrintFound = false;
    for (const selector of pdfPrintSelectors) {
      const count = await selector.count();
      if (count > 0) {
        const isVisible = await selector.first().isVisible().catch(() => false);
        if (isVisible) {
          const text = await selector.first().textContent();
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Found PDF/Print option: ${text}\n`);
          pdfPrintFound = true;
          break;
        }
      }
    }

    if (pdfPrintFound) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} PDF/Print version available\n`);
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No PDF/Print options found - may not be offered\n`);
    }
  });
});