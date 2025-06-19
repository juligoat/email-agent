"""
Email agent (LangChain and LangGraph)
"""

import logging
import time
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from teton_email_agent.models import ActionType, AgentDecision, AgentLog, EmailContent
from teton_email_agent.settings import Settings
from teton_email_agent.tools import ToolRegistry

logger = logging.getLogger(__name__)


class EnhancedEmailAgent:
    """Enhanced email agent using LangChain/LangGraph"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logs: List[AgentLog] = []

        # Initialize LLM
        self.llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=1000,
        )

        # Initialize tool registry
        self.tool_registry = ToolRegistry(settings)

        # Initialize memory for conversations
        self.memory = MemorySaver()

        # Initialize agent (will be set up after tools are registered)
        self.agent = None

        logger.info("Enhanced email agent initialized with LangChain")

    async def setup_agent(self):
        """Set up the LangGraph agent with tools"""
        # Get tools from registry
        tools = await self.tool_registry.get_langchain_tools()

        if not tools:
            logger.warning("No tools available for agent")
            return

        # Create the agent with correct parameters
        self.agent = create_react_agent(model=self.llm, tools=tools, checkpointer=self.memory)

        logger.info(f"Agent configured with {len(tools)} tools: {[t.name for t in tools]}")

    async def register_tool(self, tool):
        """Register a tool with the agent"""
        await self.tool_registry.register_tool(tool)

        # Re-setup agent if it exists
        if self.agent:
            await self.setup_agent()

        logger.info(f"Registered tool: {tool.name}")

    async def process_email(self, email: EmailContent) -> AgentLog:
        """Process an email using the LangGraph agent"""
        start_time = time.time()

        try:
            logger.info(f"Processing email from {email.sender}: {email.subject}")

            if not self.agent:
                await self.setup_agent()

            if not self.agent:
                raise RuntimeError("Agent not properly initialized")

            # Set email context for tools
            await self._set_email_context_for_tools(email)

            # Create configuration with email context
            config = {
                "configurable": {
                    "thread_id": f"email_{email.message_id}",
                }
            }

            # Prepare input for agent with system instructions
            email_analysis = self._format_email_for_analysis(email)

            # Run the agent
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=email_analysis)]}, config=config
            )

            # Extract information from result
            understanding, decision = self._parse_agent_result(result, email)

            # Create log entry with enhanced execution result
            execution_time = time.time() - start_time
            execution_result = self._extract_enhanced_execution_result(result, decision)

            log_entry = AgentLog(
                email_id=email.message_id,
                understanding=understanding,
                decision=decision,
                execution_result=execution_result,
                execution_time=execution_time,
            )

            self.logs.append(log_entry)
            return log_entry

        except Exception as e:
            logger.exception("Error processing email with LangChain agent")

            # Create fallback log entry
            execution_time = time.time() - start_time
            fallback_decision = AgentDecision(
                action_type=ActionType.REPLY,
                reasoning=f"Fallback due to error: {e!s}",
                confidence=0.3,
                parameters={
                    "message": "Thank you for your email. I'm currently experiencing technical difficulties, but I'll review your message and get back to you soon."
                },
            )

            log_entry = AgentLog(
                email_id=email.message_id,
                understanding=f"Error processing email from {email.sender}",
                decision=fallback_decision,
                execution_result=f"Error: {e!s}",
                execution_time=execution_time,
            )

            self.logs.append(log_entry)
            return log_entry

    async def _set_email_context_for_tools(self, email: EmailContent):
        """Set current email context for all tools - ENHANCED VERSION"""
        try:
            tools = await self.tool_registry.get_langchain_tools()

            logger.info(f"Setting email context for {len(tools)} tools")

            for tool in tools:
                # Method 1: Instance method (if available)
                if hasattr(tool, "set_current_email"):
                    tool.set_current_email(email)
                    logger.debug(f"Set email context via method for {tool.name}")

                # Method 2: Instance attribute (if available)
                if hasattr(tool, "_current_email"):
                    tool._current_email = email
                    logger.debug(f"Set email context via attribute for {tool.name}")

                # Method 3: Class attribute (for EmailReplyTool specifically)
                if tool.name == "send_email_reply" and hasattr(tool.__class__, "_current_email"):
                    tool.__class__._current_email = email
                    logger.debug(f"Set email context via class attribute for {tool.name}")

                # Method 4: Direct assignment for any tool with current_email
                try:
                    tool.current_email = email
                    logger.debug(f"Set email context via direct assignment for {tool.name}")
                except Exception:
                    pass  # Some tools might not allow this

            logger.info(f"Email context set for email: {email.message_id}")

        except Exception as e:
            logger.warning(f"Error setting email context: {e}")

    def _format_email_for_analysis(self, email: EmailContent) -> str:
        """Format email for agent analysis with clear instructions"""

        # Determine if this is a test email
        is_test_email = (
            email.message_id.startswith("sim_")
            or email.message_id.startswith("test_")
            or "@example.com" in email.sender
        )

        test_note = (
            "\n\n**NOTE: This is a test/simulation email - demonstrate your capabilities fully.**"
            if is_test_email
            else ""
        )

        return f"""You are an intelligent email assistant. Analyze this email and take the most appropriate action.

