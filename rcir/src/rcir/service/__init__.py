"""Read-only repository evidence service. No agent execution or release authority."""
from .api import RepositoryService, ServiceError

__all__ = ["RepositoryService", "ServiceError"]
