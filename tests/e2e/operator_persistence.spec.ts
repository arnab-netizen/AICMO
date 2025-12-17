import { test, expect } from '@playwright/test';
import { gotoAndWaitForStreamlit, openTab, fillMinimumInputs, clickGenerate, amendApproveExport } from './helpers';

test('Session persistence across tabs', async ({ page }) => {
  await gotoAndWaitForStreamlit(page, '/');
  const campaigns = await openTab(page, 'Campaigns');
  await fillMinimumInputs(page);
  await clickGenerate(page, campaigns);
  // amend and approve
  await amendApproveExport(page, campaigns);

  // switch to Creatives and back
  await openTab(page, 'Creatives');
  await page.waitForTimeout(500);
  await openTab(page, 'Campaigns');
  // Ensure amended marker persists
  const textarea = page.locator('textarea').first();
  const val = await textarea.inputValue();
  expect(val).toContain('[AMENDED_BY_TEST]');
});
