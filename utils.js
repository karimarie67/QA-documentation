import fs from 'fs';
import nodePath from 'path';

function sanitizeForPath(str) {
  return String(str).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

export async function logAndScreenshot(page, testInfo, message, path, logFile = 'test-results/test-logs.txt') {
  fs.mkdirSync(nodePath.dirname(logFile), { recursive: true });
  fs.appendFileSync(logFile, `TC_${testInfo.title}: ${message}\n`);
  if (!page.isClosed()) {
    try {
      fs.mkdirSync(nodePath.dirname(path), { recursive: true });
      await page.screenshot({ path, fullPage: true, timeout: 3000 });
      fs.appendFileSync(logFile, `Screenshot saved: ${path}\n`);
    } catch (err) {
      fs.appendFileSync(logFile, `Screenshot failed: ${err.message}\n`);
    }
  } else {
    fs.appendFileSync(logFile, `Screenshot skipped: Page is closed\n`);
  }
}

export async function logOnFailure(page, testInfo, message, screenshotPath, logFile = 'test-results/test-logs.txt') {
  await logAndScreenshot(page, testInfo, message, screenshotPath, logFile);
  throw new Error(message);
}

export async function safeGoto(page, testInfo, url, options = { waitUntil: 'networkidle' }) {
  const maxRetries = 3;
  let finalUrl = url;
  const screenshotDir = `test-results/screenshots/${sanitizeForPath(testInfo.title)}`;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    if (page.isClosed()) {
      await logAndScreenshot(page, testInfo, `Page is closed before goto attempt ${attempt} for ${url}`, `${screenshotDir}/goto_attempt_${attempt}_closed.png`);
      return { success: false, finalUrl };
    }
    try {
      const response = await page.goto(finalUrl, { ...options, timeout: 20000 });
      const status = response ? response.status() : 'no response';
      const redirectUrl = response && status >= 300 && status < 400 ? response.headerValue('location') : null;
      await logAndScreenshot(page, testInfo, `Navigated to ${finalUrl} with status ${status}${redirectUrl ? `, Redirect: ${redirectUrl}` : ''} on attempt ${attempt}`, `${screenshotDir}/goto_attempt_${attempt}.png`);
      if (redirectUrl && redirectUrl !== finalUrl) {
        finalUrl = redirectUrl.startsWith('/') ? `${new URL(page.url()).origin}${redirectUrl}` : redirectUrl;
        await logAndScreenshot(page, testInfo, `Following redirect to ${finalUrl} on attempt ${attempt}`, `${screenshotDir}/goto_attempt_${attempt}_redirect.png`);
        continue;
      }
      return { success: true, finalUrl };
    } catch (err) {
      await logAndScreenshot(page, testInfo, `Goto attempt ${attempt} failed for ${finalUrl}: ${err.message}`, `${screenshotDir}/goto_attempt_${attempt}_error.png`);
      if (attempt === maxRetries) return { success: false, finalUrl };
      await page.waitForTimeout(1000);
    }
  }
  return { success: false, finalUrl };
}