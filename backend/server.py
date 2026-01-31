from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
import hashlib
import openai
import random
from pymongo import ASCENDING

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# JWT and Auth
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'default_secret')
JWT_ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

APP_NAME = os.environ.get("APP_NAME", "Fraud Forge API")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"
API_PREFIX = os.environ.get("API_PREFIX", "/api")

# Create the main app
app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=DEBUG_MODE)
api_router = APIRouter(prefix=API_PREFIX)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def init_database() -> None:
    await db.command("ping")
    await db.users.create_index([("email", ASCENDING)], unique=True)
    await db.rules.create_index([("id", ASCENDING)], unique=True)
    await db.runs.create_index([("id", ASCENDING)], unique=True)
    await db.battles.create_index([("id", ASCENDING)], unique=True)
    await db.rsb_packages.create_index([("id", ASCENDING)], unique=True)
    await db.evidence_packs.create_index([("id", ASCENDING)], unique=True)
    await db.knowledge_nodes.create_index([("id", ASCENDING)], unique=True)
    await db.rag_documents.create_index([("id", ASCENDING)], unique=True)
    await db.rag_documents.create_index([("collection", ASCENDING), ("created_at", ASCENDING)])
    await db.teams.create_index([("team_id", ASCENDING)], unique=True)
    await db.agents.create_index([("agent_id", ASCENDING)], unique=True)
    await db.agent_tasks.create_index([("task_id", ASCENDING)], unique=True)
    await db.agent_tasks.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.agent_requests.create_index([("request_id", ASCENDING)], unique=True)
    await db.run_events.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.audit_logs.create_index([("target_id", ASCENDING), ("created_at", ASCENDING)])
    await db.quality_checks.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.evaluations.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.approvals.create_index([("status", ASCENDING)])
    await db.approvals.create_index([("resource_type", ASCENDING), ("resource_id", ASCENDING)])

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "analyst"

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BattleCreate(BaseModel):
    scenario_name: str
    parameters: Dict[str, Any] = {}

class Battle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_name: str
    status: str = "pending"
    parameters: Dict[str, Any] = {}
    turns: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {"success_rate": 0, "money_at_risk": 0, "time_to_immunity": 0, "patterns_learned": 0}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

class RuleCreate(BaseModel):
    name: str
    description: str
    rule_type: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int = 0

class Rule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    rule_type: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int
    status: str = "draft"
    version: int = 1
    test_results: Optional[Dict[str, Any]] = None
    proposed_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RuleProposalCreate(BaseModel):
    name: str
    description: str
    rule_type: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int = 0
    requestor_id: str
    metadata: Dict[str, Any] = {}

class RuleApprovalDecision(BaseModel):
    approver_id: str
    decision: str = "approved"
    notes: Optional[str] = None

class RuleActionRequest(BaseModel):
    actor_id: str
    notes: Optional[str] = None
    metadata: Dict[str, Any] = {}

class EvidenceExportApprovalRequest(BaseModel):
    requestor_id: str
    mode: str = "external"
    metadata: Dict[str, Any] = {}

class RSBPackage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    description: str
    manifest: Dict[str, Any]
    rules: List[str] = []
    compliance_badges: List[str] = []
    test_results: Optional[Dict[str, Any]] = None
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RSBPackageCreate(BaseModel):
    name: str
    version: str
    description: str
    manifest: Dict[str, Any]
    rules: List[str] = []
    compliance_badges: List[str] = []

class EvidencePack(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    battle_id: str
    narrative: str
    triggered_rules: List[str]
    contributing_factors: List[Dict[str, Any]]
    confidence: float
    logs: List[Dict[str, Any]]
    approvals: List[Dict[str, Any]] = []
    checksum: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_type: str
    resource_id: str
    action: str
    status: str = "pending"
    requestor_id: str
    approvers: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ApprovalCreate(BaseModel):
    resource_type: str
    resource_id: str
    action: str
    requestor_id: str
    metadata: Dict[str, Any] = {}

class AuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str
    action: str
    target_type: str
    target_id: str
    decision: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QualityCheckResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    status: str
    checks: List[Dict[str, Any]] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    summary: str
    metrics: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class KnowledgeNode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str  # rule, pattern, compliance, evidence
    name: str
    data: Dict[str, Any] = {}
    connections: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class KnowledgeNodeCreate(BaseModel):
    node_type: str
    name: str
    data: Dict[str, Any] = {}
    connections: List[str] = []

class RunStartRequest(BaseModel):
    scenario_id: str = "demo"
    seed: Optional[int] = None
    mode: str = "auto"

class RunSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    seed: int
    mode: str = "auto"
    status: str = "running"
    current_stage: str = "init"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: Optional[str] = None

class RunEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    event_type: str
    payload: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentTask(BaseModel):
    model_config = ConfigDict(extra="ignore")
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    team_id: str
    target_agent_id: Optional[str] = None
    task_type: str
    inputs: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {}
    constraints: List[str] = []
    acceptance_criteria: List[str] = []
    priority: int = 0
    status: str = "pending"
    created_by: str = "system"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    seed: Optional[int] = None

class AgentResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str
    outputs: List[Dict[str, Any]] = []
    metrics: Dict[str, Any] = {}
    decision_trace: List[str] = []
    logs_ref: Optional[str] = None

class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: str
    summary: str
    source_tool: Optional[str] = None
    source_run: Optional[str] = None
    source_step: Optional[str] = None
    payload: Dict[str, Any] = {}

class Decision(BaseModel):
    model_config = ConfigDict(extra="ignore")
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_type: str
    outcome: str
    confidence: float = 0.0
    rationale: List[str] = []

class ExplanationBundle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    summary: str
    details: str
    evidence: List[EvidenceItem] = []
    confidence_statement: Optional[str] = None

class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tool_name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    safety_level: str = "synthetic_only"
    allowed_teams: List[str] = []

class ToolCall(BaseModel):
    tool_name: str
    params: Dict[str, Any] = {}
    team_id: Optional[str] = None
    seed: Optional[int] = None

class ToolResult(BaseModel):
    tool_name: str
    status: str
    output: Dict[str, Any] = {}
    seed: Optional[int] = None

class AgentTrace(BaseModel):
    model_config = ConfigDict(extra="ignore")
    agent_id: str
    team_id: str
    plan: List[Dict[str, Any]] = []
    outputs: Dict[str, Any] = {}
    notes: List[str] = []

class TeamProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_id: str
    internal_name: str
    bank_facing_name: str
    color_token: str
    mission_statement: str
    capability_tags: List[str] = []
    default_agent_roles: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TeamProfileCreate(BaseModel):
    team_id: str
    internal_name: str
    bank_facing_name: str
    color_token: str
    mission_statement: str
    capability_tags: List[str] = []
    default_agent_roles: List[str] = []

class AgentProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    team_id: str
    role: str
    capabilities: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []
    operating_mode: str = "manual"
    guardrails: List[str] = []
    status: str = "idle"
    metrics: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentProfileCreate(BaseModel):
    agent_name: str
    team_id: str
    role: str
    capabilities: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []
    operating_mode: str = "manual"
    guardrails: List[str] = []
    status: str = "idle"
    metrics: Dict[str, Any] = {}

class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_team: str
    to_team: str
    artifact_type: str
    priority: str = "medium"
    due_by: Optional[str] = None
    payload: Dict[str, Any] = {}
    status: str = "open"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    responded_at: Optional[str] = None

class AgentRequestCreate(BaseModel):
    from_team: str
    to_team: str
    artifact_type: str
    priority: str = "medium"
    due_by: Optional[str] = None
    payload: Dict[str, Any] = {}

class AgentRequestDecision(BaseModel):
    status: str = "fulfilled"
    response: Dict[str, Any] = {}

class RAGDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    collection: str
    title: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None
    synthetic_only: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RAGDocumentCreate(BaseModel):
    collection: str
    title: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}
    synthetic_only: bool = True

class RAGQueryRequest(BaseModel):
    query: str
    collections: Optional[List[str]] = None
    top_k: int = 5
    use_hybrid: bool = True
    include_graph_context: bool = True
    retrieval_threshold: float = 0.55
    max_context_tokens: int = 1200
    synthetic_only: bool = True
    run_id: Optional[str] = None
    team_id: Optional[str] = None

class RAGHit(BaseModel):
    doc_id: str
    collection: str
    title: Optional[str]
    score: float
    snippet: str
    metadata: Dict[str, Any] = {}

class RAGResponse(BaseModel):
    query: str
    answer: str
    hits: List[RAGHit] = []
    context: List[str] = []
    graph_context: List[Dict[str, Any]] = []
    retrieval_score: float = 0.0
    used_fallback: bool = False
    generated_by: str = "synthetic"

# ============== AUTH HELPERS ==============

def create_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role, "exp": datetime.now(timezone.utc).timestamp() + 86400}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== RUN SESSION HELPERS ==============

TRACE_ROOT = ROOT_DIR / "run_artifacts"

