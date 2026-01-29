# RSB (Rule Suite Box) Format Understanding Document

## Executive Summary

This document provides a comprehensive understanding of the RSB (Rule Suite Box) file format used by Fraud Forge to package and distribute fraud detection rules. This understanding is critical for building the Fraud Forge Client Application, which must parse, visualize, merge, and deploy RSB files.

**Based on Analysis of:** `RS_ACCOUNT_TAKEOVER.rsb`
<UID> = <9 digit unique Number>_ddmmyyyy_X where X is a primenumber. eg: 000000001_22012026_1
---

## 1. RSB File Format Overview

### 1.1 What is an RSB File?

An **RSB (Rule Suite Box)** file is a **ZIP archive** containing:
- Fraud detection rule definitions (metadata and logic)
- Executable rule implementation code (Python)
- Test suites and validation logic
- Compliance and explainability documentation
- Patch/integration scripts for deployment

**Key Characteristics:**
- **Format:** ZIP archive (`.rsb` extension)
- **Compression:** Deflate compression method
- **Version:** ZIP format v2.0+
- **Structure:** Well-organized directory hierarchy
- **Platform:** Python-based implementation
- **Self-contained:** Everything needed to deploy a rule

### 1.2 RSB File Structure

```
RS_ACCOUNT_TAKEOVER.rsb (ZIP Archive)
│
├── manifest.json                           # RSB metadata and versioning
│
├── rule/                                   # Rule definition directory
│   ├── specification.json                  # Rule specification (structured)
│   ├── description.md                      # Human-readable description
│   ├── rule.json                          # Complete rule definition
│   └── rule_Patch.py                      # Script to patch rule into registry
│
├── code/                                   # Executable implementation
│   ├── ruleC_RS_ACCOUNT_TAKEOVER_<UID>.py      # Core rule logic
│   └── ruleCP_RS_ACCOUNT_TAKEOVER_<UID>.py     # Code patch helper
│
├── tests/                                  # Test suites
│   ├── ruleUT_RS_ACCOUNT_TAKEOVER_<UID>.py     # Unit tests
│   ├── ruleIT_RS_ACCOUNT_TAKEOVER_<UID>.py     # Integration tests
│   ├── ruleUTP_RS_ACCOUNT_TAKEOVER_<UID>.py    # Unit test (patched)
│   └── ruleITP_RS_ACCOUNT_TAKEOVER_<UID>.py    # Integration test (patched)
│
├── testcases/                                         # Testing
│   ├── RS_ACCOUNT_TAKEOVER_<UID>_edge_cases.json      # Edge case test data
│   ├── RS_ACCOUNT_TAKEOVER_<UID>_edge_cases_Data.json # Test data
│   └── RS_ACCOUNT_TAKEOVER_<UID>_test_results.json    # Test results summary
│
└── compliance/                             # Explainability & compliance
    ├── RS_ACCOUNT_TAKEOVER_<UID>_xai.json  # Explainable AI metadata
    ├── RS_ACCOUNT_TAKEOVER_<UID>_Business_explanation.md
    ├── RS_ACCOUNT_TAKEOVER_<UID>_Dev_explanation.md
    └── RS_ACCOUNT_TAKEOVER_<UID>_Compliance_explanation.json
```

**File Count:** 18 files

---

## 2. Detailed File Format Specifications

### 2.1 manifest.json

**Purpose:** RSB-level metadata identifying the package

**Schema:**
```json
{
  "attack_type": "string",        // Type of fraud this rule detects
  "created_at": "ISO8601",        // Creation timestamp (UTC)
  "format": "string",             // Always "RSB"
  "name": "string",               // Human-readable rule name
  "rule_id": "string",            // Unique rule identifier
  "rule_version": "semver",       // Semantic version (e.g., "1.0.0")
  "version": "string"             // RSB format version
}
```

**Example:**
```json
{
  "attack_type": "account_takeover",
  "created_at": "2026-01-24T11:02:48.985959+00:00",
  "format": "RSB",
  "name": "Detect account_takeover",
  "rule_id": "R-ACCOUNT_TAKEOVER",
  "rule_version": "1.0.0",
  "version": "1.0"
}
```

**Key Fields:**
- **rule_id**: Primary identifier (e.g., `R-ACCOUNT_TAKEOVER`)
- **attack_type**: Fraud category classification
- **created_at**: UTC timestamp for version tracking
- **rule_version**: Semantic versioning for rule evolution

