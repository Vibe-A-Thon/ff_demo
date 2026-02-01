# Test Suite Overview

## Structure
- Unit tests for core utilities and services.
- Integration tests for FastAPI endpoints using TestClient.
- E2E tests for battle and war loop flows using in-memory DB.

## Running Tests
```bash
pytest -v
```

## Layout
- tests/conftest.py: In-memory DB wiring for API tests.
- tests/fixtures.py: Reusable fixtures and helpers.
- tests/mock_data/: Synthetic RSB and payload fixtures.

## Coverage
```bash
pytest --cov=backend/app --cov-report=term-missing --cov-fail-under=85
```
