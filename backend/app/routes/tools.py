"""Tool execution routes.

Provides listing and execution for synthetic tool registry.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from app.models import ToolCall, ToolResult
from app.tooling import TOOL_REGISTRY, TOOL_IMPLEMENTATIONS, derive_seed
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/tools")
async def list_tools(current_user: dict = Depends(require_permission("tools:read"))):
    """List available tools.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        list: Tool specifications.

    Raises:
        None: No explicit exceptions are raised.
    """
    await record_audit(
        current_user.get("id", "unknown"),
        "tools.list",
        "tool",
        "list",
    )
    return list(TOOL_REGISTRY.values())

@router.post("/tools/{tool_name}/run")
async def run_tool(tool_name: str, payload: ToolCall, current_user: dict = Depends(require_permission("tools:write"))):
    """Run a tool with parameters.

    Args:
        tool_name: Tool identifier.
        payload: Tool invocation payload.

    Returns:
        ToolResult: Execution result.

    Raises:
        HTTPException: If tool is missing or access is denied.
    """
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if payload.team_id and tool.allowed_teams and payload.team_id not in tool.allowed_teams:
        raise HTTPException(status_code=403, detail="Team not allowed to run this tool")

    base_seed = payload.seed if payload.seed is not None else int(datetime.now(timezone.utc).timestamp())
    derived_seed = derive_seed(base_seed, tool_name)
    impl = TOOL_IMPLEMENTATIONS.get(tool_name)
    if not impl:
        raise HTTPException(status_code=500, detail="Tool implementation missing")

    output = impl(payload.params, derived_seed)
    await record_audit(
        current_user.get("id", "unknown"),
        "tool.executed",
        "tool",
        tool_name,
        metadata={"team_id": payload.team_id, "seed": derived_seed},
    )
    logger.info(
        "tool.executed",
        extra={"payload": {"tool": tool_name, "team_id": payload.team_id, "seed": derived_seed}},
    )
    return ToolResult(tool_name=tool_name, status="ok", output=output, seed=derived_seed)