---

### 2.2 rule/specification.json

**Purpose:** Structured rule specification for rule engines

**Schema:**
```json
{
  "action": "string",             // Action to take if rule matches
  "conditions": ["array"],        // Rule trigger conditions (can be empty)
  "confidence": "float",          // Confidence score (0.0 - 1.0)
  "description": "string",        // Brief description
  "name": "string",               // Rule display name
  "rule_id": "string"             // Matches manifest.json rule_id
}
```

**Example:**
```json
{
  "action": "review",
  "conditions": [],
  "confidence": 0.7,
  "description": "Generated rule",
  "name": "Detect account_takeover",
  "rule_id": "R-ACCOUNT_TAKEOVER"
}
```

**Key Fields:**
- **action**: What to do when rule triggers
  - Possible values: `review`, `block`, `flag`, `alert`, `score`
- **confidence**: How confident the AI is (0.7 = 70% confidence)
- **conditions**: Rule logic conditions (empty = pattern-based detection)

---

### 2.3 rule/rule.json

**Purpose:** Complete rule definition (superset of specification.json)

**Schema:**
```json
{
  "action": "string",
  "conditions": ["array"],
  "confidence": "float",
  "description": "string",
  "name": "string",
  "rule_id": "string",
  "version": "semver"             // Rule version (added field)
}
```

**Example:**
```json
{
  "action": "review",
  "conditions": [],
  "confidence": 0.7,
  "description": "Generated rule",
  "name": "Detect account_takeover",
  "rule_id": "R-ACCOUNT_TAKEOVER",
  "version": "1.0.0"
}
```

**Differences from specification.json:**
- Includes `version` field
- May include additional metadata fields in production RSBs

---

### 2.4 rule/description.md

**Purpose:** Human-readable markdown description for documentation

**Format:** Markdown

**Example:**
```markdown
# Detect account_takeover

Generated rule
```

**Usage:**
- Display in Client Application UI
- Include in audit reports
- Documentation generation

---

### 2.5 code/ruleC_*.py - Core Rule Implementation

**Purpose:** Executable Python function implementing the fraud detection logic

**File Naming Convention:**
```
ruleC_<attack_type>_<RULE_ID>.py
Example: ruleC_RS_ACCOUNT_TAKEOVER_<UID>.py
```

**Code Structure:**
```python
def detect_r_<rule_name>(txs):
    """Auto-generated rule: <Rule Name>
    
    Returns a non-empty value to flag suspicious behavior.
    
    Rule ID: <RULE_ID>
    Action: <action>
    Confidence: <confidence>
    """
    txs = txs or []
    
    # Feature extraction
    amounts = []
    patterns = []
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        try:
            amounts.append(float(tx.get('amount', 0.0)))
        except Exception:
            amounts.append(0.0)
        md = tx.get('metadata') or {}
        patterns.append(md.get('pattern'))
    
    # Computed features
    tx_count = len(amounts)
    max_amount = max(amounts) if amounts else 0.0
    min_amount = min(amounts) if amounts else 0.0
    total_amount = sum(amounts) if amounts else 0.0
    
    # Rule logic
    if (any(p == 'account_takeover' for p in patterns)):
        return [{
            'signal': 'rule_match',
            'rule_id': 'R-ACCOUNT_TAKEOVER',
            'tx_count': tx_count,
            'max_amount': max_amount
        }]
    
    return None
```

**Key Aspects:**
- **Input:** `txs` - List of transaction dictionaries
- **Output:** 
  - `None` or empty → Allow transaction
  - Non-empty list/dict → Flag transaction
- **Return Format:** List of signal dictionaries with metadata
- **Pattern Detection:** Checks transaction metadata for fraud patterns

**Transaction Dictionary Format:**
```python
{
    'transaction_id': 'string',
    'timestamp': 'ISO8601',
    'account_id': 'string',
    'counterparty_id': 'string',
    'amount': float,
    'currency': 'string',
    'metadata': {
        'pattern': 'string',        # Fraud pattern identifier
        # ... other metadata
    }
}
```

---

### 2.6 code/ruleCP_*.py - Code Patch Helper

**Purpose:** Script to integrate rule code into existing Python rule suite files

