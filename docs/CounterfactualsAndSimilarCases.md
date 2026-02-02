# Counterfactuals & Similar-Case Retrieval Feature

## Overview

The **Counterfactuals & Similar-Case Retrieval** feature provides explainable AI (XAI) capabilities for the Fraud Forge platform. It generates actionable counterfactual explanations and retrieves historically similar cases by analyzing real evidence packs and telemetry data.

## Architecture

### Components

1. **CounterfactualService** (`backend/app/services/counterfactual_service.py`)
   - Extracts features from evidence items
   - Extracts triggered rules from evidence and events
   - Generates feature-based counterfactuals
   - Generates rule-based counterfactuals
   - Provides LLM-enhanced explanations (optional)

2. **SimilarCaseService** (`backend/app/services/counterfactual_service.py`)
   - Builds case signatures from evidence items
   - Builds pack signatures from evidence packs
   - Scores similarity between cases using weighted metrics
   - Retrieves similar cases from the database

3. **API Endpoints** (`backend/app/routes/xai.py`)
   - `GET /xai/explain/{run_id}` - Enhanced explanation bundle
   - `POST /xai/counterfactuals` - Generate counterfactuals
   - `POST /xai/similar-cases` - Find similar cases
   - `GET /xai/evidence-pack/{pack_id}/similar` - Find cases similar to a pack

4. **Frontend Component** (`frontend/src/components/CounterfactualPanel.jsx`)
   - Interactive counterfactual cards with evidence links
   - Similar case cards with similarity breakdowns
   - Tabbed interface for switching between views

## Feature Details

### Counterfactual Generation

Counterfactuals answer the question: **"What would need to change for the decision to be different?"**

#### Feature Weights

| Feature             | Weight | Description             |
| ------------------- | ------ | ----------------------- |
| `risk_score`        | 0.25   | Overall risk assessment |
| `velocity_score`    | 0.15   | Transaction velocity    |
| `device_risk_score` | 0.15   | Device fingerprint risk |
| `geo_risk_score`    | 0.10   | Geographic anomaly      |
| `behavior_score`    | 0.15   | Behavioral analysis     |
| `amount`            | 0.10   | Transaction amount      |
| `anomaly_count`     | 0.05   | Number of anomalies     |
| `model_score`       | 0.05   | ML model prediction     |

#### Categorical Levels

Features with categorical values are mapped to levels:

- `low` → 0.0
- `medium` → 0.33
- `high` → 0.67
- `critical` → 1.0

#### Decision Hierarchy

| Current Decision | Target Outcomes   |
| ---------------- | ----------------- |
| `block`          | `review`, `allow` |
| `review`         | `allow`           |
| `monitor`        | `review`          |
| `allow`          | (none)            |

### Similar-Case Retrieval

Similar cases are found by comparing case signatures using multiple similarity metrics:

#### Signature Components

- **Rules**: Set of triggered rule IDs
- **Artifacts**: Evidence types, tools, teams, events
- **Tokens**: Keywords from narrative/summary text
- **Decision**: Final decision outcome
- **Metrics**: Numeric run metrics (avg_score, risk_score)
- **Features**: Extracted feature values
- **Signature Hash**: MD5 hash for quick matching

#### Similarity Scoring

| Component  | Weight | Method                      |
| ---------- | ------ | --------------------------- |
| Rules      | 0.25   | Jaccard index               |
| Artifacts  | 0.15   | Jaccard index               |
| Tokens     | 0.15   | Jaccard index               |
| Decision   | 0.15   | Exact match                 |
| Metrics    | 0.15   | Numeric similarity          |
| Features   | 0.15   | Weighted numeric similarity |
| Hash bonus | +0.10  | Exact signature match       |

## API Reference

### GET /api/xai/explain/{run_id}

Returns an enhanced explanation bundle with counterfactuals and similar cases.

**Response:**

```json
{
  "bundle_id": "uuid",
  "decision_id": "block",
  "summary": "...",
  "details": "...",
  "evidence": [...],
  "evidence_graph": {...},
  "counterfactuals": [
    {
      "label": "Reduce Risk Score",
      "changes": {"risk_score": 0.3},
      "expected_outcome": "review",
      "confidence": 0.85,
      "evidence_links": ["evidence:signal:ev-1"]
    }
  ],
  "similar_cases": [
    {
      "case_id": "pack-123",
      "summary": "Similar high-risk case",
      "similarity": 0.72,
      "metadata": {
        "matched_rules": ["R-ATO-001"],
        "score_breakdown": {...}
      }
    }
  ]
}
```

