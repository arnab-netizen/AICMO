CREATE OR REPLACE VIEW site_spec AS
SELECT
  s.id,
  s.slug,
  s.title,
  s.theme,
  s.settings,
  s.status,
  s.created_at,
  s.updated_at,
  (
    SELECT jsonb_agg(
             jsonb_build_object('path', p.path, 'title', p.title, 'seo', p.seo)
             ORDER BY p.path
           )
    FROM page p WHERE p.site_id = s.id
  ) AS pages,
  (
    SELECT jsonb_agg(
             jsonb_build_object('type', ss.type, 'props', ss.props, 'order', ss."order")
             ORDER BY ss."order"
           )
    FROM site_section ss WHERE ss.site_id = s.id
  ) AS sections,
  (
    SELECT jsonb_agg(
             jsonb_build_object('kind', a.kind, 'url', a.url, 'meta', a.meta)
             ORDER BY a.id
           )
    FROM asset a WHERE a.site_id = s.id
  ) AS assets
FROM site s;
