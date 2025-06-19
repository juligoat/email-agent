"""
Enhanced main API
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from teton_email_agent.email_processor import EmailProcessor
from teton_email_agent.models import EmailContent
from teton_email_agent.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
email_processor: Optional[EmailProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global email_processor

    # Startup
    logger.info("🚀 Starting Enhanced Email Agent")

    try:
        settings = Settings()
        email_processor = EmailProcessor(settings)
        await email_processor.initialize()
        app.state.email_processor = email_processor
        logger.info("✅ Application startup complete")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down")
    if email_processor:
        await email_processor.cleanup()


app = FastAPI(
    title="Enhanced Email Agent",
    description="LangChain-powered email assistant with intelligent tool orchestration",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Enhanced API Models
class EmailSimulation(BaseModel):
    sender: str
    subject: str
    body: str
    scenario: str = "general"


class TestEmailRequest(BaseModel):
    scenario: str = "default"  # "default", "weather", "pricing", "research"


# Core Endpoints
@app.get("/")
async def root():
    """API information"""
    return {
        "message": "Enhanced Email Agent API",
        "version": "2.0.0",
        "agent_type": "LangChain Enhanced",
        "status": "running",
        "features": [
            "🧠 Smart Tool Orchestration",
            "🔍 Web Search Integration",
            "💬 Intelligent Email Replies",
            "📊 Clear Tool Usage Tracking",
            "🎯 Enhanced Result Display",
        ],
        "dashboard": "http://localhost:8501",
        "improvements": [
            "✨ Clear tool usage indicators (🔍 Web Search vs 💡 Knowledge)",
            "📧 Properly formatted email replies",
            "📊 Enhanced execution result display",
            "🎯 Better test scenario variety",
        ],
    }


@app.get("/agent/status")
async def get_agent_status():
    """Get agent status"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        status = await email_processor.get_agent_status()
        return status
    except Exception as e:
        logger.exception("Error getting agent status")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/logs")
async def get_agent_logs(limit: int = 20):
    """Get recent logs with enhanced formatting"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        logs = email_processor.get_recent_logs(limit)

        # Enhance logs for better display
        enhanced_logs = []
        for log in logs:
            enhanced_log = {
                "timestamp": log.timestamp,
                "email_id": log.email_id,
                "understanding": log.understanding,
                "decision": {
                    "action_type": str(log.decision.action_type),
                    "reasoning": log.decision.reasoning,
                    "confidence": log.decision.confidence,
                    "parameters": log.decision.parameters,
                },
                "execution_result": log.execution_result,
                "execution_time": f"{log.execution_time:.2f}s" if log.execution_time else "N/A",
                # Add tool usage indicators
                "used_web_search": "🔍" in log.decision.reasoning,
                "used_knowledge": "💡" in log.decision.reasoning
                or "existing knowledge" in log.decision.reasoning.lower(),
                "tools_used": [],
            }

            # Extract tools used from reasoning
            if "🔍" in log.decision.reasoning:
                enhanced_log["tools_used"].append("web_search")
            if "💬" in log.decision.reasoning:
                enhanced_log["tools_used"].append("direct_reply")

            enhanced_logs.append(enhanced_log)

        return {
            "logs": enhanced_logs,
            "total_logs": len(logs),
            "processing_stats": {
                "web_search_used": sum(1 for log in enhanced_logs if log["used_web_search"]),
                "knowledge_used": sum(1 for log in enhanced_logs if log["used_knowledge"]),
                "avg_confidence": sum(log["decision"]["confidence"] for log in enhanced_logs)
                / len(enhanced_logs)
                if enhanced_logs
                else 0,
            },
        }
    except Exception as e:
        logger.exception("Error getting logs")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/emails/test")
async def send_test_email(request: TestEmailRequest = None):
    """Send enhanced test email with different scenarios"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Enhanced test scenarios
        scenarios = {
            "default": {
                "sender": "test.user@example.com",
                "subject": "General Inquiry - Service Information",
                "body": "Hi! I'm interested in learning more about your email agent service. Can you tell me about the features, pricing options, and how it works? I'm evaluating different solutions for our team.",
                "expected_tool": "direct_reply",
            },
            "weather": {
                "sender": "weather.request@example.com",
                "subject": "Current Weather Information Request",
                "body": "Hi there! I need to know the current weather conditions and forecast for today. Can you help me get the latest weather information?",
                "expected_tool": "web_search",
            },
            "pricing": {
                "sender": "pricing.inquiry@example.com",
                "subject": "Pricing and Cost Information",
                "body": "Hello, I'd like to get current pricing information for your service plans. What are the latest rates and what's included in each tier?",
                "expected_tool": "web_search",
            },
            "research": {
                "sender": "research.team@example.com",
                "subject": "Latest AI Technology Trends",
                "body": "Hi! We're researching the latest trends in AI technology and email automation. Can you provide insights on current developments and market trends?",
                "expected_tool": "web_search",
            },
            "knowledge": {
                "sender": "simple.question@example.com",
                "subject": "Basic Question - Capital of France",
                "body": "Hi, I have a simple question: What is the capital of France? Thanks!",
                "expected_tool": "direct_reply",
            },
        }

        # Get scenario
        scenario_name = request.scenario if request else "default"
        if scenario_name not in scenarios:
            scenario_name = "default"

        test_data = scenarios[scenario_name]

        # Create test email
        test_email = EmailContent(
            sender=test_data["sender"],
            subject=test_data["subject"],
            body=test_data["body"],
            message_id=f"test_{scenario_name}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
        )

        # Process the email
        result = await email_processor.process_email(test_email)

        # Enhanced result formatting
        enhanced_result = {
            "message": "✅ Test email processed successfully",
            "scenario": {
                "name": scenario_name,
                "description": f"Tests {test_data['expected_tool']} capability",
                "expected_tool": test_data["expected_tool"],
            },
            "input": {
                "sender": test_data["sender"],
                "subject": test_data["subject"],
                "body": test_data["body"],
            },
            "processing_result": {
                "email_id": result.email_id,
                "understanding": result.understanding,
                "action_taken": str(result.decision.action_type),
                "reasoning": result.decision.reasoning,
                "confidence": f"{result.decision.confidence:.1%}",
                "execution_time": f"{result.execution_time:.2f}s"
                if result.execution_time
                else "N/A",
                "tool_usage": {
                    "used_web_search": "🔍" in result.decision.reasoning,
                    "used_existing_knowledge": "💡" in result.decision.reasoning
                    or "existing knowledge" in result.decision.reasoning.lower(),
                    "tool_indicator": "🔍 Web Search"
                    if "🔍" in result.decision.reasoning
                    else "💡 Existing Knowledge",
                },
            },
            "execution_details": result.execution_result,
            "available_tools": await email_processor.agent.get_available_tools(),
            "agent_info": {
                "type": "LangChain Enhanced Agent",
                "version": "2.0.0",
                "capabilities": ["Tool Orchestration", "Web Search", "Smart Replies"],
            },
        }

        return enhanced_result

    except Exception as e:
        logger.exception("Error in test email processing")
        return {
            "message": "❌ Test email processing failed",
            "error": str(e),
            "scenario": scenario_name if "scenario_name" in locals() else "unknown",
        }


