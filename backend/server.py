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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# JWT and Auth
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'default_secret')
JWT_ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Fraud Forge API")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ApprovalCreate(BaseModel):
    resource_type: str
    resource_id: str
    action: str
    requestor_id: str

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
    
    await db.rules.update_one({"id": rule_id}, {"$set": {"test_results": test_results}})
    return test_results

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
async def export_evidence_pack(pack_id: str):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    
    return {
        "filename": f"evidence_pack_{pack_id}.json",
        "content_type": "application/json",
        "data": pack,
        "checksum": pack.get("checksum", ""),
        "exported_at": datetime.now(timezone.utc).isoformat()
    }

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
    return {"message": "Rejected"}

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
    
    return {"message": "Demo data seeded successfully", "rules": len(created_rules), "nodes": len(created_nodes), "battles": 3}

# ============== ROOT ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "Fraud Forge API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router and middleware
app.include_router(api_router)

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
