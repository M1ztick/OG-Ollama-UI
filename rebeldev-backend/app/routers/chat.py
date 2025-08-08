"""
Chat API router - Handles chat completion requests.
Supports multiple AI providers: Ollama, OpenAI, Perplexity.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    ModelsResponse,
    ErrorResponse,
)
from ..services.ollama import OllamaService
from ..services.openai import OpenAIService
from ..services.perplex import PerplexityService
import json
from typing import AsyncGenerator

router = APIRouter()

# Service instances
SERVICE_REGISTRY = {
    "ollama": OllamaService(),
    "openai": OpenAIService(),
    "perplexity": PerplexityService(),
}


def get_service(provider: str):
    """Retrieve the appropriate service for a given provider."""
    service = SERVICE_REGISTRY.get(provider)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )
    return service


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Create chat completion"
)
async def chat_completion(request: ChatRequest) -> ChatResponse:
    """Create a chat completion from the specified provider."""
    try:
        service = get_service(request.provider)
        return await service.chat_completion(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.post(
    "/chat/stream",
    responses={500: {"model": ErrorResponse}},
    summary="Create streaming chat completion"
)
async def chat_completion_stream(request: ChatRequest) -> StreamingResponse:
    """Create a streaming chat completion using Server-Sent Events (SSE)."""
    try:
        service = get_service(request.provider)

        async def stream() -> AsyncGenerator[str, None]:
            try:
                async for chunk in service.chat_completion_stream(request):
                    yield f"data: {json.dumps(chunk.dict())}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get(
    "/models",
    response_model=ModelsResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Get available models"
)
async def get_available_models(provider: str = "ollama") -> ModelsResponse:
    """Retrieve the list of available models from a specific provider."""
    try:
        service = get_service(provider)
        models = await service.get_models()
        return ModelsResponse(models=models, count=len(models))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.get(
    "/health",
    summary="Check health of AI services",
    responses={200: {"description": "Health status of all providers"}}
)
async def health_check() -> dict:
    """Perform a health check for all registered AI providers."""
    status_map = {}
    for name, service in SERVICE_REGISTRY.items():
        try:
            await service.health_check()
            status_map[name] = True
        except Exception:
            status_map[name] = False

    overall_status = "healthy" if any(status_map.values()) else "unhealthy"
    return {
        "status": overall_status,
        "providers": status_map,
    }
