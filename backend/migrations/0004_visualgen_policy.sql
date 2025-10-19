-- Track creative templates / safe zones / network masks
CREATE TABLE IF NOT EXISTS creative_templates(
  template_id TEXT PRIMARY KEY,
  size TEXT,
  layout TEXT,
  safe_zones_json JSONB,
  layers_json JSONB
);
