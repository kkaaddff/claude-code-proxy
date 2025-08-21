# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Installation and Setup

```bash
conda activate mcp-atlassian
# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Start the server
source .env
python start_proxy.py

# Run with help flag to see configuration options
python src/main.py --help
```

### Development and Testing

```bash
# Run tests
python tests/test_main.py

# Or using pytest
pytest tests/test_main.py -v

# Run specific test functions
pytest tests/test_main.py::test_basic_chat -v

# Run with coverage
pytest tests/test_main.py --cov=src --cov-report=html
```

## Architecture Overview

### Core Purpose

This is a FastAPI-based proxy server that converts Claude API requests to OpenAI API format, enabling Claude Code CLI to work with OpenAI-compatible providers (OpenAI, Azure OpenAI, Ollama, etc.).

### Key Components

#### Entry Points

- `src/main.py` - Main FastAPI application and server entry point
- `start_proxy.py` - Simple startup script for development
- `requirements.txt` - All project dependencies

#### API Layer

- `src/api/endpoints.py` - All API endpoints (`/v1/messages`, `/health`, `/test-connection`)
- Handles request validation, streaming responses, and client authentication
- Key endpoint: `/v1/messages` for main chat completion functionality

#### Core Infrastructure

- `src/core/config.py` - Configuration management with environment variable handling
- `src/core/client.py` - Async OpenAI client with Azure support and cancellation
- `src/core/model_manager.py` - Model mapping logic (Claude → OpenAI models)
- `src/core/constants.py` - Constants for API roles, content types, tool formats

#### Conversion Layer

- `src/conversion/request_converter.py` - Converts Claude requests to OpenAI format
- `src/conversion/response_converter.py` - Converts OpenAI responses back to Claude format
- Handles multimodal content, tool calling, and streaming responses

#### Models

- `src/models/claude.py` - Claude API request/response models
- `src/models/openai.py` - OpenAI API request/response models (if used)

### Architecture Patterns

#### Model Mapping Strategy

The proxy intelligently maps Claude model requests to configured OpenAI models:

- `claude-3-haiku*` → `SMALL_MODEL` (default: `gpt-4o-mini`)
- `claude-3-sonnet*` → `MIDDLE_MODEL` (default: `BIG_MODEL`)
- `claude-3-opus*` → `BIG_MODEL` (default: `gpt-4o`)
- Direct OpenAI/GPT models are passed through unchanged
- Supports other providers (ARK, Doubao, DeepSeek) as-is

#### Request Flow

1. Client makes Claude API request to `/v1/messages`
2. `validate_api_key()` checks client authentication (if configured)
3. `request_converter.py` converts Claude request to OpenAI format
4. `model_manager.py` maps Claude model to appropriate OpenAI model
5. `OpenAIClient` forwards request to target provider
6. `response_converter.py` converts OpenAI response back to Claude format
7. Response returned to client

#### Streaming Support

- Full Server-Sent Events (SSE) streaming support
- Real-time cancellation handling via request IDs
- Proper error handling in streaming mode
- Maintains open connection until completion or cancellation

#### Error Handling

- Comprehensive error classification in `OpenAIClient.classify_openai_error()`
- Specific error messages for common issues (rate limits, auth failures, etc.)
- Graceful degradation and proper HTTP status codes
- Detailed logging throughout the pipeline

### Configuration System

#### Environment Variables

- `OPENAI_API_KEY` (required) - Target provider API key
- `OPENAI_BASE_URL` (optional) - API base URL (default: OpenAI)
- `ANTHROPIC_API_KEY` (optional) - Expected client key for authentication
- `BIG_MODEL`, `MIDDLE_MODEL`, `SMALL_MODEL` - Model mappings
- `HOST`, `PORT` - Server configuration
- `MAX_TOKENS_LIMIT`, `REQUEST_TIMEOUT` - Performance settings

#### Model Configuration

Models are configured with intelligent defaults and fallbacks:

- `MIDDLE_MODEL` defaults to `BIG_MODEL` value for consistency
- Token limits are enforced (max: 4096, min: 100)
- Timeout and retry logic for reliability

### Testing Approach

#### Test Coverage

The test suite (`tests/test_main.py`) covers:

- Basic chat completion
- Streaming responses
- Function/tool calling
- System messages
- Multimodal inputs (text + images)
- Conversation flows with tool use
- Token counting
- Health checks and connection testing

#### Test Execution

Tests are designed to run against a live server and require:

- Valid `OPENAI_API_KEY` in environment
- Server running on `localhost:8082`
- Use `asyncio.run()` for test execution

### Development Notes

#### Code Structure

- Async/await pattern throughout for performance
- FastAPI dependency injection for authentication
- Pydantic models for request/response validation
- Modular design with clear separation of concerns

#### Multimodal Support

- Base64 image encoding support
- Text and image content types properly converted
- Maintains Claude's multimodal format

#### Tool Calling

- Full OpenAI tools compatibility
- Claude tool_use blocks converted to tool_calls
- Tool results properly handled and converted back
- Supports complex conversation flows

#### Performance Considerations

- Connection pooling for API calls
- Request cancellation support
- Efficient streaming with proper cleanup
- Configurable timeouts and retry logic
