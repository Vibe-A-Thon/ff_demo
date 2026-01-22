# Fraud Forge

Autonomous Fraud Simulation & Self-Healing Defense Platform.

## Architecture

Fraud Forge is a Hybrid Multi-Agent System with a Lifecycle Workflow Engine.

- **Presentation Layer**: Streamlit UI
- **API Layer**: FastAPI Backend
- **AI/Agent Layer**: LangGraph State Machine + 8 Team Orchestrators
- **Memory Layer**: ChromaDB (Vectors) + PostgreSQL (Structured) + Redis (Cache)
- **Infrastructure Layer**: Docker Compose

## Quick Start

1.  Copy environment variables:
    ```bash
    cp .env.example .env
    ```

2.  Start services:
    ```bash
    docker-compose up --build
    ```

## Directory Structure

- `src/`: Backend API and Agent logic
- `ui/`: Streamlit frontend
- `data/`: Data storage
- `scripts/`: Utility scripts
