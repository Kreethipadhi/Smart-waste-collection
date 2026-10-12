from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.database import db


class BaseAgent(ABC):
    """
    Base class for all autonomous AI agents in the Smart Waste System.
    Provides standardized logging, inter-agent communication, and state mutation.
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def log(self, action: str, details: Dict[str, Any], level: str = "INFO"):
        """Records agent activity to system database and state log."""
        entry = db.log_agent_action(self.name, action, details, level=level)
        return entry

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's core decision logic on the shared workflow state.
        Must return the updated state dictionary.
        """
        pass
