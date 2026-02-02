## `MIRA_understanding.md`

# MIRA_understanding.md — MIRA Commentator Widget (Clippy-style XAI Orchestrator)

## 0) What is MIRA?
**MIRA (Multi-purpose Intelligent & insight Response Agent)** is Fraud Forge’s always-on, cross-screen **Commentator / XAI Orchestrator**.

Think “Clippy” for enterprise fraud operations — but modern:
- **Always available** (global widget on every screen)
- **Explains what’s happening** in **simple English**
- **Narrates key events**, decisions, agent actions, and outcomes
- **Guides the user** with next-best-actions, shortcuts, and safety warnings
- **Generates explainable summaries** for evidence, audits, and judge demos

MIRA is also a **beautiful Letter “M” animation character** (brand mascot + interaction surface).

---

## 1) Why MIRA exists (hackathon & product value)

### 1.1 Hackathon impact (why judges remember it)
MIRA turns your application from “dashboard + flows” into a **living system** that:
- narrates a battle like a **sports commentator**
- explains rules & mitigations in plain language
- provides real-time “what/why/so-what/now-what” context
- feels **enterprise + human-friendly** (rare combination)

**Hackathon-winning angle:**
> “Fraud Forge is explainable-by-design — every screen has an AI narrator that makes complex multi-agent behavior understandable.”

### 1.2 Enterprise value (why banks buy it)
- reduces training time for analysts
- supports audit/compliance reviews with consistent narratives
- improves operational safety (fewer misclicks / blind deployments)
- increases adoption and trust (system explains itself)

---

## 2) Where MIRA appears (global availability)
MIRA should appear as a **floating widget** (bottom-right by default) across:
- War Room / Battle Arena
- Thinking Visualizer (stage-by-stage reasoning stream)
- Brain Surgery Station (hot-swap/patch/merge)
- Difference Visualizer (code/spec diffs)
- RSB Manager (rule suite import/merge/validate)
- Rule Editor + Test Runner
- Approvals & Governance
- Evidence Pack Viewer
- Metrics Dashboard
- Admin / Settings

### 2.1 Global UI behaviors
- Collapsed: small animated “M” icon + status dot
- Expanded: chat-like panel + **Timeline** + **Actions**
- Dock/undock + resize
- Pin to keep open during demo
- Hotkeys:
  - `Ctrl+M` open/close
  - `Ctrl+Shift+M` “Judge Demo Mode”

---

## 3) What MIRA says (commentary types)
MIRA speaks in **simple English**, but can switch to technical mode.

### 3.1 Commentary categories
1) **Screen narration**
   - “You’re viewing the War Room. The Red Team is simulating a mule network…”
2) **Event narration**
   - “Blue Team raised a high-confidence alert on Pattern A0-99.”
3) **Decision explanation (XAI)**
   - “This triggered because 3 signals aligned: beneficiary churn, device anomaly, and velocity spike.”
4) **Process guidance**
   - “Next, review evidence, then decide: block, step-up authentication, or monitor.”
5) **Safety & governance**
   - “This RSB import changes action from REVIEW to BLOCK — approval required.”
6) **Outcome summary**
   - “Battle completed: 87% detection coverage, 12% reduction in false positives.”
7) **Demo storytelling**
   - “This is where Fraud Forge becomes self-improving: learn → distill → patch → deploy.”

### 3.2 Tone / verbosity modes
- **Plain mode (default):** non-technical, short
- **Technical mode:** IDs, thresholds, module names
- **Judge demo mode:** structured narrative + mini conclusions
- **Silent mode:** only safety warnings (no chatter)

---

## 4) What MIRA can do (interactive capabilities)
MIRA is not just chat — it’s a **control surface**.

### 4.1 User-facing features
- “Explain this” button (context-aware)
- “Why did this trigger?” (XAI drilldown)
- “Show me evidence” (opens evidence panel)
- “Run next step” (safe guided actions via UI hooks)
- “Summarize this screen” (1-click)
- “Export commentary” (for Evidence Pack / BRC)
- “Teach me” (micro-tutorials per screen)
- “Highlight risky changes” (diff/merge warnings)

### 4.2 Assistive actions (safe by design)
MIRA can propose actions; execution is gated by:
- RBAC
- environment (sandbox/prod)
- approvals for high-impact actions
- “dry-run” preview

Examples:
- “Validate uploaded RSB”
- “Generate merge preview”
- “Open Rule Diff for STR-042”
- “Start battle replay from BRC import”

