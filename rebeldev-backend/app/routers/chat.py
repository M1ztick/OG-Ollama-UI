"""
Chat API router - Handles chat completion requests.
Supports multiple AI providers: Ollama, OpenAI, Perplexity.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.schemas import ChatRequest, ChatResponse, ModelsResponse
from ..services.ollama import OllamaService
from ..services.openai import OpenAIService
from ..services.perplex import PerplexityService
import json

router = APIRouter()

# Service instances
SERVICE_REGISTRY = {
    "ollama": OllamaService(),
    "openai": OpenAIService(),
    "perplexity": PerplexityService(),
}

def get_service(provider: str):
    """Get the appropriate service based on provider."""
    if provider not in SERVICE_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    return SERVICE_REGISTRY[provider]


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """Create a chat completion (non-streaming)."""
    try:
        service = get_service(request.provider)
        return await service.chat_completion(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/chat/stream")
async def chat_completion_stream(request: ChatRequest):
    """Create a streaming chat completion."""
    try:
        service = get_service(request.provider)

        async def stream():
            async for chunk in service.chat_completion_stream(request):
                yield f"data: {json.dumps(chunk.dict())}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/models", response_model=ModelsResponse)
async def get_available_models(provider: str = "ollama"):
    """Get list of available models for a provider."""
    try:
        service = get_service(provider)
        models = await service.get_models()
        return ModelsResponse(models=models, count=len(models))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def health_check():
    """Check health of all AI services."""
    status = {}
    for name, service in SERVICE_REGISTRY.items():
        try:
            await service.health_check()
            status[name] = True
        except Exception:
            status[name] = False

    return {
        "status": "healthy" if any(status.values()) else "unhealthy",
        "providers": status,
    }
