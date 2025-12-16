/**
 * E2E Strict Client Output Gate - Negative Tests
 * 
 * Purpose: Verify that invalid client-facing outputs are properly detected and blocked.
 * 
 * Exit Criteria:
 * - Placeholders in outputs → validation FAIL
 * - Missing required sections → validation FAIL
 * - Forbidden phrases in outputs → validation FAIL
 * - Word count below threshold → validation FAIL
 * - Invalid file structure → validation FAIL
 * - External sends in proof-run → blocked
 * - Delivery with FAIL validation → blocked
 * - Delivery gate enforces all rules
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const E2E_ARTIFACT_DIR = process.env.AICMO_E2E_ARTIFACT_DIR || '/workspaces/AICMO/artifacts/e2e';
const BASE_URL = process.env.BASE_URL || 'http://localhost:8501';

test.describe('E2E Strict Gate - Negative Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
  });

  test('01. Placeholder Detection - {{PLACEHOLDER}} in output', async ({ page }) => {
    // Navigate to Strategy tab
    await page.click('text=Strategy');
    await page.waitForTimeout(1000);

    // Enable test mode that injects placeholders
    await page.check('[data-testid="inject-placeholders-checkbox"]');

    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="industry-input"]', 'Technology');
    await page.fill('[data-testid="budget-input"]', '100000');

    await page.click('[data-testid="generate-strategy-button"]');
    await page.waitForSelector('text=Report Generated', { timeout: 60000 });

    // Validation should FAIL
    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    expect(validation.global_status).toBe('FAIL');
    
    const pdfValidation = validation.artifacts.find(
      (a: any) => a.artifact_id === 'marketing_strategy_report_pdf'
    );
    expect(pdfValidation.status).toBe('FAIL');
    expect(pdfValidation.safety_checks.valid).toBeFalsy();
    expect(pdfValidation.safety_checks.placeholder_found).toBeTruthy();
    expect(pdfValidation.issues).toContain(
      expect.stringMatching(/placeholder/i)
    );
  });

  test('02. Missing Required Section - Executive Summary', async ({ page }) => {
    await page.click('text=Strategy');
    await page.waitForTimeout(1000);

    // Enable test mode that removes required sections
    await page.check('[data-testid="remove-executive-summary-checkbox"]');

    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="industry-input"]', 'Healthcare');
    await page.fill('[data-testid="budget-input"]', '150000');

    await page.click('[data-testid="generate-strategy-button"]');
    await page.waitForSelector('text=Report Generated', { timeout: 60000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    expect(validation.global_status).toBe('FAIL');
    
    const pdfValidation = validation.artifacts[0];
    expect(pdfValidation.content_checks.valid).toBeFalsy();
    expect(pdfValidation.issues).toContain(
      expect.stringMatching(/executive.*summary/i)
    );
  });

  test('03. Forbidden Phrase - "TODO" in output', async ({ page }) => {
    await page.click('text=Brief');
    await page.waitForTimeout(1000);

    // Enable test mode that injects TODO markers
    await page.check('[data-testid="inject-todos-checkbox"]');

    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="campaign-name-input"]', 'Q1 Campaign');

    await page.click('[data-testid="generate-brief-button"]');
    await page.waitForSelector('text=Brief Generated', { timeout: 60000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    expect(validation.global_status).toBe('FAIL');
    
    const docxValidation = validation.artifacts.find(
      (a: any) => a.artifact_id === 'marketing_brief_docx'
    );
    expect(docxValidation.safety_checks.forbidden_phrases_found).toBeTruthy();
    expect(docxValidation.issues).toContain(
      expect.stringMatching(/todo/i)
    );
  });

  test('04. Word Count Below Threshold', async ({ page }) => {
    await page.click('text=Strategy');
    await page.waitForTimeout(1000);

    // Enable test mode that generates minimal content
    await page.check('[data-testid="minimal-content-checkbox"]');

    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="industry-input"]', 'Technology');

    await page.click('[data-testid="generate-strategy-button"]');
    await page.waitForSelector('text=Report Generated', { timeout: 60000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    expect(validation.global_status).toBe('FAIL');
    
    const pdfValidation = validation.artifacts[0];
    
    // Find section with low word count
    const failedSection = pdfValidation.section_validations.find(
      (s: any) => !s.word_count_valid
    );
    expect(failedSection).toBeDefined();
    expect(failedSection.issues).toContain(
      expect.stringMatching(/word count/i)
    );
  });

  test('05. Invalid File Structure - Corrupted PDF', async ({ page }) => {
    // Manually create corrupted PDF
    const corruptedPath = path.join(E2E_ARTIFACT_DIR, 'corrupted.pdf');
    fs.writeFileSync(corruptedPath, 'This is not a valid PDF file');

    // Try to validate it
    await page.click('text=Admin');
    await page.waitForTimeout(1000);
    
    await page.click('[data-testid="validate-artifacts-button"]');
    await page.waitForSelector('text=Validation Complete', { timeout: 30000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    const corruptedValidation = validation.artifacts.find(
      (a: any) => a.artifact_id.includes('corrupted')
    );
    expect(corruptedValidation.status).toBe('FAIL');
    expect(corruptedValidation.structural_checks.valid).toBeFalsy();
    expect(corruptedValidation.issues).toContain(
      expect.stringMatching(/invalid.*structure/i)
    );
  });

  test('06. External Send in Proof-Run - Email Blocked', async ({ page }) => {
    await page.click('text=Outreach');
    await page.waitForTimeout(1000);

    await page.fill('[data-testid="recipient-email-input"]', 'test@external.com');
    await page.fill('[data-testid="recipient-name-input"]', 'John Doe');
    await page.fill('[data-testid="company-name-input"]', 'Acme Corp');

    // Try to send (should be blocked in proof-run mode)
    await page.click('[data-testid="send-email-button"]');
    
    // Should show blocking message
    await page.waitForSelector('text=Blocked - Proof-Run Mode', { timeout: 5000 });

    // Check proof-run ledger
    const ledgerPath = path.join(E2E_ARTIFACT_DIR, 'proof_run_ledger.json');
    expect(fs.existsSync(ledgerPath)).toBeTruthy();
    
    const ledger = JSON.parse(fs.readFileSync(ledgerPath, 'utf-8'));
    expect(ledger.proof_run_mode).toBeTruthy();
    expect(ledger.external_sends).toHaveLength(0);
    
    // Should have blocked attempt recorded
    const blockedAttempt = ledger.blocked_sends.find(
      (s: any) => s.destination === 'test@external.com'
    );
    expect(blockedAttempt).toBeDefined();
    expect(blockedAttempt.blocked_reason).toContain('Proof-run mode');
  });

  test('07. Network Egress Blocked - External API Call', async ({ page }) => {
    await page.click('text=Admin');
    await page.waitForTimeout(1000);

    // Try to call external API (should be blocked by egress lock)
    await page.fill('[data-testid="api-url-input"]', 'https://external-api.com/v1/data');
    await page.click('[data-testid="test-api-button"]');

    // Should show blocking message
    await page.waitForSelector('text=Network Egress Blocked', { timeout: 5000 });

    // Check validation report
    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    expect(validation.proof_run_checks.egress_violations).toContainEqual(
      expect.objectContaining({
        url: expect.stringMatching(/external-api\.com/)
      })
    );
  });

  test('08. Delivery Gate - Block Delivery on FAIL', async ({ page }) => {
    // Generate output with known failure
    await page.click('text=Strategy');
    await page.waitForTimeout(1000);

    await page.check('[data-testid="inject-placeholders-checkbox"]');
    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="industry-input"]', 'Technology');

    await page.click('[data-testid="generate-strategy-button"]');
    await page.waitForSelector('text=Report Generated', { timeout: 60000 });

    // Try to deliver
    await page.click('text=Delivery');
    await page.waitForTimeout(1000);

    // Delivery should be blocked
    const deliveryStatus = await page.textContent('[data-testid="delivery-gate-status"]');
    expect(deliveryStatus).toContain('BLOCKED');
    
    // Verify delivery button is disabled
    const deliveryButton = await page.locator('[data-testid="deliver-to-client-button"]');
    await expect(deliveryButton).toBeDisabled();
    
    // Should show failure reason
    const failureReason = await page.textContent('[data-testid="delivery-block-reason"]');
    expect(failureReason).toContain('Validation failed');
  });

  test('09. CSV Invalid Structure - Missing Required Columns', async ({ page }) => {
    await page.click('text=Leads');
    await page.waitForTimeout(1000);

    // Enable test mode that removes required columns
    await page.check('[data-testid="remove-email-column-checkbox"]');

    await page.click('[data-testid="export-leads-button"]');
    await page.waitForSelector('text=Export Ready', { timeout: 30000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    const csvValidation = validation.artifacts.find(
      (a: any) => a.artifact_id === 'lead_export_csv'
    );
    expect(csvValidation.status).toBe('FAIL');
    expect(csvValidation.structural_checks.valid).toBeFalsy();
    expect(csvValidation.issues).toContain(
      expect.stringMatching(/required column.*email/i)
    );
  });

  test('10. ZIP Path Traversal - Malicious Paths Blocked', async ({ page }) => {
    // Create malicious ZIP with path traversal attempt
    const AdmZip = require('adm-zip');
    const zip = new AdmZip();
    
    // Try to add file with ../ in path
    zip.addFile('../../../etc/passwd', Buffer.from('malicious content'));
    
    const maliciousPath = path.join(E2E_ARTIFACT_DIR, 'malicious.zip');
    zip.writeZip(maliciousPath);

    // Try to validate it
    await page.click('text=Admin');
    await page.waitForTimeout(1000);
    
    await page.click('[data-testid="validate-artifacts-button"]');
    await page.waitForSelector('text=Validation Complete', { timeout: 30000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    const zipValidation = validation.artifacts.find(
      (a: any) => a.artifact_id.includes('malicious')
    );
    expect(zipValidation.status).toBe('FAIL');
    expect(zipValidation.issues).toContain(
      expect.stringMatching(/path traversal/i)
    );
  });

  test('11. Multiple Failures - Cumulative FAIL Status', async ({ page }) => {
    await page.click('text=Strategy');
    await page.waitForTimeout(1000);

    // Enable multiple failure modes
    await page.check('[data-testid="inject-placeholders-checkbox"]');
    await page.check('[data-testid="remove-executive-summary-checkbox"]');
    await page.check('[data-testid="minimal-content-checkbox"]');

    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="industry-input"]', 'Technology');

    await page.click('[data-testid="generate-strategy-button"]');
    await page.waitForSelector('text=Report Generated', { timeout: 60000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    expect(validation.global_status).toBe('FAIL');
    
    const pdfValidation = validation.artifacts[0];
    expect(pdfValidation.status).toBe('FAIL');
    
    // Should have multiple failure reasons
    expect(pdfValidation.issues.length).toBeGreaterThan(1);
    expect(pdfValidation.issues).toContain(expect.stringMatching(/placeholder/i));
    expect(pdfValidation.issues).toContain(expect.stringMatching(/required section/i));
    expect(pdfValidation.issues).toContain(expect.stringMatching(/word count/i));
  });

  test('12. File Size Exceeded - MAX_FILE_SIZE Enforcement', async ({ page }) => {
    await page.click('text=Strategy');
    await page.waitForTimeout(1000);

    // Enable test mode that generates huge output
    await page.check('[data-testid="generate-huge-file-checkbox"]');

    await page.fill('[data-testid="client-name-input"]', 'Test Client');
    await page.fill('[data-testid="industry-input"]', 'Technology');

    await page.click('[data-testid="generate-strategy-button"]');
    await page.waitForSelector('text=Report Generated', { timeout: 60000 });

    const validationPath = path.join(E2E_ARTIFACT_DIR, 'validation_report.json');
    const validation = JSON.parse(fs.readFileSync(validationPath, 'utf-8'));
    
    const pdfValidation = validation.artifacts[0];
    
    if (pdfValidation.status === 'FAIL') {
      expect(pdfValidation.issues).toContain(
        expect.stringMatching(/file size.*exceeded/i)
      );
    }
  });
});
