import { test, expect, Page } from '@playwright/test';

type DiagnosticsState = {
  campaign_id: number | null;
  paused: boolean;
  leads: number;
  attributions: number;
  outreach_attempts: number;
  jobs: number;
  audit_logs: number;
  last_job_status: string | null;
};

// ---------- Helpers ----------
async function waitForStreamlitReady(page: Page) {
  await page.waitForSelector('section[data-testid="stSidebar"]', { timeout: 30000 });
  await page.waitForTimeout(750);
}

async function gotoDashboard(page: Page) {
  await page.getByText('Dashboard', { exact: true }).click();
  await page.waitForTimeout(500);
}

async function readDiagnostics(page: Page): Promise<DiagnosticsState> {
  // Expect the diagnostics JSON node to exist in E2E mode.
  const jsonNode = page.locator('[data-testid="aicmo-e2e-state-json"]');
  await expect(jsonNode).toBeVisible({ timeout: 10000 });

  const raw = (await jsonNode.textContent())?.trim() ?? '';
  expect(raw.length).toBeGreaterThan(0);

  let parsed: any;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    throw new Error(`Diagnostics JSON is not valid JSON. Raw:\n${raw}`);
  }

  // Validate required keys exist (fail hard if diagnostics contract drifts).
  const required = [
    'campaign_id', 'paused', 'leads', 'attributions',
    'outreach_attempts', 'jobs', 'audit_logs', 'last_job_status'
  ];
  for (const k of required) {
    if (!(k in parsed)) throw new Error(`Diagnostics missing key: ${k}. Full: ${raw}`);
  }

  return parsed as DiagnosticsState;
}

async function hardResetTestData(page: Page) {
  await gotoDashboard(page);

  const resetBtn = page.locator('[data-testid="aicmo-e2e-reset"]');
  await expect(resetBtn).toBeVisible({ timeout: 10000 });
  await resetBtn.click();

  // deterministic success marker
  await expect(page.locator('[data-testid="aicmo-e2e-reset-ok"]'))
    .toBeVisible({ timeout: 15000 });

  // allow DB commit + UI rerender
  await page.waitForTimeout(500);

  const s = await readDiagnostics(page);
  expect(s.leads).toBe(0);
  expect(s.jobs).toBe(0);
  expect(s.outreach_attempts).toBe(0);
}

function missingUIFail(name: string): never {
  throw new Error(
    `E2E UI control missing: ${name}. ` +
    `Implement it in Streamlit under AICMO_REVENUE_ENGINE_UI=1 with a stable data-testid.`
  );
}

