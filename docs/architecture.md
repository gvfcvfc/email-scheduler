## System Overview
- FastAPI backend
- PostgreSQL database
- Celery worker for async email sending
- JWT authentication

## Core Flow
User → API → DB → Celery → Email sent