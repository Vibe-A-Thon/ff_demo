# Fraud Forge Demo (ff_demo)

## Architecture Overview
Fraud Forge is an AI-vs-AI fraud defense platform with an eight-team war loop. The backend exposes FastAPI services for battles, workflow governance, approvals, RSB package management, and explainability. The frontend provides War Room, Evidence, and RSB management UI.

See [docs/Architecture.md](docs/Architecture.md) for the full system overview.

## RBAC & Security
- RBAC roles and permissions are documented in [RBAC.md](RBAC.md).
- API endpoints enforce role-based permissions via `require_permission`.

## Setup
1. Configure environment variables in a .env file (see backend/.env for required values).
2. Start services with Docker Compose.
3. Start the backend:
	- `cd backend`
	- `uvicorn app.main:app --reload`
4. Start the frontend:
	- `cd frontend`
	- `npm install`
	- `npm start`

## Testing
- Unit and integration tests: `pytest -v`
- Coverage: `pytest --cov=backend/app --cov-report=term-missing --cov-fail-under=85`

See [docs/Testing_Guide.md](docs/Testing_Guide.md) for more details.

## Deployment
- Use Docker Compose for local deployments.
- CI runs linting, type checking, security scanning, and test coverage enforcement.
- See [docs/Deployment.md](docs/Deployment.md) for environment configuration details.

## Notes
- The backend uses MongoDB for persistence.
- Additional services (Postgres, Redis, ChromaDB, Neo4j) are provisioned for Phase 1 infrastructure expansion.
