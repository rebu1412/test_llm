import os


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    return value


VLLM_TIMEOUT_S = float(get_env("VLLM_TIMEOUT_S", "120"))
QWEN_TIMEOUT_S = float(get_env("QWEN_TIMEOUT_S", "120"))
QWEN_API_KEY = get_env("QWEN_API_KEY")
QWEN_API_BASE = get_env(
    "QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
