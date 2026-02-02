# APMC / Brain Surgery — Complete Feature Documentation

> **Version:** 2.0  
> **Last Updated:** 2026-02-02  
> **Status:** 100% Implementation Complete  

---

## 📋 Executive Summary

The **APMC (Agents Portable Memory Capsule)** and **Brain Surgery** features provide enterprise-grade capabilities for transferring, merging, and hot-swapping agent intelligence across Fraud Forge instances. This is the "PDF of Agentic AI" — a portable, validated, and auditable artifact format for agent knowledge transfer.

### Key Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| **AMC Import** | ✅ Complete | Upload and validate AMC packages |
| **AMC Export** | ✅ Complete | Export team intelligence to portable format |
| **AMC Validation** | ✅ Complete | Schema, hash, and policy validation |
| **AMC Preview** | ✅ Complete | 3-frame merge preview visualization |
| **Conflict Detection** | ✅ Complete | Automatic conflict identification |
| **Conflict Resolution** | ✅ Complete | Interactive resolution workflow |
| **Sandbox Validation** | ✅ Complete | Pre-merge safety tests |
| **Hot-Swap Execution** | ✅ Complete | Live activation of merged state |
| **Rollback Management** | ✅ Complete | Point-in-time recovery |
| **Knowledge Graph Viz** | ✅ Complete | Merge visualization for all frames |
| **SoD Enforcement** | ✅ Complete | Separation of Duties for all actions |
| **Audit Logging** | ✅ Complete | Full audit trail for compliance |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     BRAIN SURGERY WORKFLOW                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │   UPLOAD    │───▶│  VALIDATE   │───▶│   PREVIEW   │           │
│  │   AMC File  │    │  Schema/Hash│    │  3-Frame    │           │
│  └─────────────┘    └─────────────┘    └─────────────┘           │
│                                              │                     │
│                                              ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │  HOT-SWAP   │◀───│   SANDBOX   │◀───│  CONFLICTS  │           │
│  │  Execute    │    │  Validation │    │  Resolution │           │
│  └─────────────┘    └─────────────┘    └─────────────┘           │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐    ┌─────────────┐                               │
│  │  ROLLBACK   │◀───│   MONITOR   │                               │
│  │  Available  │    │   Active    │                               │
│  └─────────────┘    └─────────────┘                               │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

### Backend

```
backend/app/
├── services/capsules/amc/
│   ├── amc_service.py              # Core AMC operations (800 lines)
│   ├── brain_surgery_service.py    # Session, hot-swap, rollback (600+ lines)
│   ├── lesson_distiller.py         # BRC/Battle → AMC conversion (400 lines)
│   ├── demo_amc_generator.py       # Demo AMC file generator (300 lines)
│   ├── policies/
│   │   └── amc_prohibited_content.yaml
│   └── schemas/
│       ├── amc_schema.json
│       ├── agent_profile_schema.json
│       └── memory_schema.json
├── routes/
│   ├── amc.py                      # AMC API routes
│   ├── brain_surgery.py            # Brain Surgery API routes
│   └── lessons.py                  # Lesson Distiller routes
├── cli/
│   └── amc_cli.py                  # CLI for validate/inspect/diff/export
└── tests/
    └── test_brain_surgery_service.py  # Comprehensive tests
```

### Frontend

```
frontend/src/
├── pages/
│   └── BrainSurgery.jsx           # Full UI (1900+ lines)
├── components/
│   └── AMCExplorer.jsx            # AMC file viewer with tree (500 lines)
└── lib/
    └── api.js                     # Brain Surgery + Lessons API functions
```

---

## 🔌 API Reference

### Brain Surgery Session Management

#### Start Surgery Session

```http
POST /api/brain-surgery/sessions
Content-Type: multipart/form-data

Parameters:
  team_id: string (required) - Target team ID
  file: File (optional) - AMC file to analyze immediately

Response:
{
  "session_id": "surgery_blue_20260202_120000",
  "team_id": "blue",
  "actor_id": "user-123",
  "status": "initialized" | "conflicts_detected" | "ready_for_merge",
  "baseline": { ... },
  "import_preview": { ... },
  "merged_preview": { ... },
  "conflicts": [ ... ],
  "validation": { ... },
  "hot_swap_ready": boolean
}
```

#### List Sessions

```http
GET /api/brain-surgery/sessions?team_id=blue&status=active&limit=20
```

