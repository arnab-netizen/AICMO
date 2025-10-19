-- Runs: seconds_used, cost_estimate
ALTER TABLE runs
  ADD COLUMN IF NOT EXISTS seconds_used INT,
  ADD COLUMN IF NOT EXISTS cost_estimate NUMERIC,
  ADD COLUMN IF NOT EXISTS version TEXT;

-- Artifacts: sha256, size_bytes, content_type
ALTER TABLE artifacts
  ADD COLUMN IF NOT EXISTS sha256 TEXT,
  ADD COLUMN IF NOT EXISTS size_bytes INT,
  ADD COLUMN IF NOT EXISTS content_type TEXT;

-- Brand policies for compliance/ban rules + exceptions
CREATE TABLE IF NOT EXISTS brand_policies(
  brand_id UUID PRIMARY KEY,
  rules_json JSONB,
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS brand_exceptions(
  brand_id UUID,
  rule_key TEXT,
  rationale TEXT,
  expires_at timestamptz,
  created_at timestamptz DEFAULT now()
);

-- Optional: module memory (tone embeddings / style prefs)
CREATE TABLE IF NOT EXISTS module_memory (
  id UUID PRIMARY KEY,
  module TEXT,
  key TEXT,
  value_json JSONB,
  updated_at timestamptz DEFAULT now()
);
