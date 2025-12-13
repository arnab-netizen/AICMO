"""Learning - Events."""
from aicmo.shared.events import DomainEvent

class LearningEventLogged(DomainEvent):
    event_type: str
    context_keys: list[str]

class ArtifactStored(DomainEvent):
    artifact_id: str
    artifact_type: str

__all__ = ["LearningEventLogged", "ArtifactStored"]
