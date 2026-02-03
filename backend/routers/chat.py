import asyncio

from fastapi import APIRouter

from backend.config import QWEN_TIMEOUT_S, VLLM_TIMEOUT_S
from backend.schemas import BotConfig, BotResult, CompareRequest, CompareResponse
from backend.services.qwen_client import call_qwen_api
from backend.services.vllm_client import call_vllm


router = APIRouter(prefix="/chat", tags=["chat"])


async def dispatch_bot(bot: BotConfig, question: str, side: str) -> BotResult:
    if bot.type == "vllm":
        result = await call_vllm(bot, question, VLLM_TIMEOUT_S)
        return result.model_copy(update={"side": side})
    if bot.type == "qwen_api":
        result = await call_qwen_api(bot, question, QWEN_TIMEOUT_S)
        return result.model_copy(update={"side": side})
    return BotResult(
        side=side,
        bot_name=bot.name,
        model=bot.model,
        answer="",
        latency_ms=0,
        provider=bot.type,
        error=f"Unsupported bot type: {bot.type}.",
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_chat(payload: CompareRequest) -> CompareResponse:
    left_task = dispatch_bot(payload.left_bot, payload.question, "left")
    right_task = dispatch_bot(payload.right_bot, payload.question, "right")

    left_result, right_result = await asyncio.gather(left_task, right_task)

    return CompareResponse(
        question=payload.question,
        results=[left_result, right_result],
    )
