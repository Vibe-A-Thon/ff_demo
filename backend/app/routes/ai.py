import logging
from fastapi import APIRouter
from app.rag_utils import openai_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ai/think")
async def ai_think(prompt: dict):
    stage = prompt.get("stage", "analysis")
    context = prompt.get("context", "")
    team = prompt.get("team", "blue")

    system_prompts = {
        "red": "You are the Red Team AI, an offensive fraud attacker. Think step-by-step about how to evade detection.",
        "blue": "You are the Blue Team AI, a defensive fraud detector. Think step-by-step about how to detect and prevent fraud.",
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
                {"role": "user", "content": f"Stage: {stage}\nContext: {context}\n\nProvide your reasoning in 3-4 concise steps."},
            ],
            max_tokens=500,
        )
        return {"thinking": response.choices[0].message.content, "team": team, "stage": stage}
    except Exception as exc:
        logger.error(f"AI thinking error: {exc}")
        return {
            "thinking": f"[Simulated {team} team thinking for {stage}]: Analyzing patterns... Evaluating risk vectors... Formulating response strategy.",
            "team": team,
            "stage": stage,
        }