#### Get Session

```http
GET /api/brain-surgery/sessions/{session_id}
```

### Conflict Resolution

```http
POST /api/brain-surgery/sessions/{session_id}/resolve-conflict
Content-Type: multipart/form-data

Parameters:
  conflict_id: string - ID of conflict to resolve
  resolution: string - Resolution choice: "keep_existing" | "accept_import" | "merge_both"
```

### Sandbox Validation

```http
POST /api/brain-surgery/sessions/{session_id}/sandbox

Response:
{
  "session_id": "...",
  "sandbox_results": {
    "executed_at": "2026-02-02T12:30:00Z",
    "passed": true | false,
    "tests": [
      {
        "id": "test_memory_coherence",
        "name": "Memory Coherence Check",
        "status": "passed" | "warning" | "failed",
        "logs": [ ... ]
      }
    ],
    "summary": {
      "total": 5,
      "passed": 4,
      "warnings": 1,
      "failed": 0
    }
  },
  "hot_swap_ready": true
}
```

### Hot-Swap Execution

```http
POST /api/brain-surgery/sessions/{session_id}/hot-swap
Content-Type: multipart/form-data

Parameters:
  mode: string - "hot_swap" | "gradual" | "shadow"

Response:
{
  "session_id": "...",
  "status": "hot_swap_active",
  "activation": {
    "activation_id": "swap_...",
    "mode": "hot_swap",
    "executed_by": "user-456",
    "executed_at": "2026-02-02T12:45:00Z",
    "rollback_available": true,
    "rollback_window_minutes": 15
  }
}
```

### Rollback

```http
POST /api/brain-surgery/rollback
Content-Type: multipart/form-data

Parameters:
  team_id: string (required)
  snapshot_id: string (optional) - If not provided, uses most recent

Response:
{
  "rollback": {
    "rollback_id": "rb_blue_20260202_130000",
    "status": "completed"
  },
  "restored_snapshot": { ... },
  "current_state": { ... }
}
```

### Team State & Rollback Snapshots

```http
GET /api/brain-surgery/teams/{team_id}/state
GET /api/brain-surgery/teams/{team_id}/rollback-snapshots?limit=10
```

### Knowledge Graph for Merge

```http
GET /api/brain-surgery/sessions/{session_id}/knowledge-graph

Response:
{
  "baseline": {
    "nodes": [ ... ],
    "edges": [ ... ]
  },
  "import": {
    "nodes": [ ... ],
    "edges": [ ... ]
  },
  "merged": {
    "nodes": [ ... ],
    "edges": [ ... ]
  },
  "conflicts": [ ... ]
}
```

---

## 🔒 Security & Governance

### Separation of Duties (SoD)

| Action | Cannot Be Performed By |
|--------|------------------------|
| Execute Hot-Swap | Person who started the session |
| Activate Package | Person who imported the package |
| Rollback | Unrestricted (emergency action) |

### Audit Events

| Event | Fields Logged |
|-------|---------------|
| `brain_surgery.session_started` | session_id, team_id, actor_id |
| `brain_surgery.amc_analyzed` | session_id, validation_result |
| `brain_surgery.conflict_resolved` | session_id, conflict_id, resolution |
| `brain_surgery.sandbox_executed` | session_id, passed |
| `brain_surgery.hot_swap_executed` | session_id, mode, team_id |
| `brain_surgery.rollback_executed` | rollback_id, team_id, snapshot_id |

---

## 🧪 Sandbox Validation Tests

The sandbox validation runs 5 critical safety tests before allowing hot-swap:

| Test | Description |
|------|-------------|
| **Memory Coherence Check** | Validates semantic/episodic memory integrity |
| **Skill Graph Compatibility** | Ensures skill graphs can merge without cycles |
| **Reasoning Pattern Validation** | Checks decision patterns for conflicts |
| **Guardrail Enforcement Check** | Verifies guardrails are preserved |
| **Rollback Safety Check** | Confirms rollback snapshot is valid |

---

## 🎨 UI Components

### Brain Surgery Operations Panel

The main UI panel includes:

1. **Session Controls**
   - Team selector (8 teams)
   - Hot-swap mode selector (Immediate, Gradual, Shadow)
   - Start Session button
   - Load State button
   - Run Sandbox button

2. **Session Status Card**
   - Session ID badge
   - Status indicator with color coding
   - Hot-swap ready indicator
   - Unresolved conflicts count

