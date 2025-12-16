#!/usr/bin/env python3
"""DEPRECATED_AOL_RUNNER

This is a dev/integration testing runner for the AOL (Autonomy Orchestration Layer) daemon.

**Production deployment must use: scripts/run_aol_worker.py**

Rationale:
- run_aol_daemon.py has --ticks flag (not suitable for production)
- run_aol_daemon.py is used for integration testing only
- RUNBOOK_RENDER_STREAMLIT.md:74 specifies: python scripts/run_aol_worker.py

This file is retained for historical reference only.
If run directly, raises RuntimeError to prevent accidental deployment.
"""

import sys

raise RuntimeError(
    "DEPRECATED_AOL_RUNNER: scripts/run_aol_daemon.py is dev-only code. "
    "Use 'python scripts/run_aol_worker.py' for production. "
    "See RUNBOOK_RENDER_STREAMLIT.md:74 for details."
)

sys.exit(1)
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from aicmo.orchestration.daemon import AOLDaemon
from aicmo.orchestration.models import AOLControlFlags
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def main():
    parser = argparse.ArgumentParser(description="Run AICMO Autonomy Orchestration Layer daemon")
    parser.add_argument(
        "--ticks",
        type=int,
        default=None,
        help="Max ticks to run (None = run forever)",
    )
    parser.add_argument(
        "--proof",
        action="store_true",
        help="Initialize in PROOF mode (artifacts only, no real execution)",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "sqlite:////tmp/aol.db"),
        help="Database URL (default: DATABASE_URL env or sqlite:////tmp/aol.db)",
    )
    
    args = parser.parse_args()
    
    # Ensure database exists and initialize tables
    try:
        engine = create_engine(args.db_url, future=True)
        
        # Create all tables
        from aicmo.orchestration.models import Base
        Base.metadata.create_all(engine)
        
        # Initialize control flags if needed
        session_maker = sessionmaker(bind=engine)
        session = session_maker()
        stmt = select(AOLControlFlags).limit(1)
        flags = session.execute(stmt).scalar_one_or_none()
        
        if not flags:
            flags = AOLControlFlags(
                paused=False,
                killed=False,
                proof_mode=args.proof,
            )
            session.add(flags)
            session.commit()
        elif args.proof:
            flags.proof_mode = True
            session.commit()
        
        session.close()
        
        print(f"[AOL] Database initialized: {args.db_url}")
        print(f"[AOL] PROOF mode: {args.proof}")
        print(f"[AOL] Max ticks: {args.ticks or 'unlimited'}")
        
    except Exception as e:
        print(f"[AOL] Failed to initialize database: {str(e)}", file=sys.stderr)
        return 1
    
    # Run daemon
    daemon = AOLDaemon(args.db_url)
    exit_code = daemon.run(max_ticks=args.ticks)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
