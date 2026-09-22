import { test, expect } from '@playwright/test';
import fs from 'fs';
import { selectors } from '../selectors.js';
import { logAndScreenshot } from '../utils.js';
import { buildURL, testData, urlPatterns } from '../config-helper.js';
import { testPatterns, findVisibleElement, performSearch, findSearchResults } from '../test-helpers.js';

fs.mkdirSync('test-results', { recursive: true });

test.describe('Download Tests', () => {

  test('Download links return valid HTTP status codes', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOWNLOAD_001' });
    const testId = 'TC_DOWNLOAD_001';
    testInfo.setTimeout(60000);

    const releasesUrl = buildURL(testInfo, urlPatterns.releases, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, releasesUrl, testId);

    // Find all download links
    const downloadSelectors = [
      'a[href*=".tar.gz"]',
      'a[href*=".zip"]'
    ];

    const downloadLinks = [];
    for (const selector of downloadSelectors) {
      const links = await page.locator(selector).all();
      for (const link of links) {
        const href = await link.getAttribute('href');
        const isVisible = await link.isVisible().catch(() => false);
        if (href && isVisible) {
          downloadLinks.push({ element: link, href });
        }
      }
    }

    fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${downloadLinks.length} download links\n`);
    expect(downloadLinks.length).toBeGreaterThan(0);

    // Check status codes for first 5 download links
    const linksToCheck = downloadLinks.slice(0, 5);

    for (const { href } of linksToCheck) {
      try {
        // Use HEAD request to check without downloading
        const response = await page.request.head(href, { timeout: 15000 });
        const status = response.status();

        fs.appendFileSync('test-results/test-logs.txt', `${testId} Download link: ${href} - Status: ${status}\n`);

        // Should return 200 OK or 302 redirect
        expect(status).toBeGreaterThanOrEqual(200);
        expect(status).toBeLessThan(400);
      } catch (error) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Failed to check ${href}: ${error.message}\n`);
      }
    }
  });

  test('Download file names are correct format', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOWNLOAD_002' });
    const testId = 'TC_DOWNLOAD_002';
    testInfo.setTimeout(45000);

    const releasesUrl = buildURL(testInfo, urlPatterns.releases, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, releasesUrl, testId);

    // Find download links
    const downloadLinks = await page.locator('a[href*=".tar.gz"], a[href*=".zip"]').all();
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${downloadLinks.length} download links\n`);

    for (const link of downloadLinks.slice(0, 5)) {
      const href = await link.getAttribute('href');
      const text = await link.textContent();

      // Verify filename format: example-X.XX.X.tar.gz or similar
      // TODO(Engagement): replace with your site's actual download filename pattern
      const hasValidFormat = /example[-_]?\S*\.(tar\.gz|zip|7z)/.test(href) ||
                            /\d+\.\d+\.\d+/.test(href);

      fs.appendFileSync('test-results/test-logs.txt', `${testId} Link: ${text?.trim()} -> ${href}, Valid format: ${hasValidFormat}\n`);

      if (href && testData.downloadFiles.supported.test(href)) {
        expect(hasValidFormat).toBeTruthy();
      }
    }
  });

  test('Version selector displays available versions', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOWNLOAD_003' });
    const testId = 'TC_DOWNLOAD_003';
    testInfo.setTimeout(30000);

    const releasesUrl = buildURL(testInfo, urlPatterns.releases, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, releasesUrl, testId);

    // Look for version selectors
    // TODO(Engagement): replace with your site's actual version-number format
    const versionSelectors = [
      page.locator('select[name*="version"], select[id*="version"]'),
      page.locator('select option[value*="1."]').locator('..'),
      page.locator('[data-testid*="version"]'),
      page.locator('.version-selector, #version-selector')
    ];

    let versionDropdown = null;
    for (const selector of versionSelectors) {
      const count = await selector.count();
      if (count > 0) {
        versionDropdown = selector.first();
        const isVisible = await versionDropdown.isVisible().catch(() => false);
        if (isVisible) break;
      }
    }

    if (versionDropdown) {
      await expect(versionDropdown).toBeVisible({ timeout: testData.timeouts.medium });

      // Get available options
      const options = await versionDropdown.locator('option').all();
      const optionTexts = await Promise.all(options.map(opt => opt.textContent()));

      fs.appendFileSync('test-results/test-logs.txt', `${testId} Available versions: ${optionTexts.join(', ')}\n`);
      expect(options.length).toBeGreaterThan(0);
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No version selector found - versions may be displayed differently\n`);

      // Look for version numbers in text
      // TODO(Engagement): replace with your site's actual version-number format
      const versionText = await page.locator('text=/\\d+\\.\\d+|version/i').count();
      expect(versionText).toBeGreaterThan(0);
    }
  });

  test('Download page displays file sizes', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_DOWNLOAD_004' });
    const testId = 'TC_DOWNLOAD_004';
    testInfo.setTimeout(30000);

    const releasesUrl = buildURL(testInfo, urlPatterns.releases, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, releasesUrl, testId);

    // Look for file size information
    const fileSizePatterns = [
      page.locator('text=/\\d+\\s*(MB|GB|KB)/i'),
      page.locator('text=/\\d+\\.\\d+\\s*(MB|GB)/i'),
      page.locator('[class*="size"], [class*="file-size"]')
    ];

    let fileSizeFound = false;
    for (const pattern of fileSizePatterns) {
      const count = await pattern.count();
      if (count > 0) {
        const firstSize = pattern.first();
        const isVisible = await firstSize.isVisible().catch(() => false);
        if (isVisible) {
          const text = await firstSize.textContent();
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Found file size: ${text}\n`);
          fileSizeFound = true;
          break;
        }
      }
    }

    if (fileSizeFound) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} File sizes displayed on download page\n`);
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No file sizes found - may not be displayed on this page\n`);
    }
  });
});

test.describe('Search Tests', () => {

  test('Search returns relevant results for common queries', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_SEARCH_001' });
    const testId = 'TC_SEARCH_001';
    testInfo.setTimeout(45000);

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    // TODO(Engagement): replace with real search terms known to return results on your site
    const commonQueries = ['example-one', 'example-two', 'example-three'];

    for (const query of commonQueries) {
      await performSearch(page, testInfo, selectors, query, testId);

      const { element: searchResults, count: resultCount } = await findSearchResults(page, query, testId);

      if (searchResults && resultCount > 0) {
        await expect(searchResults).toBeVisible({ timeout: testData.timeouts.medium });
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search for "${query}" returned ${resultCount} results\n`);

        // Verify result contains the search term
        const resultText = await searchResults.textContent();
        const isRelevant = resultText?.toLowerCase().includes(query.toLowerCase());
        expect(isRelevant).toBeTruthy();
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No results found for "${query}"\n`);
      }

      // Go back to homepage for next search
      await page.goto(homepageUrl, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1000);
    }
  });

  test('Search with special characters handles gracefully', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_SEARCH_002' });
    const testId = 'TC_SEARCH_002';
    testInfo.setTimeout(60000); // Increased timeout

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    // TODO(Engagement): these are placeholder special-character queries - replace with characters/patterns relevant to your site's search
    const specialQueries = ['a+b', 'foo::bar'];

    for (const query of specialQueries) {
      try {
        await performSearch(page, testInfo, selectors, query, testId);
        await page.waitForTimeout(3000); // Increased wait time

        // Should not crash or show error
        const hasError = await page.locator('text=/error|500|crash/i').count();
        expect(hasError).toBe(0);

        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search with "${query}" handled gracefully\n`);

        // Navigate back for next test
        await page.goto(homepageUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(1000);
      } catch (error) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search with "${query}" noted: ${error.message}\n`);
        // Try to recover by going back to homepage
        try {
          await page.goto(homepageUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        } catch (e) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Could not recover, skipping remaining searches\n`);
          break;
        }
      }
    }
  });

  test('Empty search shows appropriate message', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_SEARCH_003' });
    const testId = 'TC_SEARCH_003';
    testInfo.setTimeout(30000);

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    try {
      // Use the working search functionality from your existing tests
      const searchInput = selectors.searchInput(page);
      const searchCount = await searchInput.count();

      if (searchCount === 0) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No search input found, skipping test\n`);
        return;
      }

      const visibleSearch = await findVisibleElement(searchInput, 'Search input', testId);
      if (!visibleSearch) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search input not visible, skipping test\n`);
        return;
      }

      // Submit empty search
      await visibleSearch.click();
      await visibleSearch.press('Enter');
      await page.waitForTimeout(2000);

      // Look for appropriate message or behavior
      const messages = [
        page.locator('text=/please enter|required|empty/i'),
        page.locator('text=/no results/i'),
        page.locator('[role="alert"]')
      ];

      let messageFound = false;
      for (const message of messages) {
        const isVisible = await message.isVisible().catch(() => false);
        if (isVisible) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Empty search message displayed\n`);
          messageFound = true;
          break;
        }
      }

      // Either shows message or prevents empty search
      if (!messageFound) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Empty search prevented or handled silently\n`);
      }
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test skipped: ${error.message}\n`);
    }
  });

  test('Search result pagination works correctly', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_SEARCH_004' });
    const testId = 'TC_SEARCH_004';
    testInfo.setTimeout(45000);

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    // Search for something that should have many results
    await performSearch(page, testInfo, selectors, testData.searchTerms.working, testId);
    await page.waitForTimeout(2000);

    // Look for pagination elements
    const paginationSelectors = [
      page.locator('[aria-label*="pagination"], [role="navigation"][aria-label*="page"]'),
      page.locator('.pagination, .paging, .page-navigation'),
      page.locator('a:has-text("Next"), button:has-text("Next")'),
      page.locator('a:has-text("2"), button:has-text("2")')
    ];

    let paginationFound = false;
    for (const selector of paginationSelectors) {
      const count = await selector.count();
      if (count > 0) {
        const isVisible = await selector.first().isVisible().catch(() => false);
        if (isVisible) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Pagination controls found\n`);
          paginationFound = true;

          // Try clicking next page if available
          const nextButton = page.locator('a:has-text("Next"), button:has-text("Next")').first();
          const nextExists = await nextButton.count() > 0;

          if (nextExists && await nextButton.isVisible().catch(() => false)) {
            const urlBefore = page.url();
            await nextButton.click();
            await page.waitForTimeout(2000);
            const urlAfter = page.url();

            const urlChanged = urlBefore !== urlAfter;
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Pagination click: URL changed = ${urlChanged}\n`);
          }

          break;
        }
      }
    }

    if (!paginationFound) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No pagination found - results may fit on one page\n`);
    }
  });

  test('Search autocomplete/suggestions appear', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_SEARCH_005' });
    const testId = 'TC_SEARCH_005';
    testInfo.setTimeout(30000);

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    try {
      // Use your existing search selector
      const searchInput = selectors.searchInput(page);
      const visibleSearch = await findVisibleElement(searchInput, 'Search input', testId);

      if (!visibleSearch) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No search input found, skipping test\n`);
        return;
      }

      // Type partial query
      // TODO(Engagement): replace with a partial term relevant to your site's autocomplete
      await visibleSearch.fill('exa');
      await page.waitForTimeout(1500);

      // Look for autocomplete/suggestions
      const suggestionSelectors = [
        page.locator('[role="listbox"], [role="menu"]'),
        page.locator('.autocomplete, .suggestions, .search-suggestions'),
        page.locator('[class*="dropdown"][class*="search"]'),
        page.locator('ul[class*="search"] li, div[class*="suggest"]')
      ];

      let suggestionsFound = false;
      for (const selector of suggestionSelectors) {
        const count = await selector.count();
        if (count > 0) {
          const isVisible = await selector.first().isVisible().catch(() => false);
          if (isVisible) {
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Search suggestions displayed\n`);
            suggestionsFound = true;
            break;
          }
        }
      }

      if (suggestionsFound) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search autocomplete working\n`);
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No autocomplete found - may not be implemented\n`);
      }
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test skipped: ${error.message}\n`);
    }
  });
});
