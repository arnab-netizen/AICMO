-- SiteGen base schema
-- Safe UUID helpers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects may exist in another schema; we just store project_id as UUID
CREATE TABLE IF NOT EXISTS site (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL,
  name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS site_spec (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  site_id UUID NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  version INT NOT NULL,
  spec JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Optional: page + asset registries for future enrichment
CREATE TABLE IF NOT EXISTS page (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  site_id UUID NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  title TEXT,
  meta JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (site_id, path)
);

CREATE TABLE IF NOT EXISTS asset (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  site_id UUID NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,          -- image | font | file | etc
  url TEXT NOT NULL,
  meta JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deployment (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  site_id UUID NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,      -- vercel | netlify | gh-pages
  preview_url TEXT,
  prod_url TEXT,
  status TEXT NOT NULL DEFAULT 'created',  -- created|previewed|promoted|failed
  meta JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS site_build (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  site_id UUID NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  workflow_id TEXT NOT NULL,
  run_id TEXT,
  status TEXT NOT NULL DEFAULT 'started',  -- started|running|succeeded|failed
  logs JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_site_spec_site_version ON site_spec(site_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_deployment_site ON deployment(site_id);
CREATE INDEX IF NOT EXISTS idx_build_site ON site_build(site_id);