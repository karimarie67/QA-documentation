import test from 'node:test';
import assert from 'node:assert/strict';
import {
  mobileToggleFallbacks,
  mobileMenuFallbacks,
  searchInputFallbacks,
  searchTriggerFallbacks,
  logoFallbacks,
  navFallbacks,
  navLinksFallbacks,
  contentFallbacks,
  ctaFallbacks,
  externalLinksFallbacks,
  footerFallbacks,
  searchResultsFallbacks,
  downloadLinksFallbacks,
  formsInputFallbacks,
  formsButtonFallbacks,
  formsSelectFallbacks,
  formsTextareaFallbacks,
  modalsFallbacks,
  alertsFallbacks,
  loadingFallbacks,
  selectors,
} from '../../selectors.js';

// All 20 plain-array fallback exports from selectors.js.
const allFallbackExports = {
  mobileToggleFallbacks,
  mobileMenuFallbacks,
  searchInputFallbacks,
  searchTriggerFallbacks,
  logoFallbacks,
  navFallbacks,
  navLinksFallbacks,
  contentFallbacks,
  ctaFallbacks,
  externalLinksFallbacks,
  footerFallbacks,
  searchResultsFallbacks,
  downloadLinksFallbacks,
  formsInputFallbacks,
  formsButtonFallbacks,
  formsSelectFallbacks,
  formsTextareaFallbacks,
  modalsFallbacks,
  alertsFallbacks,
  loadingFallbacks,
};

// Flatten a fallback entry (either a plain CSS selector string, or a
// descriptor object per selectors.js's toLocator/buildChain shape:
// { role, roleOptions?, selector?, childSelector?, hasText?, hasNotIframe?, first? })
// to a single string we can substring-search for "boost".
function entryToString(entry) {
  if (typeof entry === 'string') {
    return entry;
  }
  return JSON.stringify(entry, (key, value) =>
    value instanceof RegExp ? value.toString() : value
  );
}

function assertNoBoostReferences(name, fallbackArray) {
  for (const entry of fallbackArray) {
    const str = entryToString(entry);
    assert.doesNotMatch(
      str,
      /boost/i,
      `${name} entry should not reference "boost" (found in: ${str})`
    );
  }
}

test('every *Fallbacks array export', async t => {
  for (const [name, arr] of Object.entries(allFallbackExports)) {
    await t.test(`${name} is a non-empty array`, () => {
      assert.ok(Array.isArray(arr), `${name} should be an array`);
      assert.ok(arr.length > 0, `${name} should have length > 0`);
    });

    await t.test(`${name} contains no "boost" references`, () => {
      assertNoBoostReferences(name, arr);
    });
  }
});

test('logoFallbacks', async t => {
  await t.test('contains exactly the expected generic fallback chain, in order', () => {
    assert.deepEqual(logoFallbacks, [
      { selector: '.logo img, #logo img, [class*="logo"] img', hasNotIframe: true },
      { selector: 'header img, nav img', first: true },
      { selector: 'a[href="/"] img, a[href="./"] img', first: true },
    ]);
  });
});

test('downloadLinksFallbacks', async t => {
  await t.test('contains exactly the expected generic fallback chain, in order', () => {
    assert.deepEqual(downloadLinksFallbacks, [
      'a[href$=".tar.gz"], a[href$=".zip"], a[href$=".exe"]',
      'a:has-text("Download"), a:has-text("tar.gz"), a:has-text("zip")',
      '[class*="download"], #download',
      'button:has-text("Download")',
    ]);
  });
});

test('selectors function API', async t => {
  // Every selectors.X entry the additive refactor is supposed to leave
  // untouched, including the nested selectors.forms.* group - a dropped or
  // renamed entry here would otherwise pass test:unit and test:template-check
  // silently, since neither exercises call sites directly.
  const topLevelNames = [
    'mobileToggle', 'mobileMenu', 'searchInput', 'searchTrigger', 'logo',
    'nav', 'navLinks', 'content', 'cta', 'externalLinks', 'footer',
    'searchResults', 'downloadLinks', 'modals', 'alerts', 'loading',
  ];
  for (const name of topLevelNames) {
    await t.test(`selectors.${name} is a function`, () => {
      assert.equal(typeof selectors[name], 'function');
    });
  }

  await t.test('selectors.forms is an object', () => {
    assert.equal(typeof selectors.forms, 'object');
  });

  for (const name of ['input', 'button', 'select', 'textarea']) {
    await t.test(`selectors.forms.${name} is a function`, () => {
      assert.equal(typeof selectors.forms[name], 'function');
    });
  }
});
