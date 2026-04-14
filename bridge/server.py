"""
FastAPI Bridge Server

Receives HTTP requests from the Discord receiver and forwards them
to the core daemon for tool execution.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from daemon.service import DaemonService
from daemon.registry import ToolResult

logger = logging.getLogger(__name__)

# Request/Response models
class ToolCallRequest(BaseModel):
    """Request to execute a tool."""
    tool: str = Field(..., description="Name of the tool to execute")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class ToolCallResponse(BaseModel):
    """Response from tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    tools_count: int
    tools: list[str]


class DiscordAuthor(BaseModel):
    """Discord message author info."""
    username: str
    id: Optional[str] = None


class DiscordEnvelope(BaseModel):
    """Envelope format from discord-gateway."""
    type: str
    data: 'DiscordMessageData'


class DiscordMessageData(BaseModel):
    """Discord message data with camelCase from gateway."""
    channelId: str
    messageId: str
    author: DiscordAuthor
    content: str
    timestamp: str
    guildId: Optional[str] = None
    isDirectMessage: bool = False


class DiscordMessageResponse(BaseModel):
    """Response to send back to Discord."""
    content: str
    reply_to_message_id: Optional[str] = None


# Global daemon reference
_daemon: Optional[DaemonService] = None


async def get_daemon_service() -> DaemonService:
    """Get or initialize the daemon service."""
    global _daemon
    if _daemon is None:
        # Reset the global registry to ensure fresh state (lazy import to avoid module-level singleton)
        from daemon.registry import _global_registry
        from daemon.service import get_daemon
        _global_registry = None
        
        _daemon = get_daemon()
        await _daemon.start()
    return _daemon


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    daemon = await get_daemon_service()
    logger.info("Bridge server starting...")
    yield
    # Shutdown
    logger.info("Bridge server shutting down...")
    if _daemon:
        await _daemon.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Scout Bridge",
    description="Transport layer for Scout core daemon",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns daemon status and registered tools.
    """
    daemon = await get_daemon_service()
    status = await daemon.health_check()
    return HealthResponse(**status)


@app.post("/execute", response_model=ToolCallResponse)
async def execute_tool(request: ToolCallRequest) -> ToolCallResponse:
    """
    Execute a tool call via the daemon.
    
    Args:
        request: Tool name and parameters
        
    Returns:
        Tool execution result
    """
    daemon = await get_daemon_service()
    result: ToolResult = await daemon.execute_tool(request.tool, **request.params)
    
    return ToolCallResponse(
        success=result.success,
        result=result.result,
        error=result.error,
    )


@app.post("/discord/in", response_model=DiscordMessageResponse)
async def receive_discord_message(request: Request) -> DiscordMessageResponse:
    """
    Receive and process a Discord message.
    
    Accepts the envelope format from discord-gateway:
    { type: 'discord_message', data: { channelId, messageId, author: { username }, content, timestamp, guildId, isDirectMessage } }
    
    Wires to orchestrator ActionLoop for LLM processing.
    """
    # Parse the raw body to handle envelope format
    body = await request.json()
    logger.info(f"Received Discord envelope: type={body.get('type')}")
    
    # Extract message data from envelope
    if body.get('type') == 'discord_message' and 'data' in body:
        msg_data = body['data']
        channel_id = msg_data.get('channelId', '')
        message_id = msg_data.get('messageId', '')
        author_username = msg_data.get('author', {}).get('username', 'unknown')
        content = msg_data.get('content', '')
        timestamp = msg_data.get('timestamp', '')
        is_direct = msg_data.get('isDirectMessage', False)
    else:
        # Fallback: treat body as direct message
        channel_id = body.get('channel_id', body.get('channelId', ''))
        message_id = body.get('message_id', body.get('messageId', ''))
        author_username = body.get('author', 'unknown')
        content = body.get('content', '')
        timestamp = body.get('timestamp', '')
        is_direct = body.get('isDirectMessage', False)
    
    logger.info(f"Processing message from {author_username}: {content[:50]}...")
    
    # Run orchestrator in thread pool to avoid blocking
    try:
        result = await run_orchestrator(channel_id, content, {
            'username': author_username,
            'is_direct_message': is_direct,
        })
        response_text = result.response
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        response_text = f"Sorry, I encountered an error processing your request."
    
    return DiscordMessageResponse(
        content=response_text,
        reply_to_message_id=message_id,
    )


async def run_orchestrator(channel_id: str, message: str, user_info: dict) -> 'ActionResult':
    """
    Run the orchestrator action loop in an async context.
    
    Imports and creates ActionLoop inline to avoid circular imports
    at module load time.
    """
    # Import here to avoid circular deps
    from orchestrator.action_loop import ActionLoop, ActionResult
    from memory_layer import MemoryStore
    
    loop = ActionLoop(memory_store=MemoryStore())
    
    # Run in executor to avoid blocking the event loop
    # since ActionLoop.run() is async but the LLM call may block
    result = await loop.run(
        channel_id=channel_id,
        user_message=message,
        user_info=user_info,
    )
    
    return result


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with structured JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with structured JSON."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
        }
    )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    uvicorn.run(
        "bridge.server:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )