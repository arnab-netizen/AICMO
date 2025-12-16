# AICMO Persistence Conventions

**Document Purpose**: Establish consistent patterns for database persistence across all AICMO business modules.

**Status**: Phase 4 Lane B - Active  
**Date**: December 13, 2025  
**Authority**: Binding for all module persistence implementations

---

## 1. Base & ORM Framework

### SQLAlchemy Base
- **Single Base**: Use `aicmo.core.db.Base` (wraps `backend.db.base.Base`)
- **No Custom Base Classes**: All models inherit directly from Base
- **Import Pattern**:
  ```python
  from aicmo.core.db import Base
  
  class MyEntityDB(Base):
      __tablename__ = "my_entities"
  ```

### SQLAlchemy Version
- **Version**: 2.0.45
- **Style**: Use 2.0 style (no legacy 1.x patterns)
- **Async**: Not required for Lane B (sync session management)

---

## 2. Table Naming Conventions

### Business Module Tables
All business entity tables use singular snake_case with module prefix:

| Module | Table Naming Pattern | Example |
|--------|---------------------|---------|
| Onboarding | `onboarding_{entity}` | `onboarding_brief`, `onboarding_intake` |
| Strategy | `strategy_{entity}` | `strategy_document`, `strategy_approval` |
| Production | `production_{entity}` | `production_asset`, `production_draft` |
| QC | `qc_{entity}` | `qc_evaluation`, `qc_result` |
| Delivery | `delivery_{entity}` | `delivery_job`, `delivery_package` |

### CAM Tables (Already Exist)
CAM tables do NOT follow the prefix pattern (legacy compatibility):
- `campaigns`, `leads`, `outreach_attempts`, etc.
- **Rule**: Do NOT rename CAM tables in Lane B

---

## 3. Primary Key Strategy

### ID Column Standard
```python
from sqlalchemy import Column, String
from aicmo.core.db import Base

class EntityDB(Base):
    __tablename__ = "module_entity"
    
    id = Column(String, primary_key=True)  # UUID stored as string
```

### ID Generation
- **Format**: UUID4 as string
- **Generation**: Application layer (domain models, not DB defaults)
- **Pattern**:
  ```python
  import uuid
  
  entity_id = str(uuid.uuid4())
  ```

### Why String IDs?
- Cross-module references don't need foreign keys (decoupled modules)
- Consistent with existing CAM patterns
- Simple, portable, no DB-specific UUID types

---

## 4. Timestamps

### Standard Timestamp Columns
All entities MUST include:
```python
from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone

class EntityDB(Base):
    __tablename__ = "module_entity"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

### Timestamp Rules
- **Timezone**: Always use `timezone=True` and UTC
- **Default**: Use Python `default=lambda: datetime.now(timezone.utc)`, NOT `server_default`
- **Update**: Use `onupdate` for `updated_at`
- **Why**: Application-controlled timestamps, testable, consistent

---

## 5. JSON Columns

### Use JSON for Embedded Data
For complex nested data (like QC results, package contents):
```python
from sqlalchemy import Column, String, JSON

class EntityDB(Base):
    __tablename__ = "module_entity"
    
    id = Column(String, primary_key=True)
    metadata_ = Column("metadata", JSON, nullable=False, default=dict)
