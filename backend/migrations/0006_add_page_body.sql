-- 0006_add_page_body.sql
ALTER TABLE page ADD COLUMN IF NOT EXISTS body TEXT;
