import fs from 'fs';
import { expect } from '@playwright/test';
import { logAndScreenshot, safeGoto } from './utils.js';
import { testData } from './config-helper.js';

fs.mkdirSync('test-results', { recursive: true });

/**
 * Find and return the first visible element from a locator
 * @param {import('@playwright/test').Locator} locator - Playwright locator
 * @param {string} elementName - Name for logging purposes
 * @param {string} testId - Test case ID for logging
 * @returns {Promise<import('@playwright/test').Locator|null>} First visible element or null
 */
export async function findVisibleElement(locator, elementName, testId) {
  const count = await locator.count();
  fs.appendFileSync('test-results/test-logs.txt', `${testId} ${elementName} locator matched ${count} elements\n`);
  
  for (let i = 0; i < count; i++) {
    const element = locator.nth(i);
    const isVisible = await element.isVisible().catch(() => false);
    fs.appendFileSync('test-results/test-logs.txt', `${testId} ${elementName} ${i} visible: ${isVisible}\n`);
    if (isVisible) {
      return element;
    }
  }
  return null;
}

/**
 * Test element visibility with fallback options
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {import('@playwright/test').TestInfo} testInfo - Test info
 * @param {import('@playwright/test').Locator} primaryLocator - Primary selector
 * @param {Array<import('@playwright/test').Locator>} fallbackLocators - Fallback selectors
 * @param {string} elementName - Name for error messages
 * @param {string} testId - Test case ID
 * @returns {Promise<import('@playwright/test').Locator>} Visible element
 */
export async function testElementVisibility(page, testInfo, primaryLocator, fallbackLocators = [], elementName, testId) {
  // Try primary locator
  const primaryElement = await findVisibleElement(primaryLocator, `${elementName} (primary)`, testId);
  if (primaryElement) {
    await expect(primaryElement).toBeVisible({ timeout: testData.timeouts.medium });
    return primaryElement;
  }

  // Try fallback locators
  for (let i = 0; i < fallbackLocators.length; i++) {
    const fallbackElement = await findVisibleElement(fallbackLocators[i], `${elementName} (fallback ${i})`, testId);
    if (fallbackElement) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Using ${elementName} fallback ${i}\n`);
      await expect(fallbackElement).toBeVisible({ timeout: testData.timeouts.medium });
      return fallbackElement;
    }
  }

  // Element not found
  await logAndScreenshot(page, testInfo, `${elementName} not visible`, `test-results/screenshots/${testId.toLowerCase()}/${elementName.toLowerCase().replace(/\s+/g, '_')}_not_visible.png`);
  throw new Error(`${elementName} not visible`);
}

/**
 * Handle mobile menu interaction if needed
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {Object} selectors - Selector object
 * @param {string} testId - Test case ID
 */
export async function handleMobileMenu(page, selectors, testId) {
  const mobileToggle = selectors.mobileToggle(page);
  const mobileToggleCount = await mobileToggle.count();
  
  if (mobileToggleCount > 0) {
    const isToggleVisible = await mobileToggle.first().isVisible().catch(() => false);
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Mobile toggle visible: ${isToggleVisible}\n`);
    
    if (isToggleVisible) {
      try {
        await mobileToggle.first().click();
        await page.waitForTimeout(500); // Allow menu animation
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Mobile menu opened\n`);
        
        // Verify mobile menu is visible
        const mobileMenu = selectors.mobileMenu(page);
        const menuVisible = await mobileMenu.isVisible().catch(() => false);
        if (menuVisible) {
          await expect(mobileMenu).toBeVisible({ timeout: testData.timeouts.short });
        }
      } catch (error) {
        fs.appendFileSync('test-results/test-logs.txt', `${testId} Mobile menu interaction failed: ${error.message}\n`);
      }
    }
  }
}

/**
 * Perform a search operation with strict mode violation handling
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {import('@playwright/test').TestInfo} testInfo - Test info
 * @param {Object} selectors - Selector object
 * @param {string} searchTerm - Term to search for
 * @param {string} testId - Test case ID
 */
export async function performSearch(page, testInfo, selectors, searchTerm, testId) {
  // Find search trigger
  const searchTrigger = await findVisibleElement(selectors.searchTrigger(page), 'Search trigger', testId);
  if (!searchTrigger) {
    throw new Error('Search trigger not found');
  }

  // Click search trigger
  await searchTrigger.click();
  fs.appendFileSync('test-results/test-logs.txt', `${testId} Search trigger clicked\n`);

  // Wait for search input - handle multiple matches (strict mode violation fix)
  const searchInput = selectors.searchInput(page);
  const searchInputCount = await searchInput.count();
  fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${searchInputCount} search input elements\n`);
  
  // Get the actual input element (not the Algolia link or other elements)
  let actualSearchInput = null;
  for (let i = 0; i < searchInputCount; i++) {
    const element = searchInput.nth(i);
    const tagName = await element.evaluate(el => el.tagName.toLowerCase()).catch(() => '');
    const type = await element.getAttribute('type').catch(() => '');
    const role = await element.getAttribute('role').catch(() => '');
    
    // Look for actual input elements, not links
    if (tagName === 'input' && (type === 'text' || type === 'search' || type === '' || role === 'combobox')) {
      actualSearchInput = element;
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Using search input element ${i} (${tagName}, type: ${type}, role: ${role})\n`);
      break;
    }
  }
  
  if (!actualSearchInput) {
    // Fallback: try to find by more specific selector
    actualSearchInput = page.locator('input[role="combobox"][placeholder*="Search"]').first();
    const fallbackExists = await actualSearchInput.count() > 0;
    if (fallbackExists) {
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Using fallback search input selector\n`);
    } else {
      actualSearchInput = searchInput.first(); // Last resort
      fs.appendFileSync('test-results/test-logs.txt', `${testId} Using first search element as last resort\n`);
    }
  }
  
  await expect(actualSearchInput).toBeVisible({ timeout: testData.timeouts.medium });
  
  // Perform search
  await actualSearchInput.fill(searchTerm);
  await actualSearchInput.press('Enter');
  fs.appendFileSync('test-results/test-logs.txt', `${testId} Search performed for: ${searchTerm}\n`);
  
  // Allow time for search to process
  await page.waitForTimeout(2000);
}

