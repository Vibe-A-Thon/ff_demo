"""WebSocket routes for battle streaming."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from app.db import db
from app.rag_utils import openai_client
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import get_current_user
from app.core.rbac import has_permission

router = APIRouter()
logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, battle_id: str):
        """Accept and register a websocket connection.

        Args:
            websocket: Incoming WebSocket.
            battle_id: Battle identifier.

        Returns:
            None: This method returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        await websocket.accept()
        if battle_id not in self.active_connections:
            self.active_connections[battle_id] = []
        self.active_connections[battle_id].append(websocket)
        logger.info(
            "ws.connected",
            extra={"payload": {"battle_id": battle_id, "connections": len(self.active_connections[battle_id])}},
        )

    def disconnect(self, websocket: WebSocket, battle_id: str):
        """Remove a websocket connection.

        Args:
            websocket: WebSocket to remove.
            battle_id: Battle identifier.

        Returns:
            None: This method returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        if battle_id in self.active_connections:
            self.active_connections[battle_id].remove(websocket)
            logger.info(
                "ws.disconnected",
                extra={"payload": {"battle_id": battle_id, "connections": len(self.active_connections[battle_id])}},
            )

    async def broadcast(self, battle_id: str, message: dict):
        """Broadcast a message to all connections for a battle.

        Args:
            battle_id: Battle identifier.
            message: Payload to send.

        Returns:
            None: This method returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        if battle_id in self.active_connections:
            for connection in self.active_connections[battle_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    continue

manager = ConnectionManager()


async def _authorize_websocket(websocket: WebSocket) -> dict | None:
    auth_header = websocket.headers.get("authorization")
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return None
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    try:
        user = await get_current_user(credentials)
    except Exception:
        await websocket.close(code=4401)
        return None
    role = user.get("role", "")
    if not has_permission(role, "battle:read"):
        await websocket.close(code=4403)
        return None
    return user

@router.websocket("/ws/battle/{battle_id}")
async def websocket_battle(websocket: WebSocket, battle_id: str):
    """Handle websocket connections for battle updates.

    Args:
        websocket: Incoming WebSocket.
        battle_id: Battle identifier.

    Returns:
        None: This handler keeps the connection open until disconnect.

    Raises:
        WebSocketDisconnect: When the client disconnects.
    """
    user = await _authorize_websocket(websocket)
    if not user:
        return
    await manager.connect(websocket, battle_id)
    await record_audit(
        user.get("id", "unknown"),
        "battle.websocket.connected",
        "battle",
        battle_id,
        metadata={"mode": "websocket"},
    )
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "run_turn":
                turn_data = await simulate_battle_turn(
                    battle_id,
                    message.get("turn_number", 1),
                    actor_id=user.get("id", "unknown"),
                )
                await manager.broadcast(battle_id, turn_data)
            elif message.get("type") == "stream_thinking":
                async for chunk in stream_ai_thinking(message.get("team", "blue"), message.get("context", "")):
                    await websocket.send_json({"type": "thinking_chunk", "chunk": chunk})
    except WebSocketDisconnect:
        manager.disconnect(websocket, battle_id)

async def simulate_battle_turn(battle_id: str, turn_number: int, actor_id: str | None = None):
    """Simulate and persist a battle turn.

    Args:
        battle_id: Battle identifier.
        turn_number: Turn index.

    Returns:
        dict: Turn payload.

    Raises:
        None: No explicit exceptions are raised.
    """
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
            "patterns_learned": turn_number,
        },
    }

    await db.battles.update_one(
        {"id": battle_id},
        {"$push": {"turns": turn_data}, "$set": {"metrics": turn_data["metrics"]}},
    )
    await record_audit(
        actor_id or "unknown",
        "battle.turn.simulated",
        "battle",
        battle_id,
        metadata={"turn_number": turn_number, "mode": "websocket"},
    )
    logger.info(
        "ws.turn.simulated",
        extra={"payload": {"battle_id": battle_id, "turn_number": turn_number}},
    )

    return turn_data

async def stream_ai_thinking(team: str, context: str):
    """Stream synthetic thinking output for a team.

    Args:
        team: Team identifier.
        context: Context string.

    Returns:
        AsyncIterator[str]: Streamed thinking chunks.

    Raises:
        None: No explicit exceptions are raised.
    """
    stages = ["Recon", "Ideation", "Evaluation", "Action"]

    for stage in stages:
        thinking = f"[{team.upper()} - {stage}] "
        if team == "red":
            thoughts = [
                "Analyzing target vulnerabilities...",
                "Identifying potential attack vectors...",
                "Evaluating evasion techniques...",
                "Executing strategic maneuver...",
            ]
        else:
            thoughts = [
                "Scanning for anomalies...",
                "Cross-referencing patterns...",
                "Calculating risk scores...",
                "Deploying countermeasures...",
            ]

        thinking += thoughts[stages.index(stage)]
        yield thinking
        await asyncio.sleep(0.5)
