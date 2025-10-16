-- Minimal seed demo SQL
INSERT INTO site (slug, title) VALUES ('founder-os', 'Founder-OS') ON CONFLICT (slug) DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM site_section WHERE site_id = (SELECT id FROM site WHERE slug='founder-os') LIMIT 1) THEN
    INSERT INTO site_section (site_id, "type", props, "order")
    VALUES ((SELECT id FROM site WHERE slug='founder-os'), 'hero', '{"headline":"Ship faster"}', 1);
  END IF;
END$$;
