"""Identity - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.identity.api.dtos import UserDTO, AuthContextDTO, PermissionDTO
from aicmo.shared.ids import UserId

class AuthnPort(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict) -> AuthContextDTO:
        pass

class AuthzPort(ABC):
    @abstractmethod
    def authorize(self, user_id: UserId, resource: str, action: str) -> bool:
        pass

class CurrentUserPort(ABC):
    @abstractmethod
    def get_current_user(self) -> UserDTO:
        pass

__all__ = ["AuthnPort", "AuthzPort", "CurrentUserPort"]
