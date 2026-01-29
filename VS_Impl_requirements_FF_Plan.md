# Fraud Forge Application - Complete Implementation Plan (implement_VS_Impl_requirements_FF_Plan.md)

## Executive Summary

**Implementation Plan for Fraud Forge Application**  
**Version:** 2.0 | Production-Ready Implementation  
**Date:** January 30, 2026  

This document provides a comprehensive, step-by-step implementation plan for building the complete Fraud Forge Application. It is designed to be self-explanatory and actionable for GitHub Copilot, with detailed instructions for each component, file structure, code snippets, and integration points.

The plan is organized into phases with clear deliverables, dependencies, and validation steps. Each step includes:
- **Objective:** What to achieve
- **Files to Create/Modify:** Specific file paths and contents
- **Code Implementation:** Detailed code snippets and logic
- **Integration Points:** How it connects to other components
- **Testing:** Validation and verification steps

---

## Table of Contents

1. [Project Setup & Infrastructure](#1-project-setup--infrastructure)
2. [Backend Foundation (FastAPI)](#2-backend-foundation-fastapi)
3. [Database & Data Layer](#3-database--data-layer)
4. [AI/ML Core (RAG & Agents)](#4-aiml-core-rag--agents)
5. [Frontend Foundation (React)](#5-frontend-foundation-react)
6. [Core UI Components](#6-core-ui-components)
7. [Battle Engine & Simulation](#7-battle-engine--simulation)
8. [Rule Management (RSB)](#8-rule-management-rsb)
9. [Explainability (XAI) System](#9-explainability-xai-system)
10. [Workflow & State Machine](#10-workflow--state-machine)
11. [Security & RBAC](#11-security--rbac)
12. [Testing & Validation](#12-testing--validation)
13. [Deployment & DevOps](#13-deployment--devops)
14. [Demo Preparation](#14-demo-preparation)

---

## 1. Project Setup & Infrastructure

### 1.1 Initialize Project Structure

**Objective:** Create the complete project directory structure with all necessary folders and configuration files.

**Files to Create:**
- `docker-compose.yml` (root level)
- `backend/requirements.txt`
- `frontend/package.json`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `.gitignore`
- `README.md`

**Implementation Steps:**

1. **Create Root Directory Structure:**
   ```
   fraud-forge/
   ├── backend/
   │   ├── app/
   │   │   ├── __init__.py
   │   │   ├── main.py
   │   │   ├── config.py
   │   │   ├── database.py
   │   │   ├── models/
   │   │   ├── schemas/
   │   │   ├── services/
   │   │   ├── routers/
   │   │   └── utils/
   │   ├── requirements.txt
   │   ├── Dockerfile
   │   └── tests/
   ├── frontend/
   │   ├── public/
   │   ├── src/
   │   │   ├── components/
   │   │   ├── pages/
   │   │   ├── contexts/
   │   │   ├── hooks/
   │   │   ├── lib/
   │   │   └── utils/
   │   ├── package.json
   │   ├── Dockerfile
   │   └── nginx.conf
   ├── docker-compose.yml
   ├── .gitignore
   └── README.md
   ```

2. **Create docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://user:password@db:5432/fraudforge
         - REDIS_URL=redis://redis:6379
       depends_on:
         - db
         - redis
       volumes:
         - ./backend:/app

     frontend:
       build: ./frontend
       ports:
         - "3000:80"
       depends_on:
         - backend

     db:
       image: postgres:15
       environment:
         POSTGRES_DB: fraudforge
         POSTGRES_USER: user
         POSTGRES_PASSWORD: password
       volumes:
         - postgres_data:/var/lib/postgresql/data

     redis:
       image: redis:7-alpine

     chromadb:
       image: chromadb/chroma:latest
       ports:
         - "8001:8000"
       volumes:
         - chroma_data:/chroma/chroma

     neo4j:
       image: neo4j:5.15
       environment:
         NEO4J_AUTH: neo4j/password
       ports:
         - "7474:7474"
         - "7687:7687"
       volumes:
         - neo4j_data:/data

   volumes:
     postgres_data:
     chroma_data:
     neo4j_data:
   ```

3. **Create backend/requirements.txt:**
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   sqlalchemy==2.0.23
   psycopg2-binary==2.9.9
   redis==5.0.1
   chromadb==0.4.18
   langchain==0.0.350
   langgraph==0.0.15
   openai==1.3.5
   pydantic==2.5.0
   python-multipart==0.0.6
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4
   neo4j==5.15.0
   rank-bm25==0.2.2
   ragas==0.0.22
   pytest==7.4.3
   ```

4. **Create frontend/package.json:**
   ```json
   {
     "name": "fraud-forge-frontend",
     "version": "0.1.0",
     "private": true,
     "dependencies": {
       "@types/node": "^16.18.39",
       "@types/react": "^18.2.25",
       "@types/react-dom": "^18.2.11",
       "react": "^18.2.0",
       "react-dom": "^18.2.0",
       "react-scripts": "5.0.1",
       "typescript": "^4.9.5",
       "web-vitals": "^2.1.4",
       "@tanstack/react-query": "^4.35.3",
       "axios": "^1.5.0",
       "react-router-dom": "^6.16.0",
       "zustand": "^4.4.1",
       "tailwindcss": "^3.3.3",
       "autoprefixer": "^10.4.16",
       "postcss": "^8.4.30",
       "lucide-react": "^0.292.0",
       "react-force-graph-2d": "^1.25.0",
       "monaco-editor": "^0.44.0",
       "socket.io-client": "^4.7.2",
       "d3": "^7.8.5"
     },
     "scripts": {
       "start": "react-scripts start",
       "build": "react-scripts build",
       "test": "react-scripts test",
       "eject": "react-scripts eject"
     }
   }
   ```

**Validation:** Run `docker-compose up --build` and verify all services start without errors.

---

## 2. Backend Foundation (FastAPI)

### 2.1 Create FastAPI Application

**Objective:** Set up the main FastAPI application with CORS, middleware, and basic routing.

**Files to Create:**
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/__init__.py`

**Implementation Steps:**

1. **Create backend/app/config.py:**
   ```python
   from pydantic import BaseSettings
   from typing import Optional

   class Settings(BaseSettings):
       app_name: str = "Fraud Forge API"
       debug: bool = False
       version: str = "2.0.0"
       api_prefix: str = "/api/v1"

       database_url: str
       redis_url: str
       openai_api_key: str
       chroma_url: str = "http://chromadb:8001"
       neo4j_url: str = "bolt://neo4j:7687"
       neo4j_user: str = "neo4j"
       neo4j_password: str

       jwt_secret_key: str
       jwt_algorithm: str = "HS256"
       jwt_expiration_hours: int = 24

       class Config:
           env_file = ".env"

   settings = Settings()
   ```

2. **Create backend/app/main.py:**
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from fastapi.security import HTTPBearer
   from .config import settings
   from .database import create_tables
   from .routers import auth, battles, rules, agents, xai

   app = FastAPI(
       title=settings.app_name,
       version=settings.version,
       debug=settings.debug
   )

   # CORS middleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "http://frontend:80"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Security
   security = HTTPBearer()

   # Create database tables
   @app.on_event("startup")
   async def startup_event():
       await create_tables()

   # Include routers
   app.include_router(auth.router, prefix=settings.api_prefix)
   app.include_router(battles.router, prefix=settings.api_prefix)
   app.include_router(rules.router, prefix=settings.api_prefix)
   app.include_router(agents.router, prefix=settings.api_prefix)
   app.include_router(xai.router, prefix=settings.api_prefix)

   @app.get("/")
   async def root():
       return {"message": "Fraud Forge API", "version": settings.version}
   ```

**Integration Points:** This sets up the foundation for all backend services.

**Testing:** Start the backend with `uvicorn app.main:app --reload` and verify the root endpoint returns the expected JSON.

---

## 3. Database & Data Layer

### 3.1 SQLAlchemy Models

**Objective:** Define all database models for users, battles, rules, agents, and artifacts.

**Files to Create:**
- `backend/app/database.py`
- `backend/app/models/__init__.py`
- `backend/app/models/user.py`
- `backend/app/models/battle.py`
- `backend/app/models/rule.py`
- `backend/app/models/agent.py`
- `backend/app/models/artifact.py`

**Implementation Steps:**

1. **Create backend/app/database.py:**
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
   from sqlalchemy.orm import sessionmaker
   from .config import settings

   engine = create_async_engine(settings.database_url, echo=settings.debug)
   async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

   async def get_db():
       async with async_session() as session:
           try:
               yield session
           finally:
               await session.close()

   async def create_tables():
       from .models import Base
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   ```

2. **Create backend/app/models/user.py:**
   ```python
   from sqlalchemy import Column, Integer, String, Boolean, DateTime
   from sqlalchemy.sql import func
   from .base import Base

   class User(Base):
       __tablename__ = "users"

       id = Column(Integer, primary_key=True, index=True)
       username = Column(String, unique=True, index=True)
       email = Column(String, unique=True, index=True)
       hashed_password = Column(String)
       role = Column(String)  # SA, BA, Analyst, Operator
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime(timezone=True), server_default=func.now())
       updated_at = Column(DateTime(timezone=True), onupdate=func.now())
   ```

**Continue with other models following similar patterns for Battle, Rule, Agent, Artifact.**

**Validation:** Run database migrations and verify tables are created correctly.

---

## 4. AI/ML Core (RAG & Agents)

### 4.1 RAG Service Implementation

**Objective:** Implement the multi-type RAG system with ChromaDB and Neo4j integration.

**Files to Create:**
- `backend/app/services/rag_service.py`
- `backend/app/services/vector_store.py`
- `backend/app/services/graph_store.py`
- `backend/app/services/hybrid_search.py`

**Implementation Steps:**

1. **Create backend/app/services/rag_service.py:**
   ```python
   import chromadb
   from langchain.embeddings import OpenAIEmbeddings
   from langchain.vectorstores import Chroma
   from .config import settings

   class RAGService:
       def __init__(self):
           self.client = chromadb.HttpClient(host="chromadb", port=8000)
           self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
           self.vector_store = Chroma(
               client=self.client,
               collection_name="fraud_forge",
               embedding_function=self.embeddings
           )

       async def add_documents(self, documents: list, metadata: dict = None):
           """Add documents to the vector store"""
           texts = [doc.page_content for doc in documents]
           metadatas = [doc.metadata for doc in documents]
           ids = [f"doc_{i}" for i in range(len(documents))]
           
           self.vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)

       async def search(self, query: str, top_k: int = 5) -> list:
           """Search for relevant documents"""
           docs = self.vector_store.similarity_search(query, k=top_k)
           return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]

       async def generate_answer(self, query: str, context: list) -> str:
           """Generate answer using retrieved context"""
           # Implementation using OpenAI GPT
           pass
   ```

**Integration Points:** Connects to the battle engine for real-time retrieval and to the XAI system for explanations.

**Testing:** Add sample documents and verify search returns relevant results.

---

## 5. Frontend Foundation (React)

### 5.1 React Application Setup

**Objective:** Set up the React application with TypeScript, Tailwind, and routing.

**Files to Create:**
- `frontend/src/index.js`
- `frontend/src/App.js`
- `frontend/src/index.css`
- `frontend/tailwind.config.js`
- `frontend/tsconfig.json`

**Implementation Steps:**

1. **Create frontend/src/App.js:**
   ```jsx
   import React from 'react';
   import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
   import Layout from './components/Layout';
   import BattleArena from './pages/BattleArena';
   import BrainSurgery from './pages/BrainSurgery';
   import RSBManager from './pages/RSBManager';
   import MetricsDashboard from './pages/MetricsDashboard';
   import XAI from './pages/XAI';
   import TeamDirectory from './pages/TeamDirectory';
   import EvidencePackViewer from './pages/EvidencePackViewer';
   import WarPractice from './pages/WarPractice';
   import Login from './pages/Login';
   import { AuthProvider } from './contexts/AuthContext';

   const queryClient = new QueryClient();

   function App() {
     return (
       <QueryClientProvider client={queryClient}>
         <AuthProvider>
           <Router>
             <Routes>
               <Route path="/login" element={<Login />} />
               <Route path="/" element={<Layout />}>
                 <Route index element={<BattleArena />} />
                 <Route path="brain-surgery" element={<BrainSurgery />} />
                 <Route path="rsb-manager" element={<RSBManager />} />
                 <Route path="metrics" element={<MetricsDashboard />} />
                 <Route path="xai" element={<XAI />} />
                 <Route path="teams" element={<TeamDirectory />} />
                 <Route path="evidence" element={<EvidencePackViewer />} />
                 <Route path="war-practice" element={<WarPractice />} />
               </Route>
             </Routes>
           </Router>
         </AuthProvider>
       </QueryClientProvider>
     );
   }

   export default App;
   ```

**Integration Points:** Sets up the routing structure for all application screens.

**Testing:** Start the frontend with `npm start` and verify routing works correctly.

---

## 6. Core UI Components

### 6.1 Layout and Navigation

**Objective:** Create the main layout with sidebar navigation and RBAC-based access control.

**Files to Create:**
- `frontend/src/components/Layout.jsx`
- `frontend/src/components/Sidebar.jsx`
- `frontend/src/components/TopNav.jsx`

**Implementation Steps:**

1. **Create frontend/src/components/Layout.jsx:**
   ```jsx
   import React from 'react';
   import { Outlet } from 'react-router-dom';
   import Sidebar from './Sidebar';
   import TopNav from './TopNav';
   import { useAuth } from '../contexts/AuthContext';

   const Layout = () => {
     const { user } = useAuth();

     if (!user) {
       return <div>Loading...</div>;
     }

     return (
       <div className="flex h-screen bg-gray-900 text-white">
         <Sidebar />
         <div className="flex-1 flex flex-col">
           <TopNav />
           <main className="flex-1 overflow-auto p-6">
             <Outlet />
           </main>
         </div>
       </div>
     );
   };

   export default Layout;
   ```

**Continue with detailed implementation for all components.**

---

## 7. Battle Engine & Simulation

### 7.1 Battle Arena Implementation

**Objective:** Create the real-time battle simulation interface with Red vs Blue teams.

**Files to Create:**
- `frontend/src/pages/BattleArena.jsx`
- `backend/app/routers/battles.py`
- `backend/app/services/battle_service.py`

**Implementation Steps:**

1. **Create backend/app/services/battle_service.py:**
   ```python
   from typing import Dict, List
   from ..models.battle import Battle
   from ..schemas.battle import BattleCreate, BattleUpdate
   from ..database import async_session
   from .rag_service import RAGService
   from .agent_service import AgentService

   class BattleService:
       def __init__(self):
           self.rag_service = RAGService()
           self.agent_service = AgentService()

       async def start_battle(self, battle_data: BattleCreate) -> Battle:
           # Create battle record
           # Initialize Red and Blue teams
           # Start simulation loop
           pass

       async def get_battle_status(self, battle_id: int) -> Dict:
           # Return current battle state
           pass

       async def execute_turn(self, battle_id: int) -> Dict:
           # Execute one turn of Red vs Blue
           # Update metrics and status
           pass
   ```

**Integration Points:** Connects to RAG for knowledge retrieval and agents for decision making.

---

## 8. Rule Management (RSB)

### 8.1 RSB Processing Service

**Objective:** Implement RSB import, validation, and deployment functionality.

**Files to Create:**
- `backend/app/services/rsb_service.py`
- `frontend/src/pages/RSBManager.jsx`

**Implementation Steps:**

1. **Create backend/app/services/rsb_service.py:**
   ```python
   import zipfile
   import json
   from pathlib import Path
   from typing import Dict, List
   from ..models.rule import Rule
   from ..schemas.rule import RuleCreate

   class RSBService:
       def __init__(self, upload_dir: str = "uploads/rsb"):
           self.upload_dir = Path(upload_dir)
           self.upload_dir.mkdir(exist_ok=True)

       async def process_rsb_file(self, file_path: str) -> Dict:
           """Process uploaded RSB file"""
           with zipfile.ZipFile(file_path, 'r') as zip_ref:
               # Extract and validate structure
               manifest = json.loads(zip_ref.read('manifest.json'))
               rule_spec = json.loads(zip_ref.read('rule/specification.json'))
               
               # Validate rule
               validation_result = await self.validate_rule(rule_spec)
               
               if validation_result['valid']:
                   # Store rule in database
                   rule_data = RuleCreate(
                       name=manifest['name'],
                       version=manifest['version'],
                       specification=rule_spec,
                       code=zip_ref.read('rule/rule.py').decode('utf-8')
                   )
                   # Save to database
                   
               return {
                   'valid': validation_result['valid'],
                   'errors': validation_result.get('errors', []),
                   'rule_id': rule.id if validation_result['valid'] else None
               }

       async def validate_rule(self, rule_spec: Dict) -> Dict:
           """Validate rule specification"""
           # Implement validation logic
           pass
   ```

---

## 9. Explainability (XAI) System

### 9.1 XAI Service Implementation

**Objective:** Build the explainable AI system for decision transparency.

**Files to Create:**
- `backend/app/services/xai_service.py`
- `frontend/src/pages/XAI.jsx`

**Implementation Steps:**

1. **Create backend/app/services/xai_service.py:**
   ```python
   from typing import Dict, List
   from ..models.explanation import Explanation
   from .rag_service import RAGService

   class XAIService:
       def __init__(self):
           self.rag_service = RAGService()

       async def generate_explanation(self, decision_id: str, context: Dict) -> Explanation:
           """Generate human-readable explanation for AI decision"""
           
           # Retrieve relevant context from RAG
           context_docs = await self.rag_service.search(
               f"Explain decision: {context.get('decision_type', '')}", 
               top_k=3
           )
           
           # Generate explanation using LLM
           explanation_prompt = f"""
           Explain this AI decision in simple terms:
           Decision: {context.get('decision', '')}
           Context: {context.get('context', '')}
           Evidence: {context_docs}
           
           Provide:
           1. What happened
           2. Why it happened
           3. What it means
           4. Confidence level
           """
           
           # Call OpenAI API
           explanation_text = await self._call_openai(explanation_prompt)
           
           return Explanation(
               decision_id=decision_id,
               explanation=explanation_text,
               confidence=context.get('confidence', 0.0),
               evidence=context_docs
           )

       async def _call_openai(self, prompt: str) -> str:
           # Implementation
           pass
   ```

---

## 10. Workflow & State Machine

### 10.1 State Machine Implementation

**Objective:** Implement the war loop state machine with human intervention points.

**Files to Create:**
- `backend/app/services/workflow_service.py`
- `backend/app/models/workflow.py`

**Implementation Steps:**

1. **Create backend/app/services/workflow_service.py:**
   ```python
   from enum import Enum
   from typing import Dict, Optional
   from ..models.workflow import WorkflowState

   class WorkflowState(Enum):
       RED_SIMULATE = "red_simulate"
       BLUE_DETECT = "blue_detect"
       PURPLE_RULESPEC_UPDATE = "purple_rulespec_update"
       GREEN_BUILD_PATCH = "green_build_patch"
       BLACK_STRESS_TEST = "black_stress_test"
       ORANGE_REVIEW_APPROVE = "orange_review_approve"
       WHITE_COMPLIANCE_AUDIT = "white_compliance_audit"
       GOLD_XAI_PACK = "gold_xai_pack"
       DONE = "done"

   class WorkflowService:
       def __init__(self):
           self.state_transitions = {
               WorkflowState.RED_SIMULATE: WorkflowState.BLUE_DETECT,
               WorkflowState.BLUE_DETECT: WorkflowState.PURPLE_RULESPEC_UPDATE,
               # Define all transitions
           }

       async def advance_workflow(self, workflow_id: str, current_state: WorkflowState) -> WorkflowState:
           """Advance workflow to next state"""
           next_state = self.state_transitions.get(current_state)
           
           if next_state:
               # Check for human intervention requirements
               if self._requires_approval(next_state):
                   # Set to pending approval state
                   pass
               else:
                   # Auto-advance
                   pass
           
           return next_state

       def _requires_approval(self, state: WorkflowState) -> bool:
           """Check if state requires human approval"""
           approval_states = [
               WorkflowState.ORANGE_REVIEW_APPROVE,
               WorkflowState.WHITE_COMPLIANCE_AUDIT
           ]
           return state in approval_states
   ```

---

## 11. Security & RBAC

### 11.1 Authentication Service

**Objective:** Implement JWT-based authentication with role-based access control.

**Files to Create:**
- `backend/app/services/auth_service.py`
- `backend/app/routers/auth.py`
- `frontend/src/contexts/AuthContext.jsx`

**Implementation Steps:**

1. **Create backend/app/services/auth_service.py:**
   ```python
   from datetime import datetime, timedelta
   from typing import Optional
   from jose import JWTError, jwt
   from passlib.context import CryptContext
   from ..config import settings
   from ..models.user import User

   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   class AuthService:
       def __init__(self):
           self.secret_key = settings.jwt_secret_key
           self.algorithm = settings.jwt_algorithm
           self.access_token_expire_hours = settings.jwt_expiration_hours

       def verify_password(self, plain_password: str, hashed_password: str) -> bool:
           return pwd_context.verify(plain_password, hashed_password)

       def get_password_hash(self, password: str) -> str:
           return pwd_context.hash(password)

       def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
           to_encode = data.copy()
           if expires_delta:
               expire = datetime.utcnow() + expires_delta
           else:
               expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
           
           to_encode.update({"exp": expire})
           encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
           return encoded_jwt

       async def authenticate_user(self, username: str, password: str) -> Optional[User]:
           # Query user from database
           # Verify password
           # Return user if valid
           pass

       def get_current_user(self, token: str) -> Optional[dict]:
           try:
               payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
               username: str = payload.get("sub")
               role: str = payload.get("role")
               if username is None:
                   return None
               return {"username": username, "role": role}
           except JWTError:
               return None
   ```

---

## 12. Testing & Validation

### 12.1 Unit and Integration Tests

**Objective:** Create comprehensive test suite for all components.

**Files to Create:**
- `backend/tests/test_battle_service.py`
- `backend/tests/test_rag_service.py`
- `frontend/src/__tests__/BattleArena.test.jsx`

**Implementation Steps:**

1. **Create backend/tests/test_rag_service.py:**
   ```python
   import pytest
   from app.services.rag_service import RAGService

   @pytest.mark.asyncio
   async def test_rag_search():
       service = RAGService()
       
       # Add test documents
       test_docs = [
           {"page_content": "Fraud detection using AI", "metadata": {"type": "rule"}},
           {"page_content": "Machine learning for banking", "metadata": {"type": "concept"}}
       ]
       await service.add_documents(test_docs)
       
       # Search
       results = await service.search("fraud detection", top_k=2)
       
       assert len(results) > 0
       assert "fraud" in results[0]["content"].lower()
   ```

**Testing Strategy:** Unit tests for services, integration tests for API endpoints, E2E tests for critical user flows.

---

## 13. Deployment & DevOps

### 13.1 CI/CD Pipeline

**Objective:** Set up automated deployment pipeline.

**Files to Create:**
- `.github/workflows/deploy.yml`
- `docker-compose.prod.yml`

**Implementation Steps:**

1. **Create .github/workflows/deploy.yml:**
   ```yaml
   name: Deploy to Production

   on:
     push:
       branches: [ main ]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.9'
       - name: Install dependencies
         run: |
           cd backend
           pip install -r requirements.txt
       - name: Run tests
         run: |
           cd backend
           pytest

     deploy:
       needs: test
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - name: Deploy to production
         run: |
           echo "Deploying to production server"
           # Add deployment commands
   ```

---

## 14. Demo Preparation

### 14.1 Demo Data and Scenarios

**Objective:** Prepare realistic demo data and scenarios for hackathon presentation.

**Files to Create:**
- `backend/app/data/demo_data.py`
- `backend/app/scripts/seed_demo.py`

**Implementation Steps:**

1. **Create backend/app/data/demo_data.py:**
   ```python
   DEMO_USERS = [
       {
           "username": "sa_admin",
           "email": "sa@fraudforge.com",
           "password": "demo123",
           "role": "SA"
       },
       {
           "username": "ba_user",
           "email": "ba@fraudforge.com", 
           "password": "demo123",
           "role": "BA"
       }
   ]

   DEMO_FRAUD_SCENARIOS = [
       {
           "name": "Account Takeover",
           "description": "Simulated ATO attack with credential stuffing",
           "complexity": "medium",
           "expected_detection_rate": 0.85
       }
   ]

   DEMO_RULES = [
       {
           "name": "Suspicious Login Detection",
           "code": """
   def detect_suspicious_login(transaction):
       # Rule logic here
       return transaction.get('unusual_location', False)
           """,
           "version": "1.0.0"
       }
   ]
   ```

**Final Validation:** Run full demo flow from login to evidence pack export, ensuring all features work end-to-end.

---

*This implementation plan provides step-by-step instructions for building the complete Fraud Forge Application. Each section includes detailed code examples, file structures, and integration points to guide GitHub Copilot through the development process.*