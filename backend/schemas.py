from typing import Literal, Optional

from pydantic import BaseModel, Field


class BotConfig(BaseModel):
    type: Literal["vllm", "qwen_api"]
    name: str
    model: str
    endpoint: Optional[str] = None


class CompareRequest(BaseModel):
    question: str = Field(..., min_length=1)
    left_bot: BotConfig
    right_bot: BotConfig


class BotResult(BaseModel):
    side: Literal["left", "right"]
    bot_name: str
    model: str
    answer: str
    latency_ms: float
    provider: Optional[str] = None
    error: Optional[str] = None


class CompareResponse(BaseModel):
    question: str
    results: list[BotResult]
