"""
Chat API router - Handles chat completion requests
Supports multiple AI providers: Ollama, OpenAI, Perplexity
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from ..models.schemas import (
    ChatRequest,
    ChatResponse,
    ModelsResponse,
)
from ..services.ollama import OllamaService
from ..services.openai import OpenAIService
from ..services.perplex import PerplexityService

router = APIRouter()

# Service instances
ollama_service = OllamaService()
openai_service = OpenAIService()
perplexity_service = PerplexityService()


def get_service(provider: str):
    """Get the appropriate service based on provider"""
    services = {
        "ollama": ollama_service,
        "openai": openai_service,
        "perplexity": perplexity_service,
    }

    if provider not in services:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    return services[provider]


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Create a chat completion (non-streaming)
    """
    try:
        service = get_service(request.provider)
        response = await service.chat_completion(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/chat/stream")
async def chat_completion_stream(request: ChatRequest):
    """
    Create a streaming chat completion
    """
    try:
        service = get_service(request.provider)

        async def generate_stream():
            async for chunk in service.chat_completion_stream(request):
                yield f"data: {json.dumps(chunk.dict())}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/models", response_model=ModelsResponse)
async def get_available_models(provider: str = "ollama"):
    """
    Get list of available models for a provider
    """
    try:
        service = get_service(provider)
        models = await service.get_models()
        return ModelsResponse(models=models, count=len(models))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def health_check():
    """
    Check health of all AI services
    """
    try:
        providers = {}

        # Check Ollama
        try:
            await ollama_service.health_check()
            providers["ollama"] = True
        except Exception:
            providers["ollama"] = False

        # Check OpenAI
        try:
            await openai_service.health_check()
            providers["openai"] = True
        except Exception:
            providers["openai"] = False

        # Check Perplexity
        try:
            await perplexity_service.health_check()
            providers["perplexity"] = True
        except Exception:
            providers["perplexity"] = False

        return {
            "status": "healthy" if any(providers.values()) else "unhealthy",
            "providers": providers,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