// ---------- Test Suite ----------
test.describe('AICMO Revenue Marketing Engine E2E (Streamlit)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForStreamlitReady(page);
    await hardResetTestData(page);
  });

  test('Test 1: Campaign lifecycle gates dispatch (system pause)', async ({ page }) => {
    test.setTimeout(90000);
    await gotoDashboard(page);

    // REQUIRED: system pause control must have a stable selector in E2E mode
    const pauseToggle = page.locator('[data-testid="aicmo-system-pause-toggle"]');
    if (!(await pauseToggle.count())) missingUIFail('aicmo-system-pause-toggle');

    // pause
    await pauseToggle.click();
    await expect(page.locator('[data-testid="aicmo-system-paused-badge"]')).toBeVisible();

    let s = await readDiagnostics(page);
    expect(s.paused).toBe(true);

    // resume
    await pauseToggle.click();
    await expect(page.locator('[data-testid="aicmo-system-paused-badge"]')).not.toBeVisible();

    s = await readDiagnostics(page);
    expect(s.paused).toBe(false);
  });

  test('Test 2: Lead capture + attribution + dedupe', async ({ page }) => {
    test.setTimeout(90000);
    await gotoDashboard(page);

    // REQUIRED UI controls
    const email = page.locator('[data-testid="aicmo-lead-email"]');
    const utmCampaign = page.locator('[data-testid="aicmo-lead-utm-campaign"]');
    const submit = page.locator('[data-testid="aicmo-lead-submit"]');

    if (!(await email.count())) missingUIFail('aicmo-lead-email');
    if (!(await utmCampaign.count())) missingUIFail('aicmo-lead-utm-campaign');
    if (!(await submit.count())) missingUIFail('aicmo-lead-submit');

    // Add lead
    await email.fill('e2e.lead@example.com');
    await utmCampaign.fill('e2e_campaign_A');
    await submit.click();

    await expect.poll(async () => (await readDiagnostics(page)).leads, { timeout: 10000 })
      .toBe(1);

    // Add same lead again with changed UTM (should dedupe lead row, but update attribution/last_touch)
    await email.fill('e2e.lead@example.com');
    await utmCampaign.fill('e2e_campaign_B');
    await submit.click();

    const s = await readDiagnostics(page);
    expect(s.leads).toBe(1);                 // dedupe
    expect(s.attributions).toBeGreaterThan(0); // attribution rows exist
  });

  test('Test 3: DNC / unsubscribe enforcement blocks outreach', async ({ page }) => {
    test.setTimeout(90000);
    await gotoDashboard(page);

    // Create a lead first (reuse capture controls)
    const email = page.locator('[data-testid="aicmo-lead-email"]');
    const submit = page.locator('[data-testid="aicmo-lead-submit"]');
    if (!(await email.count())) missingUIFail('aicmo-lead-email');
    if (!(await submit.count())) missingUIFail('aicmo-lead-submit');

    await email.fill('e2e.dnc@example.com');
    await submit.click();
    await expect.poll(async () => (await readDiagnostics(page)).leads, { timeout: 10000 })
      .toBe(1);

    // Toggle DNC for that lead
    const leadPicker = page.locator('[data-testid="aicmo-lead-picker"]');
    const dncToggle = page.locator('[data-testid="aicmo-lead-dnc-toggle"]');
    const dncSave = page.locator('[data-testid="aicmo-lead-dnc-save"]');

    if (!(await leadPicker.count())) missingUIFail('aicmo-lead-picker');
    if (!(await dncToggle.count())) missingUIFail('aicmo-lead-dnc-toggle');
    if (!(await dncSave.count())) missingUIFail('aicmo-lead-dnc-save');

    await leadPicker.selectOption({ label: 'e2e.dnc@example.com' });
    await dncToggle.click();
    await dncSave.click();

    // Attempt to enqueue + dispatch outreach
    const enqueue = page.locator('[data-testid="aicmo-enqueue-email-job"]');
    const dispatch = page.locator('[data-testid="aicmo-run-dispatcher-once"]');
    if (!(await enqueue.count())) missingUIFail('aicmo-enqueue-email-job');
    if (!(await dispatch.count())) missingUIFail('aicmo-run-dispatcher-once');

    await enqueue.click();
    await dispatch.click();

    const s = await readDiagnostics(page);
    // Must not have proof sent attempts for DNC lead
    expect(s.outreach_attempts).toBe(0);
    expect(s.jobs).toBeGreaterThanOrEqual(0);
  });

  test('Test 4: Proof-run distribution job execution (email)', async ({ page }) => {
    test.setTimeout(90000);
    await gotoDashboard(page);

    // Create a consented lead
    const email = page.locator('[data-testid="aicmo-lead-email"]');
    const submit = page.locator('[data-testid="aicmo-lead-submit"]');
    if (!(await email.count())) missingUIFail('aicmo-lead-email');
    if (!(await submit.count())) missingUIFail('aicmo-lead-submit');

    await email.fill('e2e.send@example.com');
    await submit.click();

    await expect.poll(async () => (await readDiagnostics(page)).leads, { timeout: 10000 })
      .toBe(1);

    // Enqueue and dispatch once
    const enqueue = page.locator('[data-testid="aicmo-enqueue-email-job"]');
    const dispatch = page.locator('[data-testid="aicmo-run-dispatcher-once"]');
    if (!(await enqueue.count())) missingUIFail('aicmo-enqueue-email-job');
    if (!(await dispatch.count())) missingUIFail('aicmo-run-dispatcher-once');

    await enqueue.click();
    await dispatch.click();

    // Proof-run should result in PROOF_SENT (or equivalent)
    await expect.poll(async () => (await readDiagnostics(page)).last_job_status, { timeout: 15000 })
      .not.toBeNull();

    const s = await readDiagnostics(page);
    expect(s.jobs).toBeGreaterThan(0);
    expect(s.outreach_attempts).toBeGreaterThanOrEqual(1);
    expect(String(s.last_job_status)).toMatch(/PROOF|SIMUL|SENT/i);
  });

  test('Test 5: Artifacts export exists and is correct', async ({ page }) => {
    test.setTimeout(90000);
    await gotoDashboard(page);

    // Export Leads CSV
    const exportBtn = page.locator('[data-testid="aicmo-export-leads-csv"]');
    if (!(await exportBtn.count())) missingUIFail('aicmo-export-leads-csv');

    const download = await Promise.all([
      page.waitForEvent('download', { timeout: 15000 }),
      exportBtn.click(),
    ]);

    const dl = download[0];
    const path = await dl.path();
    expect(path).toBeTruthy();

    // Generate report artifact
    const reportBtn = page.locator('[data-testid="aicmo-generate-campaign-report"]');
    if (!(await reportBtn.count())) missingUIFail('aicmo-generate-campaign-report');

    await reportBtn.click();

    // Diagnostics should expose last report path and report has required section headings
    const reportPathNode = page.locator('[data-testid="aicmo-last-report-path"]');
    const reportOkNode = page.locator('[data-testid="aicmo-last-report-has-required-sections"]');
    if (!(await reportPathNode.count())) missingUIFail('aicmo-last-report-path');
    if (!(await reportOkNode.count())) missingUIFail('aicmo-last-report-has-required-sections');

    await expect(reportPathNode).toBeVisible({ timeout: 15000 });
    await expect(reportOkNode).toHaveText(/true/i, { timeout: 15000 });
  });

  test('Bonus: E2E Diagnostics panel is functional', async ({ page }) => {
    test.setTimeout(60000);
    await gotoDashboard(page);

    await expect(page.locator('[data-testid="aicmo-e2e-state-json"]')).toBeVisible();
    await expect(page.locator('[data-testid="aicmo-e2e-reset"]')).toBeVisible();

    const s = await readDiagnostics(page);
    expect(s.leads).toBeGreaterThanOrEqual(0);
    expect(s.jobs).toBeGreaterThanOrEqual(0);
  });
});