**Functionality:**
- Adds import marker to external suite file
- Idempotent (safe to run multiple times)
- Creates suite file if it doesn't exist

**Usage:**
```bash
python ruleCP_RS_ACCOUNT_TAKEOVER_<UID>.py \
    --suite-file /path/to/Rules_Suite_account_takeover.py \
    --module-file /path/to/code/ruleC_*.py
```

**Import Marker Format:**
```python
### RSB_IMPORT account_takeover RS_ACCOUNT_TAKEOVER
```

---

### 2.7 rule/rule_Patch.py - Rule Registry Patcher

**Purpose:** Script to add rule definition to an external JSON registry

**Functionality:**
- Reads `rule/rule.json`
- Appends to target registry JSON file
- Prevents duplicate entries (by rule_id)
- Creates registry file if missing

**Usage:**
```bash
python rule_Patch.py \
    --rule-json /path/to/rule/rule.json \
    --target /path/to/rules_registry.json
```

**Registry Format:**
```json
{
  "rules": [
    {
      "rule_id": "R-ACCOUNT_TAKEOVER",
      "name": "Detect account_takeover",
      "action": "review",
      "confidence": 0.7,
      "version": "1.0.0",
      ...
    },
    // ... more rules
  ]
}
```

---

### 2.8 tests/ - Test Suite Files

**Purpose:** Comprehensive testing infrastructure

#### 2.8.1 ruleUT_*.py - Unit Tests

**Purpose:** Unit tests for rule logic using pytest framework

**Key Features:**
- Loads rule implementation dynamically
- Tests edge cases from `edge_cases.json`
- Validates rule behavior on boundary conditions
- Normalizes outcomes (allow vs. flag)

**Test Categories:**
- **Normal cases:** Expected to return "allow"
- **Boundary cases:** Expected to return "flag"
- **Edge cases:** Extreme values, empty data, malformed input

**Example Test:**
```python
def test_ruleC_RS_ACCOUNT_TAKEOVER_<UID>_handles_edge_cases():
    # Load rule function
    func = _load_rule_callable(rule_path)
    
    # Load edge cases
    edge_cases = json.loads(ec_path.read_text())
    
    # Test each case
    for ec in edge_cases:
        txs = [{ ... }]  # Construct test transaction
        val = func(txs)
        outcome = _normalize_outcome(val)
        expected = _expected(ec['category'])
        assert outcome == expected
```

#### 2.8.2 ruleIT_*.py - Integration Tests

**Purpose:** Integration tests for rule within larger system context

**Typical Tests:**
- Rule interaction with fraud engine
- Performance benchmarks
- Concurrency tests
- Resource usage tests

#### 2.8.3 edge_cases.json

**Purpose:** Test case definitions for edge case testing

**Format:**
```json
[
  {
    "category": "boundary",        // "normal" or "boundary"
    "title": "High amount transaction",
    "example": {
      "amount": 999999.99,
      "pattern": "account_takeover"
    }
  },
  {
    "category": "normal",
    "title": "Empty transaction list",
    "example": {}
  }
]
```

#### 2.8.4 test_results.json

**Purpose:** Summary of test execution results

**Format:**
```json
{
  "passed": true,
  "failures": [],
  "warnings": []
}
```

---

### 2.9 compliance/ - Explainability & Compliance

**Purpose:** Documentation for regulatory compliance and explainability

#### 2.9.1 xai_explanation.json - Explainable AI

**Purpose:** Machine-readable explanation of rule behavior

**Schema:**
```json
{
  "narrative": "string",          // Human-readable explanation
  "key_factors": ["array"],       // Important decision factors
  "disclaimers": ["array"]        // Legal/technical disclaimers
}
```

**Use Cases:**
- Regulatory compliance (explain why transaction flagged)
- Customer dispute resolution
- Model auditing

#### 2.9.2 *_Business_explanation.md

**Purpose:** Business impact documentation

**Audience:** Business stakeholders, compliance officers

**Typical Content:**
- What fraud this rule detects
- Business impact (false positives, detection rate)
- Cost/benefit analysis
- Risk mitigation strategy

#### 2.9.3 *_Dev_explanation.md

**Purpose:** Technical implementation documentation

**Audience:** Developers, data scientists

**Typical Content:**
- Algorithm explanation
- Feature engineering details
- Performance characteristics
- Known limitations

