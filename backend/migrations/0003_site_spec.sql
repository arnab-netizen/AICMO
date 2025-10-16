-- create page and site_section tables and a materialized site_spec view
CREATE TABLE IF NOT EXISTS page (
  id BIGSERIAL PRIMARY KEY,
  site_id BIGINT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  title TEXT,
  seo JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS site_section (
  id BIGSERIAL PRIMARY KEY,
  site_id BIGINT NOT NULL REFERENCES site(id) ON DELETE CASCADE,
  "type" TEXT NOT NULL,
  props JSONB,
  "order" INTEGER DEFAULT 0
);

-- simple site_spec view that aggregates pages and sections into JSON
CREATE OR REPLACE VIEW site_spec AS
SELECT
  s.slug,
  COALESCE((SELECT json_agg(json_build_object('id', p.id, 'path', p.path, 'title', p.title, 'seo', p.seo)) FROM page p WHERE p.site_id = s.id), '[]'::json) AS pages,
  COALESCE((SELECT json_agg(json_build_object('id', ss.id, 'type', ss."type", 'props', ss.props, 'order', ss."order")) FROM site_section ss WHERE ss.site_id = s.id), '[]'::json) AS sections
FROM site s;
