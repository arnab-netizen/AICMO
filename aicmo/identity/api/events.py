"""Identity - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import UserId

class UserAuthenticated(DomainEvent):
    user_id: UserId

class UserLoggedOut(DomainEvent):
    user_id: UserId

__all__ = ["UserAuthenticated", "UserLoggedOut"]
