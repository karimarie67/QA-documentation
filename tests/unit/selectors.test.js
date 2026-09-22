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
  await t.test('has exactly 3 entries (down from 6 after removing Boost-specific ones)', () => {
    assert.equal(logoFallbacks.length, 3);
  });

  await t.test('none of its 3 entries reference Boost_Symbol_Transparent or any boost string', () => {
    for (const entry of logoFallbacks) {
      const str = entryToString(entry);
      assert.doesNotMatch(str, /Boost_Symbol_Transparent/i);
      assert.doesNotMatch(str, /boost/i);
    }
  });
});

test('downloadLinksFallbacks', async t => {
  await t.test('has exactly 4 entries (down from 6)', () => {
    assert.equal(downloadLinksFallbacks.length, 4);
  });

  await t.test('none of its entries reference archives.boost.io or boost_1_85_0/boost-1.85.0', () => {
    for (const entry of downloadLinksFallbacks) {
      const str = entryToString(entry);
      assert.doesNotMatch(str, /archives\.boost\.io/i);
      assert.doesNotMatch(str, /boost[_-]1[._]85[._]0/i);
    }
  });
});

test('selectors function API', async t => {
  await t.test('selectors.logo is still a function', () => {
    assert.equal(typeof selectors.logo, 'function');
  });

  await t.test('selectors.downloadLinks is still a function', () => {
    assert.equal(typeof selectors.downloadLinks, 'function');
  });
});
