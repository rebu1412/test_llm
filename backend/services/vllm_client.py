from typing import Any

import httpx

from backend.schemas import BotConfig, BotResult
from backend.services.timer import elapsed_ms, start_timer


async def call_vllm(bot: BotConfig, question: str, timeout_s: float) -> BotResult:
    if not bot.endpoint:
        return BotResult(
            side="left",
            bot_name=bot.name,
            model=bot.model,
            answer="",
            latency_ms=0,
            provider="vllm",
            error="Missing vLLM endpoint.",
        )

    payload: dict[str, Any] = {
        "model": bot.model,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
    }

    start_time = start_timer()
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(bot.endpoint, json=payload)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            model_name = data.get("model", bot.model)
            latency = elapsed_ms(start_time)
            return BotResult(
                side="left",
                bot_name=bot.name,
                model=model_name,
                answer=answer,
                latency_ms=latency,
                provider="vllm",
            )
    except Exception as exc:  # pragma: no cover - surface to client
        latency = elapsed_ms(start_time)
        return BotResult(
            side="left",
            bot_name=bot.name,
            model=bot.model,
            answer="",
            latency_ms=latency,
            provider="vllm",
            error=str(exc),
        )
