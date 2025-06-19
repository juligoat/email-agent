"""
Base tool class (really simple, for now)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from teton_email_agent.models import EmailContent, ToolResult

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for agent tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], email: EmailContent) -> ToolResult:
        """Execute the tool"""
        pass
