import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getBaseURL,
  buildURL,
  urlPatterns,
  expectedUrlPatterns,
  testData,
} from '../../config-helper.js';

// Minimal fake TestInfo shape - these functions only ever read
// testInfo.project.use.baseURL, so no real Playwright page/browser is needed.
function fakeTestInfo(baseURL) {
  return { project: { use: { baseURL } } };
}

test('getBaseURL', async t => {
  await t.test('returns testInfo.project.use.baseURL when set', () => {
    const info = fakeTestInfo('https://staging.example.com');
    assert.equal(getBaseURL(info), 'https://staging.example.com');
  });

  await t.test('falls back to placeholder default when baseURL is undefined', () => {
    const info = fakeTestInfo(undefined);
    assert.equal(getBaseURL(info), 'https://www.example.com');
  });

  await t.test('falls back to placeholder default when baseURL is falsy (empty string)', () => {
    const info = fakeTestInfo('');
    assert.equal(getBaseURL(info), 'https://www.example.com');
  });
});

test('buildURL', async t => {
  await t.test('constructs a basic URL by joining baseURL and path', () => {
    const info = fakeTestInfo('https://www.example.com');
    const url = buildURL(info, '/libraries/');
    assert.equal(url, 'https://www.example.com/libraries/');
  });

  await t.test('defaults path to "/" when omitted', () => {
    const info = fakeTestInfo('https://www.example.com');
    const url = buildURL(info);
    assert.equal(url, 'https://www.example.com/');
  });

  await t.test('cachebust option adds a cachebust query param', () => {
    const info = fakeTestInfo('https://www.example.com');
    const url = new URL(buildURL(info, '/releases/', { cachebust: true }));
    assert.ok(url.searchParams.has('cachebust'));
    // Should be a numeric-looking timestamp string.
    assert.match(url.searchParams.get('cachebust'), /^\d+$/);
  });

  await t.test('params option adds custom query parameters', () => {
    const info = fakeTestInfo('https://www.example.com');
    const url = new URL(
      buildURL(info, '/search/', { params: { q: 'widgets', page: '2' } })
    );
    assert.equal(url.searchParams.get('q'), 'widgets');
    assert.equal(url.searchParams.get('page'), '2');
  });

  await t.test('cachebust and params can be combined', () => {
    const info = fakeTestInfo('https://www.example.com');
    const url = new URL(
      buildURL(info, '/search/', { cachebust: true, params: { q: 'widgets' } })
    );
    assert.ok(url.searchParams.has('cachebust'));
    assert.equal(url.searchParams.get('q'), 'widgets');
  });
});

test('urlPatterns', async t => {
  const expectedKeys = [
    'homepage',
    'libraries',
    'releases',
    'documentation',
    'community',
    'search',
    'docLibsVersion',
    'releaseNotes',
  ];

  await t.test('is an object with exactly the expected keys', () => {
    assert.equal(typeof urlPatterns, 'object');
    assert.deepEqual(Object.keys(urlPatterns).sort(), [...expectedKeys].sort());
  });

  await t.test('docLibsVersion is a function returning a string containing the version arg', () => {
    assert.equal(typeof urlPatterns.docLibsVersion, 'function');
    const result = urlPatterns.docLibsVersion('2_3_4');
    assert.equal(typeof result, 'string');
    assert.ok(result.includes('2_3_4'));
  });

  await t.test('releaseNotes is a function returning a string containing the version arg', () => {
    assert.equal(typeof urlPatterns.releaseNotes, 'function');
    const result = urlPatterns.releaseNotes('9_9_9');
    assert.equal(typeof result, 'string');
    assert.ok(result.includes('9_9_9'));
  });
});

test('expectedUrlPatterns', async t => {
  const expectedKeys = [
    'afterCTAClick',
    'afterSearch',
    'afterLogoClick',
    'githubBoost',
    'downloadSite',
    'communityLinks',
  ];

  await t.test('is an object with exactly the expected keys', () => {
    assert.equal(typeof expectedUrlPatterns, 'object');
    assert.deepEqual(Object.keys(expectedUrlPatterns).sort(), [...expectedKeys].sort());
  });

  await t.test('every value is a RegExp', () => {
    for (const key of expectedKeys) {
      assert.ok(
        expectedUrlPatterns[key] instanceof RegExp,
        `expected expectedUrlPatterns.${key} to be a RegExp`
      );
    }
  });

  await t.test('afterCTAClick matches a post-CTA-click URL and rejects an unrelated one', () => {
    assert.match('https://www.example.com/libraries/', expectedUrlPatterns.afterCTAClick);
    assert.doesNotMatch('https://www.example.com/about/', expectedUrlPatterns.afterCTAClick);
  });

  await t.test('afterSearch matches a search results URL and rejects an unrelated one', () => {
    assert.match('https://www.example.com/search/?q=widgets', expectedUrlPatterns.afterSearch);
    assert.doesNotMatch('https://www.example.com/about/', expectedUrlPatterns.afterSearch);
  });

  await t.test('afterLogoClick matches the homepage root', () => {
    assert.match('https://www.example.com/', expectedUrlPatterns.afterLogoClick);
  });

  await t.test('githubBoost matches the placeholder github org pattern and rejects an unrelated URL', () => {
    assert.match('https://github.com/<your-org>/example-repo', expectedUrlPatterns.githubBoost);
    assert.doesNotMatch('https://gitlab.com/other-org/example-repo', expectedUrlPatterns.githubBoost);
  });

  await t.test('downloadSite matches a download URL and rejects an unrelated one', () => {
    assert.match('https://downloads.example.com/latest', expectedUrlPatterns.downloadSite);
    assert.doesNotMatch('https://www.example.com/about/', expectedUrlPatterns.downloadSite);
  });

  await t.test('communityLinks matches a github issues URL and rejects an unrelated one', () => {
    assert.match('https://github.com/example-org/example-repo/issues', expectedUrlPatterns.communityLinks);
    assert.doesNotMatch('https://www.example.com/about/', expectedUrlPatterns.communityLinks);
  });
});

test('testData', async t => {
  await t.test('searchTerms.working and .alternative are non-empty strings', () => {
    assert.equal(typeof testData.searchTerms.working, 'string');
    assert.ok(testData.searchTerms.working.length > 0);
    assert.equal(typeof testData.searchTerms.alternative, 'string');
    assert.ok(testData.searchTerms.alternative.length > 0);
  });

  await t.test('downloadFiles.tarGz/.zip/.supported are RegExps', () => {
    assert.ok(testData.downloadFiles.tarGz instanceof RegExp);
    assert.ok(testData.downloadFiles.zip instanceof RegExp);
    assert.ok(testData.downloadFiles.supported instanceof RegExp);
  });

  await t.test('timeouts.short/medium/long/download are numbers', () => {
    assert.equal(typeof testData.timeouts.short, 'number');
    assert.equal(typeof testData.timeouts.medium, 'number');
    assert.equal(typeof testData.timeouts.long, 'number');
    assert.equal(typeof testData.timeouts.download, 'number');
  });

  await t.test('viewport.desktop/.mobile are {width, height} objects', () => {
    for (const key of ['desktop', 'mobile']) {
      assert.equal(typeof testData.viewport[key].width, 'number');
      assert.equal(typeof testData.viewport[key].height, 'number');
    }
  });
});