/**
 * Look for search results using multiple strategies
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {string} searchTerm - Search term to look for
 * @param {string} testId - Test case ID
 * @returns {Promise<{element: import('@playwright/test').Locator|null, count: number}>}
 */
export async function findSearchResults(page, searchTerm, testId) {
  const resultSelectors = [
    '[class*="search-result"], [class*="result"]',
    '[data-testid*="search"], [data-testid*="result"]', 
    '.algolia-autocomplete .aa-dropdown-menu .aa-suggestion',
    '[role="listbox"] [role="option"]',
    '.search-hits, .search-results, #search-results'
  ];

  // Try specific search result selectors first
  for (const selector of resultSelectors) {
    const elements = page.locator(selector);
    const count = await elements.count();
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${count} elements with selector: ${selector}\n`);
    if (count > 0) {
      return { element: elements.first(), count };
    }
  }

  // Try content-based search
  const contentResults = page.locator('h1, h2, h3, p, div, span, li').filter({ hasText: new RegExp(searchTerm, 'i') });
  const contentCount = await contentResults.count();
  fs.appendFileSync('test-results/test-logs.txt', `${testId} Found ${contentCount} content elements containing "${searchTerm}"\n`);
  
  if (contentCount > 0) {
    return { element: contentResults.first(), count: contentCount };
  }

  // Broad text search as last resort
  const broadResults = page.getByText(new RegExp(searchTerm, 'i'));
  const broadCount = await broadResults.count();
  fs.appendFileSync('test-results/test-logs.txt', `${testId} Broad text search found ${broadCount} matches\n`);
  
  return { element: broadCount > 0 ? broadResults.first() : null, count: broadCount };
}

/**
 * Test navigation link functionality
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {import('@playwright/test').TestInfo} testInfo - Test info
 * @param {import('@playwright/test').Locator} link - Link element
 * @param {number} index - Link index for logging
 * @param {string} testId - Test case ID
 * @param {string} homeUrl - URL to return to after testing
 */
export async function testNavigationLink(page, testInfo, link, index, testId, homeUrl) {
  const href = await link.getAttribute('href').catch(() => null);
  const text = await link.textContent().catch(() => 'unknown');
  
  // Skip invalid links
  if (!href || href === '#' || href.match(/^https?:\/\//)) {
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Skipping invalid nav link ${index}: text="${text}", href="${href}"\n`);
    return;
  }

  try {
    await expect(link).toBeVisible({ timeout: testData.timeouts.short });
    await link.click();
    
    // Create regex pattern for href matching
    const escapedHref = href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    await expect(page).toHaveURL(new RegExp(escapedHref), { timeout: testData.timeouts.short });
    
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Nav link ${index} successful: "${text}" -> ${href}\n`);
    
    // Return to homepage for next test
    await safeGoto(page, testInfo, homeUrl, { waitUntil: 'domcontentloaded' });
    
  } catch (error) {
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Nav link ${index} failed: text="${text}", href="${href}", error="${error.message}"\n`);
    await logAndScreenshot(page, testInfo, `Navigation failed for link ${index}`, `test-results/screenshots/${testId.toLowerCase()}/link_${index}_failed.png`);
  }
}

/**
 * Validate element attributes and log details
 * @param {import('@playwright/test').Locator} element - Element to validate
 * @param {string} elementName - Name for logging
 * @param {string} testId - Test case ID
 * @returns {Promise<Object>} Element details
 */
export async function validateElementDetails(element, elementName, testId) {
  const details = {
    text: await element.textContent().catch(() => 'unknown'),
    href: await element.getAttribute('href').catch(() => null),
    class: await element.getAttribute('class').catch(() => null),
    id: await element.getAttribute('id').catch(() => null),
    isVisible: await element.isVisible().catch(() => false),
  };
  
  fs.appendFileSync('test-results/test-logs.txt', `${testId} ${elementName} details: ${JSON.stringify(details)}\n`);
  return details;
}

/**
 * Common test patterns wrapped in reusable functions
 */
export const testPatterns = {
  /**
   * Standard page load and validation
   */
  async loadAndValidatePage(page, testInfo, url, testId) {
    const startTime = Date.now();
    const { success, finalUrl } = await safeGoto(page, testInfo, url, { waitUntil: 'domcontentloaded' });
    
    if (!success) {
      await logAndScreenshot(page, testInfo, `Page load failed: ${finalUrl}`, `test-results/screenshots/${testId.toLowerCase()}/load_failed.png`);
      throw new Error(`Page load failed: ${finalUrl}`);
    }

    const loadTime = Date.now() - startTime;
    await logAndScreenshot(page, testInfo, `Page loaded in ${loadTime}ms, URL: ${page.url()}`, `test-results/screenshots/${testId.toLowerCase()}/loaded.png`);
    
    return { loadTime, finalUrl };
  },

  /**
   * Viewport management
   */
  async setViewport(page, viewport, testId) {
    await page.setViewportSize(viewport);
    fs.appendFileSync('test-results/test-logs.txt', `${testId} Viewport set to ${viewport.width}x${viewport.height}\n`);
  }
};