```

### JSON Column Rules
- **Type**: Use `JSON` type (SQLAlchemy handles DB differences)
- **Default**: Use `default=dict` or `default=list` for empty collections
- **Naming**: If column name conflicts with Python keyword, use trailing underscore + `name` parameter

---

## 6. Relationships & Foreign Keys

### Cross-Module References
**RULE**: Business modules do NOT use SQLAlchemy relationships or foreign keys for cross-module references.

❌ **Wrong**:
```python
# onboarding_brief table with FK to campaigns table
brief_id = Column(String, ForeignKey("campaigns.id"))
campaign = relationship("CampaignDB")
```

✅ **Correct**:
```python
# onboarding_brief table stores campaign_id as string (no FK)
campaign_id = Column(String, nullable=False)
```

### Why No Cross-Module FKs?
- Modules are bounded contexts (decoupled)
- CAM may be in different DB in future
- Referential integrity enforced by workflow/saga, not DB

### Same-Module Relationships
Within a module, relationships ARE allowed:
```python
# production_draft has FK to production_asset (same module)
asset_id = Column(String, ForeignKey("production_asset.id"), nullable=False)
asset = relationship("ProductionAssetDB")
```

---

## 7. Enum Columns

### Store Enums as Strings
```python
from sqlalchemy import Column, String, Enum as SQLEnum
from enum import Enum

