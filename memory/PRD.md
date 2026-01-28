# Fraud Forge - Product Requirements Document

## Original Problem Statement
Enterprise-grade UI for fraud detection simulation that proves Failure → Learning → Immunity while being auditable and safe for banks. Features Red vs Blue team battles, AI reasoning visualization, metrics dashboards, knowledge graph management, and compliance tools.

## User Personas
1. **Fraud Analysts** - Run battle simulations, analyze patterns, manage rules
2. **Compliance Officers** - Review evidence packs, approve changes, ensure SoD
3. **Security Engineers** - Manage RSB packages, configure rules, view diffs
4. **Executives** - View metrics dashboards, monitor KPIs

## Core Requirements (Static)
- Dark theme enterprise UI
- Real-time WebSocket battle streaming
- Force-directed knowledge graph visualization
- RBAC and approval workflows
- Evidence pack export functionality
- OpenAI integration for AI reasoning

## What's Been Implemented (Jan 28, 2025)

### Backend (FastAPI + MongoDB)
- ✅ Battle management (CRUD, start/stop, real-time turns)
- ✅ Rule management with test runner
- ✅ RSB package import/test/merge
- ✅ Evidence pack generation and export
- ✅ Knowledge graph nodes and connections
- ✅ Approval queue with multi-approver flow
- ✅ Metrics dashboard aggregation
- ✅ AI thinking endpoint with OpenAI integration
- ✅ WebSocket support for real-time updates
- ✅ JWT authentication with bcrypt password hashing

### Frontend (React + Tailwind)
- ✅ **Login/Register UI** - Sign In, Register tabs, Demo Mode quick access
- ✅ War Room - Red vs Blue battle simulation with thinking visualizers
- ✅ **Streaming AI Thinking** - Real-time text streaming with LIVE indicators
- ✅ **Demo Autoplay Mode** - Automated battle progression with variable pacing
- ✅ **Real-time Alerts** - Threshold-based alerts for TTI, Success Rate, Money at Risk
- ✅ Brain Surgery Station - Force-directed graph with drag-drop nodes
- ✅ Metrics Dashboard - KPIs, charts, time-to-immunity trends
- ✅ RSB Manager - Package list, import, test, merge
- ✅ Difference Visualizer - Split-pane diff with accept/reject
- ✅ Evidence Pack Viewer - XAI narrative, export ZIP
- ✅ Rule Editor - Form builder, code view, test results
- ✅ Approvals - Queue, approve/reject, SoD checks
- ✅ Sidebar navigation with user profile dropdown

## Prioritized Backlog

### P0 (Critical)
- All core features implemented ✅
- Login/Register UI ✅
- Demo autoplay mode ✅
- Real-time alerts ✅
- WebSocket streaming ✅

### P1 (High Priority)
- Role-based route protection enforcement
- Persistent alert history panel
- Battle replay with before/after comparison

### P2 (Medium Priority)  
- Slow-motion playback mode
- Accessibility improvements (screen reader, keyboard nav)
- High-contrast mode
- Email notifications for approvals

### P3 (Nice to Have)
- Custom report generation
- Integration with external SIEM systems
- Multi-tenant support
- Custom threshold configuration UI

## Next Tasks
1. Implement login/register UI screens
2. Add role-based route protection
3. Enable live WebSocket battle streaming
4. Add demo autoplay mode
5. Implement evidence pack ZIP download
