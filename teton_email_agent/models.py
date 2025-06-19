"""
Data models for the email agent
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    REPLY = "reply"
    SCHEDULE_MEETING = "schedule_meeting"
    ARCHIVE = "archive"
    FLAG_URGENT = "flag_urgent"


class EmailContent(BaseModel):
    sender: str
    subject: str
    body: str
    message_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        extra = "allow"


class AgentDecision(BaseModel):
    action_type: ActionType
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    email_id: str
    understanding: str
    decision: AgentDecision
    execution_result: Optional[str] = None
    execution_time: Optional[float] = None


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0
