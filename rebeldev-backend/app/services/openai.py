"""
OpenAI service for handling requests to OpenAI API
"""

import aiohttp
import json
from typing import List, AsyncGenerator, Optional
from datetime import datetime

from ..models.schemas import ChatRequest, ChatResponse, StreamChunk, ModelInfo
from ..config import settings


class OpenAIService:
    """Service for interacting with OpenAI API"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        if not self.api_key:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
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
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        raise Exception(f"OpenAI API error: {response.status}")

                    data = await response.json()
                    models = []

                    # Filter to only chat completion models
                    chat_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o"]

                    for model_data in data.get("data", []):
                        model_id = model_data["id"]
                        if any(chat_model in model_id for chat_model in chat_models):
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
        """
        Non-streaming chat completion
        """
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        try:
            messages = self._build_messages(request)

            payload = {
                "model": request.model,
                "messages": messages,
                "stream": False,
                "temperature": request.temperature or 0.7,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"OpenAI API error {response.status}: {error_text}"
                        )

                    data = await response.json()
                    choice = data["choices"][0]

                    return ChatResponse(
                        message=choice["message"]["content"],
                        model=data["model"],
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
        """
        Streaming chat completion
        """
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        try:
            messages = self._build_messages(request)

            payload = {
                "model": request.model,
                "messages": messages,
                "stream": True,
                "temperature": request.temperature or 0.7,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"OpenAI API error {response.status}: {error_text}"
                        )

                    # Read streaming response
                    async for line in response.content:
                        line_str = line.decode("utf-8").strip()

                        if line_str.startswith("data: "):
                            data_str = line_str[6:]  # Remove "data: " prefix

                            if data_str == "[DONE]":
                                yield StreamChunk(content="", done=True)
                                break

                            try:
                                data = json.loads(data_str)
                                choice = data["choices"][0]
                                delta = choice.get("delta", {})

                                if "content" in delta:
                                    chunk = StreamChunk(
                                        content=delta["content"],
                                        done=False,
                                        metadata={
                                            "model": data.get("model"),
                                            "id": data.get("id"),
                                            "finish_reason": choice.get(
                                                "finish_reason"
                                            ),
                                        },
                                    )
                                    yield chunk

                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            raise Exception(f"OpenAI streaming failed: {str(e)}")

    def _build_messages(self, request: ChatRequest) -> List[dict]:
        """
        Build OpenAI messages format from chat request
        """
        messages = []

        # Add system message if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        # Add conversation history
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": request.message})

        return messages
