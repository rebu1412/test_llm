from typing import Any

import httpx

from backend.config import QWEN_API_BASE, QWEN_API_KEY
from backend.schemas import BotConfig, BotResult
from backend.services.timer import elapsed_ms, start_timer


async def call_qwen_api(bot: BotConfig, question: str, timeout_s: float) -> BotResult:
    if not QWEN_API_KEY:
        return BotResult(
            side="right",
            bot_name=bot.name,
            model=bot.model,
            answer="",
            latency_ms=0,
            provider="qwen_api",
            error="Missing QWEN_API_KEY environment variable.",
        )

    endpoint = bot.endpoint or f"{QWEN_API_BASE}/chat/completions"
    payload: dict[str, Any] = {
        "model": bot.model,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
    }

    headers = {"Authorization": f"Bearer {QWEN_API_KEY}"}

    start_time = start_timer()
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            model_name = data.get("model", bot.model)
            latency = elapsed_ms(start_time)
            return BotResult(
                side="right",
                bot_name=bot.name,
                model=model_name,
                answer=answer,
                latency_ms=latency,
                provider="qwen_api",
            )
    except Exception as exc:  # pragma: no cover - surface to client
        latency = elapsed_ms(start_time)
        return BotResult(
            side="right",
            bot_name=bot.name,
            model=bot.model,
            answer="",
            latency_ms=latency,
            provider="qwen_api",
            error=str(exc),
        )
