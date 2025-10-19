# fanout imports for unit-coverage subset
from backend.routers import health as _cov_health  # noqa: F401
from backend import db as _cov_db  # noqa: F401
from backend import models as _cov_models  # noqa: F401
from backend.modules.taste import service as _cov_taste  # noqa: F401
