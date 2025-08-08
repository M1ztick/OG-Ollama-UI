"""
Ollama service for handling requests to local Ollama instances
"""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime
from typing import List, AsyncGenerator, Optional

from ..models.schemas import ChatRequest, ChatResponse, StreamChunk, ModelInfo
from ..config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with the Ollama API"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.session = session or aiohttp.ClientSession()

    async def close(self):
        """Gracefully close aiohttp session"""
        if not self.session.closed:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if Ollama API is reachable"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def get_models(self) -> List[ModelInfo]:
        """Fetch list of models from Ollama"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")

                data = await response.json()
                models = []

                for model_data in data.get("models", []):
                    models.append(
                        ModelInfo(
                            name=model_data["name"],
                            provider="ollama",
                            size=model_data.get("size"),
                            modified_at=(
                                datetime.fromisoformat(
                                    model_data["modified_at"].replace("Z", "+00:00")
                                )
                                if model_data.get("modified_at")
                                else None
                            ),
                            description=f"Ollama model: {model_data['name']}",
                        )
                    )

                return models

        except Exception as e:
            logger.exception("Failed to fetch Ollama models")
            raise Exception(f"Failed to fetch Ollama models: {str(e)}") from e

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Perform a non-streaming chat completion using Ollama"""
        try:
            logger.info(f"[Ollama] Requesting non-streamed completion for model '{request.model}'")

            prompt = self.build_prompt(request)
            payload = {
                "model": request.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature or 0.7,
                },
            }

            if request.max_tokens:
                payload["options"]["num_predict"] = request.max_tokens

            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")

                data = await response.json()

                return ChatResponse(
                    message=data.get("response", ""),
                    model=request.model,
                    provider="ollama",
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    },
                    metadata={
                        "done": data.get("done", False),
                        "total_duration": data.get("total_duration"),
                        "load_duration": data.get("load_duration"),
                        "prompt_eval_duration": data.get("prompt_eval_duration"),
                        "eval_duration": data.get("eval_duration"),
                    },
                )

        except Exception as e:
            logger.exception("Ollama chat completion failed")
            raise Exception(f"Ollama chat completion failed: {str(e)}") from e

    async def chat_completion_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Perform a streaming chat completion using Ollama"""
        try:
            logger.info(f"[Ollama] Requesting streamed completion for model '{request.model}'")

            prompt = self.build_prompt(request)
            payload = {
                "model": request.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": request.temperature or 0.7,
                },
            }

            if request.max_tokens:
                payload["options"]["num_predict"] = request.max_tokens

            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")

                async for line in response.content:
                    try:
                        line = line.decode("utf-8").strip()
                        if not line:
                            continue
                        data = json.loads(line)

                        yield StreamChunk(
                            content=data.get("response", ""),
                            done=data.get("done", False),
                            metadata={
                                "model": request.model,
                                "eval_count": data.get("eval_count"),
                                "eval_duration": data.get("eval_duration"),
                            },
                        )

                        if data.get("done"):
                            break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode stream chunk: {line} — {e}")
                        continue

        except Exception as e:
            logger.exception("Ollama streaming chat completion failed")
            raise Exception(f"Ollama streaming failed: {str(e)}") from e

    def build_prompt(self, request: ChatRequest) -> str:
        """Constructs a prompt string based on chat history and the current message."""
        parts = []

        if request.system_prompt:
            parts.append(f"System: {request.system_prompt}")

        for msg in request.history:
            role_map = {
                "user": "Human",
                "assistant": "Assistant",
                "system": "System"
            }
            role_label = role_map.get(msg.role, msg.role.capitalize())
            parts.append(f"{role_label}: {msg.content}")

        parts.append(f"Human: {request.message}")
        parts.append("Assistant:")

        return "\n\n".join(parts)
