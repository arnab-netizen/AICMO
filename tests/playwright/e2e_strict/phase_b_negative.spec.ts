/**
 * Phase B Negative E2E Test
 * 
 * Proves that the export gate correctly blocks delivery for contract violations:
 * - Invalid output (TODO in section title) fails contract validation
 * - Validation status shows FAIL
 * - Downloads are blocked with clear messaging
 * - Validation report contains explicit violation reason
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Test configuration
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:8501';
const ARTIFACTS_DIR = process.env.AICMO_E2E_ARTIFACT_DIR || './.artifacts/e2e';
const TIMEOUT = 120000; // 2 minutes for export generation

test.describe('Phase B - Negative E2E (FAIL Validation)', () => {
  
  test('should detect contract violation, show FAIL status, and block downloads', async ({ page }) => {
    // Navigate to app
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    
    // Wait for app to load
    await page.waitForTimeout(2000);
    
    // PHASE 4.1: Deterministic navigation proof
    console.log('📍 PHASE 4.1 Step A: Verify app loaded...');
    await expect(page.locator('[data-testid="e2e-app-loaded"]')).toBeVisible();
    console.log('✓ App loaded sentinel visible');
    
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
    
    // PHASE 4.1 Step E: Confirm Export branch sentinel
    console.log('📍 PHASE 4.1 Step E: Verify Export branch executing...');
    await expect(page.locator('[data-testid="e2e-on-export-page"]')).toBeVisible();
    console.log('✓ Export branch sentinel visible');
    
    // Step 2: Enable violation mode via checkbox
    console.log('📍 Step 2: Enabling violation mode...');
    const e2eDiagnostics = page.locator('.e2e-diagnostics');
    
    if (await e2eDiagnostics.isVisible()) {
      console.log('✓ E2E diagnostics visible');
      
      try {
        const violationCheckbox = page.locator('input[type="checkbox"]').first();
        const isChecked = await violationCheckbox.isChecked({ timeout: 5000 });
        
        if (!isChecked) {
          console.log('📍 Checking violation mode checkbox...');
          await violationCheckbox.check();
          await page.waitForTimeout(1000);
          console.log('✓ Violation mode enabled');
        } else {
          console.log('✓ Violation mode already enabled');
        }
      } catch (e) {
        console.log('⚠️ Could not interact with violation checkbox');
        throw new Error('Failed to enable violation mode - checkbox not found');
      }
    }
    
    // Step 3: Capture handler entries before click
    console.log('📍 Step 3: Capturing handler entries before click...');
    const handlerEntriesBefore = await page.locator('[data-testid="e2e-export-handler-entries"]').textContent() || '0';
    const entriesBeforeNum = parseInt(handlerEntriesBefore, 10);
    console.log(`✓ Handler entries before click: ${entriesBeforeNum}`);
    
    // Step 4: Trigger export with violation
    console.log('📍 Step 4: Clicking export button (violation mode ON)...');
    const exportButton = page.getByRole('button', { name: /Generate export file/i });
    await exportButton.waitFor({ state: 'visible', timeout: 10000 });
    await exportButton.click({ timeout: TIMEOUT });
    console.log('✓ Export button clicked');
    
    // PHASE 4.3 Step 2: Verify handler incremented
    console.log('📍 PHASE 4.3 Step 2: Verify handler entries incremented...');
    await page.waitForTimeout(1000);  // Wait for rerun
    const handlerEntriesAfter = await page.locator('[data-testid="e2e-export-handler-entries"]').textContent() || '0';
    const entriesAfterNum = parseInt(handlerEntriesAfter, 10);
    console.log(`✓ Handler entries after click: ${entriesAfterNum}`);
    
    if (entriesAfterNum === entriesBeforeNum + 1) {
      console.log('✓ Handler incremented by exactly 1');
    } else {
      throw new Error(`Handler entries did not increment correctly: before=${entriesBeforeNum}, after=${entriesAfterNum}`);
    }
    
    // Step 5: Wait for state to become FAIL (not ERROR)
    console.log('📍 Step 5: Waiting for export state to become FAIL...');
    const exportState = page.locator('[data-testid="e2e-export-state"]').last();  // Get LAST element
    let stateText = '';
    let attempts = 0;
    const maxAttempts = 60; // 60 seconds max
    
    while (attempts < maxAttempts) {
      stateText = await exportState.textContent() || '';
      console.log(`  Poll ${attempts + 1}: ${stateText}`);
      
      if (stateText.includes('FAIL')) {
        console.log('✓ Export state is FAIL (validation blocked as expected)');
        break;
      } else if (stateText.includes('PASS')) {
        throw new Error('Export unexpectedly passed validation with TODO violation!');
      } else if (stateText.includes('ERROR')) {
        // ERROR is acceptable but FAIL is preferred
        console.log('⚠️ Export state is ERROR (acceptable, but FAIL is better)');
        break;
      }
      
      await page.waitForTimeout(1000);
      attempts++;
    }
    
    if (!stateText.includes('FAIL') && !stateText.includes('ERROR')) {
      throw new Error(`Timeout waiting for FAIL state. Last state: ${stateText}`);
    }
    
    // Step 6: Read last_error and verify it mentions TODO/forbidden
    console.log('📍 Step 6: Checking error message...');
    const errorLocator = page.locator('[data-testid="e2e-export-last-error"]').last();  // Get LAST element
    const errorText = await errorLocator.textContent();
    const errorMsg = errorText?.replace('ERROR: ', '').trim() || '';
    console.log(`✓ Error message: ${errorMsg}`);
    
    if (!errorMsg.toLowerCase().includes('todo') && !errorMsg.toLowerCase().includes('forbidden')) {
      console.log('⚠️ Warning: Error message does not explicitly mention TODO or forbidden');
    }
    
    // Step 7: Verify blocked downloads message is visible
    console.log('📍 Step 7: Verifying downloads blocked message...');
    const blockedMsg = page.locator('[data-testid="e2e-downloads-blocked"]');
    await blockedMsg.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ Downloads blocked message visible');
    
    // Step 7.5: Verify NO deliverable wrappers exist (proof that downloads are blocked)
    console.log('📍 Step 7.5: Verifying deliverable download wrappers are absent...');
    const deliverableWrappers = page.locator('[data-testid^="e2e-download-"][data-testid!="e2e-download-manifest"][data-testid!="e2e-download-validation"][data-testid!="e2e-download-section-map"][data-testid!="e2e-download-validation-fail"][data-testid!="e2e-download-section-map-fail"]');
    const deliverableCount = await deliverableWrappers.count();
    if (deliverableCount > 0) {
      throw new Error(`Found ${deliverableCount} deliverable wrappers when FAIL state should block them!`);
    }
    console.log('✓ No deliverable wrappers found (downloads correctly blocked)');
    
    // Step 8: Download validation JSON for inspection
    console.log('📍 Step 8: Downloading validation JSON...');
    const runTimestamp = Date.now();
    const testRunDir = path.join(ARTIFACTS_DIR, `playwright_negative_${runTimestamp}`);
    
    if (!fs.existsSync(testRunDir)) {
      fs.mkdirSync(testRunDir, { recursive: true });
    }
    
    const validationPath = path.join(testRunDir, 'validation.json');
    const validationDownloadPromise = page.waitForEvent('download');
    await page.locator('[data-testid="e2e-download-validation-fail"]').locator('button').click();
    const validationDownload = await validationDownloadPromise;
    await validationDownload.saveAs(validationPath);
    console.log(`✓ Validation saved to: ${validationPath}`);
    
    const validationContent = fs.readFileSync(validationPath, 'utf-8');
    const validation = JSON.parse(validationContent);
    
    // Assert TODO violation is present
    const validationStr = JSON.stringify(validation).toLowerCase();
    if (!validationStr.includes('todo')) {
      throw new Error('Validation JSON does not contain TODO violation evidence');
    }
    console.log('✓ TODO violation found in validation JSON');
    
    // Step 9: Verify deliverable download buttons are ABSENT
    console.log('📍 Step 9: Verifying deliverable downloads are absent...');
    const deliverableButtons = await page.locator('[data-testid^="e2e-download-client_output"]').locator('button').count();
    console.log(`✓ Deliverable download buttons: ${deliverableButtons} (should be 0)`);
    
    if (deliverableButtons > 0) {
      throw new Error(`Expected 0 deliverable download buttons, but found ${deliverableButtons}`);
    }
    
    // Step 10: Create test summary JSON
    console.log('📍 Step 10: Creating test summary...');
    
    const summary = {
      test: 'Phase B Negative',
      timestamp: new Date().toISOString(),
      run_id: `playwright_negative_${runTimestamp}`,
      export_state: stateText,
      last_error: errorMsg,
      result: 'PASS',  // Test passes because we proved FAIL works
      test_assertions: {
        export_state_fail: stateText.includes('FAIL'),
        error_mentions_violation: errorMsg.toLowerCase().includes('todo') || errorMsg.toLowerCase().includes('forbidden'),
        blocked_message_visible: true,
        validation_has_todo: validationStr.includes('todo'),
        deliverable_buttons_absent: deliverableButtons === 0
      },
      validation_file: validationPath
    };
    
    // Save summary
    const summaryPath = path.join(testRunDir, 'test_summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    console.log(`✓ Test summary saved to: ${summaryPath}`);
    
    // Step 11: Final assertions
    console.log('📍 Step 11: Final assertions...');
    
    expect(summary.test_assertions.export_state_fail).toBe(true);
    expect(summary.test_assertions.validation_has_todo).toBe(true);
    expect(summary.test_assertions.deliverable_buttons_absent).toBe(true);
    expect(summary.test_assertions.blocked_message_visible).toBe(true);
    
    console.log('✅ Phase B Negative Test PASSED (Validation correctly blocked deliverables with TODO)');
  });
  
});

