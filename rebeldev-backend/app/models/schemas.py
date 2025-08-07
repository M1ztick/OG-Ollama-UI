"""
Pydantic models for request/response validation
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Individual chat message"""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now, description="Message timestamp"
    )


class ChatRequest(BaseModel):
    """Request for chat completion"""

    message: str = Field(..., description="User message")
    model: str = Field(default="llama3.2", description="AI model to use")
    provider: Literal["ollama", "openai", "perplexity"] = Field(
        default="ollama", description="AI provider"
    )
    stream: bool = Field(default=True, description="Enable streaming response")
    history: List[ChatMessage] = Field(default=[], description="Conversation history")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    temperature: Optional[float] = Field(
        0.7, description="Response creativity (0.0-2.0)"
    )


class ChatResponse(BaseModel):
    """Response from chat completion"""

    message: str = Field(..., description="AI response message")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider used")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional response metadata"
    )


class StreamChunk(BaseModel):
    """Individual chunk in streaming response"""

    content: str = Field(..., description="Chunk content")
    done: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


class ModelInfo(BaseModel):
    """Information about an available model"""

    name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Provider offering the model")
    size: Optional[int] = Field(None, description="Model size in bytes")
    modified_at: Optional[datetime] = Field(None, description="Last modification time")
    description: Optional[str] = Field(None, description="Model description")


class ModelsResponse(BaseModel):
    """Response containing available models"""

    models: List[ModelInfo] = Field(..., description="List of available models")
    count: int = Field(..., description="Number of models")


class ErrorResponse(BaseModel):
    """Error response format"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    providers: Optional[Dict[str, bool]] = Field(
        None, description="Provider availability"
    )
