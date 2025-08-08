"""
OpenAI service for handling requests to OpenAI API
"""

import aiohttp
import json
import logging
from datetime import datetime
from typing import List, AsyncGenerator, Optional

from ..models.schemas import ChatRequest, ChatResponse, StreamChunk, ModelInfo
from ..config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Gracefully close aiohttp session"""
        await self.session.close()

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        if not self.api_key:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with self.session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def get_models(self) -> List[ModelInfo]:
        """Get list of available models from OpenAI"""
        if not self.api_key:
            return []

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with self.session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API error: {response.status}")

                data = await response.json()
                models = []

                chat_models = ["gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

                for model_data in data.get("data", []):
                    model_id = model_data["id"]
                    if any(name in model_id for name in chat_models):
                        models.append(
                            ModelInfo(
                                name=model_id,
                                provider="openai",
                                modified_at=datetime.fromtimestamp(
                                    model_data.get("created", 0)
                                ),
                                description=f"OpenAI model: {model_id}",
                            )
                        )
                return models

        except Exception as e:
            raise Exception(f"Failed to fetch OpenAI models: {str(e)}")

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Non-streaming chat completion"""
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        try:
            logger.info(f"Calling OpenAI model '{request.model}' (stream=False)")
            messages = self.build_messages(request)

            payload = {
                "model": request.model,
                "messages": messages,
                "stream": False,
                "temperature": request.temperature or 0.7,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")

                data = await response.json()
                choice = data.get("choices", [{}])[0]

                return ChatResponse(
                    message=choice.get("message", {}).get("content", ""),
                    model=data.get("model", request.model),
                    provider="openai",
                    usage=data.get("usage", {}),
                    metadata={
                        "finish_reason": choice.get("finish_reason"),
                        "id": data.get("id"),
                        "created": data.get("created"),
                    },
                )

        except Exception as e:
            raise Exception(f"OpenAI chat completion failed: {str(e)}")

    async def chat_completion_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """Streaming chat completion"""
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        try:
            logger.info(f"Calling OpenAI model '{request.model}' (stream=True)")
            messages = self.build_messages(request)

            payload = {
                "model": request.model,
                "messages": messages,
                "stream": True,
                "temperature": request.temperature or 0.7,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")

                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line.removeprefix("data: ").strip()

                    if data_str == "[DONE]":
                        yield StreamChunk(content="", done=True)
                        break

                    try:
                        data = json.loads(data_str)
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})

                        if "content" in delta:
                            yield StreamChunk(
                                content=delta["content"],
                                done=False,
                                metadata={
                                    "model": data.get("model"),
                                    "id": data.get("id"),
                                    "finish_reason": choice.get("finish_reason"),
                                },
                            )

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            raise Exception(f"OpenAI streaming failed: {str(e)}")

    def build_messages(self, request: ChatRequest) -> List[dict]:
        """Build OpenAI messages format from chat request"""
        messages = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": request.message})
        return messages