class EventBus:
    def __init__(self):
        self.active_queues: Dict[str, asyncio.Queue] = {}

    def get_queue(self, run_id: str) -> asyncio.Queue:
        if run_id not in self.active_queues:
            self.active_queues[run_id] = asyncio.Queue()
        return self.active_queues[run_id]

    async def publish(self, run_id: str, event: Dict[str, Any]):
        queue = self.active_queues.get(run_id)
        if queue:
            await queue.put(event)

event_bus = EventBus()

def _append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

def _get_trace_path(run_id: str) -> Path:
    return TRACE_ROOT / run_id / "trace.jsonl"

async def write_trace(run_id: str, entry: Dict[str, Any]) -> None:
    entry_with_time = {**entry, "trace_ts": datetime.now(timezone.utc).isoformat()}
    trace_path = _get_trace_path(run_id)
    await asyncio.to_thread(_append_line, trace_path, json.dumps(entry_with_time, default=str))

async def record_run_event(run_id: str, event_type: str, payload: Dict[str, Any]) -> RunEvent:
    event = RunEvent(run_id=run_id, event_type=event_type, payload=payload)
    await db.run_events.insert_one(event.model_dump())
    await event_bus.publish(run_id, event.model_dump())
    await write_trace(run_id, {"event_type": event_type, "payload": payload})
    return event

# ============== AUDIT HELPERS ==============

async def record_audit(actor_id: str, action: str, target_type: str, target_id: str, decision: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> AuditLogEntry:
    entry = AuditLogEntry(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        decision=decision,
        metadata=metadata or {},
    )
    await db.audit_logs.insert_one(entry.model_dump())
    return entry

def rule_tests_pass(test_results: Optional[Dict[str, Any]]) -> bool:
    if not test_results:
        return False
    failed = test_results.get("failed", 1)
    coverage = test_results.get("coverage", 0)
    return failed == 0 and coverage >= 80

def redact_evidence_pack(pack: Dict[str, Any], mode: str) -> Dict[str, Any]:
    if mode == "internal":
        return pack

    redacted = {k: v for k, v in pack.items() if k not in {"logs", "contributing_factors"}}
    redacted["logs"] = [
        {
            "event_type": entry.get("event_type"),
            "rule_id": entry.get("rule_id"),
        }
        for entry in pack.get("logs", [])
    ]
    redacted["contributing_factors"] = [
        {"factor": factor.get("factor")}
        for factor in pack.get("contributing_factors", [])
    ]
    return redacted

# ============== TEAM + AGENT HELPERS ==============

def _default_team_payloads() -> List[Dict[str, Any]]:
    return [
        {
            "team_id": "red",
            "internal_name": "Red Team",
            "bank_facing_name": "The Challengers",
            "color_token": "red",
            "mission_statement": "Simulate real-world fraudsters and evolve attacks.",
            "capability_tags": ["attack", "simulation", "mutation"],
            "default_agent_roles": ["Orchestrator", "Scenario Generator", "Executor"],
        },
        {
            "team_id": "blue",
            "internal_name": "Blue Team",
            "bank_facing_name": "The Defenders",
            "color_token": "blue",
            "mission_statement": "Detect, prevent, and respond to fraud in real time.",
            "capability_tags": ["detection", "response", "scoring"],
            "default_agent_roles": ["Orchestrator", "Rule Evaluator", "Decision Agent"],
        },
        {
            "team_id": "purple",
            "internal_name": "Purple Team",
            "bank_facing_name": "The Strategists",
            "color_token": "purple",
            "mission_statement": "Design strategies, rules, and threat models.",
            "capability_tags": ["strategy", "rule-design", "threat-model"],
            "default_agent_roles": ["Orchestrator", "Root Cause Analyst", "Rule Author"],
        },
        {
            "team_id": "green",
            "internal_name": "Green Team",
            "bank_facing_name": "The Builders",
            "color_token": "green",
            "mission_statement": "Implement strategies and rules into production code.",
            "capability_tags": ["implementation", "integration", "features"],
            "default_agent_roles": ["Orchestrator", "Rule-to-Code Translator", "Feature Engineer"],
        },
        {
            "team_id": "black",
            "internal_name": "Black Team",
            "bank_facing_name": "The Stressors",
            "color_token": "black",
            "mission_statement": "Stress test robustness and discover edge cases.",
            "capability_tags": ["chaos", "stress", "regression"],
            "default_agent_roles": ["Orchestrator", "Edge-Case Generator", "Chaos Injector"],
        },
        {
            "team_id": "orange",
            "internal_name": "Orange Team",
            "bank_facing_name": "The Gatekeepers",
            "color_token": "orange",
            "mission_statement": "Review, validate, and approve releases.",
            "capability_tags": ["review", "security", "release"],
            "default_agent_roles": ["Orchestrator", "Security Reviewer", "Release Assessor"],
        },
        {
            "team_id": "gold",
            "internal_name": "Gold Team",
            "bank_facing_name": "The Narrators",
            "color_token": "gold",
            "mission_statement": "Explain decisions with evidence and narratives.",
            "capability_tags": ["explainability", "narrative", "audit"],
            "default_agent_roles": ["Orchestrator", "Decision Explainer", "Evidence Trace"],
        },
        {
            "team_id": "white",
            "internal_name": "White Team",
            "bank_facing_name": "The Council",
            "color_token": "white",
            "mission_statement": "Ensure compliance, fairness, and audit readiness.",
            "capability_tags": ["compliance", "ethics", "audit"],
            "default_agent_roles": ["Orchestrator", "Policy Reviewer", "Compliance Auditor"],
        },
    ]

def _default_agent_payloads() -> List[Dict[str, Any]]:
    return [
        {
            "agent_name": "Red Orchestrator",
            "team_id": "red",
            "role": "Campaign Manager",
            "capabilities": ["planning", "delegation", "attack-design"],
            "inputs": ["Scenario"],
            "outputs": ["AttackPlan"],
            "operating_mode": "auto",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "Blue Orchestrator",
            "team_id": "blue",
            "role": "Defense Manager",
            "capabilities": ["detection", "decisioning", "response"],
            "inputs": ["Telemetry"],
            "outputs": ["Decision"],
            "operating_mode": "auto",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "Purple Strategist",
            "team_id": "purple",
            "role": "Rule Author",
            "capabilities": ["rule-design", "analysis"],
            "inputs": ["Evidence", "Telemetry"],
            "outputs": ["RuleSpec"],
            "operating_mode": "semi-auto",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "Green Builder",
            "team_id": "green",
            "role": "Rule-to-Code Translator",
            "capabilities": ["implementation", "testing"],
            "inputs": ["RuleSpec"],
            "outputs": ["Patch"],
            "operating_mode": "semi-auto",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "Black Stressor",
            "team_id": "black",
            "role": "Chaos Injection",
            "capabilities": ["stress", "edge-cases"],
            "inputs": ["Patch"],
            "outputs": ["StressTestReport"],
            "operating_mode": "auto",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "Orange Gatekeeper",
            "team_id": "orange",
            "role": "Release Reviewer",
            "capabilities": ["review", "approval"],
            "inputs": ["Patch", "TestEvidence"],
            "outputs": ["ApprovalDecision"],
            "operating_mode": "manual",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "Gold Narrator",
            "team_id": "gold",
            "role": "Decision Explainer",
            "capabilities": ["xai", "narrative"],
            "inputs": ["Decision", "Evidence"],
            "outputs": ["ExplanationPack"],
            "operating_mode": "auto",
            "guardrails": ["synthetic_only"],
        },
        {
            "agent_name": "White Council",
            "team_id": "white",
            "role": "Compliance Auditor",
            "capabilities": ["compliance", "audit"],
            "inputs": ["ApprovalDecision", "Evidence"],
            "outputs": ["CompliancePack"],
            "operating_mode": "manual",
            "guardrails": ["synthetic_only"],
        },
    ]

# ============== RAG HELPERS ==============

def _tokenize(text: str) -> List[str]:
    return [t for t in "".join([c.lower() if c.isalnum() else " " for c in text]).split() if t]

def _keyword_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = len(set(query_tokens) & set(doc_tokens))
    return overlap / max(len(set(query_tokens)), 1)

def _simple_embed(text: str, dim: int = 128) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vector = [0.0] * dim
    for i, b in enumerate(digest):
        vector[i % dim] += (b / 255.0) - 0.5
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm else vector

async def _get_embedding(text: str) -> List[float]:
    if openai_client:
        try:
            response = await openai_client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.warning(f"Embedding fallback: {exc}")
    return _simple_embed(text)

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    length = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(length))
    norm_a = sum(a[i] * a[i] for i in range(length)) ** 0.5
    norm_b = sum(b[i] * b[i] for i in range(length)) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def _approx_tokens(text: str) -> int:
    return len(text.split())

def _build_context_snippets(hits: List[Dict[str, Any]], max_tokens: int) -> List[str]:
    snippets: List[str] = []
    running = 0
    for hit in hits:
        content = hit.get("content", "")
        chunk = f"[{hit.get('collection')}:{hit.get('id')}] {content}"
        chunk_tokens = _approx_tokens(chunk)
        if running + chunk_tokens > max_tokens:
            break
        snippets.append(chunk)
        running += chunk_tokens
    return snippets

