"""
Autonomous Email Agent - Main Application
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from teton_email_agent.email_processor import EmailProcessor
from teton_email_agent.settings import Settings

# Global instances
email_processor: Optional[EmailProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global email_processor

    # Startup
    settings = Settings()
    print("Starting Autonomous Email Agent")

    try:
        email_processor = EmailProcessor(settings)
        await email_processor.initialize()
        app.state.email_processor = email_processor
        print("Application startup complete")
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    if email_processor:
        await email_processor.cleanup()


app = FastAPI(
    title="Autonomous Email Agent",
    description="AI-powered email assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class EmailWebhook(BaseModel):
    sender: str
    subject: str
    body: str
    message_id: str


class ConfigUpdate(BaseModel):
    groq_api_key: Optional[str] = None


@app.get("/")
async def root():
    """Health check"""
    return {
        "message": "Autonomous Email Agent API",
        "status": "running",
        "agent_initialized": email_processor is not None,
    }


@app.get("/agent/status")
async def get_agent_status():
    """Get agent status"""
    if not email_processor or not email_processor.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {
        "status": "active",
        "total_emails_processed": len(email_processor.agent.logs),
        "gmail_connected": email_processor.gmail_integration is not None,
        "active_tools": list(email_processor.agent.tools.keys()),
    }


@app.get("/agent/logs")
async def get_agent_logs(limit: int = 20):
    """Get recent logs"""
    if not email_processor or not email_processor.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return email_processor.agent.get_recent_logs(limit)


@app.post("/emails/test")
async def send_test_email():
    """Send test email"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await email_processor.send_test_email()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return result


@app.post("/emails/webhook")
async def receive_email(email_data: EmailWebhook, background_tasks: BackgroundTasks):
    """Receive email via webhook"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    from teton_email_agent.models import EmailContent

    email = EmailContent(
        sender=email_data.sender,
        subject=email_data.subject,
        body=email_data.body,
        message_id=email_data.message_id,
        timestamp=datetime.now(),
    )

    background_tasks.add_task(process_email_background, email)
    return {"message": "Email queued for processing"}


async def process_email_background(email):
    """Process email in background"""
    try:
        if email_processor:
            await email_processor.process_email(email)
    except Exception as e:
        print(f"Error processing email: {e}")


@app.post("/config/update")
async def update_config(config: ConfigUpdate):
    """Update configuration"""
    if not email_processor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await email_processor.update_configuration(config.dict(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        return {"message": result}


@app.delete("/agent/logs")
async def clear_logs():
    """Clear logs"""
    if not email_processor or not email_processor.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    email_processor.agent.clear_logs()
    return {"message": "Logs cleared"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