---

## 5) How MIRA knows what’s happening (event intelligence)
MIRA subscribes to a **unified event bus** for:
- UI interactions
- Agent orchestration events
- Pipeline stage transitions
- Artifact lifecycle events (AMC/RSB/BRC)
- Governance events (approvals, policy blocks)
- Metrics & anomaly results

### 5.1 Event sources
1) **UI Event Stream** — route changes, clicks, uploads, selections
2) **Agent Events** — started, tool call, output produced, stage completed
3) **Battle Orchestrator** — stage start/end, scenario changes, outcomes
4) **Artifacts** — AMC/RSB/BRC export/import/validate/replay
5) **Governance & Security** — policy scan results, PII detection, RBAC blocks

### 5.2 Event schema (minimum)
Each event should have:
- `event_id`, `timestamp`, `event_type`
- `screen_context` (page, selected entity ids)
- `actor` (user | agent | system)
- `severity` (info | warn | blocker)
- `summary` (short human readable)
- `details` (structured payload, redacted)
- `links` (evidence ids, artifact ids)
- `xai` optional (factors + why)

---

## 6) MIRA architecture (LLM optional; deterministic fallback)
MIRA must work even if no LLM is available (hackathon reliability).

### 6.1 Two-layer generation strategy
**Layer A — Deterministic Narration (always-on)**
- template-based commentary per event type
- works offline
- zero hallucination risk

**Layer B — AI Enhancement (optional)**
- summarization across multiple events
- natural language storytelling
- “Explain in one paragraph” / “Compare two runs”

If AI fails, MIRA falls back to deterministic narration.

### 6.2 MIRA components
1) **MIRA Widget (Frontend)** — panel + animation + tabs + buttons
2) **Context Collector** — builds “screen snapshot” + recent event window
3) **Commentary Engine** — templates + (optional) LLM adapter (LLM-agnostic)
4) **Safety Filter** — redaction + forbidden output checks
5) **Action Router** — maps “Validate RSB” etc. to safe APIs
6) **MIRA Preferences** — remembers verbosity/mode per user

---

## 7) Character/animation requirements (Letter M mascot)
### 7.1 Visual requirements
- unique “M” character, friendly but enterprise
- idle animation (blink + breathing)
- talking animation (mouth/face movement)
- gesture animation (pointing, nodding, warning)
- status expressions: success, thinking, warning, blocked

### 7.2 Recommended animation tech
- **Lottie** (JSON vector animation) for best web performance
- or SVG + CSS animations
- or sprite sheet (PNG sequence)
- optional: GIF fallback

### 7.3 Accessibility
- supports “reduce motion”
- text equivalents for narration
- no flashing effects

---

## 8) Safety and compliance (must)
- never display raw PII or bank identifiers
- strict redaction for:
  - account numbers, customer names
  - internal URLs, employee names
  - case IDs, ticket IDs
- show only:
  - hashed IDs
  - aggregated telemetry
  - generalized descriptions

**Important:** MIRA must not leak Bank A data when demonstrating portability features.

---

## 9) Integration points with Fraud Forge features
### 9.1 War Room / Battle Arena
- narrate stage start/end
- highlight Red vs Blue reasoning differences
- surface “top 3 turning points”

### 9.2 Thinking Visualizer
- summarize per stage
- show reasoning as “because … therefore …”

### 9.3 Brain Surgery Station
- warn on risky merges
- explain what patch does
- link to validation/test results

### 9.4 RSB Manager
- narrate pipeline: “Structure OK → Tests OK → Compliance OK → Ready to Stage”

### 9.5 Approvals & Governance
- highlight “SAFE_TO_PROCEED / BLOCKED”
- generate short approval brief

### 9.6 Evidence Pack
- export MIRA narration as part of evidence artifacts
- auto-generate executive summary

---

## 10) Metrics for “MIRA success” (demo-friendly)
- time-to-understanding (self-reported)
- % of events narrated
- % narration with evidence links
- unsafe actions prevented
- 1-click exports generated
- judge “wow moments” per flow (storyboard count)

---

## 11) Hackathon-winning extras (high ROI)
1) **Demo Script Mode** — preloaded commentary storyboard for presentation
2) **Narration Timeline** — filter by warnings / blockers / team
3) **Explainability Toggle** — plain vs technical switch
4) **One-click Judge Report** — exports “what happened + why + what changed”
5) **Contextual micro-tutorials** — “Run a battle in 30 seconds”
```

---