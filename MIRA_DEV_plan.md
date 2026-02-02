## `MIRA_DEV_plan.md`

# MIRA_DEV_plan.md — Phase-by-Phase Development Plan (Clippy-style Commentator/XAI Orchestrator)

This plan is designed so GitHub Copilot can build MIRA end-to-end:
**UI widget + event bus + commentary engine + safety + actions + deep integrations**.

---

## Phase 0 — Lock requirements, event taxonomy, and UI spec
### Deliverables
- MIRA widget UX spec (collapsed/expanded, tabs, hotkeys)
- Event taxonomy (enum list)
- Event schema (JSON schema)
- Commentary modes: Plain / Technical / Judge Demo / Silent
- Safety redaction rules (regex + dictionaries)
- Minimum action list per screen (safe actions)

### Tasks
1) Define event types:
   - `UI_NAVIGATION`, `UI_SELECTION`, `UI_UPLOAD`
   - `BATTLE_STAGE_START`, `BATTLE_STAGE_END`, `BATTLE_RESULT`
   - `AGENT_TOOL_CALL`, `AGENT_OUTPUT`, `AGENT_ERROR`
   - `ARTIFACT_EXPORTED`, `ARTIFACT_IMPORTED`, `ARTIFACT_VALIDATED`
   - `GOV_APPROVAL_REQUIRED`, `GOV_APPROVED`, `GOV_BLOCKED`
2) Define screen context object:
   - page name, selected rule ids, current battle id, current artifact id, etc.
3) Define deterministic commentary templates per event type.

### Acceptance criteria
- A single JSON event can be rendered into readable narration deterministically.

---

## Phase 1 — Build the MIRA widget shell (Frontend)
### Deliverables
- Global floating widget mounted at App root
- Collapsed/expanded states
- Tabs: **Commentary**, **Timeline**, **Actions**, **Settings**
- Animation placeholder (static “M” first)
- Hotkeys + accessibility

### Tasks
- Implement `MiraWidget`:
  - local state: open/close, mode, verbosity, pinned
  - props/context: route + current selected entity ids
- Implement message feed UI:
  - timestamp, severity icon, short text, expandable details
- Add “Explain this screen” button (backend wired later)

### Acceptance criteria
- MIRA shows on every screen and can display mocked messages reliably.

---

## Phase 2 — Implement a unified Event Bus (Frontend + Backend)
### Goal
A single pipeline for emitting system events to MIRA.

### Deliverables
- Frontend event emitter:
  - `emitUiEvent(type, payload)`
- Backend event intake:
  - `POST /mira/events`
- Event store:
  - in-memory for hackathon (upgrade to DB later)
- WebSocket/SSE stream:
  - `/mira/stream`

### Tasks
1) Instrument UI:
   - route transitions
   - “major actions” (upload/import/deploy/run/replay/approve)
2) Backend ingestion:
   - validate schema
   - redact sensitive fields
   - store and broadcast to stream
3) Frontend live stream client:
   - push into timeline + commentary feed

### Acceptance criteria
- Clicking around screens produces live timeline entries in MIRA.

---

## Phase 3 — Deterministic Commentary Engine (always-on)
### Goal
Narration must be reliable even without LLMs.

### Deliverables
- Template library:
  - `templates/<event_type>.j2` OR Python format map
- `commentary_engine.py`:
  - `render(event, mode) -> MiraMessage`
- Severity rules:
  - warn/blocker triggers

### Tasks
- Render:
  - 1-line “what happened”
  - optional “why it matters”
  - optional links/evidence
- Implement “screen summary”:
  - last N events + screen context → 5 bullets

### Acceptance criteria
- Every major event type narrates in simple, correct English.

---

## Phase 4 — AI Enhancement Layer (optional, LLM-agnostic)
### Goal
Upgrade narration to “explainability storytelling” while staying safe + swappable across LLMs.

### Deliverables
- `llm_adapter.py` (provider abstraction)
- `mira_ai_summarizer.py`:
  - window summarization
  - “change explanation” for diffs
  - “battle story” for judge mode
- Prompt templates (hashable/versioned)
- Guardrails:
  - output safety scan
  - fallback to deterministic mode

### Tasks
1) Backend endpoints:
   - `POST /mira/explain` (screen + event window)
   - `POST /mira/story` (battle narrative)
