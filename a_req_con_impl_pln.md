# 🚀 FRAUD FORGE: IMPLEMENTATION PLAN (a_req_con_impl_pln.md)

**Strategy:** "Visuals First, Logic Deep"  
**Goal:** 100% Hackathon Victory  
**Timeline:** 4 Phases (Aggressive Sprint)  
**Status:** ✅ PHASE 2 COMPLETE

---

## 📅 PHASE 1: THE VISUAL FACE-LIFT (IMMEDIATE PRIORITY)
**Objective:** Make the app *look* like a winner immediately. Even with mock data, the UI must stun.

### 1.1 🧠 Brain Surgery Graph (UI Component)
- **Task:** Create `src/components/BrainSurgery/KnowledgeGraph.tsx`.
- **Tech:** React Force Graph (`react-force-graph-2d`).
- **Data:** Mock JSON with Blue Nodes (Knowledge) and Green Nodes (Patches).
- **Ani:** Implement "Merge" animation where Green nodes coalesce into Blue.
- **Reference Requirement:** [a_req_con.md 2.1]

### 1.2 💭 7-Stage Thinking Visualizer
- **Task:** Create `src/components/Thinking/ThinkingPipeline.tsx`.
- **UI:** A horizontal stepper showing the 7 stages (Recon -> Learning).
- **Logic:** Connect to a dummy SSE stream or timer to auto-advance active stage style.
- **Reference Requirement:** [a_req_con.md 2.2]

### 1.3 🕹️ War Room "God Mode" HUD
- **Task:** Overlay `src/components/WarRoom/LiveScoreboard.tsx` on the Battle Arena.
- **Metrics:** Animated `CountUp` for "$ Money Saved" and "Immunity %".
- **Style:** Glassmorphism, Neon text, absolute positioning over the map/graph.
- **Reference Requirement:** [a_req_con.md 5.2]

---

## 📅 PHASE 2: THE DEEP LOGIC (THE BRAIN)
**Objective:** Connect the beautiful UI to a powerful, real Multi-Agent backend.

### 2.1 🧬 Full Roster Seeding (54 Agents)
- **Task:** Update `backend/scripts/demo_data_generator.py`.
- **Detail:** Hardcode the creation of all 54 Agent Identities (8 Teams).
- **Output:** DB populated with comprehensive agent metadata (Role, Capabilities).
- **Reference Requirement:** [a_req_con.md 1.3]

### 2.2 📚 5-Collection RAG Architecture
- **Task:** Enhance `backend/app/services/rag/vector_store.py`.
- **Action:** Explicitly initialize the 5 collections (`attacks`, `patterns`, `taxonomy`, `rules`, `explanations`).
- **Seed:** Ingest the `banking_fraud_taxonomy_catalog_120.json` into the `taxonomy` collection.
- **Reference Requirement:** [a_req_con.md 1.2]

### 2.3 🔄 "Never Fail Twice" Learning Loop
- **Task:** Modify `RedPhantom` and `BlueSentinel` classes.
- **Logic:** Add `post_battle_hook()`:
    - `vector_store.add_document('attacks', attack_vector)`
    - `vector_store.add_document('patterns', defense_signature)`
- **Validation:** Ensure the "Brain Surgery Graph" (Phase 1) updates node count after a battle.
- **Reference Requirement:** [a_req_con.md 1.1]

---

## 📅 PHASE 3: ENTERPRISE & GOVERNANCE
**Objective:** Prove this is "Bank Ready" and safe.

### 3.1 📦 PEP Export/Import Engine
- **Task:** Create `backend/app/services/pep_service.py`.
- **Export:** Zip selected `taxonomy` + `rules` docs -> `brain_export_v1.pep`.
- **Import:** Unzip -> Validate Checksum -> Trigger "Brain Surgery" merge event.
- **UI:** 'Export Brain' / 'Import Brain' modals in Settings.
- **Reference Requirement:** [a_req_con.md 3.1, 3.2]

### 3.2 👮 HITL / HOTL Middleware
- **Task:** Implement `SettingsMiddleware` in FastAPI.
- **Logic:** Intercept `/api/deploy/*` requests.
    - Check global state `Settings.governance_mode`.
    - If `HITL`: Return 202 + "Pending Approval".
    - If `HOTL`: Execute.
- **UI:** "Pending Approvals" badge in the Top Navbar.
- **Reference Requirement:** [a_req_con.md 4.1]

### 3.3 🥇 Gold Team Explainer Panel
- **Task:** Create `src/components/Shared/ExplainabilityDrawer.tsx`.
- **Logic:** Fetch structured explanation from `/api/explain/{id}`.
- **Content:** "Likely Reason", "Confidence", "Evidence Links".
- **Reference Requirement:** [a_req_con.md 4.2]

---

## 📅 PHASE 4: THE DEMO POLISH (THE CLOSER)
**Objective:** Script the perfect pitch.

### 4.1 🎬 One-Click "Story Mode"
- **Task:** Create `backend/app/services/demo_orchestrator.py`.
- **Endpoint:** `POST /api/demo/run_story_mode`.
- **Sequence:**
    1.  Reset DB.
    2.  Battle 1 (Fail).
    3.  Sleep 2s.
    4.  Trigger Learn.
    5.  Battle 2 (Success).
- **UI:** A giant "RUN DEMO" button on the Dashboard (hidden in prod, visible for hackathon).
- **Reference Requirement:** [a_req_con.md 5.1]

### 4.2 🖼️ Final Asset Polish
- **Task:** Review all icons/colors.
- **Check:** Ensure Team Colors (Red/Blue/Purple/etc.) are consistent across all 54 cards and graphs.
- **Effect:** Add "Confetti" or "Shield Pulse" animation on Blue Victory.

---

**Execution Order:** Phase 1 -> Phase 2 -> Phase 3 -> Phase 4.
**Critical Path:** The "Brain Surgery" graph and "Thinking Visualizer" are the highest ROI visual items. RAG is the highest ROI technical item.
