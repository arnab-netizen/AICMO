from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from backend.db import get_engine

SEED_SITES = [
    {"name": "Demo Site"},
    {"name": "Founder-OS"},
    {"name": "AOK Kernel"},
]


def main() -> None:
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    with Session.begin() as s:
        # Insert minimal sites if table exists
        try:
            for row in SEED_SITES:
                s.execute(
                    sa.text(
                        """
                    INSERT INTO site (name, slug)
                    VALUES (:name, lower(regexp_replace(:name, '[^a-zA-Z0-9]+', '-', 'g')))
                    ON CONFLICT (slug) DO NOTHING
                """
                    ),
                    {"name": row["name"]},
                )

            # Ensure a simple page and a hero section exist for the founder-os demo site
            s.execute(
                sa.text(
                    """
                INSERT INTO page (site_id, path, title, seo)
                SELECT id, '/', 'Home', jsonb_build_object('title','Founder-OS')
                FROM site
                WHERE slug = 'founder-os' AND NOT EXISTS (
                  SELECT 1 FROM page p WHERE p.site_id = site.id AND p.path = '/'
                )
            """
                )
            )

            s.execute(
                sa.text(
                    """
                INSERT INTO site_section (site_id, "type", props, "order")
                SELECT id, 'hero', jsonb_build_object('headline','Ship faster'), 1
                FROM site
                WHERE slug = 'founder-os' AND NOT EXISTS (
                  SELECT 1 FROM site_section ss WHERE ss.site_id = site.id AND ss."type" = 'hero'
                )
            """
                )
            )
        except Exception as e:
            print("Seed failed:", e)
            raise
    print("✅ Seed complete.")


if __name__ == "__main__":
    main()
