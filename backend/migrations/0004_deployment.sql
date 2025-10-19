-- 0004_deployment.sql
CREATE TABLE IF NOT EXISTS deployment (
  id SERIAL PRIMARY KEY,
  site_id INT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_deployment_site_created
  ON deployment(site_id, created_at DESC);
