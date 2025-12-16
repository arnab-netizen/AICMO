"""Onboarding module - Internal adapters (MVP + DB persistence)."""
from datetime import datetime, timezone
from typing import Dict, Protocol
from aicmo.onboarding.api.ports import BriefNormalizePort, IntakeCapturePort, OnboardingQueryPort
from aicmo.onboarding.api.dtos import (
    IntakeFormDTO,
    DiscoveryNotesDTO,
    NormalizedBriefDTO,
    ScopeDTO,
    OnboardingStatusDTO,
)
from aicmo.shared.ids import ClientId, BriefId


# ============================================================================
# Repository Protocol (allows both inmemory and DB implementations)
# ============================================================================

class BriefRepository(Protocol):
    """Repository interface for brief persistence."""
    
    def save_brief(self, brief: NormalizedBriefDTO) -> None:
        """Save a normalized brief."""
        ...
    
    def get_brief(self, brief_id: BriefId) -> NormalizedBriefDTO | None:
        """Retrieve a brief by ID."""
        ...
    
    def save_intake(self, brief_id: BriefId, intake: IntakeFormDTO) -> None:
        """Save intake form data."""
        ...


# ============================================================================
# In-Memory Repository (original, no DB)
# ============================================================================

class InMemoryBriefRepo:
    """In-memory storage for briefs (Phase 3 - no DB tables)."""
    
    def __init__(self):
        self._briefs: Dict[BriefId, NormalizedBriefDTO] = {}
        self._intake_forms: Dict[BriefId, IntakeFormDTO] = {}
    
    def save_brief(self, brief: NormalizedBriefDTO) -> None:
        self._briefs[brief.brief_id] = brief
    
    def get_brief(self, brief_id: BriefId) -> NormalizedBriefDTO | None:
        return self._briefs.get(brief_id)
    
    def save_intake(self, brief_id: BriefId, intake: IntakeFormDTO) -> None:
        self._intake_forms[brief_id] = intake


# ============================================================================
# Database Repository (Phase 4 Lane B - real persistence)
# ============================================================================

class DatabaseBriefRepo:
    """Database storage for briefs using SQLAlchemy."""
    
    def __init__(self):
        # Import DB models and session here to avoid circular imports
        from aicmo.onboarding.internal.models import BriefDB, IntakeDB
        from aicmo.core.db import get_session
        
        self._BriefDB = BriefDB
        self._IntakeDB = IntakeDB
        self._get_session = get_session
    
    def save_brief(self, brief: NormalizedBriefDTO) -> None:
        """Save brief to database."""
        with self._get_session() as session:
            brief_db = self._BriefDB(
                id=brief.brief_id,
                client_id=brief.client_id,
                deliverables=brief.scope.deliverables,
                exclusions=brief.scope.exclusions,
                timeline_weeks=str(brief.scope.timeline_weeks) if brief.scope.timeline_weeks else None,
                objectives=brief.objectives,
                target_audience=brief.target_audience,
                brand_guidelines=brief.brand_guidelines,
                metadata={},  # Can be extended later
                normalized_at=brief.normalized_at,
                created_at=brief.normalized_at,  # Use normalized_at as created_at
                updated_at=datetime.now(timezone.utc),
            )
            session.merge(brief_db)  # Use merge to handle updates
            session.commit()
    
    def get_brief(self, brief_id: BriefId) -> NormalizedBriefDTO | None:
        """Retrieve brief from database."""
        with self._get_session() as session:
            brief_db = session.query(self._BriefDB).filter_by(id=brief_id).first()
            if not brief_db:
                return None
            
            return self._to_dto(brief_db)
    
    def save_intake(self, brief_id: BriefId, intake: IntakeFormDTO) -> None:
        """Save intake form to database."""
        import uuid
        
        with self._get_session() as session:
            intake_db = self._IntakeDB(
                id=str(uuid.uuid4()),
                brief_id=brief_id,
                client_id="client_mvp",  # TODO: Get from intake or context
                responses=intake.responses,
                attachments=[],
                submitted_at=intake.submitted_at,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(intake_db)
            session.commit()
    
    def _to_dto(self, brief_db) -> NormalizedBriefDTO:
        """Convert DB model to DTO."""
        # Ensure timezone awareness (SQLite may drop tzinfo)
        normalized_at = brief_db.normalized_at
        if normalized_at and normalized_at.tzinfo is None:
            normalized_at = normalized_at.replace(tzinfo=timezone.utc)
        
        return NormalizedBriefDTO(
            brief_id=brief_db.id,
            client_id=brief_db.client_id,
            scope=ScopeDTO(
                deliverables=brief_db.deliverables or [],
                exclusions=brief_db.exclusions or [],
                timeline_weeks=int(brief_db.timeline_weeks) if brief_db.timeline_weeks and brief_db.timeline_weeks.isdigit() else None,
            ),
            objectives=brief_db.objectives or [],
            target_audience=brief_db.target_audience,
            brand_guidelines=brief_db.brand_guidelines or {},
            normalized_at=normalized_at,
        )


# ============================================================================
# Port Adapters (use repository via dependency injection)
# ============================================================================

class BriefNormalizeAdapter(BriefNormalizePort):
    """Minimal brief normalization adapter."""
    
    def __init__(self, repo: BriefRepository):
        self._repo = repo
    
    def normalize_brief(
        self, brief_id: BriefId, discovery_notes: DiscoveryNotesDTO
    ) -> NormalizedBriefDTO:
        """
        Convert intake + discovery into normalized brief.
        
        MVP: Simple extraction from notes, no complex validation.
        """
        # Extract scope from discovery notes (minimal parsing)
        deliverables = ["Content Strategy", "Social Media Pack", "Email Campaign"]
        
        brief = NormalizedBriefDTO(
            brief_id=brief_id,
            client_id=ClientId("client_mvp"),
            scope=ScopeDTO(
                deliverables=deliverables,
                exclusions=[],
                timeline_weeks=8,
            ),
            objectives=["Increase brand awareness", "Drive conversions"],
            target_audience="B2B decision makers",
            brand_guidelines={"tone": "professional", "colors": ["blue", "white"]},
            normalized_at=datetime.now(timezone.utc),
        )
        
        self._repo.save_brief(brief)
        return brief


class IntakeCaptureAdapter(IntakeCapturePort):
    """Minimal intake capture adapter."""
    
    def __init__(self, repo: BriefRepository):
        self._repo = repo
    
    def capture_intake(self, client_id: ClientId, form_data: IntakeFormDTO) -> BriefId:
        """Store intake form and return brief ID."""
        brief_id = BriefId(f"brief_{client_id}_{int(datetime.now(timezone.utc).timestamp())}")
        self._repo.save_intake(brief_id, form_data)
        return brief_id


class OnboardingQueryAdapter(OnboardingQueryPort):
    """Minimal query adapter."""
    
    def __init__(self, repo: BriefRepository):
        self._repo = repo
    
    def get_onboarding_status(self, client_id: ClientId) -> OnboardingStatusDTO:
        """Get onboarding status (MVP: always returns complete)."""
        return OnboardingStatusDTO(
            client_id=client_id,
            stage="COMPLETE",
            intake_complete=True,
            brief_validated=True,
            workspace_created=True,
        )

