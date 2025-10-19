-- 0005_constraints.sql

-- Ensure each site has at most one page per path ("/", "/about", etc.)
CREATE UNIQUE INDEX IF NOT EXISTS ux_page_site_path ON page(site_id, path);

-- Speed up listing pages by site_id
CREATE INDEX IF NOT EXISTS idx_page_site ON page(site_id);

-- Deployment status lookup by site
CREATE INDEX IF NOT EXISTS idx_deployment_site_status_created
  ON deployment(site_id, status, created_at DESC);
