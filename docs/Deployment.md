# Deployment Guide

## Local Deployment (Docker Compose)
1. Copy environment variables:
   - Create backend/.env with MongoDB URI, JWT secret, and optional OpenAI key.
2. Start services:
   - `docker-compose up --build`
3. Backend API:
   - http://localhost:8000
4. Frontend:
   - http://localhost:3000

### Compose Services
- backend: FastAPI API service.
- frontend: React UI.
- mongo: Primary document store.
- db, redis, chromadb, neo4j: Optional expansion services for Phase 1.

## Manual Backend Run
1. `cd backend`
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload`

## CI/CD
- GitHub Actions runs lint, type checks, security scan, and pytest with coverage gating.
- Coverage threshold: 40% (see .coveragerc).

## Environment Variables
- `MONGO_URL`
- `DB_NAME`
- `JWT_SECRET_KEY`
- `OPENAI_API_KEY` (optional)
- `OPENAI_EMBEDDING_MODEL` (optional)
- `CORS_ORIGINS`

## Security Notes
- Never commit secrets. Use environment variables or secret managers.
- Production should use a managed MongoDB service and rotate JWT secrets periodically.
