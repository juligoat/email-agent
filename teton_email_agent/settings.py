"""
Streamlined configuration for project purropses
"""

from typing import List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class AgentConfigurationError(Exception):
    """Raised when agent configuration is invalid"""

    def __init__(self, message: str = "GROQ_API_KEY must be provided"):
        super().__init__(message)


class Settings(BaseSettings):
    """Streamlined settings for interview demonstration"""

    # REQUIRED
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key for LLM")

    # GMAIL INTEGRATION (Optional)
    gmail_credentials_path: str = Field(default="credentials.json")
    gmail_token_path: str = Field(default="token.json")

    # CORE AGENT SETTINGS
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    email_check_interval: int = Field(default=60, ge=10, le=3600)

    # SECURITY (Basic)
    email_whitelist: str = Field(default="", description="Comma-separated email addresses")

    # TOOLS (Simple)
    web_search_enabled: bool = Field(default=True)
    auto_reply_enabled: bool = Field(default=True)

    # LANGCHAIN
    langchain_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    langchain_max_tokens: int = Field(default=1000, ge=100, le=4000)
    langchain_model: str = Field(default="llama-3.1-8b-instant")

    # DEVELOPMENT
    debug_mode: bool = Field(default=False)
    mock_mode: bool = Field(default=False)

    model_config = {"env_file": ".env", "case_sensitive": False}

    @model_validator(mode="after")
    def validate_configuration(self):
        """Validate essential configuration"""
        if not self.groq_api_key and not self.mock_mode:
            raise AgentConfigurationError()
        return self

    def get_email_whitelist(self) -> List[str]:
        """Get email whitelist as a list"""
        if not self.email_whitelist.strip():
            return []
        return [email.strip().lower() for email in self.email_whitelist.split(",") if email.strip()]

    def is_sender_whitelisted(self, sender_email: str) -> bool:
        """Check if sender is in whitelist"""
        whitelist = self.get_email_whitelist()

        # If no whitelist set, allow all
        if not whitelist:
            return True

        # Extract email from "Name <email@domain.com>" format
        if "<" in sender_email and ">" in sender_email:
            email = sender_email.split("<")[1].split(">")[0].strip()
        else:
            email = sender_email.strip()

        email = email.lower()

        # Check against whitelist
        for whitelisted in whitelist:
            if email == whitelisted or whitelisted in email:
                return True
        return False

    def get_langchain_config(self) -> dict:
        """Get LangChain configuration"""
        return {
            "temperature": self.langchain_temperature,
            "max_tokens": self.langchain_max_tokens,
            "model_name": self.langchain_model,
        }
