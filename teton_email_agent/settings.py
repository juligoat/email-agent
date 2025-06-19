"""
Configuration management
"""

from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class AgentConfigurationError(Exception):
    """Raised when agent configuration is invalid"""

    def __init__(self, message: str = "GROQ_API_KEY must be provided"):
        super().__init__(message)


class Settings(BaseSettings):
    """Application settings"""

    # Groq API
    groq_api_key: Optional[str] = Field(default=None)

    # Gmail
    gmail_credentials_path: str = Field(default="credentials.json")
    gmail_token_path: str = Field(default="token.json")

    # Agent
    email_check_interval: int = Field(default=60)
    confidence_threshold: float = Field(default=0.7)

    # Email whitelist
    email_whitelist: str = Field(default="")

    # Optional fields that might be in .env but aren't used
    llm_provider: Optional[str] = Field(default=None)
    host: Optional[str] = Field(default=None)
    port: Optional[str] = Field(default=None)
    debug: Optional[bool] = Field(default=None)

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "allow"  # Allow extra fields from .env
    }

    @model_validator(mode="after")
    def validate_groq_api_key(self):
        if not self.groq_api_key:
            raise AgentConfigurationError()
        return self

    def get_email_whitelist(self):
        """Get email whitelist as a list"""
        if not self.email_whitelist.strip():
            return []
        return [email.strip() for email in self.email_whitelist.split(",") if email.strip()]

    def is_sender_whitelisted(self, sender_email: str) -> bool:
        """Check if sender is in whitelist"""
        whitelist = self.get_email_whitelist()

        # If no whitelist set, allow all (backward compatibility)
        if not whitelist:
            return True

        # Extract email from "Name <email@domain.com>" format
        if "<" in sender_email and ">" in sender_email:
            email = sender_email.split("<")[1].split(">")[0].strip()
        else:
            email = sender_email.strip()

        # Check against whitelist (case insensitive)
        return any(whitelisted.lower() in email.lower() for whitelisted in whitelist)