#### 2.9.4 *_Compliance_explanation.json

**Purpose:** Structured compliance metadata

**Potential Fields:**
```json
{
  "regulation_compliance": ["GDPR", "PCI-DSS"],
  "fairness_metrics": { ... },
  "bias_testing_results": { ... },
  "data_lineage": { ... }
}
```

---

## 3. RSB File Naming Convention

**Pattern:**
```
RS_<attack_type>_<RULE_ID>.rsb
```

**Example:**
```
RS_ACCOUNT_TAKEOVER.rsb
```

**Components:**
- **RS**: "Rule Suite" prefix (standard)
- **attack_type**: Fraud category (lowercase, underscore-separated)
- **RULE_ID**: Unique rule identifier (uppercase, hyphen-separated)
- **.rsb**: RSB file extension

---

## 4. RSB Version Evolution

### 4.1 Versioning Scheme

RSB files use **semantic versioning** (semver):

```
MAJOR.MINOR.PATCH

Example: 1.0.0
```

**Version Components:**
- **MAJOR:** Incompatible API changes, major rule logic overhaul
- **MINOR:** Backward-compatible functionality additions
- **PATCH:** Backward-compatible bug fixes, threshold tuning

### 4.2 Version Update Scenarios

| Change Type | Example | Version Change |
|-------------|---------|----------------|
| Bug fix in rule logic | Fixed off-by-one error | 1.0.0 → 1.0.1 |
| Add new condition | Add device check | 1.0.1 → 1.1.0 |
| Change action | review → block | 1.1.0 → 2.0.0 |
| Threshold tuning | confidence 0.7 → 0.8 | 1.1.0 → 1.1.1 |
| Add test cases | New edge cases | 1.1.1 → 1.1.2 |

---

## 5. Network Graph Representation

### 5.1 Conceptual Model

While this specific RSB file is a **single rule**, in a complete Fraud Forge deployment:

**Rule Network Graph:**
- **Nodes:** Individual rules (e.g., R-ACCOUNT_TAKEOVER)
- **Edges:** Dependencies/execution flow between rules
  - Sequential execution (Rule A → Rule B)
  - Conditional branching (If Rule A triggers → Run Rule B)
  - Score aggregation (Rules feed into risk score calculation)

**For Visualization in Client App:**

```
Single Rule (Standalone):
  [R-ACCOUNT_TAKEOVER]
  
Multi-Rule Network:
  [R-VELOCITY_CHECK] ──→ [R-ACCOUNT_TAKEOVER] ──→ [RISK_SCORER]
           ↓                      ↓
    [R-DEVICE_CHECK]      [R-BEHAVIOR_ANALYSIS]
```

### 5.2 Network Graph Metadata

**Node Attributes:**
- **rule_id**: Unique identifier
- **name**: Display name
- **attack_type**: Category/color coding
- **confidence**: Visual size/opacity
- **action**: Visual shape/icon
- **version**: Version badge

**Edge Attributes:**
- **type**: "sequential", "conditional", "parallel"
- **weight**: Dependency strength
- **condition**: Trigger condition (if conditional)

---

## 6. RSB Integration & Deployment

### 6.1 Deployment Process

**Step 1: Extract RSB**
```bash
unzip RS_ACCOUNT_TAKEOVER.rsb -d /tmp/rsb_extract/
```

**Step 2: Validate RSB**
```bash
# Check manifest
cat /tmp/rsb_extract/manifest.json

# Validate rule definition
cat /tmp/rsb_extract/rule/rule.json

# Run tests
pytest /tmp/rsb_extract/tests/
```

**Step 3: Patch Rule Registry**
```bash
python /tmp/rsb_extract/rule/rule_Patch.py \
    --rule-json /tmp/rsb_extract/rule/rule.json \
    --target /etc/fraud_engine/rules_registry.json
```

**Step 4: Patch Code Suite**
```bash
python /tmp/rsb_extract/code/ruleCP_*.py \
    --suite-file /opt/fraud_engine/Rules_Suite_account_takeover.py
```

**Step 5: Copy Rule Implementation**
```bash
cp /tmp/rsb_extract/code/ruleC_*.py /opt/fraud_engine/rules/
```

**Step 6: Restart Fraud Engine**
```bash
systemctl restart fraud-detection-engine
```

### 6.2 Rollback Process

