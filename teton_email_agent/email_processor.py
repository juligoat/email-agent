"""
Email processing service now with LangChain integration
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from teton_email_agent.core import EnhancedEmailAgent
from teton_email_agent.gmail import GmailIntegration
from teton_email_agent.models import EmailContent
from teton_email_agent.settings import Settings

logger = logging.getLogger(__name__)


class AgentNotInitializedError(Exception):
    """Raised when agent is not initialized"""

    pass


class EmailProcessor:
    """Enhanced email processing service with LangChain integration"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.agent: Optional[EnhancedEmailAgent] = None
        self.gmail_integration: Optional[GmailIntegration] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize the processor with enhanced agent"""
        try:
            logger.info("Initializing enhanced email processor...")

            # Initialize enhanced agent
            self.agent = EnhancedEmailAgent(self.settings)
            logger.info("Enhanced agent created")

            # Initialize Gmail if configured
            if os.path.exists(self.settings.gmail_credentials_path):
                logger.info("Initializing Gmail integration...")
                self.gmail_integration = GmailIntegration(
                    self.settings.gmail_credentials_path, self.settings.gmail_token_path
                )

                if await self.gmail_integration.authenticate():
                    logger.info("Gmail authentication successful")

                    # Set Gmail integration in tool registry
                    self.agent.tool_registry.set_gmail_integration(self.gmail_integration)

                    # Show whitelist info if configured
                    whitelist = self.settings.get_email_whitelist()
                    if whitelist:
                        logger.info(f"Email whitelist active: {whitelist}")
                    else:
                        logger.info("No email whitelist configured - all emails will be processed")

                    # Start monitoring
                    self.monitoring_task = asyncio.create_task(self._start_monitoring())
                else:
                    logger.warning("Gmail authentication failed")
                    self.gmail_integration = None
            else:
                logger.info(
                    f"Gmail credentials not found at {self.settings.gmail_credentials_path}"
                )

            # Setup the agent with tools
            await self.agent.setup_agent()

            self.is_initialized = True
            logger.info("Email processor initialization complete")

        except Exception:
            logger.exception("Failed to initialize email processor")
            self.is_initialized = False
            raise

    async def _start_monitoring(self):
        """Start Gmail monitoring with whitelist check"""
        if not self.gmail_integration:
            logger.warning("Gmail integration not available for monitoring")
            return

        logger.info("Starting Gmail monitoring...")

        async def email_callback(email: EmailContent):
            """Process incoming emails with whitelist filtering"""
            try:
                # WHITELIST CHECK
                if not self.settings.is_sender_whitelisted(email.sender):
                    logger.info(f"SKIPPED email from {email.sender} - not in whitelist")
                    return

                # Process the email
                logger.info(f"PROCESSING email from {email.sender}: {email.subject}")

                # Set current email context for tools
                await self._set_email_context_for_tools(email)

                # Process with enhanced agent
                result = await self.process_email(email)

                logger.info(f"Email processing completed: {result.decision.action_type}")

            except Exception:
                logger.exception(f"Error in email callback for {email.sender}")

        try:
            await self.gmail_integration.start_monitoring(
                email_callback, self.settings.email_check_interval
            )
        except Exception:
            logger.exception("Error in Gmail monitoring")

    async def _set_email_context_for_tools(self, email: EmailContent):
        """Set current email context for all tools that need it"""
        if not self.agent or not self.agent.tool_registry:
            return

        # Get all tools from registry
        tools = await self.agent.tool_registry.get_langchain_tools()

        for tool in tools:
            # Set email context for tools that support it
            if hasattr(tool, "set_current_email"):
                tool.set_current_email(email)
            elif hasattr(tool, "current_email"):
                tool.current_email = email

    async def process_email(self, email: EmailContent):
        """Process a single email using the enhanced agent"""
        if not self.agent:
            raise AgentNotInitializedError("Agent not initialized. Call initialize() first.")

        if not self.is_initialized:
            raise AgentNotInitializedError("Email processor not fully initialized.")

        try:
            # Set email context for tools
            await self._set_email_context_for_tools(email)

            # Process with enhanced agent
            result = await self.agent.process_email(email)

            return result

        except Exception:
            logger.exception(f"Error processing email {email.message_id}")
            raise

    async def send_test_email(self):
        """Send a test email to verify agent functionality"""
        if not self.agent:
            raise AgentNotInitializedError("Agent not initialized")

        # Create test email with various scenarios
        test_scenarios = [
            {
                "sender": "test.user@example.com",
                "subject": "Test Email - General Question",
                "body": "Hi! I have a question about your email agent service. Can you tell me how it works and what features are available? I'm particularly interested in the pricing options.",
                "scenario": "general_inquiry",
            },
            {
                "sender": "meeting.request@company.com",
                "subject": "Meeting Request",
                "body": "Hello, I would like to schedule a meeting to discuss our upcoming project. Are you available next Tuesday at 2 PM for about an hour?",
                "scenario": "meeting_request",
            },
            {
                "sender": "support.needed@client.com",
                "subject": "Need Help with Setup",
                "body": "I'm having trouble setting up the email agent. Can you provide some guidance on the initial configuration steps?",
                "scenario": "support_request",
            },
        ]

        # Use the first scenario by default, but could be randomized
        test_data = test_scenarios[0]

        test_email = EmailContent(
            sender=test_data["sender"],
            subject=test_data["subject"],
            body=test_data["body"],
            message_id=f"test_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
        )

        try:
            result = await self.process_email(test_email)

            return {
                "message": "Test email processed successfully",
                "scenario": test_data["scenario"],
                "result": {
                    "email_id": result.email_id,
                    "understanding": result.understanding,
                    "action": result.decision.action_type.value
                    if hasattr(result.decision.action_type, "value")
                    else str(result.decision.action_type),
                    "reasoning": result.decision.reasoning,
                    "confidence": result.decision.confidence,
                    "execution_result": result.execution_result,
                    "execution_time": result.execution_time,
                    "parameters": result.decision.parameters,
                },
                "tools_used": await self.agent.get_available_tools(),
                "agent_type": "LangChain Enhanced Agent",
            }

        except Exception as e:
            logger.exception("Error in test email processing")
            return {
                "message": "Test email processing failed",
                "error": str(e),
                "scenario": test_data["scenario"],
            }

    async def update_configuration(self, updates: dict):
        """Update configuration and reinitialize if needed"""
        try:
            logger.info(f"Updating configuration: {list(updates.keys())}")

            # Update settings
            for key, value in updates.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
                    logger.info(f"Updated {key}")

            # If critical settings changed, reinitialize
            critical_settings = {"groq_api_key", "gmail_credentials_path", "gmail_token_path"}
            if any(key in critical_settings for key in updates):
                logger.info("Critical settings changed, reinitializing agent...")

                # Stop monitoring
                if self.monitoring_task:
                    self.monitoring_task.cancel()

                # Reinitialize
                await self.initialize()
                return "Agent reinitialized with new configuration"
            else:
                return "Configuration updated successfully"

        except Exception as e:
            logger.exception("Error updating configuration")
            return f"Configuration update failed: {e!s}"

    async def get_agent_status(self):
        """Get comprehensive agent status"""
        if not self.agent:
            return {"status": "not_initialized", "message": "Agent not initialized"}

        try:
            tools = await self.agent.get_available_tools()
            logs_count = len(self.agent.get_recent_logs())
            tool_stats = self.agent.get_tool_statistics()

            return {
                "status": "active" if self.is_initialized else "initializing",
                "total_emails_processed": logs_count,
                "gmail_connected": self.gmail_integration is not None,
                "active_tools": tools,
                "tool_statistics": tool_stats,
                "monitoring_active": self.monitoring_task is not None
                and not self.monitoring_task.done(),
                "whitelist_enabled": bool(self.settings.get_email_whitelist()),
                "confidence_threshold": self.settings.confidence_threshold,
                "agent_type": "LangChain Enhanced Agent",
            }

        except Exception as e:
            logger.exception("Error getting agent status")
            return {"status": "error", "message": f"Error getting status: {e!s}"}

    async def get_tool_performance(self):
        """Get tool performance metrics"""
        if not self.agent:
            return {}

        try:
            return self.agent.get_tool_statistics()
        except Exception:
            logger.exception("Error getting tool performance")
            return {}

    async def test_tool(self, tool_name: str, test_params: dict = None):
        """Test a specific tool"""
        if not self.agent:
            raise AgentNotInitializedError("Agent not initialized")

        try:
            # Create a test email for tool context
            test_email = EmailContent(
                sender="tool.test@example.com",
                subject=f"Tool Test - {tool_name}",
                body="This is a test email for tool testing purposes.",
                message_id=f"tool_test_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
            )

            # Set email context
            await self._set_email_context_for_tools(test_email)

            # Get tool from registry
            tools = await self.agent.tool_registry.get_langchain_tools()
            target_tool = None

            for tool in tools:
                if tool.name == tool_name:
                    target_tool = tool
                    break

            if not target_tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": [tool.name for tool in tools],
                }

            # Test the tool with default or provided parameters
            if not test_params:
                test_params = (
                    {"query": "test query"}
                    if "search" in tool_name
                    else {"message": "test message"}
                )

            # Execute tool
            result = await target_tool.arun(**test_params)

            return {
                "success": True,
                "tool_name": tool_name,
                "result": result,
                "test_params": test_params,
            }

        except Exception as e:
            logger.exception(f"Error testing tool {tool_name}")
            return {"success": False, "error": str(e), "tool_name": tool_name}

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up email processor...")

        try:
            # Cancel monitoring task
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            # Cleanup Gmail integration
            if self.gmail_integration:
                # Close any open sessions in tools
                tools = await self.agent.tool_registry.get_langchain_tools() if self.agent else []
                for tool in tools:
                    if hasattr(tool, "__aexit__"):
                        try:
                            await tool.__aexit__(None, None, None)
                        except Exception as e:
                            logger.warning(f"Error cleaning up tool {tool.name}: {e}")

            self.is_initialized = False
            logger.info("Email processor cleanup complete")

        except Exception:
            logger.exception("Error during cleanup")

    def get_recent_logs(self, limit: int = 20):
        """Get recent processing logs"""
        if not self.agent:
            return []
        return self.agent.get_recent_logs(limit)

    def clear_logs(self):
        """Clear processing logs"""
        if self.agent:
            self.agent.clear_logs()
