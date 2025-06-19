"""
Tool registry
"""

import logging
from typing import Any, Dict, List

from teton_email_agent.tools.reply import EmailReplyTool
from teton_email_agent.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing agent tools"""

    def __init__(self, settings):
        self.settings = settings
        self.tools = []
        self.gmail_integration = None
        self.statistics = {
            "tools_registered": 0,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "tool_usage": {},
        }

    async def get_langchain_tools(self) -> List[Any]:
        """Get all LangChain tools"""
        if not self.tools:
            await self._initialize_default_tools()
        return self.tools

    async def _initialize_default_tools(self):
        """Initialize default tools"""
        try:
            # Email reply tool
            if self.settings.auto_reply_enabled:
                reply_tool = EmailReplyTool(settings=self.settings)
                if self.gmail_integration:
                    reply_tool.set_gmail_integration(self.gmail_integration)
                self.tools.append(reply_tool)
                logger.info("✅ Email reply tool registered")

            # Web search tool
            if self.settings.web_search_enabled:
                search_tool = WebSearchTool()
                self.tools.append(search_tool)
                logger.info("✅ Web search tool registered")

            self.statistics["tools_registered"] = len(self.tools)
            logger.info(f"📊 Tool registry initialized with {len(self.tools)} tools")

        except Exception:
            logger.exception("Error initializing default tools")

    async def register_tool(self, tool):
        """Register a new tool"""
        try:
            self.tools.append(tool)
            self.statistics["tools_registered"] += 1
            logger.info(f"✅ Tool registered: {tool.name}")
        except Exception as e:
            logger.exception(f"Error registering tool: {e}")

    def set_gmail_integration(self, gmail_integration):
        """Set Gmail integration for tools that need it"""
        self.gmail_integration = gmail_integration

        # Update existing reply tools
        for tool in self.tools:
            if isinstance(tool, EmailReplyTool):
                tool.set_gmail_integration(gmail_integration)

    def get_tool_names(self) -> List[str]:
        """Get list of tool names"""
        return [tool.name for tool in self.tools]

    def get_statistics(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        return self.statistics.copy()

    def record_tool_call(self, tool_name: str, success: bool):
        """Record tool usage statistics"""
        self.statistics["total_calls"] += 1

        if success:
            self.statistics["successful_calls"] += 1
        else:
            self.statistics["failed_calls"] += 1

        if tool_name not in self.statistics["tool_usage"]:
            self.statistics["tool_usage"][tool_name] = {"calls": 0, "successes": 0, "failures": 0}

        self.statistics["tool_usage"][tool_name]["calls"] += 1
        if success:
            self.statistics["tool_usage"][tool_name]["successes"] += 1
        else:
            self.statistics["tool_usage"][tool_name]["failures"] += 1
