"""
Ollama service for handling requests to local Ollama instances
"""

import aiohttp
import asyncio
import json
from typing import List, AsyncGenerator, Optional
from datetime import datetime

from ..models.schemas import ChatRequest, ChatResponse, StreamChunk, ModelInfo
from ..config import settings


class OllamaService:
    """Service for interacting with Ollama API"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.timeout = settings.OLLAMA_TIMEOUT

    async def health_check(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    async def get_models(self) -> List[ModelInfo]:
        """Get list of available models from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")

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
            raise Exception(f"Failed to fetch Ollama models: {str(e)}")

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Non-streaming chat completion
        """
        try:
            # Build prompt from history and current message
            prompt = self._build_prompt(request)

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

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Ollama API error {response.status}: {error_text}"
                        )

                    data = await response.json()

                    return ChatResponse(
                        message=data.get("response", ""),
                        model=request.model,
                        provider="ollama",
                        usage={
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0)
                            + data.get("eval_count", 0),
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
            raise Exception(f"Ollama chat completion failed: {str(e)}")

    async def chat_completion_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Streaming chat completion
        """
        try:
            # Build prompt from history and current message
            prompt = self._build_prompt(request)

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

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Ollama API error {response.status}: {error_text}"
                        )

                    # Read streaming response
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode("utf-8"))

                                chunk = StreamChunk(
                                    content=data.get("response", ""),
                                    done=data.get("done", False),
                                    metadata={
                                        "model": request.model,
                                        "eval_count": data.get("eval_count"),
                                        "eval_duration": data.get("eval_duration"),
                                    },
                                )

                                yield chunk

                                if data.get("done"):
                                    break

                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            raise Exception(f"Ollama streaming failed: {str(e)}")

    def _build_prompt(self, request: ChatRequest) -> str:
        """
        Build a prompt from the chat history and current message
        """
        prompt_parts = []

        # Add system prompt if provided
        if request.system_prompt:
            prompt_parts.append(f"System: {request.system_prompt}")

        # Add conversation history
        for msg in request.history:
            if msg.role == "user":
                prompt_parts.append(f"Human: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
            elif msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")

        # Add current user message
        prompt_parts.append(f"Human: {request.message}")
        prompt_parts.append("Assistant:")

        return "\n\n".join(prompt_parts)
