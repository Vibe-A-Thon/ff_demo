# Fraud Forge Architecture

## Overview
Fraud Forge is an AI-vs-AI fraud defense system built around an eight-team war loop. The backend provides FastAPI services for battles, RSB package management, workflow governance, and auditability. The frontend delivers operator and reviewer experiences for War Room, Evidence, RSB Manager, and approvals.

## Eight-Team War Loop
1. **Red** – Simulate adversarial fraud scenarios
2. **Blue** – Detect and respond in real time
3. **Purple** – Draft RuleSpecs and strategy
4. **Green** – Generate patches and code artifacts
5. **Black** – Execute stress and replay tests
6. **Orange** – Review and approve changes
7. **White** – Compliance and audit checks
8. **Gold** – Explainability and narrative output

## Core Services
- **API Layer**: FastAPI routes in backend/app/routes for battles, runs, workflows, RSB packages, approvals, and RAG.
- **Service Layer**: Workflow engine, rule validation, and RSB utilities in backend/app.
- **Persistence Layer**: MongoDB collections for users, runs, approvals, evidence, and audit logs accessed via backend/app/db.py.
- **Agent Orchestration**: Team-specific agent orchestration in backend/app/agents.py and backend/app/agent_registry.py.

## Repo Layout Mapping
- backend/app/core: Cross-cutting concerns (logging, exceptions, request context, RBAC).
- backend/app/routes: API surface and FastAPI endpoints.
- backend/app/models.py: Pydantic models for API and persistence.
- frontend/src: UI screens and components.
- tests: Unit/integration/E2E tests with in-memory DB fixtures.

## Governance
- **HITL/HOTL Modes**: Human approvals gate risky steps; autonomous actions are logged with evidence.
- **RBAC**: Role-based permissions enforced for workflow control, RSB patching, and approvals.
- **Audit Trail**: Every action is captured with actor, artifact, decision, and evidence references.

## Observability
- Structured JSON logging with correlation IDs.
- Global exception handling with consistent error responses.
- Audit logs persisted for compliance reporting.
