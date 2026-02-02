# 🛡️ Fraud Forge: The AI vs. AI Defense Platform
> **"The only way to beat a machine... is with a better machine."**

**Fraud Forge** is a next-generation **Autonomous Cyber-Defense Platform** that leverages multi-agent AI simulations to proactively detect, test, and immunize financial systems against fraud.

By simulating an eternal "War Game" between attacking AI (Red Team) and defending AI (Blue Team), Fraud Forge reduces **Time-to-Immunity** from weeks to minutes, generating self-healing code patches and robust rule specifications autonomously.

---

## 🚀 Key Innovations

### 🧠 **AI vs. AI "War Room"**
Real-time battles where **Red Team agents** mutate attack vectors (credential stuffing, velocity spikes) and **Blue Team agents** evolve defense rules instantly. It's not just simulation—it's **evolutionary security**.

### 💉 **"Brain Surgery" Knowledge Graph**
Inspect and modify the collective intelligence of the agent swarm. The **Neural Mesh** visualizes how agents "think," allowing humans to perform "surgery" on agent logic (merging memories, pruning bad pathways) with zero downtime.

### ⏱️ **Time-to-Immunity (TTI)**
The platform measures success in **seconds**. When a new threat is detected, the **Green Team** automatically generates, tests, and deploys a code fix (hot-patch) to immunize the system before the attack scales.

### 🔍 **XAI & Persistent Memory**
*   **Persistent Agent Memory**: Every battle fought is remembered. Agents recall past lessons to improve future strategies.
*   **Gold Team Explainability**: Every decision comes with a "Why". Automated evidence packs and narrative explanations for regulators and auditors.

---

## 🤖 The 8-Team Architecture
Fraud Forge orchestrates a specialized swarm of 8 agent teams, each with a distinct mission:

| Token | Team | Mission |
| :--- | :--- | :--- |
| 🔴 | **Red Team** | **Attacker**: Simulates realistic fraud, evolves attack vectors, and probes for weaknesses. |
| 🔵 | **Blue Team** | **Defender**: Detects threats, scores risk, and protects the perimeter in real-time. |
| 🟣 | **Purple Team** | **Strategist**: Analyzes battle results to design new defense rules and threat models. |
| 🟢 | **Green Team** | **Builder**: Converts robust rules into production-ready code patches and features. |
| ⚫ | **Black Team** | **Stressor**: Runs chaos engineering, load tests, and edge-case validation. |
| 🟠 | **Orange Team** | **Gatekeeper**: Validates releases, checks for regressions, and manages rollbacks. |
| 🟡 | **Gold Team** | **Narrator**: Generates human-readable explanations and evidence trails for audit. |
| ⚪ | **White Team** | **Governor**: Enforces compliance, ethics, fairness, and regulatory alignment. |

---

## 🏗️ Tech Stack

*   **Frontend**: React (Vite), TailwindCSS, Framer Motion, Recharts, Lucide.
*   **Backend**: Python (FastAPI), Pydantic, AsyncIO.
*   **AI/ML**: OpenAI GPT-4o, LangChain, Vector Embeddings.
*   **Data & State**:
    *   **MongoDB**: Document storage for runs and artifacts.
    *   **PostgreSQL**: Structured transactional data.
    *   **Redis**: High-speed caching and message brokering.
    *   **ChromaDB**: Vector store for RAG (Retrieval Augmented Generation).
    *   **Neo4j**: Graph database for agent knowledge and lineage.
*   **Infrastructure**: Docker, Docker Compose.

---

## ⚡ Getting Started

### Prerequisites
*   Docker & Docker Compose
*   Node.js v18+ (for local frontend dev)
*   Python 3.11+ (for local backend dev)
*   OpenAI API Key

### Quick Start (Docker)
The easiest way to stand up the full stack:

1.  **Configure Environment**:
    ```bash
    cp .env.example .env
    # Edit .env and add your OPENAI_API_KEY
    ```

2.  **Launch the Forge**:
    ```bash
    docker-compose up --build
    ```

3.  **Access the War Room**:
    *   Frontend: [http://localhost:3000](http://localhost:3000)
    *   Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Development

**Backend**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

---

## 🛡️ Governance & Security
*   **Role-Based Access Control (RBAC)**: Strict separation of duties (SoD). A "Red Team" operator cannot approve a "Green Team" patch.
*   **Human-in-the-Loop (HITL)**: Critical actions (like deploying code or blocking high-value transactions) pause for human verification.
*   **Audit Trails**: Every agent action, decision, and memory recall is cryptographically time-stamped and logged.

---

## 🏆 Hackathon Status
*   **Completion**: ~95% Feature Complete
*   **Focus**: UI Polish, Stability, and "Wow" Demonstrations.
*   **Next Steps**: Final Docker validation and demo flow optimizations.

> *Built with ❤️ by the Fraud Forge Team*
