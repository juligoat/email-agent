"""
Email processing service
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from teton_email_agent.core import EmailAgent
from teton_email_agent.gmail import GmailIntegration
from teton_email_agent.models import EmailContent
from teton_email_agent.reply import EmailReplyTool
from teton_email_agent.settings import Settings

logger = logging.getLogger(__name__)


class AgentNotInitializedError(Exception):
    """Raised when agent is not initialized"""

    pass


class EmailProcessor:
    """Main email processing service"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.agent: Optional[EmailAgent] = None
        self.gmail_integration: Optional[GmailIntegration] = None
        self.monitoring_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the processor"""
        try:
            # Initialize agent
            self.agent = EmailAgent(self.settings)
            logger.info("Agent initialized")

            # Initialize Gmail if configured
            if os.path.exists(self.settings.gmail_credentials_path):
                self.gmail_integration = GmailIntegration(
                    self.settings.gmail_credentials_path, self.settings.gmail_token_path
                )

                if await self.gmail_integration.authenticate():
                    logger.info("Gmail authenticated")
                    # Show whitelist info if configured
                    whitelist = self.settings.get_email_whitelist()
                    if whitelist:
                        logger.info(f"Email whitelist active: {whitelist}")

                    # Start monitoring
                    self.monitoring_task = asyncio.create_task(self._start_monitoring())
                else:
                    logger.warning("Gmail authentication failed")
                    self.gmail_integration = None

            # Register tools
            reply_tool = EmailReplyTool(self.gmail_integration, self.settings)
            self.agent.register_tool(reply_tool)

            logger.info("Email processor initialized")

        except Exception:
            logger.exception("Failed to initialize")
            raise

    async def _start_monitoring(self):
        """Start Gmail monitoring with whitelist check"""
        if not self.gmail_integration:
            return

        async def email_callback(email: EmailContent):
            # WHITELIST CHECK
            if not self.settings.is_sender_whitelisted(email.sender):
                logger.info(f"SKIPPED email from {email.sender} - not in whitelist")
                return

            # Process the email
            logger.info(f"PROCESSING email from {email.sender}: {email.subject}")
            await self.process_email(email)

        await self.gmail_integration.start_monitoring(
            email_callback, self.settings.email_check_interval
        )

    async def process_email(self, email: EmailContent):
        """Process a single email"""
        if not self.agent:
            raise AgentNotInitializedError()

        return await self.agent.process_email(email)

    async def send_test_email(self):
        """Send a test email"""
        if not self.agent:
            raise AgentNotInitializedError()

        test_email = EmailContent(
            sender="test@example.com",
            subject="Test Email",
            body="This is a test email to verify the agent is working correctly.",
            message_id=f"test_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
        )

        result = await self.process_email(test_email)

        return {
            "message": "Test email processed",
            "result": {
                "understanding": result.understanding,
                "action": result.decision.action_type,
                "reasoning": result.decision.reasoning,
                "confidence": result.decision.confidence,
                "execution_result": result.execution_result,
            },
        }

    async def update_configuration(self, updates: dict):
        """Update configuration"""
        if "groq_api_key" in updates:
            self.settings.groq_api_key = updates["groq_api_key"]
            # Reinitialize agent
            await self.initialize()
            return "Agent reinitialized with new API key"
        return "Configuration updated"

    async def cleanup(self):
        """Cleanup resources"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