3. **Hot-Swap & Rollback Card**
   - Execute Hot-Swap button (disabled until sandbox passes)
   - Rollback button with snapshot count
   - SoD violation warnings

4. **Conflicts Panel**
   - List of detected conflicts
   - Resolution buttons per conflict
   - Visual status (resolved/unresolved)

5. **Sandbox Results Card**
   - Pass/Fail badge
   - Test summary grid (Total, Passed, Warnings, Failed)
   - Color-coded metrics

---

## 🔄 Hot-Swap Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **hot_swap** | Immediate activation | Production updates, urgent fixes |
| **gradual** | Phased rollout with checkpoints | Large-scale changes, risk mitigation |
| **shadow** | Parallel execution for comparison | Testing, validation before production |

---

## 📊 Data Structures

### Surgery Session State

```typescript
interface SurgerySession {
  session_id: string;
  team_id: string;
  actor_id: string;
  started_at: string; // ISO timestamp
  status: 'initialized' | 'conflicts_detected' | 'ready_for_merge' 
        | 'sandbox_running' | 'sandbox_passed' | 'sandbox_failed'
        | 'hot_swap_executing' | 'hot_swap_active';
  baseline: Snapshot;
  import_preview: Snapshot | null;
  merged_preview: Snapshot | null;
  conflicts: Conflict[];
  validation: ValidationResult | null;
  sandbox_results: SandboxResults | null;
  hot_swap_ready: boolean;
  rollback_snapshot_id: string | null;
  activation: Activation | null;
}

interface Conflict {
  id: string;
  type: 'role_change' | 'knowledge_drift';
  agent_id: string;
  title: string;
  detail: string;
  severity: 'low' | 'medium' | 'high';
  resolution: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  options: string[];
}

interface SandboxResults {
  executed_at: string;
  executed_by: string;
  tests: SandboxTest[];
  passed: boolean;
  summary: {
    total: number;
    passed: number;
    warnings: number;
    failed: number;
  };
}
```

---

## ✅ Implementation Checklist

- [x] AMC import with file upload
- [x] AMC validation (schema, hash, policy)
- [x] AMC export for all teams
- [x] 3-frame merge preview (Baseline, Import, Merged)
- [x] Conflict detection (role changes, knowledge drift)
- [x] Interactive conflict resolution
- [x] Sandbox validation with 5 test types
- [x] Hot-swap execution (3 modes)
- [x] Rollback management (snapshot creation, restore)
- [x] Knowledge graph visualization for merge
- [x] SoD enforcement (session starter ≠ executor)
- [x] Full audit logging
- [x] Comprehensive test suite
- [x] Frontend UI complete with all controls
- [x] API routes registered and functional

---

## 🚀 Usage Example

### Complete Hot-Swap Flow

```javascript
// 1. Start surgery session with AMC file
const formData = new FormData();
formData.append("team_id", "blue");
formData.append("file", amcFile);
const session = await brainSurgeryAPI.startSession(formData);

// 2. Review and resolve any conflicts
if (session.conflicts.length > 0) {
  for (const conflict of session.conflicts) {
    const resolveForm = new FormData();
    resolveForm.append("conflict_id", conflict.id);
    resolveForm.append("resolution", "accept_import");
    await brainSurgeryAPI.resolveConflict(session.session_id, resolveForm);
  }
}

// 3. Run sandbox validation
const validated = await brainSurgeryAPI.runSandbox(session.session_id);
if (!validated.sandbox_results.passed) {
  throw new Error("Sandbox validation failed");
}

// 4. Execute hot-swap (must be different user)
const hotSwapForm = new FormData();
hotSwapForm.append("mode", "hot_swap");
const activated = await brainSurgeryAPI.executeHotSwap(session.session_id, hotSwapForm);

// 5. (Optional) Rollback if issues detected
const rollbackForm = new FormData();
rollbackForm.append("team_id", "blue");
await brainSurgeryAPI.rollback(rollbackForm);
```

---

## 📈 Metrics & Monitoring

Key metrics to track:

- Sessions started per day
- Conflict detection rate
- Sandbox pass/fail ratio
- Hot-swap success rate
- Average time-to-activation
- Rollback frequency

---

**This documentation covers the complete APMC / Brain Surgery feature set. All capabilities are now at 100% implementation.**
