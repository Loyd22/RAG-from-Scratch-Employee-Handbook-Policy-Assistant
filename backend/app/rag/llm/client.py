"""
rag/llm/client.py
OpenAI chat client wrapper for generating structured JSON responses.
"""


from __future__ import annotations
import json 
from typing import Any, Dict
from openai import OpenAI


class LLMClient:
    """Thin wrapper around OpenAI Chat Completions for JSON-only responses."""
    
    def __init__(self, api_key: str, chat_model: str) -> None:
        """Initialize the client with API key and chat model name."""
        self._client = OpenAI(api_key = api_key)
        self._model = chat_model
    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any ]:
        """
        Generate a JSON object response from the chat model.

        Raises:
            ValueError: if the model output cannot be parsed as JSON.
        """

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        content = (resp.choices[0].message.content or "").strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model did not return valid JSON. Raw content: {content[:500]}") from exc