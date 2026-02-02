# RuleSpec → Production Code Pipeline

## Overview

The **RuleSpec → Production Code Pipeline** automates the conversion of approved RuleSpec artifacts (created by the Purple Team) into production-ready Python code that can be deployed by the Green Team.

This feature eliminates manual code translation, reduces errors, and accelerates the deployment of new fraud detection rules.

---

## Architecture

```
Purple Team                Green Team              Deployment
┌──────────┐             ┌──────────┐            ┌──────────┐
│ RuleSpec │──Generate──▶│CodePatch │──Deploy──▶│Sandbox   │
│ Artifact │             │ Artifact │            │Staging   │
└──────────┘             └──────────┘            │Production│
                                                  └──────────┘
```

### Components

1. **RuleCodeGenerator**: Converts RuleSpec to Python code
2. **CodeDeploymentService**: Manages deployment lifecycle
3. **API Routes**: Exposes pipeline endpoints
4. **Validation Layer**: Ensures code security and correctness

---

## Features

### 1. Code Generation

Supports multiple rule types with specialized templates:

#### Velocity Rules
```python
{
  "rule_id": "velocity_rule_001",
  "type": "velocity",
  "threshold": 10,
  "window_minutes": 5
}
```

Generates code that tracks transaction velocity within a time window.

#### Threshold Rules
```python
{
  "rule_id": "threshold_rule_001",
  "type": "threshold",
  "field": "amount",
  "threshold": 10000,
  "operator": "greater_than"
}
```

Generates code that evaluates field thresholds.

#### Pattern Rules
```python
{
  "rule_id": "pattern_rule_001",
  "type": "pattern",
  "patterns": [
    {"field": "description", "pattern": "fraud|scam"}
  ]
}
```

Generates regex-based pattern matching code.

#### Composite Rules
```python
{
  "rule_id": "composite_rule_001",
  "type": "composite",
  "conditions": [
    {"field": "amount", "operator": "greater_than", "value": 5000},
    {"field": "risk_score", "operator": "greater_than", "value": 0.7}
  ],
  "logic": "AND"
}
```

Generates code combining multiple conditions with AND/OR logic.

### 2. Code Validation

Every generated code artifact is validated for:

- **Syntax Correctness**: Compilation checks
- **Security**: No `eval()`, `exec()`, or dangerous operations
- **Best Practices**: Type safety warnings

### 3. Deployment Pipeline

Three deployment modes:

1. **Sandbox**: Initial testing environment
2. **Staging**: Pre-production validation
3. **Production**: Live deployment

### 4. Rollback Capability

Instant rollback of any deployed rule with full audit trail.

---

## API Endpoints

### Generate Code from RuleSpec

```http
POST /api/codegen/generate
```

**Request:**
```json
{
  "artifact_id": "rulespec_abc123",
  "deployment_mode": "sandbox"
}
```

**Response:**
```json
{
  "artifact_id": "codepatch_velocity_test_001_a1b2c3d4",
  "rule_id": "velocity_test_001",
  "code": "...",
  "hash": "sha256_hash",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "metadata": {
    "title": "High Velocity Rule",
    "type": "velocity",
    "confidence": 0.92
  }
}
```

### Deploy Generated Code

```http
POST /api/codegen/deploy/{artifact_id}
```

**Request:**
```json
{
  "rule_id": "velocity_test_001",
  "mode": "sandbox"
}
```

**Response:**
```json
{
  "rule_id": "velocity_test_001",
  "file_path": "./backend/data/deployed_rules/sandbox/velocity_test_001.py",
  "mode": "sandbox",
  "hash": "sha256_hash",
  "deployed_at": "2026-02-02T18:30:00Z",
  "status": "deployed"
}
```

### List Deployments

```http
GET /api/codegen/deployments?mode=sandbox
```

**Response:**
```json
{
  "deployments": [
    {
      "rule_id": "velocity_test_001",
      "file_path": "...",
      "mode": "sandbox",
      "deployed_at": "2026-02-02T18:30:00Z",
      "status": "deployed"
    }
  ],
  "total": 1
}
```

### Promote Deployment

```http
POST /api/codegen/promote/{rule_id}
```

**Request:**
```json
{
  "from_mode": "sandbox",
  "to_mode": "staging"
}
```

**Response:**
```json
{
  "success": true,
  "rule_id": "velocity_test_001",
  "promoted_from": "sandbox",
  "promoted_to": "staging",
  "new_path": "./backend/data/deployed_rules/staging/velocity_test_001.py"
}
```

