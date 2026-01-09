"""API package"""

from .projects import router as projects_router
from .tasks import router as tasks_router
from .change_requests import router as change_requests_router
from .artifacts import router as artifacts_router

__all__ = ["projects_router", "tasks_router", "change_requests_router", "artifacts_router"]
