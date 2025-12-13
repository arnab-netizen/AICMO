"""Client Review - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.client_review.api.dtos import ReviewPackageDTO, ClientFeedbackDTO, RevisionPlanDTO
from aicmo.shared.ids import DraftId, ReviewPackageId

class ClientReviewRequestPort(ABC):
    @abstractmethod
    def create_review_package(self, draft_id: DraftId) -> ReviewPackageDTO:
        pass

class FeedbackCapturePort(ABC):
    @abstractmethod
    def capture_feedback(self, package_id: ReviewPackageId, feedback: ClientFeedbackDTO) -> None:
        pass

class RevisionPlanPort(ABC):
    @abstractmethod
    def create_revision_plan(self, package_id: ReviewPackageId) -> RevisionPlanDTO:
        pass

class ClientReviewQueryPort(ABC):
    @abstractmethod
    def get_package(self, package_id: ReviewPackageId) -> ReviewPackageDTO:
        pass

__all__ = ["ClientReviewRequestPort", "FeedbackCapturePort", "RevisionPlanPort", "ClientReviewQueryPort"]
