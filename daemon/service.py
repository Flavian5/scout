"""
Core Daemon Service

Long-running daemon process that hosts the tool registry and handles requests.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from daemon.registry import ToolRegistry, get_registry, ToolResult

logger = logging.getLogger(__name__)


class DaemonService:
    """
    Core daemon that runs continuously and hosts the tool registry.
    
    Provides:
    - Tool registry for in-process tool execution
    - Graceful shutdown handling
    - Health check endpoint
    """

    def __init__(self, port: int = 8080):
        self.port = port
        self.registry: ToolRegistry = get_registry()
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the daemon service."""
        logger.info("Starting Scout Core Daemon...")
        self._running = True
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        # Register built-in skills
        await self._register_skills()

        # Mark as running
        self._shutdown_event.clear()
        logger.info(f"Scout Core Daemon running on port {self.port}")
        logger.info(f"Registered tools: {self.registry.list_tools()}")

    async def _register_skills(self) -> None:
        """Register available skill modules."""
        skill_modules = [
            'skills.discord_bot.check',
            'skills.signal_detector.detect',
            'skills.email_alerts.check',
            'skills.linear_tickets.check',
        ]
        
        for skill_path in skill_modules:
            try:
                self.registry.load_skill_module(skill_path)
            except Exception as e:
                logger.warning(f"Could not load {skill_path}: {e}")

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down Scout Core Daemon...")
        self._running = False
        self._shutdown_event.set()

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()

    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self._running

    async def health_check(self) -> dict:
        """Return daemon health status."""
        return {
            "status": "healthy" if self._running else "stopped",
            "tools_count": len(self.registry.list_tools()),
            "tools": self.registry.list_tools(),
        }

    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool via the registry."""
        return await self.registry.execute(name, **kwargs)


# Default daemon instance
_daemon: Optional[DaemonService] = None


def get_daemon() -> DaemonService:
    """Get or create the global daemon instance."""
    global _daemon
    if _daemon is None:
        _daemon = DaemonService()
    return _daemon


async def run_daemon(port: int = 8080) -> None:
    """Run the daemon service."""
    daemon = get_daemon()
    daemon.port = port
    await daemon.start()
    await daemon.wait_for_shutdown()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(run_daemon())