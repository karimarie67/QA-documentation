import { test } from '@playwright/test';

/**
 * Get the base URL from the current project configuration
 * @param {import('@playwright/test').TestInfo} testInfo - Test info object
 * @returns {string} The base URL for the current project
 */
export function getBaseURL(testInfo) {
  const config = testInfo.project.use;
  // TODO(Engagement): replace this placeholder with the Engagement's actual base URL.
  return config.baseURL || 'https://www.example.com';
}

/**
 * Build a URL relative to the current project's base URL
 * @param {import('@playwright/test').TestInfo} testInfo - Test info object  
 * @param {string} path - The path to append to base URL
 * @param {Object} options - URL options
 * @param {boolean} options.cachebust - Add cachebust parameter
 * @param {Object} options.params - Additional query parameters
 * @returns {string} Complete URL
 */
export function buildURL(testInfo, path = '/', options = {}) {
  const baseURL = getBaseURL(testInfo);
  const url = new URL(path, baseURL);
  
  if (options.cachebust) {
    url.searchParams.set('cachebust', Date.now().toString());
  }
  
  if (options.params) {
    Object.entries(options.params).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }
  
  return url.toString();
}

/**
 * Common URL patterns used in tests
 */
export const urlPatterns = {
  homepage: '/',
  libraries: '/libraries/',
  releases: '/releases/',
  // TODO(Engagement): placeholder - align with docLibsVersion's path scheme below.
  documentation: '/docs/',
  community: '/community/',
  search: '/search/',
  // Version-specific URLs
  // TODO(Engagement): this path scheme and default version are placeholders -
  // update them to match the Engagement's actual versioned-docs URL structure.
  docLibsVersion: (version = '1_0_0') => `/docs/${version}/`,
  releaseNotes: (version = '1_0_0') => `/docs/${version}/release_notes/`,
};

/**
 * Expected URL patterns for navigation validation
 */
export const expectedUrlPatterns = {
  afterCTAClick: /libraries|releases|docs|learn|download/i,
  afterSearch: /search|results|q=/i,
  afterLogoClick: /\/?$/,
  // TODO(Engagement): replace with the Engagement's actual GitHub org/repo pattern.
  githubBoost: /github\.com\/<your-org>/,
  // TODO(Engagement): replace with the Engagement's actual download host/site pattern.
  downloadSite: /downloads?\.example\.com|download|release/i,
  // TODO(Engagement): replace with the Engagement's actual community-link pattern.
  communityLinks: /github.com.*issues|discourse|community\.example\.com/i,
};

/**
 * Test data constants
 */
export const testData = {
  searchTerms: {
    // TODO(Engagement): replace with search terms known to return results on the target site.
    working: 'example-search-term', // Known to work
    alternative: 'example-alternative-term',
  },
  downloadFiles: {
    // TODO(Engagement): replace with the Engagement's actual downloadable filename patterns.
    tarGz: /example[-_]?\S*\.tar\.gz$/,
    zip: /example[-_]?\S*\.zip$/,
    supported: /\.(zip|tar\.gz|tar\.bz2|7z|exe)$/,
  },
  timeouts: {
    short: 5000,
    medium: 15000, 
    long: 30000,
    download: 60000,
  },
  viewport: {
    desktop: { width: 1280, height: 720 },
    mobile: { width: 800, height: 600 },
  }
};
