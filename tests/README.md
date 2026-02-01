# Test Suite Overview

## Structure
- Unit tests for core utilities and services.
- Integration tests for FastAPI endpoints using TestClient.
- E2E tests for battle and war loop flows using in-memory DB.

## Running Tests
```bash
pytest -v
```

## Coverage
```bash
pytest --cov=backend/app --cov-report=term-missing --cov-fail-under=85
```