2) UI controls:
   - mode switch: deterministic-only vs hybrid
   - judge demo mode toggle
3) Safety re-scan on AI output:
   - redact again + policy block if needed

### Acceptance criteria
- If AI fails, the system still works and narration stays accurate.

---

## Phase 5 — Action Router (MIRA as a control surface)
### Goal
MIRA should help users complete workflows with 1 click (safely).

### Deliverables
- Action registry per screen:
  - action id, label, required RBAC, API mapping, risk level
- Backend:
  - `POST /mira/action/preview`
  - `POST /mira/action/execute`
- UI Actions tab:
  - context-aware actions + confirmations

### Tasks
- Implement preview:
  - show “what will change” before execution
- RBAC gating:
  - hide/disable disallowed actions
- Environment gating:
  - sandbox vs prod rules
- Approval gating:
  - high-risk actions require approvals

### Acceptance criteria
- From MIRA, user can safely run things like “Validate RSB”, “Open Evidence”, “Generate Summary”.

---

## Phase 6 — Deep integrations with War Room / AMC / RSB / BRC
### Goal
MIRA must narrate real Fraud Forge pipelines (not only UI clicks).

### Deliverables
- Orchestrator emits stage events:
  - stage start/end, agent outputs ready, validations complete
- MIRA “Stage Lens”:
  - stage name + progress + next step
- Evidence linking:
  - each narrated event links to artifact IDs and evidence IDs

### Tasks (must cover)
1) War Room narration:
   - turning points
   - “Red did X, Blue responded with Y”
2) RSB pipeline narration:
   - upload → validate → stage → deploy → rollback
3) AMC portability narration:
   - validate capsule → scan → preview → import → activate
4) BRC replay narration:
   - synced timeline during battle replay

### Acceptance criteria
- A full battle run produces a coherent narrated timeline with evidence links.

---

## Phase 7 — MIRA preferences & personalization (optional)
### Deliverables
- Store per-user settings:
  - verbosity, mode, voice on/off, pinned actions
- First-run tutorial
- “teach me” micro hints per screen

### Acceptance criteria
- MIRA remembers user preferences across sessions.

---

## Phase 8 — Safety, governance, auditability (must)
### Deliverables
- Redaction + forbidden-output scanner for every message (deterministic + AI)
- “redaction transparency”:
  - “Some details were hidden for security.”
- Audit events:
  - action previews, executions, exports
- RBAC integration for every action

### Acceptance criteria
- MIRA cannot leak sensitive bank data in any mode and logs every action.

---

## Phase 9 — Hackathon polish: animation + demo mode
### Deliverables
- Unique animated mascot:
  - idle, thinking, speaking, warning, success
- Demo storyboard:
  - pre-seeded commentary for the presentation flow
- “One-click Judge Report” export:
  - battle story + changes + outcomes in Markdown
- Performance:
  - event batching
  - UI virtualization for long timelines

### Acceptance criteria
- Demo feels cinematic and smooth; judges immediately “get it”.

---

# Implementation checklist (for Copilot)

## A) Backend endpoints
- `POST /mira/events`
- `GET /mira/stream` (SSE) OR WebSocket
- `POST /mira/explain`
- `POST /mira/story`
- `POST /mira/action/preview`
- `POST /mira/action/execute`
- `GET /mira/timeline?battle_id=...`

## B) Data models
- `MiraEvent`
- `MiraMessage`
- `MiraAction`
- `MiraContext`

## C) Key UI components
- `MiraWidget`
- `MiraTimeline`
- `MiraActionsPanel`
- `MiraSettings`
- `MiraMessageCard`

## D) Safety rules
- Regex detectors:
  - account numbers, card patterns, emails, phone numbers
- Keyword dictionaries:
  - internal system names, employee references, ticket/case ids
- Output scan for deterministic and AI generated text

---

# Hackathon-winning suggestions (shortlist)
1) MIRA narrates **multi-agent battles** like a commentator (wow factor)
2) MIRA provides **plain English explainability** on every screen
3) MIRA offers **one-click safe actions** (real product feel)
4) MIRA exports **judge-ready reports** (evidence + story)
5) MIRA’s animated mascot makes the experience **memorable and branded**
```

---