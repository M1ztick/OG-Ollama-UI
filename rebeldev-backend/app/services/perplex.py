"""
Perplexity service for handling requests to Perplexity API
"""

import aiohttp
import json
import logging
from datetime import datetime
from typing import List, AsyncGenerator, Optional

from ..models.schemas import ChatRequest, ChatResponse, StreamChunk, ModelInfo
from ..config import settings

logger = logging.getLogger(__name__)


class PerplexityService:
    """Service for interacting with Perplexity API"""

    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Gracefully close aiohttp session"""
        await self.session.close()

    async def health_check(self) -> bool:
        """Check if Perplexity API is accessible"""
        if not self.api_key:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            test_payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }

            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                return response.status in [200, 400]

        except Exception:
            return False

    async def get_models(self) -> List[ModelInfo]:
        """Return static list of known Perplexity models"""
        return [
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

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Non-streaming chat completion"""
        if not self.api_key:
            raise Exception("Perplexity API key not configured")

        try:
            logger.info(f"Calling Perplexity model '{request.model}' (stream=False)")
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
                    raise Exception(f"Perplexity API error {response.status}: {error_text}")

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
        """Streaming chat completion"""
        if not self.api_key:
            raise Exception("Perplexity API key not configured")

        try:
            logger.info(f"Calling Perplexity model '{request.model}' (stream=True)")
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
                    raise Exception(f"Perplexity API error {response.status}: {error_text}")

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
                                    "citations": data.get("citations", []),
                                },
                            )

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            raise Exception(f"Perplexity streaming failed: {str(e)}")

    def build_messages(self, request: ChatRequest) -> List[dict]:
        """Build Perplexity-compatible chat messages"""
        messages = []

        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": request.message})
        return messages