### POST /api/xai/counterfactuals

Generate counterfactuals for a specific run.

**Request:**

```json
{
  "run_id": "run-123",
  "decision": "block",
  "max_counterfactuals": 5
}
```

**Response:**

```json
{
  "run_id": "run-123",
  "decision": "block",
  "counterfactuals": [...],
  "features_used": 5,
  "rules_used": 3,
  "generated_at": "2024-01-15T12:00:00Z"
}
```

### POST /api/xai/similar-cases

Find similar cases for a run.

**Request:**

```json
{
  "run_id": "run-123",
  "min_similarity": 0.2,
  "max_results": 5
}
```

**Response:**

```json
{
  "run_id": "run-123",
  "similar_cases": [...],
  "signature_hash": "abc123def456",
  "generated_at": "2024-01-15T12:00:00Z"
}
```

## Usage Examples

### Backend (Python)

```python
from app.services.counterfactual_service import (
    CounterfactualService,
    SimilarCaseService,
)
from app.models import EvidenceItem

# Initialize services
cf_service = CounterfactualService()
sc_service = SimilarCaseService()

# Extract features from evidence
features = cf_service.extract_features_from_evidence(evidence_items)

# Generate counterfactuals
counterfactuals = cf_service.generate_combined_counterfactuals(
    features, rules, "block", run_metrics
)

# Build case signature
signature = sc_service.build_case_signature(
    run_id, decision, evidence_items, events, metrics
)

# Find similar cases
similar_cases = await sc_service.find_similar_cases(
    signature, evidence_packs, min_similarity=0.2
)
```

### Frontend (React)

```jsx
import { xaiAPI } from "../lib/api";
import CounterfactualPanel from "../components/CounterfactualPanel";

// Use the panel component
<CounterfactualPanel
  runId="run-123"
  onViewPack={(packId) => navigate(`/evidence/${packId}`)}
/>;

// Or call APIs directly
const { data } = await xaiAPI.getCounterfactuals({
  run_id: "run-123",
  max_counterfactuals: 5,
});
```

## Testing

Run the counterfactual service tests:

```bash
cd ff_demo
python -m pytest tests/test_counterfactual_service.py -v
python -m pytest tests/test_xai_utils.py -v
```

## Evidence Linking

All counterfactuals and similar cases are linked to real evidence:

1. **Counterfactuals** include:
   - `evidence_links`: List of evidence item references
   - `rule_id`: Associated rule (if rule-based)
   - `feature_importance`: Weight of the feature

2. **Similar Cases** include:
   - `evidence_pack_id`: Reference to the matching pack
   - `matched_rules`: Rules shared between cases
   - `score_breakdown`: Detailed similarity metrics

## LLM Enhancement (Optional)

When an LLM client is configured, the service can:

1. Generate enhanced counterfactual descriptions
2. Create context-aware summaries
3. Explain rule interactions

```python
# With LLM client
cf_service = CounterfactualService(llm_client=llm_client)
enhanced_desc = await cf_service.generate_llm_counterfactual_explanation(
    counterfactual, context="..."
)
```

## Configuration

The feature uses the following constants (defined in `counterfactual_service.py`):

- `FEATURE_WEIGHTS`: Weight for each feature in scoring
- `CATEGORICAL_LEVELS`: Mapping for categorical features
- `DECISION_HIERARCHY`: Target outcomes for each decision
- `NUMERIC_KEYS` / `CATEGORICAL_KEYS`: Feature type classification

## Status

✅ **100% Complete**

- [x] Feature extraction from evidence
- [x] Rule extraction from evidence and events
- [x] Feature-based counterfactual generation
- [x] Rule-based counterfactual generation
- [x] Case signature building
- [x] Similarity scoring with weighted metrics
- [x] Similar case retrieval
- [x] API endpoints
- [x] Frontend component
- [x] Evidence linking
- [x] LLM enhancement (optional)
- [x] Unit tests
- [x] Documentation
