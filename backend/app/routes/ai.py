"""AI helper routes."""

import logging
from fastapi import APIRouter, Depends
from app.core.external_services import LLMClient
from app.deps import get_llm_client
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ai/think")
async def ai_think(
    prompt: dict,
    current_user: dict = Depends(require_permission("ai:write")),
    llm_client: LLMClient | None = Depends(get_llm_client),
):
    """Generate team thinking output.

    Args:
        prompt: Prompt payload with stage, context, and team.
        llm_client: Optional LLM client.

    Returns:
        dict: Thinking response.

    Raises:
        None: No explicit exceptions are raised.
    """
    stage = prompt.get("stage", "analysis")
    context = prompt.get("context", "")
    team = prompt.get("team", "blue")

    system_prompts = {
        "red": "You are the Red Team AI, an offensive fraud attacker. Think step-by-step about how to evade detection.",
        "blue": "You are the Blue Team AI, a defensive fraud detector. Think step-by-step about how to detect and prevent fraud.",
    }

    if not llm_client:
        logger.info(
            "ai.think.synthetic",
            extra={"payload": {"team": team, "stage": stage}},
        )
        await record_audit(
            current_user.get("id", "unknown"),
            "ai.think",
            "ai",
            team,
            metadata={"stage": stage, "mode": "synthetic"},
        )
        return {
            "thinking": f"[Simulated {team} team thinking for {stage}]: Analyzing patterns... Evaluating risk vectors... Formulating response strategy.",
            "team": team,
            "stage": stage,
        }

    try:
        thinking = await llm_client.chat_completions_create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompts.get(team, system_prompts["blue"])},
                {"role": "user", "content": f"Stage: {stage}\nContext: {context}\n\nProvide your reasoning in 3-4 concise steps."},
            ],
            max_tokens=500,
        )
        logger.info("ai.think.generated", extra={"payload": {"team": team, "stage": stage}})
        await record_audit(
            current_user.get("id", "unknown"),
            "ai.think",
            "ai",
            team,
            metadata={"stage": stage, "mode": "llm"},
        )
        return {"thinking": thinking, "team": team, "stage": stage}
    except Exception as exc:
        logger.error(f"AI thinking error: {exc}")
        logger.info(
            "ai.think.fallback",
            extra={"payload": {"team": team, "stage": stage}},
        )
        await record_audit(
            current_user.get("id", "unknown"),
            "ai.think",
            "ai",
            team,
            metadata={"stage": stage, "mode": "fallback", "reason": str(exc)},
        )
        return {
            "thinking": f"[Simulated {team} team thinking for {stage}]: Analyzing patterns... Evaluating risk vectors... Formulating response strategy.",
            "team": team,
            "stage": stage,
        }
