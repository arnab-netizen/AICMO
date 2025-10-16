import glob
from sqlalchemy import text
from backend.db import ENGINE

def run():
    files = sorted(glob.glob("backend/migrations/*.sql"))
    if not files:
        print("No migrations found.")
        return
    if ENGINE is None:
        print("ENGINE not initialized; cannot run migrations.")
        return
    with ENGINE.begin() as conn:
        for f in files:
            print(f"Applying {f} ...")
            sql = open(f, "r", encoding="utf-8").read()
            for stmt in filter(None, [s.strip() for s in sql.split(";")]):
                conn.execute(text(stmt))
    print("Migrations complete.")

if __name__ == "__main__":
    run()
