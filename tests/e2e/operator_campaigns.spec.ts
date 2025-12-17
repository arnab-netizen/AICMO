import { test } from '@playwright/test';
import {
  expectNoConsoleErrors,
  gotoAndWaitForStreamlit,
  openTab,
  fillMinimumInputs,
  clickGenerate,
  assertDeliverablesVisible,
  amendApproveExport,
} from './helpers';

test('Operator Campaigns E2E flow', async ({ page }) => {
  const assertNoConsole = await expectNoConsoleErrors(page);
  await gotoAndWaitForStreamlit(page, '/');
  const tabKey = await openTab(page, 'Campaigns');
  await fillMinimumInputs(page);

  // track generate requests
  const genRequests: any[] = [];
  page.on('requestfinished', async (req) => {
    try {
      const url = req.url();
      const resp = req.response();
      if (url.includes('/aicmo/generate') && resp) {
        genRequests.push({ url, status: resp.status() });
      } else if (resp) {
        const text = await resp.text();
        if (text && text.includes('deliverables')) genRequests.push({ url, status: resp.status() });
      }
    } catch {}
  });

  await clickGenerate(page, tabKey);
  await page.waitForTimeout(2000);
  await assertDeliverablesVisible(page, tabKey);

  if (genRequests.length === 0) throw new Error('No /aicmo/generate request observed');
  for (const r of genRequests) if (r.status !== 200) throw new Error('Generate request failed with non-200 status');

  await amendApproveExport(page, tabKey);
  await assertNoConsole();
});