**Step 1: Identify Previous Version**
```bash
# From snapshot or backup
ls /var/backups/rsb/
# RS_ACCOUNT_TAKEOVER_v0.9.0.rsb
```

**Step 2: Extract Previous RSB**
```bash
unzip RS_ACCOUNT_TAKEOVER_v0.9.0.rsb -d /tmp/rsb_rollback/
```

**Step 3: Restore Registry**
```bash
# Remove current rule from registry
python remove_rule.py --rule-id R-ACCOUNT_TAKEOVER \
    --target /etc/fraud_engine/rules_registry.json

# Add old rule
python /tmp/rsb_rollback/rule/rule_Patch.py \
    --rule-json /tmp/rsb_rollback/rule/rule.json \
    --target /etc/fraud_engine/rules_registry.json
```

**Step 4: Restore Code**
```bash
cp /tmp/rsb_rollback/code/ruleC_*.py /opt/fraud_engine/rules/
```

**Step 5: Restart Engine**
```bash
systemctl restart fraud-detection-engine
```

---

## 7. Client Application Integration Points

### 7.1 File Parsing Requirements

The Fraud Forge Client Application must be able to:

**1. Extract RSB Archive**
- Unzip RSB file to temporary directory
- Handle ZIP format v2.0+ with deflate compression

**2. Read Manifest**
- Parse `manifest.json`
- Extract: rule_id, name, version, attack_type, created_at

**3. Read Rule Definition**
- Parse `rule/rule.json`
- Extract: action, confidence, description, conditions

**4. Read Rule Implementation**
- Syntax highlight Python code from `code/ruleC_*.py`
- Optional: Execute code for testing (sandbox required)

**5. Read Test Results**
- Parse `tests/test_results.json`
- Display passed/failed status

**6. Read Compliance Docs**
- Render markdown files
- Display XAI explanation

### 7.2 Visualization Requirements

**Network Graph Node:**
```javascript
{
  id: "R-ACCOUNT_TAKEOVER",
  label: "Detect account_takeover",
  category: "account_takeover",
  confidence: 0.7,
  action: "review",
  version: "1.0.0",
  status: "active",  // active, new, modified, deprecated
  // Visual properties
  color: "#FF9800",  // Based on attack_type
  size: 35,          // Based on confidence (0.7 * 50)
  shape: "diamond",  // Based on action
  // Metadata
  created_at: "2025-12-29T11:02:48Z",
  test_status: "passed"
}
```

**Color Scheme by Attack Type:**
```javascript
const attackTypeColors = {
  'account_takeover': '#FF9800',  // Orange
  'card_testing': '#2196F3',      // Blue
  'velocity': '#4CAF50',          // Green
  'behavioral': '#9C27B0',        // Purple
  'amount_based': '#F44336',      // Red
  'geolocation': '#00BCD4',       // Cyan
  'device_fraud': '#FF5722',      // Deep Orange
  'merchant_fraud': '#795548'     // Brown
};
```

**Shape by Action:**
```javascript
const actionShapes = {
  'review': 'diamond',
  'block': 'octagon',
  'flag': 'triangle',
  'alert': 'star',
  'score': 'circle'
};
```

### 7.3 Merge Logic Requirements

**When merging two RSB files:**

**Scenario 1: Same rule_id, different versions**
```
Existing: R-ACCOUNT_TAKEOVER v1.0.0 (confidence: 0.7)
New:      R-ACCOUNT_TAKEOVER v1.1.0 (confidence: 0.8)

Action: UPDATE
Decision: Replace existing with new (version upgrade)
Conflict: None (clear version progression)
```

**Scenario 2: Same rule_id, different actions**
```
Existing: R-ACCOUNT_TAKEOVER (action: review)
New:      R-ACCOUNT_TAKEOVER (action: block)

Action: CONFLICT
Decision: User must choose (action change is significant)
Options:
  - Keep existing (review)
  - Use new (block)
  - Custom (configure separately)
```

**Scenario 3: Completely new rule**
```
Existing: [no R-ACCOUNT_TAKEOVER]
New:      R-ACCOUNT_TAKEOVER v1.0.0

Action: ADD
Decision: Add new rule to network
Conflict: None
```

### 7.4 Display Requirements