def _contains_sensitive_identifiers(text: str) -> bool:
    digits = [c for c in text if c.isdigit()]
    if len(digits) >= 9:
        return True
    lowered = text.lower()
    flags = ["ssn", "social security", "account number", "routing number", "credit card"]
    return any(flag in lowered for flag in flags)

# ============== XAI HELPERS ==============

def build_evidence_items(events: List[Dict[str, Any]], max_items: int = 6) -> List[EvidenceItem]:
    evidence_items: List[EvidenceItem] = []
    for event in events[-max_items:]:
        summary = event.get("event_type", "signal")
        payload = event.get("payload", {})
        evidence_items.append(
            EvidenceItem(
                evidence_type=summary,
                summary=f"Event {summary} recorded",
                source_tool=payload.get("tool"),
                source_run=event.get("run_id"),
                source_step=payload.get("step"),
                payload=payload,
            )
        )
    return evidence_items

def build_explanation_bundle(run_id: str, decision: str, evidence_items: List[EvidenceItem]) -> ExplanationBundle:
    summary = f"Decision '{decision}' generated from synthetic evidence for run {run_id}."
    details = "Evidence items include simulator outputs, risk scores, and response actions."
    confidence_statement = "Confidence is based on deterministic synthetic scoring." 
    return ExplanationBundle(
        decision_id=decision,
        summary=summary,
        details=details,
        evidence=evidence_items,
        confidence_statement=confidence_statement,
    )

# ============== GRAPH + DIFF HELPERS ==============

def build_run_graph(run_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    def _add_node(node_id: str, node_type: str, label: str) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "type": node_type, "label": label}

    run_node = f"run:{run_id}"
    _add_node(run_node, "run", f"Run {run_id}")

    for event in events:
        event_id = event.get("id") or str(uuid.uuid4())
        event_type = event.get("event_type", "event")
        event_node = f"event:{event_id}"
        _add_node(event_node, "event", event_type)
        edges.append({"source": run_node, "target": event_node, "type": "emits"})

        payload = event.get("payload", {})
        agent = payload.get("agent")
        if agent:
            agent_node = f"agent:{agent}"
            _add_node(agent_node, "agent", agent)
            edges.append({"source": agent_node, "target": event_node, "type": "produces"})

        tool = payload.get("tool")
        if tool:
            tool_node = f"tool:{tool}"
            _add_node(tool_node, "tool", tool)
            edges.append({"source": tool_node, "target": event_node, "type": "feeds"})

    return {"nodes": list(nodes.values()), "edges": edges}

def summarize_run_metrics(run: Dict[str, Any]) -> Dict[str, Any]:
    last_metrics = run.get("last_metrics", {})
    return {
        "avg_score": last_metrics.get("avg_score", 0),
        "decision": run.get("last_decision", "unknown"),
        "actions": last_metrics.get("actions", 0),
        "steps": run.get("step_count", 0),
    }

def run_quality_checks(run: Dict[str, Any], events: List[Dict[str, Any]]) -> QualityCheckResult:
    issues: List[Dict[str, Any]] = []
    last_decision = run.get("last_decision")
    if not last_decision:
        issues.append({"check": "decision_present", "status": "fail", "message": "Missing decision"})
    else:
        issues.append({"check": "decision_present", "status": "pass"})

    evidence_events = [e for e in events if e.get("event_type") == "xai.generated"]
    if not evidence_events:
        issues.append({"check": "xai_generated", "status": "warn", "message": "No XAI bundle generated"})
    else:
        issues.append({"check": "xai_generated", "status": "pass"})

    status = "pass" if all(i["status"] == "pass" for i in issues) else "warn"
    return QualityCheckResult(run_id=run.get("id", "unknown"), status=status, checks=issues)

def build_evaluation_report(run: Dict[str, Any]) -> EvaluationReport:
    metrics = summarize_run_metrics(run)
    summary = "Run evaluation completed with synthetic checks."
    return EvaluationReport(run_id=run.get("id", "unknown"), summary=summary, metrics=metrics)

# ============== TOOL REGISTRY + SIMULATOR ==============

def _derive_seed(base_seed: int, salt: str) -> int:
    seed_input = f"{base_seed}:{salt}".encode("utf-8")
    return int(hashlib.sha256(seed_input).hexdigest()[:12], 16)

def _rng(seed: int) -> random.Random:
    return random.Random(seed)

