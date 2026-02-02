# 🏆 FRAUD FORGE: CONSOLIDATED REQUIREMENTS GAP ANALYSIS (a_req_con.md)

**Status:** Awaiting Development of Critical "Winning" Features  
**Target:** 100% Hackathon Victory  
**Date:** 2026-02-02

---

## 🛑 EXECUTIVE SUMMARY: THE MISSING 20%
While the foundational scaffolding (FastAPI, React, basic War Room) exists, the **"Winning Differentiators"**—the features that make judges say "Wow"—are currently missing or incomplete. This document strictly lists **only what must be built** to bridge the gap from "Good App" to "Hackathon Winner".

---

## 1. 🧠 AI & RAG ARCHITECTURE (THE BRAIN)

### 1.1 "Never Fail Twice" Learning Loop (Missing Key Logic)
**Current State:** Backend has seeded collisions but no *active* feedback loop that updates RAG.
**Requirement:**
- Implement the `learn()` function in `RedPhantom` and `BlueSentinel` agents.
- **Trigger:** Post-battle, automatically embed the outcome into the Vector Store.
- **Logic:**
    - If Red wins: Store attack vector in `attacks` collection.
    - If Blue wins: Store detection signature in `patterns` collection.
- **Showcase:** A specific API endpoint `/api/learn-from-battle/{battle_id}` that can be called to demonstrate "instant immunity".

### 1.2 Multi-Collection RAG (Missing Collections)
**Current State:** Single generic vector store implied; need strict separation.
**Requirement:**
- Implement 5 distinct ChromaDB collections:
    1.  `attacks`: Red Team offensive memory.
    2.  `patterns`: Blue Team defensive patterns.
    3.  `taxonomy`: The 120 static fraud scenarios (from seed data).
    4.  `rules`: Index of all active rule code (for RAG retrieval).
    5.  `explanations`: Gold Team's past XAI outputs.
- **Action:** Update `demo_data_generator.py` to pre-seed *all 5* collections, not just generic nodes.

### 1.3 Full 54-Agent Roster (Partial Implementation)
**Current State:** Only ~5 agents are currently seeded/visible.
**Requirement:**
- **Data:** Update seeding to explicitly create all 54 agents (8 Teams) in the DB.
- **Display:** The "Agent Management" and "Team Status" screens must render exactly 54 cards, grouped by Team Color. They can share logic, but must have unique IDs/Names (e.g., "Red.Recon.01", "Blue.Graph.04").

---

## 2. 🎨 VISUAL WOW (THE FACE)

### 2.1 Brain Surgery Station (Missing Screen)
**Current State:** Conceptual only.
**Requirement:**
- **Tech:** `react-force-graph-2d` or `3d`.
- **Function:** A dedicated full-screen visualization of the "Knowledge Graph".
- **Interaction:**
    - Show **Blue Nodes** (Current Rules).
    - Show **Green Nodes** (Incoming Patch/Learning).
    - **Animation:** When "Merge" is clicked, Green nodes physically fly into the Blue cluster and turn Blue.
- **Why:** This verifies the "Learning" claim visually.

### 2.2 7-Stage Thinking Visualizer (Missing Component)
**Current State:** Generic "Thinking..." spinner/text.
**Requirement:**
- **UI:** A component showing 7 distinct "Process Cards" that light up sequentially during a Battle Turn:
    1.  `[RECON]` → 2. `[IDEATION]` → 3. `[PLANNING]` → 4. `[EVASION]` → 5. `[EXECUTION]` → 6. `[REFLECTION]` → 7. `[LEARNING]`
- **Data:** The Backend must emit SSE (Server Sent Events) events corresponding to these stages: `{"stage": "IDEATION", "log": "Mutating payload..."}`.

### 2.3 Difference Visualizer (Missing Component)
**Current State:** Basic text comparison.
**Requirement:**
- **UI:** A "Rich Diff" view for Rule Code.
- **Layout:** 3-Pane View:
    - **Left:** Old Code.
    - **Right:** New Code (with Green/Red highlights).
    - **Bottom:** "Reasoning" (Why was this change made?).
- **Tech:** `monaco-editor` diff view or standard `diff-match-patch` highlighting.

---

## 3. 📦 PORTABLE INTELLIGENCE (THE PRODUCT)

### 3.1 PEP (Portable Evolution Pack) Engine
**Current State:** Does not exist.
**Requirement:**
- **Backend:** A service that:
    1.  Selects specific RAG documents + Rule Code.
    2.  Anonymizes them (removes PII/Tenant ID).
    3.  Packages them into a `.pep` (Zip) file.
    4.  Generates a SHA-256 Checksum `manifest.json`.
- **UI:** A specialized "Export Brain" modal in Settings.

### 3.2 "Import Brain" Workflow
**Current State:** Does not exist.
**Requirement:**
- **UI:** Drag-and-drop a `.pep` file.
- **Flow:**
    1.  Upload -> Validate Checksum.
    2.  Show "Preview" (Diff of what will change).
    3.  "Commence Brain Surgery" (triggers the Graph Animation from 2.1).

---

## 4. 🛡️ ENTERPRISE GOVERNANCE (THE MOAT)

### 4.1 HITL / HOTL Global Switch
**Current State:** Settings toggle exists but logic is unconnected.
**Requirement:**
- **Backend Middleware:** Check the Global Setting before any "Write" operation (e.g., Deploy Rule).
    - **If HITL:** Block request, create `ApprovalRequest` record, return 202 Accepted.
    - **If HOTL:** Auto-approve, log "Auto-Approved by Policy", execute immediately.
- **UI:** A "Pending Approvals" notification bell/list for the blocked requests.

### 4.2 Gold Team "Explain Anything" Panel
**Current State:** Scattered tooltips.
**Requirement:**
- **UI:** A global side-drawer (Right Sidebar).
- **Trigger:** Right-click *any* Battle Event, Rule, or Agent -> "Explain This".
- **Content:** Gold Team Agent generates a structured explanation:
    - **What:** "Blocked Transaction #991".
    - **Why:** "Velocity > 5 within 10s".
    - **Evidence:** Link to specific Trace log.

---

## 5. 🎬 DEMO MAGIC (THE CLOSER)

### 5.1 One-Click "Story Mode"
**Current State:** Manual clicking required.
**Requirement:**
- **Feature:** A "Demo God Button".
- **Scripted Flow:**
    1.  Clean DB.
    2.  Seed "Scenario F05" (ACH Fraud).
    3.  Run Battle 1 (Force Red Win).
    4.  Run "Learn" (Auto-Patch).
    5.  Run Battle 2 (Force Blue Win).
    6.  Open Charts showing "Immunity Gained".
- **Why:** Ensures a perfect 3-minute pitch interaction without risk of random AI failure.

### 5.2 Live Scoreboard Overlay
**Current State:** Basic metrics in tabs.
**Requirement:**
- **UI:** a "HUD" (Heads Up Display) overlay on the War Room.
- **Metrics:**
    - "💰 Money Saved" (Ticking counter).
    - "🛡️ Immunity Score" (Percentage bar).
    - "⚡ Attacks/Sec" (Sparkline).
- **Style:** Neon/Cyberpunk aesthetic to distinct it from standard admin UI.

---

**Approval:** These requirements are FINAL. No deviations allowed. Proceed to Implementation Plan. 🚀