**RSB Information Panel:**
```
┌─────────────────────────────────────────────────┐
│ RSB: RS_ACCOUNT_TAKEOVER     │
├─────────────────────────────────────────────────┤
│ Rule Name: Detect account_takeover              │
│ Rule ID: R-ACCOUNT_TAKEOVER                     │
│ Version: 1.0.0                                  │
│ Attack Type: account_takeover                   │
│ Created: 2025-12-29 11:02:48 UTC                │
│                                                 │
│ Action: review                                  │
│ Confidence: 70%  ████████████░░░░░░░            │
│                                                 │
│ Test Status: ✅ All tests passed                │
│ File Size: 11 KB                                │
│ Checksum: a3f7c8e9...                          │
└─────────────────────────────────────────────────┘
```

---

## 8. Data Model for Client Application

### 8.1 RSB Object Model

```typescript
interface RSB {
  // File metadata
  filename: string;
  filepath: string;
  filesize: number;
  checksum: string;
  
  // Manifest
  manifest: {
    attack_type: string;
    created_at: string;
    format: string;
    name: string;
    rule_id: string;
    rule_version: string;
    version: string;
  };
  
  // Rule definition
  rule: {
    action: 'review' | 'block' | 'flag' | 'alert' | 'score';
    conditions: any[];
    confidence: number;  // 0.0 to 1.0
    description: string;
    name: string;
    rule_id: string;
    version: string;
  };
  
  // Rule description (markdown)
  description: string;
  
  // Code implementation
  code: {
    core: string;           // Python code content
    core_path: string;      // Path to ruleC_*.py
    patch: string;          // Patch helper code
    patch_path: string;     // Path to ruleCP_*.py
  };
  
  // Test suite
  tests: {
    unit_tests: string;     // Python test code
    integration_tests: string;
    edge_cases: EdgeCase[];
    results: TestResults;
  };
  
  // Compliance
  compliance: {
    xai_explanation: XAIExplanation;
    business_explanation: string;  // Markdown
    dev_explanation: string;       // Markdown
    compliance_explanation: any;
  };
  
  // Deployment status
  status: 'available' | 'staged' | 'deployed' | 'archived';
  deployed_at?: string;
  deployed_by?: string;
}

interface EdgeCase {
  category: 'normal' | 'boundary';
  title: string;
  example: any;
}

interface TestResults {
  passed: boolean;
  failures: string[];
  warnings: string[];
}

interface XAIExplanation {
  narrative: string;
  key_factors: string[];
  disclaimers: string[];
}
```

### 8.2 Network Graph Model

```typescript
interface RuleNetwork {
  nodes: RuleNode[];
  edges: RuleEdge[];
  metadata: NetworkMetadata;
}

interface RuleNode {
  // Identity
  id: string;              // rule_id (e.g., "R-ACCOUNT_TAKEOVER")
  label: string;           // rule name
  
  // Classification
  category: string;        // attack_type
  action: string;          // review, block, etc.
  
  // Metrics
  confidence: number;      // 0.0 - 1.0
  version: string;         // semver
  
  // Status
  status: 'existing' | 'new' | 'modified' | 'deprecated';
  
  // Visual properties
  x?: number;
  y?: number;
  color: string;
  size: number;
  shape: string;
  
  // Metadata
  created_at: string;
  test_status: 'passed' | 'failed' | 'not_run';
  rsb_filename: string;
}

interface RuleEdge {
  source: string;          // source rule_id
  target: string;          // target rule_id
  type: 'sequential' | 'conditional' | 'parallel';
  weight: number;          // 0.0 - 1.0
  condition?: string;      // If type === 'conditional'
}

interface NetworkMetadata {
  total_nodes: number;
  total_edges: number;
  attack_types: string[];
  avg_confidence: number;
  version: string;
  created_at: string;
}
```

---

## 9. Key Insights for Client Development

### 9.1 Critical Design Decisions

**1. RSB is a Single Rule, Not a Network**
- Each RSB file contains ONE fraud detection rule
- Network graph is formed by deploying MULTIPLE RSB files
- Client must aggregate multiple RSBs to create network visualization

**2. Python-Based Implementation**
- Rules are implemented in Python
- Client can display code but may not execute (security concern)
- Consider sandboxed Python execution for testing

**3. Self-Contained Deployment**
- RSB includes everything: code, tests, docs, patch scripts
- Can be deployed independently
- Patch scripts handle integration with existing systems

