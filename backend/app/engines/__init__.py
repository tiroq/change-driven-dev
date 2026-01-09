"""
Engine package for AI assistant adapters.
"""
from .engine_base import (
    EngineBase,
    EngineStatus,
    EngineMessage,
    EngineResponse,
    EngineFactory
)
from .copilot_cli import CopilotCLIEngine

__all__ = [
    "EngineBase",
    "EngineStatus",
    "EngineMessage",
    "EngineResponse",
    "EngineFactory",
    "CopilotCLIEngine"
]
