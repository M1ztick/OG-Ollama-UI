"""
Main FastAPI application for OG-Ollama-UI backend
Provides API endpoints for chat functionality with multiple AI providers
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from .routers import chat
from .config import settings
from .services.ollama import OllamaService
from .services.openai import OpenAIService
from .services.perplex import PerplexityService

# Initialize logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OG-Ollama-UI API",
    description="Backend API for OG-Ollama-UI chat application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

# Service instances (shared)
ollama_service = OllamaService()
openai_service = OpenAIService()
perplexity_service = PerplexityService()


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully close services"""
    logger.info("Shutting down... closing HTTP sessions.")
    await ollama_service.close()
    await openai_service.close()
    await perplexity_service.close()


@app.get("/")
async def root():
    """Root endpoint - API status check"""
    return {
        "message": "OG-Ollama-UI API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is operational"}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(status_code=404, content={"detail": "Endpoint not found"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
