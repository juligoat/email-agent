"""
Email reply tool
"""

import logging
from typing import Any, Dict

from teton_email_agent.base import BaseTool
from teton_email_agent.models import EmailContent, ToolResult

logger = logging.getLogger(__name__)


class EmailReplyTool(BaseTool):
    """Tool for sending email replies"""

    def __init__(self, gmail_integration=None, settings=None):
        super().__init__(name="reply", description="Send email replies")
        self.gmail_integration = gmail_integration
        self.settings = settings

    async def execute(self, parameters: Dict[str, Any], email: EmailContent) -> ToolResult:
        """Execute email reply"""
        try:
            message = parameters.get("message")
            if not message:
                return ToolResult(tool_name=self.name, success=False, error="No message provided")

            # Whitelist check before sending reply
            if self.settings and not self.settings.is_sender_whitelisted(email.sender):
                logger.warning(f"BLOCKED reply to non-whitelisted sender: {email.sender}")
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Sender {email.sender} not in whitelist - reply blocked",
                )

            # If we have Gmail integration, send actual email
            if self.gmail_integration:
                success = await self.gmail_integration.send_reply(email, message)
                if success:
                    return ToolResult(
                        tool_name=self.name, success=True, result=f"Reply sent to {email.sender}"
                    )
                else:
                    return ToolResult(
                        tool_name=self.name, success=False, error="Failed to send email"
                    )

            # Mock reply for testing
            logger.info(f"Mock reply to {email.sender}: {message[:50]}...")
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
        else:
            return ToolResult(
                tool_name=self.name, success=True, result=f"Mock reply sent to {email.sender}"
            )