@app.post("/emails/simulate")
async def simulate_email(email_data: EmailSimulation):
    """Simulate email processing with enhanced result display"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Create email content
        email = EmailContent(
            sender=email_data.sender,
            subject=email_data.subject,
            body=email_data.body,
            message_id=f"sim_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
        )

        # Process the email
        result = await email_processor.process_email(email)

        # Enhanced response
        return {
            "message": "✅ Email simulation completed",
            "scenario": email_data.scenario,
            "input": {
                "sender": email_data.sender,
                "subject": email_data.subject,
                "body": email_data.body,
            },
            "analysis": {
                "understanding": result.understanding,
                "action_taken": str(result.decision.action_type),
                "reasoning": result.decision.reasoning,
                "confidence": f"{result.decision.confidence:.1%}",
                "execution_time": f"{result.execution_time:.2f}s",
            },
            "tool_usage": {
                "used_web_search": "🔍" in result.decision.reasoning,
                "used_knowledge": "💡" in result.decision.reasoning
                or "existing knowledge" in result.decision.reasoning.lower(),
                "indicator": "🔍 Web Search"
                if "🔍" in result.decision.reasoning
                else "💡 Existing Knowledge",
            },
            "execution_details": result.execution_result,
        }
    except Exception as e:
        logger.exception("Error in email simulation")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/scenarios")
async def get_test_scenarios():
    """Get available test scenarios"""
    return {
        "scenarios": {
            "default": {
                "name": "General Service Inquiry",
                "description": "Tests basic service information response using existing knowledge",
                "expected_tool": "💡 Direct Reply",
                "use_case": "Customer asking about features and pricing",
            },
            "weather": {
                "name": "Weather Information Request",
                "description": "Tests web search for current weather data",
                "expected_tool": "🔍 Web Search",
                "use_case": "User requesting current weather conditions",
            },
            "pricing": {
                "name": "Current Pricing Inquiry",
                "description": "Tests web search for latest pricing information",
                "expected_tool": "🔍 Web Search",
                "use_case": "Customer asking for current market rates",
            },
            "research": {
                "name": "Technology Research Query",
                "description": "Tests web search for current tech trends and information",
                "expected_tool": "🔍 Web Search",
                "use_case": "Research request requiring up-to-date information",
            },
            "knowledge": {
                "name": "Basic Knowledge Question",
                "description": "Tests direct response using existing knowledge",
                "expected_tool": "💡 Direct Reply",
                "use_case": "Simple factual question that doesn't need web search",
            },
        },
        "usage": "Use POST /emails/test with scenario parameter to test specific capabilities",
    }


@app.get("/tools/")
async def get_available_tools():
    """Get available tools with enhanced information"""
    if not email_processor or not email_processor.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        tools = await email_processor.agent.get_available_tools()
        tool_stats = email_processor.agent.get_tool_statistics()

        return {
            "tools": {
                "send_email_reply": {
                    "name": "Email Reply Tool",
                    "description": "Sends formatted email replies",
                    "indicator": "💬",
                    "use_case": "Direct responses using existing knowledge",
                },
                "web_search": {
                    "name": "Web Search Tool",
                    "description": "Searches web for current information",
                    "indicator": "🔍",
                    "use_case": "Current events, weather, latest pricing, research",
                },
            },
            "statistics": tool_stats,
            "total_tools": len(tools),
            "tool_orchestration": {
                "description": "Agent automatically chooses the right tool based on email content",
                "decision_factors": [
                    "Content analysis (current vs static information)",
                    "Keywords (latest, current, recent, trends)",
                    "Question type (factual vs research)",
                    "Information availability in knowledge base",
                ],
            },
        }
    except Exception as e:
        logger.exception("Error getting tools")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Enhanced Email Agent API...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
