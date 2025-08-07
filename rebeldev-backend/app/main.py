"""
Main FastAPI application for OG-Ollama-UI backend
Provides API endpoints for chat functionality with multiple AI providers
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routers import chat
from .config import settings

# Create FastAPI application
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
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])


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


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Endpoint not found"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
