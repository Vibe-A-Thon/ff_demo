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
- ✅ **Alert History Panel** - Persistent history with filter tabs, mark as read, clear all
- ✅ **Configurable Thresholds** - Bank risk profiles (Conservative, Moderate, High-Volume, Fintech)
- ✅ **Role-based Access Control** - Admin, Analyst, Engineer, Compliance roles with route protection
- ✅ **Battle Replay & Comparison** - Before/after comparison with playback controls
- ✅ Brain Surgery Station - Force-directed graph with drag-drop nodes
- ✅ Metrics Dashboard - KPIs, charts, time-to-immunity trends
- ✅ RSB Manager - Package list, import, test, merge
- ✅ Difference Visualizer - Split-pane diff with accept/reject
- ✅ Evidence Pack Viewer - XAI narrative, export ZIP
- ✅ Rule Editor - Form builder, code view, test results
- ✅ Approvals - Queue, approve/reject, SoD checks
- ✅ Sidebar navigation with user profile dropdown and role indicators

## Prioritized Backlog

### P0 (Critical)
- All core features implemented ✅
- Login/Register UI ✅
- Demo autoplay mode ✅
- Real-time alerts ✅
- WebSocket streaming ✅
- Alert History Panel ✅
- Configurable Thresholds ✅
- Role-based Access Control ✅
- Battle Replay & Comparison ✅

### P1 (High Priority)
- User profile management page
- Export threshold configurations
- Email notifications for critical alerts

### P2 (Medium Priority)  
- Slow-motion playback mode
- Accessibility improvements (screen reader, keyboard nav)
- High-contrast mode
- Custom date range filters for metrics

### P3 (Nice to Have)
- Custom report generation
- Integration with external SIEM systems
- Multi-tenant support
- Threshold configuration sync across users

## Next Tasks
1. Implement login/register UI screens
2. Add role-based route protection
3. Enable live WebSocket battle streaming
4. Add demo autoplay mode
5. Implement evidence pack ZIP download
