# OG-Ollama-UI API Documentation

## Overview

The OG-Ollama-UI API provides a unified interface for interacting with multiple AI providers including Ollama, OpenAI, and Perplexity. It supports both streaming and non-streaming chat completions.

## Base URL

```
http://localhost:8000
```

## Authentication

- **Ollama**: No authentication required (local instance)
- **OpenAI**: Requires `OPENAI_API_KEY` environment variable
- **Perplexity**: Requires `PERPLEXITY_API_KEY` environment variable

## Endpoints

### Chat Completion

#### POST `/api/chat`

Create a non-streaming chat completion.

**Request Body:**

```json
{
  "message": "Hello, how are you?",
  "model": "llama3.2",
  "provider": "ollama",
  "stream": false,
  "history": [
    {
      "role": "user",
      "content": "Previous message",
      "timestamp": "2025-01-01T00:00:00Z"
    }
  ],
  "system_prompt": "You are a helpful assistant",
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Response:**

```json
{
  "message": "Hello! I'm doing well, thank you for asking.",
  "model": "llama3.2",
  "provider": "ollama",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  },
  "metadata": {
    "done": true,
    "total_duration": 1234567890
  }
}
```

#### POST `/api/chat/stream`

Create a streaming chat completion.

**Request Body:** Same as above with `"stream": true`

**Response:** Server-Sent Events (SSE) stream

```
data: {"content": "Hello", "done": false, "metadata": {...}}
data: {"content": "!", "done": false, "metadata": {...}}
data: {"content": "", "done": true, "metadata": {...}}
data: [DONE]
```

### Models

#### GET `/api/models?provider=ollama`

Get available models for a provider.

**Query Parameters:**

- `provider` (optional): `ollama`, `openai`, or `perplexity` (default: `ollama`)

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2",
      "provider": "ollama",
      "size": 4096000000,
      "modified_at": "2025-01-01T00:00:00Z",
      "description": "Ollama model: llama3.2"
    }
  ],
  "count": 1
}
```

### Health Check

#### GET `/api/health`

Check the health of all AI services.

**Response:**

```json
{
  "status": "healthy",
  "providers": {
    "ollama": true,
    "openai": false,
    "perplexity": true
  }
}
```

#### GET `/health`

Simple API health check.

**Response:**

```json
{
  "status": "healthy",
  "message": "API is operational"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:

- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error (service unavailable, API key issues, etc.)

## Data Models

### ChatMessage

```json
{
  "role": "user|assistant|system",
  "content": "string",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### ModelInfo

```json
{
  "name": "string",
  "provider": "string",
  "size": 123456789,
  "modified_at": "2025-01-01T00:00:00Z",
  "description": "string"
}
```

## Example Usage

### Python Example

```python
import aiohttp
import asyncio

async def chat_with_ollama():
    async with aiohttp.ClientSession() as session:
        payload = {
            "message": "What is the capital of France?",
            "model": "llama3.2",
            "provider": "ollama"
        }

        async with session.post(
            "http://localhost:8000/api/chat",
            json=payload
        ) as response:
            data = await response.json()
            print(data["message"])

asyncio.run(chat_with_ollama())
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello there!",
    "model": "llama3.2",
    "provider": "ollama"
  }'
```

### Streaming Example

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me a story",
    "model": "llama3.2",
    "provider": "ollama",
    "stream": true
  }'
```

## Development

### Running the API

1. Install dependencies:

   ```bash
   cd rebeldev-backend
   pip install -r requirements.txt
   ```

2. Set environment variables (optional):

   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export PERPLEXITY_API_KEY="your-perplexity-key"
   ```

3. Run the server:

   ```bash
   python -m app.main
   ```

4. Access API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
