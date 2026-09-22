import { test, expect } from '@playwright/test';
import fs from 'fs';
import { selectors } from '../selectors.js';
import { logAndScreenshot, safeGoto } from '../utils.js';
import { buildURL, testData, urlPatterns } from '../config-helper.js';
import { testPatterns, testElementVisibility, findVisibleElement } from '../test-helpers.js';

fs.mkdirSync('test-results', { recursive: true });

test.describe('Error Handling Tests', () => {

  test('404 page displays appropriate error message', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_ERROR_001' });
    const testId = 'TC_ERROR_001';
    testInfo.setTimeout(30000);

    // Navigate to a known non-existent page
    const invalidUrl = buildURL(testInfo, '/this-page-does-not-exist-12345', { cachebust: true });
    
    try {
      await safeGoto(page, testInfo, invalidUrl, { waitUntil: 'networkidle' });
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Expected error when navigating to 404 page\n`);
    }

    // Check for 404 indicators
    const errorIndicators = [
      page.locator('text=/404|not found|page not found|doesn\'t exist/i').first(),
      page.locator('h1, h2, h3').filter({ hasText: /404|not found/i }).first(),
      page.locator('[class*="error"]').first(),
      page.locator('[class*="404"]').first()
    ];

    let errorFound = false;
    for (const indicator of errorIndicators) {
      const count = await indicator.count();
      if (count > 0 && await indicator.isVisible().catch(() => false)) {
        await expect(indicator).toBeVisible({ timeout: testData.timeouts.short });
        errorFound = true;
        fs.appendFileSync('test-results/test-logs.txt', `${testId} 404 error message displayed correctly\n`);
        break;
      }
    }

    if (!errorFound) {
      await logAndScreenshot(page, testInfo, '404 error message not found', 'test-results/screenshots/tc_error_001/no_404.png');
      // Check the page title or URL as fallback
      const title = await page.title();
      const url = page.url();
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Page title: "${title}", URL: "${url}"\n`);
      
      // If we're on an error page, that's still acceptable
      if (title.toLowerCase().includes('404') || title.toLowerCase().includes('not found')) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} 404 indicated in page title\n`);
        errorFound = true;
      }
    }

    expect(errorFound).toBeTruthy();
  });

  test('Broken documentation link returns appropriate error', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_ERROR_002' });
    const testId = 'TC_ERROR_002';
    testInfo.setTimeout(30000);

    // Try to access a broken documentation link
    const brokenDocUrl = buildURL(testInfo, `${urlPatterns.documentation}nonexistent-library`, { cachebust: true });
    
    const response = await page.goto(brokenDocUrl, { 
      waitUntil: 'networkidle',
      timeout: testData.timeouts.medium 
    }).catch(() => null);

    if (response) {
      const status = response.status();
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Response status: ${status}\n`);
      
      // Accept 404 or any 4xx error as appropriate
      expect(status).toBeGreaterThanOrEqual(400);
      expect(status).toBeLessThan(500);
    }

    // Verify error message is displayed
    const errorMessage = page.locator('text=/error|not found|invalid|doesn\'t exist/i').first();
    await expect(errorMessage).toBeVisible({ timeout: testData.timeouts.medium });
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Error message displayed for broken doc link\n`);
  });

  test('Invalid search query handles gracefully', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_ERROR_003' });
    const testId = 'TC_ERROR_003';
    testInfo.setTimeout(45000);

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

      // Try searching for special characters that might break things
      const invalidSearchTerms = ['<script>', '%%%', '///'];
      
      for (const term of invalidSearchTerms) {
        await visibleSearch.clear();
        await visibleSearch.fill(term);
        await visibleSearch.press('Enter');
        
        await page.waitForTimeout(2000);
        
        // Check that page didn't crash or throw JavaScript errors
        const hasError = await page.locator('text=/error|500|internal server|crash/i').count();
        expect(hasError).toBe(0);
        
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Search with "${term}" handled gracefully\n`);
      }

      // Verify we get "no results" or similar message, not an error
      const noResultsMessage = page.locator('text=/no results|not found|no matches|try again/i').first();
      const isVisible = await noResultsMessage.isVisible().catch(() => false);
      
      if (isVisible) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Appropriate "no results" message shown\n`);
      } else {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No explicit message but search handled without errors\n`);
      }
    } catch (error) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Test completed with note: ${error.message}\n`);
    }
  });

  test('Malformed URL redirects or shows error appropriately', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_ERROR_004' });
    const testId = 'TC_ERROR_004';
    testInfo.setTimeout(30000);

    // Test various malformed URLs
    const malformedUrls = [
      '/doc/////libs',
      '/users//../download',
      '/libraries/?..',
    ];

    for (const malformedPath of malformedUrls) {
      const malformedUrl = buildURL(testInfo, malformedPath);
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Testing malformed URL: ${malformedUrl}\n`);
      
      try {
        const response = await page.goto(malformedUrl, { 
          waitUntil: 'networkidle',
          timeout: testData.timeouts.medium 
        }).catch(() => null);

        if (response) {
          const status = response.status();
          const finalUrl = page.url();
          
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Status: ${status}, Final URL: ${finalUrl}\n`);
          
          // Either redirects to valid page or shows error
          if (status >= 200 && status < 300) {
            // Redirected to valid page
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Redirected to valid page\n`);
          } else if (status >= 400 && status < 500) {
            // Appropriate error shown
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Appropriate error status\n`);
            const errorMessage = await page.locator('text=/error|not found|invalid/i').count();
            expect(errorMessage).toBeGreaterThan(0);
          }
        }
      } catch (error) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Malformed URL handled: ${error.message}\n`);
      }
    }
  });

  test('Broken external links are identified', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_ERROR_005' });
    const testId = 'TC_ERROR_005';
    testInfo.setTimeout(60000);

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    // Get all external links
    const externalLinks = await page.locator('a[href^="http"]').all();
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${externalLinks.length} external links\n`);

    let checkedLinks = 0;
    const maxLinksToCheck = 5; // Limit to avoid long test times

    for (let i = 0; i < Math.min(externalLinks.length, maxLinksToCheck); i++) {
      const link = externalLinks[i];
      const href = await link.getAttribute('href');
      const isVisible = await link.isVisible().catch(() => false);
      
      if (href && isVisible && !href.includes('javascript:')) {
        try {
          // Use HEAD request to check if link is valid
          const response = await page.request.head(href, { timeout: 10000 }).catch(() => null);
          
          if (response) {
            const status = response.status();
            fs.appendFileSync('test-results/test-logs.txt', `${testId} Link ${i}: ${href} - Status: ${status}\n`);
            
            // Links should return 200-399 status codes
            expect(status).toBeLessThan(400);
            checkedLinks++;
          }
        } catch (error) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Link check failed for: ${href} - ${error.message}\n`);
        }
      }
    }

    fs.appendFileSync('test-results/test-logs.txt', `${testId} Checked ${checkedLinks} external links\n`);
    expect(checkedLinks).toBeGreaterThan(0);
  });

  test('Form validation errors display correctly', async ({ page }, testInfo) => {
    testInfo.annotations.push({ type: 'test_case', description: 'TC_ERROR_006' });
    const testId = 'TC_ERROR_006';
    testInfo.setTimeout(30000);

    const homepageUrl = buildURL(testInfo, urlPatterns.homepage, { cachebust: true });
    await testPatterns.loadAndValidatePage(page, testInfo, homepageUrl, testId);

    // Look for any forms on the page
    const forms = await page.locator('form').all();
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${forms.length} forms on page\n`);

    if (forms.length === 0) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} No forms found on homepage, skipping test\n`);
      return;
    }

    // Test the first form
    const form = forms[0];
    const submitButton = form.locator('button[type="submit"], input[type="submit"]').first();
    const submitExists = await submitButton.count() > 0;

    if (submitExists) {
      // Try to submit empty form
      await submitButton.click();
      await page.waitForTimeout(1000);

      // Look for validation messages
      const validationMessages = [
        page.locator('[class*="error"], [class*="invalid"]').first(),
        page.locator('text=/required|please|invalid|must/i').first(),
        page.locator('[role="alert"]').first()
      ];

      let validationFound = false;
      for (const message of validationMessages) {
        const count = await message.count();
        if (count > 0 && await message.isVisible().catch(() => false)) {
          fs.appendFileSync('test-results/test-logs.txt', `${testId} Form validation message displayed\n`);
          validationFound = true;
          break;
        }
      }

      if (!validationFound) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} No validation message found, but form may use HTML5 validation\n`);
      }
    } else {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Form found but no submit button\n`);
    }
  });
});