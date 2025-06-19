"""
Gmail integration
"""

import asyncio
import base64
import contextlib
import email
import logging
import os
from datetime import datetime
from email.mime.text import MIMEText
from typing import ClassVar, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from teton_email_agent.models import EmailContent

logger = logging.getLogger(__name__)

# Constants for default paths
DEFAULT_CREDENTIALS_PATH = "credentials.json"
DEFAULT_TOKEN_PATH = "token.json"  # nosec - This is a filename, not a password


class GmailIntegration:
    """Gmail API integration"""

    SCOPES: ClassVar[List[str]] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(
        self, credentials_path: str = DEFAULT_CREDENTIALS_PATH, token_path: str = DEFAULT_TOKEN_PATH
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.last_check_time = None

    async def authenticate(self) -> bool:
        """Authenticate with Gmail"""
        try:
            creds = None

            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        logger.warning("Gmail credentials not found")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())

            self.service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail authenticated successfully")
        except Exception:
            logger.exception("Gmail authentication failed")
            return False
        else:
            return True

    async def get_new_emails(
        self, since_timestamp: Optional[datetime] = None
    ) -> List[EmailContent]:
        """Get new emails"""
        if not self.service:
            return []

        try:
            query = "is:unread"
            if since_timestamp:
                date_str = since_timestamp.strftime("%Y/%m/%d")
                query += f" after:{date_str}"

            results = (
                self.service.users().messages().list(userId="me", q=query, maxResults=10).execute()
            )

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                email_content = await self._get_email_content(message["id"])
                if email_content:
                    emails.append(email_content)

            self.last_check_time = datetime.now()
            logger.info(f"Retrieved {len(emails)} new emails")
        except HttpError:
            logger.exception("Error fetching emails")
            return []
        else:
            return emails

    async def _get_email_content(self, message_id: str) -> Optional[EmailContent]:
        """Get email content"""
        if not self.service:
            return None

        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = message["payload"].get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            date_header = next((h["value"] for h in headers if h["name"] == "Date"), None)

            # IMPORTANT: Get the actual email Message-ID for threading
            email_message_id = next(
                (h["value"] for h in headers if h["name"] == "Message-ID"), None
            )
            references = next((h["value"] for h in headers if h["name"] == "References"), "")

            timestamp = datetime.now()
            if date_header:
                with contextlib.suppress(Exception):
                    timestamp = email.utils.parsedate_to_datetime(date_header)

            body = self._extract_body(message["payload"])

            # Create EmailContent with threading info
            email_content = EmailContent(
                sender=sender,
                subject=subject,
                body=body,
                message_id=message_id,  # Gmail message ID
                timestamp=timestamp,
            )

            # Add threading information as extra attributes
            email_content.email_message_id = email_message_id  # Actual email Message-ID
            email_content.references = references

        except Exception:
            logger.exception("Error getting email content")
            return None
        else:
            return email_content

    def _extract_body(self, payload) -> str:
        """Extract email body - simplified version"""
        body = ""

        # Handle multipart messages
        if "parts" in payload:
            for part in payload["parts"]:
                extracted = self._extract_text_from_part(part)
                if extracted:
                    body = extracted
                    break
        else:
            # Handle simple messages
            body = self._extract_text_from_part(payload)

        # Clean up the body
        body = body.strip()

        # Log the extracted body for debugging
        logger.info(f"Extracted email body (first 100 chars): {body[:100]}...")

        return body

    def _extract_text_from_part(self, part) -> str:
        """Helper to extract text from a message part"""
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode("utf-8")
                except Exception:
                    logger.warning("Failed to decode email part")

        # Handle nested parts
        if "parts" in part:
            for nested_part in part["parts"]:
                extracted = self._extract_text_from_part(nested_part)
                if extracted:
                    return extracted

        return ""

    async def send_reply(self, original_email: EmailContent, reply_content: str) -> bool:
        """Send reply with proper threading"""
        if not self.service:
            return False

        try:
            # Create the reply message
            message = MIMEText(reply_content)
            message["to"] = original_email.sender
            message["subject"] = (
                f"Re: {original_email.subject.replace('Re: ', '').replace('RE: ', '')}"
            )

            # CRITICAL: Add threading headers for Gmail conversation grouping
            if hasattr(original_email, "email_message_id") and original_email.email_message_id:
                # Set In-Reply-To header (most important for threading)
                message["In-Reply-To"] = original_email.email_message_id

                # Set References header (chain of message IDs)
                references = []
                if hasattr(original_email, "references") and original_email.references:
                    references.extend(original_email.references.split())
                references.append(original_email.email_message_id)
                message["References"] = " ".join(references)

                logger.info(f"Threading reply with In-Reply-To: {original_email.email_message_id}")
            else:
                logger.warning("No Message-ID found - reply may not thread properly")

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            logger.info(
                f"Threaded reply sent to {original_email.sender} (Message ID: {result.get('id')})"
            )

        except Exception:
            logger.exception("Error sending threaded reply")
            return False
        else:
            return True

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        if not self.service:
            return False

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

            logger.info(f"Marked email {message_id} as read")
        except Exception:
            logger.exception(f"Error marking email {message_id} as read")
            return False
        else:
            return True

    async def start_monitoring(self, callback, interval: int = 60):
        """Start monitoring for new emails"""
        logger.info("Starting email monitoring")

        while True:
            try:
                new_emails = await self.get_new_emails(self.last_check_time)
                for email in new_emails:
                    try:
                        await callback(email)
                    except Exception:
                        logger.exception(f"Error in callback for email {email.message_id}")
                    finally:
                        # Always mark as read to prevent reprocessing, even on errors
                        await self.mark_as_read(email.message_id)

                await asyncio.sleep(interval)
            except Exception:
                logger.exception("Error in monitoring")
                await asyncio.sleep(interval)
