# 🤖 Autonomous Email Agent

AI-powered email assistant that automatically processes Gmail and takes intelligent actions.

## ⚡ Quick Start

```bash
# 1. Setup
make install

# 2. Configure .env with:
#   - GROQ_API_KEY
#   - EMAIL_WHITELIST

# 3. Setup Gmail OAuth
#   - Download credentials.json from Google Cloud Console
#   - Enable Gmail API

# 4. Run
make run
```

## 🚀 Features

- **Smart Email Processing**: Understands email content using Groq LLM
- **Autonomous Actions**: Replies, archives, flags urgent, schedules meetings
- **Gmail Integration**: Real-time monitoring with proper email threading
- **Security**: Email whitelist prevents unauthorized processing
- **Web Interface**: Monitor agent activity at `http://localhost:8000`

## 🔧 Commands

```bash
make run          # Start the agent
make demo         # Run demo
make test         # Run tests
make help         # See all commands
```

## 📊 Monitoring

- **Status**: `GET /agent/status`
- **Logs**: `GET /agent/logs`
- **Test**: `POST /emails/test`

## 🛡️ Security

Only processes emails from whitelisted senders. Configure in `.env`:
```
EMAIL_WHITELIST=trusted@domain.com,another@domain.com
```

## 🏗️ Architecture

```
Email → Gmail API → Agent (Groq LLM) → Tools → Actions
```

Built with FastAPI, Pydantic, and async Python for production reliability.