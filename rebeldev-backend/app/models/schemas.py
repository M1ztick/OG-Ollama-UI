"""
Pydantic models for request/response validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ProviderEnum(str, Enum):
    ollama = "ollama"
    openai = "openai"
    perplexity = "perplexity"


class ChatMessage(BaseModel):
    """Individual chat message"""

    role: Role = Field(..., description="Message role", example="user")
    content: str = Field(..., description="Message content", example="Hello!")
    timestamp: Optional[datetime] = Field(
        default_factory=utc_now,
        description="Message timestamp in UTC",
        example="2025-08-08T14:30:00Z"
    )


class ChatRequest(BaseModel):
    """Request for chat completion"""

    message: str = Field(..., description="User message", example="What's the weather?")
    model: str = Field(default="llama3.2", description="AI model to use", example="llama3.2")
    provider: ProviderEnum = Field(
        default=ProviderEnum.ollama,
        description="AI provider to use"
    )
    stream: bool = Field(default=True, description="Enable streaming response")
    history: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens in the response")
    temperature: Optional[float] = Field(
        0.7,
        description="Controls randomness in response generation (0.0 to 2.0)"
    )


class ChatResponse(BaseModel):
    """Response from chat completion"""

    message: str = Field(..., description="AI response message")
    model: str = Field(..., description="Model used for generation")
    provider: ProviderEnum = Field(..., description="Provider used")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")


class StreamChunk(BaseModel):
    """Individual chunk in streaming response"""

    content: str = Field(..., description="Chunk content")
    done: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


class ModelInfo(BaseModel):
    """Information about an available model"""

    name: str = Field(..., description="Model name", example="llama3.2")
    provider: ProviderEnum = Field(..., description="Provider offering the model")
    size: Optional[int] = Field(None, description="Model size in bytes")
    modified_at: Optional[datetime] = Field(None, description="Last modification time")
    description: Optional[str] = Field(None, description="Model description")

    class Config:
        orm_mode = True


class ModelsResponse(BaseModel):
    """Response containing available models"""

    models: List[ModelInfo] = Field(..., description="List of available models")
    count: int = Field(..., description="Number of models")


class ErrorResponse(BaseModel):
    """Error response format"""

    error: str = Field(..., description="Error type", example="ValidationError")
    message: str = Field(..., description="Error message", example="Invalid request payload")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status", example="ok")
    message: str = Field(..., description="Status message", example="Service is running")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    providers: Optional[Dict[str, bool]] = Field(
        None, description="Provider availability"
    )
