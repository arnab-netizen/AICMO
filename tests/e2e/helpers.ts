import { expect, Page } from '@playwright/test';

export async function expectNoConsoleErrors(page: Page) {
  const errors: string[] = [];
  page.on('console', (msg) => {
    try {
      const text = msg.text();
      if (msg.type() === 'error') errors.push(text);
      const badPatterns = ['Traceback', 'StreamlitAPIException', 'Invalid binary data format', 'NoneType'];
      for (const p of badPatterns) if (text.includes(p)) errors.push(text);
    } catch (e) {
      errors.push('console-listen-failed');
    }
  });
  page.on('pageerror', (err) => {
    errors.push(String(err));
  });

  // small helper to assert zero errors at checkpoints
  return async function assertNoConsoleErrors() {
    if (errors.length > 0) {
      throw new Error('Console/page errors detected:\n' + errors.join('\n---\n'));
    }
  };
}

export async function gotoAndWaitForStreamlit(page: Page, path = '/') {
  const url = path.startsWith('http') ? path : `${page.context().baseURL}${path}`;
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  // Wait for a known element in the nav (fallbacks)
  const navCandidates = [
    page.getByRole('button', { name: 'Intake' }),
    page.getByRole('button', { name: 'Campaigns' }),
    page.locator('text=Generate'),
  ];
  for (const c of navCandidates) {
    try {
      await c.first().waitFor({ timeout: 10000 });
      return;
    } catch (e) {
      // try next
    }
  }
  // final fallback: wait for body to contain "Streamlit"
  await page.locator('body').waitFor({ timeout: 15000 });
}

export async function openTab(page: Page, tabName: string): Promise<string> {
  const btn = page.getByRole('button', { name: tabName });
  const tabKey = tabName.toLowerCase().replace(/\s+/g, '-');
  if (await btn.count() > 0) {
    await btn.first().click();
    // assert anchor exists
    const anchor = page.locator(`[data-testid="tab-${tabKey}"]`);
    await expect(anchor).toBeVisible();
    return tabKey;
  }
  // fallback: click any element with exact text
  const textEl = page.locator(`text=^${tabName}$`);
  if (await textEl.count() > 0) {
    await textEl.first().click();
    const anchor = page.locator(`[data-testid="tab-${tabKey}"]`);
    await expect(anchor).toBeVisible();
    return tabKey;
  }
  throw new Error(`Tab '${tabName}' not found`);
}

export async function fillMinimumInputs(page: Page) {
  // Fill first visible text inputs
  const inputs = page.locator('input[type="text"]:not([disabled])');
  const count = await inputs.count();
  for (let i = 0; i < Math.min(4, count); i++) {
    const el = inputs.nth(i);
    try {
      await el.fill('Test');
    } catch {}
  }

  // Fill textareas
  const areas = page.locator('textarea:not([disabled])');
  const aCount = await areas.count();
  for (let i = 0; i < Math.min(2, aCount); i++) {
    await areas.nth(i).fill('Test content for E2E verification.');
  }

  // Choose first valid select option
  const selects = page.locator('select:not([disabled])');
  const sCount = await selects.count();
  for (let i = 0; i < sCount; i++) {
    try {
      const options = await selects.nth(i).locator('option').allTextContents();
      if (options.length > 1) await selects.nth(i).selectOption({ index: 1 });
    } catch {}
  }
}

export async function clickGenerate(page: Page, tabKey?: string) {
  if (tabKey) {
    const genAnchor = page.locator(`[data-testid="btn-generate-${tabKey}"]`);
    await expect(genAnchor).toBeVisible();
  }
  const btn = page.getByRole('button', { name: /Generate/i });
  if (await btn.count() === 0) throw new Error('Generate button not found');
  await btn.first().click();
  await page.waitForTimeout(500);
}

export async function assertDeliverablesVisible(page: Page, tabKey?: string) {
  if (tabKey) {
    const outputAnchor = page.locator(`[data-testid="output-${tabKey}"]`);
    await expect(outputAnchor).toBeVisible();
  }
  const bodyText = await page.locator('body').innerText();
  // Fail if only manifest markers present
  const manifestPatterns = [/"creatives"\s*:\s*\[/i, /creatives_generated/i];
  for (const p of manifestPatterns) {
    if (p.test(bodyText) && bodyText.length < 400) {
      throw new Error('UI shows manifest-only JSON instead of human-readable deliverables');
    }
  }
  // Require either long human-readable content or multiple headings
  const headings = (bodyText.match(/^#{1,6}\s+/gm) || []).length;
  if (bodyText.length < 200 && headings < 2) {
    throw new Error('Deliverables content too short or missing headings');
  }
}

export async function amendApproveExport(page: Page, tabKey?: string) {
  // find editable textarea or markdown editor
  if (tabKey) {
    const draftAnchor = page.locator(`[data-testid="draft-editor-${tabKey}"]`);
    await expect(draftAnchor).toBeVisible();
  }
  const textarea = page.locator('textarea').first();
  if (await textarea.count() === 0) throw new Error('Editable area for amendment not found');
  const marker = '[AMENDED_BY_TEST]';
  await textarea.click();
  const prev = await textarea.inputValue();
  await textarea.fill(prev + '\n\n' + marker);

  // click Approve
  if (tabKey) {
    const approveAnchor = page.locator(`[data-testid="btn-approve-${tabKey}"]`);
    await expect(approveAnchor).toBeVisible();
  }
  const approve = page.getByRole('button', { name: /Approve/i });
  if (await approve.count() === 0) throw new Error('Approve button not found');
  await approve.first().click();

  // wait for export/download button
  if (tabKey) {
    const exportAnchor = page.locator(`[data-testid="export-${tabKey}"]`);
    await expect(exportAnchor).toBeVisible();
  }
  const exportBtn = page.getByRole('button', { name: /(Export|Download)/i });
  if (await exportBtn.count() === 0) throw new Error('Export/Download button not found');

  // perform download and validate
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 15000 }),
    exportBtn.first().click(),
  ]);
  const path = await download.path();
  if (!path) throw new Error('Download did not complete');
  // read file and assert contains marker and size > 200 bytes
  const fs = require('fs');
  const content = fs.readFileSync(path, 'utf8');
  if (content.length < 200) throw new Error('Downloaded file too small');
  if (!content.includes('[AMENDED_BY_TEST]')) throw new Error('Amendment marker not found in downloaded file');
}
