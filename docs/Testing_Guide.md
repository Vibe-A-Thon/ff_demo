# Testing Guide

## Running Tests
```bash
pytest -v
```

## Test Layout
- tests/conftest.py wires the in-memory DB for API tests.
- tests/fixtures.py and tests/mock_data provide fixtures and synthetic payloads.
- API integration tests live in tests/test_api_*.py.
- E2E war loop tests live in tests/test_e2e_*.py.

## Coverage
```bash
pytest --cov=backend/app --cov-report=term-missing --cov-fail-under=40
```

## Test Types
- **Unit Tests**: Core utilities, RBAC, logging, RSB utilities, and RAG helpers.
- **Integration Tests**: FastAPI endpoints via TestClient.
- **E2E Tests**: War loop flow using in-memory DB and deterministic mocks.

## Adding New Tests
1. Add fixtures in tests/fixtures.py for reusable data.
2. Keep tests deterministic with fixed seeds or mocks.
3. Use parameterized tests for edge cases.
4. Update coverage expectations if new modules are added.
