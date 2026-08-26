"""V4 统一模型客户端 — 所有实验脚本共用此模块调用本地端点."""

import time
from pathlib import Path

import yaml


def load_config():
    config_path = Path(__file__).with_suffix(".yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ModelClient:
    def __init__(self, config=None):
        self.config = config or load_config()
        self.endpoint = self.config["endpoint"]
        self.model_name = self.config.get("model_name")
        self.temperature = self.config.get("temperature", 0)
        self.max_tokens = self.config.get("max_tokens", 4096)
        self.timeout = self.config.get("timeout_seconds", 120)
        self.retries = self.config.get("retry_attempts", 3)

    def chat(self, messages, **kwargs):
        import openai

        client = openai.OpenAI(
            base_url=self.endpoint,
            api_key="dummy",
        )
        for attempt in range(self.retries):
            try:
                response = client.chat.completions.create(
                    model=self.model_name or "default",
                    messages=messages,
                    temperature=kwargs.get("temperature", self.temperature),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    timeout=self.timeout,
                )
                return {
                    "content": response.choices[0].message.content,
                    "usage": response.usage.model_dump() if response.usage else {},
                    "finish_reason": response.choices[0].finish_reason,
                }
            except Exception:
                if attempt == self.retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return None

    def get_env_info(self):
        return {
            "endpoint": self.endpoint,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "config_source": str(Path(__file__).with_suffix(".yaml")),
        }


def chat(messages, **kwargs):
    """便捷函数：直接使用默认配置调用."""
    client = ModelClient()
    return client.chat(messages, **kwargs)
