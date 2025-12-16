/**
 * Phase B Positive E2E Test
 * 
 * Proves that the export gate works end-to-end with PASS validation:
 * - Valid output passes contract validation
 * - Manifest + validation + section_map JSONs are generated
 * - Downloads are available and match manifest
 * - Parity check: downloaded files == manifest artifacts
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

// Test configuration
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:8501';
const ARTIFACTS_DIR = process.env.AICMO_E2E_ARTIFACT_DIR || './.artifacts/e2e';
const TIMEOUT = 120000; // 2 minutes for export generation

// Helper: compute SHA256 of file
function computeSha256(filePath: string): string {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

test.describe('Phase B - Positive E2E (PASS Validation)', () => {
  
  test('should generate valid export with PASS validation and downloadable artifacts', async ({ page }) => {
    // Navigate to app
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    
    // Wait for app to load
    await page.waitForTimeout(2000);
    
    // PHASE 4.1: Deterministic navigation proof
    console.log('📍 PHASE 4.1 Step A: Verify app loaded...');
    await expect(page.locator('[data-testid="e2e-app-loaded"]')).toBeVisible();
    console.log('✓ App loaded sentinel visible');
    
    // PHASE 4.1 Step B: Assert nav current visible (before clicking)
    console.log('📍 PHASE 4.1 Step B: Check initial nav value...');
    const navCurrentBefore = await page.locator('[data-testid="e2e-nav-current"]').textContent();
    console.log(`✓ Initial nav value: ${navCurrentBefore}`);
    
    // PHASE 4.1 Step C: Click Export via deterministic selector
    console.log('📍 PHASE 4.1 Step C: Click Export radio...');
    try {
      const exportLabel = page.locator('label').filter({ hasText: /^Export$/ }).first();
      await exportLabel.click({ timeout: 5000 });
    } catch (e) {
      console.log('Label selector failed, trying text selector...');
      const exportText = page.getByText('Export', { exact: true });
      await exportText.click({ timeout: 5000 });
    }
    await page.waitForTimeout(2000);
    
    // PHASE 4.1 Step D: Confirm nav is now Export
    console.log('📍 PHASE 4.1 Step D: Verify nav changed to Export...');
    await expect(page.locator('[data-testid="e2e-nav-current"]')).toHaveText('Export');
    const navCurrentAfter = await page.locator('[data-testid="e2e-nav-current"]').textContent();
    console.log(`✓ Nav changed to: ${navCurrentAfter}`);
    
    // PHASE 4.1 Step E: Confirm Export branch sentinel
    console.log('📍 PHASE 4.1 Step E: Verify Export branch executing...');
    await expect(page.locator('[data-testid="e2e-on-export-page"]')).toBeVisible();
    console.log('✓ Export branch sentinel visible');
    
    // Step 2: Verify we're in E2E mode and disable violation mode
    console.log('📍 Step 2: Verifying E2E mode...');
    const e2eDiagnostics = page.locator('.e2e-diagnostics');
    if (await e2eDiagnostics.isVisible()) {
      console.log('✓ E2E diagnostics visible');
      
      try {
        const violationCheckbox = page.locator('input[type="checkbox"]').first();
        const isChecked = await violationCheckbox.isChecked({ timeout: 5000 });
        
        if (isChecked) {
          console.log('📍 Unchecking violation mode...');
          await violationCheckbox.uncheck();
          await page.waitForTimeout(1000);
        } else {
          console.log('✓ Violation mode already unchecked');
        }
      } catch (e) {
        console.log('⚠️ Could not interact with violation checkbox, continuing anyway...');
      }
    }
    
    // Step 3: Verify export button and handler counter
    console.log('📍 Step 3: Checking export handler counter...');
    await page.waitForTimeout(1000);  // Extra wait for UI render
    const handlerCounterLocator = page.locator('[data-testid="e2e-export-handler-entries"]');
    await handlerCounterLocator.waitFor({ state: 'visible', timeout: 5000 });
    const handlerEntriesBefore = await handlerCounterLocator.textContent() || '0';
    const entriesBeforeNum = parseInt(handlerEntriesBefore, 10);
    console.log(`✓ Handler entries before click: ${entriesBeforeNum}`);
    
    // Step 4: Click export button
    console.log('📍 Step 4: Clicking export button...');
    const exportButton = page.getByRole('button', { name: /Generate export file/i });
    await exportButton.waitFor({ state: 'visible', timeout: 10000 });
    await exportButton.click({ timeout: TIMEOUT });
    console.log('✓ Export button clicked');
    
    // PHASE 4.2 Step 2: Verify handler incremented
    console.log('📍 PHASE 4.2 Step 2: Verify handler entries incremented...');
    for (let i = 0; i < 5; i++) {
      await page.waitForTimeout(2000);
      const handlerEntriesCheck = await page.locator('[data-testid="e2e-export-handler-entries"]').textContent() || '0';
      const entriesCheckNum = parseInt(handlerEntriesCheck, 10);
      console.log(`  Poll ${i + 1}: Handler entries = ${entriesCheckNum}`);
      if (entriesCheckNum === entriesBeforeNum + 1) {
        console.log('✓ Handler incremented by exactly 1');
        break;
      }
    }
    const handlerEntriesAfter = await page.locator('[data-testid="e2e-export-handler-entries"]').textContent() || '0';
    const entriesAfterNum = parseInt(handlerEntriesAfter, 10);
    console.log(`✓ Handler entries after click: ${entriesAfterNum}`);
    
    if (entriesAfterNum === entriesBeforeNum + 1) {
      console.log('✓ Handler incremented by exactly 1');
    } else {
      throw new Error(`Handler entries did not increment correctly: before=${entriesBeforeNum}, after=${entriesAfterNum}`);
    }
    
    // PHASE 4.2 Step 3: Wait for state PASS
    console.log('📍 PHASE 4.2 Step 3: Waiting for export state to become PASS...');
    console.log('📍 Step 5: Waiting for export state to become PASS...');
    const exportState = page.locator('[data-testid="e2e-export-state"]').last();  // Get LAST element (most recent)
    let stateText = '';
    let attempts = 0;
    const maxAttempts = 60; // 60 seconds max
    
    while (attempts < maxAttempts) {
      stateText = await exportState.textContent() || '';
      console.log(`  Poll ${attempts + 1}: ${stateText}`);
      
      if (stateText.includes('PASS')) {
        console.log('✓ Export state is PASS');
        break;
      } else if (stateText.includes('FAIL') || stateText.includes('ERROR')) {
        throw new Error(`Export failed with state: ${stateText}`);
      }
      
      await page.waitForTimeout(1000);
      attempts++;
    }
    
    if (!stateText.includes('PASS')) {
      throw new Error(`Timeout waiting for PASS state. Last state: ${stateText}`);
    }
    
    // Step 6: Read run_id from sentinel
    console.log('📍 Step 6: Reading run_id...');
    const runIdLocator = page.locator('[data-testid="e2e-export-run-id"]').last();  // Get LAST element
    const runIdText = await runIdLocator.textContent();
    const runId = runIdText?.replace('RUN_ID: ', '').trim() || '';
    console.log(`✓ Run ID: ${runId}`);
    
    if (!runId || runId === 'NONE') {
      throw new Error('Run ID not set after successful export');
    }
    
    // Step 7: Wait for downloads ready marker
    console.log('📍 Step 7: Waiting for downloads ready...');
    const downloadsReady = page.locator('[data-testid="e2e-downloads-ready"]');
    await downloadsReady.waitFor({ state: 'attached', timeout: 10000 });
    console.log('✓ Downloads ready marker found');
    
    // Step 8: Download manifest and parse
    console.log('📍 Step 8: Downloading manifest...');
    const runTimestamp = Date.now();
    const testRunDir = path.join(ARTIFACTS_DIR, `playwright_positive_${runTimestamp}`);
    
    if (!fs.existsSync(testRunDir)) {
      fs.mkdirSync(testRunDir, { recursive: true });
    }
    
    // Wait longer and scroll to ensure downloads section is visible
    await page.waitForTimeout(5000);
    await page.evaluate(() => window.scrollBy(0, 800));
    await page.waitForTimeout(3000);
    
    // Debug: Check what's actually on the page
    const pageContent = await page.content();
    const hasManifestDiv = pageContent.includes('e2e-download-manifest');
    const hasButton = pageContent.includes('<button');
    console.log(`📍 Page content check: has manifest div=${hasManifestDiv}, has button=${hasButton}`);
    
    // List all testids on page
    const allTestIds = await page.locator('[data-testid]').all();
    console.log(`📍 Found ${allTestIds.length} elements with data-testid`);
    for (const el of allTestIds.slice(-10)) {
      const testid = await el.getAttribute('data-testid');
      console.log(`  - ${testid}`);
    }
    
    const manifestPath = path.join(testRunDir, 'manifest.json');
    const manifestButton = page.locator('[data-testid="e2e-download-manifest"]').locator('button');
    console.log('📍 Waiting for manifest button visibility...');
    try {
      await manifestButton.waitFor({ state: 'visible', timeout: 20000 });
      console.log('✓ Manifest button visible');
    } catch (e) {
      console.log(`❌ Manifest button not found. Checking for manifest div...`);
      const manifestDiv = page.locator('[data-testid="e2e-download-manifest"]');
      const isVisible = await manifestDiv.isVisible();
      console.log(`  Manifest div visible: ${isVisible}`);
      throw e;
    }
    
    const manifestDownloadPromise = page.waitForEvent('download');
    await manifestButton.click();
    const manifestDownload = await manifestDownloadPromise;
    await manifestDownload.saveAs(manifestPath);
    console.log(`✓ Manifest saved to: ${manifestPath}`);
    
    const manifestContent = fs.readFileSync(manifestPath, 'utf-8');
    const manifest = JSON.parse(manifestContent);
    console.log(`✓ Manifest parsed: ${manifest.artifacts?.length || 0} artifacts`);
    
    // Step 9: Download validation JSON
    console.log('📍 Step 9: Downloading validation...');
    const validationPath = path.join(testRunDir, 'validation.json');
    const validationButton = page.locator('[data-testid="e2e-download-validation"]').locator('button');
    await validationButton.waitFor({ state: 'visible', timeout: 10000 });
    const validationDownloadPromise = page.waitForEvent('download');
    await validationButton.click();
    const validationDownload = await validationDownloadPromise;
    await validationDownload.saveAs(validationPath);
    console.log(`✓ Validation saved to: ${validationPath}`);
    
    // Step 10: Download section map JSON
    console.log('📍 Step 10: Downloading section map...');
    const sectionMapPath = path.join(testRunDir, 'section_map.json');
    const sectionMapButton = page.locator('[data-testid="e2e-download-section-map"]').locator('button');
    await sectionMapButton.waitFor({ state: 'visible', timeout: 10000 });
    const sectionMapDownloadPromise = page.waitForEvent('download');
    await sectionMapButton.click();
    const sectionMapDownload = await sectionMapDownloadPromise;
    await sectionMapDownload.saveAs(sectionMapPath);
    console.log(`✓ Section map saved to: ${sectionMapPath}`);
    
    // Step 11: Download all artifacts from manifest and verify SHA256
    console.log('📍 Step 11: Downloading deliverables and verifying SHA256...');
    const downloadedFiles: string[] = [];
    const sha256Mismatches: string[] = [];
    
    if (manifest.artifacts && Array.isArray(manifest.artifacts)) {
      for (const artifact of manifest.artifacts) {
        const artifactId = artifact.artifact_id;
        const filename = artifact.filename;
        const expectedSha256 = artifact.sha256;  // From manifest
        
        console.log(`  Downloading ${artifactId}: ${filename}...`);
        
        const artifactPath = path.join(testRunDir, filename);
        const artifactDownloadPromise = page.waitForEvent('download');
        const artifactButton = page.locator(`[data-testid="e2e-download-${artifactId}"]`).locator('button');
        await artifactButton.click();
        const artifactDownload = await artifactDownloadPromise;
        await artifactDownload.saveAs(artifactPath);
        
        // Assert file size > 0
        const stats = fs.statSync(artifactPath);
        if (stats.size === 0) {
          throw new Error(`Downloaded file ${filename} has size 0`);
        }
        
        // Compute SHA256 and compare
        const actualSha256 = computeSha256(artifactPath);
        if (expectedSha256 && actualSha256 !== expectedSha256) {
          sha256Mismatches.push(`${filename}: expected ${expectedSha256}, got ${actualSha256}`);
        }
        
        console.log(`  ✓ ${filename} (${stats.size} bytes, SHA256: ${actualSha256.substring(0, 16)}...)`);
        downloadedFiles.push(filename);
      }
    }
    
    if (sha256Mismatches.length > 0) {
      throw new Error(`SHA256 mismatches:\n${sha256Mismatches.join('\n')}`);
    }
    
    console.log(`✓ Downloaded ${downloadedFiles.length} deliverables with SHA256 verification passed`);
    
    // Step 12: Assert filename parity
    console.log('📍 Step 12: Checking filename parity...');
    const manifestFilenames = manifest.artifacts?.map((a: any) => a.filename).sort() || [];
    const actualFilenames = downloadedFiles.sort();
    
    console.log(`  Manifest filenames: ${JSON.stringify(manifestFilenames)}`);
    console.log(`  Downloaded filenames: ${JSON.stringify(actualFilenames)}`);
    
    if (JSON.stringify(manifestFilenames) !== JSON.stringify(actualFilenames)) {
      throw new Error(`Filename mismatch! Manifest: ${manifestFilenames.join(', ')} vs Downloaded: ${actualFilenames.join(', ')}`);
    }
    
    console.log('✓ Filename parity passed');
    
    // Step 13: Create test summary
    console.log('📍 Step 13: Creating test summary...');
    
    const summary = {
      test: 'Phase B Positive',
      timestamp: new Date().toISOString(),
      run_id: runId,
      export_state: stateText,
      result: 'PASS',
      test_assertions: {
        export_state_pass: stateText.includes('PASS'),
        run_id_set: runId && runId !== 'NONE',
        downloads_ready: true,
        manifest_downloaded: true,
        validation_downloaded: true,
        section_map_downloaded: true,
        deliverables_count: downloadedFiles.length,
        filename_parity_pass: JSON.stringify(manifestFilenames) === JSON.stringify(actualFilenames)
      },
      downloaded_files: downloadedFiles,
      manifest_files: manifestFilenames
    };
    
    // Save summary
    const summaryPath = path.join(testRunDir, 'test_summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    console.log(`✓ Test summary saved to: ${summaryPath}`);
    
    // Step 14: Final assertions
    console.log('📍 Step 14: Final assertions...');
    
    expect(summary.test_assertions.export_state_pass).toBe(true);
    expect(summary.test_assertions.run_id_set).toBe(true);
    expect(summary.test_assertions.downloads_ready).toBe(true);
    expect(summary.test_assertions.manifest_downloaded).toBe(true);
    expect(summary.test_assertions.filename_parity_pass).toBe(true);
    expect(downloadedFiles.length).toBeGreaterThan(0);
    
    console.log('✅ Phase B Positive Test PASSED (Full E2E with downloads and parity)');
  });
  
});