class Status(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class EntityDB(Base):
    __tablename__ = "module_entity"
    
    id = Column(String, primary_key=True)
    status = Column(String, nullable=False)  # Store as string, not SQLEnum
```

### Enum Rules
- **Type**: Use `String` column, NOT `SQLEnum`
- **Validation**: Enforce enum validity in domain model, not DB
- **Why**: Portable, no DB-specific enum types, simpler migrations

---

## 8. Session Management

### Use Existing Session Factories
```python
from aicmo.core.db import get_session, SessionLocal

# Option 1: Context manager (preferred)
with get_session() as session:
    session.add(entity_db)
    session.commit()

# Option 2: Direct SessionLocal (for custom lifecycle)
session = SessionLocal()
try:
    session.add(entity_db)
    session.commit()
finally:
    session.close()
```

### Session Rules
- **No Engine Creation**: Never call `create_engine()` in modules
- **No SessionMaker Creation**: Use `aicmo.core.db.SessionLocal`
- **Transactions**: Use session context managers for automatic rollback

---

## 9. Repository Pattern

### Repository Structure
Each module's persistence adapter implements:
```python
from aicmo.core.db import get_session, Base

class EntityRepository:
    def save(self, entity: EntityDomain) -> None:
        with get_session() as session:
            entity_db = EntityDB(
                id=entity.id,
                field1=entity.field1,
                # ... map domain to DB model
            )
            session.add(entity_db)
            session.commit()
    
    def get_by_id(self, entity_id: str) -> EntityDomain | None:
        with get_session() as session:
            entity_db = session.query(EntityDB).filter_by(id=entity_id).first()
            if not entity_db:
                return None
            return self._to_domain(entity_db)
    
    def _to_domain(self, entity_db: EntityDB) -> EntityDomain:
        return EntityDomain(
            id=entity_db.id,
            field1=entity_db.field1,
            # ... map DB to domain model
        )
```

### Repository Rules
- **Location**: In `module/internal/adapters.py` (implementation detail)
- **No ORM Leakage**: DB models never escape repository boundary
- **Mapping**: Always map DB models ↔ domain models explicitly
- **Session Scope**: Open session per operation (no long-lived sessions)

---

## 10. Dual-Mode Support

### Environment Variable
```bash
export AICMO_PERSISTENCE_MODE=db      # Use real database
export AICMO_PERSISTENCE_MODE=inmemory # Use in-memory (default)
```

### Configuration Integration
```python
from pydantic_settings import BaseSettings

class AicmoSettings(BaseSettings):
    persistence_mode: str = "inmemory"  # or "db"
    
    class Config:
        env_prefix = "AICMO_"
```

### Adapter Selection
```python
# In composition root
settings = AicmoSettings()

if settings.persistence_mode == "db":
    repo = EntityDatabaseRepository()
else:
    repo = EntityInMemoryRepository()
```

### Dual-Mode Rules
- **Default**: `inmemory` (no DB required for tests)
- **Tests**: ALL tests pass in both modes
- **Determinism**: Both modes produce identical workflow results
- **No Conditionals in Business Logic**: Mode selection happens at composition time

---

## 11. Migration Strategy

### Alembic Integration
- **Tool**: Use existing Alembic configuration (`alembic.ini`, `db/alembic/env.py`)
- **Autogenerate**: Use `alembic revision --autogenerate -m "description"`
- **Migration Location**: `db/alembic/versions/`

### Migration Workflow
```bash
# 1. Create DB models in module/internal/models.py
# 2. Import models in db/alembic/env.py (for autogenerate detection)
# 3. Generate migration
alembic revision --autogenerate -m "add_onboarding_brief_table"

# 4. Review generated migration (edit if needed)
# 5. Apply migration
alembic upgrade head
```

### Migration Rules
- **One Module at a Time**: Each module gets its own migration(s)
- **Review Autogenerate**: Always check generated SQL before applying
- **Backwards Compatible**: Avoid breaking changes when possible
- **Test Migrations**: Run `alembic upgrade head` in test environment first

---

## 12. Testing Conventions

### Test Database Setup
```python
# In conftest.py or test fixtures
from aicmo.core.db import Base, SessionLocal
from sqlalchemy import create_engine

@pytest.fixture(scope="function")
def db_session():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    session = SessionLocal(bind=engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
```

### Test Rules
- **Isolation**: Each test gets fresh DB (function scope)
- **In-Memory**: Tests use SQLite in-memory (fast, no cleanup)
- **Both Modes**: Critical tests run in both `inmemory` and `db` modes
- **No Mocking ORM**: Test with real SQLAlchemy session

---

## 13. File Organization

### DB Models Location
```
aicmo/
└── {module}/
    └── internal/
        ├── models.py         # DB models (EntityDB classes)
        └── adapters.py       # Repository implementations
```

### Import Rules
- **DB Models**: `from aicmo.{module}.internal.models import EntityDB`
- **Base**: `from aicmo.core.db import Base`
- **Session**: `from aicmo.core.db import get_session, SessionLocal`

### What Goes Where
- **models.py**: SQLAlchemy model classes only
- **adapters.py**: Repository classes (save/load logic)
- **domain models**: Stay in `aicmo/{module}/domain.py` (no DB awareness)

---

## 14. Anti-Patterns to Avoid

### ❌ Active Record Pattern
```python
# Don't do this
class EntityDB(Base):
    def save_self(self):
        session.add(self)
        session.commit()
```

### ❌ ORM Leakage
```python
# Don't return DB models from ports
def get_entity(entity_id: str) -> EntityDB:  # ❌ Wrong
    ...

def get_entity(entity_id: str) -> EntityDomain:  # ✅ Correct
    ...
```

### ❌ Lazy Loading Surprises
```python
# Don't rely on lazy loading outside session
entity_db = session.query(EntityDB).first()
session.close()
related = entity_db.related_items  # ❌ Will fail
```

### ❌ DB-Specific Functions
```python
# Don't use DB-specific functions in models
created_at = Column(DateTime, server_default=func.now())  # ❌ Not portable
```

---

## 15. Compliance Checklist

Before completing module persistence implementation:

- [ ] Table name follows `{module}_{entity}` convention
- [ ] Primary key is `id = Column(String, primary_key=True)`
- [ ] `created_at` and `updated_at` timestamps present
- [ ] No cross-module foreign keys
- [ ] DB models in `{module}/internal/models.py`
- [ ] Repository in `{module}/internal/adapters.py`
- [ ] No ORM types in domain models or ports
- [ ] Tests pass in both `inmemory` and `db` modes
- [ ] Migration created and applied successfully
- [ ] Documentation updated if new patterns introduced

---

## References

- SQLAlchemy 2.0 Docs: https://docs.sqlalchemy.org/en/20/
- Alembic Tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Existing Base: [aicmo/core/db.py](../aicmo/core/db.py)
- CAM Models Example: [aicmo/cam/db_models.py](../aicmo/cam/db_models.py)

---

**End of Document**
