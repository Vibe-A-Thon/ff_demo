from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

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
    metrics: Dict[str, Any] = {
        "success_rate": 0,
        "money_at_risk": 0,
        "time_to_immunity": 0,
        "patterns_learned": 0,
    }
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
    rule_id: Optional[str] = None
    rule_spec: Optional[Dict[str, Any]] = None
    rule_definition: Optional[Dict[str, Any]] = None
    description_md: Optional[str] = None
    code: Optional[str] = None
    code_patch: Optional[str] = None
    patch_script: Optional[str] = None
    files: List[Dict[str, Any]] = []
    test_files: List[str] = []
    testcases: List[str] = []
    compliance_badges: List[str] = []
    compliance_docs: List[Dict[str, Any]] = []
    test_results: Optional[Dict[str, Any]] = None
    validation: Dict[str, Any] = {}
    conflicts: List[Dict[str, Any]] = []
    conflict_resolutions: Dict[str, Any] = {}
    checksum: Optional[str] = None
    source_filename: Optional[str] = None
    storage_path: Optional[str] = None
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RSBPackageCreate(BaseModel):
    name: str
    version: str
    description: str
    manifest: Dict[str, Any]
    rules: List[str] = []
    compliance_badges: List[str] = []
    rule_id: Optional[str] = None
    rule_spec: Optional[Dict[str, Any]] = None
    rule_definition: Optional[Dict[str, Any]] = None
    description_md: Optional[str] = None
    code: Optional[str] = None
    files: List[Dict[str, Any]] = []

class EvidencePack(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    battle_id: Optional[str] = None
    run_id: Optional[str] = None
    narrative: str
    triggered_rules: List[str]
    contributing_factors: List[Dict[str, Any]]
    confidence: float
    logs: List[Dict[str, Any]]
    approvals: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, Any]] = []
    workflow_history: List[Dict[str, Any]] = []
    workflow_state: Optional[str] = None
    metrics: Dict[str, Any] = {}
    xai_bundle: Optional[Dict[str, Any]] = None
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
    node_type: str
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
    workflow_state: str = "incident_created"
    workflow_status: str = "running"
    workflow_history: List[Dict[str, Any]] = []
    pending_approval: Optional[Dict[str, Any]] = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: Optional[str] = None

class RunEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    event_type: str
    payload: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WorkflowAdvanceRequest(BaseModel):
    actor_id: str
    mode: str = "manual"
    outcome: Optional[str] = None
    notes: Optional[str] = None

class WorkflowDecisionRequest(BaseModel):
    actor_id: str
    actor_role: Optional[str] = None
    decision: str = "approved"
    notes: Optional[str] = None

class WorkflowAutoRunRequest(BaseModel):
    actor_id: str
    max_steps: int = 25
    outcome: Optional[str] = None
    notes: Optional[str] = None

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
    evidence_graph: Optional[Dict[str, Any]] = None
    counterfactuals: List[Dict[str, Any]] = []
    similar_cases: List[Dict[str, Any]] = []

class EvidenceGraphNode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    node_id: str
    node_type: str
    label: str
    metadata: Dict[str, Any] = {}

class EvidenceGraphEdge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source: str
    target: str
    relation: str
    metadata: Dict[str, Any] = {}

class EvidenceGraph(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nodes: List[EvidenceGraphNode] = []
    edges: List[EvidenceGraphEdge] = []

class Counterfactual(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str
    changes: Dict[str, Any]
    expected_outcome: str

class SimilarCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    case_id: str
    summary: str
    similarity: float
    metadata: Dict[str, Any] = {}

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
    allowed_roles: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    synthetic_only: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RAGDocumentCreate(BaseModel):
    collection: str
    title: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}
    allowed_roles: Optional[List[str]] = None
    synthetic_only: bool = True

class RAGMediaDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    collection: str
    title: Optional[str] = None
    media_type: str
    metadata: Dict[str, Any] = {}
    allowed_roles: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    synthetic_only: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RAGMediaDocumentCreate(BaseModel):
    collection: str
    title: Optional[str] = None
    media_type: str
    metadata: Dict[str, Any] = {}
    allowed_roles: Optional[List[str]] = None
    synthetic_only: bool = True

class RAGQueryRequest(BaseModel):
    query: str
    collections: Optional[List[str]] = None
    top_k: int = 5
    use_hybrid: bool = True
    include_graph_context: bool = True
    rag_mode: str = "hybrid"
    enable_crag: bool = False
    graph_hops: int = 1
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
    rag_mode_used: str = "hybrid"
    corrections: List[str] = []
    verification_score: float = 0.0
    verification_passed: bool = False
    agentic_trace: List[Dict[str, Any]] = []

class RAGEvaluationCase(BaseModel):
    query: str
    expected_collections: Optional[List[str]] = None
    expected_doc_ids: Optional[List[str]] = None
    expected_keywords: Optional[List[str]] = None
    synthetic_only: bool = True
    reference_answer: Optional[str] = None

class RAGEvaluationRequest(BaseModel):
    cases: List[RAGEvaluationCase]
    top_k: int = 5
    use_hybrid: bool = True
    rag_mode: str = "hybrid"
    include_graph_context: bool = False
    retrieval_threshold: float = 0.55
    graph_hops: int = 1

class RAGEvaluationReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    summary: str
    metrics: Dict[str, Any] = {}
    per_case: List[Dict[str, Any]] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