**4. Test-Driven Quality**
- Every RSB includes comprehensive test suite
- Test results are pre-computed (test_results.json)
- Client should display test status as quality indicator

**5. Versioning is Critical**
- Semantic versioning enables intelligent merge decisions
- Version comparison logic needed for conflict resolution
- Timeline tracking requires version history

### 9.2 Recommended Client Features

**Based on RSB Format:**

**1. Code Viewer with Syntax Highlighting**
- Display Python rule implementation
- Show docstrings and comments
- Optional: Code diff between versions

**2. Test Results Dashboard**
- Parse test_results.json
- Show passed/failed status
- Link to edge_cases.json for details

**3. Compliance Documentation Viewer**
- Render markdown explanations
- Display XAI narrative
- Export compliance reports

**4. Rule Metadata Comparison**
- Side-by-side comparison of rule versions
- Highlight changed fields (action, confidence, conditions)
- Visual diff for easier understanding

**5. Deployment Validation**
- Pre-deployment checks:
  - ✓ Tests passed
  - ✓ Checksum valid
  - ✓ No conflicting rule_id
  - ✓ Version is newer than current

### 9.3 Potential Enhancements

**1. RSB Catalog/Repository**
- Store all downloaded RSBs in local database
- Full-text search across rules
- Tag/categorize by attack_type

**2. Rule Performance Tracking**
- If integrated with fraud engine, track:
  - True positive rate
  - False positive rate
  - Execution time
  - Resource usage

**3. Rule Recommendations**
- Analyze deployed rules
- Suggest compatible RSBs from Fraud Forge
- "Customers using R-ACCOUNT_TAKEOVER also use R-VELOCITY_CHECK"

**4. Custom Rule Creation**
- Template-based RSB generation
- User defines logic, app generates RSB structure
- Export for submission to Fraud Forge

---

## 10. Technical Implementation Guide

### 10.1 Python Libraries for RSB Parsing

```python
import zipfile
import json
from pathlib import Path
from typing import Dict, Any

class RSBParser:
    """Parse and extract RSB file contents."""
    
    def __init__(self, rsb_path: str):
        self.rsb_path = Path(rsb_path)
        self.extract_dir = None
        
    def extract(self, target_dir: str = None) -> Path:
        """Extract RSB to target directory."""
        if target_dir is None:
            target_dir = f"/tmp/rsb_{self.rsb_path.stem}"
        
        self.extract_dir = Path(target_dir)
        with zipfile.ZipFile(self.rsb_path, 'r') as zip_ref:
            zip_ref.extractall(self.extract_dir)
        
        return self.extract_dir
    
    def read_manifest(self) -> Dict[str, Any]:
        """Read and parse manifest.json."""
        manifest_path = self.extract_dir / "manifest.json"
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def read_rule(self) -> Dict[str, Any]:
        """Read and parse rule/rule.json."""
        rule_path = self.extract_dir / "rule" / "rule.json"
        with open(rule_path, 'r') as f:
            return json.load(f)
    
    def read_code(self) -> str:
        """Read rule implementation code."""
        code_files = list((self.extract_dir / "code").glob("ruleC_*.py"))
        if code_files:
            with open(code_files[0], 'r') as f:
                return f.read()
        return ""
    
    def read_test_results(self) -> Dict[str, Any]:
        """Read test execution results."""
        results_path = self.extract_dir / "tests" / "test_results.json"
        with open(results_path, 'r') as f:
            return json.load(f)
    
    def get_rsb_info(self) -> Dict[str, Any]:
        """Get complete RSB information."""
        self.extract()
        return {
            'manifest': self.read_manifest(),
            'rule': self.read_rule(),
            'code': self.read_code(),
            'test_results': self.read_test_results(),
            'filename': self.rsb_path.name,
            'filesize': self.rsb_path.stat().st_size
        }

# Usage
parser = RSBParser("RS_ACCOUNT_TAKEOVER.rsb")
rsb_info = parser.get_rsb_info()
print(rsb_info['rule']['confidence'])  # 0.7
```

### 10.2 JavaScript/TypeScript Implementation