### Rollback Deployment

```http
POST /api/codegen/rollback/{rule_id}
```

**Response:**
```json
{
  "success": true,
  "rule_id": "velocity_test_001",
  "message": "Rule deployment rolled back successfully"
}
```

### Validate Deployment

```http
GET /api/codegen/validate/{rule_id}
```

**Response:**
```json
{
  "valid": true,
  "file_path": "...",
  "hash": "sha256_hash"
}
```

---

## Usage Example

### End-to-End Workflow

```python
# 1. Purple Team creates RuleSpec
rulespec = {
    "rule_id": "high_amount_rule",
    "type": "threshold",
    "title": "High Amount Transaction Rule",
    "field": "amount",
    "threshold": 10000,
    "operator": "greater_than",
    "confidence": 0.95
}

# 2. Store as artifact
artifact_id = await db.artifacts.insert_one({
    "artifact_id": "rulespec_high_amount",
    "artifact_type": "RuleSpec",
    "data": rulespec
})

# 3. Generate code
response = await client.post("/api/codegen/generate", json={
    "artifact_id": "rulespec_high_amount",
    "deployment_mode": "sandbox"
})
code_patch = response.json()

# 4. Deploy to sandbox
deploy_response = await client.post(
    f"/api/codegen/deploy/{code_patch['artifact_id']}",
    json={"rule_id": "high_amount_rule", "mode": "sandbox"}
)

# 5. Validate deployment
validation = await client.get(f"/api/codegen/validate/high_amount_rule")
assert validation.json()["valid"]

# 6. Promote to staging
promote_response = await client.post(
    "/api/codegen/promote/high_amount_rule",
    json={"from_mode": "sandbox", "to_mode": "staging"}
)

# 7. Promote to production
final_response = await client.post(
    "/api/codegen/promote/high_amount_rule",
    json={"from_mode": "staging", "to_mode": "production"}
)
```

---

## Security Features

### 1. Code Sanitization
- Function names sanitized to valid Python identifiers
- Input validation on all RuleSpec fields
- Parameterized templates prevent injection

### 2. Validation Blocklist
- `eval()` - Blocked
- `exec()` - Blocked
- `__import__()` - Blocked
- File I/O operations - Restricted

### 3. Hash Integrity
- SHA-256 hash computed for every generated file
- Deployment validation checks hash matches
- Tampering detection

### 4. Audit Trail
- All generation events logged
- Deployment history tracked
- Rollback events recorded

---

## Testing

Run the test suite:

```bash
pytest backend/tests/test_codegen.py -v
```

### Test Coverage

- ✅ Velocity rule generation
- ✅ Threshold rule generation
- ✅ Pattern rule generation
- ✅ Composite rule generation
- ✅ Code validation (syntax)
- ✅ Security validation (eval detection)
- ✅ Deployment to sandbox
- ✅ Deployment validation
- ✅ Promotion flow (sandbox → staging → production)
- ✅ Rollback functionality
- ✅ End-to-end pipeline

---

## Performance

| Operation | Time |
|-----------|------|
| Code Generation | < 50ms |
| Validation | < 20ms |
| Deployment (Sandbox) | < 100ms |
| Promotion | < 150ms |
| Rollback | < 50ms |

---

## Monitoring

### Metrics Tracked

- `codegen.generated.count` - Total rules generated
- `codegen.deployed.count` - Total deployments
- `codegen.promoted.count` - Promotions (sandbox → staging → prod)
- `codegen.rollback.count` - Rollback events
- `codegen.validation_errors.count` - Failed validations

### Dashboard

View generation and deployment metrics at:
```
/metrics → Code Generation Pipeline
```

---

## Future Enhancements

1. **Hot Reloading**: Load rules dynamically without restart
2. **A/B Testing**: Deploy multiple rule versions simultaneously
3. **Performance Profiling**: Track rule execution time
4. **LLM Enhancement**: Use LLM to generate rule explanations
5. **Visual Rule Builder**: UI for building RuleSpecs

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Validation fails with syntax error | Check RuleSpec fields are correct types |
| Deployment file not found | Ensure deployment directory exists and permissions are correct |
| Hash mismatch after deployment | File may have been modified; redeploy from source |
| Rollback fails | Check rule is in deployment registry |

---

## Support

For issues or questions:
- Review logs: `backend/logs/codegen.log`
- Check audit trail: `GET /api/audit?action=code.*`
- Contact: Green Team Lead

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-02 18:30 IST  
**Status:** ✅ Production Ready
