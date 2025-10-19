from sqlalchemy import text
from backend.db import get_session


def init_views():
    with open("backend/sql/init_views.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    with get_session() as s:
        s.execute(text(sql))
        s.commit()
