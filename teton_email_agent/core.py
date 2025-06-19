"""
Core email agent implementation using Groq and some basic prompt engineering / tooling.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List

from groq import AsyncGroq

from teton_email_agent.models import ActionType, AgentDecision, AgentLog, EmailContent
from teton_email_agent.settings import Settings

logger = logging.getLogger(__name__)


class EmailAgent:
    """Core email processing agent using Groq"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tools: Dict[str, Any] = {}
        self.logs: List[AgentLog] = []
        self.groq_client = AsyncGroq(api_key=settings.groq_api_key)

        logger.info("Email agent initialized with Groq")

    def register_tool(self, tool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    async def process_email(self, email: EmailContent) -> AgentLog:
        """Process an email"""
        start_time = time.time()

        try:
            logger.info(f"Processing email: {email.subject}")

            # Understand email
            understanding = await self._understand_email(email)

            # Make decision
            decision = await self._make_decision(email, understanding)

            # Execute action
            execution_result = None
            if decision.confidence >= self.settings.confidence_threshold:
                execution_result = await self._execute_action(decision, email)
            else:
                execution_result = f"Skipped due to low confidence ({decision.confidence:.2f})"

            # Create log
            execution_time = time.time() - start_time
            log_entry = AgentLog(
                email_id=email.message_id,
                understanding=understanding,
                decision=decision,
                execution_result=execution_result,
                execution_time=execution_time,
            )

            self.logs.append(log_entry)
        except Exception:
            logger.exception("Error processing email")
            raise
        else:
            return log_entry

    async def _understand_email(self, email: EmailContent) -> str:
        """Understand email content using Groq"""
        prompt = f"""Analyze this email and summarize what the sender wants:

From: {email.sender}
Subject: {email.subject}
Body: {email.body}

Provide a brief summary of the email's main purpose and any specific questions or requests."""

        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3,
            )
        except Exception:
            logger.exception("Error understanding email")
            return f"Email from {email.sender} about {email.subject}"
        else:
            content = response.choices[0].message.content
            return (
                content.strip() if content else f"Email from {email.sender} about {email.subject}"
            )

    async def _make_decision(self, email: EmailContent, understanding: str) -> AgentDecision:
        """Make decision about what action to take"""

        prompt = f"""Analyze this email and decide what action to take.

Email summary: {understanding}
From: {email.sender}
Subject: {email.subject}
Body: {email.body}

Available actions: reply, schedule_meeting, archive, flag_urgent

If the email has questions, choose "reply" and provide helpful answers.
If it requests a meeting, choose "schedule_meeting".
If it's promotional/newsletter, choose "archive".
If it's urgent, choose "flag_urgent".

For replies, write a well-formatted, natural response with proper spacing.

Example good reply format:
"Hi there!

Thanks for your questions. Here are the answers:

1. The President of the United States is Joe Biden.
2. I don't have personal political opinions as an AI assistant.
3. The capital of Denmark is Copenhagen.

Feel free to ask if you need more information!"

Respond with ONLY valid JSON (no extra text):
{{
    "action_type": "reply",
    "reasoning": "Brief reason for this action",
    "confidence": 0.8,
    "parameters": {{"message": "Your well-formatted response with proper spacing"}}
}}

Make sure your message is properly formatted and answers any specific questions."""

        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.5,
            )

            # Get the raw response
            content = response.choices[0].message.content
            if not content:
                content = ""  # Handle empty response gracefully

            content = content.strip()
            logger.info(f"Raw AI response: {content[:200]}...")

            # Try to extract and clean JSON
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_text = content[json_start:json_end]

                # Clean up common JSON issues
                json_text = json_text.replace("\n", " ")
                json_text = json_text.replace("\\", "\\\\")
                json_text = json_text.replace('""', '"')

                try:
                    decision_data = json.loads(json_text)
                except json.JSONDecodeError:
                    logger.exception("JSON parsing failed")
                    logger.info(f"Problematic JSON: {json_text}")
                    raise
            else:
                # Fallback: try parsing the whole response
                decision_data = json.loads(content)

        except Exception:
            logger.exception("Error making decision")
            # Create a simple fallback response
            return AgentDecision(
                action_type=ActionType.REPLY,
                reasoning="Fallback decision due to parsing error",
                confidence=0.7,
                parameters={
                    "message": "Thank you for your email! I'll review it and get back to you with a detailed response."
                },
            )

        # Format the reply message if it's a reply action
        if (
            decision_data.get("action_type") == "reply"
            and "parameters" in decision_data
            and "message" in decision_data["parameters"]
        ):
            decision_data["parameters"]["message"] = self._format_reply_message(
                decision_data["parameters"]["message"]
            )

        return AgentDecision(**decision_data)

    def _format_reply_message(self, message: str) -> str:
        """Clean up and format reply message"""
        if not message:
            return message

        # Fix common formatting issues
        formatted = message.replace("\\n", "\n")
        formatted = formatted.replace("\n\n\n", "\n\n")

        # Add space after periods if missing
        formatted = re.sub(r"\.([A-Z])", r". \1", formatted)
        formatted = re.sub(r"\.([I])", r". \1", formatted)

        # Clean up extra spaces
        formatted = re.sub(r" +", " ", formatted)
        formatted = formatted.strip()

        return formatted

    async def _execute_action(self, decision: AgentDecision, email: EmailContent) -> str:
        """Execute the decided action"""
        try:
            if decision.action_type == ActionType.REPLY:
                if "reply" in self.tools:
                    result = await self.tools["reply"].execute(decision.parameters, email)
                    return result.result if result.success else result.error or "Reply failed"
                else:
                    message = decision.parameters.get("message", "Thank you for your email.")
                    return f"Reply: {message}"

            elif decision.action_type == ActionType.ARCHIVE:
                return "Email marked for archiving"

            elif decision.action_type == ActionType.FLAG_URGENT:
                return "Email flagged as urgent"

            elif decision.action_type == ActionType.SCHEDULE_MEETING:
                return "Meeting scheduling requested"

            else:
                return f"Action {decision.action_type} executed"

        except Exception as e:
            logger.exception("Error executing action")
            return f"Error: {e!s}"

    def get_recent_logs(self, limit: int = 20) -> List[AgentLog]:
        """Get recent logs"""
        return self.logs[-limit:] if self.logs else []

    def clear_logs(self):
        """Clear logs"""
        self.logs.clear()