```typescript
import JSZip from 'jszip';
import { promises as fs } from 'fs';

class RSBParser {
  private rsbPath: string;
  private zip: JSZip | null = null;
  
  constructor(rsbPath: string) {
    this.rsbPath = rsbPath;
  }
  
  async load(): Promise<void> {
    const data = await fs.readFile(this.rsbPath);
    this.zip = await JSZip.loadAsync(data);
  }
  
  async readManifest(): Promise<any> {
    const content = await this.zip?.file('manifest.json')?.async('string');
    return content ? JSON.parse(content) : null;
  }
  
  async readRule(): Promise<any> {
    const content = await this.zip?.file('rule/rule.json')?.async('string');
    return content ? JSON.parse(content) : null;
  }
  
  async readCode(): Promise<string> {
    // Find ruleC_*.py file
    const files = Object.keys(this.zip?.files || {});
    const codeFile = files.find(f => f.startsWith('code/ruleC_') && f.endsWith('.py'));
    
    if (codeFile) {
      return await this.zip?.file(codeFile)?.async('string') || '';
    }
    return '';
  }
  
  async getRSBInfo(): Promise<RSBInfo> {
    await this.load();
    
    const manifest = await this.readManifest();
    const rule = await this.readRule();
    const code = await this.readCode();
    
    return {
      manifest,
      rule,
      code,
      filename: this.rsbPath.split('/').pop() || '',
      filesize: (await fs.stat(this.rsbPath)).size
    };
  }
}

// Usage
const parser = new RSBParser('RS_ACCOUNT_TAKEOVER.rsb');
const rsbInfo = await parser.getRSBInfo();
console.log(rsbInfo.rule.confidence);  // 0.7
```

---

## 11. Appendix: Complete File Contents

### A.1 manifest.json
```json
{
  "attack_type": "account_takeover",
  "created_at": "2025-12-29T11:02:48.985959+00:00",
  "format": "RSB",
  "name": "Detect account_takeover",
  "rule_id": "R-ACCOUNT_TAKEOVER",
  "rule_version": "1.0.0",
  "version": "1.0"
}
```

### A.2 rule/specification.json
```json
{
  "action": "review",
  "conditions": [],
  "confidence": 0.7,
  "description": "Generated rule",
  "name": "Detect account_takeover",
  "rule_id": "R-ACCOUNT_TAKEOVER"
}
```

### A.3 rule/rule.json
```json
{
  "action": "review",
  "conditions": [],
  "confidence": 0.7,
  "description": "Generated rule",
  "name": "Detect account_takeover",
  "rule_id": "R-ACCOUNT_TAKEOVER",
  "version": "1.0.0"
}
```

### A.4 Sample Transaction Format
```json
{
  "transaction_id": "txn_12345",
  "timestamp": "2025-01-11T15:30:00Z",
  "account_id": "acct_67890",
  "counterparty_id": "merchant_abc",
  "amount": 129.99,
  "currency": "USD",
  "metadata": {
    "pattern": "account_takeover",
    "device_id": "device_xyz",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "geolocation": {
      "country": "US",
      "city": "New York"
    }
  }
}
```

---

## 12. Summary & Recommendations

### Key Takeaways

1. **RSB is a ZIP Archive** containing a complete fraud detection rule package
2. **Single Rule Per RSB** - networks are formed by aggregating multiple RSBs
3. **Python-Based Implementation** with comprehensive testing and documentation
4. **Semantic Versioning** enables intelligent version comparison and merging
5. **Self-Contained** with all deployment scripts and compliance documentation

### Client Application Requirements

✅ **Must Have:**
- ZIP extraction and parsing
- JSON parsing for manifest and rule definitions
- Python syntax highlighting for code display
- Markdown rendering for documentation
- Version comparison logic
- Merge conflict detection

✅ **Should Have:**
- Network graph visualization (multi-RSB aggregation)
- Test results dashboard
- Compliance documentation viewer
- Code diff viewer for versions
- Deployment validation checks

✅ **Nice to Have:**
- Sandboxed Python execution for rule testing
- Performance metrics integration
- Rule recommendation engine
- Custom RSB creation tools

### Next Steps

1. **Prototype RSB Parser** using provided code examples
2. **Design Database Schema** for storing RSB metadata
3. **Create Network Graph Aggregation** logic for multi-RSB visualization
4. **Implement Merge Conflict Detection** based on rule_id and version
5. **Build UI Components** for RSB visualization and comparison

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-19  
**Based on RSB:** RS_ACCOUNT_TAKEOVER.rsb  
**RSB Format Version:** 1.0