def _simulate_transactions(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    rng = _rng(seed)
    count = int(params.get("count", 25))
    scenario = params.get("scenario", "demo")
    rails = params.get("rails", ["cards", "upi", "ach"])
    events = []
    for idx in range(count):
        amount = round(rng.uniform(5, 5000), 2)
        event = {
            "event_id": f"tx_{seed}_{idx}",
            "scenario": scenario,
            "rail": rails[idx % len(rails)],
            "amount": amount,
            "velocity_bucket": "high" if amount > 2500 else "normal",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        events.append(event)
    return {"events": events, "count": len(events)}

def _apply_attack(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    rng = _rng(seed)
    events = params.get("events", [])
    attack_type = params.get("attack_type", "velocity_anomaly")
    mutated = []
    for event in events:
        mutated_event = {**event}
        if attack_type == "velocity_anomaly":
            mutated_event["velocity_bucket"] = "spike"
            mutated_event["amount"] = round(float(event.get("amount", 0)) * rng.uniform(1.2, 2.2), 2)
        elif attack_type == "identity_mismatch":
            mutated_event["identity_match"] = False
        else:
            mutated_event["signal"] = "synthetic_variation"
        mutated.append(mutated_event)
    return {"attacked_events": mutated, "attack_type": attack_type}

def _score_risk(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    rng = _rng(seed)
    events = params.get("events", [])
    scores = []
    for event in events:
        base = 0.35 if event.get("velocity_bucket") == "spike" else 0.15
        score = min(0.99, base + rng.uniform(0.05, 0.4))
        scores.append({"event_id": event.get("event_id"), "risk_score": round(score, 3)})
    return {"scores": scores, "avg_score": round(sum(s["risk_score"] for s in scores) / max(len(scores), 1), 3)}

def _respond_actions(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    rng = _rng(seed)
    scores = params.get("scores", [])
    actions = []
    for score in scores:
        risk = score.get("risk_score", 0)
        if risk >= 0.8:
            action = "block"
        elif risk >= 0.5:
            action = "review"
        else:
            action = "allow"
        actions.append({"event_id": score.get("event_id"), "action": action, "risk_score": risk})
    return {"actions": actions, "decision": rng.choice(["contain", "monitor", "escalate"])}

TOOL_REGISTRY: Dict[str, ToolSpec] = {
    "simulate_transactions": ToolSpec(
        tool_name="simulate_transactions",
        description="Generate synthetic transaction events for a scenario.",
        input_schema={"scenario": "string", "count": "int", "rails": "list"},
        output_schema={"events": "list", "count": "int"},
        allowed_teams=["red", "blue", "black", "gold"],
    ),
    "apply_attack": ToolSpec(
        tool_name="apply_attack",
        description="Apply synthetic attack patterns to events.",
        input_schema={"events": "list", "attack_type": "string"},
        output_schema={"attacked_events": "list", "attack_type": "string"},
        allowed_teams=["red"],
    ),
    "score_risk": ToolSpec(
        tool_name="score_risk",
        description="Score synthetic events for risk.",
        input_schema={"events": "list"},
        output_schema={"scores": "list", "avg_score": "float"},
        allowed_teams=["blue", "green", "black"],
    ),
    "respond_actions": ToolSpec(
        tool_name="respond_actions",
        description="Generate response actions based on risk scores.",
        input_schema={"scores": "list"},
        output_schema={"actions": "list", "decision": "string"},
        allowed_teams=["blue", "orange", "white"],
    ),
}

TOOL_IMPLEMENTATIONS = {
    "simulate_transactions": _simulate_transactions,
    "apply_attack": _apply_attack,
    "score_risk": _score_risk,
    "respond_actions": _respond_actions,
}

# ============== AGENTS V1 ==============

class BaseAgent:
    agent_id: str
    team_id: str

    def __init__(self, agent_id: str, team_id: str):
        self.agent_id = agent_id
        self.team_id = team_id

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        outputs: Dict[str, Any] = {}
        for step in plan_steps:
            tool_name = step.get("tool")
            params = step.get("params", {})
            impl = TOOL_IMPLEMENTATIONS.get(tool_name)
            if not impl:
                continue
            step_seed = _derive_seed(seed, tool_name)
            outputs[tool_name] = impl(params, step_seed)
        return outputs

    async def reflect(self, outputs: Dict[str, Any]) -> List[str]:
        return []

    async def emit(self, context: Dict[str, Any], seed: int) -> AgentTrace:
        plan_steps = await self.plan(context)
        outputs = await self.act(plan_steps, seed)
        notes = await self.reflect(outputs)
        return AgentTrace(agent_id=self.agent_id, team_id=self.team_id, plan=plan_steps, outputs=outputs, notes=notes)

class RedAgent(BaseAgent):
    def __init__(self):
        super().__init__("red.orchestrator.v1", "red")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        scenario = context.get("scenario_id", "demo")
        return [
            {"tool": "simulate_transactions", "params": {"scenario": scenario, "count": 25, "rails": ["cards", "upi", "ach"]}},
            {"tool": "apply_attack", "params": {"attack_type": "velocity_anomaly", "events": context.get("events", [])}},
        ]

class BlueAgent(BaseAgent):
    def __init__(self):
        super().__init__("blue.orchestrator.v1", "blue")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        events = context.get("events", [])
        return [
            {"tool": "score_risk", "params": {"events": events}},
            {"tool": "respond_actions", "params": {"scores": context.get("scores", [])}},
        ]

class GoldAgent(BaseAgent):
    def __init__(self):
        super().__init__("gold.orchestrator.v1", "gold")

    async def plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    async def act(self, plan_steps: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
        decision = context.get("decision", "monitor")
        summary = f"Gold team summary: decision={decision} based on synthetic signals."
        details = "Signals indicate elevated velocity and risk scoring."
        return {"summary": summary, "details": details}

RED_AGENT = RedAgent()
BLUE_AGENT = BlueAgent()
GOLD_AGENT = GoldAgent()

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=Dict[str, Any])
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user_data.password)
    user = User(email=user_data.email, name=user_data.name, role=user_data.role)
    user_dict = user.model_dump()
    user_dict["password_hash"] = hashed_password
    
    await db.users.insert_one(user_dict)
    token = create_token(user.id, user.role)
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}}

# ============== RUN SESSION ROUTES ==============

@api_router.post("/runs/start", response_model=RunSession)
async def start_run(payload: RunStartRequest):
    seed_value = payload.seed if payload.seed is not None else int(datetime.now(timezone.utc).timestamp())
    run = RunSession(scenario_id=payload.scenario_id, seed=seed_value, mode=payload.mode)
    await db.runs.insert_one(run.model_dump())
    await record_run_event(run.id, "run.started", {"scenario_id": run.scenario_id, "seed": run.seed, "mode": run.mode})
    return run

@api_router.get("/runs/{run_id}", response_model=Dict[str, Any])
async def get_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return {"run": run, "events": events}

@api_router.post("/runs/{run_id}/step", response_model=Dict[str, Any])
async def step_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    step_index = int(run.get("step_count", 0)) + 1
    base_seed = int(run.get("seed", int(datetime.now(timezone.utc).timestamp())))
    step_seed = _derive_seed(base_seed, f"step-{step_index}")

    await record_run_event(run_id, "stage.changed", {"stage": "red_simulate", "step": step_index})
    red_trace = await RED_AGENT.emit({"scenario_id": run.get("scenario_id")}, step_seed)
    simulated = red_trace.outputs.get("simulate_transactions", {})
    attacked = red_trace.outputs.get("apply_attack", {})

    events = attacked.get("attacked_events") or simulated.get("events") or []
    await record_run_event(run_id, "agent.output", {"agent": red_trace.agent_id, "team": red_trace.team_id, "outputs": red_trace.outputs})

    await record_run_event(run_id, "stage.changed", {"stage": "blue_detect", "step": step_index})
    blue_trace = await BLUE_AGENT.emit({"events": events}, step_seed)
    scored = blue_trace.outputs.get("score_risk", {})
    response = blue_trace.outputs.get("respond_actions", {})
    await record_run_event(run_id, "agent.output", {"agent": blue_trace.agent_id, "team": blue_trace.team_id, "outputs": blue_trace.outputs})

    decision = response.get("decision", "monitor")
    await record_run_event(run_id, "stage.changed", {"stage": "gold_explain", "step": step_index})
    gold_trace = await GOLD_AGENT.emit({"decision": decision}, step_seed)
    await record_run_event(run_id, "agent.output", {"agent": gold_trace.agent_id, "team": gold_trace.team_id, "outputs": gold_trace.outputs})

    update_fields = {
        "current_stage": "gold_explain",
        "step_count": step_index,
        "last_decision": decision,
        "last_metrics": {
            "avg_score": scored.get("avg_score", 0),
            "decision": decision,
            "actions": len(response.get("actions", [])),
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.runs.update_one({"id": run_id}, {"$set": update_fields})
    return {
        "run_id": run_id,
        "step": step_index,
        "red": red_trace.model_dump(),
        "blue": blue_trace.model_dump(),
        "gold": gold_trace.model_dump(),
        "metrics": update_fields["last_metrics"],
    }

# ============== XAI ROUTES ==============

@api_router.get("/xai/explain/{run_id}", response_model=ExplanationBundle)
async def explain_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    decision = run.get("last_decision", "monitor")
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    evidence_items = build_evidence_items(events)
    bundle = build_explanation_bundle(run_id, decision, evidence_items)

    await record_run_event(run_id, "xai.generated", {
        "decision": decision,
        "bundle_id": bundle.bundle_id,
        "evidence_count": len(evidence_items),
    })

    return bundle

# ============== GRAPH + COMPARE ROUTES ==============

@api_router.get("/runs/{run_id}/graph")
async def get_run_graph(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    graph = build_run_graph(run_id, events)
    return {"run_id": run_id, "graph": graph}

@api_router.get("/runs/compare")
async def compare_runs(run_a: str, run_b: str):
    run_a_doc = await db.runs.find_one({"id": run_a}, {"_id": 0})
    run_b_doc = await db.runs.find_one({"id": run_b}, {"_id": 0})

    if not run_a_doc or not run_b_doc:
        raise HTTPException(status_code=404, detail="Run not found")

    metrics_a = summarize_run_metrics(run_a_doc)
    metrics_b = summarize_run_metrics(run_b_doc)

    delta = {
        "avg_score": metrics_b["avg_score"] - metrics_a["avg_score"],
        "actions": metrics_b["actions"] - metrics_a["actions"],
        "steps": metrics_b["steps"] - metrics_a["steps"],
        "decision_changed": metrics_a["decision"] != metrics_b["decision"],
    }

    return {"run_a": metrics_a, "run_b": metrics_b, "delta": delta}

@api_router.get("/tools", response_model=List[ToolSpec])
async def list_tools():
    return list(TOOL_REGISTRY.values())

@api_router.post("/tools/{tool_name}/run", response_model=ToolResult)
async def run_tool(tool_name: str, payload: ToolCall):
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if payload.team_id and tool.allowed_teams and payload.team_id not in tool.allowed_teams:
        raise HTTPException(status_code=403, detail="Team not allowed to run this tool")

    base_seed = payload.seed if payload.seed is not None else int(datetime.now(timezone.utc).timestamp())
    derived_seed = _derive_seed(base_seed, tool_name)
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if not impl:
        raise HTTPException(status_code=500, detail="Tool implementation missing")

    output = impl(payload.params, derived_seed)
    return ToolResult(tool_name=tool_name, status="ok", output=output, seed=derived_seed)

@api_router.post("/auth/login", response_model=Dict[str, Any])
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email}, {"_id": 0})
    if not user or not pwd_context.verify(login_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["role"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}}

@api_router.get("/auth/me", response_model=Dict[str, Any])
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"], "name": current_user["name"], "role": current_user["role"]}

# ============== BATTLE ROUTES ==============

@api_router.get("/battles", response_model=List[Battle])
async def get_battles():
    battles = await db.battles.find({}, {"_id": 0}).to_list(100)
    return battles

@api_router.get("/battles/{battle_id}", response_model=Battle)
async def get_battle(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    return battle

@api_router.post("/battles", response_model=Battle)
async def create_battle(battle_data: BattleCreate):
    battle = Battle(scenario_name=battle_data.scenario_name, parameters=battle_data.parameters)
    await db.battles.insert_one(battle.model_dump())
    return battle

@api_router.post("/battles/{battle_id}/start", response_model=Battle)
async def start_battle(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    await db.battles.update_one({"id": battle_id}, {"$set": {"status": "running"}})
    battle["status"] = "running"
    return battle

@api_router.post("/battles/{battle_id}/stop", response_model=Battle)
async def stop_battle(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    completed_at = datetime.now(timezone.utc).isoformat()
    await db.battles.update_one({"id": battle_id}, {"$set": {"status": "completed", "completed_at": completed_at}})
    battle["status"] = "completed"
    battle["completed_at"] = completed_at
    return battle

@api_router.delete("/battles/{battle_id}")
async def delete_battle(battle_id: str):
    result = await db.battles.delete_one({"id": battle_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Battle not found")
    return {"message": "Battle deleted"}

# ============== RULE ROUTES ==============

@api_router.get("/rules", response_model=List[Rule])
async def get_rules():
    rules = await db.rules.find({}, {"_id": 0}).to_list(100)
    return rules

@api_router.get("/rules/{rule_id}", response_model=Rule)
async def get_rule(rule_id: str):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@api_router.post("/rules", response_model=Rule)
async def create_rule(rule_data: RuleCreate):
    rule = Rule(**rule_data.model_dump())
    await db.rules.insert_one(rule.model_dump())
    return rule

@api_router.put("/rules/{rule_id}", response_model=Rule)
async def update_rule(rule_id: str, rule_data: RuleCreate):
    existing = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    updated_at = datetime.now(timezone.utc).isoformat()
    update_data = rule_data.model_dump()
    update_data["updated_at"] = updated_at
    update_data["version"] = existing.get("version", 1) + 1
    
    await db.rules.update_one({"id": rule_id}, {"$set": update_data})
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

@api_router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    result = await db.rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}

@api_router.post("/rules/{rule_id}/test", response_model=Dict[str, Any])
async def test_rule(rule_id: str):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Simulate test results
    import random
    test_results = {
        "passed": random.randint(8, 15),
        "failed": random.randint(0, 3),
        "total": 15,
        "coverage": round(random.uniform(85, 100), 2),
        "execution_time": round(random.uniform(0.1, 2.0), 3),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rules.update_one(
        {"id": rule_id},
        {"$set": {"test_results": test_results, "status": "tested"}}
    )
    return test_results

@api_router.post("/rules/propose", response_model=Dict[str, Any])
async def propose_rule(rule_data: RuleProposalCreate):
    rule = Rule(
        name=rule_data.name,
        description=rule_data.description,
        rule_type=rule_data.rule_type,
        conditions=rule_data.conditions,
        actions=rule_data.actions,
        priority=rule_data.priority,
        status="proposed",
        proposed_by=rule_data.requestor_id,
    )
    await db.rules.insert_one(rule.model_dump())

    approval = ApprovalRequest(
        resource_type="rule",
        resource_id=rule.id,
        action="approve",
        requestor_id=rule_data.requestor_id,
        metadata=rule_data.metadata,
    )
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(
        rule_data.requestor_id,
        "rule_proposed",
        "rule",
        rule.id,
        metadata=rule_data.metadata,
    )
    return {"rule": rule, "approval_request": approval}

@api_router.post("/rules/{rule_id}/approve", response_model=Rule)
async def approve_rule(rule_id: str, decision: RuleApprovalDecision):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if decision.decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be approved or rejected")

    status = "approved" if decision.decision == "approved" else "rejected"
    approved_at = datetime.now(timezone.utc).isoformat()
    await db.rules.update_one(
        {"id": rule_id},
        {"$set": {"status": status, "approved_by": decision.approver_id, "approved_at": approved_at}}
    )

    await db.approvals.update_one(
        {"resource_id": rule_id, "status": "pending"},
        {
            "$set": {"status": status},
            "$push": {"approvers": {"id": decision.approver_id, "decision": status, "notes": decision.notes}},
        },
    )
    await record_audit(
        decision.approver_id,
        "rule_approval",
        "rule",
        rule_id,
        decision=status,
        metadata={"notes": decision.notes},
    )
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

@api_router.post("/rules/{rule_id}/stage", response_model=Rule)
async def stage_rule(rule_id: str, request: RuleActionRequest):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule.get("status") not in {"approved", "tested"}:
        raise HTTPException(status_code=400, detail="Rule must be approved before staging")

    if not rule_tests_pass(rule.get("test_results")):
        raise HTTPException(status_code=400, detail="Rule tests must pass before staging")

    await db.rules.update_one({"id": rule_id}, {"$set": {"status": "staged"}})
    await record_audit(
        request.actor_id,
        "rule_staged",
        "rule",
        rule_id,
        metadata=request.metadata,
    )
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

@api_router.post("/rules/{rule_id}/deploy", response_model=Rule)
async def deploy_rule(rule_id: str, request: RuleActionRequest):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule.get("status") != "staged":
        raise HTTPException(status_code=400, detail="Rule must be staged before deployment")

    await db.rules.update_one({"id": rule_id}, {"$set": {"status": "deployed"}})
    await record_audit(
        request.actor_id,
        "rule_deployed",
        "rule",
        rule_id,
        metadata=request.metadata,
    )
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

# ============== RSB PACKAGE ROUTES ==============

@api_router.get("/rsb-packages", response_model=List[RSBPackage])
async def get_rsb_packages():
    packages = await db.rsb_packages.find({}, {"_id": 0}).to_list(100)
    return packages

@api_router.get("/rsb-packages/{package_id}", response_model=RSBPackage)
async def get_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    return package

@api_router.post("/rsb-packages", response_model=RSBPackage)
async def create_rsb_package(package_data: RSBPackageCreate):
    package = RSBPackage(**package_data.model_dump())
    await db.rsb_packages.insert_one(package.model_dump())
    return package

@api_router.post("/rsb-packages/{package_id}/test", response_model=Dict[str, Any])
async def test_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    
    import random
    test_results = {
        "unit_tests": {"passed": random.randint(20, 30), "failed": random.randint(0, 2), "total": 30},
        "integration_tests": {"passed": random.randint(8, 12), "failed": random.randint(0, 1), "total": 12},
        "compliance_checks": {"passed": random.randint(5, 8), "failed": 0, "total": 8},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"test_results": test_results, "status": "tested"}})
    return test_results

@api_router.post("/rsb-packages/{package_id}/merge", response_model=Dict[str, Any])
async def merge_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    
    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"status": "merged"}})
    return {"message": "Package merged successfully", "status": "merged"}

@api_router.delete("/rsb-packages/{package_id}")
async def delete_rsb_package(package_id: str):
    result = await db.rsb_packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    return {"message": "RSB Package deleted"}

# ============== EVIDENCE PACK ROUTES ==============

@api_router.get("/evidence-packs", response_model=List[EvidencePack])
async def get_evidence_packs():
    packs = await db.evidence_packs.find({}, {"_id": 0}).to_list(100)
    return packs

@api_router.get("/evidence-packs/{pack_id}", response_model=EvidencePack)
async def get_evidence_pack(pack_id: str):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    return pack

@api_router.post("/evidence-packs/generate/{battle_id}", response_model=EvidencePack)
async def generate_evidence_pack(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    # Generate evidence pack from battle data
    pack_data = {
        "battle_id": battle_id,
        "narrative": f"Battle '{battle['scenario_name']}' completed with {len(battle.get('turns', []))} turns.",
        "triggered_rules": [t.get("rule_id", "unknown") for t in battle.get("turns", []) if t.get("rule_id")],
        "contributing_factors": [{"factor": "Pattern match", "weight": 0.8}, {"factor": "Velocity check", "weight": 0.6}],
        "confidence": 0.92,
        "logs": battle.get("turns", [])[-10:] if battle.get("turns") else []
    }
    
    pack = EvidencePack(**pack_data)
    pack_dict = pack.model_dump()
    pack_dict["checksum"] = hashlib.sha256(json.dumps(pack_dict, sort_keys=True, default=str).encode()).hexdigest()
    
    await db.evidence_packs.insert_one(pack_dict)
    return pack_dict

@api_router.get("/evidence-packs/{pack_id}/export")
async def export_evidence_pack(pack_id: str, mode: str = "internal", requestor_id: Optional[str] = None):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")

    if mode not in {"internal", "external"}:
        raise HTTPException(status_code=400, detail="Invalid export mode")

    if mode == "external":
        approval = await db.approvals.find_one(
            {
                "resource_type": "evidence_pack",
                "resource_id": pack_id,
                "action": "export",
                "status": "approved",
            },
            {"_id": 0},
        )
        if not approval:
            raise HTTPException(status_code=403, detail="External export requires approval")

    redacted_pack = redact_evidence_pack(pack, mode)
    if requestor_id:
        await record_audit(
            requestor_id,
            "evidence_pack_export",
            "evidence_pack",
            pack_id,
            decision=mode,
            metadata={"mode": mode},
        )
    
    return {
        "filename": f"evidence_pack_{pack_id}.json",
        "content_type": "application/json",
        "data": redacted_pack,
        "checksum": pack.get("checksum", ""),
        "export_mode": mode,
        "exported_at": datetime.now(timezone.utc).isoformat()
    }

@api_router.post("/evidence-packs/{pack_id}/request-export-approval", response_model=ApprovalRequest)
async def request_evidence_export_approval(pack_id: str, request: EvidenceExportApprovalRequest):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")

    approval = ApprovalRequest(
        resource_type="evidence_pack",
        resource_id=pack_id,
        action="export",
        requestor_id=request.requestor_id,
        metadata={"mode": request.mode, **request.metadata},
    )
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(
        request.requestor_id,
        "evidence_pack_export_requested",
        "evidence_pack",
        pack_id,
        metadata=approval.metadata,
    )
    return approval

# ============== TEAM + AGENT REGISTRY ROUTES ==============

@api_router.get("/teams", response_model=List[TeamProfile])
async def list_teams():
    teams = await db.teams.find({}, {"_id": 0}).to_list(50)
    if not teams:
        for payload in _default_team_payloads():
            team = TeamProfile(**payload)
            await db.teams.insert_one(team.model_dump())
        teams = await db.teams.find({}, {"_id": 0}).to_list(50)
    return teams

@api_router.get("/teams/{team_id}", response_model=TeamProfile)
async def get_team(team_id: str):
    team = await db.teams.find_one({"team_id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@api_router.post("/teams/seed")
async def seed_teams():
    existing = await db.teams.count_documents({})
    if existing:
        return {"message": "Teams already seeded", "count": existing}
    payloads = _default_team_payloads()
    teams = [TeamProfile(**payload).model_dump() for payload in payloads]
    if teams:
        await db.teams.insert_many(teams)
    return {"message": "Teams seeded", "count": len(teams)}

@api_router.get("/agents", response_model=List[AgentProfile])
async def list_agents(team_id: Optional[str] = None):
    query: Dict[str, Any] = {}
    if team_id:
        query["team_id"] = team_id
    agents = await db.agents.find(query, {"_id": 0}).to_list(200)
    return agents

@api_router.get("/agents/{agent_id}", response_model=AgentProfile)
async def get_agent(agent_id: str):
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@api_router.post("/agents/register", response_model=AgentProfile)
async def register_agent(agent_data: AgentProfileCreate):
    profile = AgentProfile(**agent_data.model_dump())
    await db.agents.insert_one(profile.model_dump())
    return profile

@api_router.post("/agents/seed")
async def seed_agents():
    existing = await db.agents.count_documents({})
    if existing:
        return {"message": "Agents already seeded", "count": existing}
    payloads = _default_agent_payloads()
    agents = [AgentProfile(**payload).model_dump() for payload in payloads]
    if agents:
        await db.agents.insert_many(agents)
    return {"message": "Agents seeded", "count": len(agents)}

@api_router.post("/agents/tasks", response_model=AgentTask)
async def create_agent_task(task_data: AgentTask):
    if task_data.inputs:
        joined = json.dumps(task_data.inputs, default=str)
        if _contains_sensitive_identifiers(joined):
            raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    await db.agent_tasks.insert_one(task_data.model_dump())
    return task_data

@api_router.get("/agents/tasks", response_model=List[AgentTask])
async def list_agent_tasks(run_id: Optional[str] = None, team_id: Optional[str] = None, status_filter: Optional[str] = None):
    query: Dict[str, Any] = {}
    if run_id:
        query["run_id"] = run_id
    if team_id:
        query["team_id"] = team_id
    if status_filter:
        query["status"] = status_filter
    tasks = await db.agent_tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return tasks

@api_router.post("/agents/tasks/{task_id}/complete", response_model=AgentResult)
async def complete_agent_task(task_id: str, result: AgentResult):
    task = await db.agent_tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.agent_tasks.update_one(
        {"task_id": task_id},
        {"$set": {"status": result.status, "result": result.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return result

@api_router.post("/agents/requests", response_model=AgentRequest)
async def create_agent_request(request_data: AgentRequestCreate):
    req = AgentRequest(**request_data.model_dump())
    await db.agent_requests.insert_one(req.model_dump())
    return req

@api_router.get("/agents/requests", response_model=List[AgentRequest])
async def list_agent_requests(team_id: Optional[str] = None, status_filter: Optional[str] = None):
    query: Dict[str, Any] = {}
    if team_id:
        query["$or"] = [{"from_team": team_id}, {"to_team": team_id}]
    if status_filter:
        query["status"] = status_filter
    requests = await db.agent_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return requests

@api_router.post("/agents/requests/{request_id}/respond", response_model=AgentRequest)
async def respond_agent_request(request_id: str, decision: AgentRequestDecision):
    request_doc = await db.agent_requests.find_one({"request_id": request_id}, {"_id": 0})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    updated = {
        "status": decision.status,
        "response": decision.response,
        "responded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.agent_requests.update_one({"request_id": request_id}, {"$set": updated})
    request_doc.update(updated)
    return request_doc

# ============== RAG ROUTES ==============

@api_router.get("/rag/collections")
async def list_rag_collections():
    collections = await db.rag_documents.distinct("collection")
    return {"collections": sorted(collections)}

@api_router.get("/rag/documents", response_model=List[RAGDocument])
async def list_rag_documents(collection: Optional[str] = None, limit: int = 50):
    query: Dict[str, Any] = {}
    if collection:
        query["collection"] = collection
    docs = await db.rag_documents.find(query, {"_id": 0}).sort("created_at", -1).to_list(max(limit, 1))
    return docs

@api_router.post("/rag/documents", response_model=RAGDocument)
async def create_rag_document(doc_data: RAGDocumentCreate):
    if doc_data.synthetic_only and _contains_sensitive_identifiers(doc_data.content):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    embedding = await _get_embedding(doc_data.content)
    doc = RAGDocument(**doc_data.model_dump(), embedding=embedding)
    await db.rag_documents.insert_one(doc.model_dump())
    return doc

@api_router.post("/rag/seed")
async def seed_rag_data(reset: bool = False):
    if reset:
        await db.rag_documents.delete_many({})

    taxonomy_path = ROOT_DIR.parent / "banking_fraud_taxonomy_catalog_120.json"
    seeded = 0
    if taxonomy_path.exists():
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        if isinstance(taxonomy, list):
            for item in taxonomy:
                title = item.get("name") or item.get("id") or "Taxonomy"
                content = item.get("description") or json.dumps(item, ensure_ascii=False)
                embedding = await _get_embedding(content)
                doc = RAGDocument(
                    collection="taxonomy",
                    title=title,
                    content=content,
                    metadata=item,
                    embedding=embedding,
                )
                await db.rag_documents.insert_one(doc.model_dump())
                seeded += 1

    defaults = [
        {"collection": "attacks", "title": "Velocity Burst", "content": "Fraudsters split transactions into rapid bursts to evade single-threshold rules.", "metadata": {"team": "red"}},
        {"collection": "patterns", "title": "Account Takeover", "content": "ATO indicators: device mismatch, impossible travel, high-risk beneficiary changes.", "metadata": {"team": "blue"}},
        {"collection": "rules", "title": "VEL-001", "content": "Velocity rule: flag when tx_count > 5 in 10 minutes with shared device signals.", "metadata": {"team": "purple"}},
        {"collection": "explanations", "title": "Decision Template", "content": "Explain outcomes using top signals, rule hits, and confidence statement.", "metadata": {"team": "gold"}},
    ]
    for entry in defaults:
        embedding = await _get_embedding(entry["content"])
        doc = RAGDocument(**entry, embedding=embedding)
        await db.rag_documents.insert_one(doc.model_dump())
        seeded += 1

    return {"message": "RAG data seeded", "count": seeded}

@api_router.post("/rag/retrieve", response_model=List[RAGHit])
async def rag_retrieve(request: RAGQueryRequest):
    if request.synthetic_only and _contains_sensitive_identifiers(request.query):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    query: Dict[str, Any] = {}
    if request.collections:
        query["collection"] = {"$in": request.collections}
    if request.synthetic_only:
        query["synthetic_only"] = True
    docs = await db.rag_documents.find(query, {"_id": 0}).to_list(500)
    if not docs:
        return []

    query_embedding = await _get_embedding(request.query)
    query_tokens = _tokenize(request.query)
    scored: List[Dict[str, Any]] = []
    for doc in docs:
        doc_embedding = doc.get("embedding") or _simple_embed(doc.get("content", ""))
        vector_score = _cosine_similarity(query_embedding, doc_embedding)
        keyword_score = _keyword_score(query_tokens, _tokenize(doc.get("content", "")))
        score = vector_score if not request.use_hybrid else (0.7 * vector_score + 0.3 * keyword_score)
        scored.append({**doc, "score": score})

    scored.sort(key=lambda d: d.get("score", 0), reverse=True)
    hits: List[RAGHit] = []
    for doc in scored[: request.top_k]:
        snippet = doc.get("content", "")[:180]
        hits.append(
            RAGHit(
                doc_id=doc.get("id"),
                collection=doc.get("collection"),
                title=doc.get("title"),
                score=round(doc.get("score", 0), 4),
                snippet=snippet,
                metadata=doc.get("metadata", {}),
            )
        )
    return hits

@api_router.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGQueryRequest):
    if request.synthetic_only and _contains_sensitive_identifiers(request.query):
        raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")

    async def _retrieve(with_collections: Optional[List[str]]) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if with_collections:
            query["collection"] = {"$in": with_collections}
        if request.synthetic_only:
            query["synthetic_only"] = True
        docs = await db.rag_documents.find(query, {"_id": 0}).to_list(500)
        if not docs:
            return []
        query_embedding = await _get_embedding(request.query)
        query_tokens = _tokenize(request.query)
        scored_docs: List[Dict[str, Any]] = []
        for doc in docs:
            doc_embedding = doc.get("embedding") or _simple_embed(doc.get("content", ""))
            vector_score = _cosine_similarity(query_embedding, doc_embedding)
            keyword_score = _keyword_score(query_tokens, _tokenize(doc.get("content", "")))
            score = vector_score if not request.use_hybrid else (0.7 * vector_score + 0.3 * keyword_score)
            scored_docs.append({**doc, "score": score})
        scored_docs.sort(key=lambda d: d.get("score", 0), reverse=True)
        return scored_docs[: request.top_k]

    used_fallback = False
    scored_docs = await _retrieve(request.collections)
    avg_score = sum(doc.get("score", 0) for doc in scored_docs) / max(len(scored_docs), 1)
    if avg_score < request.retrieval_threshold:
        fallback_docs = await _retrieve(None)
        if fallback_docs:
            scored_docs = fallback_docs
            used_fallback = True
            avg_score = sum(doc.get("score", 0) for doc in scored_docs) / max(len(scored_docs), 1)

    context_snippets = _build_context_snippets(scored_docs, request.max_context_tokens)
    graph_context: List[Dict[str, Any]] = []
    if request.include_graph_context:
        query_tokens = _tokenize(request.query)
        nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(200)
        for node in nodes:
            text = f"{node.get('name', '')} {json.dumps(node.get('data', {}), default=str)}".lower()
            if any(token in text for token in query_tokens):
                graph_context.append(node)
            if len(graph_context) >= 10:
                break

    answer = ""
    generated_by = "synthetic"
    if openai_client and context_snippets:
        try:
            system_prompt = "You are a fraud defense assistant. Use only the provided context. If context is insufficient, say so. Keep responses synthetic-only and avoid real identifiers."
            prompt = "\n".join(context_snippets) + f"\n\nUser question: {request.query}"
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
            )
            answer = response.choices[0].message.content
            generated_by = "openai"
        except Exception as exc:
            logger.error(f"RAG generation error: {exc}")

    if not answer:
        if scored_docs:
            bullets = [f"- {doc.get('title') or doc.get('collection')}: {doc.get('content', '')[:160]}" for doc in scored_docs]
            answer = "Summary from retrieved knowledge:\n" + "\n".join(bullets)
        else:
            answer = "No relevant synthetic knowledge found for this query."

    hits = [
        RAGHit(
            doc_id=doc.get("id"),
            collection=doc.get("collection"),
            title=doc.get("title"),
            score=round(doc.get("score", 0), 4),
            snippet=doc.get("content", "")[:180],
            metadata=doc.get("metadata", {}),
        )
        for doc in scored_docs
    ]

    response = RAGResponse(
        query=request.query,
        answer=answer,
        hits=hits,
        context=context_snippets,
        graph_context=graph_context,
        retrieval_score=round(avg_score, 4),
        used_fallback=used_fallback,
        generated_by=generated_by,
    )

    if request.run_id:
        await record_run_event(
            request.run_id,
            "rag.query",
            {"team_id": request.team_id, "query": request.query, "score": response.retrieval_score},
        )

    return response

# ============== KNOWLEDGE GRAPH ROUTES ==============

@api_router.get("/knowledge-nodes", response_model=List[KnowledgeNode])
async def get_knowledge_nodes():
    nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(500)
    return nodes

@api_router.post("/knowledge-nodes", response_model=KnowledgeNode)
async def create_knowledge_node(node_data: KnowledgeNodeCreate):
    node = KnowledgeNode(**node_data.model_dump())
    await db.knowledge_nodes.insert_one(node.model_dump())
    return node

@api_router.put("/knowledge-nodes/{node_id}/connect/{target_id}")
async def connect_nodes(node_id: str, target_id: str):
    result = await db.knowledge_nodes.update_one(
        {"id": node_id},
        {"$addToSet": {"connections": target_id}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Nodes connected"}

@api_router.delete("/knowledge-nodes/{node_id}")
async def delete_knowledge_node(node_id: str):
    result = await db.knowledge_nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    # Remove connections to this node
    await db.knowledge_nodes.update_many({}, {"$pull": {"connections": node_id}})
    return {"message": "Node deleted"}

# ============== APPROVAL ROUTES ==============

@api_router.get("/approvals", response_model=List[ApprovalRequest])
async def get_approvals():
    approvals = await db.approvals.find({}, {"_id": 0}).to_list(100)
    return approvals

@api_router.post("/approvals", response_model=ApprovalRequest)
async def create_approval(approval_data: ApprovalCreate):
    approval = ApprovalRequest(**approval_data.model_dump())
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(approval.requestor_id, "approval.requested", "approval", approval.id, metadata=approval.metadata)
    return approval

@api_router.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: str, approver_id: str):
    approval = await db.approvals.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approver_entry = {"approver_id": approver_id, "timestamp": datetime.now(timezone.utc).isoformat(), "action": "approved"}
    await db.approvals.update_one(
        {"id": approval_id},
        {"$push": {"approvers": approver_entry}, "$set": {"status": "approved"}}
    )
    await record_audit(approver_id, "approval.decision", "approval", approval_id, decision="approved")
    return {"message": "Approved"}

@api_router.post("/approvals/{approval_id}/reject")
async def reject_request(approval_id: str, approver_id: str):
    approval = await db.approvals.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approver_entry = {"approver_id": approver_id, "timestamp": datetime.now(timezone.utc).isoformat(), "action": "rejected"}
    await db.approvals.update_one(
        {"id": approval_id},
        {"$push": {"approvers": approver_entry}, "$set": {"status": "rejected"}}
    )
    await record_audit(approver_id, "approval.decision", "approval", approval_id, decision="rejected")
    return {"message": "Rejected"}

# ============== GOVERNANCE ROUTES ==============

REQUIRED_APPROVAL_STAGES = ["orange_review_approve", "white_compliance_audit"]

@api_router.post("/runs/{run_id}/request-approval")
async def request_run_approval(run_id: str, stage: str, requestor_id: str):
    if stage not in REQUIRED_APPROVAL_STAGES:
        raise HTTPException(status_code=400, detail="Stage does not require approval")

    approval = ApprovalRequest(
        resource_type="run",
        resource_id=run_id,
        action=stage,
        requestor_id=requestor_id,
        metadata={"stage": stage},
    )
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(requestor_id, "approval.requested", "run", run_id, metadata={"stage": stage, "approval_id": approval.id})
    return approval

@api_router.get("/runs/{run_id}/safe-to-proceed")
async def safe_to_proceed(run_id: str):
    approvals = await db.approvals.find({"resource_id": run_id, "resource_type": "run"}, {"_id": 0}).to_list(50)
    approved_actions = {a.get("action") for a in approvals if a.get("status") == "approved"}
    missing = [stage for stage in REQUIRED_APPROVAL_STAGES if stage not in approved_actions]
    return {"run_id": run_id, "safe_to_proceed": len(missing) == 0, "missing": missing}

@api_router.get("/audit/logs", response_model=List[AuditLogEntry])
async def get_audit_logs():
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return logs

# ============== EVALUATION ROUTES ==============

@api_router.get("/runs/{run_id}/quality", response_model=QualityCheckResult)
async def get_run_quality(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    result = run_quality_checks(run, events)
    await db.quality_checks.insert_one(result.model_dump())
    return result

@api_router.get("/runs/{run_id}/evaluate", response_model=EvaluationReport)
async def evaluate_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    report = build_evaluation_report(run)
    await db.evaluations.insert_one(report.model_dump())
    await record_run_event(run_id, "evaluation.completed", {"report_id": report.report_id})
    return report

# ============== METRICS ROUTES ==============

@api_router.get("/metrics/dashboard")
async def get_dashboard_metrics():
    battles = await db.battles.find({}, {"_id": 0}).to_list(100)
    rules = await db.rules.find({}, {"_id": 0}).to_list(100)
    
    completed_battles = [b for b in battles if b.get("status") == "completed"]
    total_success = sum(b.get("metrics", {}).get("success_rate", 0) for b in completed_battles)
    avg_success = total_success / len(completed_battles) if completed_battles else 0
    
    return {
        "total_battles": len(battles),
        "completed_battles": len(completed_battles),
        "running_battles": len([b for b in battles if b.get("status") == "running"]),
        "avg_success_rate": round(avg_success, 2),
        "total_rules": len(rules),
        "active_rules": len([r for r in rules if r.get("status") == "active"]),
        "patterns_learned": sum(b.get("metrics", {}).get("patterns_learned", 0) for b in completed_battles),
        "avg_time_to_immunity": round(sum(b.get("metrics", {}).get("time_to_immunity", 0) for b in completed_battles) / max(len(completed_battles), 1), 2),
        "time_series": [
            {"timestamp": b.get("created_at"), "success_rate": b.get("metrics", {}).get("success_rate", 0), "time_to_immunity": b.get("metrics", {}).get("time_to_immunity", 0)}
            for b in completed_battles[-20:]
        ]
    }

# ============== AI THINKING ROUTES ==============

@api_router.post("/ai/think")
async def ai_think(prompt: Dict[str, str]):
    """Generate AI thinking for battle scenarios"""
    stage = prompt.get("stage", "analysis")
    context = prompt.get("context", "")
    team = prompt.get("team", "blue")
    
    system_prompts = {
        "red": "You are the Red Team AI, an offensive fraud attacker. Think step-by-step about how to evade detection.",
        "blue": "You are the Blue Team AI, a defensive fraud detector. Think step-by-step about how to detect and prevent fraud."
    }
    
    if not openai_client:
        return {
            "thinking": f"[Simulated {team} team thinking for {stage}]: Analyzing patterns... Evaluating risk vectors... Formulating response strategy.",
            "team": team,
            "stage": stage,
        }

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompts.get(team, system_prompts["blue"])},
                {"role": "user", "content": f"Stage: {stage}\nContext: {context}\n\nProvide your reasoning in 3-4 concise steps."}
            ],
            max_tokens=500
        )
        return {"thinking": response.choices[0].message.content, "team": team, "stage": stage}
    except Exception as e:
        logger.error(f"AI thinking error: {e}")
        return {"thinking": f"[Simulated {team} team thinking for {stage}]: Analyzing patterns... Evaluating risk vectors... Formulating response strategy.", "team": team, "stage": stage}

# ============== WEBSOCKET CONNECTION MANAGER ==============

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, battle_id: str):
        await websocket.accept()
        if battle_id not in self.active_connections:
            self.active_connections[battle_id] = []
        self.active_connections[battle_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, battle_id: str):
        if battle_id in self.active_connections:
            self.active_connections[battle_id].remove(websocket)
    
    async def broadcast(self, battle_id: str, message: dict):
        if battle_id in self.active_connections:
            for connection in self.active_connections[battle_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/battle/{battle_id}")
async def websocket_battle(websocket: WebSocket, battle_id: str):
    await manager.connect(websocket, battle_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "run_turn":
                # Simulate battle turn
                turn_data = await simulate_battle_turn(battle_id, message.get("turn_number", 1))
                await manager.broadcast(battle_id, turn_data)
            elif message.get("type") == "stream_thinking":
                # Stream AI thinking
                async for chunk in stream_ai_thinking(message.get("team", "blue"), message.get("context", "")):
                    await websocket.send_json({"type": "thinking_chunk", "chunk": chunk})
    except WebSocketDisconnect:
        manager.disconnect(websocket, battle_id)

async def simulate_battle_turn(battle_id: str, turn_number: int):
    """Simulate a battle turn between Red and Blue teams"""
    import random
    
    red_actions = ["Account Takeover Attempt", "Velocity Attack", "Device Spoofing", "Credential Stuffing", "Social Engineering"]
    blue_actions = ["Pattern Detection", "Velocity Check", "Device Fingerprinting", "ML Model Score", "Rule Engine Match"]
    
    red_action = random.choice(red_actions)
    blue_action = random.choice(blue_actions)
    red_success = random.random() < 0.4
    
    turn_data = {
        "type": "turn_update",
        "turn_number": turn_number,
        "red_team": {"action": red_action, "success": red_success, "timestamp": datetime.now(timezone.utc).isoformat()},
        "blue_team": {"action": blue_action, "blocked": not red_success, "timestamp": datetime.now(timezone.utc).isoformat()},
        "metrics": {
            "success_rate": random.randint(60, 95),
            "money_at_risk": random.randint(1000, 50000),
            "time_to_immunity": random.randint(1, 10),
            "patterns_learned": turn_number
        }
    }
    
    # Update battle in DB
    await db.battles.update_one(
        {"id": battle_id},
        {"$push": {"turns": turn_data}, "$set": {"metrics": turn_data["metrics"]}}
    )
    
    return turn_data

async def stream_ai_thinking(team: str, context: str):
    """Stream AI thinking chunks"""
    stages = ["Recon", "Ideation", "Evaluation", "Action"]
    
    for stage in stages:
        thinking = f"[{team.upper()} - {stage}] "
        if team == "red":
            thoughts = [
                "Analyzing target vulnerabilities...",
                "Identifying potential attack vectors...",
                "Evaluating evasion techniques...",
                "Executing strategic maneuver..."
            ]
        else:
            thoughts = [
                "Scanning for anomalies...",
                "Cross-referencing patterns...",
                "Calculating risk scores...",
                "Deploying countermeasures..."
            ]
        
        thinking += thoughts[stages.index(stage)]
        yield thinking
        await asyncio.sleep(0.5)

# ============== SEED DATA ==============

@api_router.post("/seed-data")
async def seed_data():
    """Seed initial demo data"""
    import random
    
    # Clear existing data
    await db.battles.delete_many({})
    await db.rules.delete_many({})
    await db.knowledge_nodes.delete_many({})
    await db.rsb_packages.delete_many({})
    await db.rag_documents.delete_many({})
    
    # Create sample rules
    rules_data = [
        {"name": "VEL-001", "description": "Velocity check for rapid transactions", "rule_type": "velocity", "conditions": [{"field": "tx_count", "operator": ">", "value": 5}], "actions": [{"type": "flag", "severity": "high"}], "priority": 1, "status": "active"},
        {"name": "STR-042", "description": "Suspicious transaction pattern", "rule_type": "pattern", "conditions": [{"field": "amount", "operator": ">", "value": 10000}], "actions": [{"type": "block", "severity": "critical"}], "priority": 2, "status": "active"},
        {"name": "DEV-015", "description": "Device fingerprint mismatch", "rule_type": "device", "conditions": [{"field": "device_id", "operator": "!=", "value": "known"}], "actions": [{"type": "challenge", "severity": "medium"}], "priority": 3, "status": "active"},
        {"name": "GEO-008", "description": "Geolocation anomaly detection", "rule_type": "geo", "conditions": [{"field": "distance", "operator": ">", "value": 500}], "actions": [{"type": "flag", "severity": "medium"}], "priority": 4, "status": "draft"},
    ]
    
    created_rules = []
    for rule_data in rules_data:
        rule = Rule(**rule_data)
        await db.rules.insert_one(rule.model_dump())
        created_rules.append(rule.id)
    
    # Create knowledge nodes
    nodes_data = [
        {"node_type": "root", "name": "Blue Sentinel Core", "data": {"description": "Central defense system"}},
        {"node_type": "rule", "name": "Rule: VEL-001", "data": {"rule_id": created_rules[0]}},
        {"node_type": "rule", "name": "Rule: STR-042", "data": {"rule_id": created_rules[1]}},
        {"node_type": "pattern", "name": "Pattern: ATO-99", "data": {"pattern_type": "account_takeover"}},
        {"node_type": "compliance", "name": "Compliance: PCI-DSS", "data": {"standard": "PCI-DSS 4.0"}},
    ]
    
    created_nodes = []
    for node_data in nodes_data:
        node = KnowledgeNode(**node_data)
        await db.knowledge_nodes.insert_one(node.model_dump())
        created_nodes.append(node.id)
    
    # Connect nodes to root
    root_id = created_nodes[0]
    for node_id in created_nodes[1:]:
        await db.knowledge_nodes.update_one({"id": root_id}, {"$addToSet": {"connections": node_id}})
    
    # Add evidence nodes
    for i in range(8):
        evidence_node = KnowledgeNode(node_type="evidence", name=f"Evidence", data={"evidence_id": f"EV-{i:03d}"})
        await db.knowledge_nodes.insert_one(evidence_node.model_dump())
        # Connect to random rule node
        parent_idx = random.randint(1, 4)
        if parent_idx < len(created_nodes):
            await db.knowledge_nodes.update_one({"id": created_nodes[parent_idx]}, {"$addToSet": {"connections": evidence_node.id}})

    # Seed minimal RAG documents
    rag_entries = [
        {"collection": "taxonomy", "title": "Account Takeover", "content": "ATO patterns include device change, new payee addition, and high-risk beneficiary transfers.", "metadata": {"category": "ATO"}},
        {"collection": "patterns", "title": "Velocity Fraud", "content": "Rapid transaction bursts over short windows often indicate automated fraud scripts.", "metadata": {"category": "velocity"}},
        {"collection": "rules", "title": "VEL-001", "content": "Flag accounts with more than 5 transfers within 10 minutes.", "metadata": {"team": "purple"}},
        {"collection": "explanations", "title": "Decision Rationale", "content": "Provide top three signals, rules triggered, and confidence statement.", "metadata": {"team": "gold"}},
    ]
    for entry in rag_entries:
        embedding = await _get_embedding(entry["content"])
        doc = RAGDocument(**entry, embedding=embedding)
        await db.rag_documents.insert_one(doc.model_dump())
    
    # Create sample battles
    for i in range(3):
        battle = Battle(
            scenario_name=f"Demo Battle {i+1}",
            status="completed" if i < 2 else "pending",
            parameters={"difficulty": "medium", "max_turns": 10},
            metrics={
                "success_rate": random.randint(70, 95),
                "money_at_risk": random.randint(5000, 50000),
                "time_to_immunity": max(1, 10 - i*3),
                "patterns_learned": (i+1) * 5
            }
        )
        if i < 2:
            battle.completed_at = datetime.now(timezone.utc).isoformat()
        await db.battles.insert_one(battle.model_dump())
    
    # Create sample RSB package
    rsb = RSBPackage(
        name="Fraud Detection Core v2.1",
        version="2.1.0",
        description="Core fraud detection rules and patterns",
        manifest={"rules": len(created_rules), "patterns": 5, "compliance": ["PCI-DSS", "SOX"]},
        rules=created_rules[:2],
        compliance_badges=["PCI-DSS", "SOX", "GDPR"]
    )
    await db.rsb_packages.insert_one(rsb.model_dump())
    
    return {"message": "Demo data seeded successfully", "rules": len(created_rules), "nodes": len(created_nodes), "battles": 3, "rag_docs": len(rag_entries)}

# ============== ROOT ROUTES ==============

@app.get("/")
async def app_root():
    return {"message": APP_NAME, "version": APP_VERSION}

@api_router.get("/")
async def root():
    return {"message": APP_NAME, "version": APP_VERSION}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router and middleware
app.include_router(api_router)

@app.on_event("startup")
async def startup_db_client():
    await init_database()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
