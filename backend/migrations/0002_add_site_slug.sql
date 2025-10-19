-- add slug column to site and populate from name
ALTER TABLE site ADD COLUMN IF NOT EXISTS slug TEXT;
UPDATE site SET slug = lower(regexp_replace(name, '[^a-zA-Z0-9]+', '-', 'g')) WHERE slug IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS site_slug_idx ON site (slug);
