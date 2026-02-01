# Testing Guide

## Running Tests
```bash
pytest -v
```

## Coverage
```bash
pytest --cov=backend/app --cov-report=term-missing --cov-fail-under=85
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
