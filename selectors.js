/**
 * Internal helper: turn a single fallback definition into a Playwright locator.
 * A definition is either:
 *   - a plain CSS selector string -> page.locator(string)
 *   - a descriptor object with one of:
 *       { role, roleOptions? }        -> page.getByRole(role, roleOptions)
 *       { selector }                  -> page.locator(selector)
 *     plus optional modifiers:
 *       { childSelector }             -> .locator(childSelector)
 *       { hasText }                   -> .filter({ hasText })
 *       { hasNotIframe: true }        -> .filter({ hasNot: page.locator('iframe') })
 *       { first: true }               -> .first()
 */
function toLocator(page, def) {
  if (typeof def === 'string') {
    return page.locator(def);
  }

  let loc = def.role
    ? page.getByRole(def.role, def.roleOptions)
    : page.locator(def.selector);

  if (def.childSelector) {
    loc = loc.locator(def.childSelector);
  }
  if (def.hasText) {
    loc = loc.filter({ hasText: def.hasText });
  }
  if (def.hasNotIframe) {
    loc = loc.filter({ hasNot: page.locator('iframe') });
  }
  if (def.first) {
    loc = loc.first();
  }

  return loc;
}

/**
 * Internal helper: build a `.or(...)`-chained locator from an ordered array
 * of fallback definitions (see toLocator above).
 */
function buildChain(page, defs) {
  if (!defs || defs.length === 0) {
    throw new Error('buildChain: fallback array is empty - add at least one selector definition.');
  }
  return defs.map(def => toLocator(page, def)).reduce((acc, loc) => acc.or(loc));
}

// Mobile navigation selectors with comprehensive fallbacks
export const mobileToggleFallbacks = [
  'button[class*="menu"], button[aria-label*="menu" i], .mobile-toggle, #mobile-toggle, [class*="hamburger"]',
  'button[aria-expanded], button[data-toggle="menu"]',
  '.nav-toggle, .navbar-toggle, .menu-toggle',
];

export const mobileMenuFallbacks = [
  '[class*="mobile-menu"], [class*="nav-menu"][class*="open"], nav ul[class*="show"], .mobile-nav',
  '[aria-expanded="true"] + ul, [aria-expanded="true"] + div',
  '.navbar-collapse.show, .nav-menu.active',
];

// Search functionality selectors
export const searchInputFallbacks = [
  { role: 'combobox', roleOptions: { name: /search/i } },
  'input[type="search"], input[name="q"], input[placeholder*="search" i]',
  '#search-input, .search-input, [class*="search-input"]',
  '[role="searchbox"], [aria-label*="search" i]',
];

export const searchTriggerFallbacks = [
  // TODO(Engagement): '#gecko-search-button' is a site-specific element ID -
  // replace with your site's actual search-trigger ID/selector.
  '#gecko-search-button',
  'button[aria-label*="search" i], button[title*="search" i]',
  '.search-trigger, #search-trigger, [class*="search-btn"]',
  'button:has-text("Search"), [type="submit"][value*="search" i]',
];

// Logo selector with multiple fallback strategies
export const logoFallbacks = [
  { selector: '.logo img, #logo img, [class*="logo"] img', hasNotIframe: true },
  { selector: 'header img, nav img', first: true },
  { selector: 'a[href="/"] img, a[href="./"] img', first: true },
];

// Navigation selectors
export const navFallbacks = [
  { role: 'navigation', first: true },
  'header nav, .navbar, .navigation',
  { selector: 'nav, div[class*="nav"], section[class*="nav"]', first: true },
];

export const navLinksFallbacks = [
  { role: 'navigation', childSelector: 'a' },
  'nav a, header a, [class*="nav"] a',
  '.navbar a, .navigation a',
];

// Content area selectors
export const contentFallbacks = [
  { role: 'main' },
  'main, [role="main"], .content, #content',
  '.main-content, .page-content, #main',
  { role: 'heading', roleOptions: { level: 1 } },
  { selector: 'h1, h2, h3', first: true },
  { selector: 'article, section', first: true },
];

