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

from daemon.service import get_daemon, DaemonService
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


class DiscordMessageRequest(BaseModel):
    """Incoming Discord message to process."""
    channel_id: str
    message_id: str
    content: str
    author: str
    timestamp: str
    reply_to: Optional[str] = None


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
async def receive_discord_message(request: DiscordMessageRequest) -> DiscordMessageResponse:
    """
    Receive and process a Discord message.
    
    For now, this echoes back the message with a simple response.
    Full LLM processing is handled by the orchestrator (SEM-85).
    """
    logger.info(f"Received Discord message from {request.author}: {request.content[:50]}...")
    
    # Simple echo response for now
    return DiscordMessageResponse(
        content=f"Received: {request.content[:100]}",
        reply_to_message_id=request.message_id,
    )


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