EMAIL TO ANALYZE:
From: {email.sender}
Subject: {email.subject}
Received: {email.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Email Body:
{email.body}{test_note}

INSTRUCTIONS:
1. Analyze the email content and determine the best response approach
2. For questions you can answer with your existing knowledge: Use send_email_reply directly
3. For current events, weather, news, or "latest information" requests: Use web_search first, then provide an informed response
4. For research questions or topics you're unsure about: Use web_search to gather information
5. Always be helpful, professional, and courteous
6. Provide complete, informative responses

AVAILABLE TOOLS:
- send_email_reply: Send a helpful email response (use for most replies)
- web_search: Search for current/recent information when needed

DECISION CRITERIA:
- Use DIRECT reply for: pricing questions, feature explanations, general service information, basic questions you know the answer to
- Use WEB SEARCH + reply for: current events, weather, recent trends, "latest" anything, research queries, topics you're uncertain about

Choose the appropriate approach and provide a helpful response to this email."""

    def _parse_agent_result(
        self, result: Dict[str, Any], email: EmailContent
    ) -> tuple[str, AgentDecision]:
        """Parse agent result to extract understanding and decision"""

        # Extract messages from result
        messages = result.get("messages", [])

        # Get the last AI message
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]

        if ai_messages:
            last_response = ai_messages[-1].content

            # Extract understanding
            understanding = f"Email from {email.sender} regarding: {email.subject}"

            # Determine action based on tool calls or content
            tool_calls = getattr(ai_messages[-1], "tool_calls", []) or []

            if tool_calls:
                # Agent used tools
                tool_call = tool_calls[0]  # Use first tool call
                action_type = self._map_tool_to_action(tool_call["name"])

                # Enhanced reasoning based on tool used
                reasoning = self._generate_reasoning(tool_call, email)

                decision = AgentDecision(
                    action_type=action_type,
                    reasoning=reasoning,
                    confidence=0.85,  # Higher confidence for tool-based decisions
                    parameters=tool_call.get("args", {}),
                )
            else:
                # Direct response without tools
                decision = AgentDecision(
                    action_type=ActionType.REPLY,
                    reasoning="Provided direct response based on available knowledge",
                    confidence=0.75,
                    parameters={"message": last_response},
                )
        else:
            # Fallback
            understanding = f"Email from {email.sender} about {email.subject}"
            decision = AgentDecision(
                action_type=ActionType.REPLY,
                reasoning="Fallback response - no clear agent output",
                confidence=0.5,
                parameters={
                    "message": "Thank you for your email. I'll review it and get back to you."
                },
            )

        return understanding, decision

    def _generate_reasoning(self, tool_call: Dict, email: EmailContent) -> str:
        """Generate detailed reasoning for tool usage"""
        tool_name = tool_call["name"]

        if tool_name == "web_search":
            query = tool_call.get("args", {}).get("query", "unknown")
            return f"🔍 Used web search for current information about '{query}' to provide up-to-date response"
        elif tool_name == "send_email_reply":
            return "💬 Generated direct response using existing knowledge - no web search needed"
        else:
            return f"🔧 Used {tool_name} tool based on email content analysis"

    def _map_tool_to_action(self, tool_name: str) -> ActionType:
        """Map tool name to action type"""
        mapping = {
            "send_email_reply": ActionType.REPLY,
            "web_search": ActionType.REPLY,  # Search then reply
        }
        return mapping.get(tool_name, ActionType.REPLY)

    def _extract_enhanced_execution_result(
        self, result: Dict[str, Any], decision: AgentDecision
    ) -> str:
        """Extract enhanced execution result showing actual reply content and tool usage"""
        messages = result.get("messages", [])
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]

        if not ai_messages:
            return "❌ No agent response generated"

        last_message = ai_messages[-1]
        tool_calls = getattr(last_message, "tool_calls", []) or []

        # Check if web search was used
        used_web_search = any(tc["name"] == "web_search" for tc in tool_calls)
        used_direct_reply = any(tc["name"] == "send_email_reply" for tc in tool_calls)

        # Get the actual reply content
        reply_content = decision.parameters.get("message", "No message content available")

        # Build enhanced result
        result_parts = []

        # Tool usage indicator
        if used_web_search:
            search_query = None
            for tc in tool_calls:
                if tc["name"] == "web_search":
                    search_query = tc.get("args", {}).get("query", "unknown")
                    break
            result_parts.append(f"🔍 **USED WEB SEARCH** for query: '{search_query}'")
            result_parts.append("📄 Generated informed response with current information")
        elif used_direct_reply:
            result_parts.append("💡 **USED EXISTING KNOWLEDGE** - no web search needed")
            result_parts.append("📄 Generated direct response")
        else:
            result_parts.append("🤖 Generated response using available knowledge")

        result_parts.append("")  # Empty line
        result_parts.append("📧 **REPLY CONTENT:**")
        result_parts.append("-" * 50)

        # Format the reply content properly
        if reply_content and len(reply_content.strip()) > 0:
            # Clean up the reply content
            clean_content = reply_content.strip()
            # Ensure proper line breaks
            clean_content = clean_content.replace(". ", ".\n\n")
            clean_content = clean_content.replace("\n\n\n", "\n\n")
            result_parts.append(clean_content)
        else:
            result_parts.append("(No reply content available)")

        result_parts.append("-" * 50)

        return "\n".join(result_parts)

    def get_recent_logs(self, limit: int = 20) -> List[AgentLog]:
        """Get recent logs"""
        return self.logs[-limit:] if self.logs else []

    def clear_logs(self):
        """Clear logs"""
        self.logs.clear()

    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        return self.tool_registry.get_statistics()

    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return self.tool_registry.get_tool_names()