// CTA (Call to Action) button selectors with comprehensive patterns
export const ctaFallbacks = [
  { role: 'link', roleOptions: { name: /download|release|get started|latest|learn more/i } },
  { role: 'button', roleOptions: { name: /download|release|get started|latest|learn more/i } },
  'a[href*="download"], a[href*="release"], a[href*="get-started"]',
  { selector: 'a', hasText: /download.*latest.*release|get.*started|learn.*more/i },
  '.cta, #cta, [class*="cta"], [class*="download"], [class*="release"]',
  { selector: 'a[class*="btn"], button[class*="btn"]', hasText: /download|release|get started|latest/i },
  '[role="button"]:has-text("Download"), [role="button"]:has-text("Get Started")',
];

// External links selector
export const externalLinksFallbacks = [
  { selector: 'a[href^="http"]', hasText: /.+/ },
  { selector: 'a[href^="https"]', hasText: /.+/ },
  { selector: 'a[target="_blank"]', hasText: /.+/ },
];

// Footer selector
export const footerFallbacks = [
  { role: 'contentinfo', first: true },
  'footer, .footer, #footer',
  '[role="contentinfo"]',
];

// Search results selectors
export const searchResultsFallbacks = [
  '[class*="search-result"], [class*="result"]',
  '[data-testid*="search"], [data-testid*="result"]',
  '.algolia-autocomplete .aa-dropdown-menu .aa-suggestion',
  '[role="listbox"] [role="option"]',
  '.search-hits, .search-results, #search-results',
];

// Download link patterns
export const downloadLinksFallbacks = [
  'a[href$=".tar.gz"], a[href$=".zip"], a[href$=".exe"]',
  'a:has-text("Download"), a:has-text("tar.gz"), a:has-text("zip")',
  '[class*="download"], #download',
  'button:has-text("Download")',
];

// Form elements
export const formsInputFallbacks = ['input:not([type="hidden"])'];
export const formsButtonFallbacks = ['button, input[type="submit"], input[type="button"]'];
export const formsSelectFallbacks = ['select'];
export const formsTextareaFallbacks = ['textarea'];

// Common UI elements
export const modalsFallbacks = [
  '[role="dialog"], .modal, .popup',
  '[aria-modal="true"]',
  '.overlay, .lightbox',
];

export const alertsFallbacks = [
  '[role="alert"], .alert, .notification',
  '.error, .warning, .success, .info',
  '[class*="toast"], [class*="snackbar"]',
];

// Loading indicators
export const loadingFallbacks = [
  '.loading, .spinner, [class*="load"]',
  '[aria-busy="true"]',
  '.progress, [role="progressbar"]',
];

export const selectors = {
  // Mobile navigation selectors with comprehensive fallbacks
  mobileToggle: page => buildChain(page, mobileToggleFallbacks),

  mobileMenu: page => buildChain(page, mobileMenuFallbacks),

  // Search functionality selectors
  searchInput: page => buildChain(page, searchInputFallbacks),

  searchTrigger: page => buildChain(page, searchTriggerFallbacks),

  // Logo selector with multiple fallback strategies
  logo: page => buildChain(page, logoFallbacks),

  // Navigation selectors
  nav: page => buildChain(page, navFallbacks),

  navLinks: page => buildChain(page, navLinksFallbacks),

  // Content area selectors
  content: page => buildChain(page, contentFallbacks),

  // CTA (Call to Action) button selectors with comprehensive patterns
  cta: page => buildChain(page, ctaFallbacks),

  // External links selector
  externalLinks: page => buildChain(page, externalLinksFallbacks),

  // Footer selector
  footer: page => buildChain(page, footerFallbacks),

  // Search results selectors
  searchResults: page => buildChain(page, searchResultsFallbacks),

  // Download link patterns
  downloadLinks: page => buildChain(page, downloadLinksFallbacks),

  // Form elements
  forms: {
    input: page => buildChain(page, formsInputFallbacks),
    button: page => buildChain(page, formsButtonFallbacks),
    select: page => buildChain(page, formsSelectFallbacks),
    textarea: page => buildChain(page, formsTextareaFallbacks),
  },

  // Common UI elements
  modals: page => buildChain(page, modalsFallbacks),

  alerts: page => buildChain(page, alertsFallbacks),

  // Loading indicators
  loading: page => buildChain(page, loadingFallbacks),
};
