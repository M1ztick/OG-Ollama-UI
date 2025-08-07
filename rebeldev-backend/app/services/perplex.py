"""
Perplexity service for handling requests to Perplexity API
"""

import aiohttp
import json
from typing import List, AsyncGenerator, Optional
from datetime import datetime

from ..models.schemas import ChatRequest, ChatResponse, StreamChunk, ModelInfo
from ..config import settings


class PerplexityService:
    """Service for interacting with Perplexity API"""

    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"

    async def health_check(self) -> bool:
        """Check if Perplexity API is accessible"""
        if not self.api_key:
            return False

        try:
            # Simple test request to check API accessibility
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                test_payload = {
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                }
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status in [
                        200,
                        400,
                    ]  # 400 is also OK, means API is accessible
        except Exception:
            return False

    async def get_models(self) -> List[ModelInfo]:
        """Get list of available models from Perplexity"""
        # Perplexity doesn't have a models endpoint, so we return known models
        models = [
            ModelInfo(
                name="llama-3.1-sonar-small-128k-online",
                provider="perplexity",
                description="Llama 3.1 Sonar Small 128K Online - Fast model with web access",
            ),
            ModelInfo(
                name="llama-3.1-sonar-large-128k-online",
                provider="perplexity",
                description="Llama 3.1 Sonar Large 128K Online - Powerful model with web access",
            ),
            ModelInfo(
                name="llama-3.1-sonar-huge-128k-online",
                provider="perplexity",
                description="Llama 3.1 Sonar Huge 128K Online - Most capable model with web access",
            ),
            ModelInfo(
                name="llama-3.1-8b-instruct",
                provider="perplexity",
                description="Llama 3.1 8B Instruct - Fast offline model",
            ),
            ModelInfo(
                name="llama-3.1-70b-instruct",
                provider="perplexity",
                description="Llama 3.1 70B Instruct - Powerful offline model",
            ),
        ]

        return models

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Non-streaming chat completion
        """
        if not self.api_key:
            raise Exception("Perplexity API key not configured")

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
                            f"Perplexity API error {response.status}: {error_text}"
                        )

                    data = await response.json()
                    choice = data["choices"][0]

                    return ChatResponse(
                        message=choice["message"]["content"],
                        model=data["model"],
                        provider="perplexity",
                        usage=data.get("usage", {}),
                        metadata={
                            "finish_reason": choice.get("finish_reason"),
                            "id": data.get("id"),
                            "created": data.get("created"),
                            "citations": data.get("citations", []),
                        },
                    )

        except Exception as e:
            raise Exception(f"Perplexity chat completion failed: {str(e)}")

    async def chat_completion_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Streaming chat completion
        """
        if not self.api_key:
            raise Exception("Perplexity API key not configured")

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
                            f"Perplexity API error {response.status}: {error_text}"
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
                                            "citations": data.get("citations", []),
                                        },
                                    )
                                    yield chunk

                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            raise Exception(f"Perplexity streaming failed: {str(e)}")

    def _build_messages(self, request: ChatRequest) -> List[dict]:
        """
        Build Perplexity messages format from chat request
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
