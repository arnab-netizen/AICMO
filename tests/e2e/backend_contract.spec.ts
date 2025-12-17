import { test, expect } from '@playwright/test';

const BACKEND = process.env.AICMO_BACKEND_BASE_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8000';

test.describe('Backend contract', () => {
  test('POST /aicmo/generate for creatives returns non-empty deliverables', async ({ request }) => {
    const payload = { module: 'creatives', brief: { brand_name: 'T', product_service: 'X' } };
    const r = await request.post(`${BACKEND}/aicmo/generate`, { data: payload });
    expect(r.status()).toBe(200);
    const j = await r.json();
    expect(j.status).toBeDefined();
    expect(j.deliverables).toBeDefined();
    expect(Array.isArray(j.deliverables)).toBeTruthy();
    expect(j.deliverables.length).toBeGreaterThan(0);
    for (const d of j.deliverables) expect(d.content_markdown && d.content_markdown.length > 0).toBeTruthy();
  });

  test('POST /aicmo/generate for campaigns returns non-empty deliverables', async ({ request }) => {
    const payload = { module: 'campaigns', brief: { brand_name: 'T', product_service: 'X' } };
    const r = await request.post(`${BACKEND}/aicmo/generate`, { data: payload });
    expect(r.status()).toBe(200);
    const j = await r.json();
    expect(j.status).toBeDefined();
    expect(j.deliverables).toBeDefined();
    expect(Array.isArray(j.deliverables)).toBeTruthy();
    expect(j.deliverables.length).toBeGreaterThan(0);
  });

  test('POST /aicmo/generate for strategy returns non-empty deliverables', async ({ request }) => {
    const payload = { module: 'strategy', brief: { brand_name: 'T', product_service: 'X' } };
    const r = await request.post(`${BACKEND}/aicmo/generate`, { data: payload });
    expect(r.status()).toBe(200);
    const j = await r.json();
    expect(j.status).toBeDefined();
    expect(j.deliverables).toBeDefined();
    expect(Array.isArray(j.deliverables)).toBeTruthy();
    expect(j.deliverables.length).toBeGreaterThan(0);
  });
});
