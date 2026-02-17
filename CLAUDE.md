# TickAlert

## Notes for Claude
1. "Before writing any code, describe your approach and wait for approval. Always ask clarifying questions before writing any code if requirements are ambiguous."

2. "If a task requires changes to more than 3 files, stop and break it into smaller tasks first."

3. "After writing code, list what could break and suggest tests to cover it."

4. "When there's a bug, start by writing a test that reproduces it, then fix it until the test passes."

5. "Every time I correct you, add a new rule to the CLAUDE .md file so it never happens again."

## Project Tech Stack (MVP)

### Core
- Language: Python 3.11+
- Telegram framework: aiogram (v3, async)
- Delivery model: Webhook (FastAPI endpoint)
- ASGI server: Uvicorn

### Infrastructure
- Containerization: Docker
- Hosting: Railway (Web Service)
- Database: PostgreSQL (Railway Postgres)

### Data / Persistence
- DB driver: asyncpg
- ORM: SQLAlchemy 2.0 (async) + Alembic migrations

### DevOps
- Version control: git + GitHub
- Configuration: environment variables (.env locally, Railway vars in prod)
- Logging: standard logging / structlog (pick one, keep consistent)

### Repo conventions
- src/ (application code)
- handlers/ (bot routes/commands/callbacks)
- db/ (models, session, repositories)
- config.py (reads env vars only)
- No secrets committed (BOT_TOKEN, DATABASE_URL, WEBHOOK_SECRET are env-only)