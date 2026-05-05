from __future__ import annotations

from typing import Any

from utils import call_openai_json


class LLMClient:
    def json(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> dict[str, Any]:
        data = call_openai_json(system_prompt, user_prompt, temperature=temperature)
        return data if isinstance(data, dict) else {}
