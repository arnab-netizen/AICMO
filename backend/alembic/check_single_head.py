import os
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory

cfg = Config(os.getenv("ALEMBIC_CONFIG", "backend/alembic.ini"))
script = ScriptDirectory.from_config(cfg)
heads = list(script.get_heads())

if len(heads) != 1:
    print("ERROR: Alembic has multiple heads:", heads)
    for rev in heads:
        rev_obj = script.get_revision(rev)
        print(f"- {rev_obj.revision} '{rev_obj.docstring or ''}'")
    sys.exit(1)

print(f"OK: single Alembic head → {heads[0]}")
